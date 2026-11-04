# Agent tooling repository

This repository is the local source of truth for reusable agent skills, commands,
scripts, and harness adapters.

## Local setup

Place the repository at `~/.agents` so supported harnesses can discover the
shared skills. Use the linking scripts and the harness-specific instructions
under [AGENTS.md](AGENTS.md) when enabling skills.

Generated inventory manifests are machine-local and intentionally ignored by
Git. Cleanup reports and other local backups are also not part of the public
repository.

## Branch workflow

- `local` is the private working branch used by local harnesses. It is not
  pushed to `origin`.
- `main` is the sanitized public branch. Changes are copied to it explicitly,
  never merged from `local`, and only `main` is pushed.
- Keep the working tree on `local` when running harnesses that need local
  manifests or other ignored files.

The public branch must not contain credentials, personal contact information,
machine-specific paths, generated manifests, or local cleanup reports.

## Repository guidance

Contributor and agent workflow rules are documented in
[AGENTS.md](AGENTS.md). The repository's reusable skills are under
[skills/](skills/), and shared helper scripts are under [scripts/](scripts/).
