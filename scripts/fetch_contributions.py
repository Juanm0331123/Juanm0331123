#!/usr/bin/env python3
"""
Fetch the last year of daily contribution counts and write data/contributions.json
with derived stats (streaks, best day, monthly totals).

Source order:
  1. Public contributions HTML fragment (no auth, same data the profile shows)
  2. GitHub GraphQL contributionCalendar (if GITHUB_TOKEN / GH_TOKEN is set)
  --demo  generates synthetic data, only for previewing the art locally.
"""
import datetime as dt
import json
import os
import random
import re
import sys

from common import DATA_PATH, load_profile

USERNAME = os.environ.get("GH_PROFILE_USER") or load_profile()["username"]
LEVEL_FROM_GQL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
                  "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def from_graphql(token):
    import requests
    query = """query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
    r = requests.post("https://api.github.com/graphql", timeout=30,
                      headers={"Authorization": f"bearer {token}"},
                      json={"query": query, "variables": {"login": USERNAME}})
    r.raise_for_status()
    payload = r.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [{"date": d["date"], "count": d["contributionCount"],
             "level": LEVEL_FROM_GQL.get(d["contributionLevel"], 0)}
            for w in weeks for d in w["contributionDays"]]


def from_html():
    import requests
    from bs4 import BeautifulSoup
    r = requests.get(f"https://github.com/users/{USERNAME}/contributions", timeout=30,
                     headers={"User-Agent": "profile-readme-bot/1.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        m = re.match(r"(\d+)", tips.get(td.get("id"), ""))
        days.append({"date": date, "count": int(m.group(1)) if m else 0,
                     "level": int(td.get("data-level") or 0)})
    if not days:
        raise RuntimeError("no calendar cells found -- GitHub markup may have changed")
    return days


def demo():
    rnd = random.Random(7)
    today = dt.date.today()
    start = today - dt.timedelta(days=364 + (today.weekday() + 1) % 7)
    days = []
    for i in range((today - start).days + 1):
        d = start + dt.timedelta(days=i)
        busy = 0.75 if d.weekday() < 5 else 0.35
        c = rnd.choice([1, 2, 3, 4, 6, 9, 14]) if rnd.random() < busy else 0
        days.append({"date": d.isoformat(), "count": c})
    for d in days:
        c = d["count"]
        d["level"] = 0 if c == 0 else 1 if c < 3 else 2 if c < 6 else 3 if c < 10 else 4
    return days


def streaks(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today isn't over yet
    cur, end = 0, idx
    while idx >= 0 and days[idx]["count"] > 0:
        cur, idx = cur + 1, idx - 1
    current = {"length": cur, "start": days[idx + 1]["date"] if cur else None,
               "end": days[end]["date"] if cur else None}

    best = run = 0
    best_range = (None, None)
    for i, d in enumerate(days):
        run = run + 1 if d["count"] > 0 else 0
        if run > best:
            best, best_range = run, (days[i - run + 1]["date"], d["date"])
    return current, {"length": best, "start": best_range[0], "end": best_range[1]}


def build(days, source):
    days.sort(key=lambda d: d["date"])
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    best = max(days, key=lambda d: d["count"])
    current, longest = streaks(days)
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "username": USERNAME,
        "source": source,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


def main():
    if "--demo" in sys.argv:
        days, source = demo(), "demo"
    else:
        # The public fragment matches exactly what your profile shows (including
        # private contributions if you enabled that setting); GraphQL is the fallback.
        try:
            days, source = from_html(), "html"
        except Exception as e:
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
            if not token:
                raise
            print(f"public HTML failed ({e}); trying GraphQL", file=sys.stderr)
            days, source = from_graphql(token), "graphql"
    data = build(days, source)
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[{source}] {data['total_contributions']} contributions · "
          f"streak {data['current_streak']['length']} · longest {data['longest_streak']['length']}")


if __name__ == "__main__":
    main()
