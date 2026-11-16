#!/usr/bin/env python3
"""Big-ball version of the A1 tube items for the video models (pilot).

Same physics and timing as stimgen.py; only the look changes:
  - 768 x 512 output (stimgen geometry scaled by 1.6)
  - ball radius 12 scene px -> about 38 px across on screen (was 14), so it covers
    more than one 32 x 32 latent cell of LTX-Video / 16 x 16 of Wan
  - wider tube walls, soft shadow and a highlight on the ball
  - context/still stop on the last frame with the whole (bigger) ball inside the tube
meta.json coordinates are in output pixels (already scaled).

  python make_big.py --out inputs_big                 # 5 pilot items
  python make_big.py --out inputs_big --all           # all 30 A1 items
"""
import argparse, json, math, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "stimgen"))
import numpy as np
from PIL import Image
import stimgen as sg

OUT_W, OUT_H = 768, 512
SCALE = OUT_W / sg.W
BALL_R = 12.0
SHADOW = (205, 205, 205)
HILITE = (255, 120, 120)

sg.SS = 5
sg.Item.ball_r = BALL_R
sg.Tube.HALF_W = 17.0


def frame(self):
    return np.asarray(self.img.resize((OUT_W, OUT_H), Image.LANCZOS))


def render(self, pos=None, frames=None, occluded=False):
    pos = self.pos if pos is None else pos
    frames = range(len(pos)) if frames is None else frames
    out = []
    for f in frames:
        cv = sg.Canvas()
        self.draw_scene(cv, f, pos)
        p = pos[f]
        if np.all(np.isfinite(p)):
            cv.circle(p + np.array([2.5, 3.0]), self.ball_r, SHADOW)
            cv.circle(p, self.ball_r, sg.BALL)
            cv.circle(p - np.array([3.5, 3.5]), self.ball_r * 0.3, HILITE)
        out.append(cv.frame())
    return out


def draw_scene(self, cv, f, pos):
    w1, w2 = self._walls()
    cv.line(w1, fill=sg.WALL, width=3.5)
    cv.line(w2, fill=sg.WALL, width=3.5)


def input_frame(self):
    # last frame with the whole ball (radius BALL_R) still inside the tube
    step = self.params["speed"] / sg.FPS
    return self.k - int(math.ceil((BALL_R + 0.5) / step))


sg.Canvas.frame = frame
sg.Item.render = render
sg.Tube.draw_scene = draw_scene
sg.Tube.input_frame = input_frame

PILOT = [("straight", 120, 1), ("c90", 120, 1), ("c180", 120, 1), ("c270", 120, 1), ("spiral", 120, 1)]


def scale(v):
    return (np.asarray(v, float) * SCALE).round(2).tolist()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="inputs_big")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    todo = ([(s, v, k) for s in ["straight", "c90", "c180", "c270", "spiral"] for v in (120, 200) for k in (1, 2, 3)]
            if a.all else PILOT)
    for shape, v, seed in todo:
        item = sg.Tube(shape, v, seed)
        if shape == "straight":       # curving foil for the straight tube too (curvature 1/120 px, as in slide21-test)
            td, xy = item.post("impetus", kappa0=1 / 120.0, sign=float(item.params["turn"]))
            item.anomalies["anomalous_impetus"] = item.splice(td, xy)
        item.occluder = None          # model inputs only: no occluder or options task
        item.options = None
        meta = sg.process(item, a.out)
        d = os.path.join(a.out, item.family, item.id)
        for f in ("occluded.mp4", "occluded_last.png", "options.png"):
            if os.path.exists(os.path.join(d, f)):
                os.remove(os.path.join(d, f))
        meta["size"] = [OUT_W, OUT_H]
        meta["ball_radius"] = round(BALL_R * SCALE, 2)
        meta["scale_from_2d"] = SCALE
        meta["ball_xy"] = scale(meta["ball_xy"])
        for k in list(meta):
            if k.endswith("_xy") and k != "ball_xy":
                meta[k] = scale(meta[k])
        meta["scene"]["centerline"] = scale(meta["scene"]["centerline"])
        meta["scene"]["half_width"] = round(meta["scene"]["half_width"] * SCALE, 2)
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"))
        print(item.id, "k", meta["critical_frame"], "ctx_end", meta["context_end_frame"])


if __name__ == "__main__":
    main()
