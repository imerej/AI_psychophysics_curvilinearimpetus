# Slide 21, v2 full run (night of 26 to 27 Oct 2026)

Stimuli: 30 A1 items re-rendered in Blender (768x512, 24 fps, 28 px striped ball rolling without slipping), Kaggle kernel `slide21-render3d-v2-all`.
Model: LTX-Video 0.9.5 (2B) on 2 T4s, clip mode (last 33 frames before the exit), 81 frames, 40 steps, 6 samples per item. Kernel `slide21-gen-v2-all`.

## Result (after both quality checks, 144 of 180 clips kept)

| Tube | Kept | Keeps curving | Straight | Bends outward |
|---|---|---|---|---|
| 90° | 32/36 | 62% | 25% | 12% |
| 180° | 30/36 | 70% | 17% | 13% |
| 270° | 31/36 | 77% | 13% | 10% |
| Spiral | 27/36 | 59% | 22% | 19% |
| Straight (control) | 24/36 | 4% | 96% | 0% |

Curved tubes: 81 of 120 keep curving (68%), against 1 of 24 on the straight control. Fisher exact, one-sided, p ≈ 4e-9.
By speed: 64% at 120 px/s, 72% at 200 px/s.
Tracker check only (no scene check): 91 of 133 (68%) against 2 of 30 (7%).

V-JEPA 2 (vitl-fpc64-256), first readout (whole frame): from a clip it prefers the curving future on 5 of 24 curved items and on 4 of 6 straight controls, with gaps under 2%.

V-JEPA 2, careful readout (`vjepa2/vjepa_probe.py`, `vjepa2/vjepa_probe.csv`): surprise on the ball patches, 512 px crop around the exit at 12 fps. The curving future is more surprising than the true one on 27 of 30 items (median +1.8%); on curved tubes it prefers the curving future on 2 of 24. No impetus bias. Calibration: a ball that stops dead is more surprising (30 of 30 on the whole future, +3.7%), but a ball that vanishes or rolls back scores as less surprising, so the L1 surprise measures predictability and is only safe between futures with the same content.

## Files
- `per_clip.csv`: tracker labels and paths for the 180 clips.
- `scene.csv`: second check (`scene_check.py`): changed pixels away from the ball, in ball areas (90th percentile over frames), and the number of frames with two ball-sized red blobs.
- `per_clip_strict.csv`, `summary_strict.csv`: labels after both checks (dropped if changed > 0.5 or two-ball frames >= 5).
- `summary.csv`, `vjepa.csv`: as written by the Kaggle notebook.
- `sheets/`: one contact sheet per item (real future, 6 samples, every tracked path).

## Not done
- Cosmos-Predict2 was not run: too heavy for a T4, and its license does not allow turning the guardrail off.
- LTX-Video 13B (0.9.7-dev) needs an A100: `../gen_v2_A100_colab.ipynb` is ready (not tested), with `stim3d_v2.zip` from the render kernel.
