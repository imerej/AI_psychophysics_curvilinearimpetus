# Do world models make human-like physics errors?

Unified paper plan combining idea 1 (naive-physics trajectory biases) and idea 3 (oscillators, chaos, parameter sweeps). Written 2026-10-12. It builds on `ideas/idea1-trajectory-biases/research-brief.md` and `ideas/idea3-complex-trajectories/design.md`; details already written there are referenced rather than repeated. Claims marked *(inferred)* are my own estimates or readings, not checked facts. **Budget version (updated 2026-10-12): own computer plus at most €20 of cloud; see §5.**

## 1. Pitch in one paragraph

Benchmarks score video world models as right or wrong. Cognitive science has 45 years of data on *how* humans are wrong about motion: we think a ball leaving a curved tube keeps curving, that dropped objects fall straight down, that heavier pendulums swing faster, and yet we are close to Newtonian when we *watch* motion instead of reasoning about it. We run the classic paradigms, plus parametric oscillator and chaos stimuli, on open video world models and on humans with identical stimuli. We then classify every model error as **Newtonian**, **noisy-Newton** (unbiased perceptual noise), **human-like bias** (the specific systematic error humans make), or **non-human failure** (case-based retrieval, freezing, regression to stereotyped motion). The headline question is which of these four a model's errors look like, and whether that changes with how much motion the model sees, as it does for humans.

## 2. Literature check (the two open questions from the briefs)

### 2.1 Does "World Models' Last Exam in Physics" cover oscillators?

