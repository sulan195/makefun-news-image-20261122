#!/usr/bin/env python3
"""Render the front page for Sunday 22 November 2026 — revision 2.

Build-time only: the grader never runs this file (main.py only copies the
bundled entry.png). Every headline, date and illustration is drawn
programmatically with Pillow, so no text is ever garbled and no map or flag
can be drawn wrong. Deterministic: no randomness, no clock, no network.

Layout (1024x1024, "THE WORLD IN ONE DAY"): series band, giant date
masthead, dek, stat strip, region bar, UTC timeline, three hero stories
with drawn scenes, a 3x3 grid of illustrated stories, an "also" list of
22 more stories, a dot world map with numbered pins, a date-check box
and a sources footer. 34 stories in all.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 24
CONTENT = W - 2 * MARGIN  # 976

PAPER = (247, 243, 234)
INK = (20, 19, 15)
NAVY = (24, 42, 67)
NIGHT = (16, 26, 48)
RED = (163, 18, 18)
DARKRED = (122, 20, 16)
BLUE = (46, 109, 164)
RUST = (179, 84, 30)
OLIVE = (122, 154, 1)
PURPLE = (122, 72, 150)
OCHRE = (176, 128, 20)
TEAL = (0, 128, 128)
SLATE = (96, 100, 108)
GREY = (96, 92, 84)
LIGHT_LINE = (210, 204, 190)
GOLD = (240, 196, 64)
SKY = (196, 220, 232)
SEA = (58, 96, 138)

REGION_COLORS = {
    "EUROPE": BLUE,
    "MIDDLE EAST": RUST,
    "ASIA-PACIFIC": OLIVE,
    "AMERICAS": PURPLE,
    "AFRICA": OCHRE,
    "OCEANIA": TEAL,
    "WORLD": SLATE,
}

FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/noto",
]


def load_font(names, size):
    """Load the first available font from names, else PIL's default."""
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


def serif_italic(size):
    return load_font(["DejaVuSerif-Italic.ttf", "LiberationSerif-Italic.ttf",
                      "NotoSerif-Italic.ttf"], size)


def sans_bold(size):
    return load_font(["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
                      "NotoSans-Bold.ttf"], size)


def sans(size):
    return load_font(["DejaVuSans.ttf", "LiberationSans-Regular.ttf",
                      "NotoSans-Regular.ttf"], size)


def wrap(draw, text, font, max_width):
    """Greedy word wrap; a word wider than max_width is split by char."""
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
    width = draw.textlength(text, font=font)
    draw.text(((x0 + x1 - width) / 2, y), text, font=font, fill=fill)
    return font.size


def rule(draw, y, weight=2, fill=INK, x0=MARGIN, x1=W - MARGIN):
    draw.rectangle([x0, y, x1, y + weight - 1], fill=fill)


