# Idea 2: Do world models learn physical laws in the same order as infants?

Research brief, 12 Oct 2026. Claims marked *(inferred)* are my judgement, not something I checked in a source.

## 1. Bottom line

- **The gap is real and recent.** Garrido et al. (2025) showed V-JEPA passes infant-style violation-of-expectation (VoE) tests but only evaluated final models. The one paper that tracked VoE over training (Schulze Buschoff et al., ICML 2023) used a small RSSM on synthetic scenes and found the order did *not* match children. Nobody has done this on modern self-supervised video world models trained on natural video.
- **The main obstacle is checkpoints.** No major open video world model (V-JEPA 2, Cosmos, VideoMAE) releases dense intermediate checkpoints. Open-Sora gives only a few stage checkpoints. The realistic path is to **train your own small V-JEPA-style models and save checkpoints densely** ("Pythia for video"), which Garrido et al. suggest is affordable: a 115M encoder and 128 hours of unique video still beat 70–85% on VoE.
- **Strongest test: the within-category orderings** Baillargeon documented (e.g. support: contact → type of contact → amount of contact). They are cleaner predictions than cross-category orderings like "permanence before gravity," whose infant ages are more contested.

## 2. Infant developmental timeline (looking-time/VoE literature)

Ages are approximate first-success ages in VoE studies; many are debated (see caveats).

