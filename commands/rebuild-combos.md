---
name: rebuild-combos
description: Rebuild My-Agents OmniRoute COMBOS from the latest model and provider CSV exports.
---

Rebuild the `COMBOS` variable in the My-Agents repository from the latest
OmniRoute CSV exports.

## Required workflow

1. Locate the `~/.agents` checkout and find:
   - `omniroute-setup/INSTRUCTIONS.md`
   - `omniroute-setup/omniroute_free_combos.py`
   - `omniroute-setup/omniroute_models.csv`
   - `omniroute-setup/omniroute_providers.csv`
2. Read `omniroute-setup/README.md`, `INSTRUCTIONS.md`, the complete combo
   builder, and both CSV files before editing.
3. Follow `INSTRUCTIONS.md` exactly:
   - `working=true` is eligible.
   - `failure_reason=quota_exceeded` or `rate_limited` is eligible as a
     fallback after working models.
   - Every other failure is ineligible.
   - Preserve exact CSV model IDs.
   - Keep the six locked combo names and their existing strategies.
   - Require confirmed vision support for `free-vision`.
   - Keep `free-coding-fast` as `round-robin`.
4. Rebuild only the `COMBOS` variable in
   `omniroute-setup/omniroute_free_combos.py`. Do not change combo names,
   worker mappings, HTTP behavior, or unrelated configuration.
5. Put working models before quota/rate-limited fallbacks and avoid duplicate
   aliases within a combo.
6. Validate every selected ID against the CSV and report:
   - health counts and eligible count,
   - final count per combo,
   - excluded or unverified models,
   - retained quota/rate-limited fallbacks,
   - duplicate IDs and strategy/worker validation.
7. Run Python syntax validation and the builder's existing validation if the
   required OmniRoute environment is available. Do not claim the remote
   combos were applied unless the builder was actually run successfully.

If the CSVs are missing, health fields are ambiguous, or the `~/.agents`
checkout cannot be located, stop and report the exact blocker instead of
guessing. Never commit generated exports or credentials.
