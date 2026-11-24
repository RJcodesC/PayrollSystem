"""The Alcatraz Escape – Part 1: The Spoon.
True story (June 1962). 2D stick figures over 3D Blender plates (engine3d/sets.py).
Sources in sources.md. Dramatised visuals; narration sticks to widely reported facts."""
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

PLATES = os.path.join(ROOT, "assets", "plates", "alcatraz")
_plates = {}

FRANK = Character("frank", Look(coat="#8fb3d9", coat_dark="#6b8fb8", hair="side"), seed=0.4)
JOHN = Character("john", Look(coat="#8fb3d9", coat_dark="#6b8fb8", hair="tuft"), seed=1.9)
CLAR = Character("clarence", Look(coat="#8fb3d9", coat_dark="#6b8fb8", hair="curl"), seed=3.3)
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


def big_arm(ctx, hx, hy, from_x, from_y, holding=True, ang=-30):
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
    ctx.set_source_rgb(*hexc("#8fb3d9"))
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


def series_tag(ctx):
    w = 400
    ctx.save()
    ctx.translate(540, 120)
    ctx.rectangle(-w / 2, -38, w, 76)
    ctx.set_source_rgba(0.05, 0.05, 0.06, 0.75)
    ctx.fill()
    text_center(ctx, "ALCATRAZ  ·  PART 1", 0, 0, 40, "#ffd84a")
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


# ------------------------------------------------------------------ scenes
# 1. HOOK – the island
def s_island(f):
    plate(f.ctx, "island")


def s_island_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.12), y=tween(f.t, 0, f.dur, 960, 900))


# 2. "A spoon."
def s_spoon(f):
    c, t = f.ctx, f.t
    plate(c, "vent")
    p = EASES["out"](f.r(0.0, 0.35))
    big_arm(c, tween(t, 0, 0.35, 1300, 690), tween(t, 0, 0.35, 1500, 1180), 1400, 2100, ang=-35)
    bg.sparkle_burst(c, 560, 1000, f.r(0.3, 0.9), color="#ffffff", n=8, r=150)
    _ = p


def s_spoon_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.05, 1.18), shake=10 * pulse(f.t, 0.3, 0.3))


# 3. Imagine you're locked in Alcatraz
def s_block(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cellblock")
    tc = T.word(1, "counting")
    gx = tween(t, 0, f.dur, 640, 560)
    gs = tween(t, 0, f.dur, 1.05, 1.35)
    gy = tween(t, 0, f.dur, 1500, 1620)
    char(f, GUARD, x=gx, y=gy, s=gs, face=-1, walk=1.4, expr="angry", look=-1)
    # tally marks popping as he counts
    for k in range(5):
        tk = tc + k * 0.28
        if t > tk:
            p = EASES["back"](f.r(tk, tk + 0.18))
            c.save()
            c.translate(230 + k * 38, 560)
            c.scale(p, p)
            c.rectangle(-6, -60, 12, 120) if k < 4 else c.rectangle(-90, -8, 180, 16)
            c.set_source_rgb(*hexc("#ffd84a"))
            c.fill_preserve()
            c.set_source_rgb(*INK)
            c.set_line_width(4)
            c.stroke()
            c.restore()


def s_block_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.12, 1.0))


# 4. 36 tried / not one made it
def s_stats(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "island")
    c.rectangle(-200, -200, 1500, 2400)
    c.set_source_rgba(0, 0, 0, 0.45)
    c.fill()
    t36 = T.word(0, "Thirty")
    t0 = T.word(1, "officially")
    big_number(c, "36", "TRIED TO ESCAPE", 540, 650, f.r(t36, t36 + 0.3))
    big_number(c, "0", "OFFICIALLY MADE IT", 540, 1080, f.r(t0 - 0.3, t0), "#e04a4a")


def s_stats_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.15, 1.05), shake=6 * pulse(f.t, f.T.word(1, "officially"), 0.3))


