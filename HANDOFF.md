# Project handoff

**The Schema Changed and Nobody Told the Agent** — silent failure and diff-conditioned
recovery under tool-schema drift.

Welcome. This project is now yours. It is a complete first version: the testbed is frozen,
the experiments are run, the paper is written and builds, the website and film exist. It is
close to, but not yet at, the bar for a top venue. This document tells you plainly where it
stands and what to do about it.

| | |
|---|---|
| **State** | Full draft, 15 pages, ICLR format, anonymous and named builds |
| **Simulated review score** | **5.67 / 10** average (rigor 6, novelty 5, clarity/impact 6) |
| **Estimated ICLR acceptance** | **about 49%** (historical rate for that score band: the coin-flip zone) |
| **Reachable with the roadmap below** | 6.0–6.5 (about 78%) after Phase 1; 6.5–7.0 (about 94%) after Phase 2 |
| **Money spent so far** | under $8 of API spend plus 1.7 GPU hours |
| **Money needed for the roadmap** | roughly $30–40 plus a few GPU hours |

The scores come from a simulated review ([`REVIEW.md`](REVIEW.md)), calibrated against 33,000
real ICLR decisions. They are estimates. Read that file in full before changing anything; it
is the most useful page in the repository.

---

## 1. Your first day

1. Read the paper: `paper/iclr/paper_iclr_submission.pdf`. About 45 minutes.
2. Read [`REVIEW.md`](REVIEW.md). About 20 minutes.
3. Follow **Setup** in [`README.md`](README.md), then run the four no-cost checks:
   - `python3 -m pytest experiments/test_mechanics.py -q` passes 12 tests.
   - `python3 experiments/build_testbed.py` regenerates the testbed with the frozen hash.
   - `python3 experiments/analyze.py` reproduces `results/analysis.json` byte for byte
     (`git status` stays clean).
   - `tectonic paper_iclr_submission.tex` builds a 15-page PDF.
4. Open a few records in `results/runs_openai_gpt-5.6-luna_core.jsonl` with `cond == "C"`
   and read what the model did with the diff sitting in its system prompt. The paper's most
   quotable result ("the diff does nothing for models that ignore it") becomes concrete once
   you have seen a v1-style call emitted under a v2 change log.
5. Skim `lit_review/LIT_REVIEW.md` so you know the closest neighbours (MCPEvol-Bench,
   ToolBench-X, ToolMisuseBench, SilentProbe) and exactly how this work differs from each.

If all four checks pass, you have a working copy and can trust the numbers in the paper.

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

**Literature.** 55 papers, every arXiv ID verified, with full-text reads of the three closest
benchmarks. The verdict was "alive but crowded": "first drift benchmark" framing is taken by
MCPEvol-Bench and ToolBench-X, so the paper leads with the recovery comparison and the
wrong-semantics ledger, and demotes the testbed to an instrument. Keep that framing.

**Pre-registration.** Four directions were written into `MILESTONES.md` with dates before any
data. D1 (newly-required is the most silent class) reversed, for a mechanical reason foreseen
at registration; D2 (diff recovers >50% at <10% token cost) held on recovery for Gemini only
and missed the token target (13.7%); D3 and D4 held. All reported as such. Keep this habit:
write the prediction down before each new arm.

**Testbed.** SchemaDrift-120: 30 tools across ten domains, 120 tasks (90 single-step, 30
two-step), two phrasings each, five deterministic minimal-pair drift classes, 240 task-drift
pairs (48 per class), a strict/lenient mock executor, and a three-way outcome ledger. Frozen
with a SHA-256 hash before any drifted episode; one documented amendment during baseline
calibration.

**Experiments.** 4,800 episodes: Gemini 3.6 Flash and Qwen2.5-7B on the full grid plus noise
and phrasing batteries; Gemini 3.1 Pro and GPT-5.6-luna on the primary 120 pairs. Conditions:
baseline, silent drift (both profiles), diff, full v2 schema, error retry. 24 accepted-wrong
episodes hand-audited, 24/24 confirmed.

