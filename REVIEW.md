# Simulated A* review — "The Schema Changed and Nobody Told the Agent"

Target venue: **ICLR** (the paper uses the ICLR 2026 style file). Paper type: **analysis with
a benchmark instrument**. It is judged on whether the measurement changes what the field
believes, whether the evidence rules out alternatives, and whether the instrument is one
others will use.

Reviewed build: `paper/iclr/paper_iclr_submission.pdf` (15 pages, 4 figures, 3 main-text
tables + 3 appendix tables, 41 references), cross-checked against `results/analysis.json`,
which re-runs byte-identically from the raw episode logs.

> These are estimated scores from a simulated review, not real reviews. Borderline outcomes
> at A* venues are noisy (the NeurIPS consistency experiments found about 50% disagreement
> on borderline papers). Treat the acceptance number as a base rate, not a promise.

## Scorecard

| Reviewer | Emphasis | Score (1–10) |
|---|---|---|
| R1 | Rigor | **6** |
| R2 | Novelty | **5** |
| R3 | Clarity / impact | **6** |
| **Average** | | **5.67** (confidence 4/5) |

**Calibrated acceptance estimate: about 49%.** The 5.5–6.0 average-score band was accepted
48.5% of the time across 4,336 real ICLR submissions (from a calibration table of 33,000+
public ICLR decisions binned by average reviewer score). This is the coin-flip zone. ICLR
2026's overall acceptance rate was 27%, so no venue adjustment is applied. Half a point more
(6.0–6.5) moves the base rate to 78%; one point more (6.5–7.0) to 94%.

---

## Summary

The paper measures what happens to tool-calling agents when the tool schema changes and the
agent's prompt still carries the old one. It freezes SchemaDrift-120 (30 tools, 120 checkable
tasks) and applies five deterministic single-edit drift classes (rename, enum-tighten,
newly-required, type-change, default-change) as minimal pairs. A mock executor with strict
and lenient tolerance profiles classifies every drifted call as error-surfaced,
accepted-correct, or accepted-wrong. Four model families (Gemini 3.6 Flash, Gemini 3.1 Pro,
GPT-5.6-luna, Qwen2.5-7B) run 4,800 episodes across a baseline, the silent-drift core, and
three recovery levers: a structured JSON diff, the full new schema, and one raw-error retry.
Silent drift removes 55–87 points of task success. Default-change never surfaces an error,
and a lenient executor turns rename and type drift into accepted-wrong calls (24/24
hand-audited, including an $80 payment sent as EUR 80). The 28-token diff recovers 96–98% of
the loss on both Gemini models and beats full-schema re-injection (82–83%), but recovers
nothing on GPT-5.6-luna or Qwen2.5-7B. GPT-5.6-luna's habit of filling every optional
parameter makes it mechanically immune to two of the five classes.

## The claim in one sentence

"Unannounced schema drift wrecks tool-calling agents, often silently; a tiny machine-readable
diff repairs almost all of it for models that read it, and nothing for models that don't."

This is easy to restate and easy to champion. The trouble is the last clause: the paper
observes that two families ignore the diff but does not test why, and the comparison that
makes the diff look better than the full schema is partly a comparison of information
content, not of artifact form.

## Strengths

- **Deterministic minimal-pair drift with single-cause attribution.** Every drifted schema
  differs from v1 by exactly one edit, so every failure has a known cause. This is a genuine
  step past the LLM-mutated, compound drift of MCPEvol-Bench and ToolBench-X, and Table 1
  says precisely what each neighbour does not cover.
- **The accepted-wrong cell, audited.** A three-way ledger conditional on drift class ×
  executor policy, with 24/24 hand-verified wrong-semantics calls that have concrete stakes
  (a $2,500 invoice as $250,000; a two-day grant as 2,880 hours). No prior drift work
  measures this cell.
- **A mechanism, not just a number, for the diff result.** Per-class breakdown shows why
  the diff beats the full schema on newly-required drift (D 0.40 vs C 1.00 on Flash): the
  new schema no longer contains the deleted default, the diff does. That is a real insight
  about what a change artifact must carry.
- **Calling style as an exposure axis.** Fill rate 1.00 vs 0.45–0.71 explains
  GPT-5.6-luna's 0.96 survival on required + default drift against 0.25–0.31 for Gemini. It
  is mechanical, checkable, and useful to practitioners choosing a model.
