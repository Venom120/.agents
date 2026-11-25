# Agent tooling repository

This repository is the local source of truth for reusable agent skills, commands,
scripts, and harness adapters.

Start with [SETUP.md](SETUP.md) when installing this orchestration on a user's
laptop. It discovers installed harnesses, asks which supported harnesses to
configure, runs the sync pipeline, and refreshes [INDEX.md](INDEX.md).

## Local setup

Place the repository at `~/.agents` so supported harnesses can discover the
shared skills. Use the linking scripts and the harness-specific instructions
under [AGENTS.md](AGENTS.md) when enabling skills.

### Link a manually added skill on Windows

After adding a skill directory under `C:\Users\<username>\.agents\skills`,
replace `your-skill-name` below with that directory name. These commands create
a directory junction, so Claude reads the canonical skill files from `.agents`.

PowerShell:

```powershell
$skill = "your-skill-name"
$source = Join-Path $HOME ".agents\skills\$skill"
$target = Join-Path $HOME ".claude\skills\$skill"
New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
New-Item -ItemType Junction -Path $target -Target $source
```

Command Prompt:

```cmd
set "SKILL=your-skill-name"
if not exist "%USERPROFILE%\.claude\skills" mkdir "%USERPROFILE%\.claude\skills"
mklink /J "%USERPROFILE%\.claude\skills\%SKILL%" "%USERPROFILE%\.agents\skills\%SKILL%"
```

The target link must not already exist. To remove only the link while keeping
the skill source, use `rmdir "%USERPROFILE%\.claude\skills\%SKILL%"` in
Command Prompt or `Remove-Item $target` in PowerShell.

## Desktop-agent plugins, skills, and Claude mods

Skills and Claude mods use different discovery paths. A skill is a directory
containing `SKILL.md`; a Claude mod is a plugin module containing a
`.claude-plugin\plugin.json` and, when applicable, a `hooks\hooks.json`.
Linking a skill does not activate a Claude mod's hooks.

### Install a plugin repository and expose all skills

Keep the external checkout under `.agents` and keep it ignored by the parent
repository. Copy its skills into the real canonical `.agents\skills` directory;
never create a junction or symlink inside `.agents\skills`. For example, the
Elephant-Goldfish Model checkout is:

```text
%USERPROFILE%\.agents\elephant-goldfish-model
```

On Windows, install each new skill as a real directory in the shared source,
then link that canonical directory to Claude:

```powershell
$repo = Join-Path $HOME ".agents\elephant-goldfish-model"
$shared = Join-Path $HOME ".agents\skills"
$claude = Join-Path $HOME ".claude\skills"
New-Item -ItemType Directory -Force -Path $shared, $claude | Out-Null
Get-ChildItem (Join-Path $repo "skills") -Directory | ForEach-Object {
    $source = Join-Path $shared $_.Name
    $target = Join-Path $claude $_.Name
    if (-not (Test-Path $source)) {
        Copy-Item -LiteralPath $_.FullName -Destination $source -Recurse
    }
    if (-not (Test-Path $target)) {
        New-Item -ItemType Junction -Path $target -Target $source | Out-Null
    }
}
```

Codex discovers the real shared `.agents\skills` directories directly. Claude Code
uses the `.claude\skills` junctions. Restart the desktop agent after adding or
updating skills. The sync pipeline rejects links in `.agents\skills` or
`.agents\mods` so the source remains portable and self-contained.

### Install and expose Claude mods

Keep each mod as a real canonical directory under `.agents\mods\<mod-name>`, then link
the complete mod directory into Claude's mod directory. Preserve the manifest
and hook files; do not link only the hook source:

```powershell
$modName = "cache-keeper"
$source = Join-Path $HOME ".agents\mods\$modName"
$target = Join-Path $HOME ".claude\mods\$modName"
New-Item -ItemType Directory -Force -Path (Split-Path $source), (Split-Path $target) | Out-Null
if (-not (Test-Path $target)) {
    New-Item -ItemType Junction -Path $target -Target $source
}
```

Apply the same procedure to every directory under `.agents\mods`; do not
assume that installing a plugin repository's skills also installs its mods.
After linking mods, restart Claude so its mod loader registers the plugin and
hooks. The current local Claude mod inventory includes `cache-keeper`, whose
manifest is `.claude-plugin\plugin.json` and whose hook registration is
`hooks\hooks.json`.

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