def fit_font(draw, text, maker, start, minimum, max_width):
    """Largest font from maker(size) whose text fits max_width."""
    size = start
    while size > minimum:
        font = maker(size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return maker(minimum)


def tag_chip(draw, x, y, text, fill):
    """Small certainty tag: coloured box with white bold text."""
    font = sans_bold(11)
    tw = draw.textlength(text, font=font)
    draw.rectangle([x, y, x + tw + 12, y + 17], fill=fill)
    draw.text((x + 6, y + 2), text, font=font, fill=(255, 255, 255))
    return tw + 12


TAG_COLORS = {"REPORTED": SLATE, "CLAIM": DARKRED, "FORECAST": TEAL}

# ---------------------------------------------------------------- scenes
# Flat, original spot illustrations drawn with polygons/rectangles only.


def scene_ukraine(draw, x0, y0, x1, y1):
    """Night sky, drones, a lit apartment block, a searchlight beam."""
    draw.rectangle([x0, y0, x1, y1], fill=NIGHT)
    for sx, sy in ((18, 14), (52, 30), (96, 10), (140, 26), (70, 48),
                   (180, 12), (24, 58), (150, 52)):
        draw.ellipse([x0 + sx, y0 + sy, x0 + sx + 3, y0 + sy + 3],
                     fill=(220, 226, 240))
    draw.ellipse([x1 - 52, y0 + 10, x1 - 22, y0 + 40], fill=(232, 230, 210))
    # searchlight beam from lower left
    draw.polygon([(x0 + 10, y1), (x0 + 128, y0 + 22), (x0 + 142, y0 + 32),
                  (x0 + 30, y1)], fill=(198, 190, 138))
    # drones: x body with four rotor dots
    for dx, dy, s in ((60, 30, 13), (120, 52, 10), (88, 70, 8)):
        cx, cy = x0 + dx, y0 + dy
        draw.line([(cx - s, cy - s), (cx + s, cy + s)], fill=GOLD, width=2)
        draw.line([(cx - s, cy + s), (cx + s, cy - s)], fill=GOLD, width=2)
        draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=RED)
    # apartment block, right side
    bx0, by0 = x1 - 108, y0 + 30
    draw.rectangle([bx0, by0, x1 - 12, y1], fill=(38, 44, 62))
    for r in range(3):
        for c in range(3):
            wx = bx0 + 10 + c * 32
            wy = by0 + 10 + r * 19
            lit = (r + c) % 3 != 0
            draw.rectangle([wx, wy, wx + 18, wy + 12],
                           fill=GOLD if lit else (70, 78, 100))
    # damaged corner
    draw.polygon([(x1 - 12, by0), (x1 - 44, by0 + 26), (x1 - 12, by0 + 52)],
                 fill=NIGHT)
    draw.rectangle([x0, y1 - 8, x1, y1], fill=(10, 14, 26))


def scene_cop31(draw, x0, y0, x1, y1):
    """A summit table: seated delegates, a screen, a clock at the deadline."""
    draw.rectangle([x0, y0, x1, y1], fill=(214, 228, 226))
    draw.rectangle([x0, y0, x0 + 118, y1], fill=(168, 198, 188))
    # screen: the final text as a document, its fossil-fuel line struck out
    draw.rectangle([x0 + 14, y0 + 14, x0 + 104, y0 + 68], fill=(240, 244, 238))
    for li in range(4):
        draw.rectangle([x0 + 22, y0 + 22 + li * 9, x0 + 96, y0 + 25 + li * 9],
                       fill=(150, 156, 150))
    draw.line([(x0 + 20, y0 + 62), (x0 + 98, y0 + 20)], fill=RED, width=3)
    # clock, upper right
    kx, ky, kr = x1 - 44, y0 + 34, 24
    draw.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], outline=INK, width=3)
    draw.line([(kx, ky), (kx, ky - 15)], fill=INK, width=3)
    draw.line([(kx, ky), (kx + 11, ky + 5)], fill=INK, width=3)
    # table and delegates
    ty = y1 - 40
    draw.rectangle([x0 + 130, ty, x1 - 16, ty + 12], fill=(110, 74, 40))
    for i in range(6):
        hx = x0 + 152 + i * 30
        draw.ellipse([hx - 8, ty - 26, hx + 8, ty - 10], fill=(52, 44, 36))
        draw.pieslice([hx - 11, ty - 12, hx + 11, ty + 12], 180, 360,
                      fill=(52, 44, 36))
    draw.rectangle([x0, y1 - 10, x1, y1], fill=(150, 170, 162))


