# Project handoff

**The Schema Changed and Nobody Told the Agent** — silent failure and diff-conditioned
recovery under tool-schema drift.

Welcome. This project is now yours. The testbed is frozen, the experiments are run, the
analysis is scripted, and the website and film explain the results. Your job is to first
reproduce it, then understand it, then improve it. This document says how, in that order.

| | |
|---|---|
| **What exists** | Frozen testbed, 4,800 logged episodes, one analysis script, figures, website, film |
| **Your first task** | Reproduce the analysis and figures on your machine (Section 1, no API keys needed) |
| **Then** | Understand the design (Section 2–3), then the roadmap (Section 5) |
| **Money spent so far** | under $8 of API spend plus 1.7 GPU hours |
| **Money needed for the roadmap** | roughly $30–40 plus a few GPU hours |

---

## 1. Your first task: reproduce it

Do this before anything else. It takes about an hour, costs nothing, and at the end you will
know that every number on the website is one you can regenerate yourself.

1. **Watch and read the website** (about 20 minutes):
   https://abraar237.github.io/shema-drift-research/. The film at the top is 3:25 and gives
   the whole story; the sections below it give the numbers and figures.
2. **Clone and set up** following the **Setup** section of [`README.md`](README.md).
3. **Run the four checks** from the README's *Reproduce* section, in order:
   - `python3 -m pytest experiments/test_mechanics.py -q` → 12 passed.
   - `python3 experiments/build_testbed.py` → the printed hash matches
     `experiments/testbed_frozen.sha256`.
   - `python3 experiments/analyze.py` → `git status --short results` prints nothing. The
     analysis is seeded, so the output must be byte-identical to the committed file.
   - `python3 figures/build_figures.py` → three PDFs in `figures/out/`. Open them and
     compare with the figures on the website.
4. **Read the raw data.** Open `results/runs_gemini-3.6-flash_core.jsonl` and find one
   record each with `cond` equal to `A`, `B_strict`, `C`, `D`, `E`. Read the prompt, the tool
   schema the model saw, the call it made, and the executor's response. Then open
   `results/runs_openai_gpt-5.6-luna_core.jsonl`, filter to `cond == "C"`, and look at what
   the model did with the schema diff sitting in its system prompt. The website's most
   quotable claim ("the diff does nothing for models that ignore it") becomes concrete once
   you have seen a v1-style call emitted under a v2 change log.
5. **Read `results/audit_accepted_wrong_sample.json`**, the 24 hand-checked calls that were
   accepted without error and did the wrong thing.

If all four checks pass and you can explain to someone else what one record in the log
contains, you are ready to go on. If a check fails, fix your environment before touching
anything else, and do not edit `results/`.

## 2. The project in one paragraph

An agent that calls tools carries a copy of each tool's schema in its prompt. The service
behind the tool enforces its own copy. In deployment the two drift apart: a parameter is
renamed, an enum value retired, an optional field made mandatory, an integer turned into a
formatted string, a default flipped. We froze a testbed of 30 tools and 120 checkable tasks,
applied each of those five changes one at a time, and watched four model families call the
drifted tools without being told. Success collapses. Some failures raise errors; some are
accepted and do the wrong thing, like paying in the wrong currency. Then we compared three ways
of telling the agent: a 28-token structured diff, the full new schema, or the raw error and a
retry. The diff repairs almost everything for the two Gemini models and nothing for the other
two, and why that is remains the open question.

## 3. What is already done

**Literature.** 55 papers, every arXiv ID verified (`lit_review/`), with full-text reads of the
three closest benchmarks (MCPEvol-Bench, ToolBench-X, ToolMisuseBench). "First drift
benchmark" is taken; this project's contribution is the recovery comparison and the
wrong-semantics ledger. Keep that framing.

**Pre-registration.** Four directions were written into `MILESTONES.md` with dates before any
data. One reversed for a mechanical reason foreseen at registration; one missed its token
target (13.7% instead of under 10%); two held. Keep this habit: write the prediction down
before each new arm.

