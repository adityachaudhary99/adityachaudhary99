#!/usr/bin/env python3
"""Generate dark_mode.svg + light_mode.svg for the profile README.

Left panel  : block-shade ASCII (" ░▒▓█") of assets/portrait.jpg, generated
              inline and sized so its row count == the neofetch line count, so
              both columns are exactly the same height.
Right panel : neofetch card in the Andrew6rant layout — ". Key: ....... value"
              with keys left-aligned and values aligned to one column via
              dot-leaders. Full-width section rules; no cursor.

GitHub-safe (learned the hard way): GitHub strips <style> + CSS animation from
README SVGs, so every element has an inline `fill` and is visible by default
(a template that hides text behind stripped CSS renders EMPTY). Stat values
carry the ids stats.py fills with live data.

Deps: Pillow (local only — the Action runs stats.py, which needs no PIL).
Run: python build_svg.py    (then stats.py re-injects the live numbers)
"""
from html import escape
from PIL import Image, ImageOps

RAMP = " ░▒▓█"          # light -> dark; try " .:-=+*#%@" for classic char-ramp
ART_COLS = 46

FIELDS = [
    ("head", "cal", "@github"),
    ("kv", "Site", "thecalendre.tech"),
    ("kv", "Uptime", ("age_data", "on GitHub since 2021")),
    ("kv", "Focus", "distributed systems · AI-agent infra"),
    ("kv", "Editor", "VS Code · Cursor"),
    ("kv", "Harness", "Claude Code · Codex"),
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
X0 = 22
VAL_COL = 22            # column (chars) where values begin
TOP = 34
NEO_CHARS = 60

TEXT_ROWS = len(FIELDS)                       # one line-slot per entry
NEO_X = X0 + int(ART_COLS * FS * 0.62) + 30
WIDTH = NEO_X + int(NEO_CHARS * FS * 0.62) + 16
HEIGHT = TOP + TEXT_ROWS * LH + 20
FONT = "ui-monospace,'JetBrains Mono','Cascadia Code',Consolas,monospace"


def make_art(cols, rows):
    im = Image.open("assets/portrait.jpg").convert("L")
    w, h = im.size
    im = im.crop((int(w*0.14), int(h*0.06), int(w*0.86), int(h*0.58)))
    im = ImageOps.autocontrast(im, cutoff=2).resize((cols, rows))  # fit to text height
    px = im.load()
    return ["".join(RAMP[int((1 - px[x, y] / 255.0) * (len(RAMP) - 1))] for x in range(cols))
            for y in range(rows)]


def ts(text, fill, tid=None):
    idattr = f' id="{tid}"' if tid else ""
    return f'<tspan{idattr} fill="{fill}">{escape(text)}</tspan>'


def kv_row(t, key, val, y):
    ndots = max(2, VAL_COL - len(f'. {key}: '))
    row = f'<tspan x="{NEO_X}" y="{y}">' + ts(". ", t["dim"]) + ts(key, t["key"]) + ts(": ", t["dim"])
    if isinstance(val, tuple):
        vid, vtext = val
        row += ts("." * ndots + " ", t["cc"], vid + "_dots") + ts(vtext, t["val"], vid)
    else:
        row += ts("." * ndots + " ", t["cc"]) + ts(val, t["val"])
    return row + "</tspan>"


def stat_row(t, label, y, extra):
    nd = max(2, VAL_COL - len(f'. {label}: '))
    head = (f'<tspan x="{NEO_X}" y="{y}">' + ts(". ", t["dim"]) + ts(label, t["key"]) + ts(": ", t["dim"]))
    return head + extra(nd) + "</tspan>"


def render(theme, art):
    t = THEMES[theme]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}px" height="{HEIGHT}px" '
         f'font-family="{FONT}" font-size="{FS}px">']
    p.append(f'<rect width="{WIDTH}px" height="{HEIGHT}px" fill="{t["bg"]}" rx="14"/>')
    p.append(f'<rect x="6" y="6" width="{WIDTH-12}px" height="{HEIGHT-12}px" fill="none" '
             f'stroke="{t["frame"]}" stroke-width="1" rx="10"/>')
    p.append('<text xml:space="preserve">')

    for i, line in enumerate(art):
        p.append(f'<tspan x="{X0}" y="{TOP + i*LH}" fill="{t["art"]}">{escape(line)}</tspan>')

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
            rule = "─" * max(4, NEO_CHARS - len(f[1]) - 3)
            p.append(f'<tspan x="{NEO_X}" y="{y}">' + ts("─ ", t["cc"])
                     + f'<tspan fill="{t["fg"]}" font-weight="bold">{escape(f[1])}</tspan>'
                     + ts(" " + rule, t["cc"]) + "</tspan>")
        elif kind == "kv":
            p.append(kv_row(t, f[1], f[2], y))
        elif kind == "stat_repos":
            p.append(stat_row(t, "Repos", y, lambda nd: (
                ts("." * nd + " ", t["cc"], "repo_data_dots") + ts("0", t["val"], "repo_data")
                + ts(" {", t["dim"]) + ts("Contributed", t["key"]) + ts(": ", t["dim"]) + ts("0", t["val"], "contrib_data")
                + ts("} | ", t["dim"]) + ts("Stars", t["key"]) + ts(" ... ", t["cc"], "star_data_dots") + ts("0", t["val"], "star_data"))))
        elif kind == "stat_commits":
            p.append(stat_row(t, "Commits", y, lambda nd: (
                ts("." * nd + " ", t["cc"], "commit_data_dots") + ts("0", t["val"], "commit_data")
                + ts(" | ", t["dim"]) + ts("Followers", t["key"]) + ts(" .. ", t["cc"], "follower_data_dots") + ts("0", t["val"], "follower_data"))))
        elif kind == "stat_loc":
            p.append(stat_row(t, "Lines of code", y, lambda nd: (
                ts("." * nd + " ", t["cc"], "loc_data_dots") + ts("0", t["val"], "loc_data")
                + ts(" ( ", t["dim"]) + ts("0", t["add"], "loc_add") + ts("++", t["add"]) + ts(", ", t["dim"])
                + ts(" ", t["cc"], "loc_del_dots") + ts("0", t["dele"], "loc_del") + ts("--", t["dele"]) + ts(" )", t["dim"]))))
        y += LH
    p.append("</text></svg>")
    return "\n".join(p)


art = make_art(ART_COLS, TEXT_ROWS)
open("assets/portrait.ascii.txt", "w", encoding="utf-8", newline="\n").write("\n".join(art) + "\n")
for theme, fname in (("dark", "dark_mode.svg"), ("light", "light_mode.svg")):
    open(fname, "w", encoding="utf-8", newline="\n").write(render(theme, art))
    print("wrote", fname)
