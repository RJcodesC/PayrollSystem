"""Pilot: The Man Who Sold the Eiffel Tower (Victor Lustig, 1925).
Every visual/sfx beat is keyed to words in the narration so timing survives voice changes."""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from engine import bg  # noqa: E402
from engine.cast import LUSTIG, POISSON, DEALER_A, DEALER_B, BUYER2, POLICE  # noqa: E402
from engine.core import tween, ramp, pulse, EASES, clamp, hexc  # noqa: E402
from engine.render import Episode, Scene, N, Say, label  # noqa: E402
from engine.rig import INK, _star  # noqa: E402
from engine.text import text_center  # noqa: E402

G = 1610   # ground line for street scenes
GI = 1640  # ground line for interiors
S = 1.7    # hero scale


# ------------------------------------------------------------------ episode props
def sold_sign(ctx, x, y, p, rot=-8, txt="SOLD", color="#d63c46", size=1.0):
    """A sign slammed onto the screen. p: 0 hidden -> 1 landed."""
    if p <= 0:
        return
    s = (1 + 1.6 * (1 - EASES["out"](clamp(p)))) * size
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(rot))
    ctx.scale(s, s)
    w, h = 300 + 40 * (len(txt) - 4), 130
    ctx.rectangle(-w / 2, -h / 2, w, h)
    ctx.set_source_rgba(*hexc(color), min(1, p * 3))
    ctx.fill_preserve()
    ctx.set_source_rgba(*INK, min(1, p * 3))
    ctx.set_line_width(9)
    ctx.stroke()
    ctx.rectangle(-w / 2 + 14, -h / 2 + 14, w - 28, h - 28)
    ctx.set_source_rgba(1, 1, 1, min(1, p * 3))
    ctx.set_line_width(4)
    ctx.stroke()
    text_center(ctx, txt, 0, 2, 84, "#ffffff")
    ctx.restore()


