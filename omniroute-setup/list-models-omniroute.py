#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================================
# OmniRoute Model/Provider Exporter
# ============================================================================
#
# PURPOSE
# -------
# This script is a READ-ONLY diagnostic tool. It exports the current
# list of models and providers from a running OmniRoute instance to
# CSV and JSON files. It does NOT create, update, or delete anything
# in OmniRoute.
#
# WHY YOU WOULD RUN IT
# --------------------
# 1. To see which models are currently available before editing
#    `omniroute_free_combos.py` (the combo builder).
# 2. To check that all model IDs used in the combo builder are still
#    present in OmniRoute.
# 3. To generate a snapshot of the provider pool for audit/debug.
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
# 3. Run the script from inside the setup/omniroute/ directory:
#
#      cd ~/.agents/omniroute-setup
#      python3 list-models-omniroute.py
#
#    By default, completed probes are resumed from the CSV checkpoint. To
#    ignore the checkpoint and start every probe again:
#
#      python3 list-models-omniroute.py --fresh
#
# 4. The script writes five files into the current working directory:
#
#      omniroute_models.csv         (flat table with resumable probe status)
#      omniroute_providers.csv      (flat table of every provider)
#      omniroute_models_raw.json    (exact response from OmniRoute)
#      omniroute_models.json         (only working/quota-exceeded models)
#      omniroute_providers_raw.json (exact response from OmniRoute)
#
# 5. Feed the CSVs back to the combo builder (`omniroute_free_combos.py`)
#    when you want to refresh or audit the model list.
#
# LANGUAGE / REQUIREMENTS
# -----------------------
# Python 3.8+ with the `requests` and `rich` libraries:
#
#      python -m pip install -r req.txt
#
# ============================================================================

import csv
import argparse
import json
import os
import sys
from pathlib import Path

import requests
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Column
from rich.text import Text


# ============================================================================
# CONFIGURATION
# ============================================================================
#
# You can override the OmniRoute base URL via the OMNIROUTE_BASE_URL
# environment variable. Default is http://localhost:20128 which matches
# the local OmniRoute instance.
#
# The management key is REQUIRED. It is a DIFFERENT key from
# OMNIROUTE_API_KEY (the inference key used by the subagents).
# ============================================================================

# Recommended: keep the key in an environment variable.
OMNIROUTE_MANAGE_KEY = os.environ.get("OMNIROUTE_MANAGE_KEY", "").strip()
OMNIROUTE_API_KEY = os.environ.get("OMNIROUTE_API_KEY", "").strip()

OMNIROUTE_BASE_URL = os.environ.get(
    "OMNIROUTE_BASE_URL",
    "http://localhost:20128",
).rstrip("/")

MODELS_API_URL = (
    f"{OMNIROUTE_BASE_URL}/api/v1/vscode/"
    f"{OMNIROUTE_MANAGE_KEY}/models"
)

PROVIDERS_API_URL = f"{OMNIROUTE_BASE_URL}/api/providers"

REQUEST_TIMEOUT = 10
MODEL_TEST_TIMEOUT = 5

MODELS_CSV = "omniroute_models.csv"
PROVIDERS_CSV = "omniroute_providers.csv"

MODELS_RAW = "omniroute_models_raw.json"
MODELS_FILTERED = "omniroute_models.json"
PROVIDERS_RAW = "omniroute_providers_raw.json"

MODEL_TEST_URL = f"{OMNIROUTE_BASE_URL}/v1/chat/completions"

# Exclude OmniRoute's automatic routing aliases and OpenCode Zen models from
# the CSV used to audit model candidates. The raw JSON remains unfiltered.
EXCLUDED_MODEL_ID_PREFIXES = ("auto/",)
EXCLUDED_MODEL_OWNERS = ("opencode",)
RATE_LIMIT_MARKERS = (
    "rate limit",
    "ratelimit",
    "too many requests",
    "quota",
    "insufficient_quota",
    "quota exceeded",
)


