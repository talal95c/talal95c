"""Generate the animated SVGs of the profile README (light + dark).

Run by .github/workflows/update.yml every 6 hours. Without GITHUB_TOKEN the
cached files in data/ are reused.
"""

import datetime as dt
import json
import math
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = ROOT / "data" / "contributions.json"
DEEPML = "https://raw.githubusercontent.com/talal95c/deep-ml/main/progress.json"
DEEPML_CACHE = ROOT / "data" / "deepml.json"
USER = os.environ.get("GH_USER", "talal95c")
W = 840

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
EASE = "cubic-bezier(.2,.8,.2,1)"

THEMES = {
    "light": {
        "bg": "#ffffff", "chrome": "#f6f8fa", "border": "#d1d9e0", "text": "#1f2328",
        "muted": "#59636e", "faint": "#818b98", "accent": "#1a7f37",
        "heat": ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
    },
    "dark": {
        "bg": "#0d1117", "chrome": "#151b23", "border": "#3d444d", "text": "#f0f6fc",
        "muted": "#9198a1", "faint": "#656c76", "accent": "#3fb950",
        "heat": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
    },
}


def ease_out(p):
    return 1 - (1 - p) ** 3


def base_css(t):
    return f"""
text{{font-family:{FONT};fill:{t['text']}}}
.muted{{fill:{t['muted']}}} .faint{{fill:{t['faint']}}}
.rise{{opacity:0;animation:rise .8s {EASE} forwards}}
.f{{opacity:0}}
@keyframes rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
@keyframes on{{from,to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{
  *{{animation:none!important}} .rise{{opacity:1}} .f{{opacity:0}} .f.last{{opacity:1}}
}}"""


def svg(width, height, css, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title><style>{css}</style>{body}</svg>\n"
    )


def donut_frames(n=48, cols=42, rows=21, scale=150, cw=6.3, lh=11.4):
    """Frames of the classic donut.c torus, one full turn so the loop is seamless."""
    chars = ".,-~:;=!*#$@"
    frames = []
    for f in range(n):
        a = b = 2 * math.pi * f / n
        out = [[" "] * cols for _ in range(rows)]
        zbuf = [[0.0] * cols for _ in range(rows)]
        ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
        for j in range(0, 628, 7):
            ct, st = math.cos(j / 100), math.sin(j / 100)
            for i in range(0, 628, 2):
                cp, sp = math.cos(i / 100), math.sin(i / 100)
                h = ct + 2
                d = 1 / (sp * h * sa + st * ca + 5)
                tt = sp * h * ca - st * sa
                x = int(cols / 2 + scale / cw * d * (cp * h * cb - tt * sb))
                y = int(rows / 2 + scale / lh * d * (cp * h * sb + tt * cb))
                lum = int(8 * ((st * sa - sp * ct * ca) * cb - sp * ct * sa - st * ca - cp * ct * sb))
                if 0 <= y < rows and 0 <= x < cols and d > zbuf[y][x]:
                    zbuf[y][x] = d
                    out[y][x] = chars[max(lum, 0)]
        frames.append(["".join(r).rstrip() for r in out])
    return frames


