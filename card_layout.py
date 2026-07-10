"""Shared row-layout math for the neofetch card.

Both build_svg.py (initial render) and stats.py (daily value injection) import
this, so the dot-leader lengths that right-align every value to the same edge
are computed in exactly one place. All rows are NEO_CHARS monospace characters
wide; a row is `. Key: <dots> value [more]`, and the dots stretch so the row
always ends at the right edge — Andrew6rant style.
"""

NEO_CHARS = 60


def leader(prefix, value_len, tail_len=0):
    """Dot count that pads `prefix + dots + ' ' + value + tail` to NEO_CHARS."""
    return max(2, NEO_CHARS - len(prefix) - value_len - tail_len - 1)


def kv_dots(key, value_len):
    return leader(f". {key}: ", value_len)


def repos_dots(repos, contrib, stars):
    """`. Repos: <d1> R {Contributed: C} | Stars: <d2> S` — d2 fixed-ish so the
    Stars block hugs the right edge; d1 absorbs everything else."""
    d2 = max(2, 8 - len(stars))
    tail = len(f" {{Contributed: {contrib}}} | Stars: ") + d2 + 1 + len(stars)
    d1 = max(2, NEO_CHARS - len(". Repos: ") - len(repos) - tail - 1)
    return d1, d2


def commits_dots(commits, followers):
    """`. Commits: <d1> C | Followers: <d2> F`"""
    d2 = max(2, 8 - len(followers))
    tail = len(" | Followers: ") + d2 + 1 + len(followers)
    d1 = max(2, NEO_CHARS - len(". Commits: ") - len(commits) - tail - 1)
    return d1, d2


def loc_dots(net, add, dele):
    """`. Lines of code: <d1> N ( A++, D-- )`"""
    tail = len(f" ( {add}++, {dele}-- )")
    return max(2, NEO_CHARS - len(". Lines of code: ") - len(net) - tail - 1)