# 5. Frank Morris & the vent
def s_frank(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell")
    tv = T.word(1, "vent")
    look_down = f.r(tv - 0.6, tv)
    char(f, FRANK, x=640, y=1450, s=1.7, face=-1, expr="sly" if t > tv - 0.3 else "thinking",
         look=-1, lookY=look_down * 1.0, tilt=-8 * look_down, fa=20, fb=120)


def s_frank_ov(f):
    tn = f.T.word(0, "Frank")
    ov(f, lambda f: label(f.ctx, "FRANK MORRIS", 540, 330, f.r(tn, tn + 0.25)))


def s_frank_cam(f):
    tv = f.T.word(1, "vent")
    return dict(z=tween(f.t, tv - 0.8, tv, 1.0, 1.35), x=tween(f.t, tv - 0.8, tv, 540, 380),
                y=tween(f.t, tv - 0.8, tv, 960, 1180))


# 6. crumbling concrete
def s_crumble(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "vent")
    tc = T.word(1, "crumbling")
    dust_bits(c, 560, 1040, t, 0.3, 12)
    big_arm(c, 760 + 20 * math.sin(f.gt * 3), 1050, 1400, 1900, holding=False)
    if t > tc:
        text_center(c, "CRACK!", 420, 820, 90 * EASES["back"](f.r(tc, tc + 0.2)) + 1, "#ffd84a", stroke=14)


def s_crumble_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.1, 1.3), shake=5 * pulse(f.t, f.T.word(1, "crumbling"), 0.4))


# 7. steals a spoon
def s_mess(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "messhall")
    ts = T.word(0, "spoon")
    grab = f.r(ts - 0.2, ts + 0.1)
    hide = f.r(ts + 0.35, ts + 0.7)
    char(f, GUARD, x=880, y=1500, s=1.15, face=1, expr="neutral", look=1)
    p = dict(x=480, y=1640, s=1.5, face=1, expr="sly", look=1 - 2 * hide,
             fa=tween(t, ts - 0.2, ts + 0.1, 10, 70) * (1 - hide) + 10 * hide, fb=10 + 60 * hide,
             lean=8 * grab, sweat=f.r(ts + 0.3, ts + 0.5))
    pts = char(f, FRANK, **p)
    if t > ts:
        hx, hy = world_pt(p, pts["hand_f"])
        spoon(c, hx, hy, 20, 1.0)
    else:
        spoon(c, 640, 1360, 80, 1.0)


def s_mess_cam(f):
    ts = f.T.word(0, "spoon")
    return dict(z=tween(f.t, 0, ts, 1.05, 1.25), x=tween(f.t, 0, ts, 540, 560), y=1250)


# 8. scraping every night
def s_scrape(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "vent")
    words = [T.word(1, w) for w in ("Every", "Single", "Night")]
    stroke = math.sin(f.gt * 11) * 60
    big_arm(c, 640 + stroke, 1180 + stroke * 0.3, 1400, 2050, ang=-60)
    dust_bits(c, 560, 1200, t, 0.1, 10)
    labels = ["DAY 1", "DAY 30", "DAY 120"]
    for i, tw in enumerate(words):
        nxt = words[i + 1] if i + 1 < 3 else f.dur
        if tw <= t < nxt:
            text_center(c, labels[i], 540, 640, 120 * EASES["back"](f.r(tw, tw + 0.15)) + 1, "#ffffff", stroke=18)


def s_scrape_cam(f):
    words = [f.T.word(1, w) for w in ("Every", "Single", "Night")]
    return dict(z=1.15 + 0.05 * sum(f.t > w for w in words), shake=sum(5 * pulse(f.t, w, 0.2) for w in words))


