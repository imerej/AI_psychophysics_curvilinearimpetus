#!/usr/bin/env python3
"""Builds slide21_pilot_kaggle.ipynb with the pilot inputs and both scoring scripts embedded,
so the notebook needs no Kaggle dataset.   python build_notebook.py inputs_big"""
import base64, io, json, os, sys, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("inputs", nargs="?", default="inputs_big")
ap.add_argument("--models", default="vjepa,ltx,wan", help="which parts to run")
ap.add_argument("--out", default="slide21_pilot_kaggle.ipynb")
ap.add_argument("--style", default="2d", choices=["2d", "3d"])
a = ap.parse_args()
inputs = a.inputs
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tf:
    tf.add(inputs, arcname="inputs_big")
    tf.add(os.path.join(HERE, "..", "analyze.py"), arcname="analyze.py")
    tf.add(os.path.join(HERE, "analyze_v2.py"), arcname="pilot/analyze_v2.py")
blob = base64.b64encode(buf.getvalue()).decode()

cells = []
md = lambda s: cells.append(dict(cell_type="markdown", metadata={}, source=s))
code = lambda s: cells.append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=s))

md("""# Slide 21 pilot: bigger ball, better settings

5 A1 tube items (straight, 90°, 180°, 270°, spiral; 120 px/s, seed 1), re-rendered at 768×512 with a ball about 38 px across.

1. **V-JEPA 2**: surprise on the true vs the curving continuation (still and clip).
2. **LTX-Video 0.9.5**: 50 steps, motion prompt, still or last 17 frames of the clip, 2 samples each (20 clips).
3. **Wan 2.2 TI2V-5B**: from the still, 1 sample per item (5 clips). Stops itself if one clip takes more than 25 min.
4. Robust tracker and quality check (`analyze_v2.py`).""")
code('!pip install -q -U "diffusers>=0.35" "transformers>=4.55" accelerate sentencepiece ftfy imageio imageio-ffmpeg matplotlib')
code(f'''import base64, io, tarfile, os
BLOB = "{blob}"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.makedirs("/kaggle/working/src", exist_ok=True)
tarfile.open(fileobj=io.BytesIO(base64.b64decode(BLOB)), mode="r:gz").extractall("/kaggle/working/src")
del BLOB
print(os.listdir("/kaggle/working/src"))''')
code('''# ---- settings
RUN_VJEPA, RUN_LTX, RUN_WAN = {RUNS}
LTX_SAMPLES, WAN_SAMPLES = 2, 1
MODES = ["still", "clip"]
LTX_REPO = "Lightricks/LTX-Video-0.9.5"
WAN_REPO = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
VJEPA_REPO = "facebook/vjepa2-vitl-fpc64-256"
W, H = 768, 512
NUM_FRAMES = 49                  # LTX: 8k+1; Wan: 4k+1
LTX_STEPS, WAN_STEPS = 50, 40
CLIP_COND = 17                   # LTX clip mode: last 17 input frames (8k+1)
WAN_MAX_S = 25 * 60              # give up on Wan if one clip takes longer than this
STYLE = "{STYLE}"
SCENE = ("a curved metal tube lying on a wooden table, filmed by a static camera" if STYLE == "3d"
         else "a curved grey tube lying on a flat light grey table, seen from directly above")
def prompt_for(direction):
    # the direction the ball is already rolling at the tube mouth (people get it from the picture too)
    return (f"A glossy red ball rolls quickly through {SCENE}. The ball is moving towards the {direction} "
            "of the frame; it rolls out of the open end of the tube and keeps rolling across the table. "
            "Realistic, smooth continuous motion, static camera, the ball keeps its size, shape and colour.")
NEGATIVE = ("static, frozen, still image, ball disappears, ball shrinks, ball fades, morphing, tube changes shape, "
            "camera motion, blurry, distorted, text, watermark, worst quality")

import glob, json, sys, time, csv, math
import numpy as np, torch, imageio.v2 as imageio
from PIL import Image
ROOT = "/kaggle/working/src"; sys.path.insert(0, ROOT); sys.path.insert(0, ROOT + "/pilot")
import analyze
import analyze_v2
ITEMS = analyze_v2.load_items(ROOT + "/inputs_big")
def direction(m):
    _, ang, _ = analyze_v2.exit_frame(m)
    d = math.degrees(ang) % 360
    return ["right", "bottom right", "bottom", "bottom left", "left", "top left", "top", "top right"][int(((d + 22.5) % 360) // 45)]
DIRS = {iid: direction(m) for iid, m in ITEMS.items()}
print(DIRS)
OUT = "/kaggle/working/out"
for d in ("ltx", "wan"): os.makedirs(f"{OUT}/{d}", exist_ok=True)
print(len(ITEMS), "items;", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO GPU")

def frames_of(m, name):
    fr = np.stack(imageio.mimread(os.path.join(m["dir"], m["files"][name]), memtest=False))[..., :3]
    return fr

def to_model(img):                               # every model input is resized to W x H
    return Image.fromarray(img).resize((W, H), Image.LANCZOS) if isinstance(img, np.ndarray) else img.resize((W, H), Image.LANCZOS)

def check(v, name):
    v = np.nan_to_num(v)
    ok = v.std() > 2
    print(f"{name}: std {v.std():.1f}", "" if ok else "BLANK")
    return ok''')