**Testbed.** SchemaDrift-120: 30 tools across ten domains, 120 tasks (90 single-step, 30
two-step), two phrasings each, five deterministic minimal-pair drift classes, 240 task-drift
pairs (48 per class), a strict/lenient mock executor, and a three-way outcome ledger
(error surfaced / accepted correct / accepted wrong). Frozen with a SHA-256 hash before any
drifted episode; one documented amendment during baseline calibration.

**Experiments.** 4,800 episodes: Gemini 3.6 Flash and Qwen2.5-7B on the full grid plus noise
and phrasing batteries; Gemini 3.1 Pro and GPT-5.6-luna on the primary 120 pairs. Conditions:
baseline (A), silent drift under both executor profiles (B), diff in context (C), full v2
schema (D), raw-error retry (E). 24 accepted-wrong episodes hand-audited, 24/24 confirmed.

**Analysis.** One script produces every number. Within-pair paired differences, bootstrap
CIs, sign-flip permutation, paired effect sizes, direct class × condition interaction tests,
one Benjamini–Hochberg family of 112 tests (74 survive).

**Outreach.** The website (`docs/`), three GIFs, and the film (`video/`).

### The findings, and how much to trust each

| Finding | Evidence | Trust |
|---|---|---|
| Silent drift removes 55–87 points of success | 4 families, paired, all p < 5e-5 | Solid, for drift that always touches a used parameter (an upper bound per drift) |
| Default-change never surfaces an error | Ledger, all families, both profiles | True by construction: a default change cannot fail validation |
| Lenient executor turns rename/type drift into accepted-wrong (67–100%) | Ledger + 24/24 audit | Solid for this executor; the type class was designed to coerce silently |
| Diff recovers 96–98% on Gemini and beats full schema (82–83%) | n = 240 / 120 pairs | Solid; "beats" is partly because the diff carries the deleted old default and the new schema does not |
| Diff recovers nothing on GPT-5.6-luna and Qwen | n = 120 / 240 | Solid as an absence; **unexplained** |
| Filling every optional parameter gives immunity to two classes | 4 families, one point each | Mechanically true; four points is not a trend |
| Retry can only fix what errors | Per-class, Flash | Solid and follows from the ledger |

## 4. Where the study is weak

In order of how much each one hurts:

1. **The most quotable result has no explanation.** Two families ignore the diff. Nobody has
   varied where the diff sits (system prompt, user turn, tool result), how it is phrased
   (JSON vs prose), whether an explicit "apply this change log" instruction helps, or whether
   more thinking budget helps. About $10 to find out.
2. **"Diff beats full schema" is confounded.** The full v2 schema has lost the old default;
   the diff still carries it. The missing conditions are v2 schema + diff together, and v2
   schema with the previous default annotated. About $3.
3. **Some of the silent-failure headline is by construction.** A default change cannot fail
   validation; the type class was chosen so coercion silently mis-scales. Both are
   legitimate design choices and should be described as such.
4. **The executor is a mock** with two hand-designed profiles. No drifted call has been
   replayed through pydantic, FastAPI, or a real MCP server.
5. **Drift always bites, and never in bundles.** Every drift targets a used parameter; there
   is no compound-drift arm and no estimate of how often real changes fall into each class.
6. **Family confound.** Both diff-readers are Gemini; both non-readers are not. Thinking
   budgets differ across families.
7. **Small things:** token sizes are chars/4 estimates rather than tokenizer counts; the
   calling-style plot has four points.

None of these is an invalid result. The problem is one missing explanation and one confounded
comparison, both cheap to fix.

## 5. Roadmap

Do the phases in order. Phase 1 is the cheapest and matters the most.

### Phase 1 — Answer the two open questions (weeks 1–2, about $15)

- [ ] **Diff-following ablation** on GPT-5.6-luna and Qwen2.5-7B (primary 120 pairs):
      placement (system prompt / user turn / tool result) × format (JSON / prose) × explicit
      "apply this change log step by step" instruction × thinking budget where available.
      Report which, if any, unlocks recovery.
- [ ] **Information vs form:** add condition C+D (v2 schema plus the diff) and D′ (v2
      schema with "previous default: X" in the parameter description). If D′ matches C, the
      diff's advantage is information, not artifact form.
