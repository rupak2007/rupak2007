#!/usr/bin/env python3
"""Rupak's character, animated. Every frame is derived from the master grids in
girl_master.py (FRONT and SIDE), so hair, outfit, colours and proportions never drift.

Writes
  assets/sprites/girl-front.png        static full body, native size
  assets/sprites/girl-idle-{0,1,2}.png idle frames: rest, breath, blink
  assets/sprites/girl-walk.png         6-frame side walk sheet (facing right)
  assets/sprites/girl-walk.gif         the walk as a GIF (3x, 130 ms per frame)
  assets/sprites/portrait.png          still fallback for the info card
  assets/divider.svg                   her walking left to right, a cat trotting behind

Run: python3 scripts/girl.py [preview.png]   (needs Pillow; the Action does not run this)
Mirror: walk_frames(right=False) gives the right-to-left walk."""
import base64
import io
import pathlib
import sys

from PIL import Image, ImageOps

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402
import girl_master as M  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPRITES = ROOT / "assets" / "sprites"
CAT_SHEET = ROOT / "raw" / "anime" / "Sprites" / "NPCs" / "Animals" / "sheet_cat.png"
N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
N4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]


# ---- grid helpers -------------------------------------------------------------------
def grid(rows):
    return [list(r) for r in rows]


def blank(h, w):
    return [["."] * w for _ in range(h)]


def strip_outline(g):
    """Drop the outer outline ring so layers can be cut apart and re-outlined."""
    h, w = len(g), len(g[0])
    out = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] == "O" and any(not (0 <= y + dy < h and 0 <= x + dx < w) or g[y + dy][x + dx] == "."
                                      for dy, dx in N8):
                out[y][x] = "."
    return out


def ring(g):
    """Outline: every empty pixel touching the shape (4-neighbour) becomes O."""
    h, w = len(g), len(g[0])
    out = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] == "." and any(0 <= y + dy < h and 0 <= x + dx < w and g[y + dy][x + dx] not in "._"
                                      for dy, dx in N4):
                out[y][x] = "O"
    return out


def over(dst, src, ox=0, oy=0):
    for y, r in enumerate(src):
        for x, c in enumerate(r):
            if c != "." and 0 <= y + oy < len(dst) and 0 <= x + ox < len(dst[0]):
                dst[y + oy][x + ox] = c
    return dst


def shear(g, y0, y1, off, anchor):
    """Shift each row horizontally, growing linearly from 0 at `anchor` to `off` at y1 and
    staying at `off` below it (so a foot moves as one piece)."""
    out = blank(len(g), len(g[0]))
    for y, r in enumerate(g):
        s = 0 if y <= anchor else round(off * min(1, (y - anchor) / max(1, y1 - anchor)))
        for x, c in enumerate(r):
            if c != "." and 0 <= x + s < len(r):
                out[y][x + s] = c
    return out


def pad(g, left, right, top=0, bottom=0):
    w = len(g[0]) + left + right
    return [["."] * w for _ in range(top)] + [["."] * left + r + ["."] * right for r in g] + \
        [["."] * w for _ in range(bottom)]


def to_png(g):
    im = Image.new("RGBA", (len(g[0]), len(g)), (0, 0, 0, 0))
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c != ".":
                im.putpixel((x, y), M.PAL[c] + ((110,) if c == "_" else (255,)))
    return im


# ---- front idle -----------------------------------------------------------------------
WAIST = 36  # rows above this rise and settle with her breathing


def front_frames():
    base = pad(grid(M.FRONT), 1, 1, 1, 1)
    rest = [r[:] for r in base]
    breath = [r[:] for r in base]
    for y in range(WAIST + 1, 0, -1):    # exhale: head, shoulders and hair settle 1px
        breath[y] = base[y - 1][:]
    breath[0] = ["."] * len(base[0])
    blink = [r[:] for r in base]
    for y, x0 in ((16, 6), (17, 6)):     # rows 15-16 of the master, +1 for the padding
        row = blink[y]
        for x in range(x0, x0 + 15):
            if row[x] in "Ee":
                row[x] = "s" if y == 16 else "E"
    return [rest, breath, blink]


# ---- side walk --------------------------------------------------------------------------
PONYTAIL = """
.hhhh.
hhHhhh
hhhhhh
.hhhhh
.hhhH.
.hhhh.
.hhhh.
.hHhh.
..hhh.
..hhh.
..hhH.
..hhh.
...hh.
...hh.
..hhh.
..hh..
..h...
"""
TAIL_AT = (6, 17)
# one leg in profile (calf, knee sock, chunky sneaker), hung from just under the hem
LEG = """
..ssk
..ssk
..sssk
..sssk
..sssk
..sssk
...ssk
...ssk
...ssk
...ssk
...ssk
...xxX
...xxX
...xxX
...xxX
...xxX
...xxX
..gggggW
..ggggggg
..gggGgggg
.gggggggggg
.gggggggggW
.GGGGGGGGGG
"""
LEG_AT = (11, 64)  # top-left of the tail in the padded side grid (x, y)
HEM = 63       # last skirt row; legs hang from under it
KNEE = 60      # legs pivot here (hidden by the skirt)
ANKLE = 79     # the shoe below moves as one piece
SHOULDER = 25  # arm pivot


