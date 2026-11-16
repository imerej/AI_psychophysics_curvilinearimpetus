import json, os
cells = []
def md(s): cells.append(dict(cell_type="markdown", metadata={}, source=s.strip("\n")))
def code(s): cells.append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=s.strip("\n")))

md(r"""
# Slide 21 test: do models keep curving after a tube?

Runs on a free Kaggle GPU (Settings → Accelerator → **GPU T4 x2**, Internet **on**).
Add the dataset `slide21-test` (the folder with `inputs/` and `analyze.py`) with **Add Input**.

1. **V-JEPA 2** (world model, judge): surprise on the correct vs the curving continuation of all 30 tube items, from a still or from a clip. A few minutes.
2. **LTX-Video 0.9.5, 2B** (video generator): continues each item from the still or from the last 9 frames of the clip. Every input stops one frame before the ball reaches the tube mouth, so nothing after the exit is shown. `SAMPLES` per item and mode (2 by default: 120 clips).
3. Scores everything with `analyze.py` and draws the slide-21 plot.

Everything is saved to `/kaggle/working/out` as it goes, so a rerun skips what is done. Download `/kaggle/working/slide21_results.zip` at the end.
""")
code(r"""
!pip install -q -U "diffusers>=0.33" "transformers>=4.53" accelerate sentencepiece imageio imageio-ffmpeg matplotlib
""")
code(r"""
# ---- settings
RUN_VJEPA = True
RUN_LTX = True
SAMPLES = 2                     # LTX samples per item and mode (the plan says 4; 2 is enough for today)
SHAPES = ["straight", "c90", "c180", "c270", "spiral"]
SPEEDS = [120, 200]
MODES = ["still", "clip"]
LTX_REPO = "Lightricks/LTX-Video-0.9.5"     # 2B model; fits a T4
VJEPA_REPO = "facebook/vjepa2-vitl-fpc64-256"
NUM_FRAMES = 33                 # 2 s at 16 fps (LTX needs 8k+1 frames)
STEPS = 30
PROMPT = ("A small red ball moving on a plain light grey background, seen from directly above. "
          "Simple flat 2D animation, static camera, grey tube outline.")
NEGATIVE = "worst quality, blurry, jittery, distorted, camera motion, text, watermark"

import glob, json, os, sys, time, csv, math
import numpy as np, torch, imageio.v2 as imageio
from PIL import Image

src = sorted(glob.glob("/kaggle/input/**/analyze.py", recursive=True))
assert src, "Add the slide21-test dataset (Add Input) first"
ROOT = os.path.dirname(src[0]); sys.path.insert(0, ROOT)
import analyze
ITEMS = analyze.load_items(ROOT)
ITEMS = {k: m for k, m in ITEMS.items() if m["params"]["shape"] in SHAPES and m["params"]["speed"] in SPEEDS}
OUT = "/kaggle/working/out"; os.makedirs(f"{OUT}/ltx", exist_ok=True)
print(len(ITEMS), "items;", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NO GPU")

def frames_of(m, name):
    return np.stack(imageio.mimread(os.path.join(m["dir"], m["files"][name]), memtest=False))[..., :3]
""")
md("## 1 · V-JEPA 2: is the curving continuation less surprising?")
code(r"""
if RUN_VJEPA:
    from transformers import AutoModel, AutoVideoProcessor
    vj = AutoModel.from_pretrained(VJEPA_REPO, torch_dtype=torch.float16).cuda().eval()
    proc = AutoVideoProcessor.from_pretrained(VJEPA_REPO)
    BG = 242

    def square(fr):                       # pad 480x320 to 480x480 with the background grey
        T, H, W, _ = fr.shape
        out = np.full((T, W, W, 3), BG, np.uint8); y0 = (W - H) // 2
        out[:, y0:y0 + H] = fr
        return out

    def to_tensor(fr):
        x = proc(videos=square(fr), return_tensors="pt")["pixel_values_videos"]
        return x.to("cuda", torch.float16)

    METHOD = None
    @torch.no_grad()
    def surprise(fr16):
        # 16 frames: 8 context (ending 1 frame before the exit, ball still in the tube) + 8 future. Encode the context alone, let the
        # predictor fill in the future tokens, compare with the encoding of the real future.
        global METHOD
        x = to_tensor(fr16)
        full = vj.get_vision_features(x)                  # (1, N, D)
        N = full.shape[1]; Nc = N // 2
        tm = [torch.arange(Nc, N, device="cuda")[None]]
        cm = [torch.arange(Nc, device="cuda")[None]]
        try:
            ctx = vj.get_vision_features(x[:, :8])        # (1, Nc, D), no access to the future
            pred = vj.predictor(encoder_hidden_states=ctx, context_mask=cm, target_mask=tm).last_hidden_state
            assert pred.shape == full[:, Nc:].shape, (pred.shape, full.shape)
            METHOD = METHOD or "context-only encoding + predictor"
        except Exception as e:                            # fallback: hide the future by freezing the last context frame
            fake = np.concatenate([fr16[:8], np.repeat(fr16[7:8], 8, 0)])
            o = vj(pixel_values_videos=to_tensor(fake), context_mask=cm, target_mask=tm)
            pred = o.predictor_output.last_hidden_state
            METHOD = METHOD or f"frozen-future fallback ({type(e).__name__}: {e})"
        return (pred.float() - full[:, Nc:].float()).abs().mean().item()

    rows = []
    for iid, m in sorted(ITEMS.items()):
        k = m["critical_frame"]
        cor, imp = frames_of(m, "full"), frames_of(m, "anomalous_impetus")
        for mode in MODES:
            def clip16(fr):
                c = m["context_end_frame"]                     # last input frame = k - 1
                fut = fr[c + 1:c + 9]
                ctx = fr[c - 7:c + 1] if mode == "clip" else np.repeat(fr[c:c + 1], 8, 0)
                return np.concatenate([ctx, fut])
            sc, si = surprise(clip16(cor)), surprise(clip16(imp))
            rows.append(dict(item_id=iid, shape=m["params"]["shape"], speed=m["params"]["speed"], mode=mode,
                             surprise_correct=sc, surprise_impetus=si))
    print("method:", METHOD)
    with open(f"{OUT}/vjepa.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for mode in MODES:
        for s in SHAPES:
            v = [r["surprise_impetus"] < r["surprise_correct"] for r in rows if r["mode"] == mode and r["shape"] == s]
            print(f"V-JEPA {mode:5s} {s:8s} curving judged more natural in {100*np.mean(v):5.1f}% of {len(v)} items")
    del vj; torch.cuda.empty_cache()
""")
md("## 2 · LTX-Video: generate the continuation")
code(r"""
if RUN_LTX:
    from diffusers import LTXConditionPipeline
    from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition

    def load(dtype):
        p = LTXConditionPipeline.from_pretrained(LTX_REPO, torch_dtype=dtype)
        # encode the prompt once, then drop the big T5 text encoder so the rest fits the T4
        p.text_encoder.to("cuda")
        with torch.no_grad():
            emb = p.encode_prompt(prompt=PROMPT, negative_prompt=NEGATIVE, do_classifier_free_guidance=True,
                                  device="cuda", max_sequence_length=128)
        p.text_encoder.to("cpu"); torch.cuda.empty_cache()   # stays on the CPU, unused from here
        p.transformer.to("cuda"); p.vae.to("cuda"); p.vae.enable_tiling()
        return p, emb

    DTYPE = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16   # T4/P100: fp16
    pipe, EMB = load(DTYPE)

    def generate(m, mode, seed):
        k = m["critical_frame"]
        if mode == "still":
            cond = LTXVideoCondition(image=Image.open(os.path.join(m["dir"], m["files"]["still"])).convert("RGB"), frame_index=0)
        else:
            ctx = frames_of(m, "context")[-analyze.CLIP_COND_FRAMES:]      # last 9 frames, ends 1 frame before the exit
            cond = LTXVideoCondition(video=[Image.fromarray(f) for f in ctx], frame_index=0)
        pe, pm, npe, npm = EMB
        kw = dict(conditions=[cond], prompt_embeds=pe, prompt_attention_mask=pm,
                  negative_prompt_embeds=npe, negative_prompt_attention_mask=npm,
                  width=480, height=320, num_frames=NUM_FRAMES, num_inference_steps=STEPS,
                  guidance_scale=3.0, generator=torch.Generator("cpu").manual_seed(seed), output_type="np")
        try:
            v = pipe(frame_rate=16, **kw).frames[0]
        except TypeError:
            v = pipe(**kw).frames[0]
        return (np.clip(np.nan_to_num(v), 0, 1) * 255).astype(np.uint8)

    # first clip doubles as a check that half precision works on this GPU
    first = next(iter(sorted(ITEMS.values(), key=lambda m: m["item_id"])))
    t0 = time.time(); test = generate(first, "still", 0); dt = time.time() - t0
    if test.std() < 2:                                  # blank output: half precision overflowed
        print("blank output in", DTYPE, "- reloading in float32 (slower)")
        del pipe; torch.cuda.empty_cache(); DTYPE = torch.float32
        pipe, EMB = load(DTYPE); t0 = time.time(); test = generate(first, "still", 0); dt = time.time() - t0
    print(f"{DTYPE}: {dt:.0f} s per clip; {len(ITEMS)*len(MODES)*SAMPLES} clips to make")
    Image.fromarray(np.concatenate([test[0], test[len(test)//2], test[-1]], 1)).save(f"{OUT}/check_first_clip.png")
    display(Image.open(f"{OUT}/check_first_clip.png"))
""")
code(r"""
if RUN_LTX:
    todo = [(m, mode, j) for m in sorted(ITEMS.values(), key=lambda m: (m["params"]["speed"], m["item_id"]))
            for j in range(SAMPLES) for mode in MODES]
    for i, (m, mode, j) in enumerate(todo, 1):
        path = f"{OUT}/ltx/{m['item_id']}__{mode}__s{j}.mp4"
        if os.path.exists(path):
            continue
        seed = 1000 * j + int.from_bytes(m["item_id"].encode(), "little") % 997
        v = generate(m, mode, seed)
        imageio.mimwrite(path, v, fps=16, macro_block_size=16)
        if i % 10 == 0:
            print(f"{i}/{len(todo)}", time.strftime("%H:%M:%S"))
    print("done")
""")
md("## 3 · Score and plot")
code(r"""
import subprocess
res = "/kaggle/working/results"
print(subprocess.run([sys.executable, os.path.join(ROOT, "analyze.py"), "--inputs", ROOT, "--gen", f"{OUT}/ltx",
                      "--vjepa", f"{OUT}/vjepa.csv", "--out", res], capture_output=True, text=True).stdout)
if os.path.exists(f"{res}/slide21_humans_vs_ai.png"):
    display(Image.open(f"{res}/slide21_humans_vs_ai.png"))
!cd /kaggle/working && zip -qr slide21_results.zip results out/vjepa.csv out/check_first_clip.png out/ltx && ls -la slide21_results.zip
""")
nb = dict(nbformat=4, nbformat_minor=5, cells=cells,
          metadata=dict(kernelspec=dict(name="python3", display_name="Python 3", language="python"),
                        language_info=dict(name="python"), kaggle=dict(accelerator="nvidiaTeslaT4", isInternetEnabled=True)))
json.dump(nb, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slide21_kaggle.ipynb"), "w"), indent=1)