def scene_bahrain(draw, x0, y0, x1, y1):
    """Radar towers on a shore, one burning: a claim met by a denial."""
    draw.rectangle([x0, y0, x1, y1], fill=(226, 206, 178))
    draw.rectangle([x0, y1 - 30, x1, y1], fill=SEA)
    for tx in (x0 + 56, x0 + 168):
        draw.polygon([(tx - 16, y1 - 30), (tx + 16, y1 - 30),
                      (tx + 8, y0 + 30), (tx - 8, y0 + 30)], fill=(90, 90, 96))
        draw.ellipse([tx - 20, y0 + 12, tx + 20, y0 + 34], fill=(70, 70, 78))
        draw.line([(tx, y0 + 23), (tx + 30, y0 + 8)], fill=(70, 70, 78),
                  width=2)
    # flames on the right tower
    fx = x0 + 168
    draw.polygon([(fx + 4, y0 + 52), (fx + 22, y0 + 76), (fx + 16, y1 - 34),
                  (fx - 6, y1 - 34), (fx - 14, y0 + 74)], fill=RUST)
    draw.polygon([(fx + 6, y0 + 66), (fx + 16, y0 + 84), (fx + 12, y1 - 34),
                  (fx, y1 - 34), (fx - 4, y0 + 82)], fill=RED)
    draw.ellipse([fx - 4, y0 + 6, fx + 26, y0 + 30], fill=(120, 116, 110))


def thumb_ballot(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(232, 226, 210))
    draw.rectangle([x0 + 16, y0 + 34, x1 - 16, y1 - 8], fill=NAVY)
    draw.rectangle([x0 + 30, y0 + 44, x1 - 30, y0 + 49], fill=PAPER)
    draw.polygon([(x0 + 30, y0 + 6), (x0 + 52, y0 + 6), (x0 + 48, y0 + 36),
                  (x0 + 30, y0 + 36)], fill=RED)
    draw.text((x0 + 33, y0 + 12), "✓", font=sans_bold(14), fill=(255, 255, 255))


def thumb_cricket(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(104, 148, 66))
    draw.rectangle([x0 + 30, y0 + 8, x0 + 52, y1 - 8], fill=(216, 198, 150))
    draw.rectangle([x0 + 38, y0 + 12, x0 + 44, y0 + 24], fill=(90, 60, 30))
    draw.ellipse([x0 + 58, y0 + 44, x0 + 68, y0 + 54], fill=RED)
    draw.line([(x0 + 14, y0 + 54), (x0 + 34, y0 + 20)], fill=(90, 60, 30),
              width=4)


def thumb_f1(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(30, 30, 36))
    draw.rectangle([x0, y1 - 16, x1, y1], fill=(70, 70, 78))
    for i in range(6):
        draw.rectangle([x0 + 4 + i * 14, y1 - 16, x0 + 11 + i * 14, y1 - 9],
                       fill=(200, 200, 200))
    draw.polygon([(x0 + 10, y1 - 22), (x0 + 30, y1 - 30), (x0 + 58, y1 - 30),
                  (x0 + 72, y1 - 22)], fill=RED)
    draw.rectangle([x0 + 6, y1 - 34, x0 + 20, y1 - 28], fill=RED)
    draw.rectangle([x0 + 62, y1 - 36, x0 + 76, y1 - 30], fill=RED)
    for wx in (x0 + 18, x0 + 60):
        draw.ellipse([wx, y1 - 24, wx + 13, y1 - 11], fill=(8, 8, 8))


def thumb_nba(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(198, 150, 92))
    draw.rectangle([x0 + 26, y0 + 8, x0 + 58, y0 + 30], outline=INK, width=2)
    draw.ellipse([x0 + 32, y0 + 28, x0 + 52, y0 + 38], outline=RED, width=3)
    draw.line([(x0 + 34, y0 + 36), (x0 + 38, y0 + 48)], fill=(240, 240, 240),
              width=1)
    draw.line([(x0 + 50, y0 + 36), (x0 + 46, y0 + 48)], fill=(240, 240, 240),
              width=1)
    draw.ellipse([x0 + 52, y0 + 48, x0 + 70, y0 + 66], fill=RUST)
    draw.arc([x0 + 52, y0 + 48, x0 + 70, y0 + 66], 90, 270, fill=INK, width=1)


