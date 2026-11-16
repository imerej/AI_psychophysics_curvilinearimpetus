#!/usr/bin/env python3
"""Score the slide-21 test: does the model keep curving after the ball leaves the tube?

Two readouts, both per tube shape and input mode (still vs clip):

  generate  (LTX-Video): track the red ball in each generated clip, measure how much the
            path bends after the exit, and class it as impetus (bends the way the tube
            bent), no bias (straight), centrifugal (bends the other way), or invalid
            (ball lost or not moving). y = % impetus among valid clips.
  judge     (V-JEPA 2): for each item, compare the model's surprise on the correct
            (straight) continuation and on the impetus (curving) one.
            y = % of items where the curving continuation is LESS surprising.

Usage:
  python analyze.py --inputs inputs --gen out/ltx --vjepa out/vjepa.csv --humans human/data --out results

Human data (human/experiment.html, one CSV per person) is scored with the same rules:
drawn paths go through classify() exactly like tracked model paths, and a "which looks
natural" choice of the curving version counts like V-JEPA preferring it.
Only needs numpy, imageio (+ imageio-ffmpeg); matplotlib for the plot (optional).
"""

import argparse
import csv
import glob
import json
import math
import os
from collections import defaultdict

import numpy as np

try:
    import imageio.v2 as imageio
except ImportError:  # pragma: no cover
    imageio = None

SHAPES = ["straight", "c90", "c180", "c270", "spiral"]
SHAPE_LABEL = {"straight": "straight", "c90": "90°", "c180": "180°", "c270": "270°", "spiral": "spiral"}
CLIP_COND_FRAMES = 9      # clip mode: frames 0..8 of a generated clip are the conditioning (ends 1 frame before the exit)
BEND_DEG = 5.0            # |heading change| above this = the path bends (set before looking at data)
MIN_POINTS = 4            # tracked frames after the exit needed for a valid clip
MIN_TRAVEL = 30.0         # px the ball must move forward after the exit for a valid clip

# human reference points on slide 21 (x index on the shape axis, % curving)
HUMANS = [
    dict(label="humans, drawn from a still (McCloskey et al. 1980)", x=2.5, y=33, marker="D", color="#D98A4E"),
    dict(label=None, x=4, y=51, marker="D", color="#D98A4E"),
    dict(label="humans, 1 of 6 after a still (McCloskey & Kohl 1983)", x=3.92, y=25, marker="s", color="#D98A4E"),
    dict(label="humans, 1 of 6 after watching (McCloskey & Kohl 1983)", x=4.08, y=28, marker="s", color="#2E5A87"),
]


def load_items(inputs):
    items = {}
    for p in glob.glob(os.path.join(inputs, "**", "meta.json"), recursive=True):
        m = json.load(open(p))
        if m.get("family") == "A1":
            m["dir"] = os.path.dirname(p)
            items[m["item_id"]] = m
    return items


def track(frames):
    """Centre of the red ball in each frame (NaN when not found). frames: (T, H, W, 3) uint8."""
    f = frames.astype(np.int16)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    mask = (r > 140) & (r - np.maximum(g, b) > 70)
    out = np.full((len(frames), 2), np.nan)
    for i, m in enumerate(mask):
        ys, xs = np.nonzero(m)
        if len(xs) >= 6:
            # keep the largest blob roughly: pixels near the median
            mx, my = np.median(xs), np.median(ys)
            keep = (np.abs(xs - mx) < 20) & (np.abs(ys - my) < 20)
            if keep.sum() >= 6:
                out[i] = xs[keep].mean(), ys[keep].mean()
    return out


def classify(points, exit_xy, side):
    """Class one path after the exit.

    points: (N, 2) ball centres after the exit, in time order (NaNs allowed).
    exit_xy: the ball at the exit; the exit tangent is +x in every A1 item.
    side: +1 / -1, the image-y direction the tube was bending at the exit
          (for the straight tube: the item's turn side, so either bend counts as curving).
    Returns (label, heading_change_deg towards the tube side, n_points).
    """
    p = points[np.all(np.isfinite(points), axis=1)]
    if len(p) < MIN_POINTS:
        return "invalid_lost", float("nan"), len(p)
    d = p - np.asarray(exit_xy)
    d = d[d[:, 0] >= 0]                     # only the part after the tube mouth (inputs stop inside the tube)
    if len(d) < MIN_POINTS:
        return "invalid_lost", float("nan"), len(d)
    fwd = d[:, 0]
    if fwd.max() < MIN_TRAVEL:
        return "invalid_stopped", float("nan"), len(p)
    # heading of the late part of the path relative to the exit tangent (+x)
    far = d[fwd >= 0.5 * fwd.max()]
    vec = far[-1] - d[0] if len(far) else d[-1] - d[0]
    ang = math.degrees(math.atan2(vec[1] * side, vec[0]))
    if ang > BEND_DEG:
        return "impetus", ang, len(p)
    if ang < -BEND_DEG:
        return "centrifugal", ang, len(p)
    return "no_bias", ang, len(p)


