#!/usr/bin/env python3
"""Builds the recurring character from getjared's CC0 anime-collection paperdoll layers
(walk base + black school uniform + hair), re-tones each layer into the profile's greys,
and writes:
  assets/divider.gif           the character walking across a thin rule
  assets/sprites/portrait.png  a front-facing still for the info card
Run: python3 scripts/sprite.py
"""
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402
from night import H  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "raw" / "anime" / "Sprites"
CELL = 64

# layer -> (dark, light) ramp; each source pixel keeps its relative brightness within the ramp
RAMPS = {
    "base": (H("#6e7681"), H("#d6dde4")),     # skin: the brightest thing on him
    "uniform": (H("#0b0e13"), H("#2d343e")),  # black gakuran
    "hair": (H("#1f262f"), H("#59626e")),     # dark hair
}
OUTLINE = H("#020306")


def lum(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]


def tone(layer, name):
    lo, hi = RAMPS[name]
    px = list(layer.get_flattened_data()) if hasattr(layer, "get_flattened_data") else list(layer.getdata())
    vals = [lum(p) for p in px if p[3] > 0]
    mn, mx = min(vals), max(vals)
    out = []
    for p in px:
        if p[3] == 0:
            out.append(p)
            continue
        if name == "base" and p[3] < 255:  # the drop shadow under his feet
            out.append((5, 7, 10, p[3]))
            continue
        L = lum(p)
        if L < 40:  # keep the artist's dark outlines as outlines
            out.append(OUTLINE + (p[3],))
            continue
        t = (L - mn) / max(1, mx - mn)
        if name == "uniform" and p[0] > 150 and p[1] > 120 and p[2] < 100:  # brass buttons
            out.append(H(build.ACCENT) + (255,))
            continue
        out.append(tuple(round(lo[i] + (hi[i] - lo[i]) * t) for i in range(3)) + (p[3],))
    im = Image.new("RGBA", layer.size)
    im.putdata(out)
    return im


def sheet():
    base = Image.open(SRC / "#OLD-BASE" / "Sheet_Walk.png").convert("RGBA")
    uni = Image.open(SRC / "Paperdoll" / "black_school_uniform.png").convert("RGBA")
    hair = Image.open(SRC / "Paperdoll" / "hair_red.png").convert("RGBA")
    out = tone(base, "base")
    for layer, name in ((uni, "uniform"), (hair, "hair")):
        t = tone(layer, name)
        out.alpha_composite(t)
    return out


def cell(sh, row, col):
    return sh.crop((col * CELL, row * CELL, (col + 1) * CELL, (row + 1) * CELL))


def main():
    sh = sheet()
    (ROOT / "assets" / "sprites").mkdir(parents=True, exist_ok=True)
    sh.save(ROOT / "raw" / "character_sheet.png")

    # portrait: front idle, 4x, trimmed and centred in the info card's 184x220 slot
    front = cell(sh, 0, 0)
    bb = front.getbbox()
    fig = front.crop(bb)
    fig = fig.resize((fig.width * 4, fig.height * 4), Image.NEAREST)
    slot = Image.new("RGBA", (184, 220), H(build.BG) + (255,))
    for y in range(0, 220, 4):  # faint scanlines behind him, CRT-ish
        for x in range(184):
            if (y // 4) % 2 == 0:
                slot.putpixel((x, y), H("#10151c") + (255,))
    slot.alpha_composite(fig, ((184 - fig.width) // 2, 220 - fig.height - 8))
    slot.save(ROOT / "assets" / "sprites" / "portrait.png")

    # divider: walks right along a 1px rule, then a short pause off-stage
    W, Hh, rule_y = 840, 64, 58
    walk_row = 2  # facing right
    frames_walk = [cell(sh, walk_row, c) for c in range(4)]
    bg = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))  # transparent: works on light and dark GitHub
    for x in range(W):
        bg.putpixel((x, rule_y), H(build.FAINT) + (255,))
    frames, speed = [], 3
    x = -40
    k = 0
    while x < W:
        f = bg.copy()
        f.alpha_composite(frames_walk[k % 4], (x, rule_y - 58))
        frames.append(f)
        x += speed
        k += 1
    frames += [bg] * 20
    # GIF has 1-bit alpha: snap partial alpha (the soft foot shadow) to solid, use index 0 as clear
    KEY = (255, 0, 255)
    def flat(f):
        rgb = Image.new("RGB", f.size, KEY)
        a = f.getchannel("A").point(lambda v: 255 if v > 60 else 0)
        rgb.paste(f.convert("RGB"), mask=a)
        return rgb
    flats = [flat(f) for f in frames]
    pal = flats[len(flats) // 3].quantize(colors=48, dither=Image.Dither.NONE)
    pf = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in flats]
    key_idx = pf[0].getpixel((0, 0))
    out = ROOT / "assets" / "divider.gif"
    pf[0].save(out, save_all=True, append_images=pf[1:], duration=120, loop=0, optimize=False,
               disposal=2, transparency=key_idx)
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB", len(frames), "frames")


ICONS = {"tracewright": (37, 11), "ciphraud": (33, 11)}  # Kenney 1-Bit Pack tiles (col, row)


def icons():
    sheet = Image.open(ROOT / "raw" / "kenney" / "Tilesheet" / "monochrome-transparent_packed.png").convert("RGBA")
    (ROOT / "assets" / "icons").mkdir(parents=True, exist_ok=True)
    for name, (c, r) in ICONS.items():
        tile = sheet.crop((c * 16, r * 16, c * 16 + 16, r * 16 + 16))
        ink = Image.new("RGBA", tile.size, H(build.TEXT) + (255,))
        ink.putalpha(tile.getchannel("A"))
        ink.resize((48, 48), Image.NEAREST).save(ROOT / "assets" / "icons" / f"{name}.png")
        print("wrote icon", name)


if __name__ == "__main__":
    main()
    icons()
