#!/usr/bin/env python3
"""Idle poses for the info-card portrait, made only by moving existing pixels of
assets/sprites/avatar.png (written by character.py). Nothing is drawn.

  avatar-breath.png  head, shoulders and torso (rows 0..WAIST) one pixel higher; the waist
                     row is held in place so the body stays joined
  avatar-glance.png  head (rows 0..NECK) one pixel to the right, toward the text

Run locally after changing avatar.png: python3 scripts/avatar.py
"""
import pathlib

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPRITES = ROOT / "assets" / "sprites"
WAIST, NECK = 46, 30  # rows in avatar.png as written by character.py (1px top padding)


def shifted(src, rows, dx=0, dy=0, keep_seam=None):
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    for y in range(src.height):
        for x in range(src.width):
            p = src.getpixel((x, y))
            if not p[3]:
                continue
            if y in rows:
                nx, ny = x + dx, y + dy
                if 0 <= nx < src.width and 0 <= ny < src.height:
                    out.putpixel((nx, ny), p)
                if keep_seam is not None and y == keep_seam:
                    out.putpixel((x, y), p)
            else:
                if out.getpixel((x, y))[3] == 0:
                    out.putpixel((x, y), p)
    return out


def main():
    src = Image.open(SPRITES / "avatar.png").convert("RGBA")
    breath = shifted(src, range(0, WAIST + 1), dy=-1, keep_seam=WAIST)
    glance = shifted(src, range(0, NECK + 1), dx=1)
    breath.save(SPRITES / "avatar-breath.png")
    glance.save(SPRITES / "avatar-glance.png")
    print("wrote avatar-breath.png, avatar-glance.png")


if __name__ == "__main__":
    main()