def terminal(t, info):
    h = 320
    frames = donut_frames()
    n, period = len(frames), 4.8
    css = base_css(t) + f"""
.mono,.mono text{{font-family:{MONO};white-space:pre}}
.d{{fill:{t['muted']};opacity:0;animation:fr {period}s step-end infinite}}
@keyframes fr{{0%{{opacity:1}}{100 / n:.3f}%{{opacity:0}}100%{{opacity:0}}}}
.k{{fill:{t['accent']};font-weight:700}}
.line{{opacity:0;animation:type .35s steps(1) forwards}}
@keyframes type{{to{{opacity:1}}}}
.reveal{{animation:wipe .5s steps(24) forwards}}
@keyframes wipe{{from{{width:0}}to{{width:520px}}}}
.cursor{{fill:{t['text']};animation:blink 1.1s step-end infinite}}
@keyframes blink{{50%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{.d{{opacity:0}} .d0{{opacity:1}} .line{{opacity:1}}}}"""
    body = [
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<path d="M0.5 36V12.5a12 12 0 0 1 12-12h{W - 25}a12 12 0 0 1 12 12V36z" fill="{t["chrome"]}"/>',
        f'<line x1="0.5" y1="36" x2="{W - 0.5}" y2="36" stroke="{t["border"]}"/>',
    ]
    for k, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        body.append(f'<circle cx="{20 + k * 18}" cy="18" r="5.5" fill="{c}"/>')
    body.append(f'<text class="muted mono" x="{W / 2}" y="22.5" font-size="12" text-anchor="middle">talal@paris: ~</text>')
    body.append('<g class="mono" font-size="10.5">')
    for i, frame in enumerate(frames):
        lines = "".join(
            f'<text x="24" y="{64 + r * 11.4:.1f}" xml:space="preserve">{escape(row)}</text>'
            for r, row in enumerate(frame) if row.strip()
        )
        body.append(f'<g class="d d{i}" style="animation-delay:{-period * i / n:.3f}s">{lines}</g>')
    body.append("</g>")
    x0, y0, lh = 316, 80, 24
    body.append(f'<text class="mono line" x="{x0}" y="{y0}" font-size="14"><tspan class="k">talal</tspan>@<tspan class="k">paris</tspan></text>')
    body.append(f'<text class="mono line faint" x="{x0}" y="{y0 + 18}" font-size="14" style="animation-delay:.15s">{"─" * 11}</text>')
    for i, (key, value) in enumerate(info):
        y = y0 + 18 + lh * (i + 1)
        body.append(
            f'<text class="mono line" x="{x0}" y="{y}" font-size="14" style="animation-delay:{0.3 + i * 0.22:.2f}s">'
            f'<tspan class="k">{escape(key):<9}</tspan> {escape(value)}</text>'
        )
    yc = y0 + 18 + lh * (len(info) + 1) + 6
    delay = 0.3 + len(info) * 0.22
    body.append(f'<g class="line" style="animation-delay:{delay:.2f}s">')
    for k, c in enumerate(t["heat"][1:] + [t["muted"], t["text"]]):
        body.append(f'<rect x="{x0 + k * 22}" y="{yc - 12}" width="18" height="12" rx="2" fill="{c}"/>')
    body.append("</g>")
    body.append(
        f'<text class="mono line" x="{x0}" y="{yc + 30}" font-size="14" style="animation-delay:{delay + 0.2:.2f}s">'
        f'<tspan class="k">$</tspan></text>'
        f'<rect class="cursor line" x="{x0 + 16}" y="{yc + 18}" width="8" height="15" style="animation:type .35s steps(1) {delay + 0.2:.2f}s forwards,blink 1.1s step-end {delay + 0.2:.2f}s infinite"/>'
    )
    return svg(W, h, css, "".join(body), "talal@paris — neofetch")


def counter(x, y, start, end, fmt, size, delay, dur=1.4, frames=28, anchor="start", weight=700):
    """Count-up: one text per frame, each shown during its own time window."""
    step = dur / (frames - 1)
    out = []
    for i in range(frames):
        value = start + (end - start) * ease_out(i / (frames - 1))
        last = i == frames - 1
        begin = 0 if i == 0 else delay + i * step
        length = delay + step if i == 0 else step
        anim = f"on .01s linear {begin:.3f}s forwards" if last else f"on {length:.3f}s linear {begin:.3f}s"
        out.append(
            f'<text class="f{" last" if last else ""}" x="{x}" y="{y}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" letter-spacing="-0.5" '
            f'style="animation:{anim};font-variant-numeric:tabular-nums">{escape(fmt(value))}</text>'
        )
    return "".join(out)



def fetch_calendar():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return json.loads(CACHE.read_text())
    query = (
        "query($login:String!){user(login:$login){contributionsCollection{"
        "totalCommitContributions totalRepositoriesWithContributedCommits contributionCalendar{"
        "totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"
    )
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        coll = json.load(res)["data"]["user"]["contributionsCollection"]
    cal = coll["contributionCalendar"]
    levels = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    data = {
        "total": cal["totalContributions"],
        "commits": coll["totalCommitContributions"],
        "repos": coll["totalRepositoriesWithContributedCommits"],
        "weeks": [
            [[d["date"], d["contributionCount"], levels[d["contributionLevel"]]] for d in w["contributionDays"]]
            for w in cal["weeks"]
        ],
    }
    CACHE.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    return data



