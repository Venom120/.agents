# AGENTS.md — plug-and-play agent playbook

> **How to use.** 1) Clone/copy this repo to `~/.agents`. 2) Copy this file into your project root as `AGENTS.md` (Codex, OpenCode,
> Antigravity) or `CLAUDE.md` (Claude Code) — same content. 3) Fill **§P** (or run `/init-playbook`, which does it and adds a tooling
> block). 4) Delete sections you do not need; keep your project copy near 150 lines and link long docs instead of pasting them.
> The rules below were distilled from a large production codebase (layered FastAPI + React app). Stack-specific names are examples:
> swap in your equivalents, keep the discipline.

## P. Project profile (fill in)
- **Stack / layout:** `<languages, frameworks, folders, ports>`
- **Commands:** build `<…>` · run `<…>` · test `<…>` · lint/typecheck `<…>` · e2e/lifecycle check `<…>`
- **Deploy:** `<how code reaches production>` · **Environment:** secrets only in git-ignored env files, never in compose/CI files
- **Docs index:** `<README per folder, numbered flow guides, ER diagram, PLAN.md, TODO.md>` — read the folder README + matching guide before working in a folder.

## 1. Operating principles
> **TOP RULE — ASK, DON'T ASSUME.** Never act on your own for anything new, out of scope or not explicitly asked (extra tests, scripts,
> refactors, "smoke tests", tangents). Present the plan, get explicit approval, then act. If behaviour is not established by code,
> docs or this file: inspect, state the ambiguity, ask ONE focused question with minimal options, wait.
1. **Smallest correct change.** No scope creep, no unrequested abstractions, no speculative config. Reading and verification are never skipped.
2. **Approval gates:** schema/model/architecture changes, new dependencies, app-shell/routing changes, large refactors, doc edits (one "update
   docs" approval covers every affected doc), installs of skills/plugins/MCP, anything destructive (§13).
3. **Never revert** the user's (or a prior session's) changes without asking; explain the impact of reverting versus keeping.
4. **Report honestly:** what changed, what was verified, what failed (with output), what was skipped, remaining risks. Do not claim "done" without a real check.
5. **Learn:** when corrected, or when you hit a major convention/gotcha, propose adding it here (edit in place; push detail into docs).

## 2. Workflow (every non-trivial task)
1. **Understand** — read this file, the folder README, the matching guide, then the code. Trace the whole flow before editing.
2. **Match** — pick skills/agents/MCPs from §4. If none fits, search for a skill and **ask before installing**.
3. **Plan** — steps, files, risks, verification. Independent steps → parallel subagents, **one folder/area per subagent**; research before implement; never send an implementer in cold.
4. **Approve** — present the plan; wait for the go-ahead on anything major or ambiguous.
5. **Implement** — compile/typecheck each file after editing; follow the surrounding code's idiom, naming and comment density.
6. **Verify** — run the project's real checks (§7); fix root causes, not symptoms (grep every caller of what you change).
7. **Review & report** — review the diff; then summarise (what / verified / risks); ask about docs.

**Subagents:** may write tests but **never run suites** — only the parent runs them. Put `ONLY YOU (the parent) WILL RUN THE TESTS` in every subagent prompt that touches tests, and repeat the relevant rules in the prompt (they do not inherit this file).

## 3. Planning documents (`PLAN.md` + `TODO.md`)
- **PLAN.md** is phase-divided: Research · DTO/types · Repository · Service/Router · Frontend types/API · Frontend page · Tests · Docs. Each phase has Goal / Blast radius / DB / API / Optimization and a mermaid diagram where it helps. **TODO.md** mirrors it as checklists; keep both in sync at every phase gate.
- **A plan is not final until its questionnaire is.** Every question the agent has is asked (structured question tool) and settled BEFORE the plan is presented as final or any phase starts; record each answer in both files. Settled decisions are not relitigated.
- State the defaults you chose ("veto any"), the risks (each pauses its phase and returns to the user), and a verification matrix.
- Ambiguity or a caveat found mid-implementation pauses the phase and goes back to the questionnaire; log it in TODO.md.

## 4. Capability routing
The skills/commands/MCP servers you actually have live in `~/.agents` (see §14); `/init-playbook` writes this project's real map between
`<!-- ai-tooling:begin -->` and `<!-- ai-tooling:end -->`. Generic routing:

