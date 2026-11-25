# Desktop-agent setup and sync

This file is the entry point for a user's laptop AI agent. Attach it to the
agent after cloning or pulling this repository and say:

> Read `SETUP.md`, discover the AI harnesses installed on this laptop, ask me
> which detected harnesses to configure, then run the sync pipeline.

The agent must ask before installing or changing anything. It must not print,
copy, or modify credentials, OAuth files, `.env` files, or MCP secrets.

## Pipeline

```text
discover harnesses
        |
ask which supported harnesses to configure
        |
sync source skills, commands, and Claude mods
        |
refresh inventory and INDEX.md
        |
check broken links and duplicates
        |
restart selected desktop agents
```

## 1. Clone or update the complete checkout

After cloning, initialize and pull every Git submodule before discovering or
syncing harnesses:

```powershell
git submodule sync --recursive
git submodule update --init --recursive
```

The sync pipeline then detects nested `SKILL.md` files inside submodule
repositories, copies them into real canonical `skills/<name>` directories,
and links those canonical skills to the selected harnesses.

For an existing checkout, update the parent repository and its submodules
together:

```powershell
git pull --recurse-submodules
git submodule sync --recursive
git submodule update --init --recursive
```

Run these commands on `local`. The agent must not switch to `main` for normal
work; use the documented `cp` flow only when the user explicitly asks to
commit and push.

## 2. Discover and ask

Run this read-only discovery from the repository root:

```powershell
python scripts/sync.py
```

The supported harness targets are:

| Harness | Detection path | Installation behavior |
|---|---|---|
| Claude Code | `~/.claude` | Per-skill links, shared commands, Claude mods |
| OpenCode | `~/.config/opencode` | Per-skill links and shared commands |
| Codex | `~/.codex` | Reads `~/.agents/skills` directly |
| Antigravity | `~/.gemini` | Whole-folder link at `~/.gemini/config/skills` |

The discovery also reports common unsupported or not-yet-configured harness
directories such as Cursor, Kiro, and Copilot. Do not configure those unless a
future adapter is documented here.

Ask the user which detected supported harnesses to configure. Do not infer
consent from detection alone. Example answer: `claude,codex,antigravity`.

## 3. Sync after confirmation

Run the approved selection:

```powershell
python scripts/sync.py --harness claude,codex,antigravity --apply
```

Replace the harness list with the user's answer. The sync is idempotent:

- source skills are real directories at `skills/<name>/SKILL.md`;
- canonical skills and mods under `.agents` are never symlinks or junctions;
- Claude and OpenCode receive per-skill links;
- Codex reads the shared source directly;
- Antigravity receives a whole-folder link;
- shared commands are linked for Claude and OpenCode;
- every tracked mod under `mods/<name>` is linked to Claude's
  `~/.claude/mods/<name>` as a complete directory;
- existing real directories are never overwritten.

A Claude mod is not a skill. Its `.claude-plugin/plugin.json` and any
`hooks/hooks.json` must remain in the linked directory. Linking a skill alone
does not activate Claude hooks. Restart the affected desktop agents after a
successful sync.

## 4. Verify and keep the index current

The apply pipeline runs the read-only inventory and regenerates [INDEX.md](INDEX.md).
The index is the checklist of every source skill and tracked mod. After adding
or removing a skill, command, or mod:

```powershell
python scripts/sync.py --harness <confirmed-harnesses> --apply
```

To refresh only the tracked checklist without changing local harness links:

```powershell
python scripts/sync.py --refresh-index
```

Then inspect the generated inventory for broken links or duplicates:

```powershell
python scripts/inventory.py --dry-run
```

If the repository was updated with Git, pull first, then repeat this sync. The
laptop agent can be asked either to read this file from the checkout or to
receive the file as an attachment.

## 5. Source and branch safety

Keep the checkout at `~/.agents`. The `local` branch is private and is never
pushed; `main` is the sanitized public branch. A laptop sync may read and link
files, but it must not commit or push unless the user separately asks.

Never put secrets in this repository. External plugin checkouts should remain
ignored unless their distributable source is intentionally added under the
documented source directories. Copy imported skill directories into
`.agents/skills`; do not link them there.

See [README.md](README.md) for the skill/mod distinction and
[AGENTS.md](AGENTS.md) for the full operating rules.
