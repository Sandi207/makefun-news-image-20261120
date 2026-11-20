#!/usr/bin/env python3
"""Render the supplied 20 November 2026 news, entirely offline.

All artwork is original geometry. Coordinates are in final-image pixels;
every drawing operation uses a 2x canvas before a single Lanczos downsample.
Usage: python3 render.py [OUTPUT_DIRECTORY]
"""

import argparse
import math
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


SIZE = 1024
SCALE = 2
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
PAPER = "#F4EDDF"
INK = "#202E35"
MUTED = "#566267"
RED = "#BE4A35"
GOLD = "#E2AD4C"
BLUE = "#507D94"
PALE_BLUE = "#DAE5E5"
GREEN = "#668879"
WHITE = "#FFF8EB"


@lru_cache(maxsize=None)
def font(size, face="sans"):
    files = {
        "sans": "DejaVuSans.ttf",
        "bold": "DejaVuSans-Bold.ttf",
        "serif": "DejaVuSerif-Bold.ttf",
    }
    return ImageFont.truetype(str(FONT_DIR / files[face]), round(size * SCALE))


class Canvas:
    """Small drawing vocabulary; all coordinates and strokes scale together."""

    def __init__(self, width, height, background):
        self.image = Image.new("RGB", (width * SCALE, height * SCALE), background)
        self.draw = ImageDraw.Draw(self.image)

    @staticmethod
    def box(bounds):
        return tuple(round(value * SCALE) for value in bounds)

    @staticmethod
    def points(points):
        return [(round(x * SCALE), round(y * SCALE)) for x, y in points]

    def rect(self, bounds, fill, outline=None, width=1):
        self.draw.rectangle(self.box(bounds), fill, outline, round(width * SCALE))

    def rounded(self, bounds, radius, fill, outline=None, width=1):
        self.draw.rounded_rectangle(
            self.box(bounds), round(radius * SCALE), fill, outline, round(width * SCALE)
        )

    def ellipse(self, bounds, fill, outline=None, width=1):
        self.draw.ellipse(self.box(bounds), fill, outline, round(width * SCALE))

    def polygon(self, points, fill, outline=None, width=1):
        scaled = self.points(points)
        self.draw.polygon(scaled, fill)
        if outline:
            self.draw.line(scaled + [scaled[0]], outline, round(width * SCALE), joint="curve")

    def line(self, points, fill=INK, width=2):
        self.draw.line(self.points(points), fill, round(width * SCALE), joint="curve")

    def arc(self, bounds, start, end, fill, width=2):
        self.draw.arc(self.box(bounds), start, end, fill, round(width * SCALE))

    def text(self, xy, value, size, fill=INK, face="sans", anchor="lt"):
        self.draw.text(self.points([xy])[0], value, font=font(size, face), fill=fill, anchor=anchor)

    def text_width(self, value, size, face="sans"):
        return self.draw.textlength(value, font=font(size, face)) / SCALE

    def lines(self, xy, values, size, leading, face="sans", fill=INK, max_width=None):
        x, y = xy
        for index, value in enumerate(values):
            if max_width is not None:
                measured = self.text_width(value, size, face)
                if measured > max_width:
                    raise ValueError(f"Text exceeds its column ({measured:.1f}px): {value}")
            self.text((x, y + index * leading), value, size, fill, face)

    def paste(self, other, xy):
        self.image.paste(other.image, self.points([xy])[0])


def star(c, x, y, radius, fill, points=5):
    vertices = []
    for index in range(points * 2):
        angle = -math.pi / 2 + index * math.pi / points
        length = radius if index % 2 == 0 else radius * 0.43
        vertices.append((x + math.cos(angle) * length, y + math.sin(angle) * length))
    c.polygon(vertices, fill)


def flame(c, x, y, size):
    c.polygon(
        [(x, y), (x - size * .55, y - size * .35), (x - size * .48, y - size * .9),
         (x - size * .17, y - size * .72), (x + size * .03, y - size * 1.6),
         (x + size * .43, y - size * .83), (x + size * .62, y - size * .55),
         (x + size * .45, y - size * .1)], RED
    )
    c.polygon(
        [(x - size * .14, y), (x - size * .24, y - size * .45),
         (x + size * .11, y - size * .95), (x + size * .3, y - size * .28),
         (x + size * .19, y)], GOLD
    )


def missile(c, x, y):
    c.line([(x - 28, y - 17), (x - 8, y - 5)], WHITE, 3)
    c.polygon([(x - 9, y - 10), (x + 15, y + 5), (x + 21, y + 17),
               (x + 8, y + 15), (x - 16, y)], INK)
    c.polygon([(x - 10, y - 6), (x - 20, y - 5), (x - 15, y - 15)], RED)


