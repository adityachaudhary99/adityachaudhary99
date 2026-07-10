#!/usr/bin/env python3
"""Generate dark_mode.svg + light_mode.svg for the profile README.

Rendering rules (GitHub-safe — learned the hard way):
  * GitHub sanitizes README SVGs: it strips <script> and CSS @keyframes/animation,
    and may drop <style> blocks. So we use NO CSS animation and NO opacity tricks —
    every element is painted with an inline `fill` and is visible by default. A
    template that hides text behind stripped CSS renders as an EMPTY card.
  * The only motion is a blinking cursor via a SMIL <animate> (SMIL is allowed on
    GitHub). If it were ever stripped, the cursor just stays solid — still visible.

Left panel  : Braille art (assets/portrait.braille.txt).
Right panel : neofetch card; stat values carry the ids today.py fills with live
              GitHub data (age/repo/contrib/star/commit/follower/loc).
Run:  python build_svg.py   (re-run after editing art or FIELDS; then today.py
      re-injects the live numbers)
"""
from html import escape

ART = open("assets/portrait.braille.txt", encoding="utf-8").read().splitlines()

FIELDS = [
    ("head", "cal", "@github"),
    ("rule", None, None),
    ("kv", "Site", "thecalendre.tech"),
    ("kv", "Uptime", ("age_data", "on GitHub since 2021")),
    ("kv", "Focus", "distributed systems · AI-agent infra"),
    ("kv", "Editor", "Claude Code · Neovim"),
    ("kv", "Langs", "Go · Rust · TypeScript · Python"),
    ("kv", "Infra", "Docker · Terraform · Airflow"),
    ("blank", None, None),
    ("kv", "Ships.CLI", "yank · agentop"),
    ("kv", "Ships.Web", "0-suite · contextdev"),
    ("kv", "Ships.Agents", "smartloop · Hermes"),
    ("blank", None, None),
    ("rule", "Contact", None),
    ("kv", "Portfolio", "thecalendre.tech"),
    ("kv", "X", "@thecalendre"),
    ("blank", None, None),
    ("rule", "GitHub Stats", None),
    ("stat_repos", None, None),
    ("stat_commits", None, None),
    ("stat_loc", None, None),
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
NEO_X = ART_X + int(ART_COLS * FS * 0.62) + 34
TOP = 34
WIDTH = NEO_X + 560
HEIGHT = TOP + max(len(ART), len(FIELDS)) * LH + 22
FONT = "ui-monospace,'JetBrains Mono','Cascadia Code',Consolas,monospace"


def ts(text, fill, tid=None):
    idattr = f' id="{tid}"' if tid else ""
    return f'<tspan{idattr} fill="{fill}">{escape(text)}</tspan>'


def render(theme):
    t = THEMES[theme]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}px" height="{HEIGHT}px" '
         f'font-family="{FONT}" font-size="{FS}px">']
    p.append(f'<rect width="{WIDTH}px" height="{HEIGHT}px" fill="{t["bg"]}" rx="14"/>')
    p.append(f'<rect x="6" y="6" width="{WIDTH-12}px" height="{HEIGHT-12}px" fill="none" '
             f'stroke="{t["frame"]}" stroke-width="1" rx="10"/>')
    p.append('<text xml:space="preserve">')

    # left: braille art
    for i, line in enumerate(ART):
        p.append(f'<tspan x="{ART_X}" y="{TOP + i*LH}" fill="{t["art"]}">{escape(line)}</tspan>')

    # right: neofetch
    y = TOP
    for kind, a, b in FIELDS:
        if kind == "blank":
            y += LH; continue
        row = f'<tspan x="{NEO_X}" y="{y}">'
        if kind == "head":
            row += (f'<tspan fill="{t["fg"]}" font-weight="bold">{escape(a)}</tspan>'
                    + ts(b, t["cc"]) + ts("  " + "─"*30, t["cc"]))
        elif kind == "rule":
            label = f'<tspan fill="{t["fg"]}" font-weight="bold">{escape(a)} </tspan>' if a else ""
            dash = "─" * (34 - (len(a)+1 if a else 0))
            row += ts("─ ", t["cc"]) + label + ts(dash, t["cc"])
        elif kind == "kv":
            pad = max(3, 15 - len(a))
            if isinstance(b, tuple):
                vid, vtext = b
                row += ts(a, t["key"]) + ts(f' {"."*pad} ', t["cc"], vid+"_dots") + ts(vtext, t["val"], vid)
            else:
                row += ts(a, t["key"]) + ts(f' {"."*pad} ', t["cc"]) + ts(b, t["val"])
        elif kind == "stat_repos":
            row += (ts("Repos", t["key"]) + ts(" .... ", t["cc"], "repo_data_dots") + ts("0", t["val"], "repo_data")
                    + ts(" {", t["dim"]) + ts("Contributed", t["key"]) + ts(": ", t["dim"]) + ts("0", t["val"], "contrib_data")
                    + ts("} | ", t["dim"]) + ts("Stars", t["key"]) + ts(" ... ", t["cc"], "star_data_dots") + ts("0", t["val"], "star_data"))
        elif kind == "stat_commits":
            row += (ts("Commits", t["key"]) + ts(" .. ", t["cc"], "commit_data_dots") + ts("0", t["val"], "commit_data")
                    + ts(" | ", t["dim"]) + ts("Followers", t["key"]) + ts(" .. ", t["cc"], "follower_data_dots") + ts("0", t["val"], "follower_data"))
        elif kind == "stat_loc":
            row += (ts("Lines of code", t["key"]) + ts(" . ", t["cc"], "loc_data_dots") + ts("0", t["val"], "loc_data")
                    + ts(" ( ", t["dim"]) + ts("0", t["add"], "loc_add") + ts("++", t["add"]) + ts(", ", t["dim"])
                    + ts(" ", t["cc"], "loc_del_dots") + ts("0", t["dele"], "loc_del") + ts("--", t["dele"]) + ts(" )", t["dim"]))
        p.append(row + "</tspan>")
        y += LH
    p.append("</text>")
    # blinking terminal cursor (SMIL — GitHub-safe; solid if ever stripped)
    p.append(f'<rect x="{NEO_X}" y="{y-FS+2}" width="8" height="{FS}" fill="{t["art"]}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" '
             f'dur="1.06s" repeatCount="indefinite"/></rect>')
    p.append("</svg>")
    return "\n".join(p)


for theme, fname in (("dark", "dark_mode.svg"), ("light", "light_mode.svg")):
    open(fname, "w", encoding="utf-8", newline="\n").write(render(theme))
    print("wrote", fname)
