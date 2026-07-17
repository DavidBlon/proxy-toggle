"""Shared renderer for the ProxyToggle icon.

The design mirrors ``cmd_proxy_toggle_icon.svg``: a dark rounded tile with a
terminal ``>_`` prompt and a toggle switch. ``draw_frame`` is parametrised by a
slider progress (0 = off / left, 1 = on / right) so the same routine renders
both the static application icon and every frame of the tray animation.
"""

from PIL import Image, ImageDraw, ImageFont

# Logical canvas of the source SVG; everything is drawn in these coordinates
# and then scaled to the requested pixel size.
CANVAS = 680
FONT_PATH = r"C:\Windows\Fonts\consolb.ttf"

# Toggle track geometry (matches the SVG).
TRACK_LEFT, TRACK_TOP = 180, 380
TRACK_RIGHT, TRACK_BOTTOM = 500, 520
TRACK_MID_Y = (TRACK_TOP + TRACK_BOTTOM) / 2
KNOB_R = 52
KNOB_MIN_X, KNOB_MAX_X = TRACK_LEFT + KNOB_R, TRACK_RIGHT - KNOB_R  # 232 .. 448

COLOR_OFF_TRACK = (51, 65, 85, 255)      # #334155
COLOR_ON_TRACK = (34, 197, 94, 255)      # #22c55e
COLOR_BG_TOP = (30, 42, 74)              # #1e2a4a
COLOR_BG_BOTTOM = (15, 23, 42)           # #0f172a
COLOR_PROMPT = (56, 189, 248, 255)       # #38bdf8
COLOR_TRACK_FILL = (11, 18, 32, 255)     # #0b1220
COLOR_TRACK_STROKE = (51, 65, 85, 255)   # #334155


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_color(c1, c2, t):
    return tuple(round(_lerp(c1[i], c2[i], t)) for i in range(len(c1)))


def _diagonal_gradient(size, top, bottom):
    """Top-left -> bottom-right linear gradient."""
    img = Image.new("RGB", (size, size))
    px = img.load()
    denom = 2 * (size - 1)
    for y in range(size):
        for x in range(size):
            px[x, y] = _lerp_color(top, bottom, (x + y) / denom)
    return img


def _rounded_alpha(size, box, radius):
    """Alpha mask: opaque inside a rounded rectangle, transparent outside."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


def draw_frame(size, progress=1.0):
    """Render the icon at ``size`` px with the slider at ``progress`` (0..1)."""
    scale = size / CANVAS
    box = lambda v: tuple(round(c * scale) for c in v)

    # --- background tile with diagonal gradient, clipped to a rounded square ---
    tile = box((90, 90, 590, 590))
    radius = round(110 * scale)
    bg = _diagonal_gradient(size, COLOR_BG_TOP, COLOR_BG_BOTTOM).convert("RGBA")
    bg.putalpha(_rounded_alpha(size, tile, radius))

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    image.alpha_composite(bg)
    draw = ImageDraw.Draw(image)

    # --- terminal prompt ">_" ---
    try:
        font = ImageFont.truetype(FONT_PATH, round(120 * scale))
    except OSError:
        font = ImageFont.load_default()
    draw.text(box((185, 180)), ">", font=font, fill=COLOR_PROMPT)
    draw.text(box((290, 180)), "_", font=font, fill=COLOR_PROMPT)

    # --- toggle track (dark pill with thin stroke) ---
    track_box = box((TRACK_LEFT, TRACK_TOP, TRACK_RIGHT, TRACK_BOTTOM))
    track_radius = round(70 * scale)
    draw.rounded_rectangle(
        track_box, radius=track_radius, fill=COLOR_TRACK_FILL,
        outline=COLOR_TRACK_STROKE, width=max(1, round(3 * scale)),
    )

    # Coloured active half follows the knob side; cross-fade near the middle.
    progress = max(0.0, min(1.0, progress))
    active = _lerp_color(COLOR_OFF_TRACK, COLOR_ON_TRACK, progress)
    knob_x = _lerp(KNOB_MIN_X, KNOB_MAX_X, progress)
    if progress >= 0.5:
        active_box = box((TRACK_LEFT, TRACK_TOP, knob_x, TRACK_BOTTOM))
    else:
        active_box = box((knob_x, TRACK_TOP, TRACK_RIGHT, TRACK_BOTTOM))
    pill_mask = _rounded_alpha(size, track_box, track_radius)
    active_half = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(active_half).rounded_rectangle(
        active_box, radius=track_radius, fill=active,
    )
    clipped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    clipped.paste(active_half, (0, 0), pill_mask)
    image.alpha_composite(clipped)

    # --- knob (white with a soft vertical gradient) ---
    cx, cy = round(knob_x * scale), round(TRACK_MID_Y * scale)
    r = round(KNOB_R * scale)
    kg = Image.new("RGBA", (r * 2, r * 2), (0, 0, 0, 0))
    for yy in range(r * 2):
        t = yy / (r * 2 - 1)
        kg.paste(
            _lerp_color((255, 255, 255), (226, 232, 240), t) + (255,),
            (0, yy, r * 2, yy + 1),
        )
    knob_mask = Image.new("L", (r * 2, r * 2), 0)
    ImageDraw.Draw(knob_mask).ellipse((0, 0, r * 2 - 1, r * 2 - 1), fill=255)
    kg.putalpha(knob_mask)
    image.alpha_composite(kg, (cx - r, cy - r))

    return image
