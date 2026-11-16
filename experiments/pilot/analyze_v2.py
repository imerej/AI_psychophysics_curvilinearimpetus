#!/usr/bin/env python3
"""Pilot scoring for slide 21 with a robust tracker and a quality check.

Changes from ../analyze.py (classify() and its thresholds are reused, scaled to the frame size):
  - Tracker follows the ball from its known position at the end of the input. Each frame it only
    looks near the predicted position (last position + last velocity), so a red smear elsewhere
    can no longer make the path jump across the frame.
  - Quality check: a clip is "invalid_degraded" when the generated ball is much smaller than the
    real one (median area < 40 %) or much bigger (> 250 %) or goes missing for more than a quarter of the frames while it
    should still be on screen. These are counted, not hidden.
  - Several models: --gen ltx=out/ltx --gen wan=out/wan. Clips are <item>__<mode>__s<j>.mp4.
    --cond ltx_clip=17 says how many frames at the start of a clip are the conditioning input.

  python analyze_v2.py --inputs inputs_big --gen ltx=out/ltx --gen wan=out/wan --cond ltx_clip=17 \\
                       --vjepa out/vjepa.csv --out results
"""
import argparse, csv, glob, json, math, os, sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import analyze as A  # noqa: E402

import imageio.v2 as imageio  # noqa: E402

MIN_AREA_FRAC = 0.4     # generated ball median area vs real ball, below = degraded
MAX_AREA_FRAC = 2.5     # above = degraded too (ball swells, camera zooms, or red spreads)
MAX_MISSING = 0.25      # share of on-screen frames where the ball is not found, above = degraded


def load_items(inputs):
    """2D items (meta.json from stimgen / make_big.py) and 3D items (meta3d.json from make3d.py).
    3D items get the same fields as 2D ones; positions come from full_ball_xy_px."""
    items = A.load_items(inputs)
    for p in glob.glob(os.path.join(inputs, "**", "meta3d.json"), recursive=True):
        m = json.load(open(p))
        if m.get("family") != "A1":
            continue
        _, _, shape, v, s = m["item_id"].split("_")
        d = os.path.dirname(p)
        still = imageio.imread(os.path.join(d, m["files"]["still"]))[None, ..., :3]
        r = math.sqrt(max(red_mask(still).sum(), 20) / math.pi)
        n_ctx = len(imageio.mimread(os.path.join(d, m["files"]["context"]), memtest=False))
        m["context_end_frame"] = n_ctx - 1          # trust the clip itself over the stored number
        m.update(dir=d, ball_xy=m["full_ball_xy_px"], anomalous_impetus_xy=m.get("anomalous_impetus_ball_xy_px"),
                 ball_radius=r, params=dict(shape=shape, speed=int(v[1:]), seed=int(s[1:])), is3d=True)
        items[m["item_id"]] = m
    return items


def exit_frame(m, sx=1.0):
    """Exit point, exit heading (rad, image coords) and the side the tube bent towards (+1/-1).
    2D items: heading 0 (+x) and the side from the item. 3D items (perspective camera): heading from
    the true path just after the exit, side from where the curving foil goes."""
    k = m["critical_frame"]
    xy = np.array(m["ball_xy"], float) * sx
    ex = xy[k]
    if not m.get("is3d"):
        return ex, 0.0, A.item_side(m)
    tan = xy[min(k + 3, len(xy) - 1)] - ex
    ang = math.atan2(tan[1], tan[0])
    side = 1.0
    if m.get("anomalous_impetus_xy"):
        imp = np.array(m["anomalous_impetus_xy"], float) * sx
        d = imp[min(k + 10, len(imp) - 1)] - ex
        side = float(np.sign(math.cos(ang) * d[1] - math.sin(ang) * d[0]) or 1.0)
    return ex, ang, side


def rotate(xy, origin, ang):
    c, s = math.cos(-ang), math.sin(-ang)
    d = xy - origin
    return np.stack([c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1]], axis=1) + origin


def red_mask(frames):
    f = frames.astype(np.int16)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    return (r > 140) & (r - np.maximum(g, b) > 70)


def track_from(frames, start_xy, ball_r, step):
    """Follow the ball from start_xy. Returns (T, 2) centres (NaN = not found) and (T,) areas."""
    mask = red_mask(frames)
    T, H, W = mask.shape
    yy, xx = np.mgrid[0:H, 0:W]
    out = np.full((T, 2), np.nan)
    area = np.zeros(T)
    last = np.asarray(start_xy, float)
    vel = np.zeros(2)
    lost = 0
    min_px = max(6, 0.1 * math.pi * ball_r ** 2)
    for t in range(T):
        pred = last + vel * (lost + 1)
        rad = 1.5 * ball_r + 2.5 * step * (1 + lost)
        x0, x1 = int(max(0, pred[0] - rad)), int(min(W, pred[0] + rad + 1))
        y0, y1 = int(max(0, pred[1] - rad)), int(min(H, pred[1] + rad + 1))
        if x1 <= x0 or y1 <= y0:
            lost += 1
            continue
        m = mask[t, y0:y1, x0:x1]
        near = m & (((xx[y0:y1, x0:x1] - pred[0]) ** 2 + (yy[y0:y1, x0:x1] - pred[1]) ** 2) <= rad ** 2)
        n = near.sum()
        if n < min_px:
            lost += 1
            continue
        c = np.array([xx[y0:y1, x0:x1][near].mean(), yy[y0:y1, x0:x1][near].mean()])
        out[t] = c
        area[t] = n
        new_vel = (c - last) / (lost + 1)
        vel = new_vel if t else vel
        last = c
        lost = 0
    return out, area


