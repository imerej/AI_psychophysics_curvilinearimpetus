"""LTX-Video 13B (0.9.7-dev) continues each tube clip from its last 33 frames: the same protocol, prompt and
seeds as the LTX 2B run on Kaggle (clip mode, 81 frames at 24 fps, 40 steps, guidance 3), so the only change is
model size.  Output: runs/ltx13b/<item>__clip__s<j>.mp4
   python stage_ltx13b.py [--seeds 3] [--items all] [--dry]"""
import argparse, os, time
import numpy as np
from PIL import Image
import common as C

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, default=3)
ap.add_argument("--items", default="all")
ap.add_argument("--steps", type=int, default=40)
ap.add_argument("--repo", default="Lightricks/LTX-Video-0.9.7-dev")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()
STAGE, W, H, COND, NF = "ltx13b", C.LTX_W, C.LTX_H, C.LTX_COND, 81
out = C.outdir(STAGE); ITEMS = C.items(a.items)

if not a.dry:
    import torch
    from diffusers import LTXConditionPipeline
    from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
    pipe = LTXConditionPipeline.from_pretrained(a.repo, torch_dtype=torch.bfloat16).to("cuda")
    pipe.vae.enable_tiling()

todo = [(iid, j) for iid in ITEMS for j in range(a.seeds)]
for n, (iid, j) in enumerate(todo):
    path = f"{out}/{iid}__clip__s{j}.mp4"
    if os.path.exists(path):
        continue
    m = ITEMS[iid]; t0 = time.time()
    ctx = C.ltx_frames(m)                                       # the last 33 context frames at 768x512
    if a.dry:          # placeholder: the conditioning frames, then the last one held
        arr = np.stack([np.asarray(f) for f in ctx]); v = np.concatenate([arr, np.repeat(arr[-1:], NF - COND, 0)])
    else:
        cond = LTXVideoCondition(video=ctx, frame_index=0)
        seed = 7919 * j + sum(map(ord, iid))                     # same seeds as the 2B run
        v = pipe(conditions=[cond], prompt=C.ltx_prompt(m), negative_prompt=C.LTX_NEG, width=W, height=H, num_frames=NF,
                 frame_rate=24, num_inference_steps=a.steps, guidance_scale=3.0,
                 generator=torch.Generator("cpu").manual_seed(seed), output_type="np").frames[0]
        v = (np.clip(np.nan_to_num(v), 0, 1) * 255).astype(np.uint8)
    C.save_video(path, v, 24)
    C.log(STAGE, f"{n + 1}/{len(todo)} {os.path.basename(path)} {time.time() - t0:.0f}s")
C.done(STAGE, dict(clips=len(todo), repo=a.repo, dry=a.dry))
