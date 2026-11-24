"""Vision-language model (default Qwen2.5-VL 72B, 4-bit AWQ, served by vLLM): the "reasoning" corner.
It sees 4 frames spanning the last second before the exit (in order) and picks where the ball goes next.
The options are worded by direction of travel, so they read the same for curved and straight tubes:
  straight on / bends to the left / bends to the right
Each item is asked 3 times, the options rotated so each takes each letter once. Temperature 0.
The answer is mapped to the same labels as the videos: impetus (bends the way the tube bent),
centrifugal (the other way), no_bias (straight). For the straight tube, either bend counts as impetus.
Output: runs/vlm/answers.csv (one row per question; re-running asks only the missing ones)
   python stage_vlm.py [--model Qwen/Qwen2.5-VL-72B-Instruct-AWQ] [--items all] [--dry]

How this stage fits in the big run
----------------------------------
The other models in the run either *generate* the future (LTX, Cosmos, Wan: a video we then track) or
*judge* it (V-JEPA: which future surprises it less). A vision-language model (VLM) is the third way of asking
the same question: we simply *ask* it, in words, what the ball will do, and read its answer.

Where the pieces live
---------------------
- The prompt, the 3 answer options, the 3 option orders and the choice of input frames are all defined in
  common.py (VLM_Q, VLM_OPTS, VLM_ORDERS, vlm_frames, vlm_question). They are kept there, not here, so that
  show_inputs.py can display exactly what the model receives.
- The "which way did the tube bend" side used to label an answer comes from common.impetus_side(), which uses
  the same ground truth (meta3d.json: the curving foil's path) as the video scorer (analyze_v2.exit_frame).
- run_stages.sh runs this file with the vLLM virtual environment (/workspace/venv-vlm), not the diffusers one.

Flow of this file
-----------------
1. read the command line, load the 30 tube items
2. read answers.csv if it exists, so questions already answered are skipped (the stage can resume)
3. build one chat message per (item, option order) still missing: 4 images + the question text
4. send them all to the model in one batch (or fake the answers with --dry)
5. turn each raw answer into a letter, then a choice (straight/left/right), then a label
   (impetus / no_bias / centrifugal / invalid), and append one row per question to answers.csv
6. write the DONE marker, so run_stages.sh and a re-run know this stage is finished
"""
# ---------------------------------------------------------------------------------------------------------------
# Imports
#   argparse : command-line options (--model, --items, --dry)
#   base64, io : encode each frame as a PNG inside a "data:" URL, the format vLLM's chat API accepts for images
#   csv : read and append answers.csv
#   os : paths
#   re : find the answer letter (A, B or C) in the model's raw text
#   PIL.Image : turn a numpy frame into a PNG
#   common (as C) : shared helpers for every stage (items, frames, prompt, options, output folder, logging)
# vllm is NOT imported here: it is imported further down only for a real run, so --dry works on a machine
# without a GPU or without vLLM installed.
# ---------------------------------------------------------------------------------------------------------------
import argparse, base64, csv, io, os, re
from PIL import Image
import common as C

# ---------------------------------------------------------------------------------------------------------------
# 1. Command line
#   --model : which Hugging Face model vLLM loads. The default is Qwen2.5-VL 72B quantised to 4 bits with AWQ,
#             which makes the 72-billion-parameter model fit (~40 GB of weights) on one 80 GB GPU.
#             InternVL3-78B-AWQ is a drop-in alternative.
#   --items : "all" (the 30 tube items), or a comma-separated list of substrings of item ids to run a subset,
#             e.g. "--items c90,straight" (see common.items()).
#   --dry   : load no model; every answer is "A". Used by demo_mock_pod.py to rehearse the whole pipeline.
# ---------------------------------------------------------------------------------------------------------------
ap = argparse.ArgumentParser()
ap.add_argument("--model", default="Qwen/Qwen2.5-VL-72B-Instruct-AWQ", help="or OpenGVLab/InternVL3-78B-AWQ")
ap.add_argument("--items", default="all")
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()

# STAGE   : the stage name; it is also the output folder name (runs/vlm/) and the results zip name (results_vlm.zip)
# out     : that folder, created if needed (C.outdir)
# ITEMS   : {item_id: metadata dict} for the 3D tube items, sorted by id. Each metadata dict holds the item's
#           folder, its videos, the true ball path, the curving foil's path, the exit frame, the fps, and
#           params (shape: c90 / c180 / c270 / spiral / straight, speed, seed).
# CSV     : the output file, one row per question asked
STAGE = "vlm"; out = C.outdir(STAGE); ITEMS = C.items(a.items)
CSV = os.path.join(out, "answers.csv")


