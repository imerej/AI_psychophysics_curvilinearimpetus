#!/usr/bin/env python3
"""Runs the slide 21 big run on Runpod from this workspace, with a budget guard.

  python orchestrate.py plan                 # what would run, estimated hours and cost (no spending)
  python orchestrate.py bundle               # write bundle.zip, exactly what `start` uploads (no spending)
  python orchestrate.py launch run1          # rent the pod (prints the pod's web address to allow)
  python orchestrate.py start run1           # upload code + stimuli, install, start the stages on the pod
  python orchestrate.py watch run1           # poll; fetch results as stages finish; enforce the budget; terminate at the end
  python orchestrate.py terminate            # stop all billing for this run's pod now
  python orchestrate.py status

Budget guard (all three apply):
  1. before launch: refuse if the Runpod balance is below the run's estimate, or if the run's cap would push total
     spend past TOTAL_CAP;
  2. while running: every minute, spend = balance at launch - balance now (and uptime x hourly price, whichever is
     higher); at the run's cap the pod is terminated straight away;
  3. on the pod: each stage has a time limit (run_stages.sh), after which the next stage starts;
  4. backstop on the pod (selfdestruct.sh), if this watcher dies: the pod terminates itself at the run's cap
     (cap / hourly price after launch) or 90 min after its stages end.
The pod is terminated (not just stopped) after each run, so nothing bills between runs. Results are downloaded
as each stage ends, so a terminated pod never loses finished work; a stopped stage resumes where it left off."""
import base64, io, json, os, re, secrets, sys, time, zipfile
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state.json")
RESULTS = os.path.join(HERE, "results")
EXP = os.path.dirname(HERE)                                          # experiments/
STIM = os.environ.get("STIM_DIR", os.path.join(HERE, "stim3d"))     # v2 renders (768x512, 24 fps): get_stimuli.sh
# the repo's own scoring code, copied into the bundle at the same relative paths (pod/common.py imports it)
SRC = {"src/analyze.py": "analyze.py", "src/pilot/analyze_v2.py": "pilot/analyze_v2.py",
       "src/pilot/v2/vjepa2/vjepa_probe.py": "pilot/v2/vjepa2/vjepa_probe.py"}
TOTAL_CAP = 28.0                       # USD over both runs; leaves $2 of the $30 untouched
GPUS = ["NVIDIA A100 80GB PCIe", "NVIDIA A100-SXM4-80GB",     # community cloud, cheapest first
        "NVIDIA RTX PRO 6000 Blackwell Server Edition",        # 96 GB, $1.69/h: fallback when no A100 is free
        "NVIDIA H100 PCIe", "NVIDIA H100 80GB HBM3"]
SECURE_GPUS = ["NVIDIA A100 80GB PCIe", "NVIDIA A100-SXM4-80GB"]    # secure cloud ($2.09/h) when community has none
IMAGE = "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04"   # only its system Python is used; venvs bring torch
# the venvs get torch 2.14/2.15 (vLLM 0.34 pins 2.14), whose wheels are built for CUDA 13: only hosts whose driver
# supports CUDA 13 can run them, so the pod is only rented on such a host (else torch silently falls back to the CPU)
CUDA_OK = ["13.0", "13.1", "13.2"]

