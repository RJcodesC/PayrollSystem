"""The Great Emu War (1932) - true story, FILM version.

Five long camera-driven shots through a 3D outback wheat farm (engine3d/sets_outback.py). Characters are
2D puppets on the IK rig (cast.py): every arm/leg pose comes from the vetted pose library or IK targets,
and the limb log is checked before rendering. Voice: free Edge neural voice. Facts: sources.md."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import cairo  # noqa: E402

from cast import MAJOR, SGT, GUNNER, FARMER, EMU, REST, POINT, HANDS_UP, FACEPALM, SHRUG  # noqa: E402
from script import LINES as TEXT, VOICE, RATE  # noqa: E402
from engine.audio import edge_voice  # noqa: E402
from engine.core import pulse, EASES, clamp, hexc  # noqa: E402
from engine.creatures import Emu, lewis_gun  # noqa: E402
from engine.filmplan import FilmScene  # noqa: E402
from engine.render import Episode, N, label  # noqa: E402
from engine.text import text_center  # noqa: E402

M = "sets_outback"
EMU_DRAW = 0.84  # emu art is a bit taller than the rig: scale so the head lands at the anchor height
FLOCK = [Emu(f"e{i}", seed=i * 0.37) for i in range(16)]


# ---------------------------------------------------------------- helpers
def line_idx(f):
    k = 0
    for i, ln in enumerate(f.scene.lines):
        if f.t >= ln.start - 0.05:
            k = i
    return k


def ex(f, name):
    return f.scene.exprs[name][line_idx(f)]


def K(t, loc, tgt, lens=24, linear=False):
    k = {"t": float(t), "loc": list(loc), "target": list(tgt), "lens": lens}
    if linear:
        k["linear"] = True
    return k


def hold(keys, t):
    k = dict(keys[-1])
    k["t"] = float(t)
    k.pop("linear", None)
    keys.append(k)
    return keys


def go(keys, t, loc, tgt, lens):
    keys.append(K(t, loc, tgt, lens))
    return keys


def shadow(c, x, y, s, w=95):
    c.save()
    c.translate(x, y + 3)
    c.scale(w * s, 16 * s)
    c.arc(0, 0, 1, 0, 2 * math.pi)
    c.restore()
    c.set_source_rgba(0.15, 0.04, 0.0, 0.35)
    c.fill()


class Stage:
    """Collects puppets for one frame and draws them far-to-near (correct overlaps)."""

    def __init__(self, f):
        self.f, self.items = f, []

    def person(self, ch, anchor, **pose):
        def draw():
            x, y, s = self.f.scene.shot.anchor(anchor, self.f.gt)
            shadow(self.f.ctx, x, y, s)
            p = dict(x=x, y=y, s=s, idle=0, blink=0)
            p.update(pose)
            self.f.char(ch, p)
        self.items.append((self.f.scene.shot.depth(anchor, self.f.gt), draw))

    def emu(self, emu, anchor, face=None, **pose):
        def draw():
            sh = self.f.scene.shot
            x, y, s = sh.anchor(anchor, self.f.gt)
            fc = face
            if fc is None:  # face the way it is moving on screen
                x2 = sh.anchor(anchor, self.f.gt + 0.08)[0]
                fc = 1 if x2 >= x - 0.5 else -1
            shadow(self.f.ctx, x, y, s, 120)
            p = dict(x=x, y=y, s=s * EMU_DRAW, face=fc)
            p.update(pose)
            emu.draw(self.f.ctx, p, self.f.gt)
        self.items.append((self.f.scene.shot.depth(anchor, self.f.gt), draw))

    def extra(self, depth, fn):
        self.items.append((depth, fn))

    def draw(self):
        for _, fn in sorted(self.items, key=lambda it: -it[0]):
            fn()


def ov(f, warm=0.0):
    g = cairo.RadialGradient(540, 960, 520, 540, 960, 1300)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.12, 0.03, 0.0, 0.45)
    f.ctx.rectangle(0, 0, 1080, 1920)
    f.ctx.set_source(g)
    f.ctx.fill()
    if warm:
        f.ctx.rectangle(0, 0, 1080, 1920)
        f.ctx.set_source_rgba(1.0, 0.45, 0.15, 0.12 * warm)
        f.ctx.fill()


def gun_at(f, anchor, s_char, face, fire=0.0, angle=0.0, bipod=True):
    """Lewis gun at a projected 3D point, scaled to the scene (1.25 m long)."""
    x, y, _ = f.scene.shot.anchor(anchor, f.gt)
    sg = s_char * 0.675
    return lewis_gun(f.ctx, x, y, sg, face=face, angle=angle, t=f.gt, fire=fire, bipod=bipod), (x, y, sg)


def bullets_icon(c, x, y, s=1.0):
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rectangle(-9, -10, 18, 40)
    c.set_source_rgb(*hexc("#c9952a"))
    c.fill_preserve()
    c.set_source_rgb(0.08, 0.08, 0.08)
    c.set_line_width(3)
    c.stroke()
    c.move_to(-9, -10)
    c.curve_to(-9, -30, 9, -30, 9, -10)
    c.close_path()
    c.set_source_rgb(*hexc("#b06a2a"))
    c.fill_preserve()
    c.set_source_rgb(0.08, 0.08, 0.08)
    c.stroke()
    c.restore()


def card(c, p, x, y, w, h):
    s = EASES["back"](clamp(p))
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    c.rectangle(-w / 2, -h / 2, w, h)
    c.set_source_rgba(0.06, 0.05, 0.05, 0.9)
    c.fill_preserve()
    c.set_source_rgb(1, 1, 1)
    c.set_line_width(6)
    c.stroke()
    c.restore()
    return s


# ================================================================= SHOT A: the hook (lines 0-1)
# Low in the wheat, looking back at the sandbag post: three soldiers, a machine gun... and in the
# foreground, an emu leans into frame and stares them down.
SOLDIERS_SB = {"major": [4.55, -1.0, 0, 1.75], "sgt": [4.55, 1.0, 0, 1.75], "gunner": [4.7, 0.05, 0, 1.68]}
GUN_SB = [5.25, 0.15, 0.82, 0.1]


def camA(T):
    tb, tw = T.word(0, "birds"), T.word(1, "won")
    k = [K(0, (10.5, 4.8, 1.0), (4.6, -0.3, 1.15), 22)]
    go(k, tb - 0.2, (9.3, 3.7, 1.05), (4.6, -0.3, 1.2), 26)
    hold(k, T.line(0)[1] + 0.05)
    go(k, tw - 0.15, (8.6, 3.1, 1.15), (4.6, -0.1, 1.25), 30)
    hold(k, T.dur + 1)
    return k


def anchorsA(T):
    return {**SOLDIERS_SB, "gun": GUN_SB}


def drawA(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    st = Stage(f)
    tb = T.word(0, "birds")
    st.person(MAJOR, "major", face=1, expr=ex(f, "major"), **(POINT if k == 0 else HANDS_UP))
    st.person(SGT, "sgt", face=1, expr=ex(f, "sgt"), **(REST if k == 0 else HANDS_UP))
    _, _, sg = f.scene.shot.anchor("gunner", f.gt)
    fire = 1.0 if k == 0 and t > T.word(0, "war") and t < tb - 0.1 else 0.0

    def gunner():
        pts, _ = gun_at(f, "gun", sg, 1, fire=fire, angle=3)
        x, y, s = f.scene.shot.anchor("gunner", f.gt)
        shadow(c, x, y, s)
        f.char(GUNNER, dict(x=x, y=y, s=s, idle=0, blink=0, face=1, expr=ex(f, "gunner"), crouch=0.5, lean=12,
                            hand_f_at={"world": pts["grip"]}, hand_b_at={"world": pts["fore"]}))
        gun_at(f, "gun", sg, 1, fire=fire, angle=3)
    st.extra(f.scene.shot.depth("gunner", f.gt), gunner)
    st.draw()
    # foreground emu leans in from the right and stares them down
    p = EASES["out"](f.r(tb - 0.45, tb - 0.05))
    smug = k == 1
    EMU.draw(c, dict(x=1500 - 330 * p, y=2350, s=3.1, face=-1, expr="smug" if smug else "stare",
                     head_tilt=-8 if smug else 4, neck=0.95), f.gt)


def ovA(f):
    c, T = f.ctx, f.T
    ov(f)
    t19 = T.word(0, "1932")
    label(c, "1932", 540, 300, f.r(t19, t19 + 0.2) * (1 - f.r(T.line(0)[1], T.line(0)[1] + 0.3)), size=110,
          color="#ffffff")
    tw = T.word(1, "won")
    label(c, "THE BIRDS WON", 540, 300, f.r(tw, tw + 0.2), size=86, color="#ffd23f")


def shakeA(f):
    T = f.T
    w0, w1 = T.word(0, "war"), T.word(0, "birds")
    return dict(shake=5 * (1 if w0 < f.t < w1 - 0.1 else 0) + 9 * pulse(f.t, T.word(1, "won"), 0.35))


# ================================================================= SHOT B: the farm (lines 2-4)
FARMER_ROAD = [1.3, 12.6, 0, 1.75]
GRAZE = [(4.6, 11.2), (5.6, 13.4), (6.9, 10.1), (7.4, 14.8), (8.8, 12.0), (10.2, 9.0), (10.8, 15.6), (12.5, 11.8),
         (13.6, 8.0), (15.0, 14.0), (17.5, 10.5), (19.0, 16.5), (21.5, 9.5), (24.0, 13.0), (27.0, 11.0), (30.0, 15.0)]


def camB(T):
    tf, th = T.word(1, "fences"), T.word(2, "help")
    k = [K(0, (2.0, -9.0, 11.0), (9.0, 14.0, 0.0), 22)]
    go(k, tf - 0.2, (-0.6, 5.2, 1.7), (5.5, 12.5, 0.9), 22)   # crane down onto the broken fence
    hold(k, T.line(1)[1] + 0.05)
    go(k, th - 0.2, (-1.4, 9.4, 1.6), (2.0, 13.2, 1.2), 26)    # the farmer
    hold(k, T.dur + 1)
    return k


def anchorsB(T):
    a = {"farmer": FARMER_ROAD}
    for i, (x, y) in enumerate(GRAZE):
        a[f"e{i}"] = [x, y, 0, 1.8]
    return a


def drawB(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    st = Stage(f)
    for i in range(len(GRAZE)):
        peck = max(0.0, math.sin(f.gt * (2.2 + i * 0.13) + i * 1.7)) ** 2
        st.emu(FLOCK[i], f"e{i}", face=-1 if i % 3 else 1, peck=peck, expr="dumb" if i % 4 else "smug")
    pose = FACEPALM if k == 2 else (SHRUG if k == 1 else REST)
    st.person(FARMER, "farmer", face=1, expr=ex(f, "farmer"), **pose)
    st.draw()


def ovB(f):
    c, T = f.ctx, f.T
    ov(f)
    tw = T.word(0, "Western")
    label(c, "WESTERN AUSTRALIA", 540, 300, f.r(tw, tw + 0.2) * (1 - f.r(T.line(0)[1], T.line(0)[1] + 0.3)),
          size=70, color="#ffffff")


# ================================================================= SHOT C: the army arrives, first attack (5-7)
TRUCK_LINE = {"major": [1.6, -4.2, 0, 1.75], "sgt": [1.6, -3.2, 0, 1.75], "gunner": [1.6, -2.2, 0, 1.68]}
FLEE = [((8, 1.5), (16, 6)), ((9, -1), (15, -8)), ((10.5, 3), (11, 12)), ((11.5, 0.5), (20, 1)),
        ((12.5, -2.5), (13, -11)), ((9.5, 4.5), (6, 11)), ((13, 2), (19, 9)), ((14.5, -0.5), (22, -5)),
        ((16, 1.5), (25, 2)), ((17, -3), (23, -10))]


def camC(T):
    tt, ts = T.word(0, "three"), T.word(2, "scattered")
    k = [K(0, (5.6, 1.2, 1.7), (0.2, -6.5, 1.4), 20)]
    go(k, tt - 0.2, (4.4, -0.6, 1.6), (1.6, -3.2, 1.3), 26)   # lands on the three soldiers
    hold(k, T.line(1)[1] + 0.05)
    go(k, ts - 0.2, (3.0, -3.4, 1.45), (12.0, 2.5, 0.8), 20)  # swing round to the field as they open fire
    hold(k, T.dur + 1)
    return k


def anchorsC(T):
    t2 = T.line(2)[0]
    ts = T.word(2, "scattered")
    a = {}
    for n in ("major", "sgt", "gunner"):  # by the truck, then at the sandbags (moved while off screen)
        tx, ty, tz, h = TRUCK_LINE[n]
        sx, sy, sz, _ = SOLDIERS_SB[n]
        a[n] = {"keys": [[0, tx, ty, tz], [t2 - 0.3, tx, ty, tz], [t2 - 0.29, sx, sy, sz]], "h": h}
    a["gun"] = GUN_SB
    for i, ((x0, y0), (x1, y1)) in enumerate(FLEE):
        a[f"f{i}"] = {"keys": [[0, x0, y0, 0], [ts - 0.25, x0, y0, 0], [ts + 2.4, x1, y1, 0]], "h": 1.8,
                      "linear": True}
    return a


def drawC(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    st = Stage(f)
    ts = T.word(2, "scattered")
    if k < 2:
        st.person(MAJOR, "major", face=-1, expr=ex(f, "major"), **(POINT if k == 1 else REST))
        st.person(SGT, "sgt", face=-1, expr=ex(f, "sgt"), **REST)
        st.person(GUNNER, "gunner", face=-1, expr=ex(f, "gunner"), **REST)
    else:
        fire = 1.0 if T.line(2)[0] < t < ts + 0.6 else 0.0
        st.person(MAJOR, "major", face=1, expr=ex(f, "major"), **POINT)
        st.person(SGT, "sgt", face=1, expr=ex(f, "sgt"), **(HANDS_UP if t > ts else REST))
        _, _, sg = f.scene.shot.anchor("gunner", f.gt)

        def gunner():
            pts, _ = gun_at(f, "gun", sg, 1, fire=fire, angle=2)
            x, y, s = f.scene.shot.anchor("gunner", f.gt)
            shadow(c, x, y, s)
            f.char(GUNNER, dict(x=x, y=y, s=s, idle=0, blink=0, face=1, expr=ex(f, "gunner"), crouch=0.5, lean=12,
                                hand_f_at={"world": pts["grip"]}, hand_b_at={"world": pts["fore"]}))
            gun_at(f, "gun", sg, 1, fire=fire, angle=2)
        st.extra(f.scene.shot.depth("gunner", f.gt), gunner)
    for i in range(len(FLEE)):
        running = ts - 0.25 < t < ts + 2.4
        st.emu(FLOCK[i], f"f{i}", run=2.6 if running else 0, dust=1 if running else 0,
               expr="shock" if running else "stare", face=None if running else -1)
    st.draw()


def ovC(f):
    c, t, T = f.ctx, f.t, f.T
    ov(f)
    k = line_idx(f)
    if k == 1:  # cutaway card: 2 guns, 10,000 bullets
        p = f.r(T.line(1)[0] - 0.05, T.line(1)[0] + 0.25) * (1 - f.r(T.line(1)[1] - 0.15, T.line(1)[1] + 0.1))
        if p > 0:
            card(c, p, 540, 520, 860, 460)
            s = EASES["back"](clamp(p))
            c.save()
            c.translate(540, 520)
            c.scale(s, s)
            for j in (-1, 1):
                if t > T.word(1, "Two") + (0.0 if j < 0 else 0.15):
                    lewis_gun(c, j * 180 - 70, -90, 0.42, face=1, angle=0, t=f.gt, bipod=False)
            tb = T.word(1, "Ten")
            n = int(10000 * EASES["out"](f.r(tb, T.line(1)[1] - 0.2)))
            if t > tb - 0.05:
                text_center(c, f"{n:,}", 0, 70, 120, "#ffd23f", stroke=10)
                text_center(c, "BULLETS", 0, 170, 56, "#ffffff", stroke=8)
            c.restore()
    if k == 0:
        tt = T.word(0, "three")
        label(c, "3 SOLDIERS", 540, 330, f.r(tt, tt + 0.2), size=96, color="#ffffff")


def shakeC(f):
    T = f.T
    ts = T.word(2, "scattered")
    return dict(shake=6 if T.line(2)[0] < f.t < ts + 0.6 else 0)


# ================================================================= SHOT D: the truck chase + the jam (8-10)
def truck_y(T, t):
    """Truck drives up the road at a steady speed, then brakes and stops."""
    t0, t1 = 0.0, T.line(1)[1] + 0.2
    if t <= t1:
        return -22 + (t - t0) * 13.0
    tb = min(t - t1, 0.7)
    return -22 + (t1 - t0) * 13.0 + 13.0 * tb - 13.0 / 1.4 * tb * tb


def camD(T):
    t1 = T.line(1)[1] + 0.2
    tj = T.word(2, "jammed")
    k = []
    for i in range(0, int(t1 / 0.5) + 1):
        tt = min(t1, i * 0.5)
        y = truck_y(T, tt)
        k.append(K(tt, (-4.2, y - 4.5, 1.7), (1.0, y + 3.5, 1.2), 22, linear=True))
    ys = truck_y(T, t1 + 1.0)
    k.append(K(t1 + 0.7, (-4.2, ys - 4.5, 1.7), (1.0, ys + 3.5, 1.2), 22, linear=True))
    go(k, tj - 0.2, (-1.6, ys - 3.6, 2.5), (9.0, ys + 6.0, 0.9), 22)   # over the gunner's shoulder: the flock
    hold(k, T.dur + 1)
    return k


def moveD(T):
    ks = []
    n = int((T.dur + 1) / 0.25) + 1
    for i in range(n):
        tt = i * 0.25
        ks.append([tt, 0.0, truck_y(T, tt), 0.0, 0.0])
    return {"truck": ks}


def anchorsD(T):
    n = int((T.dur + 1) / 0.25) + 1
    gk = [[i * 0.25, 0.25, truck_y(T, i * 0.25) - 2.2, 0.9] for i in range(n)]
    gun = [[i * 0.25, 0.3, truck_y(T, i * 0.25) - 0.9, 2.05] for i in range(n)]
    a = {"gunner": {"keys": gk, "h": 1.68, "linear": True}, "gun": {"keys": gun, "h": 0.1, "linear": True}}
    t1 = T.line(1)[1] + 0.2
    ys = truck_y(T, t1 + 1.0)
    # racing emus: start beside/behind the truck, overtake it along the fence line
    for i in range(5):
        x = 4.6 + (i % 3) * 1.2
        y0 = -24 - i * 2.5
        y1 = y0 + 17.5 * (t1 + 0.4)
        a[f"r{i}"] = {"keys": [[0, x, y0, 0], [t1 + 0.4, x, y1, 0], [T.dur + 1, x + 1.5, y1 + 10, 0]], "h": 1.8,
                      "linear": True}
    # the huge flock waiting ahead when the gun jams
    for i in range(10):
        a[f"w{i}"] = [5.5 + (i % 4) * 2.2, ys + 4 + (i // 4) * 3.0 + (i % 2), 0, 1.8]
    return a


def drawD(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    st = Stage(f)
    t1 = T.line(1)[1] + 0.2
    tj = T.word(2, "jammed")
    moving = t < t1 + 0.6
    bounce = 10 * abs(math.sin(f.gt * 11)) if moving else 0
    for i in range(5):
        st.emu(FLOCK[i], f"r{i}", run=2.8, dust=1, expr="happy" if k >= 1 else "stare")
    if k == 2:
        for i in range(10):
            st.emu(FLOCK[5 + i % 11], f"w{i}", face=-1, expr="stare", head_tilt=(i % 3 - 1) * 6)
    _, _, sg = f.scene.shot.anchor("gunner", f.gt)
    jam = t > tj
    fire = 1.0 if (k == 0 and t > T.word(0, "truck") - 0.2) or (k == 1) else 0.0
    if jam:
        fire = 0.0

    def gunner():
        x, y, s = f.scene.shot.anchor("gunner", f.gt)
        pts, _ = gun_at(f, "gun", sg, 1, fire=fire, angle=4 + bounce * 0.3, bipod=False)
        f.char(GUNNER, dict(x=x, y=y - bounce, s=s, idle=0, blink=0, face=1, expr=ex(f, "gunner"),
                            hand_f_at={"world": pts["grip"]}, hand_b_at={"world": pts["fore"]}))
        pts, (gx, gy, gs) = gun_at(f, "gun", sg, 1, fire=fire, angle=4 + bounce * 0.3, bipod=False)
        if jam:  # a sad little puff of smoke from the jammed gun
            q = f.r(tj, tj + 1.2)
            for j in range(3):
                c.arc(gx + 300 * gs * 1.0 + j * 18, gy - 60 * gs - q * 90 - j * 22, 16 + q * 24 + j * 6, 0,
                      2 * math.pi)
                c.set_source_rgba(0.85, 0.85, 0.85, 0.7 * (1 - q))
                c.fill()
    st.extra(f.scene.shot.depth("gunner", f.gt), gunner)
    st.draw()


def ovD(f):
    c, T = f.ctx, f.T
    ov(f)
    tj = T.word(2, "jammed")
    label(c, "*CLICK*", 540, 330, f.r(tj, tj + 0.15), size=110, color="#ffffff")


def shakeD(f):
    T = f.T
    t1 = T.line(1)[1] + 0.2
    return dict(shake=(4 if f.t < t1 + 0.6 else 0) + 8 * pulse(f.t, T.word(2, "jammed"), 0.3))


# ================================================================= SHOT E: the score, sunset (11-15)
FENCE_EMUS = [(4.4, -1.5), (4.0, 1.2), (5.6, 3.3), (4.3, 5.6), (6.2, 7.4), (4.8, 9.4)]


def camE(T):
    tf, tt, ts, tk = T.word(0, "thousand"), T.word(2, "tanks"), T.word(3, "stayed"), T.word(4, "fake")
    k = [K(0, (7.2, -4.8, 1.3), (4.6, 0.0, 1.0), 24)]
    go(k, tf - 0.2, (6.9, -3.6, 1.35), (4.6, 0.0, 1.05), 27)
    hold(k, T.line(1)[1] + 0.05)
    go(k, tt - 0.2, (6.4, -2.6, 1.6), (4.6, -1.0, 1.5), 30)               # on the Major
    hold(k, T.line(2)[1] + 0.05)
    go(k, ts - 0.2, (10.5, 6.5, 1.5), (0.0, -10.0, 1.3), 20)             # wide: the truck leaves, emus stay
    hold(k, T.line(3)[1] + 0.05)
    go(k, tk - 0.2, (8.2, 4.0, 1.55), (4.3, 5.6, 1.45), 30)              # push in on the smug emu
    hold(k, T.dur + 1)
    return k


def moveE(T):
    t3 = T.line(3)[0]
    return {"truck": [[0, 0, -7, 0, 180], [t3, 0, -7, 0, 180], [t3 + 4.0, 0, -60, 0, 180]]}


def anchorsE(T):
    a = {"major": [4.55, -1.0, 0, 1.75], "sgt": [4.4, 0.9, 0, 1.75], "gunner": [4.7, 0.05, 0, 1.68]}
    for i, (x, y) in enumerate(FENCE_EMUS):
        a[f"s{i}"] = [x, y, 0, 1.8]
    return a


def drawE(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = line_idx(f)
    st = Stage(f)
    if k < 3:
        st.person(MAJOR, "major", face=1, expr=ex(f, "major"), **(POINT if k == 2 else REST))
        st.person(SGT, "sgt", face=1, expr=ex(f, "sgt"), crouch=0.35, **SHRUG)
        st.person(GUNNER, "gunner", face=1, expr=ex(f, "gunner"), crouch=0.6, **REST)
    else:
        for i in range(len(FENCE_EMUS)):
            st.emu(FLOCK[i], f"s{i}", face=-1, expr="smug" if i == 3 else "stare", head_tilt=(i % 3 - 1) * 5,
                   neck=1.0)
    st.draw()


def ovE(f):
    c, t, T = f.ctx, f.t, f.T
    ov(f, warm=1.0)
    k = line_idx(f)
    if k in (0, 1):
        p = f.r(T.line(0)[0], T.line(0)[0] + 0.25) * (1 - f.r(T.line(1)[1], T.line(1)[1] + 0.25))
        if p > 0:
            card(c, p, 540, 520, 900, 420)
            s = EASES["back"](clamp(p))
            c.save()
            c.translate(540, 520)
            c.scale(s, s)
            if k == 0:
                n = int(9860 * EASES["out"](f.r(T.line(0)[0] + 0.2, T.word(0, "bullets"))))
                text_center(c, f"{n:,}", 0, -30, 150, "#ffd23f", stroke=10)
                text_center(c, "BULLETS FIRED", 0, 100, 56, "#ffffff", stroke=8)
            else:
                tb = T.word(1, "bullets")
                for j in range(10):
                    if t > T.line(1)[0] + j * 0.08:
                        bullets_icon(c, -380 + j * 44, -20, 1.3)
                if t > tb:
                    text_center(c, "=", 120, -10, 110, "#ffffff", stroke=8)
                if t > T.word(1, "emu") - 0.1:
                    FLOCK[0].draw(c, dict(x=300, y=150, s=0.32, face=-1, expr="smug"), f.gt)
                text_center(c, "PER EMU", 0, 150, 52, "#ffffff", stroke=8)
            c.restore()
    if k == 2:
        tt = T.word(2, "tanks")
        label(c, "“...LIKE TANKS”", 540, 330, f.r(tt, tt + 0.2), size=90, color="#ffd23f")
    if k == 4:
        tf = T.word(4, "Follow")
        label(c, "FOLLOW FOR MORE", 540, 330, f.r(tf, tf + 0.2), size=84, color="#ffffff")


# ---------------------------------------------------------------- assemble
GAPS = {0: 0.0, 1: 0.35, 2: 0.3, 3: 0.15, 4: 0.15, 5: 0.2, 6: 0.25, 7: 0.25, 8: 0.2, 9: 0.15, 10: 0.2,
        11: 0.25, 12: 0.15, 13: 0.25, 14: 0.25, 15: 0.3}
LINES = []
for i, txt in enumerate(TEXT):
    ln = N(txt, gap=GAPS.get(i, 0.2))
    ln.audio = edge_voice(txt, VOICE, RATE.get(i, "+0%"), "+0Hz")
    LINES.append(ln)


def burst(t0, t1, gain=0.45):
    out, t = [], t0
    while t < t1:
        out.append((t, "hit", gain))
        t += 0.085
    return out


SCENES = [
    FilmScene("A_hook", LINES[0:2], drawA, "outback", "golden", camA, anchorsA, module=M, camera=shakeA, overlay=ovA,
              keywords=[(0, "birds"), (1, "won")], named=[(0, "Australia", "major")],
              exprs={"major": ["angry", "shock"], "sgt": ["angry", "worried"], "gunner": ["angry", "worried"]},
              exposure=0.0,
              cues=lambda T: burst(T.word(0, "war"), T.word(0, "birds") - 0.1)
              + [(T.word(0, "birds") - 0.4, "whoosh", 0.8), (T.word(0, "birds"), "dun", 0.7),
                 (T.word(1, "won"), "fail", 0.8)], pad=0.1),
    FilmScene("B_farm", LINES[2:5], drawB, "outback", "golden", camB, anchorsB, module=M, overlay=ovB,
              keywords=[(1, "fences"), (2, "help")], named=[(2, "farmers", "farmer")],
              exprs={"farmer": ["worried", "angry", "sad"]}, trans="cut",
              cues=lambda T: [(0.0, "whoosh", 0.5), (T.word(1, "crops"), "pop", 0.6),
                              (T.word(1, "fences"), "hit", 0.7), (T.word(2, "help"), "ding", 0.5)], pad=0.1),
    FilmScene("C_army", LINES[5:8], drawC, "outback", "golden", camC, anchorsC, module=M, overlay=ovC,
              camera=shakeC, keywords=[(0, "three"), (2, "scattered")], named=[(0, "soldiers", "sgt")],
              exprs={"major": ["smug", "smug", "angry"], "sgt": ["neutral", "neutral", "worried"],
                     "gunner": ["neutral", "smug", "angry"]}, trans="cut",
              cues=lambda T: [(T.word(0, "three") + 0.15, "crickets", 0.7), (T.line(1)[0], "pop", 0.6),
                              (T.word(1, "Ten"), "chaching", 0.5)]
              + burst(T.line(2)[0], T.word(2, "scattered") + 0.6)
              + [(T.word(2, "scattered"), "run", 0.8)], pad=0.1),
    FilmScene("D_truck", LINES[8:11], drawD, "outback_road", "golden", camD, anchorsD, module=M, overlay=ovD,
              camera=shakeD, move=moveD, keywords=[(2, "jammed")], named=[(0, "truck", "gunner")],
              exprs={"gunner": ["angry", "shock", "sad"]}, trans="whip",
              cues=lambda T: [(0.0, "run", 0.6), (T.word(0, "truck"), "whoosh", 0.6)]
              + burst(T.word(0, "truck") - 0.2, T.line(1)[1], 0.35)
              + [(T.word(1, "outran"), "boing", 0.7), (T.word(2, "jammed"), "clink", 1.0),
                 (T.word(2, "jammed") + 0.2, "fail", 0.8)], pad=0.1),
    FilmScene("E_sunset", LINES[11:16], drawE, "outback", "sunset", camE, anchorsE, module=M, overlay=ovE,
              move=moveE, keywords=[(0, "thousand"), (2, "tanks"), (3, "stayed"), (4, "fake")],
              exprs={"major": ["sad", "sad", "angry", "sad", "sad"], "sgt": ["sad"] * 5, "gunner": ["sad"] * 5},
              exposure=0.1, trans="cut",
              cues=lambda T: [(T.line(0)[0], "tick", 0.6), (T.word(0, "bullets"), "chaching", 0.5),
                              (T.word(1, "emu"), "pop", 0.7), (T.word(2, "tanks"), "dun", 0.8),
                              (T.line(3)[0], "whoosh", 0.4), (T.word(3, "stayed"), "reveal", 0.7),
                              (T.word(4, "Follow"), "ding", 0.5)], pad=0.8),
]

EPISODE = Episode("emu_war", SCENES, music="caper", music_gain=0.13, caption_style="ricks", caption_y=1440,
                  voice_tempo=1.04)
