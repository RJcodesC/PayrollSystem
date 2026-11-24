"""3D sets for 'Why Airplane Windows Are Round' (original stylised models, not real liveries)."""
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sets import reset, mat, box, cyl, sphere, light, world, camera, render, R  # noqa: E402


def jet(loc=(0, 0, 0), rot=0.0, square=True, scale=1.0, body=None):
    """Simple 1950s-style jet airliner: fuselage along +Y (nose at +Y)."""
    body = body or mat("jetbody", (0.92, 0.93, 0.95), 0.35, metal=0.3)
    stripe = mat("stripe", (0.12, 0.30, 0.62), 0.4)
    glass = mat("winglass", (0.05, 0.07, 0.1), 0.1)
    parts = []
    x0, y0, z0 = 0.0, 0.0, 0.0
    s = scale
    before = set(bpy.data.objects)
    parts.append(cyl((x0, y0, z0), 1.5 * s, 22 * s, body, rot=(R(90), 0, 0), verts=40))
    parts.append(sphere((x0, y0 + 11 * s, z0), 1.5 * s, body, scale=(1, 2.4, 1)))
    tail = sphere((x0, y0 - 11 * s, z0 + 0.3 * s), 1.5 * s, body, scale=(0.8, 3.2, 0.8))
    parts.append(tail)
    parts.append(box((x0, y0, z0 - 0.2 * s), (3.06 * s, 22 * s, 0.35 * s), stripe, bevel=0))
    for side in (-1, 1):  # wings
        w = box((x0 + side * 7 * s, y0 + 0.5 * s, z0 - 0.7 * s), (12 * s, 4 * s, 0.3 * s), body,
                rot=(0, R(side * -4), R(side * 18)))
        parts.append(w)
        parts.append(box((x0 + side * 3 * s, y0 - 12.5 * s, z0 + 0.3 * s), (4.5 * s, 2 * s, 0.2 * s), body,
                         rot=(0, 0, R(side * 15))))
    parts.append(box((x0, y0 - 12.5 * s, z0 + 2.4 * s), (0.25 * s, 3 * s, 3.6 * s), body, rot=(R(-18), 0, 0)))
    for k in range(14):  # windows on the -X side (camera side)
        y = y0 + 7 * s - k * 1.15 * s
        if square:
            box((x0 - 1.47 * s, y, z0 + 0.45 * s), (0.1 * s, 0.55 * s, 0.55 * s), glass, bevel=0)
        else:
            cyl((x0 - 1.47 * s, y, z0 + 0.45 * s), 0.27 * s, 0.1 * s, glass, rot=(0, R(90), 0), verts=24)
    box((x0 - 0.9 * s, y0 + 12.3 * s, z0 + 0.7 * s), (0.6 * s, 1.0 * s, 0.4 * s), glass, bevel=0)  # cockpit
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:  # bake modifiers so the join keeps bevels
        bpy.context.view_layer.objects.active = o
        for m in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.ops.object.select_all(action="DESELECT")
    for o in new:
        o.select_set(True)
    bpy.context.view_layer.objects.active = new[0]
    bpy.ops.object.join()
    j = bpy.context.object
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    j.location = loc
    j.rotation_euler = (0, 0, rot)
    return j


def look_cam(loc, target, lens=30):
    """Camera at loc aimed at target (vertical 9:16 frame)."""
    from mathutils import Vector
    cam = camera(loc, (0, 0, 0), lens)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return cam


def sky_world(top=(0.10, 0.32, 0.85), bottom=(0.50, 0.72, 1.0), strength=1.2):
    world(bottom, strength, top=top)


def clouds(n, area, z, rng, size=(3, 8)):
    white = mat("cloud", (1, 1, 1), 1.0)
    for i in range(n):
        cx, cy = rng.uniform(*area[0]), rng.uniform(*area[1])
        for k in range(5):
            sphere((cx + rng.uniform(-4, 4), cy + rng.uniform(-2, 2), z + rng.uniform(-1, 1.5)),
                   rng.uniform(*size), white, scale=(1.4, 1, 0.7))


def build_sky_plane(sc):
    rng = random.Random(3)
    jet((0, 0, 0), square=True)
    clouds(14, ((-80, 80), (-40, 120)), -18, rng)
    sky_world()
    light("SUN", (0, 0, 50), 4.0, (1, 0.97, 0.9), rot=(R(40), R(-30), R(20)))
    look_cam((-18, 8, -5), (0, 3.5, 0), lens=24)


def build_windows(sc, square=True):
    jet((0, 0, 0), square=square)
    rng = random.Random(4)
    clouds(10, ((-90, 20), (-60, 80)), -16, rng)
    sky_world()
    light("SUN", (0, 0, 50), 4.0, (1, 0.97, 0.9), rot=(R(50), R(-40), R(-60)))
    camera((-5.0, 3.2, 0.5), (R(90), 0, R(-90)), lens=40)


def build_cabin(sc, square=True):
    wall = mat("cabinwall", (0.93, 0.91, 0.86), 0.6)
    carpet = mat("carpet", (0.35, 0.18, 0.2), 0.9)
    seat = mat("seat", (0.15, 0.32, 0.6), 0.7)
    sky = mat("cabsky", (0.6, 0.8, 1), 1, emit=((0.65, 0.82, 1.0), 6))
    box((0, 8, -0.05), (3.4, 20, 0.1), carpet, bevel=0)
    box((0, 8, 2.3), (3.4, 20, 0.1), wall, bevel=0)
    for side in (-1, 1):
        box((side * 1.75, 8, 1.15), (0.1, 20, 2.4), wall, bevel=0)
        for k in range(14):
            y = -0.5 + k * 1.3
            if square:
                box((side * 1.69, y, 1.35), (0.04, 0.45, 0.45), sky, bevel=0)
            else:
                cyl((side * 1.69, y, 1.35), 0.22, 0.04, sky, rot=(0, R(90), 0), verts=24)
            for x in (0.75, 1.25):
                box((side * x, y, 0.45), (0.45, 0.5, 0.15), seat)
                box((side * x, y - 0.25, 0.85), (0.45, 0.1, 0.8), seat)
    light("AREA", (0, 8, 2.2), 900, (1, 0.95, 0.85), size=3)
    world((0.5, 0.6, 0.8), 0.6)
    camera((0, -1.2, 1.35), (R(88), 0, 0), lens=22)


