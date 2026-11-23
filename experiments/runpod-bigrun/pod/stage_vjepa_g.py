"""V-JEPA 2 ViT-g (1B): the same careful surprise readout as the ViT-L run (vjepa_probe.py: ball tokens,
three views, five futures incl. impossible ones for calibration), so the only change is model size.
Output: runs/vjepa_g/vjepa_probe.csv
   python stage_vjepa_g.py [--model facebook/vjepa2-vitg-fpc64-256] [--dry]"""
import argparse, os, subprocess, sys
import common as C
ap = argparse.ArgumentParser()
ap.add_argument("--model", default="facebook/vjepa2-vitg-fpc64-256")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()
STAGE = "vjepa_g"; out = C.outdir(STAGE); csv_path = os.path.join(out, "vjepa_probe.csv")
if os.path.exists(csv_path):
    C.log(STAGE, "already done"); sys.exit(0)
cmd = [sys.executable, os.path.join(C.HERE, "src", "pilot", "v2", "vjepa2", "vjepa_probe.py"), "--inputs", C.STIM, "--out", csv_path + ".part"]
if a.dry: cmd += ["--dry", os.path.join(out, "dry_views")]
r = subprocess.run(cmd, env=dict(os.environ, VJEPA_MODEL=a.model))
if r.returncode: sys.exit(r.returncode)
os.replace(csv_path + ".part", csv_path)
C.done(STAGE, dict(model=a.model, dry=a.dry)); C.log(STAGE, "done")