def uri(arr):
    """Encode one frame (a numpy array, height x width x 3, uint8) as a base64 PNG "data:" URL.
    vLLM's OpenAI-style chat format takes images as {"type": "image_url", "image_url": {"url": ...}}; a data URL
    puts the picture inside the message itself, so no file server or upload is needed. PNG is lossless, so the
    model sees exactly the rendered pixels (no JPEG artefacts around the ball)."""
    b = io.BytesIO(); Image.fromarray(arr).save(b, "PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


# ---------------------------------------------------------------------------------------------------------------
# 2. Resume: which questions are already answered?
# A question is identified by (item_id, order index). If answers.csv already exists (the stage was stopped by its
# time limit, the pod restarted, ...), those pairs are read into `have` and skipped below. csv.DictReader returns
# every field as a string, which is why the order index is compared as str(o) further down.
# ---------------------------------------------------------------------------------------------------------------
have = set()
if os.path.exists(CSV):
    have = {(r["item_id"], r["order"]) for r in csv.DictReader(open(CSV))}

# ---------------------------------------------------------------------------------------------------------------
# 3. Build the questions
# For each item:
#   imgs = C.vlm_frames(m): 4 frames of the item's context clip (what the model is allowed to see; it stops
#          before the ball leaves the tube), at t = -1, -2/3, -1/3 and 0 s before the end of the clip, oldest first.
#          Native size (768 x 512 for the v2 stimuli). Four frames are enough to show the ball's speed and
#          direction in the tube without giving the model a video it might not read as one.
# For each of the 3 option orders in C.VLM_ORDERS:
#     0: A = straight, B = left,     C = right
#     1: A = left,     B = right,    C = straight
#     2: A = right,    B = straight, C = left
#   so each option sits behind each letter exactly once. A model with a letter preference ("always A") then
#   spreads its answers evenly over the three options instead of looking like a bias for one of them, and the
#   agreement across the 3 orders (computed in score_bigrun.py) shows how stable its answer really is.
# Each question becomes one chat conversation with a single user turn:
#   content = [image 1, image 2, image 3, image 4, question text]
# The question text (C.vlm_question) is C.VLM_Q with {n} = 4 and the options listed as "A) ...", "B) ...",
# "C) ..." in that order's sequence, ending with "Answer with one letter only."
# jobs holds (item_id, order index, order list, messages) for every question still to ask.
# ---------------------------------------------------------------------------------------------------------------
jobs = []
for iid, m in ITEMS.items():
    imgs = C.vlm_frames(m)                                          # last second, 4 frames
    for o, order in enumerate(C.VLM_ORDERS):
        if (iid, str(o)) in have:
            continue                                                # already answered in an earlier run
        content = [{"type": "image_url", "image_url": {"url": uri(x)}} for x in imgs]
        content.append({"type": "text", "text": C.vlm_question(order, len(imgs))})
        jobs.append((iid, o, order, [{"role": "user", "content": content}]))
C.log(STAGE, f"{len(jobs)} questions to ask ({len(have)} already answered)")

# ---------------------------------------------------------------------------------------------------------------
# 4. Ask the model
# ---------------------------------------------------------------------------------------------------------------
if jobs:
    if a.dry:
        # Rehearsal: no model, every answer is "A". With the rotated orders this gives
        # straight / left / right for orders 0 / 1 / 2, which exercises every branch of the labelling below.
        texts = ["A"] * len(jobs)
    else:
        from vllm import LLM, SamplingParams
        # LLM(...) downloads (first time) and loads the model onto the GPU.
        #   max_model_len=16384 : room for 4 images (Qwen2.5-VL: about 500 tokens each at 768 x 512)
        #                         plus the question; also caps the memory vLLM reserves for its KV cache.
        #   limit_mm_per_prompt={"image": 4} : allow (and reserve memory for) up to 4 images in one prompt.
        #   gpu_memory_utilization=0.92 : let vLLM use 92% of the GPU for weights + cache.
        #   trust_remote_code=True : allow model-specific code from the Hugging Face repo (needed by InternVL).
        llm = LLM(model=a.model, max_model_len=16384, limit_mm_per_prompt={"image": 4}, gpu_memory_utilization=0.92,
                  trust_remote_code=True)
        # llm.chat applies the model's own chat template to every conversation and runs them all as one batch
        # (vLLM schedules them on the GPU together, much faster than one by one).
        #   temperature=0 : greedy decoding, always the most likely token, so the answer is reproducible.
        #   max_tokens=8  : a letter needs 1-2 tokens; 8 leaves room for "A)" or "A." without letting the model
        #                   write an explanation.
        res = llm.chat([j[3] for j in jobs], SamplingParams(temperature=0, max_tokens=8))
        texts = [r.outputs[0].text for r in res]                    # one raw text answer per question, same order as jobs

    # -----------------------------------------------------------------------------------------------------------
    # 5. Label the answers and append them to answers.csv
    # The file is opened in append mode so earlier answers are kept; the header is written only when the file is new.
    # Columns:
    #   model    : the model id (so files from different models can be pooled)
    #   item_id, shape, speed : which tube item
    #   order    : 0, 1 or 2, the option order used
    #   letter   : the letter found in the answer (A/B/C), or "" if none
    #   choice   : what that letter meant in this order: straight / left / right, or ""
    #   label    : impetus / centrifugal / no_bias / invalid (same vocabulary as the video scorer)
    #   raw      : the model's text, stripped and cut to 80 characters, kept so odd answers can be checked by hand
    # -----------------------------------------------------------------------------------------------------------
    new = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "item_id", "shape", "speed", "order", "letter", "choice", "label", "raw"])
        if new: w.writeheader()
        for (iid, o, order, _), t in zip(jobs, texts):
            # Find the answer letter: upper-case the text, then take the FIRST A, B or C that stands alone as a word
            # (\b = word boundary). "B", "B)", "B.", "The answer is B" all give B; letters inside words are ignored.
            # Caveat: upper-casing means an article "a" ("a straight line") would also read as A; with max_tokens=8
            # and "Answer with one letter only" this is unlikely, and `raw` keeps the text to check.
            m = ITEMS[iid]; mt = re.search(r"\b([ABC])\b", t.strip().upper())
            # Undo the rotation: the letter's position (A=0, B=1, C=2) indexes into this question's order list.
            # e.g. order 1 = [left, right, straight]: "C" -> index 2 -> "straight".
            choice = order["ABC".index(mt.group(1))] if mt else ""
            # Map the choice to the study's labels:
            #   no letter found                  -> invalid
            #   "straight"                       -> no_bias     (correct physics: the ball goes straight on)
            #   any bend after a STRAIGHT tube   -> impetus     (there is no tube curvature to compare with, so
            #                                                    either side counts as "curving")
            #   bend towards the tube's side     -> impetus     (keeps curving the way the tube bent: the classic
            #                                                    human "curvilinear impetus" error)
            #   bend away from the tube's side   -> centrifugal (bends outward)
            # C.impetus_side(m) returns "left" or "right": the side the tube was turning at its exit, as seen in
            # the ball's direction of travel, read from the rendered curving foil (same rule as the video scorer).
            # NOTE (code review, Nov 2026): the video scorer counts only ONE side as "curving" for the straight
            # tube (the side of its foil), while this line counts BOTH. A model answering at random therefore
            # scores 33% "curving" on curved tubes but 67% on the straight control, so the VLM's straight
            # column is not comparable with the video models'. Left unchanged here, as the overnight run used it;
            # report left/right separately, or compare with C.impetus_side(m) as for curved tubes, to fix it.
            if not choice: label = "invalid"
            elif choice == "straight": label = "no_bias"
            elif m["params"]["shape"] == "straight": label = "impetus"         # any bend after a straight tube
            else: label = "impetus" if choice == C.impetus_side(m) else "centrifugal"
            w.writerow(dict(model=a.model, item_id=iid, shape=m["params"]["shape"], speed=m["params"]["speed"], order=o,
                            letter=mt.group(1) if mt else "", choice=choice, label=label, raw=t.strip()[:80]))

# ---------------------------------------------------------------------------------------------------------------
# 6. Mark the stage as finished
# C.done writes runs/vlm/DONE (with the model name and whether it was a dry run). run_stages.sh skips a stage that
# has DONE, and zips runs/vlm/ into results_vlm.zip for the local watcher to download. The summary of these answers
# (percentages per tube shape, and how often the 3 option orders agree) is computed later, locally, by
# score_bigrun.py (vlm_summary).
# ---------------------------------------------------------------------------------------------------------------
C.done(STAGE, dict(model=a.model, dry=a.dry))
