#!/usr/bin/env python3
"""The profile's character: a schoolgirl sprite the profile owner generated with ChatGPT
(first of the five in raw/girls.png), resampled from its upscaled render back to its pixel
grid (39x91), background removed, and toned into the profile's greys with the bow in the
accent colour. Writes:
  assets/sprites/avatar.png    native pixels for the info card (avatar.py makes its idle poses)
  assets/sprites/portrait.png  2x still, the info card's fallback
  assets/divider.svg           walking the divider rule, with a cat trotting behind her
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


LEGS = {"left": range(6, 19), "right": range(19, 31)}  # columns, below the skirt hem
HEM = 68                                                # first leg row
CAT_SHEET = ROOT / "raw" / "anime" / "Sprites" / "NPCs" / "Animals" / "sheet_cat.png"


def walk_frames(im):
    """A front-facing walk made by moving her own pixels: one foot lifts a pixel (its leg loses
    a row of sock, so the leg stays joined to the hem), then a passing frame with her whole body
    a pixel higher, then the other foot. Nothing new is drawn."""
    w, h = im.size

    def step(side):
        out = Image.new("RGBA", (w, h + 1), (0, 0, 0, 0))
        out.alpha_composite(im, (0, 1))
        src = out.copy()
        for x in LEGS[side]:
            for y in range(HEM + 2, h + 1):  # skip the sock's top row; everything below rises
                out.putpixel((x, y - 1), src.getpixel((x, y)))
            out.putpixel((x, h), (0, 0, 0, 0))
        return out

    up = Image.new("RGBA", (w, h + 1), (0, 0, 0, 0))
    up.alpha_composite(im, (0, 0))
    return [step("left"), up, step("right"), up]


def cat_walk():
    """getjared's CC0 cat walking right (row 2 of the sheet), toned to the profile's greys,
    soft shadow dropped."""
    sheet = Image.open(CAT_SHEET).convert("RGBA")
    tones = {"outline": OUTLINE, "body": H("#6e7681"), "light": H("#aab3be"), "shade": H("#434c59")}
    frames = []
    for c in range(4):
        cell = sheet.crop((c * 64, 128, c * 64 + 64, 192))
        out = Image.new("RGBA", cell.size, (0, 0, 0, 0))
        for y in range(64):
            for x in range(64):
                r, g, b, a = cell.getpixel((x, y))
                if a < 255:
                    continue
                L = lum((r, g, b))
                t = "outline" if L < 70 else ("shade" if L < 160 else ("light" if r > 225 else "body"))
                out.putpixel((x, y), tones[t] + (255,))
        frames.append(out)
    box = None
    for f in frames:
        bb = f.getchannel("A").getbbox()
        box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    return [f.crop(box) for f in frames]


def divider(im):
    """She walks the rule left to right with a cat trotting behind her, then a pause off-stage.
    Animated SVG (always plays on GitHub), pixelated scaling, transparent background."""
    girl, cat = walk_frames(im), cat_walk()
    W, step_s, speed = 840, 0.14, 3           # one frame every 140ms, 3px per frame
    gw, gh = girl[0].size
    cw, ch_ = cat[0].size
    rule_y = gh + 2
    Hh = rule_y + 4
    gap = 26                                  # cat trails her by this many px
    start, end = -(gw + gap + cw + 4), W + 4
    travel = (end - start) / speed * step_s
    T = round(travel + 3.0, 2)                # then three seconds off-stage
    done = travel / T * 100
    pix = "image-rendering:optimizeSpeed;image-rendering:crisp-edges;image-rendering:pixelated"
    cyc = len(girl) * step_s

    def frames(prefix, imgs, x, y):
        els = []
        for k, f in enumerate(imgs):
            els.append(f'<image class="{prefix}" style="animation-delay:{k * step_s - cyc:.2f}s" x="{x}" y="{y}" '
                       f'width="{f.width}" height="{f.height}" href="data:image/png;base64,{b64(f)}"/>')
        return "".join(els)

    css = (f".mv{{animation:mv {T}s linear infinite}}"
           f"@keyframes mv{{0%{{transform:translateX({start}px)}}{done:.3f}%{{transform:translateX({end}px)}}"
           f"100%{{transform:translateX({end}px)}}}}"
           f".g,.c{{visibility:hidden;{pix};animation:st {cyc:.2f}s steps(1,end) infinite}}"
           f"@keyframes st{{0%{{visibility:visible}}25%{{visibility:hidden}}100%{{visibility:hidden}}}}")
    body = (frames("g", girl, cw + gap, rule_y - gh) + frames("c", cat, 0, rule_y - ch_))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" '
           f'role="img" aria-label="divider">\n<style>{css}</style>\n'
           f'<rect x="0" y="{rule_y}" width="{W}" height="1" fill="{build.FAINT}"/>\n'
           f'<g class="mv">{body}</g>\n</svg>\n')
    out = ROOT / "assets" / "divider.svg"
    out.write_text(svg, encoding="utf-8")
    print("wrote", out, f"{out.stat().st_size / 1024:.0f} KB", f"loop {T}s")


if __name__ == "__main__":
    im = styled()
    im.save(ROOT / "raw" / "girl1_styled.png")
    padded = Image.new("RGBA", (im.width + 1, im.height + 1), (0, 0, 0, 0))
    padded.alpha_composite(im, (0, 1))  # room to rise on the breath and turn on the glance
    padded.save(ROOT / "assets" / "sprites" / "avatar.png")
    portrait(im)
    divider(im)
