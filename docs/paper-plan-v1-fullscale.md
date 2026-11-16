# Do world models make human-like physics errors?

Unified paper plan combining idea 1 (naive-physics trajectory biases) and idea 3 (oscillators, chaos, parameter sweeps). Written 2026-10-12. It builds on `ideas/idea1-trajectory-biases/research-brief.md` and `ideas/idea3-complex-trajectories/design.md`; details already written there are referenced rather than repeated. Claims marked *(inferred)* are my own estimates or readings, not checked facts.

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

## 5. Stimuli

All synthetic, generated from exact physics (scipy ODEs; MuJoCo or PyBullet where contacts matter), in two styles: **minimal 2D** (coloured ball on a plain background; trivial tracking; used for humans) and **rendered 3D** (Blender/Kubric lab scene, closer to model training data). 16–24 fps, ~5 s outputs, periods 1–4 s.

| Family | Paradigm | Factors | Items (minimal style) | Source idea |
|---|---|---|---|---|
| A1 | Curved tube exit (top-down and oblique) | curvature: straight, 90°, 180°, 270°, spiral × 3 exit speeds × 2 viewpoints × 3 seeds | 90 | 1 |
| A2 | Ball on string swung in a circle, string snaps | 4 release phases × 2 speeds × 3 seeds | 24 | 1 |
| A3 | Pendulum string cut | 5 cut phases (bottom, mid-swing, near turning point) × 2 amplitudes × 3 seeds | 30 | 1 + 3 |
| B1 | Drop from a moving cart | 4 cart speeds (incl. 0) × 2 heights × 3 seeds | 24 | 1 |
| B2 | Free projectile arcs (control) | 3 angles × 3 speeds × 2 seeds | 18 | 1 |
| C1 | Simple pendulum | 6 lengths (2 out-of-range) × 2 bob sizes × 2 amplitudes | 24 | 3 |
| C2 | Vertical mass–spring | 3 stiffness × 2 masses × 2 bob colours | 12 | 3 |
| C3 | Ball in bowl | 4 bowl radii × 2 release heights × 2 ball sizes | 16 | 3 |
| D1 | Double pendulum | 3 energy levels (quasi-periodic → chaotic) × 4 initial conditions | 12 | 3 |
| | **Total** | | **≈ 250 items** | |

Each item is rendered with **two conditioning modes**: single frame at the critical moment (exit, release, cut) and a multi-frame clip (e.g. 1 s before the critical moment plus 2–3 frames after, or ¼/½/1 period for oscillators). The 3D style is added for a subset (A1, A3, C1, D1) to test whether style changes the bias. Prompts: one fixed neutral prompt per family, plus prompt-free where the model supports it.

## 6. Models

Start with four that the briefs already vetted, chosen to span architecture and conditioning:

| Model | Role | Conditioning | GPU *(inferred, check before committing)* |
|---|---|---|---|
| **Cosmos-Predict2 / 2.5 Video2World (2B)** | "World model" by design | native multi-frame | 1× 24–48 GB |
| **Wan 2.1 / 2.2 I2V (14B)** | strongest open I2V in Morpheus | single frame; multi-frame via VACE | 1× 80 GB |
| **LTX-Video** | fast, multi-frame conditioning, cheap for many samples | single and multi-frame | 1× 24 GB |
| **V-JEPA 2** | latent predictor, discriminative only | multi-frame | 1× 24 GB |

Optional additions if time allows: HunyuanVideo-I2V or CogVideoX-I2V (scale comparison); a small from-scratch model à la Kang et al. trained with and without constrained circular motion (tests *where* the impetus bias comes from, but this is the most expensive extension, so treat it as follow-up); one VLM (any frontier API model) on static diagrams for the reasoning corner; one closed video model via API as a frontier reference.

