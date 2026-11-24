"""Why Airplane Windows Are Round (true story: de Havilland Comet, 1952-54).
Ricks-style explainer: everyday thing -> disaster mystery -> crazy experiment -> 'aha' -> everyday payoff.
Sources: UK Ministry of Transport Comet inquiry (1955), RAE Farnborough water-tank tests; widely covered
(e.g. Smithsonian Air & Space, BBC Future)."""
import math
import os
import sys

import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from engine import bg  # noqa: E402
from engine.core import tween, pulse, EASES, clamp, hexc  # noqa: E402
from engine.render import Episode, Scene, N, label  # noqa: E402
from engine.rig import Character, Look, INK  # noqa: E402
from engine.text import text_center  # noqa: E402

PLATES = os.path.join(ROOT, "assets", "plates", "air")
_pl = {}

PASS = Character("passenger", Look(style="ricks", coat="#3f8f5c", coat_dark="#2c6a43", tie="#e8c547", hat="bowler",
                                    hat_color="#3a2a20"), seed=0.7)
ENG = Character("engineer", Look(style="ricks", coat="#f2f2ee", coat_dark="#c9c9c2", hair="tuft", glasses=True, tie="#2f6fe0"), seed=2.1)
ENG2 = Character("engineer2", Look(style="ricks", coat="#f2f2ee", coat_dark="#c9c9c2", mustache="thick", hair="side"), seed=3.7)
BIG = 2.7


# ---------------------------------------------------------------- helpers
def plate(ctx, name):
    if name not in _pl:
        _pl[name] = cairo.ImageSurface.create_from_png(os.path.join(PLATES, name + ".png"))
    s = _pl[name]
    ctx.set_source_surface(s, -(s.get_width() - 1080) / 2, -(s.get_height() - 1920) / 2)
    ctx.paint()


def char(f, ch, **p):
    s = p.get("s", 1.4)
    f.ctx.save()
    f.ctx.translate(p["x"], p["y"] + 4)
    f.ctx.scale(95 * s, 15 * s)
    f.ctx.arc(0, 0, 1, 0, 2 * math.pi)
    f.ctx.restore()
    f.ctx.set_source_rgba(0, 0, 0, 0.3)
    f.ctx.fill()
    return f.char(ch, p)


def wpt(p, local):
    return (p["x"] + local[0] * p.get("s", 1.4), p["y"] - p.get("jump", 0) + local[1] * p.get("s", 1.4))


def vignette(ctx, k=0.45):
    g = cairo.RadialGradient(540, 960, 500, 540, 960, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, k)
    ctx.rectangle(0, 0, 1080, 1920)
    ctx.set_source(g)
    ctx.fill()


def ov(f, extra=None):
    vignette(f.ctx)
    if extra:
        extra(f)


def pop_text(ctx, txt, x, y, p, size=110, color="#ffd84a"):
    if p > 0:
        text_center(ctx, txt, x, y, size * EASES["back"](clamp(p)) + 1, color, stroke=int(size / 6.5))


def crack(ctx, x, y, p, seed=1, length=260, color=(0.05, 0.05, 0.05)):
    """Jagged crack growing from (x, y) with progress p."""
    if p <= 0:
        return
    import random
    rng = random.Random(seed)
    pts = [(x, y)]
    ang = rng.uniform(-0.6, 0.6) - 0.5
    for i in range(12):
        ang += rng.uniform(-0.7, 0.7)
        step = length / 12
        pts.append((pts[-1][0] + math.cos(ang) * step, pts[-1][1] + math.sin(ang) * step))
    n = max(2, int(len(pts) * clamp(p)))
    ctx.move_to(*pts[0])
    for q in pts[1:n]:
        ctx.line_to(*q)
    ctx.set_source_rgb(*color)
    ctx.set_line_width(7)
    ctx.set_line_cap(1)
    ctx.stroke()


def drink(ctx, x, y):
    ctx.move_to(x - 22, y - 70)
    ctx.line_to(x + 22, y - 70)
    ctx.line_to(x, y - 30)
    ctx.close_path()
    ctx.set_source_rgba(1, 0.85, 0.5, 0.9)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.move_to(x, y - 30)
    ctx.line_to(x, y)
    ctx.stroke()


