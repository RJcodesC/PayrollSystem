"""3D background plates for StickStudio, built and rendered with Blender (bpy, Cycles CPU).

Plates are rendered slightly larger than the 1080x1920 frame (default 1.2x) so the 2D layer can
pan/zoom over them. Usage:  python3 sets.py OUTDIR set1 [set2 ...] [--samples N] [--scale S]
"""
import math
import os
import sys

import bpy

R = math.radians


# ------------------------------------------------------------------ helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def mat(name, color, rough=0.7, brick=None, emit=None, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if brick:
        b = nt.nodes.new("ShaderNodeTexBrick")
        b.inputs["Color1"].default_value = (*brick[0], 1)
        b.inputs["Color2"].default_value = (*brick[1], 1)
        b.inputs["Mortar"].default_value = (*brick[2], 1)
        b.inputs["Scale"].default_value = brick[3]
        b.inputs["Mortar Size"].default_value = 0.012
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["UV"], b.inputs["Vector"])
        nt.links.new(b.outputs["Color"], bsdf.inputs["Base Color"])
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emit[1]
    return m


def box(loc, size, m, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(m)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL")
        b.width = bevel
        b.segments = 2
    return o


def cyl(loc, r, depth, m, rot=(0, 0, 0), verts=16):
    bpy.ops.mesh.primitive_cylinder_add(location=loc, radius=r, depth=depth, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def sphere(loc, r, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, radius=r, segments=32, ring_count=16)
    o = bpy.context.object
    o.scale = scale
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def array(o, count, offset):
    a = o.modifiers.new("arr", "ARRAY")
    a.count = count
    a.use_relative_offset = False
    a.use_constant_offset = True
    a.constant_offset_displace = offset
    return o


def light(kind, loc, energy, color=(1, 1, 1), rot=(0, 0, 0), size=0.2):
    bpy.ops.object.light_add(type=kind, location=loc, rotation=rot)
    L = bpy.context.object.data
    L.energy = energy
    L.color = color
    if kind == "AREA":
        L.size = size
    elif kind in ("POINT", "SPOT"):
        L.shadow_soft_size = size
    return L


def world(color, strength=0.5, top=None):
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    nt = w.node_tree
    bgn = nt.nodes["Background"]
    if top:  # vertical gradient sky
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.45
        ramp.color_ramp.elements[0].color = (*color, 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (*top, 1)
        nt.links.new(tc.outputs["Window"], sep.inputs["Vector"])
        nt.links.new(sep.outputs["Y"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bgn.inputs["Color"])
    else:
        bgn.inputs["Color"].default_value = (*color, 1)
    bgn.inputs["Strength"].default_value = strength
    bpy.context.scene.world = w


def camera(loc, rot, lens=24):
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    cam = bpy.context.object
    cam.data.lens = lens
    bpy.context.scene.camera = cam
    return cam


def render(sc, out, w, h, samples, exposure=0.0, look="AgX - Punchy"):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = look
    sc.view_settings.exposure = exposure
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ shared materials
def palette():
    return dict(
        wall=mat("wall", (0.55, 0.62, 0.52), 0.9, brick=((0.50, 0.60, 0.50), (0.44, 0.54, 0.45), (0.36, 0.42, 0.37), 6.0)),
        floor=mat("floor", (0.28, 0.30, 0.33), 0.6),
        steel=mat("steel", (0.22, 0.24, 0.27), 0.35, metal=0.6),
        bar=mat("bar", (0.30, 0.33, 0.36), 0.3, metal=0.8),
        sheet=mat("sheet", (0.92, 0.91, 0.87), 0.9),
        blanket=mat("blanket", (0.25, 0.33, 0.45), 0.9),
        porcelain=mat("porcelain", (0.92, 0.93, 0.95), 0.2),
        vent=mat("vent", (0.30, 0.32, 0.35), 0.5, metal=0.4),
        night=mat("night", (0.05, 0.08, 0.18), 1.0, emit=((0.25, 0.35, 0.7), 2.0)),
        crumble=mat("crumble", (0.62, 0.58, 0.50), 1.0),
    )


# ------------------------------------------------------------------ sets
def build_cell(sc, P, cam="wide", night=False):
    box((0, 0, -0.05), (3.2, 4.4, 0.1), P["floor"])
    box((0, 2.05, 1.5), (3.2, 0.1, 3.0), P["wall"])
    box((-1.55, 0, 1.5), (0.1, 4.4, 3.0), P["wall"])
    box((1.55, 0, 1.5), (0.1, 4.4, 3.0), P["wall"])
    box((0, 0, 3.05), (3.2, 4.4, 0.1), P["wall"])
    box((0, 1.99, 2.3), (0.6, 0.05, 0.5), P["night"])
    for x in (-0.18, 0, 0.18):
        box((x, 1.96, 2.3), (0.03, 0.03, 0.52), P["bar"])
    box((1.05, 0.9, 0.45), (0.9, 2.0, 0.08), P["steel"])
    box((1.05, 0.9, 0.55), (0.85, 1.9, 0.14), P["sheet"])
    box((1.05, 0.6, 0.63), (0.86, 1.2, 0.04), P["blanket"])
    for (x, y) in ((0.65, -0.05), (1.45, -0.05), (0.65, 1.85), (1.45, 1.85)):
        box((x, y, 0.22), (0.05, 0.05, 0.45), P["steel"])
    box((-0.9, 1.8, 0.85), (0.5, 0.4, 0.2), P["porcelain"])
    box((-0.9, 1.95, 0.45), (0.06, 0.06, 0.7), P["steel"])
    # the vent: dark grille with crumbled concrete around it
    box((-0.45, 1.995, 0.28), (0.36, 0.03, 0.26), P["vent"])
    g = box((-0.6, 1.975, 0.28), (0.02, 0.03, 0.22), P["steel"], bevel=0)
    array(g, 6, (0.06, 0, 0))
    for (x, z, r) in ((-0.67, 0.12, 0.03), (-0.25, 0.13, 0.025), (-0.23, 0.45, 0.02), (-0.65, 0.44, 0.02)):
        sphere((x, 1.97, z), r, P["crumble"], scale=(1.4, 0.6, 1))
    if night:  # lights out: cold moonlight through the window + faint corridor spill
        light("AREA", (0, 2.3, 2.4), 260, (0.45, 0.55, 1.0), rot=(R(-60), 0, 0), size=0.5)
        light("AREA", (0, -2.6, 2.0), 40, (0.5, 0.55, 0.8), rot=(R(70), 0, 0), size=2.0)
        world((0.01, 0.012, 0.02), 0.3)
    else:
        light("POINT", (0, 0.8, 2.7), 70, (1.0, 0.85, 0.65), size=0.15)
        light("AREA", (0, 2.3, 2.3), 140, (0.55, 0.65, 1.0), rot=(R(-70), 0, 0), size=0.6)
        world((0.06, 0.06, 0.08), 0.6)
    # a pillow so the bed reads from above
    box((1.05, 1.65, 0.66), (0.6, 0.35, 0.1), P["sheet"], bevel=0.04)
    if cam == "med":
        camera((-0.1, -1.0, 1.05), (R(88), 0, R(-4)), lens=26)
    elif cam == "bed":
        camera((0.6, 0.3, 2.6), (R(28), 0, R(-25)), lens=24)
    elif cam == "vent":
        camera((-0.3, 1.0, 0.36), (R(92), 0, R(9)), lens=24)
    else:
        camera((0, -2.9, 1.25), (R(88), 0, 0), lens=22)


def build_cellblock(sc, P):
    """Long cellhouse aisle: tiers of barred cells on the left, wall + windows on the right."""
    L = 30
    box((0, L / 2 - 2, -0.05), (8, L + 4, 0.1), P["floor"])
    cellwall = mat("cellwall", (0.62, 0.66, 0.60), 0.85)
    for tier in range(3):
        z0 = tier * 2.7
        box((-2.6, L / 2 - 2, z0 + 1.3), (0.3, L + 4, 2.6), cellwall, bevel=0)
        dark = mat(f"dark{tier}", (0.05, 0.05, 0.06), 1.0)
        # cell openings (dark) along the aisle, with bar arrays in front
        for k in range(14):
            y = k * 2.0
            box((-2.42, y, z0 + 1.15), (0.05, 1.6, 2.1), dark, bevel=0)
            b = cyl((-2.34, y - 0.75, z0 + 1.15), 0.025, 2.1, P["bar"], verts=8)
            array(b, 11, (0, 0.15, 0))
            box((-2.34, y, z0 + 2.25), (0.06, 1.7, 0.08), P["bar"])
        if tier > 0:  # catwalk + rail
            box((-2.0, L / 2 - 2, z0 - 0.05), (1.0, L + 4, 0.08), P["steel"])
            box((-1.5, L / 2 - 2, z0 + 1.0), (0.05, L + 4, 0.05), P["bar"])
            post = cyl((-1.5, -2, z0 + 0.5), 0.025, 1.0, P["bar"], verts=8)
            array(post, 18, (0, 1.8, 0))
    # right wall with tall windows
    box((3.0, L / 2 - 2, 4.5), (0.3, L + 4, 9), cellwall, bevel=0)
    sky = mat("winsky", (0.6, 0.75, 1.0), 1.0, emit=((0.75, 0.85, 1.0), 4.0))
    for k in range(6):
        box((2.84, 2 + k * 5, 5.0), (0.05, 1.6, 3.0), sky, bevel=0)
    box((0, L / 2 - 2, 9.1), (8, L + 4, 0.2), cellwall, bevel=0)
    # end wall
    box((0, L + 2, 4.5), (8, 0.3, 9), P["wall"], bevel=0)
    light("AREA", (0.5, 10, 8.6), 1400, (1.0, 0.95, 0.85), rot=(0, 0, 0), size=6)
    light("SUN", (5, 0, 10), 2.5, (0.85, 0.9, 1.0), rot=(R(55), R(-35), 0))
    world((0.08, 0.09, 0.1), 0.5)
    camera((0.9, -3.5, 1.7), (R(86), 0, R(14)), lens=20)


def build_island(sc, P):
    """Alcatraz-like island at dusk: rock, cellhouse, lighthouse, calm cold water."""
    water = mat("water", (0.05, 0.12, 0.22), 0.08)
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
    bpy.context.object.data.materials.append(water)
    rock = mat("rock", (0.30, 0.26, 0.22), 0.95)
    for (x, y, z, sx, sy, sz) in ((0, 60, -2, 30, 14, 8), (-14, 58, -3, 14, 10, 7), (16, 62, -3, 14, 10, 6)):
        sphere((x, y, z), 1, rock, scale=(sx, sy, sz))
    house = mat("house", (0.85, 0.82, 0.74), 0.8)
    box((0, 60, 7.5), (26, 9, 6), house)
    box((0, 60, 10.8), (26.5, 9.5, 0.6), mat("roof", (0.35, 0.33, 0.32), 0.7))
    lit = mat("lit", (1, 0.85, 0.5), 1, emit=((1.0, 0.75, 0.4), 6.0))
    for i in range(10):
        for row in range(2):
            box((-11 + i * 2.4, 55.4, 6.0 + row * 2.4), (0.8, 0.1, 1.2), lit, bevel=0)
    cyl((15, 58, 10), 1.0, 12, house, verts=24)
    cyl((15, 58, 16.6), 1.4, 1.2, mat("lamp", (1, 0.95, 0.7), 1, emit=((1, 0.9, 0.6), 30)), verts=24)
    # moon
    sphere((-30, 160, 45), 5, mat("moon", (1, 0.96, 0.8), 1, emit=((1, 0.95, 0.8), 8)))
    world((0.95, 0.45, 0.30), 1.0, top=(0.10, 0.10, 0.28))
    light("SUN", (0, 0, 30), 1.5, (1.0, 0.6, 0.45), rot=(R(80), 0, R(180)))
    light("POINT", (15, 57, 16.6), 3000, (1, 0.85, 0.6), size=1)
    camera((3, -12, 2.4), (R(87), 0, R(2)), lens=40)


def build_messhall(sc, P):
    tile = mat("tile", (0.82, 0.82, 0.76), 0.5, brick=((0.85, 0.85, 0.80), (0.80, 0.80, 0.74), (0.6, 0.6, 0.56), 10.0))
    wood = mat("wood", (0.45, 0.30, 0.18), 0.6)
    tray = mat("tray", (0.65, 0.68, 0.72), 0.3, metal=0.7)
    spoonm = mat("spoon", (0.85, 0.87, 0.9), 0.15, metal=1.0)
    box((0, 6, -0.05), (10, 18, 0.1), P["floor"])
    box((0, 14, 2.5), (10, 0.2, 5), tile, bevel=0)
    box((-4.9, 6, 2.5), (0.2, 18, 5), tile, bevel=0)
    box((4.9, 6, 2.5), (0.2, 18, 5), tile, bevel=0)
    box((0, 6, 5.05), (10, 18, 0.1), mat("ceil", (0.75, 0.75, 0.7), 0.8), bevel=0)
    for row, x in enumerate((-2.0, 2.0)):
        for k in range(3):
            y = 1.5 + k * 4
            box((x, y, 0.75), (1.0, 3.0, 0.08), wood)
            box((x, y, 0.37), (0.12, 2.6, 0.74), P["steel"])
            for side in (-0.8, 0.8):
                box((x + side, y, 0.45), (0.35, 3.0, 0.06), wood)
            for j in range(4):
                ty = y - 1.1 + j * 0.72
                box((x - 0.25, ty, 0.81), (0.35, 0.5, 0.03), tray)
                cyl((x - 0.05, ty + 0.05, 0.84), 0.012, 0.18, spoonm, rot=(R(90), 0, R(20)), verts=8)
    sky = mat("winsky2", (0.7, 0.8, 1), 1, emit=((0.8, 0.88, 1.0), 3.0))
    for k in range(3):
        box((-4.78, 2 + k * 4, 3.0), (0.05, 1.8, 2.0), sky, bevel=0)
    light("AREA", (0, 6, 4.8), 450, (1.0, 0.92, 0.8), size=6)
    light("SUN", (-5, 6, 6), 2, (0.85, 0.9, 1.0), rot=(R(50), R(40), 0))
    world((0.1, 0.1, 0.12), 0.5)
    camera((0.0, -2.6, 1.6), (R(84), 0, 0), lens=20)


def build_corridor(sc, P):
    """The hidden utility corridor behind the cells: pipes, grime, one work light."""
    grime = mat("grime", (0.32, 0.31, 0.27), 0.95, brick=((0.34, 0.33, 0.28), (0.28, 0.27, 0.23), (0.2, 0.2, 0.17), 5.0))
    pipe = mat("pipe", (0.45, 0.25, 0.15), 0.4, metal=0.7)
    pipe2 = mat("pipe2", (0.35, 0.37, 0.4), 0.3, metal=0.8)
    box((0, 8, -0.05), (1.6, 20, 0.1), mat("grate", (0.15, 0.15, 0.16), 0.6, metal=0.5))
    box((-0.85, 8, 4), (0.1, 20, 8), grime, bevel=0)
    box((0.85, 8, 4), (0.1, 20, 8), grime, bevel=0)
    for i, (x, z, r, m) in enumerate(((-0.6, 0.6, 0.08, pipe), (-0.6, 1.0, 0.05, pipe2), (0.6, 1.6, 0.1, pipe2),
                                      (0.6, 2.4, 0.06, pipe), (-0.55, 3.2, 0.12, pipe2))):
        cyl((x, 8, z), r, 20, m, rot=(R(90), 0, 0))
    v = cyl((-0.55, 3, 4), 0.07, 8, pipe)
    array(v, 4, (0, 4.0, 0))
    cyl((0.55, 5, 4), 0.06, 8, pipe2)
    bulb = mat("bulb", (1, 0.9, 0.6), 1, emit=((1, 0.8, 0.45), 40))
    sphere((0.4, 4.5, 2.9), 0.06, bulb)
    light("POINT", (0.4, 4.5, 2.85), 420, (1.0, 0.75, 0.45), size=0.05)
    light("POINT", (0, 14, 2.5), 80, (0.5, 0.6, 1.0), size=0.3)
    light("POINT", (0, 1.0, 1.6), 40, (0.6, 0.65, 0.8), size=0.5)
    world((0.01, 0.01, 0.015), 0.3)
    camera((0, -0.8, 1.4), (R(84), 0, 0), lens=18)


def build_roof(sc, P):
    """Cellhouse roof at night: tar roof, vent hatch, chimney stacks, the bay and city lights beyond."""
    roofm = mat("roofm", (0.18, 0.18, 0.2), 0.8)
    box((0, 10, -0.1), (14, 26, 0.2), roofm, bevel=0)
    box((0, 23, -0.6), (14.5, 0.4, 1.2), roofm, bevel=0)
    vent = mat("venthood", (0.45, 0.47, 0.5), 0.4, metal=0.6)
    box((-1.6, 3.5, 0.45), (1.2, 1.2, 0.9), vent)
    box((-1.6, 3.5, 0.95), (1.4, 1.4, 0.1), vent)
    for (x, y) in ((3.5, 9), (-4.5, 14), (2.0, 17)):
        box((x, y, 1.2), (0.8, 0.8, 2.4), mat("brick%d" % int(x), (0.5, 0.3, 0.25), 0.9,
                                                  brick=((0.5, 0.3, 0.24), (0.42, 0.25, 0.2), (0.3, 0.28, 0.26), 4.0)))
    water = mat("bay", (0.02, 0.05, 0.12), 0.1)
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -12))
    bpy.context.object.data.materials.append(water)
    city = mat("city", (1, 0.8, 0.5), 1, emit=((1.0, 0.75, 0.45), 8))
    import random
    rng = random.Random(2)
    for i in range(70):
        box((rng.uniform(-80, 80), rng.uniform(170, 200), -11 + rng.uniform(0, 6)), (0.6, 0.6, 0.6), city, bevel=0)
    sphere((25, 220, 60), 6, mat("moon2", (1, 0.96, 0.8), 1, emit=((1, 0.95, 0.85), 10)))
    world((0.03, 0.05, 0.12), 1.0, top=(0.01, 0.01, 0.04))
    light("SUN", (0, 0, 20), 0.6, (0.6, 0.7, 1.0), rot=(R(60), 0, R(200)))
    light("SPOT", (6, 20, 6), 2500, (1, 0.95, 0.8), rot=(R(60), 0, R(150)), size=0.3)
    camera((0.5, -3.2, 1.5), (R(84), 0, R(-3)), lens=22)


SETS = {
    "cell_med": lambda sc, P: build_cell(sc, P, "med"),
    "cell_bed": lambda sc, P: build_cell(sc, P, "bed"),
    "cell_night": lambda sc, P: build_cell(sc, P, "wide", night=True),
    "cell_night_med": lambda sc, P: build_cell(sc, P, "med", night=True),
    "cell_night_bed": lambda sc, P: build_cell(sc, P, "bed", night=True),
    "roof": build_roof,
    "cell": lambda sc, P: build_cell(sc, P, "wide"),
    "vent": lambda sc, P: build_cell(sc, P, "vent"),
    "cellblock": build_cellblock,
    "island": build_island,
    "messhall": build_messhall,
    "corridor": build_corridor,
}
EXPOSURE = {"cell_med": -0.3, "cell_bed": -0.3, "cell_night": 0.6, "cell_night_med": 0.6, "cell_night_bed": 0.6,
            "roof": 0.8, "island": 0.0, "corridor": 0.4, "cellblock": -0.2, "messhall": -0.3, "cell": -0.3, "vent": 0.2}

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
        P = palette()
        SETS[n](sc, P)
        out = os.path.join(outdir, n + ".png")
        render(sc, out, int(1080 * scale), int(1920 * scale), samples, EXPOSURE.get(n, 0.0))
        print("PLATE", out, flush=True)
