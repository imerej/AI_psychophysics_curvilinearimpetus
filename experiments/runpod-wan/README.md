# Wan 2.2 image-to-video on RunPod

`run_wan.py` asks the open-weight **Wan 2.2 I2V A14B** model to continue a still of the ball about to leave the spiral tube, and saves the generated clips for scoring with `../analyze.py`.

Inputs (`inputs/`):
- `spiral_real.png`: the realistic Blender render of `A1_tube_spiral_v120_s1`, last frame before the exit.
- `spiral_mirror.png`: the same scene with the spiral mirrored on the table, so that "keeps curving" means bending *up* the image (rules out a "things fall downwards" habit).

## Run it
1. On runpod.io, deploy a pod with an **A100 80GB** or **H100**, the "RunPod PyTorch" template, and a **150 GB volume** (the weights are about 70 GB).
2. Open a terminal on the pod:
   ```bash
   cd /workspace
   git clone https://github.com/imerej/AI_psychophysics_curvilinearimpetus.git
   cd AI_psychophysics_curvilinearimpetus/experiments/runpod-wan
   pip install -q -U -r requirements.txt
   python run_wan.py --test   # one 20-step clip: checks the setup and gives the time per clip
   python run_wan.py          # 3 clips per input image (3 s, 16 fps)
   ```
   The first run downloads the model into `/workspace/hf` (10 to 20 min).
3. Download `out.zip`, then **stop and terminate** the pod (a stopped pod still bills for its disk).

Expected cost: about 1 to 1.5 GPU hours, a few dollars.

## Prompt
The prompt describes the scene but never mentions a direction or a curve, so the image is the only cue:

> A glossy red ball is rolling quickly through a metal tube lying on a table, filmed by a static camera looking down at the table at about 45 degrees. The ball is exiting the tube: it rolls out of the open end of the tube and keeps rolling. The tube is solid: the ball cannot pass through its walls. Do not change the tube: it stays exactly as it is and does not move. Realistic, smooth continuous motion, static camera, the ball keeps its size, shape and colour.

A negative prompt rules out freezing, a vanishing or duplicated ball, a deforming tube and camera motion (see the script).

Status: script checked against the current diffusers API, not yet run on a GPU.