def stamp(ctx, txt, x, y, p, color="#d63c46", rot=-10):
    if p <= 0:
        return
    s = 1 + 1.5 * (1 - EASES["out"](clamp(p)))
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(rot))
    ctx.scale(s, s)
    w = 120 + 62 * len(txt)
    ctx.rectangle(-w / 2, -80, w, 160)
    ctx.set_source_rgba(*hexc(color), min(1, p * 3))
    ctx.set_line_width(14)
    ctx.stroke()
    text_center(ctx, txt, 0, 0, 110, color)
    ctx.restore()


def bubble(ctx, txt, x, y, p, size=56):
    if p <= 0:
        return
    from engine.text import text_width
    s = EASES["back"](clamp(p))
    w, h = text_width(ctx, txt, size) + 70, size + 50
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    r = 28
    ctx.new_path()
    ctx.arc(-w / 2 + r, -h / 2 + r, r, math.pi, 1.5 * math.pi)
    ctx.arc(w / 2 - r, -h / 2 + r, r, 1.5 * math.pi, 2 * math.pi)
    ctx.arc(w / 2 - r, h / 2 - r, r, 0, 0.5 * math.pi)
    ctx.line_to(20, h / 2)
    ctx.line_to(-10, h / 2 + 45)
    ctx.line_to(-20, h / 2)
    ctx.arc(-w / 2 + r, h / 2 - r, r, 0.5 * math.pi, math.pi)
    ctx.close_path()
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(7)
    ctx.stroke()
    text_center(ctx, txt, 0, 0, size, "#141418")
    ctx.restore()


# ---------------------------------------------------------------- the stress-flow diagram (2D cutaway)
def blueprint(ctx):
    ctx.rectangle(-300, -300, 1700, 2600)
    ctx.set_source_rgb(*hexc("#123a6b"))
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.07)
    ctx.set_line_width(2)
    for i in range(-5, 40):
        ctx.move_to(i * 60, -300)
        ctx.line_to(i * 60, 2300)
        ctx.move_to(-300, i * 60)
        ctx.line_to(1500, i * 60)
    ctx.stroke()