def thumb_ship(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(168, 198, 220))
    draw.rectangle([x0, y1 - 18, x1, y1], fill=SEA)
    draw.polygon([(x0 + 12, y1 - 26), (x1 - 12, y1 - 26), (x1 - 22, y1 - 14),
                  (x0 + 20, y1 - 14)], fill=(70, 74, 84))
    draw.rectangle([x0 + 34, y1 - 40, x0 + 52, y1 - 26], fill=(70, 74, 84))
    draw.polygon([(x0 + 40, y0 + 8), (x0 + 54, y0 + 26), (x0 + 50, y1 - 40),
                  (x0 + 34, y1 - 40), (x0 + 30, y0 + 24)], fill=RUST)
    draw.polygon([(x0 + 42, y0 + 18), (x0 + 50, y0 + 30), (x0 + 47, y1 - 40),
                  (x0 + 38, y1 - 40)], fill=RED)


def thumb_power(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(40, 40, 48))
    px = x0 + 42
    draw.line([(px - 16, y1 - 6), (px, y0 + 14), (px + 16, y1 - 6)],
              fill=(150, 150, 158), width=2)
    draw.line([(px - 22, y0 + 26), (px + 22, y0 + 26)], fill=(150, 150, 158),
              width=2)
    draw.line([(px - 18, y0 + 38), (px + 18, y0 + 38)], fill=(150, 150, 158),
              width=2)
    draw.polygon([(px + 2, y0 + 30), (px - 8, y0 + 50), (px + 1, y0 + 50),
                  (px - 3, y1 - 16), (px + 10, y0 + 44), (px + 2, y0 + 44)],
                 fill=GOLD)


def thumb_factory(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(216, 206, 190))
    draw.rectangle([x0 + 10, y1 - 34, x1 - 10, y1 - 6], fill=(96, 92, 88))
    draw.polygon([(x0 + 10, y1 - 34), (x0 + 24, y1 - 46), (x0 + 38, y1 - 34),
                  (x0 + 52, y1 - 46), (x1 - 10, y1 - 34)], fill=(70, 68, 64))
    draw.rectangle([x1 - 22, y0 + 12, x1 - 14, y1 - 34], fill=(70, 68, 64))
    draw.polygon([(x0 + 34, y0 + 16), (x0 + 46, y0 + 34), (x0 + 42, y1 - 34),
                  (x0 + 28, y1 - 34), (x0 + 26, y0 + 30)], fill=RUST)
    draw.polygon([(x0 + 36, y0 + 26), (x0 + 43, y0 + 38), (x0 + 40, y1 - 34),
                  (x0 + 32, y1 - 34)], fill=RED)


def thumb_vatican(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=SKY)
    cx = x0 + 42
    draw.pieslice([cx - 24, y0 + 18, cx + 24, y0 + 66], 180, 360,
                  fill=(226, 220, 204))
    draw.rectangle([cx - 24, y0 + 42, cx + 24, y1 - 6], fill=(226, 220, 204))
    draw.rectangle([cx - 2, y0 + 4, cx + 2, y0 + 18], fill=(120, 100, 60))
    draw.line([(cx - 5, y0 + 8), (cx + 5, y0 + 8)], fill=(120, 100, 60),
              width=2)
    for wx in (cx - 16, cx - 4, cx + 8):
        draw.rectangle([wx, y1 - 22, wx + 6, y1 - 12], fill=(120, 110, 90))


def thumb_drone(draw, x0, y0, x1, y1):
    draw.rectangle([x0, y0, x1, y1], fill=(206, 186, 158))
    draw.rectangle([x0 + 8, y1 - 22, x0 + 34, y1 - 6], fill=(150, 128, 96))
    draw.rectangle([x0 + 48, y1 - 18, x0 + 72, y1 - 6], fill=(150, 128, 96))
    cx, cy = x0 + 44, y0 + 22
    draw.line([(cx - 14, cy - 10), (cx + 14, cy + 10)], fill=INK, width=3)
    draw.line([(cx - 14, cy + 10), (cx + 14, cy - 10)], fill=INK, width=3)
    draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=RED)