**Analysis.** One script produces every number. Within-pair paired differences, bootstrap
CIs, sign-flip permutation, paired d_z, direct class × condition interaction tests, one
Benjamini–Hochberg family of 112 tests (74 survive; the non-survivors are named).

**Paper.** 15 pages, 4 figures, 6 tables, 41 verified references, reproducibility and LLM-use
statements. Two wrappers share one body so the anonymous and named PDFs cannot drift.

**Outreach.** A project website (`docs/`), three GIFs, and a 3:25 narrated film (`video/`).
These describe the current results; update them only after the paper changes.

### The findings, and how much to trust each

| Finding | Evidence | Trust |
|---|---|---|
| Silent drift removes 55–87 points of success | 4 families, paired, all p < 5e-5, d_z 1.1–2.5 | Solid, for drift that always touches a used parameter (an upper bound per drift) |
| Default-change never surfaces an error | Ledger, all families, both profiles | True by construction; say so in the abstract |
| Lenient executor turns rename/type drift into accepted-wrong (67–100%) | Ledger + 24/24 audit | Solid for this executor; the type class was designed to coerce silently |
| Diff recovers 96–98% on Gemini and beats full schema (82–83%) | n = 240 / 120 pairs, BH-surviving | Solid; the "beats" part is partly information content (the diff carries the old default), not form |
| Diff recovers nothing on GPT-5.6-luna and Qwen | n = 120 / 240, recovery −0.06 / 0.06, n.s. | Solid as an absence; **unexplained**: no prompt, placement or format ablation |
| Filling every optional parameter gives immunity to two classes | 4 families, one point each | Mechanically true; "predicts" from n = 4 is an overclaim |
| Retry can only fix what errors (0.00 on rename, −0.06 on default-change) | Per-class, Flash | Solid and follows from the ledger |

## 4. Where the paper is weak

The full argument is in `REVIEW.md`. The short version, in order of how much each one hurts:

1. **The most quotable result has no explanation.** Two families ignore the diff. The paper
   never varies where the diff sits (system prompt, user turn, tool result), how it is
   phrased (JSON vs prose), whether an explicit "apply this change log" instruction helps,
   or whether more thinking budget helps. Every reviewer will ask for this experiment. It
   costs about $10.
2. **"Diff beats full schema" is confounded.** The full v2 schema has lost the old default;
   the diff still carries it. The missing conditions are v2 schema + diff together, and v2
   schema with the previous default annotated. About $3.
3. **Some of the silent-failure headline is by construction.** A default change cannot fail
   validation; the type class was chosen so coercion silently mis-scales. Both are
   legitimate, but the abstract presents them as findings.
4. **The executor is a mock** with two hand-designed profiles. No drifted call has been
   replayed through pydantic, FastAPI, or a real MCP server.
5. **Drift always bites, and never in bundles.** Every drift targets a used parameter; there
   is no compound-drift arm and no estimate of how often real changes fall into each class.
6. **Family confound.** Both diff-readers are Gemini; both non-readers are not. Thinking
   budgets differ across families and GPT-5.6-luna's is unstated.
7. **Small things:** token sizes are chars/4 estimates rather than tokenizer counts; the
   teaser is on page 3 rather than page 1; the calling-style plot has four points.

None of these is an invalid result. The problem is one missing explanation and one confounded
comparison, both cheap to fix.

## 5. Roadmap

Do the phases in order. Phase 1 is the cheapest and moves the score the most.

### Phase 1 — Answer the two questions reviewers will ask (weeks 1–2, about $15)

- [ ] **Diff-following ablation** on GPT-5.6-luna and Qwen2.5-7B (primary 120 pairs):
      placement (system prompt / user turn / tool result) × format (JSON / prose) × explicit
      "apply this change log step by step" instruction × thinking budget where available.
      Report which, if any, unlocks recovery. Then rewrite the deployment advice accordingly.
- [ ] **Information vs form:** add condition C+D (v2 schema plus the diff) and D′ (v2
      schema with "previous default: X" in the parameter description). If D′ matches C, the
      diff's advantage is information, not artifact form; say so.
