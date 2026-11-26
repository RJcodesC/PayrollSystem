import os, sys, math
sys.path.insert(0, os.getcwd()); sys.path.insert(0, "episodes/emu_war")
import cairo
from cast import *
from engine.rig import LIMB_ISSUES
from engine.creatures import lewis_gun
from engine.text import text_center
W, H = 2400, 1500
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
c = cairo.Context(surf)
g = cairo.LinearGradient(0, 0, 0, H)
g.add_color_stop_rgb(0, 0.98, 0.86, 0.62); g.add_color_stop_rgb(1, 0.93, 0.62, 0.36)
c.rectangle(0, 0, W, H); c.set_source(g); c.fill()
text_center(c, "THE GREAT EMU WAR · CHARACTER SHEET", W / 2, 60, 60, "#ffffff", stroke=10)
def ground(y):
    c.set_source_rgba(0, 0, 0, 0.12); c.rectangle(0, y, W, 6); c.fill()
def lab(t, x, y): text_center(c, t, x, y, 34, "#ffffff", stroke=8)
S = 0.95
Y1 = 690; ground(Y1)
row = [(MAJOR, "THE MAJOR"), (SGT, "SERGEANT"), (GUNNER, "GUNNER"), (FARMER, "FARMER")]
for i, (ch, name) in enumerate(row):
    x = 260 + i * 400
    if ch is MAJOR:
        ch.draw(c, dict(x=x, y=Y1, s=S, face=1, idle=0, blink=0, expr="smug", **REST), 0)
        lab(name, x, Y1 + 50)
        continue
    ch.draw(c, dict(x=x, y=Y1, s=S, face=1, idle=0, blink=0, expr="neutral", **REST), 0)
    lab(name, x, Y1 + 50)
EMU.draw(c, dict(x=1980, y=Y1, s=S * 1.0, face=-1, expr="stare"), 0)
lab("THE EMU", 1950, Y1 + 50)
# key poses
Y2 = 1380; ground(Y2)
# 1 gunner crouched behind the Lewis gun, hands on it via IK
gx, gy = 300, Y2 - 150
pts = lewis_gun(c, gx, gy, 0.8, face=1, angle=4, t=0.1, fire=1.0)
GUNNER.draw(c, dict(x=gx - 90, y=Y2, s=S, face=1, idle=0, blink=0, expr="angry", crouch=0.55,
                    hand_f_at={"world": pts["grip"]}, hand_b_at={"world": pts["fore"]}, lean=14), 0)
lewis_gun(c, gx, gy, 0.8, face=1, angle=4, t=0.1, fire=1.0)
lab("AIM (IK hands on gun)", 330, Y2 + 50)
# 2 major pointing
MAJOR.draw(c, dict(x=760, y=Y2, s=S, face=1, idle=0, blink=0, expr="angry", **POINT), 0)
lab("POINT", 790, Y2 + 50)
# 3 sergeant, hands on head (shock)
SGT.draw(c, dict(x=1120, y=Y2, s=S, face=1, idle=0, blink=0, expr="shock", **HANDS_UP), 0)
lab("SHOCK", 1120, Y2 + 50)
# 4 farmer facepalm
FARMER.draw(c, dict(x=1440, y=Y2, s=S, face=1, idle=0, blink=0, expr="sad", **FACEPALM), 0)
lab("FACEPALM", 1440, Y2 + 50)
# 5 emu running / angry / pecking
EMU.draw(c, dict(x=1790, y=Y2, s=0.8, face=1, run=1.6, expr="angry", dust=1), 0.13)
lab("RUN", 1790, Y2 + 50)
EMU2.draw(c, dict(x=2150, y=Y2, s=0.8, face=-1, expr="smug", peck=0.0, neck=0.8, head_tilt=-8), 0)
lab("SMUG", 2150, Y2 + 50)
surf.write_to_png(sys.argv[1])
print("limb issues:", LIMB_ISSUES)