def score_model(items, gen_dir, model, cond, model_fps=None):
    rows = []
    for path in sorted(glob.glob(os.path.join(gen_dir, "*.mp4"))):
        try:
            item_id, mode, samp = os.path.basename(path)[:-4].split("__")
        except ValueError:
            continue
        m = items.get(item_id)
        if m is None:
            continue
        frames = np.stack(imageio.mimread(path, memtest=False))[..., :3]
        H, W = frames.shape[1:3]
        sx = W / m["size"][0]                       # in case the model changed the size
        sc = W / 480.0                              # thresholds of analyze.py are for 480 px wide
        ball_r = m["ball_radius"] * sx
        bxy = np.array(m["ball_xy"], float) * sx
        step = float(np.nanmedian(np.hypot(*np.diff(bxy, axis=0).T)))   # px per frame of the real ball
        if model_fps:                                # model output at another frame rate than the stimulus
            step *= m["fps"] / model_fps
        start = cond.get(f"{model}_{mode}", 1)
        c_end = m["context_end_frame"]
        start_xy = np.array(m["ball_xy"][c_end]) * sx
        xy, area = track_from(frames[start - 1:], start_xy, ball_r, step)
        xy, area = xy[1:], area[1:]                 # drop the last conditioning frame
        exit_xy, ang, side = exit_frame(m, sx)
        # frames where the ball should still be on screen (it has not left the picture yet)
        found = np.isfinite(xy[:, 0])
        last_found = np.max(np.nonzero(found)[0]) if found.any() else -1
        lp = xy[last_found] if last_found >= 0 else start_xy
        left_frame = lp[0] > W - 2 * ball_r or lp[0] < 2 * ball_r or lp[1] > H - 2 * ball_r or lp[1] < 2 * ball_r
        span = (last_found + 1) if left_frame else len(xy)
        missing = 1 - found[:span].mean() if span else 1.0
        area_frac = float(np.median(area[found]) / (math.pi * ball_r ** 2)) if found.any() else 0.0
        old = (A.MIN_TRAVEL, A.MIN_POINTS)
        A.MIN_TRAVEL = 30.0 * sc
        try:
            label, ang, n = A.classify(rotate(xy, exit_xy, ang), exit_xy, side)
        finally:
            A.MIN_TRAVEL, A.MIN_POINTS = old
        if not label.startswith("invalid") and (area_frac < MIN_AREA_FRAC or area_frac > MAX_AREA_FRAC or missing > MAX_MISSING):
            label = "invalid_degraded"
        rows.append(dict(model=model, item_id=item_id, shape=m["params"]["shape"], speed=m["params"]["speed"],
                         mode=mode, sample=samp, label=label, bend_deg=round(ang, 2), n_points=n,
                         area_frac=round(area_frac, 2), missing=round(float(missing), 2),
                         path=json.dumps([[round(a, 1), round(b, 1)] if np.isfinite(a) else None for a, b in xy])))
    return rows


def summarise(gen, vj):
    out = []
    by = defaultdict(list)
    for r in gen:
        by[(r["model"], r["shape"], r["mode"])].append(r["label"])
    for (model, shape, mode), labs in sorted(by.items()):
        valid = [l for l in labs if not l.startswith("invalid")]
        n = len(valid)
        pct = lambda k: round(100 * sum(l == k for l in valid) / n, 1) if n else ""
        out.append(dict(model=model, readout="generate", shape=shape, mode=mode, n_total=len(labs), n_valid=n,
                        pct_curving=pct("impetus"), pct_no_bias=pct("no_bias"), pct_centrifugal=pct("centrifugal"),
                        n_degraded=sum(l == "invalid_degraded" for l in labs),
                        n_stopped=sum(l == "invalid_stopped" for l in labs),
                        n_lost=sum(l == "invalid_lost" for l in labs)))
    byv = defaultdict(list)
    for r in vj:
        byv[(r["shape"], r["mode"])].append(float(r["surprise_impetus"]) < float(r["surprise_correct"]))
    for (shape, mode), v in sorted(byv.items()):
        out.append(dict(model="vjepa", readout="judge", shape=shape, mode=mode, n_total=len(v), n_valid=len(v),
                        pct_curving=round(100 * sum(v) / len(v), 1), pct_no_bias="", pct_centrifugal="",
                        n_degraded="", n_stopped="", n_lost=""))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", default="inputs_big")
    ap.add_argument("--gen", action="append", default=[], help="model=folder")
    ap.add_argument("--cond", action="append", default=[], help="model_mode=frames, e.g. ltx_clip=17")
    ap.add_argument("--fps", action="append", default=[], help="model=fps when a model outputs another frame rate")
    ap.add_argument("--vjepa", default="out/vjepa.csv")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    items = load_items(a.inputs)
    cond = {k: int(v) for k, v in (c.split("=") for c in a.cond)}
    gen = []
    for g in a.gen:
        model, folder = g.split("=", 1)
        if os.path.isdir(folder):
            fps = dict(f.split("=") for f in a.fps)
            gen += score_model(items, folder, model, cond, float(fps[model]) if model in fps else None)
    vj = list(csv.DictReader(open(a.vjepa))) if os.path.exists(a.vjepa) else []
    A.write_csv(gen, os.path.join(a.out, "per_clip.csv"))
    summ = summarise(gen, vj)
    A.write_csv(summ, os.path.join(a.out, "summary.csv"))
    for r in summ:
        print(f"{r['model']:6s} {r['mode']:5s} {r['shape']:8s} curving {str(r['pct_curving']):>5}%  "
              f"valid {r['n_valid']}/{r['n_total']}  degraded {r['n_degraded']} stopped {r['n_stopped']} lost {r['n_lost']}")


if __name__ == "__main__":
    main()
