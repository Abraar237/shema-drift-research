# The Schema Changed and Nobody Told the Agent

**Silent failure and diff-conditioned recovery under tool-schema drift.**
Mohammed Abraar, Vizuara Research.

Paper: [named preprint](paper/iclr/paper_iclr_preprint.pdf) · [anonymous build](paper/iclr/paper_iclr_submission.pdf) · Website: https://abraar237.github.io/shema-drift-research/

Tool-calling agents are built against a tool schema. The schema then versions: fields get
renamed, enums get tightened, optional arguments become required, types change, defaults
change. We measure what happens when the schema changes and the agent is not told.

## Headline results (4,800 episodes, 4 model families)

| Condition | Gemini Flash | Gemini Pro | GPT-5.6-luna | Qwen2.5-7B |
|---|---|---|---|---|
| v1 baseline | .992 | .975 | .933 | .867 |
| silent drift (strict executor) | .154 | .108 | .383 | .221 |
| + 28-token structured diff | **.975** | **.942** | .350 | .263 |
| + full v2 schema | .838 | .825 | .692 | .646 |
| + raw-error retry | .442 | .342 | .367 | .471 |

1. **Drift removes 55 to 87 points of task success.**
2. **Default-change drift never surfaces an error under any validator**, and a lenient
   executor converts 67 to 100 percent of rename and type drift into calls accepted with
   wrong semantics. All 24 hand-audited wrong-semantics calls are confirmed, including an
   $80 payment executed as EUR 80 and a $2,500 invoice issued as $250,000.
3. **A machine-readable schema diff (13.7 percent of the schema's tokens) recovers 96 to 98
   percent of the lost success on Gemini models and beats full-schema re-injection**,
   because the diff carries the old contract, including deleted defaults.
4. **The same diff recovers nothing on GPT-5.6-luna and Qwen2.5-7B**: both keep emitting
   old-schema calls with the change log in context.
5. **Calling style is a mechanical exposure axis**: GPT-5.6-luna fills every optional
   parameter explicitly and is therefore immune to newly-required and default-change drift.

## SchemaDrift-120

A frozen testbed: 30 tools, 120 programmatically checkable tasks, five deterministic
minimal-pair drift classes (rename, enum-tighten, newly-required, type-change,
default-change), a dual-profile mock executor (strict / lenient), and a per-call outcome
ledger (error surfaced / accepted correct / accepted with wrong semantics).

- `experiments/testbed_frozen.json` — the frozen instrument (hash in `experiments/testbed_frozen.sha256`)
- `experiments/build_testbed.py` — validator + drift derivation + freeze
- `experiments/executor.py`, `experiments/harness.py` — executor, conditions, scoring (unit tests in `test_mechanics.py`)
- `experiments/run_gemini.py`, `run_openrouter.py`, `modal_qwen.py` — arm runners (resume-safe JSONL, temperature 0, cost-tracked)
- `experiments/analyze.py` — every number in the paper traces to `results/analysis.json`
- `results/` — raw episode logs, analysis output, the audited wrong-semantics sample, spend log
- `figures/` — figure build scripts (house style module)
- `lit_review/` — verified literature review and novelty delineation

Total marginal compute: under 8 US dollars of metered API spend plus 1.7 GPU hours (A10G).

## Reproduce

```bash
cd experiments
python3 -m pytest test_mechanics.py -q   # executor/ledger mechanics
python3 build_testbed.py                 # regenerate + verify the frozen testbed hash
python3 analyze.py                       # rebuild results/analysis.json from raw logs
```

Runner scripts need `GEMINI_API_KEY` / `OPENROUTER_API_KEY` in `../.env` (never committed)
and a Modal account for the open-weight arm.
