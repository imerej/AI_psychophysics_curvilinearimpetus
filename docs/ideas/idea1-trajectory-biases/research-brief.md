# Idea 1: Do world models reproduce human trajectory biases?

Research brief, 2026-10-12. Claims marked *(inferred)* come from my own reading of the search results rather than a direct check.

## 1. Human findings worth replicating

| Bias | Classic paradigm | Key refs | What humans get wrong |
|---|---|---|---|
| **Curvilinear impetus** | Ball exits a curved/spiral tube; draw or choose the exit path | McCloskey, Caramazza & Green 1980 (*Science*); McCloskey 1983 | ~30–50% predict the ball keeps curving after it leaves the tube (correct: straight tangent line) |
| **Rotational impetus** | Ball on a string swung in a circle; string snaps | McCloskey et al. 1980 | People predict a curved path after release |
| **Straight-down belief** | Object dropped from a moving carrier (plane, walking person) | McCloskey, Washburn & Felch 1983 | People predict a vertical fall instead of a forward parabola |
| **Animation helps** | Same problems as dynamic displays; judge natural vs anomalous | Kaiser, Proffitt & Anderson 1985; Kaiser et al. 1992 | Errors drop sharply when people *watch* motion instead of reasoning about it. This is the key moderator for video models. |
| **Representational momentum / gravity bias** | Remembered final position of a moving object | Freyd & Finke 1984; Hubbard 1995, 2005 | Memory is displaced forward along the path and downward (toward gravity) |
| **Projectile shape errors** | Predict parabolic arcs | Hecht & Bertamini 2000 | Trajectories that are too symmetric or "drop off a cliff" |
| **Noisy-Newton account** | Probabilistic simulation explains many judgments | Battaglia, Hamrick & Tenenbaum 2013; Smith & Vul 2013 | Some "biases" are rational noise, not wrong theories. This gives a competing hypothesis for the paper. |

The cleanest pairing is the static vs. dynamic split: humans are biased when they *reason* (drawings, text) and mostly accurate when they *perceive* (animations). That gives you a 2×2 that can tell the hypotheses apart:

- Text/language models (LLMs, VLMs) on drawn/verbal problems: do they show the impetus error like humans?
- Video world models given actual motion: are they accurate like humans' perceptual system, or do they curve?

## 2. Prior AI work (what's been done, where the gap is)

