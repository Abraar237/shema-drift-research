#!/usr/bin/env python3
"""Build + freeze SchemaDrift-120.

Validates the spec invariants from the FORMAT CONTRACT in testbed_domains_a.py,
derives per-class v2 schemas, structured diffs, and v2 ground truths, assigns two
drift classes per task balanced to 48 per class, and emits testbed_frozen.json
plus its sha256. Any invariant violation is a hard failure.
"""

import hashlib
import json
import pathlib
import random
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from testbed_domains_a import TOOLS_A, TASKS_A  # noqa: E402
from testbed_domains_b import TOOLS_B, TASKS_B  # noqa: E402

CLASSES = ["rename", "enum_tighten", "required", "type_change", "default_change"]
TARGET_PER_CLASS = 48  # 120 tasks x 2 assignments / 5 classes


def _fmt_frac(fr: Fraction) -> str:
    if fr.denominator == 1:
        return str(fr.numerator)
    return str(float(fr))


CONVERTERS = {
    "cents_to_decimal": lambda v: f"{v // 100}.{v % 100:02d}",
    "minutes_to_hours": lambda v: _fmt_frac(Fraction(v, 60)),
    "grams_to_kg": lambda v: _fmt_frac(Fraction(v, 1000)),
    "mb_to_gb": lambda v: _fmt_frac(Fraction(v, 1024)),
    "int_to_plain_string": lambda v: str(v),
}
# converters where naive str(int) coercion is format-valid but semantically wrong scale
RESCALING = {"cents_to_decimal", "minutes_to_hours", "grams_to_kg", "mb_to_gb"}

PY_TYPES = {"string": str, "integer": int, "boolean": bool}


def fail(msg):
    raise SystemExit(f"SPEC VIOLATION: {msg}")


def validate_tool(tool):
    name = tool["name"]
    params = tool["params"]
    for pname, p in params.items():
        if p.get("required"):
            if "default" in p:
                fail(f"{name}.{pname}: required param has default")
        else:
            if "default" not in p:
                fail(f"{name}.{pname}: optional param missing default")
            if "enum" in p and p["default"] not in p["enum"]:
                fail(f"{name}.{pname}: default not in enum")
        if p["type"] not in PY_TYPES:
            fail(f"{name}.{pname}: bad type {p['type']}")
        if not p.get("desc"):
            fail(f"{name}.{pname}: missing desc")
    if not (3 <= len(params) <= 8):
        fail(f"{name}: {len(params)} params out of range")
    drift = tool["drift"]
    if set(drift) != set(CLASSES):
        fail(f"{name}: drift slots {set(drift)}")
    slot_params = [drift[c]["param"] for c in CLASSES]
    if len(set(slot_params)) != 5:
        fail(f"{name}: drift slots not distinct: {slot_params}")
    for c in CLASSES:
        p = params.get(drift[c]["param"]) or fail(f"{name}: drift {c} unknown param")
        if c == "rename":
            if p.get("required"):
                fail(f"{name}: rename target must be optional")
            if drift[c]["new"] in params:
                fail(f"{name}: rename collides with existing param")
        elif c == "enum_tighten":
            if "enum" not in p:
                fail(f"{name}: enum_tighten target has no enum")
            if drift[c]["removed"] not in p["enum"]:
                fail(f"{name}: removed value not in enum")
            if drift[c]["replacement"] in p["enum"]:
                fail(f"{name}: replacement already in enum")
        elif c == "required":
            if p.get("required"):
                fail(f"{name}: required-slot target already required")
        elif c == "type_change":
            if p["type"] != "integer":
                fail(f"{name}: type_change target not integer")
            if drift[c]["converter"] not in CONVERTERS:
                fail(f"{name}: unknown converter")
            if not drift[c].get("new_desc"):
                fail(f"{name}: type_change missing new_desc")
        elif c == "default_change":
            if p.get("required"):
                fail(f"{name}: default_change target must be optional")
            if drift[c]["new_default"] == p["default"]:
                fail(f"{name}: default unchanged")


def validate_args_against_v1(tool, args, ctx):
    params = tool["params"]
    for pname, p in params.items():
        if p.get("required") and pname not in args:
            fail(f"{ctx}: missing required {tool['name']}.{pname}")
    for aname, aval in args.items():
        if aname not in params:
            fail(f"{ctx}: unknown arg {tool['name']}.{aname}")
        p = params[aname]
        if isinstance(aval, str) and aval.startswith("$1."):
            continue  # step-result reference
        if not isinstance(aval, PY_TYPES[p["type"]]) or (p["type"] == "integer" and isinstance(aval, bool)):
            fail(f"{ctx}: {tool['name']}.{aname} type {type(aval).__name__} != {p['type']}")
        if "enum" in p and aval not in p["enum"]:
            fail(f"{ctx}: {tool['name']}.{aname}={aval!r} not in enum")


