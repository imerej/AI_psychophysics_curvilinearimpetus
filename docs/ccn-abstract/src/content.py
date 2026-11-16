TITLE = "Impetus in the Machine: Do Video Generators and World Models Make Human-Like Errors About Curved Motion?"
AUTHORS = "Jérémie Robin and Han Sem Sohn"
AFFIL = "AI Psychophysics, Sungkyunkwan University"
EMAIL = ""  # contact e-mails left out of the public repo

ABSTRACT = ("Asked where a ball goes after it leaves a curved tube, many people say it keeps curving, although physics predicts a straight path. "
"This \u201cimpetus\u201d error is one of the best-known misconceptions in intuitive physics. AI video models are increasingly used as learned "
"simulators of the physical world, but they are evaluated on whether they are right, not on whether they are wrong in the same way as people. "
"We showed two kinds of video models short clips of a ball rolling through tubes of different shapes, stopping just before it exits. A video "
"generation model, asked to continue the clip, made the ball keep curving in about two thirds of cases, more often than people in classic studies, "
"and almost never after a straight tube. A world model, asked instead which ending was more surprising, preferred the correct straight path. "
"The same input therefore produces a human-like error when a model must generate the future, but not when it evaluates it, echoing the gap in "
"people between predicting a path and judging a moving display. Comparing how models are wrong, not only how often, gives a sharper test of what "
"physical knowledge they learn.")

