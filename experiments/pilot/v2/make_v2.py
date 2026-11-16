#!/usr/bin/env python3
"""2D source items for the model-friendly 3D render (v2). Same physics as stimgen.py, but:
  - 24 fps (video models are trained on 24-30 fps footage) and 2 s after the exit
  - bigger ball (radius 14 scene px instead of 7) and a wider tube (half width 19)
  - context / still stop on the last frame with the whole ball inside the tube
  - the straight tube gets a curving foil too (curvature 1/120 px), so it can be judged
meta.json stays in 480 x 320 scene units; render3d_v2.py renders it at 768 x 512.

  python make_v2.py --out stimuli_v2                # 5 pilot items
  python make_v2.py --out stimuli_v2 --all          # all 30 A1 items
"""
import argparse, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "..", "..", "stimgen")):
    sys.path.insert(0, p)
import stimgen as sg

sg.FPS = 24
BALL_R = 14.0
sg.Item.ball_r = BALL_R
sg.Tube.HALF_W = 19.0
POST_S = 2.0

_orig_post = sg.Tube.post


def input_frame(self):
    step = self.params["speed"] / sg.FPS
    return self.k - int(math.ceil((BALL_R + 0.5) / step))


sg.Tube.input_frame = input_frame
PILOT = [("straight", 120, 1), ("c90", 120, 1), ("c180", 120, 1), ("c270", 120, 1), ("spiral", 120, 1)]


def make(shape, v, seed):
    # stimgen keeps 25 frames after the exit; at 24 fps we want POST_S seconds, so extend pos
    item = sg.Tube(shape, v, seed)
    import numpy as np
    extra = int(POST_S * sg.FPS) - (len(item.pos) - item.k)
    if extra > 0:
        item.pos = np.concatenate([item.pos, np.full((extra, 2), np.nan)])
        td, xy = item.post(T=POST_S + 0.5)
        item.pos = item.splice(td, xy)
        for name in list(item.anomalies):
            item.anomalies[name] = np.concatenate([item.anomalies[name], np.full((extra, 2), np.nan)])
            td, xy = item.post("impetus", T=POST_S + 0.5)
            item.anomalies[name] = item.splice(td, xy)
    if shape == "straight":
        td, xy = item.post("impetus", T=POST_S + 0.5, kappa0=1 / 120.0, sign=float(item.params["turn"]))
        item.anomalies["anomalous_impetus"] = item.splice(td, xy)
    item.occluder = None
    item.options = None
    return item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="stimuli_v2")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--no-video", action="store_true", help="meta only (render3d only needs meta.json)")
    a = ap.parse_args()
    todo = ([(s, v, k) for s in ["straight", "c90", "c180", "c270", "spiral"] for v in (120, 200) for k in (1, 2, 3)]
            if a.all else PILOT)
    for shape, v, seed in todo:
        item = make(shape, v, seed)
        m = sg.process(item, a.out, videos=not a.no_video)
        print(item.id, "frames", m["n_frames"], "k", m["critical_frame"], "context ends", m["context_end_frame"])


if __name__ == "__main__":
    main()
