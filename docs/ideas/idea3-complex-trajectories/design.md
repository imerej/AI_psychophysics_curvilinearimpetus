# Idea 3: Can world models predict complex trajectories?

Research notes and a proposed design (pendulums, springs, balls in bowls, double pendulums). Written 2026-10-12.

## 1. Bottom line

- **The plain question is already partly answered.** Morpheus (2025) tested pendulum, double pendulum and spring (plus 6 other Newtonian systems) on 10 video generators with real recordings. Best combined score was about 0.66 against about 0.96 for real video, and open models (Wan2.1, Cosmos-Predict2) were as good as or better than Veo3 and Kling. A paper that only asks "can they predict a pendulum?" will read as a replication.
- **The open gap is the psychophysics.** None of the benchmarks below (a) vary physical parameters parametrically to get psychometric-style functions (predicted period vs. true period, sensitivity to irrelevant variables like mass), (b) run humans on the *same* stimuli and compare error patterns, or (c) treat chaos properly, i.e. ask whether the *spread* of a model's samples matches the physical uncertainty in the double pendulum, rather than scoring against one ground-truth trajectory.
- **Recommended framing:** "Psychophysics of oscillation and chaos in video world models": measure laws (T ∝ √L, T ∝ √(m/k), mass invariance, energy conservation), discrimination thresholds, and predictability horizons, in models and humans, with matched stimuli.

## 2. Prior work worth citing

| Work | What it did | Relevance |
|---|---|---|
| **Morpheus** (arXiv 2504.02918) | 9 real setups incl. pendulum, double pendulum, spring; SAM-2 tracking, PINN-fit "dynamical score", energy/period invariance score; models: Veo3, Kling, Wan2.1, Cosmos-Predict1/2, CogVideoX, PyramidalFlow, LTX-Video | Closest prior. Reuse its scoring pipeline; differentiate on parametric design + humans + chaos |
| **Physics-IQ** (Motamed et al., arXiv 2501.09038, WACV 2026) | 66 real scenarios, IoU/MSE metrics normalized to real-vs-real "physical variance"; best model 29.5/100; visual realism uncorrelated with physics | Good idea to borrow: normalize to physical variance |
| **Kang et al., "How far is video generation from world model"** (arXiv 2411.02385) | DiTs trained on Box2D: near-perfect in-distribution, ~10× worse OOD; "case-based" retrieval, priority color > size > velocity > shape | Predicts models will fail to extrapolate parameter scaling laws; motivates OOD parameter levels |
| **WorldBench** (arXiv 2601.21282) | Isolates single concepts; estimates g, viscosity, friction from generated video; Cosmos 1/2/2.5, Wan 2.2, Hunyuan, CogVideoX, LTX-2, Kling, Runway | Parameter-estimation scoring is the same logic as recovering period/length |
| **World Models' Last Exam in Physics** (arXiv 2610.08791, Oct 2026) | 40 tasks, task-specific quantitative measurements, 8 models, best 57.8/100 | Very recent; I only read the abstract (full text was rate-limited), so check whether it includes oscillators |
| **Garrido et al., V-JEPA intuitive physics** (arXiv 2502.11831) | Violation-of-expectation via prediction "surprise" on IntPhys, GRASP, InfLevel | Template for testing latent (non-pixel) world models |
| **T2VPhysBench, VideoPhy-2** | Text-to-video physics judged mostly by VLMs/humans | Morpheus showed VLM judges fail on clean physics: avoid VLM scoring |

### Human data

- **Pendulum string-cut / ballistic release:** Caramazza et al. (1981) found that people often draw wrong paths after a pendulum string is cut. Smith, Battaglia & Vul (CogSci 2013, "Consistent physics underlying ballistic motion prediction") showed that *prediction* tasks follow noisy Newtonian physics, while *drawing* tasks show idiosyncratic biases. Smith et al. later argued that physical intuitions differ between tasks, not domains. **Implication:** the human task format matters as much as the stimulus. Use prediction tasks (intercept/occlusion), not drawing.
- **Pendulum period misconceptions:** Many people believe a heavier bob swings faster. This goes back to Inhelder & Piaget's pendulum task, where children fail to isolate length from weight. It is a clean bias to test in models (does a bigger/darker bob change the generated period?) and links to idea 2 (developmental order).
- **Perceived velocity of pendular/gravitational motion:** Lacquaniti's group ("Implied dynamics biases the visual perception of velocity", PLoS ONE 2014, PMC3965519) found that observers' velocity judgments are biased toward gravity-consistent motion. I could not open the full text (captcha), so verify the details before citing.
- **Curved-path (impetus) errors:** McCloskey's ball-exiting-a-curved-tube work. "Ball in a bowl" and "ball leaving a curved track" stimuli overlap with idea 1, so the two ideas can share stimuli.
- **Noisy Newton** (Battaglia, Hamrick & Tenenbaum 2013; Smith & Vul 2013): human prediction ≈ physics simulation + perceptual noise. This gives a principled *ideal observer* for each stimulus, and it is the key to the chaos analysis below.