# stage: (what, units, est. hours on one A100 80GB incl. weight download, time limit on the pod, extra args)
STAGES = {
    "vjepa_g":  ("V-JEPA 2 ViT-g (1B): surprise, real vs curving future", "30 items x 5 futures x 4 views", 0.5, 1.0),
    "ltx13b":   ("LTX-Video 13B: continue the 33-frame clip", "30 clips x 3 seeds = 90 videos", 3.0, 4.5),
    "vlm":      ("Qwen2.5-VL 72B (AWQ 4-bit): pick straight / left / right", "30 items x 3 option orders = 90 answers", 0.7, 1.5),
    "cosmos2b": ("Cosmos-Predict2 2B: continue from the still", "30 stills x 2 seeds = 60 videos", 2.5, 3.5),
    "wan22":    ("Wan 2.2 I2V A14B, 480p: continue from the still", "30 stills x 1 seed = 30 videos", 4.0, 6.0),
}
# caps raised 23 Nov (run1 14 -> 16, run2 12 -> 11, total still <= 28): community had no A100 at launch time, so
# run1 may run on secure cloud at $2.09/h (~7.1 h ~ $14.8)
RUNS = {"run1": dict(stages=["vjepa_g", "vlm", "ltx13b", "cosmos2b"], setup_h=0.4, cap=16.0, disk=220),
        "run2": dict(stages=["wan22"], setup_h=0.3, cap=11.0, disk=150),
        # both runs on one pod: one proxy host to allow instead of two, one setup instead of two
        "all": dict(stages=["vjepa_g", "vlm", "ltx13b", "cosmos2b", "wan22"], setup_h=0.4, cap=26.5, disk=280)}
PRICE = 1.19                            # USD/h, A100 80GB PCIe community (catalog, 23 Nov 2026); SXM is 1.39


def key():
    """RUNPOD_API_KEY from the environment (set in the cloud environment's settings), else ~/.runpod/config.toml."""
    if os.environ.get("RUNPOD_API_KEY"):
        return os.environ["RUNPOD_API_KEY"]
    return re.search(r'api_key\s*=\s*"([^"]+)"', open(os.path.expanduser("~/.runpod/config.toml")).read()).group(1)


def gq(q, v=None):
    r = requests.post("https://api.runpod.io/graphql", json={"query": q, "variables": v or {}},
                      headers={"Authorization": f"Bearer {key()}"}, timeout=60)
    d = r.json()
    if d.get("errors"):
        raise RuntimeError(d["errors"])
    return d["data"]


def balance():
    return float(gq("{ myself { clientBalance } }")["myself"]["clientBalance"])


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"runs": {}}


def save(s):
    json.dump(s, open(STATE, "w"), indent=1)


def est(run):
    R = RUNS[run]; h = R["setup_h"] + sum(STAGES[s][2] for s in R["stages"])
    return h, h * PRICE


def plan():
    tot_h = tot_c = 0
    for run, R in RUNS.items():
        h, c = est(run)
        if run != "all": tot_h += h; tot_c += c
        print(f"\n{run}  (cap ${R['cap']:.0f}, pod disk {R['disk']} GB)  setup + downloads ~{R['setup_h']} h")
        for s in R["stages"]:
            what, units, eh, lim = STAGES[s]
            print(f"  {s:9s} {what:58s} {units:38s} ~{eh:.1f} h  ~${eh * PRICE:.2f}  (limit {lim} h)")
        print(f"  total ~{h:.1f} h  ~${c:.2f}")
    print(f"\nboth runs ~{tot_h:.1f} h ~${tot_c:.2f} at ${PRICE}/h; hard cap over both ${TOTAL_CAP}")


def spent_total(s):
    return sum(r.get("spent", 0) for r in s["runs"].values())


