#!/usr/bin/env python3
"""Render assets/card.svg (840x880): neofetch-style info + live streak/contribution stats."""
import datetime as dt
import os

from common import (ACCENT, ACCENT_2, ASSETS, BORDER, DATA_PATH, GREEN, LEVELS, MUTED,
                    PANEL, SANS, TEXT, esc, frame, load_json, load_profile, write)

W, H = 840, 880


def fmt_date(s):
    return dt.date.fromisoformat(s).strftime("%b %d") if s else "—"


def fmt_range(r):
    if not r["start"]:
        return "start one today"
    return f'{fmt_date(r["start"])} → {fmt_date(r["end"])}'


def stat_box(x, y, w, h, label, value, unit, sub, color, delay):
    return (
        f'<g class="t" style="animation-delay:{delay:.2f}s">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>'
        f'<text x="{x + 20}" y="{y + 32}" fill="{MUTED}" font-size="16">$ {esc(label)}</text>'
        f'<text x="{x + 20}" y="{y + 80}" fill="{color}" font-size="42" font-weight="700">{esc(value)}'
        f'<tspan fill="{MUTED}" font-size="18" font-weight="400"> {esc(unit)}</tspan></text>'
        f'<text x="{x + 20}" y="{y + h - 16}" fill="{MUTED}" font-size="13" font-family="{SANS}">{esc(sub)}</text></g>'
    )


def main():
    prof = load_profile()
    data = load_json(DATA_PATH)
    user = prof["prompt_user"]
    out = []

    # --- neofetch block -------------------------------------------------
    y = 76
    out.append(
        f'<text class="t" x="40" y="{y}" font-size="24" font-weight="700">'
        f'<tspan fill="{GREEN}">{esc(user)}</tspan><tspan fill="{TEXT}">@</tspan>'
        f'<tspan fill="{ACCENT}">github</tspan></text>'
    )
    out.append(f'<text class="t" x="40" y="{y + 22}" fill="{MUTED}" font-size="20">{"─" * 16}</text>')
    y += 58
    for i, (k, v) in enumerate(prof["info"]):
        out.append(
            f'<text class="t" x="40" y="{y}" font-size="20" style="animation-delay:{0.08 * (i + 1):.2f}s">'
            f'<tspan fill="{ACCENT}" font-weight="700">{esc(k)}</tspan><tspan fill="{MUTED}">: </tspan>'
            f'<tspan fill="{TEXT}">{esc(v)}</tspan></text>'
        )
        y += 31
    # palette strip
    y += 4
    palette = ["#ff5f56", "#ffbd2e", "#27c93f", ACCENT, ACCENT_2, "#f472b6", "#e6edf3", "#30363d"]
    out.append(f'<g class="t" style="animation-delay:{0.08 * (len(prof["info"]) + 1):.2f}s">' + "".join(
        f'<rect x="{40 + i * 34}" y="{y}" width="30" height="16" rx="3" fill="{c}"/>' for i, c in enumerate(palette)) + "</g>")
    y += 40

    # --- stat boxes ----------------------------------------------------
    gap, bw, bh = 16, (W - 80 - 16) / 2, 132
    cur, lon = data["current_streak"], data["longest_streak"]
    best = data["best_day"]
    boxes = [
        ("current streak", str(cur["length"]), "days", fmt_range(cur), GREEN),
        ("longest streak", str(lon["length"]), "days", fmt_range(lon), ACCENT),
        ("contributions", f'{data["total_contributions"]:,}', "/ year",
         f'{data["active_days"]} active days · {data["avg_per_active_day"]} per day', ACCENT_2),
        ("best day", str(best["count"]), "contribs", fmt_date(best["date"]) + " — personal record", "#f472b6"),
    ]
    for i, b in enumerate(boxes):
        bx = 40 + (i % 2) * (bw + gap)
        by = y + (i // 2) * (bh + gap)
        out.append(stat_box(bx, by, bw, bh, *b, delay=0.9 + i * 0.12))
    y += 2 * bh + gap + 28

    # --- monthly bars ----------------------------------------------------
    months = data["monthly"][-12:]
    peak = max((m["total"] for m in months), default=1) or 1
    chart_h = H - y - 104
    out.append(f'<text class="t" x="40" y="{y + 4}" fill="{MUTED}" font-size="16" style="animation-delay:1.4s">$ monthly --last 12</text>')
    base = y + 24 + chart_h
    slot = (W - 80) / max(len(months), 1)
    for i, m in enumerate(months):
        h = max(3, m["total"] / peak * chart_h)
        bx = 40 + i * slot + slot * 0.18
        lvl = 4 if m["total"] == peak else 3 if m["total"] > peak * .6 else 2 if m["total"] > peak * .3 else 1
        label = dt.date.fromisoformat(m["month"] + "-01").strftime("%b")
        out.append(
            f'<rect class="b" x="{bx:.1f}" y="{base - h:.1f}" width="{slot * 0.64:.1f}" height="{h:.1f}" rx="3" '
            f'fill="{LEVELS[lvl]}" style="animation-delay:{1.5 + i * 0.05:.2f}s"><title>{label}: {m["total"]}</title></rect>'
            f'<text x="{bx + slot * 0.32:.1f}" y="{base + 20:.1f}" fill="{MUTED}" font-size="12" text-anchor="middle">{label}</text>'
        )

    updated = data["generated_at"][:10]
    out.append(f'<text x="{W / 2}" y="{H - 16}" fill="#484f58" font-size="12" text-anchor="middle">'
               f'updated {updated} · auto-refreshed daily by GitHub Actions</text>')

    style = (
        ".t{opacity:0;animation:in .45s ease-out both}"
        "@keyframes in{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:none}}"
        ".b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .6s ease-out both}"
        "@keyframes grow{to{transform:scaleY(1)}}"
    )
    write(os.path.join(ASSETS, "card.svg"), frame(W, H, f"{user}@github: ~$ neofetch --stats", "".join(out), style))


if __name__ == "__main__":
    main()
