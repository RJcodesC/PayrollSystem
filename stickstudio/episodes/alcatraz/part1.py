"""The Alcatraz Escape – Part 1 (v2): a full mini-story with a payoff.
Structure learned from top stick-figure explainers: ~2.5 s shots, big characters, dialogue,
reactions, setup -> mockery -> plan -> twist -> payoff -> cliffhanger.
True story (June 1962); sources in ../alcatraz_p1/sources.md."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

import kit  # noqa: E402
from kit import FRANK, JOHN, CLAR, WEST, GUARD, plate, char, world_pt, ov, label, text_center  # noqa: E402
from engine import bg  # noqa: E402
from engine.core import tween, pulse, EASES, clamp, hexc  # noqa: E402
from engine.render import Episode, Scene, N, Say  # noqa: E402

kit.SERIES_TAG[0] = "ALCATRAZ  ·  PART 1"
BIG = 2.7      # medium-shot scale: character ~70% of frame height
OV = lambda f: ov(f)  # noqa: E731


def keys(ctx, x, y, t):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(t * 9)
    ctx.arc(0, 0, 22, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc("#d9b44a"))
    ctx.set_line_width(6)
    ctx.stroke()
    for k in range(3):
        ctx.save()
        ctx.rotate(k * 2.1)
        bg.rect(ctx, 18, -5, 40, 10, "#d9b44a", 3)
        ctx.restore()
    ctx.restore()


# ---------------------------------------------------------------- 1-2 "Nobody escapes the Rock"
def s1(f):
    plate(f.ctx, "cellblock")
    x = tween(f.t, 0, f.dur, 560, 540)
    s = tween(f.t, 0, f.dur, 1.3, 2.0)
    p = dict(x=x, y=tween(f.t, 0, f.dur, 1560, 1760), s=s, face=-1, walk=1.3, expr="smug", fa=110, fb=30)
    pts = char(f, GUARD, **p)
    keys(f.ctx, *world_pt(p, pts["hand_f"]), f.gt)


def s2(f):
    plate(f.ctx, "cellblock")
    t, T = f.t, f.T
    tn = T.word(0, "Rock")
    laugh = f.r(tn + 0.1, tn + 0.3)
    bob = abs(math.sin(f.gt * 14)) * 30 * laugh
    char(f, GUARD, x=560, y=2150 - bob, s=3.2, face=-1, expr="grin" if laugh > 0 else "smug", look=0.6,
         fa=40 + 60 * laugh, fb=90, ba=20, bb=60, tilt=-10 * laugh, squash=0.3 * laugh * math.sin(f.gt * 28))
    if laugh > 0:
        text_center(f.ctx, "HA! HA!", 820, 560 - 20 * math.sin(f.gt * 10), 80, "#ffd84a", stroke=14)


def c2(f):
    return dict(z=tween(f.t, 0, 0.4, 1.25, 1.12, "out"), y=1000, shake=4 * f.r(f.T.word(0, "Rock"), f.dur))


# ---------------------------------------------------------------- 3 stats
def s3(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "island")
    kit.darken(c, 0.35 * f.r(0, 0.6))
    t36 = T.word(0, "Thirty")
    t0 = T.word(1, "officially")
    kit.big_number(c, "36", "TRIED TO ESCAPE", 540, 650, f.r(t36, t36 + 0.3))
    kit.big_number(c, "0", "OFFICIALLY MADE IT", 540, 1060, f.r(t0 - 0.3, t0), "#e04a4a")


def c3(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.15), shake=7 * pulse(f.t, f.T.word(1, "officially"), 0.3))


# ---------------------------------------------------------------- 4 Frank & the vent
def s4(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell_med")
    tv = T.word(0, "vent")
    d = f.r(tv - 0.5, tv)
    char(f, FRANK, x=640, y=2120, s=BIG, face=-1, expr="sly" if t > tv else "thinking", look=-1, lookY=d,
         tilt=-12 * d, fa=20, fb=125)


def o4(f):
    tn = f.T.word(0, "Frank")
    ov(f, lambda f: label(f.ctx, "FRANK MORRIS", 540, 330, f.r(tn, tn + 0.25)))


def c4(f):
    tv = f.T.word(0, "vent")
    return dict(z=tween(f.t, tv - 0.3, f.dur, 1.0, 1.25), x=tween(f.t, tv - 0.3, f.dur, 540, 420),
                y=tween(f.t, tv - 0.3, f.dur, 960, 1150))


# ---------------------------------------------------------------- 5 rotten concrete
def s5(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "vent")
    tr = T.word(0, "rotted")
    poke = pulse(t, tr - 0.2, 0.5)
    kit.big_arm(c, 640 - 80 * poke, 1130, 1400, 1950, holding=False)
    kit.dust_bits(c, 560, 1080, t, tr, 14)
    if t > tr:
        text_center(c, "CRUMBLE", 540, 760, 100 * EASES["back"](f.r(tr, tr + 0.2)) + 1, "#ffd84a", stroke=16)


def c5(f):
    return dict(z=tween(f.t, 0, f.dur, 1.1, 1.3), shake=6 * pulse(f.t, f.T.word(0, "rotted"), 0.35))


# ---------------------------------------------------------------- 6 swipes a spoon
def s6(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "messhall")
    ts = T.word(0, "spoon")
    grab = f.r(ts - 0.35, ts - 0.05)
    hide = f.r(ts + 0.1, ts + 0.4)
    char(f, GUARD, x=900, y=1560, s=1.4, face=1, expr="neutral", look=1)
    p = dict(x=430, y=1950, s=2.4, face=1, expr="sly", look=1 - 2 * hide, lookY=0.3 * (1 - hide),
             fa=70 * grab * (1 - hide) + 10, fb=10 + 70 * hide, lean=10 * grab, sweat=hide)
    pts = char(f, FRANK, **p)
    if t > ts - 0.05:
        kit.spoon(c, *world_pt(p, pts["hand_f"]), 20, 1.6)
    else:
        kit.spoon(c, 690, 1390, 80, 1.6)


def c6(f):
    return dict(z=1.1, x=560, y=1180)


# ---------------------------------------------------------------- 7 scrape every night
def s7(f):
    c, t = f.ctx, f.t
    plate(c, "vent")
    stroke = math.sin(f.gt * 12) * 70
    kit.big_arm(c, 650 + stroke, 1180 + stroke * 0.3, 1400, 2050, ang=-60)
    kit.dust_bits(c, 560, 1200, t, 0.0, 12)
    marks = [(0.0, "DAY 1"), (f.dur * 0.35, "DAY 30"), (f.dur * 0.7, "DAY 120")]
    for i, (tm, lab) in enumerate(marks):
        nxt = marks[i + 1][0] if i + 1 < 3 else f.dur + 1
        if tm <= t < nxt:
            text_center(c, lab, 540, 640, 130 * EASES["back"](f.r(tm, tm + 0.15)) + 1, "#ffffff", stroke=18)


def c7(f):
    return dict(z=1.15 + 0.05 * (f.t > f.dur * 0.35) + 0.05 * (f.t > f.dur * 0.7), shake=4)


# ---------------------------------------------------------------- 8 vacuum-motor drill
def s8(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell_med")
    tv = T.word(0, "vacuum")
    on = t > tv
    p = dict(x=820, y=2120, s=BIG, face=-1, expr="grin" if on else "sly", fa=65, fb=10, ba=60, bb=20,
             lean=10, look=-1, lookY=0.4)
    pts = char(f, FRANK, **p)
    hx, hy = world_pt(p, pts["hand_f"])
    jit = math.sin(f.gt * 60) * 4 if on else 0
    kit.drill(c, hx - 60 + jit, hy + jit, -1.6, f.gt * 40)
    if on:
        kit.sparks(c, hx - 300, hy, f.gt, 14)
        text_center(c, "BZZZZZ", 600, 560, 90, "#ffd84a", stroke=14)


def c8(f):
    return dict(z=1.0, x=560, y=1000, shake=5 * f.r(f.T.word(0, "vacuum"), f.dur))


# ---------------------------------------------------------------- 9 accordion
def s9(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell_med")
    ta = T.word(0, "accordion")
    p = dict(x=470, y=2120, s=BIG, face=1, expr="grin" if t > ta else "sly", fa=60, fb=-20, ba=60, bb=-20,
             tilt=7 * math.sin(f.gt * 3))
    pts = char(f, FRANK, **p)
    hx, hy = world_pt(p, pts["hand_f"])
    if t > ta - 0.3:
        kit.accordion(c, hx - 60, hy, 0.5 + 0.5 * math.sin(f.gt * 6))
        kit.notes(c, hx - 120, hy - 200, f.gt)
        # a guard at the bars, bopping along
        char(f, GUARD, x=tween(t, ta, ta + 0.5, 1400, 1010, "out"), y=1600, s=1.7, face=-1, expr="smile",
             tilt=10 * math.sin(f.gt * 6), jump=abs(math.sin(f.gt * 6)) * 15)


def c9(f):
    return dict(z=1.05, x=600, y=980)


# ---------------------------------------------------------------- 10 the crew
def s10(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell")
    tb = T.word(0, "Anglin")
    tw = T.word(0, "West")
    char(f, FRANK, x=300, y=1480, s=1.7, face=1, expr="smile", look=1)
    for i, (ch, x1, t0) in enumerate(((JOHN, 600, tb), (CLAR, 780, tb + 0.15), (WEST, 950, tw))):
        x = tween(t, t0 - 0.3, t0 + 0.2, 1400, x1, "out")
        char(f, ch, x=x, y=1500 + i * 10, s=1.6, face=-1, expr="grin", fa=150 if t > t0 + 0.3 else 30, fb=20,
             walk=2.0 if t0 - 0.3 < t < t0 + 0.2 else 0)


def o10(f):
    tb, tw = f.T.word(0, "Anglin"), f.T.word(0, "West")
    ov(f, lambda f: (label(f.ctx, "THE ANGLIN BROTHERS", 540, 330, f.r(tb, tb + 0.25), size=48),
                     label(f.ctx, "ALLEN WEST", 540, 440, f.r(tw, tw + 0.25), size=48, color="#ffffff")))


# ---------------------------------------------------------------- 11 the corridor
def s11(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "corridor")
    tr = T.word(0, "roof")
    char(f, FRANK, x=tween(t, 0, f.dur, 430, 560), y=1820, s=1.6, face=1, walk=1.1, expr="shock" if t > tr else "worried",
         lookY=-1 if t > tr - 0.4 else 0, sweat=0.7)
    if t > tr:
        p = EASES["back"](f.r(tr, tr + 0.25))
        text_center(c, "↑ ROOF ↑", 540, 520, 100 * p + 1, "#ffd84a", stroke=16)


def c11(f):
    tr = f.T.word(0, "roof")
    return dict(z=tween(f.t, 0, f.dur, 1.2, 1.05), y=tween(f.t, tr - 0.6, tr, 1250, 880))


# ---------------------------------------------------------------- 12 bed checks
def s12(f):
    c, t = f.ctx, f.t
    plate(c, "cell_night_bed")
    sweep = tween(t, 0.2, f.dur, -0.5, 0.6)
    kit.flashlight(c, -100, 300, 520 + 400 * sweep, 1100 + 300 * sweep, f.r(0.1, 0.3))


def c12(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.1))


# ---------------------------------------------------------------- 13 fake heads
def s13(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell_med")
    ts, tp, th = T.word(0, "soap"), T.word(0, "toilet"), T.word(0, "hair")
    p = dict(x=330, y=2120, s=BIG, face=1, expr="sly" if t < th else "grin", fa=75, fb=10, look=1, lookY=0.4)
    char(f, FRANK, **p)
    c.save()
    c.translate(780, 900)
    c.scale(1.8, 1.8)
    kit.soap(c, -110, 0, f.r(ts, ts + 0.2))
    kit.toilet_paper(c, 0, 0, f.r(tp, tp + 0.2))
    kit.hair_clump(c, 110, 10, f.r(th, th + 0.2))
    c.restore()
    tb = T.word(0, "barbershop")
    if t > tb:
        k = EASES["back"](f.r(tb, tb + 0.35))
        kit.dummy_head(c, 780, 600, 130 * k + 1)
        bg.sparkle_burst(c, 780, 600, f.r(tb, tb + 0.6), n=10, r=220)


def c13(f):
    return dict(z=1.05, x=600, y=980)


# ---------------------------------------------------------------- 14 looks like sleeping men
def s14(f):
    c, t = f.ctx, f.t
    plate(c, "cell_night_bed")
    kit.dummy_head(c, 450, 790, 62, rot=-0.5)
    sweep = tween(t, 0.3, f.dur - 0.3, -0.6, 0.5)
    kit.flashlight(c, -100, 300, 520 + 400 * sweep, 1000 + 300 * sweep, f.r(0.2, 0.4))
    if t > f.dur * 0.55:
        kit.bubble(c, "Zzz...", 680, 560, f.r(f.dur * 0.55, f.dur * 0.55 + 0.2), size=58)


def c14(f):
    return dict(z=tween(f.t, 0, f.dur, 1.1, 1.3), x=tween(f.t, 0, f.dur, 540, 500), y=tween(f.t, 0, f.dur, 960, 860))


# ---------------------------------------------------------------- 15 the night
def s15(f):
    c, t = f.ctx, f.t
    plate(c, "cell_night")
    into = f.r(f.dur * 0.35, f.dur * 0.9, "in")
    s = 1.6 * (1 - 0.75 * into)
    char(f, FRANK, x=tween(t, 0, f.dur, 620, 420), y=tween(t, 0, f.dur, 1560, 1260), s=s, face=-1, walk=1.4,
         expr="worried", look=-1, alpha=1 - into * 0.9)


def c15(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.25), x=tween(f.t, 0, f.dur, 540, 460), y=tween(f.t, 0, f.dur, 960, 1100))


# ---------------------------------------------------------------- 16-17 Allen West is stuck
def s16(f):
    c, t = f.ctx, f.t
    plate(c, "cell_night_med")
    push = math.sin(f.gt * 9)
    char(f, WEST, x=560 + push * 12, y=2120, s=BIG, face=-1, expr="worried" if t < f.dur * 0.5 else "angry",
         lean=20 + push * 6, fa=80, fb=0, ba=70, bb=10, sweat=1, look=-1, lookY=0.6)
    text_center(c, "STUCK!", 760, 560, 110 * EASES["back"](f.r(0.4, 0.6)) + 1, "#e04a4a", stroke=16)


def c16(f):
    return dict(z=1.05, x=520, y=1000, shake=3)


def s17(f):
    c, t = f.ctx, f.t
    plate(c, "corridor")
    kit.darken(c, 0.35)
    char(f, WEST, x=540, y=1830, s=1.7, face=1 if (f.gt % 1.6) < 0.8 else -1, expr="sad", look=0.0)
    if t > f.dur * 0.5:
        text_center(c, "ALONE.", 540, 600, 100 * EASES["back"](f.r(f.dur * 0.5, f.dur * 0.5 + 0.2)) + 1,
                    "#ffffff", stroke=16)


def c17(f):
    return dict(z=tween(f.t, 0, f.dur, 1.25, 1.05))


# ---------------------------------------------------------------- 18 the roof
def s18(f):
    c, t = f.ctx, f.t
    plate(c, "roof")
    kit.searchlight(c, 1150, 300, tween(t, 0, f.dur, 2.4, 3.0), a=0.8)
    for i, ch in enumerate((FRANK, JOHN, CLAR)):
        st = i * 0.35
        x = tween(t, st, st + f.dur * 0.75, -150, 1250)
        char(f, ch, x=x, y=1560 + i * 25, s=1.25, face=1, run=3, expr="worried", lookY=0)


def c18(f):
    return dict(z=1.05, x=540, y=1000)


# ---------------------------------------------------------------- 19 the morning
def s19(f):
    c, t = f.ctx, f.t
    plate(c, "cellblock")
    x = tween(t, 0, f.dur, 560, 560)
    s = tween(t, 0, f.dur, 1.4, 2.1)
    char(f, GUARD, x=x, y=tween(t, 0, f.dur, 1580, 1780), s=s, face=-1, walk=1.4, expr="neutral",
         fa=70, fb=40)


def o19(f):
    ov(f, lambda f: label(f.ctx, "NEXT MORNING", 540, 330, f.r(0, 0.25), color="#ffffff"))


# ---------------------------------------------------------------- 20-21 the head rolls
HEAD_XY = (450, 790)


def s20(f):
    c, t = f.ctx, f.t
    plate(c, "cell_bed")
    kit.dummy_head(c, *HEAD_XY, 62, rot=-0.5)
    reach = EASES["out"](f.r(0.1, f.dur - 0.1))
    kit.big_arm(c, tween(reach, 0, 1, -60, HEAD_XY[0] - 70), tween(reach, 0, 1, 500, HEAD_XY[1] - 40),
                -300, 300, holding=False, sleeve="#2b3a55")


def s21(f):
    c, t = f.ctx, f.t
    plate(c, "cell_bed")
    tr = f.T.word(0, "rolled")
    p = f.r(tr - 0.15, tr + 0.6, "in")
    hx = HEAD_XY[0] - 250 * p
    hy = HEAD_XY[1] + 700 * p - 260 * math.sin(math.pi * p)
    if p >= 1:
        b = f.t - (tr + 0.6)
        hy += -60 * abs(math.sin(b * 8)) * math.exp(-b * 4)
    kit.dummy_head(c, hx, hy, 62, rot=-0.5 - 7 * p)
    kit.big_arm(c, HEAD_XY[0] - 70, HEAD_XY[1] - 40, -300, 300, holding=False, sleeve="#2b3a55")
    if t > tr + 0.3:
        kit.bubble(c, "AAAAAH!!", 560, 420, f.r(tr + 0.3, tr + 0.5), size=78)


def c21(f):
    tr = f.T.word(0, "rolled")
    return dict(z=tween(f.t, tr, tr + 0.6, 1.0, 1.12), shake=14 * pulse(f.t, tr + 0.55, 0.5))


# ---------------------------------------------------------------- 22 lockdown
def s22(f):
    c, t = f.ctx, f.t
    plate(c, "island")
    for i in range(3):
        kit.searchlight(c, 300 + i * 260, 960, -1.2 - 0.6 * math.sin(f.gt * 1.3 + i), 1100, 0.8)


def o22(f):
    kit.siren(f.ctx, f.gt)
    ov(f, lambda f: label(f.ctx, "LOCKDOWN", 540, 560, f.r(0.1, 0.35), color="#e04a4a", tcolor="#ffffff", size=90))


def c22(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.15), shake=3)


# ---------------------------------------------------------------- 23 the cliffhanger
def s23(f):
    c, t = f.ctx, f.t
    plate(c, "island")
    kit.darken(c, 0.55)
    kit.searchlight(c, 540, 960, -1.6 + 0.5 * math.sin(f.gt * 0.8), 1300, 0.6)


def o23(f):
    kit.vignette(f.ctx, 0.85)
    kit.series_tag(f.ctx)
    tp = f.T.word(1, "Part")
    label(f.ctx, "PART 2  →", 540, 640, f.r(tp, tp + 0.3), size=90)


def c23(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.3))


SCENES = [
    Scene("rock_wide", [N("Every guard on Alcatraz loved to say it.")], s1, overlay=OV, pad=0.05,
          cues=lambda T: [(0.0, "waves", 0.4), (0.1, "steps", 0.6)]),
    Scene("rock_cu", [Say(GUARD, "Nobody escapes the Rock.")], s2, c2, overlay=OV, trans="punch", pad=0.6,
          cues=lambda T: [(T.word(0, "Rock") + 0.1, "dun", 0.6)]),
    Scene("stats", [N("Thirty-six men tried."), N("Not one officially made it.", gap=0.1)], s3, c3, overlay=OV,
          trans="whip", pad=0.25, cues=lambda T: [(T.word(0, "Thirty"), "pop", 0.8), (T.word(1, "officially"), "hit", 0.6)]),
    Scene("frank", [N("Then Frank Morris noticed the little vent under his sink.")], s4, c4, overlay=o4,
          trans="whip", pad=0.1, cues=lambda T: [(T.word(0, "Frank"), "pop", 0.7), (T.word(0, "vent"), "ding", 0.4)]),
    Scene("rotten", [N("Salty sea air had rotted the concrete around it.")], s5, c5, overlay=OV, trans="punch",
          pad=0.1, cues=lambda T: [(T.word(0, "rotted"), "scrape", 0.6), (T.word(0, "rotted") + 0.1, "hit", 0.3)]),
    Scene("spoon", [N("So he swiped a spoon,")], s6, c6, overlay=OV, trans="whip", pad=0.1,
          cues=lambda T: [(T.word(0, "spoon") - 0.05, "clink", 1.0), (T.word(0, "spoon") + 0.15, "whoosh", 0.4)]),
    Scene("scrape", [N("and every single night, he scraped.", gap=0.0)], s7, c7, overlay=OV, trans="punch",
          pad=0.5, cues=lambda T: [(0.0, "scrape", 0.9), (0.7, "scrape", 0.9), (1.4, "scrape", 0.9)]),
    Scene("drill", [N("Then he built a drill out of a stolen vacuum cleaner motor.")], s8, c8, overlay=OV,
          trans="whip", pad=0.25, cues=lambda T: [(T.word(0, "vacuum"), "buzz", 0.9), (T.word(0, "vacuum") + 0.5, "buzz", 0.9),
                                                 (T.word(0, "vacuum") + 1.0, "buzz", 0.9)]),
    Scene("accordion", [N("And to hide the noise, he played the accordion.")], s9, c9, overlay=OV, trans="whip",
          pad=0.5, cues=lambda T: [(T.word(0, "accordion") - 0.3, "accordion", 1.0)]),
    Scene("crew", [N("Three more joined in: the Anglin brothers, and Allen West.")], s10, overlay=o10,
          trans="whip", pad=0.2, cues=lambda T: [(T.word(0, "Anglin"), "pop", 0.7), (T.word(0, "West"), "pop", 0.7)]),
    Scene("corridor", [N("Behind the vents, a forgotten corridor led all the way up to the roof.")], s11, c11,
          overlay=OV, trans="fade", pad=0.15, cues=lambda T: [(0.1, "steps", 0.4), (T.word(0, "roof"), "reveal", 0.5)]),
    Scene("bedcheck", [N("But every night, guards checked every bed.")], s12, c12, overlay=OV, trans="cut",
          pad=0.15, cues=lambda T: [(0.1, "steps", 0.6)]),
    Scene("heads", [N("So they made fake heads out of soap, toilet paper, and real hair from the barbershop.")],
          s13, c13, overlay=OV, trans="whip", pad=0.25,
          cues=lambda T: [(T.word(0, w), "pop", 0.7) for w in ("soap", "toilet", "hair")]
          + [(T.word(0, "barbershop"), "reveal", 0.6)]),
    Scene("sleeping", [N("In the dark, they looked just like sleeping men.")], s14, c14, overlay=OV,
          trans="fade", pad=0.3, cues=lambda T: [(0.3, "steps", 0.4)]),
    Scene("night", [N("June eleventh, 1962. Lights out.", spoken="June eleventh, nineteen sixty-two. Lights out.")],
          s15, c15, overlay=OV, trans="flash", pad=0.2, cues=lambda T: [(0.0, "dun", 0.6)]),
    Scene("stuck", [N("But Allen West's vent was stuck.")], s16, c16, overlay=OV, trans="whip", pad=0.25,
          cues=lambda T: [(0.3, "stamp", 0.6), (0.7, "stamp", 0.6), (1.1, "stamp", 0.6)]),
    Scene("alone", [N("By the time he broke through, the others were gone.")], s17, c17, overlay=OV, trans="cut",
          pad=0.3, cues=lambda T: [(T.word(0, "gone"), "fail", 0.5)]),
    Scene("roof", [N("The other three climbed onto the roof and vanished into the night.")], s18, c18, overlay=OV,
          trans="whip", pad=0.15, cues=lambda T: [(0.1, "run", 0.6), (0.9, "run", 0.6), (T.word(0, "vanished"), "whoosh", 0.6)]),
    Scene("morning", [N("Next morning, a guard went to wake Frank Morris.")], s19, overlay=o19, trans="flash",
          pad=0.05, cues=lambda T: [(0.1, "steps", 0.6), (1.0, "steps", 0.6)]),
    Scene("reach", [N("He reached in to shake him,")], s20, overlay=OV, trans="cut", pad=0.0, cues=lambda T: []),
    Scene("roll", [N("and the head rolled right onto the floor.", gap=0.0)], s21, c21, overlay=OV, trans="cut",
          pad=0.9, cues=lambda T: [(T.word(0, "rolled") + 0.55, "hit", 1.0), (T.word(0, "rolled") + 0.6, "stamp", 0.8)]),
    Scene("lockdown", [N("Alcatraz went into full lockdown.")], s22, c22, overlay=o22, trans="flash", pad=0.2,
          cues=lambda T: [(0.0, "whistle", 0.5), (0.5, "whistle", 0.5)]),
    Scene("tease", [N("But how do you cross a freezing bay with no boat?"), N("Part two.", gap=0.3)], s23, c23,
          overlay=o23, trans="cut", pad=0.9, cues=lambda T: [(0.0, "waves", 0.6), (T.word(1, "Part"), "pop", 0.8)]),
]

EPISODE = Episode("alcatraz_part1_v2", SCENES, narrator_voice="am_michael", voices={"guard": "am_eric"},
                  speed=1.2, music="mystery", caption_y=1330)
