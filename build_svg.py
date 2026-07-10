#!/usr/bin/env python3
"""Generate dark_mode.svg + light_mode.svg for the profile README.

Style: neofetch card in the Andrew6rant layout — ". Key: ....... value" with
dot-leaders aligning all values to one column, full-width section rules, a top
`cal@github ────` rule. No cursor.

GitHub-safe rendering (learned the hard way): GitHub strips <style> and CSS
@keyframes/animation from README SVGs. So NO CSS animation, NO opacity tricks —
every element has an inline `fill` and is visible by default. (A template that
hides text behind stripped CSS renders as an EMPTY card.)

Left panel  : Braille art (assets/portrait.braille.txt).
Right panel : neofetch; stat values carry the ids today.py fills with live data.
Run: python build_svg.py   (then today.py re-injects live numbers)
"""
from html import escape

ART = open("assets/portrait.braille.txt", encoding="utf-8").read().splitlines()

# ("kv", key, value)  value=str or (id, placeholder) for a live-data field.
# ("rule", label|None)  ("head", name, tail)  ("blank",)  ("stat_*",)
FIELDS = [
    ("head", "cal", "@github"),
    ("kv", "Site", "thecalendre.tech"),
    ("kv", "Uptime", ("age_data", "on GitHub since 2021")),
    ("kv", "Focus", "distributed systems · AI-agent infra"),
    ("kv", "Editor", "Claude Code · Neovim"),
    ("kv", "Langs", "Go · Rust · TypeScript · Python"),
    ("kv", "Infra", "Docker · Terraform · Airflow"),
    ("blank",),
    ("kv", "Ships.CLI", "yank · agentop"),
    ("kv", "Ships.Web", "0-suite · contextdev"),
    ("kv", "Ships.Agents", "smartloop · Hermes"),
    ("blank",),
    ("kv", "Hobbies.HW", "rooted OnePlus 7 Pro · Magisk + Termux"),
    ("kv", "Hobbies.SW", "on-device llama.cpp · offline wiki + maps"),
    ("blank",),
    ("rule", "Contact"),
    ("kv", "Portfolio", "thecalendre.tech"),
    ("kv", "X", "@thecalendre"),
    ("blank",),
    ("rule", "GitHub Stats"),
    ("stat_repos",),
    ("stat_commits",),
    ("stat_loc",),
]

THEMES = {
    "dark":  dict(bg="#0d1117", fg="#e6edf3", art="#5fb98c", key="#5fb98c",
                  val="#e6edf3", cc="#42504a", add="#3fb950", dele="#f85149",
                  dim="#8b949e", frame="#233041"),
    "light": dict(bg="#faf9f6", fg="#1f2328", art="#2f7d5a", key="#2f7d5a",
                  val="#1f2328", cc="#c1c7c2", add="#1a7f37", dele="#cf222e",
                  dim="#6a737d", frame="#e6e4dd"),
}

FS = 14
LH = 19
ART_X = 22
ART_COLS = max((len(l) for l in ART), default=0)
NEO_X = ART_X + int(ART_COLS * FS * 0.62) + 30
NEO_CHARS = 60          # right-column width in chars
VAL_COL = 22            # column (chars from line start) where values begin
TOP = 34
WIDTH = NEO_X + int(NEO_CHARS * FS * 0.62) + 16
HEIGHT = TOP + max(len(ART), sum(1 for f in FIELDS)) * LH + 20
FONT = "ui-monospace,'JetBrains Mono','Cascadia Code',Consolas,monospace"


def ts(text, fill, tid=None):
    idattr = f' id="{tid}"' if tid else ""
    return f'<tspan{idattr} fill="{fill}">{escape(text)}</tspan>'


def kv_row(t, key, val, y):
    """. Key: ....... value  — dots pad so values align at VAL_COL."""
    lead = f'. {key}: '
    ndots = max(2, VAL_COL - len(lead))
    row = f'<tspan x="{NEO_X}" y="{y}">'
    row += ts(". ", t["dim"]) + ts(key, t["key"]) + ts(": ", t["dim"])
    if isinstance(val, tuple):
        vid, vtext = val
        row += ts("." * ndots + " ", t["cc"], vid + "_dots") + ts(vtext, t["val"], vid)
    else:
        row += ts("." * ndots + " ", t["cc"]) + ts(val, t["val"])
    return row + "</tspan>"