def drone(c, x, y):
    c.line([(x - 18, y - 4), (x + 18, y + 4)], INK, 3)
    c.line([(x - 4, y - 13), (x + 4, y + 12)], INK, 3)
    for dx, dy in [(-18, -4), (18, 4), (-4, -13), (4, 12)]:
        c.ellipse((x + dx - 6, y + dy - 2, x + dx + 6, y + dy + 2), None, INK, 1.5)
    c.ellipse((x - 4, y - 5, x + 4, y + 5), RED)


def badge(c, number):
    c.rect((0, 0, 34, 27), INK)
    c.text((17, 5), number, 17, WHITE, "bold", "mt")


def kyiv():
    c = Canvas(464, 108, "#D9E1E3")
    c.ellipse((233, 8, 303, 78), "#E8D5B3")
    c.rect((0, 101, 464, 112), BLUE)
    # Three residential blocks, with windows and visible fire.
    for x, y, width, height, color in [
        (52, 48, 63, 55, "#86999C"), (127, 33, 56, 70, "#677F85"),
        (197, 61, 64, 42, "#8D9EA0")
    ]:
        c.rect((x, y, x + width, y + height), color, INK, 1.5)
        for wx in range(x + 9, x + width - 4, 17):
            for wy in range(y + 10, y + height - 5, 17):
                c.rect((wx, wy, wx + 7, wy + 8), WHITE)
    flame(c, 88, 64, 20)
    flame(c, 156, 51, 23)
    flame(c, 228, 77, 19)
    # A visibly struck bridge; the gap is illustrative, not a damage map.
    c.line([(274, 85), (332, 85)], INK, 7)
    c.line([(369, 85), (457, 85)], INK, 7)
    c.line([(332, 85), (344, 94)], INK, 6)
    c.line([(356, 96), (369, 85)], INK, 6)
    for x in (288, 315, 389, 430):
        c.line([(x, 85), (x, 108)], INK, 4)
    c.arc((277, 43, 333, 127), 190, 345, INK, 2)
    c.arc((375, 43, 446, 127), 195, 345, INK, 2)
    star(c, 351, 77, 16, RED, 8)
    missile(c, 302, 28)
    missile(c, 398, 18)
    drone(c, 88, 22)
    c.text((180, 9), "KYIV", 15, INK, "bold")
    badge(c, "01")
    return c


def flag(c, x, y, country, width=49, height=28):
    if country == "US":
        c.rect((x, y, x + width, y + height), WHITE)
        for index in range(7):
            top = y + index * height / 7
            c.rect((x, top, x + width, top + height / 14), RED)
        c.rect((x, y, x + width * .43, y + height * .58), BLUE)
        for dx in (5, 12, 19):
            for dy in (5, 11):
                c.ellipse((x + dx - 1, y + dy - 1, x + dx + 1, y + dy + 1), WHITE)
    elif country == "CN":
        c.rect((x, y, x + width, y + height), RED)
        star(c, x + 10, y + 10, 5, GOLD)
        for dx, dy in [(18, 4), (23, 9), (23, 16), (18, 21)]:
            star(c, x + dx, y + dy, 2, GOLD)
    elif country == "RU":
        c.rect((x, y, x + width, y + height / 3), WHITE)
        c.rect((x, y + height / 3, x + width, y + 2 * height / 3), BLUE)
        c.rect((x, y + 2 * height / 3, x + width, y + height), RED)
    else:
        c.rect((x, y, x + width, y + height), BLUE)
        for index in range(12):
            angle = index * math.pi / 6
            star(c, x + width / 2 + math.sin(angle) * 9,
                 y + height / 2 - math.cos(angle) * 9, 1.7, GOLD)
    c.rect((x, y, x + width, y + height), None, INK, 1)


def diplomat(c, x, y, hair):
    c.polygon([(x - 23, y + 50), (x - 17, y + 22), (x - 7, y + 18),
               (x + 7, y + 18), (x + 17, y + 22), (x + 23, y + 50)], INK)
    c.polygon([(x - 9, y + 19), (x + 9, y + 19), (x, y + 39)], WHITE)
    c.polygon([(x, y + 25), (x - 3, y + 32), (x, y + 42), (x + 3, y + 32)], RED)
    c.ellipse((x - 11, y - 5, x + 11, y + 20), "#DCB59A", INK, 1)
    c.arc((x - 12, y - 6, x + 12, y + 19), 185, 350, hair, 5)
    c.line([(x - 5, y + 5), (x - 3, y + 5)], INK, 1)
    c.line([(x + 3, y + 5), (x + 5, y + 5)], INK, 1)


