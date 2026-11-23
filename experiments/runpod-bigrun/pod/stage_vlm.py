"""Vision-language model (default Qwen2.5-VL 72B, 4-bit AWQ, served by vLLM): the "reasoning" corner.
It sees 4 frames spanning the last second before the exit (in order) and picks where the ball goes next.
The options are worded by direction of travel, so they read the same for curved and straight tubes:
  straight on / bends to the left / bends to the right
Each item is asked 3 times, the options rotated so each takes each letter once. Temperature 0.
The answer is mapped to the same labels as the videos: impetus (bends the way the tube bent),
centrifugal (the other way), no_bias (straight). For the straight tube, either bend counts as impetus.
Output: runs/vlm/answers.csv (one row per question; re-running asks only the missing ones)
   python stage_vlm.py [--model Qwen/Qwen2.5-VL-72B-Instruct-AWQ] [--items all] [--dry]"""
import argparse, base64, csv, io, os, re
from PIL import Image
import common as C

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="Qwen/Qwen2.5-VL-72B-Instruct-AWQ", help="or OpenGVLab/InternVL3-78B-AWQ")
ap.add_argument("--items", default="all")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()
STAGE = "vlm"; out = C.outdir(STAGE); ITEMS = C.items(a.items)
CSV = os.path.join(out, "answers.csv")


def uri(arr):
    b = io.BytesIO(); Image.fromarray(arr).save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


have = set()
if os.path.exists(CSV):
    have = {(r["item_id"], r["order"]) for r in csv.DictReader(open(CSV))}
jobs = []
for iid, m in ITEMS.items():
    imgs = C.vlm_frames(m)                                          # last second, 4 frames
    for o, order in enumerate(C.VLM_ORDERS):
        if (iid, str(o)) in have:
            continue
        content = [{"type": "image_url", "image_url": {"url": uri(x)}} for x in imgs]
        content.append({"type": "text", "text": C.vlm_question(order, len(imgs))})
        jobs.append((iid, o, order, [{"role": "user", "content": content}]))
C.log(STAGE, f"{len(jobs)} questions to ask ({len(have)} already answered)")

if jobs:
    if a.dry:
        texts = ["A"] * len(jobs)
    else:
        from vllm import LLM, SamplingParams
        llm = LLM(model=a.model, max_model_len=16384, limit_mm_per_prompt={"image": 4}, gpu_memory_utilization=0.92,
                  trust_remote_code=True)
        res = llm.chat([j[3] for j in jobs], SamplingParams(temperature=0, max_tokens=8))
        texts = [r.outputs[0].text for r in res]
    new = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "item_id", "shape", "speed", "order", "letter", "choice", "label", "raw"])
        if new: w.writeheader()
        for (iid, o, order, _), t in zip(jobs, texts):
            m = ITEMS[iid]; mt = re.search(r"\b([ABC])\b", t.strip().upper())
            choice = order["ABC".index(mt.group(1))] if mt else ""
            if not choice: label = "invalid"
            elif choice == "straight": label = "no_bias"
            elif m["params"]["shape"] == "straight": label = "impetus"         # any bend after a straight tube
            else: label = "impetus" if choice == C.impetus_side(m) else "centrifugal"
            w.writerow(dict(model=a.model, item_id=iid, shape=m["params"]["shape"], speed=m["params"]["speed"], order=o,
                            letter=mt.group(1) if mt else "", choice=choice, label=label, raw=t.strip()[:80]))
C.done(STAGE, dict(model=a.model, dry=a.dry))
