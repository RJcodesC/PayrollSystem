"""Why Pirates Wore Eye Patches - FILM version (measured grammar).
Six long shots through 3D sets; the camera travels, lands, then the key word is spoken.
Characters are frozen 2D puppets placed in 3D (projected each frame). Light changes with the story."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import patch as P  # noqa: E402  (characters + 2D effects from the first version)
from engine.core import tween, pulse, EASES, clamp, hexc  # noqa: E402
from engine.filmplan import FilmScene  # noqa: E402
from engine.render import Episode, N, label  # noqa: E402
from engine.text import text_center  # noqa: E402
import cairo  # noqa: E402

from engine.rig import Character, Look  # noqa: E402

HERO = Character("hero", Look(coat="#f4f1e8", coat_dark="#cfc8b6", outfit="stripes", stripe="#d82a35", sash="#d82a35",
                              belt="#3a2416", sleeve="#d82a35", boots="#2a1a10", hat="bandana", hat_color="#d82a35",
                              patch=True, stubble=True, style="ricks"), seed=0.6)
CAPT = Character("capt", Look(coat="#efe6cf", coat_dark="#c4bba3", outfit="coat", vest="#1c46a8", belt="#2a1a10",
                              sleeve="#1c46a8", boots="#141418", hat="tricorn", hat_color="#1a1a1e",
                              hat_band="#f0b818", beard="#3a2416", style="ricks"), seed=1.4)
TEST = Character("tester", Look(coat="#5aa8ff", coat_dark="#3a86de", outfit="labcoat", hair="messy", glasses=True,
                                tie="#e8323e", boots="#3a3a40", patch=True, style="ricks"), seed=2.4)


# ---------------------------------------------------------------- helpers
def puppet(f, ch, anchor, **pose):
    """Draw a frozen puppet at its projected 3D anchor (R7: no idle bob, no blinking)."""
    x, y, s = f.scene.shot.anchor(anchor, f.gt)
    c = f.ctx
    c.save()
    c.translate(x, y + 3)
    c.scale(100 * s, 18 * s)
    c.arc(0, 0, 1, 0, 2 * math.pi)
    c.restore()
    c.set_source_rgba(0.05, 0.03, 0.08, 0.35)
    c.fill()
    p = dict(x=x, y=y, s=s, idle=0, blink=0)
    p.update(pose)
    pts = f.char(ch, p)
    return p, pts


def screen(f, anchor):
    x, y, s = f.scene.shot.anchor(anchor, f.gt)
    return x, y, s


def K(t, loc, tgt, lens=24):
    return {"t": float(t), "loc": list(loc), "target": list(tgt), "lens": lens}


def hold(keys, t):
    """Repeat the last key at time t (camera rests until then)."""
    k = dict(keys[-1])
    k["t"] = float(t)
    keys.append(k)
    return keys


def ex(f, ch):
    """The line's single expression for this character (R6)."""
    return f.scene.exprs[ch.name][P.line_idx(f)]


def OV(f):
    P.vignette(f.ctx, 0.4)


# deck geometry
HERO_DECK = [0.3, 2.2, 0.0, 1.8]
FACE_CU = ((0.42, 0.95, 1.62), (0.3, 2.2, 1.55))
DECK_MED = ((0.95, -0.7, 1.8), (0.3, 2.2, 1.35))


# ---------------------------------------------------------------- SHOT A: deck, golden hour (lines 0-2)
def camA(T):
    tg, ta, tb = T.word(0, "good", edge="end"), T.word(1, "attack"), T.word(2, "blinding")
    k = [K(0, *FACE_CU, 24)]
    hold(k, tg + 0.25)
    k.append(K(ta - 0.35, (1.7, -1.2, 2.4), (12, 55, 4.5), 30))
    hold(k, T.line(1)[1] + 0.1)
    k.append(K(tb - 0.25, *DECK_MED, 22))
    hold(k, T.dur + 1)
    return k


