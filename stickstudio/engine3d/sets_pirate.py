"""3D sets for 'Why Pirates Wore Eye Patches' (original stylised models)."""
import math
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sets import reset, mat, box, cyl, sphere, light, world, camera, render, R  # noqa: E402
from sets_air import look_cam, clouds  # noqa: E402

WOOD = (0.45, 0.27, 0.13)
WOOD_D = (0.30, 0.17, 0.08)


def planks(name, size, loc, base=WOOD, n=14, axis="y"):
    """A plank surface: many thin boxes with slightly varied colours."""
    rng = random.Random(hash(name) % 1000)
    w = size[0] / n if axis == "y" else size[1] / n
    for i in range(n):
        c = tuple(min(1, max(0, v * rng.uniform(0.85, 1.12))) for v in base)
        m = mat(f"{name}{i}", c, 0.7)
        if axis == "y":
            box((loc[0] - size[0] / 2 + w * (i + 0.5), loc[1], loc[2]), (w * 0.96, size[1], size[2]), m, bevel=0.01)
        else:
            box((loc[0], loc[1] - size[1] / 2 + w * (i + 0.5), loc[2]), (size[0], w * 0.96, size[2]), m, bevel=0.01)


def ocean(z=0.0, color=(0.0, 0.32, 0.55)):
    water = mat("ocean", color, 0.12)
    bpy.ops.mesh.primitive_plane_add(size=1200, location=(0, 0, z))
    bpy.context.object.data.materials.append(water)


def sky(top=(0.02, 0.2, 0.75), bottom=(0.45, 0.72, 1.0)):
    world(bottom, 1.0, top=top)


def barrel(loc, s=1.0):
    cyl(loc, 0.42 * s, 1.0 * s, mat("barrel%d" % int(loc[0] * 10 + loc[1]), WOOD, 0.7), verts=20)
    for dz in (-0.3, 0.3):
        cyl((loc[0], loc[1], loc[2] + dz * s), 0.44 * s, 0.07 * s, mat("hoop", (0.15, 0.15, 0.16), 0.4, metal=0.7),
            verts=20)


def cannon(loc, rot=0.0):
    iron = mat("iron", (0.08, 0.08, 0.09), 0.4, metal=0.8)
    c = cyl((loc[0], loc[1], loc[2] + 0.45), 0.22, 1.8, iron, rot=(R(90), 0, rot), verts=20)
    box((loc[0], loc[1], loc[2] + 0.2), (0.8, 1.0, 0.4), mat("carriage", WOOD_D, 0.8))
    return c


def sail(loc, w, h, color=(0.95, 0.92, 0.82)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(R(90), 0, 0))
    o = bpy.context.object
    o.scale = (w, h, 1)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat("sail%d" % int(loc[2] * 10), color, 0.9))
    bend = o.modifiers.new("bend", "SIMPLE_DEFORM")
    bend.deform_method = "BEND"
    bend.angle = R(25)
    bend.deform_axis = "Z"
    sol = o.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.03
    return o