def item_side(m):
    k = m["params"].get("exit_curvature", 0.0)
    return float(np.sign(k)) if abs(k) > 1e-9 else float(m["params"].get("turn", 1))


def score_generated(items, gen_dir):
    """Generated clips are named <item_id>__<mode>__s<j>.mp4 (mode = still or clip)."""
    rows = []
    for path in sorted(glob.glob(os.path.join(gen_dir, "*.mp4"))):
        name = os.path.basename(path)[:-4]
        try:
            item_id, mode, samp = name.split("__")
        except ValueError:
            continue
        m = items.get(item_id)
        if m is None:
            continue
        frames = np.stack(imageio.mimread(path, memtest=False))[..., :3]
        xy = track(frames)
        start = 1 if mode == "still" else CLIP_COND_FRAMES
        exit_xy = np.array(m["ball_xy"][m["critical_frame"]])
        label, ang, n = classify(xy[start:], exit_xy, item_side(m))
        rows.append(dict(item_id=item_id, shape=m["params"]["shape"], speed=m["params"]["speed"],
                         mode=mode, sample=samp, label=label, bend_deg=round(ang, 2), n_points=n))
    return rows


def score_humans(items, folder):
    draw, judge = [], []
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        for r in csv.DictReader(open(path, newline="")):
            m = items.get(r["item_id"])
            if m is None:
                continue
            base = dict(participant=r["participant"], physics=r["physics"], item_id=r["item_id"],
                        shape=r["shape"], speed=int(r["speed"]), mode=r["mode"])
            if r["task"] == "draw":
                pts = np.array(json.loads(r["drawn_xy"]), float).reshape(-1, 2)
                exit_xy = np.array(m["ball_xy"][m["critical_frame"]])
                label, ang, n = classify(pts, exit_xy, item_side(m))
                draw.append(dict(base, label=label, bend_deg=round(ang, 2), n_points=n))
            elif r["task"] == "judge":
                judge.append(dict(base, chose_curving=int(r["chose_curving"])))
    return draw, judge


def summarise(gen_rows, vjepa_rows, hdraw=(), hjudge=()):
    out = []
    for model, rows_ in (("Humans (ours)", hdraw),):
        byh = defaultdict(list)
        for r in rows_:
            byh[(r["shape"], r["mode"])].append(r["label"])
        for (shape, mode), labs in sorted(byh.items()):
            valid = [l for l in labs if not l.startswith("invalid")]
            n = len(valid)
            pct = lambda k: round(100 * sum(l == k for l in valid) / n, 1) if n else float("nan")
            out.append(dict(model=model, readout="draw", shape=shape, mode=mode, n_total=len(labs), n_valid=n,
                            pct_curving=pct("impetus"), pct_no_bias=pct("no_bias"), pct_centrifugal=pct("centrifugal"),
                            pct_invalid=round(100 * (len(labs) - n) / len(labs), 1)))
    byj = defaultdict(list)
    for r in hjudge:
        byj[(r["shape"], r["mode"])].append(r["chose_curving"])
    for (shape, mode), v in sorted(byj.items()):
        out.append(dict(model="Humans (ours)", readout="judge", shape=shape, mode=mode, n_total=len(v), n_valid=len(v),
                        pct_curving=round(100 * sum(v) / len(v), 1), pct_no_bias="", pct_centrifugal="", pct_invalid=0))
    by = defaultdict(list)
    for r in gen_rows:
        by[(r["shape"], r["mode"])].append(r["label"])
    for (shape, mode), labs in sorted(by.items()):
        valid = [l for l in labs if not l.startswith("invalid")]
        n = len(valid)
        pct = lambda k: round(100 * sum(l == k for l in valid) / n, 1) if n else float("nan")
        out.append(dict(model="LTX-Video", readout="generate", shape=shape, mode=mode, n_total=len(labs),
                        n_valid=n, pct_curving=pct("impetus"), pct_no_bias=pct("no_bias"),
                        pct_centrifugal=pct("centrifugal"), pct_invalid=round(100 * (len(labs) - n) / len(labs), 1)))
    byv = defaultdict(list)
    for r in vjepa_rows:
        byv[(r["shape"], r["mode"])].append(float(r["surprise_impetus"]) < float(r["surprise_correct"]))
    for (shape, mode), v in sorted(byv.items()):
        out.append(dict(model="V-JEPA 2", readout="judge", shape=shape, mode=mode, n_total=len(v), n_valid=len(v),
                        pct_curving=round(100 * sum(v) / len(v), 1), pct_no_bias="", pct_centrifugal="", pct_invalid=0))
    return out


