"""The 3AM Elevator – Part 3 (viewers commented "break the glass" -> the key leads to the stairs).
Original interactive stick-figure horror (PG: suspense, no gore). Fiction."""
import math
import os
import random
import sys

import cairo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from engine import bg  # noqa: E402
from engine.core import tween, pulse, EASES, clamp, hexc, noise1  # noqa: E402
from engine.render import Episode, Scene, N, Say  # noqa: E402
from engine.rig import Character, Look, INK  # noqa: E402
from engine.text import text_center, text_width  # noqa: E402

KID = Character("kid", Look(stick=True, limb="#f2f2f2", skin="#f2f2f2"), seed=0.8)

# ------------------------------------------------------------------ stairwell set
X0, Y0, X1, Y1 = -60, 1700, 1140, 800       # stair line (bottom-left -> top-right)
SLOPE = (Y0 - Y1) / (X1 - X0)
STEP_W = 64


def stair_y(x):
    return Y0 - (x - X0) * SLOPE


def stairwell(ctx, t, sign="13"):
    def static(c):
        g = cairo.LinearGradient(0, 0, 0, 1920)
        g.add_color_stop_rgb(0, *hexc("#1c2427"))
        g.add_color_stop_rgb(1, *hexc("#0c1012"))
        c.rectangle(-200, -200, 1500, 2400)
        c.set_source(g)
        c.fill()
        # concrete wall blocks
        c.set_source_rgba(1, 1, 1, 0.045)
        c.set_line_width(3)
        for r in range(-2, 22):
            y = r * 110
            c.move_to(-200, y)
            c.line_to(1300, y)
            off = 120 if r % 2 else 0
            for k in range(-1, 6):
                c.move_to(k * 240 + off, y)
                c.line_to(k * 240 + off, y + 110)
        c.stroke()
        # upper landing + door with light under it (top right)
        c.rectangle(760, 420, 260, 380)
        c.set_source_rgb(*hexc("#2a3438"))
        c.fill_preserve()
        c.set_source_rgb(*INK)
        c.set_line_width(7)
        c.stroke()
        c.arc(980, 620, 10, 0, 2 * math.pi)
        c.set_source_rgb(*hexc("#8a949a"))
        c.fill()
        # floor sign frame (left wall)
        c.rectangle(130, 430, 250, 190)
        c.set_source_rgb(*hexc("#20292c"))
        c.fill_preserve()
        c.set_source_rgb(*hexc("#5b666b"))
        c.set_line_width(6)
        c.stroke()
        text_center(c, "FLOOR", 255, 470, 34, "#7d898e")
        # stairs: filled mass + step edges
        c.new_path()
        c.move_to(X0, Y0)
        x, y = X0, Y0
        while x < X1:
            c.line_to(x, y - STEP_W * SLOPE)
            x += STEP_W
            y -= STEP_W * SLOPE
            c.line_to(x, y)
        c.line_to(X1 + 200, y)
        c.line_to(X1 + 200, 2300)
        c.line_to(X0 - 200, 2300)
        c.close_path()
        c.set_source_rgb(*hexc("#3a4448"))
        c.fill_preserve()
        c.set_source_rgb(*INK)
        c.set_line_width(6)
        c.stroke()
        # stair underside shading
        c.move_to(X0, Y0 + 200)
        c.line_to(X1 + 200, Y1 + 200)
        c.line_to(X1 + 200, 2300)
        c.line_to(X0 - 200, 2300)
        c.close_path()
        c.set_source_rgba(0, 0, 0, 0.35)
        c.fill()
        # landing floor under the door
        c.rectangle(740, 800, 600, 30)
        c.set_source_rgb(*hexc("#3a4448"))
        c.fill_preserve()
        c.set_source_rgb(*INK)
        c.stroke()
        # railing
        c.set_line_width(9)
        c.set_source_rgb(*hexc("#7d898e"))
        c.move_to(X0, Y0 - 230)
        c.line_to(X1, Y1 - 230)
        c.stroke()
        c.set_line_width(6)
        for k in range(0, 20):
            px = X0 + 40 + k * STEP_W * 2
            if px > X1:
                break
            c.move_to(px, stair_y(px) - 8)
            c.line_to(px, stair_y(px) - 230)
        c.stroke()
        # lamp
        c.rectangle(470, 140, 140, 26)
        c.set_source_rgb(*hexc("#c9d6d9"))
        c.fill()

    bg.blit(ctx, "stairwell", static)
    # light under the door (flickers subtly)
    a = 0.75 + 0.25 * noise1(t * 3, 2)
    ctx.rectangle(764, 786, 252, 12)
    ctx.set_source_rgba(*hexc("#ffe7a8"), a)
    ctx.fill()
    g = cairo.LinearGradient(0, 800, 0, 700)
    g.add_color_stop_rgba(0, *hexc("#ffe7a8"), 0.25 * a)
    g.add_color_stop_rgba(1, *hexc("#ffe7a8"), 0.0)
    ctx.rectangle(740, 700, 300, 100)
    ctx.set_source(g)
    ctx.fill()
    # floor number (red, flickers)
    flick = 1.0 if noise1(t * 9, 4) > -0.75 else 0.35
    text_center(ctx, sign, 255, 555, 96, (0.9 * flick, 0.15 * flick, 0.15 * flick))
    # spotlight cone + dust
    g = cairo.LinearGradient(0, 160, 0, 1700)
    g.add_color_stop_rgba(0, *hexc("#cfe5ea"), 0.22)
    g.add_color_stop_rgba(1, *hexc("#cfe5ea"), 0.0)
    ctx.move_to(480, 165)
    ctx.line_to(600, 165)
    ctx.line_to(1000, 1700)
    ctx.line_to(80, 1700)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()
    rng = random.Random(7)
    for i in range(40):
        x = (rng.uniform(80, 1000) + t * rng.uniform(-8, 8)) % 1080
        y = (rng.uniform(200, 1700) + t * rng.uniform(5, 18)) % 1700
        ctx.arc(x, y, rng.uniform(1.5, 3.5), 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.25)
        ctx.fill()


