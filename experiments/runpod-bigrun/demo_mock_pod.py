#!/usr/bin/env python3
"""End-to-end rehearsal on this machine, with no GPU and no Runpod spending.

A fake pod: pod/server.py runs locally on port 8000 with its job folder in a temporary directory. The real
orchestrate.py then uploads the real bundle, starts the real run_stages.sh with every stage in --dry mode
(no model loaded; placeholder videos and answers), watches it, downloads the results zips and "terminates".
Only three things are faked: the pod's address (localhost), the Runpod balance, and the terminate call.

   python demo_mock_pod.py            (about a minute; needs numpy, pillow, imageio, imageio-ffmpeg, requests)"""
import os, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import orchestrate as O

tmp = tempfile.mkdtemp(prefix="mockpod_"); job = os.path.join(tmp, "job")
O.STATE = os.path.join(tmp, "state.json"); O.RESULTS = os.path.join(tmp, "results")
O.api = lambda run: ("http://127.0.0.1:8000", {"X-Job-Token": "demo"})
O.balance = lambda: 30.0
O.terminate = lambda run=None: print(f"[mock] terminate {run}: on Runpod this deletes the pod and billing stops")

srv = subprocess.Popen([sys.executable, os.path.join(HERE, "pod", "server.py")],
                       env=dict(os.environ, JOB_TOKEN="demo", JOB_DIR=job))
try:
    time.sleep(1)
    print("wrong token ->", O.requests.get("http://127.0.0.1:8000/", headers={"X-Job-Token": "x"}).status_code)
    print("missing file ->", O.call("run1", "GET", "/file?name=nope.zip").status_code)
    print("path escape ->", O.call("run1", "GET", "/file?name=../../etc/passwd").status_code)

    O.save({"runs": {"run1": dict(pod="mock", token="demo", price=1.19, gpu="none", launched=time.time(),
                                  balance0=30.0, spent=0.0, fetched=[])}})
    # same as `start`, minus the setup (venvs) and the self-destruct backstop; stages run with --dry on this python
    data = O.bundle()
    print("upload", O.call("run1", "POST", "/upload?name=bundle.zip", data=data, timeout=600).text, len(data) // 1024, "KB")
    stages = " ".join(f"{s}:{O.STAGES[s][3]}" for s in ["vjepa_g", "vlm", "ltx13b", "cosmos2b", "wan22"])
    cmd = (f"cd {job} && python3 -m zipfile -e bundle.zip . && STAGE_ARGS=--dry PY_GEN={sys.executable} "
           f"PY_VLM={sys.executable} bash run_stages.sh '{stages}'")
    print("start", O.call("run1", "POST", "/run?name=main", data=cmd.encode()).text)
    O.RUNS["run1"]["stages"] = stages.replace(":", " ").split()[::2]
    O.watch("run1", every=5)
    print("\nresults downloaded to", O.RESULTS)
    for st in sorted(os.listdir(O.RESULTS)):
        p = os.path.join(O.RESULTS, st)
        if os.path.isdir(p): print(f"  {st:9s} {len(os.listdir(p))} files")
finally:
    srv.terminate()
