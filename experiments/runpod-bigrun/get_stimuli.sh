#!/bin/bash
# Downloads the 30 v2 tube items (Blender, 768x512, 24 fps, striped ball; 38 MB) that every model in this run
# receives, from the output of the Kaggle render kernel. Needs the kaggle CLI and a Kaggle token.
# (stimuli/A1_3d in this repo is the earlier 480x320, 16 fps render; the LTX 2B and V-JEPA L results use v2.)
set -e; cd "$(dirname "$0")"
kaggle kernels output jrmiii/slide21-render3d-v2-all -p . --file-pattern '^stim3d/.*' --page-size 200
ls stim3d/A1 | wc -l
