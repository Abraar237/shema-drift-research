#!/usr/bin/env python3
"""Gemini arm runner (Flash + Pro). One episode per record, randomized order,
resume-safe JSONL, temperature 0, cost-tracked with the $25 hard stop.

Usage:
  python3 run_gemini.py --model gemini-3.6-flash --grid core --limit 5      # dry run
  python3 run_gemini.py --model gemini-3.6-flash --grid core
  python3 run_gemini.py --model gemini-3.6-flash --grid noise
  python3 run_gemini.py --model gemini-3.6-flash --grid phrasing
  python3 run_gemini.py --model gemini-3.1-pro-preview --grid core --set primary
"""

import argparse
import json
import pathlib
import random
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import harness  # noqa: E402
from cost_tracker import log_cost, check_budget  # noqa: E402

RESULTS = HERE.parent / "results"
RESULTS.mkdir(exist_ok=True)

CONDS = ["A", "B_strict", "B_lenient", "C", "D", "E"]
THINKING = {"gemini-3.6-flash": "MINIMAL", "gemini-3.1-pro-preview": "LOW"}


def api_key():
    for line in (HERE.parent / ".env").read_text().splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("GEMINI_API_KEY not in .env")


KEY = api_key()


def gemini_call(model, body, tries=6):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={KEY}")
    data = json.dumps(body).encode()
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=data,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:400]
            if e.code == 429 and "prepayment" in msg.lower():
                raise SystemExit(f"GEMINI CREDITS DEPLETED — top up at ai.studio/projects. {msg}")
            if e.code in (429, 500, 503) and attempt < tries - 1:
                time.sleep(2 ** attempt + random.random())
                continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("unreachable")


def make_call_model(model, tag_holder):
    def call_model(system, user, declarations, transcript):
        contents = [{"role": "user", "parts": [{"text": user}]}]
        last_call_id = None
        for turn in transcript:
            if turn["role"] == "assistant_tool_call":
                part = turn.get("raw") or {"functionCall": {"name": turn["name"], "args": turn["args"]}}
                last_call_id = part.get("functionCall", {}).get("id")
                contents.append({"role": "model", "parts": [part]})
            else:
                fr = {"name": turn["name"], "response": {"content": turn["content"]}}
                if last_call_id:
                    fr["id"] = last_call_id
                contents.append({"role": "user", "parts": [{"functionResponse": fr}]})
        body = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system}]},
            "tools": [{"functionDeclarations": declarations}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 1024,
                                 "thinkingConfig": {"thinkingLevel": THINKING[model]}},
        }
        resp = gemini_call(model, body)
        usage = resp.get("usageMetadata", {})
        log_cost(model, tag_holder[0], usage)
        check_budget()
        try:
            parts = resp["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError):
            return {"final": "(empty)"}
        for part in parts:
            if "functionCall" in part:
                fc = part["functionCall"]
                return {"name": fc["name"], "args": fc.get("args", {}), "raw": part}
        text = " ".join(p.get("text", "") for p in parts)
        return {"final": text}
    return call_model


def jobs_for_grid(grid, subset):
    tasks = harness.frozen()["tasks"]
    jobs = []
    if grid == "core":
        for t in tasks:
            classes = t["assigned"][:1] if subset == "primary" else t["assigned"]
            jobs.append((t, "A", t["assigned"][0], 0))
            for cls in classes:
                for cond in ["B_strict", "B_lenient", "C", "D", "E"]:
                    jobs.append((t, cond, cls, 0))
    elif grid == "noise":  # 30 stratified tasks x 5 identical B_strict calls
        strat = [t for i, t in enumerate(sorted(tasks, key=lambda x: x["id"])) if i % 4 == 0]
        for t in strat[:30]:
            for rep in range(5):
                jobs.append((t, "B_strict", t["assigned"][0], 0, rep))
    elif grid == "phrasing":  # A + B_strict on phrasing 2
        for t in tasks:
            jobs.append((t, "A", t["assigned"][0], 1))
            jobs.append((t, "B_strict", t["assigned"][0], 1))
    else:
        raise SystemExit(f"unknown grid {grid}")
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--grid", default="core")
    ap.add_argument("--set", dest="subset", default="doubled", choices=["primary", "doubled"])
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    out_path = RESULTS / f"runs_{args.model.replace('/', '_')}_{args.grid}.jsonl"
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            r = json.loads(line)
            done.add((r["task"], r["cond"], r["class"], r["phrasing"], r.get("rep", 0)))

    jobs = jobs_for_grid(args.grid, args.subset)
    rng = random.Random(42)
    rng.shuffle(jobs)
    if args.limit:
        jobs = jobs[:args.limit]

    tag_holder = [""]
    call_model = make_call_model(args.model, tag_holder)
    n_done = n_skip = 0
    with out_path.open("a") as f:
        for job in jobs:
            t, cond, cls, ph = job[0], job[1], job[2], job[3]
            rep = job[4] if len(job) > 4 else 0
            key = (t["id"], cond, cls, ph, rep)
            if key in done:
                n_skip += 1
                continue
            tag_holder[0] = f"{t['id']}-{cond}-{cls}-p{ph}-r{rep}"
            rec = harness.run_episode(t, cond, cls, call_model, phrasing_idx=ph)
            rec["rep"] = rep
            rec["model"] = args.model
            f.write(json.dumps(rec) + "\n")
            f.flush()
            n_done += 1
            if n_done % 50 == 0:
                print(f"...{n_done} done (skipped {n_skip}), spend ${check_budget():.2f}")
    print(f"DONE: {n_done} new episodes, {n_skip} skipped, total spend ${check_budget():.2f}")


if __name__ == "__main__":
    main()
