#!/usr/bin/env python3
"""Shows exactly what each model of the big run receives, so it can be checked before any GPU time is spent.

The images come from the same functions the stages call (pod/common.py: ltx_frames, still, vlm_frames,
vlm_question, ltx_prompt) and, for V-JEPA, from vjepa_probe.py --dry, which saves the very clips it would feed
the model. Output: inputs_preview/index.html (one self-contained page).
   python show_inputs.py [--items v120_s1]      (needs stim3d/: run get_stimuli.sh first)"""
import argparse, base64, html, io, json, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("STIM_DIR", os.path.join(HERE, "stim3d")); os.environ.setdefault("JOB_DIR", tempfile.mkdtemp())
sys.path.insert(0, os.path.join(HERE, "pod"))
import common as C

ap = argparse.ArgumentParser(); ap.add_argument("--items", default="v120_s1"); a = ap.parse_args()
OUT = os.path.join(HERE, "inputs_preview"); os.makedirs(OUT, exist_ok=True)
ALL = C.items(); SEL = C.items(a.items)
ORDER_SHAPES = ["straight", "c90", "c180", "c270", "spiral"]
SEL = dict(sorted(SEL.items(), key=lambda kv: ORDER_SHAPES.index(kv[1]["params"]["shape"])))


def jpg(img, q=82, size=None):
    img = img if isinstance(img, Image.Image) else Image.fromarray(img)
    if size: img = img.resize(size)
    b = io.BytesIO(); img.save(b, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


# V-JEPA: the probe's own dry mode writes the 16-frame clips it would send (8 context + 8 future), for v120_s1 items
vj = tempfile.mkdtemp()
subprocess.run([sys.executable, os.path.join(HERE, "..", "pilot", "v2", "vjepa2", "vjepa_probe.py"), "--inputs", C.STIM,
                "--out", os.path.join(vj, "x.csv"), "--dry", vj], check=True, stdout=subprocess.DEVNULL)

SHAPE_NAME = {"straight": "Straight tube (control)", "c90": "90° arc", "c180": "180° arc", "c270": "270° arc",
              "spiral": "Spiral, 1.1 turns"}
data = []
for iid, m in SEL.items():
    fps, c, k = m["fps"], m["context_end_frame"], m["critical_frame"]
    side = C.impetus_side(m); shape = m["params"]["shape"]
    ltx = C.ltx_frames(m)
    vf = C.vlm_frames(m); step = max(1, round(fps / 3))
    orders = []
    for o, order in enumerate(C.VLM_ORDERS):
        lab = {}
        for L, opt in zip("ABC", order):
            lab[L] = ("no bias" if opt == "straight" else
                      "curving" if (shape == "straight" or opt == side) else "outward")
        orders.append(dict(text=C.vlm_question(order), labels=lab))
    vjv = []
    for view, desc in (("whole", "whole frame, padded square, 12 fps"), ("crop12", "512 px square at the exit, 12 fps"),
                       ("crop24", "256 px square at the exit, 24 fps")):
        row = {}
        for fut in ("correct", "impetus", "vanish", "reverse", "freeze"):
            p = os.path.join(vj, f"{iid}_{view}_{fut}.jpg")
            if os.path.exists(p): row[fut] = jpg(Image.open(p), 80)
        vjv.append(dict(view=view, desc=desc, futs=row))
    data.append(dict(
        id=iid, shape=shape, name=SHAPE_NAME[shape], speed=m["params"]["speed"], fps=fps,
        ctx_end=c, exit=k, lead_ms=round((k - c) / fps * 1000), side=side, direction=C.direction(m),
        ltx=[jpg(f, 72, (576, 384)) for f in ltx], ltx_first=c - len(ltx) + 1, ltx_prompt=C.ltx_prompt(m),
        still=jpg(C.still(m, 768, 512), 88),
        vlm=[jpg(f, 85) for f in vf], vlm_idx=[c - step * j for j in (3, 2, 1, 0)], orders=orders, vjepa=vjv))

thumbs = [dict(id=iid, shape=m["params"]["shape"], speed=m["params"]["speed"], side=C.impetus_side(m),
               src=jpg(C.still(m, 768, 512), 70, (288, 192))) for iid, m in
          sorted(ALL.items(), key=lambda kv: (ORDER_SHAPES.index(kv[1]["params"]["shape"]), kv[0]))]
meta = dict(prompt_still=C.PROMPT_STILL, neg_still=C.NEG, ltx_neg=C.LTX_NEG, n_items=len(ALL))

page = open(os.path.join(HERE, "show_inputs_template.html")).read()
page = page.replace("/*DATA*/null", json.dumps(dict(items=data, thumbs=thumbs, meta=meta)))
open(os.path.join(OUT, "index.html"), "w").write(page)
print("wrote", os.path.join(OUT, "index.html"), os.path.getsize(os.path.join(OUT, "index.html")) // 1024, "KB")
