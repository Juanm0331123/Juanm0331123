#!/usr/bin/env python3
"""Render assets/card.svg: neofetch-style info + live streak/contribution stats.

Shown at half size next to portrait.svg, so every font here is twice the size
it should read at on GitHub (28 -> 14 px).
"""
import datetime as dt
import os

from common import (ACCENT, ACCENT_2, ASSETS, BORDER, DATA_PATH, GREEN, LEVELS, MUTED, PANEL,
                    SANS, TEXT, WHOAMI_BAR, WHOAMI_H, WHOAMI_W, esc, frame, load_json,
                    load_profile, write)

W, H = WHOAMI_W, WHOAMI_H
X = 40


def fmt_date(s):
    return dt.date.fromisoformat(s).strftime("%b %d") if s else "—"


def fmt_range(r):
    if not r["start"]:
        return "start one today"
    return f'{fmt_date(r["start"])} → {fmt_date(r["end"])}'


def stat_box(x, y, w, h, label, value, unit, sub, color, delay):
    return (
        f'<g class="t" style="animation-delay:{delay:.2f}s">'
        f'<rect x="{x:.0f}" y="{y}" width="{w:.0f}" height="{h}" rx="14" fill="{PANEL}" stroke="{BORDER}" stroke-width="1.5"/>'
        f'<text x="{x + 24:.0f}" y="{y + 42}" fill="{MUTED}" font-size="24">$ {esc(label)}</text>'
        f'<text x="{x + 24:.0f}" y="{y + 106}" fill="{color}" font-size="58" font-weight="700">{esc(value)}'
        f'<tspan fill="{MUTED}" font-size="26" font-weight="400"> {esc(unit)}</tspan></text>'
        f'<text x="{x + 24:.0f}" y="{y + h - 20}" fill="{MUTED}" font-size="23" font-family="{SANS}">{esc(sub)}</text></g>'
    )


def main():
    prof = load_profile()
    data = load_json(DATA_PATH)
    user = prof["prompt_user"]
    out = []

    # --- neofetch block -------------------------------------------------
    y = WHOAMI_BAR + 58
    out.append(
        f'<text class="t" x="{X}" y="{y}" font-size="38" font-weight="700">'
        f'<tspan fill="{GREEN}">{esc(user)}</tspan><tspan fill="{TEXT}">@</tspan>'
        f'<tspan fill="{ACCENT}">github</tspan></text>'
    )
    palette = ["#ff5f56", "#ffbd2e", "#27c93f", ACCENT, ACCENT_2, "#f472b6", "#e6edf3", "#30363d"]
    out.append('<g class="t">' + "".join(
        f'<rect x="{W - X - (len(palette) - i) * 40 + 6}" y="{y - 24}" width="34" height="22" rx="4" fill="{c}"/>'
        for i, c in enumerate(palette)) + "</g>")
    out.append(f'<line class="t" x1="{X}" y1="{y + 22}" x2="{W - X}" y2="{y + 22}" stroke="{BORDER}" stroke-width="2"/>')
    y += 80
    for i, (k, v) in enumerate(prof["info"]):
        out.append(
            f'<text class="t" x="{X}" y="{y}" font-size="28" style="animation-delay:{0.08 * (i + 1):.2f}s">'
            f'<tspan fill="{ACCENT}" font-weight="700">{esc(k)}</tspan><tspan fill="{MUTED}">: </tspan>'
            f'<tspan fill="{TEXT}">{esc(v)}</tspan></text>'
        )
        y += 44
    y += 4

    # --- stat boxes ----------------------------------------------------
    gap, bh = 18, 162
    bw = (W - 2 * X - gap) / 2
    cur, lon, best = data["current_streak"], data["longest_streak"], data["best_day"]
    boxes = [
        ("current streak", str(cur["length"]), "days", fmt_range(cur), GREEN),
        ("longest streak", str(lon["length"]), "days", fmt_range(lon), ACCENT),
        ("contributions", f'{data["total_contributions"]:,}', "/ year",
         f'{data["active_days"]} active days · {data["avg_per_active_day"]}/day', ACCENT_2),
        ("best day", str(best["count"]), "contribs", f'{fmt_date(best["date"])} · personal record', "#f472b6"),
    ]
    for i, b in enumerate(boxes):
        bx = X + (i % 2) * (bw + gap)
        by = y + (i // 2) * (bh + gap)
        out.append(stat_box(bx, by, bw, bh, *b, delay=0.9 + i * 0.12))
    y += 2 * bh + gap + 50

    # --- monthly bars ----------------------------------------------------
    months = data["monthly"][-12:]
    peak = max((m["total"] for m in months), default=1) or 1
    out.append(f'<text class="t" x="{X}" y="{y}" fill="{MUTED}" font-size="24" style="animation-delay:1.4s">$ monthly --last 12</text>')
    base = H - 82
    chart_h = base - y - 22
    slot = (W - 2 * X) / max(len(months), 1)
    for i, m in enumerate(months):
        h = max(4, m["total"] / peak * chart_h)
        bx = X + i * slot + slot * 0.14
        lvl = 4 if m["total"] == peak else 3 if m["total"] > peak * .6 else 2 if m["total"] > peak * .3 else 1
        label = dt.date.fromisoformat(m["month"] + "-01").strftime("%b")
        out.append(
            f'<rect class="b" x="{bx:.1f}" y="{base - h:.1f}" width="{slot * 0.72:.1f}" height="{h:.1f}" rx="4" '
            f'fill="{LEVELS[lvl]}" style="animation-delay:{1.5 + i * 0.05:.2f}s"><title>{label}: {m["total"]}</title></rect>'
            f'<text x="{bx + slot * 0.36:.1f}" y="{base + 28:.1f}" fill="{MUTED}" font-size="19" text-anchor="middle">{label}</text>'
        )

    updated = data["generated_at"][:10]
    out.append(f'<text x="{W / 2}" y="{H - 18}" fill="#6e7681" font-size="19" text-anchor="middle">'
               f'updated {updated} · auto-refreshed daily</text>')

    style = (
        ".t{opacity:0;animation:in .45s ease-out both}"
        "@keyframes in{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:none}}"
        ".b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .6s ease-out both}"
        "@keyframes grow{to{transform:scaleY(1)}}"
    )
    write(os.path.join(ASSETS, "card.svg"),
          frame(W, H, f"{user}@github: ~$ neofetch --stats", "".join(out), style, bar=WHOAMI_BAR))


if __name__ == "__main__":
    main()
