#!/usr/bin/env python3
"""Refresh the live stat fields in dark_mode.svg / light_mode.svg.

Lean replacement for the upstream today.py: fetches only what the card shows —
account age, owned/contributed repo counts, total stars, all-time commit
contributions, followers, and lines of code. LOC comes from GitHub's
server-computed contributor-stats endpoint (one REST call per repo, no commit
walk) and is cached by `pushed_at` in loc_cache.json, so the first run does the
full pass but a daily rerun only re-fetches repos that changed since.

Env: ACCESS_TOKEN (a read-only PAT), USER_NAME.
Usage (CI or local): ACCESS_TOKEN=... USER_NAME=adityachaudhary99 python stats.py
"""
import os
import re
import sys
import time
import json
import hashlib
import datetime
import requests
from dateutil.relativedelta import relativedelta

import card_layout as cl

TOKEN = os.environ["ACCESS_TOKEN"]
USER = os.environ["USER_NAME"]
HEADERS = {"Authorization": "token " + TOKEN}
API = "https://api.github.com/graphql"


def gql(query, variables, tries=6):
    """POST with backoff on transient 429/5xx and connection drops."""
    err = None
    for attempt in range(tries):
        try:
            r = requests.post(API, json={"query": query, "variables": variables}, headers=HEADERS, timeout=30)
        except requests.exceptions.RequestException as e:
            err = e
            time.sleep(min(30, 2 ** attempt)); continue
        if r.status_code == 200:
            data = r.json()
            if "errors" in data:
                raise SystemExit("GraphQL errors: " + str(data["errors"]))
            return data["data"]
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(30, 2 ** attempt)); continue
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:200]}")
    raise SystemExit(f"gave up after {tries} tries: {err}")


def core():
    q = """query($login:String!){ user(login:$login){
      id
      createdAt
      followers { totalCount }
      owned:   repositories(ownerAffiliations:[OWNER]) { totalCount }
      contrib: repositories(ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]) { totalCount }
    } }"""
    return gql(q, {"login": USER})["user"]


CACHE = "loc_cache.json"


def rest(path, tries=8):
    """GET a REST endpoint with backoff. 202 = GitHub is still computing the
    stat (retry); 204/empty = empty repo. Returns (status, json-or-None)."""
    url = "https://api.github.com" + path
    for attempt in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
        except requests.exceptions.RequestException:
            time.sleep(min(20, 2 ** attempt)); continue
        if r.status_code == 202:                 # stats being generated
            time.sleep(3); continue
        if r.status_code == 204 or not r.text.strip():
            return r.status_code, None
        if r.status_code == 200:
            return 200, r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(20, 2 ** attempt)); continue
        return r.status_code, None               # 403/404/… -> skip this repo
    return 0, None


def repo_loc(full_name):
    """Additions/deletions I authored in one repo, from the server-computed
    contributor-stats endpoint — no commit walk. Returns (added, deleted)."""
    st, data = rest(f"/repos/{full_name}/stats/contributors")
    if st != 200 or not data:
        return 0, 0
    for c in data:
        a = c.get("author") or {}
        if a.get("login", "").lower() == USER.lower():
            return sum(w["a"] for w in c["weeks"]), sum(w["d"] for w in c["weeks"])
    return 0, 0


def rkey(full_name):
    """Cache key for a repo. Hashed because loc_cache.json is committed to a
    PUBLIC repo and the listing includes private repos — their names must not
    leak. A truncated sha1 of the full_name is stable and anonymous."""
    return hashlib.sha1(full_name.encode()).hexdigest()[:12]


def loc():
    """Total lines I authored across every owned repo (public + private).

    Fast + incremental: list owned repos with their `pushed_at`, and only hit
    the (server-computed) contributor-stats endpoint for repos that changed
    since the last run — everything else is reused from loc_cache.json. So the
    first run walks all repos, but a daily rerun only re-fetches the handful I
    actually pushed to. Cache entries for repos the current token can't see are
    RETAINED (not dropped), so private-repo lines survive even if the Action's
    PAT is public-only. Returns (added, deleted, net)."""
    try:
        cache = json.load(open(CACHE, encoding="utf-8"))
    except Exception:
        cache = {}
    # migrate any pre-hash cache (plain full_name keys) to hashed keys
    cache = {(k if "/" not in k else rkey(k)): v for k, v in cache.items()}

    repos, page = [], 1
    while True:
        st, batch = rest(f"/user/repos?affiliation=owner&per_page=100&sort=pushed&page={page}")
        if st != 200 or not batch:
            break
        repos += [(x["full_name"], x["pushed_at"]) for x in batch]
        if len(batch) < 100:
            break
        page += 1

    new_cache = dict(cache)          # keep unlisted (token-invisible) entries
    for full, pushed in repos:
        k = rkey(full)
        c = cache.get(k)
        if not (c and c.get("pushed_at") == pushed):   # changed since last run
            a, d = repo_loc(full)
            new_cache[k] = {"pushed_at": pushed, "add": a, "del": d}

    added = sum(v["add"] for v in new_cache.values())
    deleted = sum(v["del"] for v in new_cache.values())
    json.dump(new_cache, open(CACHE, "w", encoding="utf-8"), indent=0, sort_keys=True)
    return added, deleted, added - deleted


