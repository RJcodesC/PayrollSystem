"""Why Pirates Wore Eye Patches (the dark-adaptation theory). All-ages myth explainer.
Framed honestly as a theory: no historical proof pirates did this; MythBusters (2007) found it plausible.
Eye fact: full dark adaptation of the rods takes roughly 20-30 minutes."""
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
from engine.text import text_center, text_width  # noqa: E402

PLATES = os.path.join(ROOT, "assets", "plates", "pirate")
VOICE = os.path.join(ROOT, "assets", "voice", "pirate_patch")
_pl = {}

HERO = Character("hero", Look(coat="#d63c46", coat_dark="#a12a33", hat="bandana", hat_color="#c8313a", patch=True,
                              style="ricks"), seed=0.6)
CAPT = Character("capt", Look(coat="#1f3a6b", coat_dark="#142848", hat="tricorn", hat_color="#1a1a1e",
                              hat_band="#d9b44a", beard="#3a2416", style="ricks"), seed=1.4)
TEST = Character("tester", Look(coat="#3a7bd5", coat_dark="#2a5ca3", hair="side", patch=True, style="ricks"), seed=2.4)
BIG = 2.8


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
    pts = f.char(ch, p)
    return pts


def wpt(p, local):
    return (p["x"] + local[0] * p.get("s", 1.4), p["y"] - p.get("jump", 0) + local[1] * p.get("s", 1.4))


def line_idx(f):
    k = 0
    for i, ln in enumerate(f.scene.lines):
        if f.t >= ln.start - 0.05:
            k = i
    return k


def vignette(ctx, k=0.45):
    g = cairo.RadialGradient(540, 960, 500, 540, 960, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, k)
    ctx.rectangle(0, 0, 1080, 1920)
    ctx.set_source(g)
    ctx.fill()


def OV(f):
    vignette(f.ctx)


def pop(ctx, txt, x, y, p, size=120, color="#ffd84a"):
    if p > 0:
        text_center(ctx, txt, x, y, size * EASES["back"](clamp(p)) + 1, color, stroke=int(size / 6.5))


def dark(ctx, a, tint=(0.0, 0.0, 0.03)):
    if a > 0:
        ctx.rectangle(-400, -400, 1900, 2800)
        ctx.set_source_rgba(*tint, clamp(a))
        ctx.fill()


def eyes_in_dark(ctx, p, pts, look=0.0, blink=False):
    """Just two white eyes floating in the darkness (cartoon trope)."""
    hx, hy = wpt(p, pts["head"])
    s = p.get("s", 1.4)
    for dx in (-13, 35):
        ctx.save()
        ctx.translate(hx + (dx + look * 8) * s * (1 if p.get("face", 1) >= 0 else -1), hy - 4 * s)
        ctx.scale(10 * s, (2 if blink else 15) * s)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()


def glare(ctx, x, y, a=1.0):
    g = cairo.RadialGradient(x, y, 10, x, y, 700)
    g.add_color_stop_rgba(0, 1, 1, 0.92, 0.95 * a)
    g.add_color_stop_rgba(0.35, 1, 0.95, 0.75, 0.45 * a)
    g.add_color_stop_rgba(1, 1, 0.95, 0.75, 0.0)
    ctx.rectangle(-400, -400, 1900, 2800)
    ctx.set_source(g)
    ctx.fill()


def smoke(ctx, x, y, t, t0):
    if t < t0:
        return
    for i in range(7):
        tt = t - t0 - i * 0.05
        if 0 < tt < 1.4:
            r = 30 + 90 * tt
            ctx.arc(x + i * 22 - 60 + tt * 40, y - tt * 60 + math.sin(i) * 20, r, 0, 2 * math.pi)
            ctx.set_source_rgba(0.92, 0.92, 0.9, 0.85 * (1 - tt / 1.4))
            ctx.fill()
    if t - t0 < 0.15:
        ctx.arc(x, y, 90, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 0.8, 0.3, 1 - (t - t0) / 0.15)
        ctx.fill()


