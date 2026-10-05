#!/usr/bin/env python3
"""The profile's original character, animated from the master art in girl_art.py.

Writes (all transparent PNG, native pixel size)
  assets/sprites/girl-front.png        22x48  front idle master
  assets/sprites/girl-idle-{0..3}.png  22x48  rest, breath, blink, hair sway
  assets/sprites/girl-walk.png        240x50  8-frame side walk sheet (30x50 cells, facing right)
  assets/sprites/girl-walk.gif         walk preview, 4x, 130 ms per frame
  assets/sprites/portrait.png          info-card still fallback (184x220)
  assets/divider.svg                   her walking left to right, a cat trotting behind

Run: python3 scripts/girl.py [preview.png]   (needs Pillow; the Action does not run this)
Mirror: side_frames(right=False) is the same walk facing left."""
import base64
import io
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402
import girl_art as A  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPRITES = ROOT / "assets" / "sprites"
CAT_SHEET = ROOT / "raw" / "anime" / "Sprites" / "NPCs" / "Animals" / "sheet_cat.png"


def grid(text):
    rows = text.strip("\n").split("\n")
    w = max(len(r) for r in rows)
    return [list(r.ljust(w, ".")) for r in rows]


def blank(h, w):
    return [["."] * w for _ in range(h)]


def over(dst, src, ox=0, oy=0):
    for y, r in enumerate(src):
        for x, c in enumerate(r):
            if c != "." and 0 <= y + oy < len(dst) and 0 <= x + ox < len(dst[0]):
                dst[y + oy][x + ox] = c
    return dst


def shear(g, off, top, bottom):
    """Rows shift by 0 at `top` growing to `off` at `bottom`, then stay at `off` (rigid foot)."""
    out = blank(len(g), len(g[0]))
    for y, r in enumerate(g):
        s = 0 if y <= top else round(off * min(1, (y - top) / max(1, bottom - top)))
        for x, c in enumerate(r):
            if c != "." and 0 <= x + s < len(r):
                out[y][x + s] = c
    return out


def to_png(g):
    im = Image.new("RGBA", (len(g[0]), len(g)), (0, 0, 0, 0))
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c != ".":
                im.putpixel((x, y), A.PALETTE[c] + ((110,) if c == "_" else (255,)))
    return im


# ---- front idle -----------------------------------------------------------------------
WAIST = 32   # rows above this settle 1px when she breathes out
EYES = (14, 15)


def front_frames():
    base = grid(A.FRONT)
    rest = [r[:] for r in base]
    breath = [r[:] for r in base]
    for y in range(WAIST, 0, -1):
        breath[y] = base[y - 1][:]
    breath[0] = ["."] * len(base[0])
    blink = [r[:] for r in base]
    for x in range(len(base[0])):
        if blink[EYES[0]][x] == "E":
            blink[EYES[0]][x] = "s"
        if blink[EYES[1]][x] in "eE":
            blink[EYES[1]][x] = "E"
    sway = [r[:] for r in base]           # the cowlick tips over a pixel
    for y in (0, 1):
        sway[y] = ["."] + base[y][:-1]
    return [rest, breath, blink, sway]


IDLE_LOOP = (6.4, [(0, 0, 1.6), (1, 1.6, 3.0), (0, 3.0, 4.0), (2, 4.0, 4.16), (0, 4.16, 5.0),
                   (3, 5.0, 5.8), (0, 5.8, 6.4)])


# ---- side walk: 8 frames ----------------------------------------------------------------
#          contact down  pass   up   contact down  pass   up
NEAR = [4, 2, 0, -2, -4, -2, 1, 3]        # near foot, px ahead of the hip
FAR = NEAR[4:] + NEAR[:4]                  # the other foot, half a cycle later
NEAR_LIFT = [0, 0, 0, 0, 0, 1, 2, 1]       # foot raised while it swings through
FAR_LIFT = FAR_LIFT = [0, 1, 2, 1, 0, 0, 0, 0]
HAND = [-2, -1, 0, 1, 2, 1, 0, -1]         # near arm swings against the near leg
BOB = [0, 1, 0, -1, 0, 1, 0, -1]           # +1 = down a pixel
TUFT = [0, 0, -1, -1, 0, 0, -1, -1]        # cowlick and bob ends trail a pixel on the rise
W, H = 30, 50
X0 = 4                                      # all side pieces sit 4px in from the left


def darker(g):
    t = {"s": "k", "g": "G", "G": "n", "X": "x"}
    return [[t.get(c, c) for c in r] for r in g]


def leg_layer(off, lift, far):
    leg = grid(A.LEG)
    g = blank(H, W)
    lx, ly = A.LEG_AT
    over(g, darker(leg) if far else leg, X0 + lx, ly - lift)
    return shear(g, off, ly, ly + 7)


def side_frame(k):
    f = blank(H, W)
    over(f, leg_layer(FAR[k], FAR_LIFT[k], True))
    over(f, leg_layer(NEAR[k], NEAR_LIFT[k], False))
    up = blank(H, W)
    head = grid(A.SIDE_HEAD)
    if TUFT[k]:
        for y in range(0, 3):
            head[y] = head[y][1:] + ["."] if TUFT[k] < 0 else ["."] + head[y][:-1]
        for y in range(17, 21):   # the bob's ends at her nape trail with the tuft
            head[y] = head[y][1:] + ["."] if head[y][1] != "." else head[y]
    over(up, grid(A.SIDE_TORSO), X0, len(head))
    ax, ay = A.ARM_AT
    arm = blank(H, W)
    over(arm, grid(A.ARM), X0 + ax, ay)
    over(up, shear(arm, HAND[k], ay + 2, ay + 12))
    over(up, head, X0, 0)
    b = BOB[k]
    for y in range(H):
        for x in range(W):
            c = up[y][x]
            if c != "." and 0 <= y + b + 1 < H:
                f[y + b + 1][x] = c
    return f


