#!/usr/bin/env python3
"""Shared cost tracker for all experiment runners in this project.

Budget per MISSION.md: total cap $30.00, HARD STOP at $25.00.
Pattern copied from speaker-identity-bias/experiments/cost_tracker.py.

Usage from a runner script:
    from cost_tracker import log_cost, check_budget
    resp = call(model, body)
    log_cost(model, "run-<task_id>-<condition>", usage)   # usage dict, see below
    check_budget()   # raises SystemExit once HARD_STOP_USD is exceeded

`usage` accepts either Gemini usageMetadata keys (promptTokenCount,
candidatesTokenCount, thoughtsTokenCount) or OpenAI-style keys
(prompt_tokens, completion_tokens). Gemini thinking tokens bill as OUTPUT.
"""

import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parent
COST_LOG = ROOT / "cost_log.jsonl"

HARD_STOP_USD = 25.00
TOTAL_CAP_USD = 30.00

# $/1M tokens, conservative (rounded UP from provider pages, checked 2026-09-09).
PRICE = {
    "gemini-3.6-flash": {"in": 0.50, "out": 3.00},
    "gemini-3.1-pro-preview": {"in": 2.00, "out": 12.00},
    "openai/gpt-5.6-luna": {"in": 0.20, "out": 1.20},  # OpenRouter, pinned 2026-09-09
    "modal-qwen2.5-7b": {"in": 0.0, "out": 0.0},  # GPU time logged separately via log_gpu
}
DEFAULT_PRICE = {"in": 2.0, "out": 12.0}  # unknown model -> assume expensive


def _read_all():
    if not COST_LOG.exists():
        return []
    return [json.loads(l) for l in COST_LOG.read_text().splitlines() if l.strip()]


def total_spend():
    return sum(r["est_cost_usd"] for r in _read_all())


def log_cost(model, tag, usage, phase="experiments"):
    tin = usage.get("promptTokenCount", usage.get("prompt_tokens", 0))
    tout = (usage.get("candidatesTokenCount", usage.get("completion_tokens", 0))
            + usage.get("thoughtsTokenCount", 0))
    p = PRICE.get(model, DEFAULT_PRICE)
    cost = (tin * p["in"] + tout * p["out"]) / 1e6
    with COST_LOG.open("a") as f:
        f.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "phase": phase, "model": model, "tag": tag,
            "tokens_in": tin, "tokens_out": tout, "est_cost_usd": round(cost, 6),
        }) + "\n")
    return cost


def log_gpu(tag, hours, usd_per_hour=1.10, phase="experiments"):
    """Log Modal GPU spend (A10G default $1.10/hr) into the same ledger."""
    cost = hours * usd_per_hour
    with COST_LOG.open("a") as f:
        f.write(json.dumps({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "phase": phase, "model": "modal-gpu", "tag": tag,
            "gpu_hours": round(hours, 4), "est_cost_usd": round(cost, 6),
        }) + "\n")
    return cost


def check_budget():
    spent = total_spend()
    if spent >= HARD_STOP_USD:
        raise SystemExit(
            f"HARD STOP: logged spend ${spent:.4f} >= cap ${HARD_STOP_USD:.2f}. "
            "Halting all further API calls. Review experiments/cost_log.jsonl."
        )
    return spent


if __name__ == "__main__":
    print(f"Total logged spend: ${total_spend():.4f} / hard-stop ${HARD_STOP_USD:.2f} "
          f"/ total cap ${TOTAL_CAP_USD:.2f}")
