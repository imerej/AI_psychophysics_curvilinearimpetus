#!/usr/bin/env python3
"""Build experiment_draw_judge.html: the human version of the slide-21 tube test.

Reads the same 30 A1 items the models get (../inputs/A1/*/meta.json) and embeds the ball
paths and tube outlines in one self-contained page, so the browser redraws the exact
stimuli the models see (480 x 320, 16 fps) with no video files.

  python build_draw_judge.py            # writes experiment_draw_judge.html next to this script
"""

import glob
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = os.path.join(HERE, "..", "inputs", "A1")


def clean(xy):
    return [[round(x, 1), round(y, 1)] if all(map(math.isfinite, (x, y))) else None for x, y in xy]


items = []
for p in sorted(glob.glob(os.path.join(INPUTS, "*", "meta.json"))):
    m = json.load(open(p))
    items.append(dict(id=m["item_id"], shape=m["params"]["shape"], speed=m["params"]["speed"],
                      k=m["critical_frame"], ctx_end=m["context_end_frame"],
                      ball=clean(m["ball_xy"]), imp=clean(m["anomalous_impetus_xy"]),
                      line=m["scene"]["centerline"], hw=m["scene"]["half_width"]))
assert len(items) == 30, len(items)

html = open(os.path.join(HERE, "experiment_draw_judge_template.html")).read()
html = html.replace("/*ITEMS*/[]", json.dumps(items, separators=(",", ":")))
out = os.path.join(HERE, "experiment_draw_judge.html")
open(out, "w").write(html)
print(f"wrote {out} ({os.path.getsize(out) // 1024} KB, {len(items)} items)")