def side_layers():
    g = strip_outline(pad(grid(M.SIDE), 4, 4))
    h, w = len(g), len(g[0])
    # legs: drop the traced pair and hang the drawn leg under the hem
    for y in range(HEM + 1, h):
        for x in range(w):
            g[y][x] = "."
    leg = blank(h + 2, w + 8)
    over(leg, grid(LEG.strip("\n").split("\n")), *LEG_AT)
    # ponytail: round off the back of the head at the nape, then hang the drawn tail there
    tail = blank(h, w)
    nape = {17: 2, 18: 3, 19: 4, 20: 5, 21: 6, 22: 8}
    for y in range(17, 44):
        for x in range(0, 16):
            if g[y][x] in "hH" and (y > 22 or x < nape[y] + 4):
                g[y][x] = "."
    over(tail, grid(PONYTAIL.strip("\n").split("\n")), *TAIL_AT)
    # near arm: white sleeve and hand
    arm = blank(h, w)
    for y in range(22, 56):
        for x in range(9, 18):
            c = g[y][x]
            if c in "wW" or (y >= 47 and c in "sk"):
                arm[y][x] = c
                g[y][x] = "d" if x >= 11 else "."
    for y in range(40, HEM + 1):  # re-run the pleats over what the arm uncovered
        for x in range(w):
            if g[y][x] in "dDq":
                g[y][x] = "q" if (x - 8) % 3 == 0 and y > 42 else ("D" if (x - 8) % 3 == 1 and y > 46 else "d")
    g = [[c if c != "O" else ("O") for c in r] for r in g]
    return g, tail, arm, leg


def darker(g):
    t = {"s": "k", "w": "W", "g": "W", "W": "G", "x": "x", "X": "x", "k": "k"}
    return [[t.get(c, c) for c in r] for r in g]


def lift(g, n):
    return g[n:] + [["."] * len(g[0]) for _ in range(n)] if n else g


#        near  far  near-lift far-lift  hand  bob  tail
CYCLE = [(+6, -6, 0, 0, -3, 0, 0),    # contact: near leg forward, both feet down
         (+3, -4, 0, 1, -2, 1, -1),   # down: weight settles a pixel, back heel rising
         (0, -1, 0, 2, 0, 0, -1),     # passing: far leg swings through, foot lifted
         (-6, +6, 0, 0, +3, 0, 0),    # contact: far leg forward
         (-4, +3, 1, 0, +2, 1, -1),   # down
         (-1, 0, 2, 0, 0, 0, -1)]     # passing: near leg swings through


def side_frame(k, layers):
    body, tail, arm, leg = layers
    near, far, nl, fl, hand, bob, tdx = CYCLE[k]
    h, w = len(body), len(body[0])
    bottom = len(leg)
    f = blank(h + 2, w)
    over(f, ring(lift(darker(shear(leg, KNEE, ANKLE, far, KNEE)), fl)))
    over(f, ring(lift(shear(leg, KNEE, ANKLE, near, KNEE), nl)))
    up = blank(h, w)
    over(up, ring(body))
    over(up, ring(shear(tail, 20, 34, tdx, 22)), 0, 0)
    over(up, ring(shear(arm, SHOULDER, 55, hand, SHOULDER)))
    # everything above the hem rides the bob; legs stay planted
    for y in range(HEM + 1 + 1):
        for x in range(w):
            c = up[y][x]
            if c != "." and y + bob < len(f):
                f[y + bob][x] = c
    # body pixels that moved down a row leave the gap above the hem filled by the skirt
    return f


def side_frames(right=True):
    layers = side_layers()
    frames = [side_frame(k, layers) for k in range(6)]
    return frames if right else [[r[::-1] for r in f] for f in frames]


def with_shadow(g, cx=None):
    g = [r[:] for r in g] + [["."] * len(g[0])]
    ys = [y for y, r in enumerate(g) for c in r if c != "."]
    bottom = max(ys)
    xs = [x for x, c in enumerate(g[bottom]) if c != "."]
    x0, x1 = min(xs) - 2, max(xs) + 2
    for x in range(max(0, x0), min(len(g[0]), x1 + 1)):
        if g[bottom + 1 if bottom + 1 < len(g) else bottom][x] == ".":
            g[bottom + 1 if bottom + 1 < len(g) else bottom][x] = "_"
    return g


# ---- cat -------------------------------------------------------------------------------
def cat_frames():
    sheet = Image.open(CAT_SHEET).convert("RGBA")
    out = []
    for c in range(4):
        cell = sheet.crop((c * 64, 64, c * 64 + 64, 128))
        f = cell.crop(cell.getbbox())
        im = Image.new("RGBA", f.size)
        for y in range(f.height):
            for x in range(f.width):
                p = f.getpixel((x, y))
                if p[3]:
                    L = (p[0] * 3 + p[1] * 6 + p[2]) / 10
                    t = M.PAL["O"] if L < 40 else (40, 44, 58) if L < 120 else (70, 76, 94)
                    im.putpixel((x, y), t + (p[3],))
        out.append(im)
    return out