def creature(ctx, x, y, s, t, reach=0.0, alpha=1.0, grin=1.0):
    """Tall thin shadow creature: black stick limbs, white hollow eyes, wide grin."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if alpha < 1:
        ctx.push_group()
    sway = math.sin(t * 1.3) * 3
    hip = (0, -330)
    neck = (sway, -650)
    ctx.set_line_cap(1)
    ctx.set_line_join(1)

    def stroke(pts, w):
        for col, ww in (((0.35, 0.4, 0.42), w + 5), ((0.02, 0.02, 0.03), w)):
            ctx.set_source_rgb(*col)
            ctx.set_line_width(ww)
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            ctx.stroke()

    stroke([(-40, 0), (-30, -170), hip, (30, -170), (44, 0)], 14)
    stroke([hip, neck], 16)
    # arms: one hangs, one reaches forward (to the left, toward the kid) by `reach`
    stroke([(neck[0], neck[1] + 30), (-50, -440), (-60, -230)], 12)
    ra = -reach * 1.1
    elbow = (neck[0] - 80 - 130 * reach, neck[1] + 120 - 60 * reach)
    hand = (elbow[0] - 70 - 170 * reach, elbow[1] + 160 - 230 * reach)
    stroke([(neck[0], neck[1] + 30), elbow, hand], 12)
    for k in range(4):  # long fingers
        a = math.radians(200 + k * 22 + ra * 10)
        stroke([hand, (hand[0] + math.cos(a) * 55, hand[1] + math.sin(a) * 55)], 5)
    # head
    hx, hy = neck[0] - 6, neck[1] - 92
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(math.radians(-8 + math.sin(t * 0.9) * 5))
    ctx.scale(0.86, 1.0)
    ctx.arc(0, 0, 100, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(0.02, 0.02, 0.03)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.35, 0.4, 0.42)
    ctx.set_line_width(5)
    ctx.stroke()
    for ex in (-34, 30):
        ctx.save()
        ctx.translate(hx + ex, hy - 18)
        ctx.scale(1, 1.25)
        ctx.arc(0, 0, 21, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(0.95, 0.95, 0.95)
        ctx.fill()
        ctx.arc(hx + ex - 5, hy - 16, 6, 0, 2 * math.pi)
        ctx.set_source_rgb(0.02, 0.02, 0.03)
        ctx.fill()
    if grin > 0:
        ctx.save()
        ctx.translate(hx - 2, hy + 38)
        w = 58 * grin
        ctx.move_to(-w, -8)
        ctx.curve_to(-w * 0.5, 30, w * 0.5, 30, w, -8)
        ctx.curve_to(w * 0.5, 12, -w * 0.5, 12, -w, -8)
        ctx.close_path()
        ctx.set_source_rgb(0.95, 0.95, 0.95)
        ctx.fill()
        ctx.set_source_rgb(0.02, 0.02, 0.03)
        ctx.set_line_width(3)
        for k in range(-3, 4):
            ctx.move_to(k * w / 4, 0)
            ctx.line_to(k * w / 4, 20)
        ctx.stroke()
        ctx.restore()
    if alpha < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(alpha)
    ctx.restore()


def wall_shadow(ctx, x, y, h, a):
    """Huge distorted creature shadow cast on the wall."""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(h / 900, h / 900)
    ctx.set_source_rgba(0, 0, 0, 0.82 * a)
    ctx.move_to(-50, 0)
    ctx.line_to(-20, -500)
    ctx.line_to(-160, -320)
    ctx.line_to(-180, -300)
    ctx.line_to(-10, -560)
    ctx.line_to(-15, -700)
    ctx.arc(0, -790, 95, math.radians(100), math.radians(440))
    ctx.line_to(15, -700)
    ctx.line_to(20, -560)
    ctx.line_to(60, -340)
    ctx.line_to(30, -500)
    ctx.line_to(50, 0)
    ctx.close_path()
    ctx.fill()
    ctx.restore()


def darkness(ctx, a):
    if a > 0:
        ctx.rectangle(-300, -300, 1700, 2600)
        ctx.set_source_rgba(0, 0, 0, clamp(a))
        ctx.fill()


def vignette(ctx, red=0.0):
    g = cairo.RadialGradient(540, 960, 380, 540, 960, 1250)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.8)
    ctx.rectangle(0, 0, 1080, 1920)
    ctx.set_source(g)
    ctx.fill()
    if red > 0:
        ctx.rectangle(0, 0, 1080, 1920)
        ctx.set_source_rgba(0.55, 0.05, 0.08, 0.35 * red)
        ctx.fill()


def hallway(ctx, t):
    """Dark elevator lobby on floor 13 with a BREAK GLASS box."""
    def static(c):
        c.rectangle(-200, -200, 1500, 2400)
        c.set_source_rgb(*hexc("#151c1f"))
        c.fill()
        c.set_source_rgba(1, 1, 1, 0.04)
        c.set_line_width(3)
        for k in range(-1, 10):
            c.move_to(k * 140, -200)
            c.line_to(k * 140, 1500)
        c.stroke()
        # elevator doors (closed)
        c.rectangle(170, 520, 520, 980)
        c.set_source_rgb(*hexc("#0b0f10"))
        c.fill()
        for x in (190, 435):
            c.rectangle(x, 540, 235, 960)
            g = cairo.LinearGradient(x, 0, x + 235, 0)
            g.add_color_stop_rgb(0, *hexc("#6f7b80"))
            g.add_color_stop_rgb(0.5, *hexc("#9aa6ab"))
            g.add_color_stop_rgb(1, *hexc("#5d686c"))
            c.set_source(g)
            c.fill()
        c.rectangle(330, 420, 200, 80)
        c.set_source_rgb(*hexc("#0b0f10"))
        c.fill()
        # floor
        c.rectangle(-200, 1500, 1500, 900)
        c.set_source_rgb(*hexc("#20292c"))
        c.fill()
        c.move_to(-200, 1500)
        c.line_to(1300, 1500)
        c.set_source_rgb(*INK)
        c.set_line_width(6)
        c.stroke()
        # break-glass box frame
        c.rectangle(790, 760, 190, 250)
        c.set_source_rgb(*hexc("#c8313a"))
        c.fill_preserve()
        c.set_source_rgb(*INK)
        c.set_line_width(6)
        c.stroke()
        text_center(c, "BREAK", 885, 800, 34, "#ffffff")
        text_center(c, "GLASS", 885, 840, 34, "#ffffff")

    bg.blit(ctx, "hallway13", static)
    flick = 1.0 if noise1(t * 9, 4) > -0.75 else 0.35
    text_center(ctx, "13", 430, 460, 62, (0.9 * flick, 0.15 * flick, 0.15 * flick))
    g = cairo.LinearGradient(0, 100, 0, 1500)
    g.add_color_stop_rgba(0, *hexc("#cfe5ea"), 0.2)
    g.add_color_stop_rgba(1, *hexc("#cfe5ea"), 0.0)
    ctx.move_to(380, 100)
    ctx.line_to(700, 100)
    ctx.line_to(1100, 1500)
    ctx.line_to(80, 1500)
    ctx.close_path()
    ctx.set_source(g)
    ctx.fill()


def glass_pane(ctx, broken, t_since):
    """Glass of the break-glass box; shatters into flying shards."""
    x0, y0, w, h = 810, 870, 150, 120
    if not broken:
        ctx.rectangle(x0, y0, w, h)
        ctx.set_source_rgba(0.8, 0.95, 1.0, 0.45)
        ctx.fill_preserve()
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(3)
        ctx.stroke()
        ctx.move_to(x0 + 20, y0 + 30)
        ctx.line_to(x0 + 60, y0 + 10)
        ctx.stroke()
        return
    rng = random.Random(3)
    for i in range(16):
        sx, sy = x0 + rng.uniform(0, w), y0 + rng.uniform(0, h)
        vx, vy = rng.uniform(-500, 300), rng.uniform(-700, -100)
        tt = min(t_since, 1.4)
        px, py = sx + vx * tt, sy + vy * tt + 1400 * tt * tt
        if py > 1500:
            py = 1500
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(rng.uniform(0, 6) + tt * rng.uniform(-8, 8))
        sz = rng.uniform(10, 26)
        ctx.move_to(-sz, -sz * 0.4)
        ctx.line_to(sz * 0.8, -sz * 0.6)
        ctx.line_to(sz * 0.2, sz)
        ctx.close_path()
        ctx.set_source_rgba(0.85, 0.97, 1.0, 0.8)
        ctx.fill_preserve()
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.restore()


def key_with_tag(ctx, x, y, s, swing=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.rotate(swing)
    ctx.set_line_width(5)
    ctx.set_source_rgb(*hexc("#d9b44a"))
    ctx.arc(0, 0, 22, 0, 2 * math.pi)
    ctx.stroke()
    ctx.rectangle(-5, 20, 10, 80)
    ctx.rectangle(5, 70, 18, 9)
    ctx.rectangle(5, 88, 14, 9)
    ctx.fill()
    ctx.move_to(0, -22)
    ctx.line_to(-30, -60)
    ctx.set_source_rgb(*hexc("#c9c9c9"))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.save()
    ctx.translate(-70, -90)
    ctx.rotate(-0.25)
    ctx.rectangle(-75, -32, 150, 64)
    ctx.set_source_rgb(*hexc("#efe6c9"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.stroke()
    text_center(ctx, "STAIRS", 0, 2, 34, "#b8333a")
    ctx.restore()
    ctx.restore()


# ------------------------------------------------------------------ screen-space UI (matches Part 1)
def header(ctx):
    ctx.rectangle(0, 0, 1080, 250)
    ctx.set_source_rgba(0, 0, 0, 0.85)
    ctx.fill()
    text_center(ctx, "THE 3AM ELEVATOR", 540, 85, 70, "#ffffff")
    text_center(ctx, "PART 3 · BREAK THE GLASS", 540, 170, 62, "#f2c84b")


def rule_box(ctx, n, line1, line2, p):
    if p <= 0:
        return
    s = EASES["back"](clamp(p))
    ctx.save()
    ctx.translate(540, 330)
    ctx.scale(s, s)
    w, h = 900, 130
    ctx.rectangle(-w / 2, -h / 2, w, h)
    ctx.set_source_rgba(0.04, 0.04, 0.05, 0.92)
    ctx.fill_preserve()
    ctx.set_source_rgb(*hexc("#d63c46"))
    ctx.set_line_width(5)
    ctx.stroke()
    ctx.rectangle(-w / 2, -h / 2, 160, h)
    ctx.set_source_rgb(*hexc("#d63c46"))
    ctx.fill()
    text_center(ctx, "RULE", -w / 2 + 80, -28, 30, "#ffffff")
    text_center(ctx, str(n), -w / 2 + 80, 22, 66, "#ffffff")
    text_center(ctx, line1, 80, -22, 40, "#ffffff")
    text_center(ctx, line2, 80, 28, 40, "#f2c84b")
    ctx.restore()


def choice_buttons(ctx, p, t):
    if p <= 0:
        return
    for i, (letter, l1, l2, col) in enumerate((("A", "KEEP", "CLIMBING", "#d63c46"), ("B", "TURN", "AROUND", "#2f6fe0"))):
        pp = EASES["back"](clamp(p * 1.4 - i * 0.25))
        if pp <= 0:
            continue
        beat = 1 + 0.04 * max(0, math.sin(t * 7 + i * 1.6))
        ctx.save()
        ctx.translate(290 + i * 500, 1470)
        ctx.scale(pp * beat, pp * beat)
        w, h = 440, 170
        r = 26
        ctx.new_path()
        ctx.arc(-w / 2 + r, -h / 2 + r, r, math.pi, 1.5 * math.pi)
        ctx.arc(w / 2 - r, -h / 2 + r, r, 1.5 * math.pi, 2 * math.pi)
        ctx.arc(w / 2 - r, h / 2 - r, r, 0, 0.5 * math.pi)
        ctx.arc(-w / 2 + r, h / 2 - r, r, 0.5 * math.pi, math.pi)
        ctx.close_path()
        ctx.set_source_rgb(*hexc(col))
        ctx.fill_preserve()
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(6)
        ctx.stroke()
        text_center(ctx, letter, -w / 2 + 75, 4, 120, "#ffffff")
        text_center(ctx, l1, 60, -28, 46, "#ffffff")
        text_center(ctx, l2, 60, 28, 46, "#ffffff")
        ctx.restore()


# ------------------------------------------------------------------ helpers
def kid_on_stairs(f, x, **kw):
    pose = dict(x=x, y=stair_y(x) - 6, s=1.55, face=1, lean=6)
    pose.update(kw)
    return f.char(KID, pose)


def overlay_std(f, rule=None, red=0.0):
    vignette(f.ctx, red)
    header(f.ctx)
    if rule:
        n, a, b, t0 = rule
        rule_box(f.ctx, n, a, b, f.r(t0, t0 + 0.25))


# 0a. HOOK – break the glass
def s0_draw(f):
    c, t, T = f.ctx, f.t, f.T
    hallway(c, f.gt)
    tb = T.word(0, "break")
    hit = T.word(0, "glass")
    wind = f.r(tb - 0.35, hit - 0.08)
    strike = f.r(hit - 0.08, hit, "in")
    broken = t >= hit
    glass_pane(c, broken, t - hit)
    if broken:
        key_with_tag(c, 885, 930, 0.7, math.sin((t - hit) * 6) * 0.3 * math.exp(-(t - hit) * 1.5))
    f.char(KID, dict(x=620, y=1500, s=1.5, face=1, lean=10 * strike - 6 * wind,
                     fa=tween(t, tb - 0.35, hit - 0.08, 10, 150) * (1 - strike) + 95 * strike,
                     fb=tween(t, tb - 0.35, hit - 0.08, 12, 60) * (1 - strike) - 5 * strike,
                     expr="angry" if t < hit + 0.3 else "shock", sweat=1))


def s0_cam(f):
    hit = f.T.word(0, "glass")
    return dict(z=tween(f.t, 0, hit, 1.2, 1.45), x=tween(f.t, 0, hit, 560, 760), y=tween(f.t, 0, hit, 1150, 1000),
                shake=16 * pulse(f.t, hit, 0.35))


# 0b. THE KEY
def s0b_draw(f):
    c, t, T = f.ctx, f.t, f.T
    hallway(c, f.gt)
    glass_pane(c, True, 5)
    tk = T.word(0, "key")
    grab = f.r(tk, tk + 0.4)
    kx = tween(t, tk, tk + 0.4, 885, 860)
    f.char(KID, dict(x=620, y=1500, s=1.5, face=1, fa=95 * grab + 30 * (1 - grab), fb=-5, expr="worried",
                     look=1, lookY=-0.3, sweat=1))
    key_with_tag(c, kx, tween(t, tk, tk + 0.4, 930, 1000), tween(t, 0, 0.6, 0.7, 1.0), math.sin(f.gt * 3) * 0.15)


def s0b_cam(f):
    tt = f.T.word(0, "STAIRS")
    return dict(z=tween(f.t, 0, tt, 1.6, 2.4), x=tween(f.t, 0, tt, 780, 830), y=tween(f.t, 0, tt, 1000, 920))


# 1. running up
def s1_draw(f):
    c, t = f.ctx, f.t
    stairwell(c, f.gt)
    x = tween(t, 0, f.dur, 60, 330, "out")
    kid_on_stairs(f, x, run=2.6 if t < f.dur - 0.3 else 0, expr="shock", sweat=1)


def s1_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.25, 1.1), x=tween(f.t, 0, f.dur, 360, 480), y=1180,
                shake=3)


# 2. FLOOR 13
def s2_draw(f):
    c, t, T = f.ctx, f.t, f.T
    stairwell(c, f.gt)
    kid_on_stairs(f, 330, expr="shock" if t > T.word(0, "13") else "worried", look=-1, lookY=-1, tilt=-10,
                  fa=40, fb=60)


def s2_cam(f):
    t13 = f.T.word(0, "13")
    return dict(z=tween(f.t, 0, t13, 1.1, 1.9, "inout"), x=tween(f.t, 0, t13, 480, 300),
                y=tween(f.t, 0, t13, 1180, 640), shake=10 * pulse(f.t, t13, 0.4))


# 3. RULE 4 + counting
def s3_draw(f):
    c, t, T = f.ctx, f.t, f.T
    stairwell(c, f.gt)
    counts = [T.word(1, w) for w in ("Eleven", "Twelve", "Thirteen")]
    n = sum(1 for ct in counts if t >= ct)
    x = 330 + n * STEP_W * 1.0 + (STEP_W * f.r(counts[n] - 0.25, counts[n]) if n < 3 else 0)
    stepping = any(ct - 0.25 < t < ct for ct in counts)
    kid_on_stairs(f, x, walk=2.2 if stepping else 0, expr="worried", look=1, lookY=-0.6)


def s3_cam(f):
    return dict(z=1.25, x=520, y=1150)


def s3_over(f):
    overlay_std(f, rule=(4, "COUNT EVERY STEP", "OUT LOUD", f.T.word(0, "four")))


# 4. SIGN STILL 13
def s4_draw(f):
    c, t, T = f.ctx, f.t, f.T
    stairwell(c, f.gt)
    kid_on_stairs(f, 330 + 3 * STEP_W, expr="shock", look=-1, lookY=-0.8, sweat=1, jump=10 * pulse(t, 0.4, 0.3))


def s4_cam(f):
    ts = f.T.word(0, "still")
    return dict(z=tween(f.t, 0, ts, 1.25, 1.8), x=tween(f.t, 0, ts, 520, 290), y=tween(f.t, 0, ts, 1150, 650),
                shake=8 * pulse(f.t, ts, 0.4))


# 5. FOURTEENTH STEP – shadow on the wall
def s5_draw(f):
    c, t, T = f.ctx, f.t, f.T
    stairwell(c, f.gt)
    tf = T.word(0, "fourteenth")
    grow = f.r(tf, f.dur, "inout")
    wall_shadow(c, 760 - 120 * grow, 1250, 600 + 700 * grow, f.r(tf, tf + 0.3))
    kid_on_stairs(f, 330 + 3 * STEP_W, expr="shock" if t > tf else "worried", sweat=1,
                  jump=0, look=-0.2, fa=30, fb=80, ba=30, bb=80, idle=2.0)


def s5_cam(f):
    tf = f.T.word(0, "fourteenth")
    return dict(z=tween(f.t, tf, f.dur, 1.15, 1.35), x=480, y=1100, shake=6 * pulse(f.t, tf, 0.5))


# 6. RULE 5
def s6_draw(f):
    c, t = f.ctx, f.t
    stairwell(c, f.gt)
    wall_shadow(c, 640, 1250, 1300, 1)
    kid_on_stairs(f, 330 + 3 * STEP_W, expr="worried", sweat=1, look=-1 if (t % 1.2) < 0.6 else 1,
                  tilt=math.sin(t * 20) * 2, fa=30, fb=80, ba=30, bb=80)


def s6_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.6, 1.9), x=560, y=900)


def s6_over(f):
    overlay_std(f, rule=(5, "NEVER LOOK BACK", "ON THE STAIRS", f.T.word(0, "five")))


# 7. LIGHTS FLICKER – it gets closer each flash
def s7_draw(f):
    c, t, T = f.ctx, f.t, f.T
    stairwell(c, f.gt)
    tf = T.word(0, "flicker")
    flashes = [tf + 0.0, tf + 0.55, tf + 1.05, tf + 1.45]
    k = sum(1 for fl in flashes if t >= fl)
    pos = [(-60, 0.0), (40, 0.95), (140, 1.05), (230, 1.12), (300, 1.18)]
    cx, cs = pos[min(k, 4)]
    if k > 0:
        creature(c, cx, stair_y(cx) + 6, cs, f.gt, reach=0.15 * k)
    kid_on_stairs(f, 330 + 3 * STEP_W, expr="shock", sweat=1, fa=30, fb=80, ba=30, bb=80, look=0.8)
    dark = 0.0
    for fl in flashes:
        if fl - 0.12 <= t < fl:
            dark = 0.96
    darkness(c, dark)


def s7_cam(f):
    tf = f.T.word(0, "flicker")
    return dict(z=1.12, x=460, y=1150, shake=4 + 8 * pulse(f.t, tf + 1.45, 0.4))


# 8. THE DOOR ABOVE / SOMETHING BEHIND
def s8_draw(f):
    c, t, T = f.ctx, f.t, f.T
    stairwell(c, f.gt)
    creature(c, 300, stair_y(300) + 6, 1.18, f.gt, reach=0.6)
    kid_on_stairs(f, 330 + 3 * STEP_W, expr="shock", sweat=1, fa=30, fb=80, ba=30, bb=80, look=1, lookY=-0.6)


def s8_cam(f):
    tb = f.T.word(1, "Behind")
    if f.t < tb:
        return dict(z=tween(f.t, 0, 0.8, 1.2, 1.6), x=tween(f.t, 0, 0.8, 500, 880), y=tween(f.t, 0, 0.8, 1100, 660))
    return dict(z=tween(f.t, tb, tb + 0.5, 1.6, 1.3), x=tween(f.t, tb, tb + 0.5, 880, 420),
                y=tween(f.t, tb, tb + 0.5, 660, 1000))


# 9. CHOICE
def s9_draw(f):
    c, t, T = f.ctx, f.t, f.T
    stairwell(c, f.gt)
    reach = 0.6 + 0.35 * f.r(0, f.dur, "inout")
    creature(c, 300, stair_y(300) + 6, 1.18, f.gt, reach=reach)
    kid_on_stairs(f, 330 + 3 * STEP_W, expr="shock", sweat=1, fa=30, fb=80, ba=30, bb=80, look=0.6,
                  tilt=math.sin(f.gt * 24) * 1.5)
    if (f.gt * 1.7) % 1 < 0.06:
        darkness(c, 0.85)


def s9_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.12, 1.22), x=470, y=990, shake=2)


def s9_over(f):
    overlay_std(f, red=0.6 + 0.4 * math.sin(f.gt * 3))
    choice_buttons(f.ctx, f.r(f.T.word(0, "Keep") - 0.1, f.T.word(1, "turn") + 0.3), f.gt)


SCENES = [
    Scene("hook", [N("You said: break the glass.")], s0_draw, s0_cam, overlay=lambda f: overlay_std(f),
          cues=lambda T: [(0.0, "hit", 0.5), (T.word(0, "glass"), "glass", 1.0), (T.word(0, "glass"), "hit", 0.7)],
          pad=0.45),
    Scene("key", [N("Inside... a key. The tag says: STAIRS.")], s0b_draw, s0b_cam, overlay=lambda f: overlay_std(f),
          trans="punch", cues=lambda T: [(T.word(0, "key"), "ding", 0.4), (T.word(0, "STAIRS"), "hit", 0.6)],
          pad=0.3),
    Scene("run", [N("So he ran.")], s1_draw, s1_cam, overlay=lambda f: overlay_std(f), trans="whip",
          cues=lambda T: [(0.05 + i * 0.19, "step", 0.8) for i in range(8)], pad=0.35, min_dur=1.6),
    Scene("floor13", [N("But the sign on the wall says... 13.", spoken="But the sign on the wall says... thirteen.")],
          s2_draw, s2_cam, overlay=lambda f: overlay_std(f), trans="cut",
          cues=lambda T: [(T.word(0, "13"), "hit", 0.9)], pad=0.4),
    Scene("rule4", [N("Rule four. Count every step out loud."),
                    Say(KID, "Eleven... Twelve... Thirteen.", gap=0.3, speed=0.85)],
          s3_draw, s3_cam, overlay=s3_over, trans="flash",
          cues=lambda T: [(T.word(1, w) - 0.05, "step", 1.0) for w in ("Eleven", "Twelve", "Thirteen")], pad=0.3),
    Scene("still13", [N("The sign still says 13.", spoken="The sign still says thirteen.")], s4_draw, s4_cam,
          overlay=lambda f: overlay_std(f), cues=lambda T: [(0.1, "creak", 0.8), (T.word(0, "still"), "hit", 0.7)],
          pad=0.3),
    Scene("fourteenth", [N("Then you hear it. A fourteenth step... behind you.")], s5_draw, s5_cam,
          overlay=lambda f: overlay_std(f), trans="flash",
          cues=lambda T: [(T.word(0, "fourteenth") - 0.1, "step", 1.4), (T.word(0, "behind"), "heartbeat", 0.9)],
          pad=0.4),
    Scene("rule5", [N("Rule five. Never look back on the stairs.")], s6_draw, s6_cam, overlay=s6_over,
          cues=lambda T: [(0.0, "heartbeat", 0.8), (1.8, "heartbeat", 0.8)], pad=0.3),
    Scene("flicker", [N("The lights flicker... and every time they do... it's closer.")], s7_draw, s7_cam,
          overlay=lambda f: overlay_std(f, red=f.r(f.T.word(0, "closer"), f.dur)),
          cues=lambda T: [(T.word(0, "flicker") + d - 0.12, "buzz", 0.8) for d in (0.0, 0.55, 1.05, 1.45)]
          + [(T.word(0, "closer"), "hit", 1.0)], pad=0.3),
    Scene("door", [N("Above you, a door. Light underneath it."), N("Behind you... something breathing.", gap=0.2)],
          s8_draw, s8_cam, overlay=lambda f: overlay_std(f, red=0.5), trans="flash",
          cues=lambda T: [(T.word(1, "Behind"), "heartbeat", 1.0), (T.word(1, "breathing"), "creak", 0.6)], pad=0.3),
    Scene("choice", [N("Keep climbing..."), N("or turn around?", gap=0.25),
                     N("Comment A or B. The top comment decides Part 4.", gap=0.35)],
          s9_draw, s9_cam, overlay=s9_over,
          cues=lambda T: [(T.word(0, "Keep"), "pop", 0.6), (T.word(1, "turn"), "pop", 0.6)]
          + [(0.3 + 1.75 * i, "heartbeat", 0.7) for i in range(4)], pad=1.2),
]

EPISODE = Episode("elevator_part3", SCENES, narrator_voice="am_onyx", voices={"kid": "am_echo"},
                  speed=1.0, music="horror", caption_y=1250)
