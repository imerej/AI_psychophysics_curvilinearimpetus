"""Shared helpers for the slide 21 big run: items, prompts, resumable outputs.
Every stage writes into /workspace/job/runs/<stage>/ and skips any output file that already exists,
so a stage that stops (crash, budget guard, pod restart) carries on where it left off when run again.
--dry (in every stage): no model is loaded; placeholder outputs are written so the whole pipeline
(paths, names, scoring) can be checked on a machine without a GPU."""
import json, math, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
# src/ is filled by orchestrate.py with the repo's own scoring code, in the same layout as experiments/:
#   src/analyze.py, src/pilot/analyze_v2.py, src/pilot/v2/vjepa2/vjepa_probe.py
sys.path.insert(0, os.path.join(HERE, "..", "..", "pilot"))   # when run from the repo (show_inputs.py)
sys.path.insert(0, os.path.join(HERE, "src", "pilot"))
import numpy as np, imageio.v2 as imageio
import analyze_v2

JOB = os.environ.get("JOB_DIR", "/workspace/job")
STIM = os.environ.get("STIM_DIR", os.path.join(JOB, "stim3d"))
RUNS = os.path.join(JOB, "runs")

# latest wording agreed in the thread: no direction, camera at ~45 degrees, solid tube, tube unchanged
PROMPT_STILL = ("A glossy red ball with an orange stripe is rolling quickly through a metal tube lying on a table, filmed by a "
                "static camera looking down at the table at about 45 degrees. The ball is exiting the tube: it rolls out of the "
                "open end of the tube and keeps rolling. The tube is solid: the ball cannot pass through its walls. Do not change "
                "the tube: it stays exactly as it is and does not move. Realistic, smooth continuous motion, static camera, the "
                "ball keeps its size, shape and colour.")
NEG = ("static, frozen, still image, ball disappears, ball shrinks, ball grows, ball fades, two balls, morphing, "
       "tube changes shape, ball passes through the tube, camera motion, zoom, cut, blurry, distorted, text, watermark, "
       "worst quality, low quality")


# ---------- what each model receives (used by the stages AND by show_inputs.py) ----------
from PIL import Image

LTX_W, LTX_H, LTX_COND = 768, 512, 33
# LTX 13B keeps the prompt of the LTX 2B run (with the exit direction), so the only change is model size
LTX_SCENE = "a curved metal tube lying on a wooden table, filmed from above by a static camera"
LTX_NEG = ("static, frozen, still image, ball disappears, ball shrinks, ball grows, ball fades, two balls, morphing, "
           "tube changes shape, camera motion, zoom, cut, blurry, distorted, text, watermark, worst quality")


def direction(m):
    """Exit direction in screen terms (right, bottom left, ...) from the true path just after the exit."""
    _, ang, _ = analyze_v2.exit_frame(m)
    d = math.degrees(ang) % 360
    return ["right", "bottom right", "bottom", "bottom left", "left", "top left", "top", "top right"][int(((d + 22.5) % 360) // 45)]


def ltx_prompt(m):
    return (f"A glossy red ball with an orange stripe rolls quickly through {LTX_SCENE}. The ball is moving towards the "
            f"{direction(m)} of the frame; it rolls out of the open end of the tube and keeps rolling across the table. "
            "Realistic, smooth continuous motion, static camera, the ball keeps its size, shape and colour.")


def ltx_frames(m):
    """The last 33 frames of the context clip (1.4 s at 24 fps), at 768x512: LTX continues from them."""
    return [Image.fromarray(f).resize((LTX_W, LTX_H)) for f in frames(m, "context")[-LTX_COND:]]


def still(m, w, h):
    """The still (last frame before the exit), resized for Wan (768x512) or Cosmos (1056x704)."""
    return Image.open(os.path.join(m["dir"], m["files"]["still"])).convert("RGB").resize((w, h))


VLM_OPTS = {"straight": "It continues in a straight line.",
            "left": "Its path bends to the left (as seen in the ball's direction of travel).",
            "right": "Its path bends to the right (as seen in the ball's direction of travel)."}
VLM_ORDERS = [["straight", "left", "right"], ["left", "right", "straight"], ["right", "straight", "left"]]
VLM_Q = ("These {n} images are frames from a video, in time order, filmed by a static camera looking down at a table at "
         "about 45 degrees. A red ball is rolling quickly through a metal tube and is about to roll out of the tube's open "
         "end. The tube is solid and the table is flat. What will the ball's path look like after it leaves the tube?\n"
         "{opts}\nAnswer with one letter only.")


def vlm_frames(m):
    """4 frames of the context clip spanning its last second (t = -1, -2/3, -1/3, 0 s), at native size."""
    fr = frames(m, "context"); c = len(fr) - 1; step = max(1, round(m["fps"] / 3))
    return [fr[c - step * k] for k in (3, 2, 1, 0)]


def vlm_question(order, n=4):
    return VLM_Q.format(n=n, opts="\n".join(f"{L}) {VLM_OPTS[k]}" for L, k in zip("ABC", order)))


def impetus_side(m):
    """'right' or 'left': the side the tube was bending at the exit, in the ball's frame (image y points down,
    so a turn towards +y while moving is a right turn; analyze_v2.exit_frame gives +1 for that case)."""
    _, _, side = analyze_v2.exit_frame(m)
    return "right" if side > 0 else "left"


def items(select="all"):
    it = analyze_v2.load_items(STIM)
    it = {k: m for k, m in it.items() if m.get("is3d")}
    if select != "all":
        it = {k: m for k, m in it.items() if any(s in k for s in select.split(","))}
    return dict(sorted(it.items()))


def frames(m, name):
    return np.stack(imageio.mimread(os.path.join(m["dir"], m["files"][name]), memtest=False))[..., :3]


def outdir(stage):
    d = os.path.join(RUNS, stage); os.makedirs(d, exist_ok=True); return d


def log(stage, msg):
    line = f"[{time.strftime('%H:%M:%S')}] {stage}: {msg}"
    print(line, flush=True)
    with open(os.path.join(outdir(stage), "progress.log"), "a") as fh:
        fh.write(line + "\n")


def done(stage, info=None):
    with open(os.path.join(outdir(stage), "DONE"), "w") as fh:
        json.dump(info or {}, fh)


def is_done(stage):
    return os.path.exists(os.path.join(RUNS, stage, "DONE"))


def save_video(path, frames_u8, fps):
    tmp = path + ".part.mp4"
    imageio.mimwrite(tmp, list(frames_u8), fps=fps, macro_block_size=16)
    os.replace(tmp, path)          # a half-written clip never counts as done


def size_for(img_w, img_h, area, mod):
    """Model resolution with the image's shape and about `area` pixels, in multiples of `mod`."""
    h = round(math.sqrt(area * img_h / img_w)) // mod * mod
    w = round(math.sqrt(area * img_w / img_h)) // mod * mod
    return w, h
