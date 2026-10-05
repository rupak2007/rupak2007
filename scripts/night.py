"""Re-grade kotnaszynce's CC0 'animated cityscape' (pastel day) into the profile's night palette.

The source uses only ~32 colours, so the grade is a per-colour mapping by hue class and
brightness, plus a darker treatment for the foreground ledge. Pixels are never moved or
redrawn; only their colours change.
"""
from PIL import Image

def lum(c):
    r, g, b = c
    return 0.299 * r + 0.587 * g + 0.114 * b

def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))

H = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
SKY_LO, SKY_HI = H("#0b0f15"), H("#1c2531")
CITY_LO, CITY_HI = H("#161c25"), H("#3a4350")
PINK_LO, PINK_HI = H("#4a5260"), H("#a3adb9")
LEDGE_LO, LEDGE_HI = H("#090c11"), H("#232b36")
MOON = H("#c9d1d9")
REFLECT = H("#3d8a94")
WATER_LO, WATER_HI = H("#0e151c"), H("#1d3038")
GLOW = H("#7ee0ec")

def classify(c):
    r, g, b = c
    if r > 240 and g > 240 and b < 215:
        return "sun"
    if b > r + 15:
        return "cyan"
    if r > g + 25:
        return "pink"
    return "grey"

HORIZON = 73  # scene row where the water starts

def grade(c, y, foreground_y):
    k, L = classify(c), lum(c)
    if k == "sun":
        return MOON if y < HORIZON else REFLECT
    if k == "cyan" and HORIZON <= y < foreground_y:
        return mix(WATER_LO, WATER_HI, max(0, min(1, (L - 160) / 80)))
    if k == "cyan":
        t = (L - 160) / 95
        return mix(SKY_LO, SKY_HI, max(0, min(1, 1 - t)) * .6 + .2)
    if L > 225:  # pinkish-white sky
        return mix(SKY_LO, SKY_HI, (255 - L) / 30 * .5)
    if k == "pink":
        return mix(PINK_LO, PINK_HI, (L - 150) / 90)
    lo, hi = (LEDGE_LO, LEDGE_HI) if y >= foreground_y else (CITY_LO, CITY_HI)
    return mix(lo, hi, max(0, min(1, (L - 110) / 90)))

def night_frames(src, foreground_y=90, edit=None):
    im = Image.open(src)
    out, cache = [], {}
    for i in range(im.n_frames):
        im.seek(i)
        f = im.convert("RGB")
        if edit:
            f = edit(f)
        px = f.load()
        for y in range(f.height):
            region = 0 if y < HORIZON else (1 if y < foreground_y else 2)
            for x in range(f.width):
                key = (px[x, y], region)
                if key not in cache:
                    cache[key] = grade(px[x, y], y, foreground_y)
                px[x, y] = cache[key]
        out.append(f)
    return out, im.info.get("duration", 200)
