#!/usr/bin/env python3
"""Generate dark_mode.svg + light_mode.svg for the profile README.

Left panel  : detail-segmented ASCII art of assets/portrait.jpg rendered at a
              smaller font size than the text (~78x46 chars) so the figure has
              real resolution — the man reads solid in dense chars, the sky is
              a sparse star scatter, the rocks are dim texture. Plain
              brightness fails on this image (the rocks are the darkest thing,
              so "dark = ink" buries the mid-gray man); we key the figure off
              DETAIL (high-pass = |image - blur|) instead.
Right panel : neofetch card, Andrew6rant layout — every row is exactly
              card_layout.NEO_CHARS monospace chars, `. Key: <dots> value`,
              with dot-leaders stretched so ALL values right-align to the same
              edge. stats.py recomputes the dots when it injects live values.

GitHub-safe (learned the hard way): GitHub strips <style> + CSS animation from
README SVGs, so every element has an inline `fill` and is visible by default
(a template that hides text behind stripped CSS renders EMPTY).

Deps: Pillow (local only — the Action runs stats.py, which needs no PIL).
Run: python build_svg.py    (then stats.py re-injects the live numbers)
"""
from html import escape
from PIL import Image, ImageFilter
import PIL.ImageChops as ImageChops
import card_layout as cl

# ---- text panel ----
FS = 14
LH = 19
X0 = 22
TOP = 34
FONT = "ui-monospace,'JetBrains Mono','Cascadia Code',Consolas,monospace"

# ---- art panel (own, smaller font -> ~2x the resolution of the text grid) ----
AFS = 9
ALH = 9.5
ART_COLS = 78

# seed values — stats.py replaces these (and their dot-leaders) with live data
SEED = dict(age="4 years, 8 months, 21 days", repos="91", contrib="97",
            stars="11", commits="991", followers="44",
            loc="323,322", loc_add="1,926,149", loc_del="1,602,827")

