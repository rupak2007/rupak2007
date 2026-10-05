#!/usr/bin/env python3
"""Composes assets/hero.svg.

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
from scene_edit import Editor  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCALE, PAD_X, PAD_Y, BAR, W = 2, 16, 16, 27, 840
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


def png_b64(im):
    import base64, io
    buf = io.BytesIO()
    rgb = im.convert("RGB")  # full colour, no palette squeeze: the graded scene keeps every tone
    rgb.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def main():
    """hero.svg: an animated SVG, not a GIF. GitHub puts a click-to-play control on GIFs for
    viewers whose animation setting is off; SVG animations always run."""
    src = ROOT / "raw" / "cityscape.gif"
    scenes, duration = night_frames(src, edit=Editor(Image.open(src)))  # person + cat on the ledge
    scenes = [f.crop((0, 0, f.width, CROP_H)) for f in scenes]  # drop the empty bottom steps
    sw, sh = scenes[0].width * SCALE, scenes[0].height * SCALE
    w, h = W, BAR + PAD_Y * 2 + sh
    sx = w - PAD_X - sw  # scene sits on the right; the name gets its own column on the left
    n, T = len(scenes), len(scenes) * duration / 1000

    frames = []
    for i, f in enumerate(scenes):
        b64 = png_b64(f)  # native resolution; the browser scales it with nearest-neighbour below
        frames.append(f'<image class="f" style="animation-delay:{i * duration / 1000 - T:.3f}s" '
                      f'x="{sx}" y="{PAD_Y}" width="{sw}" height="{sh}" href="data:image/png;base64,{b64}"/>')
    slot = 100 / n
    # pixelated scaling happens at the viewer's real screen resolution, so blocks stay sharp at
    # any width and on high-DPI screens instead of being resampled from a fixed 3x bitmap
    style = (f"<style>.f{{visibility:hidden;animation:fr {T:.2f}s steps(1,end) infinite;"
             f"image-rendering:optimizeSpeed;image-rendering:crisp-edges;image-rendering:pixelated}}"
             f"@keyframes fr{{0%{{visibility:visible}}{slot:.4f}%{{visibility:hidden}}100%{{visibility:hidden}}}}"
             f".cur{{animation:bl 1.2s steps(1,end) infinite}}"
             f"@keyframes bl{{0%{{opacity:1}}50%{{opacity:0}}100%{{opacity:0}}}}</style>")

    # name, stacked, in the 5x7 font at 6px per font pixel (a multiple of the scene's 2px grid)
    px, lines = 6, NAME.split()
    block_h = len(lines) * 7 * px + (len(lines) - 1) * 3 * px
    nx, ny = PAD_X + 26, PAD_Y + (sh - block_h) // 2
    name = ""
    for k, word in enumerate(lines):
        y = ny + k * 10 * px
        name += build.pixel_text(word, nx + 3, y + 3, scale=px, fill="#06080b")
        name += build.pixel_text(word, nx, y, scale=px, fill=build.TEXT)
    last_end = nx + build.pixel_width(lines[-1], scale=px)
    cur = (f'<rect class="cur" x="{last_end + px}" y="{ny + (len(lines) - 1) * 10 * px + 5 * px}" '
           f'width="{4 * px}" height="{2 * px}" fill="{build.ACCENT}"/>')
    frame = (f'<rect x="{sx - .5}" y="{PAD_Y - .5}" width="{sw + 1}" height="{sh + 1}" '
             f'fill="none" stroke="{build.EDGE}"/>')
    body = style + "".join(frames) + name + cur + frame
    svg = build.window(w, h, "rupak.exe — 接続中…", body,
                       label="RUPAK RAJ in pixel letters over a night riverside")
    out = ROOT / "assets" / "hero.svg"
    out.write_text(svg, encoding="utf-8")
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB", f"{w}x{h}", n, "frames")


if __name__ == "__main__":
    main()
