#!/usr/bin/env python3
"""Company-wise LeetCode questions, ranked by how often they're reported.

Data: https://github.com/liquidslr/leetcode-company-wise-problems (fetched at
runtime, never redistributed). Standard library only.

Usage:
  questions.py list [QUERY]                    # find a company's exact name
  questions.py get COMPANY [--window W] [--difficulty D] [--topic T]
                           [--limit N] [--format md|json]
      W: 30d | 3m | 6m | older | all   (default: 6m, falling back to all)
      D: easy | medium | hard (comma-separated)
  questions.py topics COMPANY [--window W]     # topic frequency summary

Cache: $CRACKED_HOME/cache (default ~/.cracked/cache), refreshed after 7 days.
Set GITHUB_TOKEN to raise the GitHub API rate limit (60 requests/hour unauthenticated).
Names are matched case- and punctuation-insensitively, with aliases (e.g. "Tata Consultancy
Services" -> tcs, "Facebook" -> Meta). An empty window widens automatically (30d -> 3m -> 6m -> all).
"""
import argparse
import csv
import difflib
import io
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

REPO = "liquidslr/leetcode-company-wise-problems"
RAW = f"https://raw.githubusercontent.com/{REPO}/main"
TREE = f"https://api.github.com/repos/{REPO}/git/trees/main"
WINDOWS = {
    "30d": "1. Thirty Days.csv",
    "3m": "2. Three Months.csv",
    "6m": "3. Six Months.csv",
    "older": "4. More Than Six Months.csv",
    "all": "5. All.csv",
}
WIDEN = {"30d": ["30d", "3m", "6m", "all"], "3m": ["3m", "6m", "all"], "6m": ["6m", "all"],
         "older": ["older", "all"], "all": ["all"]}
COMMITS = f"https://api.github.com/repos/{REPO}/commits?per_page=1"
# Common names that differ from the dataset's folder names. Targets are checked against the
# live company list at runtime; an alias whose target is missing is ignored.
ALIASES = {
    "tataconsultancyservices": "tcs", "tataconsultancy": "tcs", "tcsltd": "tcs",
    "alphabet": "Google", "googlellc": "Google",
    "facebook": "Meta", "metaplatforms": "Meta",
    "aws": "Amazon", "amazonwebservices": "Amazon",
    "hcltech": "HCL", "hcltechnologies": "HCL",
    "cognizanttechnologysolutions": "Cognizant", "cts": "Cognizant",
    "infosyslimited": "Infosys", "wiprolimited": "Wipro",
    "jpmc": "J.P. Morgan", "jpmorganchase": "J.P. Morgan",
    "walmart": "Walmart Labs", "walmartglobaltech": "Walmart Labs",
}
SUFFIXES = ("limited", "ltd", "inc", "pvtltd", "private", "technologies", "india", "corp", "corporation")
TTL = 7 * 24 * 3600
CACHE = os.path.join(os.environ.get("CRACKED_HOME") or os.path.expanduser("~/.cracked"), "cache")


def fetch(url, cache_name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, cache_name)
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < TTL:
        with open(path, encoding="utf-8") as f:
            return f.read()
    headers = {"User-Agent": "cracked-skills"}
    if url.startswith("https://api.github.com/") and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if os.path.exists(path):  # stale cache beats nothing
            return open(path, encoding="utf-8").read()
        raise
    except urllib.error.URLError:
        if os.path.exists(path):
            return open(path, encoding="utf-8").read()
        sys.exit("error: offline and no cached copy. Connect to the internet and retry.")
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return body


def companies():
    body = fetch(TREE, "companies.json")
    data = json.loads(body)
    if data.get("truncated"):
        print("warning: the company list from GitHub was truncated; some companies may be missing", file=sys.stderr)
    return sorted(e["path"] for e in data.get("tree", []) if e["type"] == "tree")


def norm(s):
    return re.sub(r"[^0-9a-z]", "", s.casefold())