# ---- outputs -------------------------------------------------------------------------
def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


PIX = "image-rendering:optimizeSpeed;image-rendering:crisp-edges;image-rendering:pixelated"


def divider(walk, cat):
    """She strolls left to right along the rule; the cat trots a few steps behind."""
    fw, fh = walk[0].size
    W, Hh = 840, fh + 2
    rule_y = Hh - 2
    step, n, speed = 0.13, 6, 2           # 130 ms a frame, 2 px a frame: an unhurried walk
    cycle = step * n
    cw, ch = cat[0].size
    lead = cw + 24                        # the cat's distance behind her
    travel = (W + fw + lead) / speed * step
    T = travel + 2.0
    done = travel / T * 100
    girl = "".join(f'<image class="g" style="animation-delay:{k * step - cycle:.2f}s" x="0" y="{rule_y - fh + 1}" '
                   f'width="{fw}" height="{fh}" href="data:image/png;base64,{b64(f)}"/>' for k, f in enumerate(walk))
    cstep = 0.15
    cats = "".join(f'<image class="c" style="animation-delay:{k * cstep - 4 * cstep:.2f}s" x="{-lead}" '
                   f'y="{rule_y - ch + 1}" width="{cw}" height="{ch}" href="data:image/png;base64,{b64(f)}"/>'
                   for k, f in enumerate(cat))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" role="img" aria-label="divider">
<style>
.mv{{animation:mv {T:.2f}s linear infinite}}
@keyframes mv{{0%{{transform:translate(-{fw}px,0)}}{done:.3f}%{{transform:translate({W + lead}px,0)}}100%{{transform:translate({W + lead}px,0)}}}}
.g{{visibility:hidden;{PIX};animation:wk {cycle:.2f}s steps(1,end) infinite}}
@keyframes wk{{0%{{visibility:visible}}{100 / n:.3f}%{{visibility:hidden}}100%{{visibility:hidden}}}}
.c{{visibility:hidden;{PIX};animation:ck {4 * cstep:.2f}s steps(1,end) infinite}}
@keyframes ck{{0%{{visibility:visible}}25%{{visibility:hidden}}100%{{visibility:hidden}}}}
</style>
<rect x="0" y="{rule_y}" width="{W}" height="1" fill="{build.FAINT}"/>
<g class="mv">{cats}{girl}</g>
</svg>
"""


def portrait_still(fig):
    s = int((220 - 14) // fig.height)
    big = fig.resize((fig.width * s, fig.height * s), Image.NEAREST)
    slot = Image.new("RGBA", (184, 220), tuple(int(build.BG[i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    slot.alpha_composite(big, ((184 - big.width) // 2, 220 - big.height - 6))
    return slot


def common_canvas(frames):
    w = max(len(f[0]) for f in frames)
    h = max(len(f) for f in frames)
    return [to_png(pad(f, 0, w - len(f[0]), h - len(f), 0)) for f in frames]


def main(preview=None):
    idle = common_canvas([with_shadow(f) for f in front_frames()])
    walk = common_canvas([with_shadow(f) for f in side_frames()])
    cat = cat_frames()
    if preview:
        Z = 5
        ims = idle + walk
        W = sum(i.width + 6 for i in ims)
        Hh = max(i.height for i in ims)
        strip = Image.new("RGBA", (W, Hh), (52, 58, 70, 255))
        x = 0
        for i in ims:
            strip.alpha_composite(i, (x, Hh - i.height))
            x += i.width + 6
        strip.resize((W * Z, Hh * Z), Image.NEAREST).save(preview)
        return idle, walk, cat
    SPRITES.mkdir(parents=True, exist_ok=True)
    idle[0].save(SPRITES / "girl-front.png")
    for k, f in enumerate(idle):
        f.save(SPRITES / f"girl-idle-{k}.png")
    fw, fh = walk[0].size
    sheet = Image.new("RGBA", (fw * 6, fh))
    for k, f in enumerate(walk):
        sheet.alpha_composite(f, (fw * k, 0))
    sheet.save(SPRITES / "girl-walk.png")
    big = []
    for f in walk:
        b = Image.new("RGBA", (fw * 3, fh * 3), (13, 17, 23, 255))
        b.alpha_composite(f.resize((fw * 3, fh * 3), Image.NEAREST))
        big.append(b.convert("P", palette=Image.ADAPTIVE))
    big[0].save(SPRITES / "girl-walk.gif", save_all=True, append_images=big[1:], duration=130, loop=0)
    portrait_still(idle[0]).save(SPRITES / "portrait.png")
    (ROOT / "assets" / "divider.svg").write_text(divider(walk, cat), encoding="utf-8")
    print("idle", idle[0].size, "walk", walk[0].size, "cat", cat[0].size)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
