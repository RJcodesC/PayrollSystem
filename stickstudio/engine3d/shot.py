"""Render one shot: an animated 3D camera through a set, plus per-frame screen projections of
character anchor points (so 2D characters can be composited at the right place and size).

Film grammar (measured from top stick-figure channels):
- the camera travels slowly into the next moment, then LANDS; key words are spoken while it is still
- wide lens, camera close to the characters
- low sun, long shadows, blue in the shade, haze on the horizon; light changes when the story turns

Usage:  python3 shot.py SPEC.json
SPEC = {"set": "deck", "module": "sets_pirate", "light": "golden", "out": "dir", "w": 540, "h": 960,
        "samples": 8, "times": [..seconds..],
        "cam": [{"t": 0, "loc": [x,y,z], "target": [x,y,z], "lens": 24}, ...],
        "anchors": {"hero": [x, y, z, height_m], ...}}
Writes out/frame_XXXXX.png (reusing a render when the camera did not move) and out/proj.json.
"""
import importlib
import json
import math
import os
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sets import reset, light, R  # noqa: E402


def ease(p):
    p = max(0.0, min(1.0, p))
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def cam_at(keys, t):
    """Eased interpolation between camera keys. Between two keys with the same pose the camera rests."""
    if t <= keys[0]["t"]:
        k = keys[0]
        return Vector(k["loc"]), Vector(k["target"]), k.get("lens", 24)
    for a, b in zip(keys, keys[1:]):
        if a["t"] <= t <= b["t"]:
            p = ease((t - a["t"]) / max(1e-6, b["t"] - a["t"]))
            la, lb = Vector(a["loc"]), Vector(b["loc"])
            ta, tb = Vector(a["target"]), Vector(b["target"])
            return la.lerp(lb, p), ta.lerp(tb, p), a.get("lens", 24) + (b.get("lens", 24) - a.get("lens", 24)) * p
    k = keys[-1]
    return Vector(k["loc"]), Vector(k["target"]), k.get("lens", 24)


def strip_lights_and_cameras():
    for o in list(bpy.data.objects):
        if o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)


def lighting(preset):
    """Low sun + long shadows + blue shade + haze (mist pass composited in)."""
    sc = bpy.context.scene
    w = sc.world
    if preset == "golden":
        light("SUN", (0, 0, 30), 4.5, (1.0, 0.72, 0.45), rot=(R(78), 0, R(-35)), size=0.3)  # sun ~12 deg high
        sky_strength, haze, haze_col = 1.0, 0.28, (1.0, 0.8, 0.6)
    elif preset == "sunset":
        light("SUN", (0, 0, 30), 3.5, (1.0, 0.5, 0.28), rot=(R(84), 0, R(-25)), size=0.3)
        sky_strength, haze, haze_col = 0.85, 0.38, (1.0, 0.58, 0.38)
    elif preset == "hold":  # below deck: one warm lantern, blue fill
        light("POINT", (0.8, 6, 1.95), 220, (1, 0.62, 0.28), size=0.1)
        light("AREA", (0, 0, 2.2), 60, (0.35, 0.45, 0.9), size=3)
        sky_strength, haze, haze_col = 0.3, 0.18, (0.35, 0.22, 0.12)
    elif preset == "lab":
        light("AREA", (0, 12, 7.8), 2200, (0.75, 0.82, 1.0), size=10)
        light("SPOT", (0, 6, 7.5), 1500, (1.0, 0.9, 0.75), size=0.4)
        sky_strength, haze, haze_col = 0.4, 0.12, (0.5, 0.6, 0.75)
    else:
        sky_strength, haze, haze_col = 1.0, 0.3, (0.8, 0.85, 0.9)
    if w and w.node_tree and "Background" in w.node_tree.nodes:
        w.node_tree.nodes["Background"].inputs["Strength"].default_value = sky_strength
    return haze, haze_col


