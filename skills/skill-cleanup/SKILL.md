---
name: skill-cleanup
description: Audit and clean up the whole AI tooling ecosystem (skills, commands, agents, plugins, MCP servers, hooks, rules) across Claude Code, OpenCode, Codex, Antigravity and projects. Use when the user says skill-cleanup, audit my skills/plugins/MCP, find duplicate or unused skills, centralize skills into ~/.agents, check broken symlinks/junctions, or review what is installed. Supports a full audit or a targeted one (a harness, a directory, a category).
argument-hint: "[full | claude | opencode | codex | antigravity | project <dir> | skills | commands | agents | plugins | mcp | hooks | duplicates | unused]"
---

# /skill-cleanup — audit, review, centralize, verify

`~/.agents/` is the single source of truth. Skills live ONLY in `~/.agents/skills/<name>/`; harnesses see them through
directory junctions (Windows) or native discovery. Never keep two independent copies of a reusable skill.

Arguments: `$ARGUMENTS` (empty = full audit). Work interactively; **never delete, move or disable anything the user has not approved in this run.**

## Mode A — full audit  /  Mode B — targeted audit
1. Run `python ~/.agents/scripts/inventory.py [--target <harness|category>] [--project <dir>]`.
   - Full run refreshes `~/.agents/manifests/{skills,commands,integrations,inventory}.json` and writes `reports/changes-<ts>.md` (added / removed / changed / broken since the last run). Read that report first: on a repeat run only review what changed.
   - Targeted runs (`claude`, `mcp`, `skills`, `project <dir>` ...) print a summary and do NOT overwrite manifests; use `--out file.json` for the full JSON.
2. Read the JSON (not the filesystem again). Only open individual `SKILL.md` files when the user asks or a decision needs it.
3. Read `~/.agents/manifests/decisions.json`: items already decided (keep/remove/...) are not asked again unless they changed.

## Classify every item (evidence, not guesses)
- **Usage:** `usage` in the manifest comes from Claude's `skillUsage` counter (explicit invocations only). `pluginUsage` counts are LOAD counts, not use. Say "no recorded use", never "unused", unless the user confirms.
- **Redundancy:** same name in several real copies, identical descriptions, or overlap with another skill/plugin (e.g. `ecc:*`, `agent-protocols:*` mirror many `~/.agents` skills). Show both paths.
- **Token overhead:** description chars are always in context; SKILL.md bodies only when invoked. Report `desc_chars` and an ESTIMATE (chars / 4). Label estimates as estimates; separate them from disk size.
- **Utility/health:** broken junctions, missing `SKILL.md`, items not in `.skill-lock.json` (hand-made), outdated or incompatible.

## Interactive review (mandatory)
Present batches of at most 8 items. Per significant item give: name + path; what it does; usage evidence; dependencies; overlap; 2-3 reasons to keep; 2-3 reasons not to; estimated overhead; recommendation = one of
`KEEP | MERGE | CENTRALIZE | MOVE TO PROJECT | MOVE TO GLOBAL | DISABLE | REMOVE | INVESTIGATE FURTHER`.
Clearly identical duplicates may be grouped but must list every original path. Ask with AskUserQuestion after each batch. Large plugins (e.g. `ecc`) are ONE entry with counts unless the user asks to drill down. Record every answer in `manifests/decisions.json` (`{item, action, date}`).

## Execute only approved decisions
- **Move/centralize a skill:** `mv <old> ~/.agents/skills/<name>` then `bash ~/.agents/scripts/link-skill.sh <name> [target-skills-dir]` (idempotent junction). Windows junctions need no admin; file symlinks do, so commands are copied by script, not linked.
- **Install third-party skills:** `npx skills add <owner/repo> -g -a claude-code -y -s <name...>`; the CLI COPIES into `~/.claude/skills`, so move each result into `~/.agents/skills` and relink. Never pass `-a '*'` or the old agent list (it recreates deleted harness folders).
- **Remove a skill:** delete it; no backup is needed when the user says remove (their rule). Remove its junctions too (in Git Bash use `cmd //c "rmdir $(cygpath -w <junction>)"`; hand-written `C:\...` paths in double quotes fail; rmdir never touches the source).
- **Edit configs** (settings.json, opencode.jsonc, config.toml, hooks): back up the file to `~/.agents/backups/<ts>/` first, edit minimally, re-validate (JSON/TOML parse).
- **Never** touch credentials, tokens, OAuth files, `auth.json`, `.credentials*`, `.env*`, or print `env`/`args` of MCP servers. Do not delete unrelated data or app-managed folders (`~/.claude/skills/synced`, `~/.claude/plugins/**`, `.system` skills).
- Plugins stay where their harness installed them (moving breaks updates and `${CLAUDE_PLUGIN_ROOT}` hooks); centralize by reference only (`~/.agents/plugins/<name>` junction to the marketplace clone) when asked.
- Do not `git commit`/`git push` `~/.agents` unless the user asks; offer it at the end.

## Policy (user rule)
Never recommend removing a GLOBAL skill just because the current project does not use it; other projects may. Valid reasons: the user asks, an older/duplicate copy, a broken or incompatible skill, or heavy overhead that clearly overlaps another skill. Say which reason applies.

## Harness discovery (verified 2026-11-03; re-verify when a version changes)
| Harness | Global skill paths | Notes |
|---|---|---|
| Claude Code | `~/.claude/skills` | needs a junction per skill |
| OpenCode | `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` | already sees `~/.agents` |
| Codex | `~/.agents/skills` | disable per skill with `[[skills.config]] path=... enabled=false` in `~/.codex/config.toml` |
| Antigravity | `~/.gemini/config/skills` (IDE legacy `~/.gemini/antigravity/skills`) | whole-folder junction to `~/.agents/skills` |
Commands/agents have different native formats per harness; keep each harness's own adapter, never symlink across formats.

## Verify and report
1. Re-run `inventory.py` (full) and confirm `broken_links` is empty and no new duplicates.
2. Confirm discovery: new skills appear in the session skill list / the harness's list command.
3. Write `~/.agents/reports/cleanup-<ts>.md`: what changed, before/after counts, and a **rollback line for every structural change** (e.g. `cmd //c rmdir "C:\Users\<username>\.claude\skills\<name>"`, `mv` back, restore config from backups).
4. Offer: commit `~/.agents` (only if the user says yes).

Idempotent: a second run with nothing new reports "no changes" and asks nothing.
