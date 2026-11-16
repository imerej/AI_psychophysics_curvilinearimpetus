#!/usr/bin/env python3
"""Build experiment.html: McCloskey & Kohl (1983) Experiment 2, rebuilt with our A1 spiral tube.

Their procedure (JEP:LMC 9:146-156, pp. 149-151), kept as is:
  - one spiral-tube problem, one answer per person
  - two between-subject conditions: "no motion" (diagram + description, then choose) and
    "trajectories" (each of the six alternatives animated twice, then choose)
  - six alternatives: A correct, B-D curvilinear impetus, E-F other (Fig. 3)
  - answer = pick one of six cards (tube + path), laid out in a new random order per person
  - tube centred in a square field 15 cm wide, spiral 5.5 cm at its widest, ball moving at
    constant speed through the tube and on along the path to the edge of the field, then a
    static picture of tube + path

From our A1 family (stimgen.py, item A1_tube_spiral_v200_s1), kept as is so the models and the
people see the same tube: spiral shape (1.1 turns), wall width, ball size, speed 200 px/s,
exit tangent and turning direction. The six paths are drawn after their Fig. 3 (heading change
after the exit: B 50 deg, C 140 deg towards the tube's turn, D keeps following the spiral for
another 0.6 turn outside the tube and then goes straight; E bends outward 35 deg; F an
outward-then-back S). They are approximations of the figure, which gives no numbers.

  python build_mk_experiment.py          # writes experiment.html next to this script
"""

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "stimgen"))
import stimgen as sg  # noqa: E402

ITEM = ("spiral", 200, 1)        # shape, speed px/s, seed
FPS = 48                         # display rate (theirs: 50 frames/s)
SPIRAL_CM, FIELD_CM = 5.5, 15.0  # their spiral width and display field
HEADINGS = dict(B=50, C=140, E=-35)   # deg, + = towards the tube's turn
D_EXTRA_TURNS = 0.6


def path_after_exit(p0, v, side, kappa_t, T=6.0, dt=1.0 / 960):
    """Constant-speed path whose curvature over time is kappa_t(t) (+ = tube side)."""
    n = int(T / dt)
    xy = np.zeros((n, 2))
    p = np.array(p0, float)
    th = 0.0                                  # exit tangent is +x for every A1 item
    for i in range(n):
        xy[i] = p
        th += side * kappa_t(i * dt) * v * dt
        p = p + v * dt * np.array([math.cos(th), math.sin(th)])
    return xy


def spiral_extension(it, extra_turns):
    """The tube's own spiral (stimgen Tube._centerline) continued past the exit."""
    L = it.TUBE_LEN
    phi0 = np.linspace(0, 2.25 * math.pi, 600)
    raw0 = np.stack([(12 + 9 * phi0) * np.cos(phi0), (12 + 9 * phi0) * np.sin(phi0)], 1)
    scale = L / np.hypot(*np.diff(raw0, axis=0).T).sum()
    phi = np.linspace(2.25 * math.pi, (2.25 + 2 * extra_turns) * math.pi, 400)
    raw = np.stack([(12 + 9 * phi) * np.cos(phi), (12 + 9 * phi) * np.sin(phi)], 1)
    turn = it.params["turn"]
    c0 = raw0 * scale * np.array([1, turn])
    ce = raw * scale * np.array([1, turn])
    tan = c0[-1] - c0[-4]
    ang = math.atan2(tan[1], tan[0])
    R = np.array([[math.cos(-ang), -math.sin(-ang)], [math.sin(-ang), math.cos(-ang)]])
    ce = (ce - c0[-1]) @ R.T + it.c[-1]
    return ce


