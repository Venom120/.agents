#!/usr/bin/env python3
"""AI tooling inventory (stdlib only, read-only except its own outputs).

Writes ~/.agents/manifests/{skills,commands,integrations}.json and, when a previous
manifest exists, ~/.agents/reports/changes-<UTC timestamp>.md with what changed.

Usage:
  inventory.py                      full audit of every known harness
  inventory.py --target claude      only one harness: claude|opencode|codex|antigravity|agents|project
  inventory.py --target mcp         only a category: skills|commands|agents|plugins|mcp|hooks
  inventory.py --project <dir>      also scan <dir>/.claude, <dir>/.agents, <dir>/.mcp.json
  inventory.py --dry-run            print summary, write nothing
  inventory.py --out <file.json>    write the full inventory JSON there; manifests are NOT touched

Secrets: only names, transports and command basenames are recorded. env, args, headers,
tokens and credential files are never read into the output.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
AGENTS = HOME / ".agents"
MAN = AGENTS / "manifests"
REP = AGENTS / "reports"

SKILL_DIRS = {
    "agents": AGENTS / "skills",
    "claude": HOME / ".claude" / "skills",
    "opencode": HOME / ".config" / "opencode" / "skills",
    "codex": HOME / ".codex" / "skills",
    "antigravity": HOME / ".gemini" / "config" / "skills",
}
COMMAND_DIRS = {
    "agents": AGENTS / "commands",
    "claude": HOME / ".claude" / "commands",
    "opencode": HOME / ".config" / "opencode" / "commands",
}
AGENT_DIRS = {
    "agents": AGENTS / "agents",
    "claude": HOME / ".claude" / "agents",
    "opencode": HOME / ".config" / "opencode" / "agents",
    "copilot": HOME / ".copilot" / "agents",
}
HARNESS_HOMES = {
    "claude": HOME / ".claude", "codex": HOME / ".codex", "opencode": HOME / ".config" / "opencode",
    "antigravity": HOME / ".gemini", "cursor": HOME / ".cursor", "kiro": HOME / ".kiro",
    "copilot": HOME / ".copilot", "kilo": HOME / ".config" / "kilo", "serena": HOME / ".serena",
}
REPARSE = 0x400


def is_link(p: Path) -> bool:
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return p.is_symlink() or bool(getattr(st, "st_file_attributes", 0) & REPARSE)


def link_target(p: Path) -> str | None:
    try:
        return os.readlink(p).replace("\\\\?\\", "")
    except OSError:
        return None


def frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:6000]
    except OSError:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    out: dict = {}
    if not m:
        return out
    key = None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if km:
            key = km.group(1)
            out[key] = km.group(2).strip().strip("'\"").strip(">|").strip()
        elif key and line.startswith((" ", "\t")):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def folder_bytes(p: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(p):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def claude_usage() -> dict:
    d = load_json(HOME / ".claude.json", {})
    out = {}
    for k, v in (d.get("skillUsage") or {}).items():
        if isinstance(v, dict):
            out[k] = {"count": v.get("usageCount"), "last_ms": v.get("lastUsedAt")}
    return out


def scan_skills(harnesses: list[str], extra: list[tuple[str, Path]]) -> list[dict]:
    lock = load_json(AGENTS / ".skill-lock.json", {}).get("skills", {})
    usage = claude_usage()
    items = []
    dirs = [(h, SKILL_DIRS[h]) for h in harnesses if h in SKILL_DIRS] + extra
    for harness, base in dirs:
        if not base.exists():
            continue
        # a whole-folder junction (Antigravity) is one entry, not a copy
        whole = is_link(base)
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            fm = frontmatter(skill_md) if skill_md.exists() else {}
            linked = is_link(entry)
            name = entry.name
            items.append({
                "name": name,
                "harness": harness,
                "path": str(entry),
                "kind": "folder-junction" if whole else ("junction" if linked else "real"),
                "target": link_target(base if whole else entry) if (linked or whole) else None,
                "broken": (linked or whole) and not skill_md.exists(),
                "has_skill_md": skill_md.exists(),
                "description": fm.get("description", ""),
                "desc_chars": len(fm.get("description", "")),
                "skill_md_bytes": skill_md.stat().st_size if skill_md.exists() else 0,
                "folder_bytes": folder_bytes(entry) if (harness == "agents" or not linked) else None,
                "lock_source": (lock.get(name) or {}).get("source"),
                "in_lock": name in lock,
                "usage": usage.get(name),
            })
    return items


def scan_md_dir(dirs: dict, harnesses: list[str], extra: list[tuple[str, Path]], suffixes=(".md",)) -> list[dict]:
    items = []
    for harness, base in [(h, dirs[h]) for h in harnesses if h in dirs] + extra:
        if not base.exists():
            continue
        whole = is_link(base) and harness != "agents"
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in suffixes:
                fm = frontmatter(p)
                items.append({
                    "name": p.stem.replace(".agent", ""), "harness": harness, "path": str(p),
                    "kind": "folder-junction" if whole else ("junction/link" if is_link(p) else "real"),
                    "description": fm.get("description", ""), "bytes": p.stat().st_size,
                })
    return items


def mcp_servers(project: Path | None) -> list[dict]:
    out = []

    def add(src, name, transport, command=None, scope="global"):
        out.append({"name": name, "source": src, "transport": transport,
                    "command": os.path.basename(command) if command else None, "scope": scope})

    cj = load_json(HOME / ".claude.json", {})
    for n, v in (cj.get("mcpServers") or {}).items():
        add("~/.claude.json", n, v.get("type") or "stdio", v.get("command"))
    for proj, v in (cj.get("projects") or {}).items():
        for n, s in (v.get("mcpServers") or {}).items():
            add("~/.claude.json", n, s.get("type") or "stdio", s.get("command"), f"project:{proj}")
    mj = (project or Path.cwd()) / ".mcp.json"
    for n, v in (load_json(mj, {}).get("mcpServers") or {}).items():
        add(str(mj), n, v.get("type") or "stdio", v.get("command") or v.get("url"), "project")
    toml = HOME / ".codex" / "config.toml"
    if toml.exists():
        for m in re.finditer(r"^\[mcp_servers\.([A-Za-z0-9_-]+)\]\s*$", toml.read_text(encoding="utf-8", errors="replace"), re.M):
            add("~/.codex/config.toml", m.group(1), "stdio")
    for src, path in (("~/.gemini/config/mcp_config.json", HOME / ".gemini" / "config" / "mcp_config.json"),
                      ("~/.copilot/mcp-config.json", HOME / ".copilot" / "mcp-config.json")):
        for n, v in (load_json(path, {}).get("mcpServers") or {}).items():
            add(src, n, v.get("type") or "stdio", v.get("command"))
    oc = HOME / ".config" / "opencode" / "opencode.jsonc"
    if oc.exists():
        txt = oc.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'"mcp"\s*:\s*\{', txt)
        if m:
            depth, i = 1, m.end()
            block_start = i
            while i < len(txt) and depth:
                depth += (txt[i] == "{") - (txt[i] == "}")
                i += 1
            for nm in re.finditer(r'^\s{2,8}"([A-Za-z0-9_.-]+)"\s*:\s*\{', txt[block_start:i], re.M):
                add("~/.config/opencode/opencode.jsonc", nm.group(1), "unknown")
    return out


def hooks(project: Path | None) -> list[dict]:
    out = []
    files = [HOME / ".claude" / "settings.json", HOME / ".claude" / "settings.local.json"]
    if project:
        files += [project / ".claude" / "settings.json", project / ".claude" / "settings.local.json"]
    for f in files:
        for ev, arr in (load_json(f, {}).get("hooks") or {}).items():
            for a in arr:
                for h in a.get("hooks", []):
                    cmd = h.get("command") or h.get("type", "")
                    out.append({"source": str(f), "event": ev, "matcher": a.get("matcher", ""),
                                "command": re.sub(r"\s+", " ", cmd)[:60]})
    return out


def plugins() -> list[dict]:
    out = []
    ip = load_json(HOME / ".claude" / "plugins" / "installed_plugins.json", {})
    enabled = load_json(HOME / ".claude" / "settings.json", {}).get("enabledPlugins", {})
    for k, v in (ip.get("plugins", ip)).items():
        v0 = v[0] if isinstance(v, list) else v
        root = Path(v0.get("installPath", ""))
        count = lambda pat: len(list(root.glob(pat))) if root.exists() else 0
        out.append({"name": k, "harness": "claude", "version": v0.get("version"), "enabled": enabled.get(k),
                    "skills": count("skills/*/SKILL.md"), "commands": count("commands/**/*.md"),
                    "agents": count("agents/*.md"), "hooks": (root / "hooks" / "hooks.json").exists()})
    toml = HOME / ".codex" / "config.toml"
    if toml.exists():
        for m in re.finditer(r'^\[plugins\."([^"]+)"\]', toml.read_text(encoding="utf-8", errors="replace"), re.M):
            out.append({"name": m.group(1), "harness": "codex"})
    return out


def duplicates(skills: list[dict]) -> list[dict]:
    allowed = set(load_json(MAN / "decisions.json", {}).get("allowed_duplicates", []))
    skills = [s for s in skills if s["name"] not in allowed]
    by_name: dict[str, list[dict]] = {}
    for s in skills:
        by_name.setdefault(s["name"], []).append(s)
    dups = []
    for name, rows in by_name.items():
        real = [r for r in rows if r["kind"] == "real"]
        if len(real) > 1:
            dups.append({"name": name, "kind": "multiple real copies", "paths": [r["path"] for r in real]})
    seen: dict[str, str] = {}
    for s in skills:
        if s["harness"] != "agents" or not s["description"]:
            continue
        h = hashlib.sha1(s["description"].encode()).hexdigest()
        if h in seen and seen[h] != s["name"]:
            dups.append({"name": s["name"], "kind": "same description as", "paths": [seen[h]]})
        seen.setdefault(h, s["name"])
    return dups


def diff_report(old: dict, new: dict) -> str:
    lines = []

    def keyed(d, section, key):
        return {key(i): i for i in d.get(section, [])}

    for section, key in (("skills", lambda i: f"{i['harness']}:{i['name']}"),
                         ("commands", lambda i: f"{i['harness']}:{i['name']}"),
                         ("agents", lambda i: f"{i['harness']}:{i['name']}"),
                         ("plugins", lambda i: f"{i['harness']}:{i['name']}"),
                         ("mcp", lambda i: f"{i['source']}:{i['name']}")):
        a, b = keyed(old, section, key), keyed(new, section, key)
        added, removed = sorted(set(b) - set(a)), sorted(set(a) - set(b))
        changed = sorted(k for k in set(a) & set(b) if {x: a[k].get(x) for x in ("kind", "target", "version", "broken", "enabled")}
                         != {x: b[k].get(x) for x in ("kind", "target", "version", "broken", "enabled")})
        if added or removed or changed:
            lines.append(f"### {section}")
            lines += [f"- added: {k}" for k in added] + [f"- removed: {k}" for k in removed] + [f"- changed: {k}" for k in changed]
    return "\n".join(lines) or "No changes since the previous inventory."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="all")
    ap.add_argument("--project")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    project = Path(a.project).resolve() if a.project else None
    cats = {"skills", "commands", "agents", "plugins", "mcp", "hooks"}
    harness_names = {"claude", "opencode", "codex", "antigravity", "agents", "copilot", "project"}
    t = a.target.lower()
    want_cats = cats if t in ("all", *harness_names) else ({t} if t in cats else cats)
    hs = [h for h in SKILL_DIRS] if t in ("all",) or t in cats else ([t] if t in SKILL_DIRS else [])
    extra_s, extra_c, extra_a = [], [], []
    if project or t == "project":
        p = project or Path.cwd()
        extra_s = [("project", p / ".claude" / "skills"), ("project", p / ".agents" / "skills")]
        extra_c = [("project", p / ".claude" / "commands")]
        extra_a = [("project", p / ".claude" / "agents")]
    inv = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "target": t}
    inv["harnesses"] = {h: p.exists() for h, p in HARNESS_HOMES.items()}
    if "skills" in want_cats:
        inv["skills"] = scan_skills(hs, extra_s)
        inv["duplicates"] = duplicates(inv["skills"])
        inv["broken_links"] = [s["path"] for s in inv["skills"] if s["broken"]]
    if "commands" in want_cats:
        ch = [h for h in COMMAND_DIRS] if t in ("all", *cats) else ([t] if t in COMMAND_DIRS else [])
        inv["commands"] = scan_md_dir(COMMAND_DIRS, ch, extra_c)
        # real command files in a harness folder that is not linked to ~/.agents/commands (project scope is intentional)
        inv["loose_commands"] = [c["path"] for c in inv["commands"] if c["kind"] == "real" and c["harness"] not in ("agents", "project")]
    if "agents" in want_cats:
        ah = [h for h in AGENT_DIRS] if t in ("all", *cats) else ([t] if t in AGENT_DIRS else [])
        inv["agents"] = scan_md_dir(AGENT_DIRS, ah, extra_a, suffixes=(".md",))
    if "plugins" in want_cats:
        inv["plugins"] = plugins()
    if "mcp" in want_cats:
        inv["mcp"] = mcp_servers(project)
    if "hooks" in want_cats:
        inv["hooks"] = hooks(project)

    summary = {k: len(v) for k, v in inv.items() if isinstance(v, list)}
    print(json.dumps({"summary": summary, "broken_links": inv.get("broken_links", []), "loose_commands": inv.get("loose_commands", []),
                      "duplicates": len(inv.get("duplicates", []))}, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(inv, indent=1), encoding="utf-8")
        print("wrote", a.out)
        return 0
    if a.dry_run or t != "all":
        if t != "all" and not a.dry_run:
            print("targeted audit: manifests not overwritten (run a full audit to refresh them)")
        return 0
    MAN.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    latest = MAN / "inventory.json"
    old = load_json(latest, {})
    for name, keys in (("skills", ["skills", "duplicates", "broken_links"]), ("commands", ["commands", "loose_commands", "agents"]),
                       ("integrations", ["harnesses", "plugins", "mcp", "hooks"])):
        (MAN / f"{name}.json").write_text(json.dumps({k: inv.get(k) for k in ["generated", *keys]}, indent=1), encoding="utf-8")
    latest.write_text(json.dumps(inv, indent=1), encoding="utf-8")
    if old:
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (REP / f"changes-{stamp}.md").write_text(f"# Inventory changes {stamp}\n\n{diff_report(old, inv)}\n", encoding="utf-8")
        print("change report: reports/" + f"changes-{stamp}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