def declaration():
    c = Canvas(464, 108, "#DCE5DA")
    c.ellipse((328, -34, 475, 114), "#CCD9CA")
    for x, country, name, hair in [
        (72, "US", "TRUMP", GOLD), (142, "CN", "XI", INK),
        (212, "RU", "PUTIN", "#9B8B74")
    ]:
        flag(c, x - 24, 5, country)
        diplomat(c, x, 39, hair)
        c.text((x, 94), name, 12, INK, "bold", "mt")
    # A four-point published declaration, without invented signatures.
    c.rect((266, 11, 342, 103), WHITE, INK, 2)
    c.polygon([(327, 11), (342, 26), (327, 26)], "#E1DDCC", INK, 1)
    c.text((280, 19), "4", 27, INK, "bold")
    for y in (55, 68, 81, 94):
        c.line([(277, y), (280, y + 3), (285, y - 3)], GREEN, 2)
        c.line([(292, y), (331, y)], MUTED, 2)
    # The declaration's explicit rejection of nuclear war.
    c.ellipse((365, 24, 442, 101), None, INK, 2)
    cx, cy = 403.5, 62.5
    for angle in (30, 150, 270):
        points = [(cx, cy)]
        for step in range(15):
            a = math.radians(angle - 25 + step * 50 / 14)
            points.append((cx + math.cos(a) * 27, cy + math.sin(a) * 27))
        c.polygon(points, INK)
    c.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), "#DCE5DA")
    c.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), INK)
    c.line([(377, 90), (430, 35)], RED, 6)
    badge(c, "02")
    return c


def gulf():
    c = Canvas(464, 108, "#C9DEE0")
    # Stylized shores framing a shipping channel, not a geographic map.
    c.polygon([(0, 0), (102, 0), (99, 18), (120, 32), (98, 50),
               (66, 44), (48, 66), (0, 61)], "#D9B882")
    c.polygon([(0, 112), (0, 90), (63, 80), (98, 62), (120, 77),
               (99, 93), (133, 112)], "#D9B882")
    c.text((38, 13), "HORMUZ", 13, INK, "bold")
    for y in (64, 79, 96):
        c.line([(133, y), (318, y)], "#93B8BF", 1)
    # Tanker, cargo deck, mine, and fire east of the channel.
    c.polygon([(146, 69), (324, 69), (306, 95), (174, 95)], INK)
    c.rect((153, 56, 197, 69), WHITE, INK, 1.5)
    c.rect((161, 49, 179, 56), INK)
    for x in (161, 172, 183):
        c.rect((x, 60, x + 5, 64), BLUE)
    c.rect((205, 61, 306, 69), RED)
    for x in (215, 249, 283):
        c.ellipse((x - 8, 53, x + 8, 66), "#D3BA94", INK, 1)
    c.line([(304, 52), (304, 63)], INK, 2)
    flame(c, 242, 60, 26)
    flame(c, 266, 61, 20)
    c.ellipse((263, 6, 286, 24), "#8A9999")
    c.ellipse((277, -6, 311, 13), "#8A9999")
    # A mine symbol in the water, visually distinct from the vessel.
    mx, my = 129, 94
    for index in range(8):
        a = index * math.pi / 4
        c.line([(mx + math.cos(a) * 5, my + math.sin(a) * 5),
                (mx + math.cos(a) * 12, my + math.sin(a) * 12)], INK, 2)
    c.ellipse((mx - 6, my - 6, mx + 6, my + 6), INK)
    missile(c, 180, 18)
    c.rect((342, 0, 464, 112), "#E9E3D1")
    c.text((403, 14), "CRUDE FLOW", 12, INK, "bold", "mt")
    c.text((403, 34), "~½", 40, INK, "bold", "mt")
    c.text((403, 84), "PRE-WAR LEVEL", 10, MUTED, "bold", "mt")
    badge(c, "03")
    return c