# ============================================================================
# HELPERS
# ============================================================================

def normalize_value(value):
    """Keep nested JSON/list values intact inside a CSV cell."""
    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    return value


class LogStream:
    """Write command output to the selected log without duplicating it."""

    def __init__(self, handle):
        self.handle = handle

    def write(self, value):
        self.handle.write(value)
        self.handle.flush()

    def flush(self):
        self.handle.flush()

    def isatty(self):
        return False


class ProgressDisplay:
    """Render model probe progress with Rich while recording plain log lines."""

    def __init__(self, total, terminal, log_handle, info_lines, models):
        self.total = total
        self.log_handle = log_handle
        self.passed = sum(
            1
            for model in models
            if model_status(model.get("status", 0))
            and str(model.get("working", "")).lower() == "true"
        )
        self.failed = sum(
            1
            for model in models
            if model_status(model.get("status", 0))
            and str(model.get("working", "")).lower() != "true"
        )
        self.initial_completed = self.passed + self.failed
        self.console = Console(
            file=terminal,
            force_terminal=True,
            color_system="standard",
            soft_wrap=False,
        )
        self.progress = Progress(
            TextColumn(
                "[{task.completed}/{task.total}]",
                markup=False,
                table_column=Column(
                    width=11,
                    no_wrap=True,
                ),
            ),
            TextColumn(
                "{task.fields[model]}",
                table_column=Column(
                    ratio=1,
                    overflow="ellipsis",
                    no_wrap=True,
                ),
            ),
            BarColumn(bar_width=24),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TextColumn(
                "{task.fields[state]}",
                table_column=Column(
                    width=24,
                    overflow="ellipsis",
                    no_wrap=True,
                ),
            ),
            console=self.console,
            expand=True,
            auto_refresh=False,
            redirect_stdout=False,
            redirect_stderr=False,
        )
        self.summary = Text()
        self.live = Live(
            Group(self.progress, self.summary),
            console=self.console,
            refresh_per_second=10,
            transient=False,
            redirect_stdout=False,
            redirect_stderr=False,
        )
        self.console.print(
            Panel(
                Group(
                    Text("OMNIROUTE MODEL EXPORTER", style="bold cyan"),
                    *(
                        Text(line, style="white")
                        for line in info_lines
                    ),
                ),
                border_style="cyan",
                title="OmniRoute",
                title_align="left",
                padding=(0, 1),
            )
        )
        self.task_id = self.progress.add_task(
            "health checks",
            total=total,
            completed=self.initial_completed,
            model=(
                "Resuming..."
                if self.initial_completed
                else "Starting..."
            ),
            state=(
                "[yellow]checkpoint[/yellow]"
                if self.initial_completed
                else "[dim]waiting[/dim]"
            ),
        )
        self._refresh_summary(self.initial_completed)
        self.live.start()
        self.live.refresh()

        log_lines = [
            "OMNIROUTE MODEL EXPORTER",
            *info_lines,
        ]
        self.log_handle.write("\n".join(log_lines) + "\n")
        self.log_handle.flush()

    def update(self, completed, model_id, result=None, resumed=False):
        state = "resumed" if resumed else (
            "ok" if result and result.get("working") else "failed"
        )
        reason = ""
        if state == "failed":
            reason = (
                (result or {}).get("reason")
                or (result or {}).get("failure_reason")
                or "unknown"
            )
        state_label = (
            f"FAIL: {reason}" if reason else state.upper()
        )
        state_style = "green" if state in ("ok", "resumed") else "red"
        state_text = Text(state_label, style=state_style)
        if not resumed and result and result.get("working"):
            self.passed += 1
        elif not resumed:
            self.failed += 1
        self.progress.update(
            self.task_id,
            completed=completed,
            model=model_id,
            state=state_text,
            refresh=True,
        )
        self._refresh_summary(completed)
        self.live.refresh()
        self.log_handle.write(
            f"[{completed}/{self.total}] | {state_label}: {model_id}\n"
        )
        self.log_handle.write(
            f"PASS: {self.passed} | FAIL: {self.failed} | "
            f"REMAINING: {self.total - completed}\n"
        )
        self.log_handle.flush()

    def _refresh_summary(self, completed=0):
        remaining = max(self.total - completed, 0)
        self.summary.plain = (
            f"PASS: {self.passed} | FAIL: {self.failed} | "
            f"REMAINING: {remaining}"
        )
        self.summary.style = "bold green"

    def close(self):
        self.live.stop()


