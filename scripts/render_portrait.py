#!/usr/bin/env python3
"""
Render assets/portrait.svg: the left half of the `whoami` section.

An ASCII line-art portrait built from assets/photo.png (a cut-out with a
transparent background) that prints row by row like a terminal, followed by a
`whoami` prompt. Pencil-sketch (colour dodge) edges give the line art; the
alpha channel hides the background and adds the silhouette outline.

The photo is static, so the output only changes when the photo or the
"portrait" block of profile.json changes.
"""
import os

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from common import (ACCENT, BORDER, GREEN, MUTED, ROOT, TEXT, WHOAMI_BAR, WHOAMI_H, WHOAMI_W,
                    ASSETS, esc, frame, load_profile, write)

RAMP = " `.:-=+*cs#%@"
CELL_ASPECT = 1.875        # glyph cell height / width
SUPERSAMPLE = 4
ROW_SECONDS = 0.045        # reveal time per row
PAD = 20                   # left/right margin of the art
FOOT = 74                  # height of the whoami prompt strip


def sketch_darkness(img, alpha):
    """0..1 ink density per pixel: dodge-sketch edges + silhouette outline."""
    on_white = Image.alpha_composite(Image.new("RGBA", img.size, "white"), img)
    gray = np.asarray(ImageOps.autocontrast(on_white.convert("L"), cutoff=1), float)
    blurred = Image.fromarray((255 - gray).astype("uint8")).filter(
        ImageFilter.GaussianBlur(SUPERSAMPLE * 3))
    dodge = np.clip(gray * 255 / np.maximum(1, 255 - np.asarray(blurred, float)), 0, 255)
    edges = np.clip((1 - dodge / 255) * 2.6, 0, 1)

    mask = Image.fromarray((alpha * 255).astype("uint8"))
    outline = np.asarray(mask.filter(ImageFilter.FIND_EDGES)
                         .filter(ImageFilter.GaussianBlur(SUPERSAMPLE * 0.6)), float) / 255
    outline = np.clip(outline * 3, 0, 1)
    m = SUPERSAMPLE * 2    # the crop border is not part of the silhouette
    outline[:m, :] = outline[-m:, :] = outline[:, :m] = outline[:, -m:] = 0
    return np.maximum(edges * (alpha > 0.5), outline * 0.9)


def ascii_rows(photo, crop, cols, rows):
    left, top, width = crop
    height = round(width * rows * CELL_ASPECT / cols)
    img = Image.open(photo).convert("RGBA").crop((left, top, left + width, top + height))
    size = (cols * SUPERSAMPLE, rows * SUPERSAMPLE)
    img = img.resize(size, Image.LANCZOS)
    alpha = np.asarray(img.getchannel("A"), float) / 255
    dark = sketch_darkness(img, alpha)
    cells = Image.fromarray((dark * 255).astype("uint8")).resize((cols, rows), Image.BOX)
    top_level = len(RAMP) - 1
    return ["".join(RAMP[min(top_level, int(v / 255 * top_level + .5))] for v in row)
            for row in np.asarray(cells, float)]


def portrait(lines, top, cw, ch):
    """Each row is unveiled by a growing clip rect while a block cursor sweeps across it."""
    width = WHOAMI_W - 2 * PAD
    out = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        begin, y = i * ROW_SECONDS, top + i * ch
        out.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{y:.1f}" height="{ch + 1:.1f}" width="0">'
            f'<animate attributeName="width" to="{width}" begin="{begin:.3f}s" dur="{ROW_SECONDS}s" fill="freeze"/>'
            f'</rect></clipPath>'
            f'<text clip-path="url(#r{i})" xml:space="preserve" x="{PAD}" y="{y + ch * 0.78:.1f}" '
            f'font-size="{ch * 0.82:.1f}" textLength="{width}" lengthAdjust="spacing">{esc(line)}</text>'
            f'<rect y="{y + ch * 0.1:.1f}" width="{cw:.1f}" height="{ch * 0.8:.1f}" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + width}" begin="{begin:.3f}s" dur="{ROW_SECONDS}s" fill="freeze"/>'
            f'<set attributeName="opacity" to=".9" begin="{begin:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_SECONDS:.3f}s"/></rect>'
        )
    return f'<g fill="url(#accent)">{"".join(out)}</g>', len(lines) * ROW_SECONDS


def whoami(prof, done):
    """Bottom strip: `juan@github:~$ whoami` answered once the portrait finishes printing."""
    y, user = WHOAMI_H - FOOT / 2 + 9, prof["prompt_user"]
    return (
        f'<line x1="0" y1="{WHOAMI_H - FOOT}" x2="{WHOAMI_W}" y2="{WHOAMI_H - FOOT}" stroke="{BORDER}"/>'
        f'<text x="{PAD + 8}" y="{y:.0f}" font-size="26" xml:space="preserve">'
        f'<tspan fill="{GREEN}">{esc(user)}@github</tspan><tspan fill="{MUTED}">:</tspan>'
        f'<tspan fill="{ACCENT}">~</tspan><tspan fill="{MUTED}">$ </tspan><tspan fill="{TEXT}">whoami </tspan>'
        f'<tspan fill="{TEXT}" font-weight="700" opacity="0">{esc(prof["name"])} '
        f'<set attributeName="opacity" to="1" begin="{done:.2f}s"/></tspan>'
        f'<tspan fill="{ACCENT}">█<animate attributeName="opacity" values="1;1;0;0" '
        f'keyTimes="0;.5;.51;1" dur="1.1s" repeatCount="indefinite"/></tspan></text>'
    )


def main():
    prof = load_profile()
    cfg = prof["portrait"]
    cols = cfg["cols"]
    cw = (WHOAMI_W - 2 * PAD) / cols
    ch = cw * CELL_ASPECT
    top = WHOAMI_BAR + 12
    rows = int((WHOAMI_H - FOOT - 8 - top) / ch)
    lines = ascii_rows(os.path.join(ROOT, cfg["photo"]), cfg["crop"], cols, rows)
    art, done = portrait(lines, top, cw, ch)
    title = f'{prof["prompt_user"]}@github: ~$ ./portrait.sh'
    svg = frame(WHOAMI_W, WHOAMI_H, title, art + whoami(prof, done), bar=WHOAMI_BAR)
    write(os.path.join(ASSETS, "portrait.svg"), svg)


if __name__ == "__main__":
    main()