def cyclone():
    c = Canvas(464, 108, "#D5E6E5")
    c.polygon([(223, 0), (260, 24), (233, 50), (263, 74),
               (245, 112), (464, 112), (464, 0)], "#C9D2B3")
    c.line([(223, 0), (260, 24), (233, 50), (263, 74), (245, 112)], GREEN, 2)
    # Three sweeping spiral bands and an eye make the cyclone unmistakable.
    for start in (0, 120, 240):
        points = []
        for index in range(71):
            angle = math.radians(start + index * 3.3)
            radius = 11 + index * .67
            points.append((128 + math.cos(angle) * radius * 1.32,
                           56 + math.sin(angle) * radius * .87))
        c.line(points, BLUE, 10)
    c.ellipse((120, 48, 136, 64), WHITE)
    c.line([(59, 94), (85, 94)], BLUE, 2)
    c.line([(176, 100), (210, 100)], BLUE, 2)
    c.line([(179, 18), (200, 18)], BLUE, 2)
    # Coast, a shelter, and an evacuation arrow.
    c.rect((360, 66, 414, 105), WHITE, INK, 1.5)
    c.polygon([(350, 67), (387, 38), (424, 67)], RED, INK, 1.5)
    c.rect((382, 82, 395, 105), INK)
    c.rect((366, 76, 376, 86), BLUE)
    c.line([(284, 91), (344, 91)], INK, 4)
    c.polygon([(344, 91), (332, 82), (332, 100)], INK)
    for x, y in [(302, 82), (326, 75)]:
        c.ellipse((x - 4, y - 15, x + 4, y - 7), INK)
        c.line([(x, y - 5), (x, y + 5)], INK, 3)
        c.line([(x, y + 5), (x - 4, y + 13)], INK, 2)
        c.line([(x, y + 5), (x + 5, y + 13)], INK, 2)
    c.text((278, 10), "300,000+", 28, INK, "bold")
    c.text((280, 43), "EVACUATED", 13, INK, "bold")
    c.text((37, 5), "ODISHA, INDIA", 12, INK, "bold")
    badge(c, "04")
    return c


def europe():
    c = Canvas(464, 108, "#E3E2D4")
    c.ellipse((-15, -44, 184, 143), "#D2D9CA")
    # Facing flags and empty chairs show readiness for talks.
    flag(c, 64, 14, "EU", 61, 35)
    flag(c, 335, 14, "RU", 61, 35)
    c.line([(64, 14), (64, 104)], INK, 2)
    c.line([(396, 14), (396, 104)], INK, 2)
    c.rounded((146, 47, 181, 80), 4, GREEN, INK, 2)
    c.rounded((282, 47, 317, 80), 4, RED, INK, 2)
    for x in (153, 174, 289, 310):
        c.line([(x, 80), (x, 107)], INK, 2)
    c.ellipse((132, 61, 331, 92), "#BBA176", INK, 2)
    c.line([(177, 88), (177, 110)], INK, 3)
    c.line([(285, 88), (285, 110)], INK, 3)
    c.rect((215, 67, 250, 81), WHITE, INK, 1)
    c.line([(222, 72), (242, 72)], MUTED, 1)
    c.line([(222, 76), (236, 76)], MUTED, 1)
    # Dialogue marks remain separated, reflecting no actual meeting yet.
    c.rounded((160, 7, 218, 37), 6, WHITE, INK, 1.5)
    c.polygon([(173, 37), (173, 44), (182, 37)], WHITE, INK, 1)
    c.rounded((246, 7, 304, 37), 6, WHITE, INK, 1.5)
    c.polygon([(282, 37), (292, 44), (292, 37)], WHITE, INK, 1)
    for x in (177, 189, 201, 263, 275, 287):
        c.ellipse((x - 2, 20, x + 2, 24), INK)
    c.text((86, 63), "EUROPE", 12, INK, "bold", "mt")
    c.text((367, 63), "MOSCOW", 12, INK, "bold", "mt")
    badge(c, "05")
    return c


def italy():
    c = Canvas(464, 108, "#E8DECD")
    c.rect((0, 87, 464, 112), "#D1C6AE")
    # A union placard and stopped railway train, with Italy's colors.
    c.line([(87, 43), (87, 111)], INK, 4)
    c.rect((39, 12, 137, 72), RED, INK, 2)
    c.text((88, 19), "CGIL", 24, WHITE, "bold", "mt")
    c.text((88, 48), "24 HOURS", 12, WHITE, "bold", "mt")
    c.line([(162, 97), (373, 97)], INK, 2)
    c.line([(149, 109), (384, 109)], INK, 2)
    for x in range(172, 375, 23):
        c.line([(x, 96), (x - 7, 110)], INK, 2)
    c.rounded((180, 32, 359, 89), 13, INK)
    c.rect((182, 52, 355, 75), WHITE)
    c.rect((182, 73, 355, 80), RED)
    c.rect((195, 42, 230, 64), PALE_BLUE)
    for x in (242, 271, 300):
        c.rounded((x, 43, x + 20, 61), 3, BLUE)
    c.rounded((332, 42, 348, 76), 3, GOLD)
    for x in (208, 325):
        c.ellipse((x - 8, 81, x + 8, 97), INK)
        c.ellipse((x - 3, 86, x + 3, 92), PAPER)
    c.line([(244, 32), (256, 19), (280, 19), (291, 32)], INK, 2)
    c.line([(150, 14), (369, 14)], MUTED, 1)
    # An Italian tricolor behind a clear pause symbol.
    for left, color in [(386, GREEN), (405, WHITE), (424, RED)]:
        c.rect((left, 14, left + 19, 48), color)
    c.ellipse((382, 57, 446, 121), RED)
    c.rect((402, 74, 410, 99), WHITE)
    c.rect((420, 74, 428, 99), WHITE)
    c.text((268, 2), "RAIL: 21:00", 12, INK, "bold", "mt")
    badge(c, "06")
    return c


