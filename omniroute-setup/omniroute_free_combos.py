#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================================
# OmniRoute Free Combo Builder
# ============================================================================
#
# PURPOSE
# -------
# This script creates (or updates) the six "free" Engine Combos that the
# My-Agents pipeline routes against. Each combo is a named, ordered list of
# model IDs that OmniRoute will try in priority order. OmniRoute itself
# handles provider/model selection, retries, cooldowns, and resilience;
# this script only defines the combos.
#
# HOW IT FITS IN THE ARCHITECTURE
# -------------------------------
#
#   User
#     -> Master  (fixed to omniroute/free-reasoning)
#     -> Pipeline Worker (one of six hidden subagents)
#     -> OmniRoute Engine Combo (created by THIS script)
#     -> Provider / Model Pool
#
# The My-Agents hidden subagents are pinned to these six combos:
#   - free-coding-deep      -> pipeline-worker-deep
#   - free-coding-standard  -> pipeline-worker-standard
#   - free-coding-fast      -> pipeline-worker-fast
#   - free-reasoning        -> pipeline-worker-reasoning
#   - free-context          -> pipeline-worker-context
#   - free-vision           -> pipeline-worker-vision
#
# When a subagent runs, its `provider: omniroute` + `model: <combo-name>`
# setting causes OmniRoute to walk the list in this script until a model
# responds successfully.
#
# WHY A SCRIPT AND NOT INLINE CONFIG?
# -----------------------------------
# OmniRoute's combo API is the only place where provider/model selection
# for a "logical route" can be defined and ordered. Doing it inline inside
# agent definitions would couple agents to raw provider models, which the
# AGENTS.md rules forbid (see AGENTS.md rule 14). Keeping the combos in
# this script means agents reference a stable combo name and providers
# can churn underneath without code changes.
#
# USAGE
# -----
# 1. Make sure OmniRoute is running (see omniroute-setup/README.md).
# 2. Export your management key:
#
#      Linux/macOS:
#        export OMNIROUTE_MANAGE_KEY='YOUR_KEY'
#      Windows (PowerShell):
#        $env:OMNIROUTE_MANAGE_KEY='YOUR_KEY'
#
# 3. Run the script:
#
#      python ~/.agents/omniroute-setup/omniroute_free_combos.py
#
# The script is idempotent: it creates missing combos and updates
# existing ones. Unrelated combos are never touched.
#
# MANAGEMENT API KEY
# ------------------
# The OMNIROUTE_MANAGE_KEY env var is required. It is a DIFFERENT key from
# OMNIROUTE_API_KEY (the one subagents use to talk to OmniRoute). The
# management key has admin-level access; the API key is read-only for
# inference. Never share or commit the management key.
#
# API
# ---
#     http://127.0.0.1:20128
#
# ============================================================================

import os
import sys
import requests

BASE_URL = os.getenv(
    "OMNIROUTE_BASE_URL",
    "http://127.0.0.1:20128",
).rstrip("/")

MANAGE_KEY = os.getenv("OMNIROUTE_MANAGE_KEY")

if not MANAGE_KEY:
    print("[ERROR] OMNIROUTE_MANAGE_KEY is not set.")
    print()
    print("This script needs the OmniRoute MANAGEMENT key (not the API key).")
    print("Set it first:")
    print("  Linux/macOS : export OMNIROUTE_MANAGE_KEY='YOUR_KEY'")
    print("  Windows PS  : $env:OMNIROUTE_MANAGE_KEY='YOUR_KEY'")
    sys.exit(1)


# ============================================================
# CONFIRMED MODEL IDS (from omniroute_models.csv)
# ============================================================
#
# Ranked by workload fit, current probe health, capability metadata and
# provider diversity from the latest model/provider CSV exports.
#
# Excluded:
#   - mistral/codestral-latest (hallucination issues)
#   - nvidia/openai/gpt-oss-120b (no tool calling)
#   - nvidia/openai/gpt-oss-20b (no tool calling)
#   - openrouter/auto (meta-router, not a real model)
#   - openrouter/nvidia/nemotron-3.5-content-safety:free (safety-only, no tool calling)
#
# The model list below is the single source of truth. If a model goes
# offline, just remove its line and re-run the script. If you want to
# add a new model, first run list-models-omniroute.py to confirm the
# ID, then add it at the appropriate rank.
#
# ============================================================

# Each combo below corresponds 1:1 to a hidden My-Agents pipeline
# worker. Do NOT rename a combo here without also renaming the
# `model:` field in the matching pipeline-worker-*.md file
# (and the matching agent.cordis.yml persona). The naming is locked.





