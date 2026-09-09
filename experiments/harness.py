#!/usr/bin/env python3
"""Condition assembly, canonicalization, and per-call/task scoring for
SchemaDrift-120. Model-agnostic: runners supply a `call_model` function that
takes (system_text, user_text, tool_declarations, transcript) and returns a
parsed tool call {"name": .., "args": {..}} or {"final": text}.

Conditions:
  A  agent sees v1, executor v1 (baseline)
  B  agent sees v1, executor v2 (profile strict|lenient)  -> cond ids B_strict, B_lenient
  C  agent sees v1 + structured JSON diff, executor v2 strict
  D  agent sees v2, executor v2 strict
  E  agent sees v1, executor v2 strict, raw error fed back, ONE retry per step
"""

import datetime
import json
import pathlib

import executor as ex

HERE = pathlib.Path(__file__).resolve().parent
_FROZEN = None


def frozen():
    global _FROZEN
    if _FROZEN is None:
        _FROZEN = json.loads((HERE / "testbed_frozen.json").read_text())
    return _FROZEN

SYSTEM = (
    "You are a tool-calling assistant. Complete the user's request by calling the "
    "provided tools with correct arguments. Use parameter defaults by omitting a "
    "parameter when the user does not specify it. Amounts, durations, and sizes must "
    "be expressed in the units the schema asks for. Call one tool at a time; after "
    "all required calls are done, reply with the single word DONE."
)

DIFF_NOTE = (
    "\n\nNOTE: the API behind tool '{tool}' was updated after the schema above was "
    "cached. Machine-readable change log for '{tool}' (apply it when calling):\n{diff}"
)

MAX_CALLS = 4  # hard stop per task episode


def declaration(name, tool_v1, params):
    """Render one tool declaration (provider-neutral JSON schema)."""
    props, req = {}, []
    for pname, p in params.items():
        prop = {"type": p["type"], "description": p["desc"]}
        if "enum" in p:
            prop["enum"] = p["enum"]
        if not p.get("required"):
            prop["description"] += f" (optional; default: {json.dumps(p['default'])})"
        else:
            req.append(pname)
        props[pname] = prop
    return {"name": name, "description": tool_v1["description"],
            "parameters": {"type": "object", "properties": props, "required": req}}


def build_condition(task, cond, drift_class):
    """Return dict with system, user, declarations, active_schemas, profile, retry."""
    tools_v1 = frozen()["tools_v1"]
    dt = task["drift_tool"]
    key = f"{dt}::{drift_class}"
    v2_params = frozen()["v2_schemas"][key]
    diff = frozen()["diffs"][key]

    step_tools = sorted({s["tool"] for s in task["steps"]})
    decls, active, profile, retry = [], {}, "strict", False
    system = SYSTEM
    for name in step_tools:
        t = tools_v1[name]
        shown = t["params"]
        active[name] = t["params"]  # default: v1 everywhere
        if name == dt and cond != "A":
            active[name] = v2_params
            if cond == "D":
                shown = v2_params
        decls.append(declaration(name, t, shown))
    if cond == "A":
        pass
    elif cond in ("B_strict", "E"):
        profile = "strict"
        retry = (cond == "E")
    elif cond == "B_lenient":
        profile = "lenient"
    elif cond == "C":
        system = SYSTEM + DIFF_NOTE.format(tool=dt, diff=json.dumps(diff["changes"], indent=1))
    elif cond == "D":
        pass
    else:
        raise ValueError(cond)
    return {"system": system, "declarations": decls, "active": active,
            "profile": profile, "retry": retry}


# ---------------- canonicalization ----------------

def _norm(v):
    if isinstance(v, str):
        s = v.strip()
        # ISO datetime normalization
        try:
            iso = s.replace("Z", "+00:00")
            dtv = datetime.datetime.fromisoformat(iso)
            if dtv.tzinfo:
                return ("dt", dtv.astimezone(datetime.timezone.utc).isoformat())
            return ("dt", dtv.isoformat())
        except ValueError:
            pass
        # decimal-string normalization
        try:
            return ("num", float(s)) if any(c.isdigit() for c in s) and s.replace(".", "", 1).replace("-", "", 1).isdigit() else ("str", s.casefold())
        except ValueError:
            return ("str", s.casefold())
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, (int, float)):
        return ("num", float(v))
    return ("str", str(v))


def semantically_equal(a, b):
    return _norm(a) == _norm(b)