# 9. accordion during music hour
def s_music(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell")
    ta = T.word(1, "accordion")
    sq = 0.5 + 0.5 * math.sin(f.gt * 6) if t > ta - 0.3 else 0.5
    p = dict(x=500, y=1450, s=1.7, face=1, expr="grin" if t > ta else "sly", fa=60, fb=-20, ba=60, bb=-20,
             tilt=6 * math.sin(f.gt * 3))
    pts = char(f, FRANK, **p)
    hx, hy = world_pt(p, pts["hand_f"])
    if t > ta - 0.3:
        accordion(c, hx - 30, hy, sq)
        notes(c, hx - 60, hy - 120, f.gt)
    tc = T.word(1, "cover")
    if t > tc:
        char(f, GUARD, x=tween(t, tc, tc + 0.6, 1300, 960), y=1450, s=1.35, face=-1,
             expr="smile", walk=1.4 if t < tc + 0.6 else 0, tilt=8 * math.sin(f.gt * 3))


def s_music_cam(f):
    return dict(z=1.1, x=600, y=1000)


# 10. the Anglin brothers
def s_brothers(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell")
    tb = T.word(0, "Anglin")
    char(f, FRANK, x=330, y=1450, s=1.6, face=1, expr="smile", look=1)
    for i, (ch, x0, x1) in enumerate(((JOHN, 1400, 700), (CLAR, 1500, 900))):
        st = tb + i * 0.2
        x = tween(t, st, st + 0.5, x0, x1, "out")
        p = dict(x=x, y=1460 + i * 20, s=1.55, face=-1, expr="grin", fa=80, fb=40,
                 walk=1.8 if st < t < st + 0.5 else 0)
        pts = char(f, ch, **p)
        hx, hy = world_pt(p, pts["hand_f"])
        if t > st:
            spoon(c, hx, hy, -30, 1.0)


def s_brothers_ov(f):
    tb = f.T.word(0, "Anglin")
    ov(f, lambda f: label(f.ctx, "JOHN & CLARENCE ANGLIN", 540, 330, f.r(tb, tb + 0.25), size=48))


def s_brothers_cam(f):
    return dict(z=1.05, x=600)


# 11. the hidden corridor
def s_corridor(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "corridor")
    tr = T.word(1, "roof")
    char(f, FRANK, x=tween(t, 0, f.dur, 460, 540), y=1760, s=1.3, face=1, walk=1.0, expr="shock" if t > tr else "worried",
         look=0, lookY=-1 if t > tr - 0.5 else 0, sweat=0.7)
    if t > tr:
        p = EASES["back"](f.r(tr, tr + 0.25))
        c.save()
        c.translate(540, 520)
        c.scale(p, p)
        c.move_to(-60, 40)
        c.line_to(0, -40)
        c.line_to(60, 40)
        c.set_source_rgb(*hexc("#ffd84a"))
        c.set_line_width(26)
        c.stroke()
        c.restore()
        text_center(c, "ROOF", 540, 640, 70 * p + 1, "#ffd84a", stroke=12)


def s_corridor_cam(f):
    tr = f.T.word(1, "roof")
    return dict(z=tween(f.t, 0, f.dur, 1.15, 1.05), y=tween(f.t, tr - 0.8, tr, 1200, 900))


# 12. cliffhanger – the bed check
def s_check(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell")
    c.rectangle(-200, -200, 1500, 2400)
    c.set_source_rgba(0.02, 0.03, 0.08, 0.55)
    c.fill()
    te = T.word(1, "empty")
    gx = 280
    char(f, GUARD, x=gx, y=1520, s=1.45, face=1, expr="angry", look=1, fa=80, fb=-10)
    flashlight(c, 300, 1150, 900, 1250, f.r(0.2, 0.5))
    if t > te:
        text_center(c, "EMPTY BED", 840, 1030, 70 * EASES["back"](f.r(te, te + 0.2)) + 1, "#e04a4a", stroke=12)
        text_center(c, "= GAME OVER", 840, 1110, 56 * EASES["back"](f.r(te + 0.3, te + 0.5)) + 1, "#ffffff", stroke=10)


def s_check_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.0, 1.15), x=620)


# 13. the tease
def s_tease(f):
    c, t, T = f.ctx, f.t, f.T
    plate(c, "cell")
    c.rectangle(-200, -200, 1500, 2400)
    c.set_source_rgba(0, 0, 0, 0.55 + 0.3 * f.r(T.word(0, "creeps"), f.dur))
    c.fill()
    # a "sleeping" shape in the bed, with a head that is just a little too still...
    c.save()
    c.translate(850, 1150)
    c.arc(0, 0, 55, 0, 2 * math.pi)
    c.set_source_rgb(*hexc("#e8dcc8"))
    c.fill_preserve()
    c.set_source_rgb(*INK)
    c.set_line_width(6)
    c.stroke()
    if t > T.word(0, "creeps"):
        for ex in (-18, 18):
            c.arc(ex, -5, 9, 0, 2 * math.pi)
            c.set_source_rgb(1, 1, 1)
            c.fill_preserve()
            c.set_source_rgb(*INK)
            c.set_line_width(3)
            c.stroke()
            c.arc(ex, -5, 3, 0, 2 * math.pi)
            c.fill()
    c.restore()


def s_tease_ov(f):
    vignette(f.ctx, 0.8)
    series_tag(f.ctx)
    tp = f.T.word(1, "Part")
    p = f.r(tp, tp + 0.3)
    if p > 0:
        label(f.ctx, "PART 2  →", 540, 560, p, size=80)


def s_tease_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.1, 1.45), x=tween(f.t, 0, f.dur, 640, 820), y=tween(f.t, 0, f.dur, 1000, 1100))


