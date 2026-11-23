#!/usr/bin/env python3
"""Scores everything the big run brings back, in one go, with the same rules as the LTX 2B run (pilot/v2/results_all).

  python score_bigrun.py [--results results] [--stim stim3d] [--out results/scored] [--no-scene]

Generators (ltx13b clip mode; cosmos2b, wan22 from the still): ../pilot/analyze_v2.py tracks the ball after the exit
and labels each clip impetus (keeps curving the way the tube bent) / no_bias (straight) / centrifugal (bends outward),
or invalid (degraded, stopped, lost). Then the scene check (../pilot/v2/scene_check.py) drops clips where the scene
changes (changed > 0.5 ball areas) or a second ball appears (>= 5 frames): the "strict" table, as in the 2B run.
V-JEPA 2 ViT-g: per view, the share of items where the curving future is LESS surprising than the true one (ball
tokens), next to ViT-L on the same view; calibration: a ball that freezes should be MORE surprising than the true one.
VLM: share of answers per label, and how often the 3 option orders agree.
For each model: curved tubes vs straight control, one-sided Fisher exact test on "keeps curving".
Writes per_clip.csv, summary.csv (generators + V-JEPA + VLM, one row per model x shape) and summary.md."""
import argparse, csv, json, os, subprocess, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EXP, "pilot")); sys.path.insert(0, EXP)
import analyze_v2  # noqa: E402
from scipy.stats import fisher_exact  # noqa: E402

# model folder -> (clip mode, conditioning frames at the start of each clip, output fps)
GEN = {"ltx13b": ("clip", 33, 24), "cosmos2b": ("still", 1, 16), "wan22": ("still", 1, 16)}
SHAPES = ["c90", "c180", "c270", "spiral", "straight"]
VJ_L = os.path.join(EXP, "pilot", "v2", "vjepa2", "vjepa_probe.csv")          # ViT-L, same probe
LTX2B = os.path.join(EXP, "pilot", "v2", "results_all", "summary_strict.csv")  # LTX 2B, same protocol
MAX_CHANGED, MAX_TWO = 0.5, 5


def pct(n, d):
    return round(100 * n / d, 1) if d else ""


def scene(stim, folder, mode, cond):
    out = subprocess.run([sys.executable, os.path.join(EXP, "pilot", "v2", "scene_check.py"), "--inputs", stim,
                          "--gen", folder, "--mode", mode, "--cond", str(cond)], capture_output=True, text=True, check=True)
    return {(r["item_id"], r["sample"]): r for r in csv.DictReader(out.stdout.splitlines()) if r["kind"] == "gen"}


def gen_rows(items, res, stim, do_scene):
    rows = []
    for model, (mode, cond, fps) in GEN.items():
        folder = os.path.join(res, model)
        if not os.path.isdir(folder):
            continue
        rs = analyze_v2.score_model(items, folder, model, {f"{model}_{mode}": cond}, None if fps == 24 else fps)
        sc = scene(stim, folder, mode, cond) if do_scene else {}
        for r in rs:
            s = sc.get((r["item_id"], r["sample"]))
            r["changed"] = s["changed"] if s else ""
            r["two_ball_frames"] = s["two_ball_frames"] if s else ""
            bad = s and (float(s["changed"]) > MAX_CHANGED or int(s["two_ball_frames"]) >= MAX_TWO)
            r["label_strict"] = "invalid_scene" if bad and not r["label"].startswith("invalid") else r["label"]
        rows += rs
    return rows


def gen_summary(rows, key):
    out, fisher = [], {}
    by = defaultdict(list)
    for r in rows:
        by[(r["model"], r["shape"])].append(r[key])
    for model in dict.fromkeys(r["model"] for r in rows):
        for shape in SHAPES:
            labs = by.get((model, shape), [])
            v = [l for l in labs if not l.startswith("invalid")]
            c = Counter(v)
            out.append(dict(model=model, readout="generate", shape=shape, n_total=len(labs), n_valid=len(v),
                            pct_curving=pct(c["impetus"], len(v)), pct_straight=pct(c["no_bias"], len(v)),
                            pct_outward=pct(c["centrifugal"], len(v))))
        cur = [l for s in SHAPES[:4] for l in by.get((model, s), []) if not l.startswith("invalid")]
        st = [l for l in by.get((model, "straight"), []) if not l.startswith("invalid")]
        a, b = sum(l == "impetus" for l in cur), sum(l == "impetus" for l in st)
        p = fisher_exact([[a, len(cur) - a], [b, len(st) - b]], alternative="greater")[1] if cur and st else float("nan")
        fisher[model] = (a, len(cur), b, len(st), p)
    return out, fisher