FIELDS = [
    ("head", "cal", "@github"),
    ("kv", "Site", "thecalendre.tech"),
    ("dkv", "Uptime", "age_data", SEED["age"]),
    ("kv", "Focus", "distributed systems, AI-agent infra"),
    ("kv", "Editor", "VS Code, Cursor"),
    ("kv", "Harness", "Claude Code, Codex"),
    ("kv", "Langs", "Go, Rust, TypeScript, Python"),
    ("kv", "Infra", "Docker, Terraform, Airflow"),
    ("blank",),
    ("kv", "Ships.CLI", "yank, agentop"),
    ("kv", "Ships.Web", "0-suite, contextdev"),
    ("kv", "Ships.Agents", "smartloop, Hermes"),
    ("blank",),
    ("kv", "Hobbies.HW", "rooted OnePlus 7 Pro, Magisk + Termux"),
    ("kv", "Hobbies.SW", "on-device llama.cpp, offline wiki + maps"),
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

TEXT_ROWS = len(FIELDS)
PANEL_H = TEXT_ROWS * LH
ART_ROWS = int(PANEL_H / ALH)
ART_W = int(ART_COLS * AFS * 0.6)
NEO_X = X0 + ART_W + 30
WIDTH = NEO_X + int(cl.NEO_CHARS * FS * 0.62) + 16
HEIGHT = TOP + PANEL_H + 20


def h2(x, y):
    """Small deterministic 2-D hash -> 0..96 (no runtime randomness; must be
    stable across rebuilds). Mixed constants avoid the visible moiré that a
    plain linear hash paints across the scatter regions."""
    n = (x * 374761393 + y * 668265263) ^ (x * y * 362437)
    n = (n ^ (n >> 13)) * 1274126177
    return (n ^ (n >> 16)) % 97


def make_art(cols, rows):
    MAN = " .:-=+*#%@"
    base = Image.open("assets/portrait.jpg").convert("L")
    w, h = base.size
    base = base.crop((int(w*0.10), int(h*0.05), int(w*0.90), int(h*0.62)))
    hi = base.resize((cols*3, rows*3))
    tone = hi.resize((cols, rows))
    detail = ImageChops.difference(hi, hi.filter(ImageFilter.GaussianBlur(3))).resize((cols, rows))
    tp, dp = tone.load(), detail.load()

    out = [[" "]*cols for _ in range(rows)]
    for y in range(rows):
        for x in range(cols):
            v, d = tp[x, y], dp[x, y]
            if d >= 12:
                # the figure: brighter -> denser char, floored so he stays solid
                out[y][x] = MAN[min(4 + int((v/255.0)*5), 9)]
            elif v < 48:
                # black rock -> dim scatter texture
                r = h2(x, y)
                out[y][x] = ":" if r < 16 else ("." if r < 38 else " ")
            else:
                # smooth sky -> sparse stars, thinning toward the horizon
                r = h2(x, y)
                th = 5 if y < rows*0.35 else (3 if y < rows*0.55 else 2)
                if r < th:
                    out[y][x] = "*" if r == 1 else "."
    return ["".join(r) for r in out]


def ts(text, fill, tid=None):
    idattr = f' id="{tid}"' if tid else ""
    return f'<tspan{idattr} fill="{fill}">{escape(text)}</tspan>'


def row_open(y):
    return f'<tspan x="{NEO_X}" y="{y}">'


def kv_row(t, key, val, y, vid=None):
    dots = cl.kv_dots(key, len(val))
    r = row_open(y) + ts(". ", t["dim"]) + ts(key, t["key"]) + ts(": ", t["dim"])
    r += ts("." * dots, t["cc"], vid + "_dots" if vid else None) + ts(" ", t["cc"])
    r += ts(val, t["val"], vid)
    return r + "</tspan>"


def render(theme, art):
    t = THEMES[theme]
    s = SEED
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}px" height="{HEIGHT}px" '
         f'font-family="{FONT}" font-size="{FS}px">']
    p.append(f'<rect width="{WIDTH}px" height="{HEIGHT}px" fill="{t["bg"]}" rx="14"/>')
    p.append(f'<rect x="6" y="6" width="{WIDTH-12}px" height="{HEIGHT-12}px" fill="none" '
             f'stroke="{t["frame"]}" stroke-width="1" rx="10"/>')

    # art gets its own <text> so it can run at the smaller font size
    p.append(f'<text xml:space="preserve" font-size="{AFS}px">')
    for i, line in enumerate(art):
        p.append(f'<tspan x="{X0}" y="{TOP + i*ALH:g}" fill="{t["art"]}">{escape(line)}</tspan>')
    p.append('</text>')

    p.append('<text xml:space="preserve">')
    y = TOP + 6
    for f in FIELDS:
        kind = f[0]
        if kind == "blank":
            y += LH; continue
        if kind == "head":
            _, name, tail = f
            rule = "─" * max(4, cl.NEO_CHARS - len(name) - len(tail) - 1)
            p.append(row_open(y)
                     + f'<tspan fill="{t["fg"]}" font-weight="bold">{escape(name)}</tspan>'
                     + ts(tail, t["dim"]) + ts(" " + rule, t["cc"]) + "</tspan>")
        elif kind == "rule":
            rule = "─" * max(4, cl.NEO_CHARS - len(f[1]) - 3)
            p.append(row_open(y) + ts("─ ", t["cc"])
                     + f'<tspan fill="{t["fg"]}" font-weight="bold">{escape(f[1])}</tspan>'
                     + ts(" " + rule, t["cc"]) + "</tspan>")
        elif kind == "kv":
            p.append(kv_row(t, f[1], f[2], y))
        elif kind == "dkv":
            p.append(kv_row(t, f[1], f[3], y, vid=f[2]))
        elif kind == "stat_repos":
            d1, d2 = cl.repos_dots(s["repos"], s["contrib"], s["stars"])
            p.append(row_open(y)
                     + ts(". ", t["dim"]) + ts("Repos", t["key"]) + ts(": ", t["dim"])
                     + ts("." * d1, t["cc"], "repo_data_dots") + ts(" ", t["cc"])
                     + ts(s["repos"], t["val"], "repo_data")
                     + ts(" {", t["dim"]) + ts("Contributed", t["key"]) + ts(": ", t["dim"])
                     + ts(s["contrib"], t["val"], "contrib_data")
                     + ts("} ", t["dim"])
                     + ts("| ", t["dim"]) + ts("Stars", t["key"]) + ts(": ", t["dim"])
                     + ts("." * d2, t["cc"], "star_data_dots") + ts(" ", t["cc"])
                     + ts(s["stars"], t["val"], "star_data") + "</tspan>")
        elif kind == "stat_commits":
            d1, d2 = cl.commits_dots(s["commits"], s["followers"])
            p.append(row_open(y)
                     + ts(". ", t["dim"]) + ts("Commits", t["key"]) + ts(": ", t["dim"])
                     + ts("." * d1, t["cc"], "commit_data_dots") + ts(" ", t["cc"])
                     + ts(s["commits"], t["val"], "commit_data") + ts(" ", t["cc"])
                     + ts("| ", t["dim"]) + ts("Followers", t["key"]) + ts(": ", t["dim"])
                     + ts("." * d2, t["cc"], "follower_data_dots") + ts(" ", t["cc"])
                     + ts(s["followers"], t["val"], "follower_data") + "</tspan>")
        elif kind == "stat_loc":
            d1, pad = cl.loc_dots(s["loc"], s["loc_add"], s["loc_del"])
            p.append(row_open(y)
                     + ts(". ", t["dim"]) + ts("Lines of code", t["key"]) + ts(": ", t["dim"])
                     + ts("." * d1, t["cc"], "loc_data_dots") + ts(" ", t["cc"])
                     + ts(s["loc"], t["val"], "loc_data") + ts(" ", t["cc"])
                     + ts("( ", t["dim"]) + ts(s["loc_add"], t["add"], "loc_add") + ts("++", t["add"])
                     + ts(", ", t["dim"]) + ts(" " * pad, t["cc"], "loc_pad")
                     + ts(s["loc_del"], t["dele"], "loc_del") + ts("--", t["dele"])
                     + ts(" )", t["dim"]) + "</tspan>")
        y += LH
    p.append("</text></svg>")
    return "\n".join(p)


art = make_art(ART_COLS, ART_ROWS)
open("assets/portrait.ascii.txt", "w", encoding="utf-8", newline="\n").write("\n".join(art) + "\n")
for theme, fname in (("dark", "dark_mode.svg"), ("light", "light_mode.svg")):
    open(fname, "w", encoding="utf-8", newline="\n").write(render(theme, art))
    print("wrote", fname)
