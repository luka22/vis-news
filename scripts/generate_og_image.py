#!/usr/bin/env python3
"""
Generates docs/og-image.png — the social-share card for issa.news.
Run manually whenever the masthead branding changes; not part of the
regular pipeline (main.py never touches this file).
"""
import io
import math
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent
OUT = ROOT / "docs" / "og-image.png"
CREST_URL = "https://www.gradvis.hr/wp-content/uploads/2019/06/grb_vis.png"

W, H = 1200, 630

PAPER = "#fdf8f0"
NAVY = "#0f3050"
SEA = "#1a4a6b"
RED = "#D4002A"
MUTED = "#7a6f5c"
HAIRLINE = "#d9cebc"

FONT_PATH = "/System/Library/Fonts/Supplemental/Charter.ttc"


def font(index: int, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size, index=index)


def fetch_crest() -> Image.Image:
    with urllib.request.urlopen(CREST_URL) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGBA")


def coastline_band(draw: ImageDraw.ImageDraw, top_y: int) -> None:
    """A horizon-line wave separating the paper above from a navy band below."""
    amplitude, wavelength = 20, 460
    points = [(0, H)]
    for x in range(0, W + 1, 4):
        y = top_y + amplitude * math.sin((x / wavelength) * 2 * math.pi)
        points.append((x, y))
    points.append((W, H))
    draw.polygon(points, fill=NAVY)


def main() -> None:
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # top flag stripe
    draw.rectangle([0, 0, W, 8], fill=RED)

    # crest
    crest = fetch_crest()
    crest_h = 132
    crest_w = round(crest.width * crest_h / crest.height)
    crest_resized = crest.resize((crest_w, crest_h), Image.LANCZOS)
    crest_x, crest_y = 90, 64
    img.paste(crest_resized, (crest_x, crest_y), crest_resized)

    # masthead
    title_x = crest_x + crest_w + 34
    draw.text((title_x, crest_y - 6), "Viške novosti", font=font(3, 84), fill=NAVY)
    draw.text((title_x + 4, crest_y + 92), "Vis Island News", font=font(1, 38), fill=SEA)

    # hairline + tagline
    rule_y = 250
    draw.line([(90, rule_y), (W - 90, rule_y)], fill=HAIRLINE, width=2)
    draw.text(
        (90, rule_y + 26),
        "Dnevne vijesti s otoka Visa — daily news from Vis island, Croatia",
        font=font(0, 29),
        fill=MUTED,
    )

    # coastline signature + wordmark
    coastline_band(draw, top_y=400)
    draw.text((90, 500), "I S S A . N E W S", font=font(3, 34), fill=PAPER)

    img.save(OUT)
    print(f"wrote {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