| Task | Use | Avoid when |
|---|---|---|
| Explore / locate code | an explore subagent, symbol-search MCP, Read/Grep | you already know the file |
| Library/framework docs | a docs MCP | business-logic questions |
| Architecture, schema, API shape | architect agent + DB-change checklist | trivial edits |
| Backend / frontend code | implementer agent + the project's feature skill, **after the plan is approved** | unapproved or unresearched areas |
| UI check on localhost | browser/Playwright MCP against the local gateway | production URLs |
| Tests | test-engineer **writes**, the parent **runs** | a subagent running suites |
| Review before commit | code-review skill/agent | before code exists |
| Debug | debugging skill; read logs first | guessing without evidence |
| Security | security reviewer + the project's security checklist | — |
| Server / prod data | read-only server/DB tooling; mutations only with approval of the **exact** SQL/command | any other mutation |
| Docs | ask first (§12) | unapproved |

Rules: never claim a tool is installed unless the inventory shows it; global and project items that overlap → record the choice; never install silently.

## 5. Architecture rules (layered backend)
Flow: **routers → services → repositories → models.**
1. **Routers** only wire HTTP: auth/permission dependency, DTO in/out, one service call. Role-prefixed routes (`/api/<role>/…`), common routes under `/api/auth`; role folders snake_case; never register routes on the app object directly.
2. **Services** are organised by functionality, not role. Every service function has a docstring: **what / who / required permissions**. One-way private imports are fine; circular imports are forbidden.
3. **Repositories** own ALL database access. Services never write raw SQL or call the session directly.
4. **DTOs:** one file per endpoint (`dto/<domain>/<Endpoint>.py`); shared `MessageResponse`/`ErrorResponse` at the root. Responses expose only what the client reads; sensitive fields are reviewed (§8).
5. **Models:** enums are `str, Enum` and stored by value; link tables for many-to-many (composite PK); optional 1:1, list 1:M; nullable "unlimited" columns default to `None` (a non-zero Python default overrides an explicit `None` at flush). Never change a column type without approval.
6. **Single source of truth for cross-cutting logic.** Permission resolution, data-scope ("lens") rules, passed-out/expiry logic, scoring maths, eligibility predicates each live in ONE function; everything else calls it. Never re-implement.
7. **Counters and money-like quantities** move only through a guarded single `UPDATE … WHERE balance + n <= limit` and every movement writes an append-only ledger row; invariant tests assert `sum(ledger) == counter`.
8. **Async ORM:** eager-load relationships before touching them (no lazy loads); `refresh` drops loaded relationships; pass load options to repository getters; never chain offset/limit on eager-loaded collections.
9. **Soft delete by default:** entities carry `status`/`deleted_at`/`deleted_by`; a global read filter hides deleted rows (raw/Core SQL is NOT filtered — use explicit predicates); deleted rows keep their unique values until purged; deletes with data take a `replacement_id` and re-point children in ONE transaction; every delete/restore/replace/purge writes an audit row. Only an explicit purge job hard-deletes (grace period).
10. **Third-party data:** read both key spellings when a client library snake-cases (`pkg.get("package_id") or pkg.get("packageId")`); investigate vendors from their collection/probe scripts before asking the user; use bounded `asyncio.gather` + semaphore where the vendor has no batch API.

## 6. Data, migrations and seeds
- **Seed/mock data has ONE source of truth.** History tables (growth, score bands, logins) are COUNTED from per-entity timelines by a simulator — never hand-write per-day numbers. Tests filter by mock ids only and clean up row-by-row; never drop all tables in tests.
- **Migrations:** the bootstrap module only creates types/tables/indexes. A release that needs a column or data move on a live table adds ONE idempotent, single-transaction, clearly named step called from the migration runner, and **removes it again** once the production checklist (read-only SQL) shows it applied. Destructive changes use expand/contract: ship the code first, drop the old object manually afterwards.
- A new UNIQUE constraint/index needs a friendly message in the error registry. A new field/model/enum value → ask whether to update mocks, field/relationship tests, the ER diagram, and run validation.
- Production data is touched by **read-only** inspection; mutation SQL needs the user's approval of that exact SQL. **Never delete rows on a server.**

## 7. Testing and verification
- Run suites in the same environment as production-like runtime (the container). **Before any run, confirm the container holds the edited code** (bind-mount: compare file hashes host vs container; rebuild if different). A hot-reloading container must not see edits during seed/validate runs; wait for `healthy`.
- **Cadence:** targeted tests while iterating; the FULL suite once after the last change of a batch/phase, plus the end-to-end lifecycle validator. Run long commands in the background; investigate an outlier duration instead of re-running; docs-only/lint-only changes skip re-gating. Per-test timeout (120 s).
- **Output convention:** the runner prints ONE letter per test/check live (P/F/S/E) and writes the full verbose output to a git-ignored log. Wait for the end, read the log only for F/E, never re-run just to see a failure. Keep a "known failures" list.
- **Route coverage gate:** a lifecycle validator calls every public route (reviewed allowlist for exceptions), creates top-down, exercises features, deletes bottom-up and checks for residue. A new/changed route needs a call there; permission/DTO changes keep it 100% green.
- Frontend: lint + typecheck + production build; then a browser click-through on localhost for UI changes. Say plainly what was NOT verified (browser, prod-like data, migrations).

