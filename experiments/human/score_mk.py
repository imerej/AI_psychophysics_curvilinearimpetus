#!/usr/bin/env python3
"""Score the McCloskey & Kohl spiral replication (experiment.html) against their Table 2.

  python score_mk.py                      # reads data/mk_spiral_*.csv, writes data/mk_summary.csv (+ .png)
  python score_mk.py --data other/folder

Categories are theirs: A = correct, B-D = curvilinear impetus, E-F = other.
Their Table 2 (Exp. 2, n = 36 per condition): no motion 24 / 9 / 3, trajectories 23 / 10 / 3.
"""

import argparse
import csv
import glob
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = ["correct", "curvilinear", "other"]
CONDS = ["no_motion", "trajectories"]
MK = {"no_motion": [24, 9, 3], "trajectories": [23, 10, 3]}


def chi2_2x3(a, b):
    """Pearson chi-square for a 2 x 3 table, df = 2 (p = exp(-x/2) exactly for df = 2)."""
    cols = [x + y for x, y in zip(a, b)]
    n = sum(cols)
    if n == 0 or sum(a) == 0 or sum(b) == 0:
        return float("nan"), float("nan")
    x = 0.0
    for row in (a, b):
        for o, c in zip(row, cols):
            e = sum(row) * c / n
            if e > 0:
                x += (o - e) ** 2 / e
    return x, math.exp(-x / 2)


def counts(rows):
    return [sum(r["category"] == c for r in rows) for c in CATS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(HERE, "data"))
    args = ap.parse_args()
    rows = []
    for f in sorted(glob.glob(os.path.join(args.data, "mk_spiral_*.csv"))):
        rows += list(csv.DictReader(open(f, newline="")))
    if not rows:
        print("no mk_spiral_*.csv files in", args.data)
        return
    seen = {}
    for r in rows:   # a participant number counts once (the last file wins)
        seen[r["participant"]] = r
    rows = list(seen.values())

    out = []
    print(f"{len(rows)} participants\n")
    print(f"{'':28s}{'correct':>9s}{'curvilin.':>11s}{'other':>7s}{'n':>5s}")
    for cond in CONDS:
        sub = [r for r in rows if r["condition"] == cond]
        groups = [("all", sub)] + [(p, [r for r in sub if r["physics"] == p]) for p in ("none", "high_school", "college")]
        for g, rs in groups:
            c = counts(rs)
            if g != "all" and not rs:
                continue
            n = len(rs)
            print(f"{cond + ' / ' + g:28s}" + "".join(f"{v:>{w}d}" for v, w in zip(c, (9, 11, 7))) + f"{n:>5d}")
            out.append(dict(source="ours", condition=cond, physics=g, n=n,
                            **{k: v for k, v in zip(CATS, c)},
                            **{"pct_" + k: round(100 * v / n, 1) if n else "" for k, v in zip(CATS, c)}))
        mk = MK[cond]
        print(f"{cond + ' / McCloskey 1983':28s}" + "".join(f"{v:>{w}d}" for v, w in zip(mk, (9, 11, 7))) + f"{36:>5d}")
        out.append(dict(source="mccloskey_kohl_1983", condition=cond, physics="all", n=36,
                        **{k: v for k, v in zip(CATS, mk)},
                        **{"pct_" + k: round(100 * v / 36, 1) for k, v in zip(CATS, mk)}))
        x, p = chi2_2x3(counts(sub), mk)
        print(f"  ours vs theirs: chi2(2) = {x:.2f}, p = {p:.3f}\n")

    a, b = counts([r for r in rows if r["condition"] == "no_motion"]), counts([r for r in rows if r["condition"] == "trajectories"])
    x, p = chi2_2x3(a, b)
    print(f"no motion vs trajectories (ours): chi2(2) = {x:.2f}, p = {p:.3f}   (theirs: chi2(2) = .07)")
    print("small samples: expected counts under 5 make these chi-square p values rough")

    dst = os.path.join(args.data, "mk_summary.csv")
    with open(dst, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("wrote", dst)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    colors = ["#2a9d8f", "#e76f51", "#8d99ae"]
    for ax, cond in zip(axs, CONDS):
        ours = next(o for o in out if o["source"] == "ours" and o["condition"] == cond and o["physics"] == "all")
        theirs = MK[cond]
        xs = range(3)
        if ours["n"]:
            ax.bar([i - 0.2 for i in xs], [100 * ours[c] / ours["n"] for c in CATS], 0.38, color=colors, label=f"ours (n={ours['n']})")
        ax.bar([i + 0.2 for i in xs], [100 * v / 36 for v in theirs], 0.38, color=colors, alpha=0.4, hatch="//", label="McCloskey & Kohl 1983 (n=36)")
        ax.set_xticks(list(xs), ["correct (A)", "curvilinear (B-D)", "other (E-F)"])
        ax.set_title(cond.replace("_", " "))
        ax.set_ylim(0, 100)
        ax.legend(fontsize=8, frameon=False)
    axs[0].set_ylabel("% of participants")
    fig.tight_layout()
    png = os.path.join(args.data, "mk_summary.png")
    fig.savefig(png, dpi=150)
    print("wrote", png)


if __name__ == "__main__":
    main()
