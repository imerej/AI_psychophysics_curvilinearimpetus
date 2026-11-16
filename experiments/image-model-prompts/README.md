# Image and closed video models (run by hand)

Closed models with no open API access in our budget (Gemini image editing, Veo 3.1) are tested by hand with the same spiral item, `A1_tube_spiral_v120_s1`.

## Files
| File | What it is |
|---|---|
| `spiral_v120_s1_frame1_earlier.png`, `spiral_v120_s1_frame2_later.png` | Realistic render: two frames 0.5 s apart, the second being the last frame before the exit |
| `spiral_v120_s1_*_mirrored.png` | The same, re-rendered with the spiral mirrored on the table (a curving answer would bend *upwards*) |
| `spiral_2d_v120_s1_*.png` | The flat 2D version of the same item (grey tube outline, red dot), plain and mirrored |

The realistic unmirrored still is `../../stimuli/A1_3d/A1_tube_spiral_v120_s1/still.png`.

## Image editing (e.g. Gemini): one still
Upload the still in a new chat, three times per image:

> This image is a frame from a simple top-view animation. A red ball is rolling quickly through a tube (drawn as two grey lines) and is exiting the tube through its open end. Edit this image: keep the ball where it is, and add three more copies of the same ball showing where it will be at three consecutive moments after this frame, equally spaced in time (about half a second apart). Change nothing else: same drawing style, same scene, same ball size, same image size.

## Image editing: two frames
Upload `frame1_earlier` then `frame2_later`:

> The two images are frames from the same simple top-view animation, taken half a second apart: the first image is earlier, the second image is later. A red ball is rolling quickly through a tube (drawn as two grey lines) and is exiting the tube. Edit the second image: keep the ball where it is, and add three more copies of the same ball showing where it will be 0.5 seconds, 1 second and 1.5 seconds after the second image. Change nothing else: same drawing style, same scene, same ball size, same image size.

For the realistic renders, describe the scene as a metal tube on a table instead of a 2D drawing.

## Video (e.g. Veo 3.1): image-to-video from one start frame
No end frame (it would give the answer away), shortest length, 3 runs per start frame:

> A glossy red ball is rolling quickly through a metal tube lying on a table, filmed by a static camera looking down at the table at about 45 degrees. The ball is exiting the tube: it rolls out of the open end of the tube and keeps rolling. Do not change the tube: it stays exactly as it is and does not move. Realistic, smooth continuous motion, static camera, the ball keeps its size, shape and colour.

Each output is tracked and scored with the same keeps-curving / straight / outward rule as the open models (`../analyze.py`).
