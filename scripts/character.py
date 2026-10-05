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

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402
from night import H  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
NATIVE = ROOT / "raw" / "girl1_native.png"

# luminance bands -> profile greys (lifted so dark hair still reads on the dark page)
BANDS = [(20, "#0a0d12"), (34, "#232a35"), (55, "#333c48"), (110, "#4d5765"),
         (150, "#7a8390"), (190, "#a9b2bd"), (256, "#dfe5ea")]


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def styled():
    src = Image.open(NATIVE).convert("RGB")
    w, h = src.size
    # background: flood fill the near-black from the border
    bg, stack = set(), [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in bg or not (0 <= x < w and 0 <= y < h) or lum(src.getpixel((x, y))) >= 16:
            continue
        bg.add((x, y))
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            if (x, y) in bg:
                continue
            r, g, b = src.getpixel((x, y))
            if r - g > 40:
                c = H("#4fa3ad")                          # the bow, in the dimmer accent
            else:
                L = lum((r, g, b))
                c = H(next(col for top, col in BANDS if L < top))
            out.putpixel((x, y), c + (255,))
    return out.crop(out.getchannel("A").getbbox())


SKIN, LASH = H("#dfe5ea"), H("#333c48")
EYES = [(x, y) for y in (23, 24) for x in list(range(10, 15)) + list(range(19, 25))]
WAIST = 45  # rows above the belt rise on the breath


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
        if p[3] and p[:3] not in (SKIN, H("#0a0d12"), H("#232a35")):
            blink.putpixel((x, y + 1), (SKIN if y == 23 else LASH) + (255,))
    return {"rest": rest, "breath": breath, "blink": blink}


def b64(im):
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def portrait(im):
    fig = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    slot = Image.new("RGBA", (184, 220), H(build.BG) + (255,))
    for y in range(0, 220, 4):  # faint scanlines behind her, CRT-ish
        if (y // 4) % 2 == 0:
            for x in range(184):
                slot.putpixel((x, y), H("#10151c") + (255,))
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
