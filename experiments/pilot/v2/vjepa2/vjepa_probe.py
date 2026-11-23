"""V-JEPA 2 surprise, done more carefully than in the first runs.
For each item, 16-frame clips (8 context + 8 future) are built for five futures:
  correct (true straight exit), impetus (curving foil), and three impossible ones for calibration:
  vanish (ball erased after the exit), reverse (ball rolls back into the tube), freeze (ball stops dead).
Four views of the same clip:
  whole  : whole frame padded to a square, 12 fps (as in the first runs)
  whole6 : whole frame padded to a square, 6 fps: the 8 future frames span 1.33 s after the input ends, so the
           true and curving balls end a median 4.3 ball radii apart (vs 0.1-1.3 in the other views); on the
           straight-tube items the ball has left the frame by the last 1-2 frames
  crop12 : 512 px square around the exit point, 12 fps, resized to 256
  crop24 : 256 px square around the exit point, 24 fps, native resolution
Two scores per view: mean L1 error over all future tokens ("all") and over the tokens where the ball
is, on either the true or the curving path ("ball"). The same token set is used for every future.
   python vjepa_probe.py --inputs STIM --out vjepa_probe.csv [--dry DIR]   (--dry: no model, writes check images)"""
import argparse, math, os, sys, csv
import numpy as np, imageio.v2 as imageio
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import analyze_v2

PATCH, RES = 16, 256
MEAN, STD = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])

def frames_of(m, name):
    return np.stack(imageio.mimread(os.path.join(m["dir"], m["files"][name]), memtest=False))[..., :3]

def erase_ball(fr, xy, src, r):
    """Paint the ball (and its shadow) out of frames fr, using the same pixels of a frame src where it is elsewhere."""
    out = fr.copy(); H, W = fr.shape[1:3]; yy, xx = np.mgrid[0:H, 0:W]
    for t in range(len(fr)):
        if xy[t] is None: continue
        mk = (xx - xy[t][0]) ** 2 + (yy - xy[t][1]) ** 2 < (2.4 * r) ** 2
        out[t][mk] = src[mk]
    return out

def futures(m):
    c = m["context_end_frame"]; full = frames_of(m, "full"); imp = frames_of(m, "anomalous_impetus")
    n = len(full); r = m["ball_radius"]
    F = dict(correct=full, impetus=imp[:n] if len(imp) >= n else np.concatenate([imp, imp[-1:].repeat(n - len(imp), 0)]))
    F["vanish"] = np.concatenate([full[:c + 1], erase_ball(full[c + 1:], m["ball_xy"][c + 1:], full[0], r)])
    rev = full[:c + 1][::-1]                          # c, c-1, ... : the ball rolls back the way it came
    F["reverse"] = np.concatenate([full[:c + 1], rev[1:], rev[-1:].repeat(max(0, n - 2 * c - 1), 0)])[:n]
    F["freeze"] = np.concatenate([full[:c + 1], full[c:c + 1].repeat(n - c - 1, 0)])
    return F

def clip_idx(c, fps_step):
    """16 frame indices: 8 context up to c, 8 future after it."""
    return [c - fps_step * (7 - i) for i in range(8)] + [c + fps_step * (i + 1) for i in range(8)]

def view(fr, idx, m, kind):
    """Returns (16, RES, RES, 3) uint8 and a function mapping image xy to RES-space xy."""
    H, W = fr.shape[1:3]; c = m["context_end_frame"]; ex, ey = m["ball_xy"][c]
    if kind in ("whole", "whole6"):
        side = max(H, W); ox, oy = (side - W) // 2, (side - H) // 2
        canvas = np.empty((16, side, side, 3), np.uint8); canvas[:] = np.median(fr[0, 0], axis=0).astype(np.uint8)
        canvas[:, oy:oy + H, ox:ox + W] = fr[idx]
        sc = RES / side
        return np.stack([np.array(Image.fromarray(f).resize((RES, RES), Image.BILINEAR)) for f in canvas]), (lambda x, y: ((x + ox) * sc, (y + oy) * sc))
    L = int(round((512 if kind == "crop12" else 256) * W / 768))
    L = min(L, H, W)
    x0 = int(np.clip(ex - L / 2, 0, W - L)); y0 = int(np.clip(ey - L / 2, 0, H - L))
    sc = RES / L
    crop = fr[idx, y0:y0 + L, x0:x0 + L]
    if L != RES: crop = np.stack([np.array(Image.fromarray(f).resize((RES, RES), Image.BILINEAR)) for f in crop])
    return crop, (lambda x, y: ((x - x0) * sc, (y - y0) * sc))

