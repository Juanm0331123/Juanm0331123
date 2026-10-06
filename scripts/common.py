"""Shared paths, palette and helpers for the profile-art scripts."""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_PATH = os.path.join(ROOT, "data", "contributions.json")
PROFILE_PATH = os.path.join(ROOT, "profile.json")
ASSETS = os.path.join(ROOT, "assets")

# GitHub dark palette + one accent
BG_TOP = "#111722"
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#22d3ee"      # cyan
ACCENT_2 = "#a78bfa"    # violet
GREEN = "#39d353"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

# portrait.svg and card.svg sit side by side at half size, so they share one canvas
# and every font in them is sized for that 50 % scale (28 px here -> 14 px on GitHub).
WHOAMI_W, WHOAMI_H, WHOAMI_BAR = 840, 1120, 48

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_profile():
    return load_json(PROFILE_PATH)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def window_chrome(width, title, height=30):
    """Mac-style terminal title bar used by every card; scales with its height."""
    cy, r, font = height / 2, height / 6, height * 0.42
    dots = "".join(
        f'<circle cx="{height * (0.67 + i * 0.53):.1f}" cy="{cy}" r="{r:.1f}" fill="{c}"/>'
        for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")))
    return (
        f'<line x1="0" y1="{height}" x2="{width}" y2="{height}" stroke="{BORDER}"/>{dots}'
        f'<text x="{width / 2}" y="{cy + font * 0.35:.1f}" fill="{MUTED}" font-size="{font:.0f}" '
        f'text-anchor="middle" font-family="{MONO}">{esc(title)}</text>'
    )


def frame(width, height, title, body, style="", bar=30):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{MONO}">'
        f"<style>{style}"
        "@media (prefers-reduced-motion: reduce){*{animation:none!important;opacity:1!important;transform:none!important}}"
        "</style>"
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        f'<linearGradient id="accent" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{width}" y2="{height * 0.6:.0f}">'
        f'<stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT_2}"/></linearGradient></defs>'
        f'<rect width="{width}" height="{height}" rx="12" fill="url(#bg)"/>'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="none" stroke="{BORDER}"/>'
        f"{window_chrome(width, title, bar)}{body}</svg>"
    )


def write(path, svg):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {os.path.relpath(path, ROOT)} ({len(svg) // 1024} KB)")
