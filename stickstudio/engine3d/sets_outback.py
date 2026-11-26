"""Outback wheat farm, Western Australia 1932 (The Great Emu War).

Layout (metres, z up):
  dirt road      x in [-2.5, 2.5], running along y
  wire fence     x = 3.2 (posts every 3 m); a knocked-down section at y in [9, 16]
  wheat field    x > 3.6 (dense wheat cards near the road, textured field further out)
  sandbag post   x ~ 5.5, y in [-1.6, 1.6] (soldiers stand behind it at x ~ 4.6, facing +x)
  farmhouse      (-13, 20), windmill (-7, 27), gum trees around, hills on the horizon (+y far)
  truck          object named "truck", built at the origin facing +y, parked at (0, -7)
"""
import math
import os
import random
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sets import mat, box, cyl, sphere, R  # noqa: E402


def noise_mat(name, c1, c2, scale=4.0, rough=0.9, detail=6.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = detail
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def field_mat():
    """Far wheat: golden with row stripes and noise."""
    m = bpy.data.materials.new("field")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.95
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 0.9
    wave.inputs["Distortion"].default_value = 2.0
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.6
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "FLOAT"
    mix.inputs["Factor"].default_value = 0.5
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.62, 0.3, 0.03, 1)
    ramp.color_ramp.elements[1].color = (0.92, 0.58, 0.1, 1)
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], mix.inputs[2])
    nt.links.new(nz.outputs["Fac"], mix.inputs[3])
    nt.links.new(mix.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def wheat_cards(x0, x1, y0, y1, n, seed=1, gap=None, wscale=1.0, clear=()):
    """Thousands of thin golden stalk cards with a seed head, as one mesh."""
    rnd = random.Random(seed)
    me = bpy.data.meshes.new("wheat")
    bm = bmesh.new()
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        if gap and gap[0] < y < gap[1] and x < gap[2]:  # trampled patch by the broken fence
            if rnd.random() < 0.8:
                continue
        if any(a <= x <= b and c <= y <= d for (a, b, c, d) in clear):  # trampled patches
            continue
        h = rnd.uniform(0.75, 1.05)
        a = rnd.uniform(0, math.pi)
        lean = rnd.uniform(-0.12, 0.12)
        dx, dy = math.cos(a) * 0.009 * wscale, math.sin(a) * 0.009 * wscale
        tx, ty = lean * h, lean * h * 0.5
        v = [bm.verts.new((x - dx, y - dy, 0)), bm.verts.new((x + dx, y + dy, 0)),
             bm.verts.new((x + dx * 2.2 + tx, y + dy * 2.2 + ty, h)), bm.verts.new((x - dx * 2.2 + tx, y - dy * 2.2 + ty, h))]
        bm.faces.new(v)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("wheat", me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new("stalk")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.8
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.42, 0.24, 0.03, 1)
    ramp.color_ramp.elements[1].color = (1.0, 0.74, 0.16, 1)
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nt.links.new(sep.outputs[2], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    o.data.materials.append(m)
    return o


def gum_tree(loc, h=7.0, seed=0):
    rnd = random.Random(seed)
    bark = noise_mat(f"bark{seed}", (0.75, 0.72, 0.66), (0.92, 0.9, 0.85), 3)
    leaf = noise_mat(f"leaf{seed}", (0.24, 0.32, 0.16), (0.42, 0.5, 0.26), 2)
    x, y, z = loc
    cyl((x, y, z + h * 0.35), 0.22, h * 0.7, bark, verts=10)
    for k in range(2):  # two leaning branches
        a = rnd.uniform(0, 2 * math.pi)
        cyl((x + math.cos(a) * 0.6, y + math.sin(a) * 0.6, z + h * 0.68), 0.1, h * 0.35, bark,
            rot=(math.sin(a) * 0.6, -math.cos(a) * 0.6, 0), verts=8)
    for k in range(6):  # clumpy canopy
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.6, 1.8)
        sphere((x + math.cos(a) * rr, y + math.sin(a) * rr, z + h * rnd.uniform(0.75, 1.0)), rnd.uniform(1.0, 1.6),
               leaf, scale=(1, 1, 0.6))


def windmill(loc):
    steel = mat("steel", (0.55, 0.56, 0.58), 0.4, metal=0.7)
    red = mat("vane", (0.72, 0.18, 0.12), 0.5)
    x, y, z = loc
    H = 8.0
    for dx, dy in ((-0.8, -0.8), (0.8, -0.8), (0.8, 0.8), (-0.8, 0.8)):  # tapered lattice legs
        L = math.hypot(H, 0.6)
        cyl((x + dx * 0.6, y + dy * 0.6, z + H / 2), 0.05, L, steel, rot=(-dy * 0.09, dx * 0.09, 0), verts=6)
    for k in range(1, 5):
        zz = z + k * H / 5
        w = 1.6 * (1 - k / 6.5)
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            box((x + (a[0] + b[0]) * w / 4, y + (a[1] + b[1]) * w / 4, zz),
                (abs(a[0] - b[0]) * w / 2 + 0.04, abs(a[1] - b[1]) * w / 2 + 0.04, 0.05), steel, bevel=0)
    hub = (x, y - 0.4, z + H + 0.3)
    cyl(hub, 0.2, 0.3, steel, rot=(R(90), 0, 0))
    for k in range(14):  # fan blades
        a = k * 2 * math.pi / 14
        box((hub[0] + math.cos(a) * 1.1, hub[1] - 0.1, hub[2] + math.sin(a) * 1.1), (1.4, 0.03, 0.32), steel,
            rot=(0, -a, 0), bevel=0)
    box((x, y + 1.3, z + H + 0.3), (0.05, 2.2, 0.9), red, bevel=0)  # tail vane
    cyl((x + 2.2, y, z + 0.6), 1.2, 1.2, mat("tank", (0.5, 0.52, 0.5), 0.5, metal=0.5))  # water tank


def farmhouse(loc):
    wall = noise_mat("weatherboard", (0.82, 0.78, 0.68), (0.95, 0.92, 0.84), 6)
    iron = mat("corrugated", (0.6, 0.62, 0.62), 0.35, metal=0.8)
    trim = mat("trim", (0.25, 0.4, 0.3), 0.6)
    x, y, z = loc
    box((x, y, z + 1.5), (6, 9, 3), wall)
    for s in (-1, 1):  # pitched iron roof
        box((x + s * 1.75, y, z + 3.6), (3.9, 10.2, 0.08), iron, rot=(0, s * R(-28), 0), bevel=0)
    box((x + 3.8, y, z + 2.6), (1.8, 10, 0.06), iron, rot=(0, R(10), 0), bevel=0)  # veranda roof
    for k in range(5):
        cyl((x + 4.6, y - 4.5 + k * 2.25, z + 1.3), 0.07, 2.6, trim, verts=8)
    box((x + 3.02, y - 1.5, z + 1.1), (0.05, 1.0, 2.1), trim)  # door
    for dy in (1.5, 3.3):
        box((x + 3.02, y + dy, z + 1.6), (0.05, 1.0, 1.0), mat(f"win{dy}", (0.12, 0.16, 0.2), 0.1))
    box((x - 1.5, y + 3.0, z + 4.2), (0.6, 0.6, 1.6), mat("chimney", (0.55, 0.3, 0.22), 0.8))


def fence(x, y0, y1, broken=(9, 16)):
    post = noise_mat("post", (0.35, 0.25, 0.15), (0.55, 0.42, 0.28), 8)
    wire = mat("wire", (0.4, 0.4, 0.42), 0.4, metal=0.8)
    y = y0
    while y <= y1:
        if broken[0] <= y <= broken[1]:
            cyl((x + 0.35, y, 0.35), 0.06, 1.3, post, rot=(R(12), R(70), 0), verts=8)  # knocked flat
        else:
            cyl((x, y, 0.6), 0.06, 1.3, post, verts=8)
        y += 3.0
    for zz in (0.45, 0.8, 1.15):
        for (a, b) in ((y0, broken[0] - 1), (broken[1] + 2, y1)):
            cyl((x, (a + b) / 2, zz), 0.008, b - a, wire, rot=(R(90), 0, 0), verts=4)
        cyl((x + 0.6, (broken[0] + broken[1]) / 2, 0.05 + zz * 0.05), 0.008, broken[1] - broken[0], wire,
            rot=(R(90), R(8), 0), verts=4)  # sagging on the ground


def sandbags(x, y0, y1):
    bag = noise_mat("bag", (0.6, 0.52, 0.36), (0.75, 0.66, 0.48), 12)
    for row in range(3):
        n = int((y1 - y0) / 0.55)
        for k in range(n):
            yy = y0 + k * 0.55 + (0.27 if row % 2 else 0) + 0.27
            if yy > y1:
                continue
            o = sphere((x, yy, 0.16 + row * 0.27), 0.3, bag, scale=(1.0, 0.95, 0.5))
            o.rotation_euler = (0, 0, R(90))


def truck():
    """1930s army truck: cab, long bonnet, round mudguards, flat tray. Built at the origin facing +y,
    joined into one object named 'truck'."""
    olive = noise_mat("olive", (0.33, 0.36, 0.22), (0.42, 0.45, 0.28), 5, rough=0.6)
    dark = mat("tyre", (0.05, 0.05, 0.05), 0.8)
    chrome = mat("chrome", (0.8, 0.8, 0.82), 0.2, metal=1.0)
    glass = mat("glass", (0.15, 0.2, 0.25), 0.05)
    wood = noise_mat("tray", (0.45, 0.32, 0.18), (0.6, 0.45, 0.28), 10)
    before = set(bpy.data.objects)
    box((0, 1.6, 0.95), (1.3, 1.6, 0.7), olive)                 # bonnet
    cyl((0, 1.6, 1.3), 0.62, 1.6, olive, rot=(R(90), 0, 0), verts=24).scale = (1, 1, 0.35)  # rounded top
    box((0, 2.42, 1.0), (1.1, 0.08, 0.75), chrome)              # grille
    cyl((0.45, 2.45, 1.25), 0.12, 0.12, chrome, rot=(R(90), 0, 0))  # headlights
    cyl((-0.45, 2.45, 1.25), 0.12, 0.12, chrome, rot=(R(90), 0, 0))
    box((0, 0.3, 1.45), (1.6, 1.1, 1.5), olive)                 # cab
    box((0, 0.86, 1.75), (1.4, 0.04, 0.55), glass)              # windscreen
    for s in (-1, 1):
        box((s * 0.81, 0.3, 1.75), (0.04, 0.7, 0.5), glass)     # side windows
    box((0, -1.9, 0.85), (2.0, 3.2, 0.12), wood)                # tray floor
    for s in (-1, 1):
        box((s * 0.98, -1.9, 1.1), (0.06, 3.2, 0.4), wood)     # tray sides
    box((0, -3.47, 1.1), (2.0, 0.06, 0.4), wood)
    for (wy, wx) in ((1.7, 0.85), (1.7, -0.85), (-2.3, 0.9), (-2.3, -0.9)):
        cyl((wx, wy, 0.45), 0.45, 0.3, dark, rot=(0, R(90), 0), verts=24)
        cyl((wx + math.copysign(0.16, wx), wy, 0.45), 0.2, 0.04, chrome, rot=(0, R(90), 0), verts=16)
        box((wx, wy, 0.98), (0.36, 1.1, 0.06), olive, bevel=0.02)  # mudguard over each wheel
    new = [o for o in bpy.data.objects if o not in before]
    for o in bpy.data.objects:
        o.select_set(o in new)
    bpy.context.view_layer.objects.active = new[0]
    bpy.ops.object.join()
    t = bpy.context.object
    t.name = "truck"
    return t


def build_outback(sc, truck_at=(0, -7, 0), truck_rot=0.0, sandbag=True):
    dirt = noise_mat("dirt", (0.5, 0.16, 0.05), (0.68, 0.27, 0.09), 0.8, detail=8)
    road = noise_mat("road", (0.62, 0.3, 0.13), (0.78, 0.44, 0.22), 1.5, detail=8)
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 100, 0))
    bpy.context.object.data.materials.append(dirt)
    box((0, 60, 0.01), (5, 260, 0.02), road, bevel=0)
    fld = box((40, 40, 0.03), (72, 140, 0.06), field_mat(), bevel=0)
    fld.location.x = 3.6 + 36
    wheat_cards(3.7, 13, -14, 40, 42000, seed=3, gap=(9, 16, 7.5), clear=[(3.6, 6.3, -2.6, 3.4)])
    wheat_cards(13, 40, -14, 75, 30000, seed=4, wscale=3.0)
    fence(3.2, -20, 70)
    if sandbag:
        sandbags(5.5, -1.6, 1.6)
        box((4.9, 2.4, 0.25), (0.6, 0.5, 0.5), noise_mat("crate", (0.4, 0.3, 0.16), (0.55, 0.42, 0.25), 8))  # ammo
        box((4.9, 2.4, 0.75), (0.55, 0.45, 0.45), noise_mat("crate2", (0.38, 0.29, 0.15), (0.52, 0.4, 0.23), 8))
    farmhouse((-13, 20, 0))
    windmill((-7, 27, 0))
    for i, (x, y) in enumerate(((-6, -6), (-19, 8), (-10, 46), (-25, 30), (24, 75), (-4, 70), (40, 95), (-30, 60))):
        gum_tree((x, y, 0), h=6.5 + (i % 3), seed=i)
    hill = mat("hill", (0.55, 0.42, 0.36), 0.9)
    for i, x in enumerate(range(-160, 200, 45)):
        sphere((x, 230 + (i % 3) * 25, -8), 40 + (i % 4) * 12, hill, scale=(1.4, 1, 0.35))
    t = truck()
    t.location = truck_at
    t.rotation_euler = (0, 0, truck_rot)
    # warm sky gradient
    w = sc.world or bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1.0, 0.78, 0.5, 1)
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = (0.18, 0.45, 0.95, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs[2], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])


SETS = {
    "outback": lambda sc: build_outback(sc),
    "outback_road": lambda sc: build_outback(sc, truck_at=(0, -7, 0), sandbag=False),
}
