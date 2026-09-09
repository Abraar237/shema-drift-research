# EXPERIMENT PLAN (frozen at CP2, 2026-09-09)

Paper working title: **"The Tool Changed and Nobody Told the Agent: Silent Failure and
Diff-Conditioned Recovery Under Tool-Schema Drift"**. Benchmark name: **SchemaDrift-120**.

Reframing locked at CP1: the headline contributions are (1) the **recovery-lever
comparison** — structured schema-diff vs full new-schema re-injection vs error-feedback
retry vs nothing — and (2) the **drift-class-conditioned outcome ledger** including the
accepted-with-wrong-semantics cell. The deterministic minimal-pair drift taxonomy is the
instrument, not the headline. MCPEvol-Bench (2607.14642), ToolBench-X (2606.25819),
ToolMisuseBench (2604.01508), SilentProbe (2609.00035) are cited and delineated up front.

## 1. Testbed: SchemaDrift-120 (frozen BEFORE any drift is applied)

- **30 tools**, 3 each across 10 domains: calendar, payments, filesystem, CRM,
  email/messaging, web search, e-commerce, travel, HR, analytics. Each tool is a
  JSON-Schema function declaration (OpenAI/Gemini function-calling format) with 3–7
  parameters and, by construction, at least: one enum parameter, one optional parameter
  with a documented default, one integer parameter, one renameable string parameter —
  so every drift class is applicable to every tool.
- **120 tasks** (4 per tool): 90 single-step, 30 two-step (max 3 agent turns, tool
  results fed back). Each task = a natural-language user request + frozen ground-truth
  call(s) with canonical arguments. Ground truth is checkable programmatically:
  exact match on canonicalized arguments (sorted keys, numeric equivalence, ISO-8601
  datetime normalization) plus per-tool semantic checkers where several encodings are
  valid.
- **Two phrasings per task** authored at freeze time. Phrasing 1 is the primary arm;
  phrasing 2 feeds the phrasing-robustness battery (predecessor lesson: no
  single-anything designs).
- Testbed is frozen (git-hashed JSON) before any drift transform or any model call.

## 2. Drift classes (deterministic minimal-pair transforms)

Each task is assigned drift classes targeting a parameter its ground-truth call
actually uses; each drifted schema differs from v1 by EXACTLY ONE transform.

| Class | Transform | Example |
|---|---|---|
| RENAME | parameter renamed via fixed synonym table | `query` → `search_term` |
| ENUM-TIGHTEN | the enum value used by ground truth is removed/renamed | `priority: "normal"` → allowed `{"low","standard","high"}` |
| REQUIRED | optional-with-default parameter becomes required | `calendar_id` (default "primary") now required |
| TYPE-CHANGE | int → string with format change | `amount_cents: 1250` → `amount: "12.50"` (string decimal) |
| DEFAULT-CHANGE | documented default silently changes; task ground truth relied on it | `currency` default USD → EUR |

Assignment: every task gets **2 assigned classes** (balanced: 48 task-drift pairs per
class, 240 total). The **primary set** is the first assigned class per task (24/class,
120 pairs) and is what every model family runs; the doubled set runs on the cheap
families only (§5).

## 3. Executor (local mock; returns realistic error strings or silent acceptance)

Validates the agent's call against the ACTIVE schema version. Two profiles, both run
for condition B (real APIs genuinely differ here, and the profile mechanically
determines which drifts CAN surface):

- **strict**: unknown parameter → 400-style error; missing required → error; enum
  violation → error; type mismatch → error. Error strings modeled on pydantic/Stripe.
- **lenient**: unknown parameters silently dropped (common real-API behavior); type
  mismatch coerced when possible; missing required and enum violations still error.

**Outcome ledger, frozen definitions (per drifted call):**
- `ACCEPTED_CORRECT` — accepted; executed semantics match user intent.
- `ERROR_SURFACED` — executor returned an error string.
- `ACCEPTED_WRONG` — accepted with NO error, executed semantics differ from user
  intent (e.g., renamed param dropped → new default applied; coerced "1250" ≠ "12.50";
  changed default silently applied). **This is the headline cell.**
- Silent-failure rate = ACCEPTED_WRONG / (ERROR_SURFACED + ACCEPTED_WRONG).
- We will report that per-class silent-failure composition is partly a mechanical
  consequence of executor profile — that is a finding (which real-API policies convert
  drift into silence), not a confound to hide; both profiles are reported side by side.

## 4. Conditions (per task-drift pair)