- **Kang et al. 2024/ICML 2025, "How Far is Video Generation from World Model"** ([arXiv 2411.02385](https://arxiv.org/abs/2411.02385), [site](https://phyworld.github.io/)): trained video diffusion models on 2D ball physics. They generalize in-distribution but fail out of distribution and do case-based retrieval (priority: color > size > velocity > shape). This is the closest methodological template: synthetic, controllable, measured trajectories.
- **Physics-IQ, Motamed et al. 2025** ([arXiv 2501.09038](https://arxiv.org/abs/2501.09038), WACV 2026): real-video continuation benchmark (fluids, solids, optics). Physical understanding is poor and unrelated to visual realism. Its evaluation protocol (condition on the first frames, compare the continuation) is reusable.
- **Garrido et al. 2025, V-JEPA intuitive physics** ([arXiv 2502.11831](https://arxiv.org/abs/2502.11831)): violation-of-expectation via prediction-error "surprise". The model shows above-chance object permanence and continuity. This gives you a *non-generative* readout you can apply to curved-vs-straight exits.
- **IntPhys 2** ([arXiv 2506.09849](https://arxiv.org/abs/2506.09849)): models are near chance on harder scenes.
- **"Interpreting Physics in Video World Models"** ([arXiv 2602.07050](https://arxiv.org/pdf/2602.07050)): probing internal physics representations, useful for a mechanistic section.
- Others: Physion (Bear et al. 2021), VideoPhy / PhyGenBench (prompted generation of physical scenes).

**Gap** *(inferred: I searched specifically and found no paper doing this)*: nobody seems to have run the classic McCloskey-style **naive-physics bias paradigms** (curved tube, string release, carrier drop) on video world models, nor compared their *error patterns* (not just accuracy) to human data. Existing benchmarks score right/wrong. This paper would ask whether the errors look human. That framing is the psychophysics contribution.

## 3. Candidate models (open weights, can condition on frames)

| Model | Type | Why include |
|---|---|---|
| **V-JEPA 2** (Meta, 2025) | Latent predictive, not generative | Surprise-based VoE readout; also an action-conditioned variant |
| **NVIDIA Cosmos-Predict2 / 2.5** | Explicit "world foundation model", video2world | Marketed as physics-aware; continuation from frames |
| **Wan 2.1 / 2.2** (Alibaba) | Image/video-to-video diffusion | Strong open I2V baseline |
| **HunyuanVideo (I2V)**, **CogVideoX-I2V**, **LTX-Video**, **Stable Video Diffusion** | Diffusion I2V | Varied scale and architecture, allows a scaling analysis |
| **Kang et al. style small models trained from scratch** | Controlled | Lets you manipulate training data (e.g., add or remove circular motion) and test *why* a bias appears |
| Closed (optional): Veo 3, Sora 2, Genie 3 (if access) | | Frontier comparison only, not central |
| LLMs/VLMs (text or image versions of the problems) | | The "reasoning" arm of the 2×2 |

*(Inferred: check current licenses, frame-conditioning support and GPU needs before committing. Cosmos and Wan 14B need A100/H100-class GPUs; LTX and CogVideoX-2B run on a 24 GB card.)*

## 4. Experimental design sketch

### Stimuli (synthetic, fully parametric)
Render with a physics engine (MuJoCo, PyBullet or Kubric) in a simple, consistent visual style, and add a photoreal variant to test for style effects:
1. **Curved tube exit**: tube curvature (90°, 180°, 270°, spiral), exit speed, viewpoint (top-down vs oblique)
2. **String release**: ball swinging in a circle, release at varying phases
3. **Carrier drop**: object released from a moving cart or plane, carrier speeds
4. **Control conditions**: straight tube, no constraint, and plain projectile arcs, to separate "curving bias" from generic trajectory noise

Each condition shows the context frames up to the moment of exit or release (plus a few frames after it), and then the model predicts the rest.

### Two readouts per model
- **Generative (production task, the analogue of drawing the path)**: sample N≈20–50 continuations per stimulus, track the ball (segmentation like SAM 2 plus a centroid tracker), and fit the post-exit path.
  - Main dependent variable: **signed curvature** of the post-exit path (κ>0 means it keeps bending in the tube's direction). Also deviation angle from the tangent at fixed distance, and the proportion of "impetus-type" trajectories (classify the way McCloskey coded drawings: straight / curved-continuing / other).
- **Discriminative (judgment task, like the animated-display studies)**: show both a correct (straight) and an anomalous (curved) continuation and compare prediction error or likelihood (V-JEPA surprise; diffusion denoising loss as an approximate likelihood). Does the model prefer the curved path?

### Human comparison
Rerun a short online human study on the *same* stimuli (Prolific, ~100 participants). Use a static drawing task plus an animated natural-vs-anomalous judgment. That gives a direct human–model comparison on identical items instead of relying on 1980s numbers. Compare error profiles, not just means: does model curvature scale with tube curvature, speed and viewpoint the way human errors do? (Humans err more on spiral than on single-bend tubes, and less on top-down animated views.)

### Manipulations that make it a paper, not a benchmark
- **Training-data account**: with small from-scratch models, vary the proportion of constrained curved motion in training. If a curving bias emerges from data statistics, that supports a "statistical prior" story (compare Kang et al.'s case-based finding).
- **Scale / model family**: does the bias shrink or grow with scale?
- **Context length**: more post-exit frames should shrink the bias if the model reads velocity from the motion.
- **Reasoning vs perception (the 2×2)**: LLM/VLM on text/diagrams versus video models on motion, mirroring the human static/dynamic dissociation.

### Analysis
Use mixed-effects models (curvature ~ model × tube curvature × speed × viewpoint + (1|stimulus)). Measure human–model alignment as the correlation of item-level error rates, and add a noisy-Newton simulator baseline (Newtonian physics plus perceptual noise) to test whether model errors look like *noise* or like a *wrong theory* (systematic curvature).

## 5. Risks
- **Models may fail for boring reasons** (the ball vanishes, morphs or stops). Score validity first (object persists, gets tracked) and report the bias only on valid samples.
- **Prompt and text conditioning confounds** in text+image models: use empty or neutral prompts and pure frame conditioning where possible.
- **Compute**: sampling ~50 continuations × ~200 stimuli × 6 models is substantial. Start with 2 models (V-JEPA 2 and one diffusion I2V model) as a pilot.

## 6. Suggested pilot (first 2–3 weeks)
1. Render about 40 curved-tube stimuli (4 curvatures × 2 speeds × 5 seeds) plus straight-tube controls.
2. Run Cosmos-Predict2 (or LTX-Video, if GPU-limited) for generation and V-JEPA 2 for surprise.
3. Extract trajectories and compute post-exit curvature.
4. If either model curves systematically above the controls, the idea has legs, and you can scale up to the other paradigms and the human study.

## Key references
- McCloskey, Caramazza & Green (1980). Curvilinear motion in the absence of external forces. *Science* 210.
- McCloskey (1983). Intuitive physics. *Scientific American*.
- Kaiser, Proffitt & Anderson (1985). Judgments of natural and anomalous trajectories in the presence and absence of motion. *JEP:LMC* ([NTRS](https://ntrs.nasa.gov/citations/19860032184)).
- Freyd & Finke (1984); Hubbard (2005). Representational momentum.
- Battaglia, Hamrick & Tenenbaum (2013). Simulation as an engine of physical scene understanding. *PNAS*.
- Kang et al. (2024). How Far is Video Generation from World Model. [arXiv 2411.02385](https://arxiv.org/abs/2411.02385)
- Motamed et al. (2025). Do generative video models understand physical principles? [arXiv 2501.09038](https://arxiv.org/abs/2501.09038)
- Garrido et al. (2025). Intuitive physics understanding emerges from self-supervised pretraining on natural videos. [arXiv 2502.11831](https://arxiv.org/abs/2502.11831)
- Bordes et al. (2025). IntPhys 2. [arXiv 2506.09849](https://arxiv.org/abs/2506.09849)
- Interpreting Physics in Video World Models (2026). [arXiv 2602.07050](https://arxiv.org/abs/2602.07050)