**Partially verified, and probably not a threat.** From the arXiv abstract page, Hugging Face and alphaXiv ([arXiv 2610.08791](https://arxiv.org/abs/2610.08791)): 40 tasks across six categories (mechanics, optics, fluids, thermal/phase change, electromagnetism, surface tension); each task is one initial image plus a text prompt plus predefined physical criteria, with no reference videos; 8 models, 1,280 videos; best model Seedance 2.5 at 57.76/100. None of the pages I could read lists the individual tasks or mentions pendulums, springs, oscillators or projectiles. I could not read the full text because arXiv rate-limited the request, so **someone should open the PDF and check the mechanics task list**.

Even if it includes a pendulum, it differs from us on every axis that matters here: single image plus prompt (so no velocity information), pass/fail criteria rather than parametric sweeps, no human data, and no error-pattern analysis.

### 2.2 Has anyone tested naive-physics biases on video models?

**No paper found that does this.** Searches for impetus, curved-tube, carrier-drop and McCloskey paradigms combined with video generation or world models returned nothing (searched 2026-10-12; *inferred* gap, absence of evidence). The closest work, which the paper must cite and position against:

| Work | What it does | How we differ |
|---|---|---|
| **Li et al., ECCV 2026, "Human-Level Accuracy, Non-human Strategies"** ([arXiv 2609.22788](https://arxiv.org/html/2609.22788), [Springer](https://link.springer.com/chapter/10.1007/978-3-032-37132-4_5)) | Physion outcome prediction with V-JEPA 2, VideoMAEv2, DINOv2 vs public human responses. V-JEPA 2 is at 73.2% vs humans 74.2%, but model–human κ ≈ 0.48 vs human–human ≈ 0.91; "non-human strategies". | **Most important new related work.** It already makes the "same accuracy, different errors" point, so our novelty is *which* errors: classic bias paradigms with known human signatures, generative readouts (trajectories, not binary outcomes), parametric laws, and the static-vs-dynamic manipulation. Its result is also a prediction for us (H6). |
| **LikePhys** (Yuan et al. 2025, [arXiv 2510.11512](https://arxiv.org/abs/2510.11512)) | Denoising loss as a likelihood surrogate to make video diffusion models choose between valid and invalid videos; models struggle on chaotic dynamics and improve with scale. | We borrow this as the discriminative readout for diffusion models. |
| **The Invisible Hand of Physics** (Esmati et al. 2026, [arXiv 2606.05328](https://arxiv.org/abs/2606.05328)) | Plausibility is linearly decodable from diffusion transformer states (≈81% on IntPhys/InfLevel), beating V-JEPA. | Supports a "knows more than it shows" contrast: a model may *judge* a straight exit correct but *generate* a curved one, which is a direct analogue of the human static/dynamic dissociation. |
| Kang et al. 2024; Physics-IQ; Morpheus; WorldBench; Garrido et al. (V-JEPA VoE); IntPhys 2; Interpreting Physics in Video World Models | See the two briefs. | Accuracy benchmarks or mechanistic probes, none with bias paradigms or matched human data. |
| LLMs on conceptual physics (e.g. GPT-4 on the Force Concept Inventory; [West 2023](https://arxiv.org/abs/2303.17012), [Kortemeyer 2023](https://arxiv.org/abs/2301.12127)) | Text models answer misconception-laden questions. | Precedent for the "reasoning" arm (VLMs on static diagrams); not the main contribution. |

Worth a later look, not read: "World Models That Know When They Don't Know" ([arXiv 2512.05927](https://arxiv.org/abs/2512.05927)), on calibrated uncertainty in video generation, may matter for the chaos-calibration analysis.

## 3. Framing and contribution

1. **An error taxonomy, not a score.** For each stimulus we have the Newtonian answer, a noisy-Newton ideal-observer distribution, and the documented human bias direction. Every model sample can be placed against all three.
2. **The static vs. dynamic dissociation, transposed to models.** Humans err when reasoning from a still diagram and are much better when watching motion (Kaiser, Proffitt & Anderson 1985). Video models have a natural analogue: **single-frame conditioning** (a still of the ball at the tube exit, so no motion information) vs. **multi-frame conditioning** (the clip leading up to and slightly past the exit). A VLM answering a static multiple-choice diagram completes the "reasoning" corner.
3. **Matched humans on identical items**, giving item-level alignment with a human–human noise ceiling (following Li et al. 2026 and Geirhos-style error consistency).
4. **Chaos as calibration.** On the double pendulum the right answer is a distribution. Are model samples over-confident, calibrated or under-confident relative to physics plus perceptual noise, and how do humans compare?

Working title options: "Do world models make human-like physics errors?" / "Impetus in the machine: naive-physics biases in video world models".

## 4. Hypotheses (pre-registrable)

| # | Hypothesis | Main DV | Competing outcome that would also be interesting |
|---|---|---|---|
| H1 | **Impetus.** Under single-frame conditioning, models continue the tube's curvature after exit (signed curvature > straight-tube control); the bias grows with tube curvature, as in humans (spiral > 90° bend). | Signed post-exit curvature κ; % impetus-type paths | No curvature but non-human failures (ball stops, vanishes): "not wrong like us, just wrong" |
| H2 | **Motion helps models too.** Multi-frame context shrinks the H1 bias, paralleling the human animation advantage. | κ × conditioning interaction | Bias persists with motion, which would mean the prior beats the evidence, unlike humans |
| H3 | **Straight-down / carrier drop.** Objects released from a moving cart get too little forward velocity (vertical or backward-drifting fall). | Horizontal landing error relative to the parabola | — |
| H4 | **Mass–period belief.** Irrelevant bob size or darkness shifts the generated pendulum period (heavier-looks-faster). | Period ratio big/small bob (should be 1.0) | Effect in the opposite direction (bigger = slower, a "sluggish" prior) |
| H5 | **Laws are only approximately learned.** Period scales with √L, √(m/k), √R with slope < 0.5 in log–log; much worse at out-of-range parameter levels (case-based, Kang et al.). | log–log slope; in-range vs OOD error | — |
| H6 | **Alignment.** Item-level model errors correlate with human errors well below the human–human ceiling (cf. κ ≈ 0.48 vs 0.91 in Li et al.), *except* on the classic bias items, where we predict partial alignment because both humans and models learn from the same visual statistics. | Item-level error correlation / κ vs ceiling | Alignment high everywhere, a strong "shared prior" result |
| H7 | **Chaos.** On the high-energy double pendulum, model sample spread is too narrow (over-confident) and drifts toward periodic-looking motion; humans are closer to noisy-Newton. | CRPS, spread–skill ratio, predictability horizon vs Lyapunov time | Models under-confident (samples nearly random) |
| H8 | **Judge vs. generate.** Discriminative readouts (V-JEPA surprise; diffusion likelihood) prefer the correct straight path more often than the generative readout produces it. | Agreement between judgment and generation per item | — |

## 5. Budget rules (own computer + at most €20 of cloud)

This version replaces the earlier full-scale plan (kept in `paper-plan-v1-fullscale.md`). Everything below is sized so that:

- **Your own computer** does stimulus generation, tracking, analysis, writing, and hosts nothing.
- **Kaggle Notebooks (free)** do most GPU work: a 16 GB T4 or P100, 12-hour sessions, roughly 30 GPU-hours per week (the figure users report; Kaggle shows your actual quota in account settings).
- **€20 is a reserve**, not the plan: about 35–40 hours of a rented RTX 4090 on Vast.ai at ≈ $0.53/h (price seen 11 Oct 2026; it moves). Spend it only if the free route is too slow for the second generative model.
- **The human study costs nothing**: a browser experiment on free hosting with volunteer participants.

The scientific design (§3–§4) is unchanged. What shrinks is the number of items, models and samples, and the 3D render style is dropped.

## 6. Stimuli (minimal 2D only)

Exact physics with scipy, rendered with matplotlib or pygame on your computer: a coloured ball on a plain background, 16 fps, 480×320 px, 2–3 s clips (33–49 frames). Small and short keeps generation cheap and makes tracking trivial.

| Family | Paradigm | Factors | Items |
|---|---|---|---|
| A1 | Curved tube exit, top-down | curvature: straight, 90°, 180°, 270°, spiral × 2 exit speeds × 3 seeds | 30 |
| A2 | Ball on a string swung in a circle, string snaps | 4 release phases × 3 seeds | 12 |
| A3 | Pendulum string cut | 4 cut phases × 3 seeds | 12 |
| B1 | Drop from a moving cart | 4 cart speeds (incl. 0) × 3 seeds | 12 |
| C1 | Simple pendulum, mass–period belief and √L law | 5 lengths (1 out of range) × 2 bob sizes × 2 seeds | 20 |
| D1 | Double pendulum (chaos calibration) | 2 energy levels × 3 initial conditions | 6 |
| | **Total** | | **92 items** |

Each item has two conditioning modes: **single frame** at the critical moment, and a **short clip** leading up to it. Springs, the ball in a bowl and the 3D style are cut; they can come back in a follow-up if the pilot works.

## 7. Models (all free or nearly free)

| Model | Role | Where it runs *(inferred; measure in the pilot)* |
|---|---|---|
| **V-JEPA 2 (ViT-L)** | Discriminative only: surprise on correct vs anomalous continuations. Cheapest arm, no video generation needed. | Kaggle T4, minutes to a few hours for all items |
| **LTX-Video 0.9.x, 2B distilled** (the older small release, not LTX-2.5, which needs a 32 GB GPU) | Main generative model; supports image and multi-frame conditioning; very fast | Kaggle T4, order of a minute per clip |
| **Wan 2.2 TI2V-5B** | Second generative model (image-to-video, stronger quality) | ≈ 10 GB in FP16, so it fits a T4 but is slow there; ≈ 9 min per 5 s 720p clip on a 4090 officially, much less at 480p and 2–3 s. Kaggle if patient, the €20 reserve if not |
| **Tiny video model trained from scratch** (Kang et al. style, 64×64 px, tens of millions of parameters) | Tests *where* a bias comes from: train one copy with curved constrained motion in the data and one without, then check whether only the first shows impetus | Kaggle, roughly 10–20 GPU-hours per model *(inferred)*. Optional but the strongest "why" result per euro |
| **One open VLM** (e.g. Qwen2.5-VL-7B) on static diagrams | The "reasoning" corner of the 2×2 | Kaggle T4 in 4-bit, an hour or two |

Cut from the earlier plan: Wan 14B, Cosmos, HunyuanVideo, CogVideoX and all closed API models. Cosmos-Predict2-2B can come back only if a free 24 GB+ GPU turns up.

Baselines (free, run on your computer): ground-truth physics, noisy-Newton observer, "copy last cycle", and an explicit "continue curvature" impetus model.

## 8. Readouts and analysis

**Generative.** 4 samples per item and mode (16 for D1). Track the ball by colour threshold on your computer. Validity screen first (object persists, single object, moves), with the discard rate reported per model as a result. Then:
- A/B: signed curvature after the exit or release; deviation from the tangent; McCloskey-style path classification (straight / curved-continuing / other); landing error vs the parabola.
- C1: damped-sinusoid fit for period and amplitude drift; log–log slope vs L; period ratio big/small bob.
- D1: divergence time vs Lyapunov horizon; CRPS and spread–skill ratio vs the noisy-Newton ensemble (with 16 samples this is coarse, so report it as exploratory).

**Discriminative.** V-JEPA 2 surprise on correct vs anomalous continuations, with graded perturbations for psychometric thresholds. Diffusion likelihood scoring (LikePhys-style) on LTX if time allows; it costs only forward passes.

**Error taxonomy.** For each model × item, compare the samples' likelihood under noisy-Newton, noisy-Newton + human bias, and a non-physical failure model; report the share of items each explains best.

**Statistics.** Mixed-effects models, e.g. `curvature ~ agent × conditioning × tube_curvature × speed + (1|item)`; item-level human–model error correlation against a split-half human ceiling; bootstrap CIs over items.

## 9. Human study (free)

- **Platform:** jsPsych experiment hosted on GitHub Pages, data saved to OSF through DataPipe. All three are free.
- **Participants:** volunteers (students, friends, social media, or a university participant pool for course credit if you have access). Target 40–60; 30 is the minimum for item-level correlations to mean anything.
- **One session, ≈ 15 minutes, within-subject:** (1) static block: pick the path from 4 drawn options on still frames (McCloskey forced choice); (2) dynamic block: watch the clip, the ball goes behind an occluder, click where it reappears; (3) short 2AFC block: which continuation looks natural. Static always comes first so watching motion does not teach the answers.
- **Published human data as a backstop:** McCloskey et al. (1980) error rates for the tube and string problems, and the public Physion human responses, so the paper has a human reference even if recruitment is slow.
- **Ethics:** if you are at a university, you will still need its ethics approval and a consent page, even for unpaid volunteers. Pre-register on OSF (free) before the full model runs.

## 10. Pilot (first 2–3 weeks, €0)

1. On your computer: write the generator for A1 (20 items: 4 curvatures + straight × 2 speeds × 2 seeds) and C1 (10 items).
2. On Kaggle: run V-JEPA 2 surprise on straight vs curved exits, and LTX-Video with single-frame and clip conditioning, 4 samples each (≈ 240 clips). Time a few clips of Wan 2.2 5B on the T4 to decide whether it needs the €20.
3. On your computer: track, compute curvature and period, plot.
4. Go/no-go: continue if a model curves more than the straight-tube control under single-frame conditioning, *or* bob size shifts period by more than 5%, *or* the errors are clearly non-human (still a paper, framed as "accuracy without human-like errors"). Ask 10 volunteers to try the static and dynamic blocks in parallel.

## 11. Cost

| Item | Estimate |
|---|---|
| Stimuli, tracking, analysis | €0 (your computer) |
| Full generation: ≈ 92 items × 2 modes × 4 samples + D1 extra ≈ 900 clips per model | LTX: ≈ 15 Kaggle hours, about one week of free quota *(inferred)*. Wan 5B: several weeks of Kaggle quota, or ≈ 30–40 h on a rented 4090 ≈ €15–20 |
| V-JEPA 2, VLM, likelihood scoring | a few Kaggle hours, €0 |
| Tiny from-scratch models (optional) | ≈ 20–40 Kaggle hours for two models, €0 *(inferred)* |
| Human study | €0 (volunteers, free hosting) |
| **Total cash** | **€0–20** |

Timing is the real cost: with only free GPUs, expect the full model runs to take about 4–6 weeks of calendar time, mostly waiting on Kaggle's weekly quota.

## 12. Paper outline and timeline

1. Intro: naive physics, the static/dynamic dissociation, and why "how models are wrong" matters for world models used in planning and robotics.
2. Related work (§2 above).
3. Stimuli and error taxonomy.
4. Results I: classic biases (A, B) by conditioning mode; human comparison.
5. Results II: oscillator laws and the mass–period belief (C).
6. Results III: chaos calibration (D).
7. Results IV: judge vs generate, and item-level alignment.
8. Discussion: statistical priors vs physical theories; implications for evaluation.

Suggested timeline *(inferred; check deadlines)*: pilot by early November 2026; pre-registration and the volunteer human study in November–December; full model runs on free Kaggle quota November–January. A short version fits **CogSci 2027** (deadline usually early February); the full paper fits **NeurIPS 2027** (Datasets & Benchmarks or main track, deadline usually May) or a journal such as *Nature Human Behaviour* / *PNAS* if the human–model alignment result is strong.

## 13. Main risks

- **Models fail for boring reasons** (freeze, vanish): screen validity first and report failure rates as part of the taxonomy.
- **Single-frame conditioning is underdetermined** (a still has no velocity): this is the point of the manipulation, and it is matched by the human static diagrams, which are equally underdetermined about speed. The curvature DV does not depend on speed, so the comparison is still fair. Report it as a separate condition, never pooled.
- **Text-prompt confound**: neutral prompts, prompt-free where possible, and a prompt-wording control on a subset.
- **Free GPUs are slow and can change**: Kaggle quotas and GPU types are not guaranteed. Checkpoint every run so a 12-hour session cutoff loses nothing, and keep the €20 for the one model that cannot finish otherwise.
- **Scoop risk**: the Li et al. ECCV 2026 paper shows the "human accuracy, non-human errors" framing is live. Move quickly on the pilot and lead with the bias paradigms and generative trajectories, which nobody has done.

## Sources checked for this plan

- World Models' Last Exam in Physics: https://arxiv.org/abs/2610.08791 (abstract; HF and alphaXiv pages; full text not read, rate-limited)
- Li et al. 2026, Human-Level Accuracy, Non-human Strategies: https://link.springer.com/chapter/10.1007/978-3-032-37132-4_5 (abstract/metadata)
- LikePhys: https://huggingface.co/papers/2510.11512 (abstract)
- The Invisible Hand of Physics: https://huggingface.co/papers/2606.05328 (abstract)
- All other sources: see the idea 1 and idea 3 briefs.