## 8. Security and production
- Production is **fail-closed**: real secret keys required, locked CORS, docs endpoints off, test/validate commands refused, destructive CLI paths demand a typed password/`YES` (never a password on a command line).
- Secrets only in git-ignored env files. Never log passwords, tokens, OTPs, request bodies or one-time/secret codes; log other users' emails masked; security-relevant actions emit an audit event (no values).
- Sessions: HttpOnly cookies, no tokens in `localStorage`, auth responses carry no tokens, revocation via token version. Throttle OTP/login, cap guesses, constant cooldowns; fail CLOSED when the throttle store is down for security gates.
- **The server is the authority; the UI only hides.** Scope/permission is computed in one place (§5.6). Out-of-scope = 404/403, never partial data.
- Sensitive values are masked in lists and revealed one row per call with an audit; exports that contain them are capped and audited. A **response-contract test** fails on any new sensitive-looking response field until it is reviewed in an allowlist.
- Verify third-party ownership claims via the third party (never trust user-typed handles); outbound calls have timeouts and retries in ONE layer; link URLs are allow-listed (http/https only).

## 9. Logging, errors, observability
- One module logger per file; the global handler logs each error ONCE (never log-and-re-raise); every response carries a request id; services/repositories are auto-instrumented; slow requests are traced.
- User-facing text for known failures (unique violations, throttles) comes from a registry, not ad-hoc strings. Email/SMS goes only through the single messaging service (budgets, fallbacks, send logs).

## 10. API design, performance and data access
Performance is a requirement: assess it for every feature and implement what is relevant — paginated APIs (keyset for large sets), server-side search with a debounced client, selective columns, indexes for measured/common queries, N+1 prevention, connection pooling, Redis/browser caching (cache keys include every filter), background jobs for slow work (return a `job_id`, stream progress over SSE), parallel independent requests with bounded concurrency, external-call timeouts, skeleton loading, lazy images (WEBP/AVIF), code splitting, list virtualization, compression, self-hosted limited fonts, real-user monitoring. **Measure, document the bottleneck, do not add speculative infrastructure; preserve correctness and security.**
- Filters and their options come from the backend (`metadata.filter_options`); never rebuild a filter cascade on the client. Dashboards narrow, never widen, the caller's scope.
- Use ids (`degree_id`), never free-text names, as relations. Counts shown to users are derived, not stored twice; one predicate serves both queueing and counting.

## 11. Frontend
- **Two layers.** UI (renders, owns no I/O): `components/ui` atoms, shared widgets, pages that compose them. Frontend-backend layer (everything that talks to the server, waits, caches, guards): `api/` (the ONLY server calls), `hooks/`, `contexts/`, `utils/`. Keep them apart.
- **API files:** named `async function`, one per endpoint, `// VERB /path` comment, `return response.data`, no try/catch, no toast (one axios interceptor shows errors). **DTO types mirror backend DTOs exactly** (snake_case, header comment naming the source).
- **Page contract:** state that a user would refresh/share lives in the **URL** (page, search, every filter, tab) via one hook; server-paged lists via one paged-list hook (cache key = every filter except page/search); search debounced into the URL; mutations: `await api` → toast → patch/refetch; empty `catch` with a comment; effects that await guard with a `cancelled` flag and clean up timers/listeners.
- **Screen anatomy:** header (icon tile + title + subtitle + primary action) → optional stat row → filter card (search, selects, "Clear" only when active) → data table + pagination → modals. Mutations happen in a **modal**, never inline. Permission-gated controls are **not rendered** (never "disabled with a tooltip").
- **States:** first load = skeleton shaped like the content; empty = muted icon + one sentence; error = toast only; validation = toast before the call; busy buttons disabled until the promise settles; crash = error boundary.
- **Design system:** tokens as CSS variables (light + dark), never hard-coded hex; one icon library; one motion library (reduced-motion safe); one font stack; consistent radius/spacing scale; domain colours (levels, statuses) only from one util. Every table header sortable (URL-backed, server allow-listed columns). Mobile-first, keyboard-accessible, `aria-label` on icon-only buttons. New screens copy the closest existing page; record conventions in a `FRONTEND.md`.
- **Hierarchies** are parent-first selects; a child is disabled until its parent is chosen and cleared when the parent changes. Display strings never hard-code a domain word that differs between segments; read it from a label helper.
- **Demo mode** (if the product has one): a URL prefix switches router basename, API prefix and storage keys; the middleware makes every write `403 view_only` except an allowlist; destructive controls are not rendered.

