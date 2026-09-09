# MISSION: Agents Break Silently When Tool Schemas Version
## A schema-drift audit of tool-calling agents, with a diff-conditioning recovery test

You are a Claude Code agent starting a complete research project in this folder. Your user is
Mohammed Abraar (author name on the paper; email abraar@vizz.vizuara.ai). This file is your
complete brief: the problem, the plan, the tools, the rules, and the checkpoint protocol.
Read it fully before doing anything.

---

## 0. THE CHECKPOINT PROTOCOL (this governs everything)

Work phase by phase. **At the end of every phase, STOP and report to the user** with what you
found, what you built, where the files are, and what comes next. **Do not start the next phase
until the user says continue.** The phases and their checkpoint gates:

1. **CP1 · Lit review + pre-emption check** -> report, wait for approval
2. **CP2 · Experiment plan frozen (with budget)** -> report, wait for approval
3. **CP3 · Experiments complete, analysis done** -> report headline numbers, wait
4. **CP4 · Paper written (PDF compiled, figures, 30+ verified citations)** -> deliver, wait
5. **CP5 · Published: GitHub repo + GitHub Pages website + film + GIFs** -> deliver links, wait
6. **CP6 · Self-review: run the calibrated A*-reviewer on the paper, report scores + fix list**

Track progress in `MILESTONES.md` (scaffolded) and update it at every checkpoint.
Record every result and script inside THIS folder. Log every API call's cost (see §5).

---

## 1. THE PROBLEM (what we are testing)

Tool-calling agents are built against a tool schema (MCP servers, OpenAPI specs, function
declarations). Schemas **version**: fields get renamed, enums get tightened, arguments become
newly required, defaults change. The pitch: when this happens, agents **fail silently** — the
call is either rejected downstream with no surfaced error, or worse, accepted with wrong
semantics — and task success drops with no visible signal. The proposed fix is cheap:
**condition generation on a structured schema diff** (old-vs-new, machine-readable) and measure
how much of the lost success it recovers.

**Core questions:**
1. How much does agent task success drop under each drift class (rename / enum-tighten /
   newly-required / type-change / default-change), and how much of the drop is SILENT
   (no error surfaced to the agent or user)?
2. Does prompting with a structured schema diff recover it? How does that compare against
   (a) full new-schema-in-context, (b) an error-feedback retry loop, (c) nothing?
3. Is the effect judge- and family-dependent (Gemini vs GPT vs open-weight)?

**Pre-registered directions (record in MILESTONES.md before ANY data collection):**
- Newly-required arguments cause the largest silent failure rate; renames the most recoverable.
- Diff-conditioning recovers >50% of the dropped success at <10% of the token cost of
  full-schema re-injection.
- Failure rates differ by model family at matched task difficulty.
- A nontrivial fraction of drifted calls SUCCEED with wrong semantics (the scariest cell) —
  quantify it.

**Design sketch (CP2 refines; keep it API-only, no GPU training):**
- Build a **frozen testbed of ~30 realistic tools** (JSON-schema function declarations across
  domains: calendar, payments, filesystem, CRM, search...) with ~120 single- and multi-step
  tasks whose ground-truth calls are checkable programmatically (exact-match on canonicalized
  arguments + semantic checkers where needed). Freeze BEFORE any drift is applied.
- Apply **5 drift classes** as deterministic transforms of the schemas (rename via synonym
  table, enum subset, promote-optional-to-required, int->string type change, default removal).
- Conditions per task: v1-schema baseline / v2 schema silently swapped (agent still believes
  v1) / v2 + structured diff / v2 + full new schema / v2 + one retry with the raw error string.
- **Models under test:** gemini-3.6-flash and gemini-3.1-pro (native API, temperature 0),
  one GPT-family model via OPENROUTER_API_KEY, and one open-weight tool-caller (e.g.
  Qwen2.5-7B-Instruct with function-calling template) on Modal — 4 families total.
- Executor harness: a local mock executor that validates calls against the ACTIVE schema and
  returns realistic error strings (or silent acceptance for the wrong-semantics cells).
- Metrics: task success, silent-failure rate, wrong-semantics rate, tokens per condition,
  recovery fraction. Paired per-task stats: bootstrap CIs, sign-flip permutation tests
  (copy `analyze.py` conventions from the reference projects).