def launch(run):
    s = load(); h, c = est(run); b = balance()
    print(f"balance ${b:.2f}; {run} estimate ~{h:.1f} h ~${c:.2f}; cap ${RUNS[run]['cap']}; spent so far ${spent_total(s):.2f}")
    if b < c * 1.2:
        sys.exit("STOP: balance is below the estimate + 20%; nothing launched")
    if spent_total(s) + RUNS[run]["cap"] > TOTAL_CAP:
        sys.exit(f"STOP: this run's cap would pass the total cap ${TOTAL_CAP}; nothing launched")
    token = secrets.token_urlsafe(24)
    srv = base64.b64encode(open(os.path.join(HERE, "pod", "server.py"), "rb").read()).decode()
    q = """mutation($i: PodFindAndDeployOnDemandInput) { podFindAndDeployOnDemand(input: $i) { id costPerHr machine { gpuDisplayName } } }"""
    last = None
    for cloud, gpu in [("COMMUNITY", g) for g in GPUS] + [("SECURE", g) for g in SECURE_GPUS]:
        i = dict(cloudType=cloud, gpuCount=1, gpuTypeId=gpu, name=f"slide21-{run}", volumeInGb=RUNS[run]["disk"],
                 containerDiskInGb=30, minVcpuCount=8, allowedCudaVersions=CUDA_OK, minMemoryInGb=100, volumeMountPath="/workspace", ports="8000/http",
                 imageName=IMAGE,
                 dockerArgs="bash -c 'echo $SRV_B64 | base64 -d > /server.py && JOB_DIR=/workspace/job python3 /server.py'",
                 env=[dict(key="SRV_B64", value=srv), dict(key="JOB_TOKEN", value=token)]
                     + ([dict(key="HF_TOKEN", value=os.environ["HF_TOKEN"])] if os.environ.get("HF_TOKEN") else []))
        try:
            p = gq(q, {"i": i})["podFindAndDeployOnDemand"]
            if p: break
        except RuntimeError as e:
            last = e; print("  no", cloud, gpu, "->", str(e)[:120])
    else:
        sys.exit(f"no A100 80GB available right now ({last}); nothing launched")
    s["runs"][run] = dict(pod=p["id"], token=token, price=p["costPerHr"], gpu=p["machine"]["gpuDisplayName"],
                          launched=time.time(), balance0=b, spent=0.0, fetched=[])
    save(s)
    print(f"launched {p['id']} ({p['machine']['gpuDisplayName']}, ${p['costPerHr']}/h)")
    print(f"ALLOW HOST: {p['id']}-8000.proxy.runpod.net")


def api(run):
    r = load()["runs"][run]
    return f"https://{r['pod']}-8000.proxy.runpod.net", {"X-Job-Token": r["token"]}


def call(run, method, path, **kw):
    base, h = api(run)
    return requests.request(method, base + path, headers=h, timeout=kw.pop("timeout", 120), **kw)


