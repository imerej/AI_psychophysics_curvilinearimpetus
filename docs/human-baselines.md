# Human baselines for each stimulus family

Written 2026-10-17 for matching the AI stimuli to the original human studies, since the human experiments will not be rerun.

**Link status.** ✅ = I opened the page and it showed this paper. 🔗 = the DOI comes from a publisher or university record I opened, but doi.org / PsycNET block automated checks, so I could not click through it myself. ⚠️ = DOI taken from the standard citation, not confirmed by any page I opened. Open PDFs are listed only when I reached the file.

**The one thing that matters most for matching.** Human error rates depend heavily on the response format, not just the picture. The same pendulum item gives 33% correct when drawn and 23% correct in 5-option forced choice (Kaiser et al. 1992), and Cooke & Breedin (1994) found impetus answers come and go with format and display. So for each family, the number to compare against is the one from the study whose *format* our item copies: drawn paths → McCloskey/Caramazza; forced-choice still → Kaiser 1992 Exp 1A; "which looks natural" on animations → Kaiser 1985/1992; occluded prediction → Smith et al. 2018.

---

## How much human data each study has

"Responses per person" is the number of answers each participant gave to the items we would compare against. "Raw data" means trial- or participant-level data that someone could reanalyse. **None of these studies has public raw data that I could find**, so every comparison has to use the percentages or means printed in the papers. "?" means I could not find it in any text I could open; the full paper should have it.

| Family | Study | Participants | Responses per person | What is reported | How solid |
|---|---|---|---|---|---|
| A1 | McCloskey et al. 1980 | ~47–50 students (15 no physics, 22 high-school, 10 college) | 1 drawing per tube shape (C, spiral) | % curved per item, by physics background | **Thin**: one answer per item, ~50 people, one university. A 95% CI on 51% at n=50 is about ±14 points. |
| A1 | McCloskey 1983 chapter | same ~48; 13 interviewees | as above | Same %; qualitative interviews | Same data, more description |
| A1 | McCloskey & Kohl 1983 | Exp 2: 72 (spiral; 36 no motion, 36 watched 6 animated paths); Exp 3: 50 (puck, 48 scored) | 1 choice (Exp 2) or 1 launch (Exp 3) per person | Counts correct / curvilinear / other by condition and physics level (Exp 2: 65 / 26 / 8%; Exp 3: 67 / 25 / 8%) | **Moderate**: n=36 per condition, one answer each |
| A1 | Kaiser, Proffitt & Anderson 1985 | ? adults + 5th graders | Forced choice over several animated vs static paths | Choice preferences by condition and gender | ? (sample sizes not in the abstracts I read) |
| A1 | Kaiser et al. 1986 | ? children aged 4–12 + college students | 1 drawing per tube (straight, C, spiral) | % curved by age | ? |
| A1 | Freyd & Jones 1994 | ? (several experiments) | Many probe trials per person (typical for this method) | Mean memory displacement | ? (PDF is a scan I could not read) |
| A1 | Cooke & Breedin 1994 | ? | Several formats per person | % by format | ? |
| A1 | Kallai & Reiner 2010 | ? | Many trials (EEG) | Abstract only | **Weak**: conference abstract, not peer reviewed |
| A2 | McCloskey et al. 1980 / 1983 | ~48–50 students | 1 drawing | 30% curved, 51% correct, 19% other | **Thin**, as for A1 |
| A2 | McCloskey & Kohl 1983 Exp 1 | 90 (30 per condition: no motion, rotation, 6 animated paths) | 1 choice of 6 per person | Counts correct / curvilinear / centrifugal per condition (total 67 / 24 / 9%) | **Moderate**: n=30 per condition |
| A2 | Hubbard 1996 | ? | Many probe trials | Mean displacement | ? (no release condition anyway) |
| A3 | Caramazza et al. 1981 | ? (the companion report says "about a quarter" correct) | 4 cut points per person | % correct by cut point | ? |
| A3 | Kaiser et al. 1992 Exp 1A / 1B | 80 / 48 | 1A: 2 drawings + 2 choices; 1B: 10 pairs per cut point × 2 cut points | % correct; mean correct out of 4 | **Moderate**: decent N, but only apex and nadir |
| A3 | **Smith, Battaglia & Vul 2018** | Exp 1: 32 (35 recruited); Exp 2: 67 (33 motion, 34 static) | Exp 1: **240 catching + 240 cutting trials** (48 items × 5) + 4 drawings; Exp 2: 4 drawings | Item-level fits to a physics model, drawing classifications | **Best in the set**: many trials per person, all 4 cut points. Their supplement has 2 movies of the task, but I found no public data. |
| B1 | McCloskey, Washburn & Felch 1983 | 177 (paper), 120 (two dynamic exps), 18 (computer displays), 36 (videotape) | ~1 per problem | % forward / straight down / backward | **Moderate**: the largest sample here, but one answer per item |
| B1 | McCloskey 1983 | 48 (airplane), 18 (video) | 1 | % by answer type | Thin |
| B1 | Kaiser et al. 1992 Exp 2A / 2B | 40 / 40 | 2A: drawings of 6 animations; 2B: all 15 pairs × 2 | % by trajectory type | Moderate |
| B1 | Kaiser, Proffitt & McCloskey 1985 | 100 children + 20 adults (Exp 1); 22 children + 17 adults (Exp 2) | ~1–6 placements | % straight down by age | **Thin for adults** (20 and 17) |
| B1 | Shaffer et al. 2022 | 42, 43, 64, 46 across 4 exps | 1–2 per exp | % biased answers | Moderate, and recent |
| C1 | **Frick et al. 2005** | 48 adults + 48 children, **16 per task** | 18 trials (9 length × bob combinations × 2) | Strategy counts, between-block consistency, constant error | **Thin per cell**: only 16 adults did the watching (adjustment) task |
| C1 | Pittenger 1985, 1990 | ? | ? | Detection rates | ? |
| C1 | Bozzi 1958 | ? | ? | Natural-period settings | ? (no copy online) |
| D1 | none | — | — | — | No human data |

