#!/usr/bin/env python3
"""Stimulus generator for "Do world models make human-like physics errors?".

Renders the six stimulus families of the budget plan (paper-plan.md, section 6)
as small 2D clips with exact physics:

  A1  ball leaving a curved tube (top-down)          impetus bias
  A2  ball on a string swung in a circle, string snaps (top-down)
  A3  pendulum string cut (side view)
  B1  ball dropped from a moving trolley (side view)  straight-down bias
  C1  simple pendulum, length x bob size              mass-period belief, sqrt(L) law
  D1  double pendulum, low vs high energy             chaos calibration

For every item it writes, in <out>/<family>/<item_id>/:
  full.mp4        ground-truth clip
  context.mp4     the clip up to just before the critical moment (nothing after it is shown),
                  for "short clip" conditioning
  still.png       the last frame of context.mp4, for "single frame" conditioning
  anomalous*.mp4  a physically wrong continuation (impetus curve, straight-down fall,
                  or pendulum period x1.2 / /1.2) for 2AFC and likelihood tests
  occluded.mp4    human prediction task: the ball goes behind a grey occluder, clip ends
  options.png     human static task: 4 candidate paths (A-D), McCloskey-style forced choice
  meta.json       parameters, per-frame ball positions, critical frame, answers

Only needs numpy, Pillow and imageio (+ imageio-ffmpeg). Run `python stimgen.py --help`.
"""

import argparse
import csv
import json
import math
import os
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import imageio.v2 as imageio
except ImportError:  # pragma: no cover
    imageio = None

# ---------------------------------------------------------------- global setup
W, H = 480, 320          # output size in pixels (both divisible by 16)
FPS = 16
SS = 3                   # supersampling factor for anti-aliased drawing
G = 981.0                # gravity in px/s^2 (1 m = 100 px)
BALL_R = 7

BG = (242, 242, 242)
BALL = (230, 30, 30)     # pure red: track with a colour threshold
BALL2 = (40, 90, 230)    # blue (first bob of the double pendulum)
INK = (60, 60, 60)
WALL = (120, 120, 120)
OCCL = (150, 150, 150)
PATH = (40, 40, 40)
LABELS = "ABCD"


# ---------------------------------------------------------------- physics
def free_flight(p0, v0, g=(0.0, 0.0), kappa0=0.0, sign=0.0, tau=0.4,
                T=3.0, floor_y=None, dt=1.0 / 640):
    """Point-mass flight from p0 with velocity v0 under gravity g.

    kappa0/sign/tau add a fictitious sideways acceleration kappa(t)*|v|^2 that
    makes the path keep curving (the naive 'impetus' belief); kappa(t) =
    kappa0*exp(-t/tau) (tau=None keeps it constant). kappa0=0 is real physics.
    The ball stops when it reaches floor_y (ball centre). Returns (t, xy).
    """
    n = int(round(T / dt)) + 1
    t = np.arange(n) * dt
    xy = np.zeros((n, 2))
    p = np.array(p0, float)
    v = np.array(v0, float)
    g = np.array(g, float)
    landed = False
    for i in range(n):
        xy[i] = p
        if landed:
            continue
        a = g.copy()
        speed = math.hypot(*v)
        if kappa0 and speed > 1e-9:
            k = kappa0 if tau is None else kappa0 * math.exp(-t[i] / tau)
            normal = sign * np.array([-v[1], v[0]]) / speed
            a = a + k * speed * speed * normal
        v = v + a * dt
        p = p + v * dt
        if floor_y is not None and p[1] >= floor_y:
            p[1] = floor_y
            landed = True
    return t, xy


def sample(t_dense, xy_dense, t):
    t = np.asarray(t, float)
    return np.stack([np.interp(t, t_dense, xy_dense[:, 0]),
                     np.interp(t, t_dense, xy_dense[:, 1])], axis=-1)


def rk4(f, y0, T, dt):
    n = int(round(T / dt)) + 1
    ys = np.zeros((n, len(y0)))
    y = np.array(y0, float)
    for i in range(n):
        ys[i] = y
        k1 = f(y)
        k2 = f(y + 0.5 * dt * k1)
        k3 = f(y + 0.5 * dt * k2)
        k4 = f(y + dt * k3)
        y = y + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
    return np.arange(n) * dt, ys


def pendulum_rhs(g, L):
    return lambda y: np.array([y[1], -(g / L) * math.sin(y[0])])


def double_pendulum_rhs(g, l1, l2, m1=1.0, m2=1.0):
    def f(y):
        t1, w1, t2, w2 = y
        d = t1 - t2
        den = 2 * m1 + m2 - m2 * math.cos(2 * d)
        a1 = (-g * (2 * m1 + m2) * math.sin(t1) - m2 * g * math.sin(t1 - 2 * t2)
              - 2 * math.sin(d) * m2 * (w2 * w2 * l2 + w1 * w1 * l1 * math.cos(d))) / (l1 * den)
        a2 = (2 * math.sin(d) * (w1 * w1 * l1 * (m1 + m2) + g * (m1 + m2) * math.cos(t1)
              + w2 * w2 * l2 * m2 * math.cos(d))) / (l2 * den)
        return np.array([w1, a1, w2, a2])
    return f