def anchorsA(T):
    return {"hero": HERO_DECK, "enemy": [16, 70, 6, 4.0]}


def drawA(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = P.line_idx(f)
    tg = T.word(0, "good")
    lift = f.r(tg - 0.15, tg + 0.15) * (1 - f.r(T.line(0)[1] - 0.3, T.line(0)[1]))
    shade = 1.0 if k == 2 else 0.0
    puppet(f, HERO, "hero", face=-1, expr=ex(f, HERO), patch=0.5 * lift, fa=20 + 120 * lift + 135 * shade,
           fb=60 - 5 * shade, look=0.5)
    if k == 1:
        ta = T.word(1, "attack")
        ex_, ey_, _ = screen(f, "enemy")
        P.smoke(c, ex_, ey_, t, ta - 0.1)
        P.smoke(c, ex_ - 40, ey_ + 20, t, ta + 0.3)
    if k == 2:
        P.glare(c, 250, 360, 0.6 + 0.4 * f.r(T.word(2, "blinding") - 0.2, T.word(2, "blinding") + 0.2))


def ovA(f):
    OV(f)
    T = f.T
    if P.line_idx(f) == 0:
        P.pop(f.ctx, "?!", 800, 560, f.r(T.word(0, "good") + 0.1, T.word(0, "good") + 0.35), size=150,
              color="#ffffff")
    t17 = T.word(1, "1700s")
    label(f.ctx, "1700s", 540, 330, f.r(t17, t17 + 0.25) * (1 - f.r(T.line(1)[1], T.line(1)[1] + 0.3)),
          size=90, color="#ffffff")


def camA_shake(f):
    ta = f.T.word(1, "attack")
    return dict(shake=14 * pulse(f.t, ta, 0.4) + 10 * pulse(f.t, ta + 0.4, 0.4))


# ---------------------------------------------------------------- SHOT B: below deck, dark (lines 3-7)
HOLD_HERO = [0.0, 3.0, 0.0, 1.75]
HOLD_CAPT = [0.6, 6.6, 0.0, 1.8]


def camB(T):
    k = [K(0, (0.0, -0.6, 1.45), (0.0, 3.0, 1.0), 22)]
    hold(k, T.line(1)[1] + 0.15)
    k.append(K(T.word(3, "twenty") - 0.3, (0.05, 1.35, 1.5), (0.0, 3.0, 1.35), 24))
    hold(k, T.line(3)[1] + 0.05)
    k.append(K(T.word(4, "twenty") - 0.3, (-0.35, 0.2, 1.5), (0.35, 5.0, 1.25), 22))
    hold(k, T.dur + 1)
    return k


def anchorsB(T):
    return {"hero": HOLD_HERO, "capt": HOLD_CAPT}


def drawB(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = P.line_idx(f)
    land = f.r(0, 0.4, "in")
    if k == 4:
        lunge = math.sin(f.gt * 7)
        puppet(f, CAPT, "capt", face=-1, expr=ex(f, CAPT), hold="sword", fa=80 + 30 * lunge, fb=10)
    pose, pts = puppet(f, HERO, "hero", face=1, expr=ex(f, HERO), hold="sword", fa=70, fb=20,
                       jump=700 * (1 - land) * (1 if k == 0 else 0))
    tb = T.word(0, "black")
    d = 0.95 * f.r(tb - 0.15, tb + 0.1) if k == 0 else (0.94 if k in (1, 2, 3) else 0.35)
    P.dark(c, d)
    if d > 0.5:
        P.eyes_in_dark(c, pose, pts, look=math.sin(f.gt * 4), blink=False)
    if k == 4:
        tt = T.word(4, "twenty")
        P.pop(c, "CLANG!", 560, 820, pulse(t, tt - 0.2, 0.6) * 2, size=110, color="#ffffff")


def ovB(f):
    c, t, T = f.ctx, f.t, f.T
    OV(f)
    k = P.line_idx(f)
    if k == 1:
        P.pop(c, "BONK!", 760, 860, f.r(T.line(1)[1] - 0.45, T.line(1)[1] - 0.3), size=110, color="#ffffff")
    if k in (2, 3):  # screen-space cutaway card (no cut: the shot keeps rolling behind it)
        p = EASES["back"](f.r(T.line(2)[0] - 0.1, T.line(2)[0] + 0.2))
        c.save()
        c.translate(540, 760)
        c.scale(p, p)
        c.rectangle(-430, -330, 860, 660)
        c.set_source_rgba(0.04, 0.06, 0.12, 0.92)
        c.fill_preserve()
        c.set_source_rgb(1, 1, 1)
        c.set_line_width(8)
        c.stroke()
        if k == 2:
            P.big_eye(c, 0, -20, tween(t, T.line(2)[0], T.line(2)[1], 0.25, 0.85), w=330)
            text_center(c, "PUPIL", 0, -250, 60, "#ffffff", stroke=10)
        else:
            P.clock(c, 0, 20, EASES["inout"](f.r(T.line(3)[0], T.line(3)[1])) / 3, r=200)
            P.pop(c, "20 MIN", 0, -260, f.r(T.word(3, "twenty"), T.word(3, "twenty") + 0.2), size=90)
        c.restore()


# ---------------------------------------------------------------- SHOT C: deck, the theory (lines 8-10)
def camC(T):
    k = [K(0, *DECK_MED, 22)]
    k.append(K(T.word(0, "covered") - 0.3, *FACE_CU, 24))
    hold(k, T.line(1)[1] + 0.1)
    k.append(K(T.word(2, "open") - 0.25, (-0.25, 1.0, 1.66), (0.3, 2.2, 1.55), 24))
    hold(k, T.dur + 1)
    return k


def drawC(f):
    c, T = f.ctx, f.T
    f.scene.shot.draw_bg(c, f.gt)
    puppet(f, HERO, "hero", face=-1, expr=ex(f, HERO), patch=0.0, fa=20, fb=60,
           look=math.sin(f.gt * 2.5) if P.line_idx(f) == 2 else 0)


def ovC(f):
    c, t, T = f.ctx, f.t, f.T
    OV(f)
    tt = T.word(0, "theory")
    label(c, "THE THEORY", 540, 330, f.r(tt, tt + 0.25) * (1 - f.r(T.line(0)[1], T.line(0)[1] + 0.3)), size=70)
    if P.line_idx(f) == 1:
        k = EASES["back"](f.r(T.line(1)[0], T.line(1)[0] + 0.3))
        c.save()
        c.translate(800, 620)
        c.scale(k, k)
        c.arc(0, 0, 190, 0, 2 * math.pi)
        c.set_source_rgb(*hexc("#0d1424"))
        c.fill_preserve()
        c.set_source_rgb(1, 1, 1)
        c.set_line_width(10)
        c.stroke()
        P.big_eye(c, 0, 0, 0.82, w=140)
        c.restore()
        text_center(c, "Ready for the dark", 800, 860, 46, "#ffffff", stroke=10)


# ---------------------------------------------------------------- SHOT D: below deck, the flip (lines 11-12)
def camD(T):
    k = [K(0, (0.02, 1.55, 1.55), (0.0, 3.0, 1.45), 24)]
    hold(k, T.line(0)[1] + 0.05)
    k.append(K(T.word(1, "night") - 0.25, (-0.7, -0.6, 1.5), (0.3, 5.0, 1.15), 22))
    hold(k, T.dur + 1)
    return k


def drawD(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = P.line_idx(f)
    tf = T.word(0, "flip")
    flip = f.r(tf - 0.1, tf + 0.5)
    if k == 1:
        puppet(f, CAPT, "capt", face=-1, expr=ex(f, CAPT), hold="sword", fa=40, fb=20, sweat=1)
    puppet(f, HERO, "hero", face=1, expr=ex(f, HERO), patch=flip, hold="sword" if k == 1 else None,
           fa=(110 if k == 1 else 150 * pulse(t, tf - 0.2, 0.8) + 20), fb=(-10 if k == 1 else 70))
    tb = T.word(1, "Boom")
    P.dark(c, 0.6 if t < tb else 0.1 * (1 - f.r(tb, tb + 0.4)), tint=(0.0, 0.03, 0.02))
    if tb <= t < tb + 0.2:
        c.rectangle(-400, -400, 1900, 2800)
        c.set_source_rgba(1, 1, 1, 1 - (t - tb) / 0.2)
        c.fill()


def ovD(f):
    OV(f)
    tb = f.T.word(1, "Boom")
    P.pop(f.ctx, "BOOM!", 540, 560, f.r(tb, tb + 0.2), size=150)


def camD_shake(f):
    return dict(shake=12 * pulse(f.t, f.T.word(1, "Boom"), 0.4))


# ---------------------------------------------------------------- SHOT E: the test course (lines 13-16)
def camE(T):
    k = [K(0, (0.9, -1.6, 1.7), (0.0, 1.5, 1.15), 22)]
    hold(k, T.line(0)[1] + 0.1)
    k.append(K(T.line(1)[1] - 0.2, (0.6, 1.8, 1.75), (-0.4, 5.0, 1.0), 22))
    hold(k, T.line(2)[1] + 0.05)
    k.append(K(T.word(3, "see") - 0.25, (1.5, 5.4, 1.8), (1.0, 9.0, 1.0), 22))
    hold(k, T.dur + 1)
    return k


def anchorsE(T):
    return {"tester": {"h": 1.75, "keys": [[0, 0.0, 1.5, 0.0], [T.line(1)[0], 0.0, 1.5, 0.0],
                                           [T.line(1)[1] - 0.1, -0.2, 5.15, 0.0], [T.line(2)[1], -0.2, 5.15, 0.0],
                                           [T.line(3)[0] + 0.6, 0.9, 5.4, 0.0],
                                           [T.word(3, "see"), 1.0, 9.0, 0.0], [T.dur + 1, 1.0, 9.0, 0.0]]}}


def drawE(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    k = P.line_idx(f)
    walking = (k == 1 and t < T.line(1)[1] - 0.1) or (k == 3 and t < T.word(3, "see"))
    tf = T.word(3, "Flip")
    tb = T.word(2, "bumping")
    stumble = pulse(t, tb, 0.6) if k == 2 else 0
    pose, pts = puppet(f, TEST, "tester", face=1, expr=ex(f, TEST), walk=1.6 if walking else 0,
                       patch=f.r(tf, tf + 0.4) if k == 3 else 0.0, tilt=25 * stumble, lean=-15 * stumble,
                       fa=150 if k == 0 else (110 if k == 2 else 10), fb=30 if k == 0 else 0)
    if k == 1:
        P.dark(c, 0.75 * f.r(T.word(1, "pitch") - 0.1, T.word(1, "pitch") + 0.2))
    elif k == 2:
        P.dark(c, 0.93)
        P.eyes_in_dark(c, pose, pts, look=math.sin(f.gt * 6))
    elif k == 3:
        P.dark(c, 0.93 * (1 - 0.85 * f.r(tf + 0.3, tf + 0.6)), tint=(0.0, 0.04, 0.02))


def ovE(f):
    c, t, T = f.ctx, f.t, f.T
    OV(f)
    tm = T.word(0, "MythBusters")
    label(c, "MYTHBUSTERS, 2007", 540, 330, f.r(tm, tm + 0.25) * (1 - f.r(T.line(0)[1], T.line(0)[1] + 0.3)),
          size=60, color="#ffffff")
    if P.line_idx(f) == 2:
        tb = T.word(2, "bumping")
        P.pop(c, "BONK!", 760, 900, f.r(tb, tb + 0.15), size=110, color="#ffffff")
    if P.line_idx(f) == 3:
        k = f.r(T.word(3, "see"), T.word(3, "see") + 0.2)
        if k > 0:
            sc = EASES["back"](k)
            c.save()
            c.translate(800, 760)
            c.scale(sc, sc)
            for col, w in (((0.08, 0.08, 0.1), 46), (hexc("#5ad16a"), 28)):
                c.move_to(-80, 0)
                c.line_to(-20, 60)
                c.line_to(90, -70)
                c.set_source_rgb(*col)
                c.set_line_width(w)
                c.set_line_cap(1)
                c.set_line_join(1)
                c.stroke()
            c.restore()


# ---------------------------------------------------------------- SHOT F: deck at sunset (lines 17-18)
def camF(T):
    k = [K(0, *DECK_MED, 22)]
    hold(k, T.line(0)[1] + 0.1)
    k.append(K(T.word(1, "switch") - 0.3, *FACE_CU, 24))
    hold(k, T.dur + 1)
    return k


def drawF(f):
    c, t, T = f.ctx, f.t, f.T
    f.scene.shot.draw_bg(c, f.gt)
    tl, ts = T.word(1, "lights"), T.word(1, "switch")
    k = P.line_idx(f)
    pose, pts = puppet(f, HERO, "hero", face=-1, expr=ex(f, HERO), patch=f.r(ts, ts + 0.4) if k == 1 else 0.0,
                       fa=(40 if k == 0 else (150 if t < tl else 30)), fb=(100 if k == 0 else 70))
    if k == 1 and tl + 0.15 < t < ts + 0.3:
        P.dark(c, 0.95)
        P.eyes_in_dark(c, pose, pts)


def ovF(f):
    c, T = f.ctx, f.T
    OV(f)
    tp = T.word(0, "prove")
    P.stamp(c, "NO PROOF", 540, 520, f.r(tp, tp + 0.2) * (1 - f.r(T.line(0)[1], T.line(0)[1] + 0.3)),
            color="#d63c46", size=120)
    ts = T.word(1, "switch")
    label(c, "TRY IT TONIGHT", 540, 330, f.r(ts + 0.2, ts + 0.45), size=70)


def camF_shake(f):
    return dict(shake=8 * pulse(f.t, f.T.word(0, "prove") + 0.2, 0.3))


# ---------------------------------------------------------------- assemble
L = ["That pirate eye patch? There might be a perfectly good eye under it.",
     "Picture it. It's the 1700s, and your ship is under attack.",
     "Up on deck, the sun is blinding.",
     "Then you jump below deck to fight... and it's pitch black.",
     "You can't see a thing.",
     "See, your eyes need time to adjust to the dark.",
     "Up to twenty minutes.",
     "In a sword fight, you don't have twenty minutes.",
     "So, the theory goes, pirates kept one eye covered.",
     "That eye stays in the dark all day.",
     "On deck, you use the open eye.",
     "Below deck, you flip the patch...",
     "Boom. Instant night vision.",
     "MythBusters actually tested this.",
     "They covered one eye, then ran a pitch-black obstacle course.",
     "The normal eye? Lost, bumping into everything.",
     "Flip the patch? They could see.",
     "Nobody can prove real pirates did it.",
     "But try it tonight. Cover one eye, turn off the lights... and switch."]
LINES = [N(x) for x in L]
for i, ln in enumerate(LINES):
    ln.audio = os.path.join(P.VOICE, f"line{i:02d}.mp3")
    ln.gap = 0.05

SCENES = [
    FilmScene("A_deck", LINES[0:3], drawA, "deck2", "golden", camA, anchorsA, camera=camA_shake, overlay=ovA,
              keywords=[(0, "good"), (1, "attack"), (2, "blinding")], named=[(1, "attack", "enemy")],
              exprs={"hero": ["sly", "sly", "angry"]}, exposure=-0.2,
              cues=lambda T: [(0.0, "waves", 0.4), (T.word(0, "good"), "pop", 0.7),
                              (T.word(1, "attack") - 0.1, "hit", 1.0), (T.word(1, "attack") + 0.3, "hit", 0.8),
                              (T.word(2, "blinding"), "reveal", 0.4)], pad=0.1),
    FilmScene("B_hold", LINES[3:8], drawB, "hold2", "hold", camB, anchorsB, overlay=ovB,
              keywords=[(0, "black"), (3, "twenty"), (4, "twenty")], named=[(4, "sword", "capt")],
              exprs={"hero": ["angry", "shock", "worried", "worried", "worried"], "capt": ["angry"] * 5},
              exposure=0.4, trans="cut",
              cues=lambda T: [(0.0, "whoosh", 0.6), (0.4, "stamp", 0.8), (T.word(0, "black"), "dun", 0.7),
                              (T.line(1)[1] - 0.45, "boing", 0.8), (T.line(2)[0], "pop", 0.5)]
              + [(T.line(3)[0] + k * 0.18, "tick", 1.0) for k in range(6)]
              + [(T.word(4, "twenty") - 0.2, "clink", 1.0), (T.word(4, "twenty"), "clink", 0.9)], pad=0.1),
    FilmScene("C_theory", LINES[8:11], drawC, "deck2", "golden", camC, lambda T: {"hero": HERO_DECK}, overlay=ovC,
              keywords=[(0, "covered"), (2, "open")], exprs={"hero": ["smile", "neutral", "smile"]},
              exposure=-0.2, trans="cut",
              cues=lambda T: [(T.word(0, "theory"), "pop", 0.7), (T.line(1)[0], "pop", 0.5)], pad=0.1),
    FilmScene("D_flip", LINES[11:13], drawD, "hold2", "hold", camD, anchorsB, camera=camD_shake, overlay=ovD,
              keywords=[(0, "flip"), (1, "night")], exprs={"hero": ["sly", "grin"], "capt": ["angry", "shock"]},
              exposure=0.4, trans="cut",
              cues=lambda T: [(T.word(0, "flip"), "zip", 0.8), (T.word(1, "Boom"), "hit", 1.0),
                              (T.word(1, "night"), "reveal", 0.6)], pad=0.1),
    FilmScene("E_course", LINES[13:17], drawE, "course2", "lab", camE, anchorsE, overlay=ovE,
              keywords=[(0, "tested"), (2, "bumping"), (3, "see")], named=[(0, "MythBusters", "tester")],
              exprs={"tester": ["smile", "neutral", "worried", "grin"]}, exposure=0.2, trans="flash",
              cues=lambda T: [(0.1, "ding", 0.5), (T.line(1)[0] + 0.3, "steps", 0.6),
                              (T.word(2, "bumping"), "boing", 0.9), (T.word(3, "Flip"), "zip", 0.8),
                              (T.word(3, "see"), "ding", 0.8)], pad=0.1),
    FilmScene("F_sunset", LINES[17:19], drawF, "deck2", "sunset", camF, lambda T: {"hero": HERO_DECK},
              camera=camF_shake, overlay=ovF, keywords=[(0, "prove"), (1, "switch")],
              exprs={"hero": ["sly", "smile"]}, exposure=-0.1, trans="cut",
              cues=lambda T: [(T.word(0, "prove") + 0.2, "stamp", 1.0), (T.word(1, "lights") + 0.15, "stamp", 0.5),
                              (T.word(1, "switch"), "reveal", 0.8)], pad=0.9),
]

EPISODE = Episode("pirate_film", SCENES, music="caper", music_gain=0.12, caption_style="ricks", caption_y=1440,
                  voice_tempo=1.08)