THUMBS = {
    "ballot": thumb_ballot,
    "cricket": thumb_cricket,
    "f1": thumb_f1,
    "nba": thumb_nba,
    "ship": thumb_ship,
    "power": thumb_power,
    "factory": thumb_factory,
    "vatican": thumb_vatican,
    "drone": thumb_drone,
}

# ---------------------------------------------------------------- data

HEROES = [
    ("1 · KYIV REGION, UKRAINE · WAR", "REPORTED", scene_ukraine,
     "Russia fires 186 drones at Ukraine overnight",
     "161 of 186 strike drones were downed or jammed. In Dymer, near Kyiv, "
     "a five-storey block partly collapsed; 14 may be trapped.",
     "Ukrainian Air Force · Kyiv Oblast · Reuters"),
    ("2 · ANTALYA, TÜRKIYE · CLIMATE", "REPORTED", scene_cop31,
     "Climate deal lands with no mention of fossil fuels",
     "It recalls the Dubai pact, keeps the 35% electricity goal, "
     "drops the $120bn adaptation target, admits 1.5°C will be overshot.",
     "Reuters · BBC · The Guardian"),
    ("3 · MANAMA, BAHRAIN · IRAN", "CLAIM", scene_bahrain,
     "Iran claims two US radars hit; Bahrain denies it",
     "The IRGC says it destroyed two Patriot radars Saturday night. "
     "Bahrain replies: a civilian site was hit — a fire, no injuries.",
     "Khaleej Times · Al Jazeera"),
]

GRID = [
    ("4 · HONG KONG · ELECTION", "ballot",
     "Hong Kong elects its Election Committee",
     "856 candidates, 723 seats; turnout 98.37% by 5 pm."),
    ("5 · WELLINGTON · CRICKET", "cricket",
     "India declare on 720/9 — a record in NZ",
     "Rahul 156, Pant 128, Gill 119: the highest Test total in New Zealand."),
    ("6 · LAS VEGAS · FORMULA 1", "f1",
     "Verstappen takes the Las Vegas Grand Prix",
     "From pole in 1:27:39.624; Norris +0.639, Piastri +1.529."),
    ("7 · SAN ANTONIO · NBA", "nba",
     "Wembanyama scores 50 as the Spurs roll on",
     "50 pts, 19 rebounds, 5 blocks; 114–91 over New Orleans."),
    ("8 · GULF OF FINLAND · SEA", "ship",
     "Russian cargo ship Sparta II still burning",
     "Hit by drones Saturday; Finland leads the Loviisa rescue."),
    ("9 · TEHRAN, IRAN · ENERGY", "power",
     "Iran begins rationing electricity",
     "Rolling cuts up to two hours a day as war damage bites."),
    ("10 · CIKANDE, INDONESIA · FIRE", "factory",
     "Candy-factory fire in Cikande: 3 dead, 36 missing",
     "Blaze tore through the Banten plant; search goes on."),
    ("11 · VATICAN CITY · FAITH", "vatican",
     "Pope Leo XIV hosts 1,300 poor guests",
     "Lunch for the 10th World Day of the Poor, at the Vatican."),
    ("12 · KHARTOUM, SUDAN · WAR", "drone",
     "Drones strike homes near Khartoum",
     "Army air defences engaged; toll not yet known."),
]