COMBOS = {
    "free-coding-deep": {
        "strategy": "priority",
        "models": [
            "gc/grok-4.7",
            "kr/qwen3-coder-next",
            "kr/deepseek-3.2",
            "kr/glm-5",
            "kr/minimax-m2.5",
            "kr/minimax-m2.1",
            "no-think/kr/claude-sonnet-4.5",
            "no-think/kr/claude-haiku-4.5",
            "antigravity/gemini-3-flash",
            "gemini/gemini-3-flash-preview",
            "gemini/gemini-2.5-flash",
            "groq/allam-2-7b",
        ],
    },
    "free-coding-standard": {
        "strategy": "priority",
        "models": [
            "kr/qwen3-coder-next",
            "kr/deepseek-3.2",
            "kr/minimax-m2.5",
            "kr/minimax-m2.1",
            "antigravity/gemini-3-flash",
            "gemini/gemini-3-flash-preview",
            "no-think/kr/claude-sonnet-4.5",
            "groq/allam-2-7b",
        ],
    },
    "free-coding-fast": {
        "strategy": "round-robin",
        "models": [
            "antigravity/gemini-3-flash",
            "gemini/gemini-2.5-flash",
            "gemini/gemini-3-flash-preview",
            "groq/allam-2-7b",
            "kr/minimax-m2.1",
            "kr/qwen3-coder-next",
        ],
    },
    "free-reasoning": {
        "strategy": "priority",
        "models": [
            "gc/grok-4.7",
            "kr/deepseek-3.2",
            "kr/glm-5",
            "kr/minimax-m2.5",
            "kr/minimax-m2.1",
            "kr/qwen3-coder-next",
            "gemini/gemini-3-flash-preview",
            "gemini/gemini-2.5-flash",
            "no-think/kr/claude-sonnet-4.5",
            "groq/allam-2-7b",
        ],
    },
    "free-context": {
        "strategy": "priority",
        "models": [
            "gemini/gemini-3.1-pro-preview",
            "gemini/gemini-4-argon",
            "gemini/gemini-3-flash-preview",
            "gemini/gemini-2.5-flash",
            "antigravity/gemini-3-flash",
            "gemini/gemini-3.1-flash-lite",
            "gc/grok-4.7",
            "kr/qwen3-coder-next",
        ],
    },
    "free-vision": {
        "strategy": "priority",
        "models": [
            "antigravity/gemini-3-flash",
            "gemini/gemini-3-flash-preview",
            "gemini/gemini-2.5-flash",
            "no-think/kr/claude-sonnet-4.5",
            "no-think/kr/claude-haiku-4.5",
        ],
    },
}




# ============================================================
# HTTP HELPERS
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "Authorization": f"Bearer {MANAGE_KEY}",
    "Content-Type": "application/json",
})


def get_models():
    """
    Get the currently exposed model IDs.

    This is ONLY used for validation.
    The combo contents themselves are completely hardcoded.
    """

    url = f"{BASE_URL}/api/v1/vscode/{MANAGE_KEY}/models"

    # Never print the actual key.
    safe_url = f"{BASE_URL}/api/v1/vscode/***REDACTED***/models"

    print(f"[GET] {safe_url}")

    response = requests.get(url, timeout=30)

    print(f"[HTTP] {response.status_code}")

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict):
        models = data.get("models", data.get("data", []))
    elif isinstance(data, list):
        models = data
    else:
        models = []

    model_ids = set()

    for item in models:
        if isinstance(item, str):
            model_ids.add(item)

        elif isinstance(item, dict):
            model_id = item.get("id")

            if model_id:
                model_ids.add(model_id)

    return model_ids


def build_validation_ids(exported_ids):
    """
    Convert OmniRoute's exported model IDs into the provider/model
    IDs used by combo targets.

    OmniRoute's model export can expose provider-specific models as:

        claude-sonnet-4-6__provider_antigravity

    while combo targets use:

        antigravity/claude-sonnet-4-6

    Likewise, no-think models may be exported as:

        no-think/antigravity/claude-sonnet-4-6

    while combo targets use:

        antigravity/no-think/claude-sonnet-4-6

    Normal provider/model IDs are kept unchanged.
    """

    validation_ids = set()

    for model_id in exported_ids:

        if not isinstance(model_id, str):
            continue

        validation_ids.add(model_id)

        # ----------------------------------------------------
        # Provider-suffixed export IDs
        #
        # Example:
        #   claude-sonnet-4-6__provider_antigravity
        #
        # becomes:
        #   antigravity/claude-sonnet-4-6
        # ----------------------------------------------------

        provider_marker = "__provider_"

        if provider_marker in model_id:

            model_name, provider = model_id.rsplit(
                provider_marker,
                1,
            )

            if provider and model_name:
                validation_ids.add(
                    f"{provider}/{model_name}"
                )

        # ----------------------------------------------------
        # no-think export IDs
        #
        # Example:
        #   no-think/antigravity/claude-sonnet-4-6
        #
        # becomes:
        #   antigravity/no-think/claude-sonnet-4-6
        # ----------------------------------------------------

        if model_id.startswith("no-think/"):

            remainder = model_id[len("no-think/"):]

            if "/" in remainder:

                provider, model_name = remainder.split(
                    "/",
                    1,
                )

                if provider and model_name:
                    validation_ids.add(
                        f"{provider}/no-think/{model_name}"
                    )

    return validation_ids