def flow_panel(ctx, cx, cy, w, h, shape, t, a=90, hot=0.0, label_txt=None):
    """Metal panel with force lines flowing around a hole. shape: 'round' or 'square'."""
    ctx.save()
    ctx.rectangle(cx - w / 2, cy - h / 2, w, h)
    ctx.set_source_rgb(*hexc("#c9d2dc"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.rectangle(cx - w / 2, cy - h / 2, w, h)
    ctx.clip()
    n = 13
    for i in range(n):
        y0 = (i - (n - 1) / 2) * (h / n)
        pts = []
        for k in range(80):
            x = -w / 2 + w * k / 79
            bump = max(0.0, a * 1.08 - abs(y0))
            sgn = 1 if y0 >= 0 else -1
            if shape == "round":  # smooth detour around a circle
                y = y0 + sgn * bump * math.exp(-(x / (a * 1.25)) ** 2)
            else:  # abrupt detour around a square: lines bunch up at the corners
                k_x = 1.0 if abs(x) < a * 1.1 else max(0.0, 1 - (abs(x) - a * 1.1) / (a * 0.25))
                y = y0 + sgn * bump * k_x
            pts.append((cx + x, cy + y))
        ctx.move_to(*pts[0])
        for q in pts[1:]:
            ctx.line_to(*q)
        ctx.set_dash([28, 18], -t * 120)
        ctx.set_source_rgb(*hexc("#1f5fbf"))
        ctx.set_line_width(5)
        ctx.stroke()
    ctx.set_dash([])
    # the hole (window)
    if shape == "round":
        ctx.arc(cx, cy, a, 0, 2 * math.pi)
    else:
        ctx.rectangle(cx - a, cy - a, 2 * a, 2 * a)
    ctx.set_source_rgb(*hexc("#8fc6ff"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(7)
    ctx.stroke()
    if shape == "square" and hot > 0:
        for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            g = cairo.RadialGradient(cx + sx * a, cy + sy * a, 4, cx + sx * a, cy + sy * a, 60)
            k = hot * (0.75 + 0.25 * math.sin(t * 10))
            g.add_color_stop_rgba(0, 1, 0.15, 0.1, 0.95 * k)
            g.add_color_stop_rgba(1, 1, 0.15, 0.1, 0.0)
            ctx.arc(cx + sx * a, cy + sy * a, 60, 0, 2 * math.pi)
            ctx.set_source(g)
            ctx.fill()
    ctx.restore()
    if label_txt:
        text_center(ctx, label_txt, cx, cy + h / 2 + 60, 56, "#ffffff", stroke=10)


def paperclip(ctx, x, y, bend, broken=0.0, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.set_line_cap(1)
    for side, (col, lw) in [(sd, cl) for cl in ((INK, 17), (hexc("#dfe5ec"), 9)) for sd in (-1, 1)]:
        ctx.set_source_rgb(*col)
        ctx.set_line_width(lw)
        ctx.save()
        off = broken * 60 * side
        ctx.translate(off, broken * 30)
        ctx.rotate(side * math.radians(bend) / 2 + broken * side * 0.6)
        ctx.move_to(0, 0)
        ctx.line_to(side * 110, 0)
        ctx.line_to(side * 110, -36)
        ctx.line_to(side * 20, -36)
        ctx.stroke()
        ctx.restore()
    ctx.restore()


def line_idx(f):
    """Index of the line currently being spoken (for hard cuts between sentences)."""
    k = 0
    for i, ln in enumerate(f.scene.lines):
        if f.t >= ln.start - 0.05:
            k = i
    return k


# ---------------------------------------------------------------- shots
def s1(f):  # square windows
    plate(f.ctx, "windows_square")


def c1(f):
    return dict(z=tween(f.t, 0, f.dur, 1.1, 1.35), x=tween(f.t, 0, f.dur, 420, 300), y=920)


def s2(f):  # broke apart
    c, t = f.ctx, f.t
    plate(c, "sky_plane")
    tb = f.T.word(0, "broke")
    crack(c, 470, 860, f.r(tb, tb + 0.4), seed=2, length=200)
    crack(c, 490, 870, f.r(tb + 0.1, tb + 0.5), seed=5, length=160)
    if t > tb:
        c.rectangle(0, 0, 1080, 1920)
        c.set_source_rgba(1, 1, 1, 0.8 * (1 - f.r(tb, tb + 0.25)))
        c.fill()
    tw = f.T.word(0, "why")
    pop_text(c, "?", 520, 640, f.r(tw, tw + 0.25), size=140, color="#ffffff")


def c2(f):
    tb = f.T.word(0, "broke")
    return dict(z=tween(f.t, 0, f.dur, 1.5, 1.7), x=520, y=880, shake=16 * pulse(f.t, tb, 0.6), rot=2 * pulse(f.t, tb, 0.6))


def s3(f):  # the Comet, 1952
    plate(f.ctx, "sky_plane")


def o3(f):
    t1 = f.T.word(0, "1952")
    tc = f.T.word(1, "Comet")
    ov(f, lambda f: (label(f.ctx, "1952", 540, 330, f.r(t1, t1 + 0.25), size=80, color="#ffffff"),
                     label(f.ctx, "THE FIRST JET AIRLINER", 540, 460, f.r(tc, tc + 0.25), size=50)))


def c3(f):
    if line_idx(f) == 0:
        return dict(z=tween(f.t, 0, 1.5, 2.2, 2.0), x=380, y=880)
    return dict(z=tween(f.t, 1.5, f.dur, 1.45, 1.3), x=560, y=880)


def s4(f):  # passengers loved it
    c, t = f.ctx, f.t
    plate(c, "cabin_square")
    tl = f.T.word(1, "love")
    p = dict(x=520, y=2150, s=BIG, face=1, expr="grin" if t > tl else "smile", fa=110, fb=40,
             tilt=6 * math.sin(f.gt * 2))
    pts = char(f, PASS, **p)
    drink(c, *wpt(p, pts["hand_f"]))
    bubble(c, "So fancy!", 690, 560, f.r(tl, tl + 0.2))


def c4(f):
    if line_idx(f) == 0:
        return dict(z=tween(f.t, 0, f.dur, 1.0, 1.05), y=980)
    return dict(z=1.6, x=520, y=640)


def s5(f):  # 1954, two broke apart
    c, t = f.ctx, f.t
    plate(c, "hangar")
    c.rectangle(-300, -300, 1700, 2600)
    c.set_source_rgba(0.05, 0.05, 0.1, 0.45)
    c.fill()
    t54 = f.T.word(0, "1954")
    tt = f.T.word(0, "two")
    for i, x in enumerate((360, 720)):
        p = f.r(tt + i * 0.35, tt + i * 0.35 + 0.25)
        if p > 0:
            c.save()
            c.translate(x, 900)
            s = EASES["back"](p)
            c.scale(s, s)
            bg.rect(c, -150, -110, 300, 220, "#efe6c9", 6)
            text_center(c, "JET LOST", 0, -50, 50, "#b8333a")
            text_center(c, ("JAN" if i == 0 else "APR") + " 1954", 0, 30, 44, "#141418")
            c.restore()
    pop_text(c, "1954", 540, 520, f.r(t54, t54 + 0.25), size=150, color="#ffffff")


def c5(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.12), shake=6 * pulse(f.t, f.T.word(0, "two") + 0.35, 0.3))


def s6(f):  # grounded
    c = f.ctx
    plate(c, "hangar")
    stamp(c, "GROUNDED", 540, 820, f.r(f.T.word(0, "grounded") - 0.1, f.T.word(0, "grounded") + 0.1))


def c6(f):
    return dict(z=1.05, shake=12 * pulse(f.t, f.T.word(0, "grounded") + 0.1, 0.3))


def s7(f):  # stumped -> crazy idea
    c, t = f.ctx, f.t
    plate(c, "hangar")
    tc = f.T.word(1, "crazy")
    scratch = math.sin(f.gt * 10) * 15 if t < tc else 0
    char(f, ENG2, x=820, y=1980, s=2.0, face=-1, expr="worried", fa=150 + scratch, fb=60, sweat=1)
    char(f, ENG, x=380, y=2120, s=BIG, face=1, expr="worried" if t < tc else "excited",
         fa=150 + scratch if t < tc else 160, fb=60 if t < tc else 0, look=0.3)
    if t > tc - 0.1:
        p = EASES["back"](f.r(tc - 0.1, tc + 0.15))
        c.save()
        c.translate(420, 470)
        c.scale(p, p)
        c.arc(0, 0, 60, 0, 2 * math.pi)
        c.set_source_rgb(*hexc("#fff3a0"))
        c.fill_preserve()
        c.set_source_rgb(*INK)
        c.set_line_width(6)
        c.stroke()
        bg.rect(c, -26, 52, 52, 34, "#9aa0ab", 5)
        c.restore()


def c7(f):
    if line_idx(f) == 0:
        return dict(z=1.0, y=980)
    return dict(z=1.45, x=420, y=760)


def s8(f):  # sank a whole plane
    c, t = f.ctx, f.t
    plate(c, "tank")
    tw = f.T.word(0, "water")
    if t > tw:
        for i in range(14):  # splash droplets
            tt = t - tw - i * 0.02
            if 0 < tt < 0.9:
                x = 560 + math.sin(i * 1.9) * 260 * tt
                y = 1000 - 500 * tt + 900 * tt * tt
                c.arc(x, y, 14, 0, 2 * math.pi)
                c.set_source_rgba(0.75, 0.9, 1, 1 - tt)
                c.fill()


def o8(f):
    tt = f.T.word(0, "tank")
    ov(f, lambda f: label(f.ctx, "A GIANT WATER TANK", 540, 330, f.r(tt, tt + 0.25), size=56))


def c8(f):
    return dict(z=tween(f.t, 0, f.dur, 1.2, 1.0), shake=6 * pulse(f.t, f.T.word(0, "water"), 0.4))


def s9(f):  # pumped thousands of times
    c, t = f.ctx, f.t
    plate(c, "tank")
    n = int(3000 * EASES["in"](f.r(0.4, f.dur - 0.2)))
    c.save()
    c.translate(540, 560)
    bg.rect(c, -330, -110, 660, 220, "#141418", 8)
    text_center(c, "FAKE FLIGHTS", 0, -50, 46, "#ffd84a")
    text_center(c, f"{n:,}", 0, 30, 110, "#ffffff")
    c.restore()
    # pressure gauge pulsing
    g = 0.5 + 0.5 * math.sin(f.gt * 8)
    c.save()
    c.translate(220, 1250)
    c.arc(0, 0, 110, 0, 2 * math.pi)
    c.set_source_rgb(1, 1, 1)
    c.fill_preserve()
    c.set_source_rgb(*INK)
    c.set_line_width(8)
    c.stroke()
    c.rotate(-2.3 + 2.0 * g)
    c.move_to(0, 0)
    c.line_to(0, -85)
    c.set_source_rgb(*hexc("#d63c46"))
    c.set_line_width(9)
    c.stroke()
    c.restore()


def c9(f):
    return dict(z=1.05, y=tween(f.t, 0, f.dur, 1000, 940))


WIN_CORNER = (455, 735)


def s10(f):  # a crack
    c, t = f.ctx, f.t
    plate(c, "windows_square")
    tc = f.T.word(0, "crack")
    crack(c, *WIN_CORNER, f.r(tc - 0.1, tc + 0.4), seed=7, length=240)
    pop_text(c, "CRACK!", 560, 520, f.r(tc, tc + 0.2), size=120)


def c10(f):
    tc = f.T.word(0, "crack")
    return dict(z=tween(f.t, 0, tc, 1.0, 1.35), x=tween(f.t, 0, tc, 540, 380), y=tween(f.t, 0, tc, 960, 880),
                shake=10 * pulse(f.t, tc, 0.3))


def s11(f):  # at a corner
    c, t = f.ctx, f.t
    plate(c, "windows_square")
    crack(c, *WIN_CORNER, 1, seed=7, length=240)
    k = f.r(f.T.word(0, "corner") - 0.1, f.T.word(0, "corner") + 0.15)
    if k > 0:
        c.arc(*WIN_CORNER, 70 + 10 * math.sin(f.gt * 10), 0, 2 * math.pi)
        c.set_source_rgba(1, 0.2, 0.15, 0.9 * k)
        c.set_line_width(12)
        c.stroke()


def c11(f):
    return dict(z=1.9, x=WIN_CORNER[0] + 40, y=WIN_CORNER[1] - 20)


def s12(f):  # balloon & flow
    c, t = f.ctx, f.t
    blueprint(c)
    tb = f.T.word(0, "balloon")
    puff = 1 + 0.06 * math.sin(f.gt * 5) * f.r(tb, tb + 0.3)
    c.save()
    c.translate(540, 600)
    c.scale(puff, puff)
    c.move_to(-300, -90)
    c.line_to(260, -90)
    c.curve_to(380, -90, 380, 90, 260, 90)
    c.line_to(-300, 90)
    c.close_path()
    c.set_source_rgb(*hexc("#e9edf2"))
    c.fill_preserve()
    c.set_source_rgb(*INK)
    c.set_line_width(7)
    c.stroke()
    for k in range(8):
        c.rectangle(-240 + k * 60, -25, 30, 30)
    c.set_source_rgb(*hexc("#1f3550"))
    c.fill()
    c.restore()
    if t > tb:
        for k in range(10):  # arrows pushing outward
            a = k * math.pi / 5
            r0 = 200 + 20 * math.sin(f.gt * 5)
            c.move_to(540 + math.cos(a) * r0 * 1.6, 600 + math.sin(a) * r0 * 0.6)
            c.line_to(540 + math.cos(a) * (r0 + 60) * 1.6, 600 + math.sin(a) * (r0 + 60) * 0.6)
        c.set_source_rgb(*hexc("#ffd84a"))
        c.set_line_width(8)
        c.stroke()
    tf = f.T.word(1, "flow")
    if t > tf - 0.3:
        flow_panel(c, 540, 1160, 760, 420, "round", f.gt, a=80)


def c12(f):
    if line_idx(f) == 0:
        return dict(z=tween(f.t, 0, 2.0, 1.4, 1.3), y=620)
    return dict(z=1.25, y=1160)


def c13(f):
    if line_idx(f) == 0:
        return dict(z=1.35, y=600)
    return dict(z=1.35, y=1170, shake=5 * pulse(f.t, f.T.word(1, "piles"), 0.3))


def s13(f):  # round vs square
    c, t = f.ctx, f.t
    blueprint(c)
    ts = f.T.word(1, "sharp")
    flow_panel(c, 540, 560, 760, 420, "round", f.gt, a=80, label_txt="ROUND: SMOOTH")
    if t > ts - 0.2:
        flow_panel(c, 540, 1160, 760, 420, "square", f.gt, a=80, hot=f.r(f.T.word(1, "piles"), f.T.word(1, "piles") + 0.3),
                   label_txt="SQUARE: STRESS PILES UP")


def s14(f):  # paperclip analogy
    c, t = f.ctx, f.t
    plate(c, "hangar")
    tsnap = f.T.word(2, "snap")
    t1000 = f.T.word(2, "thousand")
    char(f, ENG, x=540, y=2150, s=BIG, face=1, expr="thinking" if t < tsnap else "shock", fa=60, fb=50, ba=60, bb=50)
    speed = 3 if t < t1000 else 14
    bend = 50 * math.sin(f.gt * speed) if t < tsnap else 0
    paperclip(c, 560, 1330, bend, broken=f.r(tsnap, tsnap + 0.3), s=2.2)
    labels = [(f.T.word(0, "paperclip"), "x1"), (t1000, "x1,000")]
    for i, (tm, lab) in enumerate(labels):
        nxt = labels[i + 1][0] if i + 1 < len(labels) else tsnap
        if tm <= t < nxt:
            pop_text(c, lab, 540, 880, f.r(tm, tm + 0.15), size=110, color="#ffffff")
    pop_text(c, "SNAP!", 760, 1150, f.r(tsnap, tsnap + 0.15), size=120)


def c14(f):
    k = line_idx(f)
    sh = 12 * pulse(f.t, f.T.word(2, "snap"), 0.3)
    if k == 0:
        return dict(z=1.0, y=980)
    if k == 1:
        return dict(z=1.3, x=540, y=1000, shake=sh)
    return dict(z=1.55, x=560, y=1150, shake=sh)


def s15(f):  # rounded the corners
    c, t = f.ctx, f.t
    tr = f.T.word(0, "rounded")
    plate(c, "windows_round" if t > tr else "windows_square")
    if t > tr:
        bg.sparkle_burst(c, 470, 900, f.r(tr, tr + 0.6), n=10, r=260)


def o15(f):
    tr = f.T.word(0, "rounded")
    ov(f, lambda f: pop_text(f.ctx, "ROUNDED!", 540, 520, f.r(tr, tr + 0.2), size=120))


def c15(f):
    return dict(z=tween(f.t, 0, f.dur, 1.25, 1.05), shake=6 * pulse(f.t, f.T.word(0, "rounded"), 0.3))


def s16(f):  # payoff: every window you've looked out of
    c, t = f.ctx, f.t
    plate(c, "cabin_round")
    char(f, PASS, x=520, y=2150, s=BIG, face=-1, expr="smile", look=-1, lookY=-0.2, fa=20, fb=120)


def c16(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.1), y=980)


def s17(f):  # loop / CTA
    c = f.ctx
    plate(c, "windows_round")


def o17(f):
    ov(f, lambda f: label(f.ctx, "CHECK THE CORNERS ✈", 540, 520, f.r(0.2, 0.5), size=60))


def c17(f):
    return dict(z=tween(f.t, 0, f.dur, 1.05, 1.25))


OV = lambda f: ov(f)  # noqa: E731

SCENES = [
    Scene("square", [N("Airplane windows used to be square.")], s1, c1, overlay=OV, pad=0.1,
          cues=lambda T: [(0.0, "whoosh", 0.5)]),
    Scene("breakup", [N("Then two jets broke apart in the sky, and nobody knew why.")], s2, c2,
          overlay=OV, trans="punch", pad=0.2,
          cues=lambda T: [(T.word(0, "broke"), "hit", 1.0), (T.word(0, "why"), "dun", 0.6)]),
    Scene("comet", [N("It's 1952."),
                    N("The de Havilland Comet is the world's first jet airliner.", gap=0.1)],
          s3, c3, overlay=o3, trans="whip", pad=0.1,
          cues=lambda T: [(T.word(0, "1952"), "pop", 0.7), (T.word(1, "Comet"), "whoosh", 0.6)]),
    Scene("loved", [N("Faster and higher than anything before it."), N("Passengers love it.", gap=0.1)],
          s4, c4, overlay=OV, trans="whip", pad=0.2, cues=lambda T: [(T.word(1, "love"), "ding", 0.6)]),
    Scene("1954", [N("Then in 1954, two Comets break apart in mid-air, months apart.")],
          s5, c5, overlay=OV, trans="flash", pad=0.1,
          cues=lambda T: [(T.word(0, "1954"), "dun", 0.7), (T.word(0, "two"), "stamp", 0.7),
                          (T.word(0, "two") + 0.35, "stamp", 0.7)]),
    Scene("grounded", [N("Every Comet is grounded.")], s6, c6, overlay=OV, trans="cut", pad=0.3,
          cues=lambda T: [(T.word(0, "grounded") + 0.1, "stamp", 1.0)]),
    Scene("stumped", [N("Engineers are stumped."), N("So they try something crazy.", gap=0.1)], s7, c7,
          overlay=OV, trans="whip", pad=0.1, cues=lambda T: [(T.word(1, "crazy"), "ding", 0.8)]),
    Scene("tank", [N("They sink an entire airplane in a giant tank of water.")], s8, c8, overlay=o8,
          trans="whip", pad=0.2, cues=lambda T: [(T.word(0, "water"), "waves", 0.9), (T.word(0, "sink"), "whoosh", 0.6)]),
    Scene("pump", [N("Then pump it up and down, again and again, like thousands of flights.")], s9, c9,
          overlay=OV, trans="punch", pad=0.2,
          cues=lambda T: [(0.3 + k * 0.45, "tick", 1.0) for k in range(8)]),
    Scene("crack", [N("Until finally... a crack.")], s10, c10, overlay=OV, trans="flash", pad=0.2,
          cues=lambda T: [(T.word(0, "crack"), "hit", 1.0), (T.word(0, "crack"), "glass", 0.5)]),
    Scene("corner", [N("And it started at a corner.")], s11, c11, overlay=OV, trans="punch", pad=0.3,
          cues=lambda T: [(T.word(0, "corner"), "dun", 0.7)]),
    Scene("balloon", [N("See, up high, the cabin puffs up like a balloon."),
                      N("That force has to flow around every window.", gap=0.1)], s12, c12, overlay=OV, trans="whip",
          pad=0.2, cues=lambda T: [(T.word(0, "balloon"), "pop", 0.7), (T.word(1, "flow"), "whoosh", 0.5)]),
    Scene("flow", [N("Around a round hole, it flows smoothly."),
                   N("But at a sharp corner, it all piles up in one tiny spot.", gap=0.1)], s13, c13, overlay=OV,
          trans="cut", pad=0.2, cues=lambda T: [(T.word(1, "sharp"), "pop", 0.7), (T.word(1, "piles"), "dun", 0.7)]),
    Scene("paperclip", [N("It's like bending a paperclip."), N("Once is fine.", gap=0.1),
                        N("Do it a thousand times... snap.", gap=0.1)], s14, c14, overlay=OV, trans="whip",
          pad=0.3, cues=lambda T: [(T.word(2, "snap"), "hit", 0.9), (T.word(2, "snap"), "clink", 1.0)]),
    Scene("rounded", [N("So engineers rounded the corners.")], s15, c15, overlay=o15, trans="whip", pad=0.3,
          cues=lambda T: [(T.word(0, "rounded"), "reveal", 0.8)]),
    Scene("payoff", [N("That's why every plane window you've ever looked through has round corners.")],
          s16, c16, overlay=OV, trans="whip", pad=0.2, cues=lambda T: []),
    Scene("cta", [N("Next time you fly, check the corners.")], s17, c17, overlay=o17, trans="fade", pad=0.8,
          cues=lambda T: [(0.2, "ding", 0.6)]),
]

# Human narration (ElevenLabs "Liam" via vidIQ), one file per line, in script order.
VOICE = os.path.join(ROOT, "assets", "voice", "airplane_windows")
_i = 0
for _sc in SCENES:
    for _ln in _sc.lines:
        _ln.audio = os.path.join(VOICE, f"line{_i:02d}.mp3")
        _ln.gap = min(_ln.gap, 0.06)
        _i += 1
    if _sc is not SCENES[-1]:
        _sc.pad = min(_sc.pad, 0.12)

EPISODE = Episode("airplane_windows_v2", SCENES, music="caper", music_gain=0.14, caption_style="ricks",
                  caption_y=1440, voice_tempo=1.1)
