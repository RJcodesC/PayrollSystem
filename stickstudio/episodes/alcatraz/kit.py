"""Shared kit for The Alcatraz Escape series: cast, 3D plates, props, overlays."""
import math
import os
import sys

import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from engine import bg  # noqa: E402
from engine.core import tween, pulse, EASES, clamp, hexc  # noqa: E402
from engine.render import label  # noqa: E402
from engine.rig import Character, Look, INK  # noqa: E402
from engine.text import text_center  # noqa: E402

PLATES = os.path.join(ROOT, "assets", "plates", "alcatraz")
_plates = {}

UNIFORM = dict(coat="#8fb3d9", coat_dark="#6b8fb8")
FRANK = Character("frank", Look(**UNIFORM, hair="side"), seed=0.4)
JOHN = Character("john", Look(**UNIFORM, hair="tuft"), seed=1.9)
CLAR = Character("clarence", Look(**UNIFORM, hair="curl"), seed=3.3)
WEST = Character("west", Look(**UNIFORM, mustache="thick", glasses=True), seed=4.4)
GUARD = Character("guard", Look(coat="#2b3a55", coat_dark="#1d283d", hat="kepi", hat_color="#2b3a55",
                                hat_band="#d9b44a", badge=True, mustache="thick"), seed=5.1)


# ------------------------------------------------------------------ helpers
def plate(ctx, name):
    if name not in _plates:
        _plates[name] = cairo.ImageSurface.create_from_png(os.path.join(PLATES, name + ".png"))
    s = _plates[name]
    # plates are 1.2x the frame: centre them so the frame sits in the middle
    ctx.set_source_surface(s, -(s.get_width() - 1080) / 2, -(s.get_height() - 1920) / 2)
    ctx.paint()


def shadow(ctx, x, y, w):
    ctx.save()
    ctx.translate(x, y + 4)
    ctx.scale(w, w * 0.16)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0, 0, 0, 0.32)
    ctx.fill()


def char(f, ch, **p):
    s = p.get("s", 1.4)
    shadow(f.ctx, p["x"], p["y"], 95 * s)
    return f.char(ch, p)


def world_pt(p, local):
    """Rig returns character-local points: convert to world (x, y, s, jump)."""
    return (p["x"] + local[0] * p.get("s", 1.4), p["y"] - p.get("jump", 0) + local[1] * p.get("s", 1.4))