md("## 1 · V-JEPA 2")
code('''if RUN_VJEPA:
    from transformers import AutoModel, AutoVideoProcessor
    vj = AutoModel.from_pretrained(VJEPA_REPO, dtype=torch.float16).cuda().eval()
    proc = AutoVideoProcessor.from_pretrained(VJEPA_REPO)
    def square(fr):
        T, h, w, _ = fr.shape
        out = np.empty((T, w, w, 3), np.uint8); out[:] = np.median(fr[0, 0], axis=0).astype(np.uint8); y0 = (w - h) // 2
        out[:, y0:y0 + h] = fr
        return out
    def to_tensor(fr):
        return proc(videos=square(fr), return_tensors="pt")["pixel_values_videos"].to("cuda", torch.float16)
    METHOD = None
    @torch.no_grad()
    def surprise(fr16):
        global METHOD
        x = to_tensor(fr16)
        full = vj.get_vision_features(x); N = full.shape[1]; Nc = N // 2
        tm = [torch.arange(Nc, N, device="cuda")[None]]; cm = [torch.arange(Nc, device="cuda")[None]]
        try:
            ctx = vj.get_vision_features(x[:, :8])
            pred = vj.predictor(encoder_hidden_states=ctx, context_mask=cm, target_mask=tm).last_hidden_state
            assert pred.shape == full[:, Nc:].shape
            METHOD = METHOD or "context-only encoding + predictor"
        except Exception as e:
            fake = np.concatenate([fr16[:8], np.repeat(fr16[7:8], 8, 0)])
            pred = vj(pixel_values_videos=to_tensor(fake), context_mask=cm, target_mask=tm).predictor_output.last_hidden_state
            METHOD = METHOD or f"frozen-future fallback ({type(e).__name__})"
        return (pred.float() - full[:, Nc:].float()).abs().mean().item()
    rows = []
    for iid, m in sorted(ITEMS.items()):
        if "anomalous_impetus" not in m["files"]:
            continue                                   # no curving foil rendered for this item
        cor, imp = frames_of(m, "full"), frames_of(m, "anomalous_impetus")
        c = m["context_end_frame"]
        for mode in MODES:
            def clip16(fr):
                fut = fr[c + 1:c + 9]
                ctx = fr[c - 7:c + 1] if mode == "clip" else np.repeat(fr[c:c + 1], 8, 0)
                return np.concatenate([ctx, fut])
            rows.append(dict(item_id=iid, shape=m["params"]["shape"], speed=m["params"]["speed"], mode=mode,
                             surprise_correct=surprise(clip16(cor)), surprise_impetus=surprise(clip16(imp))))
    print("method:", METHOD)
    with open(f"{OUT}/vjepa.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows: print(r["item_id"], r["mode"], "prefers curving" if r["surprise_impetus"] < r["surprise_correct"] else "prefers straight")
    del vj; torch.cuda.empty_cache()''')
md("## 2 · LTX-Video, 50 steps, motion prompt")
code('''if RUN_LTX:
    from diffusers import LTXConditionPipeline
    from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
    def load_ltx(dtype):
        p = LTXConditionPipeline.from_pretrained(LTX_REPO, torch_dtype=dtype)
        p.text_encoder.to("cuda")
        with torch.no_grad():
            emb = {d: p.encode_prompt(prompt=prompt_for(d), negative_prompt=NEGATIVE, do_classifier_free_guidance=True,
                                      device="cuda", max_sequence_length=128) for d in set(DIRS.values())}
        p.text_encoder.to("cpu"); torch.cuda.empty_cache()
        p.transformer.to("cuda"); p.vae.to("cuda"); p.vae.enable_tiling()
        return p, emb
    DTYPE = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    pipe, EMB = load_ltx(DTYPE)
    def gen_ltx(m, mode, seed):
        if mode == "still":
            cond = LTXVideoCondition(image=to_model(Image.open(os.path.join(m["dir"], m["files"]["still"])).convert("RGB")), frame_index=0)
        else:
            ctx = frames_of(m, "context")[-CLIP_COND:]
            cond = LTXVideoCondition(video=[to_model(f) for f in ctx], frame_index=0)
        pe, pm, npe, npm = EMB[DIRS[m["item_id"]]]
        kw = dict(conditions=[cond], prompt_embeds=pe, prompt_attention_mask=pm, negative_prompt_embeds=npe,
                  negative_prompt_attention_mask=npm, width=W, height=H, num_frames=NUM_FRAMES,
                  num_inference_steps=LTX_STEPS, guidance_scale=3.0,
                  generator=torch.Generator("cpu").manual_seed(seed), output_type="np")
        try:
            v = pipe(frame_rate=16, **kw).frames[0]
        except TypeError:
            v = pipe(**kw).frames[0]
        return (np.clip(np.nan_to_num(v), 0, 1) * 255).astype(np.uint8)
    todo = [(m, mode, j) for m in sorted(ITEMS.values(), key=lambda m: m["item_id"]) for j in range(LTX_SAMPLES) for mode in MODES]
    for i, (m, mode, j) in enumerate(todo):
        path = f"{OUT}/ltx/{m['item_id']}__{mode}__s{j}.mp4"
        if os.path.exists(path): continue
        t0 = time.time()
        v = gen_ltx(m, mode, 1000 * j + 17 * i)
        if i == 0 and not check(v, "first LTX clip"):
            del pipe; torch.cuda.empty_cache(); DTYPE = torch.float32
            pipe, EMB = load_ltx(DTYPE); v = gen_ltx(m, mode, 0)
        imageio.mimwrite(path, v, fps=16, macro_block_size=16)
        print(f"LTX {i+1}/{len(todo)} {os.path.basename(path)} {time.time()-t0:.0f}s", flush=True)
    del pipe; torch.cuda.empty_cache()''')
