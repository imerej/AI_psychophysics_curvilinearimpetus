"""Render 3D versions of the 2D stimuli with Blender (v2 for the video models: 768 x 512, rolling striped ball).

Runs inside Blender (normally started for you by make3d.py):

    blender -b --factory-startup --python render3d.py -- --in stimuli --out stimuli3d

It reads each item's meta.json written by stimgen.py and rebuilds the scene in
3D: a shaded ball, a table or floor, rails, rods, a trolley, soft lighting and a
perspective camera. The ball is moved along exactly the same per-frame positions
as in the 2D clip (Blender's own physics is not used), so physics, timing and
answers are identical; only the look changes.

Output per item, in <out>/<family>/<item_id>/:
  frames_full/0001.png ...          one PNG per frame
  frames_anomalous_*/0001.png ...   the physically wrong versions
  meta3d.json                       camera, and the ball position in output pixels
                                    for every frame and version (for tracking)
make3d.py then turns the frames into full.mp4, context.mp4, still.png, ...
"""

import argparse
import glob
import json
import math
import os
import shutil
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Quaternion, Vector

W, H = 480, 320          # scene units of the 2D stimuli
RW, RH = 768, 512        # v2: render size for the video models
S = 0.01  # metres per pixel (100 px = 1 m, as in the 2D stimuli)


# ---------------------------------------------------------------- coordinates
def side(x, y, depth=0.0):
    return Vector(((x - 240) * S, depth, (H - y) * S))


def top(x, y, z=0.0):
    return Vector(((x - 240) * S, (160 - y) * S, z))


# ---------------------------------------------------------------- scene helpers
def reset_scene(fps, samples, engine):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = RW, RH
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    if engine == "eevee":
        try:
            sc.render.engine = "BLENDER_EEVEE_NEXT"   # Blender 4.2-4.4
        except TypeError:
            sc.render.engine = "BLENDER_EEVEE"        # Blender 4.1 and 5.x
    else:
        sc.render.engine = "CYCLES"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        use_gpu(sc)
    sc.view_settings.view_transform = "Standard"   # crisp colours, no filmic wash-out
    world = bpy.data.worlds.new("world")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.78, 0.82, 0.88, 1)
    bg.inputs["Strength"].default_value = 0.4
    return sc


def use_gpu(sc):
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except KeyError:
        return
    for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
        except TypeError:
            continue
        gpus = [d for d in prefs.devices if d.type != "CPU"]
        if gpus:
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
            return


