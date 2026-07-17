"""Generate the multi-resolution Windows application icon.

Rendered by :func:`icon_render.draw_frame`, the single source of truth shared
with the tray icon, so the EXE, the window title bar and the tray all match.
"""

from pathlib import Path

from icon_render import draw_frame

output = Path(__file__).parent / "assets" / "proxy_toggle.ico"
output.parent.mkdir(exist_ok=True)
draw_frame(256, progress=1.0).save(
    output,
    format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(output)
