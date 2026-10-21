"""Generate the animated SVGs of the profile README (light + dark).

Run by .github/workflows/update.yml every day. Without GITHUB_TOKEN the
cached data/contributions.json is reused.
"""

import datetime as dt
import json
import os
import textwrap
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
CACHE = ROOT / "data" / "contributions.json"
USER = os.environ.get("GH_USER", "talal95c")
W = 840

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
EASE = "cubic-bezier(.2,.8,.2,1)"

THEMES = {
    "light": {
        "bg": "#ffffff", "border": "#d1d9e0", "text": "#1f2328",
        "muted": "#59636e", "faint": "#818b98", "accent": "#1a7f37",
        "heat": ["#eff2f5", "#aceebb", "#4ac26b", "#2da44e", "#116329"],
    },
    "dark": {
        "bg": "#0d1117", "border": "#3d444d", "text": "#f0f6fc",
        "muted": "#9198a1", "faint": "#656c76", "accent": "#3fb950",
        "heat": ["#151b23", "#033a16", "#196c2e", "#2ea043", "#56d364"],
    },
}

PROJECTS = [
    {
        "slug": "legible", "name": "Legible",
        "badge": "Speaker attribution · 224-question benchmark",
        "desc": "Legal AI for French court rulings: it tells who said what, then "
                "answers with cited paragraphs. 4× fewer misattributions than a plain LLM.",
        "stack": "Python · FastAPI · Mistral · Jev · MCP",
    },
    {
        "slug": "adib", "name": "Adib",
        "badge": "Spaced repetition · web and iOS",
        "desc": "Arabic and Quran vocabulary app for web and iOS, built on "
                "word-by-word learning, spaced repetition and daily streaks.",
        "stack": "Next.js · Supabase · Capacitor · iOS",
    },
    {
        "slug": "sylo", "name": "Sylo.ai",
        "badge": "Payment risk · on-chain escrow",
        "desc": "Cross-border B2B payment router: the cheapest compliant route when "
                "all is fine, an escrow window to stop the money when something is wrong.",
        "stack": "FastAPI · Next.js · Three.js · Solidity · LightGBM",
    },
    {
        "slug": "miropolis", "name": "MiroPolis",
        "badge": "Multi-agent simulation",
        "desc": "Multi-agent digital twin of the French National Assembly: AI deputies "
                "debate, amend and vote on a bill before the real vote.",
        "stack": "Python · Flask · OASIS · LLM agents · Vue · D3",
    },
]


ROLES = [
    "AI Engineer at Safran Aircraft Engines",
    "Computer science engineering student at CY Tech",
    "Founder of Adib, an Arabic vocabulary app",
]
DEEPML = "https://raw.githubusercontent.com/talal95c/deep-ml/main/progress.json"
DEEPML_CACHE = ROOT / "data" / "deepml.json"
README = ROOT / "README.md"


def highlight_items(data, deepml):
    solved = len(deepml["items"])
    return [
        {"from": 0, "to": solved, "fmt": lambda v: f"{round(v)}",
         "label": "ML problems solved", "sub": "by hand, on Deep-ML"},
        {"from": 1, "to": 4, "fmt": lambda v: f"{v:.1f}×" if v < 4 else "4×",
         "label": "fewer misattributions", "sub": "Legible vs. a plain LLM"},
        {"from": 0, "to": data["commits"], "fmt": lambda v: f"{round(v):,}",
         "label": "commits", "sub": "in the last 12 months"},
        {"from": 0, "to": data["repos"], "fmt": lambda v: f"{round(v)}",
         "label": "repositories", "sub": "with commits this year"},
    ]


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


def header(t):
    css = base_css(t) + f"""
.dot{{fill:{t['accent']}}}
.pulse{{fill:{t['accent']};transform-origin:center;transform-box:fill-box;animation:pulse 2s ease-out infinite}}
@keyframes pulse{{from{{opacity:.6;transform:scale(1)}}to{{opacity:0;transform:scale(3)}}}}
.role{{opacity:0;animation:role {len(ROLES) * 3}s {EASE} infinite}}
@keyframes role{{0%{{opacity:0;transform:translateY(8px)}}4%,21%{{opacity:1;transform:none}}
25%{{opacity:0;transform:translateY(-8px)}}100%{{opacity:0}}}}
.line{{stroke:{t['text']};stroke-dasharray:56;stroke-dashoffset:56;animation:draw .9s {EASE} .5s forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@media (prefers-reduced-motion:reduce){{.role{{opacity:0}} .role.r0{{opacity:1}} .line{{stroke-dashoffset:0}}}}"""
    pill_w = 130
    body = [
        f'<g class="rise"><rect x="{(W - pill_w) / 2}" y="14" width="{pill_w}" height="28" rx="14" '
        f'fill="none" stroke="{t["border"]}"/>'
        f'<circle class="pulse" cx="{(W - pill_w) / 2 + 18}" cy="28" r="3.5"/>'
        f'<circle class="dot" cx="{(W - pill_w) / 2 + 18}" cy="28" r="3.5"/>'
        f'<text class="muted" x="{(W - pill_w) / 2 + 31}" y="32.5" font-size="12.5" font-weight="500">'
        f"Paris, France</text></g>",
        f'<text class="rise" x="{W / 2}" y="104" text-anchor="middle" font-size="56" font-weight="700" '
        f'letter-spacing="-2" style="animation-delay:.1s">Talal Aamir</text>',
        f'<line class="line" x1="{W / 2 - 28}" y1="126" x2="{W / 2 + 28}" y2="126" stroke-width="2" stroke-linecap="round"/>',
    ]
    for i, role in enumerate(ROLES):
        body.append(
            f'<text class="role r{i} muted" x="{W / 2}" y="166" text-anchor="middle" font-size="19" '
            f'style="animation-delay:{0.6 + i * 3}s">{escape(role)}</text>'
        )
    return svg(W, 190, css, "".join(body), "Talal Aamir — AI engineer")