def render(theme):
    t = THEMES[theme]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}px" height="{HEIGHT}px" '
         f'font-family="{FONT}" font-size="{FS}px">']
    p.append(f'<rect width="{WIDTH}px" height="{HEIGHT}px" fill="{t["bg"]}" rx="14"/>')
    p.append(f'<rect x="6" y="6" width="{WIDTH-12}px" height="{HEIGHT-12}px" fill="none" '
             f'stroke="{t["frame"]}" stroke-width="1" rx="10"/>')
    p.append('<text xml:space="preserve">')

    for i, line in enumerate(ART):
        p.append(f'<tspan x="{ART_X}" y="{TOP + i*LH}" fill="{t["art"]}">{escape(line)}</tspan>')

    y = TOP
    for f in FIELDS:
        kind = f[0]
        if kind == "blank":
            y += LH; continue
        if kind == "head":
            _, name, tail = f
            rule = "─" * max(4, NEO_CHARS - len(name) - len(tail) - 1)
            p.append(f'<tspan x="{NEO_X}" y="{y}">'
                     + f'<tspan fill="{t["fg"]}" font-weight="bold">{escape(name)}</tspan>'
                     + ts(tail, t["dim"]) + ts(" " + rule, t["cc"]) + "</tspan>")
        elif kind == "rule":
            label = f[1]
            rule = "─" * max(4, NEO_CHARS - len(label) - 3)
            p.append(f'<tspan x="{NEO_X}" y="{y}">' + ts("─ ", t["cc"])
                     + f'<tspan fill="{t["fg"]}" font-weight="bold">{escape(label)}</tspan>'
                     + ts(" " + rule, t["cc"]) + "</tspan>")
        elif kind == "kv":
            p.append(kv_row(t, f[1], f[2], y))
        elif kind == "stat_repos":
            lead = ". Repos: "; nd = max(2, VAL_COL - len(lead))
            p.append(f'<tspan x="{NEO_X}" y="{y}">' + ts(". ", t["dim"]) + ts("Repos", t["key"]) + ts(": ", t["dim"])
                     + ts("." * nd + " ", t["cc"], "repo_data_dots") + ts("0", t["val"], "repo_data")
                     + ts(" {", t["dim"]) + ts("Contributed", t["key"]) + ts(": ", t["dim"]) + ts("0", t["val"], "contrib_data")
                     + ts("} | ", t["dim"]) + ts("Stars", t["key"]) + ts(" ... ", t["cc"], "star_data_dots") + ts("0", t["val"], "star_data") + "</tspan>")
        elif kind == "stat_commits":
            lead = ". Commits: "; nd = max(2, VAL_COL - len(lead))
            p.append(f'<tspan x="{NEO_X}" y="{y}">' + ts(". ", t["dim"]) + ts("Commits", t["key"]) + ts(": ", t["dim"])
                     + ts("." * nd + " ", t["cc"], "commit_data_dots") + ts("0", t["val"], "commit_data")
                     + ts(" | ", t["dim"]) + ts("Followers", t["key"]) + ts(" .. ", t["cc"], "follower_data_dots") + ts("0", t["val"], "follower_data") + "</tspan>")
        elif kind == "stat_loc":
            lead = ". Lines of code: "; nd = max(2, VAL_COL - len(lead))
            p.append(f'<tspan x="{NEO_X}" y="{y}">' + ts(". ", t["dim"]) + ts("Lines of code", t["key"]) + ts(": ", t["dim"])
                     + ts("." * nd + " ", t["cc"], "loc_data_dots") + ts("0", t["val"], "loc_data")
                     + ts(" ( ", t["dim"]) + ts("0", t["add"], "loc_add") + ts("++", t["add"]) + ts(", ", t["dim"])
                     + ts(" ", t["cc"], "loc_del_dots") + ts("0", t["dele"], "loc_del") + ts("--", t["dele"]) + ts(" )", t["dim"]) + "</tspan>")
        y += LH
    p.append("</text>")
    p.append("</svg>")
    return "\n".join(p)


for theme, fname in (("dark", "dark_mode.svg"), ("light", "light_mode.svg")):
    open(fname, "w", encoding="utf-8", newline="\n").write(render(theme))
    print("wrote", fname)