def pendulum_period(L, theta0, g=G):
    """Exact period of a simple pendulum (arithmetic-geometric mean formula)."""
    a, b = 1.0, math.cos(theta0 / 2)
    for _ in range(30):
        a, b = (a + b) / 2, math.sqrt(a * b)
    return 2 * math.pi * math.sqrt(L / g) / a


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


# ---------------------------------------------------------------- drawing
class Canvas:
    """Draws in supersampled pixel coordinates; callers use output pixels."""

    def __init__(self):
        self.img = Image.new("RGB", (W * SS, H * SS), BG)
        self.d = ImageDraw.Draw(self.img)

    @staticmethod
    def _p(pt):
        return (pt[0] * SS, pt[1] * SS)

    def line(self, pts, fill=INK, width=2):
        pts = [self._p(p) for p in pts]
        if len(pts) >= 2:
            self.d.line(pts, fill=fill, width=int(width * SS), joint="curve")

    def circle(self, c, r, fill):
        if c is None or not np.all(np.isfinite(c)):
            return
        x, y = self._p(c)
        self.d.ellipse([x - r * SS, y - r * SS, x + r * SS, y + r * SS], fill=fill)

    def rect(self, x0, y0, x1, y1, fill):
        self.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill)

    def annulus(self, c, r_in, r_out, fill):
        x, y = self._p(c)
        self.d.ellipse([x - r_out * SS, y - r_out * SS, x + r_out * SS, y + r_out * SS], fill=fill)
        self.d.ellipse([x - r_in * SS, y - r_in * SS, x + r_in * SS, y + r_in * SS], fill=BG)

    def dashed(self, pts, fill=PATH, width=2, dash=6, gap=5):
        pts = np.asarray(pts, float)
        seg = np.hypot(*np.diff(pts, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        period = dash + gap
        start = 0.0
        while start < s[-1]:
            stop = min(start + dash, s[-1])
            q = np.linspace(start, stop, 6)
            xs = np.interp(q, s, pts[:, 0])
            ys = np.interp(q, s, pts[:, 1])
            self.line(list(zip(xs, ys)), fill=fill, width=width)
            start += period

    def text(self, xy, s, size=14, fill=PATH):
        try:
            font = ImageFont.load_default(size=size * SS)
        except TypeError:  # Pillow < 10.1
            font = ImageFont.load_default()
        x, y = self._p(xy)
        self.d.text((x, y), s, fill=fill, font=font, anchor="mm")

    def frame(self):
        return np.asarray(self.img.resize((W, H), Image.LANCZOS))


# ---------------------------------------------------------------- item model
class Item:
    """One stimulus: scenery, per-frame ball positions and extra moving parts.

    Subclasses fill:
      self.pos          (N, 2) ball centre per frame (NaN = not drawn)
      self.k            critical frame (exit / release / cut), or context end
      self.post_state   dict(p0, v0, g, kappa0, sign, floor_y) at the critical moment
    and implement draw_scene(cv, f, pos) for everything except the ball.
    """

    family = ""
    ball_r = BALL_R
    occluder = None          # ("rect", x0, y0, x1, y1) or ("annulus", cx, cy, r_in, r_out)

    def __init__(self, item_id, params):
        self.id = item_id
        self.params = params
        self.anomalies = {}  # name -> (N, 2) ball positions
        self.options = None  # list of (name, path array)
        self.extra_meta = {}

    # --- helpers shared by the trajectory families (A, B)
    def post(self, kind="correct", T=3.0, **override):
        st = dict(self.post_state)
        st.update(override)
        kappa0 = st.get("kappa0", 0.0) if kind == "impetus" else st.get("kappa_force", 0.0)
        tau = st.get("tau", 0.4)
        return free_flight(st["p0"], st["v0"], st.get("g", (0, 0)), kappa0=kappa0,
                           sign=st.get("sign", 0.0), tau=tau, T=T, floor_y=st.get("floor_y"))

    def splice(self, t_dense, xy_dense):
        """Ball positions: real motion up to frame k, then the given continuation."""
        pos = self.pos.copy()
        n = len(pos)
        tf = (np.arange(self.k, n) - self.k) / FPS
        pos[self.k:] = sample(t_dense, xy_dense, tf)
        return pos

    def draw_scene(self, cv, f, pos):
        pass

    def input_frame(self):
        """Last frame shown to a model or a person: nothing after the critical moment.

        Frame k still shows the string, rod or clamp attached (A2, A3, B1), so it is safe.
        For the tube (A1) frame k already has the ball at the mouth, so A1 overrides this."""
        return self.k

    def scene_meta(self):
        """Scene geometry in pixels, used by render3d.py to rebuild the scene in 3D."""
        return {}

    def render(self, pos=None, frames=None, occluded=False):
        pos = self.pos if pos is None else pos
        frames = range(len(pos)) if frames is None else frames
        out = []
        for f in frames:
            cv = Canvas()
            self.draw_scene(cv, f, pos)
            cv.circle(pos[f], self.ball_r, BALL)
            if occluded and self.occluder:
                draw_occluder(cv, self.occluder)
            out.append(cv.frame())
        return out


def draw_occluder(cv, occ):
    if occ[0] == "rect":
        cv.rect(*occ[1:], fill=OCCL)
    else:
        cv.annulus(occ[1:3], occ[3], occ[4], fill=OCCL)


def inside(occ, p):
    if occ is None or not np.all(np.isfinite(p)):
        return False
    if occ[0] == "rect":
        return occ[1] <= p[0] <= occ[3] and occ[2] <= p[1] <= occ[4]
    r = math.hypot(p[0] - occ[1], p[1] - occ[2])
    return occ[3] <= r <= occ[4]


def on_screen(p, margin=0):
    return -margin <= p[0] <= W + margin and -margin <= p[1] <= H + margin


# ---------------------------------------------------------------- A1 curved tube
class Tube(Item):
    family = "A1"
    TUBE_LEN = 300.0
    HALF_W = 11.0

    def __init__(self, shape, speed, seed):
        super().__init__(f"A1_tube_{shape}_v{speed}_s{seed}",
                         dict(shape=shape, speed=speed, seed=seed))
        turn = 1 if seed % 2 else -1
        rng = np.random.default_rng(100 + seed)
        c = self._centerline(shape) * np.array([1, turn])
        # align the exit tangent with +x and put the exit at the origin
        tan = c[-1] - c[-4]
        ang = math.atan2(tan[1], tan[0])
        R = np.array([[math.cos(-ang), -math.sin(-ang)], [math.sin(-ang), math.cos(-ang)]])
        c = (c - c[-1]) @ R.T
        exit_x = max(40 - c[:, 0].min(), 110)
        exit_y = H / 2 - (c[:, 1].min() + c[:, 1].max()) / 2 + rng.uniform(-10, 10)
        self.c = c + np.array([exit_x, exit_y])
        self.exit = self.c[-1]
        seg = np.hypot(*np.diff(self.c, axis=0).T)
        self.s = np.concatenate([[0], np.cumsum(seg)])
        L = self.s[-1]
        # signed curvature at the exit (heading change per unit length)
        h = np.unwrap(np.arctan2(*np.diff(self.c, axis=0).T[::-1]))
        m = max(3, len(h) // 30)
        kappa = (h[-1] - h[-1 - m]) / (self.s[-1] - self.s[-1 - m])
        self.k = int(math.floor(L / speed * FPS))
        n = self.k + 25
        t = np.arange(n) / FPS
        tc = self.k / FPS
        s_t = L - speed * (tc - t)
        self.pos = np.full((n, 2), np.nan)
        pre = t <= tc + 1e-9
        self.pos[pre, 0] = np.interp(s_t[pre], self.s, self.c[:, 0])
        self.pos[pre, 1] = np.interp(s_t[pre], self.s, self.c[:, 1])
        self.post_state = dict(p0=self.exit, v0=(speed, 0.0), g=(0, 0),
                               kappa0=abs(kappa), sign=float(np.sign(kappa)))
        td, xy = self.post()
        self.pos = self.splice(td, xy)
        self.params.update(turn=turn, exit_curvature=round(float(kappa), 5))

        x0 = max(self.exit[0] + 70, self.c[:, 0].max() + 15)
        self.occluder = ("rect", float(x0), 0.0, float(min(x0 + 170, W - 10)), float(H))

        if shape != "straight":
            td, xy = self.post("impetus")
            self.anomalies["anomalous_impetus"] = self.splice(td, xy)
        k0 = abs(kappa) if shape != "straight" else 1 / 120.0
        sgn = float(np.sign(kappa)) if shape != "straight" else 1.0
        T = 1.2
        opts = [("correct", self.post(T=T)[1]),
                ("impetus_decaying", free_flight(self.exit, (speed, 0), kappa0=k0, sign=sgn, tau=0.6, T=T)[1]),
                ("impetus_full_curve", free_flight(self.exit, (speed, 0), kappa0=k0, sign=sgn, tau=None, T=T)[1]),
                ("curve_opposite", free_flight(self.exit, (speed, 0), kappa0=k0, sign=-sgn, tau=0.6, T=T)[1])]
        self.options = opts

    def input_frame(self):
        # frame k has the ball centre at the tube mouth; frame k-1 is the last one with the
        # whole ball still inside the tube (it is >= 7.5 px from the mouth, ball radius 7)
        return self.k - 1

    def _centerline(self, shape):
        L = self.TUBE_LEN
        if shape == "straight":
            return np.stack([np.linspace(0, L, 200), np.zeros(200)], axis=1)
        if shape == "spiral":
            phi = np.linspace(0, 2.25 * math.pi, 600)
            r = 12 + 9 * phi
            c = np.stack([r * np.cos(phi), r * np.sin(phi)], axis=1)
            length = np.hypot(*np.diff(c, axis=0).T).sum()
            return c * (L / length)
        sweep = math.radians(int(shape.replace("c", "")))
        R = L / sweep
        a = np.linspace(0, sweep, 400)
        return np.stack([R * np.sin(a), R * (1 - np.cos(a))], axis=1)

    def _walls(self):
        d = np.gradient(self.c, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], axis=1)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        return self.c + self.HALF_W * nrm, self.c - self.HALF_W * nrm

    def scene_meta(self):
        return dict(view="top", centerline=np.round(self.c[::4], 2).tolist(), half_width=self.HALF_W)

    def draw_scene(self, cv, f, pos):
        w1, w2 = self._walls()
        cv.line(w1, fill=WALL, width=3)
        cv.line(w2, fill=WALL, width=3)


# ---------------------------------------------------------------- A2 string release
class StringRelease(Item):
    family = "A2"
    CENTER = np.array([240.0, 160.0])
    PERIOD = 2.2

    def __init__(self, phase_deg, seed):
        super().__init__(f"A2_string_p{phase_deg}_s{seed}", dict(phase_deg=phase_deg, seed=seed))
        direction = 1 if seed % 2 else -1
        r = {1: 65.0, 2: 70.0, 3: 75.0}.get(seed, 70.0)
        w = 2 * math.pi / self.PERIOD
        a_rel = math.radians(phase_deg)
        self.k = int(round(self.PERIOD * FPS))
        n = self.k + 25
        t = np.arange(n) / FPS
        ang = a_rel - direction * w * (self.k / FPS - t)
        self.pos = self.CENTER + r * np.stack([np.cos(ang), np.sin(ang)], axis=1)
        p0 = self.pos[self.k].copy()
        v0 = direction * w * r * np.array([-math.sin(a_rel), math.cos(a_rel)])
        self.post_state = dict(p0=p0, v0=v0, g=(0, 0), kappa0=1 / r, sign=float(direction))
        td, xy = self.post()
        self.pos = self.splice(td, xy)
        td, xy = self.post("impetus")
        self.anomalies["anomalous_impetus"] = self.splice(td, xy)
        self.params.update(direction=direction, radius=r, speed=round(w * r, 1))
        self.occluder = ("annulus", *self.CENTER.tolist(), 105.0, 150.0)
        radial = (p0 - self.CENTER) / r * w * r
        T = 1.0
        self.options = [("correct", self.post(T=T)[1]),
                        ("impetus_decaying", self.post("impetus", T=T, tau=0.6)[1]),
                        ("impetus_full_curve", self.post("impetus", T=T, tau=None)[1]),
                        ("radial_outward", free_flight(p0, radial, T=T)[1])]

    def scene_meta(self):
        return dict(view="top", center=self.CENTER.tolist(), string_until_frame=self.k)

    def draw_scene(self, cv, f, pos):
        cv.circle(self.CENTER, 4, INK)
        if f <= self.k:
            cv.line([self.CENTER, pos[f]], fill=INK, width=1.5)


# ---------------------------------------------------------------- A3 pendulum string cut
class PendulumCut(Item):
    family = "A3"
    PIVOT = np.array([240.0, 40.0])
    FLOOR = 305.0
    THETA0 = math.radians(40)

    PHASES = ("turning", "descending", "bottom", "ascending")

    def __init__(self, phase, seed):
        super().__init__(f"A3_cut_{phase}_s{seed}", dict(phase=phase, seed=seed))
        side = 1 if seed % 2 else -1
        L = {1: 150.0, 2: 140.0, 3: 160.0}.get(seed, 150.0)
        Tp = pendulum_period(L, self.THETA0)
        dt = 1.0 / (FPS * 40)
        td, ys = rk4(pendulum_rhs(G, L), [side * self.THETA0, 0.0], 2.5 * Tp, dt)
        th = ys[:, 0] * side          # mirrored so "+" is the start side
        after = td >= Tp - 1e-9
        idx = np.where(after)[0]
        if phase == "turning":
            t_cut = Tp
        else:
            target = {"descending": self.THETA0 / 2, "bottom": 0.0, "ascending": -self.THETA0 / 2}[phase]
            j = idx[np.argmax(th[idx] <= target)]
            t_cut = td[j]
        self.k = int(round(t_cut * FPS))
        n = self.k + 21
        t = np.arange(n) / FPS
        theta = np.interp(t, td, ys[:, 0])
        omega = np.interp(t, td, ys[:, 1])
        self.pos = self.PIVOT + L * np.stack([np.sin(theta), np.cos(theta)], axis=1)
        tk, wk = theta[self.k], omega[self.k]
        p0 = self.pos[self.k].copy()
        v0 = L * wk * np.array([math.cos(tk), -math.sin(tk)])
        floor_y = self.FLOOR - BALL_R
        sign = float(np.sign(cross(v0, self.PIVOT - p0))) if np.hypot(*v0) > 1 else 0.0
        self.post_state = dict(p0=p0, v0=v0, g=(0, G), kappa0=1 / L, sign=sign, floor_y=floor_y)
        tdd, xy = self.post()
        self.pos = self.splice(tdd, xy)
        self.params.update(start_side=side, length=L, cut_angle_deg=round(math.degrees(tk), 2),
                           cut_speed=round(float(np.hypot(*v0)), 1))
        if np.hypot(*v0) > 20:
            tdd, xy = self.post("impetus")
            self.anomalies["anomalous_impetus"] = self.splice(tdd, xy)
        self.occluder = ("rect", 0.0, 215.0, float(W), 290.0)
        T = 1.0
        if np.hypot(*v0) > 20:
            self.options = [("correct", self.post(T=T)[1]),
                            ("straight_down", free_flight(p0, (0, 0), (0, G), T=T, floor_y=floor_y)[1]),
                            ("impetus_curve", self.post("impetus", T=T)[1]),
                            ("tangent_no_gravity", free_flight(p0, v0, (0, 0), T=0.6)[1])]
        else:
            out = np.sign(p0[0] - self.PIVOT[0]) or 1.0
            self.options = [("correct", self.post(T=T)[1]),
                            ("launch_outward", free_flight(p0, (out * 150, 0), (0, G), T=T, floor_y=floor_y)[1]),
                            ("launch_inward", free_flight(p0, (-out * 150, 0), (0, G), T=T, floor_y=floor_y)[1]),
                            ("swing_on", free_flight(p0, (-out * 120, 60), (0, 0.4 * G), kappa0=1 / L,
                                                     sign=out, tau=0.5, T=T, floor_y=floor_y)[1])]

    def scene_meta(self):
        return dict(view="side", pivot=self.PIVOT.tolist(), floor_y=self.FLOOR, rod_until_frame=self.k)

    def draw_scene(self, cv, f, pos):
        cv.line([(0, self.FLOOR), (W, self.FLOOR)], fill=INK, width=2)
        cv.rect(self.PIVOT[0] - 20, self.PIVOT[1] - 6, self.PIVOT[0] + 20, self.PIVOT[1], fill=INK)
        if f <= self.k:
            cv.line([self.PIVOT, pos[f]], fill=INK, width=1.5)


# ---------------------------------------------------------------- B1 trolley drop
class TrolleyDrop(Item):
    family = "B1"
    RAIL_Y = 60.0
    GROUND = 300.0
    RELEASE_X = 160.0

    def __init__(self, speed, seed):
        super().__init__(f"B1_drop_u{speed}_s{seed}", dict(speed=speed, seed=seed))
        rng = np.random.default_rng(300 + seed)
        self.u = float(speed)
        rx = self.RELEASE_X + rng.uniform(-15, 15)
        self.k = 24
        n = self.k + 25
        t = np.arange(n) / FPS
        self.cart_x = rx + self.u * (t - self.k / FPS)
        ball_y = self.RAIL_Y + 30.0
        self.pos = np.stack([self.cart_x, np.full(n, ball_y)], axis=1)
        floor_y = self.GROUND - BALL_R
        p0 = self.pos[self.k].copy()
        self.post_state = dict(p0=p0, v0=(self.u, 0.0), g=(0, G), floor_y=floor_y)
        td, xy = self.post()
        self.pos = self.splice(td, xy)
        if self.u > 0:
            td, xy = self.post(v0=(0.0, 0.0))
            self.anomalies["anomalous_straight_down"] = self.splice(td, xy)
        self.params.update(release_x=round(rx, 1), drop_height=round(floor_y - ball_y, 1))
        self.occluder = ("rect", 0.0, 130.0, float(W), 270.0)
        ur = self.u if self.u > 0 else 100.0
        T = 1.0
        fl = lambda vx: free_flight(p0, (vx, 0), (0, G), T=T, floor_y=floor_y)[1]
        self.options = [("correct", fl(self.u)),
                        ("straight_down" if self.u > 0 else "forward", fl(0.0 if self.u > 0 else ur)),
                        ("backward", fl(-0.5 * ur)),
                        ("forward_too_far", fl(1.8 * ur))]

    def scene_meta(self):
        return dict(view="side", rail_y=self.RAIL_Y, floor_y=self.GROUND,
                    cart_x=np.round(self.cart_x, 2).tolist(), clamp_until_frame=self.k)

    def draw_scene(self, cv, f, pos):
        cv.line([(0, self.RAIL_Y), (W, self.RAIL_Y)], fill=INK, width=2)
        cv.line([(0, self.GROUND), (W, self.GROUND)], fill=INK, width=2)
        x = self.cart_x[f]
        cv.circle((x - 14, self.RAIL_Y - 5), 5, INK)
        cv.circle((x + 14, self.RAIL_Y - 5), 5, INK)
        cv.rect(x - 25, self.RAIL_Y, x + 25, self.RAIL_Y + 18, fill=(90, 110, 140))
        if f <= self.k:  # clamp holding the ball
            cv.line([(x, self.RAIL_Y + 18), (x, self.RAIL_Y + 23)], fill=INK, width=2)


# ---------------------------------------------------------------- C1 pendulum
class Pendulum(Item):
    family = "C1"
    PIVOT = np.array([240.0, 24.0])
    THETA0 = math.radians(25)
    DURATION = 6.0
    LENGTHS = (60, 100, 150, 210, 270)

    def __init__(self, length, bob, seed):
        super().__init__(f"C1_pend_L{length}_{bob}_s{seed}", dict(length=length, bob=bob, seed=seed))
        self.ball_r = 7 if bob == "small" else 14
        side = 1 if seed % 2 else -1
        L = float(length)
        self.L = L
        Tp = pendulum_period(L, self.THETA0)
        n = int(self.DURATION * FPS) + 1
        t = np.arange(n) / FPS
        dt = 1.0 / (FPS * 40)
        td, ys = rk4(pendulum_rhs(G, L), [side * self.THETA0, 0.0], self.DURATION, dt)
        self.pos = self._xy(np.interp(t, td, ys[:, 0]))
        self.k = int(round(Tp * FPS))                  # context = one full period
        self.k_half = int(round(0.5 * Tp * FPS))
        # anomalous continuations: period x1.2 (slow) and /1.2 (fast) after the context
        y_k = [np.interp(self.k / FPS, td, ys[:, 0]), np.interp(self.k / FPS, td, ys[:, 1])]
        rest = self.DURATION - self.k / FPS
        for name, factor in (("anomalous_slow", 1.2), ("anomalous_fast", 1 / 1.2)):
            g2 = G / factor ** 2
            td2, ys2 = rk4(pendulum_rhs(g2, L), y_k, rest, dt)
            pos = self.pos.copy()
            pos[self.k:] = self._xy(np.interp((np.arange(self.k, n) - self.k) / FPS, td2, ys2[:, 0]))
            self.anomalies[name] = pos
        self.params.update(start_side=side, amplitude_deg=25, true_period_s=round(Tp, 4),
                           small_angle_period_s=round(2 * math.pi * math.sqrt(L / G), 4),
                           out_of_range=length in (60, 270), damping=0)
        # occluder hides the whole right half, including the rod, so the bob
        # reappears when it crosses the bottom of its swing
        self.occluder = ("rect", float(self.PIVOT[0]), 0.0, float(W), float(H))

    def _xy(self, theta):
        return self.PIVOT + self.L * np.stack([np.sin(theta), np.cos(theta)], axis=-1)

    def scene_meta(self):
        return dict(view="side", pivot=self.PIVOT.tolist(), length=self.L)

    def draw_scene(self, cv, f, pos):
        cv.rect(self.PIVOT[0] - 25, self.PIVOT[1] - 6, self.PIVOT[0] + 25, self.PIVOT[1], fill=INK)
        cv.line([self.PIVOT, pos[f]], fill=INK, width=1.5)


# ---------------------------------------------------------------- D1 double pendulum
class DoublePendulum(Item):
    family = "D1"
    PIVOT = np.array([240.0, 160.0])
    L1 = L2 = 72.0
    DURATION = 6.0
    CONTEXT = 2.0
    N_ENSEMBLE = 50
    NOISE_DEG = 1.0

    def __init__(self, energy, seed):
        super().__init__(f"D1_double_{energy}_s{seed}", dict(energy=energy, seed=seed))
        if energy == "low":
            t1, t2 = math.radians(20), math.radians(20 + 5 * (seed - 2))
        else:
            t1, t2 = math.radians(120), math.radians(-20 + 20 * (seed - 1))
        f = double_pendulum_rhs(G, self.L1, self.L2)
        dt = 1.0 / (FPS * 80)
        n = int(self.DURATION * FPS) + 1
        t = np.arange(n) / FPS
        td, ys = rk4(f, [t1, 0.0, t2, 0.0], self.DURATION, dt)
        Y = np.stack([np.interp(t, td, ys[:, i]) for i in range(4)], axis=1)
        self.b1, self.pos = self._xy(Y[:, 0], Y[:, 2])
        self.k = int(self.CONTEXT * FPS)
        # noisy-Newton ensemble: perturb the angles at the end of the context
        rng = np.random.default_rng(500 + seed)
        rest = self.DURATION - self.k / FPS
        tf = (np.arange(self.k, n) - self.k) / FPS
        ens = []
        for _ in range(self.N_ENSEMBLE):
            y0 = Y[self.k].copy()
            y0[[0, 2]] += np.radians(rng.normal(0, self.NOISE_DEG, 2))
            tde, yse = rk4(f, y0, rest, dt * 2)
            _, b2 = self._xy(np.interp(tf, tde, yse[:, 0]), np.interp(tf, tde, yse[:, 2]))
            ens.append(b2)
        ens = np.array(ens)
        spread = np.median(np.hypot(*(ens - self.pos[self.k:][None]).transpose(2, 0, 1)), axis=0)
        over = np.where(spread > 30)[0]
        horizon = float(tf[over[0]]) if len(over) else None
        self.ensemble = ens
        self.params.update(theta1_deg=round(math.degrees(t1), 1), theta2_deg=round(math.degrees(t2), 1),
                           ensemble_size=self.N_ENSEMBLE, ensemble_noise_deg=self.NOISE_DEG,
                           predictability_horizon_s=horizon)

    def _xy(self, t1, t2):
        b1 = self.PIVOT + self.L1 * np.stack([np.sin(t1), np.cos(t1)], axis=-1)
        b2 = b1 + self.L2 * np.stack([np.sin(t2), np.cos(t2)], axis=-1)
        return b1, b2

    def scene_meta(self):
        return dict(view="side", pivot=self.PIVOT.tolist(), bob1_xy=np.round(self.b1, 2).tolist())

    def draw_scene(self, cv, f, pos):
        cv.circle(self.PIVOT, 4, INK)
        cv.line([self.PIVOT, self.b1[f], pos[f]], fill=INK, width=2)
        cv.circle(self.b1[f], 7, BALL2)


# ---------------------------------------------------------------- item lists
def build_items(families, demo=False):
    items = []
    if "A1" in families:
        shapes = ["straight", "c180"] if demo else ["straight", "c90", "c180", "c270", "spiral"]
        for shape in shapes:
            for v in ([120] if demo else [120, 200]):
                for s in ([1] if demo else [1, 2, 3]):
                    items.append(lambda shape=shape, v=v, s=s: Tube(shape, v, s))
    if "A2" in families:
        for p in ([20] if demo else [20, 110, 200, 290]):
            for s in ([1] if demo else [1, 2, 3]):
                items.append(lambda p=p, s=s: StringRelease(p, s))
    if "A3" in families:
        for ph in (["turning", "bottom"] if demo else PendulumCut.PHASES):
            for s in ([1] if demo else [1, 2, 3]):
                items.append(lambda ph=ph, s=s: PendulumCut(ph, s))
    if "B1" in families:
        for u in ([0, 160] if demo else [0, 80, 160, 240]):
            for s in ([1] if demo else [1, 2, 3]):
                items.append(lambda u=u, s=s: TrolleyDrop(u, s))
    if "C1" in families:
        for L in ([100] if demo else Pendulum.LENGTHS):
            for bob in ("small", "big"):
                for s in ([1] if demo else [1, 2]):
                    items.append(lambda L=L, bob=bob, s=s: Pendulum(L, bob, s))
    if "D1" in families:
        for e in ("low", "high"):
            for s in ([1] if demo else [1, 2, 3]):
                items.append(lambda e=e, s=s: DoublePendulum(e, s))
    return items


# ---------------------------------------------------------------- outputs
def write_video(path, frames):
    if imageio is None:
        raise SystemExit("imageio is not installed: pip install imageio imageio-ffmpeg")
    with imageio.get_writer(path, fps=FPS, codec="libx264", quality=8, macro_block_size=16,
                            pixelformat="yuv420p", ffmpeg_log_level="error") as w:
        for fr in frames:
            w.append_data(fr)


def write_png(path, frame):
    Image.fromarray(frame).save(path)


def occlusion_answer(item):
    """First moment the ball comes back out of the occluder after the critical frame."""
    occ = item.occluder
    pos = item.pos
    if occ is None:
        return None, None
    # dense continuation after the critical frame (correct physics)
    if hasattr(item, "post_state"):
        td, xy = item.post(T=4.0)
        tt, pts = td, xy
        t_start = item.k / FPS
    else:  # C1: use the frame trajectory, upsampled
        tt = np.arange(len(pos)) / FPS
        fine = np.linspace(0, tt[-1], len(pos) * 20)
        pts = sample(tt, pos, fine)
        tt = fine
        t_start = item.k / FPS
        sel = tt >= t_start
        tt, pts = tt[sel] - t_start, pts[sel]
    entered = None
    for i in range(len(tt)):
        ins = inside(occ, pts[i])
        if entered is None and ins:
            entered = i
        elif entered is not None and not ins:
            t_in = t_start + tt[entered]
            t_out = t_start + tt[i]
            return (t_in, t_out), pts[i]
    return None, None


def render_options(item, rng):
    cv = Canvas()
    item.draw_scene(cv, item.k, item.pos)
    order = rng.permutation(len(item.options))
    answer = None
    mapping = {}
    for label, j in zip(LABELS, order):
        name, path = item.options[j]
        keep = [p for p in path if on_screen(p, -4)]
        path = np.array(keep) if len(keep) > 1 else path[:2]
        cv.dashed(path)
        end = path[-1]
        d = path[-1] - path[max(0, len(path) - 40)]
        d = d / (np.hypot(*d) + 1e-9)
        lab = np.clip(end + 14 * d, [10, 10], [W - 10, H - 10])
        cv.text(lab, label)
        mapping[label] = name
        if name == "correct":
            answer = label
    cv.circle(item.pos[item.k], item.ball_r, BALL)
    return cv.frame(), mapping, answer, {n: np.round(p[::20], 1).tolist() for n, p in item.options}


def process(item, out_dir, videos=True):
    d = os.path.join(out_dir, item.family, item.id)
    os.makedirs(d, exist_ok=True)
    n = len(item.pos)
    files = {}
    if videos:
        write_video(os.path.join(d, "full.mp4"), item.render())
        files["full"] = "full.mp4"
        ctx_end = item.input_frame()
        write_video(os.path.join(d, "context.mp4"), item.render(frames=range(ctx_end + 1)))
        files["context"] = "context.mp4"
        if item.family == "C1":
            write_video(os.path.join(d, "context_half.mp4"), item.render(frames=range(item.k_half + 1)))
            files["context_half"] = "context_half.mp4"
        for name, pos in item.anomalies.items():
            write_video(os.path.join(d, name + ".mp4"), item.render(pos=pos))
            files[name] = name + ".mp4"
    write_png(os.path.join(d, "still.png"), item.render(frames=[item.input_frame()])[0])
    files["still"] = "still.png"

    meta = dict(item_id=item.id, family=item.family, params=item.params, fps=FPS,
                size=[W, H], n_frames=n, critical_frame=item.k,
                context_end_frame=item.input_frame(), still_frame=item.input_frame(),
                ball_radius=item.ball_r, ball_rgb=BALL, units="pixels, y down, 100 px = 1 m",
                gravity_px_s2=G if item.family in ("A3", "B1", "C1", "D1") else 0.0,
                ball_xy=np.round(item.pos, 2).tolist(), scene=item.scene_meta(), files=files)
    for name, pos in item.anomalies.items():
        meta[name + "_xy"] = np.round(pos, 2).tolist()

    times, emerge = occlusion_answer(item)
    if times is not None:
        meta["occluder"] = list(item.occluder)
        t_in, t_out = times
        # occluded clip: shows the motion until the ball is hidden, plus 3 frames
        f_in = int(math.ceil(t_in * FPS))
        f_out = int(math.floor(t_out * FPS))
        # stop while the ball is still hidden, so the clip never shows the answer
        f_end = max(f_in, min(f_in + 3, f_out - 1, n - 1))
        if videos:
            frames = item.render(frames=range(f_end + 1), occluded=True)
            write_video(os.path.join(d, "occluded.mp4"), frames)
            files["occluded"] = "occluded.mp4"
            write_png(os.path.join(d, "occluded_last.png"), frames[-1])
        meta["occlusion_task"] = dict(
            clip_last_frame=f_end,
            reappear_xy=np.round(emerge, 1).tolist(),
            reappear_time_s=round(t_out, 4),
            reappear_after_clip_end_s=round(t_out - f_end / FPS, 4))

    if item.options:
        rng = np.random.default_rng(zlib.crc32(item.id.encode()))
        img, mapping, answer, paths = render_options(item, rng)
        write_png(os.path.join(d, "options.png"), img)
        files["options"] = "options.png"
        meta["options_task"] = dict(labels=mapping, correct=answer, paths_xy=paths)

    if isinstance(item, DoublePendulum):
        np.save(os.path.join(d, "ensemble_bob2_xy.npy"), item.ensemble.astype(np.float32))
        files["ensemble"] = "ensemble_bob2_xy.npy"
        meta["ensemble_note"] = ("noisy-Newton ensemble: angles at the end of the context perturbed by "
                                 f"N(0, {DoublePendulum.NOISE_DEG} deg); array shape (runs, frames after "
                                 "context, 2), red bob centre")

    with open(os.path.join(d, "meta.json"), "w") as fh:
        json.dump(meta, fh)
    return meta


def write_index(out_dir, metas):
    rows = []
    for m in metas:
        rows.append(dict(item_id=m["item_id"], family=m["family"],
                         params=json.dumps(m["params"]), n_frames=m["n_frames"],
                         critical_frame=m["critical_frame"],
                         anomalous=";".join(k for k in m["files"] if k.startswith("anomalous")),
                         occluded="occluded" in m["files"],
                         options_correct=(m.get("options_task") or {}).get("correct", "")))
    with open(os.path.join(out_dir, "index.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    # a local gallery to look at everything in a browser
    parts = ["<!doctype html><meta charset='utf-8'><title>Stimuli</title>",
             "<style>body{font-family:sans-serif;margin:16px;background:#fafafa}"
             ".it{display:inline-block;vertical-align:top;margin:6px;padding:8px;background:#fff;"
             "border:1px solid #ddd}video,img{width:240px;display:block;margin:2px 0}"
             "small{color:#555}</style><h1>Stimuli</h1>"]
    fam = None
    for m in metas:
        if m["family"] != fam:
            fam = m["family"]
            parts.append(f"<h2>{fam}</h2>")
        base = f"{m['family']}/{m['item_id']}/"
        cell = [f"<div class='it'><b>{m['item_id']}</b>"]
        for key, fn in m["files"].items():
            if fn.endswith(".mp4"):
                cell.append(f"<small>{key}</small><video src='{base}{fn}' controls loop muted></video>")
            elif fn.endswith(".png"):
                cell.append(f"<small>{key}</small><img src='{base}{fn}'>")
        if m.get("options_task"):
            cell.append(f"<small>correct option: {m['options_task']['correct']}</small>")
        cell.append("</div>")
        parts.append("".join(cell))
    with open(os.path.join(out_dir, "index.html"), "w") as fh:
        fh.write("\n".join(parts))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="stimuli", help="output folder (default: stimuli)")
    ap.add_argument("--demo", action="store_true", help="small demo set (~12 items) instead of all 92")
    ap.add_argument("--families", default="A1,A2,A3,B1,C1,D1", help="comma-separated, e.g. A1,C1")
    ap.add_argument("--no-video", action="store_true", help="only stills, options and meta (fast)")
    args = ap.parse_args()

    fams = [f.strip().upper() for f in args.families.split(",") if f.strip()]
    makers = build_items(fams, demo=args.demo)
    os.makedirs(args.out, exist_ok=True)
    metas = []
    for i, make in enumerate(makers, 1):
        item = make()
        metas.append(process(item, args.out, videos=not args.no_video))
        print(f"[{i}/{len(makers)}] {item.id}")
    write_index(args.out, metas)
    print(f"done: {len(metas)} items in {os.path.abspath(args.out)} (open index.html to browse)")


if __name__ == "__main__":
    main()
