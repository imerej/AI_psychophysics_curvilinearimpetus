# The three reference studies, extracted

Written 2026-10-20. Sources: the full texts of Smith, Battaglia & Vul (2018, author preprint) and Kaiser, Proffitt, Whelan & Hecht (1992, full PDF). McCloskey & Kohl (1983) is from the full PDF uploaded to the project.

Numbers are as printed. Where the paper itself looks inconsistent, I flag it with ⚠️.

---

## 1. Smith, Battaglia & Vul (2018). Different physical intuitions exist between tasks, not domains

*Computational Brain & Behavior* 1:101–118. [Author PDF (MIT DSpace)](https://dspace.mit.edu/handle/1721.1/131487) · [preprint](https://www.mit.edu/~k2smith/pdf/SmithBattagliaVul_DiffPhysInt_Preprint.pdf) · DOI [10.1007/s42113-018-0007-3](https://doi.org/10.1007/s42113-018-0007-3)

### Hypothesis
- Question: does intuitive physics run on accurate physical knowledge or on biased heuristics?
- The authors' claim: accuracy depends on **the task**, not on the physical principle. The same physics (a pendulum bob released into free fall) should look Newtonian in tasks that call on simulation (catching, timing a release) and biased in explicit tasks (drawing the path).
- Against: the "domain" account (Marcus & Davis 2013), where some principles are known correctly and others wrongly, which predicts the same errors across tasks.

### Experiment 1: catching, releasing and drawing (same people)
**Participants.** 35 UC San Diego undergraduates for course credit; 3 dropped for random responding, **N = 32**. Sample size fixed in advance from a pilot.

**Stimulus.**
- Computer display at ~60 cm. Pendulum cord = **half the screen height**, maximum amplitude **35°** from vertical, period **2.5 s**. Gravity scaled as if the pendulum were 6 m away from the viewer. Cord treated as massless.
- The ball's flight after the cut was **hidden**. Feedback was hit/miss only.
- Screen resolution, ball and bucket sizes and colours are not reported.

**Tasks.**
- *Catching:* the cut happened at a preset time, signalled by a knife icon that darkened just before. Participants slid a bucket horizontally to where the ball would land. **16 release times × 3 bucket heights** (20%, 35%, 50% of screen height below the lowest point of the swing) = 48 trial types × 5 repetitions = **240 trials**.
- *Releasing:* bucket fixed; participants clicked to cut the cord. Clicking was disabled for a random 1.2–3.6 s at the start (the ball's red colour acted as a timer). Also **240 trials**, matched to catching (each catching trial's landing point became a releasing trial's bucket position).
- Catching/releasing order randomised; one practice trial each. No learning from feedback was found.
- *Drawing* (always last, on paper): 4 pendulum diagrams at different points of the swing, adapted from Caramazza et al. (1981). Draw the path if the cord is cut now. A short physics-background survey followed.

**Analysis.**
- *Calibrated physics model:* correct ballistics, with uncertainty about the pendulum's depth (so cord length and effective gravity are fitted), plus Gaussian motor noise for bucket placement (SD grows with drop height) and for cut timing.
- *Non-physical models*, each giving a release angle followed by a straight line: **Angled** (release angle piecewise-linear in cord angle), **Outward** (ball continues along the cord direction, scaled), **Straight down**, **Impetus** (ball keeps going along the arc for a fixed angle, then falls straight down; after Caramazza 1981 / McCloskey 1983).
- Compared by BIC, 500 noisy simulations per trial, bootstrap CIs.
- Drawings: 3 raters coded each person's 4 drawings into one of **11 patterns** (Fleiss κ = 0.74). Drawings were also extrapolated to give 3 "pseudo-catching" positions each (12 per person).

**Results.**
- Mean human responses vs calibrated model: **catching r = 0.988, releasing r = 0.998**. Humans vs ground truth: r = 0.969 and 0.989. The calibrated model fits humans better than ground truth does (z = 2.26 and 4.28).
- Humans have systematic biases (buckets pulled toward screen centre; releases overshoot, except near the edges), and the calibrated model reproduces them (r = 0.92 and 0.93 with human deviations).
- Model comparison, ΔBIC vs calibrated: Angled 2,981, Impetus 3,345, Outward 14,435, Straight down 14,698. Calibrated wins.
- Individuals: **24/32 (75%)** best fit by the calibrated model on the interactive tasks.
- Drawings: **7/32 (22%)** consistent with physics; **2 people (6%)** drew all four correctly; no single error pattern covered more than 22% of people. Drawing errors were *anti-correlated* with the physics model's errors (r = −0.41) and did not predict a person's own catching (mean r = 0.17).
- Agreement with other people's errors: catching r = 0.76, releasing 0.53, drawing 0.29 (drawing errors are idiosyncratic).

### Experiment 2: drawing after motion vs after a still
**Participants.** 67 UCSD undergraduates, randomly split: **Motion n = 33, Static n = 34**.

**Stimulus.** Same pendulum as Exp 1. *Motion:* one full swing, then the pendulum swings to the cut point. *Static:* only the final frame. Both saw the same image just before responding. Four cut points in random order: **apex, downswing, nadir, upswing**.

**Response.** Drag the mouse to draw the path (sampled every 20 ms); it had to start in the ball and end near the bottom of the screen. Each drawing coded by 3 raters into 6 path types + unclassified (κ = 0.60; 5% unclassified).

**Results.**
- Motion changed the drawings at the **apex** (χ² = 13.4, p = .014) and **nadir** (χ² = 10.7, p = .035), not at the downswing (χ² = 2.4) or upswing (χ² = 8.3, p = .14).
- Apex: with motion, people more often kept the ball moving sideways; with a still, more often the correct straight drop. **Correct at the apex: 24% static vs 6% motion** (χ² = 4.4, p = .043). No accuracy difference at the other three points.
- Nadir: static drawings dropped straight down; motion drawings kept the horizontal speed.
- Conclusion: motion changes the *velocity people infer*, not the physics they apply.

Counts per path type (Table 2; "correct" class as labelled in the table):

| Cut point | Condition | 1 | 2 | 3 | 4 | 5 | 6 | Uncl. |
|---|---|---|---|---|---|---|---|---|
| Apex (correct = 3) | Static | 5 | 1 | 8 | 10 | 1 | 0 | 8 |
| | Motion | 10 | 9 | 2 | 5 | 1 | 0 | 7 |
| Downswing (correct = 5) | Static | 0 | 2 | 2 | 18 | 7 | 0 | 6 |
| | Motion | 0 | 2 | 0 | 19 | 7 | 0 | 4 |
| Nadir (correct = 5) | Static | 1 | 1 | 13 | 7 | 7 | 0 | 8 |
| | Motion | 0 | 0 | 5 | 16 | 5 | 0 | 4 |
| Upswing (correct = 5) | Static | 0 | 7 | 1 | 8 | 8 | 3 | 6 |
| | Motion | 0 | 0 | 2 | 10 | 10 | 5 | 6 |

⚠️ Some rows don't add up to the group sizes (static nadir = 37, motion nadir = 30), and the text calls the correct path "path 5" while the apex row marks class 3 as correct. The path-type pictures are only in their Figure 8, so check it before using these counts.

### Human data, in short
32 people × 480 interactive trials + 4 drawings; 67 people × 4 drawings. Results are reported as correlations, BIC and category counts. **No public raw data** (the journal supplement has 2 movies of the task and a Word file).

### Match to our stimuli
Our A3 cut points (turning, descending, bottom, ascending) = their apex, downswing, nadir, upswing. Differences: our amplitude is 40° (theirs 35°), and their period is 2.5 s.

---

## 2. Kaiser, Proffitt, Whelan & Hecht (1992). Influence of animation on dynamical judgments

*JEP: Human Perception and Performance* 18(3):669–690. [Full PDF](https://www.Gwern.net/doc/psychology/cognitive-bias/illusion-of-depth/1992-kaiser.pdf) · DOI [10.1037/0096-1523.18.3.669](https://doi.org/10.1037/0096-1523.18.3.669). Only Experiments 1 (pendulum) and 2 (airplane) are relevant; Exp 3 is about water displacement.

### Hypothesis
- Animation should make people's judgments accurate only when **one dimension of information** matters dynamically: a *particle* (just the centre of mass moving), or an extended body constrained so only one property matters.
- Why: animation shows the object's motion state at every moment, and separates in time changes of state (a pendulum bob becomes a free particle when the cord is cut).
- Pendulum prediction: with true dynamics shown, people should recognise the natural path after the cut. Airplane prediction: people should recognise the natural fall whether they judge it relative to the ground or to the plane.

### Experiment 1A: static drawings and forced choice (pendulum)
**Participants.** 80 University of Virginia undergraduates (40 men, 40 women), course credit; 63 had taken high-school or college physics.

**Stimulus and task.** Paper. Cord cut at the **apex** or the **nadir**.
- Free drawing of the path.
- Forced choice: every pair of **5 candidate paths**, one pair per booklet page; pick the more natural.
- Half drew first. Drawings coded into the 5 alternatives by 2 judges (73% agreement).
- The 5 paths: the correct one (apex: straight down, since the bob has no speed; nadir: a parabola) plus common wrong answers from Caramazza et al. 1981 (e.g. a parabola at the apex).

**Results (proportion correct).**

| Cut point | Caramazza 1981 (drawing) | 1A drawing | 1A forced choice |
|---|---|---|---|
| Apex | .32 | .33 | .23 |
| Nadir | .25 | .55 | .84 (⚠️ text says 81%) |

- Most apex errors were a parabola. Order and physics courses made no difference.
- Men did better (e.g. apex drawing: 16 men vs 3 women correct).
- Scaling of preferences: at the apex the wrong parabola was preferred most and the correct path came third; at the nadir the correct path was preferred most.

### Experiment 1B: static vs kinematic vs dynamic (pendulum)
**Participants.** 48 new UVA undergraduates (24 men, 24 women), groups of 3–4.

**Display.** 114 cm (45-inch) rear-projection video screen. A human figure gave the scale; the cord was about **1.5 × the figure's height**.

**Three conditions (within subjects).**
- *Static:* each candidate path shown as a still drawing for as long as the animation would last.
- *Kinematic:* same start image, then the path drawn at **constant speed** (no real dynamics).
- *Dynamic:* the pendulum swings **two full cycles**, the cord is cut at the apex or nadir **during the third**, and the bob follows one of the 5 paths. All paths used the same scale-correct gravity; speed or direction changes in wrong paths were ramped so nothing jumped.

**Task.** Every pair of the 5 paths; choose which looks more natural. Correct path appears in 4 pairs, so the score is 0–4. Order: half dynamic → kinematic → static, half the reverse.

**Results (mean correct out of 4).**

| Cut point | Dynamic | Kinematic | Static | Test |
|---|---|---|---|---|
| Apex | **3.00** | 2.21 | 2.29 | F(1,45) = 6.64 (⚠️ printed as p < .001; this F gives about p = .01) |
| Nadir | 3.65 | 3.54 | 3.50 | F(1,45) = 2.27, ns |

- Only in the dynamic condition was the correct apex path the most preferred; in static and kinematic, the wrong parabola won.
- Seeing the dynamic version first did not improve later static or kinematic judgments (order F = 0.06).
- Men beat women in static and kinematic, not in dynamic.
- Conclusion: the benefit needs **real dynamics**; motion at constant speed does not help.

### Experiment 2A: drawing what you saw (airplane)
**Participants.** 40 UVA undergraduates (20 men, 20 women).

**Stimulus.**
- Animations made on an Amiga 1000 with Videoscape 3D, shown on a ~30–48 cm colour monitor. An airplane flies over farm fields with mountains behind; a second airplane on the ground gives scale. It carries a keg to drop at a party site in the foreground.
- The plane flies at constant speed for **1.5 s**, then releases the keg.
- Two viewpoints: **stationary** (camera fixed, plane crosses the screen) and **dolly** (camera follows the plane, background moves).
- **Six paths**, keg's horizontal speed relative to the plane's (= 1.0), taken from McCloskey et al. 1983 Exp 3:
  1. −0.25 (falls backward)
  2. 0 (straight down)
  3. 0.5 (rough air resistance)
  4. 1.0 (correct without air resistance)
  5. 1.0 slowing to 0.5 in the first 0.5 s (rough air resistance)
  6. 1.2 (faster than the plane)

**Task.** Watch each animation twice, then draw the keg's path on paper the size of the screen. Half saw stationary first. 3 coders (94% agreement) classed each drawing as backward, straight down or forward.

**Results.**
- Stationary camera: forward motion was underestimated. When the keg really fell straight down, **over half drew it going backward**. For the half-speed path, almost half drew no forward motion. For path 4, all but one drew forward motion.
- Dolly camera: no systematic bias; straight down was the hardest to reproduce.
- Correct drawings: dolly 34.67 vs stationary 28.17, t(5) = 2.70, p < .05.

### Experiment 2B: which looks natural (airplane)
**Participants.** 40 new UVA undergraduates (20 men, 20 women); all men and 12 women had taken physics. Groups of 4–5, 47.5 cm monitor.

**Task.** The same 12 animations. Every pair of paths shown twice (both orders); choose the more natural. Paths grouped as forward (3–6), straight down (2), backward (1).

**Results (most-preferred category).**

| | Forward | Straight down | Backward |
|---|---|---|---|
| McCloskey 1983 drawings (for comparison) | 53% | 36% | 11% |
| 2B stationary | **82%** | 18% | 0% |
| 2B dolly | **82%** | 15% | 3% |

- Forward above chance (67%): χ²(1, N = 40) = 8.20, p < .005. Stationary and dolly did not differ (χ² = 1.08).
- Only 3 people per condition preferred path 6 (too fast).
- Paths 3 and 5 (with air resistance) were preferred over path 4 (no air resistance).
- Conclusion: watching animation people pick a forward fall, even though in the stationary view they *draw* the relative-motion bias. Animation does not make metric judgments (speed) accurate.

### Human data, in short
80 + 48 people on the pendulum; 40 + 40 on the airplane. Reported as proportions, means out of 4, and category percentages; per-path drawing counts are only in a figure. **No raw data available.**

### Match to our stimuli
- Pendulum: our A3 context shows about one period before the cut; theirs shows two full cycles. They only test apex and nadir.
- Airplane: our B1 is a trolley seen from a fixed camera, which matches their stationary condition. Our anomalous clips are straight down only; their set also has backward (−0.25), half speed and 1.2×.

---

## 3. McCloskey & Kohl (1983). Naive physics: the curvilinear impetus principle and its role in interactions with moving objects

*JEP: Learning, Memory, and Cognition* 9(1):146–156. DOI [10.1037/0278-7393.9.1.146](https://doi.org/10.1037/0278-7393.9.1.146) · [JHU record with abstract](https://pure.johnshopkins.edu/en/publications/naive-physics-the-curvilinear-impetus-principle-and-its-role-in-i-3/) · Full text: the PDF uploaded to this project (pp. 146–156, all read).

### Hypothesis
- Two views the authors set out to test: (a) people who draw curved paths on paper still have accurate **perceptual** knowledge that objects move straight, so watching the motion should fix their answers (Exps 1–2); (b) they have accurate **practical** knowledge used in concrete, everyday tasks (Exp 3).
- The curvilinear impetus principle: an object made to move on a curved path acquires an "impetus" that keeps it curving for a while after release, then gradually straightens.
- Outcome: neither view was supported. Watching motion did not help, and in a hands-on task a quarter of people still tried to make the object curve.

### Experiment 1: ball on a string (watching motion)
**Participants.** 90 Johns Hopkins undergraduates, 30 per condition. In each condition 10 had no physics, 10 high-school physics, 10 at least one college course; 5 men and 5 women at each level.

**Display.** DEC PDP-11/20 driving a CRT laid flat, face up, so the motion is seen **from above**; viewing distance ~45 cm; 50 frames/s. Ball 0.4 cm (0.5°) on a circular path 4 cm in diameter (5°), constant speed 11.4 cm/s (14.25°/s, 54 rpm). On release the string disappears at a fixed point and the ball moves at constant speed to the edge of a 15 × 15 cm field, then a static picture of the path is shown.

**Trial (one per person).**
1. Verbal description + diagram of the ball whirled on a string, the string breaking at the marked point.
2. Condition:
   - **No motion**: nothing else.
   - **Rotation**: told a simulation might help; watched the ball circle, without release, as long as they liked (until a key press).
   - **Trajectories**: saw all 6 candidate paths animated, each twice (rotation → string breaks → ball flies off → static path), in a random order per subject.
3. Chose one of 6 paths, drawn on 12.5 × 20 cm cards pinned to a board in random order. A = straight tangent (correct); B, C = curvilinear impetus; D, E, F = "centrifugal" (outward) paths.

**Results (Table 1, number of subjects).**

| Condition | Correct | Curvilinear | Centrifugal | n |
|---|---|---|---|---|
| No motion | 18 | 8 | 4 | 30 |
| Rotation | 20 | 8 | 2 | 30 |
| Trajectories | 22 | 6 | 2 | 30 |
| **Total** | 60 (67%) | 22 (24%) | 8 (9%) | 90 |

- No effect of condition, χ²(4) = 1.76, p > .50: seeing the curved paths move made them look no less plausible.
- Physics training mattered, χ²(4) = 12.7, p < .05: no physics 43% correct / 40% curvilinear; college physics 83% / 10%.
- No sex difference, χ²(2) = 1.83, p > .25 (women 60% correct, men 73%).
- Overall rates match the paper-and-pencil data of McCloskey et al. 1980.

### Experiment 2: spiral tube (watching motion)
**Participants.** 72 Johns Hopkins undergraduates, 36 per condition (12 per physics level, 6 men + 6 women each).

**Display.** Same system. A transparent spiral tube lying flat, seen from above, 5.5 cm at its widest (6.9°); ball 0.4 cm (0.5°) at 12.2 cm/s (15.25°/s). Instruction: a ball is "shot out of the other end at high speed". After a key press the ball travels through the tube and exits on the path being shown, then a static picture of tube + path.

**Trial (one per person).** As in Exp 1, with two conditions: **no motion** and **trajectories** (6 animated alternatives, each twice). Alternatives (Fig. 3): A correct (straight on exit), B–D curvilinear impetus, E–F other.

**Results (Table 2).**

| Condition | Correct | Curvilinear | Other | n |
|---|---|---|---|---|
| No motion | 24 | 9 | 3 | 36 |
| Trajectories | 23 | 10 | 3 | 36 |
| **Total** | 47 (65%) | 19 (26%) | 6 (8%) | 72 |

- No condition effect, χ²(2) = .07, p > .50.
- Training: correct rose from 46% (no physics) to 70% (college); curvilinear fell from 42% to 17%.
- Large sex difference here, χ²(2) = 12.49, p < .005: men 83% correct / 8% curvilinear, women 47% / 44%. Mostly in no-physics subjects. The authors can't explain it (no sex difference in Exp 1).

### Experiment 3: puck through a curved segment (acting)
**Participants.** 50 Johns Hopkins people (29 men, 21 women) recruited for "a brief psychology experiment", with no mention of physics; 14 no physics, 18 high school, 18 college.

**Apparatus.** A round table 107 cm (3.5 ft) across, a 7.5 cm black strip around its edge, and a 90° segment of a circular ring, 15.25 cm wide, painted in the middle. The "puck": a ball bearing inside a loose doughnut-shaped plastic collar 2 cm across, which glides smoothly when pushed and released. Its bottom was dipped in ink so its path left a trace.

**Trial (one per person).** Start anywhere on the black edge strip, push the puck and release it before the line marking the start of the curve, so that it goes through the curve without touching the sides. Each subject launched **once**, then filled a questionnaire (physics training, strategy, what the puck did, whether that matched expectations).

**Scoring** (ink trace + questionnaire): **correct** = aimed to release it on a straight line through the segment; **curvilinear impetus** = moved it on a curved (concave-left) path before release so it would keep curving; **spin** = tried to make it curve by spinning the ball. 2 subjects could not be classified.

**Results (Table 3, n = 48).**

| Training | Correct | Curvilinear | Spin |
|---|---|---|---|
| No physics | 6 | 5 | 2 |
| High school | 11 | 5 | 1 |
| College | 15 | 2 | 1 |
| **Total** | 32 (67%) | 12 (25%) | 4 (8%) |

- 9 of the 12 curvilinear subjects said they expected the puck to keep curving and were visibly surprised when it didn't. Counting those using other strategies who said a curved push might have worked, 35% held the belief.
- Training trend not reliable, χ²(4) = 5.11, p > .05.
- Women more often used the curvilinear strategy at no-physics and high-school levels (χ²(2) = 7.63 and 8.24, p < .05); over half the women there, none of the men. No difference for college physics.
- These are the 67% / 25% / 8% numbers in McCloskey's 1983 *Scientific American* article, so that is the same experiment.

### Human data, in short
212 people (90 + 72 + 50), **one response each**. Per condition 30 (Exp 1), 36 (Exp 2), 48 (Exp 3), so a percentage near 25% has a 95% CI of about ±14–15 points. All three experiments give about two-thirds correct and a quarter curvilinear, with no benefit of watching the motion. No raw data beyond the tables.

### Match to our stimuli
- **A2 (string release)** ↔ Exp 1: same top view, same constant-speed circle. Their release point is a single fixed position; ours uses 4 angles. Their ball is 1/10 of the circle's diameter (0.4 / 4 cm); their speed is ~0.9 revolutions/s (54 rpm). They render at 50 fps; we render at 16 fps.
- **A1 (spiral)** ↔ Exp 2: spiral tube, top view, ball exiting at constant speed. Check our spiral's turns against their Fig. 3. Their tube is transparent so the ball is visible inside it; make sure ours is too.
- Response format: a 6-alternative choice among animated or static paths (1 correct, 2–3 curved, 2–3 other). For the closest comparison, give the VLM the same 6-way choice, or score generated paths into correct / curvilinear / other in the same way.
- Exp 3 (pushing a puck) has no video counterpart; use it only as evidence that the belief also drives action.