def main():
    shape, v, seed = ITEM
    it = sg.Tube(shape, v, seed)
    side = float(np.sign(it.params["exit_curvature"]))
    k0 = abs(it.params["exit_curvature"])
    w1, w2 = it._walls()
    allw = np.vstack([w1, w2])
    lo, hi = allw.min(0), allw.max(0)
    width = float((hi - lo).max())
    field = width * FIELD_CM / SPIRAL_CM          # field side in scene px
    shift = np.array([field / 2, field / 2]) - (lo + hi) / 2
    c = it.c + shift

    # motion through the tube at constant speed, entry (s = 0) to exit (s = L)
    seg = np.hypot(*np.diff(c, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]
    t_in = np.arange(0, L / v, 1.0 / FPS)
    inside = np.stack([np.interp(v * t_in, s, c[:, 0]), np.interp(v * t_in, s, c[:, 1])], 1)
    exit_xy = c[-1]

    def decay(h_deg):
        tau = math.radians(abs(h_deg)) / (k0 * v)
        sgn = 1.0 if h_deg > 0 else -1.0
        return lambda t: sgn * k0 * math.exp(-t / tau)

    tau_s = math.radians(25) / (k0 * v)
    profiles = {
        "A": lambda t: 0.0,
        "B": decay(HEADINGS["B"]), "C": decay(HEADINGS["C"]),
        "E": decay(HEADINGS["E"]),
        # F: bends outward, then back by the same amount, so it ends parallel to the exit tangent
        "F": lambda t: -k0 * math.exp(-t / tau_s) + (k0 * math.exp(-(t - 0.45) / tau_s) if t > 0.45 else 0.0),
    }
    r = sg.BALL_R
    alts = {}
    ext = spiral_extension(it, D_EXTRA_TURNS) + shift
    for name in "ABCDEF":
        if name == "D":   # along the spiral, then straight on from its last tangent, at the same speed
            es = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(ext, axis=0).T))])
            ts = np.arange(0, es[-1] / v, 1.0 / 960)
            arc = np.stack([np.interp(v * ts, es, ext[:, 0]), np.interp(v * ts, es, ext[:, 1])], 1)
            d = ext[-1] - ext[-3]
            d = d / np.hypot(*d)
            line = ext[-1] + np.outer(np.arange(1, 5 * 960) * v / 960, d)
            dense = np.vstack([arc, line])
        else:
            dense = path_after_exit(exit_xy, v, side, profiles[name])
        off = (dense[:, 0] < -r) | (dense[:, 1] < -r) | (dense[:, 0] > field + r) | (dense[:, 1] > field + r)
        end = int(np.argmax(off)) if off.any() else len(dense)
        dense = dense[:end]
        t = np.arange(len(dense)) / 960.0
        tf = np.arange(1.0 / FPS, t[-1], 1.0 / FPS)
        after = np.stack([np.interp(tf, t, dense[:, 0]), np.interp(tf, t, dense[:, 1])], 1)
        alts[name] = dict(frames=np.round(np.vstack([inside, [exit_xy], after]), 1).tolist(),
                          line=np.round(dense[::12], 1).tolist(),
                          category={"A": "correct", "B": "curvilinear", "C": "curvilinear",
                                    "D": "curvilinear", "E": "other", "F": "other"}[name])
    walls = [np.round(w + shift, 1)[::2].tolist() for w in (w1, w2)]
    tang = c[min(6, len(c) - 1)] - c[0]
    data = dict(item=it.id, fps=FPS, field_px=round(field, 1), spiral_px=round(width, 1),
                spiral_cm=SPIRAL_CM, field_cm=FIELD_CM, ball_r=r, speed_px_s=v,
                walls=walls, entry=np.round(c[0], 1).tolist(),
                entry_dir=np.round(tang / np.hypot(*tang), 3).tolist(), alternatives=alts)

    html = open(os.path.join(HERE, "mk_template.html")).read()
    html = html.replace("/*DATA*/{}", json.dumps(data, separators=(",", ":")))
    out = os.path.join(HERE, "experiment.html")
    open(out, "w").write(html)
    print(f"wrote {out} ({os.path.getsize(out) // 1024} KB); field {field:.0f} px, spiral {width:.0f} px")
    for n, a in alts.items():
        print(n, a["category"], len(a["frames"]), "frames", f"{len(a['frames']) / FPS:.2f} s")


if __name__ == "__main__":
    main()