def bundle():
    """What the pod receives: pod/ (stage scripts), src/ (the repo's scoring code) and stim3d/ (the 30 items)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(os.path.join(HERE, "pod")):
            for f in files:
                if "__pycache__" in root: continue
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, os.path.join(HERE, "pod")))
        for arc, rel in SRC.items():
            z.write(os.path.join(EXP, rel), arc)
        for root, _, files in os.walk(STIM):
            for f in files:
                p = os.path.join(root, f); z.write(p, os.path.join("stim3d", os.path.relpath(p, STIM)))
    return buf.getvalue()


def start(run):
    if not os.path.isdir(os.path.join(STIM, "A1")):
        sys.exit(f"no stimuli in {STIM}: run get_stimuli.sh first")
    for _ in range(60):                                  # wait for the pod's server
        try:
            if call(run, "GET", "/", timeout=20).status_code == 200: break
        except requests.RequestException:
            pass
        time.sleep(15)
    else:
        sys.exit("pod server did not come up in 15 min; run `terminate` if it stays down")
    data = bundle()
    print("upload", call(run, "POST", "/upload?name=bundle.zip", data=data, timeout=600).text, len(data) // 1024, "KB")
    stages = " ".join(f"{s}:{STAGES[s][3]}" for s in RUNS[run]["stages"])
    need_vlm = "1" if "vlm" in RUNS[run]["stages"] else "0"
    r = load()["runs"][run]
    left = int(RUNS[run]["cap"] / r["price"] * 3600 - (time.time() - r["launched"]))      # seconds until the cap
    cmd = (f"cd /workspace/job && python3 -m zipfile -e bundle.zip . && chmod +x *.sh && "
           f"(nohup bash selfdestruct.sh {left} > /dev/null 2>&1 &) && "
           f"{{ NEED_VLM={need_vlm} bash setup.sh > setup.log 2>&1 || "
           f"{{ echo \"$(date +%T) SETUP FAILED (see setup.log)\" >> status.txt; exit 1; }}; }} && "
           f"bash run_stages.sh '{stages}'")
    print("start", call(run, "POST", "/run?name=main", data=cmd.encode()).text)


def terminate(run=None):
    s = load()
    for name, r in s["runs"].items():
        if (run is None or name == run) and not r.get("terminated"):
            try:
                gq("mutation($i: PodTerminateInput!) { podTerminate(input: $i) }", {"i": {"podId": r["pod"]}})
                print("terminated", name, r["pod"])
            except Exception as e:                        # network error too: say so loudly, retry next poll
                print("TERMINATE FAILED", name, r["pod"], e, flush=True)
                continue
            r["terminated"] = time.time(); save(s)


def fetch(run, names):
    """Download results_<stage>.zip files not yet fetched. Never raises: a failure is printed and retried next poll."""
    s = load(); r = s["runs"][run]; os.makedirs(RESULTS, exist_ok=True)
    for n in names:
        if n in r["fetched"]: continue
        try:
            resp = call(run, "GET", f"/file?name={n}", timeout=900)
            if resp.status_code != 200:
                print("not ready", n, resp.status_code, flush=True); continue
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:            # raises if truncated
                z.extractall(RESULTS)
            open(os.path.join(RESULTS, n), "wb").write(resp.content)
            r["fetched"].append(n); save(s); print("fetched", n, len(resp.content) // 1024, "KB", flush=True)
        except Exception as e:
            print("fetch failed", n, str(e)[:200], flush=True)


def watch(run, every=60):
    while True:
        s = load(); r = s["runs"][run]
        up_h = (time.time() - r["launched"]) / 3600
        try:
            b = balance()
            r["spent"] = round(max(r["balance0"] - b, up_h * r["price"]), 2); save(s)
        except Exception as e:
            print("balance check failed:", e, flush=True)
        cap = RUNS[run]["cap"]
        if r["spent"] >= cap or spent_total(s) >= TOTAL_CAP:
            print(f"BUDGET GUARD: spent ${r['spent']:.2f} (run cap ${cap}, total ${spent_total(s):.2f}/{TOTAL_CAP}) -> terminating", flush=True)
            fetch(run, [f"results_{st}.zip" for st in RUNS[run]["stages"]])
            terminate(run); return
        try:
            st = call(run, "GET", "/file?name=status.txt", timeout=30)
            status = st.text if st.status_code == 200 else ""
        except requests.RequestException:
            status = ""
        done = [l.split()[1] for l in status.splitlines() if " end, exit " in l]
        fetch(run, [f"results_{x}.zip" for x in done])
        last = status.strip().splitlines()[-1] if status.strip() else "(setting up)"
        print(f"{time.strftime('%H:%M')} up {up_h:.2f} h, spent ~${r['spent']:.2f} / cap ${cap}: {last}", flush=True)
        if "SETUP FAILED" in status:
            try: print(call(run, "GET", "/file?name=setup.log", timeout=60).text[-3000:], flush=True)
            except requests.RequestException: pass
            terminate(run); print("setup failed, pod terminated", flush=True); return
        if "ALL FINISHED" in status:
            fetch(run, [f"results_{x}.zip" for x in RUNS[run]["stages"]])
            terminate(run); print("run finished, pod terminated", flush=True); return
        if "SELF-TERMINATE" in status:
            print("the pod terminated itself (backstop)", flush=True); return
        time.sleep(every)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "plan": plan()
    elif c == "launch": launch(sys.argv[2])
    elif c == "bundle": open(os.path.join(HERE, "bundle.zip"), "wb").write(bundle()); print("wrote bundle.zip")
    elif c == "start": start(sys.argv[2])
    elif c == "watch": watch(sys.argv[2])
    elif c == "terminate": terminate(sys.argv[2] if len(sys.argv) > 2 else None)
    elif c == "status": print(json.dumps({k: {x: v[x] for x in v if x != "token"} for k, v in load()["runs"].items()}, indent=1)); print("balance", balance())
