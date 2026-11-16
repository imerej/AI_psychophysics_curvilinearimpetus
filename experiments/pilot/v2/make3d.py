#!/usr/bin/env python3
"""Make 3D versions of the stimuli: runs Blender on render3d.py, then builds the videos.

    python make3d.py                       # 3D versions of A1, A3, B1, C1 from ./stimuli
    python make3d.py --preview             # one still per item, to check the look (fast)
    python make3d.py --items c180,L100     # only some items
    python make3d.py --blender "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe"

Needs Blender (free, blender.org; tested with 5.2) and the same Python
libraries as stimgen.py. Output goes to ./stimuli3d/<family>/<item_id>/:
  full.mp4, context.mp4, still.png, anomalous_*.mp4, meta3d.json
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def find_blender(given):
    if given:
        return given
    found = shutil.which("blender")
    if found:
        return found
    candidates = ["/Applications/Blender.app/Contents/MacOS/Blender"]
    candidates += sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"), reverse=True)
    candidates += sorted(glob.glob("/snap/bin/blender")) + sorted(glob.glob(os.path.expanduser("~/blender*/blender")))
    for c in candidates:
        if os.path.exists(c):
            return c
    sys.exit("Blender not found. Install it from blender.org, or pass --blender /path/to/blender")


def assemble(out_dir, keep_frames=False):
    import imageio.v2 as imageio

    def video(path, files):
        with imageio.get_writer(path, fps=fps, codec="libx264", quality=8, macro_block_size=16,
                                pixelformat="yuv420p", ffmpeg_log_level="error") as w:
            for f in files:
                w.append_data(imageio.imread(f)[..., :3])

    for meta_path in sorted(glob.glob(os.path.join(out_dir, "*", "*", "meta3d.json"))):
        d = os.path.dirname(meta_path)
        m = json.load(open(meta_path))
        fps, k, ctx = m["fps"], m["critical_frame"], m["context_end_frame"]
        files = {}
        for name in m["versions"]:
            frames = sorted(glob.glob(os.path.join(d, "frames_" + name, "*.png")))
            if len(frames) < m["n_frames"]:
                if len(frames) == 1 and name == "full":  # preview mode
                    shutil.copy(frames[0], os.path.join(d, "still.png"))
                    files["still"] = "still.png"
                continue
            video(os.path.join(d, name + ".mp4"), frames)
            files[name] = name + ".mp4"
            if name == "full":
                video(os.path.join(d, "context.mp4"), frames[:ctx + 1])
                files["context"] = "context.mp4"
                shutil.copy(frames[m.get("still_frame", ctx)], os.path.join(d, "still.png"))  # last context frame
                files["still"] = "still.png"
        if files and not keep_frames and "full" in files:
            for name in m["versions"]:
                shutil.rmtree(os.path.join(d, "frames_" + name), ignore_errors=True)
        m["files"] = files
        with open(meta_path, "w") as fh:
            json.dump(m, fh)
        print(f"assembled {m['item_id']}: {', '.join(files.values()) or 'nothing'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stimuli", default="stimuli", help="folder made by stimgen.py")
    ap.add_argument("--out", default="stimuli3d")
    ap.add_argument("--families", default="A1,A3,B1,C1")
    ap.add_argument("--items", default="", help="only items whose id contains one of these, comma-separated")
    ap.add_argument("--samples", type=int, default=16, help="render quality; 8 is twice as fast and noisier")
    ap.add_argument("--engine", choices=["cycles", "eevee"], default="cycles",
                    help="eevee is much faster on a computer with a decent graphics card")
    ap.add_argument("--preview", action="store_true", help="one still per item only")
    ap.add_argument("--no-anomalous", action="store_true")
    ap.add_argument("--blender", default="", help="path to the Blender program")
    ap.add_argument("--keep-frames", action="store_true", help="keep the PNG frames after making the videos")
    ap.add_argument("--assemble-only", action="store_true", help="skip rendering, only build videos")
    args = ap.parse_args()

    if not args.assemble_only:
        cmd = [find_blender(args.blender), "-b", "--factory-startup", "--python",
               os.path.join(HERE, "render3d.py"), "--",
               "--in", args.stimuli, "--out", args.out, "--families", args.families,
               "--items", args.items, "--samples", str(args.samples), "--engine", args.engine]
        if args.preview:
            cmd.append("--preview")
        if args.no_anomalous:
            cmd.append("--no-anomalous")
        print("running:", " ".join(f'"{c}"' if " " in c else c for c in cmd))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        tail = []
        for line in proc.stdout:  # show our progress lines, hide Blender's per-tile chatter
            tail = (tail + [line.rstrip()])[-30:]
            if line.startswith("render3d"):
                print(line.rstrip(), flush=True)
        if proc.wait() != 0:
            print("\n".join(tail))
            sys.exit("Blender failed (last messages above)")
    assemble(args.out, keep_frames=args.keep_frames)


if __name__ == "__main__":
    main()
