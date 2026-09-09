#!/usr/bin/env python3
"""Mock executor: validates a tool call against the ACTIVE schema and returns a
realistic error string or (silent) acceptance with the effective arguments.

Profiles:
  strict  — unknown parameter -> error; missing required -> error; enum violation
            -> error; type mismatch -> error.
  lenient — unknown parameters silently DROPPED; type mismatches coerced when
            representable (int -> "int", "3" -> 3); missing required and enum
            violations still error.

The executor never judges semantics; it returns (status, payload):
  ("accepted", {"effective_args": {...}, "result": {...}})
  ("error", "<error string>")
Semantic correctness (ACCEPTED_CORRECT vs ACCEPTED_WRONG) is decided by the
harness by comparing effective args against ground truth.
"""

PY_TYPES = {"string": str, "integer": int, "boolean": bool}


def _type_ok(value, ptype):
    if ptype == "integer" and isinstance(value, bool):
        return False
    return isinstance(value, PY_TYPES[ptype])


def _coerce(value, ptype):
    """Lenient coercion. Returns (ok, coerced)."""
    if ptype == "string" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return True, str(value)
    if ptype == "integer" and isinstance(value, str):
        try:
            return True, int(value)
        except ValueError:
            return False, None
    return False, None


def execute(params_schema, args, profile, result_payload):
    """Validate `args` against `params_schema` under `profile`."""
    assert profile in ("strict", "lenient")
    args = dict(args)

    # 1. unknown parameters
    unknown = [a for a in args if a not in params_schema]
    if unknown:
        if profile == "strict":
            return "error", f"Received unknown parameter: '{unknown[0]}'."
        for a in unknown:
            args.pop(a)  # silently dropped

    # 2. missing required
    for pname, p in params_schema.items():
        if p.get("required") and pname not in args:
            return "error", f"Missing required parameter: '{pname}'."

    # 3. types
    for pname, val in list(args.items()):
        p = params_schema[pname]
        if not _type_ok(val, p["type"]):
            if profile == "lenient":
                ok, coerced = _coerce(val, p["type"])
                if ok:
                    args[pname] = coerced
                    continue
            got = type(val).__name__
            return "error", (f"Invalid type for parameter '{pname}': "
                             f"expected {p['type']}, got {got}.")

    # 4. enums
    for pname, val in args.items():
        p = params_schema[pname]
        if "enum" in p and val not in p["enum"]:
            allowed = ", ".join(str(v) for v in p["enum"])
            return "error", (f"Invalid value '{val}' for parameter '{pname}'. "
                             f"Allowed values: {allowed}.")

    # 5. accept: fill defaults -> effective args
    effective = {}
    for pname, p in params_schema.items():
        if pname in args:
            effective[pname] = args[pname]
        elif not p.get("required"):
            effective[pname] = p["default"]
    return "accepted", {"effective_args": effective, "result": result_payload}
