#!/usr/bin/env python3
"""Kaggle notebook that renders the v2 3D stimuli with Blender on the GPU.
   python build_render_notebook.py [--all] --out render_v2.ipynb"""
import argparse, base64, io, json, os, tarfile
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument("--all", action="store_true"); ap.add_argument("--out", default="render_v2.ipynb")
ap.add_argument("--samples", type=int, default=16)
a = ap.parse_args()
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w:gz") as tf:
    for f in ("make_v2.py", "render3d.py", "make3d.py"):
        tf.add(os.path.join(HERE, f), arcname="v2/" + f)
    tf.add(os.path.join(HERE, "..", "..", "..", "stimgen", "stimgen.py"), arcname="v2/stimgen.py")
blob = base64.b64encode(buf.getvalue()).decode()
cells = []
md = lambda s: cells.append(dict(cell_type="markdown", metadata={}, source=s))
code = lambda s: cells.append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=s))
md("# Slide 21: render the v2 3D stimuli (Blender, GPU)\n\n24 fps, 768×512, bigger striped ball that rolls, context stops before the exit.")
code('''%%bash
set -e
apt-get -qq update >/dev/null 2>&1 || true
apt-get -qq install -y libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 libxkbcommon0 libsm6 libice6 libegl1 >/dev/null 2>&1 || true
cd /kaggle/working
for url in https://download.blender.org/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz \\
           https://mirrors.ocf.berkeley.edu/blender/release/Blender4.2/blender-4.2.3-linux-x64.tar.xz \\
           https://download.blender.org/release/Blender4.1/blender-4.1.1-linux-x64.tar.xz; do
  if wget -q -O blender.tar.xz "$url"; then echo "got $url"; break; fi
done
mkdir -p blender && tar -xf blender.tar.xz -C blender --strip-components=1 && rm blender.tar.xz
./blender/blender --version | head -1
pip install -q imageio imageio-ffmpeg''')
code(f'''import base64, io, tarfile, os, subprocess, sys, time, glob, json
BLOB = "{blob}"
tarfile.open(fileobj=io.BytesIO(base64.b64decode(BLOB)), mode="r:gz").extractall("/kaggle/working/src")
del BLOB
os.chdir("/kaggle/working/src/v2")
ALL = {a.all}
t0 = time.time()
r = subprocess.run([sys.executable, "make_v2.py", "--out", "/kaggle/working/stim2d", "--no-video"] + (["--all"] if ALL else []),
                   capture_output=True, text=True)
print(r.stdout[-3000:], r.stderr[-3000:])''')
code('''# which device will Cycles use?
expr = ("import bpy; p=bpy.context.preferences.addons['cycles'].preferences\\n"
        "for k in ('OPTIX','CUDA'):\\n"
        "    try:\\n        p.compute_device_type=k; p.get_devices(); print('CYCLES', k, [(d.name, d.type) for d in p.devices])\\n"
        "    except Exception as e: print('CYCLES', k, 'error', e)")
r = subprocess.run(["/kaggle/working/blender/blender", "-b", "--factory-startup", "--python-expr", expr], capture_output=True, text=True)
print("\\n".join(l for l in r.stdout.splitlines() if l.startswith("CYCLES")), r.stderr[-1500:])''')
code(f'''# one Blender per GPU, items split between them, then build the videos
import torch
NG = max(1, torch.cuda.device_count())
ids = sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob("/kaggle/working/stim2d/A1/*/meta.json"))
t0 = time.time()
procs = []
for g in range(NG):
    part = ids[g::NG]
    cmd = ["/kaggle/working/blender/blender", "-b", "--factory-startup", "--python-exit-code", "1", "--python", os.path.abspath("render3d.py"), "--",
           "--in", "/kaggle/working/stim2d", "--out", "/kaggle/working/stim3d", "--families", "A1",
           "--items", ",".join(part), "--samples", "{a.samples}", "--engine", "cycles"]
    procs.append(subprocess.Popen(cmd, env=dict(os.environ, CUDA_VISIBLE_DEVICES=str(g)), stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True))
import threading
def pump(p, g):
    tail = []
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-20:]
        if line.startswith("render3d"): print(f"[gpu{{g}}]", line.rstrip(), f"{{time.time()-t0:.0f}}s", flush=True)
    rc = p.wait(); print(f"[gpu{{g}}] blender exit {{rc}}; last lines:", *tail, sep="\\n", flush=True)
th = [threading.Thread(target=pump, args=(p, g)) for g, p in enumerate(procs)]
[x.start() for x in th]; [x.join() for x in th]
r = subprocess.run([sys.executable, "make3d.py", "--out", "/kaggle/working/stim3d", "--assemble-only"], capture_output=True, text=True)
print(r.stdout[-3000:], r.stderr[-2000:])
print(f"{{time.time()-t0:.0f}} s")''')
code('''import imageio.v2 as imageio, numpy as np
from PIL import Image
dirs = sorted(glob.glob("/kaggle/working/stim3d/A1/*"))
print(len(dirs), "items")
for d in dirs[:5]:
    m = json.load(open(d + "/meta3d.json"))
    fr = imageio.mimread(d + "/full.mp4", memtest=False)
    print(os.path.basename(d), m["size"], "frames", len(fr), "k", m["critical_frame"], "ctx", m["context_end_frame"], sorted(m["files"]))
    idx = np.linspace(m["context_end_frame"] - 20, len(fr) - 1, 6).astype(int)
    Image.fromarray(np.concatenate([fr[i] for i in idx], 1)).resize((6 * 384, 256)).save(f"/kaggle/working/strip_{os.path.basename(d)}.png")
!cd /kaggle/working && zip -qr stim3d_v2.zip stim3d && ls -la stim3d_v2.zip''')
nb = dict(cells=cells, metadata=dict(kernelspec=dict(display_name="Python 3", language="python", name="python3")), nbformat=4, nbformat_minor=5)
json.dump(nb, open(os.path.join(HERE, a.out), "w"), indent=1)
print("written", a.out, len(blob) // 1024, "KB")
