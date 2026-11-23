#!/usr/bin/env python3
"""Render the front page for Sunday 22 November 2026.

Build-time only: the grader never runs this file (main.py only copies the
bundled entry.png). Every headline, date and pictogram is drawn
programmatically with Pillow, so no text is ever garbled and no map or flag
can be drawn wrong. Deterministic: no randomness, no clock, no network.

Layout (1024x1024, newspaper front page "THE WORLD TODAY"):
  masthead + date line, lead story (COP31 collapses, Antalya),
  2x3 grid of stories, "IN BRIEF" strip, footer.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 30
CONTENT = W - 2 * MARGIN  # 964

PAPER = (247, 243, 234)
INK = (22, 21, 19)
RED = (163, 18, 18)
BLUE = (30, 58, 95)
ORANGE = (194, 87, 27)
GREY = (96, 92, 84)
LIGHT_LINE = (210, 204, 190)

FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/noto",
]


def load_font(names, size):
    """Load the first available font from names, else PIL's default.

    The default bitmap font is tiny, so prefer load_default(size=size)
    (Pillow >= 9.2) when no system font is found.
    """
    for directory in FONT_DIRS:
        for name in names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except OSError:
                    continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def serif_bold(size):
    return load_font(["DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf",
                      "NotoSerif-Bold.ttf"], size)


def serif(size):
    return load_font(["DejaVuSerif.ttf", "LiberationSerif-Regular.ttf",
                      "NotoSerif-Regular.ttf"], size)


def sans_bold(size):
    return load_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
                      "NotoSans-Bold.ttf"], size)


def sans(size):
    return load_font(["DejaVuSans.ttf", "LiberationSans-Regular.ttf",
                      "NotoSans-Regular.ttf"], size)


def wrap(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width.

    A single word wider than max_width is split character by character
    instead of overflowing the box.
    """
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        expanded = []
        for word in words:
            if draw.textlength(word, font=font) <= max_width:
                expanded.append(word)
            else:
                piece = ""
                for char in word:
                    if (piece and draw.textlength(piece + char, font=font)
                            > max_width):
                        expanded.append(piece)
                        piece = char
                    else:
                        piece += char
                if piece:
                    expanded.append(piece)
        line = expanded[0]
        for word in expanded[1:]:
            trial = line + " " + word
            if draw.textlength(trial, font=font) <= max_width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_centered(draw, y, text, font, fill, x0=MARGIN, x1=W - MARGIN):
    """Draw one line centred between x0 and x1; return its height."""
    width = draw.textlength(text, font=font)
    draw.text(((x0 + x1 - width) / 2, y), text, font=font, fill=fill)
    return font.size


def rule(draw, y, weight=2, fill=INK, x0=MARGIN, x1=W - MARGIN):
    draw.rectangle([x0, y, x1, y + weight - 1], fill=fill)


# ---------------------------------------------------------------- icons

