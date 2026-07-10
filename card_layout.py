"""Shared row-layout math for the neofetch card.

Both build_svg.py (initial render) and stats.py (daily value injection) import
this, so the dot-leader lengths that align every row are computed in exactly
one place. All rows are NEO_CHARS monospace characters wide; kv rows are
`. Key: <dots> value` with the value flush at the right edge.

The three GitHub-stats rows additionally share a fixed divider column MID: the
`|` on the Repos and Commits rows and the `(` on the Lines-of-code row all sit
at that column, and each half is padded independently — left halves with dot
leaders, the LOC right half with spaces. That is what keeps the stat block
visually even (Andrew6rant does the same).
"""

NEO_CHARS = 64
MID = 36            # column where `|` / `(` starts on the stat rows


def kv_dots(key, value_len):
    """`. Key: <dots> value` padded to NEO_CHARS."""
    return max(2, NEO_CHARS - len(f". {key}: ") - value_len - 1)


def repos_dots(repos, contrib, stars):
    """`. Repos: <d1> R {Contributed: C} | Stars: <d2> S`
    left half (through the space before `|`) is MID chars; right half fills
    the remaining NEO_CHARS - MID."""
    d1 = max(2, MID - len(". Repos: ") - 1 - len(repos) - len(f" {{Contributed: {contrib}}} "))
    d2 = max(2, (NEO_CHARS - MID) - len("| Stars: ") - 1 - len(stars))
    return d1, d2


def commits_dots(commits, followers):
    """`. Commits: <d1> C | Followers: <d2> F`"""
    d1 = max(2, MID - len(". Commits: ") - 1 - len(commits) - 1)
    d2 = max(2, (NEO_CHARS - MID) - len("| Followers: ") - 1 - len(followers))
    return d1, d2


def loc_dots(net, add, dele):
    """`. Lines of code: <d> N ( A++, <pad>D-- )` — the `(` sits at MID like
    the pipes above it; <pad> spaces absorb value-length changes on the right
    so the closing `)` stays at the right edge."""
    d = max(2, MID - len(". Lines of code: ") - 1 - len(net) - 1)
    pad = max(0, (NEO_CHARS - MID) - len("( ") - len(add) - len("++, ") - len(dele) - len("-- )"))
    return d, pad
