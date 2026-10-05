#!/usr/bin/env python3
"""Builds the profile's SVG panels from profile.config.json.

Every panel shares one window chrome so the page reads as a single desktop.
Run locally:      python3 scripts/build.py
In GitHub Actions: GITHUB_TOKEN is set, so live stats are fetched first.
"""
import base64
import datetime as dt
import json
import os
import pathlib
import urllib.request
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CFG = json.loads((ROOT / "profile.config.json").read_text(encoding="utf-8"))
ICONS = json.loads((ROOT / "scripts" / "icons.json").read_text(encoding="utf-8"))["icons"]

# ---- design tokens -------------------------------------------------------
BG = "#0d1117"      # window body
BAR = "#161b22"     # title / status bars
EDGE = "#30363d"    # borders
BEVEL = "#21262d"   # inner highlight
TEXT = "#c9d1d9"
DIM = "#8b949e"
MUTED = "#6e7681"
FAINT = "#484f58"
ACCENT = "#7ee0ec"  # the only colour on the page: used like light, sparingly
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
CH = 7.8            # approx. advance of a 13px monospace glyph

# ---- 5x7 pixel font (title lettering) ------------------------------------
_FONT = """
A .###. #...# #...# ##### #...# #...# #...#
B ####. #...# #...# ####. #...# #...# ####.
C .###. #...# #.... #.... #.... #...# .###.
D ####. #...# #...# #...# #...# #...# ####.
E ##### #.... #.... ####. #.... #.... #####
F ##### #.... #.... ####. #.... #.... #....
G .###. #...# #.... #.### #...# #...# .####
H #...# #...# #...# ##### #...# #...# #...#
I .###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.
J ..### ...#. ...#. ...#. ...#. #..#. .##..
K #...# #..#. #.#.. ##... #.#.. #..#. #...#
L #.... #.... #.... #.... #.... #.... #####
M #...# ##.## #.#.# #.#.# #...# #...# #...#
N #...# #...# ##..# #.#.# #..## #...# #...#
O .###. #...# #...# #...# #...# #...# .###.
P ####. #...# #...# ####. #.... #.... #....
Q .###. #...# #...# #...# #.#.# #..#. .##.#
R ####. #...# #...# ####. #.#.. #..#. #...#
S .#### #.... #.... .###. ....# ....# ####.
T ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# #...# #...# .###.
V #...# #...# #...# #...# #...# .#.#. ..#..
W #...# #...# #...# #.#.# #.#.# #.#.# .#.#.
X #...# #...# .#.#. ..#.. .#.#. #...# #...#
Y #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
Z ##### ....# ...#. ..#.. .#... #.... #####
0 .###. #...# #..## #.#.# ##..# #...# .###.
1 ..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.
2 .###. #...# ....# ...#. ..#.. .#... #####
3 ####. ....# ....# .###. ....# ....# ####.
4 ...#. ..##. .#.#. #..#. ##### ...#. ...#.
5 ##### #.... ####. ....# ....# #...# .###.
6 .###. #.... #.... ####. #...# #...# .###.
7 ##### ....# ...#. ..#.. .#... .#... .#...
8 .###. #...# #...# .###. #...# #...# .###.
9 .###. #...# #...# .#### ....# ....# .###.
. ..... ..... ..... ..... ..... ..... ..#..
- ..... ..... ..... .###. ..... ..... .....
_ ..... ..... ..... ..... ..... ..... #####
> .#... ..#.. ...#. ....# ...#. ..#.. .#...
! ..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..
? .###. #...# ....# ...#. ..#.. ..... ..#..
/ ....# ...#. ...#. ..#.. .#... .#... #....
: ..... ..#.. ..... ..... ..... ..#.. .....
"""
_G = {ln[0]: "".join(ln.split()[1:]) for ln in _FONT.strip().splitlines()}
_G[" "] = "." * 35
assert all(len(v) == 35 for v in _G.values())


def pixel_text(s, x, y, scale=2, fill=TEXT, gap=1):
    """Return an SVG <path> drawing `s` in the 5x7 font, top-left at (x, y)."""
    d = []
    cx = x
    for ch in s.upper():
        g = _G.get(ch, _G["?"])
        for r in range(7):
            for c in range(5):
                if g[r * 5 + c] == "#":
                    d.append(f"M{cx + c * scale} {y + r * scale}h{scale}v{scale}h-{scale}z")
        cx += (5 + gap) * scale
    return f'<path fill="{fill}" d="{"".join(d)}"/>'