def is_excluded_model(model):
    """Return whether a model is excluded from the model CSV export."""
    model_id = str(model.get("id", ""))
    owner = str(model.get("owned_by", "")).lower()

    return (
        model_id.startswith(EXCLUDED_MODEL_ID_PREFIXES)
        or owner in EXCLUDED_MODEL_OWNERS
    )


def extract_data(payload, list_keys=("data",)):
    """
    Extract a list from the common OmniRoute response shapes.

    /models normally returns:
        {"data": [...]}

    /api/providers returns:
        {"connections": [...], "total": N}

    A bare list is also accepted.
    """
    if isinstance(payload, str):
        payload = json.loads(payload)

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in list_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value

    raise TypeError(
        "Expected a list or an object containing one of: "
        + ", ".join(list_keys)
    )


def fetch_json(url, headers=None):
    # Never print the API key-containing URL.
    safe_url = url

    if OMNIROUTE_MANAGE_KEY:
        safe_url = safe_url.replace(OMNIROUTE_MANAGE_KEY, "***REDACTED***")

    print(f"[GET] {safe_url}")

    response = requests.get(
        url,
        headers=headers or {},
        timeout=REQUEST_TIMEOUT,
    )

    print(f"[HTTP] {response.status_code} {response.reason}")

    response.raise_for_status()

    return response.json()


def classify_probe_failure(response=None, error=None):
    """Return a stable reason for a failed model probe."""
    status_code = response.status_code if response is not None else None
    body = response.text.lower() if response is not None else ""

    if "quota" in body or "insufficient_quota" in body:
        return "quota_exceeded"

    if status_code == 429 or any(marker in body for marker in RATE_LIMIT_MARKERS):
        return "rate_limited"

    if status_code is not None:
        return f"http_{status_code}"

    if isinstance(error, requests.Timeout):
        return "timeout"

    return "request_error"


def probe_model(model):
    """Send a minimal request using the model's advertised API format."""
    model_id = str(model.get("id", ""))
    model_url = str(model.get("url", ""))
    api_format = str(model.get("api_format", "")).lower()
    uses_responses = (
        api_format == "responses"
        or "/responses#" in model_url
    )
    endpoint = (
        f"{OMNIROUTE_BASE_URL}/v1/responses"
        if uses_responses
        else MODEL_TEST_URL
    )
    payload = (
        {
            "model": model_id,
            "input": "Reply with OK.",
            "max_output_tokens": 16,
        }
        if uses_responses
        else {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": "Reply with OK.",
                },
            ],
            "max_tokens": 16,
            "temperature": 0,
        }
    )

    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": "Bearer " + OMNIROUTE_API_KEY,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=MODEL_TEST_TIMEOUT,
        )

        if response.ok:
            response_payload = response.json()
            has_error = (
                isinstance(response_payload, dict)
                and response_payload.get("error") not in (None, "")
            )
            if isinstance(response_payload, dict) and not has_error:
                return {
                    "id": model_id,
                    "working": True,
                    "status_code": response.status_code,
                    "reason": "ok",
                }

        return {
            "id": model_id,
            "working": False,
            "status_code": response.status_code,
            "reason": classify_probe_failure(response=response),
            "error": response.text[:500],
        }

    except (requests.RequestException, ValueError) as error:
        return {
            "id": model_id,
            "working": False,
            "status_code": None,
            "reason": classify_probe_failure(error=error),
            "error": str(error)[:500],
        }


