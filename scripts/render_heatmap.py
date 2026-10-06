#!/usr/bin/env python3
"""Render assets/contrib-heatmap.svg: animated contribution graph in a terminal window."""
import datetime as dt
import os

from common import (ASSETS, DATA_PATH, LEVELS, MUTED, SANS, TEXT, ACCENT,
                    frame, load_json, load_profile, esc, write)

CELL, GAP = 12, 3
STEP = CELL + GAP
BAR = 38                 # title bar height
X0, Y0 = 70, BAR + 46    # top-left of the grid
WIDTH = 900


def main():
    data = load_json(DATA_PATH)
    prof = load_profile()
    days = data["days"]

    # place each day on a (col, row) grid, Sunday = row 0
    cells, col = [], 0
    for i, d in enumerate(days):
        date = dt.date.fromisoformat(d["date"])
        row = (date.weekday() + 1) % 7
        if i and row == 0:
            col += 1
        cells.append((col, row, d, date))
    ncols = col + 1
    height = Y0 + 7 * STEP + 66

    parts = []
    # month labels
    last_month = None
    for c, r, d, date in cells:
        if r == 0 or c == 0:
            if date.month != last_month and (c == 0 or date.day <= 7):
                if c < ncols - 1:
                    parts.append(f'<text class="lbl" x="{X0 + c * STEP}" y="{Y0 - 10}">{date.strftime("%b")}</text>')
                last_month = date.month
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(f'<text class="lbl" x="{X0 - 42}" y="{Y0 + r * STEP + 11}">{name}</text>')

    # cells: diagonal wave reveal, active days flash on arrival
    for c, r, d, _ in cells:
        delay = (c + r * 0.8) * 0.028
        cls = "c a" if d["count"] else "c"
        tip = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {d["date"]}'
        parts.append(
            f'<rect class="{cls}" x="{X0 + c * STEP}" y="{Y0 + r * STEP}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{LEVELS[d["level"]]}" style="animation-delay:{delay:.3f}s"><title>{tip}</title></rect>'
        )

    # footer
    fy = Y0 + 7 * STEP + 40
    total = data["total_contributions"]
    parts.append(
        f'<text class="tot" x="{X0 - 42}" y="{fy}"><tspan fill="{ACCENT}">$</tspan> '
        f'{total:,} contributions in the last year</text>'
    )
    lx = X0 + ncols * STEP - 5 * STEP - 92
    parts.append(f'<text class="lbl" x="{lx}" y="{fy}">Less</text>')
    for i, color in enumerate(LEVELS):
        parts.append(f'<rect x="{lx + 44 + i * STEP}" y="{fy - 12}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
    parts.append(f'<text class="lbl" x="{lx + 50 + 5 * STEP}" y="{fy}">More</text>')

    style = (
        f"text.lbl{{fill:{MUTED};font:600 15px {SANS}}}"
        f"text.tot{{fill:{TEXT};font:700 18px {SANS}}}"
        ".c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .5s ease-out both}"
        ".a{animation:pop .5s ease-out both,flash .8s ease-out both}"
        "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:scale(1)}}"
        "@keyframes flash{0%,40%{filter:brightness(2.2)}100%{filter:brightness(1)}}"
    )
    title = f'{prof["prompt_user"]}@github: ~$ ./contributions.sh'
    write(os.path.join(ASSETS, "contrib-heatmap.svg"), frame(WIDTH, height, title, "".join(parts), style, bar=BAR))


if __name__ == "__main__":
    main()
