---
name: cost-routing
description: Stop spending expensive models on cheap work - choose the model per task and optionally route subagents automatically with a Claude Code mod. Use when the user asks to save credits or tokens, pick the right model, cut AI cost, or set up automatic model routing.
---

# Cost routing

## Which model
| Work | Model |
|---|---|
| Search, file listing, extraction, format changes, mechanical edits | `haiku` |
| Normal implementation, tests, docs, routine review | `sonnet` |
| Architecture, security, hard debugging, anything costly to get wrong | `opus` (or the session's model) |

Unsure: go one tier up. A wrong cheap answer that gets redone costs more.

## Cheapest option first
1. Don't spawn an agent for what a few direct tool calls can do.
2. Set `model:` in an agent's frontmatter, or pass `model` on the single spawn.
3. Enable the mod below for automatic routing.

## The mod (`mod/`, Claude Code with mods only; not active until enabled)
It sets the model of **subagents** by agent type, from the `ROUTES` table in
`mod/hooks/register.ts`. An explicit `model` on the spawn wins; unlisted types and forks are
left alone. A routed type's frontmatter `model` is overridden.

It leaves the main conversation's model alone on purpose: switching it mid-conversation drops the
prompt cache, which can cost more than it saves.

- Check: `claude plugin validate <skill>/mod` and `claude plugin test <skill>/mod`
- Try for one session: `claude --plugin-dir ~/.agents/skills/cost-routing/mod`
- Tune: edit `ROUTES`. Enable permanently only if the user asks.

To measure the effect, compare usage (`/cost`) on similar tasks with and without it. Do not claim
a saving you have not measured.
