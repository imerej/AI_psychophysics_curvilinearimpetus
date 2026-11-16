#!/usr/bin/env python3
"""Kaggle notebook: a hosted state-of-the-art video model (default Seedance 2.5 image-to-video on fal.ai)
continues each v2 3D stimulus from its still (last frame before the tube exit), then analyze_v2.py scores
the clips exactly like the LTX run.
Inputs: the render kernel's output (slide21-render3d-v2-all), found under /kaggle/input.
Needs a fal.ai API key stored as a Kaggle secret named FAL_KEY (Add-ons -> Secrets), and Internet on.
No GPU is needed.
   python build_api_notebook.py --items pilot --samples 1 --out gen_v2_seedance_pilot.ipynb
   python build_api_notebook.py --items all --samples 1 --out gen_v2_seedance_all.ipynb"""
import argparse, base64, io, json, os, tarfile
HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = "c90_v200_s1,c180_v200_s1,c270_v200_s1,spiral_v200_s1,straight_v200_s1"
ap = argparse.ArgumentParser()
ap.add_argument("--items", default="pilot", help="'pilot' (one per tube shape), 'all', or a comma list of substrings of item ids")
ap.add_argument("--samples", type=int, default=1)
ap.add_argument("--endpoint", default="bytedance/seedance-2.5/image-to-video",
                help="fal endpoint; the notebook also tries the /us/ variant if this one is not found")
