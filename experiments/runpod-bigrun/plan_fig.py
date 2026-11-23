"""Draws plan.png (what each run executes, time limits, budget caps) from the numbers in orchestrate.py."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import orchestrate as O
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["text.parse_math"] = False
from matplotlib.patches import FancyBboxPatch
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a63", "#d9d8d2", "#ffffff"
C1, C2, SET = "#2a78d6", "#eb6834", "#b9b8b0"
OUTF = {"vjepa_g": "vjepa_probe.csv (surprise per future)", "vlm": "answers.csv (letter -> label)",
        "ltx13b": "90 mp4 -> tracked, labelled", "cosmos2b": "60 mp4 -> tracked, labelled", "wan22": "30 mp4 -> tracked, labelled"}
INP = {"vjepa_g": "real + curving futures", "vlm": "4 frames before exit", "ltx13b": "last 33 frames (clip)",
       "cosmos2b": "still before exit", "wan22": "still before exit"}
fig = plt.figure(figsize=(13, 8.2), dpi=150, facecolor=SURF)
fig.text(0.03, 0.965, "Slide 21 big run on Runpod: what will execute once you approve", fontsize=16, weight="bold", color=INK, va="top")
fig.text(0.03, 0.928, "1 × A100 80GB (community, $1.19/h) · 30 v2 tube items (24 curved + 6 straight) · pod deleted after each run · estimates, not yet timed",
         fontsize=10, color=MUTED, va="top")
# timeline
ax = fig.add_axes([0.2, 0.55, 0.77, 0.33]); ax.set_facecolor(SURF)
rows = []
for run, col in (("run1", C1), ("run2", C2)):
    R = O.RUNS[run]; rows.append((run, "setup + downloads", R["setup_h"], SET, None))
    for s in R["stages"]: rows.append((run, s, O.STAGES[s][2], col, O.STAGES[s][3]))
y = 0; labels = []; t = 0
for i, (run, s, h, col, lim) in enumerate(rows):
    if s == "setup + downloads": t = 0
    yy = len(rows) - 1 - i + (0.6 if run == "run1" else 0)
    ax.barh(yy, h, left=t, height=0.62, color=col, edgecolor=SURF, linewidth=2)
    if lim: ax.plot([t + lim, t + lim], [yy - 0.36, yy + 0.36], color=INK, lw=1.2)
    name = O.STAGES[s][0].split(":")[0] if s in O.STAGES else s
    ax.text(-0.15, yy, name, ha="right", va="center", fontsize=9.5, color=INK)
    txt = f"~{h:.1f} h · ~${h * O.PRICE:.2f}" + (f"   ({O.STAGES[s][1]})" if s in O.STAGES else "")
    ax.text(t + max(h, lim or 0) + 0.15, yy, txt, va="center", fontsize=8.8, color=MUTED)
    t += h
ax.set_xlim(-0.05, 13); ax.set_ylim(-0.6, len(rows) + 0.2)
ax.set_yticks([]); ax.tick_params(colors=MUTED, labelsize=8.5)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_color(GRID); ax.set_xlabel("hours from pod start (each run starts its own pod)", fontsize=9, color=MUTED)
ax.text(-0.15, len(rows) - 0.2 + 0.25, "Run 1 (priority 1)", ha="right", color=C1, fontsize=10.5, weight="bold")
ax.text(-0.15, 1.75, "Run 2 (priority 2)", ha="right", color=C2, fontsize=10.5, weight="bold")
ax.plot([], [], color=INK, lw=1.2, label="time limit: the stage is stopped here, finished outputs kept"); ax.legend(loc="upper right", frameon=False, fontsize=8.5)
# table
ax2 = fig.add_axes([0.03, 0.16, 0.94, 0.3]); ax2.axis("off"); ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)
cols = ["Model", "Gets", "Does", "Units", "Output (then scored here)"]
xs = [0.0, 0.19, 0.36, 0.6, 0.8]
for x, c in zip(xs, cols): ax2.text(x, 1.0, c, fontsize=9.5, weight="bold", color=INK, va="top")
ax2.plot([0, 1], [0.92, 0.92], color=GRID, lw=1)
order = O.RUNS["run1"]["stages"] + O.RUNS["run2"]["stages"]
for i, s in enumerate(order):
    yy = 0.8 - i * 0.17; what, units = O.STAGES[s][0], O.STAGES[s][1]
    name, does = what.split(": ", 1)
    col = C1 if s in O.RUNS["run1"]["stages"] else C2
    ax2.plot([-0.008, -0.008], [yy - 0.05, yy + 0.05], color=col, lw=4, solid_capstyle="round", clip_on=False)
    for x, v in zip(xs, [name, INP[s], does, units, OUTF[s]]):
        ax2.text(x, yy, v, fontsize=8.8, color=INK if x == 0 else MUTED, va="center", wrap=True)
# budget bar
ax3 = fig.add_axes([0.03, 0.04, 0.94, 0.08]); ax3.set_xlim(0, 30); ax3.set_ylim(-1.1, 1.0); ax3.axis("off")
e1, e2 = O.est("run1")[1], O.est("run2")[1]
ax3.barh(0, 30, color="#efeee9", height=0.5)
ax3.barh(0, e1, color=C1, height=0.5, edgecolor=SURF, linewidth=2)
ax3.barh(0, e2, left=e1, color=C2, height=0.5, edgecolor=SURF, linewidth=2)
ax3.text(30, 0.5, "$30 credit", ha="right", fontsize=8.3, color=MUTED, alpha=0)
for x, lab in ((O.RUNS["run1"]["cap"], "run 1 cap $14"), (O.RUNS["run1"]["cap"] + O.RUNS["run2"]["cap"], "both caps $26"), (O.TOTAL_CAP, "hard stop $28")):
    ax3.plot([x, x], [-0.42, 0.42], color=INK, lw=1.2); ax3.text(x, 0.5, lab, ha="left" if x > 27 else ("right" if x > 25 else "center"), fontsize=8.3, color=INK)
ax3.text(0, -0.95, f"Budget ($30 credit): estimate run 1 ~${e1:.0f} + run 2 ~${e2:.0f} = ~${e1 + e2:.0f}. The guard terminates the pod at a cap, checked every minute against your Runpod balance.",
         fontsize=8.8, color=MUTED)
fig.savefig(os.path.join(HERE, "plan.png"), facecolor=SURF)
print("ok")