def bulb(ctx, x, y, p):
    if p <= 0:
        return
    s = EASES["back"](clamp(p))
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    for i in range(8):
        a = i * math.pi / 4
        ctx.move_to(math.cos(a) * 70, math.sin(a) * 70 - 10)
        ctx.line_to(math.cos(a) * 95, math.sin(a) * 95 - 10)
    ctx.set_source_rgb(*hexc("#ffd84a"))
    ctx.set_line_width(8)
    ctx.stroke()
    ctx.arc(0, -10, 48, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc("#fff3a0"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.rectangle(-22, 34, 44, 30)
    ctx.set_source_rgb(*hexc("#9aa0ab"))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.stroke()
    ctx.restore()


def paper_pile(ctx, x, y, n, stamped):
    for i in range(n):
        ctx.save()
        ctx.translate(x + (i % 3) * 8 - 8, y - i * 10)
        ctx.rotate(math.radians((i * 37) % 9 - 4))
        ctx.rectangle(-110, -14, 220, 22)
        ctx.set_source_rgb(0.99, 0.98, 0.94)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.restore()
    for k in range(stamped):
        ctx.save()
        ctx.translate(x - 150 + k * 150, y - 180)
        ctx.rotate(math.radians(-10 + k * 9))
        ctx.rectangle(-120, -100, 240, 170)
        ctx.set_source_rgb(0.99, 0.98, 0.94)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(5)
        ctx.stroke()
        ctx.set_line_width(3)
        for j in range(4):
            ctx.move_to(-95, -70 + j * 22)
            ctx.line_to(80, -70 + j * 22)
        ctx.stroke()
        ctx.rectangle(-80, 5, 160, 48)
        ctx.set_source_rgb(*hexc("#d63c46"))
        ctx.set_line_width(5)
        ctx.stroke()
        text_center(ctx, "OFFICIAL", 0, 29, 34, "#d63c46")
        ctx.restore()


def coins_rain(ctx, t, t0, x, y):
    if t < t0:
        return
    for i in range(10):
        tt = t - t0 - i * 0.04
        if tt < 0 or tt > 0.9:
            continue
        cx = x + math.sin(i * 2.3) * 160 + tt * math.cos(i) * 90
        cy = y - 260 * tt + 650 * tt * tt
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(abs(math.cos(tt * 12 + i)) * 0.9 + 0.1, 1)
        ctx.arc(0, 0, 22, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#f2c84b"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.restore()


def rubbing(t, amp=18, sp=9):
    return dict(fa=55 + math.sin(t * sp) * amp, fb=55, ba=45 - math.sin(t * sp) * amp, bb=60)


# ------------------------------------------------------------------ scenes
# 1. HOOK
def s_hook_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.paris(c, f.gt)
    ts = T.word(0, "sold")
    sold_sign(c, 540, 800, f.r(ts, ts + 0.16, "out"))
    f.char(LUSTIG, dict(x=790, y=G, s=S, face=-1, expr="smug" if t < ts else "grin",
                        fa=tween(t, ts - 0.3, ts, 10, 125, "back"), fb=tween(t, ts - 0.3, ts, 12, -15)))


def s_hook_cam(f):
    ts = f.T.word(0, "sold")
    return dict(z=tween(f.t, 0, ts, 1.55, 1.0, "inout"), y=tween(f.t, 0, ts, 760, 960),
                shake=12 * pulse(f.t, ts + 0.12, 0.25))


# 2. HOOK 2 – he came back
def s_back_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.paris(c, f.gt)
    sold_sign(c, 540, 800, 1)
    tb = T.word(0, "came")
    ta = T.word(0, "again")
    # run off left, come back from the right
    if t < tb + 0.1:
        x = tween(t, 0.0, tb + 0.1, 790, -260, "in")
        pose = dict(x=x, y=G, s=S, face=-1, run=2.6 if t > 0.1 else 0, expr="grin")
        bg.dust(c, x + 120, G, f.r(0.1, 0.7))
    else:
        x = tween(t, tb + 0.15, ta - 0.1, 1350, 790, "out")
        walking = t < ta - 0.12
        pose = dict(x=x, y=G, s=S, face=-1, walk=2.0 if walking else 0, hold="contract",
                    fa=60 if not walking else 10, fb=-10,
                    expr="wink" if t > ta + 0.15 else "sly", look=-1 if walking else 0.6)
    f.char(LUSTIG, pose)
    sold_sign(c, 560, 990, f.r(ta, ta + 0.16, "out"), rot=7, txt="AGAIN?!", color="#e8902a")


def s_back_cam(f):
    ta = f.T.word(0, "again")
    return dict(shake=12 * pulse(f.t, ta + 0.12, 0.25), z=tween(f.t, ta, f.dur, 1.0, 1.06))


# 3. WHO
def s_who_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.stage(c, f.gt, "#f6d77a")
    tn = T.word(0, "Victor")
    tnot = T.word(1, "NOT")
    hat = pulse(t, tn, 0.9)
    shrug = f.r(tnot - 0.1, tnot + 0.15, "back") * (1 - f.r(f.dur - 0.3, f.dur))
    f.char(LUSTIG, dict(x=540, y=1780, s=2.0, face=1, expr="smile" if t < tnot else "grin",
                        hat_off=hat, fa=lerp3(hat, shrug, 10, 150, 40), fb=lerp3(hat, shrug, 12, 30, 95),
                        ba=-10 + 50 * shrug, bb=12 + 85 * shrug, tilt=-8 * shrug, lean=-6 * hat))


def lerp3(h, s, base, h_val, s_val):
    return base + (h_val - base) * h + (s_val - base) * s


def s_who_overlay(f):
    T = f.T
    label(f.ctx, "VICTOR LUSTIG", 540, 330, f.r(T.word(0, "Victor"), T.word(0, "Victor") + 0.25))
    tc = T.word(1, "con")
    label(f.ctx, "PROFESSIONAL CON MAN", 540, 470, f.r(tc, tc + 0.25), color="#ffffff", size=44)
    tnot = T.word(1, "NOT")
    p = f.r(tnot, tnot + 0.2)
    if p > 0:
        label(f.ctx, "OWNS THE TOWER?  NO.", 540, 600, p, color="#d63c46", size=46, tcolor="#ffffff")


# 4. NEWSPAPER
def s_news_draw(f):
    bg.newspaper(f.ctx, f.gt)
    tf = f.T.word(0, "fortune")
    bg.sparkle_burst(f.ctx, 540, 560, f.r(tf, tf + 0.6, "out"), n=10, r=260)


def s_news_cam(f):
    T = f.T
    tr = T.word(0, "rusting")
    tf = T.word(0, "repairs")
    y = tween(f.t, 0, tr, 520, 640) if f.t < tf else tween(f.t, tf, tf + 0.6, 640, 1080)
    z = tween(f.t, 0, tr, 1.35, 1.2) if f.t < tf else tween(f.t, tf, tf + 0.6, 1.2, 1.35)
    return dict(z=z, y=y, rot=tween(f.t, 0, f.dur, -2, 1))


# 5. IDEA
def s_idea_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.paris(c, f.gt)
    ti = T.word(0, "idea")
    f.char(LUSTIG, dict(x=540, y=G, s=S, face=1, expr="sly" if t > ti - 0.2 else "thinking", hold="newspaper",
                        fa=70, fb=40, look=0.8, lookY=-0.5 if t < ti else 0.2, tilt=tween(t, ti - 0.2, ti, 0, -8)))
    bulb(c, 790, 600, f.r(ti, ti + 0.25))


def s_idea_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.15, 1.5, "inout"), y=tween(f.t, 0, f.dur, 1000, 820), x=600)


# 6. FAKE PAPERS
def s_fake_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hotel(c, f.gt)
    hits = [T.word(0, "fake"), T.word(0, "government"), T.word(0, "papers")]
    n_st = sum(1 for h in hits if t >= h)
    # stamping arm: down on each hit
    down = max([pulse(t, h - 0.14, 0.32) for h in hits] + [0])
    f.char(LUSTIG, dict(x=330, y=GI, s=S, face=1, expr="sly", hold="stamp", fa=60 + 45 * (1 - down),
                        fb=20 - 40 * (1 - down), lean=8 * down, look=1, lookY=0.8))
    bg.table(c, 700, 1400, 560)
    paper_pile(c, 700, 1360, 6, n_st)


def s_fake_cam(f):
    hits = [f.T.word(0, "fake"), f.T.word(0, "government"), f.T.word(0, "papers")]
    return dict(z=1.25, y=1180, x=560, shake=max(pulse(f.t, h, 0.18) for h in hits) * 10)


# 7. DEALERS ARRIVE
def s_arrive_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hotel(c, f.gt)
    tin = T.word(0, "invited")
    th = T.word(0, "hotel")
    f.char(LUSTIG, dict(x=230, y=GI, s=S, face=1, expr="smug", fa=tween(t, tin, tin + 0.3, 10, 95, "back"), fb=-10,
                        ba=-10))
    arrive = [(DEALER_B, 1000, 1.25, 0.0), (DEALER_A, 840, 1.3, 0.15), (POISSON, 650, 1.38, 0.3)]
    for ch, xe, s, dl in arrive:
        t0 = tin + dl
        x = tween(t, t0, t0 + 1.3, 1350 + dl * 300, xe, "out")
        moving = t0 < t < t0 + 1.2
        f.char(ch, dict(x=x, y=GI - (1.38 - s) * 120, s=s, face=-1, walk=2.2 if moving else 0,
                        expr="excited" if t > th else "neutral", look=-0.6))
    label(c, "FANCY HOTEL", 540, 120 + 60, f.r(th, th + 0.25), size=44)


def s_arrive_cam(f):
    return dict(z=1.0)


# 8. THE PITCH (Lustig speaks)
def s_pitch_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hotel(c, f.gt)
    tt = T.word(0, "tearing")
    tb = T.word(1, "buy")
    tn = T.word(1, "no", nth=0)
    shh = f.r(tn - 0.2, tn)
    f.char(LUSTIG, dict(x=210, y=GI, s=S, face=1, expr="sly" if t > tb else "smug",
                        fa=tween(t, 0, 0.4, 10, 100) * (1 - shh) + 165 * shh,
                        fb=-15 * (1 - shh) + 40 * shh, lean=4))
    shock = t > tt
    for ch, x, s in ((DEALER_B, 1010, 1.25), (DEALER_A, 870, 1.3), (POISSON, 700, 1.38)):
        lean = tween(t, tb, tb + 0.4, 0, 14)
        f.char(ch, dict(x=x, y=GI - (1.38 - s) * 120, s=s, face=-1,
                        expr="greedy" if (t > tb and ch is POISSON) else ("shock" if shock else "neutral"),
                        lean=lean, jump=18 * pulse(t, tt, 0.3), look=-0.8,
                        fa=60 if shock else 10, fb=80 if shock else 12))


def s_pitch_cam(f):
    tb = f.T.word(1, "buy")
    x = tween(f.t, tb - 0.3, tb + 0.3, 400, 760)
    return dict(z=tween(f.t, 0, 0.6, 1.45, 1.35), x=x, y=1080)


# 9. POISSON
def s_poisson_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hotel(c, f.gt)
    f.char(POISSON, dict(x=600, y=GI, s=1.5, face=-1, expr="greedy", **rubbing(f.gt), jump=8 * abs(math.sin(t * 6))))
    tb = T.word(0, "badly")
    bg.sparkle_burst(c, 600, 900, f.r(tb, tb + 0.6), n=10, r=220)


def s_poisson_overlay(f):
    tw = f.T.word(0, "Andr")
    label(f.ctx, "ANDRÉ POISSON", 540, 330, f.r(tw, tw + 0.25), color="#e8902a")
    label(f.ctx, "SCRAP METAL DEALER", 540, 450, f.r(tw + 0.2, tw + 0.45), color="#ffffff", size=40)


def s_poisson_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.3, 1.5), x=600, y=1120)