| Cond | Agent sees | Executor | Purpose |
|---|---|---|---|
| A | v1 schema | v1 | baseline |
| B | v1 schema (believes v1) | v2, strict AND lenient | silent drift, core condition |
| C | v1 schema + **structured JSON diff** (per-field records: `{param, change, old, new}`) | v2 strict | the cheap lever |
| D | v2 full schema (as if re-fetched) | v2 strict | upper bound; token cost comparator |
| E | v1 schema; on executor error, raw error string returned, ONE retry | v2 strict | practitioner's default remedy |

Protocol: one item per call, randomized order, resume-safe JSONL, temperature 0,
max_tokens ≤ 512 (Gemini: thinkingLevel MINIMAL on Flash, LOW on Pro — Pro rejects
MINIMAL). Token counts logged per call for the C-vs-D cost comparison (D2).

## 5. Models × arms

| Family | Model / route | Grid |
|---|---|---|
| Gemini fast | gemini-3.6-flash (native API) | full: doubled set, both B profiles, noise floor, phrasing battery |
| Gemini strong | gemini-3.1-pro-preview (native API) | primary set only, capped output |
| GPT | cheapest capable GPT-family function-caller on OpenRouter (target: gpt-5.6-mini; pin at first run) | primary set only ($0.83 key headroom) |
| Open-weight | Qwen2.5-7B-Instruct, vLLM on Modal A10G (weights cached in a Modal volume), hermes tool-call template, greedy | full grid (GPU time, marginal cost ~0) |

Batteries (cheap families): **noise floor** — 30 stratified tasks × 5 identical calls,
condition B-strict (Flash + Qwen); **phrasing robustness** — conditions A and B-strict
re-run on phrasing 2 (Flash + Qwen); **manual audit** — n ≥ 20 ACCEPTED_WRONG
transcripts hand-verified, audited sample ships with the release.

Call-count estimate: Flash ≈ 1,800; Pro ≈ 850; GPT ≈ 850; Qwen ≈ 1,800.

## 6. Metrics and analysis

- Task success (canonicalized exact match + semantic checkers), per condition × class ×
  family. Outcome-ledger rates as defined in §3. Tokens per condition.
- **Recovery fraction** = (success(X) − success(B-strict)) / (success(A) − success(B-strict)) for X ∈ {C, D, E}.
- Paired per-task-drift-pair differences: bootstrap 95% CIs (10,000 resamples),
  two-sided sign-flip permutation tests (20,000 permutations), paired d_z — analyze.py
  conventions copied from the predecessor repos; every paper number traces to
  `results/analysis.json`.
- **Interaction tests run directly** (drift-class × condition permutation on the
  interaction statistic) — a difference in significance is not a significant difference.
- Benjamini–Hochberg over the FULL test family from day one; effective threshold
  stated; only survivors bolded.

## 7. Budget (cap $30, hard stop $25 armed in experiments/cost_tracker.py)

| Item | Est. calls | Est. tokens (in/out per call) | Est. cost |
|---|---|---|---|
| Gemini 3.6 Flash | 1,800 | 1.8k / 300 | ~$2.6 |
| Gemini 3.1 Pro | 850 | 1.8k / 600 (LOW thinking bills as output) | ~$9.2 |
| OpenRouter GPT-mini | 850 | 1.8k / 250 | ~$0.8 (key has $0.83 — scope is sized to fit; stop+report if depleted) |
| Modal A10G (Qwen) | ~1.5–2.5 GPU-h | — | ~$2.8 |
| Slack (retries, audit re-runs) | — | — | ~$2 |
| **Total** | | | **~$17.4** |

If any arm threatens the cap: cut the doubled set first, then the lenient profile on
the expensive family — never silently exceed.

## 8. Pre-registered directions

Recorded and dated in MILESTONES.md on 2026-09-09, before any testbed generation or
data collection (verbatim from MISSION §1):
1. Newly-required arguments cause the largest silent-failure rate; renames the most
   recoverable.
2. Diff-conditioning recovers >50% of the dropped success at <10% of the token cost of
   full-schema re-injection.
3. Failure rates differ by model family at matched task difficulty.
4. A nontrivial fraction of drifted calls SUCCEED with wrong semantics; quantify it.

Reversals are reported plainly (predecessor discipline; the voice paper's reversal was
its best section). Note recorded at pre-registration time: our executor mechanics may
make REQUIRED drift surface errors rather than fail silently — if D1 reverses for that
mechanical reason, we say exactly that.

## 9. Order of operations (CP3)

1. Build + freeze testbed (git hash recorded in MILESTONES.md). 2. Drift transforms +
executor + ledger unit tests. 3. Runner dry-run on 5 tasks (Flash) — sanity + cost
check. 4. Full Flash grid → interim look. 5. Qwen on Modal. 6. GPT arm (credit check
before + during). 7. Pro arm. 8. Batteries. 9. analyze.py → results/analysis.json.
10. Manual audit of ACCEPTED_WRONG sample. 11. CP3 report.