def pixel_width(s, scale=2, gap=1):
    return len(s) * (5 + gap) * scale - gap * scale


# ---- window chrome --------------------------------------------------------
def window(w, h, title, body, status=None, label=""):
    """A square-cornered Y2K window, dark. `body` is drawn in local coords."""
    btn = []
    bx = w - 8 - 3 * 18 + 4
    for i, kind in enumerate(("min", "max", "close")):
        x = bx + i * 18
        btn.append(f'<rect x="{x + .5}" y="7.5" width="13" height="11" fill="{BG}" stroke="{EDGE}"/>')
        if kind == "min":
            btn.append(f'<rect x="{x + 4}" y="14" width="6" height="2" fill="{DIM}"/>')
        elif kind == "max":
            btn.append(f'<rect x="{x + 4.5}" y="10.5" width="5" height="5" fill="none" stroke="{DIM}"/>'
                       f'<rect x="{x + 4}" y="10" width="6" height="2" fill="{DIM}"/>')
        else:
            for k in range(5):
                btn.append(f'<rect x="{x + 4 + k}" y="{11 + k}" width="1" height="1" fill="{DIM}"/>'
                           f'<rect x="{x + 8 - k}" y="{11 + k}" width="1" height="1" fill="{DIM}"/>')
    icon = (f'<rect x="10" y="9" width="8" height="8" fill="none" stroke="{MUTED}"/>'
            f'<rect x="12" y="11" width="4" height="4" fill="{ACCENT}" opacity=".85"/>')
    sb = ""
    body_h = h - 26
    if status is not None:
        body_h -= 22
        sb = (f'<rect x="1" y="{h - 23}" width="{w - 2}" height="22" fill="{BAR}"/>'
              f'<rect x="1" y="{h - 23}" width="{w - 2}" height="1" fill="{EDGE}"/>'
              f'<text x="12" y="{h - 8}" font-size="11" fill="{MUTED}">{status}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label or title)}" font-family="{MONO}" shape-rendering="crispEdges">
<rect width="{w}" height="{h}" fill="{BG}"/>
<rect x="1" y="1" width="{w - 2}" height="25" fill="{BAR}"/>
<rect x="1" y="26" width="{w - 2}" height="1" fill="{EDGE}"/>
<rect x="1" y="1" width="{w - 2}" height="1" fill="{BEVEL}"/>
{icon}
<text x="26" y="17.5" font-size="12" fill="{DIM}" letter-spacing=".3">{escape(title)}</text>
{"".join(btn)}
<g transform="translate(0 27)">{body}</g>
{sb}
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" fill="none" stroke="{EDGE}"/>
</svg>
'''


def tspan(s, fill, **kw):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<tspan fill="{fill}"{extra}>{escape(s)}</tspan>'


def kv_line(x, y, key, value, width=16, vfill=TEXT):
    dots = " " + "." * max(2, width - len(key) - 1) + " "
    return (f'<text x="{x}" y="{y}" font-size="13" xml:space="preserve">'
            f'{tspan(key, DIM)}{tspan(dots, FAINT)}{tspan(value, vfill)}</text>')


def rule(x, y, label, x_end=816, fill=DIM, bold=False, lead=True):
    """A labelled divider. Lines are drawn, not typed, so no font needs box-drawing glyphs."""
    lx = x + (2 * CH if lead else 0)
    weight = ' font-weight="bold"' if bold else ""
    out = f'<text x="{lx}" y="{y}" font-size="13" fill="{fill}"{weight}>{escape(label)}</text>'
    if lead:
        out += f'<rect x="{x}" y="{y - 5}" width="{CH * 1.2:.0f}" height="1" fill="{FAINT}"/>'
    tx = lx + len(label) * CH + CH
    return out + f'<rect x="{tx:.0f}" y="{y - 5}" width="{x_end - tx:.0f}" height="1" fill="{FAINT}"/>'


def embed_png(path, x, y, w, h):
    p = ASSETS / path
    if not p.exists():
        return None
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f'<image x="{x}" y="{y}" width="{w}" height="{h}" style="image-rendering:pixelated" '
            f'href="data:image/png;base64,{b64}"/>')


def png_size(path):
    """Width and height from a PNG header (the Action runs without Pillow)."""
    import struct
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


AVATAR_PIXEL = (1.09, 1.0)  # the portrait was drawn on slightly wide pixels; keep its proportions


def avatar_portrait(x, y, w, h):
    """Rupak's own portrait (assets/sprites/avatar.png, stored at its native pixel size), scaled
    up by the browser with hard pixel edges, standing on faint CRT scanlines."""
    path = ASSETS / "sprites" / "avatar.png"
    if not path.exists():
        return None
    nw, nh = png_size(path)
    scale = (h - 14) / nh
    aw, ah = nw * scale * AVATAR_PIXEL[0], nh * scale * AVATAR_PIXEL[1]
    ax, ay = x + (w - aw) / 2, y + h - ah - 6
    lines = "".join(f'<rect x="{x}" y="{y + k}" width="{w}" height="4" fill="#10151c"/>' for k in range(0, h, 8))
    b64 = base64.b64encode(path.read_bytes()).decode()
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG}"/>{lines}'
            f'<image x="{ax:.1f}" y="{ay:.1f}" width="{aw:.1f}" height="{ah:.1f}" preserveAspectRatio="none" '
            f'style="image-rendering:optimizeSpeed;image-rendering:crisp-edges;image-rendering:pixelated" '
            f'href="data:image/png;base64,{b64}"/>')


# ---- live stats -----------------------------------------------------------
def fetch_stats():
    cache = ASSETS / "stats.json"
    stats = dict(CFG["stats_fallback"])
    if cache.exists():  # last good numbers, so a failed fetch never blanks the card
        stats.update(json.loads(cache.read_text()))
    token, user = os.environ.get("GITHUB_TOKEN"), CFG["github_user"]
    if not token or user == "YOUR_USERNAME":
        return stats
    q = """query($u:String!){user(login:$u){createdAt followers{totalCount}
      repositories(first:100,ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC){totalCount nodes{stargazerCount}}
      contributionsCollection{totalCommitContributions restrictedContributionsCount}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": q, "variables": {"u": user}}).encode(),
                                 headers={"Authorization": f"bearer {token}", "User-Agent": "profile-build"})
    try:
        u = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]
    except Exception as e:  # keep the last good card rather than failing the build
        print("stats fetch failed:", e)
        return stats
    created = dt.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    days = (dt.datetime.now(dt.timezone.utc) - created).days
    cc = u["contributionsCollection"]
    stats.update(
        repos=str(u["repositories"]["totalCount"]),
        stars=str(sum(n["stargazerCount"] for n in u["repositories"]["nodes"])),
        commits=str(cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        followers=str(u["followers"]["totalCount"]),
        uptime=f"{days // 365}y {(days % 365) // 30}m",
    )
    cache.write_text(json.dumps(stats, indent=1))
    return stats


def fetch_repos():
    """Public, owned repos, newest push first. Cached in assets/repos.json like the stats."""
    cache = ASSETS / "repos.json"
    repos = json.loads(cache.read_text()) if cache.exists() else []
    token, user = os.environ.get("GITHUB_TOKEN"), CFG["github_user"]
    if not token or user == "YOUR_USERNAME":
        return repos
    q = """query($u:String!){user(login:$u){repositories(first:100,ownerAffiliations:OWNER,privacy:PUBLIC,
      orderBy:{field:PUSHED_AT,direction:DESC}){nodes{name description url isFork isArchived pushedAt
      primaryLanguage{name}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": q, "variables": {"u": user}}).encode(),
                                 headers={"Authorization": f"bearer {token}", "User-Agent": "profile-build"})
    try:
        nodes = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]["repositories"]["nodes"]
    except Exception as e:  # keep the last good list rather than emptying the page
        print("repo fetch failed:", e)
        return repos
    repos = [{"name": n["name"], "description": n["description"] or "", "url": n["url"],
              "language": (n["primaryLanguage"] or {}).get("name", ""), "pushed_at": n["pushedAt"],
              "fork": n["isFork"], "archived": n["isArchived"]} for n in nodes]
    cache.write_text(json.dumps(repos, indent=1))
    return repos


def resolve_projects(repos):
    """Flagship cards keep their hand-written text but pick up the live repo link and language.
    Every other public repo is listed in projects.sh automatically, unless it is excluded."""
    user = CFG["github_user"].lower()
    skip = {n.lower() for n in CFG.get("exclude", [])} | {user}
    live = {r["name"].lower(): r for r in repos if not r.get("fork") and not r.get("archived")}
    cards = []
    for p in CFG["projects"]:
        p, r = dict(p), live.get(p["id"].lower())
        if r:
            p.update(repo=r["url"], status="public", lang=(r.get("language") or p["lang"]).lower())
        cards.append(p)
    flagship = {p["id"].lower() for p in CFG["projects"]}
    more = [r for k, r in live.items() if k not in flagship and k not in skip]
    more.sort(key=lambda r: r.get("pushed_at", ""), reverse=True)
    fallback = {k.lower(): v for k, v in CFG.get("descriptions", {}).items()}
    for r in more:  # the repo's own GitHub description; config text only if it has none
        r["blurb"] = r.get("description") or fallback.get(r["name"].lower(), "")
    return cards, more


# ---- panels ---------------------------------------------------------------
def info_card(stats):
    w = 840
    portrait = avatar_portrait(24, 22, 184, 220) or embed_png("sprites/portrait.png", 24, 22, 184, 220)
    x = 236 if portrait else 24
    portrait = portrait or ""
    lines = [rule(x, 38, CFG["handle_line"], fill=TEXT, bold=True, lead=False)]
    y = 62
    for k, v in CFG["about"]:
        lines.append(kv_line(x, y, k, v, vfill=ACCENT if k == "status" else TEXT))
        y += 20
    y += 6
    lines.append(rule(x, y, "github")); y += 22
    x2 = x + 30 * CH
    pairs = [("repos", stats["repos"], "stars", stats["stars"]),
             ("commits/yr", stats["commits"], "followers", stats["followers"])]
    for a, av, b, bv in pairs:
        lines.append(kv_line(x, y, a, av))
        lines.append(kv_line(x2, y, b, bv, width=12))
        y += 20
    lines.append(kv_line(x, y, "uptime", stats["uptime"])); y += 26
    lines.append(rule(x, y, "contact")); y += 22
    parts = []
    contact = [(k, v) for k, v in CFG["contact"] if "YOUR_" not in v]  # unset placeholders are skipped
    for k, v in contact:
        lines.append(kv_line(x, y, k, v))
        y += 20
    body = portrait + "".join(lines)
    h = max(27 + 22 + 220 + 22, 27 + y + 4)
    return window(w, h, "about.txt — rupak", body, label="Rupak Raj: AI/ML engineer. Profile and GitHub stats.")


def project_card(p):
    w, h = 412, 236
    icon = embed_png(f"icons/{p['id']}.png", 20, 20, 48, 48) or (
        f'<rect x="20.5" y="20.5" width="47" height="47" fill="none" stroke="{EDGE}" stroke-dasharray="2 3"/>')
    body = [icon, pixel_text(p["name"], 84, 22, scale=3, fill=TEXT),
            f'<text x="84" y="64" font-size="12" fill="{DIM}">{escape(p["subtitle"])}</text>']
    y = 102
    for ln in p["lines"]:
        body.append(f'<text x="20" y="{y}" font-size="13" fill="{TEXT}">{escape(ln)}</text>')
        y += 19
    tx = 20
    for t in p["tags"]:
        tw = len(t) * 6.6 + 14
        body.append(f'<rect x="{tx + .5}" y="146.5" width="{tw:.0f}" height="18" fill="{BAR}" stroke="{EDGE}"/>'
                    f'<text x="{tx + 7}" y="159" font-size="11" fill="{DIM}">{escape(t)}</text>')
        tx += tw + 6
    dot = f'<tspan fill="{ACCENT}">●</tspan>'
    status = f'{dot} {escape(p["status"])}  ·  {escape(p["lang"])}'
    return window(w, h, p["title"], "".join(body), status=status,
                  label=f'{p["name"].title()}: {p["subtitle"]}')


def projects_ls(more):
    w = 840
    col = max([12] + [len(r["name"]) + 3 for r in more])
    rows = [f'<text x="20" y="34" font-size="13" xml:space="preserve">{tspan("~/projects", ACCENT)}{tspan(" $ ", MUTED)}{tspan("ls -l --more", TEXT)}</text>']
    y, right = 58, 0
    if not more:
        rows.append(f'<text x="20" y="{y}" font-size="13" fill="{FAINT}">total 0</text>')
        y += 22
    for r in more:
        name, blurb = r["name"] + "/", r["blurb"]
        room = int((w - 24 - 20) / CH) - 9 - col
        if len(blurb) > room:
            blurb = blurb[:room - 1].rstrip() + "…"
        rows.append(f'<text x="20" y="{y}" font-size="13" xml:space="preserve">{tspan("drwxr-x  ", FAINT)}'
                    f'{tspan(name.ljust(col), TEXT)}{tspan(blurb, DIM)}</text>')
        right = max(right, 20 + (9 + col + len(blurb)) * CH)
        y += 22
    prompt_y = y + 4
    rows.append(f'<text x="20" y="{prompt_y}" font-size="13" xml:space="preserve">{tspan("~/projects", ACCENT)}{tspan(" $ ", MUTED)}</text>'
                f'<rect x="{20 + 13 * CH}" y="{prompt_y - 12}" width="8" height="14" fill="{TEXT}"/>')
    # a deadpan dialog left open on the desktop
    dx, dw, dh = 594, 222, 112
    dy = 26 if right < dx - 16 else prompt_y - 14  # beside the rows if they leave room, else below
    h = max(196, 27 + dy + dh + 31, 27 + prompt_y + 30)
    dialog = (f'<rect x="{dx + 4}" y="{dy + 4}" width="{dw}" height="{dh}" fill="#010409"/>'
              f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="{BAR}"/>'
              f'<rect x="{dx}" y="{dy}" width="{dw}" height="20" fill="{BEVEL}"/>'
              f'<text x="{dx + 8}" y="{dy + 14}" font-size="11" fill="{DIM}">model.fit()</text>'
              f'<rect x="{dx + dw - 18.5}" y="{dy + 4.5}" width="13" height="11" fill="{BG}" stroke="{EDGE}"/>'
              + "".join(f'<rect x="{dx + dw - 14 + k}" y="{dy + 8 + k}" width="1" height="1" fill="{DIM}"/>'
                        f'<rect x="{dx + dw - 10 - k}" y="{dy + 8 + k}" width="1" height="1" fill="{DIM}"/>' for k in range(5))
              + pixel_text("!", dx + 14, dy + 34, scale=3, fill=ACCENT)
              + f'<text x="{dx + 40}" y="{dy + 42}" font-size="12" fill="{TEXT}">rupak.exe is not</text>'
              f'<text x="{dx + 40}" y="{dy + 58}" font-size="12" fill="{TEXT}">responding.</text>'
              f'<text x="{dx + 40}" y="{dy + 74}" font-size="11" fill="{MUTED}">(it\'s training)</text>'
              f'<rect x="{dx + 94.5}" y="{dy + 84.5}" width="54" height="18" fill="{BG}" stroke="{EDGE}"/>'
              f'<text x="{dx + 108}" y="{dy + 97}" font-size="11" fill="{DIM}">wait</text>'
              f'<rect x="{dx + 154.5}" y="{dy + 84.5}" width="56" height="18" fill="{BG}" stroke="{FAINT}"/>'
              f'<text x="{dx + 164}" y="{dy + 97}" font-size="11" fill="{DIM}">wait.</text>'
              f'<rect x="{dx + .5}" y="{dy + .5}" width="{dw - 1}" height="{dh - 1}" fill="none" stroke="{EDGE}"/>')
    return window(w, h, "projects.sh", "".join(rows) + dialog,
                  label="More projects: " + (", ".join(r["name"] for r in more) or "none yet"))


SHORT = {"githubactions": "actions", "scikitlearn": "sklearn"}


def stack_panel():
    w = 840
    row_h, size, step = 64, 26, 74
    groups = CFG["stack"]
    h = 27 + 18 + row_h * len(groups) + 6
    body = []
    y = 18
    for label, slugs in groups:
        body.append(f'<text x="20" y="{y + 18}" font-size="13" xml:space="preserve">'
                    f'{tspan(label, DIM)}{tspan(" " + "." * (10 - len(label)), FAINT)}</text>')
        x = 132
        for s in slugs:
            ic = ICONS[s]
            sc = size / 24
            body.append(f'<g transform="translate({x + (step - size) / 2 - 10} {y}) scale({sc})">'
                        f'<path fill="{DIM}" d="{ic["path"]}" shape-rendering="geometricPrecision"/></g>'
                        f'<text x="{x + step / 2 - 10}" y="{y + size + 16}" font-size="10" fill="{MUTED}" text-anchor="middle">{escape(SHORT.get(s, ic["title"].lower()))}</text>')
            x += step
        y += row_h
    return window(w, h, "toolbox", "".join(body), label="Tech stack: " +
                  ", ".join(ICONS[s]["title"] for _, sl in groups for s in sl))


def readme(cards_data, more):
    user = CFG["github_user"]
    raw = f"https://raw.githubusercontent.com/{user}/{user}/output"
    def card(p):
        img = (f'<img src="assets/card-{p["id"]}.svg" width="49%" '
               f'alt="{escape(p["name"].title())}: {escape(p["subtitle"])}" />')
        return f'  <a href="{p["repo"]}">{img}</a>' if p.get("repo") else f"  {img}"
    cards = "\n".join(card(p) for p in cards_data)
    hero = ('<img src="assets/hero.svg" width="100%" alt="A night riverside in pixel art: '
            'a blossoming tree, a person and a cat on a ledge, a train crossing the bridge." />'
            if (ASSETS / "hero.svg").exists() else "<!-- hero.svg goes here -->")
    links = CFG.get("contact_links", {})
    contact_row = ""
    if links:
        contact_row = ('<p align="center"><sub>' + " · ".join(
            f'<a href="{u}">{k}</a>' for k, u in links.items()) + "</sub></p>\n\n")
    more_links = ""
    if more:
        more_links = ('<p align="center"><sub>' + " · ".join(
            f'<a href="{r["url"]}">{escape(r["name"])}</a>' for r in more) + "</sub></p>\n")
    divider = ('<p align="center"><img src="assets/divider.svg" width="100%" alt="" /></p>\n'
               if (ASSETS / "divider.svg").exists() else "")
    return f'''<!-- generated by scripts/build.py from profile.config.json — edit those, not this file -->
<p align="center">
  {hero}
</p>

<p align="center">
  <img src="assets/info-card.svg" width="100%" alt="about.txt: AI/ML engineer (student), B.Tech CSE (AI/ML) at SRM IST, class of 28. Into machine learning, AI systems, backend and applied AI. Open to ML internships, summer 27. Live GitHub stats and contact details." />
</p>

{contact_row}{divider}<p align="center">
{cards}
</p>

<p align="center">
  <img src="assets/projects-ls.svg" width="100%" alt="More projects: {escape(", ".join(r["name"] for r in more) or "none yet")}" />
</p>
{more_links}
<p align="center">
  <img src="assets/stack.svg" width="100%" alt="Toolbox: {escape(", ".join(ICONS[s]["title"] for _, sl in CFG["stack"] for s in sl))}" />
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="{raw}/snake-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="{raw}/snake-light.svg" />
    <img src="{raw}/snake-dark.svg" width="100%" alt="contribution graph being eaten by a snake" />
  </picture>
</p>

<p align="center"><sub>pixel art by getjared, kotnaszynce and Kenney, all CC0 · logos via Simple Icons · <a href="CREDITS.md">credits</a></sub></p>
'''


def unlink_images(md):
    """GitHub wraps every bare <img> in a link to the file. Images inside <picture> are left
    alone, so wrapping ours keeps a click on the profile from jumping into the repo."""
    import re
    return re.sub(r'(<img src="assets/[^>]*?/>)', r"<picture>\1</picture>", md)


def main():
    ASSETS.mkdir(exist_ok=True)
    stats = fetch_stats()
    cards, more = resolve_projects(fetch_repos())
    out = {"info-card.svg": info_card(stats), "projects-ls.svg": projects_ls(more), "stack.svg": stack_panel()}
    for p in cards:
        out[f"card-{p['id']}.svg"] = project_card(p)
    for name, svg in out.items():
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print("wrote", name)
    (ROOT / "README.md").write_text(unlink_images(readme(cards, more)), encoding="utf-8")
    print("wrote README.md")


if __name__ == "__main__":
    main()