def resolve(name):
    names = companies()
    by_norm = {norm(n): n for n in names}
    key = norm(name)
    if key in by_norm:
        return by_norm[key]
    if key in ALIASES and ALIASES[key] in names:
        return ALIASES[key]
    stripped = key
    for suf in SUFFIXES:
        if stripped.endswith(suf) and len(stripped) > len(suf):
            stripped = stripped[: -len(suf)]
    if stripped in by_norm:
        return by_norm[stripped]
    if stripped in ALIASES and ALIASES[stripped] in names:
        return ALIASES[stripped]
    prefix = [n for n in names if norm(n).startswith(key)]
    if len(prefix) == 1:
        return prefix[0]
    close = difflib.get_close_matches(name, names, n=5, cutoff=0.6)
    hint = prefix[:5] or close
    sys.exit(f"error: no exact company '{name}'." + (f" Did you mean: {', '.join(hint)}?" if hint else " Run: questions.py list"))


def rows(company, window):
    order = WIDEN[window]
    for w in order:
        body = fetch(f"{RAW}/{urllib.parse.quote(company)}/{urllib.parse.quote(WINDOWS[w])}",
                     f"{company}--{w}.csv".replace("/", "_"))
        if body and body.strip():
            data = list(csv.DictReader(io.StringIO(body)))
            if data:
                if w != window:
                    print(f"note: no questions in window {window} for {company}; window widened from {window} to {w}", file=sys.stderr)
                return w, data
    return window, []


def freshness(company, window):
    """Footer: when the local cache was fetched, and when the dataset was last updated upstream."""
    path = os.path.join(CACHE, f"{company}--{window}.csv".replace("/", "_"))
    cached = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat() if os.path.exists(path) else "-"
    upstream = "-"
    try:
        body = fetch(COMMITS, "upstream-commit.json")
        upstream = json.loads(body)[0]["commit"]["committer"]["date"][:10]
    except Exception:
        pass
    return f"cached {cached} · dataset last updated upstream {upstream}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list")
    p_list.add_argument("query", nargs="?", default="")
    for name in ("get", "topics"):
        p = sub.add_parser(name)
        p.add_argument("company")
        p.add_argument("--window", choices=list(WINDOWS), default="6m")
        if name == "get":
            p.add_argument("--difficulty", default="")
            p.add_argument("--topic", default="")
            p.add_argument("--limit", type=int, default=25)
            p.add_argument("--format", choices=["md", "json"], default="md")
    a = ap.parse_args()

    if a.cmd == "list":
        q = a.query.lower()
        for n in companies():
            if q in n.lower():
                print(n)
        return

    company = resolve(a.company)
    used, data = rows(company, a.window)
    if not data:
        sys.exit(f"error: the dataset has {company}, but no questions are listed for it in any window. "
                 "Use the company-intel archetype fallback (ARCHETYPES.md) and say the data is missing.")

    if a.cmd == "topics":
        c = Counter(t.strip() for r in data for t in r.get("Topics", "").split(",") if t.strip())
        diff = Counter(r["Difficulty"].title() for r in data)
        print(f"# {company} · window: {used} · {len(data)} questions")
        print("Difficulty: " + ", ".join(f"{k} {v}" for k, v in diff.most_common()))
        print("\n| Topic | Questions |\n|---|---|")
        for t, n in c.most_common(15):
            print(f"| {t} | {n} |")
        print(f"\nSource: github.com/{REPO} · {freshness(company, used)}")
        return

    if a.difficulty:
        want = {d.strip().upper() for d in a.difficulty.split(",")}
        data = [r for r in data if r["Difficulty"].upper() in want]
    if a.topic:
        t = a.topic.lower()
        data = [r for r in data if t in r.get("Topics", "").lower()]
    data.sort(key=lambda r: float(r.get("Frequency") or 0), reverse=True)
    data = data[: a.limit]

    if a.format == "json":
        print(json.dumps({"company": company, "window": used, "requested_window": a.window, "source": f"github.com/{REPO}",
                          "freshness": freshness(company, used), "questions": data}, indent=2))
        return
    print(f"# {company} · window: {used} · top {len(data)} by reported frequency\n")
    print("| # | Difficulty | Title | Freq | Topics | Link |\n|---|---|---|---|---|---|")
    for i, r in enumerate(data, 1):
        print(f"| {i} | {r['Difficulty'].title()} | {r['Title']} | {float(r['Frequency'] or 0):.0f} | {r.get('Topics','')} | {r['Link']} |")
    print(f"\nSource: github.com/{REPO} (community-reported; frequency is relative within this company)")
    print(freshness(company, used))


if __name__ == "__main__":
    main()
