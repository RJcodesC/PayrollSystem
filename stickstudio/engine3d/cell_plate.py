"""Render a stylised 3D prison-cell background plate (Blender/bpy, Cycles CPU).
Usage: python3 cell_plate.py OUT.png [width height samples]"""
import math
import sys

import bpy

out = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 1080
H = int(sys.argv[3]) if len(sys.argv) > 3 else 1920
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 48

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, color, rough=0.7, brick=None, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if brick:
        b = nt.nodes.new("ShaderNodeTexBrick")
        b.inputs["Color1"].default_value = (*brick[0], 1)
        b.inputs["Color2"].default_value = (*brick[1], 1)
        b.inputs["Mortar"].default_value = (*brick[2], 1)
        b.inputs["Scale"].default_value = brick[3]
        b.inputs["Mortar Size"].default_value = 0.015
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["UV"], b.inputs["Vector"])
        nt.links.new(b.outputs["Color"], bsdf.inputs["Base Color"])
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emit[1]
    return m


def box(name, loc, size, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.materials.append(m)
    bpy.ops.object.transform_apply(scale=True)
    bev = o.modifiers.new("bev", "BEVEL")
    bev.width = 0.02
    bev.segments = 3
    return o


wall = mat("wall", (0.55, 0.62, 0.52), 0.9, brick=((0.50, 0.60, 0.50), (0.44, 0.54, 0.45), (0.36, 0.42, 0.37), 6.0))
floor = mat("floor", (0.28, 0.30, 0.33), 0.6)
steel = mat("steel", (0.25, 0.27, 0.30), 0.35)
blanket = mat("blanket", (0.30, 0.38, 0.52), 0.9)
sheet = mat("sheet", (0.93, 0.92, 0.88), 0.9)
porcelain = mat("porcelain", (0.92, 0.93, 0.95), 0.25)
vent = mat("vent", (0.30, 0.32, 0.35), 0.5)
night = mat("night", (0.05, 0.08, 0.18), 1.0, emit=((0.15, 0.22, 0.45), 1.5))

# room 3m wide, 4m deep, 3m high; camera looks in from the bars (y = -2)
box("floor", (0, 0, -0.05), (3.2, 4.4, 0.1), floor)
box("back", (0, 2.05, 1.5), (3.2, 0.1, 3.0), wall)
box("left", (-1.55, 0, 1.5), (0.1, 4.4, 3.0), wall)
box("right", (1.55, 0, 1.5), (0.1, 4.4, 3.0), wall)
box("ceil", (0, 0, 3.05), (3.2, 4.4, 0.1), wall)
# window with night sky + bars
box("win", (0, 1.99, 2.3), (0.6, 0.05, 0.5), night)
for x in (-0.18, 0, 0.18):
    box(f"wb{x}", (x, 1.96, 2.3), (0.03, 0.03, 0.52), steel)
# bunk on the right
box("bunk", (1.05, 0.9, 0.45), (0.9, 2.0, 0.08), steel)
box("mattress", (1.05, 0.9, 0.55), (0.85, 1.9, 0.14), sheet)
box("blanket", (1.05, 0.6, 0.63), (0.86, 1.2, 0.04), blanket)
for (x, y) in ((0.65, -0.05), (1.45, -0.05), (0.65, 1.85), (1.45, 1.85)):
    box(f"leg{x}{y}", (x, y, 0.22), (0.05, 0.05, 0.45), steel)
# sink + vent grille on the back-left wall (the escape vent)
box("sink", (-0.9, 1.8, 0.85), (0.5, 0.4, 0.2), porcelain)
box("pipe", (-0.9, 1.95, 0.45), (0.06, 0.06, 0.7), steel)
box("vent", (-0.9, 1.99, 0.3), (0.45, 0.04, 0.3), vent)
for i in range(6):
    box(f"vs{i}", (-1.08 + i * 0.07, 1.96, 0.3), (0.02, 0.03, 0.26), steel)
# foreground bars (frame the shot)
for x in (-1.4, -1.25, 1.25, 1.4):
    box(f"bar{x}", (x, -1.9, 1.5), (0.06, 0.06, 3.0), steel)

# lights: warm ceiling bulb + cool moonlight through the window
bpy.ops.object.light_add(type="POINT", location=(0, 0.8, 2.7))
L = bpy.context.object.data
L.energy = 70
L.color = (1.0, 0.85, 0.65)
L.shadow_soft_size = 0.15
bpy.ops.object.light_add(type="AREA", location=(0, 2.3, 2.3), rotation=(math.radians(-70), 0, 0))
A = bpy.context.object.data
A.energy = 140
A.color = (0.55, 0.65, 1.0)
A.size = 0.6
world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.06, 0.06, 0.08, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
sc.world = world

# camera: slightly low, looking into the cell, vertical frame
bpy.ops.object.camera_add(location=(0, -2.9, 1.25), rotation=(math.radians(88), 0, 0))
cam = bpy.context.object
cam.data.lens = 22
sc.camera = cam

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x = W
sc.render.resolution_y = H
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"
sc.view_settings.exposure = -0.3
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("wrote", out)