def ball_tokens(m, idx, to_res, r_res):
    """Indices (into the target half) of the tokens covering the ball on the true or the curving path."""
    g = RES // PATCH; toks = set()
    for k in range(4, 8):                              # target tubelets = frames 8..15, two frames each
        for fi in (idx[2 * k], idx[2 * k + 1]):
            for path in (m["ball_xy"], m.get("anomalous_impetus_xy") or []):
                if fi >= len(path) or path[fi] is None: continue
                x, y = to_res(*path[fi])
                for hy in range(g):
                    for wx in range(g):
                        cx, cy = (wx + 0.5) * PATCH, (hy + 0.5) * PATCH
                        if abs(cx - x) <= PATCH / 2 + r_res and abs(cy - y) <= PATCH / 2 + r_res:
                            toks.add((k - 4) * g * g + hy * g + wx)
    return sorted(toks)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--inputs"); ap.add_argument("--out"); ap.add_argument("--dry", default="")
    a = ap.parse_args()
    items = analyze_v2.load_items(a.inputs)
    if not a.dry:
        import torch
        from transformers import AutoModel
        vj = AutoModel.from_pretrained(os.environ.get("VJEPA_MODEL", "facebook/vjepa2-vitl-fpc64-256"), dtype=torch.float16).cuda().eval()
        def surprise(clip, tok):
            x = (clip / 255.0 - MEAN) / STD
            x = torch.tensor(x, dtype=torch.float16).permute(0, 3, 1, 2)[None].cuda()   # (1, T, C, H, W)
            with torch.no_grad():
                full = vj.get_vision_features(x); N = full.shape[1]; Nc = N // 2
                ctx = vj.get_vision_features(x[:, :8])
                pred = vj.predictor(encoder_hidden_states=ctx, context_mask=[torch.arange(Nc, device="cuda")[None]],
                                    target_mask=[torch.arange(Nc, N, device="cuda")[None]]).last_hidden_state
                err = (pred.float() - full[:, Nc:].float()).abs().mean(-1)[0]
            return err.mean().item(), (err[tok].mean().item() if tok else float("nan"))
    rows = []
    for iid, m in sorted(items.items()):
        if not m.get("anomalous_impetus_xy"): continue
        c = m["context_end_frame"]; F = futures(m); step24 = max(1, round(m["fps"] / 24))
        for kind, step in (("whole", 2 * step24), ("crop12", 2 * step24), ("crop24", step24), ("whole6", 4 * step24)):
            idx = clip_idx(c, step)
            if idx[0] < 0 or idx[-1] >= len(F["correct"]): continue
            _, to_res = view(F["correct"], idx, m, kind)
            p0 = to_res(0, 0); p1 = to_res(m["ball_radius"], 0); r_res = abs(p1[0] - p0[0])
            tok = ball_tokens(m, idx, to_res, r_res)
            for fut, fr in F.items():
                clip, _ = view(fr, idx, m, kind)
                if a.dry:
                    if iid.endswith("v120_s1"):
                        os.makedirs(a.dry, exist_ok=True)
                        Image.fromarray(np.concatenate([np.concatenate(list(clip[:8]), 1), np.concatenate(list(clip[8:]), 1)], 0)).resize((1024, 256)).save(f"{a.dry}/{iid}_{kind}_{fut}.jpg")
                    s_all, s_ball = float("nan"), float("nan")
                else:
                    s_all, s_ball = surprise(clip, tok)
                rows.append(dict(item_id=iid, shape=m["params"]["shape"], speed=m["params"]["speed"], view=kind,
                                 future=fut, n_ball_tokens=len(tok), surprise_all=s_all, surprise_ball=s_ball))
            print(iid, kind, len(tok), "ball tokens", flush=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

if __name__ == "__main__":
    main()
