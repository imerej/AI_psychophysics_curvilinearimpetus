#!/usr/bin/env python3
"""Fix the 3D A1 inputs for the models: context.mp4 and still.png stop at frame k-1 (whole ball
still in the tube), like the 2D items. The Blender export had them 2 frames past the exit.
  python prep3d.py inputs_3d inputs_3d_fixed [--items id1,id2]"""
import json, os, shutil, sys, glob
import imageio.v2 as imageio
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
only = sys.argv[4].split(",") if len(sys.argv) > 4 and sys.argv[3] == "--items" else None
for d in sorted(glob.glob(os.path.join(src, "A1", "*"))):
    iid = os.path.basename(d)
    if only and iid not in only:
        continue
    o = os.path.join(dst, "A1", iid); os.makedirs(o, exist_ok=True)
    m = json.load(open(os.path.join(d, "meta3d.json")))
    k = m["critical_frame"]
    full = imageio.mimread(os.path.join(d, "full.mp4"), memtest=False)
    end = k - 1
    with imageio.get_writer(os.path.join(o, "context.mp4"), fps=m["fps"], codec="libx264", quality=8,
                            macro_block_size=16, pixelformat="yuv420p", ffmpeg_log_level="error") as w:
        for f in full[:end + 1]:
            w.append_data(f[..., :3])
    Image.fromarray(full[end][..., :3]).save(os.path.join(o, "still.png"))
    for f in ("full.mp4", "anomalous_impetus.mp4"):
        if os.path.exists(os.path.join(d, f)):
            shutil.copy(os.path.join(d, f), o)
    m["context_end_frame"] = end
    m["still_frame"] = end
    m["files"] = {k2: v for k2, v in m["files"].items() if os.path.exists(os.path.join(o, v))}
    json.dump(m, open(os.path.join(o, "meta3d.json"), "w"))
    print(iid, "k", k, "context ends at", end)
