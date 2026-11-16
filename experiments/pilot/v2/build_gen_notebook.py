#!/usr/bin/env python3
"""Kaggle notebook: LTX-Video continues the v2 3D stimuli from a clip, on both T4s in parallel,
then V-JEPA 2 judges them and analyze_v2.py scores and filters the clips.
Inputs come from the render kernel's output (kernel_sources), found under /kaggle/input.
   python build_gen_notebook.py --samples 8 --items pilot --out gen_v2_pilot.ipynb"""
import argparse, base64, io, json, os, tarfile
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--samples", type=int, default=8)
ap.add_argument("--items", default="all", help="'all' or a comma list of substrings of item ids")
ap.add_argument("--steps", type=int, default=40)
ap.add_argument("--still", type=int, default=0, help="also N samples from the still (0 = clip mode only)")
ap.add_argument("--repo", default="Lightricks/LTX-Video-0.9.5", help="e.g. Lightricks/LTX-Video-0.9.7-dev (13B, needs an A100)")
ap.add_argument("--dtype", default="float16", help="bfloat16 on A100/H100")
ap.add_argument("--inputs", default="", help="folder with the stim3d items (default: look under /kaggle/input)")
ap.add_argument("--out", default="gen_v2.ipynb")
a = ap.parse_args()
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tf:
    tf.add(os.path.join(HERE, "..", "..", "analyze.py"), arcname="analyze.py")
    tf.add(os.path.join(HERE, "..", "analyze_v2.py"), arcname="pilot/analyze_v2.py")
blob = base64.b64encode(buf.getvalue()).decode()

WORKER = r'''
import os, sys, json, math, time
import numpy as np, torch, imageio.v2 as imageio
from PIL import Image
cfg = json.load(open(sys.argv[1])); wid, nw = int(sys.argv[2]), int(sys.argv[3])
sys.path.insert(0, cfg["src"]); sys.path.insert(0, cfg["src"] + "/pilot")
import analyze_v2
ITEMS = analyze_v2.load_items(cfg["inputs"])
if cfg["items"] != "all":
    ITEMS = {k: m for k, m in ITEMS.items() if any(s in k for s in cfg["items"].split(","))}
W, H = cfg["W"], cfg["H"]
SCENE = "a curved metal tube lying on a wooden table, filmed from above by a static camera"
def direction(m):
    _, ang, _ = analyze_v2.exit_frame(m)
    d = math.degrees(ang) % 360
    return ["right", "bottom right", "bottom", "bottom left", "left", "top left", "top", "top right"][int(((d + 22.5) % 360) // 45)]
def prompt_for(d):
    return (f"A glossy red ball with an orange stripe rolls quickly through {SCENE}. The ball is moving towards the {d} "
            "of the frame; it rolls out of the open end of the tube and keeps rolling across the table. "
            "Realistic, smooth continuous motion, static camera, the ball keeps its size, shape and colour.")
NEG = ("static, frozen, still image, ball disappears, ball shrinks, ball grows, ball fades, two balls, morphing, "
       "tube changes shape, camera motion, zoom, cut, blurry, distorted, text, watermark, worst quality")
from diffusers import LTXConditionPipeline
from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
dt = getattr(torch, cfg["dtype"])
DIRS = {k: direction(m) for k, m in ITEMS.items()}
EMB_PATH = os.path.join(os.path.dirname(cfg["out"]), "prompt_emb.pt")
if wid < 0:
    # encode once (T5 only), so the GPU workers never hold the 9 GB text encoder in host RAM together
    pipe = LTXConditionPipeline.from_pretrained(cfg["repo"], transformer=None, vae=None, torch_dtype=dt)
    pipe.text_encoder.to("cuda")
    with torch.no_grad():
        EMB = {d: [t.cpu() for t in pipe.encode_prompt(prompt=prompt_for(d), negative_prompt=NEG, do_classifier_free_guidance=True,
                                                       device="cuda", max_sequence_length=128)] for d in set(DIRS.values())}
    os.makedirs(os.path.dirname(EMB_PATH), exist_ok=True); torch.save(EMB, EMB_PATH)
    print("[enc] prompts encoded:", sorted(EMB), flush=True); sys.exit(0)
EMB = {d: [t.to("cuda") for t in v] for d, v in torch.load(EMB_PATH).items()}
pipe = LTXConditionPipeline.from_pretrained(cfg["repo"], text_encoder=None, tokenizer=None, torch_dtype=dt)
pipe.transformer.to("cuda"); pipe.vae.to("cuda"); pipe.vae.enable_tiling()
def frames(m, name):
    return np.stack(imageio.mimread(os.path.join(m["dir"], m["files"][name]), memtest=False))[..., :3]
todo = []
for iid in sorted(ITEMS):
    for j in range(cfg["samples"]):
        todo.append((iid, "clip", j))
    for j in range(cfg["still"]):
        todo.append((iid, "still", j))
todo = todo[wid::nw]
os.makedirs(cfg["out"], exist_ok=True)
for i, (iid, mode, j) in enumerate(todo):
    path = f"{cfg['out']}/{iid}__{mode}__s{j}.mp4"
    if os.path.exists(path): continue
    m = ITEMS[iid]; t0 = time.time()
    if mode == "clip":
        ctx = frames(m, "context")[-cfg["cond"]:]
        cond = LTXVideoCondition(video=[Image.fromarray(f).resize((W, H)) for f in ctx], frame_index=0)
    else:
        cond = LTXVideoCondition(image=Image.open(os.path.join(m["dir"], m["files"]["still"])).convert("RGB").resize((W, H)), frame_index=0)
    pe, pm, npe, npm = EMB[DIRS[iid]]
    seed = 7919 * j + sum(map(ord, iid)) + (0 if mode == "clip" else 100000)
    v = pipe(conditions=[cond], prompt_embeds=pe, prompt_attention_mask=pm, negative_prompt_embeds=npe,
             negative_prompt_attention_mask=npm, width=W, height=H, num_frames=cfg["num_frames"], frame_rate=24,
             num_inference_steps=cfg["steps"], guidance_scale=3.0,
             generator=torch.Generator("cpu").manual_seed(seed), output_type="np").frames[0]
    v = (np.clip(np.nan_to_num(v), 0, 1) * 255).astype(np.uint8)
    imageio.mimwrite(path, v, fps=24, macro_block_size=16)
    print(f"[gpu{wid}] {i+1}/{len(todo)} {os.path.basename(path)} {time.time()-t0:.0f}s std {v.std():.1f}", flush=True)
print(f"[gpu{wid}] done", flush=True)
'''