# (kind, text). kinds: H1, H2, P, FIG, CAP, REF
BODY = [
("H1","Introduction"),
("P","When people reason explicitly about motion they make systematic errors. In the curved-tube problem, 33% of students drew a ball leaving a "
"C-shaped tube as still curving, and 51% did so for a spiral (McCloskey, Caramazza, & Green, 1980); with a six-alternative choice the rate was "
"26% (McCloskey & Kohl, 1983). The error depends on the task: people judge more accurately when they rate animated trajectories as natural or not than when they reason from a still diagram (Kaiser, Proffitt, & Anderson, 1985), although watching does not always help (McCloskey & Kohl, 1983). "
"People who draw wrong paths also act on moving objects as if they simulated correct physics with some noise "
"(Smith, Battaglia, & Vul, 2018; Battaglia, Hamrick, & Tenenbaum, 2013)."),
("P","Video models learn physics only from the statistics of what they see, so they can test whether such errors arise from visual experience. "
"Existing evaluations report accuracy (Bordes et al., 2025; Garrido et al., 2025; Kang et al., 2024; Motamed et al., 2025), and models can match "
"human accuracy while making different errors (Li et al., 2026). We ask a narrower question with a known human signature: after a curved "
"tube, do models continue the curvature? We contrast a model that generates the future with one that only evaluates it, an analogue of the "
"human contrast between predicting a path and judging a moving display."),
("H1","Methods"),
("P","*Stimuli.* We rendered 30 items in Blender (768 × 512 px, 24 fps): a red striped ball rolling through a tube on a table, seen from above. "
"Tubes were a straight control, 90°, 180° and 270° arcs and a 1.1-turn spiral, at two speeds (120 and 200 px/s), with three layout variants. "
"Model inputs were the last 33 frames before the exit, ending one frame before the ball reaches the tube mouth. For each item we also rendered "
"the true straight continuation and a foil that keeps the tube's curvature."),
("P","*Generation.* LTX-Video 0.9.5 (2B; HaCohen et al., 2024) was conditioned on the clip and generated 81 frames, six samples per item. The prompt "
"named the direction the ball was heading at the exit, which if anything favours going straight. We tracked the ball and compared the heading of "
"the late path with the exit tangent: a turn of more than 5° towards the side the tube bends was scored *curving*, more than 5° the other way "
"*outward*, otherwise *straight*. These rules were fixed before any output was seen, and scored the true and foil paths correctly. Clips where "
"the ball was lost, stopped or degraded, or where the tube deformed or a second ball appeared, were excluded (36 of 180)."),
("P","*Evaluation.* V-JEPA 2 (ViT-L; Assran et al., 2025) encoded 8 context frames and predicted 8 future frames; surprise was the L1 prediction "
"error on the tokens covering the ball, in a crop around the exit (cf. Garrido et al., 2025). An item *prefers curving* when the curving foil is "
"less surprising than the true path. As a check, a ball that stops dead raised surprise on all 30 items."),
("P","*Human comparison.* We compared the models with published human data on the same problem: drawn paths for a C-shaped tube (33% curving) "
"and a spiral (51%; McCloskey et al., 1980), and a six-alternative choice for a spiral (19 of 72 curvilinear, 26%; McCloskey & Kohl, 1983). "
"We match the C-shaped tube to our 180° arc and the spiral to our spiral, which has fewer turns (1.1 vs about 2)."),
("FIG",None),
("CAP","Figure 1: (A) Tracked paths of six LTX-Video continuations (magenta) for one 270° item, with the true straight exit (bright green) and the "
"curving foil (dark green). (B) Curving responses by tube shape. Blue: valid LTX-Video clips, with Wilson 95% CIs. Orange: V-JEPA 2 items "
"(6 per shape) for which the curving exit was less surprising (median surprise gap, curving minus straight: +0.5% straight, "
"+0.4% 90°, +2.2% 180°, +2.2% 270°, +2.7% spiral). Black: published human rates for the C-shaped tube (plotted at 180°) and the spiral."),
("H1","Results"),
("P","*Generation reproduces the error.* LTX-Video continued the curvature on 81 of 120 valid curved-tube clips (68%), against 1 of 24 on the "
"straight control (4%; Fisher exact, one-sided, p ≈ 4 × 10⁻⁹; Figure 1B). At the item level, 17 of 24 curved items curved on most samples "
"(Mann–Whitney p < .001). Rates were 62% to 77% across shapes and 64% and 72% at the two speeds, and curving samples often followed the arc "
"for a full turn (Figure 1A). An earlier run "
"with simple 2D renders gave the same pattern (59% of 46 curved-tube clips vs 1 of 11 straight). From a single still frame, the model "
"mostly froze the scene (36 of 60 clips invalid), so we report clip conditioning only."),
("P","*Evaluation does not.* V-JEPA 2 found the curving exit more surprising than the straight exit on 22 of 24 curved items (median +1.8%), so "
"it showed no impetus preference. The preference was weakest for the straight tube and the 90° arc (median gaps +0.5% and +0.4%, vs "
"+2.2% to +2.7% for the tighter curves). The straight-tube foil is only a gentle control bend (radius 120 px), so the two futures "
"barely diverge within the 0.7 s predicted, and 1 of its 6 items flipped. The differences are small, and the measure tracks predictability rather than plausibility (a ball that "
"vanishes scores as *less* surprising), so it is valid only between futures with the same content, as here."),
("P","*Comparison with humans.* The generator curved more often than people. On the C-shaped (180°) tube it curved on 70% of clips, against 33% "
"of drawn paths. On the spiral it curved on 59% of clips, against 51% of drawn paths and 26% of choices (16/27 vs 19/72; Fisher exact, "
"one-sided, p = .003). Its curves were also more extreme: people who draw a curve usually draw it gradually straightening (McCloskey, 1983)."),
("H1","Discussion"),
("P","A video generator trained on natural video reproduces, and exceeds, a classic human misconception about motion, while a latent predictive "
"model does not. The generator saw the motion and was told the exit direction, so missing velocity information does not explain the curving. "
"A plausible source is training statistics: objects seen moving along curves usually keep curving because something constrains them, so a "
"generator that extends the most typical motion extends the arc. This is the experience-based account of the human error, which cannot be "
"tested in people but can be tested in models trained on controlled data."),
("P","The generate-versus-evaluate split mirrors the human dissociation between explicit prediction and perception (Kaiser et al., 1985; Smith et "
"al., 2018), but the two models also differ in architecture, objective and size. Scoring the generator's own likelihood of each exit is the "
"next step, along with more generators, other classic errors such as the drop from a moving carrier, and testing people on the same rendered stimuli. For world models used "
"in planning, how a model is wrong matters as much as how often."),
("H1","Acknowledgments"),
("P","[[Author contributions and funding.]]"),
("H1","References"),
("REF","Assran, M., Bardes, A., Fan, D., Garrido, Q., Howes, R., Komeili, M., ... Ballas, N. (2025). V-JEPA 2: Self-supervised video models enable understanding, prediction and planning. *arXiv:2506.09985*."),
("REF","Battaglia, P. W., Hamrick, J. B., & Tenenbaum, J. B. (2013). Simulation as an engine of physical scene understanding. *Proceedings of the National Academy of Sciences, 110*(45), 18327–18332."),
("REF","Bordes, F., Garrido, Q., Kao, J. T., Williams, A., Rabbat, M., & Dupoux, E. (2025). IntPhys 2: Benchmarking intuitive physics understanding in complex synthetic environments. *arXiv:2506.09849*."),
("REF","Garrido, Q., Ballas, N., Assran, M., Bardes, A., Najman, L., Rabbat, M., Dupoux, E., & LeCun, Y. (2025). Intuitive physics understanding emerges from self-supervised pretraining on natural videos. *arXiv:2502.11831*."),
("REF","HaCohen, Y., Chiprut, N., Brazowski, B., Shalem, D., Moshe, D., Richardson, E., ... Bibi, O. (2024). LTX-Video: Realtime video latent diffusion. *arXiv:2501.00103*."),
("REF","Kaiser, M. K., Proffitt, D. R., & Anderson, K. (1985). Judgments of natural and anomalous trajectories in the presence and absence of motion. *Journal of Experimental Psychology: Learning, Memory, and Cognition, 11*(4), 795–803."),
("REF","Kang, B., Yue, Y., Lu, R., Lin, Z., Zhao, Y., Wang, K., Huang, G., & Feng, J. (2024). How far is video generation from world model: A physical law perspective. *arXiv:2411.02385*."),
("REF","Li, F., Zheng, S., Yin, Z., Cui, J., Ji, L., & Liu, J. (2026). Human-level accuracy, non-human strategies: Revealing model-human divergence in video physical reasoning. In *Computer Vision \u2013 ECCV 2026*. Springer."),
("REF","McCloskey, M. (1983). Naive theories of motion. In D. Gentner & A. L. Stevens (Eds.), *Mental models*. Erlbaum."),
("REF","McCloskey, M., Caramazza, A., & Green, B. (1980). Curvilinear motion in the absence of external forces: Naive beliefs about the motion of objects. *Science, 210*(4474), 1139–1141."),
("REF","McCloskey, M., & Kohl, D. (1983). Naive physics: The curvilinear impetus principle and its role in interactions with moving objects. *Journal of Experimental Psychology: Learning, Memory, and Cognition, 9*(1), 146–156."),
("REF","Motamed, S., Culp, L., Swersky, K., Jaini, P., & Geirhos, R. (2025). Do generative video models understand physical principles? *arXiv:2501.09038*."),
("REF","Smith, K. A., Battaglia, P. W., & Vul, E. (2018). Different physical intuitions exist between tasks, not domains. *Computational Brain & Behavior, 1*(2), 101–118."),
]