def derive_eligibility(tool, args):
    d = tool["drift"]
    elig = []
    rp = d["rename"]["param"]
    if rp in args and args[rp] != tool["params"][rp]["default"]:
        elig.append("rename")
    ep = d["enum_tighten"]["param"]
    if args.get(ep) == d["enum_tighten"]["removed"]:
        elig.append("enum_tighten")
    if d["required"]["param"] not in args:
        elig.append("required")
    tp = d["type_change"]["param"]
    if tp in args and not isinstance(args[tp], str):
        elig.append("type_change")
    if d["default_change"]["param"] not in args:
        elig.append("default_change")
    return elig


def derive_v2_schema(tool, cls):
    """Return (v2 params dict, diff record list)."""
    import copy
    params = copy.deepcopy(tool["params"])
    d = tool["drift"][cls]
    p = d["param"] if "param" in d else None
    diffs = []
    if cls == "rename":
        params[d["new"]] = params.pop(p)
        # preserve original key order roughly: acceptable, order not semantic
        diffs.append({"param": p, "change": "renamed", "old": p, "new": d["new"]})
    elif cls == "enum_tighten":
        e = params[p]["enum"]
        params[p]["enum"] = [d["replacement"] if v == d["removed"] else v for v in e]
        if params[p].get("default") == d["removed"]:
            params[p]["default"] = d["replacement"]
        diffs.append({"param": p, "change": "enum_changed", "old": d["removed"], "new": d["replacement"]})
    elif cls == "required":
        old_default = params[p].pop("default")
        params[p]["required"] = True
        diffs.append({"param": p, "change": "now_required", "old": {"default": old_default}, "new": "required, no default"})
    elif cls == "type_change":
        params[p]["type"] = "string"
        old_desc = params[p]["desc"]
        params[p]["desc"] = d["new_desc"]
        diffs.append({"param": p, "change": "type_changed",
                      "old": {"type": "integer", "desc": old_desc},
                      "new": {"type": "string", "desc": d["new_desc"]}})
    elif cls == "default_change":
        old = params[p]["default"]
        params[p]["default"] = d["new_default"]
        diffs.append({"param": p, "change": "default_changed", "old": old, "new": d["new_default"]})
    return params, diffs


def derive_v2_gt(tool, cls, args):
    """Transform the v1 ground-truth args of the drifted step into v2 ground truth."""
    d = tool["drift"][cls]
    p = d["param"]
    out = dict(args)
    if cls == "rename":
        out[d["new"]] = out.pop(p)
    elif cls == "enum_tighten":
        out[p] = d["replacement"]
    elif cls == "required":
        out[p] = tool["params"][p]["default"]
    elif cls == "type_change":
        out[p] = CONVERTERS[d["converter"]](out[p])
    elif cls == "default_change":
        out[p] = tool["params"][p]["default"]  # OLD default, now explicit
    return out