md("## 3 · Wan 2.2 TI2V-5B from the still")
code('''if RUN_WAN:
    import gc; gc.collect()
    try:
        from diffusers import WanImageToVideoPipeline, AutoencoderKLWan
        vae = AutoencoderKLWan.from_pretrained(WAN_REPO, subfolder="vae", torch_dtype=torch.float32)
        wdt = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
        wan = WanImageToVideoPipeline.from_pretrained(WAN_REPO, vae=vae, torch_dtype=wdt)
        # The T5 text encoder alone is ~11 GB: encode the prompts once, then drop it, so the
        # transformer and the VAE fit on the T4 (cpu offload kept the encoder on the GPU and ran out of memory)
        wan.text_encoder.to("cuda")
        with torch.no_grad():
            WEMB = {d: wan.encode_prompt(prompt=prompt_for(d), negative_prompt=NEGATIVE, do_classifier_free_guidance=True,
                                         device="cuda") for d in set(DIRS.values())}
        wan.text_encoder.to("cpu"); wan.text_encoder = None
        gc.collect(); torch.cuda.empty_cache()
        wan.enable_model_cpu_offload()
        try: wan.vae.enable_tiling()
        except Exception: pass
        for i, m in enumerate(sorted(ITEMS.values(), key=lambda m: m["item_id"])):
            for j in range(WAN_SAMPLES):
                path = f"{OUT}/wan/{m['item_id']}__still__s{j}.mp4"
                if os.path.exists(path): continue
                t0 = time.time()
                img = to_model(Image.open(os.path.join(m["dir"], m["files"]["still"])).convert("RGB"))
                PE, NPE = WEMB[DIRS[m["item_id"]]]
                v = wan(image=img, prompt_embeds=PE, negative_prompt_embeds=NPE, height=H, width=W, num_frames=NUM_FRAMES,
                        num_inference_steps=WAN_STEPS, guidance_scale=5.0,
                        generator=torch.Generator("cpu").manual_seed(1000 * j + i), output_type="np").frames[0]
                v = (np.clip(np.nan_to_num(v), 0, 1) * 255).astype(np.uint8)
                check(v, "Wan clip")
                imageio.mimwrite(path, v, fps=16, macro_block_size=16)
                dt = time.time() - t0
                print(f"Wan {os.path.basename(path)} {dt:.0f}s", flush=True)
                if dt > WAN_MAX_S:
                    raise RuntimeError(f"too slow on this GPU ({dt:.0f} s per clip), stopping Wan")
    except Exception as e:
        import traceback; traceback.print_exc()
        print("WAN STOPPED:", type(e).__name__, e)''')
md("## 4 · Score")
code('''import subprocess
res = "/kaggle/working/results"
r = subprocess.run([sys.executable, ROOT + "/pilot/analyze_v2.py", "--inputs", ROOT + "/inputs_big",
                    "--gen", f"ltx={OUT}/ltx", "--gen", f"wan={OUT}/wan", "--cond", f"ltx_clip={CLIP_COND}",
                    "--vjepa", f"{OUT}/vjepa.csv", "--out", res], capture_output=True, text=True)
print(r.stdout, r.stderr[-3000:])
for f in [f"{OUT}/vjepa.csv", f"{res}/summary.csv", f"{res}/per_clip.csv"]:
    print("=====", f); print(open(f).read() if os.path.exists(f) else "(missing)")
!cd /kaggle/working && zip -qr slide21_pilot_results.zip results out src/inputs_big && ls -la slide21_pilot_results.zip''')

nb = dict(cells=cells, metadata=dict(kernelspec=dict(display_name="Python 3", language="python", name="python3")),
          nbformat=4, nbformat_minor=5)
runs = ", ".join(str(m in a.models.split(",")) for m in ("vjepa", "ltx", "wan"))
for c in cells:
    c["source"] = c["source"].replace("{RUNS}", runs).replace("{STYLE}", a.style)
json.dump(nb, open(os.path.join(HERE, a.out), "w"), indent=1)
print("notebook written,", len(blob) // 1024, "KB of embedded inputs")