**Pre-emption frontier (verify FULL-TEXT at CP1 — this decides go/no-go):**
- Search hard for: "MCPEvol", "MCP-Bench" variants, tool/API schema evolution benchmarks,
  "tool drift", "API versioning LLM agents", BFCL (Berkeley Function-Calling Leaderboard)
  drift extensions, ToolBench/T-Eval/API-Bank successors, "schema change agent robustness",
  staleness/documentation-drift agent papers.
- Known adjacent (delineate, do not panic): BFCL measures function-calling accuracy on STATIC
  schemas; ToolBench/API-Bank test tool use, not schema EVOLUTION; agent-robustness work
  perturbs inputs, not the tool contract. The unclaimed core, if it holds: **version drift of
  the tool contract itself, silent-failure accounting, and diff-conditioning as the recovery
  lever**. If a paper already owns exactly this, STOP AT CP1 and report; the user decides.
- The original pitch cited "MCPEvol-Bench" as an existing testbed — TREAT THAT AS UNVERIFIED.
  If it exists, use/extend it and cite; if not, our frozen testbed IS the benchmark contribution
  (name it, e.g., SchemaDrift-120) and say so honestly.

---

## 2. THE PIPELINE (copy the two predecessor projects exactly; it worked twice)

Both predecessor papers are in `reference/` — READ THEM FIRST; their method is your template:
script-bias paper (site: https://abraar237.github.io/script-bias-llm-judges/) and voice-judge
paper (site: https://abraar237.github.io/speaker-identity-bias/).

| Stage | What to replicate | Skill (in `Agent Skills/`) |
|---|---|---|
| 1. Lit review | 4 parallel search agents by angle + 1 recency sweep; verified CSV + LIT_REVIEW.md with a novelty-delineation table written BEFORE results | `prior-work-check` |
| 2. Plan | `EXPERIMENT_PLAN.md` + HTML plan page; budget table; pre-registered directions recorded and dated | `paper-topic-selection` |
| 3. Experiments | Frozen testbed; scripted runners (one task per call, randomized, resume-safe JSONL); cost tracker with hard stop; paired stats in one `analyze.py` -> `results/analysis.json`; EVERY paper number traces to it | — |
| 4. Paper | ICLR-format LaTeX from the start (copy `iclr2026_conference.sty` etc. from the script-bias repo paper/iclr/); anonymous submission build + named preprint build; 30+ arXiv-verified references; teaser Figure 1 (HTML->headless-Chrome, standard fonts, white bg); results tables with CIs + bold BH-surviving cells | `research-paper-writing`, `paper-quality`, `paper-figures` |
| 5. Publish | Public GitHub repo (gh CLI, Abraar237) — `.gitignore` BEFORE first add, `.env` NEVER committed; GitHub Pages from `docs/`; explainer film (ElevenLabs Matilda XrExE9yKIg1WjnnlVkGX + Remotion, script approved before visuals, -14 LUFS, CONTINUOUS animated motion — bars grow on spoken numbers, counters count, no static cards); 3 concept GIFs in the CLEAN FLAT CHART style (white card, flat bars, thin gridlines, monospace numerals, replay pill, standard Helvetica — NOT hand-drawn; the user rejected the rough.js look) | `research-website`, `paper-to-video`, `social-media-gif` |
| 6. Review | `a-star-reviewer` on the PDF with its calibration data; report scores + calibrated P(accept) + effort-ranked fix list | `a-star-reviewer` |

---

## 3. METHOD LESSONS FROM THE TWO PREDECESSOR PROJECTS (do not relearn the hard way)

1. **One item per call, randomized, resume-safe, temperature 0.** Batched contexts mask effects.
2. **Pre-register directions in writing before data.** The voice project's headline REVERSED on
   replication and the honest report was the paper's best section. Report reversals plainly.
3. **Single-anything designs get killed.** The voice paper's fatal was one voice per accent
   cell. Here the analog: do not test one phrasing of each task, one seed, or one model family.
   Multiple task phrasings per tool, multiple families, and (cheap here) repeat-call noise
   floors (~30 tasks x 5 identical calls) from day one.
4. **A difference in significance is not a significant difference** — test interactions
   directly (drift-class x condition), not per-cell significance comparisons.
5. **Multiple-comparison correction from day one:** BH over the full test family, stated
   effective threshold, bold only survivors.
6. **The wrong-semantics cells need manual verification.** Sample n>=20 "succeeded but wrong"
   transcripts and hand-verify; ship the audited sample (the script paper's Hinglish-audit
   pattern). Never claim an audit that has not actually been performed.
7. **Verify every citation** against export.arxiv.org batch queries. One fake reference kills.
8. **Track spend per call** with a hard stop (copy `cost_tracker.py` pattern from the voice
   repo: https://github.com/Abraar237/speaker-identity-bias experiments/). Gemini thinking
   tokens bill as OUTPUT; thinkingLevel MINIMAL where supported (Pro rejects it; use LOW).
9. **Corrected-numbers discipline:** when a result changes, purge and update paper + website +
   film in ONE consolidated pass.
10. **Figures:** standard fonts (Times in paper figures to match body; Helvetica on web),
    white backgrounds, house palette (slate #155e8c, hot #b3006b, shelf #c0641a, good #1c7a55),
    eyebrow titles, direct labels, the finding annotated on the figure itself.
11. **OpenRouter has a $5-capped key** — budget GPT-family calls accordingly (temperature 0,
    max_tokens 700, None-safe content parsing, exponential backoff on 429s; a patched runner
    exists in the script-bias repo `experiments/run_openrouter_judge.py` — copy it).
12. **Expect reviewer moves and pre-empt them in v1:** noise floors, interaction tests,
    per-family tables, BH, verbatim prompts in the appendix, honest Limitations narrating every
    confound you know about. The reviewer WILL find the one you hide.

---

## 4. BUDGET (hard rules)

- **Total cap: $30.** Hard-stop in the cost tracker at $25. Report spend at every checkpoint.
- Expected: Gemini judging/agents ~$8-12, OpenRouter GPT arm ~$3-4 (respect the $5 key cap),
  Modal open-weight arm ~$2-4 (A10G; cache the HF weights in a Modal volume), everything else $0
  (testbed and executor are local code).
- If a planned arm would break the cap, cut scope (fewer tasks per cell) and say so, never
  silently exceed.

## 5. KEYS AND ACCOUNTS (all in `.env` in this folder — NEVER commit it, never print values)

- `GEMINI_API_KEY` — agent/judge calls (verify balance with a 1-token call FIRST; the key
  runs on prepaid credits that CAN deplete — if you get 429 RESOURCE_EXHAUSTED with a
  "prepayment credits" message, STOP and tell the user to top up at https://ai.studio/projects).
- `OPENROUTER_API_KEY` — GPT-family arm ONLY (hard $5 key cap; check remaining before runs).
- `token-id` / `token-secret` — Modal (`python3 -m modal token set ...`; profile thesreedath).
- `ELEVENLABS_API_KEY` — film narration (Matilda XrExE9yKIg1WjnnlVkGX) + music. NOTE: the key
  is TTS-scoped — `voices_read`/`user_read` return 401; do NOT probe those endpoints, just call
  text-to-speech directly.
- GitHub: `gh` CLI authenticated as Abraar237. Create the repo public at CP5.

## 6. FOLDER LAYOUT

```
schema drift research/
  MISSION.md          <- this file
  MILESTONES.md       <- checkpoint tracker; update at every gate
  .env                <- all keys (never commit)
  Agent Skills/       <- all 4 skill bundles (gifs, video, writing, review)
  reference/          <- both predecessor papers; read first
  lit_review/  experiments/  results/  paper/  figures/  site/  video/
```

## 7. FIRST ACTIONS WHEN YOU (the new session) START

1. Read this file fully, then both PDFs in `reference/` (method + honest-reporting register).
2. Install the writing skills: `cp -R "Agent Skills/3-research-paper-writing/skills/"* ~/.claude/skills/`
3. Sanity-check keys: one tiny Gemini call (watch for the prepaid-depletion 429), OpenRouter
   remaining-credit check, `modal profile current`.
4. Begin Phase 1: lit review with the pre-emption frontier in §1 as the search seed — the
   MCPEvol-Bench existence check is the FIRST query. Then **CHECKPOINT CP1: stop and report.**