# 10. BRIBE HINT
def s_bribe_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hotel(c, f.gt)
    tb = T.word(0, "bribe")
    rub = math.sin(f.gt * 14) * 10 if t > tb - 0.4 else 0
    f.char(LUSTIG, dict(x=360, y=GI, s=S, face=1, expr="sly", fa=60 + rub, fb=60, look=1, tilt=6))
    f.char(POISSON, dict(x=760, y=GI, s=1.4, face=-1, expr="worried" if t > tb else "neutral",
                         sweat=f.r(tb, tb + 0.3), lean=-6 * f.r(tb, tb + 0.3)))
    if t > tb:
        # tiny floating "$?" thought to sell the hint
        p = f.r(tb, tb + 0.25)
        text_center(c, "?", 600, 760 - 30 * p, 130 * EASES["back"](p) + 1, "#ffd84a", stroke=12)


def s_bribe_cam(f):
    return dict(z=1.3, x=560, y=1060)


# 11. POISSON CONVINCED (Poisson speaks)
def s_convinced_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hotel(c, f.gt)
    tr = T.word(0, "real")
    tc = T.word(0, "corrupt")
    give = f.r(tc - 0.2, tc + 0.25)
    f.char(LUSTIG, dict(x=330, y=GI, s=S, face=1, expr="grin" if t > tc else "sly",
                        fa=95 * give + 10, fb=-10 * give + 12, hold="moneybag" if t > tc + 0.1 else None))
    f.char(POISSON, dict(x=tween(t, tc - 0.5, tc, 760, 640), y=GI, s=1.4, face=-1,
                         expr="excited" if t > tr - 0.2 else "shock", fa=95 if t < tc + 0.1 else 20, fb=-10,
                         hold="moneybag" if t <= tc + 0.1 else None, jump=14 * pulse(t, tr - 0.2, 0.3)))
    bulb(c, 700, 640, f.r(tr - 0.25, tr) * (1 - f.r(tc, tc + 0.2)))
    coins_rain(c, t, tc, 480, 1050)