- **Statistics proportionate to the design.** Within-pair paired differences, bootstrap CIs,
  sign-flip permutation, paired d_z, direct interaction tests, one BH family of 112 tests
  with 74 survivors and the non-survivors named. A noise floor (13.3% of Flash pairs flip at
  temperature 0) and a phrasing battery (all p ≥ 0.27) bound the variance.
- **Honest reporting.** Four pre-registered directions; D1 reversed for a mechanical reason
  foreseen at registration and reported as a reversal; D2's token target (<10%) missed
  (13.7%) and reported. The freeze amendment is disclosed with its cause.
- **Four families including an open-weight model, for under $8 plus 1.7 GPU hours.**
  Reproducible: frozen testbed with hash, resume-safe logs, one analysis script, unit tests
  for the executor.

## Weaknesses (ordered by severity)

1. **The headline split ("only works for models that read it") is observed, not
   explained, and the obvious ablation is missing. (Serious.)** The diff is a JSON note in
   the system prompt. GPT-5.6-luna and Qwen keep emitting v1 calls. The paper admits the
   fix is "one experiment away": vary the diff's placement (system prompt, user turn, tool
   result), its format (JSON vs prose), add an explicit "apply this change log" instruction,
   and vary thinking budget. Without it, a reviewer cannot tell a model capability from a
   prompt-engineering artefact, and the deployment advice ("test whether your model reads
   diffs") is weaker than it could be. This is the experiment every reviewer will ask for.

2. **The diff vs full-schema comparison is confounded by information content. (Serious.)**
   Condition D shows the v2 schema, which has lost the old default; condition C shows the
   old schema plus a diff that carries it. So "diff beats full schema" is partly "old + delta
   beats new alone". The practical alternative, v2 schema plus changelog (C+D), or v2 with a
   "previously defaulted to X" annotation, is not run. Also, C puts its artifact in the
   system prompt while D swaps the schema block, so position differs too. The paper's own
   wording ("strictly more informative about the past") concedes the point without testing
   the fix.

3. **Part of the silent-failure headline is designed in.** Default-change "never surfaces
   an error under any validator" is true by definition: a default change violates nothing a
   validator can check. The abstract presents it as a finding. The type-change class was
   chosen so that naive coercion yields a valid but wrongly scaled value (the paper says
   so), which is why lenient type drift lands 67–79% in accepted-wrong. Both are fair
   design choices; the abstract should say "by construction" where it applies.

4. **The mock executor's two profiles bracket, not sample, real API behaviour.** No call is
   validated by a real framework (pydantic, FastAPI, an OpenAPI gateway) or a real MCP
   server. The ledger's per-class rates are properties of the paper's executor. One
   external-validity check against real validators would settle this cheaply.

5. **Drift always bites.** Each task's assigned drift classes target a parameter its ground
   truth uses. The 55–87 point drops are therefore for drift that is guaranteed to touch the
   call, an upper bound on the per-drift effect. There is no estimate of how often real
   schema changes hit parameters an agent actually uses, and no compound-drift arm; real
   version bumps ship several changes with a changelog of mixed quality.

6. **Family confound in the 2-vs-2 split.** Both "reads the diff" families are Gemini; both
   "ignores it" families are not. Thinking budgets differ (Flash minimal, Pro low; the
   GPT-5.6-luna setting is unstated). Two more families (one Anthropic, one more open-weight)
   would tell a family effect from a Gemini-system-prompt effect.

7. **The calling-style axis has n = 4 points, one of which is the outlier.** "Predicts" is
   too strong; "consistent with" is right. It would be more convincing with a within-model
   test: force Flash to fill every optional parameter via instruction and see whether its
   survival on required + default drift rises toward 0.96.

8. **Small per-class cells on the negative side.** GPT-5.6-luna and Pro run 24 pairs per
   class, and the Flash noise floor is 13.3% flips. Cells like .917 vs .958 are within
   noise. The paper says this, but Table 4 still invites per-cell reading.

9. **Token accounting is a chars/4 estimate**, not tokenizer counts. The 13.7% ratio and the
   "28 tokens" in the title-level claim should be measured with each provider's tokenizer;
   the measured prompt-token means exist in the analysis output and should be reported.

10. **Benchmark size.** As an instrument, 30 tools × 120 tasks with single-edit drift is
    modest next to ToolBench-X and MCPEvol-Bench. The paper correctly demotes the testbed to
    an instrument, but ICLR reviewers grading the "SchemaDrift-120" contribution will note
    it.

11. **Presentation is thin for the venue.** 15 pages, 4 figures, 6 tables against ICLR
    medians of 25 pages and 11.5 figures. There is no ablation table (the per-class table
    is the closest thing). The paper reads well, but a reviewer skimming for depth sees a
    short paper.

**Fatal vs fixable.** Nothing here invalidates a result; the numbers are clean and reproduce
exactly. Weaknesses 1 and 2 are what keep this in the coin-flip zone: both are one cheap
experiment each. 3, 7 and 9 are wording and small analysis fixes. 4–6 are the generality
work that would push it into clear-accept territory.

## Format audit (vs ICLR accepted-paper norms, 2025 sample, n=151)

| Item | This paper | ICLR norm | Verdict |
|---|---|---|---|
| Total pages (with appendix) | 15 | median 25 | Thin |
| Figures | 4 | mean 11.5 | Low |
| Tables | 6 | mean 8.7 | Slightly low |
| Ablation table | none as such | 56.8% have one | Flag |
| Page-1 teaser | yes (Fig. 1 on p. 3) | 10.6% | Differentiator; move it to page 1 |
| Error bars / CIs | yes | 40.2% | Differentiator |
| Significance tests | yes, BH-corrected | 6.1% | Strong differentiator |
| Topic fit | LLM agents / tool use / robustness | "Autonomous LLM Agent Systems" 2.7% of ICLR 2026 (5th largest topic), growing; "LLM Safety and Adversarial Robustness" 2.5% | In scope and growing |

## Questions for the authors

1. Does the diff work on GPT-5.6-luna or Qwen when placed in the user turn or a tool result,
   phrased as prose, or accompanied by an explicit "apply this change log" instruction? With
   more thinking budget?
2. What is the recovery for v2 schema + diff together (C+D), and for v2 schema with the
   previous default annotated? Is the diff's advantage its form or its information?
3. Do the strict and lenient profiles match what pydantic, FastAPI, and at least one real
   gateway or MCP server do on the same drifted calls?
4. How often do real schema changes (Stripe, GitHub, popular MCP servers) fall into each of
   your five classes, and how often do they touch a parameter an agent uses?
5. What happens under compound drift (two or three edits at once with one bundled diff)?
6. If Flash is instructed to fill every optional parameter, does its survival on required +
   default drift rise to GPT-5.6-luna's level?
7. Can you report tokenizer-measured artifact sizes rather than chars/4?
8. What thinking/reasoning setting was used for GPT-5.6-luna, and does the family
   comparison hold at matched budgets?

## What would move this to accept (ranked by score gained per unit effort)

| # | Change | Addresses | Est. effort | Est. cost |
|---|---|---|---|---|
| 1 | **Diff-following ablation** on GPT-5.6-luna and Qwen: placement × format × explicit instruction × thinking budget. Report which, if any, unlocks recovery. | W1, W6 | 1 week | ~$5–10 |
| 2 | **Information vs form:** add C+D (v2 schema + diff) and D′ (v2 schema with previous default annotated). | W2 | 2–3 days | ~$3 |
| 3 | **Two more families** (one Anthropic, one open-weight 70B-class) on the primary 120 pairs, all conditions. | W6 | 3–5 days | ~$10–15 |
| 4 | **Within-model calling-style test:** instruct Flash to fill all optional parameters; measure survival. | W7 | 1–2 days | ~$1 |
| 5 | **Real-validator check:** replay all drifted calls through pydantic, FastAPI, and one OpenAPI/MCP mock server; report agreement with the two profiles. | W4 | 3–5 days | $0 |
| 6 | **Changelog corpus:** classify 100–200 real API/MCP schema changes into the five classes (plus "other"); report prevalence and how many touch used parameters. | W5, W10 | 1 week | $0 |
| 7 | **Compound-drift arm:** 2–3 simultaneous edits with one bundled diff, Flash and Qwen. | W5 | 3–4 days | ~$3 |
| 8 | **Wording and accounting fixes:** mark "by construction" where it applies (default-change, coercion design), "consistent with" for the n=4 axis, tokenizer counts, GPT-5.6-luna thinking setting, teaser to page 1. | W3, W7, W9 | 1 day | $0 |
| 9 | **Format depth:** ablation table (from items 1–2), per-family ledger figure in the main text, expand the appendix with transcripts of diff-ignoring calls. | W11 | 2–3 days | $0 |

Realistic outlook: items 1, 2 and 8 plausibly move the average to 6.0–6.5 (about 78%).
Adding 3–5 makes 6.5–7.0 (about 94%) reachable. The paper's core is already sound; what is
missing is the explanation for its most quotable result.