ALSO = [
    "Manipur, India · Toxic-liquor toll climbs to 19; 600 in hospital (Xinhua)",
    "Junín, Peru · Quake toll updated: 1 dead, 16 hurt, 170 homes hit (Reuters)",
    "Brussels · Controllers join Monday's strike; flights grounded (Wires)",
    "Washington · FBI probes apparent hack of its crime database (AP)",
    "Brasília, Brazil · Bolsonaro in intensive care, stable (Reuters)",
    "Denmark · Russian attaché expelled over an alleged plot (Reuters)",
    "Estonia · Five Russia border crossings to shut 1 Dec (Reuters)",
    "Nepal · PM Shah lands in Delhi on first visit; meets Modi (IANS)",
    "Philippines · Chinese bomber turns back 170 km from Manila (AP)",
    "Japan · Snow strands about 1,500 people in a village (dpa)",
    "Somalia · UAE ambassador expelled; envoy recalled (Wires)",
    "Sudan · RSF accused of killing civilians in W. Kordofan (Claim)",
    "Kenya · Last Ebola patient discharged (Wires)",
    "Washington · Trump seeks 'permanent' Iran deal (Al Jazeera)",
    "Gaza · Hamas seeks urgent mediator talks (Straits Times)",
    "Gaza City · Israeli fire kills 3 in a food vehicle (Al Jazeera)",
    "Markets · Bitcoin back above $60,000 after Saturday's flush (Data)",
    "Space · BepiColombo enters Mercury orbit after 8 years (AP · ESA)",
]

STATS = [
    ("186", "DRONES FIRED AT UKRAINE OVERNIGHT"),
    ("161", "DOWNED OR JAMMED BY AIR DEFENCE"),
    ("35%", "ELECTRICITY GOAL FOR 2035, KEPT"),
    ("$120bn", "ADAPTATION TARGET DROPPED"),
    ("720/9", "INDIA'S RECORD TEST TOTAL IN NZ"),
    ("50", "WEMBANYAMA POINTS, 19 REBOUNDS"),
]

REGIONS = [("EUROPE", 6), ("MIDDLE EAST", 4), ("ASIA-PACIFIC", 6),
           ("AMERICAS", 6), ("AFRICA", 4), ("OCEANIA", 1), ("WORLD", 3)]

TIMELINE = ("03:00 COP31 objections close · 05:11 Hamas seeks talks · "
            "05:30 Verstappen wins Vegas · 06:00 COP31 approval due · "
            "07:30 Approval slips again · 09:45 Press time")

# Coarse dot world map, 47 cols x 20 rows; '#' is land.
MAP_ROWS = [
    "  ####    #########    #####################   ",
    " ######## ##########  #######################  ",
    " ############# ##### ######################### ",
    "  ############     ##########################  ",
    "   ##########       ########################   ",
    "   ##########       #######################    ",
    "    ########        #####################      ",
    "     ######          ##################        ",
    "      ####            ################         ",
    "       #####           ##############          ",
    "        #####           #############          ",
    "        ######           ###########           ",
    "         #####            ############         ",
    "         ####              ##  ################",
    "         ####                     ##########   ",
    "          ###                      ########    ",
    "          ##                             ##    ",
    "                                        ####   ",
    "                                               ",
    "                                               ",
]

# (story number, col, row) on the map grid.
PINS = [(1, 26, 3), (2, 26, 6), (3, 29, 8), (4, 37, 8), (5, 45, 17),
        (6, 6, 6), (7, 9, 8), (8, 24, 1), (9, 31, 6), (10, 36, 12),
        (11, 23, 5), (12, 26, 9)]

DATE_CHECK = ("DATE CHECK — Every story on this page happened, or was first "
              "reported, on Sunday 22 November 2026, wires read to 09:45 UTC. "
              "Left out as other days' news: the 400-drone barrage (Thu–Fri) "
              "· the Shenzhen blast (Thu) · Fred Nile dies, 92 (Sat) · "
              "NWSL final (Sat).")

FOOTER = ("CERTAINTY — REPORTED: carried by the day's wires · CLAIM: one "
          "side's account, labelled as such · FORECAST: still to happen "
          "when drawn · Sources: Reuters, BBC, AP, AFP, Al Jazeera, The "
          "Guardian, SCMP, ESPN, Xinhua, dpa, IANS · Scenes are drawn "
          "illustrations, not photographs.")

# ---------------------------------------------------------------- cards