- [ ] **Wording fixes** while the runs go: mark "by construction" for default-change and the
      coercion design; "consistent with" for the n = 4 calling-style axis; report
      tokenizer-measured artifact sizes (the measured prompt-token means are already in
      `analysis.json` under `token_costs`); state the GPT-5.6-luna thinking setting; move
      the teaser to page 1.
- [ ] **Re-score** (see Phase 4) and record the result in the log below.

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
      Flash and Qwen, 48 pairs. Does the diff still work when it lists three changes?

### Phase 3 — External validity (weeks 6–8, $0–5)

- [ ] **Changelog corpus:** collect 100–200 real schema changes (Stripe, GitHub, Slack API
      changelogs; popular MCP servers' git histories). Classify each into the five classes
      plus "other". Report prevalence and the share that touch parameters an agent would use.
      This answers "how often does this happen" and validates the taxonomy.
- [ ] **Larger catalog:** 100+ tools in context with one drifted; measures whether the agent
      finds and applies the right diff when several are served (the retrieval problem the
      limitations section names).
- [ ] **Multi-turn tasks beyond three turns**, if budget allows.

### Phase 4 — Submission

- [ ] Re-score the paper after each phase. Use the same procedure as `REVIEW.md`: restate
      the claim, attack it four ways (confound, generality, direction of inference,
      consequence), check every abstract claim against a number, name the missing experiment,
      then score as three reviewers. Be as harsh as a stranger would be. Record it below.
- [ ] Decide the venue. ICLR is realistic after Phase 1; the topic (LLM agents, tool use) is
      in scope and growing there. NeurIPS Datasets & Benchmarks fits if you expand the
      instrument. Agent and tool-use workshops are a fast fallback.
- [ ] Add an ablation table (Phase 1 results) and a per-family ledger figure to the main
      text; expand the appendix with transcripts of diff-ignoring calls.
- [ ] Rebuild figures, website, GIFs and film from the final numbers.
- [ ] Check the anonymous PDF for identifying strings before submission.

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
   the paper checkable. New tests join the BH family; update the family size (currently 112)
   in the paper.
6. **Audit by hand.** For any new accepted-wrong cell or new coding, read 20+ episodes and
   save the sample, as `results/audit_accepted_wrong_sample.json` does.
7. **Numbers flow one way:** raw logs → `analysis.json` → figures → text. Never the reverse.
8. **Report what you find.** A reversed prediction reported honestly is a strength of this
   paper. Keep it one.

## 7. Boundaries

- The executor is a local mock. Do not point runners at real third-party APIs with drifted
  calls; the payment and access-control tools are simulations.
- Keep the spend cap armed. Keep `.env` out of git.
- Verify every reference you add against the arXiv or publisher record. The current 41 are
  all verified; one invented citation undoes that.
- The testbed is synthetic and contains no real personal data. Keep it that way.

## 8. Things that will trip you up

- The model IDs are from September 2026. Providers retire models; check before a full run and
  record any substitution in the paper.
- The OpenRouter key used for the GPT arm was nearly exhausted at the end of the original
  run; you will need your own keys and Modal account in any case.
- `build_gifs.py` and `build_film.py` use macOS system fonts.
- The teaser figure is an HTML file screenshotted with headless Chrome.
- `paper/iclr/assets/` holds the figures the paper includes; `build_figures.py` writes there
  directly, but the PNG copies in `docs/assets/` are exported separately.
- Flash flips 13.3% of pairs at temperature 0. Do not read per-class cells that differ by a
  few points as real.
- `MILESTONES.md` and `EXPERIMENT_PLAN.md` describe the original checkpointed workflow. They
  are history and context, not instructions you must follow.

## 9. Score log

| Date | Version | R1 rigor | R2 novelty | R3 clarity | Avg | Est. P(accept) | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-22 | First full draft | 6 | 5 | 6 | 5.67 | ~49% | Baseline; see `REVIEW.md` |
| | | | | | | | |

Good luck. The instrument is clean, the statistics are careful, and the diff result is the
kind of thing practitioners quote. Most of the remaining work is explaining it.