SCENES = [
    Scene("hook", [N("The most escape-proof prison in America had one weakness.")], s_island, s_island_cam,
          overlay=lambda f: ov(f), cues=lambda T: [(0.0, "waves", 0.7), (0.1, "dun", 0.5)], pad=0.15),
    Scene("spoon", [N("A spoon.")], s_spoon, s_spoon_cam, overlay=lambda f: ov(f), trans="punch",
          cues=lambda T: [(0.3, "clink", 1.0), (0.3, "hit", 0.6)], pad=0.6),
    Scene("block", [N("Imagine you're locked in Alcatraz."),
                    N("Freezing water on every side, and guards counting you over and over, every single day.")],
          s_block, s_block_cam, overlay=lambda f: ov(f), trans="whip",
          cues=lambda T: [(0.2, "steps", 0.5), (1.2, "steps", 0.5)]
          + [(T.word(1, "counting") + k * 0.28, "tick", 1.0) for k in range(5)], pad=0.2),
    Scene("stats", [N("Thirty-six men tried to escape."), N("Not one officially made it.", gap=0.2)],
          s_stats, s_stats_cam, overlay=lambda f: ov(f), trans="flash",
          cues=lambda T: [(T.word(0, "Thirty"), "pop", 0.8), (T.word(1, "officially"), "dun", 0.8)], pad=0.3),
    Scene("frank", [N("So in 1962, a prisoner named Frank Morris stared at the one thing nobody watched,",
                      spoken="So in nineteen sixty-two, a prisoner named Frank Morris stared at the one thing nobody watched,"),
                    N("the little air vent under his sink.", gap=0.05)],
          s_frank, s_frank_cam, overlay=s_frank_ov, trans="whip",
          cues=lambda T: [(T.word(0, "Frank"), "pop", 0.7), (T.word(1, "vent"), "ding", 0.5)], pad=0.2),
    Scene("crumble", [N("The salty sea air had been eating that concrete for years."), N("It was crumbling.")],
          s_crumble, s_crumble_cam, overlay=lambda f: ov(f), trans="punch",
          cues=lambda T: [(0.3, "scrape", 0.5), (T.word(1, "crumbling"), "hit", 0.4)], pad=0.2),
    Scene("mess", [N("So he stole a spoon from the dining hall,")], s_mess, s_mess_cam, overlay=lambda f: ov(f),
          trans="whip", cues=lambda T: [(T.word(0, "spoon"), "clink", 0.9), (T.word(0, "spoon") + 0.4, "whoosh", 0.4)],
          pad=0.15),
    Scene("scrape", [N("and started scraping."), N("Every. Single. Night.", gap=0.15)], s_scrape, s_scrape_cam,
          overlay=lambda f: ov(f), trans="punch",
          cues=lambda T: [(0.1, "scrape", 0.9), (0.8, "scrape", 0.9)]
          + [(T.word(1, w), "stamp", 0.6) for w in ("Every", "Single", "Night")], pad=0.3),
    Scene("music", [N("But scraping makes noise."),
                    N("So during music hour, he played the accordion to cover the sound.", gap=0.15)],
          s_music, s_music_cam, overlay=lambda f: ov(f), trans="whip",
          cues=lambda T: [(0.2, "scrape", 0.7), (T.word(1, "accordion") - 0.3, "accordion", 1.0),
                          (T.word(1, "accordion") + 1.7, "accordion", 0.9)], pad=0.2),
    Scene("brothers", [N("Next door, the Anglin brothers were digging too.")], s_brothers, s_brothers_cam,
          overlay=s_brothers_ov, trans="whip",
          cues=lambda T: [(T.word(0, "brothers"), "pop", 0.7), (T.word(0, "digging"), "scrape", 0.6)], pad=0.6),
    Scene("corridor", [N("Behind the vents was a dark, forgotten corridor full of pipes..."),
                       N("and it led all the way up to the roof.", gap=0.1)],
          s_corridor, s_corridor_cam, overlay=lambda f: ov(f), trans="fade",
          cues=lambda T: [(0.2, "steps", 0.4), (T.word(1, "roof"), "reveal", 0.6)], pad=0.2),
    Scene("check", [N("There was just one problem."),
                    N("Every night, guards checked every bed. And an empty bed meant game over.", gap=0.1)],
          s_check, s_check_cam, overlay=lambda f: ov(f), trans="flash",
          cues=lambda T: [(0.2, "steps", 0.6), (T.word(1, "empty"), "dun", 0.8)], pad=0.2),
    Scene("tease", [N("So they built something that still creeps people out today."), N("Part two.", gap=0.3)],
          s_tease, s_tease_cam, overlay=s_tease_ov, trans="cut",
          cues=lambda T: [(T.word(0, "creeps"), "hit", 0.8), (T.word(1, "Part"), "pop", 0.8)], pad=1.0),
]

EPISODE = Episode("alcatraz_part1", SCENES, narrator_voice="am_michael", speed=1.1, music="mystery",
                  caption_y=1330)