def plot(summary, path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed: skipping the plot")
        return
    fig, ax = plt.subplots(figsize=(10, 5.5))
    styles = {("LTX-Video", "still"): ("#D98A4E", "-", "o"), ("LTX-Video", "clip"): ("#2E5A87", "-", "o"),
              ("V-JEPA 2", "still"): ("#D98A4E", "--", "^"), ("V-JEPA 2", "clip"): ("#2E5A87", "--", "^"),
              ("Humans (ours)/draw", "still"): ("#A64A14", "-", "s"), ("Humans (ours)/draw", "clip"): ("#1C3A5C", "-", "s"),
              ("Humans (ours)/judge", "still"): ("#A64A14", ":", "v"), ("Humans (ours)/judge", "clip"): ("#1C3A5C", ":", "v")}
    what = {"LTX-Video": "generated paths", "V-JEPA 2": "curving judged more natural",
            "Humans (ours)/draw": "drawn paths", "Humans (ours)/judge": "curving chosen as natural"}
    for (model, mode), (c, ls, mk) in styles.items():
        name, _, readout = model.partition("/")
        pts = [(SHAPES.index(r["shape"]), r["pct_curving"]) for r in summary
               if r["model"] == name and (not readout or r["readout"] == readout)
               and r["mode"] == mode and r["shape"] in SHAPES]
        if pts:
            pts.sort()
            ax.plot(*zip(*pts), color=c, ls=ls, marker=mk, ms=8, lw=2.5,
                    label=f"{name} after a {'still' if mode == 'still' else 'clip'} ({what[model]})")
    for h in HUMANS:
        ax.scatter(h["x"], h["y"], marker=h["marker"], s=110, color=h["color"], edgecolor="#1C2430",
                   zorder=5, label=h["label"])
    ax.axhline(0, color="#1C2430", lw=1, ls=":")
    ax.set_xticks(range(5), [SHAPE_LABEL[s] for s in SHAPES])
    ax.set_xlabel("tube curvature at the exit")
    ax.set_ylabel("% of paths that keep curving")
    ax.set_ylim(-3, 100)
    ax.legend(fontsize=8, loc="upper left", frameon=False)
    ax.set_title("Slide 21 · humans vs AI · curved tube (A1)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print("plot:", path)


def write_csv(rows, path):
    if not rows:
        return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", default="inputs", help="folder with the A1 items (meta.json files)")
    ap.add_argument("--gen", default="out/ltx", help="folder of generated clips")
    ap.add_argument("--vjepa", default="out/vjepa.csv", help="V-JEPA surprise table")
    ap.add_argument("--humans", default="human/data", help="folder of CSV files from human/experiment.html")
    ap.add_argument("--out", default="results", help="output folder")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    items = load_items(a.inputs)
    gen = score_generated(items, a.gen) if os.path.isdir(a.gen) else []
    vj = list(csv.DictReader(open(a.vjepa))) if os.path.exists(a.vjepa) else []
    hdraw, hjudge = score_humans(items, a.humans) if os.path.isdir(a.humans) else ([], [])
    write_csv(gen, os.path.join(a.out, "ltx_per_clip.csv"))
    write_csv(hdraw, os.path.join(a.out, "humans_draw_per_trial.csv"))
    summ = summarise(gen, vj, hdraw, hjudge)
    write_csv(summ, os.path.join(a.out, "summary.csv"))
    for r in summ:
        print(f"{r['model']:13s} {r['readout']:8s} {r['mode']:5s} {r['shape']:8s} curving {r['pct_curving']:>5}%  "
              f"(valid {r['n_valid']}/{r['n_total']})")
    plot(summ, os.path.join(a.out, "slide21_humans_vs_ai.png"))


if __name__ == "__main__":
    main()
