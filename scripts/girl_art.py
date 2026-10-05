"""An original character for the profile, drawn pixel by pixel at the boy's scale (~48px).

CHARACTER SPEC (every frame follows this)
  hair       near-black blue chin-length bob with a blunt, dead-straight fringe cut just
             above the eyes; one long lock escapes the fringe and hangs over her left eye;
             a stubby low tail tied at the nape with a dark band pokes out behind her; a
             cowlick on the crown; the bob's ends flick out over her shoulders
  face       pale; eyes nearly shut (a dark lid line with a single grey pixel of iris under
             it), soft shadows under both eyes, a flat 2px mouth; always a little withdrawn
  outfit     oversized charcoal-navy cardigan, dropped shoulders, sleeves past the wrists
             (fingertips only), two grey buttons, a lighter knitted hem band; a rounded light
             grey collar with a thin muted-red cord tied in a small knot (her only colour);
             dark pleated skirt with one lighter stripe at the hem; dark mid-calf socks;
             light chunky sneakers with a dark sole line
  palette    see PALETTE: 2-3 tones per material, one muted red, black outline
  silhouette round bob with a flat fringe line, hair flicks at the shoulders, the tail stub
             at the back, a wide cardigan over a short skirt, thin legs, big shoes

One letter per pixel. FRONT is drawn as a left half and mirrored, then the asymmetric
details (cowlick, loose lock, tail stub) are placed on top."""

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
    "b": (120, 126, 140),  # button
    "t": (16, 17, 24),     # hair tie
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

# left half of the front view (columns 0-10); the right half is its mirror
_FRONT_HALF = """
...........
...........
.......OOOO
.....OOhhhh
....Ohhhhhh
...OhhhhhhH
...OhhhhhhH
..Ohhhhhhhh
..Ohhhhhhhh
..Ohhhhhhhh
.Ohhhhhhhhh
.Ohhhhhhhhh
.OhhOOOOOOO
.OhhOssssss
.OhhOsEEEss
.OhhOskeEss
.OhhOkkksss
.OhhOssssss
.OhhhOssssm
.OhhhOkssss
OhhhhhOOOkk
OhOOcOOwwwk
.OccOwwwwwO
.OcccOwwwOr
.OczccOOOrR
.Oczccczccr
.Oczccczccz
.Oczccczccb
.Oczccczccz
.Oczccczccz
.Oczccczccb
.OsOCcczccz
.OsOCCCCCCC
..OOOOOOOOO
...OpqpPqpP
....OpqpPqp
....OPPPPPP
....OOOOOOO
......OskO.
......OssO.
......OssO.
......OxxO.
......OxXO.
......OxxO.
.....OgggGO
.....OggggO
.....OnnnnO
.....OOOOOO
"""


def _mirror_front():
    rows = [r.ljust(11, ".") for r in _FRONT_HALF.strip("\n").split("\n")]
    g = [list(r + r[::-1]) for r in rows]

    def put(y, x, txt):
        for i, c in enumerate(txt):
            if c != "?":
                g[y][x + i] = c
    put(0, 12, "OO")        # cowlick curling toward her left
    put(1, 11, "OhhO")
    put(2, 11, "hh")
    for y, txt in ((12, "hhO"), (13, "hhO"), (14, "Ohh"), (15, "?hh"), (16, "?Oh"), (17, "??O")):
        put(y, 12, txt)     # the loose lock over her left eye
    put(19, 21, "O")        # tail stub poking out past her right shoulder
    put(20, 0, "Oh")
    return "\n".join("".join(r) for r in g)


FRONT = _mirror_front()

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
..OhhhhhhhhhhhhhhhhhhO
..OhhhhhhhhhhhhhOOOOOO
..OhhhhhhhhhhhhOhssssO
..OhhhhhhhhhhhOhsEEEsO
..OhhhhhhhhhhhOhskeEssO
..OhhhhhhhhhhhOkkkssssO
..OhhhhhhhhhhOOsssmsO..
..OhhhhhhhhhhOkksssO...
...OhhhhhhhhhOOkkkO....
....OOhhhhhhOO.OkO.....
"""

# the stubby low tail, tied at the nape; drawn behind the head so it pokes out at the back
TAIL = """
..Ott
.OhtO
OhhhO
OhHhO
.OhhO
.OhO.
..O..
"""
TAIL_AT = (1, 17)    # top-left on the side canvas, before the 4px margin

# torso without the near arm; the arm is its own piece so it can swing
SIDE_TORSO = """
.....OOOOOOOOwwwO.....
.....OcccccOwwwwO.....
.....OcccccczOrRO.....
.....OccCcccczOrO.....
.....OccCccccczrO.....
.....OcCccccccczO.....
.....OcCcccccccbO.....
.....OcCcccccccczO....
.....OcCccccccccbO....
.....OcCcccccccczO....
.....OCCCCCCCCCCCO....
.....OOOOOOOOOOOOO....
.....OpqpPqpPqpPqO....
.....OpqpPqpPqpPqpO...
.....OPPPPPPPPPPPPO...
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