def effective_gt(gt_args, active_params):
    """Ground-truth effective semantics: GT args + active-schema defaults."""
    out = {}
    for pname, p in active_params.items():
        if pname in gt_args:
            out[pname] = gt_args[pname]
        elif not p.get("required"):
            out[pname] = p["default"]
    return out


def step_outcome(status, payload, gt_args, active_params):
    """Classify one executed drifted-step call."""
    if status == "error":
        return "ERROR_SURFACED"
    eff = payload["effective_args"]
    gt_eff = effective_gt(gt_args, active_params)
    if set(eff) != set(gt_eff):
        return "ACCEPTED_WRONG"
    for k in gt_eff:
        if not semantically_equal(eff[k], gt_eff[k]):
            return "ACCEPTED_WRONG"
    return "ACCEPTED_CORRECT"


# ---------------- episode runner ----------------

def run_episode(task, cond, drift_class, call_model, phrasing_idx=0):
    """Run one task episode. Returns a record dict (JSONL-ready)."""
    setup = build_condition(task, cond, drift_class)
    dt, didx = task["drift_tool"], task["drift_step_index"]
    gt_steps = task["gt_v1"] if cond == "A" else task["gt_v2"][drift_class]

    transcript = []          # provider-neutral: {"role","content"} + tool results
    executed = []            # accepted calls in order: (tool, effective_args, outcome)
    step_ptr = 0
    retries_left = 1 if setup["retry"] else 0
    calls_made = 0
    drift_outcome = None
    error_seen = None

    user_text = task["phrasings"][phrasing_idx]
    while calls_made < MAX_CALLS:
        out = call_model(setup["system"], user_text, setup["declarations"], transcript)
        if out is None or "final" in out:
            break
        calls_made += 1
        name, args = out["name"], out.get("args", {})
        transcript.append({"role": "assistant_tool_call", "name": name, "args": args,
                           "raw": out.get("raw")})
        active = setup["active"].get(name)
        if active is None:  # hallucinated tool
            transcript.append({"role": "tool_result", "name": name,
                               "content": f"Error: unknown tool '{name}'."})
            continue
        # resolve GT for this step (positional: expected step order)
        expected_gt = gt_steps[step_ptr] if step_ptr < len(gt_steps) else None
        # substitute $1.<key> refs in GT with actual step-1 result values
        if expected_gt:
            resolved_gt = {}
            for k, v in expected_gt.items():
                if isinstance(v, str) and v.startswith("$1.") and executed:
                    resolved_gt[k] = executed[0][3].get(v[3:], v)
                else:
                    resolved_gt[k] = v
            expected_gt = resolved_gt
        result_payload = {k: v.replace("{tid}", task["id"]) if isinstance(v, str) else v
                          for k, v in frozen()["tools_v1"][name]["result"].items()}
        status, payload = ex.execute(active, args, setup["profile"], result_payload)
        is_drift_step = (name == dt and step_ptr == didx and cond != "A")
        if status == "error":
            error_seen = payload
            transcript.append({"role": "tool_result", "name": name, "content": f"Error: {payload}"})
            if is_drift_step and drift_outcome is None:
                drift_outcome = "ERROR_SURFACED"
            if retries_left > 0:
                retries_left -= 1
                continue  # condition E only: raw error visible, one retry
            break  # all other conditions: episode ends on first executor error
        # accepted
        outcome = None
        if expected_gt is not None and name == (task["steps"][step_ptr]["tool"] if step_ptr < len(task["steps"]) else None):
            outcome = step_outcome(status, payload, expected_gt, active)
        if is_drift_step:
            drift_outcome = outcome or "ACCEPTED_WRONG"
        executed.append((name, args, outcome, payload["result"], payload["effective_args"]))
        transcript.append({"role": "tool_result", "name": name,
                           "content": json.dumps(payload["result"])})
        if outcome in ("ACCEPTED_CORRECT", "ACCEPTED_WRONG") or outcome is None:
            step_ptr += 1
        if step_ptr >= len(task["steps"]):
            break  # all expected steps executed; success is now decidable

    n_steps = len(task["steps"])
    step_ok = (len([e for e in executed if e[2] == "ACCEPTED_CORRECT"]) == n_steps
               and len(executed) == n_steps)
    return {
        "task": task["id"], "cond": cond, "class": drift_class,
        "phrasing": phrasing_idx, "success": bool(step_ok),
        "drift_outcome": drift_outcome, "error_seen": error_seen,
        "calls_made": calls_made, "n_steps": n_steps,
        "executed": [{"tool": e[0], "args": e[1], "outcome": e[2]} for e in executed],
    }
