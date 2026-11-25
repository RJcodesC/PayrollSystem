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