def depth_material():
    """Emission shader whose brightness = camera depth / 200 m (rendered with a Standard view transform)."""
    m = bpy.data.materials.new("depth_override")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    cd = nt.nodes.new("ShaderNodeCameraData")
    dv = nt.nodes.new("ShaderNodeMath")
    dv.operation = "DIVIDE"
    dv.inputs[1].default_value = 200.0
    em = nt.nodes.new("ShaderNodeEmission")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(cd.outputs["View Z Depth"], dv.inputs[0])
    nt.links.new(dv.outputs[0], em.inputs["Color"])
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def depth_pass(sc, vl, dmat, fname):
    """Depth for haze: 1 sample, emission override, linear output, transparent sky."""
    keep = (sc.cycles.samples, sc.cycles.use_denoising, sc.view_settings.view_transform,
            sc.view_settings.look, sc.view_settings.exposure)
    sc.cycles.samples, sc.cycles.use_denoising = 1, False
    sc.view_settings.view_transform, sc.view_settings.exposure = "Standard", 0.0
    sc.render.film_transparent = True
    vl.material_override = dmat
    sc.render.filepath = fname.replace(".png", "_depth.png")
    bpy.ops.render.render(write_still=True)
    vl.material_override = None
    sc.render.film_transparent = False
    (sc.cycles.samples, sc.cycles.use_denoising, sc.view_settings.view_transform,
     sc.view_settings.look, sc.view_settings.exposure) = keep


def main(spec_path):
    spec = json.load(open(spec_path))
    mod = importlib.import_module(spec.get("module", "sets_pirate"))
    sc = reset()
    builder = mod.SETS[spec["set"]]
    builder(sc)
    strip_lights_and_cameras()
    preset = spec.get("light", "golden")
    if preset in getattr(mod, "LIGHTS", {}):  # set modules may bring their own light rigs
        haze, haze_col = mod.LIGHTS[preset]()
    else:
        haze, haze_col = lighting(preset)
    dmat = depth_material()
    vl = sc.view_layers[0]
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    sc.camera = cam
    cam.data.sensor_fit = "VERTICAL"
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = spec.get("samples", 8)
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = spec.get("w", 540), spec.get("h", 960)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = spec.get("exposure", 0.0)
    out = spec["out"]
    os.makedirs(out, exist_ok=True)
    proj = {"frames": []}
    last_pose = None
    last_file = None
    for i, t in enumerate(spec["times"]):
        loc, tgt, lens = cam_at(spec["cam"], t)
        cam.location = loc
        cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
        cam.data.lens = lens
        bpy.context.view_layer.update()
        pose = (round(loc.x, 4), round(loc.y, 4), round(loc.z, 4), round(tgt.x, 4), round(tgt.y, 4), round(tgt.z, 4),
                round(lens, 3))
        fname = os.path.join(out, f"frame_{i:05d}.png")
        if pose == last_pose and last_file:
            fname = last_file  # camera at rest: reuse the previous render
        else:
            sc.render.filepath = fname
            bpy.ops.render.render(write_still=True)
            last_pose, last_file = pose, fname
            if haze > 0:  # the depth pass only feeds the haze; skip it for indoor rigs without haze
                depth_pass(sc, vl, dmat, fname)
        anchors = {}
        for name, val in spec.get("anchors", {}).items():
            if isinstance(val, dict):  # moving anchor: eased between keys
                ks, hgt = val["keys"], val["h"]
                x, y, z = ks[-1][1:]
                if t <= ks[0][0]:
                    x, y, z = ks[0][1:]
                for ka, kb in zip(ks, ks[1:]):
                    if ka[0] <= t <= kb[0]:
                        pp = ease((t - ka[0]) / max(1e-6, kb[0] - ka[0]))
                        x, y, z = (ka[i] + (kb[i] - ka[i]) * pp for i in (1, 2, 3))
            else:
                x, y, z, hgt = val
            foot = world_to_camera_view(sc, cam, Vector((x, y, z)))
            head = world_to_camera_view(sc, cam, Vector((x, y, z + hgt)))
            anchors[name] = {"x": foot.x, "y": 1 - foot.y, "hx": head.x, "hy": 1 - head.y, "depth": foot.z}
        proj["frames"].append({"t": t, "file": os.path.basename(fname), "anchors": anchors})
        print("FRAME", i, len(spec["times"]), flush=True)
    proj["haze"] = {"amount": haze, "color": haze_col}
    json.dump(proj, open(os.path.join(out, "proj.json"), "w"))


if __name__ == "__main__":
    main(sys.argv[1])
