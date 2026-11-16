#!/usr/bin/env python3
"""Kaggle notebook: an image-editing model (default Nano Banana on fal.ai) gets two frames of a v2 3D stimulus,
half a second apart, the second one just before the tube exit, and is asked to add the ball where it will be
0.5, 1 and 1.5 s later. The added balls are found by colour and the path is classed with analyze.classify
(keeps curving / straight / bends outward), the same rule as the video runs.
Inputs: the render kernel's output (slide21-render3d-v2-all) under /kaggle/input. Needs the Kaggle secret FAL_KEY
and Internet on. No GPU.
   python build_image_notebook.py --items pilot --samples 3 --out gen_v2_image_pilot.ipynb"""
import argparse, base64, io, json, os, tarfile
HERE = os.path.dirname(os.path.abspath(__file__))
# slow speed: at 120 px/s the ball stays in the picture for 1.5 s after the exit on every shape
PILOT = "c90_v120_s1,c180_v120_s1,c270_v120_s1,spiral_v120_s1,straight_v120_s1"
ap = argparse.ArgumentParser()
ap.add_argument("--items", default="pilot", help="'pilot', 'all', or a comma list of substrings of item ids")
ap.add_argument("--samples", type=int, default=3)
ap.add_argument("--endpoint", default="fal-ai/nano-banana/edit", help="fal image-edit endpoint taking image_urls")
ap.add_argument("--usd_per_image", type=float, default=0.04, help="for the spending cap (check fal's page)")
ap.add_argument("--max_usd", type=float, default=3.0)
ap.add_argument("--gap", type=float, default=0.5, help="seconds between the two input frames, and between predicted positions")
ap.add_argument("--name", default="nanobanana")
ap.add_argument("--out", default="gen_v2_image.ipynb")
a = ap.parse_args()
items = PILOT if a.items == "pilot" else a.items

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tf:
    tf.add(os.path.join(HERE, "..", "..", "analyze.py"), arcname="analyze.py")
    tf.add(os.path.join(HERE, "..", "analyze_v2.py"), arcname="pilot/analyze_v2.py")
blob = base64.b64encode(buf.getvalue()).decode()

