import cairo
from .core import hexc

FONT = "Inter Display Black"


def text_center(ctx, txt, x, y, size, color, font=FONT, stroke=0, stroke_color="#141418", anchor="center"):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    ext = ctx.text_extents(txt)
    if anchor == "center":
        tx = x - ext.width / 2 - ext.x_bearing
    else:
        tx = x - ext.x_bearing
    ty = y - ext.height / 2 - ext.y_bearing
    ctx.new_path()
    ctx.move_to(tx, ty)
    ctx.text_path(txt)
    if stroke:
        ctx.set_source_rgb(*hexc(stroke_color))
        ctx.set_line_width(stroke)
        ctx.set_line_join(1)
        ctx.stroke_preserve()
    ctx.set_source_rgb(*hexc(color) if isinstance(color, str) else color)
    ctx.fill()
    return ext


def text_width(ctx, txt, size, font=FONT):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    return ctx.text_extents(txt).x_advance