def test_models(models, progress_writer=None, progress_display=None):
    """Probe candidates and return each model with its health status."""
    tested_models = []
    probe_results = []

    for index, model in enumerate(models, start=1):
        model_id = str(model.get("id", ""))
        print(f"[PING {index}/{len(models)}] {model_id}")

        if model_status(model.get("status", 0)):
            print(f"[RESUME] {model_id} already completed")
            tested_models.append(dict(model))
            if progress_display is not None:
                progress_display.update(
                    index,
                    model_id,
                    result=model,
                    resumed=True,
                )
            continue

        result = probe_model(model)
        probe_results.append(result)

        tested_model = dict(model)
        tested_model["working"] = result["working"]
        tested_model["failure_reason"] = (
            "" if result["working"] else result["reason"]
        )
        tested_model["status"] = 1
        tested_models.append(tested_model)

        if progress_writer is not None:
            progress_writer(tested_models)

        if progress_display is not None:
            progress_display.update(
                index,
                model_id,
                result=result,
            )

        if result["working"]:
            print(f"[OK] {model_id}")
        else:
            print(f"[SKIP] {model_id}: {result['reason']}")

    return tested_models, probe_results


def save_filtered_models(payload, models, filename=MODELS_FILTERED):
    """Save non-excluded models with their health status."""
    if isinstance(payload, dict):
        filtered_payload = dict(payload)
        filtered_payload["data"] = models
    else:
        filtered_payload = models

    save_raw_json(filtered_payload, filename)


def save_raw_json(payload, filename):
    Path(filename).write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"[OK] Saved raw response -> {filename}")


# ============================================================================
# MODEL CSV
# ============================================================================

def export_models_to_csv(payload, filename=MODELS_CSV, tested_models=None):
    models = extract_data(payload, ("data",))
    candidate_models = [
        model
        for model in models
        if isinstance(model, dict) and not is_excluded_model(model)
    ]
    if tested_models is None:
        exportable_models = candidate_models
    else:
        exportable_models = tested_models

    fieldnames = []

    for model in exportable_models:
        for key in model.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    # Put the fields most useful for our router at the beginning.
    preferred = [
        "id",
        "name",
        "status",
        "working",
        "failure_reason",
        "owned_by",
        "root",
        "family",
        "capabilities",
        "toolCalling",
        "vision",
        "supportsThinking",
        "supportedReasoningEfforts",
        "defaultReasoningEffort",
        "context_length",
        "max_input_tokens",
        "max_output_tokens",
        "maxInputTokens",
        "maxOutputTokens",
        "input_modalities",
        "output_modalities",
        "pricing",
        "configurationSchema",
    ]

    ordered = [x for x in preferred if x in fieldnames]
    ordered += [x for x in fieldnames if x not in ordered]

    if not ordered:
        ordered = ["id", "name", "type"]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=ordered,
            extrasaction="ignore",
        )

        writer.writeheader()

        for model in exportable_models:
            writer.writerow({
                field: normalize_value(model.get(field, ""))
                for field in ordered
            })

    excluded_count = len(models) - len(exportable_models)
    print(
        f"[OK] Exported {len(exportable_models)} models "
        f"({excluded_count} excluded or failed health check) -> {filename}"
    )


