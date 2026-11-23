"""Wan 2.2 image-to-video A14B, 480p budget: each item's still (last frame before the exit) -> 49 frames at 16 fps.
Output: runs/wan22/<item>__still__s<j>.mp4
   python stage_wan22.py [--seeds 1] [--items all] [--dry]"""
import argparse, os, time
import numpy as np
from PIL import Image
import common as C

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, default=1)
ap.add_argument("--items", default="all")
ap.add_argument("--steps", type=int, default=40)
ap.add_argument("--frames", type=int, default=49, help="4k+1; 49 at 16 fps = 3 s")
ap.add_argument("--repo", default="Wan-AI/Wan2.2-I2V-A14B-Diffusers")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()
STAGE = "wan22"; out = C.outdir(STAGE); ITEMS = C.items(a.items)

if not a.dry:
    import torch
    from diffusers import WanImageToVideoPipeline
    pipe = WanImageToVideoPipeline.from_pretrained(a.repo, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()          # the two 14B experts take turns on the 80 GB GPU
    mod = pipe.vae_scale_factor_spatial * pipe.transformer.config.patch_size[1]
else:
    mod = 16

todo = [(iid, j) for iid in ITEMS for j in range(a.seeds)]
for n, (iid, j) in enumerate(todo):
    path = f"{out}/{iid}__still__s{j}.mp4"
    if os.path.exists(path):
        continue
    m = ITEMS[iid]; t0 = time.time()
    w, h = C.size_for(*m["size"], 480 * 832, mod)                 # 768x512 for the 768x512 stimuli
    img = C.still(m, w, h)
    if a.dry:
        v = np.repeat(np.asarray(img)[None], a.frames, 0)
    else:
        fr = pipe(image=img, prompt=C.PROMPT_STILL, negative_prompt=C.NEG, height=h, width=w,
                  num_frames=a.frames, num_inference_steps=a.steps, guidance_scale=3.5,
                  generator=torch.Generator("cpu").manual_seed(1000 + j)).frames[0]
        v = (np.clip(np.asarray(fr), 0, 1) * 255).astype(np.uint8)
    C.save_video(path, v, 16)
    C.log(STAGE, f"{n + 1}/{len(todo)} {os.path.basename(path)} {w}x{h} {time.time() - t0:.0f}s")
C.done(STAGE, dict(clips=len(todo), repo=a.repo, dry=a.dry))
