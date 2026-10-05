#!/usr/bin/env python3
"""The profile's character: a schoolgirl sprite the profile owner generated with ChatGPT
(first of the five in raw/girls.png), resampled from its upscaled render back to its pixel
grid (39x91), background removed, and toned into the profile's greys with the bow in the
accent colour. Writes:
  assets/sprites/avatar.png    native pixels for the info card (avatar.py makes its idle poses)
  assets/sprites/portrait.png  2x still, the info card's fallback
  assets/divider.svg           standing on the divider rule, breathing and blinking
Run: python3 scripts/character.py
"""
import base64
import io
import pathlib
import sys
from collections import Counter

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402
from night import H  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
NATIVE = ROOT / "raw" / "girl1_native.png"

# luminance bands -> profile greys: three darks so hair strands and pleats survive
BANDS = [(22, "#0b0e13"), (34, "#1b212a"), (50, "#2b333e"), (95, "#434c59"),
         (150, "#6e7681"), (200, "#aab3be"), (256, "#e3e9ee")]
DARKS = {H(c) for c in ("#1b212a", "#2b333e", "#434c59")}
BOW, BOW_SHADE = H("#4fa3ad"), H("#2e6b73")
OUTLINE = H("#030407")


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _despeckle(im, protect, passes):
    """A pixel with no same-coloured 4-neighbour takes its neighbours' most common colour."""
    w, h = im.size
    for _ in range(passes):
        s, d = im.copy().load(), im.load()
        for y in range(h):
            for x in range(w):
                p = s[x, y]
                if not p[3] or (x, y) in protect:
                    continue
                if any(0 <= x + dx < w and 0 <= y + dy < h and s[x + dx, y + dy] == p
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    continue
                n8 = [s[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if (dx or dy) and 0 <= x + dx < w and 0 <= y + dy < h and s[x + dx, y + dy][3]]
                if n8:
                    d[x, y] = Counter(n8).most_common(1)[0][0]
    return im


def _clump(im, protect, passes=2, need=5):
    """Within the dark tones (hair, uniform), a pixel outvoted by 5+ of its 8 neighbours joins
    them, so the render noise settles into clean clumps."""
    w, h = im.size
    for _ in range(passes):
        s, d = im.copy().load(), im.load()
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                p = s[x, y]
                if not p[3] or (x, y) in protect or p[:3] not in DARKS:
                    continue
                n = [s[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
                n = [q for q in n if q[3] and q[:3] in DARKS]
                if n:
                    c, k = Counter(n).most_common(1)[0]
                    if c != p and k >= need:
                        d[x, y] = c
    return im


def _outline(im):
    w, h = im.size
    out = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    out.alpha_composite(im, (1, 1))
    a, o = out.getchannel("A").load(), out.load()
    ring = [(x, y) for y in range(h + 2) for x in range(w + 2) if not a[x, y] and any(
        0 <= x + dx < w + 2 and 0 <= y + dy < h + 2 and a[x + dx, y + dy]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for xy in ring:
        o[xy] = OUTLINE + (255,)
    return out


def styled():
    """Native pixels -> profile palette -> despeckled -> dark tones clumped -> 1px outline."""
    src = Image.open(NATIVE).convert("RGB")
    w, h = src.size
    bg, stack = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:  # background: flood fill the near-black from the border
        x, y = stack.pop()
        if (x, y) in bg or not (0 <= x < w and 0 <= y < h) or lum(src.getpixel((x, y))) >= 16:
            continue
        bg.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            if (x, y) in bg:
                continue
            r, g, b = src.getpixel((x, y))
            if r - g > 40:  # the bow, in the dimmer accent with one shade
                c = BOW if lum((r, g, b)) > 70 else BOW_SHADE
            else:
                c = H(next(col for top, col in BANDS if lum((r, g, b)) < top))
            im.putpixel((x, y), c + (255,))
    im = im.crop(im.getchannel("A").getbbox())
    face = {(x, y) for y in range(19, 27) for x in range(6, 28)}       # eyes and lashes stay as drawn
    pleats = {(x, y) for y in range(47, 67) for x in range(im.width)}  # keep the skirt's folds
    im = _despeckle(im, face, passes=2)
    im = _clump(im, face | pleats)
    im = _despeckle(im, face, passes=1)
    return _outline(im)


SKIN, LASH = H("#e3e9ee"), H("#2b333e")
EYE_ROW = 24  # rows 24-25 of the outlined sprite
EYES = [(x, y) for y in (EYE_ROW, EYE_ROW + 1) for x in list(range(11, 16)) + list(range(20, 26))]
WAIST = 46  # rows above the belt rise on the breath


def poses(im):
    """rest, breath (head and chest up 1px, the waist row stretched), blink (eyes shut to a line)."""
    w, h = im.size
    rest = Image.new("RGBA", (w, h + 1), (0, 0, 0, 0))
    rest.alpha_composite(im, (0, 1))
    breath = Image.new("RGBA", (w, h + 1), (0, 0, 0, 0))
    breath.alpha_composite(im.crop((0, 0, w, WAIST + 1)), (0, 0))
    breath.alpha_composite(im.crop((0, WAIST, w, h)), (0, WAIST + 1))
    blink = rest.copy()
    for (x, y) in EYES:
        p = im.getpixel((x, y))
        if p[3] and p[:3] not in (SKIN, OUTLINE, H("#0b0e13"), H("#1b212a")):
            blink.putpixel((x, y + 1), (SKIN if y == EYE_ROW else LASH) + (255,))
    return {"rest": rest, "breath": breath, "blink": blink}


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def portrait(im):
    fig = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    slot = Image.new("RGBA", (184, 220), H(build.BG) + (255,))
    slot.alpha_composite(fig, ((184 - fig.width) // 2, 220 - fig.height - 12))
    out = ROOT / "assets" / "sprites" / "portrait.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    slot.save(out)
    print("wrote", out)


def divider(im):
    """She stands on the rule and idles: breathes, blinks. Pixelated scaling, transparent bg."""
    P = poses(im)
    W, s = 840, 1
    fw, fh = P["rest"].size
    rule_y = fh + 2
    Hh = rule_y + 4
    x = 28
    T = 6.0
    sched = [("rest", 0, 1.6), ("breath", 1.6, 3.0), ("rest", 3.0, 3.9), ("blink", 3.9, 4.05),
             ("rest", 4.05, 4.6), ("breath", 4.6, 6.0)]
    css, els = [], []
    for pose, img in P.items():
        kf = {0.0: "hidden", 100.0: "hidden"}
        for p, a, b in sched:
            if p == pose:
                kf[round(b / T * 100, 3)] = "hidden"
        for p, a, b in sched:
            if p == pose:
                kf[round(a / T * 100, 3)] = "visible"
        css.append(f"@keyframes g-{pose}{{" + "".join(f"{k}%{{visibility:{v}}}" for k, v in sorted(kf.items())) + "}")
        css.append(f".g-{pose}{{visibility:hidden;animation:g-{pose} {T}s steps(1,end) infinite;"
                   "image-rendering:optimizeSpeed;image-rendering:crisp-edges;image-rendering:pixelated}")
        els.append(f'<image class="g-{pose}" x="{x}" y="{rule_y - fh}" width="{fw * s}" height="{fh * s}" '
                   f'href="data:image/png;base64,{b64(img)}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" '
           f'role="img" aria-label="divider">\n<style>{"".join(css)}</style>\n'
           f'<rect x="0" y="{rule_y}" width="{W}" height="1" fill="{build.FAINT}"/>\n{"".join(els)}\n</svg>\n')
    out = ROOT / "assets" / "divider.svg"
    out.write_text(svg, encoding="utf-8")
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    im = styled()
    im.save(ROOT / "raw" / "girl1_styled.png")
    padded = Image.new("RGBA", (im.width + 1, im.height + 1), (0, 0, 0, 0))
    padded.alpha_composite(im, (0, 1))  # room to rise on the breath and turn on the glance
    padded.save(ROOT / "assets" / "sprites" / "avatar.png")
    portrait(im)
    divider(im)