def big_eye(ctx, cx, cy, pupil, w=420):
    """Cartoon eyeball cutaway: almond white, blue iris, black pupil that grows in the dark."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.move_to(-w, 0)
    ctx.curve_to(-w * 0.5, -w * 0.62, w * 0.5, -w * 0.62, w, 0)
    ctx.curve_to(w * 0.5, w * 0.62, -w * 0.5, w * 0.62, -w, 0)
    ctx.close_path()
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(12)
    ctx.stroke()
    ctx.arc(0, 0, w * 0.42, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc("#2f7fd0"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(8)
    ctx.stroke()
    ctx.arc(0, 0, w * 0.42 * pupil, 0, 2 * math.pi)
    ctx.set_source_rgb(0.03, 0.03, 0.04)
    ctx.fill()
    ctx.arc(-w * 0.12, -w * 0.12, w * 0.06, 0, 2 * math.pi)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()
    ctx.restore()


def clock(ctx, cx, cy, frac, r=230):
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(14)
    ctx.stroke()
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, r - 20, -math.pi / 2, -math.pi / 2 + 2 * math.pi * frac)
    ctx.close_path()
    ctx.set_source_rgba(*hexc("#ffd84a"), 0.9)
    ctx.fill()
    ctx.move_to(cx, cy)
    a = -math.pi / 2 + 2 * math.pi * frac
    ctx.line_to(cx + math.cos(a) * (r - 30), cy + math.sin(a) * (r - 30))
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(12)
    ctx.stroke()


def stamp(ctx, txt, x, y, p, color="#d63c46", rot=-8, size=90):
    if p <= 0:
        return
    s = 1 + 1.4 * (1 - EASES["out"](clamp(p)))
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(rot))
    ctx.scale(s, s)
    w = text_width(ctx, txt, size) + 80
    ctx.rectangle(-w / 2, -size * 0.8, w, size * 1.6)
    ctx.set_source_rgba(*hexc(color), min(1, p * 3))
    ctx.set_line_width(12)
    ctx.stroke()
    text_center(ctx, txt, 0, 0, size, color)
    ctx.restore()


# ---------------------------------------------------------------- shots
def s0(f):  # hook: a good eye under the patch
    c, t = f.ctx, f.t
    plate(c, "deck")
    tg = f.T.word(0, "good")
    lift = f.r(tg - 0.2, tg + 0.15) * (1 - f.r(f.dur - 0.5, f.dur - 0.2))
    char(f, HERO, x=560, y=2160, s=BIG, face=-1, expr="sly" if lift < 0.3 else "wink", patch=0.5 * lift,
         fa=20 + 120 * lift, fb=60, look=0.6)
    pop(c, "?!", 780, 620, f.r(tg + 0.1, tg + 0.35), size=150, color="#ffffff")


def c0(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.12), y=960)


def s1(f):  # ship under attack
    c, t = f.ctx, f.t
    plate(c, "sea")
    ta = f.T.word(0, "attack")
    smoke(c, 860, 1010, t, ta - 0.1)
    smoke(c, 820, 1040, t, ta + 0.25)


def o1(f):
    t17 = f.T.word(0, "1700s")
    OV(f)
    label(f.ctx, "1700s", 540, 330, f.r(t17, t17 + 0.25), size=90, color="#ffffff")


def c1(f):
    ta = f.T.word(0, "attack")
    return dict(z=tween(f.t, 0, f.dur, 1.35, 1.5), x=640, y=900,
                shake=16 * pulse(f.t, ta, 0.4) + 12 * pulse(f.t, ta + 0.35, 0.4))


def s2(f):  # blinding sun
    c, t = f.ctx, f.t
    plate(c, "deck")
    char(f, HERO, x=600, y=2160, s=BIG, face=-1, expr="angry", fa=155, fb=55, look=-0.3, lookY=-0.6)
    tb = f.T.word(0, "blinding")
    glare(c, 220, 380, 0.5 + 0.5 * f.r(tb - 0.2, tb + 0.2))


def c2(f):
    return dict(z=1.0, y=960)


def s3(f):  # jump below deck -> pitch black
    c, t = f.ctx, f.t
    plate(c, "hold")
    tb = f.T.word(0, "black")
    land = f.r(0, 0.45, "in")
    p = dict(x=520, y=1760, s=1.9, face=1, expr="shock" if t > tb else "angry", hold="sword", fa=70, fb=20,
             jump=900 * (1 - land), squash=pulse(t, 0.45, 0.2))
    pts = char(f, HERO, **p)
    d = 0.95 * f.r(tb - 0.15, tb + 0.1)
    dark(c, d)
    if d > 0.5:
        eyes_in_dark(c, p, pts, look=math.sin(f.gt * 3))


def c3(f):
    return dict(z=1.0, shake=10 * pulse(f.t, 0.45, 0.3))


def s4(f):  # can't see a thing
    c, t = f.ctx, f.t
    plate(c, "hold")
    p = dict(x=tween(t, 0, f.dur, 520, 600), y=1760, s=1.9, face=1, expr="shock", hold="sword", fa=70, fb=20)
    pts = char(f, HERO, **p)
    dark(c, 0.95)
    eyes_in_dark(c, p, pts, look=math.sin(f.gt * 5), blink=(f.gt % 1.3) < 0.1)
    pop(c, "BONK!", 700, 900, f.r(f.dur - 0.5, f.dur - 0.35), size=110, color="#ffffff")


def c4(f):
    return dict(z=1.15, shake=10 * pulse(f.t, f.dur - 0.5, 0.3))


def s5(f):  # eyes need time: pupil grows
    c, t = f.ctx, f.t
    c.rectangle(-400, -400, 1900, 2800)
    c.set_source_rgb(*hexc("#0d1424"))
    c.fill()
    big_eye(c, 540, 860, tween(t, 0.3, f.dur, 0.25, 0.85, "inout"))
    pop(c, "PUPIL", 540, 480, f.r(0.3, 0.55), size=80, color="#ffffff")


def c5(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.15))


def s6(f):  # up to 20 minutes
    c, t = f.ctx, f.t
    c.rectangle(-400, -400, 1900, 2800)
    c.set_source_rgb(*hexc("#0d1424"))
    c.fill()
    clock(c, 540, 880, EASES["inout"](f.r(0.1, f.dur - 0.2)) * 20 / 60)
    pop(c, "20 MIN", 540, 520, f.r(f.T.word(0, "twenty"), f.T.word(0, "twenty") + 0.2), size=120)


def s7(f):  # sword fight
    c, t = f.ctx, f.t
    plate(c, "hold")
    lunge = math.sin(f.gt * 7)
    char(f, CAPT, x=780 - 40 * max(0, lunge), y=1780, s=2.0, face=-1, expr="angry", hold="sword",
         fa=80 + 30 * lunge, fb=10, lean=10 * max(0, lunge))
    char(f, HERO, x=330, y=1780, s=2.0, face=1, expr="worried", sweat=1, hold="sword", fa=70 - 20 * lunge, fb=30,
         lean=-8)
    tt = f.T.word(0, "twenty")
    pop(c, "CLANG!", 560, 900, pulse(t, tt - 0.2, 0.6) * 2, size=110, color="#ffffff")
    dark(c, 0.25)


def c7(f):
    return dict(z=1.05, shake=5 * abs(math.sin(f.gt * 7)))


def s8(f):  # the theory: cover one eye
    c, t = f.ctx, f.t
    plate(c, "deck")
    char(f, HERO, x=560, y=2160, s=BIG, face=-1, expr="smile", patch=0.0, fa=20, fb=60)


def o8(f):
    tt = f.T.word(0, "theory")
    OV(f)
    label(f.ctx, "THE THEORY", 540, 330, f.r(tt, tt + 0.25), size=70)


def c8(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.35), x=tween(f.t, 0, f.dur, 540, 500), y=tween(f.t, 0, f.dur, 960, 760))


def s9(f):  # that eye stays in the dark
    c, t = f.ctx, f.t
    plate(c, "deck")
    p = dict(x=560, y=2160, s=BIG, face=-1, expr="neutral", patch=0.0, fa=20, fb=60)
    char(f, HERO, **p)
    k = EASES["back"](f.r(0.2, 0.5))
    if k > 0:  # x-ray bubble: under the patch, the eye is wide open in the dark
        c.save()
        c.translate(780, 520)
        c.scale(k, k)
        c.arc(0, 0, 190, 0, 2 * math.pi)
        c.set_source_rgb(*hexc("#0d1424"))
        c.fill_preserve()
        c.set_source_rgb(1, 1, 1)
        c.set_line_width(10)
        c.stroke()
        big_eye(c, 0, 0, 0.82, w=140)
        c.restore()
        text_center(c, "Ready for the dark", 780, 760, 46, "#ffffff", stroke=10)


def s10(f):  # on deck, use the open eye
    c, t = f.ctx, f.t
    plate(c, "deck")
    char(f, HERO, x=560, y=2160, s=BIG, face=-1, expr="smile", patch=0.0, look=math.sin(f.gt * 3), fa=20, fb=60)
    glare(c, 220, 380, 0.4)


def c10(f):
    return dict(z=1.0, y=960)


def s11(f):  # below deck, flip the patch
    c, t = f.ctx, f.t
    plate(c, "hold")
    tf = f.T.word(0, "flip")
    flip = f.r(tf - 0.1, tf + 0.5)
    char(f, HERO, x=540, y=2200, s=BIG, face=1, expr="sly", patch=flip, fa=150 * pulse(t, tf - 0.2, 0.8) + 20, fb=70)
    dark(c, 0.55)


def c11(f):
    return dict(z=1.05, y=960)


def s12(f):  # boom, night vision
    c, t = f.ctx, f.t
    plate(c, "hold")
    char(f, CAPT, x=800, y=1780, s=1.9, face=-1, expr="shock", hold="sword", fa=40, fb=20, sweat=1)
    char(f, HERO, x=330, y=1780, s=1.9, face=1, expr="grin", patch=1.0, hold="sword", fa=110, fb=-10)
    dark(c, 0.15 * (1 - f.r(0, 0.3)), tint=(0.0, 0.05, 0.02))
    if t < 0.2:
        c.rectangle(-400, -400, 1900, 2800)
        c.set_source_rgba(1, 1, 1, 1 - t / 0.2)
        c.fill()
    pop(c, "BOOM!", 540, 620, f.r(0.0, 0.2), size=150)


def c12(f):
    return dict(z=tween(f.t, 0, f.dur, 1.15, 1.0), shake=12 * pulse(f.t, 0, 0.4))


def s13(f):  # MythBusters tested it
    c, t = f.ctx, f.t
    plate(c, "course")
    char(f, TEST, x=540, y=2080, s=2.4, face=1, expr="smile", patch=0.0, fa=150, fb=30)


def o13(f):
    OV(f)
    tm = f.T.word(0, "MythBusters")
    label(f.ctx, "MYTHBUSTERS, 2007", 540, 330, f.r(tm, tm + 0.25), size=60, color="#ffffff")


def s14(f):  # covered one eye, ran the course
    c, t = f.ctx, f.t
    plate(c, "course")
    char(f, TEST, x=tween(t, 0, f.dur, 360, 640), y=1820, s=1.8, face=1, walk=1.6, expr="neutral", patch=0.0)
    dark(c, 0.75 * f.r(f.T.word(0, "pitch") - 0.1, f.T.word(0, "pitch") + 0.2))


def s15(f):  # normal eye: lost
    c, t = f.ctx, f.t
    plate(c, "course")
    tb = f.T.word(0, "bumping")
    stumble = pulse(t, tb, 0.6)
    p = dict(x=tween(t, 0, f.dur, 480, 620), y=1820, s=1.8, face=1, walk=1.2, expr="worried", patch=0.0,
             tilt=25 * stumble, lean=-15 * stumble, fa=110, fb=0, ba=110, bb=0)
    pts = char(f, TEST, **p)
    dark(c, 0.93)
    eyes_in_dark(c, p, pts, look=math.sin(f.gt * 6))
    pop(c, "BONK!", 720, 980, f.r(tb, tb + 0.15), size=110, color="#ffffff")


def c15(f):
    return dict(z=1.1, shake=10 * pulse(f.t, f.T.word(0, "bumping"), 0.3))


def s16(f):  # flip -> they could see
    c, t = f.ctx, f.t
    plate(c, "course")
    tf = f.T.word(0, "Flip")
    flip = f.r(tf, tf + 0.4)
    char(f, TEST, x=tween(t, 0.5, f.dur, 420, 700), y=1820, s=1.8, face=1, walk=1.8 if t > 0.5 else 0,
         expr="grin" if flip > 0.5 else "neutral", patch=flip, fa=150 * pulse(t, tf - 0.1, 0.5) + 10, fb=60)
    dark(c, 0.93 * (1 - 0.8 * f.r(tf + 0.3, tf + 0.6)), tint=(0.0, 0.04, 0.02))
    k = f.r(f.T.word(0, "see"), f.T.word(0, "see") + 0.2)
    if k > 0:  # drawn checkmark (the font has no tick glyph)
        sc = EASES["back"](k)
        c.save()
        c.translate(780, 820)
        c.scale(sc, sc)
        for col, w in ((INK, 46), (hexc("#5ad16a"), 28)):
            c.move_to(-80, 0)
            c.line_to(-20, 60)
            c.line_to(90, -70)
            c.set_source_rgb(*col)
            c.set_line_width(w)
            c.set_line_cap(1)
            c.set_line_join(1)
            c.stroke()
        c.restore()


def s17(f):  # no proof
    c, t = f.ctx, f.t
    plate(c, "deck")
    char(f, HERO, x=560, y=2160, s=BIG, face=-1, expr="sly", patch=0.0, fa=40, fb=100, ba=40, bb=100,
         tilt=-8)
    tp = f.T.word(0, "prove")
    stamp(c, "NO PROOF", 560, 560, f.r(tp, tp + 0.2), color="#d63c46", size=120)


def c17(f):
    return dict(z=1.0, y=960, shake=8 * pulse(f.t, f.T.word(0, "prove") + 0.2, 0.3))


def s18(f):  # try it tonight
    c, t = f.ctx, f.t
    plate(c, "hold")
    tl = f.T.word(0, "lights")
    ts = f.T.word(0, "switch")
    off = t > tl + 0.15
    p = dict(x=540, y=2200, s=BIG, face=1, expr="wink" if t > ts else "smile",
             patch=f.r(ts, ts + 0.4), fa=150 if t < tl else 30, fb=70)
    pts = char(f, HERO, **p)
    if off and t < ts + 0.3:
        dark(c, 0.95)
        eyes_in_dark(c, p, pts)


def o18(f):
    OV(f)
    ts = f.T.word(0, "switch")
    label(f.ctx, "TRY IT TONIGHT 🏴‍☠️".replace(" 🏴‍☠️", ""), 540, 330, f.r(ts + 0.2, ts + 0.45), size=70)


def c18(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.15), y=960)


SCENES = [
    Scene("hook", [N("That pirate eye patch? There might be a perfectly good eye under it.")], s0, c0, overlay=OV,
          cues=lambda T: [(0.0, "whoosh", 0.4), (T.word(0, "good"), "pop", 0.8)]),
    Scene("attack", [N("Picture it. It's the 1700s, and your ship is under attack.")], s1, c1, overlay=o1,
          trans="whip", cues=lambda T: [(0.0, "waves", 0.5), (T.word(0, "attack") - 0.1, "hit", 1.0),
                                        (T.word(0, "attack") + 0.25, "hit", 0.8)]),
    Scene("sun", [N("Up on deck, the sun is blinding.")], s2, c2, overlay=OV, trans="punch",
          cues=lambda T: [(T.word(0, "blinding"), "reveal", 0.5)]),
    Scene("jump", [N("Then you jump below deck to fight... and it's pitch black.")], s3, c3, overlay=OV,
          trans="whip", cues=lambda T: [(0.0, "whoosh", 0.6), (0.45, "stamp", 0.8), (T.word(0, "black"), "dun", 0.7)]),
    Scene("blind", [N("You can't see a thing.")], s4, c4, overlay=OV, trans="cut",
          cues=lambda T: [(T.dur - 0.5, "boing", 0.8)]),
    Scene("pupil", [N("See, your eyes need time to adjust to the dark.")], s5, c5, overlay=OV, trans="whip",
          cues=lambda T: [(0.3, "pop", 0.6)]),
    Scene("twenty", [N("Up to twenty minutes.")], s6, overlay=OV, trans="punch",
          cues=lambda T: [(0.1 + k * 0.18, "tick", 1.0) for k in range(8)]),
    Scene("fight", [N("In a sword fight, you don't have twenty minutes.")], s7, c7, overlay=OV, trans="whip",
          cues=lambda T: [(T.word(0, "twenty") - 0.2, "clink", 1.0), (T.word(0, "twenty"), "clink", 0.9)]),
    Scene("theory", [N("So, the theory goes, pirates kept one eye covered.")], s8, c8, overlay=o8, trans="whip",
          cues=lambda T: [(T.word(0, "theory"), "pop", 0.7)]),
    Scene("stays", [N("That eye stays in the dark all day.")], s9, c2, overlay=OV, trans="cut",
          cues=lambda T: [(0.2, "pop", 0.6)]),
    Scene("open", [N("On deck, you use the open eye.")], s10, c10, overlay=OV, trans="punch", cues=lambda T: []),
    Scene("flip", [N("Below deck, you flip the patch...")], s11, c11, overlay=OV, trans="whip",
          cues=lambda T: [(T.word(0, "flip"), "zip", 0.8)]),
    Scene("boom", [N("Boom. Instant night vision.")], s12, c12, overlay=OV, trans="cut",
          cues=lambda T: [(0.0, "hit", 1.0), (0.3, "reveal", 0.6)]),
    Scene("myth", [N("MythBusters actually tested this.")], s13, overlay=o13, trans="flash",
          cues=lambda T: [(0.1, "ding", 0.5)]),
    Scene("course", [N("They covered one eye, then ran a pitch-black obstacle course.")], s14, overlay=OV,
          trans="whip", cues=lambda T: [(0.3, "steps", 0.6)]),
    Scene("lost", [N("The normal eye? Lost, bumping into everything.")], s15, c15, overlay=OV, trans="cut",
          cues=lambda T: [(T.word(0, "bumping"), "boing", 0.9), (T.word(0, "bumping") + 0.4, "stamp", 0.6)]),
    Scene("see", [N("Flip the patch? They could see.")], s16, overlay=OV, trans="cut",
          cues=lambda T: [(T.word(0, "Flip"), "zip", 0.8), (T.word(0, "see"), "ding", 0.8)]),
    Scene("proof", [N("Nobody can prove real pirates did it.")], s17, c17, overlay=OV, trans="whip",
          cues=lambda T: [(T.word(0, "prove") + 0.2, "stamp", 1.0)]),
    Scene("try", [N("But try it tonight. Cover one eye, turn off the lights... and switch.")], s18, c18,
          overlay=o18, trans="whip", pad=0.9,
          cues=lambda T: [(T.word(0, "lights") + 0.15, "stamp", 0.5), (T.word(0, "switch"), "reveal", 0.8)]),
]

_i = 0
for _sc in SCENES:
    for _ln in _sc.lines:
        _ln.audio = os.path.join(VOICE, f"line{_i:02d}.mp3")
        _ln.gap = 0.05
        _i += 1
    if _sc is not SCENES[-1]:
        _sc.pad = min(_sc.pad, 0.12)

EPISODE = Episode("pirate_eye_patch", SCENES, music="caper", music_gain=0.14, caption_style="ricks",
                  caption_y=1440, voice_tempo=1.08)
