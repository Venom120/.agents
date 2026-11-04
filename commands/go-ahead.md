---
description: Execute all phases of the root plan.md (and todo.md if present), then test, validate, and summarize. No commits.
---

The user has already planned this work and approves implementation. Execute it end to end. Keep token usage minimal throughout.

Extra instructions from the user (may be empty): $ARGUMENTS

## 1. Load context (cheap)
- Read root `plan.md` (case-insensitive; also accept `PLAN.md`) and, if present, root `todo.md`. If no plan exists, stop and tell the user.
- If `graphify-out/` exists, query it (graphify skill / `graphify-out/GRAPH_REPORT.md`) instead of broad file reads or greps. Otherwise use targeted Grep/Glob and read only the line ranges you need. Do not spawn subagents unless a phase clearly needs it.
- Identify phases and their status. Skip phases already marked completed; resume from the first incomplete one.

## 2. Pre-flight check (once, before coding)
Skim all phases against the codebase. If you find a caveat, ambiguity, conflict between plan and todo, plan/code mismatch, missing dependency, or risky/irreversible step, STOP and ask the user concise clarifying questions with AskUserQuestion (recommended option first). Do not guess on anything that changes behavior or scope. Resume once answered.

## 3. Implement phase by phase
For each incomplete phase, in order:
1. Implement exactly what the phase says, matching existing code style. No extra scope.
2. If you hit a discrepancy or caveat mid-phase, pause and ask the user (AskUserQuestion). Don't silently work around it.
3. Add or update tests for the phase if the project has a test setup, and update validations (schemas, lint rules, type checks, input validation) if the project has them. Don't introduce a new test framework.
4. Immediately mark the phase completed in `plan.md` and the matching items in `todo.md` (e.g. `[x]`, or ✅/"Completed" following the file's existing convention).
Continue to the next phase without waiting for approval unless blocked by step 2.

## 4. Tests (after all phases)
- Run only the tests added or touched by this work (scoped), not the full suite.
- If any fail: fix, then re-run ONLY the tests that failed/were fixed. Repeat until green. Do not re-run the full suite.
- Never chain a test suite and a validator/lifecycle check in ONE command (no `;`, `&&`, or pipes between them): run the tests alone, read the result, fix every failure, and only then start the validator as its own separate command, so a red suite never wastes a validator run.
- If a failure reveals a plan/design problem rather than a bug, ask the user.

## 5. Validations (after tests)
- Run the project's validations (type check, lint, build/schema checks) scoped to changed files/packages where the tool supports it.
- Fix failures, then re-run only the failed validations. Repeat until clean.

## 6. Hard rules
- NEVER `git commit`, `git push`, tag, branch-publish, bump versions, or install/update plugins. Leave changes uncommitted.
- Don't touch downstream docs, docstrings, or guides yet (see below).
- Never loosen or delete tests/validations just to make them pass.

## 7. Final report (short)
Output only:
- A brief bullet list (max ~6 bullets) of what was implemented, in plain non-technical language, no jargon or file names.
- One line if anything was skipped, failed, or needs attention.
- Then ask: "Want me to update downstream docs, docstrings, guides, etc.?"