| Concept | Approx. age | Key refs |
|---|---|---|
| Object permanence (occlusion: object persists behind screen) | 2.5–3.5 mo | Baillargeon 1987; Aguiar & Baillargeon 1999 |
| Continuity (no teleporting; continuous paths) | 2.5–4 mo | Spelke et al. 1992 |
| Solidity (objects don't pass through each other) | 2.5–4 mo | Spelke et al. 1992; Baillargeon 1987 |
| Collision: hit object should move | 2.5 mo | Kotovsky & Baillargeon 1998 |
| Support: contact vs no contact | ~3 mo | Baillargeon, Needham & DeVos 1992 |
| Occlusion: occluder height/window variables | 3–4.5 mo | Baillargeon & DeVos 1991 |
| Support: type of contact (top vs side) | ~5 mo | Baillargeon 1995/1996 |
| Collision: hitter size predicts displacement | 5.5–6.5 mo | Kotovsky & Baillargeon 1998 |
| Support: amount of contact | ~6.5 mo | Baillargeon et al. 1992 |
| Gravity: unsupported objects fall / downward acceleration | ~5–7 mo (4 mo fail) | Spelke et al. 1992; Kim & Spelke 1992 |
| Containment: height variable | ~7.5 mo | Hespos & Baillargeon 2001 |
| Inertia (smooth, straight trajectories) | late, weak; ~8 mo+ and inconsistent | Spelke et al. 1994 |
| Covering: height variable | ~12 mo | Wang, Baillargeon & Paterson 2005 |
| Support: shape/mass distribution (asymmetric objects) | ~12.5 mo | Baillargeon 1995 |
| Feature-based object individuation (shape/colour) | 4.5–12 mo | Wilcox 1999; Xu & Carey 1996 |

**Theoretical framing to cite.** Baillargeon's account splits early *core principles* (persistence: continuity, solidity, cohesion) from *event-category variables* learned one at a time, in a fixed order per category, via "explanation-based learning." Spelke's core knowledge view predicts permanence/continuity/solidity are early or innate. These make a clean contrast for models: a learner with no built-in principles should, if it matches infants, still pick up persistence before variables like amount-of-contact.

**Caveats you'll have to address.**
- VoE replicability is under scrutiny (ManyBabies-style replications; low-level perceptual confounds in looking time).
- Looking ≠ acting: 2-year-olds fail search tasks on solidity/support that infants "pass" by looking (Hood et al. 2000). Compare models to *looking-time* data only.
- Cross-concept ages come from different labs, stimuli and samples, so they aren't directly comparable. Within-category sequences from one lab are much safer.

## 3. Prior AI work

**VoE benchmarks**
- **IntPhys** (Riochet et al. 2018/2021): synthetic; object permanence, shape constancy, spatio-temporal continuity.
- **IntPhys 2** (Bordes et al. 2025, Meta): harder, permanence/immutability/continuity/solidity; models are near chance while humans are ~96%.
- **GRASP** (Jassim et al. 2023): 10 properties incl. gravity, support, inertia, collision, colour constancy.
- **InfLevel** (Weihs et al. 2022): explicitly infant-inspired; continuity, solidity, gravity.
- **PLATO / Physical Concepts dataset** (Piloto et al. 2022, *Nat. Hum. Behav.*): continuity, directional inertia, object persistence, solidity, unchangeableness; object-centric model learns them with ~28 h of video.
- **ADEPT** (Smith et al. 2019), **Physion / Physion++** (Bear et al. 2021; Tung et al. 2023; prediction, not VoE), **MVP Minimal Video Pairs** (Krojer et al. 2025), **Physics-IQ** (Motamed et al. 2025), **PhyWorld** (Kang et al. 2024; generative models' physics generalisation).

**Most relevant papers**
- **Garrido et al. 2025, "Intuitive physics understanding emerges from self-supervised pretraining on natural videos"** ([arXiv 2502.11831](https://arxiv.org/abs/2502.11831); code: [jepa-intuitive-physics](https://github.com/facebookresearch/jepa-intuitive-physics)). V-JEPA: IntPhys 98%, GRASP 66%, InfLevel 62%. Above untrained baseline on permanence, continuity, shape constancy, support, gravity, inertia; near chance on solidity, collision, colour constancy. Pixel-space generators and MLLMs near chance. Varies data and model size but **no checkpoint analysis**. Their surprise metric is the template to reuse.
- **Schulze Buschoff, Schulz & Binz 2023, "The acquisition of physical knowledge in generative neural networks"** ([ICML](https://proceedings.mlr.press/v202/schulze-buschoff23a/schulze-buschoff23a.pdf)). This is the direct precursor. RSSM on rendered scenes, Baillargeon's support/occlusion/collision variables, VoE scored every epoch. Result: concepts learned at roughly the same rate, wrong order (shape/mass learned early), no size-independent collision stage. **Your paper is the scaled-up, natural-video, modern-architecture version of this, so position against it.**
- **Su, Legris, Gureckis & Ren 2025, "Learning intuitive physics may require more than visual data"** ([alphaxiv 2512.06232](https://www.alphaxiv.org/abs/2512.06232v1)). V-JEPA trained on SAYCam (child headcam) stays near chance on IntPhys 2. This is useful as a "developmentally realistic data" arm, and a warning.
- **Punzo et al. 2026** ([arXiv 2606.09646](https://arxiv.org/abs/2606.09646)): probes V-JEPA, VideoMAE, LTX-Video on IntPhys 2 / MVP. Physics info peaks at middle-to-late layers. Final models only.
- **Joseph, Garrido et al. 2026, "Interpreting physics in video world models"** ([arXiv 2602.07050](https://arxiv.org/abs/2602.07050)): a "physics emergence zone" at intermediate depth, with speed/acceleration early and direction later. This gives you a ready-made layerwise probing method to run across checkpoints.
- Binz & Endres 2019: Bayesian NN reproduced children's support/occlusion order, but with oracle supervision and 2D stimuli.

## 4. Models with intermediate checkpoints

| Option | Checkpoints | Verdict |
|---|---|---|
| V-JEPA / V-JEPA 2 (Meta) | Final only (various sizes) | Use as the "adult" endpoint and for the size axis |
| VideoMAE / VideoMAE v2 | Final only | Endpoint comparison |
| Cosmos (NVIDIA), LTX-Video, HunyuanVideo, Wan | Final only | Generative endpoints; known to be weak on VoE |
| Open-Sora 1.x / Open-Sora-Plan | A few **stage** checkpoints (low-res → high-res stages) | Coarse "developmental" points for a generative model, but stages change the data, not just training time |
| **Train your own** (V-JEPA codebase, ViT-S/B, 128 h–1 k h of video) | As dense as you want (log-spaced, ~50–100) | **Recommended core** |

*(inferred)* Training a ViT-B V-JEPA on a few hundred hours of video for a few runs is a multi-GPU-week budget, not a frontier one. Check against the V-JEPA repo configs before committing.

## 5. Sketch of a feasible design

**Models (core).** Train V-JEPA-style encoders/predictors from scratch with log-spaced checkpoints:
- 3 seeds × 2 sizes (ViT-S, ViT-B) on a natural-video corpus (HowTo100M or SSv2 subset).
- One arm trained on **SAYCam / child egocentric video** for developmental realism (expect weak absolute performance, per Su et al.).
- One **pixel-space** arm (VideoMAE-style or small diffusion) to test whether representation-space prediction is what drives the order.
- Add the released final V-JEPA 2 / Cosmos models as endpoints, and Open-Sora stage checkpoints as a coarse generative comparison.

**Stimuli.** Two sets:
1. Existing benchmarks (IntPhys, GRASP, InfLevel, PLATO) for comparability.
2. **New infant-matched VoE stimuli** rendered (e.g. ThreeDWorld, Kubric, or Blender) to replicate specific infant experiments one-to-one: Baillargeon's support sequence (contact → type → amount → shape), occlusion variables, collision size effect, containment vs covering height (7.5 vs 12 mo, the same physical rule in two event categories, which is a strong test), gravity, inertia, solidity. Match possible/impossible pairs on low-level pixel change.

**Measure.** Surprise = prediction error in representation space (Garrido et al.'s metric), paired possible vs impossible. For each concept × checkpoint: pairwise accuracy with bootstrap CIs, against an untrained-network baseline.

**Analysis.**
- *Onset* per concept = first checkpoint stably above the untrained baseline (and/or the checkpoint reaching 50% of final accuracy).
- **Primary test:** Kendall's τ between infant onset age and model onset, computed **within** event categories (support, occlusion, collision, containment) where infant order is well established; permutation test across concepts.
- **Secondary:** all-concept Spearman; does the core-principles-before-variables split hold?; stage-like jumps vs smooth parallel learning (Schulze Buschoff found parallel); seeds/sizes/data effects on order.
- **Mechanism:** layerwise probes across checkpoints (Joseph et al. method) to see when physical variables become decodable vs when VoE succeeds.
- **Controls:** low-level salience (pixel/optical-flow difference between pair members), frame shuffling, untrained nets.

**Possible outcomes worth publishing either way.** Match within categories means data statistics alone may explain infant order. Mismatch extends Schulze Buschoff to modern models and points to the need for priors, embodiment or action (in line with Su et al.).

## 6. Risks
- Infant ages are noisy and cross-lab, so keep the headline claim to within-category orders.
- Few concepts means low statistical power for rank correlations. Aim for ~15–20 concept-variables.
- Training-step order may reflect stimulus difficulty for the network (e.g. small pixel changes) rather than "conceptual" order. Low-level controls are essential.
- Solidity and collision are near chance even in final V-JEPA, so you may get floor effects. Consider a stronger final model or more data for the endpoint.
- Natural video's frequency of events (support is everywhere, occlusion is everywhere) may drive order trivially. *(inferred)* Measuring event frequency in the training corpus would make a nice explanatory covariate.

## 7. Cost estimate: training your own models on rented GPUs (added 12 Oct 2026)

**Prices** (on-demand, per GPU-hour, Spheron comparison updated Oct 2026: https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/):
H100: Vast.ai ~$1.5–2.3, Lambda $2.49–3.44, RunPod $2.99, Nebius $3.85, AWS ~$6.9, GCP ~$11. A100 80GB: ~$0.8–1.4 budget, ~$3.4 AWS.
Used below: **~€2.5 per H100-hour** (budget providers) vs **~€6–10** (AWS/GCP/Azure). USD→EUR at ~0.9 *(approximate)*.

**GPU-hours per run** *(inferred, my estimate, not a published figure)*. V-JEPA recipe: 90k iterations × batch 3,072 × 16 frames at 224 px. That is ~2 TFLOP per clip per step for ViT-L, so ~550 ExaFLOP total. At ~30% utilisation on an H100, that comes to ~500 H100-h for ViT-L, ~150–250 for ViT-B, and ~50–100 for ViT-S. A recent paper reports 36.4 ExaFLOP for a ViT-B V-JEPA 2 run (shorter schedule), which is consistent with tens to a couple of hundred H100-h. Video decoding often bottlenecks, so budget ×1.5.

| Scenario | Runs | H100-h (incl. eval + ~30% failed/debug runs) | Budget cloud | Big cloud |
|---|---|---|---|---|
| Pilot | 1–2 ViT-S, 128 h of video, ~50 checkpoints | ~150–300 | **€400–800** | €1.5–3k |
| Core paper | 3 seeds × ViT-S + ViT-B on natural video | ~1,000–1,500 | **€2.5–4k** | €8–15k |
| Full design (§5) | core + 3 SAYCam runs + 3 pixel-space runs (ViT-B) | ~2,500–3,500 | **€6–9k** | €20–35k |

**Storage and data.**
- Checkpoints: ~0.5 GB each (encoder + target + predictor) × ~100 per run × 12 runs = ~0.6 TB.
- Video: 1k h at low resolution, ~0.3–0.5 TB.
- That's ~1–2 TB at €0.02–0.07/GB-month, so **€30–150/month**. Watch egress fees if you move data between providers.
- Datasets are free but have access hurdles: SSv2 and Kinetics need a licence/download, HowTo100M is YouTube scraping, and SAYCam needs a Databrary institutional agreement.
- Rendering the VoE stimuli is CPU-cheap (tens of euros).

**Ways to cut cost.**
- LeVJEPA (arXiv 2608.27395) reports 5–20× less pretraining compute than V-JEPA 2 at similar accuracy.
- Smaller resolution and frame counts.
- Logging only the encoder at each checkpoint.
- For French academics, GENCI/Jean Zay grants compute hours free through calls for proposals.