def activity(t, data):
    weeks = data["weeks"]
    days = [d for w in weeks for d in w]
    active = sum(1 for d in days if d[1])
    best = max((d[1] for d in days), default=0)
    month = sum(d[1] for d in days[-30:])
    cell, gap = 11, 3
    pitch = cell + gap
    gx = (W - len(weeks) * pitch + gap) / 2
    gy = 132
    h = gy + 7 * pitch + 44
    css = base_css(t) + "".join(
        f".c{i}{{animation:cell .5s {EASE} {0.5 + i * 0.012:.3f}s forwards}}" for i in range(len(weeks))
    ) + "@keyframes cell{from{opacity:0}to{opacity:1}} rect.cell{opacity:0}" \
        "@media (prefers-reduced-motion:reduce){rect.cell{opacity:1}}"
    stats = [
        (data["total"], lambda v: f"{round(v):,}", "contributions in the last year"),
        (month, lambda v: f"{round(v):,}", "in the last 30 days"),
        (best, lambda v: f"{round(v):,}", "on my best day"),
        (active, lambda v: f"{round(v)}", "active days"),
    ]
    body = [f'<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>']
    col = (W - 2 * gx) / 4
    for i, (value, fmt, label) in enumerate(stats):
        x = gx + i * col
        body.append(counter(x, 64, 0, value, fmt, 30, 0.2 + i * 0.08))
        body.append(f'<text class="muted rise" x="{x}" y="88" font-size="13" style="animation-delay:{0.1 + i * 0.08:.2f}s">{label}</text>')
    prev = None
    for i, week in enumerate(weeks):
        month = dt.date.fromisoformat(week[0][0]).month
        if prev is not None and month != prev and i < len(weeks) - 2:
            name = dt.date(2000, month, 1).strftime("%b")
            body.append(f'<text class="faint" x="{gx + i * pitch}" y="{gy - 10}" font-size="11">{name}</text>')
        prev = month
        first_weekday = (dt.date.fromisoformat(week[0][0]).weekday() + 1) % 7
        for j, (_, count, level) in enumerate(week):
            y = gy + (first_weekday + j) * pitch
            body.append(
                f'<rect class="cell c{i}" x="{gx + i * pitch}" y="{y}" width="{cell}" height="{cell}" '
                f'rx="2.5" fill="{t["heat"][level]}"/>'
            )
    ly = h - 22
    lx = W - gx - 5 * pitch - 34
    body.append(f'<text class="faint" x="{lx - 8}" y="{ly + 9}" font-size="11" text-anchor="end">Less</text>')
    for k in range(5):
        body.append(f'<rect x="{lx + k * pitch}" y="{ly}" width="{cell}" height="{cell}" rx="2.5" fill="{t["heat"][k]}"/>')
    body.append(f'<text class="faint" x="{lx + 5 * pitch + 4}" y="{ly + 9}" font-size="11">More</text>')
    today = days[-1][0] if days else ""
    body.append(f'<text class="faint" x="{gx}" y="{ly + 9}" font-size="11">Updated {today}</text>')
    return svg(W, h, css, "".join(body), f'{data["total"]} contributions in the last year')




def fetch_deepml():
    try:
        with urllib.request.urlopen(DEEPML, timeout=30) as res:
            data = json.load(res)
    except OSError:
        return json.loads(DEEPML_CACHE.read_text())
    DEEPML_CACHE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    return data


def main():
    ASSETS.mkdir(exist_ok=True)
    data = fetch_calendar()
    deepml = fetch_deepml()
    info = [
        ("role", "AI Engineer @ Safran Aircraft Engines"),
        ("school", "CS engineering @ CY Tech, Paris"),
        ("building", "Adib, an Arabic & Quran vocab app"),
        ("learning", f"ML from scratch · {len(deepml['items'])} Deep-ML problems"),
        ("focus", "agentic AI · NLP · evals"),
        ("commits", f"{data['commits']:,} in the last 12 months"),
    ]
    for name, t in THEMES.items():
        (ASSETS / f"terminal-{name}.svg").write_text(terminal(t, info))
        (ASSETS / f"activity-{name}.svg").write_text(activity(t, data))


if __name__ == "__main__":
    main()
