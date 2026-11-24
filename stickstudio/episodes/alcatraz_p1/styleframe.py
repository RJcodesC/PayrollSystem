"""Style test: 'The Alcatraz Escape' series – flat, bright, Ricks-Clips-like look (original art)."""
import math, os, sys
import cairo
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from engine import bg
from engine.core import hexc
from engine.rig import Character, Look, INK
from engine.text import text_center, text_width

FRANK = Character("frank", Look(coat="#e8e2cf", coat_dark="#c9c0a5", hair="side", skin="#f6efe6"), seed=0.4)
GUARD = Character("guard", Look(coat="#3d5a8a", coat_dark="#2b4168", hat="kepi", hat_color="#2b3a55",
                               hat_band="#d9b44a", badge=True, mustache="thick"), seed=2.2)


def cell(ctx):
    # warm flat wall, floor in perspective, bunk, sink, the vent
    ctx.rectangle(-200, -200, 1500, 2400); ctx.set_source_rgb(*hexc("#d9c7a3")); ctx.fill()
    for y in range(-100, 1500, 90):
        for k, x in enumerate(range(-200, 1300, 180)):
            ctx.rectangle(x + (90 if (y // 90) % 2 else 0), y, 176, 86)
            ctx.set_source_rgb(*hexc("#cfbb94" if (k + y // 90) % 3 else "#d4c19b")); ctx.fill()
    ctx.move_to(-200, 1450); ctx.line_to(1300, 1450); ctx.line_to(1300, 2200); ctx.line_to(-200, 2200); ctx.close_path()
    ctx.set_source_rgb(*hexc("#8d8f94")); ctx.fill()
    ctx.move_to(-200, 1450); ctx.line_to(1300, 1450); ctx.set_source_rgb(*INK); ctx.set_line_width(7); ctx.stroke()
    # bunk
    bg.rect(ctx, 600, 1180, 520, 70, "#6d7f99"); bg.rect(ctx, 610, 1150, 500, 40, "#f2efe6", 5)
    for x in (620, 1080): bg.rect(ctx, x, 1250, 22, 200, "#55595f", 5)
    # sink + vent (the escape hole)
    bg.rect(ctx, 120, 1050, 230, 90, "#eef0f2"); bg.rect(ctx, 215, 1140, 40, 120, "#bfc3c8", 5)
    bg.rect(ctx, 130, 1290, 210, 140, "#5e6268", 6)
    ctx.set_source_rgb(*hexc("#2c2f33")); ctx.set_line_width(6)
    for i in range(1, 6):
        ctx.move_to(130 + i * 35, 1295); ctx.line_to(130 + i * 35, 1425)
    ctx.stroke()
    # crumbled concrete chips around the vent
    for (x, y, r) in ((150, 1440, 9), (190, 1452, 7), (300, 1446, 11), (330, 1458, 6)):
        ctx.arc(x, y, r, 0, 2 * math.pi); ctx.set_source_rgb(*hexc("#b9a67f")); ctx.fill_preserve()
        ctx.set_source_rgb(*INK); ctx.set_line_width(3); ctx.stroke()
    # cell bars in the foreground (left & right edges, keep centre clear)
    for x in (-40, 30, 1010, 1080):
        bg.rect(ctx, x, -200, 34, 2400, "#4a4f57", 5)
    # moon window
    bg.rect(ctx, 470, 330, 160, 160, "#1f2a44", 7)
    ctx.arc(560, 390, 28, 0, 2 * math.pi); ctx.set_source_rgb(*hexc("#fff3b0")); ctx.fill()
    for x in (510, 550, 590): bg.rect(ctx, x, 330, 10, 160, "#4a4f57", 3)


def spoon(ctx, x, y):
    ctx.save(); ctx.translate(x, y); ctx.rotate(math.radians(35))
    bg.rect(ctx, -5, -60, 10, 60, "#c9ced6", 3)
    ctx.save(); ctx.translate(0, -72); ctx.scale(14, 20); ctx.arc(0, 0, 1, 0, 2 * math.pi); ctx.restore()
    ctx.set_source_rgb(*hexc("#dfe3ea")); ctx.fill_preserve(); ctx.set_source_rgb(*INK); ctx.set_line_width(3); ctx.stroke()
    ctx.restore()


surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 1920)
c = cairo.Context(surf)
cell(c)
pts = FRANK.draw(c, dict(x=520, y=1540, s=1.6, face=-1, lean=22, jump=-150, expr="sly", fa=58, fb=8,
                         ba=40, bb=40, fl=85, fk=120, bl=40, bk=120, look=-1, lookY=0.7, idle=0), 1.0)
hx, hy = pts["hand_f"]  # rig returns character-local coords: convert to world
spoon(c, 520 + hx * 1.6, 1540 + 150 + hy * 1.6)
# series header + caption, Ricks-style clean type
c.rectangle(0, 0, 1080, 210); c.set_source_rgba(0, 0, 0, 0.0); c.fill()
text_center(c, "THE ALCATRAZ ESCAPE", 540, 110, 74, "#ffffff", stroke=14)
text_center(c, "PART 1 · THE SPOON", 540, 190, 54, "#ffd84a", stroke=12)
text_center(c, "HE DUG FOR MONTHS...", 540, 1640, 82, "#ffffff", stroke=16)
text_center(c, "WITH A SPOON.", 540, 1740, 82, "#ffd84a", stroke=16)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "styleframe.png")
surf.write_to_png(out)
print(out)