def s_convinced_cam(f):
    tc = f.T.word(0, "corrupt")
    return dict(z=1.3, x=520, y=1060, shake=8 * pulse(f.t, tc, 0.25))


# 12. FLEE TO AUSTRIA
def s_flee_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hills(c, f.gt)
    ta = T.word(0, "Austria")
    x = tween(t, 0, ta + 0.2, -250, 470, "out")
    running = t < ta + 0.1
    f.char(LUSTIG, dict(x=x, y=G, s=S, face=1, run=3 if running else 0, hold="moneybag", hold_back="moneybag",
                        fa=60, fb=20, expr="grin", look=1))
    bg.dust(c, x - 100, G, (t % 0.5) / 0.5 if running else f.r(ta + 0.1, ta + 0.6))


def s_flee_cam(f):
    return dict(z=1.05)


# 13. WAITING FOR NEWS
def s_wait_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.hills(c, f.gt)
    tn = T.word(1, "Nothing")
    look = math.sin(t * 4) if t < tn else 0
    f.char(LUSTIG, dict(x=470, y=G, s=S, face=1, hold="newspaper", fa=70, fb=40,
                        expr="worried" if t < tn else "smug", look=look, sweat=1 - f.r(tn, tn + 0.3),
                        ba=-10 + 70 * f.r(tn, tn + 0.3), bb=12 + 80 * f.r(tn, tn + 0.3)))


