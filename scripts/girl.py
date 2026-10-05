#!/usr/bin/env python3
"""The recurring character: a schoolgirl drawn pixel by pixel, after the reference picture Rupak
gave (long black hair with a low side ponytail, white shirt, bow, black pinafore and pleated
skirt, knee socks, white sneakers). Same scale, outline and greys as the boy she replaces; the
bow takes the page's one accent colour.

Each map is one character per pixel (see PAL); the outer 1px outline is added by render().
Writes:
  assets/sprites/portrait.png, portrait-breath.png, portrait-blink.png
                         front-facing idle poses for the info card (build.py loops them)
  assets/divider.svg     her 4-frame walk across the thin rule
Run: python3 scripts/girl.py
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

PAL = {
    "O": (2, 3, 6),                                    # outline, also the black of the uniform
    "1": (19, 23, 29), "u": (30, 36, 44),              # uniform shade, pleat / fold lines
    "2": (40, 47, 57), "3": (52, 60, 70), "4": (64, 72, 84), "5": (84, 93, 106),  # hair, dark to sheen
    "S": (205, 212, 219), "s": (158, 166, 176), "L": (222, 228, 234),            # skin, shade, eye light
    "W": (184, 192, 201), "w": (124, 132, 143),       # shirt and its shade
    "G": (112, 120, 132),                              # irises
    "R": H(build.ACCENT), "r": (58, 118, 130),         # bow
    "N": (205, 212, 219), "n": (131, 138, 149),        # sneakers
    "m": (145, 152, 162),                              # ground shadow (no outline around it)
}

FRONT = """
........2333332..........
......23344443332........
.....2334455544332.......
....233445555544332......
....234455O555O4432......
...2334555O5544O4332.....
...23445O5O44O4O4332.....
...23O44O4O4O4O3O3332....
...2O3O3O3O3O3O3O33322...
...2O3O3SO3SO3SO3O33222..
...23O3SSSOSSSSSSO3O3222.
...23OSOOOSSSSOOOSO3O3222
...2O3SG1LSSSSG1LS3O33222
...2O3SGGGSSSSGGGS3O33222
...2O3SSSSSSSSSSSS3O33222
...2O3SSSSSSSSSSSS3O32322
...2O3sSSSSSSSSSSs3O32322
...2O.3sSSSSSSSSs3.O3232
...2O..3ssSSSSss3..O32322
...2O....OsSSsO....O232O2
...2O...WOssssOW...O33322
...2O..WWWOsssOWWW.O43322
...WWO11WWRRrRRWW11O4332
..WWO111WRRRrRRRW111O3322
..WwO1111WWWrWWW1111O3322
..WwO11111OWwWO11111O332O
..WwO111111OWO111111O3322
..WwO111u1111111u111O332
..WwO111u1111111u111O232O
..WwO111111111111111O23
..wwOOOOOOOOOOOOOOOOOww
..SsO1u1u11u1u11u1u1OsS
..sSO1u1u11u1u11u1u1OSs
...O1u1u11u111u11u1u1O
...O1u1u11u111u11u1u1O
..O1u1u111u111u111u1u1O
..OOOOOOOOOOOOOOOOOOOOO
........Ss....sS........
........SS....SS........
........SS....SS........
........11....11........
........11....11........
........11....11........
........11....11........
........11....11........
.......NNn....nNN.......
......NNNnO..OnNNN......
......OOOOO..OOOOO......
....mmmmmmmmmmmmmmmm....
""".strip("\n").split("\n")

# facing right; the upper body is shared, the near arm and the legs change per frame
TOP = """
.........233332......
.......2334444332....
......233445544332...
.....23344555544332..
....2334455555444332.
....23344555554443O..
...2334455O55O44O3O..
...233445O4O44O4OSO..
...23344O3O3O3O3OSSO.
...2334O3O3O3OSSSSSO.
...2334O3O3OSSSOOSSO.
...23343O3SSSSG1LSO..
...2334O3SSSSSGGGSSO.
...2333O3sSSSSSSSSO..
...2333O3sSSSSSSSO...
...23333O3ssSSSSO....
...23333O.OOsSsO.....
...2333O3O.OssO......
...2333O33OWWsWW.....
...2333O3O11WRrO.....
..2332O3O111RRRO.....
..2332O3O1111rO......
..2332OO11111O.......
..232O11111111O......
..23O111111111O......
...2O111111111O......
...2O111111111O......
....O11111111O.......
....OOOOOOOOOOO......
...O1u1u1u1u1uO......
...O1u1u1u1u1u1O.....
..O1u1u1u1u1u1uO.....
..O1u1u1u1u1u1u1O....
..OOOOOOOOOOOOOOO....
""".strip("\n").split("\n")

# near arm (sleeve + hand) drawn over TOP: (row, col, pixels)
ARM_MID = [(22,6,"OWWO"),(23,6,"OWWwO"),(24,6,"OWWwO"),(25,6,"OWwwO"),(26,6,"OWwwO"),(27,6,"OwwO"),(28,7,"Ss")]
ARM_FWD = [(22,6,"OWWO"),(23,7,"OWWwO"),(24,7,"OWWwO"),(25,7,"OWwwO"),(26,8,"OWwwO"),(27,8,"OwwO"),(28,9,"Ss")]
ARM_BACK= [(22,6,"OWWO"),(23,5,"OWWwO"),(24,5,"OWWwO"),(25,5,"OWwwO"),(26,4,"OWwwO"),(27,4,"OwwO"),(28,4,"Ss")]

LEG_PASS = """
.......Ss.......
.......SS.......
.......SS.......
.......11.......
.......11.......
.......11.......
.......11.......
.......11.......
.......11.......
.......11.......
.......11.......
.......1NNN.....
.......NNNNn....
.......OOOOOO...
....mmmmmmmmmm..
""".strip("\n").split("\n")

LEG_STRIDE = """
......sSS.......
......sSSS......
.....sS..SS.....
.....11...11....
.....11...11....
....11.....11...
....11.....11...
....11.....11...
...11.......11..
...11.......11..
..nnN.......NNN.
.nnnn.......NNNn
.OOOO.......OOOOO
..mmmmmmmmmmmmmm.
""".strip("\n").split("\n")


def render(rows):
    """Pixel map -> RGBA image, 1px transparent margin, outlined on the outside."""
    w = max(len(r) for r in rows) + 2
    g = [["."] * w] + [list(("." + r).ljust(w, ".")) for r in rows] + [["."] * w]
    h = len(g)
    edge = [(y, x) for y in range(h) for x in range(w) if g[y][x] == "." and any(
        0 <= y + dy < h and 0 <= x + dx < w and g[y + dy][x + dx] not in ".m"
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)))]
    for y, x in edge:
        g[y][x] = "O"
    im = Image.new("RGBA", (w, h))
    for y in range(h):
        for x in range(w):
            if g[y][x] != ".":
                im.putpixel((x, y), PAL[g[y][x]] + (255,))
    return im


def walk_frame(arm, legs, bob=0):
    rows = [list(r.ljust(22, ".")) for r in TOP]
    for r, c, s in arm:
        rows[r][c:c + len(s)] = s
    rows = ["".join(r) for r in rows] + legs
    return ["." * 22] * bob + rows


def front_pose(kind):
    rows = list(FRONT)
    if kind == "breath":  # shoulders and head settle a pixel; skirt and feet stay put
        rows = ["."] + rows[:27] + rows[28:]
    if kind == "blink":   # lids come down to a line
        rows[11] = rows[11].replace("SOOOS", "SSSSS")
        rows[12] = rows[12].replace("G1L", "OOO")
        rows[13] = rows[13].replace("GGG", "SSS")
    return render(rows)


def portrait(im):
    """4x into the info card's 184x220 slot, on the same faint scanlines the boy had."""
    fig = im.resize((im.width * 4, im.height * 4), Image.NEAREST)
    slot = Image.new("RGBA", (184, 220), H(build.BG) + (255,))
    for y in range(0, 220, 8):
        for yy in range(y, min(y + 4, 220)):
            for x in range(184):
                slot.putpixel((x, yy), H("#10151c") + (255,))
    slot.alpha_composite(fig, ((184 - fig.width) // 2, 220 - fig.height - 4))
    return slot


def divider(frames):
    """An animated SVG (always runs on GitHub, unlike GIFs) of her walking the 1px rule,
    on a transparent background so it sits on light and dark GitHub alike."""
    W, Hh, rule_y, speed, step = 840, 64, 58, 3, 0.12  # 3px per 120ms frame, as the boy walked
    imgs = []
    for k, f in enumerate(frames):
        cell = Image.new("RGBA", (64, 64))
        cell.alpha_composite(f, ((64 - f.width) // 2, rule_y + 1 - f.height))
        buf = io.BytesIO()
        cell.save(buf, "PNG", optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        imgs.append(f'<image class="w" style="animation-delay:{k * step - 4 * step:.2f}s" width="64" height="64" '
                    f'href="data:image/png;base64,{b64}"/>')
    travel = (W + 40) / speed * step          # seconds to cross
    T = travel + 20 * step                    # plus a short pause off-stage
    done = travel / T * 100
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" role="img" aria-label="divider">
<style>
.mv{{animation:mv {T:.2f}s linear infinite}}
@keyframes mv{{0%{{transform:translate(-40px,0px)}}{done:.3f}%{{transform:translate({W}px,0px)}}100%{{transform:translate({W}px,0px)}}}}
.w{{visibility:hidden;image-rendering:pixelated;animation:wk {4 * step:.2f}s steps(1,end) infinite}}
@keyframes wk{{0%{{visibility:visible}}25%{{visibility:hidden}}100%{{visibility:hidden}}}}
</style>
<rect x="0" y="{rule_y}" width="{W}" height="1" fill="{build.FAINT}"/>
<g class="mv">{"".join(imgs)}</g>
</svg>
"""


def main():
    sprites = ROOT / "assets" / "sprites"
    sprites.mkdir(parents=True, exist_ok=True)
    for kind, name in (("idle", "portrait.png"), ("breath", "portrait-breath.png"), ("blink", "portrait-blink.png")):
        portrait(front_pose(kind)).save(sprites / name, optimize=True)
        print("wrote", name)
    walk = [walk_frame(ARM_MID, LEG_PASS), walk_frame(ARM_FWD, LEG_STRIDE, 1),
            walk_frame(ARM_MID, LEG_PASS), walk_frame(ARM_BACK, LEG_STRIDE, 1)]
    out = ROOT / "assets" / "divider.svg"
    out.write_text(divider([render(f) for f in walk]), encoding="utf-8")
    print("wrote", out.name, f"{out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
