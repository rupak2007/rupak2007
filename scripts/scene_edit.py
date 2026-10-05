"""Edits to kotnaszynce's CC0 cityscape, applied to every frame before the night grade:
removes the dog and the girl from the ledge, and seats a cat (from getjared's CC0
anime-collection cat sheet, as a flat silhouette to match the figures) where the dog was.
"""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAT_SHEET = ROOT / "raw" / "anime" / "Sprites" / "NPCs" / "Animals" / "sheet_cat.png"

DOG = (92, 71, 108, 90)    # x0, y0, x1, y1 inclusive, scene pixels
GIRL = (132, 68, 150, 90)
FIGURES = (84, 60, 160, 92)  # anything pink in here is a figure, never a fill source
GROUND = 89                  # the row the figures sit on
BODY, EDGE = (217, 159, 165), (213, 155, 161)  # the figures' own flat tones


def _pink(p):
    return p[0] - p[1] > 40


def build_mask(f0):
    m = set()
    for (x0, y0, x1, y1) in (DOG, GIRL):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if _pink(f0.getpixel((x, y))):
                    m.add((x, y))
    return m


def build_sources(f0, mask):
    """For each masked pixel, where to copy the background from (same frame, so the water and
    sparkle keep animating). Above the rail bar the pattern repeats every 2 rows; below it,
    every 4 columns, so copies stay on the dither grid."""
    blocked = {(x, y) for x in range(FIGURES[0], FIGURES[2]) for y in range(FIGURES[1], FIGURES[3])
               if _pink(f0.getpixel((x, y)))}
    src = {}
    for (x, y) in mask:
        if y <= 69:
            yy = y - 2
            while (x, yy) in blocked:
                yy -= 2
            src[(x, y)] = (x, yy)
            continue
        order = (-1, 1) if x <= DOG[2] else (1, -1)  # dog: borrow from the left; girl: from the right
        for k in range(1, 40):
            hit = None
            for sgn in order:
                xx = x + sgn * 4 * k
                if 0 <= xx < f0.width and (xx, y) not in blocked:
                    hit = (xx, y)
                    break
            if hit:
                src[(x, y)] = hit
                break
    return src


def cat_silhouette(scale=1.0):
    cell = Image.open(CAT_SHEET).convert("RGBA").crop((0, 128, 64, 192))  # row 2: side view, facing right
    cell = cell.crop(cell.getchannel("A").getbbox())
    sil = Image.new("RGBA", cell.size, (0, 0, 0, 0))
    for y in range(cell.height):
        for x in range(cell.width):
            r, g, b, a = cell.getpixel((x, y))
            if a == 255:  # drop the soft shadow (partial alpha)
                sil.putpixel((x, y), (EDGE if r + g + b < 200 else BODY) + (255,))
    sil = sil.crop(sil.getchannel("A").getbbox())
    if scale != 1.0:
        w, h = max(1, round(sil.width * scale)), max(1, round(sil.height * scale))
        a = sil.getchannel("A").resize((w, h), Image.NEAREST)  # hard edges keep the tail curl
        sil = Image.new("RGBA", (w, h), BODY + (0,))
        sil.putalpha(a)
    return sil


class Editor:
    def __init__(self, first_frame, cat_scale=0.8, cat_right=108):
        f0 = first_frame.convert("RGB")
        self.mask = build_mask(f0)
        self.src = build_sources(f0, self.mask)
        self.cat = cat_silhouette(cat_scale)
        self.cat_xy = (cat_right - self.cat.width + 1, GROUND - self.cat.height + 1)

    def __call__(self, frame):
        f = frame.convert("RGB")
        snap = f.copy()
        px, sp = f.load(), snap.load()
        for (x, y), (sx, sy) in self.src.items():
            px[x, y] = sp[sx, sy]
        rgba = f.convert("RGBA")
        rgba.alpha_composite(self.cat, self.cat_xy)
        return rgba.convert("RGB")