def highlights(t, items):
    gap, h = 12, 132
    tw = (W - gap * 3) / 4
    css = base_css(t)
    body = []
    for i, item in enumerate(items):
        x = i * (tw + gap)
        d = 0.08 * i
        body.append(
            f'<g class="rise" style="animation-delay:{d:.2f}s">'
            f'<rect x="{x + 0.5}" y="0.5" width="{tw - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>'
            + counter(x + 20, 58, item["from"], item["to"], item["fmt"], 34, 0.25 + d)
            + f'<text x="{x + 20}" y="88" font-size="14" font-weight="600">{escape(item["label"])}</text>'
            f'<text class="faint" x="{x + 20}" y="108" font-size="12.5">{escape(item["sub"])}</text></g>'
        )
    return svg(W, h, css, "".join(body), "Highlights")


def project_card(p, t, delay):
    cw, ch = 410, 200
    badge_w = len(p["badge"]) * 5.9 + 24
    lines = textwrap.wrap(p["desc"], 52)
    assert len(lines) <= 3, p["name"]
    css = base_css(t) + f"""
.arrow{{animation:nudge 2.4s {EASE} 1.2s infinite}}
@keyframes nudge{{0%,70%,100%{{transform:none}}80%{{transform:translate(3px,-3px)}}}}"""
    body = [
        f'<g class="rise" style="animation-delay:{delay}s">',
        f'<rect x="0.5" y="0.5" width="{cw - 1}" height="{ch - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<text x="24" y="44" font-size="22" font-weight="700" letter-spacing="-0.5">{escape(p["name"])}</text>',
        f'<text class="arrow faint" x="{cw - 24}" y="42" font-size="18" text-anchor="end">↗</text>',
        f'<rect x="24.5" y="58.5" width="{badge_w:.0f}" height="23" rx="11.5" fill="none" stroke="{t["border"]}"/>',
        f'<text class="muted" x="36" y="74.5" font-size="12" font-weight="500">{escape(p["badge"])}</text>',
    ]
    for j, line in enumerate(lines):
        body.append(f'<text class="muted" x="24" y="{112 + j * 21}" font-size="14">{escape(line)}</text>')
    body.append(f'<text class="faint" x="24" y="{ch - 22}" font-size="12" font-weight="500">{escape(p["stack"])}</text></g>')
    return svg(cw, ch, css, "".join(body), f'{p["name"]} — {p["badge"]}')


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
    body.append(f'<text class="faint" x="{gx}" y="{ly + 9}" font-size="11">Updated daily · {today}</text>')
    return svg(W, h, css, "".join(body), f'{data["total"]} contributions in the last year')


def fetch_deepml():
    try:
        with urllib.request.urlopen(DEEPML, timeout=30) as res:
            data = json.load(res)
    except OSError:
        return json.loads(DEEPML_CACHE.read_text())
    DEEPML_CACHE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    return data


def research_log(deepml, limit=5):
    items = sorted(deepml["items"].values(), key=lambda i: i["first_solved_at"], reverse=True)[:limit]
    rows = ["| Solved | Problem | Topic |", "| --- | --- | --- |"]
    for i in items:
        link = f"https://github.com/talal95c/deep-ml/tree/main/{i['path']}"
        rows.append(f"| {i['first_solved_at'][:10]} | [{i['title']}]({link}) | {i['category']} · {i['difficulty']} |")
    return "\n".join(rows)


def update_readme(deepml):
    text = README.read_text()
    start, end = "<!-- research-log:start -->", "<!-- research-log:end -->"
    head, rest = text.split(start)
    _, tail = rest.split(end)
    README.write_text(f"{head}{start}\n{research_log(deepml)}\n{end}{tail}")


def main():
    ASSETS.mkdir(exist_ok=True)
    data = fetch_calendar()
    deepml = fetch_deepml()
    update_readme(deepml)
    for name, t in THEMES.items():
        (ASSETS / f"header-{name}.svg").write_text(header(t))
        (ASSETS / f"highlights-{name}.svg").write_text(highlights(t, highlight_items(data, deepml)))
        (ASSETS / f"activity-{name}.svg").write_text(activity(t, data))
        for i, p in enumerate(PROJECTS):
            (ASSETS / f"project-{p['slug']}-{name}.svg").write_text(project_card(p, t, 0.08 * i))


if __name__ == "__main__":
    main()