def build_deck(sc):
    planks("deck", (7, 30, 0.2), (0, 6, -0.1))
    for side in (-1, 1):  # bulwarks/railings
        box((side * 3.6, 6, 0.6), (0.25, 30, 1.2), mat("bulwark", WOOD_D, 0.8))
        box((side * 3.6, 6, 1.25), (0.35, 30, 0.12), mat("rail", (0.55, 0.33, 0.15), 0.6))
    mastm = mat("mast", (0.5, 0.3, 0.14), 0.6)
    for y in (6, 16):
        cyl((0, y, 9), 0.3, 18, mastm, verts=16)
        cyl((0, y, 12), 0.12, 7, mastm, rot=(0, R(90), 0), verts=12)
        sail((0, y + 0.3, 9.5), 6.5, 5)
    rope = mat("rope", (0.75, 0.62, 0.4), 0.9)
    for (x, y) in ((-3.5, 2), (3.5, 2), (-3.5, 10), (3.5, 10)):
        cyl((x * 0.55, y + 2, 7), 0.03, 14, rope, rot=(R(18) * (1 if y < 5 else -1), R(x * 2), 0), verts=6)
    cannon((-2.6, 3, 0))
    cannon((2.6, 9, 0), rot=R(180))
    barrel((2.4, 1.5, 0.5))
    barrel((2.9, 2.4, 0.5), 0.9)
    box((-2.4, 12, 0.5), (1.2, 1.2, 1.0), mat("crate", (0.62, 0.43, 0.2), 0.8))
    # black flag at the top of the main mast
    flag = mat("flag", (0.04, 0.04, 0.05), 0.9)
    box((0.9, 16, 18.2), (1.8, 0.05, 1.1), flag, bevel=0)
    ocean(-1.0)
    ship_model((16, 70, -1.2), dark=True)
    sky()
    rng = random.Random(5)
    clouds(10, ((-120, 120), (60, 220)), 30, rng, size=(6, 14))
    sphere((-60, 200, 50), 8, mat("sun", (1, 0.95, 0.7), 1, emit=((1, 0.92, 0.6), 25)))
    light("SUN", (0, 0, 40), 5.5, (1, 0.92, 0.78), rot=(R(45), R(25), R(-30)))
    look_cam((0.5, -3.5, 2.0), (0, 8, 3.2), lens=20)


def ship_model(loc, rot=0.0, dark=False):
    hull = mat("hull%d" % int(loc[0]), (0.25, 0.13, 0.06) if dark else (0.42, 0.24, 0.1), 0.7)
    trim = mat("trim%d" % int(loc[0]), (0.75, 0.55, 0.15), 0.5)
    before = set(bpy.data.objects)
    box((0, 0, 1.0), (5, 18, 3), hull, bevel=0.3)
    box((0, -8, 2.6), (5, 4, 2.0), hull, bevel=0.2)  # stern castle
    box((0, 10, 1.4), (2.2, 4, 1.6), hull, bevel=0.3, rot=(R(10), 0, 0))  # bow
    box((-2.52, 0, 1.8), (0.05, 18, 0.25), trim, bevel=0)
    for k in range(6):
        box((-2.55, -6 + k * 2.4, 1.0), (0.06, 0.5, 0.5), mat("port", (0.05, 0.05, 0.05), 0.5), bevel=0)
    mastm = mat("mast2", (0.4, 0.24, 0.1), 0.6)
    for y, h in ((-3, 14), (3, 16)):
        cyl((0, y, 2.5 + h / 2), 0.25, h, mastm, verts=12)
        sail((0, y + 0.2, 2.5 + h * 0.6), 5.5, 4.5, (0.15, 0.13, 0.12) if dark else (0.95, 0.92, 0.82))
    box((0.8, 3, 2.5 + 16 + 0.6), (1.6, 0.05, 1.0), mat("flag2", (0.04, 0.04, 0.05), 0.9), bevel=0)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.location.x += loc[0]
        o.location.y += loc[1]
        o.location.z += loc[2]
    return new


def build_sea(sc):
    ship_model((0, 0, -0.2))
    ship_model((24, 45, -0.2), dark=True)
    ocean(0.0)
    sky()
    rng = random.Random(2)
    clouds(14, ((-150, 150), (80, 260)), 25, rng, size=(6, 14))
    sphere((-70, 220, 40), 9, mat("sun2", (1, 0.95, 0.7), 1, emit=((1, 0.92, 0.6), 25)))
    light("SUN", (0, 0, 40), 5.0, (1, 0.9, 0.75), rot=(R(50), R(20), R(-40)))
    look_cam((-16, -14, 3.0), (4, 10, 7), lens=24)


