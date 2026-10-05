"""The canonical design of Rupak's character as pixel grids.

front_base.txt / side_base.txt are the FRONT and RIGHT views of his turnaround sheet traced
onto an 88px-tall grid (one letter per pixel, see PAL). This module cleans that trace into
the profile's pixel style: hard outline, 2-3 tones per material, a drawn face, bow, belt,
pleats and sneakers. Every idle and walk frame is derived from FRONT and SIDE."""
import pathlib

HERE = pathlib.Path(__file__).parent / "girl"

PAL = {
    "O": (8, 9, 14),       # outline
    "h": (32, 36, 52),     # hair
    "H": (58, 66, 92),     # hair sheen
    "s": (240, 226, 220),  # skin
    "k": (206, 182, 176),  # skin shade
    "E": (12, 12, 18),     # lid line
    "e": (92, 94, 110),    # iris
    "m": (176, 136, 132),  # mouth
    "w": (236, 237, 240),  # shirt
    "W": (178, 183, 194),  # shirt shade
    "d": (36, 41, 62),     # pinafore
    "D": (56, 63, 90),     # pinafore light
    "q": (22, 25, 38),     # pleat line / pinafore shadow
    "b": (120, 124, 136),  # belt buckle
    "r": (162, 44, 54),    # bow
    "R": (104, 28, 38),    # bow shade
    "x": (26, 28, 38),     # sock
    "X": (48, 51, 66),     # sock light
    "g": (232, 232, 228),  # sneaker
    "G": (164, 167, 174),  # sneaker shade
    "_": (5, 7, 10),       # ground shadow (drawn translucent)
}


def load(name):
    rows = (HERE / name).read_text().split("\n")
    w = max(len(r) for r in rows) + 3  # room on the right for the profile nose and toes
    return [list(r.ljust(w, ".")) for r in rows]


def put(g, y, x, s):
    """Write string s into row y from column x ('?' leaves a pixel alone)."""
    for i, c in enumerate(s):
        if c != "?":
            g[y][x + i] = c


def remap(g, y0, y1, table, x0=0, x1=None):
    for y in range(y0, y1):
        for x in range(x0, x1 if x1 is not None else len(g[0])):
            c = g[y][x]
            if c in table:
                g[y][x] = table[c]


def as_rows(g):
    return ["".join(r) for r in g]


# ---- FRONT -------------------------------------------------------------------------
def front():
    g = load("front_base.txt")
    remap(g, 0, 20, {"d": "h", "D": "h", "H": "h", "k": "h", "W": "h", "w": "h"})
    # hair sheen: one soft band across the crown
    for y, x0, x1 in ((4, 14, 16), (5, 13, 16), (6, 13, 15), (9, 7, 9), (10, 7, 8)):
        put(g, y, x0, "H" * (x1 - x0))
    # face: bangs end in three points over the brow, half-lidded eyes, a small mouth
    put(g, 11, 5, "hhhhhhhhhhhhhhh")
    put(g, 12, 5, "hhhhOhhhhOhhhhh")
    put(g, 13, 5, "hhhOshhhhhsOhhh")
    put(g, 14, 5, "hhOssshhhsssOhh")
    put(g, 15, 5, "hhOEEEsssEEEOhh")
    put(g, 16, 5, "hhOseEsssEesOhh")
    put(g, 17, 5, "hhOkssssssskOhh")
    put(g, 18, 5, "hhhOkssmsskOhhh")
    put(g, 19, 5, "hhhhOkksskkOhhh")
    put(g, 20, 5, "hhhhhOkkkOhhhhh")
    # collar and bow (two loops, a knot, two short tails)
    put(g, 21, 4, "OWwwwwOkkkOwwwwO")
    put(g, 22, 3, "OwwwwwOrrOrrOwwwwO")
    put(g, 23, 3, "OwwwdOrRrRrRrOdwwO")
    put(g, 24, 3, "OwwwdddOrRrOdddwwO")
    put(g, 25, 3, "OwwwddddrOrddddwwO")
    put(g, 26, 3, "OwwWddddRdRddddWwO")
    # pinafore body: flat navy with one light fold, sleeves white with a shaded inner edge
    remap(g, 27, 64, {"H": "d", "h": "d", "D": "d"}, 6, 19)
    remap(g, 21, 54, {"H": "W", "D": "W", "d": "W", "k": "W", "h": "W"}, 0, 6)
    remap(g, 21, 54, {"H": "W", "D": "W", "h": "W", "k": "W"}, 19, 25)
    # belt and buckle
    put(g, 35, 6, "qqqqqqqqqqqqq")
    put(g, 36, 6, "OOOOOObbOOOOO")
    put(g, 37, 6, "qqqqqqqqqqqqq")
    # skirt pleats: a dark line every third pixel, a lighter fold beside it
    for y in range(40, 63):
        for x in range(5, 21):
            if g[y][x] == "d":
                g[y][x] = "q" if (x - 5) % 3 == 0 and y > 41 else ("D" if (x - 5) % 3 == 1 and y > 44 else "d")
    # hands
    remap(g, 48, 54, {"w": "s", "W": "k", "H": "k", "D": "k"}, 0, 25)
    for y in range(48, 54):
        for x in range(6, 21):
            if g[y][x] in "sk":
                g[y][x] = "d"
    # cuffs above the hands
    for x in range(0, 6):
        if g[47][x] in "wW":
            g[47][x] = "W"
    for x in range(19, 25):
        if g[47][x] in "wW":
            g[47][x] = "W"
    # small hands below the cuffs
    for y, (left, right) in enumerate([(".OsskO", "OkssO"), (".OsskO", "OkssO"), (".OsskO", "OkssO"),
                                       (".OssO.", "OksO."), ("..OkO.", ".OkO."), ("..OO..", ".OO..")], start=48):
        put(g, y, 0, left)
        put(g, y, 20, right)
    # legs: skin, then socks, then sneakers
    remap(g, 64, 75, {"W": "k", "H": "k", "D": "k", "d": "k", "w": "s"})
    remap(g, 74, 81, {"d": "x", "D": "X", "h": "x", "H": "X", "w": "x", "W": "x", "s": "x", "k": "x"})
    remap(g, 81, 89, {"w": "g", "W": "G", "H": "G", "D": "G", "d": "G"})
    return g


