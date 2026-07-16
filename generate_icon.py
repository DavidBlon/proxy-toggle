"""Generate the multi-resolution Windows application icon."""

from pathlib import Path
from PIL import Image, ImageDraw


def make_icon(size):
    scale = size / 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    box = lambda values: tuple(round(value * scale) for value in values)
    width = max(1, round(18 * scale))

    draw.rounded_rectangle(box((8, 8, 248, 248)), radius=round(58 * scale), fill="#0E1726")
    draw.rounded_rectangle(box((20, 20, 236, 236)), radius=round(48 * scale), outline="#24334A", width=max(1, round(3 * scale)))
    draw.line(box((68, 82, 188, 82)), fill="#25D366", width=width)
    draw.line(box((68, 174, 188, 174)), fill="#25D366", width=width)
    draw.line(box((83, 101, 173, 155)), fill="#25D366", width=max(1, round(15 * scale)))
    draw.ellipse(box((45, 55, 109, 119)), fill="#F5F7FA")
    draw.ellipse(box((147, 137, 211, 201)), fill="#F5F7FA")
    draw.ellipse(box((65, 75, 89, 99)), fill="#25D366")
    draw.ellipse(box((167, 157, 191, 181)), fill="#25D366")
    return image


output = Path(__file__).parent / "assets" / "proxy_toggle.ico"
output.parent.mkdir(exist_ok=True)
base = make_icon(256)
base.save(output, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(output)
