#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-hosted cyberpunk SVG cards for the GitHub profile README.

WHY THIS EXISTS
---------------
github-readme-stats / github-profile-trophy / github-readme-activity-graph /
capsule-render all live on ``*.vercel.app``.  In mainland China those domains are
DNS-polluted (they resolve to bogus IPs such as 69.63.176.143), so the images
silently break on the rendered profile page.

Every card below is rendered *here* and committed into the repository, so the
README can point at them with **relative** paths.  Relative paths are served by
GitHub itself, never touch a third-party domain, and therefore always load.

USAGE
-----
    GITHUB_TOKEN=xxx python .github/scripts/gen_cards.py assets/cards

Outputs: stats.svg, langs.svg, achievements.svg, activity.svg
"""

import datetime
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# ────────────────────────────── config ──────────────────────────────

API = "https://api.github.com"
USER = os.environ.get("GH_USER", "wind-04300")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/cards"

BG = "#0D1117"
PANEL = "#11161D"
LINE = "#1F2937"
CYAN = "#00F7FF"
MAGENTA = "#FF00E5"
PURPLE = "#7B2FFF"
GOLD = "#FFD700"
GREEN = "#39D353"
TEXT = "#C9D1D9"
DIM = "#6E7681"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
PALETTE = [CYAN, MAGENTA, PURPLE, GOLD, GREEN, "#FF7B72", "#79C0FF", "#A5D6FF"]

# ────────────────────────────── helpers ─────────────────────────────


def api(path, params=None, accept=None):
    url = path if path.startswith("http") else API + path
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER + "-profile-cards")
    req.add_header("Accept", accept or "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fmt(n):
    n = int(n or 0)
    if n >= 1000000:
        return "%.1fM" % (n / 1000000.0)
    if n >= 1000:
        return "%.1fk" % (n / 1000.0)
    return str(n)


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def tier_of(value, table):
    for limit, letter in table:
        if value >= limit:
            return letter
    return "C"


def css():
    return (
        "text{font-family:" + FONT + ";}"
        ".title{fill:" + CYAN + ";font-size:13px;font-weight:700;letter-spacing:2.5px;}"
        ".sub{fill:" + DIM + ";font-size:10px;letter-spacing:1px;}"
        ".num{fill:" + TEXT + ";font-size:29px;font-weight:700;}"
        ".num2{fill:" + TEXT + ";font-size:20px;font-weight:700;}"
        ".lbl{fill:" + DIM + ";font-size:9px;letter-spacing:1.5px;}"
        ".sm{fill:" + DIM + ";font-size:9px;}"
        "@keyframes pulse{0%,100%{opacity:.2}50%{opacity:1}}"
        "@keyframes dash{to{stroke-dashoffset:-386;}}"
        "@keyframes flow{to{stroke-dashoffset:-1600;}}"
        "@keyframes breathe{0%,100%{opacity:.55}50%{opacity:1}}"
        ".pulse{animation:pulse 2.6s ease-in-out infinite;}"
        ".breathe{animation:breathe 4s ease-in-out infinite;}"
        ".border{fill:none;stroke:url(#ng);stroke-width:1.5;stroke-dasharray:48 338;"
        "animation:dash 7s linear infinite;}"
        ".frame{fill:none;stroke:" + LINE + ";stroke-width:1.2;}"
        ".grid{stroke:" + LINE + ";stroke-width:1;opacity:.55;}"
        ".axis{fill:" + DIM + ";font-size:9px;}"
    )


def defs(extra=""):
    return (
        "<defs>"
        '<linearGradient id="ng" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="' + CYAN + '"/>'
        '<stop offset="50%" stop-color="' + PURPLE + '"/>'
        '<stop offset="100%" stop-color="' + MAGENTA + '"/>'
        "</linearGradient>"
        '<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="' + CYAN + '"/>'
        '<stop offset="100%" stop-color="' + MAGENTA + '"/>'
        "</linearGradient>"
        '<linearGradient id="area" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="' + MAGENTA + '" stop-opacity="0.55"/>'
        '<stop offset="100%" stop-color="' + CYAN + '" stop-opacity="0"/>'
        "</linearGradient>"
        '<filter id="glow" x="-40%" y="-40%" width="180%" height="180%">'
        '<feGaussianBlur stdDeviation="3.2" result="b"/>'
        "<feMerge><feMergeNode in=\"b\"/><feMergeNode in=\"SourceGraphic\"/></feMerge>"
        "</filter>"
        + extra
        + "</defs>"
    )


def head(w, h, label):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="%s">'
        % (w, h, w, h, esc(label))
    )


def panel(w, h):
    return (
        '<rect x="0.75" y="0.75" width="%.1f" height="%.1f" rx="13" fill="%s"/>'
        '<rect x="0.75" y="0.75" width="%.1f" height="%.1f" rx="13" class="border"/>'
        % (w - 1.5, h - 1.5, BG, w - 1.5, h - 1.5)
    )


def title_row(w, text, right=""):
    out = '<circle cx="24" cy="30" r="3.6" fill="%s" class="pulse"/>' % CYAN
    out += '<text x="36" y="34" class="title">%s</text>' % esc(text)
    if right:
        out += '<text x="%d" y="33" class="sub" text-anchor="end">%s</text>' % (
            w - 24,
            esc(right),
        )
    return out


# ────────────────────────────── data ────────────────────────────────


def fetch_commit_dates():
    """Every commit authored by USER in the last ~12 months (best effort)."""
    dates = []
    for page in range(1, 6):
        try:
            data = api(
                "/search/commits",
                {
                    "q": "author:%s" % USER,
                    "per_page": 100,
                    "page": page,
                    "sort": "committer-date",
                    "order": "desc",
                },
            )
        except Exception as exc:  # noqa: BLE001
            sys.stderr.write("[warn] search/commits page %d failed: %s\n" % (page, exc))
            break
        items = data.get("items") or []
        if not items:
            break
        for it in items:
            commit = it.get("commit") or {}
            stamp = (commit.get("author") or {}).get("date") or (
                commit.get("committer") or {}
            ).get("date")
            if stamp:
                dates.append(stamp[:10])
        if len(items) < 100:
            break
    return dates


def collect():
    user = api("/users/" + USER)
    repos = api("/users/%s/repos" % USER, {"per_page": 100, "sort": "pushed"})
    repos = [r for r in repos if not r.get("fork")]

    stars = sum(int(r.get("stargazers_count") or 0) for r in repos)
    watchers = sum(int(r.get("watchers_count") or 0) for r in repos)
    forks = sum(int(r.get("forks_count") or 0) for r in repos)

    langs = {}
    for r in repos[:40]:
        try:
            data = api(r["languages_url"])
        except Exception:  # noqa: BLE001
            continue
        for name, size in data.items():
            langs[name] = langs.get(name, 0) + int(size)

    dates = fetch_commit_dates()
    daily = {}
    for d in dates:
        daily[d] = daily.get(d, 0) + 1

    joined = (user.get("created_at") or "")[:10]
    return {
        "user": user,
        "repos": repos,
        "stars": stars,
        "watchers": watchers,
        "forks": forks,
        "langs": langs,
        "daily": daily,
        "commits": len(dates),
        "joined": joined,
        "followers": int(user.get("followers") or 0),
        "following": int(user.get("following") or 0),
        "public_repos": int(user.get("public_repos") or 0),
        "name": user.get("name") or USER,
    }


# ────────────────────────────── cards ───────────────────────────────


def card_stats(d):
    W, H = 495, 195
    score = d["commits"] + d["stars"] * 5 + d["followers"] * 4 + d["public_repos"] * 3
    level = 1 if score <= 0 else min(10, max(1, int(math.log10(score + 1) * 2.2) + 1))
    pct = min(1.0, score / 120.0)

    cells = [
        (fmt(d["commits"]), "TOTAL COMMITS"),
        (fmt(d["stars"]), "STARS EARNED"),
        (fmt(d["followers"]), "FOLLOWERS"),
        (fmt(d["public_repos"]), "REPOSITORIES"),
    ]
    centers = [81.4, 192.1, 302.9, 413.6]

    body = [head(W, H, "GitHub Stats"), defs(), "<style>" + css() + "</style>", panel(W, H)]
    body.append(title_row(W, "GITHUB STATS", "@" + USER))

    for (value, label), cx in zip(cells, centers):
        body.append(
            '<text x="%.1f" y="102" class="num" text-anchor="middle">%s</text>'
            % (cx, esc(value))
        )
        body.append(
            '<text x="%.1f" y="124" class="lbl" text-anchor="middle">%s</text>'
            % (cx, esc(label))
        )

    body.append('<line x1="26" y1="142" x2="469" y2="142" class="grid"/>')
    body.append(
        '<rect x="26" y="156" width="443" height="9" rx="4.5" fill="#161B22"/>'
    )
    body.append(
        '<rect x="26" y="156" width="%.1f" height="9" rx="4.5" fill="url(#bar)" '
        'class="breathe"/>' % max(10.0, 443 * pct)
    )
    body.append(
        '<text x="26" y="184" class="lbl" fill="%s">LEVEL %d / 10</text>'
        % (CYAN, level)
    )
    body.append(
        '<text x="469" y="184" class="lbl" text-anchor="end">JOINED %s</text>'
        % esc(d["joined"])
    )
    body.append("</svg>")
    return "".join(body)


def card_langs(d):
    W, H = 495, 195
    langs = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:5]
    total = float(sum(v for _, v in langs)) or 1.0

    body = [head(W, H, "Top Languages"), defs(), "<style>" + css() + "</style>", panel(W, H)]
    body.append(title_row(W, "TOP LANGUAGES", "BY BYTES"))

    if not langs:
        body.append(
            '<text x="247.5" y="105" class="lbl" text-anchor="middle" fill="%s">'
            "NO LANGUAGE DATA YET</text>" % DIM
        )
    else:
        y = 68.0
        for i, (name, size) in enumerate(langs):
            pct = size / total
            color = PALETTE[i % len(PALETTE)]
            body.append(
                '<text x="26" y="%.1f" fill="%s" font-size="11" font-weight="700" '
                'letter-spacing="1">%s</text>' % (y, color, esc(name.upper()))
            )
            body.append(
                '<text x="469" y="%.1f" class="sm" text-anchor="end">%.1f%%</text>'
                % (y, pct * 100)
            )
            body.append(
                '<rect x="26" y="%.1f" width="443" height="7" rx="3.5" fill="#161B22"/>'
                % (y + 7)
            )
            body.append(
                '<rect x="26" y="%.1f" width="%.1f" height="7" rx="3.5" fill="%s" '
                'class="breathe"/>' % (y + 7, max(6.0, 443 * pct), color)
            )
            y += 26.0

    body.append("</svg>")
    return "".join(body)


def card_achievements(d):
    W, H = 495, 195
    joined_year = int((d["joined"] or "2026")[:4])
    years = max(0, datetime.date.today().year - joined_year)

    badges = [
        ("\u25b2", fmt(d["commits"]), "COMMITS",
         tier_of(d["commits"], [(500, "S"), (200, "A"), (50, "B"), (1, "C")]), CYAN),
        ("\u2605", fmt(d["stars"]), "STARS",
         tier_of(d["stars"], [(500, "S"), (100, "A"), (20, "B"), (1, "C")]), GOLD),
        ("\u25cf", fmt(d["followers"]), "FOLLOWERS",
         tier_of(d["followers"], [(1000, "S"), (200, "A"), (50, "B"), (1, "C")]), MAGENTA),
        ("\u25c6", fmt(d["public_repos"]), "REPOS",
         tier_of(d["public_repos"], [(50, "S"), (20, "A"), (5, "B"), (1, "C")]), PURPLE),
        ("\u2726", str(joined_year), "SINCE",
         tier_of(years, [(5, "S"), (3, "A"), (1, "B"), (0, "C")]), GREEN),
    ]

    body = [head(W, H, "Achievements"), defs(), "<style>" + css() + "</style>", panel(W, H)]
    body.append(title_row(W, "ACHIEVEMENTS", "LIVE DATA"))

    for i, (sym, value, label, tier, color) in enumerate(badges):
        bx = 20.0 + i * 91.0
        by = 56.0
        body.append(
            '<rect x="%.1f" y="%.1f" width="82" height="94" rx="11" fill="%s" '
            'class="frame"/>' % (bx, by, PANEL)
        )
        body.append(
            '<rect x="%.1f" y="%.1f" width="82" height="94" rx="11" fill="none" '
            'stroke="%s" stroke-width="1" opacity="0.35"/>' % (bx, by, color)
        )
        body.append(
            '<rect x="%.1f" y="%.1f" width="17" height="15" rx="4" fill="%s" '
            'opacity="0.85"/>' % (bx + 59, by + 8, color)
        )
        body.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="10" '
            'font-weight="700" fill="%s">%s</text>' % (bx + 67.5, by + 19.5, BG, tier)
        )
        body.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="21" fill="%s" '
            'filter="url(#glow)" class="pulse">%s</text>'
            % (bx + 41, by + 44, color, sym)
        )
        body.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" class="num2">%s</text>'
            % (bx + 41, by + 72, esc(value))
        )
        body.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" class="lbl">%s</text>'
            % (bx + 41, by + 86, esc(label))
        )

    body.append("</svg>")
    return "".join(body)


def card_activity(d):
    W, H = 880, 210
    today = datetime.date.today()
    start = today - datetime.timedelta(days=51 * 7)

    weeks, labels, prev_month = [], [], None
    for w in range(52):
        ws = start + datetime.timedelta(days=w * 7)
        cnt = sum(
            d["daily"].get((ws + datetime.timedelta(days=k)).isoformat(), 0)
            for k in range(7)
        )
        weeks.append(cnt)
        if ws.month != prev_month:
            labels.append((w, ws.strftime("%b").upper()))
            prev_month = ws.month

    peak = max(weeks) if weeks and max(weeks) > 0 else 1
    x0, x1, yb, yt = 34.0, 846.0, 166.0, 64.0

    pts = []
    for w, v in enumerate(weeks):
        x = x0 + (x1 - x0) * w / 51.0
        y = yb - (v / float(peak)) * (yb - yt)
        pts.append((x, y))

    line = "M " + " L ".join("%.1f,%.1f" % p for p in pts)
    area = line + " L %.1f,%.1f L %.1f,%.1f Z" % (x1, yb, x0, yb)

    body = [head(W, H, "Contribution Timeline"), defs(), "<style>" + css() + "</style>", panel(W, H)]
    body.append(title_row(W, "CONTRIBUTION TIMELINE", "LAST 12 MONTHS"))

    for gy in (yb, yb - 34, yb - 68, yb - 102):
        body.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="grid"/>' % (x0, gy, x1, gy))

    body.append('<path d="%s" fill="url(#area)" class="breathe"/>' % area)
    body.append(
        '<path d="%s" fill="none" stroke="%s" stroke-width="2.4" filter="url(#glow)" '
        'stroke-linejoin="round" stroke-linecap="round" '
        'stroke-dasharray="1600" stroke-dashoffset="1600">'
        '<animate attributeName="stroke-dashoffset" from="1600" to="0" dur="2.6s" '
        'fill="freeze"/></path>' % (line, CYAN)
    )

    for w, name in labels:
        x = x0 + (x1 - x0) * w / 51.0
        body.append(
            '<text x="%.1f" y="%.1f" class="axis" text-anchor="middle">%s</text>'
            % (x, yb + 20, esc(name))
        )

    for w, v in enumerate(weeks):
        if v > 0:
            x = x0 + (x1 - x0) * w / 51.0
            y = yb - (v / float(peak)) * (yb - yt)
            body.append(
                '<circle cx="%.1f" cy="%.1f" r="3.2" fill="%s" filter="url(#glow)"/>'
                % (x, y, MAGENTA)
            )

    body.append(
        '<text x="%.1f" y="%.1f" class="lbl">%s COMMITS · PEAK %s / WEEK</text>'
        % (x0, 190, fmt(d["commits"]), fmt(peak))
    )
    body.append(
        '<text x="%.1f" y="%.1f" class="lbl" text-anchor="end">@%s</text>'
        % (x1, 190, esc(USER))
    )
    body.append("</svg>")
    return "".join(body)


# ────────────────────────────── main ────────────────────────────────


def demo_data():
    """Offline sample data - used by ``--demo`` to smoke-test the renderers."""
    today = datetime.date.today()
    daily = {}
    for i in range(0, 240, 3):
        daily[(today - datetime.timedelta(days=i)).isoformat()] = (i % 7) + 1
    return {
        "user": {},
        "repos": [],
        "stars": 12,
        "watchers": 12,
        "forks": 3,
        "langs": {
            "Python": 42000,
            "JavaScript": 18000,
            "TypeScript": 9000,
            "HTML": 4200,
            "CSS": 2500,
        },
        "daily": daily,
        "commits": 137,
        "joined": "2026-09-10",
        "followers": 5,
        "following": 3,
        "public_repos": 4,
        "name": "Demo User",
    }


def main():
    argv = sys.argv[1:]
    demo = "--demo" in argv
    rest = [a for a in argv if not a.startswith("--")]
    out = rest[0] if rest else OUT

    if demo:
        d = demo_data()
        print("[demo] rendering with offline sample data")
    else:
        if not TOKEN:
            sys.stderr.write(
                "[warn] no GITHUB_TOKEN - unauthenticated requests are rate limited\n"
            )
        d = collect()

    if not os.path.isdir(out):
        os.makedirs(out)

    cards = {
        "stats.svg": card_stats(d),
        "langs.svg": card_langs(d),
        "achievements.svg": card_achievements(d),
        "activity.svg": card_activity(d),
    }
    for name, svg in cards.items():
        path = os.path.join(out, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("  wrote %-20s %6d bytes" % (name, len(svg)))

    print(
        "  data: commits=%d stars=%d followers=%d repos=%d langs=%d joined=%s"
        % (
            d["commits"],
            d["stars"],
            d["followers"],
            d["public_repos"],
            len(d["langs"]),
            d["joined"],
        )
    )


if __name__ == "__main__":
    main()
