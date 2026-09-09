# Schema-Drift Audit · Milestones & Checkpoints

Project brief: MISSION.md. Budget cap: **$30 total** (hard stop $25). Update this file at
every checkpoint. RULE: at each CP, STOP and report to the user; wait for approval.

## Pre-registered directions (recorded BEFORE any testbed generation or data collection)
- [x] Direction 1: Newly-required arguments cause the largest silent-failure rate;
      renames the most recoverable.  Recorded: 2026-09-09
- [x] Direction 2: Diff-conditioning recovers >50% of the dropped success at <10% of the
      token cost of full-schema re-injection.  Recorded: 2026-09-09
- [x] Direction 3: Failure rates differ by model family at matched task difficulty.
      Recorded: 2026-09-09
- [x] Direction 4: A nontrivial fraction of drifted calls SUCCEED with wrong semantics;
      quantify it.  Recorded: 2026-09-09
- Note at registration: executor mechanics may force REQUIRED drift to surface errors
  rather than fail silently; if D1 reverses for that mechanical reason we report exactly
  that (reversal-reporting discipline per the voice paper).

## CP1 · Lit review + pre-emption — DONE 2026-09-08, awaiting approval
- [x] Angle agents (4) + recency sweep -> lit_review/lit_review.csv (55 ids, all verified
      against export.arxiv.org on 2026-09-08)
- [x] Full-text pre-emption reads: MCPEvol-Bench (2607.14642 — EXISTS), ToolBench-X
      (2606.25819, paper+code), ToolMisuseBench (2604.01508, paper+code)
- [x] LIT_REVIEW.md with novelty-delineation table
- [x] Verdict: ALIVE-BUT-CROWDED -> GO with reframing. Headline = C3 (diff-conditioning
      recovery comparison) + C2 (drift-class-conditioned silent/wrong-semantics ledger);
      C1 (deterministic minimal-pair drift taxonomy) demoted to instrument; C4 table stakes.
      "First drift benchmark" framing is dead (MCPEvol-Bench, ToolBench-X own it).
- [ ] **REPORTED TO USER, APPROVAL RECEIVED: ____**

Key sanity checks (2026-09-08): Gemini key OK; Modal profile thesreedath OK;
OpenRouter key has ~$0.83 remaining of its $5 cap (4.17 used) — GPT arm must be scoped
tightly or key topped up before CP3.

## CP2 · Experiment plan frozen — DONE 2026-09-09, awaiting approval
- [x] EXPERIMENT_PLAN.md + site/plan.html; budget table totals ~$17.4 of $30 cap
- [x] Pre-registered directions recorded above, dated 2026-09-09
- [x] experiments/cost_tracker.py armed with the $25 hard stop (+ Modal GPU logging)
- [x] Design: SchemaDrift-120 (30 tools / 120 tasks / 2 phrasings), 5 deterministic
      minimal-pair drift classes (48 pairs/class doubled, 24/class primary), conditions
      A/B-strict/B-lenient/C-diff/D-fullschema/E-retry, 4 families, outcome ledger with
      ACCEPTED_WRONG cell + n>=20 manual audit, noise floor 30x5, interaction tests + BH
- [ ] **REPORTED TO USER, APPROVAL RECEIVED: ____**

## CP3 · Experiments + analysis — IN PROGRESS
- [x] Frozen testbed/corpus: SchemaDrift-120 (30 tools, 120 tasks, 30 two-step,
      48 task-drift pairs/class, primary 24/class); executor+harness 12/12 tests green.
      First freeze b009f779... (2026-09-09) was amended ONCE during pre-drift baseline
      calibration (Flash condition-A 114/120): 3 phrasing ambiguities fixed (rem01,
      log04, ride03) + case-insensitive free-string canonicalization; no drifted arm
      had run. Final frozen sha256:
      e8bbd71c63b1311c76b87ceabe45456217f9054f2d5f010517e3930209d08475
- [x] All arms run 2026-09-09 (4,800 records): Flash full grid (core doubled + noise
      30x5 + phrasing), Pro primary, gpt-5.6-luna primary (OpenRouter, $0.10),
      Qwen2.5-7B full grid on Modal A10G (+noise+phrasing)
- [x] Noise floor (Flash flip 13.3%, Qwen 0.0%), phrasing battery null (p .27-1.0),
      class x condition interactions tested directly, BH over 112 tests -> 74 survive
      (threshold .0316)
- [x] analyze.py -> results/analysis.json; hand audit
      results/audit_accepted_wrong_sample.json (24/24 confirmed)
- [x] Spend: $7.64 of $25 hard stop
- [ ] **REPORTED TO USER (headline numbers), APPROVAL RECEIVED: ____**

Headline: B_strict success 11-38% vs baselines 87-99%. Diff recovery: Gemini 0.96-0.98
(beats full-schema 0.82-0.83), Qwen 0.06, luna -0.06 (CI<0). Luna fills 100% of optional
params (Flash 53%) -> immune to required+default drift by calling style. default_change
is the only universally silent class; type/rename silent only under lenient executor.
D1 partially reversed as pre-noted; D2 holds for Gemini only (diff=13.7% of schema
tokens, not <10%); D3 strongly confirmed; D4 confirmed (audited).

## CP4 · Paper — DONE 2026-09-09, awaiting approval
- [x] ICLR dual build compiles (tectonic): paper_iclr_preprint.pdf (named) +
      paper_iclr_submission.pdf (anonymous), 15 pages, 0 unresolved cites
- [x] Title: "The Schema Changed and Nobody Told the Agent: Silent Failure and
      Diff-Conditioned Recovery under Tool-Schema Drift"
- [x] 4 figures (HTML->Chrome teaser + 3 matplotlib house-style, all traced to
      analysis.json via figures/build_figures.py)
- [x] 41 references, ALL verified by 3 batch agents (41/41 OK; venues checked)
- [x] Appendix: freeze provenance + amendment note, verbatim prompts/diff/errors,
      per-class tables, full ledger, audit sample table, batteries, BH detail
- [x] Register check: no em/en dashes, no banned words; BH survivors bolded
- [ ] **DELIVERED TO USER, APPROVAL RECEIVED: ____**

## CP5 · Publish — PENDING
- [ ] Public repo (.env verified absent), Pages site, film (Matilda, animated, -14 LUFS),
      3 flat-chart GIFs
- [ ] **LINKS DELIVERED, APPROVAL RECEIVED: ____**

## CP6 · Self-review — PENDING
- [ ] a-star-reviewer scores + calibrated P(accept) + effort-ranked fix list reported

## Spend log
| Date | Item | Amount | Running total |
|---|---|---|---|
