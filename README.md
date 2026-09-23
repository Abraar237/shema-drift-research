# The Schema Changed and Nobody Told the Agent

**Silent failure and diff-conditioned recovery under tool-schema drift.**

Tool-calling agents are built against a tool schema. The schema then versions: fields get
renamed, enums get tightened, optional arguments become required, types change, defaults
change. This project measures what happens when the schema changes and the agent is not told,
and compares three ways of telling it.

**Start here:** the project website explains the whole study with a short film, figures and
the numbers: https://abraar237.github.io/shema-drift-research/

| Condition | Gemini Flash | Gemini Pro | GPT-5.6-luna | Qwen2.5-7B |
|---|---|---|---|---|
| v1 baseline | .992 | .975 | .933 | .867 |
| silent drift (strict executor) | .154 | .108 | .383 | .221 |
| + 28-token structured diff | **.975** | **.942** | .350 | .263 |
| + full v2 schema | .838 | .825 | .692 | .646 |
| + raw-error retry | .442 | .342 | .367 | .471 |

- Drift removes 55–87 points of task success (4,800 episodes, 4 model families).
- Default-change drift never surfaces an error under any validator; a lenient executor turns
  67–100% of rename and type drift into calls accepted with wrong semantics. All 24
  hand-audited wrong-semantics calls are confirmed, including an $80 payment sent as EUR 80.
- A machine-readable diff (13.7% of the schema's tokens) recovers 96–98% of the loss on
  Gemini models and beats full-schema re-injection, because it carries the old contract.
- The same diff recovers nothing on GPT-5.6-luna or Qwen2.5-7B.
- GPT-5.6-luna fills every optional parameter, which makes it mechanically immune to
  newly-required and default-change drift.

Total cost: under $8 of metered API spend plus 1.7 GPU hours (A10G).

**New here?** Read [`HANDOFF.md`](HANDOFF.md). It says what is done, what your first task is,
and what to do after that.

---

## Setup

Tested on macOS with Python 3.13. Linux works; only the GIF builder depends on macOS fonts.

### 1. Python environment

```bash
git clone https://github.com/Abraar237/shema-drift-research.git
cd shema-drift-research
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. API keys and accounts (only for re-running model calls)

```bash
cp .env.example .env        # then fill in the keys
```

| Key / account | Used for |
|---|---|
| `GEMINI_API_KEY` | Gemini 3.6 Flash and 3.1 Pro arms (`run_gemini.py`) |
| `OPENROUTER_API_KEY` | GPT-family arm (`run_openrouter.py`) |
| Modal account (`python3 -m modal token set ...`) | Qwen2.5-7B arm on an A10G (`modal_qwen.py`) |

`.env` is git-ignored. Never commit it. You do **not** need any key to reproduce the analysis,
rebuild the figures, or run the unit tests, because every raw episode is already in `results/`.

---

## Reproduce the results without spending anything (about 2 minutes)

```bash
cd experiments
python3 -m pytest test_mechanics.py -q   # 12 executor/ledger tests must pass
python3 build_testbed.py                 # regenerates the testbed; hash must match testbed_frozen.sha256
python3 analyze.py                       # reads results/runs_*.jsonl -> results/analysis.json
git status --short ../results            # should print nothing: the output is byte-identical
cd ../figures
python3 build_figures.py                 # -> figures/out/fig2_conditions_recovery.pdf, fig3_ledger.pdf, fig4_argstyle.pdf
```

The bootstrap and permutation tests are seeded, so a clean re-run reproduces the committed
`analysis.json` exactly. If `git status` shows a diff, something in your environment differs;
find out what before going further.

**Number discipline.** Every number on the website and in the figures comes from
`results/analysis.json`. If you change data or analysis, regenerate that file, then rebuild
the figures, then update any text. Never the reverse.

## Re-run the experiments from scratch (about $8 + 1.7 GPU hours)

```bash
cd experiments
python3 run_gemini.py --model gemini-3.6-flash --grid core --limit 5   # dry run first
python3 run_gemini.py --model gemini-3.6-flash --grid core
python3 run_gemini.py --model gemini-3.6-flash --grid noise
python3 run_gemini.py --model gemini-3.6-flash --grid phrasing
python3 run_gemini.py --model gemini-3.1-pro-preview --grid core --set primary
python3 run_openrouter.py --model openai/gpt-5.6-luna
python3 -m modal run modal_qwen.py --grid core      # then --grid noise, --grid phrasing
python3 analyze.py
```

- Every runner takes `--limit N` for a cheap smoke test. Run it first after any change.
- Runners are resume-safe (one JSONL record per episode), randomised, temperature 0 or
  greedy, and logged through `cost_tracker.py`, which stops at the $25 hard cap
  (`experiments/cost_log.jsonl` is the spend log).
- The testbed is frozen: `testbed_frozen.json` with its SHA-256 in `testbed_frozen.sha256`.
  If you change tools or tasks, that is a new testbed with a new hash; record it and do not
  mix its results with the old logs.
- Model IDs and prices were current in September 2026. Check that the models still exist
  before a full run.

## Website and film

- `docs/` is the static site served by GitHub Pages. Open `docs/index.html` locally to
  preview. It embeds the film, three GIFs and the figures.
- `figures/fig1_teaser.html` is the study-design figure, screenshotted with headless Chrome.
  `figures/build_gifs.py` writes the three GIFs to `docs/assets/gifs/` (macOS fonts).
- `video/build_film.py` renders the 3:25 film frame by frame from `results/analysis.json`
  and `video/timing.json`, then the frames are muxed with `narration.mp3` and `music.mp3`
  using ffmpeg (`brew install ffmpeg`). Rendered files are git-ignored;
  `docs/assets/film.mp4` is the published copy.

---

## Repository layout

| Path | Contents |
|---|---|
| `HANDOFF.md` | State of the project, your first task, and the roadmap |
| `EXPERIMENT_PLAN.md`, `MILESTONES.md` | Frozen experiment design and the checkpoint log (history; pre-registered directions are recorded in `MILESTONES.md`) |
| `experiments/` | `testbed_domains_a.py`, `testbed_domains_b.py` (tool and task specs), `build_testbed.py` (validate, derive drift, freeze), `executor.py` (mock executor, two profiles), `harness.py` (conditions, canonicalisation, scoring), `run_gemini.py`, `run_openrouter.py`, `modal_qwen.py` (arm runners), `cost_tracker.py`, `analyze.py`, `test_mechanics.py` |
| `results/` | `runs_*.jsonl` (one record per episode), `analysis.json`, `audit_accepted_wrong_sample.json` |
| `figures/` | Figure scripts, shared style, teaser, GIF builder |
| `lit_review/` | 55-paper verified literature review and novelty delineation |
| `docs/` | Project website |
| `video/` | Film source (`build_film.py`, narration, music, timing) |
| `site/plan.html` | The experiment plan as a readable page |

## Where a number comes from

| Website / figure element | `analysis.json` block (under `models/<model>/`) | Raw logs |
|---|---|---|
| Success by condition, recovery per lever (Fig. 2) | `success_rate`, `drop`, `levers` | `runs_<model>_core.jsonl` |
| Outcome ledger (Fig. 3) | `ledger` | same |
| Per-class success, interaction tests | `success_by_class`, `interaction` | same |
| Calling style (Fig. 4) | `arg_style` | same |
| Noise floor, phrasing battery | `noise_floor`, `phrasing_battery` | `runs_*_noise.jsonl`, `runs_*_phrasing.jsonl` |
| Token accounting | top-level `token_costs` | all |
| Multiple-comparison correction | top-level `bh` | all |