## 3. Proposed design

### Systems and manipulated parameters

| System | Manipulated | Law / signature to test | Irrelevant cue (bias probe) |
|---|---|---|---|
| Simple pendulum | length L (4–6 levels), amplitude θ₀ (small → large), damping | T ∝ √L; small-angle isochrony vs. large-angle lengthening; energy (turning-point height) | bob mass/size/colour |
| Mass–spring (vertical) | k (spring thickness/coils), m | T ∝ √(m/k); equilibrium shift with m | colour, bob shape |
| Ball in bowl | bowl curvature radius, release height | period ∝ √R; amplitude decay | ball size |
| Pendulum string-cut | cut phase (angle, velocity) | parabolic flight from tangent velocity (classic human error) | none |
| Double pendulum | total energy: low (quasi-periodic, normal modes) → high (chaotic) | predictability horizon vs. Lyapunov time; ensemble spread | colour |

Include **in-range and out-of-range** parameter levels (e.g. very long/short pendulums) to test Kang-style case-based failure.

### Stimuli

- **Generator:** integrate the ODEs exactly (scipy, or MuJoCo for the bowl/contacts) and render in two styles: (1) **minimal 2D** (high-contrast coloured bob on a plain background, so tracking is trivial and humans and models see the same thing), and (2) **rendered 3D** with Blender/Kubric (realistic lab scene, closer to the models' training distribution). Optionally add a small set of **real recordings** to anchor the realism axis (Morpheus/Physics-IQ style).
- **Format:** match model input (e.g. 16–24 fps, 480–720p, ~5 s outputs). Keep periods at 1–4 s so a 5 s output holds 1–4 cycles and there is no temporal aliasing.
- **Context:** condition on a *multi-frame* clip, not a single frame, because one frame cannot specify velocity or time scale. Vary context length (e.g. ¼, ½, 1 full period) as a factor: how much observation does a model need to lock onto the right period?
- **Prompt:** a fixed neutral text prompt ("a pendulum swinging, static camera"), plus a prompt-free condition where supported, so text priors are not doing the work.
- **Rough size:** 5 systems × ~6 parameter levels × 2 irrelevant-cue levels × 3 context lengths × 2 visual styles ≈ 700 conditions; × 4 samples per model ≈ 2,800 videos per model. A pilot with pendulum + spring only is about 10× smaller.

### Models (open weights first)

- **Pixel-generating, video-conditioned:** Cosmos-Predict2 / 2.5 Video2World (native multi-frame conditioning, built as a "world model"), Wan 2.1/2.2 (I2V; multi-frame via VACE or first/last frame), HunyuanVideo-I2V, CogVideoX-I2V, LTX-Video (multi-frame conditioning). Wan2.1 and Cosmos-Predict2 were the strongest open models in Morpheus.
- **Latent predictive (no pixels):** V-JEPA 2. Score it by surprise (prediction error in latent space) on correct vs. perturbed continuations, as in Garrido et al.
- **Optional closed reference:** Veo 3, Kling, Sora 2 via API, if budget allows.
- **Sanity baselines:** ground-truth physics; physics + perceptual noise (noisy-Newton ideal observer); a "copy last cycle" heuristic.

### Scoring

1. **Trajectory extraction:** colour thresholding on minimal stimuli; SAM-2 on 3D/real, as in Morpheus. Convert to angle θ(t) (or displacement x(t)).
2. **Fit a damped sinusoid** per generated video to get period, amplitude decay and phase. The main dependent variables are *predicted period vs. true period* (slope and intercept, log–log; a slope of 0.5 vs. L is the √L law) and *effect of irrelevant cues* (mass/colour should have zero effect).
3. **Invariants:** turning-point height/energy drift (Morpheus "physical invariance"); spring equilibrium position.
4. **Discard rate:** frozen motion, vanished or duplicated objects. Report it as a result, not just a filter (Morpheus saw >45% static videos for some models).
5. **Chaos (double pendulum):** (a) time until the prediction diverges past a threshold from ground truth, compared with the Lyapunov-limited horizon; (b) generate many samples per stimulus and compare the model's sample distribution to a physics ensemble whose initial conditions are jittered by perceptual noise (≈1–2°). Use CRPS / energy score and spread–skill calibration. The question becomes whether the model is *over-confident, under-confident or calibrated* about chaos, which is new.
6. **V-JEPA 2 psychometric curve:** surprise as a function of perturbation size (e.g. period scaled by 0.8–1.25, energy injected, mass-dependent period), then threshold extraction. The same 2AFC can run in humans, so the two thresholds are directly comparable.

### Human experiment (online, e.g. Prolific)

- **Occlusion prediction:** the bob swings behind an occluder; participants press a key when it will reappear (timing) or click where it lands (string-cut). Same stimuli and context lengths as the models.
- **2AFC naturalness:** which of two continuations is physically right (period/energy perturbations) gives JNDs that compare to the V-JEPA thresholds.
- **Size:** about 40–60 participants, about 30 min each, minimal-style stimuli only.
- **Comparison:** beyond accuracy, compute *error consistency* across conditions (per-condition bias correlations; Geirhos-style κ), and test whether models share human biases (mass belief, string-cut errors) or show different, non-human ones.

### Hypotheses

- **H1:** models produce oscillation-like motion but under-scale period with L, k and R (slope < 0.5 in log–log), and are much worse out of range (case-based behaviour).
- **H2:** irrelevant visual cues (bob size/darkness) shift the generated period, which would be a model analogue of the "heavier swings faster" belief.
- **H3:** energy is not conserved; amplitude drifts up or down without damping.
- **H4:** on the double pendulum, models diverge before the physical predictability horizon and their sample spread is miscalibrated (likely over-confident, regressing to periodic-looking motion).
- **H5:** humans are near noisy-Newton on prediction tasks; model–human error consistency is low.

## 4. Feasibility and risks

- **Compute:** a 2B Cosmos model runs on one 24–48 GB GPU; Wan2.1-14B I2V needs about 80 GB (or offloading). At roughly 1–4 min per 5 s video on an A100/H100, 2,800 videos per model is about 50–150 GPU-hours. The pilot (pendulum + spring, two models) fits in a few days on one GPU.
- **Single-frame models cannot see velocity.** Use multi-frame conditioning wherever possible, and report single-frame as a separate, weaker condition.
- **Static or broken generations** are common; pre-register the discard criteria.
- **Novelty risk:** Morpheus and the brand-new "World Models' Last Exam in Physics" overlap. The parametric/psychometric design, human matching and chaos calibration are what make the paper different; lead with them.
- **Synergy:** string-cut and ball-in-bowl stimuli serve idea 1 (curved-trajectory biases). Comparing Cosmos/V-JEPA checkpoints on the √L law serves idea 2 (learning order, cf. Piaget's pendulum task).

## 5. Suggested pilot (first 1–2 weeks)

1. Minimal 2D pendulum + spring generator (scipy + matplotlib/pygame), 6 lengths × 2 bob sizes × 3 context lengths.
2. Run Cosmos-Predict2-2B Video2World and Wan2.1 I2V, 4 samples each.
3. Colour-track, fit period, and plot predicted vs. true period (log–log). If the slope is clearly off 0.5 or bob size matters, the paper has its first result.

## Sources

- Morpheus: https://arxiv.org/html/2504.02918
- Physics-IQ: https://arxiv.org/html/2501.09038v3
- Kang et al.: https://arxiv.org/html/2411.02385v2
- WorldBench: https://arxiv.org/html/2601.21282
- World Models' Last Exam in Physics: https://www.alphaxiv.org/abs/2610.08791 (abstract only)
- Garrido et al., V-JEPA intuitive physics: https://arxiv.org/html/2502.11831v1
- V-JEPA 2: https://ai.meta.com/blog/v-jepa-2-world-model-benchmarks/
- Cosmos-Predict2.5: https://research.nvidia.com/labs/cosmos-lab/cosmos-predict2.5
- T2VPhysBench: https://arxiv.org/html/2505.00337v1 · VideoPhy-2: https://arxiv.org/html/2503.06800v1
- Smith, Battaglia & Vul 2013: https://www.mit.edu/~k2smith/publication/pendulums/
- Different physical intuitions between tasks: https://www.mit.edu/~k2smith/publication/diff_phys_intuitions
- Kubricht, Holyoak & Lu 2017, TICS review: https://reasoninglab.psych.ucla.edu/wp-content/uploads/sites/273/2021/04/Kubrich_etal.TICS_.2017.pdf
- Implied dynamics and velocity perception: https://pmc.ncbi.nlm.nih.gov/articles/PMC3965519 (not read, captcha)
