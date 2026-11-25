"""The 3AM Elevator - Part 4 (viewers chose A: keep climbing). Original interactive stick-figure horror
(PG: suspense, no gore). Fiction.

FILM version: five long camera-driven shots through a 3D concrete stairwell (engine3d/sets_stairs.py),
the same kid and creature as Parts 1-3 composited in as 2D puppets. Voice: free Edge neural voice."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import cairo  # noqa: E402

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("elevator_part3", os.path.join(ROOT, "episodes", "elevator_p2",
                                                                              "episode.py"))
P3 = importlib.util.module_from_spec(_spec)  # Part 3: kid, creature, key, rule box, vignette
_spec.loader.exec_module(P3)
from script import LINES as TEXT, VOICE, RATE  # noqa: E402
from engine.audio import edge_voice  # noqa: E402
from engine.core import pulse, EASES, clamp, hexc  # noqa: E402
from engine.filmplan import FilmScene  # noqa: E402
from engine.render import Episode, N, label  # noqa: E402
from engine.text import text_center  # noqa: E402

KID = P3.KID
CREATURE_UNITS = 850.0  # creature() drawing height in its own units (feet to top of head)


# ---------------------------------------------------------------- helpers
def line_idx(f):
    k = 0
    for i, ln in enumerate(f.scene.lines):
        if f.t >= ln.start - 0.05:
            k = i
    return k


def ex(f):
    return f.scene.exprs["kid"][line_idx(f)]


def shadow(c, x, y, s):
    c.save()
    c.translate(x, y + 3)
    c.scale(95 * s, 16 * s)
    c.arc(0, 0, 1, 0, 2 * math.pi)
    c.restore()
    c.set_source_rgba(0, 0, 0, 0.45)
    c.fill()


def kid(f, anchor="kid", **pose):
    """Frozen puppet at its projected 3D anchor (no idle bob, no blinking)."""
    x, y, s = f.scene.shot.anchor(anchor, f.gt)
    shadow(f.ctx, x, y, s)
    p = dict(x=x, y=y, s=s, idle=0, blink=0, expr=ex(f), sweat=1)
    p.update(pose)
    return p, f.char(KID, p)


def creature(f, anchor="creature", reach=0.4, alpha=1.0):
    x, y, s = f.scene.shot.anchor(anchor, f.gt)
    sc = s * 520 / CREATURE_UNITS
    shadow(f.ctx, x, y, s * 1.2)
    P3.creature(f.ctx, x, y, sc, f.gt, reach=reach, alpha=alpha)
    return x, y, sc


def creature_head(c, x, y, r, t, grin=1.0, alpha=1.0):
    """Just the head (for peeking down the stairwell): black, hollow white eyes, wide toothy grin."""
    c.save()
    c.translate(x, y)
    c.rotate(math.radians(math.sin(t * 0.9) * 6))
    c.push_group()
    c.save()
    c.scale(0.86, 1.0)
    c.arc(0, 0, r, 0, 2 * math.pi)
    c.restore()
    c.set_source_rgb(0.02, 0.02, 0.03)
    c.fill_preserve()
    c.set_source_rgb(0.35, 0.4, 0.42)
    c.set_line_width(r * 0.05)
    c.stroke()
    for exx in (-0.34, 0.30):
        c.save()
        c.translate(exx * r, -0.18 * r)
        c.scale(1, 1.25)
        c.arc(0, 0, 0.21 * r, 0, 2 * math.pi)
        c.restore()
        c.set_source_rgb(0.95, 0.95, 0.95)
        c.fill()
        c.arc(exx * r - 0.05 * r, -0.14 * r, 0.06 * r, 0, 2 * math.pi)
        c.set_source_rgb(0.02, 0.02, 0.03)
        c.fill()
    w = 0.58 * r * grin
    c.translate(-0.02 * r, 0.38 * r)
    c.move_to(-w, -0.08 * r)
    c.curve_to(-w * 0.5, 0.3 * r, w * 0.5, 0.3 * r, w, -0.08 * r)
    c.curve_to(w * 0.5, 0.12 * r, -w * 0.5, 0.12 * r, -w, -0.08 * r)
    c.close_path()
    c.set_source_rgb(0.95, 0.95, 0.95)
    c.fill()
    c.set_source_rgb(0.02, 0.02, 0.03)
    c.set_line_width(r * 0.03)
    for k in range(-3, 4):
        c.move_to(k * w / 4, 0)
        c.line_to(k * w / 4, 0.2 * r)
    c.stroke()
    c.pop_group_to_source()
    c.paint_with_alpha(alpha)
    c.restore()


def eyes_in_dark(c, x, y, sc):
    """When the lights die, only its eyes and grin stay visible."""
    hx, hy = x - 6 * sc, y - 742 * sc
    for exx in (-34, 30):
        c.save()
        c.translate(hx + exx * sc, hy - 18 * sc)
        c.scale(1, 1.25)
        c.arc(0, 0, 21 * sc, 0, 2 * math.pi)
        c.restore()
        c.set_source_rgb(0.97, 0.97, 0.97)
        c.fill()
    w = 58 * sc
    c.move_to(hx - w, hy + 30 * sc)
    c.curve_to(hx - w * 0.5, hy + 68 * sc, hx + w * 0.5, hy + 68 * sc, hx + w, hy + 30 * sc)
    c.curve_to(hx + w * 0.5, hy + 50 * sc, hx - w * 0.5, hy + 50 * sc, hx - w, hy + 30 * sc)
    c.set_source_rgb(0.95, 0.95, 0.95)
    c.fill()


def dark(c, a):
    if a > 0:
        c.rectangle(-400, -400, 1900, 2800)
        c.set_source_rgba(0, 0, 0.01, clamp(a))
        c.fill()


def flicker(t, starts, dur=0.11):
    return any(s <= t < s + dur for s in starts)


def header(c):
    c.rectangle(0, 0, 1080, 250)
    c.set_source_rgba(0, 0, 0, 0.85)
    c.fill()
    text_center(c, "THE 3AM ELEVATOR", 540, 85, 70, "#ffffff")
    text_center(c, "PART 4 · KEEP CLIMBING", 540, 170, 62, "#f2c84b")


def OV(f, red=0.0):
    P3.vignette(f.ctx, red)
    header(f.ctx)


def choice_buttons(c, p, t):
    if p <= 0:
        return
    opts = (("A", "THROUGH", "THE DOOR", "#d63c46"), ("B", "RUN DOWN", "TO ELEVATOR", "#2f6fe0"))
    for i, (letter, l1, l2, col) in enumerate(opts):
        pp = EASES["back"](clamp(p * 1.4 - i * 0.25))
        if pp <= 0:
            continue
        beat = 1 + 0.04 * max(0, math.sin(t * 7 + i * 1.6))
        c.save()
        c.translate(290 + i * 500, 1470)
        c.scale(pp * beat, pp * beat)
        w, h, r = 440, 170, 26
        c.new_path()
        c.arc(-w / 2 + r, -h / 2 + r, r, math.pi, 1.5 * math.pi)
        c.arc(w / 2 - r, -h / 2 + r, r, 1.5 * math.pi, 2 * math.pi)
        c.arc(w / 2 - r, h / 2 - r, r, 0, 0.5 * math.pi)
        c.arc(-w / 2 + r, h / 2 - r, r, 0.5 * math.pi, math.pi)
        c.close_path()
        c.set_source_rgb(*hexc(col))
        c.fill_preserve()
        c.set_source_rgb(1, 1, 1)
        c.set_line_width(6)
        c.stroke()
        text_center(c, letter, -w / 2 + 75, 4, 120, "#ffffff")
        text_center(c, l1, 60, -28, 44, "#ffffff")
        text_center(c, l2, 60, 28, 40, "#ffffff")
        c.restore()


def K(t, loc, tgt, lens=24):
    return {"t": float(t), "loc": list(loc), "target": list(tgt), "lens": lens}


def hold(keys, t):
    k = dict(keys[-1])
    k["t"] = float(t)
    keys.append(k)
    return keys


def go(keys, t_end, loc, tgt, lens):
    keys.append(K(t_end, loc, tgt, lens))
    return keys


# ---------------------------------------------------------------- stair geometry helpers (see sets_stairs.py)
def f2(y):
    """Ground height on flight 2 (x ~ -0.95), which climbs -y from (y=3, z=1.5) to (y=0, z=3)."""
    return 1.5 + (3.0 - y) * 0.5


# ================================================================= SHOT A: the hook (lines 0-2)
# The camera waits at the top landing, looking down flight 2. The kid climbs toward us; behind him,
# on the landing below, the creature. The hook: its grin right over his shoulder from frame one.
def camA(T):
    tb = T.word(0, "Back")
    k = [K(0, (-0.9, -1.35, 4.05), (-0.72, 2.3, 3.2), 24)]
    go(k, tb - 0.15, (-0.88, -1.0, 4.0), (-0.72, 2.3, 3.25), 30)          # creeping push-in on the faces
    hold(k, T.line(1)[0] + 0.2)
    go(k, T.word(2, "door") - 0.2, (0.75, -1.45, 5.3), (-0.85, 1.7, 2.5), 20)  # pull up and back to the door landing
    hold(k, T.dur + 1)
    return k


def anchorsA(T):
    t1, t2 = T.line(1)[0], T.line(2)[1]
    return {"kid": {"keys": [[0, -0.95, 1.85, f2(1.85)], [t1, -0.95, 1.85, f2(1.85)],
                             [t2, -0.95, 0.75, f2(0.75)]], "h": 1.75},
            "creature": {"keys": [[0, -0.55, 2.75, f2(2.75)], [t1, -0.55, 2.75, f2(2.75)],
                                  [t2, -0.6, 2.05, f2(2.05)]], "h": 2.5}}


def drawA(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    climbing = T.line(1)[0] < t < T.line(2)[1]
    cx, cy, cs = creature(f, reach=0.35 + 0.35 * f.r(T.line(2)[0], T.line(2)[1]))
    kid(f, face=-1, look=0.9 if k == 0 else -0.3, lookY=-0.2, walk=1.4 if climbing else 0,
        fa=30, fb=80, ba=30, bb=80, tilt=0 if climbing else -6)
    # the lights die for a beat on each word of the hook; only its eyes and grin remain
    words = [T.word(0, w) for w in ("Don't", "Look", "Back")]
    fl = [w - 0.16 for w in words] + [T.word(2, "closer") - 0.1, T.word(2, "closer") + 0.25]
    if flicker(t, fl, 0.12):
        dark(c, 0.93)
        eyes_in_dark(c, cx, cy, cs)


def ovA(f):
    c, T = f.ctx, f.T
    OV(f, red=0.35 + 0.35 * pulse(f.t, T.word(0, "Back"), 0.8))
    ta = T.word(1, "A")
    p = f.r(ta - 0.05, ta + 0.2) * (1 - f.r(T.line(1)[1], T.line(1)[1] + 0.3))
    if p > 0:
        s = EASES["back"](p)
        c.save()
        c.translate(540, 420)
        c.scale(s, s)
        c.rectangle(-230, -70, 460, 140)
        c.set_source_rgba(0.04, 0.04, 0.05, 0.92)
        c.fill_preserve()
        c.set_source_rgb(*hexc("#d63c46"))
        c.set_line_width(6)
        c.stroke()
        c.rectangle(-230, -70, 140, 140)
        c.fill()
        text_center(c, "A", -160, 4, 110, "#ffffff")
        text_center(c, "YOU CHOSE", 70, -24, 44, "#ffffff")
        text_center(c, "KEEP CLIMBING", 70, 28, 40, "#f2c84b")
        c.restore()


def shakeA(f):
    T = f.T
    return dict(shake=sum(10 * pulse(f.t, T.word(0, w), 0.3) for w in ("Don't", "Look", "Back"))
                + 8 * pulse(f.t, T.word(2, "closer"), 0.4))


# ================================================================= SHOT B: the door (lines 3-6)
KID_DOOR = [0.05, -1.05, 3.0, 1.75]
HANDLE = [0.36, -1.5, 3.9, 0.1]


def camB(T):
    k = [K(0, (-0.95, 2.6, 4.7), (0.05, -1.6, 3.85), 21)]
    go(k, T.word(0, "handle") - 0.15, (-0.75, 1.7, 4.45), (0.15, -1.6, 3.85), 23)
    hold(k, T.line(1)[1] + 0.25)
    go(k, T.word(2, "stairs") - 0.2, (0.85, -0.35, 4.15), (0.3, -1.55, 3.95), 32)  # in on the key and the lock
    hold(k, T.dur + 1)
    return k


def anchorsB(T):
    return {"kid": KID_DOOR, "handle": HANDLE}


def drawB(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    tl = T.word(1, "Locked")
    rattle = math.sin(t * 60) * 4 * pulse(t, tl + 0.1, 0.5)
    kid(f, face=1, look=1, fa=95 + rattle, fb=10, ba=30, bb=80, tilt=4)
    hx, hy, hs = f.scene.shot.anchor("handle", f.gt)
    if k >= 2:  # the key from Part 3 comes out, finds the lock, turns
        tk, tf = T.word(2, "key"), T.word(3, "fits")
        p = f.r(tk - 0.1, tk + 0.6)
        turn = f.r(tf - 0.15, tf + 0.1) * 1.2
        sc = hs * 6.3
        P3.key_with_tag(c, hx - 40 * (1 - p), hy - 6 + 120 * (1 - p), max(0.35, min(sc, 2.2)), swing=-0.4 + turn)


def ovB(f):
    c, T = f.ctx, f.T
    OV(f, red=0.25)
    tl = T.word(1, "Locked")
    label(c, "LOCKED", 540, 430, f.r(tl, tl + 0.2) * (1 - f.r(T.line(2)[0], T.line(2)[0] + 0.3)), size=96,
          color="#ff4d57")
    tf = T.word(3, "fits")
    label(c, "*CLICK*", 540, 430, f.r(tf, tf + 0.15), size=90, color="#ffffff")


def shakeB(f):
    T = f.T
    return dict(shake=7 * pulse(f.t, T.word(1, "Locked") + 0.1, 0.5) + 5 * pulse(f.t, T.word(3, "fits"), 0.3))


# ================================================================= SHOT C: the same stairs (lines 7-10)
def camC(T):
    k = [K(0, (1.05, 2.6, 1.85), (-0.3, -1.4, 1.2), 18)]
    go(k, T.word(0, "same") - 0.2, (0.95, 1.7, 1.65), (-0.2, -1.4, 1.25), 20)
    hold(k, T.line(0)[1] + 0.05)
    go(k, T.word(1, "13") - 0.2, (0.75, 0.15, 1.75), (0.95, -1.6, 1.7), 28)   # the sign
    hold(k, T.line(1)[1] + 0.05)
    go(k, T.word(2, "handwriting") - 0.2, (-0.2, 0.95, 1.8), (1.6, -0.8, 1.78), 17)  # the wall
    hold(k, T.dur + 1)
    return k


def anchorsC(T):
    return {"kid": {"keys": [[0, -0.05, -1.45, 0.0], [T.line(0)[1], 0.15, -0.75, 0.0]], "h": 1.75},
            "scrawl": [1.58, -0.8, 1.6, 0.5]}


def drawC(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    kid(f, face=1 if k < 2 else -1, look=-1 if k >= 2 else 0.3, walk=1.2 if t < T.line(0)[1] else 0,
        fa=30, fb=80, ba=30, bb=80)


def ovC(f):
    c, T = f.ctx, f.T
    OV(f, red=0.1)
    t6 = T.word(3, "six")
    P3.rule_box(c, 6, "STOP CLIMBING.", "IT'S NOT BEHIND YOU", f.r(t6, t6 + 0.25))


def shakeC(f):
    T = f.T
    return dict(shake=6 * pulse(f.t, T.word(1, "13"), 0.35) + 9 * pulse(f.t, T.word(3, "behind"), 0.45))


# ================================================================= SHOT D: look up (lines 11-12)
TOP = [0.0, 1.6, 11.2, 0.6]


def camD(T):
    tu = T.word(0, "up")
    k = [K(0, (0.15, 1.1, 0.55), (0.0, -0.6, 1.45), 22)]
    hold(k, tu - 0.55)
    go(k, tu - 0.1, (0.03, 1.45, 0.9), (0.0, 1.62, 12.0), 18)       # whip-tilt up the well
    hold(k, T.line(0)[1] + 0.2)
    go(k, T.word(1, "top") - 0.15, (0.02, 1.5, 4.6), (0.0, 1.62, 12.0), 20)  # slowly rising toward it
    hold(k, T.dur + 1)
    return k


def anchorsD(T):
    return {"kid": [0.0, -0.55, 0.0, 1.75], "top": TOP}


def drawD(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    tu = T.word(0, "up")
    if t < tu - 0.3:
        kid(f, face=1, look=0, lookY=-1, tilt=-12, fa=30, fb=80, ba=30, bb=80)
        return
    x, y, s = f.scene.shot.anchor("top", f.gt)
    tt = T.word(1, "top")
    reveal = f.r(T.line(1)[0], tt)
    r = max(120.0, s * 520 * 1.4) * (0.8 + 0.5 * reveal)
    # long arms gripping the railing on both sides of the well
    c.set_line_cap(1)
    for side in (-1, 1):
        c.move_to(x + side * r * 0.6, y + r * 0.3)
        c.curve_to(x + side * r * 1.6, y + r * 0.6, x + side * r * 2.2, y + r * 1.4, x + side * r * 2.9,
                   y + r * 1.2)
        c.set_source_rgb(0.02, 0.02, 0.03)
        c.set_line_width(r * 0.16)
        c.stroke()
    creature_head(c, x, y, r, f.gt, grin=0.5 + 0.6 * reveal)


def ovD(f):
    OV(f, red=0.2 + 0.5 * f.r(f.T.word(1, "waiting"), f.T.word(1, "top")))


def shakeD(f):
    T = f.T
    return dict(shake=10 * pulse(f.t, T.word(1, "top"), 0.5))


# ================================================================= SHOT E: the choice (lines 13-15)
def camE(T):
    td, te, tp = T.word(0, "door"), T.word(1, "elevator"), T.word(2, "decides")
    k = [K(0, (1.25, 2.6, 1.75), (-0.1, -1.1, 1.2), 22)]
    go(k, td - 0.2, (1.15, 2.2, 1.7), (-0.05, -1.2, 1.2), 23)
    hold(k, T.line(0)[1])
    go(k, te - 0.2, (1.2, 2.0, 1.6), (0.0, -0.8, 1.05), 24)
    hold(k, T.line(1)[1] + 0.1)
    go(k, tp - 0.2, (1.05, 1.7, 1.6), (0.0, -0.7, 1.15), 26)
    hold(k, T.dur + 1)
    return k


def anchorsE(T):
    return {"kid": [0.05, -0.75, 0.0, 1.75], "well": [0.0, 0.2, 2.75, 0.5]}


def drawE(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    kid(f, face=-1 if k == 0 else 1, look=-1 if k == 0 else 1, lookY=-0.3, fa=30, fb=80, ba=30, bb=80,
        tilt=math.sin(f.gt * 24) * 1.5)
    # it lowers itself down the well, head first, behind him
    kx, ky, ks = f.scene.shot.anchor("kid", f.gt)
    drop = EASES["inout"](f.r(T.line(1)[1], T.dur - 1.6))
    r = 150.0
    x = kx + 230
    yy = 250 - 2 * r + (ky - ks * 520 + 200 - 250 + 2 * r) * drop  # ends right beside his face
    c.set_source_rgb(0.02, 0.02, 0.03)
    c.set_line_width(r * 0.18)
    c.move_to(x, -50)
    c.line_to(x, yy - r)
    c.stroke()
    c.save()
    c.translate(x, yy)
    c.rotate(math.pi)  # hanging upside down
    creature_head(c, 0, 0, r, f.gt, grin=1.0, alpha=0.95)
    c.restore()
    if (f.gt * 1.7) % 1 < 0.05:
        dark(c, 0.85)


def ovE(f):
    c, T = f.ctx, f.T
    OV(f, red=0.55 + 0.35 * math.sin(f.gt * 3))
    choice_buttons(c, f.r(T.word(0, "door") - 0.3, T.word(1, "elevator") + 0.3), f.gt)


def shakeE(f):
    return dict(shake=2)


# ---------------------------------------------------------------- assemble
GAPS = {0: 0.0, 1: 0.45, 2: 0.15, 3: 0.2, 4: 0.55, 5: 0.5, 6: 0.45, 7: 0.1, 8: 0.35, 9: 0.35, 10: 0.3,
        11: 0.1, 12: 0.45, 13: 0.1, 14: 0.25, 15: 0.4}
LINES = []
for i, txt in enumerate(TEXT):
    spoken = txt
    cap = txt.replace("thirteen", "13")
    ln = N(cap, gap=GAPS.get(i, 0.25))
    ln.audio = edge_voice(spoken, VOICE, RATE.get(i, "-5%"), "-3Hz")
    LINES.append(ln)

SCENES = [
    FilmScene("A_hook", LINES[0:3], drawA, "stairs", "emergency", camA, anchorsA, module="sets_stairs",
              camera=shakeA, overlay=ovA, keywords=[(0, "Back"), (2, "door")],
              named=[(1, "climbing", "kid")], exprs={"kid": ["shock", "worried", "worried"]}, exposure=-0.15,
              cues=lambda T: [(0.0, "heartbeat", 1.0)]
              + [(T.word(0, w) - 0.02, "hit", 1.0) for w in ("Don't", "Look", "Back")]
              + [(T.word(0, "Back") + 0.05, "dun", 0.9), (T.line(1)[0] + 0.3, "steps", 0.6),
                 (T.word(2, "breathing"), "heartbeat", 0.9), (T.word(2, "closer") - 0.1, "buzz", 0.8)], pad=0.1),
    FilmScene("B_door", LINES[3:7], drawB, "stairs", "doorlight", camB, anchorsB, module="sets_stairs",
              camera=shakeB, overlay=ovB, keywords=[(0, "handle"), (1, "Locked"), (2, "stairs"), (3, "fits")],
              named=[(0, "handle", "handle")], exprs={"kid": ["worried", "sad", "thinking", "smile"]},
              exposure=0.1, trans="cut",
              cues=lambda T: [(0.0, "steps", 0.4), (T.word(0, "handle"), "clink", 0.7),
                              (T.word(1, "Locked") + 0.05, "scrape", 0.8), (T.word(1, "Locked") + 0.1, "hit", 0.7),
                              (T.word(2, "key"), "clink", 0.9), (T.word(2, "stairs"), "dun", 0.5),
                              (T.word(3, "fits"), "tick", 1.0), (T.word(3, "fits") + 0.25, "creak", 0.9)], pad=0.1),
    FilmScene("C_same", LINES[7:11], drawC, "stairs_open", "cold", camC, anchorsC, module="sets_stairs",
              camera=shakeC, overlay=ovC,
              keywords=[(0, "same"), (1, "13"), (2, "handwriting"), (3, "behind")],
              named=[(2, "handwriting", "scrawl")], exprs={"kid": ["worried", "worried", "sad", "worried"]},
              exposure=0.15, trans="flash",
              cues=lambda T: [(0.0, "creak", 1.0), (T.word(0, "same"), "dun", 0.9), (T.word(1, "13"), "hit", 0.8),
                              (T.word(2, "handwriting"), "scrape", 0.6), (T.word(3, "six"), "stamp", 0.8),
                              (T.word(3, "behind"), "dun", 1.0)], pad=0.1),
    FilmScene("D_up", LINES[11:13], drawD, "stairs", "cold", camD, anchorsD, module="sets_stairs",
              camera=shakeD, overlay=ovD, keywords=[(0, "up"), (1, "top")], named=[(1, "top", "top")],
              exprs={"kid": ["worried", "shock"]}, exposure=0.2, trans="cut",
              cues=lambda T: [(T.word(0, "up") - 0.4, "whoosh", 0.9), (T.word(1, "never"), "heartbeat", 1.0),
                              (T.word(1, "top"), "hit", 1.0), (T.word(1, "top"), "dun", 1.0)], pad=0.2),
    FilmScene("E_choice", LINES[13:16], drawE, "stairs_open", "emergency", camE, anchorsE, module="sets_stairs",
              camera=shakeE, overlay=ovE, keywords=[(0, "door"), (1, "elevator"), (2, "decides")],
              exprs={"kid": ["worried", "worried", "worried"]}, exposure=-0.1, trans="cut",
              cues=lambda T: [(0.0, "heartbeat", 0.8), (T.word(0, "door"), "creak", 0.6),
                              (T.word(1, "elevator"), "ding", 0.6), (T.word(2, "Comment"), "pop", 0.5),
                              (T.word(2, "decides"), "dun", 0.8)], pad=1.0),
]

EPISODE = Episode("elevator_part4", SCENES, music="horror", music_gain=0.2, caption_style="ricks",
                  caption_y=1250)