def vjepa_summary(path, model):
    if not os.path.exists(path):
        return [], {}
    d = {(r["item_id"], r["view"], r["future"]): r for r in csv.DictReader(open(path))}
    out, calib = [], {}
    for view in dict.fromkeys(k[1] for k in d):
        for shape in SHAPES:
            ids = sorted({k[0] for k in d if k[1] == view and d[k]["shape"] == shape})
            prefer = [float(d[(i, view, "impetus")]["surprise_ball"]) < float(d[(i, view, "correct")]["surprise_ball"])
                      for i in ids if (i, view, "impetus") in d]
            out.append(dict(model=model, readout=f"judge:{view}", shape=shape, n_total=len(prefer), n_valid=len(prefer),
                            pct_curving=pct(sum(prefer), len(prefer)), pct_straight="", pct_outward=""))
        ids = sorted({k[0] for k in d if k[1] == view})
        fz = [float(d[(i, view, "freeze")]["surprise_all"]) > float(d[(i, view, "correct")]["surprise_all"])
              for i in ids if (i, view, "freeze") in d]
        calib[view] = (sum(fz), len(fz))
    return out, calib


def vlm_summary(path):
    if not os.path.exists(path):
        return [], ""
    rows = list(csv.DictReader(open(path)))
    out = []
    for shape in SHAPES:
        labs = [r["label"] for r in rows if r["shape"] == shape]
        v = [l for l in labs if l != "invalid"]; c = Counter(v)
        out.append(dict(model=rows[0]["model"].split("/")[-1], readout="answer", shape=shape, n_total=len(labs),
                        n_valid=len(v), pct_curving=pct(c["impetus"], len(v)), pct_straight=pct(c["no_bias"], len(v)),
                        pct_outward=pct(c["centrifugal"], len(v))))
    per = defaultdict(set)
    for r in rows:
        per[r["item_id"]].add(r["choice"])
    agree = sum(len(s) == 1 for s in per.values())
    return out, f"the 3 option orders give the same answer on {agree} of {len(per)} items"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=os.path.join(HERE, "results"))
    ap.add_argument("--stim", default=os.path.join(HERE, "stim3d"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-scene", action="store_true")
    a = ap.parse_args()
    out = a.out or os.path.join(a.results, "scored"); os.makedirs(out, exist_ok=True)
    items = analyze_v2.load_items(a.stim)

    rows = gen_rows(items, a.results, a.stim, not a.no_scene)
    gs, fisher = gen_summary(rows, "label_strict")
    vg, calib_g = vjepa_summary(os.path.join(a.results, "vjepa_g", "vjepa_probe.csv"), "vjepa_g")
    vl, calib_l = vjepa_summary(VJ_L, "vjepa_l")
    vs, agree = vlm_summary(os.path.join(a.results, "vlm", "answers.csv"))
    if rows:
        cols = [c for c in rows[0] if c != "path"] + ["path"]
        with open(os.path.join(out, "per_clip.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    summ = gs + vs + vg + vl
    if summ:
        with open(os.path.join(out, "summary.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(summ[0])); w.writeheader(); w.writerows(summ)

    L = ["# Big run: scores", "", "Keeps curving = the path bends the way the tube bent (impetus). "
         "Generators: after the tracker and the scene check, as in the LTX 2B run.", ""]
    ref = {}
    if os.path.exists(LTX2B):
        for r in csv.DictReader(open(LTX2B)):
            ref[r["shape"]] = r
    tab = defaultdict(dict)
    for r in gs + vs:
        tab[r["model"]][r["shape"]] = r
    if ref:
        tab["ltx 2B (Oct run)"] = {s: dict(pct_curving=ref[s]["pct_curving"], n_valid=ref[s]["n_valid"],
                                            n_total=ref[s]["n_total"]) for s in ref}
    L += ["| Model | " + " | ".join(SHAPES) + " |", "|---" * (len(SHAPES) + 1) + "|"]
    for model, d in tab.items():
        L.append(f"| {model} | " + " | ".join(f"{d[s]['pct_curving']}% ({d[s]['n_valid']}/{d[s]['n_total']})"
                                              if s in d and d[s]["n_valid"] not in ("", 0, "0") else "–" for s in SHAPES) + " |")
    L += ["", "Cells: % keeps curving (kept / total clips or answers).", ""]
    for m, (a1, n1, b1, n2, p) in fisher.items():
        L.append(f"- {m}: curved tubes {a1}/{n1} keep curving vs straight control {b1}/{n2}; Fisher one-sided p = {p:.2g}")
    if agree:
        L.append(f"- VLM: {agree}")
    if vg or vl:
        L += ["", "## V-JEPA 2: curving future less surprising than the true one (ball tokens)", "",
              "| Model, view | " + " | ".join(SHAPES) + " | freeze > true (calibration) |", "|---" * (len(SHAPES) + 2) + "|"]
        for rows_v, calib in ((vg, calib_g), (vl, calib_l)):
            byv = defaultdict(dict)
            for r in rows_v:
                byv[r["readout"].split(":")[1]][r["shape"]] = r
            for view, d in byv.items():
                m = rows_v[0]["model"]
                L.append(f"| {m}, {view} | " + " | ".join(f"{d[s]['pct_curving']}% ({d[s]['n_valid']})" if s in d else "–"
                                                       for s in SHAPES) + f" | {calib[view][0]}/{calib[view][1]} |")
        L += ["", "50% = no preference. If the freeze column is not near 100%, that view's surprise is not reliable."]
    open(os.path.join(out, "summary.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L)); print("\nwrote", out)


if __name__ == "__main__":
    main()