def s_wait_cam(f):
    return dict(z=tween(f.t, 0, f.dur, 1.35, 1.55), x=500, y=1120)


# 14. TOO EMBARRASSED
def s_shame_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.police(c, f.gt)
    te = T.word(0, "embarrassed")
    if t < te:
        x = tween(t, 0, te, 1300, 720, "out")
        pose = dict(x=x, y=GI, s=1.4, face=-1, walk=2.0 if t < te - 0.1 else 0, expr="worried", look=-0.5)
    else:
        x = tween(t, te + 0.5, f.dur, 720, 950, "in")
        pose = dict(x=x, y=GI, s=1.4, face=1 if t > te + 0.45 else -1, walk=1.6 if t > te + 0.5 else 0,
                    expr="embarrassed", fa=140, fb=60, ba=140, bb=60, tilt=10)
    f.char(POISSON, pose)
    f.char(POLICE, dict(x=330, y=GI, s=1.35, face=1, expr="neutral", look=1))


def s_shame_cam(f):
    return dict(z=1.3, x=620, y=1130)


# 15. CAME BACK – AGAIN
def s_again_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.paris(c, f.gt)
    sold_sign(c, 540, 800, 1, rot=-8)
    ta = T.word(1, "again")
    x = tween(t, 0, ta - 0.6, -250, 270, "out")
    f.char(LUSTIG, dict(x=x, y=G, s=S, face=1, walk=2.0 if t < ta - 0.65 else 0, hold="contract",
                        fa=tween(t, ta - 0.5, ta - 0.1, 10, 95), fb=-10,
                        expr="wink" if t > ta else "sly"))
    f.char(BUYER2, dict(x=tween(t, 0, ta - 0.4, 1300, 830, "out"), y=G, s=1.5, face=-1,
                        walk=2.0 if t < ta - 0.45 else 0, expr="excited" if t > ta - 0.4 else "neutral"))
    sold_sign(c, 560, 560, f.r(ta, ta + 0.16, "out"), rot=7, txt="AGAIN!", color="#e8902a")
    tg = T.word(0, "story")
    label(c, "(the story goes)", 540, 330, f.r(tg, tg + 0.2) * (1 - f.r(ta, ta + 0.2)), color="#ffffff", size=44)


def s_again_cam(f):
    ta = f.T.word(1, "again")
    return dict(shake=12 * pulse(f.t, ta + 0.12, 0.25))


# 16. POLICE
def s_police_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.police(c, f.gt)
    tp = T.word(0, "police")
    f.char(BUYER2, dict(x=720, y=GI, s=1.4, face=-1, expr="angry", fa=tween(t, 0, 0.4, 10, 100), fb=-10,
                        jump=20 * abs(math.sin(t * 7)) if t < tp else 0))
    f.char(POLICE, dict(x=330, y=GI, s=1.4, face=1, expr="angry" if t > tp else "shock", hold="whistle",
                        fa=tween(t, tp - 0.35, tp - 0.05, 10, 160), fb=tween(t, tp - 0.35, tp - 0.05, 12, 80)))


def s_police_cam(f):
    tp = f.T.word(0, "police")
    return dict(z=tween(f.t, 0, tp, 1.1, 1.3), x=540, y=1100, shake=6 * pulse(f.t, tp, 0.5))