def spoon(ctx, x, y, ang=35, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(ang))
    ctx.scale(s, s)
    bg.rect(ctx, -5, -58, 10, 58, "#c9ced6", 3)
    ctx.save()
    ctx.translate(0, -70)
    ctx.scale(14, 19)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(*hexc("#e3e7ee"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()


def big_arm(ctx, hx, hy, from_x, from_y, holding=True, ang=-30, sleeve="#8fb3d9"):
    """Huge close-up arm reaching in from off-screen, holding a spoon."""
    ctx.set_line_cap(1)
    for col, w in ((INK, 46), (hexc("#f6efe6"), 0)):
        if w:
            ctx.set_source_rgb(*col)
            ctx.set_line_width(w)
            ctx.move_to(from_x, from_y)
            ctx.line_to(hx, hy)
            ctx.stroke()
    # sleeve
    ctx.set_source_rgb(*hexc(sleeve))
    ctx.set_line_width(110)
    ctx.move_to(from_x, from_y)
    ctx.line_to(from_x + (hx - from_x) * 0.25, from_y + (hy - from_y) * 0.25)
    ctx.stroke()
    if holding:
        spoon(ctx, hx - 10, hy + 10, ang, 2.4)
    ctx.arc(hx, hy, 44, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc("#f6efe6"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(9)
    ctx.stroke()


def dust_bits(ctx, x, y, t, t0, n=10):
    if t < t0:
        return
    for i in range(n):
        tt = (t - t0 - i * 0.07) % 0.9
        px = x + math.sin(i * 2.1) * 70 + tt * math.cos(i) * 40
        py = y + 350 * tt * tt + i * 3
        ctx.arc(px, py, 6 + (i % 3) * 3, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexc("#b7aa8c"), 1 - tt)
        ctx.fill()


def accordion(ctx, x, y, squeeze):
    w = 120 * (0.75 + 0.25 * squeeze)
    bg.rect(ctx, x - w / 2 - 34, y - 60, 34, 120, "#b8333a", 5)
    bg.rect(ctx, x + w / 2, y - 60, 34, 120, "#b8333a", 5)
    for k in range(7):
        xx = x - w / 2 + k * w / 6
        ctx.move_to(xx, y - 56)
        ctx.line_to(xx + w / 12, y)
        ctx.line_to(xx, y + 56)
    ctx.set_source_rgb(*hexc("#3a2a24"))
    ctx.set_line_width(5)
    ctx.stroke()


def notes(ctx, x, y, t):
    for i in range(3):
        tt = (t * 0.8 + i * 0.33) % 1
        px, py = x + math.sin(tt * 6 + i) * 40 + i * 40, y - tt * 260
        ctx.save()
        ctx.translate(px, py)
        ctx.arc(0, 0, 16, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexc("#ffd84a"), 1 - tt)
        ctx.fill()
        ctx.rectangle(12, -60, 6, 60)
        ctx.fill()
        ctx.restore()


def flashlight(ctx, x, y, tx, ty, a):
    if a <= 0:
        return
    g = cairo.RadialGradient(tx, ty, 10, tx, ty, 320)
    g.add_color_stop_rgba(0, 1, 0.95, 0.7, 0.55 * a)
    g.add_color_stop_rgba(1, 1, 0.95, 0.7, 0.0)
    ctx.move_to(x, y)
    ctx.line_to(tx - 260, ty - 120)
    ctx.line_to(tx + 260, ty + 120)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()


SERIES_TAG = ["ALCATRAZ  ·  PART 1"]


def series_tag(ctx):
    w = 400
    ctx.save()
    ctx.translate(540, 120)
    ctx.rectangle(-w / 2, -38, w, 76)
    ctx.set_source_rgba(0.05, 0.05, 0.06, 0.75)
    ctx.fill()
    text_center(ctx, SERIES_TAG[0], 0, 0, 40, "#ffd84a")
    ctx.restore()


def vignette(ctx, k=0.55):
    g = cairo.RadialGradient(540, 960, 500, 540, 960, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, k)
    ctx.rectangle(0, 0, 1080, 1920)
    ctx.set_source(g)
    ctx.fill()


def big_number(ctx, txt, sub, x, y, p, color="#ffffff"):
    if p <= 0:
        return
    s = EASES["back"](clamp(p))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    text_center(ctx, txt, 0, 0, 200, color, stroke=22)
    text_center(ctx, sub, 0, 140, 64, "#ffffff", stroke=14)
    ctx.restore()


def ov(f, extra=None):
    vignette(f.ctx)
    series_tag(f.ctx)
    if extra:
        extra(f)




# ------------------------------------------------------------------ v2 props & fx
def drill(ctx, x, y, s=1.0, spin=0.0):
    """Homemade drill: a vacuum-cleaner motor with a bit."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    bg.rect(ctx, -55, -40, 90, 70, "#9aa1a8", 5)  # motor housing
    for k in range(4):
        ctx.move_to(-45 + k * 18, -34)
        ctx.line_to(-45 + k * 18, 24)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3)
    ctx.stroke()
    bg.rect(ctx, 35, -10, 70, 14, "#c9ced6", 4)  # bit
    ctx.save()
    ctx.translate(105, -3)
    ctx.rotate(spin)
    ctx.move_to(-6, -6)
    ctx.line_to(6, 6)
    ctx.move_to(-6, 6)
    ctx.line_to(6, -6)
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.restore()
    ctx.move_to(-55, 0)
    ctx.curve_to(-110, 0, -120, 60, -160, 70)  # power cord
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.restore()


def sparks(ctx, x, y, t, n=10):
    for i in range(n):
        tt = (t * 2.3 + i / n) % 1
        a = -math.pi * 0.9 + (i * 2.4) % (math.pi * 0.8)
        d = 30 + 160 * tt
        px, py = x + math.cos(a) * d, y + math.sin(a) * d + 120 * tt * tt
        ctx.move_to(px, py)
        ctx.line_to(px - math.cos(a) * 18, py - math.sin(a) * 18)
        ctx.set_source_rgba(1, 0.8, 0.3, 1 - tt)
        ctx.set_line_width(5)
        ctx.stroke()


def dummy_head(ctx, x, y, r=55, rot=0.0, alpha=1.0):
    """The fake head: painted plaster face, eyes closed, real hair on top."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    if alpha < 1:
        ctx.push_group()
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc("#e9cfb0"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.set_line_width(4)
    for ex in (-r * 0.33, r * 0.33):  # painted closed eyes
        ctx.arc(ex, -r * 0.05, r * 0.16, 0.15 * math.pi, 0.85 * math.pi)
        ctx.stroke()
    ctx.arc(0, r * 0.3, r * 0.2, 0.2 * math.pi, 0.8 * math.pi)
    ctx.stroke()
    ctx.save()  # hair
    ctx.arc(0, 0, r, math.radians(195), math.radians(345))
    ctx.arc_negative(0, -r * 0.15, r * 0.82, math.radians(340), math.radians(200))
    ctx.close_path()
    ctx.set_source_rgb(*hexc("#4a3020"))
    ctx.fill()
    ctx.restore()
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


def soap(ctx, x, y, p):
    if p <= 0:
        return
    s = EASES["back"](clamp(p))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    bg.rect(ctx, -45, -25, 90, 50, "#f4f1e6", 5)
    text_center(ctx, "SOAP", 0, 0, 24, "#7a8b99")
    ctx.restore()


def toilet_paper(ctx, x, y, p):
    if p <= 0:
        return
    s = EASES["back"](clamp(p))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    bg.rect(ctx, -40, -45, 80, 90, "#fbfbf7", 5)
    ctx.arc(0, -45, 40, math.pi, 2 * math.pi)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.arc(0, -45, 12, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def hair_clump(ctx, x, y, p):
    if p <= 0:
        return
    s = EASES["back"](clamp(p))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.set_source_rgb(*hexc("#4a3020"))
    ctx.set_line_width(6)
    for i in range(9):
        ctx.move_to(-40 + i * 10, 20)
        ctx.curve_to(-40 + i * 10, -10, -20 + i * 6, -30, -10 + i * 4, -40)
    ctx.stroke()
    ctx.restore()


def siren(ctx, t, a=1.0):
    k = 0.5 + 0.5 * math.sin(t * 9)
    ctx.rectangle(0, 0, 1080, 1920)
    ctx.set_source_rgba(0.9, 0.08, 0.08, 0.28 * k * a)
    ctx.fill()


def searchlight(ctx, x, y, ang, length=1400, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    g = cairo.LinearGradient(0, 0, length, 0)
    g.add_color_stop_rgba(0, 1, 1, 0.85, 0.55 * a)
    g.add_color_stop_rgba(1, 1, 1, 0.85, 0.0)
    ctx.move_to(0, 0)
    ctx.line_to(length, -120)
    ctx.line_to(length, 120)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


def bubble(ctx, txt, x, y, p, size=52, tail=(0, 1)):
    """Comic speech bubble that pops in."""
    if p <= 0:
        return
    from engine.text import text_width
    s = EASES["back"](clamp(p))
    w = text_width(ctx, txt, size) + 70
    h = size + 50
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    r = 30
    ctx.new_path()
    ctx.arc(-w / 2 + r, -h / 2 + r, r, math.pi, 1.5 * math.pi)
    ctx.arc(w / 2 - r, -h / 2 + r, r, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(w / 2 - r, h / 2 - r, r, 0, 0.5 * math.pi)
    ctx.line_to(tail[0] * 60 + 30, h / 2)
    ctx.line_to(tail[0] * 90, h / 2 + 50)
    ctx.line_to(tail[0] * 60 - 10, h / 2)
    ctx.arc(-w / 2 + r, h / 2 - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(7)
    ctx.stroke()
    text_center(ctx, txt, 0, 0, size, "#141418")
    ctx.restore()


def darken(ctx, a):
    ctx.rectangle(-300, -300, 1700, 2600)
    ctx.set_source_rgba(0, 0, 0.02, a)
    ctx.fill()
