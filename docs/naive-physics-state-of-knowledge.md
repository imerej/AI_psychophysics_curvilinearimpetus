# Naive physics: what we know, why, what's open, what to expect in models

Written 2026-10-20 from the papers collected in `human-baselines.md` and `three-studies-extraction.md`, plus the AI papers in `paper-plan.md`. Claims marked *(inferred)* are my reading, not a finding from a paper.

## 1. What is established

1. **People make systematic errors when they reason explicitly about motion.** About 30–50% draw a ball leaving a curved tube as still curving (McCloskey et al. 1980: 33% C tube, 51% spiral; Hubbard 2022 review), 30% for a released ball on a string, and 35–50% say an object dropped from a moving carrier falls straight down (McCloskey, Washburn & Felch 1983). Physics courses reduce the errors but don't remove them.
2. **The errors depend heavily on how you ask.** The same pendulum item gives 33% correct when drawn and 23% in forced choice (Kaiser et al. 1992). Answers shift with format and display (Cooke & Breedin 1994). People's drawings don't predict their own catching (Smith, Battaglia & Vul 2018).
3. **When people act or watch, they are much closer to Newton.** Catching a pendulum bob or timing its release fits correct physics plus noise (r ≈ 0.99), while only 22% of the same people draw the path correctly (Smith et al. 2018). Watching animations with real dynamics fixes many errors (Kaiser, Proffitt & Anderson 1985; Kaiser et al. 1992).
4. **But watching is not a cure.** It helps only when real dynamics are shown (constant-speed motion doesn't help) and for "particle" motion, where only the centre of mass matters (Kaiser et al. 1992). The curving belief still showed up with real moving objects (McCloskey & Kohl 1983), memory of an animated ball leaving a spiral is displaced along the wrong curved path (Freyd & Jones 1994), and seeing motion made apex drawings *worse* (Smith et al. 2018). What people learn from watching doesn't transfer back to paper problems.
5. **Perception itself has stable biases.** Remembered positions shift forward along the motion and downward toward gravity (representational momentum; Hubbard 2006 review). Heavier objects are expected to fall faster (Vicovaro et al. 2021). People accept pendulums that swing too slowly as natural (Pittenger 1990; Frick et al. 2005).
6. **Many "errors" look like noise, not a wrong theory.** A simulator with correct physics plus perceptual uncertainty explains many judgments (Battaglia, Hamrick & Tenenbaum 2013; Smith & Vul 2013; Smith et al. 2018).

## 2. Proposed causes (not mutually exclusive)

| Account | Claim | Main support | Main problem |
|---|---|---|---|
| **Naive theory (impetus)** | People hold a coherent wrong theory: a pushed or constrained object gets an internal "impetus" that fades | McCloskey 1980–83; interviews describe it explicitly | Answers are inconsistent across formats and people; drawings are idiosyncratic (Cooke & Breedin 1994; Smith 2018) |
| **Default heuristic** | Impetus is a quick default used when there's no better information, by experts too | Kozhevnikov & Hegarty 2001; Hubbard 2022 | Hard to tell apart from "theory" experimentally |
| **Noisy simulation** | The mind runs roughly correct physics; errors come from uncertainty and priors | Battaglia 2013; Smith & Vul 2013; Smith 2018 interactive tasks | Doesn't explain the explicit drawing errors |
| **Two systems, task decides** | Simulation drives action and perception; rule-based reasoning drives explicit answers | Smith 2018 (drawing vs catching dissociation) | Authors favour it but can't rule out one system with different noise |
| **Perceptual illusion** | Straight-down belief comes from *seeing* motion relative to the carrier | McCloskey, Washburn & Felch 1983; Kaiser 1992 (fixed camera → drawn backward) | Specific to carrier problems |
| **Everyday experience** | Errors are over-generalised real-world regularities (friction slows things, air drag, things usually move the way they were going) | U-shaped development, worst at ages 10–12 (Kaiser et al. 1986); people prefer air-resistance paths (Kaiser 1992) | Humans' experience can't be controlled, so it's never tested directly |
| **Dimensionality** | Animation helps only when one dimension of motion matters (particle vs extended body) | Kaiser et al. 1992; Proffitt & Gilden 1989 | Explains when watching helps, not why errors exist |

## 3. Hypotheses still to be proved

- **One engine or two?** Are explicit errors a separate rule-based system, or the same simulator read out more noisily?
- **Where the biases come from.** Are they learned from the statistics of everyday visual experience (friction, drag, constrained motion), or a built-in prior? This can't be tested in humans because their experience can't be controlled. *(inferred: this is where models can contribute, since their training data can be controlled.)*
- **Why watching sometimes helps and sometimes doesn't.** "The motion state is fully shown" (Kaiser) fits some results, but not Freyd & Jones or the Smith apex result.
- **Theory or heuristic?** Is impetus a belief people hold, or a shortcut used under time pressure?
- **Straight-down: seeing or believing?** It is partly perceptual, but how much remains open.
- **Do the classic numbers replicate?** Most come from ~50 students at one university, often answering each item once. There are few modern, large replications with dynamic stimuli. *(inferred from what I found; Shaffer et al. 2022 is one for carried objects.)*

## 4. What to expect in world models and VLMs

What other AI work already shows:
- Video models generalise inside their training distribution but fail outside it, retrieving similar training cases (Kang et al. 2024).
- Real-video continuation physics is poor and unrelated to visual realism (Physics-IQ, Motamed et al. 2025).
- V-JEPA 2 matches human *accuracy* on Physion but makes different errors (κ ≈ 0.48 vs 0.91 between humans; Li et al. 2026).
- Plausibility is decodable from inside video models even when their generations are wrong ("Invisible Hand", Esmati et al. 2026).

Expectations *(inferred)*:
1. **Non-human failures will probably dominate.** Expect the ball to vanish, stop, morph or snap back to stereotyped motion more often than to curve in the human way. Score validity first; that result is still publishable ("accurate or wrong, but not wrong like us").
2. **Readout will matter, as task matters in humans.** Generating a continuation is the analogue of drawing; likelihood or plausibility scoring is the analogue of watching and judging. A generate-vs-judge dissociation is plausible given the Invisible Hand result.
3. **Single still vs clip.** From a still, velocity is unknown, so expect regression to typical motion from training data, which could look like impetus where circular motion is common. With a clip, expect better extrapolation if the model reads velocity.
4. **Real-world priors will look like human "biases".** Training videos have friction and air drag, so models may slow objects down or shorten falls. Humans prefer air-resistance paths too (Kaiser 1992). Decide in advance whether that counts as a bias, since in the real world it isn't wrong.
5. **Carrier frame.** A fixed camera with a moving trolley is where humans show the frame-relative illusion. Models trained on hand-held or tracking footage might show a camera-frame version of it.
6. **VLMs on diagrams: contamination risk.** The McCloskey problems and their correct answers are in textbooks and online, so a VLM may give the textbook answer without "reasoning". Use new renderings and variants, and compare against reworded or mirrored versions. Expect sensitivity to wording and answer format, as in humans.
7. **Where models can beat human studies.** Small models trained from scratch with controlled amounts of curved or constrained motion can test the "learned from experience" account directly, which is impossible with people.