def draw_hero(draw, x0, y0, w, h, kicker, tag, scene, headline, summary,
              sources):
    draw.rectangle([x0, y0, x0 + w, y0 + h], outline=INK, width=2)
    scene(draw, x0 + 2, y0 + 2, x0 + w - 2, y0 + 94)
    tag_chip(draw, x0 + w - 108, y0 + 8, tag, TAG_COLORS[tag])
    ty = y0 + 102
    draw.text((x0 + 10, ty), kicker, font=sans_bold(12), fill=RED)
    hf = serif_bold(20)
    hlines = wrap(draw, headline, hf, w - 20)
    if len(hlines) > 2:
        raise ValueError("hero headline overflows: %r" % headline)
    hy = ty + 20
    for line in hlines:
        draw.text((x0 + 10, hy), line, font=hf, fill=INK)
        hy += 24
    sf = sans(13)
    slines = wrap(draw, summary, sf, w - 20)
    if len(slines) > 3:
        raise ValueError("hero summary overflows: %r" % summary)
    sy = hy + 3
    for line in slines:
        draw.text((x0 + 10, sy), line, font=sf, fill=INK)
        sy += 15
    draw.text((x0 + 10, y0 + h - 19), sources, font=sans(10.5), fill=GREY)


def draw_grid_card(draw, x0, y0, w, h, kicker, thumb, headline, summary):
    draw.rectangle([x0, y0, x0 + w, y0 + h], outline=INK, width=2)
    THUMBS[thumb](draw, x0 + 2, y0 + 2, x0 + 76, y0 + h - 2)
    tx = x0 + 84
    tw = x0 + w - tx - 8
    draw.text((tx, y0 + 4), kicker, font=sans_bold(10.5), fill=RED)
    hf = serif_bold(13.5)
    hlines = wrap(draw, headline, hf, tw)
    if len(hlines) > 2:
        raise ValueError("grid headline overflows: %r" % headline)
    hy = y0 + 18
    for line in hlines:
        draw.text((tx, hy), line, font=hf, fill=INK)
        hy += 15
    sf = sans(10.5)
    slines = wrap(draw, summary, sf, tw)
    if len(slines) > 2:
        raise ValueError("grid summary overflows: %r" % summary)
    for line in slines[:2]:
        draw.text((tx, hy + 1), line, font=sf, fill=INK)
        hy += 11.5


def draw_map(draw, x0, y0):
    cell = 5
    dot = (120, 128, 140)
    for r, row in enumerate(MAP_ROWS):
        for c, ch in enumerate(row):
            if ch == "#":
                cx = x0 + c * cell
                cy = y0 + r * cell
                draw.ellipse([cx, cy, cx + 3, cy + 3], fill=dot)
    pf = sans_bold(8)
    for num, c, r in PINS:
        cx = x0 + c * cell + 1
        cy = y0 + r * cell + 1
        draw.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=RED)
        label = str(num)
        tw = draw.textlength(label, font=pf)
        draw.text((cx - tw / 2, cy - 4), label, font=pf,
                  fill=(255, 255, 255))

# ---------------------------------------------------------------- page