cells = []
md = lambda s: cells.append(dict(cell_type="markdown", metadata={}, source=s))
code = lambda s: cells.append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=s))
md(f"""# Slide 21 v2: where will the ball be? ({a.name}, image editing)

Two frames {a.gap} s apart (the second just before the tube exit) -> one edited image with the ball added at
{a.gap}, {2*a.gap:g} and {3*a.gap:g} s later. {a.samples} sample(s) per item, items: `{a.items}`.
Spending cap about ${a.max_usd:g} at ${a.usd_per_image}/image (estimate; fal bills the real price).

Before running: **Add Input** -> the `slide21-render3d-v2-all` notebook output; **Add-ons -> Secrets** -> `FAL_KEY`; **Internet on**. No GPU.
Images already downloaded are skipped, so re-running does not pay twice.""")
code('!pip install -q fal-client imageio imageio-ffmpeg scipy')
code(f'''import base64, io, tarfile, os, sys, json, glob, math, time, csv, urllib.request
import numpy as np, imageio.v2 as imageio
from PIL import Image, ImageDraw
from scipy import ndimage
from kaggle_secrets import UserSecretsClient
os.environ["FAL_KEY"] = UserSecretsClient().get_secret("FAL_KEY")
import fal_client
SRC = "/kaggle/working/src"
tarfile.open(fileobj=io.BytesIO(base64.b64decode("{blob}")), mode="r:gz").extractall(SRC)
sys.path.insert(0, SRC); sys.path.insert(0, SRC + "/pilot")
import analyze as A, analyze_v2
metas = glob.glob("/kaggle/input/**/meta3d.json", recursive=True)
INPUTS = os.path.commonpath([os.path.dirname(os.path.dirname(os.path.dirname(p))) for p in metas])
ITEMS = analyze_v2.load_items(INPUTS)
SEL = "{items}"
if SEL != "all":
    ITEMS = {{k: m for k, m in ITEMS.items() if any(s in k for s in SEL.split(","))}}
print(len(ITEMS), "items:", ", ".join(sorted(ITEMS)))
NAME, ENDPOINT, SAMPLES, USD, MAX_USD, GAP = "{a.name}", "{a.endpoint}", {a.samples}, {a.usd_per_image}, {a.max_usd}, {a.gap}
OUT = f"/kaggle/working/out/{{NAME}}"; os.makedirs(OUT, exist_ok=True); os.makedirs(OUT + "_inputs", exist_ok=True)
T = [GAP, 2 * GAP, 3 * GAP]
fmt = lambda t: f"{{t:g}} second" + ("" if t == 1 else "s")
# no direction and no mention of curving: the two frames are the only motion information
PROMPT = (f"The two images are frames from the same video, filmed from above by a static camera, taken {{fmt(GAP)}} apart: "
          "the first image is earlier, the second image is later. A glossy red ball with an orange stripe is rolling quickly "
          "through a metal tube and is exiting the tube. Edit the second image: keep the ball where it is, and add three more "
          f"copies of the same ball showing where it will be {{fmt(T[0])}}, {{fmt(T[1])}} and {{fmt(T[2])}} after the second image. "
          "Change nothing else: same camera, same scene, same ball size.")
print("prompt:", PROMPT)
print("estimated cost: $", round(len(ITEMS) * SAMPLES * USD, 2))''')
code('''# generate: one call per image, saved as it goes
def frames(m, name):
    return np.stack(imageio.mimread(os.path.join(m["dir"], m["files"][name]), memtest=False))[..., :3]
def call(args):
    try:
        return fal_client.subscribe(ENDPOINT, arguments=dict(args, num_images=1, output_format="png"), with_logs=False)
    except Exception as e:   # an argument this endpoint does not know: retry with the two required ones
        print("  call failed ->", str(e)[:300], "; retrying with prompt and image_urls only")
        return fal_client.subscribe(ENDPOINT, arguments=args, with_logs=False)
spent, log = 0.0, []
for iid in sorted(ITEMS):
    m = ITEMS[iid]; W, H = m["size"]
    ctx = frames(m, "context"); c = len(ctx) - 1; k = int(round(GAP * m["fps"]))
    ins = []
    for nm, f in (("a", ctx[c - k]), ("b", ctx[c])):
        p = f"{OUT}_inputs/{iid}_{nm}.png"; Image.fromarray(f).save(p); ins.append(p)
    urls = None
    for j in range(SAMPLES):
        path = f"{OUT}/{iid}__img__s{j}.png"
        if os.path.exists(path): continue
        if spent + USD > MAX_USD: print("spending cap reached, stopping"); break
        urls = urls or [fal_client.upload_file(p) for p in ins]
        t0 = time.time()
        res = call(dict(prompt=PROMPT, image_urls=urls))
        raw = path.replace(".png", "_raw.png"); urllib.request.urlretrieve(res["images"][0]["url"], raw)
        im = Image.open(raw).convert("RGB"); W0, H0 = im.size
        if abs(W0 / H0 - W / H) > 0.02: print(f"  note: aspect changed {W0}x{H0} vs {W}x{H}; stretched back")
        im.resize((W, H)).save(path); spent += USD
        log.append(dict(item_id=iid, sample=j, size=f"{W0}x{H0}", seconds=round(time.time() - t0)))
        print(f"{iid} s{j}: {W0}x{H0}, {time.time()-t0:.0f}s, about ${spent:.2f} so far", flush=True)
json.dump(log, open(f"{OUT}/calls.json", "w"), indent=1)''')
code('''# score: red ball-sized blobs = balls; drop the one at the current position; the rest, ordered by distance
# along the exit direction, form the predicted path, classed by analyze.classify (same 5 degree rule as the videos)
rows = []
for path in sorted(glob.glob(f"{OUT}/*__img__s*.png")):
    if path.endswith("_raw.png"): continue
    iid, _, samp = os.path.basename(path)[:-4].split("__"); m = ITEMS[iid]
    img = np.array(Image.open(path).convert("RGB"))
    r = m["ball_radius"]; area0 = math.pi * r * r
    lab, n = ndimage.label(analyze_v2.red_mask(img[None])[0])
    blobs = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if 0.3 * area0 <= len(xs) <= 3.0 * area0: blobs.append((xs.mean(), ys.mean(), len(xs)))
    cur = np.array(m["ball_xy"][m["context_end_frame"]], float)
    kept_cur = any(math.hypot(x - cur[0], y - cur[1]) < 1.5 * r for x, y, _ in blobs)
    new = np.array([(x, y) for x, y, _ in blobs if math.hypot(x - cur[0], y - cur[1]) >= 1.5 * r]).reshape(-1, 2)
    exit_xy, ang, side = analyze_v2.exit_frame(m)
    if len(new):
        rot = analyze_v2.rotate(new, exit_xy, ang); new, rot = new[np.argsort(rot[:, 0])], rot[np.argsort(rot[:, 0])]
    else:
        rot = new
    old = (A.MIN_POINTS, A.MIN_TRAVEL); A.MIN_POINTS, A.MIN_TRAVEL = 2, 30.0 * img.shape[1] / 480
    try:
        label, bend, npts = A.classify(rot, exit_xy, side)
    finally:
        A.MIN_POINTS, A.MIN_TRAVEL = old
    # real ball at the same three moments, for comparison
    k = int(round(GAP * m["fps"])); c = m["context_end_frame"]
    real = [m["ball_xy"][c + i * k] if c + i * k < len(m["ball_xy"]) else None for i in (1, 2, 3)]
    rows.append(dict(model=NAME, item_id=iid, shape=m["params"]["shape"], sample=samp, label=label,
                     bend_deg=round(bend, 2) if bend == bend else "", n_new_balls=len(new), current_ball_kept=kept_cur,
                     points=json.dumps([[round(x, 1), round(y, 1)] for x, y in new]), real=json.dumps(real)))
    # overlay for checking by eye: green = real path, magenta = detected balls
    ov = Image.fromarray(img); d = ImageDraw.Draw(ov)
    rp = [tuple(p) for p in m["ball_xy"][c:] if p]
    if len(rp) > 1: d.line(rp, fill=(0, 200, 0), width=2)
    for x, y in new: d.ellipse((x - r, y - r, x + r, y + r), outline=(255, 0, 255), width=3)
    d.text((6, 6), f"{iid} {samp}: {label} {bend:.1f} deg" if bend == bend else f"{iid} {samp}: {label}", fill=(255, 255, 0))
    os.makedirs("/kaggle/working/results/overlays", exist_ok=True); ov.save(f"/kaggle/working/results/overlays/{iid}__{samp}.jpg", quality=85)
os.makedirs("/kaggle/working/results", exist_ok=True)
with open("/kaggle/working/results/per_image.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["item_id"]); w.writeheader(); w.writerows(rows)
for r in rows: print(r["item_id"], r["sample"], r["label"], r["bend_deg"], "new balls:", r["n_new_balls"], "current kept:", r["current_ball_kept"])
curved = [r for r in rows if r["shape"] != "straight" and not r["label"].startswith("invalid")]
print(f"curved tubes: {sum(r['label'] == 'impetus' for r in curved)} of {len(curved)} valid keep curving; "
      f"straight: {[r['label'] for r in rows if r['shape'] == 'straight']}")
!cd /kaggle/working && zip -qr slide21_image_results.zip results out && ls -la slide21_image_results.zip''')
nb = dict(cells=cells, metadata=dict(kernelspec=dict(display_name="Python 3", language="python", name="python3")), nbformat=4, nbformat_minor=5)
json.dump(nb, open(os.path.join(HERE, a.out), "w"), indent=1)
print("written", a.out)