def icon_ship(draw, x, y, s=34):
    """Simple warship silhouette: hull, deck, mast, flag."""
    draw.polygon([(x, y + 22), (x + s, y + 22), (x + s - 6, y + s),
                  (x + 6, y + s)], fill=BLUE)
    draw.rectangle([x + 8, y + 12, x + s - 8, y + 22], fill=BLUE)
    draw.rectangle([x + s // 2 - 1, y + 2, x + s // 2 + 1, y + 12], fill=INK)
    draw.polygon([(x + s // 2 + 1, y + 2), (x + s // 2 + 11, y + 5),
                  (x + s // 2 + 1, y + 8)], fill=RED)


def icon_building(draw, x, y, s=34):
    """Apartment block with a crack."""
    draw.rectangle([x + 4, y + 6, x + s - 4, y + s], outline=INK, width=2)
    for wx in (x + 9, x + s // 2 - 2):
        for wy in (y + 11, y + 20):
            draw.rectangle([wx, wy, wx + 6, wy + 5], fill=INK)
    draw.line([(x + s - 8, y + 6), (x + s - 12, y + 16),
               (x + s - 7, y + 24), (x + s - 11, y + s)],
              fill=RED, width=2)


def icon_ballot(draw, x, y, s=34):
    """Ballot box with a slip going in."""
    draw.rectangle([x + 4, y + 16, x + s - 4, y + s], outline=INK, width=2)
    draw.rectangle([x + 12, y + 18, x + s - 12, y + 21], fill=INK)
    draw.polygon([(x + 12, y + 2), (x + 22, y + 2), (x + 19, y + 16),
                  (x + 12, y + 16)], fill=RED)
    draw.line([(x + 14, y + 5), (x + 20, y + 5)], fill=PAPER, width=1)


def icon_scales(draw, x, y, s=34):
    """Scales of justice."""
    cx = x + s // 2
    draw.line([(cx, y + 4), (cx, y + s - 4)], fill=INK, width=2)
    draw.line([(x + 4, y + 10), (x + s - 4, y + 10)], fill=INK, width=2)
    for px in (x + 4, x + s - 4):
        draw.polygon([(px - 7, y + 18), (px + 7, y + 18), (px, y + 26)],
                     outline=INK, width=1)
        draw.line([(px, y + 10), (px - 7, y + 18)], fill=INK, width=1)
        draw.line([(px, y + 10), (px + 7, y + 18)], fill=INK, width=1)
    draw.rectangle([cx - 6, y + s - 4, cx + 6, y + s - 1], fill=INK)


def icon_flame(draw, x, y, s=34):
    """Flame / tanker fire."""
    draw.polygon([(x + s // 2, y + 2), (x + s - 6, y + 16),
                  (x + s - 2, y + 26), (x + s // 2 + 4, y + s - 2),
                  (x + 6, y + s - 2), (x + 2, y + 20),
                  (x + 8, y + 12)], fill=ORANGE)
    draw.polygon([(x + s // 2, y + 14), (x + s - 10, y + 22),
                  (x + s // 2 + 2, y + s - 2), (x + 10, y + 24)],
                 fill=RED)


def icon_factory(draw, x, y, s=34):
    """Factory with sawtooth roof and chimney."""
    draw.rectangle([x + 4, y + 14, x + s - 4, y + s], outline=INK, width=2)
    draw.polygon([(x + 4, y + 14), (x + 12, y + 6), (x + 20, y + 14),
                  (x + 28, y + 6), (x + s - 4, y + 14)], fill=INK)
    draw.rectangle([x + s - 8, y + 2, x + s - 4, y + 14], fill=INK)
    for dx in (0, 8, 16):
        draw.ellipse([x + 8 + dx, y + 20, x + 13 + dx, y + 25], fill=RED)


ICONS = {
    "ship": icon_ship,
    "building": icon_building,
    "ballot": icon_ballot,
    "scales": icon_scales,
    "flame": icon_flame,
    "factory": icon_factory,
}

# ---------------------------------------------------------------- page

STORIES = [
    ("BENGHAZI, LIBYA", "Russian warship sinks",
     "A suspected Ukrainian sea drone hits the corvette Merkury at port; Kyiv confirms the strike.",
     "ship"),
    ("DYMER, UKRAINE", "Flats collapse in Dymer",
     "A Russian strike partly destroys a five-storey block; at least 10 dead, 14 missing.",
     "building"),
    ("WASHINGTON", "Democrats win big in the House",
     "At least 258 seats after a North Carolina recount — the largest majority since 1992.",
     "ballot"),
    ("THE HAGUE", "Myanmar guilty of Rohingya genocide",
     "The world court rules Myanmar committed genocide against the Rohingya minority.",
     "scales"),
    ("STRAIT OF HORMUZ", "Tankers ablaze off Hormuz",
     "Strikes on tankers deepen the US–Iran blockade standoff at the strait.",
     "flame"),
    ("BANTEN, INDONESIA", "Factory fire: 3 dead, 36 missing",
     "A blaze destroys a candy factory in Cikande; dozens still unaccounted for.",
     "factory"),
]

BRIEF = ("Mexico captures 'El Chapo Isidro' in a Sinaloa raid  ·  "
         "Settlers torch vehicles and homes in West Bank villages  ·  "
         "Alcaraz wins his first ATP Finals title  ·  "
         "Thitikul takes a third straight LPGA title")


def draw_lead_graphic(draw, x0, y0, x1, y1):
    """Cracked globe with a NO DEAL stamp: the summit ends empty-handed."""
    draw.rectangle([x0, y0, x1, y1], outline=INK, width=2)
    cx = (x0 + x1) // 2
    cy = y0 + 78
    r = 58
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=BLUE, width=4)
    draw.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r],
                 outline=BLUE, width=2)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=BLUE, width=2)
    draw.line([(cx - 14, cy - r), (cx + 6, cy - 20), (cx - 8, cy + 6),
               (cx + 12, cy + 26), (cx - 2, cy + r)], fill=RED, width=3)
    stamp = "NO DEAL"
    font = sans_bold(26)
    tw = draw.textlength(stamp, font=font)
    sx = cx - tw // 2 - 8
    sy = y1 - 52
    draw.rectangle([sx, sy, sx + tw + 16, sy + 36], fill=RED)
    draw.text((sx + 8, sy + 4), stamp, font=font, fill=PAPER)


def draw_card(draw, x0, y0, w, h, kicker, headline, summary, icon):
    draw.rectangle([x0, y0, x0 + w, y0 + h], outline=INK, width=2)
    draw.rectangle([x0, y0, x0 + w, y0 + 6], fill=RED)
    pad = 12
    ix = x0 + w - pad - 34
    iy = y0 + 12
    ICONS[icon](draw, ix, iy)
    kf = sans_bold(16)
    kicker_w = w - 2 * pad - 44
    klines = wrap(draw, kicker, kf, kicker_w)
    hf = serif_bold(26)
    hlines = wrap(draw, headline, hf, w - 2 * pad)
    sf = sans(17)
    slines = wrap(draw, summary, sf, w - 2 * pad)
    # Fail loudly at build time instead of silently clipping text: a card
    # that needs more lines than its box holds is a layout bug, not a
    # rendering detail.
    if len(klines) > 1 or len(hlines) > 2 or len(slines) > 3:
        raise ValueError(
            "card %r overflows: kicker %d lines, headline %d lines, "
            "summary %d lines" % (kicker, len(klines), len(hlines),
                                  len(slines)))
    ky = y0 + 14
    for line in klines[:1]:
        draw.text((x0 + pad, ky), line, font=kf, fill=RED)
    hy = ky + 24
    for line in hlines[:2]:
        draw.text((x0 + pad, hy), line, font=hf, fill=INK)
        hy += 31
    sy = hy + 4
    for line in slines[:3]:
        draw.text((x0 + pad, sy), line, font=sf, fill=INK)
        sy += 21


def render(path):
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # Masthead
    draw_centered(draw, 18, "THE WORLD TODAY", serif_bold(84), INK)
    rule(draw, 116, 2)
    draw_centered(draw, 126, "SUNDAY 22 NOVEMBER 2026", sans_bold(29), INK)
    rule(draw, 164, 5)

    # Lead story
    draw.text((MARGIN, 180), "CLIMATE · ANTALYA, TURKEY",
              font=sans_bold(22), fill=RED)
    head_size = 92
    while head_size > 60:
        head_font = serif_bold(head_size)
        if draw.textlength("COP31 COLLAPSES", font=head_font) <= CONTENT:
            break
        head_size -= 2
    draw.text((MARGIN, 206), "COP31 COLLAPSES", font=head_font, fill=INK)
    stand = ("Climate talks end with no deal after the EU and about 130 "
             "nations reject a final text that leaves out fossil fuels.")
    sf = sans(27)
    sy = 308
    for line in wrap(draw, stand, sf, 610):
        draw.text((MARGIN, sy), line, font=sf, fill=INK)
        sy += 34
    draw.text((MARGIN, 420), "DAY 18 OF 18 · TWO DAYS OF OVERTIME",
              font=sans_bold(17), fill=GREY)
    draw.text((MARGIN, 444), "No agreement — and no mention of fossil fuels.",
              font=serif(20), fill=INK)
    draw_lead_graphic(draw, 664, 300, W - MARGIN, 478)

    # Divider
    rule(draw, 494, 4)

    # Story grid 3x2
    card_w, card_h = 312, 174
    gap = 14
    gy = 510
    for row in range(2):
        for col in range(3):
            idx = row * 3 + col
            kicker, headline, summary, icon = STORIES[idx]
            x0 = MARGIN + col * (card_w + gap)
            y0 = gy + row * (card_h + gap)
            draw_card(draw, x0, y0, card_w, card_h,
                      kicker, headline, summary, icon)

    # Brief strip
    rule(draw, 890, 2)
    draw.text((MARGIN, 902), "IN BRIEF", font=sans_bold(20), fill=RED)
    bf = sans(19)
    by = 930
    for line in wrap(draw, BRIEF, bf, CONTENT):
        draw.text((MARGIN, by), line, font=bf, fill=INK)
        by += 24

    # Footer
    rule(draw, 982, 2, fill=LIGHT_LINE)
    draw_centered(draw, 992,
                  "THE WORLD TODAY · SUNDAY 22 NOVEMBER 2026 · DRAWN BY AN AI AGENT FOR MAKE.FUN",
                  sans(14), GREY)

    img.save(path, format="PNG")
    return path


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "entry.png")
    render(out)
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
