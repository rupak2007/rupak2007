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
from scene_edit import Editor, cat_frames, person_frames  # noqa: E402

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


def png_b64_rgba(im):
    import base64, io
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def actor(cls, origin, poses, schedule, period, sx, sy):
    """One <image> per pose, each shown only in its slots of `schedule` [(pose, t0, t1)], on
    its own loop so the actors drift against the scene instead of repeating with it."""
    css, els = [], []
    for pose, im in poses.items():
        slots = [(a, b) for p, a, b in schedule if p == pose]
        if not slots:
            continue
        kf = {0.0: "hidden", 100.0: "hidden"}
        for a, b in slots:
            kf[round(b / period * 100, 3)] = "hidden"
        for a, b in slots:
            kf[round(a / period * 100, 3)] = "visible"
        name = f"{cls}-{pose}"
        css.append(f"@keyframes {name}{{" + "".join(f"{k}%{{visibility:{v}}}" for k, v in sorted(kf.items())) + "}")
        css.append(f".{name}{{visibility:hidden;animation:{name} {period}s steps(1,end) infinite;"
                   f"image-rendering:optimizeSpeed;image-rendering:crisp-edges;image-rendering:pixelated}}")
        ox, oy = origin
        els.append(f'<image class="{name}" x="{sx + ox * SCALE}" y="{sy + oy * SCALE}" '
                   f'width="{im.width * SCALE}" height="{im.height * SCALE}" '
                   f'href="data:image/png;base64,{png_b64_rgba(im)}"/>')
    return "".join(css), "".join(els)


# person: breathes twice and glances at the cat once per 7.2s
PERSON_LOOP = (7.2, [("rest", 0, 1.4), ("breath", 1.4, 2.8), ("rest", 2.8, 3.8), ("glance", 3.8, 5.0),
                     ("rest", 5.0, 5.8), ("breath", 5.8, 7.2)])
# cat: sits, blinks, flicks its tail twice per 6s
CAT_LOOP = (6.0, [("sit", 0, 2.2), ("blink", 2.2, 2.36), ("sit", 2.36, 3.6), ("flick", 3.6, 4.0),
                  ("sit", 4.0, 4.2), ("flick", 4.2, 4.6), ("sit", 4.6, 6.0)])


def main():
    """hero.svg: an animated SVG, not a GIF. GitHub puts a click-to-play control on GIFs for
    viewers whose animation setting is off; SVG animations always run."""
    src = ROOT / "raw" / "cityscape.gif"
    raw0 = Image.open(src)
    scenes, duration = night_frames(src, edit=Editor(raw0))  # ledge cleared of all figures
    scenes = [f.crop((0, 0, f.width, CROP_H)) for f in scenes]  # drop the empty bottom steps
    graded0 = night_frames(src)[0][0]                           # untouched, to lift the person from
    p_origin, p_poses = person_frames(raw0.convert("RGB"), graded0)
    from collections import Counter
    tones = Counter(c[:3] for c in p_poses["rest"].get_flattened_data() if c[3])
    body = tones.most_common(1)[0][0]
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    c_origin, c_poses = cat_frames(body, min(tones, key=lum), max(tones, key=lum), H(build.ACCENT))
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
    p_css, p_els = actor("pp", p_origin, p_poses, PERSON_LOOP[1], PERSON_LOOP[0], sx, PAD_Y)
    c_css, c_els = actor("ct", c_origin, c_poses, CAT_LOOP[1], CAT_LOOP[0], sx, PAD_Y)
    style = style.replace("</style>", p_css + c_css + "</style>")
    body = style + "".join(frames) + p_els + c_els + name + cur + frame
    svg = build.window(w, h, "rupak.exe — 接続中…", body,
                       label="RUPAK RAJ in pixel letters over a night riverside, a person and a cat on the ledge")
    out = ROOT / "assets" / "hero.svg"
    out.write_text(svg, encoding="utf-8")
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB", f"{w}x{h}", n, "frames")


if __name__ == "__main__":
    main()
