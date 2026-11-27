---
name: init-playbook
description: Analyze a repository and generate or update its CLAUDE.md / AGENTS.md as a skill-and-MCP-aware execution playbook, including a re-runnable "Available AI Tooling & Recommended Workflows" section that recommends only the installed skills, commands, MCP servers and plugins that fit the project. Use when starting or refreshing AI setup for a repo, or when project requirements change.
argument-hint: "<repo path>  (default: current directory)"
---

# TASK: project-aware AI playbook + tooling recommendations

Repo path: `$ARGUMENTS` (empty = current working directory; do not ask for a path).
**Ask before writing anything. Read-only until the user approves.** Never print secrets (MCP env/args/headers, tokens).

## Step 1 — Inventory (read-only)
1. **Project analysis:** README, dependency manifests (package.json, req.txt/pyproject, go.mod, Cargo.toml, ...), folder tree, build/test/lint/run commands, test framework, CI, Docker/compose/deploy files, DB/migrations, frontend framework, existing docs. Work out what the project actually DOES and its main flows, not just the stack.
2. **Instruction files:** existing `CLAUDE.md`, `AGENTS.md`, `.claude/` (agents, commands, skills, rules, hooks, settings), `.agents/`, `.mcp.json`, `.cursor/`, `.codex/`. Note hard rules already present and any existing marked tooling section.
3. **Installed tooling (real, not assumed):** run `python ~/.agents/scripts/inventory.py --project <repo> --out <scratch>/inv.json` (never touches global manifests) and read it: skills in `~/.agents/skills` (names + descriptions; read a SKILL.md only if relevance is unclear), commands, agents, plugins, MCP servers (names/transport only), hooks. Also check harness-specific skill folders for skills not yet centralized (flag them for `/skill-cleanup`).
4. **Gap search:** use `find-skills` (`npx skills find <keywords>`) with the stack/domain keywords; shortlist up to 5 skills worth installing. **Do not install anything.**

## Step 2 — Recommendations (derived from step 1)
Recommend only items with a clear use in THIS repo; do not list everything installed.
- **Skills** already available and relevant (name + path + one-line why); redundant ones; project-specific skills worth creating.
- **Session team** (`session-teams`): only if the repo has 2+ recurring roles with separate outputs (e.g. research / build / review). Name each role, its output file, who it reports to and what it may touch; otherwise say "single session".
- **Model routing** (`cost-routing`): map this repo's task types to `haiku` / `sonnet` / `opus`; list agent types worth a `model:` pin. The routing mod is opt-in: recommend it, never enable it.
- **Commands** for development, testing, debugging, docs, code review, deployment, maintenance.
- **MCP servers:** installed-and-relevant vs. would-need-install/config (e.g. GitHub for repo/PR flows, DB for projects with a database, browser for web apps, docs MCP for framework references, design MCP for design tools). Mark which need credentials; never show them.
- **Plugins/extensions:** only where they add something not already covered.
- **Skill pipeline:** the draft prompt → skills map for this repo (see Step 4), including newly installed skills since the pipeline was last written. Skills that open a browser UI and wait, cost money or send data outside are listed as "ask first".
- **Missing tooling** and overlaps/conflicts (global vs project): options, your recommendation, what changes for each choice.

## Step 3 — STOP and ask (one message)
Conflicts, shortlisted installs (which to install), ambiguities in workflow/scope/"never do this" rules, and for an existing CLAUDE.md/AGENTS.md what you would keep, change, remove. Wait for answers. Don't guess.

## Step 4 — Write (after approval)
Update the EXISTING files in place; preserve content and formatting. Create `AGENTS.md` or other harness files only if they already exist or the user asks.
- **First run, no playbook yet:** create CLAUDE.md with: Project snapshot (stack, layout, run/build/test/lint commands) / Hard rules (carry existing ones verbatim) / Capability map (task type -> skill/subagent/MCP -> when to avoid; mark global vs project) / Execution playbook (Understand -> Match -> Plan -> Approve -> Implement -> Verify -> Review) / Ask-don't-guess / Dangerous operations (deploy, migrations, deletes, force-push, secrets, prod access are confirmation-gated) / Learning rule.
- **Every run:** add or replace ONLY the block between `<!-- ai-tooling:begin -->` and `<!-- ai-tooling:end -->` containing `## Available AI Tooling & Recommended Workflows` (under 50 lines, markers included): relevant installed skills (with `~/.agents/skills/<name>` paths), recommended commands, relevant MCP servers, plugins, suggested workflows, the model per task type, the session team (roles and hand-offs, only if recommended in Step 2), and tools that need installation/configuration (labelled "not installed"). Concise pointers, never copied skill text. Re-running updates the block; it never duplicates entries. The block states that matching skills are invoked without being asked, and links the pipeline file.
- **Every run:** create or update the skill pipeline in `.claude/rules/skill-pipeline.md` (in place; keep the user's own rows and choices; use the repo's equivalent if it has one). Contents, in under 60 lines:
  1. **Auto-invoke:** read each prompt, invoke every matching skill (and any installed one that matches but is unlisted), name them in the report; skills never override approvals, test cadence or git rules.
  2. **Change size:** ask surgical / broader / ambitious for every code change unless the prompt says; smallest-diff skills only for surgical.
  3. **Planning pipeline**, ALWAYS when `PLAN.md` / `TODO.md` is drafted or revised: understand → size and open questions → design (user-typed commands) → `be-ambitious` ideas as optional items → spec if unclear → domain skills → write the plan with a `Skills:` line and test plan per phase → offer a plan-review UI (e.g. `plannotator-annotate`, opened only on a yes) → wait for approval.
  4. **Prompt → skills table:** one row per task type this repo really has, skills in invocation order, only names the inventory shows.
  5. **Limits:** ask first (external service, sign-in, upload, spend, download, install, waiting UI); banned tools; owner-typed skills (every `disable-model-invocation` skill and any the user reserves); no agents, full test gates or commits just because a skill says so.
  Apply the same ask-before-writing rule as the block, and ask about any choice the user has not made before.
- Keep CLAUDE.md around 150 lines; link long docs instead of copying them.

## Constraints
No installs, no edits outside the instruction files (the skill pipeline file is one), no destructive commands without approval. Reference only names/paths that exist (verify with the inventory). Don't commit or push.

## Final output (always)
1 Project analysis. 2 Detected stack. 3 Relevant existing skills. 4 Recommended commands. 5 Recommended MCP servers. 6 Recommended plugins. 7 Missing tooling. 8 Instruction files updated, the skill pipeline included (and which decisions came from the user). 9 Recommendations that need approval.
