# Stimulus generator

Makes the 92 stimuli of the budget plan (`../docs/paper-plan.md`, section 6) as small 2D clips with exact physics. Runs on any computer with Python; no GPU needed. The full set takes about 10 minutes, and the demo set about 1 minute.

Already generated, so you can skip running it:
- `demo/`: 11 example items. Open `demo/index.html` in a browser to see every clip and image.
- `stimuli-full.zip`: all 92 items (12 MB).
- `demo-preview.png`: one row per demo item showing the real path (a strobe of the clip), the physically wrong path, the 4-option static task, and the last frame of the occluded clip.

## Run it yourself

1. Install Python 3.9 or newer (python.org; on Windows tick "Add Python to PATH").
2. Open a terminal in this folder and install the four libraries:
   ```
   python -m pip install -r requirements.txt
   ```
3. Generate:
   ```
   python stimgen.py --demo            # 11 items into ./stimuli
   python stimgen.py                   # all 92 items into ./stimuli
   python stimgen.py --families A1,C1  # only some families
   python stimgen.py --out mydir       # another output folder
   ```
4. Open `stimuli/index.html` in a browser to check them.

On macOS or Linux, use `python3` where this says `python`.

## What you get per item

Each item has its own folder, `stimuli/<family>/<item_id>/`:

| File | Used for |
|---|---|
| `full.mp4` | Ground truth: the whole event with correct physics |
| `context.mp4` | Model input, "short clip" condition: the motion up to just before the critical moment, with nothing after it shown. Tube (A1): stops one frame before the ball reaches the mouth, with the whole ball still inside. String, pendulum, trolley: stops at the last frame with the string, rod or clamp still attached |
| `still.png` | Model input, "single frame" condition: the last frame of `context.mp4` |
| `anomalous_*.mp4` | The same event with a human-style error: the path keeps curving (`impetus`), the ball falls straight down (`straight_down`), or the pendulum runs 1.2× too slow or too fast (`slow`, `fast`). Used for 2AFC "which looks natural?" trials and for model likelihood scoring |
| `occluded.mp4` + `occluded_last.png` | Human prediction task: the ball goes behind a grey screen and the clip stops while it is hidden. Participants click where it will come out, or press a key when it comes out (pendulum) |
| `options.png` | Human static task: 4 dashed candidate paths labelled A to D, McCloskey style. The letters are shuffled per item |
| `meta.json` | All parameters, the ball position in every frame, the critical frame, the correct option letter, where and when the ball comes out of the occluder, and the paths of all 4 options |
| `ensemble_bob2_xy.npy` | Double pendulum only: 50 "noisy Newton" continuations (start angles jittered by 1°) for the chaos analysis |

`index.csv` lists all items with their parameters and correct answers.

## The families

| Family | Event | Factors | Items |
|---|---|---|---|
| A1 | Ball leaves a tube (seen from above) | straight, 90°, 180°, 270°, spiral × 2 speeds × 3 seeds | 30 |
| A2 | Ball whirled on a string; the string snaps | 4 release angles × 3 seeds | 12 |
| A3 | Pendulum string is cut | at the turning point, descending, at the bottom, ascending × 3 seeds | 12 |
| B1 | Ball dropped from a trolley moving along a rail | 4 speeds (incl. stopped) × 3 seeds | 12 |
| C1 | Simple pendulum | 5 lengths × small or big bob × 2 seeds | 20 |
| D1 | Double pendulum | low (regular) or high (chaotic) energy × 3 starts | 6 |

Seeds change the turning direction, the swing side or small details such as the radius, so the same answer is never in the same place.

## Conventions

- 480 × 320 px, 16 frames per second, H.264 MP4.
- Coordinates are in pixels with y pointing down; 100 px = 1 m, so gravity is 981 px/s².
- The tracked ball is always pure red (RGB 230, 30, 30), and the first bob of the double pendulum is blue, so a colour threshold finds them.
- No air resistance and no damping. A ball that reaches the floor stops there.
- I checked these numbers against the physics: the measured pendulum period matches the exact formula (2.030 s vs 2.0302 s for L = 100 px), and the trolley ball lands where the parabola says (260.0 vs 259.9 px).

## 3D versions (Blender)

`make3d.py` makes realistic-looking 3D versions of the stimuli for the models: a shaded ball, a wooden table or a room with a floor, metal rails and rods, a trolley, soft shadows and a perspective camera. The ball follows exactly the same positions frame by frame as in the 2D clip, so the physics, timing and correct answers are identical; only the look changes. By default it does the four families the plan suggests (A1, A3, B1, C1); add `--families A1,A2,A3,B1,C1,D1` for all six. Humans keep the 2D versions, so there are no 3D occluder or options images.

1. Install Blender (free, blender.org). I tested with Blender 5.2; 4.2 or newer should work. You don't need to open it.
2. Generate the 2D stimuli first with this version of `stimgen.py` (the 3D script needs the scene layout it now saves in each `meta.json`).
3. Check the look in about a minute: `python make3d.py --preview` (one still per item in `stimuli3d/`).
4. Render everything: `python make3d.py`

Per item you get `full.mp4`, `context.mp4`, `still.png`, `anomalous_*.mp4` and `meta3d.json`. The 3D camera has perspective, so ball positions in pixels differ from the 2D clip; `meta3d.json` stores the ball's pixel position in every frame of every version (`full_ball_xy_px`, ...), so you can score the models without a tracker.

**Time.** In my sandbox (4 CPU cores, no graphics card) one frame took about 2.3 s, so the default set (74 items, about 8,300 frames including the anomalous versions) would take about 5 to 6 hours on a similar computer. To go faster: `--samples 8` (about twice as fast, slightly grainier), `--engine eevee` (much faster if your computer has a decent graphics card), or `--items` to render a subset. It can run overnight; if you stop it, rerun with `--items` for what is missing.

Blender is started for you; if it isn't found automatically, pass its location with `--blender`, for example `--blender "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"` on Windows or `--blender /Applications/Blender.app/Contents/MacOS/Blender` on a Mac.

## Changing things

Everything is at the top of each family class in `stimgen.py`: lengths, speeds, tube shapes, occluder positions, colours, frame rate (`FPS`) and size (`W`, `H`). Most video models want a specific size and frame count (for example LTX-Video wants frame counts of 8n+1). The scene positions are written for 480 × 320, so don't change `W` and `H`; resize the finished videos for each model instead (for example with ffmpeg). `FPS` can be changed safely. Keep the human and model versions of each item identical apart from size.