def side_frames(right=True):
    frames = [side_frame(k) for k in range(8)]
    return frames if right else [[r[::-1] for r in fr] for fr in frames]


def shadow(g, y):
    g = [r[:] for r in g]
    xs = [x for row in g[y - 3:y] for x, c in enumerate(row) if c != "."]
    for x in range(min(xs) - 1, max(xs) + 2):
        if 0 <= x < len(g[0]) and g[y][x] == ".":
            g[y][x] = "_"
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
                    t = A.PALETTE["O"] if L < 40 else (40, 44, 58) if L < 120 else (72, 78, 96)
                    im.putpixel((x, y), t + (p[3],))
        out.append(im)
    return out


# ---- outputs -------------------------------------------------------------------------
def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


PIX = "image-rendering:optimizeSpeed;image-rendering:crisp-edges;image-rendering:pixelated"
SCALE = 1   # the divider shows her at native size, like the boy


def divider(walk, cat):
    fw, fh = walk[0].size
    Wd, Hd = 840, fh + 2
    rule_y = Hd - 2
    step, n, speed = 0.13, 8, 2            # 130 ms a frame, 2 px a frame: a sleepy stroll
    cycle = step * n
    cw, ch = cat[0].size
    gap = cw + 10                          # the cat a few steps behind her
    travel = (Wd + fw + gap) / speed * step
    T = travel + 2.0
    done = travel / T * 100
    girl = "".join(f'<image class="g" style="animation-delay:{k * step - cycle:.2f}s" x="0" y="{rule_y - fh + 1}" '
                   f'width="{fw}" height="{fh}" href="data:image/png;base64,{b64(f)}"/>' for k, f in enumerate(walk))
    cstep = 0.15
    cats = "".join(f'<image class="c" style="animation-delay:{k * cstep - 4 * cstep:.2f}s" x="{-gap}" '
                   f'y="{rule_y - ch + 1}" width="{cw}" height="{ch}" href="data:image/png;base64,{b64(f)}"/>'
                   for k, f in enumerate(cat))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{Wd}" height="{Hd}" viewBox="0 0 {Wd} {Hd}" role="img" aria-label="divider">
<style>
.mv{{animation:mv {T:.2f}s linear infinite}}
@keyframes mv{{0%{{transform:translate(-{fw}px,0)}}{done:.3f}%{{transform:translate({Wd + gap}px,0)}}100%{{transform:translate({Wd + gap}px,0)}}}}
.g{{visibility:hidden;{PIX};animation:wk {cycle:.2f}s steps(1,end) infinite}}
@keyframes wk{{0%{{visibility:visible}}{100 / n:.3f}%{{visibility:hidden}}100%{{visibility:hidden}}}}
.c{{visibility:hidden;{PIX};animation:ck {4 * cstep:.2f}s steps(1,end) infinite}}
@keyframes ck{{0%{{visibility:visible}}25%{{visibility:hidden}}100%{{visibility:hidden}}}}
</style>
<rect x="0" y="{rule_y}" width="{Wd}" height="1" fill="{build.FAINT}"/>
<g class="mv">{cats}{girl}</g>
</svg>
"""


def portrait_still(fig):
    s = 4
    big = fig.resize((fig.width * s, fig.height * s), Image.NEAREST)
    bg = tuple(int(build.BG[i:i + 2], 16) for i in (1, 3, 5))
    slot = Image.new("RGBA", (184, 220), bg + (255,))
    slot.alpha_composite(big, ((184 - big.width) // 2, 220 - big.height - 8))
    return slot


def build_all():
    idle = [to_png(f) for f in front_frames()]
    walk = [to_png(shadow(f, H - 1)) for f in side_frames()]
    return idle, walk, cat_frames()


def main(preview=None):
    idle, walk, cat = build_all()
    if preview:
        Z = 8
        ims = idle + walk
        Wp = sum(i.width + 4 for i in ims)
        Hp = max(i.height for i in ims)
        strip = Image.new("RGBA", (Wp, Hp), (52, 58, 70, 255))
        x = 0
        for i in ims:
            strip.alpha_composite(i, (x, Hp - i.height))
            x += i.width + 4
        strip.resize((Wp * Z, Hp * Z), Image.NEAREST).save(preview)
        return
    SPRITES.mkdir(parents=True, exist_ok=True)
    idle[0].save(SPRITES / "girl-front.png")
    for k, f in enumerate(idle):
        f.save(SPRITES / f"girl-idle-{k}.png")
    fw, fh = walk[0].size
    sheet = Image.new("RGBA", (fw * 8, fh))
    for k, f in enumerate(walk):
        sheet.alpha_composite(f, (fw * k, 0))
    sheet.save(SPRITES / "girl-walk.png")
    gif = []
    for f in walk:
        b = Image.new("RGBA", (fw * 4, fh * 4), (13, 17, 23, 255))
        b.alpha_composite(f.resize((fw * 4, fh * 4), Image.NEAREST))
        gif.append(b.convert("P", palette=Image.ADAPTIVE))
    gif[0].save(SPRITES / "girl-walk.gif", save_all=True, append_images=gif[1:], duration=130, loop=0)
    portrait_still(idle[0]).save(SPRITES / "portrait.png")
    (ROOT / "assets" / "divider.svg").write_text(divider(walk, cat), encoding="utf-8")
    print("front", idle[0].size, "walk cell", walk[0].size, "cat", cat[0].size)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