cells = []
md = lambda s: cells.append(dict(cell_type="markdown", metadata={}, source=s))
code = lambda s: cells.append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=s))
md(f"""# Slide 21 v2: LTX-Video on the new 3D stimuli

Clip mode, last 33 input frames (24 fps), 48 new frames (2 s), {a.samples} samples per item, both T4s in parallel.
Then V-JEPA 2 and the scoring with the quality filter (`analyze_v2.py`).""")
code('!pip install -q -U "diffusers>=0.35" "transformers>=4.55" accelerate sentencepiece imageio imageio-ffmpeg')
code(f'''import base64, io, tarfile, os, sys, json, glob, subprocess, time
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
BLOB = "{blob}"
SRC = "/kaggle/working/src"
tarfile.open(fileobj=io.BytesIO(base64.b64decode(BLOB)), mode="r:gz").extractall(SRC)
del BLOB
metas = glob.glob(("{a.inputs}" or "/kaggle/input") + "/**/meta3d.json", recursive=True)
INPUTS = os.path.commonpath([os.path.dirname(os.path.dirname(os.path.dirname(p))) for p in metas])
print(len(metas), "items under", INPUTS)
CFG = dict(src=SRC, inputs=INPUTS, items="{a.items}", samples={a.samples}, still={a.still}, W=768, H=512,
           cond=33, num_frames=81, steps={a.steps}, out="/kaggle/working/out/ltx", repo="{a.repo}", dtype="{a.dtype}")
json.dump(CFG, open("/kaggle/working/cfg.json", "w"))
open("/kaggle/working/worker.py", "w").write({WORKER!r})
import torch
NG = max(1, torch.cuda.device_count()); print(NG, "GPUs")''')
code('''t0 = time.time()
import threading
def pump(p, g):
    tail = []
    for line in p.stdout:
        line = line.rstrip()
        if not line.strip() or "it/s]" in line or "s/it]" in line: continue
        tail = (tail + [line])[-40:]
        if line.startswith("[gpu") or line.startswith("[enc"): print(line, flush=True)
    rc = p.wait()
    if rc != 0: print(f"worker {g} failed, exit code {rc}:\\n" + "\\n".join(tail), flush=True)
    return rc
run = lambda g, env: subprocess.Popen([sys.executable, "/kaggle/working/worker.py", "/kaggle/working/cfg.json", str(g), str(NG)],
                                      env=dict(os.environ, **env), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
pump(run(-1, dict(CUDA_VISIBLE_DEVICES="0")), -1)
procs = []
for g in range(NG):
    procs.append(run(g, dict(CUDA_VISIBLE_DEVICES=str(g))))
    time.sleep(90)  # stagger the weight loading to keep host RAM in bounds
th = [threading.Thread(target=pump, args=(p, g)) for g, p in enumerate(procs)]
[t.start() for t in th]; [t.join() for t in th]
print(f"generation {time.time()-t0:.0f} s")''')
code('''# V-JEPA 2 on the same items (correct vs curving continuation, from the clip)
import numpy as np, imageio.v2 as imageio, csv
sys.path.insert(0, SRC); sys.path.insert(0, SRC + "/pilot")
import analyze_v2
ITEMS = analyze_v2.load_items(INPUTS)
if CFG["items"] != "all":
    ITEMS = {k: m for k, m in ITEMS.items() if any(s in k for s in CFG["items"].split(","))}
from transformers import AutoModel, AutoVideoProcessor
vj = AutoModel.from_pretrained("facebook/vjepa2-vitl-fpc64-256", dtype=torch.float16).cuda().eval()
proc = AutoVideoProcessor.from_pretrained("facebook/vjepa2-vitl-fpc64-256")
def fr_of(m, n): return np.stack(imageio.mimread(os.path.join(m["dir"], m["files"][n]), memtest=False))[..., :3]
def square(fr):
    T, h, w, _ = fr.shape; out = np.empty((T, w, w, 3), np.uint8); out[:] = np.median(fr[0, 0], axis=0).astype(np.uint8)
    out[:, (w - h) // 2:(w - h) // 2 + h] = fr; return out
@torch.no_grad()
def surprise(fr16):
    x = proc(videos=square(fr16), return_tensors="pt")["pixel_values_videos"].to("cuda", torch.float16)
    full = vj.get_vision_features(x); N = full.shape[1]; Nc = N // 2
    tm = [torch.arange(Nc, N, device="cuda")[None]]; cm = [torch.arange(Nc, device="cuda")[None]]
    ctx = vj.get_vision_features(x[:, :8])
    pred = vj.predictor(encoder_hidden_states=ctx, context_mask=cm, target_mask=tm).last_hidden_state
    return (pred.float() - full[:, Nc:].float()).abs().mean().item()
rows = []
for iid, m in sorted(ITEMS.items()):
    if "anomalous_impetus" not in m["files"]: continue
    c = m["context_end_frame"]; cor, imp = fr_of(m, "full"), fr_of(m, "anomalous_impetus")
    for mode in ("still", "clip"):
        # 16 frames at 12 fps (every 2nd frame of the 24 fps clip): 8 context + 8 future
        def clip16(fr):
            fut = fr[c + 2:c + 18:2]
            ctx = fr[c - 14:c + 1:2] if mode == "clip" else np.repeat(fr[c:c + 1], 8, 0)
            return np.concatenate([ctx, fut])
        rows.append(dict(item_id=iid, shape=m["params"]["shape"], speed=m["params"]["speed"], mode=mode,
                         surprise_correct=surprise(clip16(cor)), surprise_impetus=surprise(clip16(imp))))
os.makedirs("/kaggle/working/out", exist_ok=True)
with open("/kaggle/working/out/vjepa.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r["item_id"], r["mode"], "prefers curving" if r["surprise_impetus"] < r["surprise_correct"] else "prefers straight")
del vj; torch.cuda.empty_cache()''')
code('''res = "/kaggle/working/results"
r = subprocess.run([sys.executable, SRC + "/pilot/analyze_v2.py", "--inputs", INPUTS, "--gen", "ltx=/kaggle/working/out/ltx",
                    "--cond", "ltx_clip=33", "--vjepa", "/kaggle/working/out/vjepa.csv", "--out", res], capture_output=True, text=True)
print(r.stdout, r.stderr[-3000:])
for f in [f"{res}/summary.csv", f"{res}/per_clip.csv", "/kaggle/working/out/vjepa.csv"]:
    print("=====", f); print(open(f).read() if os.path.exists(f) else "(missing)")
!cd /kaggle/working && zip -qr slide21_v2_results.zip results out && ls -la slide21_v2_results.zip''')
code('''# contact sheets in the log (downloads of the output are not always possible): one JPEG per item,
# row 0 = real future, then the clip samples (kept ones first), 7 frames each from the last conditioning frame
import csv as _csv, base64 as _b64, io as _io
from PIL import Image, ImageDraw
pc = list(_csv.DictReader(open(f"{res}/per_clip.csv"))) if os.path.exists(f"{res}/per_clip.csv") else []
TW, TH, NC = 160, 107, 7
for iid, m in sorted(ITEMS.items()):
    c = m["context_end_frame"]; full = fr_of(m, "full")
    rows = [("real", full[c:c + 49])]
    mine = sorted([r for r in pc if r["item_id"] == iid and r["mode"] == "clip"], key=lambda r: (r["label"].startswith("invalid"), r["sample"]))
    for r in mine[:6]:
        f = f"/kaggle/working/out/ltx/{iid}__clip__{r['sample']}.mp4"
        if os.path.exists(f): rows.append((f"{r['sample']} {r['label']} {r['bend_deg']}", fr_of({"dir": os.path.dirname(f), "files": {"x": os.path.basename(f)}}, "x")[32:]))
    sheet = Image.new("RGB", (TW * NC, TH * len(rows)), "white"); d = ImageDraw.Draw(sheet)
    for ri, (lab, fr) in enumerate(rows):
        idx = np.linspace(0, len(fr) - 1, NC).astype(int)
        for ci, k in enumerate(idx): sheet.paste(Image.fromarray(fr[k]).resize((TW, TH)), (ci * TW, ri * TH))
        d.rectangle((0, ri * TH, 8 * len(lab) + 4, ri * TH + 12), fill="black"); d.text((2, ri * TH), lab, fill="yellow")
    # second panel: the tracked paths of every clip sample over the last context frame
    ov = Image.fromarray(full[c]).convert("RGB"); od = ImageDraw.Draw(ov)
    real = [tuple(p) for p in m["ball_xy"][c:] if p is not None]
    if len(real) > 1: od.line(real, fill=(0, 200, 0), width=3)
    foil = [tuple(p) for p in (m.get("anomalous_impetus_xy") or [])[c:] if p is not None]
    if len(foil) > 1: od.line(foil, fill=(0, 120, 0), width=1)
    col = dict(impetus=(220, 0, 220), no_bias=(0, 90, 255), centrifugal=(255, 140, 0))
    for r in mine:
        pts = [tuple(p) for p in json.loads(r["path"]) if p]
        if len(pts) > 1: od.line(pts, fill=col.get(r["label"], (120, 120, 120)), width=2 if r["label"] in col else 1)
    ov = ov.resize((640, int(640 * ov.height / ov.width)))
    big = Image.new("RGB", (sheet.width, sheet.height + ov.height), "white"); big.paste(sheet, (0, 0)); big.paste(ov, (0, sheet.height))
    ImageDraw.Draw(big).text((4, sheet.height + 4), "green real, magenta impetus, blue no bias, orange centrifugal, grey invalid", fill="black")
    sheet = big
    b = _io.BytesIO(); sheet.save(b, "JPEG", quality=60); s64 = _b64.b64encode(b.getvalue()).decode()
    os.makedirs(f"{res}/sheets", exist_ok=True); sheet.save(f"{res}/sheets/{iid}.jpg", quality=85)
    ch = [s64[i:i + 3000] for i in range(0, len(s64), 3000)]
    for i, x in enumerate(ch): print(f"CS|{iid}|{i}|{len(ch)}|{x}")
!cd /kaggle/working && zip -qr slide21_v2_results.zip results out && ls -la slide21_v2_results.zip''')
nb = dict(cells=cells, metadata=dict(kernelspec=dict(display_name="Python 3", language="python", name="python3")), nbformat=4, nbformat_minor=5)
json.dump(nb, open(os.path.join(HERE, a.out), "w"), indent=1)
print("written", a.out)