# ---- SIDE (facing right) ---------------------------------------------------------------
def side():
    g = load("side_base.txt")
    remap(g, 0, 21, {"d": "h", "D": "h", "H": "h"}, 0, 9)
    remap(g, 0, 11, {"d": "h", "D": "h", "H": "h", "k": "h", "W": "h"})
    for y, x0, x1 in ((3, 10, 13), (4, 9, 13), (5, 9, 12), (8, 5, 7), (9, 5, 6)):
        put(g, y, x0, "H" * (x1 - x0))
    # head in profile: bangs to the brow, one half-lidded eye, nose point, small mouth
    for y, row in enumerate([
            "...OhhhhhhhhhhhhhhhO...",
            "...OhhhhhhhhhhhhhhhhO..",
            "...OhhhhhhhhhhhhhhhhhO.",
            "...OhhhhhhhhhhhhOhhhhO.",
            "..OhhhhhhhhhhhhOssOhhO.",
            ".OhhhhhhhhhhhhOsEEEsOO.",
            ".OhhhhhhhhhhhkOsseEssO.",
            "OhhhhhhhhhhhhkksssssssO",
            "OhhhhhhhhhhhhkkssssssO.",
            "OhhhhhhhhhhhhhkkssmsO..",
            "OhhhhhhhhhhhhhOkksssO..",
            "OhhhhhhhhhhhhhhOkkkO...",
            "OhhhhhhhhhhhhhOkkO.....",
            "OhhhhhhhhhhhOwwwrRO....",
            "OhhhhhhwwwwwwRrRdO.....",
            ], start=10):
        g[y] = list(row)
    # pinafore front and back; sleeve (near arm) stays white
    remap(g, 23, 64, {"h": "d", "H": "d", "D": "d"}, 8, 20)
    remap(g, 18, 35, {"D": "h", "d": "h", "H": "h", "k": "h"}, 0, 7)
    remap(g, 21, 48, {"H": "W", "D": "W"}, 6, 13)
    # belt
    for x in range(5, 20):
        if g[35][x] in "dDhHq":
            g[35][x] = "q"
        if g[36][x] in "dDhHq":
            g[36][x] = "O"
    # pleats
    for y in range(40, 63):
        for x in range(4, 20):
            if g[y][x] == "d":
                g[y][x] = "q" if (x - 4) % 3 == 0 and y > 42 else ("D" if (x - 4) % 3 == 1 and y > 46 else "d")
    remap(g, 64, 75, {"W": "k", "H": "k", "D": "k", "d": "k", "w": "s"})
    remap(g, 74, 81, {"d": "x", "D": "X", "h": "x", "H": "X", "w": "x", "W": "x", "s": "x", "k": "x"})
    remap(g, 81, 89, {"w": "g", "W": "G", "H": "G", "D": "G", "d": "G", "h": "G"})
    return g


FRONT = as_rows(front())
SIDE = as_rows(side())
