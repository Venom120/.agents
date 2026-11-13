---
name: github-glowup
description: Audit and upgrade a candidate's GitHub profile the way recruiters and interviewers see it, covering profile README, pinned repos, repo READMEs, descriptions, topics, commit history and red flags, then draft the fixes (profile README, repo READMEs, descriptions) and apply them only with permission. Use when the user wants to improve their GitHub profile, make GitHub recruiter-ready, write a profile README, choose pinned repos, or get feedback on their GitHub.
---

# GitHub glow-up

A recruiter clicks the GitHub link on a resume and decides in about 10 seconds whether this person builds things. Make those 10 seconds count.

## 0. Setup

1. Call the Skill tool with "cracked-profile" for the GitHub username. Otherwise ask, or use `gh api user --jq .login`.
2. Gather data. Prefer `gh` (works unauthenticated for public data, with lower rate limits); fall back to `curl https://api.github.com/...`:
   - Profile: `gh api users/<u>` (name, bio, company, location, blog, followers, public_repos)
   - Repos: `gh api "users/<u>/repos?per_page=100&sort=updated"` (name, description, language, stars, fork, topics, homepage, pushed_at, archived)
   - Pinned: `gh api graphql -f query='{ user(login:"<u>") { pinnedItems(first:6, types:REPOSITORY) { nodes { ... on Repository { name description stargazerCount primaryLanguage { name } } } } } }'`
   - Profile README: `gh api repos/<u>/<u>/readme --jq .content | base64 -d` (it may not exist)
   - For the top 6 candidate repos, read each README and glance at the tree (`gh api repos/<u>/<repo>/contents`).
   - Contribution activity: `gh api graphql -f query='{ user(login:"<u>") { contributionsCollection { contributionCalendar { totalContributions } } } }'`

## 1. The 10-second view

Describe exactly what a recruiter sees, top to bottom: avatar/name/bio, profile README, pinned repos, and the contribution graph. Then give the verdict: "Does this look like someone who builds things? Yes / Kind of / No."

## 2. Audit

Score and comment on each area:

| Area | What good looks like |
|---|---|
| Bio and identity | Real name, a one-line role bio (example: "Backend dev · Go & Postgres · <grad year> grad"), location, links |
| Profile README | Short: who you are, what you're building now, 3 best projects with one line each, how to reach you. No stat-widget overload, no giant GIFs |
| Pinned repos | 4–6 of your *best original* work, matching your target role. No forks, no tutorial clones, no college assignments unless they're impressive |
| Repo READMEs | For each pinned repo: what it is, a screenshot/GIF/demo link, the stack, how to run it, key technical decisions |
| Repo hygiene | Descriptions, topics, a homepage link if deployed, a license, no committed `node_modules`/`.env`/secrets |
| Activity | Consistent, real commits. Never suggest fake-commit generators: interviewers spot them and it's dishonest |

**Check for leaked secrets** in the top repos: search for patterns like `API_KEY=`, `sk-`, `AKIA`, or a committed `.env`, using code search or the file tree. If you find any, this is the **#1 priority**: tell them to rotate the key immediately and purge it from history.

## 3. Draft the fixes

Produce, in the conversation:
1. **New bio** (3 options).
2. **Profile README**: a complete Markdown file in a **modern style**. Read [README-STYLES.md](README-STYLES.md) and the curated references in [examples/](examples/), recommend one style (A: ASCII terminal, B: clean recruiter-first, C: minimal, D: story-led, E: neofetch portrait, where their photo becomes braille ASCII via `scripts/image-to-ascii.py`) based on their role and personality, and offer to render a second style for comparison. Use only real projects and facts. **Never describe a project's features, numbers or organisation that you haven't read in its code or README, or been told.** Write `[what it does]` and ask instead. Hedging ("tell me if this is wrong") doesn't make an invented detail acceptable. Generate any ASCII banner with a tool, and check that it's ≤ 80 columns.
3. **Pin plan**: which 4–6 repos to pin and in what order, with what to unpin and why.
4. **README rewrites** for the 2–3 most important repos, from their actual code (read it), using this template: title + one-line pitch → demo/screenshot → features → tech stack → architecture (a short note, or a diagram if useful) → run locally → what I learned / technical challenges.
5. **Descriptions and topics** for each pinned repo.

**Fact check before you show any draft.** Go through every bio, README and description line and ask, for each factual claim (a feature, number, habit, organisation, tech, achievement): *did I read this in their repo or profile, or did they tell me?* If not, replace it with a `[placeholder]` or delete it. That includes flattering filler like "solving DSA daily" or "organised by pattern". Then add one line under the drafts: `Fact-checked: every claim is from your repos or what you told me; [placeholders] need your input.`

## 4. Apply (only with explicit permission)

Changes are public. Ask per item: "Want me to apply this?" Then:
- Bio: `gh api -X PATCH user -f bio="…"` (needs `gh auth` with the user scope).
- Profile README: create or update the `<u>/<u>` repo's README via a clone, commit and push, or via the contents API.
- Repo description/topics: `gh repo edit <u>/<repo> --description "…" --add-topic …`.
- Repo READMEs: clone, edit, commit, push (or open a PR if they prefer).
- Pinning has no API, so give them the exact click path.

## 5. Scorecard

Call the Skill tool with "cracked-profile" and log a scorecard titled `github.com/<u>`. Dimensions: **First Impression, Pinned Work, READMEs, Hygiene & Security, Activity**.

---

*Skill calls:* if your agent has no Skill tool, open the named skill's `SKILL.md` in the cracked skills folder (`core/`, `interview/`, `profile/`, `strategy/`) and follow it instead.
