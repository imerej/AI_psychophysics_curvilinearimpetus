# Experiments: do models keep curving after a tube?

("Slide 21" is the curved-tube study in our course study plan; the name stuck in file names.)

The first real AI run for slide 21 (A1 curved tube, humans vs AI), kept small enough to finish in one afternoon on a free Kaggle GPU.

## What it runs
| Model | Kind | What it does here | Size of the run |
|---|---|---|---|
| V-JEPA 2 (ViT-L) | world model, judge | Surprise on the correct (straight) vs the curving continuation, after a still or after a clip | 30 items × 2 modes × 2 continuations, a few minutes |
| LTX-Video 0.9.5 (2B) | video generator | Continues each item from the still, or from the last 9 frames of the clip, for 2 s | 30 items × 2 modes × `SAMPLES` (2) = 120 clips |

Every clip and still stops one frame before the ball reaches the tube mouth (whole ball still inside), for the models and the human test alike, so nothing after the exit is shown.

Items: 5 tube shapes (straight, 90°, 180°, 270°, spiral) × 2 speeds × 3 seeds, from `stimgen` A1. The straight tube gets a curving continuation too (curvature 1/120 px), so V-JEPA has a pair for it.

## Steps
1. On kaggle.com: **Datasets → New dataset**, zip `inputs/` and `analyze.py` from this folder (`zip -r slide21-test.zip inputs analyze.py`), upload the zip and name the dataset `slide21-test`.
2. **Code → New notebook → File → Import notebook**, pick `slide21_kaggle.ipynb`.
3. Right panel: **Add Input** → your `slide21-test` dataset; **Settings → Accelerator → GPU T4 x2**; **Internet on** (needs a phone-verified account).
4. **Run all.** It first makes one test clip and shows it (`check_first_clip.png`), then the rest. Outputs are saved as they go, so if the session stops, run again and it carries on.
5. Download `slide21_results.zip` from the Output panel and unzip it into a results folder for plotting.

## How a clip is scored (`analyze.py`, fixed before seeing any output)
- Track the red ball after the exit (colour threshold).
- Heading of the late path vs the exit tangent: > +5° towards the side the tube bent = **impetus (keeps curving)**, < −5° = **centrifugal**, else **no bias**.
- **Invalid**: ball found in fewer than 4 frames after the exit, or moved less than 30 px; reported per model, not hidden.
- V-JEPA: an item counts as "expects curving" when the curving continuation is less surprising than the straight one.
- Checked on known paths: the real continuations score 0% curving (bends within ±0.2°), the curving ones 100% (12–58°).

## Humans
Browser experiments for people: a replication of McCloskey & Kohl (1983) Experiment 2 with our A1 spiral (`human/experiment.html`), and the older draw + which-looks-natural test on all 30 items (`human/experiment_draw_judge.html`). See [human/README.md](human/README.md).

## Untested parts
The model-loading code follows the diffusers and transformers documentation; the notebook checks itself where it can (blank clip → reloads in float32; V-JEPA predictor call → falls back to a frozen-future version and prints which method it used).