def load_model_progress(filename=MODELS_CSV):
    """Load saved model status values for a resumable health-check run."""
    if not Path(filename).exists():
        return {}

    with open(filename, newline="", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        return {
            str(row.get("id", "")): row
            for row in rows
            if row.get("id")
        }


def model_status(value):
    """Normalize CSV status values to an integer checkpoint flag."""
    return 1 if str(value).strip() == "1" else 0


def merge_saved_progress(models, saved_rows):
    """Carry prior probe results into the current model metadata."""
    merged = []

    for model in models:
        model_id = str(model.get("id", ""))
        saved = saved_rows.get(model_id, {})
        current = dict(model)

        if model_status(saved.get("status", 0)):
            current["status"] = 1
            current["working"] = str(saved.get("working", "")).lower() == "true"
            current["failure_reason"] = saved.get("failure_reason", "")
        else:
            current["status"] = 0

        merged.append(current)

    return merged


def reset_model_status(models):
    """Return completed model rows to the fresh-run checkpoint state."""
    reset = []

    for model in models:
        current = dict(model)
        current["status"] = 0
        reset.append(current)

    return reset


# ============================================================================
# PROVIDER CSV
# ============================================================================

def export_providers_to_csv(payload, filename=PROVIDERS_CSV):
    providers = extract_data(payload, ("connections", "data", "providers"))

    if isinstance(payload, dict) and "total" in payload:
        print(
            f"[INFO] /api/providers reports total="
            f"{payload.get('total')} connections"
        )

    fieldnames = []

    for provider in providers:
        if not isinstance(provider, dict):
            continue

        for key in provider.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    preferred = [
        "id",
        "provider",
        "name",
        "authType",
        "priority",
        "isActive",
        "testStatus",
        "backoffLevel",
        "lastHealthCheckAt",
        "lastTested",
        "expiresAt",
        "tokenExpiresAt",
        "expiresIn",
        "maxConcurrent",
        "consecutiveUseCount",
        "lastUsedAt",
        "rateLimitProtection",
        "proxyEnabled",
        "perKeyProxyEnabled",
        "quotaVisible",
        "errorCode",
        "lastErrorType",
        "lastError",
        "rateLimitedUntil",
        "providerSpecificData",
    ]

    ordered = [x for x in preferred if x in fieldnames]
    ordered += [x for x in fieldnames if x not in ordered]

    if not ordered:
        ordered = ["id", "provider", "name", "isActive", "testStatus"]

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=ordered,
            extrasaction="ignore",
        )

        writer.writeheader()

        for provider in providers:
            if not isinstance(provider, dict):
                continue

            writer.writerow({
                field: normalize_value(provider.get(field, ""))
                for field in ordered
            })

    print(f"[OK] Exported {len(providers)} provider records -> {filename}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export OmniRoute models and providers."
    )
    parser.add_argument(
        "-f",
        "--fresh",
        action="store_true",
        help="Ignore saved progress and start all model health checks again.",
    )
    parser.add_argument(
        "--log-file",
        default="output.log",
        help="Write full output to this absolute or relative log path.",
    )
    args = parser.parse_args()

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log_path = Path(args.log_file).expanduser().resolve()
    log_mode = (
        "w"
        if args.fresh or not Path(MODELS_CSV).exists()
        else "a"
    )
    log_handle = open(log_path, log_mode, encoding="utf-8")
    sys.stdout = LogStream(log_handle)
    sys.stderr = LogStream(log_handle)
    progress_display = None

    try:
        if log_mode == "a":
            print()
            print("=" * 80)
            print("[RESUME] Continuing with the existing output log.")
            print("=" * 80)
            print()

        if not OMNIROUTE_MANAGE_KEY:
            raise RuntimeError(
                "OMNIROUTE_MANAGE_KEY is not set.\n\n"
                "PowerShell:\n"
                '$env:OMNIROUTE_MANAGE_KEY = "YOUR_API_KEY"\n'
            )

        if not OMNIROUTE_API_KEY:
            raise RuntimeError(
                "OMNIROUTE_API_KEY is not set. It is required to health-check "
                "each model.\n\n"
                "PowerShell:\n"
                '$env:OMNIROUTE_API_KEY = "YOUR_INFERENCE_KEY"\n'
            )

        print("=" * 80)
        print("OmniRoute Model + Provider Exporter")
        print("=" * 80)
        print(f"Base URL: {OMNIROUTE_BASE_URL}")
        print()

        # STEP 1 --------------------------------------------------------------
        print("[STEP 1/2] Fetching /models ...")

        models_payload = fetch_json(MODELS_API_URL)

        all_models = extract_data(models_payload, ("data",))
        candidate_models = [
            model
            for model in all_models
            if isinstance(model, dict) and not is_excluded_model(model)
        ]

        saved_rows = load_model_progress(MODELS_CSV)
        if args.fresh:
            candidate_models = reset_model_status(candidate_models)
        elif saved_rows:
            if not any(
                model_status(row.get("status", 0))
                for row in saved_rows.values()
            ):
                raise RuntimeError(
                    "No resumable model probes were found in the checkpoint. "
                    "Use --fresh to start all probes from the beginning."
                )
            candidate_models = merge_saved_progress(
                candidate_models,
                saved_rows,
            )
        else:
            candidate_models = reset_model_status(candidate_models)

        progress_by_id = {
            str(model.get("id", "")): dict(model)
            for model in candidate_models
        }

        def save_progress(completed_models):
            for model in completed_models:
                progress_by_id[str(model.get("id", ""))] = dict(model)

            export_models_to_csv(
                models_payload,
                MODELS_CSV,
                list(progress_by_id.values()),
            )

        export_models_to_csv(
            models_payload,
            MODELS_CSV,
            candidate_models,
        )
        progress_display = ProgressDisplay(
            len(candidate_models),
            original_stdout,
            log_handle,
            [
                f"Health checks: {len(candidate_models)} models",
                f"Endpoint: {OMNIROUTE_BASE_URL}",
                f"Log file: {log_path.name}",
            ],
            candidate_models,
        )
        tested_models, _probe_results = test_models(
            candidate_models,
            progress_writer=save_progress,
            progress_display=progress_display,
        )

        export_models_to_csv(models_payload, MODELS_CSV, tested_models)
        save_filtered_models(models_payload, tested_models)

        working_count = sum(model["working"] for model in tested_models)
        print(
            f"[INFO] Health check marked {working_count} of "
            f"{len(tested_models)} models as working"
        )

        export_models_to_csv(
            models_payload,
            MODELS_CSV,
            reset_model_status(tested_models),
        )

        save_raw_json(
            models_payload,
            MODELS_RAW,
        )

        # STEP 2 --------------------------------------------------------------
        print()
        print("[STEP 2/2] Fetching /api/providers ...")

        providers_payload = fetch_json(
            PROVIDERS_API_URL,
            headers={
                "Authorization": f"Bearer {OMNIROUTE_MANAGE_KEY}",
                "Accept": "application/json",
            },
        )

        export_providers_to_csv(
            providers_payload,
            PROVIDERS_CSV,
        )

        save_raw_json(
            providers_payload,
            PROVIDERS_RAW,
        )

        print()
        print("=" * 80)
        print("DONE")
        print("=" * 80)
        print()
        print("Give me these files for the combo-builder:")
        print(f"  {MODELS_CSV}")
        print(f"  {PROVIDERS_CSV}")
        print()
        print("If anything looks ambiguous, also give me:")
        print(f"  {MODELS_RAW}")
        print(f"  {MODELS_FILTERED}")
        print(f"  {PROVIDERS_RAW}")
        print()
        print("No OmniRoute configuration was changed.")

    except requests.RequestException as e:
        print()
        print("[ERROR] OmniRoute API request failed:")
        print(e)
        original_stdout.write(
            f"\n\033[31m[ERROR] OmniRoute API request failed: {e}\033[0m\n"
        )
        original_stdout.flush()
        raise SystemExit(1)

    except (TypeError, ValueError, RuntimeError) as e:
        print()
        print("[ERROR]")
        print(e)
        original_stdout.write(f"\n\033[31m[ERROR] {e}\033[0m\n")
        original_stdout.flush()
        raise SystemExit(1)

    finally:
        if progress_display is not None:
            progress_display.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_handle.close()