# 17. ESCAPE
def s_escape_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.paris(c, f.gt)
    sold_sign(c, 540, 800, 1, rot=-8)
    te = T.word(1, "escaped")
    if t < te:
        f.char(LUSTIG, dict(x=780, y=G, s=S, face=-1, expr="shock", look=0, jump=25 * pulse(t, 0.0, 0.3),
                            fa=60, fb=80, ba=60, bb=80))
    else:
        x = tween(t, te, te + 0.5, 780, 1500, "in")
        f.char(LUSTIG, dict(x=x, y=G, s=S, face=1, run=3.5, expr="grin", hat_off=0.3))
        bg.dust(c, 820, G, f.r(te, te + 0.6))
        bg.speed_lines(c, pulse(t, te, 0.6))
    ta = T.word(1, "Again")
    if t > ta - 0.2:
        x = tween(t, ta - 0.2, ta + 0.4, -250, 420, "out")
        f.char(POLICE, dict(x=x, y=G, s=1.4, face=1, run=3 if t < ta + 0.35 else 0, expr="angry",
                            hold="whistle", fa=160 if t > ta + 0.35 else 30, fb=80))


def s_escape_cam(f):
    return dict(z=1.05)


# 18. ENDING – loops back to the hook frame
def s_end_draw(f):
    c, t, T = f.ctx, f.t, f.T
    bg.paris(c, f.gt)
    tn = T.word(0, "Never")
    tt = T.word(1, "twice")
    # signs pulled off on "never sold", slapped back on "twice"
    off = f.r(tn, tn + 0.3)
    on1 = f.r(tt, tt + 0.16, "out")
    on2 = f.r(tt + 0.2, tt + 0.36, "out")
    if t < tt:
        sold_sign(c, 540, 800 + 900 * EASES["in"](off), 1 if off < 1 else 0, rot=-8 + 40 * off)
    else:
        sold_sign(c, 540, 800, on1, rot=-8)
        sold_sign(c, 560, 990, on2, rot=7, txt="AGAIN?!", color="#e8902a")
    pop = f.r(tt - 0.3, tt + 0.1, "back")
    f.char(LUSTIG, dict(x=820, y=G + 1600 * (1 - pop), s=S, face=-1, expr="wink" if t > tt + 0.2 else "smug",
                        fa=125 * pop, fb=-15, hat_off=pulse(t, tt + 0.2, 0.7)))


def s_end_cam(f):
    tt = f.T.word(1, "twice")
    return dict(z=tween(f.t, 0, tt, 1.08, 1.0), shake=10 * pulse(f.t, tt + 0.1, 0.25) + 8 * pulse(f.t, tt + 0.3, 0.25))


# ------------------------------------------------------------------ assemble
def cues_hook(T):
    ts = T.word(0, "sold")
    return [(0.0, "dun", 0.8), (ts, "stamp", 1.0)]