def build_hold(sc):
    """Below deck: low wooden ceiling, beams, barrels, hammocks, one dim lantern."""
    planks("hfloor", (8, 22, 0.2), (0, 8, -0.1), base=WOOD_D)
    planks("hceil", (8, 22, 0.2), (0, 8, 2.6), base=WOOD_D)
    for side in (-1, 1):
        planks("hwall%d" % side, (0.2, 22, 2.8), (side * 4, 8, 1.3), base=WOOD_D, n=10, axis="x")
    for k in range(8):
        box((0, k * 2.6, 2.4), (8, 0.3, 0.3), mat("beam%d" % k, (0.22, 0.12, 0.05), 0.8))
    for (x, y) in ((-3, 3), (-3.2, 4.1), (3, 6), (3.1, 7.2), (-3, 11), (2.8, 13)):
        barrel((x, y, 0.5))
    for k in range(3):
        box((-2.5 + k * 0.1, 9 + k * 1.2, 0.5), (1.0, 1.0, 1.0), mat("hcrate%d" % k, (0.55, 0.38, 0.18), 0.8))
    lant = mat("lantern", (1, 0.75, 0.35), 1, emit=((1, 0.7, 0.3), 30))
    sphere((0.8, 6, 2.0), 0.12, lant)
    light("POINT", (0.8, 6, 1.95), 160, (1, 0.65, 0.3), size=0.1)
    light("POINT", (0, 1, 1.6), 30, (0.55, 0.6, 0.9), size=0.6)
    world((0.02, 0.02, 0.03), 0.3)
    look_cam((0, -1.5, 1.3), (0, 10, 1.2), lens=18)


def build_course(sc):
    """A dark warehouse with a simple obstacle course (boxes, cones, tyres, hanging ropes)."""
    floor = mat("cfloor", (0.25, 0.25, 0.27), 0.5)
    wall = mat("cwall", (0.2, 0.22, 0.26), 0.8)
    box((0, 10, -0.05), (16, 30, 0.1), floor, bevel=0)
    box((-8, 10, 4), (0.3, 30, 8), wall, bevel=0)
    box((8, 10, 4), (0.3, 30, 8), wall, bevel=0)
    box((0, 25, 4), (16, 0.3, 8), wall, bevel=0)
    rng = random.Random(4)
    cone = mat("cone", (1.0, 0.4, 0.05), 0.5)
    for i in range(10):
        x, y = rng.uniform(-5, 5), rng.uniform(2, 20)
        bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.8, location=(x, y, 0.4))
        bpy.context.object.data.materials.append(cone)
    for i in range(8):
        box((rng.uniform(-6, 6), rng.uniform(3, 22), 0.5), (1, 1, 1),
            mat("cbox%d" % i, (0.6, 0.45, 0.25), 0.8))
    tyre = mat("tyre", (0.05, 0.05, 0.05), 0.8)
    for i in range(5):
        bpy.ops.mesh.primitive_torus_add(location=(rng.uniform(-4, 4), rng.uniform(5, 18), 0.15),
                                         major_radius=0.45, minor_radius=0.15)
        bpy.context.object.data.materials.append(tyre)
    light("SPOT", (0, 6, 7.5), 1800, (0.7, 0.8, 1.0), rot=(0, 0, 0), size=0.4)
    light("POINT", (0, 0, 3), 400, (0.6, 0.65, 0.9), size=1)
    light("AREA", (0, 12, 7.8), 2500, (0.75, 0.8, 1.0), size=10)
    world((0.05, 0.06, 0.08), 0.5)
    look_cam((0, -3, 3.0), (0, 10, 0.6), lens=20)


SETS = {"deck": build_deck, "sea": build_sea, "hold": build_hold, "course": build_course}
EXPOSURE = {"deck": -0.5, "sea": -0.5, "hold": 0.6, "course": 0.3}

