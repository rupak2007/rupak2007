#!/usr/bin/env python3
"""The recurring character, kept pixel-for-pixel to the reference picture Rupak gave.

trace() reads that picture (raw/girl-ref.png, an upscaled pixel-art render), finds its pixel
grid (about 5.9 x 5.6 screen px per art pixel), takes the middle of each cell, drops the black
background and settles every pixel onto a fixed palette: the profile's cool greys, with the
bow kept red as in the reference. That gives assets/sprites/girl.png, her native pixels, which
is committed, so the rest runs without the reference.

main() animates those pixels without redrawing her:
  assets/sprites/portrait.png, portrait-breath.png, portrait-blink.png
                         2x idle poses for the info card (build.py loops them)
  assets/divider.svg     her stepping across the rule: each foot lifts in turn, the body
                         bobs and the ponytail swings
Run: python3 scripts/girl.py            (python3 scripts/girl.py trace  to re-trace)
"""
import base64
import io
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402
from night import H  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = ROOT / "raw" / "girl-ref.png"
NATIVE = ROOT / "assets" / "sprites" / "girl.png"

OUTLINE = (2, 3, 6)
# source luminance band -> profile grey
BANDS = [(16, OUTLINE), (30, (19, 23, 29)), (44, (36, 43, 53)), (62, (52, 60, 71)), (90, (72, 81, 94)),
         (125, (104, 113, 125)), (165, (145, 153, 163)), (200, (184, 192, 201)), (256, (214, 220, 227))]
BOW_DARK, BOW = (98, 30, 38), (160, 52, 58)
SKIN, LASH = (214, 220, 227), (36, 43, 53)
SHADOW = H("#8b949e")

# landmarks on the native sprite (x0, x1, y0, y1 inclusive)
EYES = [(10, 13, 22, 24), (19, 23, 22, 24)]
WAIST = 47            # rows above this settle a pixel on the breath
LEGS_TOP = 67         # first row below the skirt
LEFT_LEG, RIGHT_LEG = (6, 15), (19, 29)
PONYTAIL = (29, 34, 32, 44)   # the loose end hanging past her right sleeve


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def trace():
    import numpy as np
    src = Image.open(REF).convert("RGB")
    a = np.asarray(src).astype(float)
    L = a.mean(2)

    def fit(g, lo, hi):  # strongest period in the edge profile, and where its edges fall
        best = None
        for p in np.arange(lo, hi, 0.005):
            z = (g * np.exp(2j * np.pi * np.arange(len(g)) / p)).sum()
            if best is None or abs(z) > best[0]:
                best = (abs(z), p, np.angle(z))
        _, p, ang = best
        return p, (-ang / (2 * np.pi) * p) % p + 1

    px, ox = fit(np.abs(np.diff(L, axis=1)).sum(0), 5.6, 6.2)
    py, oy = fit(np.abs(np.diff(L, axis=0)).sum(1), 5.4, 6.0)
    cols, rows = int((src.width - ox) // px), int((src.height - oy) // py)
    cell = Image.new("RGB", (cols, rows))
    for r in range(rows):
        for c in range(cols):
            x0, y0 = ox + c * px, oy + r * py
            blk = a[int(y0 + py * .3):int(y0 + py * .7) + 1, int(x0 + px * .3):int(x0 + px * .7) + 1]
            cell.putpixel((c, r), tuple(int(v) for v in np.median(blk.reshape(-1, 3), axis=0)))
    w, h = cell.size
    # background: the near-black reachable from the border
    bg, stack = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in bg or not (0 <= x < w and 0 <= y < h) or sum(cell.getpixel((x, y))) / 3 >= 8:
            continue
        bg.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    out = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            if (x, y) in bg:
                continue
            p = cell.getpixel((x, y))
            if p[0] - p[1] > 35:
                c = BOW if p[0] > 130 else BOW_DARK
            else:
                c = next(c for top, c in BANDS if lum(p) < top)
            out.putpixel((x, y), c + (255,))
    out = despeckle(tidy(out))
    out = out.crop(out.getbbox())
    NATIVE.parent.mkdir(parents=True, exist_ok=True)
    out.save(NATIVE, optimize=True)
    print("traced", NATIVE.name, out.size)


def tidy(im):
    """Drop the render's dark fringe (outline pixels touching the background; outlined() draws a
    clean one later) and close 1px gaps between pixels above and below."""
    w, h = im.size
    out = im.copy()
    for y in range(h):
        for x in range(w):
            p = im.getpixel((x, y))
            if p[3] and p[:3] == OUTLINE and any(not (0 <= x + dx < w and 0 <= y + dy < h) or im.getpixel((x + dx, y + dy))[3] == 0
                                                 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), (0, 0, 0, 0))
    gaps = out.copy()
    for y in range(1, h - 1):
        for x in range(w):
            if out.getpixel((x, y))[3] == 0 and out.getpixel((x, y - 1))[3] and out.getpixel((x, y + 1))[3]:
                gaps.putpixel((x, y), out.getpixel((x, y - 1)))
    return gaps


def despeckle(im):
    """A pixel whose four neighbours all agree on another colour takes theirs."""
    out = im.copy()
    w, h = im.size
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            n = {im.getpixel(q) for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))}
            if len(n) == 1 and im.getpixel((x, y))[3] and next(iter(n))[3]:
                out.putpixel((x, y), n.pop())
    return out


