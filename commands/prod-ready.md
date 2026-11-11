---
description: Phase-by-phase production-readiness audit (data safety first, then speed, then legal/privacy/accessibility). Read-only audit, report per phase, wait for approval before any change. No commits.
---

Audit this project for production readiness, step by step, in the phases below. Extra instructions from the user (may be empty): $ARGUMENTS

## Ground rules
- **Audit first, change nothing.** Never run a destructive command (DELETE/TRUNCATE/DROP, `--restore`, `--cleanup`, volume wipes, force-push) and never touch production data or credentials. Read code, config, compose files, docs and read-only server tools only.
- Follow the project's own rules (root `CLAUDE.md`, folder READMEs). If `graphify-out/` exists, query it before blind searches. Do not spawn subagents unless a phase clearly needs it. Keep output short.
- Do ONE phase at a time. For every item give a status and one line of evidence (file:line or "not found"): **PASS** (done), **GAP** (missing or partial), **N/A** (does not apply, say why). Do not guess: if you cannot verify, mark **UNKNOWN** and name what to check.
- After each phase print a compact table, then continue to the next phase on your own. Only stop early when blocked or when a finding needs a decision (use AskUserQuestion, recommended option first).
- At the end, present the report and **WAIT for approval**. Implement nothing until the user picks which GAPs to fix; then fix per phase, smallest correct change, and re-check only those items.

## Phase 0 - Recon (cheap)
Identify the stack, environments (local / staging / production), database(s), object storage, cache/queue, deploy path, hosting region, and where credentials live. Note anything already documented (Guides, `DB-setup/`, compose files). This frames every later phase.

## Phase 1 - Data safety: environments and access
1. Separate databases for test, staging and production; no shared DB between environments.
2. Each environment has its own credentials, none hardcoded in compose or source, none committed.
3. Server-side enforcement (not UI-only) of delete permissions and limits; bulk deletes restricted to authorized roles.
4. Cap on how many records one delete/bulk action can touch; the exact affected count is shown before it runs.
5. Typed confirmation for high-impact deletes.
6. Destructive commands/scripts on production need explicit human approval (password prompt, guard, or hook); deletion protection is on for the managed databases/buckets.
7. Every deletion is audit-logged with who and when.

## Phase 2 - Data safety: recovery
1. Soft delete / trash with restore for user-visible data; retention window and purge approval documented.
2. Versioning enabled on file/object storage.
3. Automatic backups of the database AND uploaded files; schedule and retention known.
4. Point-in-time recovery enabled (or the reason it is not).
5. At least one backup the production credentials cannot delete or overwrite (separate account/immutable/object lock).
6. Alerts when a backup fails and when a bulk delete happens.
7. Every migration is tested on a staging copy first; migrations are additive/expand-contract, reversible, one transaction where possible.
8. A restore has been tested in a separate environment and the app works on the restored data (find the evidence: a runbook, a log, a date; otherwise GAP).

## Phase 3 - Backend speed
Check: paginated list APIs; selective columns; N+1 queries (eager loading / set-based); indexes for the common and slow queries (check real query plans, not guesses); connection pooling; Redis caching of hot data with a safe invalidation rule; timeouts and bounded retries on every external call; slow or bulk work in a background job queue; independent requests run in parallel; Brotli/GZIP at the proxy; streaming for AI/long responses where applicable; OpenTelemetry (or equivalent) tracing for slow requests; application servers close to the database; load balancing / more than one app instance if traffic needs it.

## Phase 4 - Frontend speed
Check: skeleton loading screens; images in WEBP/AVIF with sizes, lazy-loaded below the fold; duplicate-request prevention (disabled buttons, in-flight dedupe); debounced search/autocomplete; code splitting per route; third-party scripts loaded after the page; list virtualization for long lists; unnecessary re-render control; optimistic UI where safe and reversible; self-hosted fonts with few weights; static files via CDN with long-lived browser caching (hashed file names); SSR/SSG only if the architecture supports it; unused dependencies removed (run the project's dependency checker, list findings, do not delete yet).

## Phase 5 - Measurement and resilience
Real-user performance monitoring; testing on a slow phone and a slow network (throttled profile); error tracking and health checks; rate limits; what happens when Redis, the queue or an external API is down.

## Phase 6 - Legal, privacy and accessibility (engineering checklist, not legal advice)
Say once in the report that a lawyer must confirm the legal wording; you only verify what the app does and shows. Check:
1. **Policies and consent**: privacy policy, terms of service, refund policy, business contact details and a published subprocessors list exist and are linked from the footer and sign-up. Sign-up has an (unticked) checkbox to accept privacy + terms, and the acceptance is recorded (who, which version, when). Marketing consent is separate and optional; every marketing email has a working unsubscribe.
2. **Cookies and tracking**: cookie banner with a real "decline non-essential"; analytics, ads and other trackers are blocked until consent. Audit every third-party SDK, script and analytics tool: what it collects, where it sends data, whether a data processing agreement exists.
3. **User data rights**: users can request access/export and deletion of their data; retention limits are set and enforced (logs, tokens, deleted accounts, uploads); no unnecessary personal data is collected; children's data (under 13 / local age of consent) needs parental consent or is not collected; user data is not used to train AI without opt-in and this is stated.
4. **Honest UI**: no fake countdown timers, fake reviews, fake scarcity, hidden fees or pre-ticked boxes (dark patterns); subscriptions are as easy to cancel as to start; auto-renewal and total price are disclosed before payment; AI-generated content is labelled.
5. **Claims**: no unsupported claims (SOC 2, ISO, "100% secure", uptime, results); uptime promises are realistic and match monitoring; customer/partner logos and testimonials only with written permission.
6. **Licenses**: licenses of images, fonts, icons, code and dependencies are verified (run the project's license checker, list copyleft or unknown ones and their obligations); open-source attribution notices are shown where required; DMCA agent registration needs are checked if users can upload or post content.
7. **Accessibility**: color contrast meets WCAG AA (check both light and dark themes), images have meaningful alt text, everything works by keyboard with a visible focus, forms have labels, motion respects reduced-motion.

## Phase 7 - Report (then wait)
Print, in this order:
1. **Scorecard**: counts of PASS / GAP / UNKNOWN / N-A per phase.
2. **Top risks**: the GAPs that can lose data or take the app down, ranked, each with a one-line fix and effort (S/M/L).
3. **Legal exposure**: the GAPs from Phase 6 that carry the most risk, and which need a lawyer.
4. **Loss and recovery numbers**, stated plainly with your assumptions and what you could not verify:
   - **Data you could lose** (RPO): per data type, based on backup frequency and PITR.
   - **Time to recover** (RTO): restore, redeploy, and verify steps with a realistic duration.
   - **Cost**: monthly estimate of the missing safeguards (backups, PITR, storage versioning, monitoring, staging environment), by provider/plan where known; say "unknown" rather than invent a price.
5. **Proposed fix order** in small phases, safest first (data safety before speed).

Then ask which items the user approves. Do not start any change before that answer. Never `git commit`, `git push`, tag or deploy.