def stars():
    total, cursor = 0, None
    q = """query($login:String!,$cursor:String){ user(login:$login){
      repositories(ownerAffiliations:[OWNER], first:100, after:$cursor){
        nodes { stargazerCount } pageInfo { hasNextPage endCursor } } } }"""
    while True:
        repos = gql(q, {"login": USER, "cursor": cursor})["user"]["repositories"]
        total += sum(n["stargazerCount"] for n in repos["nodes"])
        if not repos["pageInfo"]["hasNextPage"]:
            return total
        cursor = repos["pageInfo"]["endCursor"]


def commits(created):
    """All-time commit contributions: sum contributionsCollection per year."""
    q = """query($login:String!,$from:DateTime!,$to:DateTime!){ user(login:$login){
      contributionsCollection(from:$from,to:$to){
        totalCommitContributions restrictedContributionsCount } } }"""
    total = 0
    year = created.year
    now = datetime.datetime.now(datetime.timezone.utc)
    while year <= now.year:
        frm = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc)
        to = datetime.datetime(year, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)
        if frm < created:
            frm = created
        if to > now:
            to = now
        cc = gql(q, {"login": USER, "from": frm.isoformat(), "to": to.isoformat()})["user"]["contributionsCollection"]
        total += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
        year += 1
    return total


def main():
    u = core()
    created = datetime.datetime.strptime(u["createdAt"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    diff = relativedelta(datetime.datetime.now(datetime.timezone.utc), created)
    vals = {
        "age_data": f"{diff.years} years, {diff.months} months, {diff.days} days",
        "repo_data": f"{u['owned']['totalCount']:,}",
        "contrib_data": f"{u['contrib']['totalCount']:,}",
        "star_data": f"{stars():,}",
        "commit_data": f"{commits(created):,}",
        "follower_data": f"{u['followers']['totalCount']:,}",
    }
    try:
        add, dele, net = loc()
        vals["loc_data"] = f"{net:,}"
        vals["loc_add"] = f"{add:,}"
        vals["loc_del"] = f"{dele:,}"
    except SystemExit as e:
        # LOC is the one heavy pass; if it fails (transient 5xx), keep the
        # other stats and leave LOC pending rather than aborting the whole run.
        print("LOC skipped:", e, file=sys.stderr)
        vals.update(loc_data="—", loc_add="—", loc_del="—")

    # recompute the dot-leaders so every value stays right-aligned (the dots
    # shrink/grow with the value length — same math as build_svg.py)
    d1, d2 = cl.repos_dots(vals["repo_data"], vals["contrib_data"], vals["star_data"])
    c1, c2 = cl.commits_dots(vals["commit_data"], vals["follower_data"])
    vals.update({
        "age_data_dots": "." * cl.kv_dots("Uptime", len(vals["age_data"])),
        "repo_data_dots": "." * d1,
        "star_data_dots": "." * d2,
        "commit_data_dots": "." * c1,
        "follower_data_dots": "." * c2,
        "loc_data_dots": "." * cl.loc_dots(vals["loc_data"], vals["loc_add"], vals["loc_del"]),
    })
    for fname in ("dark_mode.svg", "light_mode.svg"):
        s = open(fname, encoding="utf-8").read()
        for k, v in vals.items():
            s = re.sub(r'(id="' + k + r'" fill="[^"]*">)[^<]*(</tspan>)',
                       lambda m, v=v: m.group(1) + v + m.group(2), s)
        open(fname, "w", encoding="utf-8", newline="\n").write(s)
    print("updated:", vals, file=sys.stderr)


if __name__ == "__main__":
    main()