def outlined(im):
    """1px outer outline, plus a margin, so she reads on light GitHub too."""
    w, h = im.size
    out = Image.new("RGBA", (w + 2, h + 2))
    out.alpha_composite(im, (1, 1))
    a = out.getchannel("A")
    for y in range(h + 2):
        for x in range(w + 2):
            if a.getpixel((x, y)) == 0 and any(0 <= x + dx < w + 2 and 0 <= y + dy < h + 2 and a.getpixel((x + dx, y + dy))
                                              for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), OUTLINE + (255,))
    return out


def move(im, box, dx, dy):
    """Shift the opaque pixels inside box=(x0, x1, y0, y1) by (dx, dy); what they uncover is cleared."""
    x0, x1, y0, y1 = box
    part = im.crop((x0, y0, x1 + 1, y1 + 1))
    out = im.copy()
    out.paste((0, 0, 0, 0), (x0, y0, x1 + 1, y1 + 1))
    out.alpha_composite(part, (x0 + dx, y0 + dy))
    return out


def blink(im):
    out = im.copy()
    for x0, x1, y0, y1 in EYES:
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                if out.getpixel((x, y))[3]:
                    out.putpixel((x, y), (LASH if y == y0 + 1 else SKIN) + (255,))
    return out


def breath(im):
    """Head and chest settle a pixel; the waist row takes the squeeze, legs stay put."""
    w, h = im.size
    out = Image.new("RGBA", (w, h))
    out.alpha_composite(im.crop((0, WAIST + 1, w, h)), (0, WAIST + 1))
    out.alpha_composite(im.crop((0, 0, w, WAIST)), (0, 1))
    return out


def step(im, side):
    """One foot lifts (the leg slides up under the skirt), body rises a pixel, ponytail swings."""
    w, h = im.size
    lx0, lx1 = LEFT_LEG if side == "left" else RIGHT_LEG
    legs = im.crop((0, LEGS_TOP, w, h))
    body = im.crop((0, 0, w, LEGS_TOP))
    out = Image.new("RGBA", (w, h))
    lifted = legs.crop((lx0, 2, lx1 + 1, legs.height))   # its top two rows go under the skirt
    rest = legs.copy()
    rest.paste((0, 0, 0, 0), (lx0, 0, lx1 + 1, legs.height))
    out.alpha_composite(rest, (0, LEGS_TOP))
    out.alpha_composite(lifted, (lx0, LEGS_TOP - 1))
    out.alpha_composite(body, (0, -1))
    return move(out, PONYTAIL, 1 if side == "left" else -1, 0)


def with_shadow(im, ground):
    """Stand the figure in a taller canvas with a soft ground shadow under her feet."""
    w, h = im.size
    out = Image.new("RGBA", (w, ground + 2))
    for x in range(3, w - 3):
        out.putpixel((x, ground), SHADOW + (150 if 5 <= x < w - 5 else 90,))
    out.alpha_composite(im, (0, ground - h + 1))
    return out


def portrait(im):
    """2x into the info card's 184x220 slot, on the same faint scanlines as before."""
    fig = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    slot = Image.new("RGBA", (184, 220), H(build.BG) + (255,))
    for y in range(0, 220, 8):
        slot.paste(H("#10151c") + (255,), (0, y, 184, min(y + 4, 220)))
    slot.alpha_composite(fig, ((184 - fig.width) // 2, 220 - fig.height - 12))
    return slot


def divider(frames, W=840, Hh=100, step_s=0.18, speed=2):
    """An animated SVG (always runs on GitHub, unlike GIFs) of her stepping along the 1px rule,
    on a transparent background so it sits on light and dark GitHub alike."""
    rule_y = Hh - 4
    fw = frames[0].width
    imgs = []
    for k, f in enumerate(frames):
        buf = io.BytesIO()
        f.save(buf, "PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        imgs.append(f'<image class="w" y="{rule_y + 2 - f.height}" style="animation-delay:{k * step_s - 4 * step_s:.2f}s" '
                    f'width="{f.width}" height="{f.height}" href="data:image/png;base64,{b64}"/>')
    travel = (W + fw) / speed * step_s   # seconds to cross
    T = travel + 16 * step_s             # plus a short pause off-stage
    done = travel / T * 100
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" role="img" aria-label="divider">
<style>
.mv{{animation:mv {T:.2f}s linear infinite}}
@keyframes mv{{0%{{transform:translate(-{fw}px,0px)}}{done:.3f}%{{transform:translate({W}px,0px)}}100%{{transform:translate({W}px,0px)}}}}
.w{{visibility:hidden;image-rendering:pixelated;animation:wk {4 * step_s:.2f}s steps(1,end) infinite}}
@keyframes wk{{0%{{visibility:visible}}25%{{visibility:hidden}}100%{{visibility:hidden}}}}
</style>
<rect x="0" y="{rule_y}" width="{W}" height="1" fill="{build.FAINT}"/>
<g class="mv">{"".join(imgs)}</g>
</svg>
"""


def main():
    girl = Image.open(NATIVE).convert("RGBA")
    sprites = NATIVE.parent
    for name, pose in (("portrait.png", girl), ("portrait-breath.png", breath(girl)), ("portrait-blink.png", blink(girl))):
        portrait(outlined(pose)).save(sprites / name, optimize=True)
        print("wrote", name)
    ground = girl.height + 2
    walk = [girl, step(girl, "left"), girl, step(girl, "right")]
    frames = [with_shadow(outlined(f), ground) for f in walk]
    out = ROOT / "assets" / "divider.svg"
    out.write_text(divider(frames), encoding="utf-8")
    print("wrote", out.name, f"{out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    trace() if sys.argv[1:] == ["trace"] else main()