Baselines: ground-truth physics; **noisy-Newton observer** (physics with initial position/velocity jittered by human perceptual noise, ≈1–2° and ≈10% speed, from Smith & Vul 2013); "copy last cycle"; "continue curvature" (an explicit impetus model, so we can ask which baseline a model's samples are closest to).

## 7. Readouts and analysis

**Generative.** Sample N continuations per item (8 standard; 32 for D1). Track the ball (colour threshold on minimal; SAM 2 on 3D). Validity screen first (object persists, single object, moves), with the discard rate reported per model as its own result. Then per family:
- A/B: signed curvature of the post-event path; deviation angle from the tangent at fixed distance; McCloskey-style path classification (straight / curved-continuing / other); landing error vs the parabola.
- C: damped-sinusoid fit, so period, amplitude drift and energy drift; log–log slope vs L, m/k, R; period ratio across irrelevant cues.
- D: divergence time vs Lyapunov horizon; CRPS / energy score and spread–skill ratio vs the noisy-Newton ensemble.

**Discriminative.** Present correct vs anomalous continuations (straight vs curved exit; correct vs ±10–25% period). Score with V-JEPA 2 surprise and diffusion denoising loss (LikePhys-style). Fit psychometric functions over perturbation size and extract thresholds that compare directly with human 2AFC thresholds.

**Error taxonomy.** For each model × item, compute the likelihood of its samples under three generative accounts (noisy-Newton, noisy-Newton + human bias term, and a non-physical failure model) and report the proportion of items best explained by each. This turns "is it human-like?" into a model-comparison question rather than a judgment call.

**Statistics.** Mixed-effects models, e.g. `curvature ~ agent × conditioning × tube_curvature × speed + (1|item) + (1|seed)`; item-level human–model error correlation and κ against a split-half human ceiling; bootstrap CIs over items.

## 8. Human study (Prolific, minimal-style stimuli only)

| Experiment | Task | Stimuli | N | Mirrors model readout |
|---|---|---|---|---|
| E1 Static | Pick the path from 4 drawn options (McCloskey forced choice), or click where the ball will be | Still frame of each A/B/C3 item (the single-frame condition) | 50 | Single-frame generation; VLM arm |
| E2 Dynamic | Watch the clip; the ball goes behind an occluder; click where/when it reappears (A, B, C), or extrapolate the bob (D) | Multi-frame clips | 50 | Multi-frame generation |
| E3 Judgment | 2AFC: which continuation is natural? Graded perturbations | Correct vs anomalous pairs | 50 | Discriminative readout and thresholds |

About 25–30 min each, between-subjects, ≈150 participants total. Ethics approval needed through your institution; pre-register H1–H8 and the discard criteria on OSF before running models at scale. E2 gives the human "ensemble" for D1 by pooling responses across participants.

## 9. Pilot (first 2–3 weeks)

Goal: decide whether there is a curvature effect and a mass–period effect worth scaling.

1. Build the minimal-style generator for A1 (40 items: 4 curvatures + straight × 2 speeds × 4 seeds) and C1 (24 items).
2. Run **LTX-Video** (cheap, many samples) and **Cosmos-Predict2-2B**, single- and multi-frame, 8 samples each, plus V-JEPA 2 surprise on straight vs curved exits.
3. Track, compute post-exit curvature and pendulum period.
4. Go/no-go: proceed if either model's curvature exceeds the straight-tube control under single-frame conditioning, *or* bob size shifts period by more than 5%, *or* the error profile is clearly non-human (which is still a paper, framed as "accuracy without human-like errors"). Run a 20-person version of E1/E2 on the same items in parallel; it is cheap and tells you whether the human effects replicate online.

## 10. Rough cost

All numbers *(inferred)* from typical inference speeds; measure in the pilot before budgeting.

| Item | Calculation | Estimate |
|---|---|---|
| Pilot generation | 64 items × 2 modes × 8 samples ≈ 1,000 videos per model; LTX ≈ seconds/video, Cosmos-2B ≈ 1–2 min/video | ≈ 20–40 H100-hours total |
| Full generation | ≈ 250 items × 2 modes × 8 samples ≈ 4,000 + D1 extra ≈ 4,400 videos per model, + 3D subset (≈ +30%) | per model: LTX ≈ 10–20 h, Cosmos-2B ≈ 80–150 h, Wan-14B ≈ 200–400 h. **Total ≈ 300–600 H100-hours** |
| Discriminative scoring | forward passes only | < 50 GPU-hours |
| GPU cost at ≈ $2–3 per H100-hour (cloud) | | **≈ $700–1,800** (less on a university cluster) |
| Human study | 150 × ~0.5 h at ≈ £10/h + Prolific fee (~33%), + pilot 20 people | **≈ £1,100–1,300** |
| Optional VLM / closed video API arm | a few hundred calls | ≈ $50–300 |

Dropping Wan-14B cuts GPU cost by more than half; it is the obvious lever if compute is tight.

## 11. Paper outline and timeline

1. Intro: naive physics, the static/dynamic dissociation, and why "how models are wrong" matters for world models used in planning and robotics.
2. Related work (§2 above).
3. Stimuli and error taxonomy.
4. Results I: classic biases (A, B) by conditioning mode; human comparison.
5. Results II: oscillator laws and the mass–period belief (C).
6. Results III: chaos calibration (D).
7. Results IV: judge vs generate, and item-level alignment.
8. Discussion: statistical priors vs physical theories; implications for evaluation.

Suggested timeline *(inferred; check deadlines)*: pilot by early November 2026; pre-registration and human E1–E3 in November–December; full model runs December–January. A short version fits **CogSci 2027** (deadline usually early February); the full paper fits **NeurIPS 2027** (Datasets & Benchmarks or main track, deadline usually May) or a journal such as *Nature Human Behaviour* / *PNAS* if the human–model alignment result is strong.

## 12. Main risks

- **Models fail for boring reasons** (freeze, vanish): screen validity first and report failure rates as part of the taxonomy.
- **Single-frame conditioning is underdetermined** (a still has no velocity): this is the point of the manipulation, and it is matched by the human static diagrams, which are equally underdetermined about speed. The curvature DV does not depend on speed, so the comparison is still fair. Report it as a separate condition, never pooled.
- **Text-prompt confound**: neutral prompts, prompt-free where possible, and a prompt-wording control on a subset.
- **Scoop risk**: the Li et al. ECCV 2026 paper shows the "human accuracy, non-human errors" framing is live. Move quickly on the pilot and lead with the bias paradigms and generative trajectories, which nobody has done.

## Sources checked for this plan

- World Models' Last Exam in Physics: https://arxiv.org/abs/2610.08791 (abstract; HF and alphaXiv pages; full text not read, rate-limited)
- Li et al. 2026, Human-Level Accuracy, Non-human Strategies: https://link.springer.com/chapter/10.1007/978-3-032-37132-4_5 (abstract/metadata)
- LikePhys: https://huggingface.co/papers/2510.11512 (abstract)
- The Invisible Hand of Physics: https://huggingface.co/papers/2606.05328 (abstract)
- All other sources: see the idea 1 and idea 3 briefs.