def main():
    tools = TOOLS_A + TOOLS_B
    tasks = TASKS_A + TASKS_B
    if len(tools) != 30:
        fail(f"{len(tools)} tools != 30")
    if len(tasks) != 120:
        fail(f"{len(tasks)} tasks != 120")
    by_name = {}
    for t in tools:
        if t["name"] in by_name:
            fail(f"duplicate tool {t['name']}")
        validate_tool(t)
        by_name[t["name"]] = t

    ids = set()
    per_tool_count = {}
    two_step = 0
    for task in tasks:
        tid = task["id"]
        if tid in ids:
            fail(f"duplicate task id {tid}")
        ids.add(tid)
        dt = task["drift_tool"]
        if dt not in by_name:
            fail(f"{tid}: unknown drift_tool {dt}")
        per_tool_count[dt] = per_tool_count.get(dt, 0) + 1
        step_tools = [s["tool"] for s in task["steps"]]
        if dt not in step_tools:
            fail(f"{tid}: drift_tool not among steps")
        if len(task["steps"]) not in (1, 2):
            fail(f"{tid}: bad step count")
        if len(task["steps"]) == 2:
            two_step += 1
        if len(task["phrasings"]) != 2:
            fail(f"{tid}: needs 2 phrasings")
        for i, step in enumerate(task["steps"]):
            st = by_name.get(step["tool"]) or fail(f"{tid}: unknown step tool")
            validate_args_against_v1(st, step["args"], f"{tid} step{i+1}")
            for v in step["args"].values():
                if isinstance(v, str) and v.startswith("$1."):
                    if i == 0:
                        fail(f"{tid}: step1 cannot reference results")
                    key = v[3:]
                    if key not in by_name[task["steps"][0]["tool"]]["result"]:
                        fail(f"{tid}: bad result ref {v}")
        # eligibility on the drifted step
        dstep = task["steps"][step_tools.index(dt)]
        derived = derive_eligibility(by_name[dt], dstep["args"])
        if set(derived) != set(task["eligible"]):
            fail(f"{tid}: declared eligible {sorted(task['eligible'])} != derived {sorted(derived)}")
        # type_change value must divide exactly
        d = by_name[dt]["drift"]
        tp = d["type_change"]["param"]
        if "type_change" in derived and tp in dstep["args"]:
            conv = d["type_change"]["converter"]
            v = dstep["args"][tp]
            if conv == "minutes_to_hours" and (v * 100) % 60 != 0:
                fail(f"{tid}: {v} minutes not clean in hours")
            if conv == "mb_to_gb" and (v * 100) % 1024 != 0 and v % 1024 != 0:
                fail(f"{tid}: {v} MB not clean in GB")
    if two_step != 30:
        fail(f"{two_step} two-step tasks != 30")
    for name, n in per_tool_count.items():
        if n != 4:
            fail(f"{name}: {n} tasks != 4")

    # ---- balanced assignment: 2 classes per task, 48 per class, deterministic ----
    rng = random.Random(20260909)
    order = sorted(tasks, key=lambda t: t["id"])
    for attempt in range(1000):
        counts = {c: 0 for c in CLASSES}
        assign = {}
        ok = True
        shuffled = order[:]
        rng.shuffle(shuffled)
        for task in shuffled:
            elig = sorted(task["eligible"], key=lambda c: (counts[c], rng.random()))
            picked = elig[:2]
            if len(picked) < 2:
                ok = False
                break
            for c in picked:
                counts[c] += 1
            assign[task["id"]] = picked
        if ok and all(counts[c] == TARGET_PER_CLASS for c in CLASSES):
            break
    else:
        fail(f"could not balance assignment; last counts {counts}")

    # primary set = first assigned class per task (24/class expected; verify)
    primary_counts = {c: 0 for c in CLASSES}
    for tid_, pair in assign.items():
        primary_counts[pair[0]] += 1
    # rebalance primaries by swapping pair order where needed
    for _ in range(2000):
        over = [c for c in CLASSES if primary_counts[c] > 24]
        under = [c for c in CLASSES if primary_counts[c] < 24]
        if not over:
            break
        moved = False
        for tid_, pair in assign.items():
            if pair[0] in over and pair[1] in under:
                primary_counts[pair[0]] -= 1
                primary_counts[pair[1]] += 1
                assign[tid_] = [pair[1], pair[0]]
                moved = True
                break
        if not moved:
            fail(f"cannot balance primary set: {primary_counts}")
    if any(primary_counts[c] != 24 for c in CLASSES):
        fail(f"primary set unbalanced: {primary_counts}")

    # ---- derive v2 schemas, diffs, ground truths ----
    v2_schemas, diffs = {}, {}
    for t in tools:
        for c in CLASSES:
            params, dd = derive_v2_schema(t, c)
            key = f"{t['name']}::{c}"
            v2_schemas[key] = params
            diffs[key] = {"tool": t["name"], "drift_class": c, "changes": dd}

    frozen_tasks = []
    for task in order:
        dt = task["drift_tool"]
        tool = by_name[dt]
        step_tools = [s["tool"] for s in task["steps"]]
        didx = step_tools.index(dt)
        entry = {
            "id": task["id"], "drift_tool": dt, "drift_step_index": didx,
            "steps": task["steps"], "phrasings": task["phrasings"],
            "eligible": sorted(task["eligible"]),
            "assigned": assign[task["id"]],
            "gt_v1": [s["args"] for s in task["steps"]],
            "gt_v2": {c: [
                derive_v2_gt(tool, c, s["args"]) if i == didx else s["args"]
                for i, s in enumerate(task["steps"])
            ] for c in assign[task["id"]]},
        }
        frozen_tasks.append(entry)

    frozen = {
        "name": "SchemaDrift-120", "frozen_at": "2026-09-09",
        "classes": CLASSES, "per_class_pairs": TARGET_PER_CLASS,
        "tools_v1": {t["name"]: {k: t[k] for k in ("domain", "description", "params", "drift", "result")} for t in tools},
        "v2_schemas": v2_schemas, "diffs": diffs, "tasks": frozen_tasks,
    }
    out = HERE / "testbed_frozen.json"
    out.write_text(json.dumps(frozen, indent=1, sort_keys=True, ensure_ascii=False))
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    (HERE / "testbed_frozen.sha256").write_text(sha + "\n")
    print(f"FROZEN OK: 30 tools, 120 tasks ({two_step} two-step), "
          f"assignments {dict(sorted(counts.items()))}, primary {dict(sorted(primary_counts.items()))}")
    print(f"sha256 {sha}")


if __name__ == "__main__":
    main()
