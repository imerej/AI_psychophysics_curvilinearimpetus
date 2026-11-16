# Study-plan deck

`study-plan-deck.pdf` presents the plan in `../paper-plan.md` (budget version) and the stimulus set in `../../stimgen/`, in the layout of the uploaded reference deck.

- Edit text in `deck.html` (one `<section>` per slide; author and course appear in each footer).
- Figures come from `figs.py`: `fig_tube.svg` is drawn from the real A1 180° item's `meta.json`; `fig_curves.svg` is illustrative, not data.
- Rebuild: `python3 figs.py && node render.js` (needs Node with Playwright and Chromium).