## 12. Documentation
- Docs (guides, READMEs, this file) are updated **only with approval**. Keep: a README per folder, numbered flow guides with a mermaid diagram, an ER diagram that stays in sync with the models (validate every mermaid edit), generated API docs that are **never hand-edited**, `PLAN.md`/`TODO.md` for the active effort.
- Keep this instruction file short: rules here, explanations in docs. Remove a rule when the code enforces it.

## 13. Git, releases and dangerous operations
- **Never** `commit`, `push`, `tag`, publish a release or bump a version unless explicitly asked in the current conversation; approval does not carry over. When asked to commit, stage everything that belongs to the change (including the user's own edits and deletions) and use a message that explains why.
- **No scratch files in commits** (run logs, `*.out`, `*.tmp`, `*.bak`, test/validate logs, caches). A pre-commit hook enforces it.
- **Confirmation-gated:** deploys, restores, schema/data migrations, any delete, `drop_all`/`TRUNCATE`/`DROP`, force-push, volume wipes, secret/env edits, production or server access. Recommended hooks: (a) a shell hook that asks before destructive commands (`git reset --hard`, `git clean`, force-push, `docker … prune`, `down -v`, `TRUNCATE`, `DROP TABLE`, `DELETE FROM`, restore commands); (b) a hook that blocks `git commit`/`push` while temp files are present.
- If the container daemon is down, stop and ask. Use `127.0.0.1` rather than `localhost` on Windows. Never mutate a production stack from a dev session.

## 14. The agent environment (`~/.agents`)
`~/.agents` is the **single source of truth** for reusable skills; harnesses see it through links or native discovery.

| Path | Purpose |
|---|---|
| `skills/<name>/SKILL.md` | reusable skills (third-party ones installed with `npx skills add <owner/repo> -g -s <name>`; lock file `.skill-lock.json`) |
| `scripts/inventory.py` | read-only audit → `manifests/*.json`, `reports/changes-*.md` (added/removed/changed/broken); `--target`, `--project`, `--out` |
| `scripts/link-skill.sh <name> [dir]` | idempotent link of a skill into a harness (junction on Windows, symlink elsewhere) |
| `manifests/decisions.json` | every keep/remove/restore decision + policy (so repeat audits do not re-ask) |
| `reports/`, `backups/`, `agents/`, `rules/`, `commands/` | reports with rollback lines; backups; harness adapters |

**Harness discovery (verify when versions change):** Claude Code `~/.claude/skills` (needs one link per skill) · OpenCode `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` · Codex `~/.agents/skills` (disable per skill in `~/.codex/config.toml`) · Antigravity `~/.gemini/config/skills` (link the whole folder) and per-project `.agents/skills`. Commands/agents have different native formats per harness: keep each harness's adapter, never symlink across formats. MCP configs differ per harness (JSON/TOML/JSONC) — track names only, never print env/args/headers.

**Two slash skills:**
- `/skill-cleanup [harness|category|project <dir>]` — audit (usage, redundancy, token overhead, health), review items in batches with pros/cons and a KEEP/MERGE/CENTRALIZE/MOVE/DISABLE/REMOVE/INVESTIGATE recommendation, execute only approved decisions, verify, write a report with rollback lines. Idempotent.
- `/init-playbook [repo]` — analyse the repo, read the inventory, recommend only tools with a clear use here, ask, then update `CLAUDE.md`/`AGENTS.md` in place and refresh the marked tooling block.

**Policy:** never remove a *global* skill only because the current project does not use it. Valid reasons: the user asks, an older/duplicate copy, broken (e.g. depends on agents that do not exist), or heavy overhead that clearly overlaps another skill. Plugins stay where their harness installs them (moving breaks updates); centralise by reference. Never touch credentials, `auth.json`, `.env*`, OAuth files.

## 15. New-project checklist
1. Copy this file → fill §P (or run `/init-playbook`). 2. Create `PLAN.md`/`TODO.md` for the first feature (§3). 3. Add the destructive-command and temp-file hooks (§13). 4. Make test/validate runners print P/F + log files (§7). 5. Add a response-contract test and an error registry early (§8, §9). 6. Link only the skills you need into your harness (`link-skill.sh`). 7. Commit nothing until asked.
