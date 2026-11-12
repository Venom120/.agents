# OmniRoute setup

This folder contains the two local tools used to inspect an OmniRoute
instance and maintain the six My-Agents engine combos.

The repository is normally checked out at `~/.agents`. Harnesses discover
the repository through that checkout; these scripts do not install or
configure a harness.

## What is included

- `list-models-omniroute.py` performs a read-only model/provider export and
  optional health probes.
- `omniroute_free_combos.py` validates the configured model IDs, then creates
  or updates only the six named combos.
- `INSTRUCTIONS.md` is the authoritative model classification and ranking
  workflow.

The Linux `systemd` unit, provider exports, raw JSON snapshots, CSV files,
Python bytecode, and credentials are intentionally not stored here.

## Requirements

- A running OmniRoute instance.
- Python 3.8 or newer.
- The `requests` package:

  ```powershell
  python -m pip install requests
  ```

- `OMNIROUTE_MANAGE_KEY` for management endpoints.
- `OMNIROUTE_API_KEY` for the model health probes run by the exporter.

Set keys only in the current process or an ignored local environment file.
Never put real keys in this repository, command arguments, or generated
reports.

## Windows PowerShell

Set the local endpoint and keys for the current shell:

```powershell
$env:OMNIROUTE_BASE_URL = "http://127.0.0.1:20128"
$env:OMNIROUTE_MANAGE_KEY = "paste-admin-key-here"
$env:OMNIROUTE_API_KEY = "paste-inference-key-here"
```

Run the read-only exporter:

```powershell
Set-Location "$HOME\.agents\omniroute-setup"
python .\list-models-omniroute.py
```

Run the combo builder only after reviewing the model exports:

```powershell
python .\omniroute_free_combos.py
```

The combo builder performs remote writes through the OmniRoute management API.
It is idempotent and only creates or updates the six combos named in the
script; unrelated combos are left untouched.

## Linux, macOS, or WSL

Use the same scripts and environment variables:

```bash
export OMNIROUTE_BASE_URL='http://127.0.0.1:20128'
export OMNIROUTE_MANAGE_KEY='paste-admin-key-here'
export OMNIROUTE_API_KEY='paste-inference-key-here'
cd ~/.agents/omniroute-setup
python3 list-models-omniroute.py
python3 omniroute_free_combos.py
```

Install and supervise OmniRoute separately using the platform's supported
method. This repository does not include or install a service unit.

## Generated files

The exporter writes local-only files in this folder:

- `omniroute_models.csv`
- `omniroute_providers.csv`
- `omniroute_models.json`
- `omniroute_models_raw.json`
- `omniroute_providers_raw.json`

These files can contain provider names, account metadata, email addresses,
credential fragments, and model endpoint metadata. Review them locally, do
not commit them, and do not send them to third parties without redaction.

## Shared command

The repository command `/rebuild-combos` uses these scripts and exports. It
must be run from the `~/.agents` checkout or another repository that contains
the checkout; it does not fetch models or apply remote changes by itself.