- [ ] **Accounting fixes** while the runs go: tokenizer-measured artifact sizes (the measured
      prompt-token means are already in `analysis.json` under `token_costs`); record the
      GPT-5.6-luna thinking setting.

### Phase 2 — Generality (weeks 3–5, about $15–25 plus GPU hours)

- [ ] **Two more families** on the primary 120 pairs, all conditions: one Anthropic model and
      one open-weight 70B-class model (Modal, same pattern as `modal_qwen.py`). This breaks the
      Gemini-vs-rest confound.
- [ ] **Within-model calling-style test:** instruct Flash to fill every optional parameter
      explicitly; measure survival on newly-required + default-change. If it rises toward
      0.96, the axis is causal and not just a family trait.
- [ ] **Real-validator check:** replay all drifted calls (they are in the logs) through
      pydantic, FastAPI, and one OpenAPI or MCP mock server. Report agreement with the strict
      and lenient profiles. No API cost.
- [ ] **Compound-drift arm:** two or three simultaneous edits per tool with one bundled diff,
      Flash and Qwen, 48 pairs.

### Phase 3 — External validity (weeks 6–8, $0–5)

- [ ] **Changelog corpus:** collect 100–200 real schema changes (Stripe, GitHub, Slack API
      changelogs; popular MCP servers' git histories). Classify each into the five classes
      plus "other". Report prevalence and the share that touch parameters an agent would use.
- [ ] **Larger catalog:** 100+ tools in context with one drifted; does the agent find and
      apply the right diff when several are served?
- [ ] **Multi-turn tasks beyond three turns**, if budget allows.

### Phase 4 — Write-up

- [ ] Update `analysis.json`, then the figures, then the website and film, in that order.
- [ ] Write up the extended study. Every claim traces to a number in `analysis.json`.

## 6. How to add an experiment without breaking anything

1. **Write the prediction first.** Add a dated line under the pre-registered directions in
   `MILESTONES.md` before collecting data.
2. **Never edit the frozen testbed in place.** New conditions reuse `testbed_frozen.json`.
   New tools, tasks or drift classes are a new testbed with a new hash; results from the two
   must not be mixed.
3. **Add a condition in `harness.py`**, not in a runner. Conditions are assembled there so
   every family runs the same thing; the runners only supply `call_model`.
4. **Add new models to the price table in `cost_tracker.py`** or the spend cap will not see
   them. Use `--limit 5` first; a smoke test costs cents.
5. **Extend `analyze.py`, do not fork it.** One script producing every number is what makes
   the study checkable. New tests join the BH family; update the family size (currently 112)
   wherever it is stated.
6. **Audit by hand.** For any new accepted-wrong cell or new coding, read 20+ episodes and
   save the sample, as `results/audit_accepted_wrong_sample.json` does.
7. **Numbers flow one way:** raw logs → `analysis.json` → figures → text. Never the reverse.
8. **Report what you find.** A reversed prediction reported honestly is a strength of this
   project. Keep it one.

## 7. Boundaries

- The executor is a local mock. Do not point runners at real third-party APIs with drifted
  calls; the payment and access-control tools are simulations.
- Keep the spend cap armed. Keep `.env` out of git.
- Verify every reference you add against the arXiv or publisher record.
- The testbed is synthetic and contains no real personal data. Keep it that way.

## 8. Things that will trip you up

- The model IDs are from September 2026. Providers retire models; check before a full run and
  record any substitution.
- You will need your own Gemini and OpenRouter keys and a Modal account.
- `build_gifs.py` and `build_film.py` use macOS system fonts.
- The teaser figure is an HTML file screenshotted with headless Chrome.
- Flash flips 13.3% of pairs at temperature 0. Do not read per-class cells that differ by a
  few points as real.
- `MILESTONES.md` and `EXPERIMENT_PLAN.md` describe the original checkpointed workflow. They
  are history and context, not instructions you must follow.

## 9. Progress log

| Date | What | Notes |
|---|---|---|
| 2026-09-23 | Handed over | Reproduce first (Section 1), then Phase 1 |
| | | |

Good luck. The instrument is clean, the statistics are careful, and the diff result is the
kind of thing practitioners quote. Most of the remaining work is explaining it.