SCENES = [
    Scene("hook", [N("In 1925, a man sold the Eiffel Tower.", spoken="In nineteen twenty-five, a man sold the Eiffel Tower.")], s_hook_draw, s_hook_cam, cues=cues_hook, pad=0.15),
    Scene("came_back", [N("Then he came back... and tried to sell it again!")], s_back_draw, s_back_cam,
          cues=lambda T: [(0.1, "run", 0.6), (T.word(0, "came"), "whoosh", 0.6), (T.word(0, "came") + 0.3, "steps", 0.6),
                          (T.word(0, "again"), "stamp", 1.0)], pad=0.25),
    Scene("who", [N("His name was Victor Lustig."), N("A con man... who did NOT own the tower.")], s_who_draw,
          overlay=s_who_overlay, trans="whip",
          cues=lambda T: [(T.word(0, "Victor"), "pop", 0.8), (T.word(1, "con"), "pop", 0.7),
                          (T.word(1, "NOT"), "boing", 0.7)]),
    Scene("news", [N("He read that the tower was rusting, and repairs would cost a fortune.")], s_news_draw,
          s_news_cam, trans="whip", cues=lambda T: [(T.word(0, "fortune"), "chaching", 0.6)]),
    Scene("idea", [N("So he had an idea.")], s_idea_draw, s_idea_cam, trans="punch",
          cues=lambda T: [(T.word(0, "idea"), "ding", 0.9)], pad=0.35),
    Scene("fake", [N("He printed fake government papers,")], s_fake_draw, s_fake_cam, trans="whip",
          cues=lambda T: [(T.word(0, w), "stamp", 0.9) for w in ("fake", "government", "papers")], pad=0.1),
    Scene("arrive", [N("and invited scrap dealers to a fancy hotel.", gap=0.0)], s_arrive_draw, s_arrive_cam,
          cues=lambda T: [(T.word(0, "invited"), "steps", 0.7), (T.word(0, "hotel"), "pop", 0.6)], pad=0.35),
    Scene("pitch", [Say(LUSTIG, "Gentlemen. The city is tearing down the tower."),
                    Say(LUSTIG, "You may buy the metal... but tell no one.")], s_pitch_draw, s_pitch_cam,
          trans="punch", cues=lambda T: [(T.word(0, "tearing") + 0.1, "gasp", 0.9), (T.word(1, "buy"), "ding", 0.5)]),
    Scene("poisson", [N("One dealer, André Poisson, wanted it badly.")], s_poisson_draw, s_poisson_cam,
          overlay=s_poisson_overlay, trans="whip",
          cues=lambda T: [(T.word(0, "Andr"), "pop", 0.8), (T.word(0, "badly"), "reveal", 0.6)]),
    Scene("bribe", [N("Then Lustig hinted... he wanted a bribe.")], s_bribe_draw, s_bribe_cam, trans="cut",
          cues=lambda T: [(T.word(0, "bribe"), "dun", 0.7)]),
    Scene("convinced", [Say(POISSON, "A bribe?! Only a REAL official would be this corrupt!", speed=1.25)], s_convinced_draw,
          s_convinced_cam, trans="punch",
          cues=lambda T: [(T.word(0, "real") - 0.25, "ding", 0.7), (T.word(0, "corrupt"), "chaching", 1.0)]),
    Scene("flee", [N("Lustig grabbed the money and fled to Austria.")], s_flee_draw, s_flee_cam, trans="whip",
          cues=lambda T: [(0.0, "run", 0.6), (0.6, "run", 0.6), (T.word(0, "Austria"), "pop", 0.5)]),
    Scene("wait", [N("He checked the newspapers every day."), N("Nothing.", gap=0.35)], s_wait_draw, s_wait_cam,
          cues=lambda T: [(T.word(1, "Nothing"), "crickets", 0.9)], pad=0.6),
    Scene("shame", [N("Poisson was too embarrassed to tell the police.")], s_shame_draw, s_shame_cam,
          trans="whip", cues=lambda T: [(0.1, "steps", 0.6), (T.word(0, "embarrassed"), "fail", 0.7)], pad=0.5),
    Scene("again", [N("So, the story goes,"), N("Lustig came back... and tried the whole trick again!")],
          s_again_draw, s_again_cam, trans="whip",
          cues=lambda T: [(0.2, "steps", 0.6), (T.word(1, "again"), "stamp", 1.0)]),
    Scene("police", [N("But this time, the buyer went to the police!")], s_police_draw, s_police_cam, trans="whip",
          cues=lambda T: [(T.word(0, "police"), "whistle", 0.8)]),
    Scene("escape", [N("And Lustig?"), N("He escaped. Again.", gap=0.25)], s_escape_draw, s_escape_cam,
          trans="whip",
          cues=lambda T: [(0.05, "dun", 0.6), (T.word(1, "escaped"), "zip", 0.9), (T.word(1, "escaped"), "whoosh", 0.8),
                          (T.word(1, "Again"), "whistle", 0.6)]),
    Scene("end", [N("The tower still stands today. Never sold..."), N("Well... twice.", gap=0.3)], s_end_draw,
          s_end_cam, trans="fade",
          cues=lambda T: [(T.word(0, "Never"), "whoosh", 0.6), (T.word(1, "twice"), "stamp", 1.0),
                          (T.word(1, "twice") + 0.2, "stamp", 1.0), (T.word(1, "twice") + 0.5, "ding", 0.6)],
          pad=0.6),
]

EPISODE = Episode("eiffel_tower", SCENES, narrator_voice="am_michael",
                  voices={"lustig": "bm_george", "poisson": "am_puck"}, speed=1.2,
                  pronounce={"André": "ɑːndɹˈeɪ", "Poisson": "pwɑːsˈɔːn"})
