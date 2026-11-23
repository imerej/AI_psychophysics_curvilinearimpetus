"""NVIDIA Cosmos-Predict2 2B Video2World ("physical AI" world model): each item's still -> 93 frames at 16 fps.
NVIDIA's licence requires its safety checker (cosmos_guardrail) to stay on; it is left on.
Output: runs/cosmos2b/<item>__still__s<j>.mp4
   python stage_cosmos2b.py [--seeds 2] [--items all] [--dry]"""
import argparse, os, time
import numpy as np
from PIL import Image
import common as C

ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, default=2)
ap.add_argument("--items", default="all")
ap.add_argument("--steps", type=int, default=35)
ap.add_argument("--repo", default="nvidia/Cosmos-Predict2-2B-Video2World")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()
STAGE = "cosmos2b"; out = C.outdir(STAGE); ITEMS = C.items(a.items)
W, H, NF = 1056, 704, 93          # Cosmos' native 704 px height, at the stimuli's 3:2 shape

if not a.dry:
    import torch
    from diffusers import Cosmos2VideoToWorldPipeline
    pipe = Cosmos2VideoToWorldPipeline.from_pretrained(a.repo, torch_dtype=torch.bfloat16).to("cuda")

todo = [(iid, j) for iid in ITEMS for j in range(a.seeds)]
for n, (iid, j) in enumerate(todo):
    path = f"{out}/{iid}__still__s{j}.mp4"
    if os.path.exists(path):
        continue
    m = ITEMS[iid]; t0 = time.time()
    img = C.still(m, W, H)
    if a.dry:
        v = np.repeat(np.asarray(img)[None], NF, 0)
    else:
        fr = pipe(image=img, prompt=C.PROMPT_STILL, negative_prompt=C.NEG, height=H, width=W, num_frames=NF,
                  num_inference_steps=a.steps, fps=16, output_type="np",
                  generator=torch.Generator("cpu").manual_seed(2000 + j)).frames[0]
        v = (np.clip(np.asarray(fr), 0, 1) * 255).astype(np.uint8)
    C.save_video(path, v, 16)
    C.log(STAGE, f"{n + 1}/{len(todo)} {os.path.basename(path)} {time.time() - t0:.0f}s")
C.done(STAGE, dict(clips=len(todo), repo=a.repo, dry=a.dry))