def get_combos():
    url = f"{BASE_URL}/api/combos"

    response = SESSION.get(url, timeout=30)

    print(f"[GET] /api/combos -> {response.status_code}")

    response.raise_for_status()

    data = response.json()

    if isinstance(data, dict):
        return data.get("combos", data.get("data", []))

    return data


def get_combo_models(combo):
    """
    Extract the model IDs from an existing combo.

    OmniRoute versions may expose combo entries as either:
        "models": [{"model": "..."}]
    or:
        "targets": [{"model": "..."}]
    or:
        "providers": [{"model": "..."}]

    This helper normalizes those forms into a plain ordered list of
    model IDs so we can compare the existing combo with our hardcoded
    definition without modifying anything unnecessarily.
    """

    if not isinstance(combo, dict):
        return None

    model_entries = combo.get("models")

    if model_entries is None:
        model_entries = combo.get("targets")

    if model_entries is None:
        model_entries = combo.get("providers")

    if model_entries is None:
        return None

    if not isinstance(model_entries, list):
        return None

    normalized = []

    for item in model_entries:

        if isinstance(item, str):
            normalized.append(item)
            continue

        if not isinstance(item, dict):
            return None

        model = item.get("model")

        if model:
            provider = item.get("provider")

            if provider and "/" not in model:
                normalized.append(
                    f"{provider}/{model}"
                )
            else:
                normalized.append(model)

            continue

        # Some API responses may use providerId instead of provider.
        model = item.get("modelId")

        if model:
            provider = item.get("provider") or item.get("providerId")

            if provider and "/" not in model:
                normalized.append(
                    f"{provider}/{model}"
                )
            else:
                normalized.append(model)

            continue

        return None

    return normalized


def update_combo(combo_id, name, strategy, models):
    """
    Update an existing combo in place.

    We intentionally use PATCH instead of deleting and recreating the
    combo. This preserves the existing combo resource and only changes
    its strategy/model configuration.
    """

    url = f"{BASE_URL}/api/combos/{combo_id}"

    payload = {
        "strategy": strategy,
        "models": [
            {
                "model": model
            }
            for model in models
        ],
    }

    response = SESSION.patch(
        url,
        json=payload,
        timeout=30,
    )

    if response.status_code in (200, 201):
        return True

    print()
    print(f"[ERROR] Failed to update combo: {name}")
    print(f"[HTTP] {response.status_code}")
    print(response.text)
    print()

    return False


