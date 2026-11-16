#!/usr/bin/env python3
"""Wan 2.2 image-to-video (A14B, open weights) on every image in inputs/, for slide 21.
Run on a RunPod pod with an 80 GB GPU (A100 80GB or H100):
    pip install -q -U diffusers transformers accelerate ftfy imageio imageio-ffmpeg sentencepiece
    python run_wan.py --test        # one short clip, to check it works and see the time per clip
    python run_wan.py               # 3 clips per image
Clips go to out/, named wan22_<image>_s<j>.mp4, plus out.zip at the end."""
import argparse, glob, os, time, zipfile
os.environ.setdefault("HF_HOME", "/workspace/hf")          # keep the ~70 GB of weights on the pod volume
import numpy as np, torch
from PIL import Image
from diffusers import WanImageToVideoPipeline
from diffusers.utils import export_to_video

PROMPT = ("A glossy red ball is rolling quickly through a metal tube lying on a table, filmed by a static camera looking "
          "down at the table at about 45 degrees. The ball is exiting the tube: it rolls out of the open end of the tube "
          "and keeps rolling. The tube is solid: the ball cannot pass through its walls. Do not change the tube: it stays "
          "exactly as it is and does not move. Realistic, smooth continuous motion, static camera, the ball keeps its "
          "size, shape and colour.")
NEG = ("static, frozen, still image, ball disappears, ball shrinks, ball grows, ball fades, two balls, morphing, "
       "tube changes shape, ball passes through the tube, camera motion, zoom, cut, blurry, distorted, text, watermark, "
       "worst quality, low quality")

ap = argparse.ArgumentParser()
ap.add_argument("--images", default="inputs")
ap.add_argument("--out", default="out")
ap.add_argument("--samples", type=int, default=3)
ap.add_argument("--frames", type=int, default=49, help="4k+1; 49 frames at 16 fps = 3 s (the ball leaves the picture by then)")
ap.add_argument("--steps", type=int, default=40)
ap.add_argument("--test", action="store_true", help="one clip of the first image, 20 steps")
ap.add_argument("--model", default="Wan-AI/Wan2.2-I2V-A14B-Diffusers")
a = ap.parse_args()

pipe = WanImageToVideoPipeline.from_pretrained(a.model, torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()      # the two 14B experts take turns on the GPU, so 80 GB is enough
mod = pipe.vae_scale_factor_spatial * pipe.transformer.config.patch_size[1]
os.makedirs(a.out, exist_ok=True)
images = sorted(glob.glob(os.path.join(a.images, "*.png")))
jobs = [(images[0], 0)] if a.test else [(p, j) for p in images for j in range(a.samples)]
print("prompt:", PROMPT)
for p, j in jobs:
    name = os.path.splitext(os.path.basename(p))[0]
    path = os.path.join(a.out, f"wan22_{name}_s{j}{'_test' if a.test else ''}.mp4")
    if os.path.exists(path):
        continue
    img = Image.open(p).convert("RGB")
    area = 480 * 832                  # Wan's 480p budget, keeping the image's 3:2 shape
    h = round(np.sqrt(area * img.height / img.width)) // mod * mod
    w = round(np.sqrt(area * img.width / img.height)) // mod * mod
    t0 = time.time()
    frames = pipe(image=img.resize((w, h)), prompt=PROMPT, negative_prompt=NEG, height=h, width=w,
                  num_frames=a.frames, num_inference_steps=20 if a.test else a.steps, guidance_scale=3.5,
                  generator=torch.Generator("cpu").manual_seed(1000 + j)).frames[0]
    export_to_video(frames, path, fps=16)
    print(f"{path}: {w}x{h}, {a.frames} frames, {time.time() - t0:.0f} s", flush=True)
with zipfile.ZipFile(a.out + ".zip", "w") as z:
    for f in sorted(glob.glob(os.path.join(a.out, "*.mp4"))):
        z.write(f)
print("done, download", a.out + ".zip")
