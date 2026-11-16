# Slide 21: first AI run on Kaggle (26 Oct 2026)

Notebook: https://www.kaggle.com/code/jrmiii/slide21-ai-test (GPU T4, dataset jrmiii/test-bias, 30 A1 items).
Same notebook as `../slide21_kaggle.ipynb`, plus a dataset-picking fix and a final cell that prints the CSVs.
The zip of generated clips and the plot stay on Kaggle (Output panel).

## Curved tubes only (straight tube = control)
| Model | Mode | Valid | Keeps curving | No bias | Centrifugal |
|---|---|---|---|---|---|
| LTX-Video 2B | clip | 46/48 | 59% | 24% | 17% |
| LTX-Video 2B | still | 21/48 | 67% | 24% | 10% |
| V-JEPA 2 ViT-L | clip | 24/24 | 71% judge curving more natural | | |
| V-JEPA 2 ViT-L | still | 24/24 | 67% | | |

Straight-tube control: LTX clip 9% curving (11 valid), LTX still 1/3 valid; V-JEPA 50% (clip) / 67% (still).
V-JEPA by shape: c90 and c180 100%, c270 33-50%, spiral 33%. Method: context-only encoding + predictor.
LTX still mode: 36/60 clips invalid because the ball stops (model often freezes the image).
Per-shape numbers: `summary.csv`; per clip: `ltx_per_clip.csv`; surprise values: `vjepa.csv`.