def create_combo(name, strategy, models):
    url = f"{BASE_URL}/api/combos"

    payload = {
        "name": name,
        "strategy": strategy,
        "models": [
            {
                "model": model
            }
            for model in models
        ],
    }

    response = SESSION.post(
        url,
        json=payload,
        timeout=30,
    )

    if response.status_code in (200, 201):
        return True

    print()
    print(f"[ERROR] Failed to create combo: {name}")
    print(f"[HTTP] {response.status_code}")
    print(response.text)
    print()

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("OmniRoute Free Combo Builder")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print()
    print(f"Hardcoded combos: {len(COMBOS)}")
    print()

    # --------------------------------------------------------
    # STEP 1
    # Validate OmniRoute connectivity
    # --------------------------------------------------------

    print("[STEP 1/4] Fetching current model IDs ...")

    try:
        exported_models = get_models()
    except Exception as exc:
        print()
        print("[ERROR] Could not fetch OmniRoute models.")
        print(exc)
        sys.exit(1)

    print(
        f"[OK] OmniRoute exposes "
        f"{len(exported_models)} model IDs"
    )
    print()

    # Build the normalized provider/model IDs used by combos.
    #
    # This is necessary because OmniRoute's model export and combo
    # endpoints use different representations for some provider
    # specific models.
    available_models = build_validation_ids(exported_models)

    # --------------------------------------------------------
    # STEP 2
    # Validate every hardcoded model
    # --------------------------------------------------------

    print("[STEP 2/4] Validating hardcoded models ...")
    print()

    invalid = []

    for combo_name, combo in COMBOS.items():

        print(f"{combo_name}")
        print(f"  Strategy: {combo['strategy']}")
        print(f"  Models:   {len(combo['models'])}")

        for model in combo["models"]:

            if model in available_models:
                print(f"    [OK] {model}")
            else:
                print(f"    [MISSING] {model}")
                invalid.append((combo_name, model))

        print()

    if invalid:

        print("=" * 80)
        print("[ERROR] Some hardcoded models are not currently exposed.")
        print("=" * 80)
        print()

        for combo_name, model in invalid:
            print(f"{combo_name}: {model}")

        print()
        print("No combos were changed.")
        sys.exit(1)

    print("[OK] All hardcoded models are available.")
    print()

    # --------------------------------------------------------
    # STEP 3
    # Read existing combos and compare ONLY our six combos
    # --------------------------------------------------------

    print("[STEP 3/4] Checking existing versions of our combos ...")
    print()

    try:
        existing = get_combos()
    except Exception as exc:
        print("[ERROR] Could not read existing combos.")
        print(exc)
        sys.exit(1)

    existing_by_name = {}

    for combo in existing:

        if isinstance(combo, dict):
            name = combo.get("name")

            if name:
                existing_by_name[name] = combo

        elif isinstance(combo, str):
            existing_by_name[combo] = {
                "name": combo
            }

    print()

    # --------------------------------------------------------
    # STEP 4
    # Create missing combos or update changed combos
    # --------------------------------------------------------

    print("[STEP 4/4] Creating or updating combos ...")
    print()

    failed = []
    created = []
    updated = []
    skipped = []

    for name, combo in COMBOS.items():

        desired_strategy = combo["strategy"]
        desired_models = combo["models"]

        existing_combo = existing_by_name.get(name)

        # ----------------------------------------------------
        # Combo does not exist
        # ----------------------------------------------------

        if existing_combo is None:

            print(
                f"[CREATE] {name} "
                f"[{desired_strategy}] "
                f"({len(desired_models)} models)"
            )

            success = create_combo(
                name,
                desired_strategy,
                desired_models,
            )

            if success:
                print("  [OK]")
                created.append(name)
            else:
                failed.append(name)

            print()
            continue

        # ----------------------------------------------------
        # Combo exists
        # ----------------------------------------------------

        combo_id = existing_combo.get("id")

        if not combo_id:
            print(f"[ERROR] Existing combo '{name}' has no ID.")
            print("  Cannot safely PATCH this combo.")
            failed.append(name)
            print()
            continue

        existing_strategy = existing_combo.get("strategy")
        existing_models = get_combo_models(existing_combo)

        # Compare both strategy and the ordered model list.
        # Order matters because priority/round-robin combos use the
        # model ordering as part of their configuration.
        strategy_match = existing_strategy == desired_strategy
        models_match = existing_models == desired_models

        if strategy_match and models_match:

            print(
                f"[SKIP] {name} "
                f"[{desired_strategy}] "
                f"({len(desired_models)} models) "
                "already matches."
            )

            skipped.append(name)
            print()
            continue

        print(
            f"[UPDATE] {name} "
            f"[{desired_strategy}] "
            f"({len(desired_models)} models)"
        )

        if not strategy_match:
            print(
                f"  Strategy: "
                f"{existing_strategy!r} -> {desired_strategy!r}"
            )

        if not models_match:

            if existing_models is None:
                print("  Models: unable to normalize existing list")
                print("          -> replacing with hardcoded list")
            else:
                print(
                    f"  Models: "
                    f"{len(existing_models)} -> {len(desired_models)}"
                )

        success = update_combo(
            combo_id,
            name,
            desired_strategy,
            desired_models,
        )

        if success:
            print("  [OK]")
            updated.append(name)
        else:
            failed.append(name)

        print()

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print("=" * 80)

    if failed:

        print("[DONE WITH ERRORS]")
        print()

        if created:
            print("Created:")
            for name in created:
                print(f"  - {name}")

            print()

        if updated:
            print("Updated:")
            for name in updated:
                print(f"  - {name}")

            print()

        if skipped:
            print("Already up to date:")
            for name in skipped:
                print(f"  - {name}")

            print()

        print("Failed combos:")

        for name in failed:
            print(f"  - {name}")

        print()
        print("Existing unrelated combos were left untouched.")
        print("=" * 80)

        sys.exit(1)

    print("[SUCCESS]")
    print()

    if created:
        print("Created:")
        for name in created:
            print(f"  - {name}")

        print()

    if updated:
        print("Updated:")
        for name in updated:
            print(f"  - {name}")

        print()

    if skipped:
        print("Already up to date:")
        for name in skipped:
            print(f"  - {name}")

        print()

    print("Existing unrelated combos were left untouched.")
    print("=" * 80)


if __name__ == "__main__":
    main()
