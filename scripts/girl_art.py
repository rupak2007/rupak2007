"""An original character for the profile, drawn pixel by pixel at the boy's scale (~48px).

CHARACTER SPEC (every frame follows this)
  hair       near-black blue, chin-length rounded bob; the fringe sweeps to her left in one
             heavy cluster that half-covers her left eye; one stubborn cowlick tuft on the
             crown; the bob's ends flick outward at the jaw
  face       pale; heavy half-lidded eyes with a dark lid line over a small grey iris; a soft
             shadow under each eye (always a bit tired); a 1px mouth, no blush
  outfit     oversized charcoal-navy cardigan with sleeves past the wrists (only fingertips
             show); light grey shirt collar points over the cardigan; a short muted-red tie
             (her only colour); dark pleated skirt just above the knee under the cardigan's
             hem; dark mid-calf socks; light chunky sneakers with a dark sole line
  palette    see PALETTE: 2-3 tones per material, one muted red, black outline
  silhouette round bob head, slightly slouched shoulders, long-sleeved A-line cardigan
             over a short skirt, thin legs, big shoes

One letter per pixel. Rows may be ragged (padded on the right)."""

PALETTE = {
    ".": None,
    "O": (8, 9, 14),       # outline
    "h": (36, 40, 56),     # hair
    "H": (54, 61, 84),     # hair sheen
    "i": (86, 96, 124),    # hair highlight
    "s": (232, 222, 216),  # skin
    "k": (196, 180, 176),  # skin shade / under-eye
    "E": (14, 14, 20),     # lid line
    "e": (110, 114, 128),  # iris
    "m": (160, 128, 126),  # mouth
    "c": (44, 49, 66),     # cardigan
    "C": (62, 69, 92),     # cardigan light
    "z": (28, 31, 44),     # cardigan shadow
    "w": (206, 210, 218),  # collar
    "W": (150, 155, 166),  # collar shade
    "r": (142, 58, 63),    # tie
    "R": (94, 37, 41),     # tie shade
    "p": (34, 37, 50),     # skirt
    "P": (50, 55, 72),     # skirt fold
    "q": (20, 22, 31),     # pleat line
    "x": (26, 28, 38),     # sock
    "X": (44, 47, 62),     # sock light
    "g": (222, 222, 216),  # sneaker
    "G": (160, 163, 170),  # sneaker shade
    "n": (70, 72, 82),     # sole
    "_": (5, 7, 10),       # ground shadow (translucent)
}

FRONT = """
...........OO.........
..........OhO.........
.......OOOOhOOO.......
.....OOhhhhhhhhOO.....
....OhhhhhhhHHhhhO....
...OhhhhhhhHHihhhhO...
...OhhhhhhhhHHhhhhO...
..OhhhhhhhhhhhhhhhhO..
..OhhhhhhhhhhhhhhhhO..
..OhhhhhhhhhhhhhhhhO..
.OhhhhhhhhhhhhhhhhhhO.
.OhhhOOhhhhhhhhhhhhhO.
.OhhOssOOOhhhhhhhhhhO.
.OhhOsssssOOOhhhhhhhO.
.OhhOsEEEssssOOhhhhhO.
.OhhOseEssssEEEOhhhhO.
.OhhOskksssssekOhhhhO.
.OhhOssssssssssOhhhhO.
.OhhhOssssmsssOhhhhO..
..OhhhOkssssskOhhhhhO.
..OhhOOOkkkkOOOhhhOO..
..OOOcOwWOkOWwOcOOO...
..OccOwwwOrOwwwOccO...
.OcccOOwOrROwOOcccO...
.OccCcOOOrROOOcCccO...
.OccCczcOrROczcCccO...
.OccCczcOrRrOczcCcO...
.OccCzccOOROOcczCccO..
.OccCzcccOOOcccczCcO..
.OczCzcccccccccczCcO..
.OccOzcccccccccczOccO.
.OsOOczcccccccczcOOsO.
.OsOOczcccccccczcOsO..
..OOOpqpPqpPqpPqpOO...
....OpqpPqpPqpPqpO....
....OpqpPqpPqpPqpqO...
....OOOOOOOOOOOOOOO...
......OskO...OksO.....
......OssO...OssO.....
......OssO...OssO.....
......OxxO...OxxO.....
......OxXO...OXxO.....
......OxxO...OxxO.....
.....OgggGO.OGgggO....
.....OggggO.OggggO....
.....OnnnnO.OnnnnO....
.....OOOOOO.OOOOOO....
"""

# side view, facing right ----------------------------------------------------------------
SIDE_HEAD = """
............OO........
...........OhO........
........OOOOhOO.......
......OOhhhhhhhOO.....
.....OhhhhhhHHhhhO....
....OhhhhhhHHihhhhO...
...OhhhhhhhhHHhhhhhO..
...OhhhhhhhhhhhhhhhhO.
..OhhhhhhhhhhhhhhhhhO.
..OhhhhhhhhhhhhhhhhhhO
..OhhhhhhhhhhhhhhhhhhO
..OhhhhhhhhhhhhhOOhhOO
..OhhhhhhhhhhhhOsssOhO
..OhhhhhhhhhhhOssssOO.
..OhhhhhhhhhhOsEEEssO.
..OhhhhhhhhhhOssEesssO
..OhhhhhhhhhhOkksssssO
..OhhhhhhhhhOOssssmsO.
...OhhhhhhhhhOkksssO..
..OhhhhhhhhhhOOkkkO...
.OhOOOhhhhhhOO.OkO....
"""

# torso without the near arm; the arm is its own piece so it can swing
SIDE_TORSO = """
.....OOOOOOOwWwO......
.....OcccccOwOrO......
.....OcccccOwrRO......
.....OccCccczOrO......
.....OccCcccczRO......
.....OcCcccccczO......
.....OcCccccccczO.....
.....OcCccccccczO.....
.....OcCccccccczO.....
.....OcCccccccczO.....
.....OcCcccccccczO....
.....OOOOOOOOOOOOO....
.....OpqpPqpPqpPqO....
.....OpqpPqpPqpPqpO...
.....OpqpPqpPqpPqpO...
.....OOOOOOOOOOOOOO...
"""

# near arm, hanging from the shoulder; sleeve past the wrist, fingertips peeking
ARM = """
.OO..
OccO.
OcCO.
OcCO.
OcCO.
OcCzO
OccCO
OccCO
OccCO
OcczO
OcczO
.OskO
.OOO.
"""
ARM_AT = (8, 22)     # top-left of the arm on the side canvas (x, y)

# one leg in profile, hung from under the hem: calf, sock, chunky sneaker
LEG = """
.OsO
.OskO
.OssO
.OssO
.OxxO
.OxxO
.OxXO
.OxxO
OgggggO
OgggGggO
OnnnnnnO
OOOOOOOO
"""
LEG_AT = (9, 37)     # top-left of the leg on the side canvas