# ====================================================================== v2: detailed, saturated sets
def wood_mat(name, base=(0.55, 0.30, 0.12), dark=(0.32, 0.16, 0.06), scale=6.0, rough=0.6):
    """Procedural wood grain: wave bands + noise between a light and a dark brown."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 1.2
    wave.inputs["Detail"].default_value = 1.0
    wave.bands_direction = "Y"
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].color = (*base, 1)
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def sail_mat(name, base=(0.98, 0.93, 0.80)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.9
    ramp.color_ramp.elements[0].color = (*base, 1)
    ramp.color_ramp.elements[1].color = (base[0] * 0.8, base[1] * 0.75, base[2] * 0.6, 1)  # seams
    nt.links.new(tc.outputs["Generated"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def wavy_ocean(z=0.0, color=(0.0, 0.42, 0.72)):
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 120, z))
    o = bpy.context.object
    sub = o.modifiers.new("sub", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 6
    tex = bpy.data.textures.new("waves", "CLOUDS")
    tex.noise_scale = 3.0
    d = o.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = 0.6
    water = mat("ocean2", color, 0.05)
    o.data.materials.append(water)
    bpy.ops.object.shade_smooth()
    return o


def helm(loc):
    wm = wood_mat("helmwood", (0.62, 0.36, 0.14), (0.38, 0.2, 0.07), 10)
    box((loc[0], loc[1], loc[2] + 0.5), (0.18, 0.18, 1.0), wm)
    bpy.ops.mesh.primitive_torus_add(location=(loc[0], loc[1] - 0.15, loc[2] + 1.15), rotation=(R(90), 0, 0),
                                     major_radius=0.42, minor_radius=0.04)
    bpy.context.object.data.materials.append(wm)
    for k in range(8):
        a = k * math.pi / 4
        cyl((loc[0], loc[1] - 0.15, loc[2] + 1.15), 0.025, 1.1, wm, rot=(R(90), a, 0), verts=8)


def cannon2(loc, rot=0.0):
    iron = mat("iron2", (0.06, 0.06, 0.07), 0.35, metal=0.85)
    carr = wood_mat("carriage2", (0.55, 0.28, 0.1), (0.3, 0.14, 0.05), 8)
    x, y, z = loc
    c = math.cos(rot)
    s_ = math.sin(rot)
    box((x, y, z + 0.32), (0.75, 1.1, 0.35), carr, rot=(0, 0, rot))
    cyl((x - s_ * 0.2, y + c * 0.2, z + 0.62), 0.2, 1.7, iron, rot=(R(84), 0, rot), verts=24)
    sphere((x + s_ * 0.6, y - c * 0.6, z + 0.6), 0.2, iron)
    for dx in (-0.42, 0.42):
        for dy in (-0.4, 0.4):
            wx, wy = x + dx * c - dy * s_ * 0, y + dy * c + dx * s_
            cyl((x + dx * c - dy * s_, y + dx * s_ + dy * c, z + 0.16), 0.16, 0.1, carr, rot=(0, R(90), rot), verts=16)


def build_deck_v2(sc):
    deckwood = wood_mat("deckwood", (0.78, 0.45, 0.17), (0.55, 0.29, 0.1), 16.0)
    railwood = wood_mat("railwood", (0.5, 0.26, 0.1), (0.28, 0.13, 0.05), 8.0)
    hullwood = wood_mat("hullwood", (0.45, 0.22, 0.08), (0.22, 0.1, 0.04), 5.0)
    # deck planks (individual boards with gaps)
    for i in range(16):
        box((-3.4 + i * 0.45 + 0.22, 6, -0.1), (0.42, 30, 0.2), deckwood, bevel=0.015)
    # hull sides + bulwark + rail + balusters
    for side in (-1, 1):
        box((side * 3.75, 6, -0.6), (0.3, 30, 2.4), hullwood)
        box((side * 3.65, 6, 0.55), (0.2, 30, 1.1), railwood)
        box((side * 3.65, 6, 1.18), (0.42, 30.2, 0.14), railwood)
        for k in range(30):
            cyl((side * 3.45, -8.5 + k * 1.0, 0.7), 0.05, 0.9, railwood, verts=8)
        box((side * 3.9, 6, -0.25), (0.08, 30, 0.22), mat("trimgold", (0.95, 0.68, 0.12), 0.4, metal=0.6), bevel=0)
    # raised stern with helm
    box((0, -6.5, 0.45), (7.2, 5, 0.9), deckwood)
    helm((0, -5.0, 0.9))
    # hatch grating
    for i in range(6):
        box((-0.7 + i * 0.28, 9.5, 0.06), (0.06, 1.8, 0.1), railwood, bevel=0)
        box((0, 8.7 + i * 0.32, 0.06), (1.8, 0.06, 0.1), railwood, bevel=0)
    # masts, yards, crow's nest, sails with seams
    mastm = wood_mat("mastwood", (0.6, 0.34, 0.14), (0.36, 0.19, 0.07), 14)
    sailm = sail_mat("sails")
    for y, top in ((6, 18), (16, 16)):
        cyl((0, y, top / 2), 0.32, top, mastm, verts=20)
        for z, wdt in ((top * 0.48, 7.5), (top * 0.78, 5.5)):
            cyl((0, y, z), 0.12, wdt, mastm, rot=(0, R(90), 0), verts=10)
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y + 0.35, z - wdt * 0.28), rotation=(R(90), 0, 0))
            o = bpy.context.object
            o.scale = (wdt * 0.92, wdt * 0.55, 1)
            bpy.ops.object.transform_apply(scale=True)
            o.data.materials.append(sailm)
            bend = o.modifiers.new("bend", "SIMPLE_DEFORM")
            bend.deform_method = "BEND"
            bend.angle = R(28)
            bend.deform_axis = "Z"
            o.modifiers.new("sol", "SOLIDIFY").thickness = 0.03
    cyl((0, 6, 15.5), 0.9, 0.15, mastm, verts=24)  # crow's nest
    bpy.ops.mesh.primitive_torus_add(location=(0, 6, 16.0), major_radius=0.9, minor_radius=0.06)
    bpy.context.object.data.materials.append(mastm)
    # rigging: shrouds + ratline rungs (rope ladders)
    rope = mat("rope2", (0.62, 0.42, 0.18), 0.9)
    for side in (-1, 1):
        for k in range(4):
            yb = 4.6 + k * 0.9
            p0, p1 = Vector3(side * 3.55, yb, 1.2), Vector3(side * 0.3, 6, 15.4)
            rope_between(p0, p1, rope)
        for j in range(1, 12):
            f = j / 12
            a = Vector3(side * (3.55 + (0.3 - 3.55) * f), 4.6 + (6 - 4.6) * f, 1.2 + 14.2 * f)
            b = Vector3(side * (3.55 + (0.3 - 3.55) * f), 7.3 + (6 - 7.3) * f, 1.2 + 14.2 * f)
            rope_between(a, b, rope, r=0.018)
    # flag with skull and crossbones
    flag = mat("flag2", (0.03, 0.03, 0.04), 0.9)
    bone = mat("bone", (0.96, 0.95, 0.9), 0.6)
    box((1.0, 6, 19.0), (2.0, 0.04, 1.3), flag, bevel=0)
    sphere((1.0, 5.97, 19.15), 0.22, bone, scale=(1, 0.2, 1))
    for a in (35, -35):
        box((1.0, 5.96, 18.75), (0.9, 0.03, 0.1), bone, rot=(0, R(a), 0), bevel=0)
    # props: cannons, barrels, crates, coiled rope, lantern
    cannon2((-2.6, 3, 0), rot=R(90))
    cannon2((2.6, 9, 0), rot=R(-90))
    cannon2((-2.6, 12, 0), rot=R(90))
    for (x, y, s_) in ((2.5, 1.5, 1.0), (2.95, 2.4, 0.9), (2.4, 2.6, 0.85)):
        barrel((x, y, 0.5 * s_), s_)
    crate = wood_mat("crate2", (0.78, 0.55, 0.25), (0.5, 0.32, 0.12), 12)
    box((-2.5, 13.5, 0.5), (1.1, 1.1, 1.0), crate)
    box((-2.3, 13.4, 1.45), (0.8, 0.8, 0.8), crate)
    bpy.ops.mesh.primitive_torus_add(location=(-1.6, 1.0, 0.12), major_radius=0.35, minor_radius=0.09)
    bpy.context.object.data.materials.append(rope)
    lant = mat("lantern2", (1, 0.75, 0.35), 1, emit=((1, 0.7, 0.3), 25))
    sphere((-0.5, 5.6, 2.2), 0.13, lant)
    # world: saturated sea and sky, a sun, puffy clouds, the enemy ship
    wavy_ocean(-1.2)
    ship_model_v2((16, 70, -1.4), dark=True)
    world((0.38, 0.66, 1.0), 1.0, top=(0.0, 0.22, 0.85))
    rng = random.Random(5)
    clouds(12, ((-120, 120), (60, 220)), 30, rng, size=(6, 14))
    sphere((-60, 200, 50), 8, mat("sun3", (1, 0.95, 0.7), 1, emit=((1, 0.92, 0.6), 25)))
    light("SUN", (0, 0, 40), 5.5, (1, 0.9, 0.72), rot=(R(45), R(25), R(-30)))
    look_cam((0.5, -3.5, 2.0), (0, 8, 3.2), lens=20)


class Vector3(tuple):
    def __new__(cls, x, y, z):
        return super().__new__(cls, (x, y, z))


def rope_between(p0, p1, m, r=0.025):
    import mathutils
    a, b = mathutils.Vector(p0), mathutils.Vector(p1)
    mid = (a + b) / 2
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, location=mid, vertices=6)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(m)
    return o


def ship_model_v2(loc, dark=False):
    """Rounded hull (subdivided box), gun ports, stern windows, masts and sails."""
    hull = wood_mat("hull2_%d" % int(loc[0]), (0.38, 0.17, 0.06) if dark else (0.5, 0.25, 0.1),
                    (0.18, 0.08, 0.03), 5)
    before = set(bpy.data.objects)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1.0))
    h = bpy.context.object
    h.scale = (2.6, 10, 1.6)
    bpy.ops.object.transform_apply(scale=True)
    h.modifiers.new("sub", "SUBSURF").levels = 2
    h.data.materials.append(hull)
    bpy.ops.object.shade_smooth()
    box((0, -8, 3.0), (4.4, 3.5, 1.8), hull, bevel=0.3)
    trim = mat("trim2_%d" % int(loc[0]), (0.95, 0.68, 0.12), 0.4, metal=0.5)
    box((-2.55, 0, 2.2), (0.06, 18, 0.2), trim, bevel=0)
    portm = mat("port2", (0.02, 0.02, 0.02), 0.5)
    for k in range(7):
        box((-2.6, -6 + k * 2.1, 1.4), (0.08, 0.5, 0.45), portm, bevel=0)
    win = mat("sternwin", (1, 0.8, 0.4), 1, emit=((1, 0.7, 0.3), 3))
    for k in range(3):
        box((-1.0 + k, -9.76, 3.1), (0.6, 0.05, 0.5), win, bevel=0)
    mastm = mat("mast3_%d" % int(loc[0]), (0.4, 0.24, 0.1), 0.6)
    sm = sail_mat("sail3_%d" % int(loc[0]), (0.25, 0.22, 0.2) if dark else (0.98, 0.93, 0.8))
    for y, hgt in ((-3, 14), (3.5, 17)):
        cyl((0, y, 2.5 + hgt / 2), 0.25, hgt, mastm, verts=12)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, y + 0.2, 2.5 + hgt * 0.6), rotation=(R(90), 0, 0))
        o = bpy.context.object
        o.scale = (5.5, 5, 1)
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(sm)
        bd = o.modifiers.new("bend", "SIMPLE_DEFORM")
        bd.deform_method = "BEND"
        bd.angle = R(25)
        bd.deform_axis = "Z"
    box((0.8, 3.5, 2.5 + 17 + 0.6), (1.6, 0.05, 1.0), mat("flag3", (0.03, 0.03, 0.04), 0.9), bevel=0)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.location.x += loc[0]
        o.location.y += loc[1]
        o.location.z += loc[2]
    return new


def build_hold_v2(sc):
    build_hold(sc)
    # warmer, more saturated wood + hammocks + hanging rope + cannon in the hold
    sw = mat("hammock", (0.85, 0.75, 0.5), 0.9)
    for k in range(2):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.8, location=(2.6, 9 + k * 2.2, 1.6),
                                            rotation=(R(90), 0, 0))
        o = bpy.context.object
        o.scale = (1, 1, 0.35)
        o.data.materials.append(sw)
    cannon2((-3.0, 7.5, 0), rot=R(90))


def build_course_v2(sc):
    """Test course with a CLEAR WALKING LANE down the middle (x in [-0.9, 1.6]); obstacles sit beside it,
    plus one crate placed right at the 'bump' spot just past the tester."""
    floor = mat("cfloor2", (0.32, 0.33, 0.36), 0.45)
    wall = mat("cwall2", (0.18, 0.28, 0.42), 0.8)
    box((0, 10, -0.05), (16, 30, 0.1), floor, bevel=0)
    box((-8, 10, 4), (0.3, 30, 8), wall, bevel=0)
    box((8, 10, 4), (0.3, 30, 8), wall, bevel=0)
    box((0, 25, 4), (16, 0.3, 8), wall, bevel=0)
    tape = mat("tape", (1.0, 0.82, 0.05), 0.5)
    for x in (-1.1, 1.8):  # yellow lane tape
        box((x, 11, 0.01), (0.08, 22, 0.02), tape, bevel=0)
    rng = random.Random(4)
    cone = mat("cone2", (1.0, 0.35, 0.02), 0.5)
    for i in range(14):
        side = -1 if i % 2 else 1
        x = (rng.uniform(-6, -1.8) if side < 0 else rng.uniform(2.6, 6.5))
        y = rng.uniform(1, 22)
        bpy.ops.mesh.primitive_cone_add(radius1=0.3, depth=0.8, location=(x, y, 0.4))
        bpy.context.object.data.materials.append(cone)
    cols = [(0.85, 0.15, 0.1), (0.1, 0.45, 0.85), (0.95, 0.75, 0.1), (0.2, 0.65, 0.3)]
    for i in range(10):
        side = -1 if i % 2 else 1
        x = (rng.uniform(-6, -2.0) if side < 0 else rng.uniform(2.8, 6.5))
        box((x, rng.uniform(2, 22), 0.5), (1, 1, 1), mat("cbox2_%d" % i, cols[i % 4], 0.6))
    box((-0.25, 6.0, 0.45), (0.9, 0.9, 0.9), mat("bumpbox", (0.85, 0.15, 0.1), 0.6))  # the one he walks into
    tyre = mat("tyre2", (0.05, 0.05, 0.05), 0.8)
    for i in range(5):
        bpy.ops.mesh.primitive_torus_add(location=(rng.uniform(2.6, 5), rng.uniform(4, 18), 0.15),
                                         major_radius=0.45, minor_radius=0.15)
        bpy.context.object.data.materials.append(tyre)
    world((0.05, 0.06, 0.1), 0.5)
    look_cam((0, -3, 3.0), (0, 10, 0.6), lens=20)


SETS.update({"deck2": build_deck_v2, "hold2": build_hold_v2, "course2": build_course_v2})
EXPOSURE.update({"deck2": -0.4, "hold2": 0.6, "course2": 0.3})


if __name__ == "__main__":
    args = sys.argv[1:]
    samples, scale = 28, 1.2
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
