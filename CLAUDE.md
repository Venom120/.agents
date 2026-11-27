# Global instructions (every project)

Canonical file: `~/.agents/CLAUDE.md`; `~/.claude/CLAUDE.md` only imports it. A project's own instructions add to these.

## Owner rules (every project; these win over the Ruflo section below)

- **Ask, don't assume.** Anything new, unclear or with more than one reasonable fix: ask, recommended option first, then wait.
- **Change size:** for every task that changes code, ask surgical, broader or ambitious, unless the request says. Smallest-diff skills apply only to surgical.
- **Skills:** invoke every matching installed skill without being asked and name them in the report. They never override approvals, test cadence or git rules. Ask before one connects a service, signs in, uploads, spends, downloads or installs.
- **Planning:** whenever `PLAN.md` / `TODO.md` is drafted or revised, run the planning pipeline (`AGENTS.md` §3, or the project's `skill-pipeline.md`): understand → ask size and open questions → design for large work → `be-ambitious` ideas as optional items → spec if unclear → domain skills → write with `Skills:` per phase → offer Plannotator → wait for approval.
- **Browser:** `agent-browser` CLI on localhost; never Playwright.
- **Permissions:** without the permission, don't render the page or control, sidebar entry included.
- **Tests:** targeted tests while iterating. Full suite and validator only with approval, never chained, never killed mid-run.
- **Progress:** when asked if something is done, check the real process and output; answer briefly in plain language.

## Git, versions and publishing (never act without asking)
- Never run `git commit`, `git push`, `git tag`, create/publish a GitHub repo or release, bump a version number, or run `claude plugin update/install` unless the user explicitly asked for that action in the current conversation. Do the edits, show what changed, and ask first.
- Approval for one commit/push/version bump does not carry over to later changes.
- After editing code, stop and let the user review; do not "ship" it on your own.

## Files and safety
- Do what was asked. Read a file before editing it; prefer editing over creating; no documentation files unless asked.
- Never commit secrets, credentials or `.env` files. Validate input at system boundaries.

## graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

## Ruflo
- For multi-file or complex work, use ToolSearch to find ruflo MCP tools (`memory_search`, `memory_store`, `hooks_route`, `guidance_recommend`) and check `[INTELLIGENCE]` suggestions in system reminders. If Ruflo is unavailable, carry on without it.
- Ruflo coordinates; you still do the work. A lease, claim or recommendation never authorises a side effect.
- Start swarms or agent teams only when the user asks. Then: one writer per worktree with its own file scope, read-only research may run in parallel, and no child gets more tools, secrets, spend or delegation than its parent.

@~/.claude/RTK.md