def render(path):
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # Series band
    draw.rectangle([0, 0, W, 26], fill=NAVY)
    draw.text((MARGIN, 5), "THE WORLD IN ONE DAY", font=sans_bold(14),
              fill=(255, 255, 255))
    right = "30 STORIES · 7 REGIONS · EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    rf = sans_bold(11.5)
    draw.text((W - MARGIN - draw.textlength(right, font=rf), 6), right,
              font=rf, fill=(255, 255, 255))

    # Masthead: the date is the biggest thing on the page after headlines.
    mf = fit_font(draw, "Sunday 22 November 2026", serif_bold, 86, 60,
                  CONTENT)
    draw_centered(draw, 34, "Sunday 22 November 2026", mf, INK)
    dek = ("186 drones over Ukraine in the night · COP31's deal names no "
           "fossil fuels · Iran's radar claim meets Bahrain's denial")
    draw_centered(draw, 122, dek, serif_italic(17), DARKRED)
    rule(draw, 148, 3)

    # Stat strip
    cell_w = CONTENT // 6
    nf = serif_bold(34)
    lf = sans_bold(10)
    for i, (num, label) in enumerate(STATS):
        cx = MARGIN + i * cell_w
        draw.text((cx + 4, 156), num, font=nf, fill=INK)
        ly = 196
        for line in wrap(draw, label, lf, cell_w - 10)[:2]:
            draw.text((cx + 4, ly), line, font=lf, fill=GREY)
            ly += 12
        if i:
            draw.line([(cx, 158), (cx, 214)], fill=LIGHT_LINE, width=1)
    rule(draw, 222, 2)

    # Region bar
    seg_w = CONTENT / len(REGIONS)
    for i, (name, count) in enumerate(REGIONS):
        sx = MARGIN + i * seg_w
        draw.rectangle([sx, 230, sx + seg_w - 2, 254],
                       fill=REGION_COLORS[name])
        label = "%s %d" % (name, count)
        lf2 = sans_bold(11.5)
        tw = draw.textlength(label, font=lf2)
        draw.text((sx + (seg_w - 2 - tw) / 2, 236), label, font=lf2,
                  fill=(255, 255, 255))
    # Timeline
    draw.text((MARGIN, 262), "THE DAY IN UTC", font=sans_bold(12), fill=INK)
    tf = fit_font(draw, TIMELINE, sans, 12, 9, CONTENT - 118)
    draw.text((MARGIN + 118, 262), TIMELINE, font=tf, fill=INK)
    rule(draw, 282, 2)

    # Heroes
    hero_w, hero_h, gap = 317, 238, 12
    for i, hero in enumerate(HEROES):
        draw_hero(draw, MARGIN + i * (hero_w + gap), 282, hero_w, hero_h,
                  *hero)

    # Grid 3x3
    card_w, card_h, ggap = 317, 72, 5
    gy = 528
    for idx, card in enumerate(GRID):
        row, col = divmod(idx, 3)
        draw_grid_card(draw, MARGIN + col * (card_w + ggap),
                       gy + row * (card_h + ggap), card_w, card_h, *card)

    # Bottom: also-list (3 columns) + map
    by = 762
    draw.text((MARGIN, by), "ALSO ON SUNDAY 22 NOVEMBER — 18 MORE STORIES",
              font=sans_bold(14), fill=RED)
    draw_map(draw, 756, by + 26)
    draw.text((756, by), "WHERE IT HAPPENED", font=sans_bold(12), fill=INK)
    draw.text((756, by + 130), "pins match story numbers", font=sans(10),
              fill=GREY)
    col_w, col_gap = 232, 10
    nf2 = sans_bold(10.5)
    bf = sans(10.5)
    cols = [ALSO[0:6], ALSO[6:12], ALSO[12:18]]
    starts = [13, 19, 25]
    for ci, items in enumerate(cols):
        cx = MARGIN + ci * (col_w + col_gap)
        cy = by + 24
        for j, item in enumerate(items):
            num = str(starts[ci] + j)
            draw.text((cx, cy), num, font=nf2, fill=RED)
            lines = wrap(draw, item, bf, col_w - 20)
            if len(lines) > 2:
                raise ValueError("also item overflows: %r" % item)
            ly = cy
            for line in lines[:2]:
                draw.text((cx + 20, ly), line, font=bf, fill=INK)
                ly += 11.5
            cy = ly + 3.5

    # Date check + footer
    rule(draw, 958, 2, fill=RED)
    df = sans(10.5)
    dy = 964
    for line in wrap(draw, DATE_CHECK, df, CONTENT)[:2]:
        draw.text((MARGIN, dy), line, font=df, fill=DARKRED)
        dy += 13
    rule(draw, 992, 1, fill=LIGHT_LINE)
    ff = sans(9.5)
    fy = 997
    for line in wrap(draw, FOOTER, ff, CONTENT)[:2]:
        draw_centered(draw, fy, line, ff, GREY)
        fy += 12

    img.save(path, format="PNG")
    return path


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "entry.png")
    render(out)
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