def build_hangar(sc):
    floor = mat("hfloor", (0.45, 0.46, 0.48), 0.5)
    wallm = mat("hwall", (0.55, 0.58, 0.55), 0.8)
    box((0, 20, -0.05), (60, 80, 0.1), floor, bevel=0)
    box((-30, 20, 12), (0.5, 80, 24), wallm, bevel=0)
    box((30, 20, 12), (0.5, 80, 24), wallm, bevel=0)
    box((0, 60, 12), (60, 0.5, 24), wallm, bevel=0)
    for k in range(7):
        box((0, k * 10 - 10, 24), (60, 0.6, 1.2), mat("truss%d" % k, (0.3, 0.32, 0.34), 0.5, metal=0.5), bevel=0)
    jet((-9, 22, 3.2), rot=R(18))
    jet((11, 34, 3.2), rot=R(-15))
    light("AREA", (0, 20, 23), 30000, (1, 0.96, 0.88), size=30)
    world((0.6, 0.7, 0.85), 0.4)
    camera((1, -20, 4), (R(85), 0, 0), lens=22)


def build_tank(sc):
    floor = mat("tfloor", (0.4, 0.4, 0.42), 0.6)
    concrete = mat("concrete", (0.62, 0.6, 0.56), 0.9)
    water = bpy.data.materials.new("water")
    water.use_nodes = True
    nt = water.node_tree
    pb = nt.nodes["Principled BSDF"]
    pb.inputs["Base Color"].default_value = (0.35, 0.7, 0.9, 1)
    pb.inputs["Roughness"].default_value = 0.08
    pb.inputs["Alpha"].default_value = 0.45
    box((0, 20, -0.05), (80, 80, 0.1), floor, bevel=0)
    box((0, 55, 15), (80, 0.5, 30), concrete, bevel=0)
    # the tank: concrete walls with a big water volume
    box((0, 25, 4), (16, 30, 8), water, bevel=0)
    for (x, y, sx, sy) in ((-8.3, 25, 0.6, 30.6), (8.3, 25, 0.6, 30.6), (0, 40.3, 17.2, 0.6)):
        box((x, y, 4.2), (sx, sy, 8.4), concrete, bevel=0)
    box((0, 9.7, 1.0), (17.2, 0.6, 2.0), concrete, bevel=0)  # low front wall so we see the water
    jet((0, 25, 3.2), square=True, scale=0.62)
    # gantry crane
    steel = mat("gantry", (0.85, 0.65, 0.12), 0.5, metal=0.4)
    for x in (-9.5, 9.5):
        box((x, 18, 7), (0.6, 0.6, 14), steel)
        box((x, 32, 7), (0.6, 0.6, 14), steel)
    box((0, 18, 14), (20, 0.8, 0.8), steel)
    box((0, 32, 14), (20, 0.8, 0.8), steel)
    for y in (18, 32):
        box((0, y, 11), (0.08, 0.08, 6), mat("cable", (0.1, 0.1, 0.1), 0.5), bevel=0)
    # pipes + pump
    pipe = mat("tpipe", (0.6, 0.15, 0.12), 0.4, metal=0.6)
    cyl((-10.5, 12, 1.2), 0.4, 8, pipe, rot=(R(90), 0, 0))
    box((-11, 8, 1.5), (2, 2, 3), mat("pump", (0.25, 0.45, 0.3), 0.5, metal=0.4))
    light("AREA", (0, 22, 26), 40000, (1, 0.97, 0.9), size=30)
    light("SUN", (0, 0, 30), 2.0, (1, 0.95, 0.85), rot=(R(45), R(25), 0))
    world((0.55, 0.65, 0.8), 0.5)
    look_cam((-6, 2, 16), (0, 24, 3), lens=20)


EXPOSURE = {"sky_plane": -0.9, "windows_square": -0.9, "windows_round": -0.9, "hangar": -0.4, "tank": -0.5}

SETS = {
    "sky_plane": build_sky_plane,
    "windows_square": lambda sc: build_windows(sc, True),
    "windows_round": lambda sc: build_windows(sc, False),
    "cabin_square": lambda sc: build_cabin(sc, True),
    "cabin_round": lambda sc: build_cabin(sc, False),
    "hangar": build_hangar,
    "tank": build_tank,
}

if __name__ == "__main__":
    args = sys.argv[1:]
    samples, scale = 32, 1.2
    if "--samples" in args:
        i = args.index("--samples")
        samples = int(args[i + 1])
        del args[i:i + 2]
    if "--scale" in args:
        i = args.index("--scale")
        scale = float(args[i + 1])
        del args[i:i + 2]
    outdir, names = args[0], args[1:]
    os.makedirs(outdir, exist_ok=True)
    for n in names:
        sc = reset()
        SETS[n](sc)
        out = os.path.join(outdir, n + ".png")
        render(sc, out, int(1080 * scale), int(1920 * scale), samples, EXPOSURE.get(n, 0.0))
        print("PLATE", out, flush=True)
