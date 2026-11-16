# Human tests for slide 21

## Main version: McCloskey & Kohl (1983) replication (`experiment.html`)

`experiment.html` reruns their Experiment 2 (spiral tube) as closely as a browser allows, with our A1 spiral tube (`A1_tube_spiral_v200_s1`, the same tube, ball and speed the models get). Double-click it; it needs no internet. English or French is picked on the first screen.

### What is the same as their study
- **One problem, one answer per person**, two between-subject conditions:
  - **No motion:** diagram + description, then the person chooses one of six paths.
  - **Trajectories:** the same, but first each of the six paths is shown as a moving ball (ball through the transparent tube at constant speed, out along the path to the edge of the field, then a still picture of tube + path). All six are shown once, then each once more, in a new random order per person.
- **Their problem text, word for word** (French translation provided), plus a check that the person understood the tube is seen from above, as they made sure of.
- **Six alternatives as in their Fig. 3:** A straight (correct); B, C, D curvilinear impetus (gentle, strong, keeps following the spiral); E, F other (bends outward, outward-then-back S).
- **Answer on six cards**, each showing tube + one path, laid out in a new random order per person.
- **Sizes:** a card calibration makes the spiral 5.5 cm wide inside a 15 × 15 cm field, viewed from about 45 cm, as on their screen.
- **Sample:** they ran 36 per condition, 12 with no physics, 12 high school, 12 university (6 women, 6 men each).

### What differs, and why
- Our spiral has 1.1 turns (theirs about 2), and its ball is a bit larger (0.10 of the spiral width vs 0.07). Both come from keeping the exact A1 tube the models see.
- The ball moves at 8 cm/s at this size (theirs 12.2 cm/s), again the A1 speed. Display is 48 frames/s (theirs 50).
- Their figure gives no numbers for paths B to F, so ours are drawn after it: B turns 50°, C 140°, D follows the spiral another 0.6 turn then goes straight, E bends 35° outward, F bends out 25° and back.
- The person starts each animation (Start button or space bar) instead of the experimenter pressing a key, and reads the text on screen instead of being read to.
- If the screen is too small for a 15 cm field, the field shrinks; the CSV records the size actually shown (`field_cm_shown`).

### Running it
1. Enter the participant number, physics level, age and gender. With **Automatic**, odd numbers get *no motion* and even numbers *trajectories*, so number people 1, 2, 3, … within each physics level.
2. The participant does the rest. At the end the browser downloads `mk_spiral_p<number>_<condition>.csv` (a copy is kept in the browser's storage too).

### Scoring against their Table 2
Put the CSVs in `human/data/`, then:
```
python score_mk.py
```
It prints correct / curvilinear / other per condition and per physics level next to their numbers (no motion 24 / 9 / 3, trajectories 23 / 10 / 3), a χ² of ours vs theirs, and no motion vs trajectories (it reproduces their χ²(2) = .07 from their counts). It writes `data/mk_summary.csv` and `data/mk_summary.png`.

Tested with four simulated participants (both conditions, both languages, one wrong top-view answer): every screen worked, the CSVs were complete, and the scorer read them.

### Changing the stimuli
`python build_mk_experiment.py` rebuilds `experiment.html` from `mk_template.html` (paths: `HEADINGS` and `D_EXTRA_TURNS` at the top).

## Older version: draw + which looks natural (`experiment_draw_judge.html`)

`experiment_draw_judge.html` runs the same 30 tube items the models get, redrawn exactly (480 × 320 px, 16 fps, same tube outlines and ball paths), in a browser. It needs no internet or install: double-click it. It works with a mouse, a trackpad or a finger on a tablet.

### What a participant does (about 12 minutes)
1. **Start screen:** participant number (from you), age, physics training (none / high school / university, as in McCloskey), gender (optional).
2. **Part 1, draw (30 trials, like the video generator):** the ball goes through a tube, then the participant draws the path after the exit, starting on the ball. Half of the tubes are shown as the moving **clip**, half as a **still** picture. Both stop one frame before the ball reaches the tube mouth (whole ball still inside), exactly like the model inputs, so nothing after the exit is shown. Clip trials can be replayed.
3. **Part 2, which looks natural (30 trials, like V-JEPA 2):** each tube plays twice, once with the correct straight exit and once with the curving one (the same two continuations V-JEPA scores), in random order. The participant picks the one that moves like a real ball. Each tube keeps the input mode it had in part 1.
4. At the end, the browser downloads `slide21_humans_p<number>_<date>.csv`. A copy is also kept in the browser's local storage as a backup.

Drawing comes before judging so that seeing the correct path doesn't teach the drawing answer.

### Counterbalancing
- Still vs clip per tube is set by the participant number. Odd and even numbers get the opposite assignment, and every tube shape gets 3 still and 3 clip trials. **Number your participants 1, 2, 3, … so half get each assignment.**
- Trial order and which version is shown first are shuffled, with the participant number as the seed, so a number always gives the same session.

### Scoring (same rules as the AI)
Put every CSV in `human/data/`, then from the `experiments/` folder:
```
python analyze.py --inputs inputs --humans human/data --gen out/ltx --vjepa out/vjepa.csv --out results
```
- Drawn paths go through the same `classify()` as the tracked model paths: a heading change of more than 5° towards the tube's side counts as **impetus**, more than 5° the other way as **centrifugal**, anything else as **no bias**.
- In part 2, choosing the curving version counts like V-JEPA finding the curving version less surprising.
- `results/slide21_humans_vs_ai.png` puts your participants, both models and the published human points on one plot.

Checked end to end with a simulated participant who curved every drawing after a still and drew straight after a clip: the drawings scored 100% and 0% curving, as they should.

### Changing the stimuli
After regenerating `../inputs`, run `python build_draw_judge.py` to rebuild `experiment_draw_judge.html` from `experiment_draw_judge_template.html`.
