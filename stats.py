#!/usr/bin/env python3
"""Refresh the live stat fields in dark_mode.svg / light_mode.svg.

Lean replacement for the upstream today.py: fetches only what the card shows —
account age, owned/contributed repo counts, total stars, all-time commit
contributions, and followers — with a handful of fast GraphQL queries. It
deliberately does NOT walk every commit for a lines-of-code total (that pass is
what made the old script slow and 502-prone), so a run takes seconds.

Env: ACCESS_TOKEN (a read-only PAT), USER_NAME.
Usage (CI or local): ACCESS_TOKEN=... USER_NAME=adityachaudhary99 python stats.py
"""
import os
import re
import sys
import time
import datetime
import requests
from dateutil.relativedelta import relativedelta

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
      createdAt
      followers { totalCount }
      owned:   repositories(ownerAffiliations:[OWNER]) { totalCount }
      contrib: repositories(ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]) { totalCount }
    } }"""
    return gql(q, {"login": USER})["user"]


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
    for fname in ("dark_mode.svg", "light_mode.svg"):
        s = open(fname, encoding="utf-8").read()
        for k, v in vals.items():
            s = re.sub(r'(id="' + k + r'" fill="[^"]*">)[^<]*(</tspan>)',
                       lambda m, v=v: m.group(1) + v + m.group(2), s)
        open(fname, "w", encoding="utf-8", newline="\n").write(s)
    print("updated:", vals, file=sys.stderr)


if __name__ == "__main__":
    main()
