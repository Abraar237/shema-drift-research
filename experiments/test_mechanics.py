#!/usr/bin/env python3
"""Unit tests for executor + harness mechanics. Run: python3 -m pytest test_mechanics.py -q

Covers the frozen per-class x profile ledger mechanics:
  RENAME          strict=ERROR_SURFACED  lenient=ACCEPTED_WRONG (dropped -> default)
  ENUM-TIGHTEN    strict=ERROR           lenient=ERROR
  REQUIRED        strict=ERROR           lenient=ERROR
  TYPE-CHANGE     strict=ERROR           lenient=ACCEPTED_WRONG (coerced, wrong scale)
  DEFAULT-CHANGE  strict=ACCEPTED_WRONG  lenient=ACCEPTED_WRONG (no violation to catch)
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import executor as ex
from harness import step_outcome, semantically_equal, effective_gt

V1 = {
    "recipient":   {"type": "string", "desc": "x", "required": True},
    "amount_cents": {"type": "integer", "desc": "x", "required": True},
    "currency":    {"type": "string", "desc": "x", "default": "USD"},
    "speed":       {"type": "string", "enum": ["standard", "instant", "scheduled"], "default": "standard", "desc": "x"},
    "funding_source": {"type": "string", "desc": "x", "default": "default_balance"},
    "memo":        {"type": "string", "desc": "x", "default": ""},
}
RES = {"payment_id": "pay_t"}
AGENT_CALL = {"recipient": "@a", "amount_cents": 1250, "speed": "instant", "memo": "Lunch"}


def v2(cls):
    import copy
    p = copy.deepcopy(V1)
    if cls == "rename":
        p["reference"] = p.pop("memo")
    elif cls == "enum":
        p["speed"]["enum"] = ["standard", "realtime", "scheduled"]
    elif cls == "required":
        p["funding_source"] = {"type": "string", "desc": "x", "required": True}
    elif cls == "type":
        p["amount_cents"] = {"type": "string", "desc": "decimal", "required": True}
    elif cls == "default":
        p["currency"]["default"] = "EUR"
    return p


def outcome(cls, profile, gt):
    status, payload = ex.execute(v2(cls), AGENT_CALL, profile, RES)
    return step_outcome(status, payload, gt, v2(cls))


def test_rename_strict_errors():
    status, msg = ex.execute(v2("rename"), AGENT_CALL, "strict", RES)
    assert status == "error" and "memo" in msg


def test_rename_lenient_silent_wrong():
    gt = {"recipient": "@a", "amount_cents": 1250, "speed": "instant", "reference": "Lunch"}
    assert outcome("rename", "lenient", gt) == "ACCEPTED_WRONG"


def test_enum_errors_both():
    for prof in ("strict", "lenient"):
        status, msg = ex.execute(v2("enum"), AGENT_CALL, prof, RES)
        assert status == "error" and "instant" in msg and "realtime" in msg


def test_required_errors_both():
    for prof in ("strict", "lenient"):
        status, msg = ex.execute(v2("required"), AGENT_CALL, prof, RES)
        assert status == "error" and "funding_source" in msg


def test_type_strict_errors():
    status, msg = ex.execute(v2("type"), AGENT_CALL, "strict", RES)
    assert status == "error" and "amount_cents" in msg and "expected string" in msg


def test_type_lenient_coerces_wrong_scale():
    gt = dict(AGENT_CALL, amount_cents="12.50")
    assert outcome("type", "lenient", gt) == "ACCEPTED_WRONG"  # "1250" != "12.50"


def test_default_change_silent_wrong_both():
    gt = dict(AGENT_CALL, currency="USD")  # intent cued by "$"
    for prof in ("strict", "lenient"):
        assert outcome("default", prof, gt) == "ACCEPTED_WRONG"


def test_v2_correct_call_accepted_correct():
    call = dict(AGENT_CALL, currency="USD")
    v = v2("default")
    status, payload = ex.execute(v, call, "strict", RES)
    gt = dict(AGENT_CALL, currency="USD")
    assert step_outcome(status, payload, gt, v) == "ACCEPTED_CORRECT"


def test_baseline_v1_accepted_correct():
    status, payload = ex.execute(V1, AGENT_CALL, "strict", RES)
    assert step_outcome(status, payload, AGENT_CALL, V1) == "ACCEPTED_CORRECT"


def test_semantic_equality():
    assert semantically_equal("2026-10-06T14:00:00Z", "2026-10-06T14:00:00+00:00")
    assert semantically_equal("1.50", "1.5")
    assert semantically_equal(1250, 1250.0)
    assert not semantically_equal("12.50", "1250")
    assert not semantically_equal(True, False)


def test_effective_gt_fills_active_defaults():
    eff = effective_gt(AGENT_CALL, v2("default"))
    assert eff["currency"] == "EUR"  # active default fills when GT omits


def test_unknown_tool_param_dropped_lenient():
    status, payload = ex.execute(V1, dict(AGENT_CALL, bogus=1), "lenient", RES)
    assert status == "accepted" and "bogus" not in payload["effective_args"]


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
