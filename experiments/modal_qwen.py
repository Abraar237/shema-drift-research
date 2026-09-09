#!/usr/bin/env python3
"""Qwen2.5-7B-Instruct arm on Modal (A10G, vLLM, hermes tool parser, greedy).
Runs the whole grid INSIDE one container call (episodes hit localhost vLLM),
returns JSONL; local entrypoint saves it and logs GPU spend.

Usage:
  python3 -m modal run modal_qwen.py --grid core --limit 5     # smoke test
  python3 -m modal run modal_qwen.py --grid core
  python3 -m modal run modal_qwen.py --grid noise
  python3 -m modal run modal_qwen.py --grid phrasing
"""

import json
import pathlib
import time

import modal

HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"

MODEL = "Qwen/Qwen2.5-7B-Instruct"
app = modal.App("schemadrift-qwen")
hf_cache = modal.Volume.from_name("schemadrift-hf-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("vllm==0.6.6.post1", "transformers==4.47.1", "requests")
    .env({"HF_HOME": "/hf"})
    .add_local_file(HERE / "harness.py", "/root/harness.py")
    .add_local_file(HERE / "executor.py", "/root/executor.py")
    .add_local_file(HERE / "testbed_frozen.json", "/root/testbed_frozen.json")
)


@app.function(image=image, gpu="A10G", volumes={"/hf": hf_cache}, timeout=3 * 3600)
def run_grid(grid: str = "core", limit: int = 0) -> str:
    import random
    import subprocess
    import sys

    import requests

    sys.path.insert(0, "/root")
    import harness

    log = open("/tmp/vllm.log", "w")
    server = subprocess.Popen(
        ["python", "-m", "vllm.entrypoints.openai.api_server",
         "--model", MODEL, "--port", "8000", "--max-model-len", "8192",
         "--enable-auto-tool-choice", "--tool-call-parser", "hermes",
         "--gpu-memory-utilization", "0.9"],
        stdout=log, stderr=subprocess.STDOUT)
    for _ in range(240):
        if server.poll() is not None:
            print(open("/tmp/vllm.log").read()[-4000:])
            raise RuntimeError("vLLM server process exited")
        try:
            requests.get("http://127.0.0.1:8000/v1/models", timeout=2)
            break
        except Exception:
            time.sleep(5)
    else:
        print(open("/tmp/vllm.log").read()[-4000:])
        raise RuntimeError("vLLM server did not come up")
    hf_cache.commit()  # persist freshly downloaded weights

    def call_model(system, user, declarations, transcript):
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": user}]
        pid = 0
        for turn in transcript:
            if turn["role"] == "assistant_tool_call":
                pid += 1
                messages.append({"role": "assistant", "content": "", "tool_calls": [
                    {"id": f"c{pid}", "type": "function",
                     "function": {"name": turn["name"], "arguments": json.dumps(turn["args"])}}]})
            else:
                messages.append({"role": "tool", "tool_call_id": f"c{pid}",
                                 "content": turn["content"]})
        body = {"model": MODEL, "messages": messages, "temperature": 0, "max_tokens": 700,
                "tools": [{"type": "function", "function": d} for d in declarations]}
        r = requests.post("http://127.0.0.1:8000/v1/chat/completions", json=body, timeout=180)
        r.raise_for_status()
        msg = (r.json().get("choices") or [{}])[0].get("message") or {}
        tcs = msg.get("tool_calls") or []
        if tcs:
            fn = tcs[0].get("function") or {}
            try:
                parsed = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                parsed = {}
            return {"name": fn.get("name", ""), "args": parsed}
        return {"final": (msg.get("content") or "")}

    tasks = harness.frozen()["tasks"]
    jobs = []
    if grid == "core":
        for t in tasks:
            jobs.append((t, "A", t["assigned"][0], 0, 0))
            for cls in t["assigned"]:
                for cond in ["B_strict", "B_lenient", "C", "D", "E"]:
                    jobs.append((t, cond, cls, 0, 0))
    elif grid == "noise":
        strat = [t for i, t in enumerate(sorted(tasks, key=lambda x: x["id"])) if i % 4 == 0]
        for t in strat[:30]:
            for rep in range(5):
                jobs.append((t, "B_strict", t["assigned"][0], 0, rep))
    elif grid == "phrasing":
        for t in tasks:
            jobs.append((t, "A", t["assigned"][0], 1, 0))
            jobs.append((t, "B_strict", t["assigned"][0], 1, 0))
    rng = random.Random(42)
    rng.shuffle(jobs)
    if limit:
        jobs = jobs[:limit]

    lines = []
    for i, (t, cond, cls, ph, rep) in enumerate(jobs):
        rec = harness.run_episode(t, cond, cls, call_model, phrasing_idx=ph)
        rec["rep"] = rep
        rec["model"] = "modal-qwen2.5-7b"
        lines.append(json.dumps(rec))
        if (i + 1) % 100 == 0:
            print(f"...{i+1}/{len(jobs)}")
    server.terminate()
    return "\n".join(lines)


@app.local_entrypoint()
def main(grid: str = "core", limit: int = 0):
    import sys
    sys.path.insert(0, str(HERE))
    from cost_tracker import log_gpu

    t0 = time.time()
    out = run_grid.remote(grid=grid, limit=limit)
    hours = (time.time() - t0) / 3600
    log_gpu(f"qwen-{grid}", hours)
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / f"runs_modal-qwen2.5-7b_{grid}.jsonl"
    existing = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            existing.add((r["task"], r["cond"], r["class"], r["phrasing"], r.get("rep", 0)))
    added = 0
    with path.open("a") as f:
        for line in out.splitlines():
            r = json.loads(line)
            k = (r["task"], r["cond"], r["class"], r["phrasing"], r.get("rep", 0))
            if k not in existing:
                f.write(line + "\n")
                added += 1
    print(f"saved {added} episodes to {path.name}; GPU {hours:.2f} h logged")