ap.add_argument("--resolution", default="480p")
ap.add_argument("--duration", default="5", help="seconds of video asked for")
ap.add_argument("--usd_per_s", type=float, default=0.27, help="price per generated second, for the spending cap (check fal's page)")
ap.add_argument("--max_usd", type=float, default=45.0, help="stop before the estimated spend passes this")
ap.add_argument("--name", default="seedance")
ap.add_argument("--out", default="gen_v2_seedance.ipynb")
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
md(f"""# Slide 21 v2: {a.name} (hosted API) on the 3D tube stimuli

Still mode: the model gets the last frame before the exit plus one fixed prompt saying the ball is exiting the tube (no direction given), and makes {a.duration} s at {a.resolution}.
{a.samples} sample(s) per item, items: `{a.items}`. Spending cap: about ${a.max_usd:.0f} at ${a.usd_per_s}/s (estimate; fal bills the real price).

Before running: **Add Input** -> the `slide21-render3d-v2-all` kernel output; **Add-ons -> Secrets** -> `FAL_KEY`; **Internet on**. No GPU needed.
Clips already downloaded are skipped, so re-running after a stop does not pay twice.""")
code('!pip install -q fal-client imageio imageio-ffmpeg')
code(f'''import base64, io, tarfile, os, sys, json, glob, math, time, subprocess, urllib.request
import numpy as np, imageio.v2 as imageio
from PIL import Image
from kaggle_secrets import UserSecretsClient
os.environ["FAL_KEY"] = UserSecretsClient().get_secret("FAL_KEY")
import fal_client
SRC = "/kaggle/working/src"
tarfile.open(fileobj=io.BytesIO(base64.b64decode("{blob}")), mode="r:gz").extractall(SRC)
sys.path.insert(0, SRC); sys.path.insert(0, SRC + "/pilot")
import analyze_v2
metas = glob.glob("/kaggle/input/**/meta3d.json", recursive=True)
INPUTS = os.path.commonpath([os.path.dirname(os.path.dirname(os.path.dirname(p))) for p in metas])
ITEMS = analyze_v2.load_items(INPUTS)
SEL = "{items}"
if SEL != "all":
    ITEMS = {{k: m for k, m in ITEMS.items() if any(s in k for s in SEL.split(","))}}
print(len(ITEMS), "items:", ", ".join(sorted(ITEMS)))
NAME, ENDPOINT, RES, DUR = "{a.name}", "{a.endpoint}", "{a.resolution}", "{a.duration}"
SAMPLES, USD_PER_S, MAX_USD = {a.samples}, {a.usd_per_s}, {a.max_usd}
OUT = f"/kaggle/working/out/{{NAME}}"; RAW = OUT + "_raw"
os.makedirs(OUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)
SCENE = "a curved metal tube, filmed from above by a static camera"
# one prompt for every item: it says the ball is about to exit, never which way it heads
# (the LTX run named a compass direction instead)
PROMPT = (f"A glossy red ball with an orange stripe rolls quickly through {{SCENE}}. The ball is exiting the tube: "
          "it rolls out of the open end of the tube and keeps rolling. "
          "Realistic, smooth continuous motion, static camera, the ball keeps its size, shape and colour.")
print("prompt:", PROMPT)
print("estimated cost:", len(ITEMS) * SAMPLES, "clips x", DUR, "s x $", USD_PER_S, "= $", round(len(ITEMS) * SAMPLES * float(DUR) * USD_PER_S, 2))''')
code('''# generate: one call per clip, saved as it goes; stops before the spending cap
def call(args):
    eps = [ENDPOINT] + ([ENDPOINT.replace("seedance-2.5/", "seedance-2.5/us/")] if "/us/" not in ENDPOINT else [])
    last, seed = None, args.pop("seed", None)
    for ep in eps:
        for extra in (dict(resolution=RES, duration=DUR, seed=seed), {}):
            try:
                kw = dict(args, **{k: v for k, v in extra.items() if v is not None})
                return ep, kw, fal_client.subscribe(ep, arguments=kw, with_logs=False)
            except Exception as e:   # unknown endpoint or argument: try the next form, print why
                last = e; print("  call failed with", ep, sorted(kw), "->", str(e)[:300])
    raise last
spent, log = 0.0, []
for iid in sorted(ITEMS):
    m = ITEMS[iid]
    url = None
    for j in range(SAMPLES):
        path = f"{OUT}/{iid}__still__s{j}.mp4"
        if os.path.exists(path): continue
        if spent + float(DUR) * USD_PER_S > MAX_USD:
            print("spending cap reached, stopping"); break
        if url is None:
            url = fal_client.upload_file(os.path.join(m["dir"], m["files"]["still"]))
        t0 = time.time()
        ep, kw, res = call(dict(prompt=PROMPT, image_url=url, seed=7919 * j + sum(map(ord, iid))))
        vurl = (res.get("video") or {}).get("url") or res.get("url")
        raw = f"{RAW}/{iid}__still__s{j}.mp4"; urllib.request.urlretrieve(vurl, raw)
        # bring the clip back to the stimulus size so the tracker's coordinates match; keep the model's fps
        rd = imageio.get_reader(raw); fps = rd.get_meta_data().get("fps", 24); fr = [f[..., :3] for f in rd]; rd.close()
        H0, W0 = fr[0].shape[:2]; W, H = m["size"]
        if abs(W0 / H0 - W / H) > 0.02: print(f"  note: aspect changed {W0}x{H0} vs {W}x{H}; stretched back")
        imageio.mimwrite(path, [np.array(Image.fromarray(f).resize((W, H))) for f in fr], fps=fps, macro_block_size=16)
        spent += float(DUR) * USD_PER_S
        log.append(dict(item_id=iid, sample=j, endpoint=ep, args=sorted(kw), fps=fps, n_frames=len(fr), size=f"{W0}x{H0}", seconds=round(time.time() - t0)))
        print(f"{iid} s{j}: {len(fr)} frames {W0}x{H0} @ {fps} fps, {time.time()-t0:.0f}s, about ${spent:.2f} so far", flush=True)
json.dump(log, open(f"{OUT}/calls.json", "w"), indent=1)
FPS = log[0]["fps"] if log else 24''')
code('''# score like the LTX run: frame 0 is the still, the tracker follows the ball after the exit
res = "/kaggle/working/results"
r = subprocess.run([sys.executable, SRC + "/pilot/analyze_v2.py", "--inputs", INPUTS, "--gen", f"{NAME}={OUT}",
                    "--cond", f"{NAME}_still=1", "--fps", f"{NAME}={FPS}", "--vjepa", "/nonexistent.csv", "--out", res],
                   capture_output=True, text=True)
print(r.stdout, r.stderr[-3000:])
for f in [f"{res}/summary.csv", f"{res}/per_clip.csv"]:
    print("=====", f); print(open(f).read() if os.path.exists(f) else "(missing)")
!cd /kaggle/working && zip -qr slide21_api_results.zip results out && ls -la slide21_api_results.zip''')
nb = dict(cells=cells, metadata=dict(kernelspec=dict(display_name="Python 3", language="python", name="python3")), nbformat=4, nbformat_minor=5)
json.dump(nb, open(os.path.join(HERE, a.out), "w"), indent=1)
print("written", a.out)
