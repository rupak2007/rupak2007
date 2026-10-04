#!/usr/bin/env python3
"""Composes assets/hero.gif.

Scene: kotnaszynce's CC0 animated cityscape (raw/cityscape.gif), re-graded to night by
night.py and scaled 3x with nearest-neighbour so every source pixel stays a crisp block.
On top: the same window chrome as the SVG panels, the name in the 5x7 pixel font set on the
scene's own pixel grid, and a blinking cursor. Run: python3 scripts/hero.py
"""
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build  # noqa: E402  (tokens + pixel font)
from night import H, night_frames  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCALE, PAD_X, PAD_Y, BAR = 3, 36, 16, 27
NAME = "RUPAK RAJ"
TEXT_X, NAME_Y = 118, 20  # in scene pixels
CROP_H = 110


def font(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


MONO = font(["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"], 12)
CJK = font(["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"], 11)


def glyphs(d, s, x, y, scale, fill):
    """Draw text in build.py's 5x7 font onto a PIL ImageDraw at scene resolution."""
    for ch in s:
        g = build._G.get(ch, build._G["?"])
        for r in range(7):
            for c in range(5):
                if g[r * 5 + c] == "#":
                    d.rectangle([x + c * scale, y + r * scale, x + c * scale + scale - 1, y + r * scale + scale - 1], fill=fill)
        x += 6 * scale
    return x


def chrome(w, h):
    im = Image.new("RGB", (w, h), H(build.BG))
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, w - 2, 25], fill=H(build.BAR))
    d.line([1, 1, w - 2, 1], fill=H(build.BEVEL))
    d.line([1, 26, w - 2, 26], fill=H(build.EDGE))
    d.rectangle([10, 9, 17, 16], outline=H(build.MUTED))
    d.rectangle([12, 11, 15, 14], fill=H(build.ACCENT))
    x = d.textlength("rupak.exe — ", font=MONO)
    d.text((26, 6), "rupak.exe — ", font=MONO, fill=H(build.DIM))
    d.text((26 + x, 7), "接続中…", font=CJK, fill=H(build.DIM))
    bx = w - 8 - 3 * 18 + 4
    for i in range(3):
        X = bx + i * 18
        d.rectangle([X, 7, X + 13, 18], fill=H(build.BG), outline=H(build.EDGE))
        if i == 0:
            d.rectangle([X + 4, 14, X + 9, 15], fill=H(build.DIM))
        elif i == 1:
            d.rectangle([X + 4, 10, X + 9, 15], outline=H(build.DIM))
            d.rectangle([X + 4, 10, X + 9, 11], fill=H(build.DIM))
        else:
            for k in range(5):
                d.point([(X + 4 + k, 11 + k), (X + 8 - k, 11 + k)], fill=H(build.DIM))
    d.rectangle([0, 0, w - 1, h - 1], outline=H(build.EDGE))
    return im


def main():
    scenes, duration = night_frames(ROOT / "raw" / "cityscape.gif")
    scenes = [f.crop((0, 0, f.width, CROP_H)) for f in scenes]  # drop the empty bottom steps
    sw, sh = scenes[0].width * SCALE, scenes[0].height * SCALE
    w, h = sw + 2 * PAD_X, BAR + PAD_Y * 2 + sh
    base = chrome(w, h)
    ImageDraw.Draw(base).rectangle([PAD_X - 1, BAR + PAD_Y - 1, PAD_X + sw, BAR + PAD_Y + sh], outline=H(build.EDGE))
    shadow, ink, accent = H("#06080b"), H(build.TEXT), H(build.ACCENT)
    frames = []
    for i, scene in enumerate(scenes):
        s = scene.copy()
        d = ImageDraw.Draw(s)
        for dx, dy, col in ((1, 1, shadow), (0, 0, ink)):
            end = glyphs(d, NAME, TEXT_X + dx, NAME_Y + dy, 2, col)
        if (i // 3) % 2 == 0:  # cursor after the name: 600ms on, 600ms off
            d.rectangle([end + 1, NAME_Y + 10, end + 7, NAME_Y + 13], fill=accent)
        f = base.copy()
        f.paste(s.resize((sw, sh), Image.NEAREST), (PAD_X, BAR + PAD_Y))
        frames.append(f)

    # one shared palette so colours don't shimmer between frames
    strip = Image.new("RGB", (w, h * len(frames)))
    for k, f in enumerate(frames):
        strip.paste(f, (0, k * h))
    pal = strip.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pframes = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    out = ROOT / "assets" / "hero.gif"
    pframes[0].save(out, save_all=True, append_images=pframes[1:], duration=duration, loop=0,
                    optimize=True, disposal=1)
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB", f"{w}x{h}", len(frames), "frames")


if __name__ == "__main__":
    main()