STORIES = [
    (kyiv, ["KYIV UNDER MASS", "MISSILE ATTACK"], [
        "Russian missiles and drones hit Kyiv.",
        "Homes burned; a bridge and",
        "infrastructure were struck.",
    ]),
    (declaration, ["PEACE DECLARATION,", "NO BREAKTHROUGH"], [
        "Trump, Xi and Putin issued 4 points.",
        "Ukraine and Iran wars unmentioned;",
        "no arms-control talks announced.",
    ]),
    (gulf, ["GULF CONFLICT", "WIDENS"], [
        "Houthis claimed 4 Saudi targets hit.",
        "Tanker hit a mine east of Hormuz.",
        "Crude shipments fell to about half.",
    ]),
    (cyclone, ["CYCLONE DANA", "MAKES LANDFALL"], [
        "300,000+ evacuated in Odisha, India.",
        "200+ trains cancelled; schools shut.",
        "Fishermen were warned ashore.",
    ]),
    (europe, ["EUROPE OPEN TO", "MOSCOW TALKS"], [
        "Europe is open to talks on Ukraine.",
        "Putin invited leaders to Moscow,",
        "demanding a clear stance on talks.",
    ]),
    (italy, ["ITALY GRINDS", "TO A HALT"], [
        "CGIL's 24-hour general strike in Italy.",
        "Local transport: guaranteed hours.",
        "National rail strike starts at 21:00.",
    ]),
]

BRIEFS = [
    "Anthropic's record $81.3 billion IPO closes today; its shares ended their debut up 17% at $97.17.",
    "Trump is back from China and holds a White House press conference today.",
    "Taiwan's regulator curbs short-selling as stocks slide for a third day.",
    "Gaza: Israel ends its major tank incursion into central Gaza.",
]


def render(destination):
    page = Canvas(SIZE, SIZE, PAPER)
    page.line([(32, 20), (318, 20)], INK, 1)
    page.line([(706, 20), (992, 20)], INK, 1)
    page.text((512, 14), "AN ILLUSTRATED NEWS BRIEF", 12, INK, "bold", "mt")
    page.text((512, 34), "THE WORLD TODAY", 62, INK, "serif", "mt")
    page.rect((32, 105, 992, 145), INK)
    page.text((512, 111), "FRIDAY 20 NOVEMBER 2026", 29, PAPER, "bold", "mt")

    for index, (illustration, headlines, caption) in enumerate(STORIES):
        x = 32 + (index % 2) * 496
        y = 161 + (index // 2) * 241
        page.paste(illustration(), (x, y))
        page.lines((x, y + 112), headlines, 26, 27, "bold", max_width=464)
        page.lines((x, y + 161), caption, 24, 25, max_width=464)
    page.line([(512, 161), (512, 877)], "#B6B3A5", 1)
    for y in (399, 640):
        page.line([(32, y), (992, y)], "#B6B3A5", 1)

    page.rect((32, 891, 992, 1000), INK)
    page.text((48, 899), "IN BRIEF", 12, GOLD, "bold")
    page.lines((48, 917), BRIEFS, 16, 19, fill=PAPER, max_width=928)

    assert page.image.size == (2048, 2048)
    final = page.image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "entry.png"
    final.save(output, format="PNG", optimize=True, compress_level=9)
    with Image.open(output) as saved:
        assert saved.size == (SIZE, SIZE)
        assert saved.format == "PNG"
    if output.stat().st_size > 1024 * 1024:
        raise ValueError("The PNG exceeds the 1 MiB bounty limit")
    print(f"Rendered {output} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output_directory", nargs="?", type=Path,
        default=Path(__file__).resolve().parent,
        help="folder for entry.png (default: the renderer's directory)",
    )
    render(parser.parse_args().output_directory)
