#!/usr/bin/env python3
"""
Render assets/banner.svg (840x880): the left half of the `whoami` section.

Default: your name as an ANSI-Shadow block banner drawn with real <rect>/<path>
shapes (font-independent, so it looks identical everywhere) + a short shell session.

Optional: drop a square-ish photo at assets/photo.png and the top of the card
becomes an ASCII portrait of it instead of the name banner.
"""
import os

import pyfiglet

from common import (ACCENT, ASSETS, MUTED, TEXT, GREEN, esc, frame, load_profile, write)

W, H = 840, 880
SHADOW = "#3d4f66"

# box-drawing char -> list of segments in a unit cell (0..1 coords)
SEG = {
    "═": [((0, .5), (1, .5))], "║": [((.5, 0), (.5, 1))],
    "╗": [((0, .5), (.5, .5)), ((.5, .5), (.5, 1))],
    "╔": [((1, .5), (.5, .5)), ((.5, .5), (.5, 1))],
    "╝": [((0, .5), (.5, .5)), ((.5, .5), (.5, 0))],
    "╚": [((1, .5), (.5, .5)), ((.5, .5), (.5, 0))],
}


def figlet_rows(word):
    rows = pyfiglet.Figlet(font="ansi_shadow", width=400).renderText(word).rstrip("\n").split("\n")
    rows = [r.rstrip() for r in rows]
    while rows and not rows[-1].strip():
        rows.pop()
    return rows


def banner(lines, top):
    blocks = [figlet_rows(w) for w in lines]
    cols = max(len(r) for b in blocks for r in b)
    cw = min(15.0, (W - 80) / cols)
    ch = cw * 1.75
    out, y, row_i = [], top, 0
    for rows in blocks:
        bw = max(len(r) for r in rows) * cw
        x0 = (W - bw) / 2
        for r in rows:
            fills, paths = [], []
            for i, chr_ in enumerate(r):
                x = x0 + i * cw
                if chr_ == "█":
                    if i and r[i - 1] == "█":
                        continue  # merged into the run started earlier
                    run = len(r[i:]) - len(r[i:].lstrip("█"))
                    fills.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{run * cw + .5:.1f}" height="{ch + .6:.1f}"/>')
                elif chr_ in SEG:
                    for (ax, ay), (bx, by) in SEG[chr_]:
                        paths.append(f"M{x + ax * cw:.1f} {y + ay * ch:.1f}L{x + bx * cw:.1f} {y + by * ch:.1f}")
            delay = row_i * 0.07
            out.append(
                f'<g class="t" style="animation-delay:{delay:.2f}s">'
                f'<path d="{" ".join(paths)}" stroke="{SHADOW}" stroke-width="2.2" fill="none" stroke-linecap="square"/>'
                f'<g fill="url(#accent)" shape-rendering="crispEdges">{"".join(fills)}</g></g>'
            )
            y += ch
            row_i += 1
        y += ch * 0.9
    return "".join(out), y


def portrait(photo, top, max_h=470):
    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(Image.open(photo)).convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)
    cols = 96
    cw = (W - 80) / cols
    ch = cw * 2
    rows = int(min(max_h / ch, cols * img.height / img.width / 2))
    img = img.resize((cols, rows))
    ramp = " .'`^,:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    px = img.load()
    out = []
    for r in range(rows):
        line = "".join(ramp[int(px[c, r] / 255 * (len(ramp) - 1))] for c in range(cols))
        out.append(
            f'<text class="t" x="40" y="{top + (r + 1) * ch:.1f}" textLength="{W - 80}" lengthAdjust="spacingAndGlyphs" '
            f'font-size="{ch * .95:.1f}" fill="url(#accent)" xml:space="preserve" style="animation-delay:{r * 0.02:.2f}s">{esc(line)}</text>'
        )
    return "".join(out), top + rows * ch + 30


def session(prof, top):
    user = prof["prompt_user"]
    prompt = f'<tspan fill="{GREEN}">{esc(user)}@github</tspan><tspan fill="{MUTED}">:</tspan><tspan fill="{ACCENT}">~</tspan><tspan fill="{MUTED}">$ </tspan>'
    lines = [
        (prompt + '<tspan fill="#e6edf3">whoami</tspan>', 0),
        (f'<tspan fill="{TEXT}" font-weight="700">{esc(prof["name"])}</tspan>', 1),
        (prompt + '<tspan fill="#e6edf3">cat tagline.txt</tspan>', 0),
        (f'<tspan fill="{MUTED}">{esc(prof["tagline"])}</tspan>', 1),
        (prompt + f'<tspan fill="#e6edf3">ls ~/work</tspan>', 0),
        (f'<tspan fill="{ACCENT}">frontend/  backend/  automation/  data/</tspan>', 1),
        (prompt + '<tspan fill="#e6edf3">cat now.txt</tspan>', 0),
        (f'<tspan fill="{TEXT}">{esc(prof["now"])}</tspan>', 1),
    ]
    out, y = [], top
    base = 1.1
    for i, (content, is_output) in enumerate(lines):
        out.append(f'<text class="t" x="44" y="{y:.0f}" font-size="21" style="animation-delay:{base + i * 0.25:.2f}s">{content}</text>')
        y += 34 if is_output else 30
        if is_output:
            y += 8
    # final prompt with blinking cursor
    out.append(
        f'<g class="t" style="animation-delay:{base + len(lines) * 0.25:.2f}s">'
        f'<text x="44" y="{y:.0f}" font-size="21">{prompt}</text>'
        f'<rect class="cur" x="{44 + 21 * 0.6 * (len(user) + 11):.0f}" y="{y - 18:.0f}" width="11" height="22" fill="{ACCENT}"/></g>'
    )
    return "".join(out)


def main():
    prof = load_profile()
    photo = os.path.join(ASSETS, "photo.png")
    if os.path.exists(photo):
        art, y = portrait(photo, 60)
    else:
        art, y = banner(prof["banner_lines"], 74)
    y = max(y + 20, 470)
    style = (
        ".t{opacity:0;animation:in .45s ease-out both}"
        "@keyframes in{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:none}}"
        ".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    )
    body = art + f'<line x1="40" y1="{y - 34}" x2="{W - 40}" y2="{y - 34}" stroke="#30363d" stroke-dasharray="4 6"/>' + session(prof, y + 12)
    write(os.path.join(ASSETS, "banner.svg"), frame(W, H, f'{prof["prompt_user"]}@github: ~$ ./whoami.sh', body, style))


if __name__ == "__main__":
    main()
