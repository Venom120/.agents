# OmniRoute model classification instructions

This file is the source of truth for rebuilding the six engine combos in
`omniroute_free_combos.py`.

## Before editing

1. Read `omniroute-setup/README.md`.
2. Read `omniroute_free_combos.py` in full.
3. Run `list-models-omniroute.py` with local environment variables set.
4. Read the generated model and provider exports locally. Never commit or
   share them without redaction.
5. If the exports are missing, ambiguous, or stale, stop rather than guessing.

The six locked combo names are:

| Combo | Workload |
|---|---|
| `free-coding-deep` | Difficult repository work and debugging |
| `free-coding-standard` | Normal implementation |
| `free-coding-fast` | Small, latency-sensitive edits |
| `free-reasoning` | Planning, analysis, and review |
| `free-context` | Large repository or document analysis |
| `free-vision` | Images, screenshots, charts, and diagrams |

Do not rename these combos or change their strategies without explicit
approval. The combo builder does not configure harnesses or agent files.

## Eligibility

Use the exported `working` and `failure_reason` fields exactly:

- `working=true`: eligible.
- `failure_reason=quota_exceeded`: eligible as a later fallback.
- `failure_reason=rate_limited`: eligible as a later fallback.
- Any other failure: exclude.
- Missing or ambiguous health data: unverified; investigate or ask.

Report counts for working, quota-exceeded, rate-limited, excluded, and
unverified models before rebuilding.

## Ranking

Research the exact model/version before ranking it. Prefer original benchmark
results and reputable independent evaluations. Record source URLs, dates,
benchmark versions, whether the result is independent, and relevant caveats.
Do not transfer scores between aliases or incompatible benchmark versions.
Unknown evidence is unknown; do not invent a score.

- **Deep coding:** agentic coding, repository changes, tool use, debugging,
  SWE-bench or Terminal-Bench evidence.
- **Standard coding:** dependable correctness, instruction following, tool use,
  and balanced latency.
- **Fast coding:** latency and throughput with a reasonable coding-quality
  floor; preserve `round-robin`.
- **Reasoning:** multi-step reasoning, planning, mathematics, and review.
  Thinking metadata is a signal, not proof.
- **Context:** documented and demonstrated long-context performance, not only
  the advertised context window.
- **Vision:** confirmed image input and visual/document reasoning. Text-only
  models must not enter this combo.

For priority combos, place working models before quota/rate-limited fallbacks.
Avoid duplicate aliases unless they provide meaningful provider diversity.
Preserve exact model IDs from the current export and verify every selected ID.

## Applying a rebuild

Use the shared `/rebuild-combos` command when available. It should:

1. Locate the `~/.agents/omniroute-setup` directory.
2. Read the guides, script, and local exports.
3. Modify only the `COMBOS` variable.
4. Validate IDs, strategies, duplicate entries, and health eligibility.
5. Run syntax validation.
6. Clearly report what was changed.

The command must not commit, push, change unrelated files, or claim that
remote combos were applied unless the combo builder was actually run
successfully with the management key.
