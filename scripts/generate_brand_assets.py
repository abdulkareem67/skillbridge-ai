"""Generate the favicon and social-card images.

Run from the repo root after changing the brand:

    python scripts/generate_brand_assets.py

The output is committed, so the app never needs Pillow at runtime — this is a
build-time tool. Keeping it in the repo means the assets can be regenerated
rather than being mystery binaries nobody can reproduce.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "backend" / "app" / "static" / "img"

INK = (238, 240, 251)
MUTED = (154, 163, 199)
BG = (11, 15, 28)
ACCENT = (109, 91, 248)
ACCENT_2 = (34, 211, 238)

# Whatever the machine has; the layout is measured, so a substitution only
# changes the typeface, never the composition.
FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
FONT_CANDIDATES_REGULAR = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def load_font(size: int, bold: bool = True):
    for path in FONT_CANDIDATES if bold else FONT_CANDIDATES_REGULAR:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))


def bolt_polygon(cx: float, cy: float, size: float):
    """A lightning bolt centred on (cx, cy), matching the ⚡ in the wordmark."""
    unit = [
        (0.52, 0.0), (0.16, 0.54), (0.44, 0.54),
        (0.34, 1.0), (0.80, 0.42), (0.50, 0.42), (0.66, 0.0),
    ]
    return [(cx + (x - 0.48) * size, cy + (y - 0.5) * size) for x, y in unit]


def draw_gradient_bolt(img: Image.Image, cx: float, cy: float, size: float):
    """Fill the bolt with the brand gradient by masking a gradient block."""
    gradient = Image.new("RGB", (int(size), int(size)))
    g = ImageDraw.Draw(gradient)
    for x in range(int(size)):
        g.line([(x, 0), (x, size)], fill=lerp(ACCENT, ACCENT_2, x / max(size - 1, 1)))

    mask = Image.new("L", (int(size), int(size)), 0)
    ImageDraw.Draw(mask).polygon(bolt_polygon(size / 2, size / 2, size), fill=255)
    img.paste(gradient, (int(cx - size / 2), int(cy - size / 2)), mask)


def make_og_image() -> None:
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # Soft diagonal wash so the card isn't a flat rectangle.
    for y in range(h):
        t = y / h
        draw.line([(0, y), (w, y)], fill=lerp(BG, (22, 28, 52), t * 0.9))

    draw.rectangle([0, 0, w, 8], fill=ACCENT)
    for x in range(w):
        draw.line([(x, 0), (x, 8)], fill=lerp(ACCENT, ACCENT_2, x / w))

    draw_gradient_bolt(img, 118, 150, 76)

    draw.text((168, 112), "SkillBridge AI", font=load_font(58), fill=INK)

    headline = load_font(64)
    draw.text((96, 250), "Find the skills you're", font=headline, fill=INK)
    draw.text((96, 326), "missing for your target job", font=headline, fill=INK)

    draw.text(
        (96, 430),
        "Upload your CV · See your match score · Get a free roadmap",
        font=load_font(30, bold=False),
        fill=MUTED,
    )

    draw.rectangle([96, 506, 316, 512], fill=ACCENT_2)

    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / "og-image.png", optimize=True)
    print("wrote og-image.png (1200x630)")


def make_icons() -> None:
    master = 512
    base = Image.new("RGB", (master, master), BG)
    ImageDraw.Draw(base).rounded_rectangle([0, 0, master, master], radius=112, fill=BG)
    draw_gradient_bolt(base, master / 2, master / 2, master * 0.62)

    rounded = Image.new("RGBA", (master, master), (0, 0, 0, 0))
    mask = Image.new("L", (master, master), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, master, master], radius=112, fill=255)
    rounded.paste(base, (0, 0), mask)

    rounded.resize((180, 180), Image.LANCZOS).save(OUT / "apple-touch-icon.png")
    print("wrote apple-touch-icon.png (180x180)")

    rounded.save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    print("wrote favicon.ico (16/32/48)")


def make_favicon_svg() -> None:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="SkillBridge AI">
  <defs>
    <linearGradient id="b" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#6d5bf8"/><stop offset="1" stop-color="#22d3ee"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="#0b0f1c"/>
  <path d="M35 10 L15 36 h16 L26 54 L49 26 H32 z" fill="url(#b)"/>
</svg>
"""
    (OUT / "favicon.svg").write_text(svg, encoding="utf-8")
    print("wrote favicon.svg")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    make_og_image()
    make_icons()
    make_favicon_svg()
