"""Builds the two figures used in deck.html.

fig_tube.svg  : real item A1_tube_c180_v120_s1 from the stimulus generator
                (tube walls, correct exit, impetus error), drawn from meta.json.
fig_curves.svg: illustrative predictions for H1/H2 (not data).
Run:  python3 figs.py   (needs only the standard library)
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.join(HERE, "..", "..", "stimgen", "demo", "A1", "A1_tube_c180_v120_s1", "meta.json")
RED, DARK, MID, LIGHT, BLUE, GREY = "#a01010", "#6e0b0b", "#c73a2e", "#e9917f", "#2f5fa7", "#8a8580"


def tube_figure():
    m = json.load(open(META))
    cl, hw = m["scene"]["centerline"], m["scene"]["half_width"]
    full, anom, crit = m["ball_xy"], m["anomalous_impetus_xy"], m["critical_frame"]

    def offset(sign):
        pts = []
        for i, (x, y) in enumerate(cl):
            a, b = cl[max(i - 1, 0)], cl[min(i + 1, len(cl) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy) or 1
            pts.append((x - sign * hw * dy / n, y + sign * hw * dx / n))
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    def poly(pts):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    xs_ = [x for x, _ in cl + full] ; ys_ = [y for _, y in cl + full]
    x0, y0 = min(xs_) - hw - 14, min(ys_) - hw - 30
    vw, vh = max(xs_) + 60 - x0, max(ys_) + hw + 30 - y0
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0:.0f} {vw:.0f} {vh:.0f}" font-family="Open Sans, Inter, sans-serif">']
    for sign in (1, -1):
        s.append(f'<polyline points="{offset(sign)}" fill="none" stroke="#6b6660" stroke-width="2.2"/>')
    # impetus error: dashed path after exit
    s.append(f'<polyline points="{poly(anom[crit:])}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-dasharray="6 5"/>')
    for x, y in anom[crit + 4::4]:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="none" stroke="{BLUE}" stroke-width="1.5"/>')
    # correct path: strobe every 3rd frame
    for x, y in full[::3]:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#e61e1e" opacity="0.9"/>')
    ex, ey = full[crit]
    s.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="8" fill="none" stroke="#222" stroke-width="1.5"/>')
    s.append(f'<text x="{ex-8:.0f}" y="{ey-16:.0f}" font-size="11" fill="#333">exit = critical frame</text>')
    s.append(f'<text x="250" y="62" font-size="11" fill="{RED}" font-weight="600">Newtonian: straight</text>')
    s.append(f'<text x="250" y="155" font-size="11" fill="{BLUE}" font-weight="600">impetus error</text>')
    s.append(f'<text x="250" y="168" font-size="11" fill="{BLUE}">keeps curving</text>')
    bx, by = full[0]
    s.append(f'<text x="{bx+16:.0f}" y="{by+5:.0f}" font-size="11" fill="#555">← ball enters (top-down view)</text>')
    s.append("</svg>")
    open(os.path.join(HERE, "fig_tube.svg"), "w").write("\n".join(s))


def curves_figure():
    # Illustrative only: share of impetus-type paths by tube shape.
    xs = ["straight", "90°", "180°", "270°", "spiral"]
    series = [
        ("Humans · static diagram", DARK, None, [4, 18, 30, 38, 48]),
        ("Humans · watching motion", LIGHT, None, [3, 6, 9, 11, 14]),
        ("Model · single frame (H1)", BLUE, "7 5", [8, 22, 34, 42, 52]),
        ("Model · short clip (H2)", "#8fb0dd", "7 5", [6, 12, 18, 23, 28]),
    ]
    W, H, L, R, T, B = 640, 400, 70, 20, 20, 60
    pw, ph = W - L - R, H - T - B
    X = lambda i: L + pw * i / (len(xs) - 1)
    Y = lambda v: T + ph * (1 - v / 60)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Open Sans, Inter, sans-serif">',
         f'<rect x="{L}" y="{T}" width="{pw}" height="{ph}" fill="#fff"/>']
    for v in range(0, 61, 15):
        s.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(v)}" y2="{Y(v)}" stroke="#e8e4de"/>')
        s.append(f'<text x="{L-10}" y="{Y(v)+4}" font-size="13" text-anchor="end" fill="#444">{v}</text>')
    for i, lab in enumerate(xs):
        s.append(f'<text x="{X(i)}" y="{T+ph+22}" font-size="13" text-anchor="middle" fill="#444">{lab}</text>')
    s.append(f'<line x1="{L}" x2="{L+pw}" y1="{Y(0)}" y2="{Y(0)}" stroke="{GREY}" stroke-width="2"/>')
    s.append(f'<text x="{L+pw-6}" y="{Y(0)-7}" font-size="12" text-anchor="end" fill="{GREY}">Newton (0 %)</text>')
    for name, col, dash, ys in series:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(ys))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"{d}/>')
        if not dash:
            for i, v in enumerate(ys):
                s.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="4.5" fill="{col}"/>')
    # H2 arrow: gap between single frame and clip at spiral
    s.append(f'<line x1="{X(4)-14}" x2="{X(4)-14}" y1="{Y(49)}" y2="{Y(30)}" stroke="#333" stroke-width="1.2" marker-end="url(#a)"/>')
    s.append('<defs><marker id="a" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#333"/></marker></defs>')
    s.append(f'<text x="{X(4)-20}" y="{Y(19)+4}" font-size="12" text-anchor="end" fill="#333">motion shrinks bias?</text>')
    lx, ly = L + 16, T + 18
    for k, (name, col, dash, _) in enumerate(series):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        y = ly + k * 20
        s.append(f'<line x1="{lx}" x2="{lx+28}" y1="{y}" y2="{y}" stroke="{col}" stroke-width="3"{d}/>')
        s.append(f'<text x="{lx+36}" y="{y+4}" font-size="12.5" fill="#222">{name}</text>')
    s.append(f'<text x="{L+pw/2}" y="{H-12}" font-size="15" font-weight="700" text-anchor="middle" fill="#222">Tube shape before the exit (family A1)</text>')
    s.append(f'<text transform="translate(20,{T+ph/2}) rotate(-90)" font-size="15" font-weight="700" text-anchor="middle" fill="#222">Impetus-type paths (%)</text>')
    s.append("</svg>")
    open(os.path.join(HERE, "fig_curves.svg"), "w").write("\n".join(s))


if __name__ == "__main__":
    tube_figure()
    curves_figure()
