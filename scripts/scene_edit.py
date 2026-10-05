"""Edits to kotnaszynce's CC0 cityscape for the hero, plus the two animated actors on the ledge.

* Editor clears all three figures and the dog off the ledge (every frame, before the night
  grade), rebuilding the railing, water and ledge behind them from the scene's own pixels.
* person_frames() lifts the remaining person out of the graded scene as its own sprite and
  makes three poses from those same pixels: rest, breathing in (shoulders up 1px), and a
  glance toward the cat (head 1px over).
* cat_frames() builds the sitting cat from shangri-la's CC0 "A Cat" idle sheet: its two
  sitting frames (tail down / tail flicked) and a blink, flipped to face the person and
  toned to match the scene's figures, eyes in the accent colour.
"""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAT_SHEET = ROOT / "raw" / "cat_idle.png"

DOG = (92, 71, 108, 90)      # x0, y0, x1, y1 inclusive, scene pixels
PERSON = (109, 66, 131, 90)
GIRL = (132, 68, 150, 90)
FIGURES = (84, 60, 160, 92)  # anything pink in here is a figure, never a fill source
GROUND = 89                  # the row the figures sit on
CAT_RIGHT = 108              # cat's right edge, where the dog sat


def _pink(p):
    return p[0] - p[1] > 40


def figure_mask(f0, box):
    x0, y0, x1, y1 = box
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if _pink(f0.getpixel((x, y)))}


def build_sources(f0, mask, extra_blocked=()):
    """Where each cleared pixel copies its background from, in the same frame, so the water
    keeps animating. Above the rail bar the pattern repeats every 2 rows; below it every 4
    columns, so copies stay on the dither grid. Borrow from the right, where the ledge is
    clear, except for the dog, whose left side is clear too."""
    blocked = {(x, y) for x in range(FIGURES[0], FIGURES[2]) for y in range(FIGURES[1], FIGURES[3])
               if _pink(f0.getpixel((x, y)))} | set(mask) | set(extra_blocked)
    src = {}
    for (x, y) in mask:
        if y <= 69:
            yy = y - 2
            while (x, yy) in blocked:
                yy -= 2
            src[(x, y)] = (x, yy)
            continue
        order = (-1, 1) if x <= DOG[2] else (1, -1)
        for k in range(1, 60):
            hit = next((x + s * 4 * k for s in order
                        if 0 <= x + s * 4 * k < f0.width and (x + s * 4 * k, y) not in blocked), None)
            if hit is not None:
                src[(x, y)] = (hit, y)
                break
    return src


class Editor:
    """Clears the dog, the person and the girl. The person comes back as an animated layer.

    The fill is a petal-free background: for each source pixel, its most common colour across
    all frames, so nothing that drifts past the source columns gets copied into the gap."""

    def __init__(self, gif):
        frames = []
        for k in range(gif.n_frames):
            gif.seek(k)
            frames.append(gif.convert("RGB"))
        gif.seek(0)
        f0 = frames[0]
        # the dog wags its tail, so clear every pixel any figure covers in any frame
        mask = set()
        for f in frames:
            mask |= figure_mask(f, DOG) | figure_mask(f, PERSON) | figure_mask(f, GIRL)
        src = build_sources(f0, mask)
        from collections import Counter
        self.bg = {xy: Counter(f.getpixel(sxy) for f in frames).most_common(1)[0][0] for xy, sxy in src.items()}

    def __call__(self, frame):
        f = frame.convert("RGB")
        px = f.load()
        for xy, c in self.bg.items():
            px[xy] = c
        return f


# ---- the person -------------------------------------------------------------
def person_frames(raw_f0, graded_f0):
    """Returns (origin_xy, {pose: RGBA}). Pixels come from the graded scene, untouched."""
    pts = figure_mask(raw_f0.convert("RGB"), PERSON)
    x0 = min(x for x, _ in pts)
    y0 = min(y for _, y in pts) - 1          # one spare row on top for the breath
    x1 = max(x for x, _ in pts)
    y1 = max(y for _, y in pts)
    w, h = x1 - x0 + 2, y1 - y0 + 1          # one spare column for the glance
    cols = {(x - x0 + 1, y - y0): graded_f0.getpixel((x, y)) for (x, y) in pts}

    def img(cells):
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        for (x, y), c in cells.items():
            im.putpixel((x, y), c + (255,))
        return im

    top = min(y for _, y in cols)
    chest = top + 13                          # head and shoulders rise, hips stay planted
    breath = {}
    for (x, y), c in cols.items():
        if y <= chest:
            breath[(x, y - 1)] = c
        if y >= chest:
            breath[(x, y)] = c
    head = top + 6                            # head and neck turn together
    glance = {((x - 1) if y <= head else x, y): c for (x, y), c in cols.items()}
    return (x0 - 1, y0), {"rest": img(cols), "breath": img(breath), "glance": img(glance)}


# ---- the cat ----------------------------------------------------------------
def cat_frames(body, edge, light, eye):
    """Sitting frames from the idle sheet: (0,0) tail down, (2,2) tail flicked."""
    sheet = Image.open(CAT_SHEET).convert("RGBA")

    def tone(cell, blink=False):
        out = Image.new("RGBA", cell.size, (0, 0, 0, 0))
        for y in range(cell.height):
            for x in range(cell.width):
                r, g, b, a = cell.getpixel((x, y))
                if not a:
                    continue
                s = r + g + b
                if s > 500:                       # the sheet's whites: eyes on the head row, else chest/paws
                    c = eye if (y == 8 and not blink) else (body if y == 8 else light)
                else:
                    c = body                          # one flat tone, like the person's silhouette
                out.putpixel((x, y), c + (255,))
        return out.transpose(Image.Transpose.FLIP_LEFT_RIGHT)  # face the person

    sit = sheet.crop((0, 0, 16, 16))
    flick = sheet.crop((32, 32, 48, 48))
    frames = {"sit": tone(sit), "blink": tone(sit, blink=True), "flick": tone(flick)}
    bb = frames["sit"].getchannel("A").getbbox()
    origin = (CAT_RIGHT - (bb[2] - 1), GROUND - (bb[3] - 1))
    return origin, frames
