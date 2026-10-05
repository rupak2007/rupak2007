#!/usr/bin/env python3
"""Project icons (Kenney 1-Bit Pack). main() is the previous character (the boy), built from getjared's
CC0 anime-collection paperdoll layers, kept in case he comes back; girl.py replaced him.
It built the recurring character from getjared's CC0 anime-collection paperdoll layers
(walk base + black school uniform + hair), re-tones each layer into the profile's greys,
and writes:
  assets/divider.svg           the character walking across a thin rule
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

    # divider: an animated SVG (always runs on GitHub, unlike GIFs) of him walking a 1px rule.
    # Transparent background, so it sits on light and dark GitHub alike.
    import base64, io
    W, Hh, rule_y, speed, step = 840, 64, 58, 3, 0.12  # 3px per 120ms frame, as before
    walk = [cell(sh, 2, c) for c in range(4)]  # row 2 faces right
    imgs = []
    for k, f in enumerate(walk):
        buf = io.BytesIO()
        f.save(buf, "PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        imgs.append(f'<image class="w" style="animation-delay:{k * step - 4 * step:.2f}s" width="64" height="64" '
                    f'style-rendering="pixelated" href="data:image/png;base64,{b64}"/>')
    travel = (W + 40) / speed * step          # seconds to cross
    T = travel + 20 * step                    # plus a short pause off-stage
    done = travel / T * 100
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" role="img" aria-label="divider">
<style>
.mv{{animation:mv {T:.2f}s linear infinite}}
@keyframes mv{{0%{{transform:translate(-40px,{rule_y - 58}px)}}{done:.3f}%{{transform:translate({W}px,{rule_y - 58}px)}}100%{{transform:translate({W}px,{rule_y - 58}px)}}}}
.w{{visibility:hidden;image-rendering:pixelated;animation:wk {4 * step:.2f}s steps(1,end) infinite}}
@keyframes wk{{0%{{visibility:visible}}25%{{visibility:hidden}}100%{{visibility:hidden}}}}
</style>
<rect x="0" y="{rule_y}" width="{W}" height="1" fill="{build.FAINT}"/>
<g class="mv">{"".join(imgs)}</g>
</svg>
"""
    out = ROOT / "assets" / "divider.svg"
    out.write_text(svg, encoding="utf-8")
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB")


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
    icons()  # the character itself now comes from girl.py; main() is the previous one