def material(name, color, rough=0.5, metal=0.0, noise=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if noise is None:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
    else:  # subtle procedural texture between two colours (wood, concrete)
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise[1]
        tex.inputs["Detail"].default_value = 6
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*color, 1)
        ramp.color_ramp.elements[1].color = (*noise[0], 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def ball_material(r):
    """v2: red ball with an orange band round its equator, so the models can see it roll.
    Orange still passes the red colour threshold of the tracker."""
    m = bpy.data.materials.new("ball")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.35
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    nt.links.new(sep.outputs["Z"], ab.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = 0.28 * r
    nt.links.new(ab.outputs[0], lt.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (0.8, 0.03, 0.03, 1)
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (0.95, 0.42, 0.03, 1)
    nt.links.new(lt.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def sphere(r, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    return assign(o, mat)


def box(size, loc, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    return assign(o, mat)


def cylinder(r, mat):
    """Unit-length cylinder along Z; place it between two points with set_between."""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=1.0, vertices=24)
    o = bpy.context.object
    bpy.ops.object.shade_smooth()
    o.rotation_mode = "QUATERNION"
    return assign(o, mat)


def plane(size, loc, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc, rotation=rot)
    return assign(bpy.context.object, mat)


def tube_rail(points, r, mat):
    cu = bpy.data.curves.new("rail", type="CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 4
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, v in zip(sp.points, points):
        p.co = (v.x, v.y, v.z, 1)
    o = bpy.data.objects.new("rail", cu)
    bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def set_between(obj, a, b, frame=None):
    d = b - a
    obj.location = (a + b) / 2
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    obj.scale = (1, 1, max(d.length, 1e-4))
    if frame is not None:
        for path in ("location", "rotation_quaternion", "scale"):
            obj.keyframe_insert(path, frame=frame)


def set_visible(obj, visible, frame):
    obj.hide_render = not visible
    obj.keyframe_insert("hide_render", frame=frame)


def camera(loc, target, lens=50):
    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = lens
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = 36
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def sun(rot, strength=3.0, angle=8):
    d = bpy.data.lights.new("sun", type="SUN")
    d.energy = strength
    d.angle = math.radians(angle)
    o = bpy.data.objects.new("sun", d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = [math.radians(a) for a in rot]
    return o


# ---------------------------------------------------------------- per-family scenes
class Scene3D:
    """Builds the static scene once; animate(xy) keyframes one version."""

    def __init__(self, meta):
        self.m = meta
        self.sc = meta["scene"]
        self.fam = meta["family"]
        self.r = meta["ball_radius"] * S
        self.mat_ball = ball_material(self.r)
        self.mat_dark = material("dark", (0.08, 0.08, 0.09), rough=0.35, metal=0.8)
        self.ball = sphere(self.r, self.mat_ball)
        self.moving = []  # objects that need keyframes
        if self.sc["view"] == "top":
            self._top_room()
        else:
            self._side_room()
        getattr(self, "build_" + self.fam)()

    # rooms ---------------------------------------------------------------
    def _top_room(self):
        wood = material("table", (0.50, 0.36, 0.24), rough=0.6, noise=((0.38, 0.26, 0.16), 8))
        plane(12, (0, 0, 0), (0, 0, 0), wood)
        camera((0, -4.7, 4.9), (0, 0.1, 0))
        sun((35, 10, 20))

    def _side_room(self):
        floor_y = self.sc.get("floor_y", H)
        self.floor_z = (H - floor_y) * S
        concrete = material("floor", (0.42, 0.40, 0.37), rough=0.8, noise=((0.32, 0.30, 0.28), 5))
        wall = material("wall", (0.62, 0.64, 0.66), rough=0.9)
        plane(30, (0, 3, self.floor_z), (0, 0, 0), concrete)
        plane(30, (0, 1.4, 5), (math.radians(90), 0, 0), wall)
        camera((0, -6.9, 1.95), (0, 0, 1.58))
        sun((50, 0, -30))

    # families ----------------------------------------------------------------
    def build_A1(self):
        c = self.sc["centerline"]
        hw = self.sc["half_width"]
        pts = [Vector(p) for p in c]
        rails = ([], [])
        for i, p in enumerate(pts):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            t = (b - a).normalized()
            n = Vector((-t.y, t.x))
            for side_i, sgn in enumerate((1, -1)):
                q = p + sgn * hw * n
                rails[side_i].append(top(q.x, q.y, 0.035))
        mat = material("rail", (0.55, 0.57, 0.6), rough=0.3, metal=0.6)
        for r in rails:
            tube_rail(r, 0.022, mat)

    def build_A2(self):
        cx, cy = self.sc["center"]
        mat = material("pin", (0.2, 0.2, 0.22), rough=0.3, metal=0.7)
        pin = cylinder(0.035, mat)
        set_between(pin, top(cx, cy, 0.0), top(cx, cy, 0.14))
        self.string = cylinder(0.007, material("string", (0.15, 0.13, 0.1), rough=0.8))
        self.moving.append("string")

    def build_A3(self):
        px, py = self.sc["pivot"]
        box((0.5, 0.15, 0.06), side(px, py - 3), self.mat_dark)
        self.rod = cylinder(0.008, material("string", (0.15, 0.13, 0.1), rough=0.8))
        self.moving.append("rod")

    def build_B1(self):
        ry = self.sc["rail_y"]
        rz = (H - ry) * S
        steel = material("steel", (0.6, 0.62, 0.65), rough=0.3, metal=0.8)
        box((8, 0.08, 0.05), (0, 0, rz), steel)
        for x in (-2.6, 2.6):
            box((0.08, 0.08, rz - self.floor_z), (x, 0.15, (rz + self.floor_z) / 2), steel)
        body_mat = material("trolley", (0.25, 0.33, 0.5), rough=0.4, metal=0.3)
        self.cart = bpy.data.objects.new("cart", None)
        bpy.context.scene.collection.objects.link(self.cart)
        parts = [box((0.5, 0.3, 0.18), (0, 0, rz - 0.025 - 0.09), body_mat)]
        for dx in (-0.14, 0.14):
            w = cylinder(0.05, self.mat_dark)
            set_between(w, Vector((dx, -0.1, rz + 0.075)), Vector((dx, 0.1, rz + 0.075)))
            parts.append(w)
        self.clamp = cylinder(0.012, self.mat_dark)
        for p in parts:
            p.parent = self.cart
        self.rz = rz
        self.moving += ["cart", "clamp"]

    def build_C1(self):
        px, py = self.sc["pivot"]
        box((0.6, 0.15, 0.06), side(px, py - 3), self.mat_dark)
        self.rod = cylinder(0.008, self.mat_dark)
        self.moving.append("rod")

    def build_D1(self):
        px, py = self.sc["pivot"]
        axle = cylinder(0.04, self.mat_dark)
        set_between(axle, side(px, py, -0.15), side(px, py, 0.05))
        self.rod1 = cylinder(0.012, self.mat_dark)
        self.rod2 = cylinder(0.012, self.mat_dark)
        self.bob1 = sphere(0.07, material("bob1", (0.08, 0.2, 0.75), rough=0.35))
        self.moving.append("double")

    # animation ------------------------------------------------------------
    def ball_at(self, x, y):
        if self.sc["view"] == "top":
            return top(x, y, self.r)
        return side(x, y)

    def animate(self, xy):
        for o in bpy.data.objects:
            o.animation_data_clear()
        sc = self.sc
        self.ball.rotation_mode = "QUATERNION"
        q = Quaternion()
        prev = None
        for f, (x, y) in enumerate(xy):
            fr = f + 1
            b = self.ball_at(x, y)
            self.ball.location = b
            self.ball.keyframe_insert("location", frame=fr)
            # v2: the ball rolls without slipping (rotation follows the distance travelled)
            if prev is not None and sc["view"] == "top" and all(math.isfinite(c) for c in b):
                d = b - prev
                if d.length > 1e-6:
                    axis = Vector((-d.y, d.x, 0.0)).normalized()
                    q = Quaternion(axis, d.length / self.r) @ q
            self.ball.rotation_quaternion = q
            self.ball.keyframe_insert("rotation_quaternion", frame=fr)
            prev = b.copy() if all(math.isfinite(c) for c in b) else prev
            if "string" in self.moving:
                cx, cy = sc["center"]
                set_between(self.string, top(cx, cy, self.r), b, fr)
                set_visible(self.string, f <= sc["string_until_frame"], fr)
            if "rod" in self.moving:
                px, py = sc["pivot"]
                set_between(self.rod, side(px, py), b, fr)
                if "rod_until_frame" in sc:
                    set_visible(self.rod, f <= sc["rod_until_frame"], fr)
            if "cart" in self.moving:
                self.cart.location = ((sc["cart_x"][f] - 240) * S, 0, 0)
                self.cart.keyframe_insert("location", frame=fr)
                cxw = (sc["cart_x"][f] - 240) * S
                set_between(self.clamp, Vector((cxw, 0, self.rz - 0.2)),
                            Vector((cxw, 0, (H - sc["rail_y"] - 30) * S + self.r)), fr)
                set_visible(self.clamp, f <= sc["clamp_until_frame"], fr)
            if "double" in self.moving:
                px, py = sc["pivot"]
                b1 = side(*sc["bob1_xy"][f])
                set_between(self.rod1, side(px, py), b1, fr)
                set_between(self.rod2, b1, b, fr)
                self.bob1.location = b1
                self.bob1.keyframe_insert("location", frame=fr)

    def project(self, xy):
        sc = bpy.context.scene
        out = []
        for x, y in xy:
            u, v, _ = world_to_camera_view(sc, sc.camera, self.ball_at(x, y))
            out.append([round(u * RW, 2), round((1 - v) * RH, 2)])
        return out


# ---------------------------------------------------------------- main
def render_range(out_dir, start, end):
    sc = bpy.context.scene
    os.makedirs(out_dir, exist_ok=True)
    sc.frame_start, sc.frame_end = start, end
    sc.render.filepath = os.path.join(os.path.abspath(out_dir), "")
    bpy.ops.render.render(animation=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="stimuli")
    ap.add_argument("--out", default="stimuli3d")
    ap.add_argument("--families", default="A1,A3,B1,C1")
    ap.add_argument("--items", default="", help="only items whose id contains one of these (comma-separated)")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--engine", choices=["cycles", "eevee"], default="cycles")
    ap.add_argument("--no-anomalous", action="store_true")
    ap.add_argument("--preview", action="store_true",
                    help="render only the critical frame of each item, to check the look quickly")
    args = ap.parse_args(argv)

    fams = [f.strip().upper() for f in args.families.split(",") if f.strip()]
    wanted = [s for s in args.items.split(",") if s]
    metas = sorted(glob.glob(os.path.join(args.src, "*", "*", "meta.json")))
    todo = []
    for p in metas:
        m = json.load(open(p))
        if m["family"] in fams and (not wanted or any(w in m["item_id"] for w in wanted)):
            if "scene" not in m:
                sys.exit(f"{p} has no scene geometry: re-run stimgen.py (newer version) first")
            todo.append(m)
    print(f"render3d: {len(todo)} items")

    for i, m in enumerate(todo, 1):
        d = os.path.join(args.out, m["family"], m["item_id"])
        os.makedirs(d, exist_ok=True)
        reset_scene(m["fps"], args.samples, args.engine)
        s3 = Scene3D(m)
        n = m["n_frames"]
        k = m["critical_frame"]
        versions = {"full": m["ball_xy"]}
        if not args.no_anomalous and not args.preview:
            for key in m:
                if key.startswith("anomalous") and key.endswith("_xy"):
                    versions[key[:-3]] = m[key]
        info = dict(item_id=m["item_id"], family=m["family"], fps=m["fps"], size=[RW, RH],
                    n_frames=n, critical_frame=k, context_end_frame=m["context_end_frame"],
                    source_meta=os.path.relpath(os.path.join(args.src, m["family"], m["item_id"], "meta.json"), d),
                    camera=dict(location=list(bpy.context.scene.camera.location),
                                rotation_euler=list(bpy.context.scene.camera.rotation_euler),
                                lens=bpy.context.scene.camera.data.lens),
                    engine=args.engine, samples=args.samples, versions=list(versions),
                    note="ball_xy_px: ball centre projected to output pixels (y down)")
        for name, xy in versions.items():
            s3.animate(xy)
            fdir = os.path.join(d, "frames_" + name)
            if args.preview:
                render_range(fdir, k + 1, k + 1)
            elif name == "full":
                render_range(fdir, 1, n)
            else:
                # identical to the full version up to the critical frame: copy those
                os.makedirs(fdir, exist_ok=True)
                for fr in range(1, k + 2):
                    shutil.copy(os.path.join(d, "frames_full", f"{fr:04d}.png"),
                                os.path.join(fdir, f"{fr:04d}.png"))
                render_range(fdir, k + 2, n)
            info[name + "_ball_xy_px"] = s3.project(xy)
        with open(os.path.join(d, "meta3d.json"), "w") as fh:
            json.dump(info, fh)
        print(f"render3d: [{i}/{len(todo)}] {m['item_id']}", flush=True)


if __name__ == "__main__":
    main()