**What this means for the paper.** For most families the human reference is a single percentage from 40–100 people, each answering an item once. That supports a coarse comparison (does the model show the bias at all, and in which direction?) but not item-level alignment or a human–human noise ceiling, which need many responses per item. Only Smith et al. 2018 (pendulum cut, interactive tasks) comes close, and even there the raw data aren't public; it could be worth emailing Kevin Smith. Report CIs on the human percentages, since at n≈50 they are about ±14 points. One inconsistency: MITECS (Proffitt) quotes "about 40%" wrong on the C tube for McCloskey et al. 1980, while the 1980 press report and the chapter give 33% (C) and 51% (spiral); use the paper's own figures.

---

## A1. Ball leaving a curved tube (curvilinear impetus)

| Study | Stimulus | Format and sample | Result | Link |
|---|---|---|---|---|
| **McCloskey, Caramazza & Green 1980**, *Science* 210:1139–1141 (the original) | Static line drawing, tube lying flat, seen from above; ball "shot out at high speed". A C-shaped tube and a spiral tube. Exact arc of the C and number of spiral turns are not given in any text I could read; check the figure in the paper. | Draw the path after exit. ~47–50 Johns Hopkins students (15 no physics, 22 high-school, 10 college physics) | Curved path drawn by **33% (C tube)** and **51% (spiral)** | DOI [10.1126/science.210.4474.1139](https://doi.org/10.1126/science.210.4474.1139) ⚠️ (resolver blocked; citation confirmed on [Harvard page](https://cogneuro.psychology.fas.harvard.edu/publications/curvilinear-motion-absence-external-forces-na%C3%AFve-beliefs-about-motion-objects) ✅ and in the [1980 press report](https://www.csmonitor.com/1980/1217/121733.html) ✅) |
| **McCloskey 1983, "Naive theories of motion"** (chapter in *Mental Models*; free preprint) | Same spiral tube figure, plus a circular tube with a 90° segment removed (a 270° arc) | Same data, more detail on drawings | 51% curved on the spiral; most curved answers *gradually straighten* | Open PDF [ERIC ED223417](https://files.eric.ed.gov/fulltext/ED223417.pdf) ✅ |
| **McCloskey & Kohl 1983**, *JEP:LMC* 9:146–156 | Exp 2: CRT seen from above, transparent spiral tube 5.5 cm wide, ball 0.4 cm at 12.2 cm/s, 50 fps; no motion vs watching 6 animated exit paths twice each, then choose 1 of 6. Exp 3: push a puck through a 90° ring segment (15.25 cm wide) painted on a 107 cm table | Exp 2 n=72, Exp 3 n=50 | Exp 2: 26% curvilinear, no effect of watching (χ²(2)=.07). Exp 3: 25% pushed the puck along a curve expecting it to keep curving | DOI [10.1037/0278-7393.9.1.146](https://doi.org/10.1037/0278-7393.9.1.146) 🔗 ([JHU record](https://pure.johnshopkins.edu/en/publications/naive-physics-the-curvilinear-impetus-principle-and-its-role-in-i-3/) ✅) |
| **Kaiser, Proffitt & Anderson 1985**, *JEP:LMC* 11:795–803 (**key animated version**) | Computer animation of a ball leaving a C-shaped or spiral tube, vs static depictions of the same paths | Forced choice / naturalness; adults and 5th graders | Correct path chosen more often with motion; static errors return after animation; imagery instructions don't help | DOI [10.1037/0278-7393.11.1-4.795](https://doi.org/10.1037/0278-7393.11.1-4.795) 🔗 ([NASA record](https://ntrs.nasa.gov/citations/19860032184) ✅) |
| Kaiser, McCloskey & Proffitt 1986, *Dev. Psych.* 22:67–71 | Drawings of straight, C and spiral tubes | Draw; ages 4–12 and adults | U-shaped: school-age children worst | DOI [10.1037/0012-1649.22.1.67](https://doi.org/10.1037/0012-1649.22.1.67) 🔗 ([record](https://uva.theopenscholar.com/dennis-proffitt/publications/development-intuitive-theories-motion-curvilinear-motion-absence) ✅) |
| **Freyd & Jones 1994**, *JEP:LMC* 20:968–976 (dynamic, memory) | Animated target moving through a spiral tube, then exiting on a straight, curved or spiral path before vanishing | Representational-momentum probe of remembered final position | Forward memory displacement was **largest for the (wrong) spiral exit**, so a curving bias survives in perception of motion | Open PDF (scanned) [uoregon.edu](https://dynamic.uoregon.edu/jjf/articles/freydjones94.pdf) ✅; DOI 10.1037/0278-7393.20.4.968 ⚠️ |
| Cooke & Breedin 1994, *Mem. & Cog.* 22:474–493 | Several displays and response formats | Draw or select paths | Little evidence for a stable impetus theory; answers are "constructed on the fly" from format and display | [10.3758/BF03200871](https://link.springer.com/article/10.3758/BF03200871) ✅ |
| Kallai & Reiner 2010 (conference abstract, not peer reviewed) | Animated virtual spiral tube, straight vs curved exit | Classification + catching, EEG | Implicit (N400) sensitivity to wrong curved motion even in people with the misconception | [Frontiers abstract](https://www.frontiersin.org/10.3389/conf.fnins.2010.11.00065/event_abstract) ✅ |

**stimgen vs originals.**
- View (top-down, tube flat, ball exits on a plane with no gravity) matches. ✓
- Originals have only **two curved shapes, C and spiral**. stimgen has c90, c180, c270 and spiral; only the spiral and one C-equivalent map onto a published human rate. Our spiral is **1.125 turns** (`phi` up to 2.25π); check this against the figure in the 1980 paper before claiming a match. The 270° tube matches the "circle with 90° removed" in McCloskey 1983, but that item has no group percentage.
- Straight tube control is in Kaiser et al. 1986 (everyone answers straight), so it has a human baseline. ✓
- `options.png` is 4-choice; the 33%/51% are from **free drawing**. Compare 4AFC answers with Kaiser 1985, or classify model/human-free-drawn paths the McCloskey way.
- Speeds (1.2 and 2 m/s) have no counterpart: the originals say only "high speed". Not a mismatch, just no human data on speed.

## A2. Ball on a string, string breaks

| Study | Stimulus | Format and sample | Result | Link |
|---|---|---|---|---|
| **McCloskey et al. 1980 / McCloskey 1983** | Static drawing: ball whirled in a horizontal circle, seen from above; string breaks at the drawn point | Draw path; ~48–50 students | **30% curved** (most gradually straightening), 51% correct tangent, 19% other | 1980 DOI above ⚠️; Sci. Am. 248(4):122–130 (citation confirmed on [academia.edu copy](https://www.academia.edu/28201242/Intuitive_Physics) ✅); [ERIC preprint](https://files.eric.ed.gov/fulltext/ED223417.pdf) ✅ |
| **McCloskey & Kohl 1983** Exp I | CRT seen from above: ball 0.4 cm on a 4 cm circle at 54 rpm, 50 fps; no motion / watch the rotation / watch 6 animated release paths twice each; choose 1 of 6 | n=90 | 24% curvilinear, 9% outward, 67% correct; no effect of condition (χ²(4)=1.76) | as above 🔗 |
| Hubbard 1996, *JEP:LMC* 22:1049–1060 (dynamic, memory) | Animated target on a circular orbit (no release) | Remembered position | Displaced forward along the tangent **and inward**, more with larger radius and speed | DOI 10.1037/0278-7393.22.4.1049 ⚠️; summary in [Hubbard 2006 review](https://www.uv.es/revispsi/articulos1.06/1HUBBARD.pdf) ✅ |

**stimgen vs originals.** Top view and horizontal circle match. ✓ The originals show **one** release point; our 4 release angles are a superset (fine, as rotations of the same item). No human data on speed or radius.

## A3. Pendulum string cut

| Study | Stimulus | Format and sample | Result | Link |
|---|---|---|---|---|
| **Caramazza, McCloskey & Green 1981**, *Cognition* 9:117–123 (the original) | Static drawings of a swinging pendulum, string cut at several points of the arc | Free drawing; "sophisticated" (physics-trained) students | Correct free-hand drawings: **apex 32%, nadir 25%** (as re-reported by Kaiser 1992); common error = continue along arc, then fall straight down | [10.1016/0010-0277(81)90007-X](https://doi.org/10.1016/0010-0277(81)90007-X) ✅ (resolves to Elsevier) |
| **Kaiser, Proffitt, Whelan & Hecht 1992**, *JEP:HPP* 18:669–689 (**key animated version**) | Exp 1A static (n=80): drawing + 5-option choice, cut at apex or nadir. Exp 1B (n=48): static vs constant-speed "kinematic" vs **full animation showing two complete swings, cut during the third**, five candidate paths | Pairwise "which looks more natural" | Drawing correct: apex 33%, nadir 55%; forced choice: apex 23%, nadir 84%. Animation helped at the apex (3.00 vs 2.29 of 4 correct), not at the nadir | Open PDF [gwern.net](https://www.Gwern.net/doc/psychology/cognitive-bias/illusion-of-depth/1992-kaiser.pdf) ✅; DOI [10.1037/0096-1523.18.3.669](https://doi.org/10.1037/0096-1523.18.3.669) 🔗 ([record](https://uva.theopenscholar.com/dennis-proffitt/publications/influence-animation-dynamical-judgments) ✅) |
| **Smith, Battaglia & Vul 2018**, *Computational Brain & Behavior* 1:101–118 (**best modern match**) | Cord = half screen height, **amplitude 35°, period 2.5 s**. Exp 1 (n=32): catch with a bucket / choose when to cut, ball path hidden, 48 trials ×5; plus drawing on Caramazza's 4 diagrams. Exp 2 (n=67): drawing at **apex, nadir, downswing, upswing** after watching one swing vs a still | Bucket placement, cut timing, on-screen drawing | Interactive answers ≈ Newton + noise (r ≈ .99); only 22% drew physics-consistent paths, 6% all four right. Apex drawing correct 24% static vs 6% with motion | Open PDF [MIT DSpace](https://dspace.mit.edu/handle/1721.1/131487) ✅; DOI [10.1007/s42113-018-0007-3](https://doi.org/10.1007/s42113-018-0007-3) 🔗; [preprint](https://www.mit.edu/~k2smith/pdf/SmithBattagliaVul_DiffPhysInt_Preprint.pdf) ✅ |

**stimgen vs originals.**
- Our 4 cut phases (turning, descending, bottom, ascending) are exactly Smith et al.'s apex, downswing, nadir, upswing. ✓ This is the best-matched family.
- Amplitude is **40°** in stimgen vs **35°** in Smith et al. (Kaiser 1992 doesn't state it in what I read). Changing `THETA0` to 35° would match.
- Context: Kaiser 1992 showed **two full swings before the cut**; Smith Exp 2 one swing. stimgen cuts after about one period. Fine for Smith; for Kaiser's numbers you'd want ~2 cycles.
- Our occluded clip (click where the ball comes out) is closest to Smith's catching task, so compare it with "Newton + noise", not with the drawing error rates.

## B1. Object dropped from a moving carrier (straight-down belief)

| Study | Stimulus | Format and sample | Result | Link |
|---|---|---|---|---|
| **McCloskey, Washburn & Felch 1983**, *JEP:LMC* 9:636–649 (the original) | Paper problems (n=177); concrete dynamic problem and **dropping a ball while walking** (n=120); **computer-generated displays** (n=18) and a **videotape of a walking person dropping a ball** (n=36) | Draw / act / report what was seen | About half predict or *see* a straight-down fall; proposed cause is a perceptual illusion with the carrier as reference frame | DOI [10.1037/0278-7393.9.4.636](https://doi.org/10.1037/0278-7393.9.4.636) 🔗 ([JHU record](https://pure.johnshopkins.edu/en/publications/intuitive-physics-the-straight-down-belief-and-its-origin-3/) ✅) |
| McCloskey 1983 (Sci. Am. / chapter) | Airplane drops a ball (drawing, n=48); walking person (verbal); videotape (n=18) | Draw / report | Airplane: 40% parabola, **36% straight down**, 13% diagonal, 11% backward. Walking: 45% forward, **49% straight down**, 6% back. Video: 4 forward, 10 straight down, 4 backward | [ERIC preprint](https://files.eric.ed.gov/fulltext/ED223417.pdf) ✅ |
| **Kaiser et al. 1992** Exp 2 (**key animated version**) | 3D animation: airplane over farmland drops a keg after 1.5 s. Camera **stationary** (plane crosses screen) or **dolly** (camera tracks plane). Six paths with horizontal speed −0.25, 0, 0.5, 1.0, 1.0→0.5, 1.2 × plane speed | 2A: draw after viewing twice (n=40); 2B: pairwise naturalness (n=40) | Stationary camera: straight-down clips were *drawn* as going backward. Naturalness: forward preferred 82%, straight down 15–18%, vs 53/36/11% in McCloskey's drawings | PDF and DOI as above ✅ |
| Kaiser, Proffitt & McCloskey 1985, *Percept. Psychophys.* 38:533–539 | Real HO-scale toy train on a 1 m table vs a ball rolled off the table | Place a cup where it lands; children and 20 adults | Adults: all right for the rolled ball, **35% straight down for the carried ball** | [10.3758/BF03207062](https://doi.org/10.3758/BF03207062) ✅ (resolves to Springer) |
| Shaffer et al. 2022, *Atten. Percept. Psychophys.* 84:1699–1717 (modern video version) | Filmed runners passing a ball (3.9–5.3 m/s), stationary camera | Choose direction / draw; n=42–64 per exp | 70–87% discount the carrier's forward motion | [10.3758/s13414-022-02514-2](https://link.springer.com/article/10.3758/s13414-022-02514-2) ✅ |

**stimgen vs originals.**
- Side view with a fixed camera and a visible moving carrier matches Kaiser's *stationary* condition and the walking videotape. ✓ That's the condition where the illusion shows; don't add camera tracking.
- Carrier: originals use a walking person, a toy train or an airplane; ours is a trolley on a rail. Closest physical match is the toy train (Kaiser 1985). Speeds 0.8–2.4 m/s span walking pace (~1.4 m/s), fine.
- Our anomalies are straight-down only. Kaiser's set also has **backward (−0.25)**, half-speed and too-fast (1.2) paths; the options.png already has backward and 1.8× too far, but the video anomalies don't.

## C1. Pendulum period (length, bob size)

| Study | Stimulus | Format and sample | Result | Link |
|---|---|---|---|---|
| **Frick, Huber, Reips & Krist 2005**, *Swiss J. Psych.* 64:103–114 (**best match**) | 3D virtual room on a CRT, "string with a brick". Lengths **60, 120, 180 cm**; bob width 15/30/45 cm (apparent mass only); **30° amplitude** | Judgment (rate time for 50 swings), imagery (hold a button for 3 cycles), perception (**adjust an animated pendulum that starts 10/20/30% too fast or slow**). 48 adults, 48 children, 16 per task | Watching: 12/16 adults use length only. Judging: many use mass, **in both directions**: 6 adults "heavier = slower", 3 "heavier = faster". Adults set the natural period **~16% too slow** | Open PDF [KOPS](https://kops.uni-konstanz.de/bitstreams/ca53c74e-8007-4b97-b457-9ff973ef53e7/download) ✅; DOI [10.1024/1421-0185.64.2.103](https://doi.org/10.1024/1421-0185.64.2.103) 🔗 ([record](https://kops.uni-konstanz.de/items/version/1159) ✅) |
| Pittenger 1990, *Ecological Psychology* 2:55–81 | Real adjustable pendulum apparatus | Detect violations of the length–period law | Sensitive to violations, but slower-than-correct motion looks natural; a pendulum 0.33 s too slow was rated natural | DOI 10.1207/s15326969eco0201_3 ⚠️ (details via Frick 2005) |
| Pittenger 1985, *Perception* 14:247–256 | Pendulum motion | Estimate length from motion | People recover length from period | [10.1068/p140247](https://doi.org/10.1068/p140247) ✅ (resolves to SAGE) |
| Bozzi 1958, *Rivista di Psicologia* | Mechanical pendulums 10–40 cm | Set "natural" period | Natural periods longer than real; mass beliefs split | No online copy found |

**stimgen vs originals.**
- **The paper plan's "heavier pendulums swing faster" is not what the human data say.** Mass beliefs show up only in verbal/judgment tasks and go both ways, more often heavier = *slower*. When people watch, they mostly ignore bob size. Worth correcting H-numbers in `paper-plan.md`.
- Amplitude 25° in stimgen vs 30° in Frick. Lengths 0.6–2.7 m in stimgen vs 0.6–1.8 m; 2.1 and 2.7 m have no human data (already flagged `out_of_range` for 2.7).
- Our anomalies are ±20% period. Humans accept ~16% too slow as natural, so the **slow** 2AFC item may sit inside the human acceptance range; the fast one should be easier. That asymmetry is itself a human baseline to compare against.
- Frick changes mass by bob width with fixed height; ours scales the whole disc (radius 7 vs 14 px). Close enough, but note it.

## D1. Double pendulum

**No human baseline found.** I searched for human prediction of double-pendulum or other chaotic motion and found none; the reviews (Kubricht, Holyoak & Lu 2017, [TICS 21:749–759](https://reasoninglab.psych.ucla.edu/wp-content/uploads/sites/273/2021/04/Kubrich_etal.TICS_.2017.pdf) ✅) don't cover it either. Since humans won't be retested, D1 can only be compared with the noisy-Newton ensemble, not with people. Say so in the paper.

---

## Further reading (overviews)

- Hubbard 2022, "The possibility of an impetus heuristic", *Psychon. Bull. Rev.* 29:2015–2033, [10.3758/s13423-022-02130-z](https://link.springer.com/article/10.3758/s13423-022-02130-z) ✅. Recent review; puts impetus-consistent answers at 30–50% across lab studies.
- Kozhevnikov & Hegarty 2001, "Impetus beliefs as default heuristics", *Psychon. Bull. Rev.* 8:439–453 ([record](https://www.nmr.mgh.harvard.edu/publications/journal_articles/4780) ✅, PMID 11700895). Physics experts show the same implicit impetus in representational momentum as novices.
- Vicovaro et al. 2021, "Evidence of weight-based representations of gravitational motion", *JEP:HPP*, [preprint](https://research.unipd.it/bitstream/11577/3418141/1/JEPHPP2021.pdf) ✅. Realistic animated falls; heavier objects are expected to fall faster.
