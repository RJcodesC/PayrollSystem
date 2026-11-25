"""3AM Elevator stairwell: a concrete switchback stairwell, three floors tall, with steel doors,
floor-13 signs, red emergency lamps, flickering fluorescent tubes and an open well you can look up through.

Layout (metres). Floor k sits at z = 3k. Each floor:
  floor landing  y in [-1.6, 0]   (door in the wall at y = -1.6)
  flight 1       x in [0.3, 1.6], climbs +y from y=0 to y=3 (z 3k -> 3k+1.5)
  mid landing    y in [3, 4.6]   z = 3k+1.5
  flight 2       x in [-1.6, -0.3], climbs -y from y=3 back to y=0 (z 3k+1.5 -> 3k+3)
The well (x in [-0.3, 0.3]) is open all the way up.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sets import mat, box, cyl, light, R  # noqa: E402

FLOORS = 4
FH = 3.0
STEPS = 10


def block_mat(name, base=(0.42, 0.44, 0.45), mortar=(0.30, 0.31, 0.32), paint=None):
    """Painted concrete block in object space, so every wall gets the same block size."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    tc = nt.nodes.new("ShaderNodeTexCoord")
    b = nt.nodes.new("ShaderNodeTexBrick")
    b.inputs["Color1"].default_value = (*base, 1)
    b.inputs["Color2"].default_value = tuple(c * 0.92 for c in base) + (1,)
    b.inputs["Mortar"].default_value = (*mortar, 1)
    b.inputs["Scale"].default_value = 2.5
    b.inputs["Mortar Size"].default_value = 0.01
    b.offset = 0.5
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    # walls run along x or y: brick pattern on (x+y, z) so both orientations look right
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs[0], add.inputs[0])
    nt.links.new(sep.outputs[1], add.inputs[1])
    nt.links.new(add.outputs[0], comb.inputs[0])
    nt.links.new(sep.outputs[2], comb.inputs[1])
    nt.links.new(comb.outputs[0], b.inputs["Vector"])
    # grime: noise darkens the lower wall
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.35
    nt.links.new(b.outputs["Color"], mix.inputs[6])
    nt.links.new(nz.outputs["Fac"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    return m


def text_obj(body, loc, size, m, rot=(R(90), 0, 0), extrude=0.005, align="CENTER"):
    cu = bpy.data.curves.new("txt", type="FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    o = bpy.data.objects.new("txt", cu)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(m)
    return o


def build_stairs(sc, open_door=False, scrawl=False):
    wallm = block_mat("block")
    stripe = mat("stripe", (0.62, 0.08, 0.07), 0.6)        # red paint band, classic stairwell
    concrete = mat("concrete", (0.36, 0.36, 0.37), 0.9)
    nosing = mat("nosing", (0.85, 0.66, 0.12), 0.5)          # yellow step edges
    rail = mat("rail", (0.18, 0.2, 0.22), 0.35, metal=0.8)
    doorm = mat("door", (0.12, 0.26, 0.24), 0.45, metal=0.3)
    frame = mat("frame", (0.1, 0.1, 0.11), 0.4, metal=0.6)
    signm = mat("sign", (0.06, 0.06, 0.07), 0.5)
    sign_txt = mat("signtxt", (0.95, 0.95, 0.92), 0.4, emit=((1, 1, 0.95), 0.6))
    red_lamp = mat("redlamp", (1, 0.1, 0.06), 0.3, emit=((1, 0.06, 0.03), 18))
    tube = mat("tube", (0.9, 1, 0.95), 0.3, emit=((0.75, 1.0, 0.9), 6))
    warm = mat("warmgap", (1, 0.7, 0.4), 0.3, emit=((1, 0.72, 0.42), 25))
    scrawlm = mat("scrawl", (0.75, 0.03, 0.03), 0.9, emit=((0.9, 0.05, 0.03), 0.6))
    void = mat("void", (0.0, 0.0, 0.0), 1.0)

    top = FLOORS * FH
    # shell: four walls + floor
    box((0, 1.5, -0.1), (3.6, 6.6, 0.2), concrete, bevel=0)
    box((-1.75, 1.5, top / 2), (0.3, 6.6, top + 0.4), wallm, bevel=0)
    box((1.75, 1.5, top / 2), (0.3, 6.6, top + 0.4), wallm, bevel=0)
    box((0, 4.75, top / 2), (3.6, 0.3, top + 0.4), wallm, bevel=0)
    box((0, -1.75, top / 2), (3.6, 0.3, top + 0.4), wallm, bevel=0)
    run = 3.0 / STEPS
    rise = 1.5 / STEPS
    for k in range(FLOORS):
        z0 = k * FH
        # red stripe at waist height on every floor
        for (x, y, sx, sy) in ((-1.59, 1.5, 0.02, 6.4), (1.59, 1.5, 0.02, 6.4), (0, 4.59, 3.4, 0.02),
                               (0, -1.59, 3.4, 0.02)):
            box((x, y, z0 + 1.05), (sx, sy, 0.16), stripe, bevel=0)
        if k > 0:  # floor landing slab
            box((0, -0.8, z0 - 0.1), (3.4, 1.6, 0.2), concrete, bevel=0.01)
        box((0, 3.8, z0 + 1.4), (3.4, 1.6, 0.2), concrete, bevel=0.01)  # mid landing
        # flights
        for i in range(STEPS):
            # flight 1: x in [0.2,1.6], climbing +y
            y = i * run + run / 2
            z = z0 + (i + 1) * rise
            box((0.95, y, z - rise / 2), (1.3, run, rise), concrete, bevel=0.005)
            box((0.95, y - run / 2 + 0.03, z + 0.002), (1.3, 0.05, 0.01), nosing, bevel=0)
            # flight 2: x in [-1.6,-0.2], climbing -y
            y2 = 3.0 - i * run - run / 2
            z2 = z0 + 1.5 + (i + 1) * rise
            box((-0.95, y2, z2 - rise / 2), (1.3, run, rise), concrete, bevel=0.005)
            box((-0.95, y2 + run / 2 - 0.03, z2 + 0.002), (1.3, 0.05, 0.01), nosing, bevel=0)
        # sloped soffits under the flights
        ang = math.atan2(1.5, 3.0)
        box((0.95, 1.5, z0 + 0.62), (1.3, 3.36, 0.12), concrete, rot=(ang, 0, 0), bevel=0)
        box((-0.95, 1.5, z0 + 2.12), (1.3, 3.36, 0.12), concrete, rot=(-ang, 0, 0), bevel=0)
        # railings along the well (x = +-0.22), rising with the flights
        L = math.hypot(3.0, 1.5)
        for sx, zb, a in ((0.32, z0, ang), (-0.32, z0 + 1.5, -ang)):
            cyl((sx, 1.5, zb + 0.75 + 0.95), 0.03, L, rail, rot=(R(90) - a, 0, 0), verts=12)
            cyl((sx, 1.5, zb + 0.75 + 0.5), 0.015, L, rail, rot=(R(90) - a, 0, 0), verts=8)
            for j in range(6):
                yy = 0.25 + j * 0.5
                zz = zb + (yy if sx > 0 else 3.0 - yy) * 0.5
                cyl((sx, yy, zz + 0.47), 0.018, 0.95, rail, verts=8)
        cyl((0, 3.05, z0 + 1.5 + 0.95), 0.03, 0.64, rail, rot=(0, R(90), 0), verts=12)
        # door on the floor landing (wall y = -1.6), sign + lamp beside it
        dz = z0
        box((0, -1.6, dz + 1.08), (1.1, 0.08, 2.2), frame, bevel=0.01)
        if open_door and k == 0:
            # door swung open into the room: dark gap with warm spill, leaf rotated 100 deg
            box((0, -1.62, dz + 1.05), (0.95, 0.06, 2.1), void, bevel=0)
            dl = box((0, 0, 0), (0.95, 0.05, 2.08), doorm, bevel=0.01)
            dl.location = (-0.475 - 0.03 + 0.03, -1.55 + 0.475, dz + 1.05)
            dl.rotation_euler = (0, 0, R(-90))
            light("POINT", (0, -1.5, dz + 1.0), 60, (1, 0.72, 0.45), size=0.2)
        else:
            box((0, -1.55, dz + 1.05), (0.95, 0.05, 2.08), doorm, bevel=0.01)
            cyl((0.36, -1.5, dz + 1.0), 0.025, 0.18, frame, rot=(0, R(90), 0), verts=10)  # handle
            box((0, -1.535, dz + 1.6), (0.3, 0.01, 0.4), mat(f"win{k}", (0.05, 0.08, 0.08), 0.1), bevel=0)
            if k == 1:  # the door he is climbing to: light under it
                box((0, -1.54, dz + 0.012), (0.9, 0.03, 0.02), warm, bevel=0)
                light("AREA", (0, -1.4, dz + 0.05), 25, (1, 0.7, 0.4), rot=(0, 0, 0), size=0.8)
        box((0.95, -1.585, dz + 1.75), (0.5, 0.02, 0.42), signm, bevel=0.005)
        text_obj("13", (0.95, -1.57, dz + 1.73), 0.32, sign_txt, rot=(R(90), 0, R(180)))
        box((-0.85, -1.57, dz + 2.45), (0.22, 0.08, 0.1), red_lamp, bevel=0.01)       # emergency lamp
        box((1.2, 1.5, dz + 2.85), (0.06, 1.2, 0.05), tube, bevel=0)                    # fluorescent tube
    if scrawl:
        # scrawled on the right wall above the bottom landing (clear of the open door leaf)
        text_obj("STOP CLIMBING", (1.58, -0.8, 1.95), 0.17, scrawlm, rot=(R(90), R(-4), R(-90)), extrude=0.002)
        text_obj("IT'S NOT BEHIND YOU", (1.58, -0.8, 1.7), 0.11, scrawlm, rot=(R(90), R(3), R(-90)),
                 extrude=0.002)
    # ceiling
    box((0, 1.5, top + 0.1), (3.6, 6.6, 0.2), concrete, bevel=0)
    w = sc.world or bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.012, 0.015, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3


def _lamps(color, energy, tubes=True, tube_energy=40):
    for k in range(FLOORS):
        z0 = k * FH
        light("POINT", (-0.85, -1.35, z0 + 2.35), energy, color, size=0.15)
        if tubes:
            light("AREA", (1.15, 1.5, z0 + 2.8), tube_energy, (0.75, 1.0, 0.88), rot=(0, R(-30), 0), size=1.2)


def light_emergency():
    _lamps((1, 0.08, 0.05), 140, tubes=True, tube_energy=12)
    return 0.0, (0, 0, 0)


def light_cold():
    _lamps((1, 0.1, 0.06), 30, tubes=True, tube_energy=70)
    light("POINT", (0.6, 1.5, FLOORS * FH - 0.4), 120, (1, 0.12, 0.06), size=0.2)  # red glow at the very top
    return 0.0, (0, 0, 0)


def light_door():
    _lamps((1, 0.1, 0.06), 70, tubes=True, tube_energy=25)
    return 0.0, (0, 0, 0)


LIGHTS = {"emergency": light_emergency, "cold": light_cold, "doorlight": light_door}

SETS = {
    "stairs": lambda sc: build_stairs(sc),
    "stairs_open": lambda sc: build_stairs(sc, open_door=True, scrawl=True),
}
