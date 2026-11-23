"""Second quality check for generated clips: does the scene stay put, and is there only one ball?
For each clip, compare every new frame with the last conditioning frame, ignoring pixels near the red ball.
changed = 90th percentile over frames of the changed-pixel count, in units of the ball's area.
blobs = number of frames with two or more ball-sized red blobs.
   python scene_check.py --inputs STIM --gen GEN_DIR --cond 33 > scene.csv
   python scene_check.py --inputs STIM --gen GEN_DIR --mode still --cond 1 > scene.csv   (image-to-video models)"""
import argparse, glob, math, os, sys
import numpy as np, imageio.v2 as imageio
from scipy import ndimage
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import analyze_v2

def stats(fr, ref_i, ball_r):
    gray = fr.astype(np.float32).mean(-1)
    red = analyze_v2.red_mask(fr)
    area = math.pi * ball_r ** 2
    ch, two = [], 0
    for t in range(ref_i + 1, len(fr)):
        near = ndimage.distance_transform_edt(~(red[t] | red[ref_i])) < 2.0 * ball_r
        ch.append(((np.abs(gray[t] - gray[ref_i]) > 35) & ~near).sum() / area)
        lab, n = ndimage.label(red[t])
        if n > 1 and (np.bincount(lab.ravel())[1:] > 0.3 * area).sum() >= 2:
            two += 1
    return float(np.percentile(ch, 90)), two

ap = argparse.ArgumentParser()
ap.add_argument("--inputs"); ap.add_argument("--gen"); ap.add_argument("--cond", type=int, default=33)
ap.add_argument("--mode", default="clip", help="clip name part: <item>__<mode>__s<j>.mp4")
a = ap.parse_args()
items = analyze_v2.load_items(a.inputs)
print("kind,item_id,sample,changed,two_ball_frames")
for iid, m in sorted(items.items()):
    full = np.stack(imageio.mimread(os.path.join(m["dir"], m["files"]["full"]), memtest=False))[..., :3]
    c = m["context_end_frame"]
    print("real,%s,real,%.2f,%d" % ((iid,) + stats(full[c:c + 49], 0, m["ball_radius"])), flush=True)
    for p in sorted(glob.glob(os.path.join(a.gen, iid + f"__{a.mode}__*.mp4"))):
        fr = np.stack(imageio.mimread(p, memtest=False))[..., :3]
        s = os.path.basename(p)[:-4].split("__")[2]
        print("gen,%s,%s,%.2f,%d" % ((iid, s) + stats(fr, a.cond - 1, m["ball_radius"] * fr.shape[2] / m["size"][0])), flush=True)
