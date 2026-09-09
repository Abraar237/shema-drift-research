# Lit review and pre-emption check — schema drift in tool-calling agents

Date: 2026-09-08. Written BEFORE any experiment data. Five parallel search agents (MCP/MCPEvol
angle, schema-evolution angle, benchmark-landscape angle, recovery-lever angle, six-month recency
sweep) plus three full-text pre-emption reads (MCPEvol-Bench, ToolMisuseBench incl. its released
code, ToolBench-X incl. its released code). All 55 arXiv ids in `lit_review.csv` verified against
the live export.arxiv.org API on 2026-09-08.

## Headline facts

1. **MCPEvol-Bench EXISTS** (arXiv 2607.14642, v1 2026-07-16). The mission flagged it as
   unverified; it is real, public (github.com/Octobrist/MCPEvol-Bench), and takes the broad
   headline: "LLM agents degrade under MCP tool evolution" with 11 mutation operators, 123
   servers, 12 models. Full-text read confirms: mutations are **LLM-driven compound rewrites
   that deliberately preserve backward compatibility**, scored by LLM judges; there is **no
   silent-failure accounting and no recovery lever that informs the agent of the change**.
2. The niche compounded fast: at least eight adjacent papers appeared March–September 2026,
   five in the last four weeks of the sweep window. The window is closing.
3. The two "kill-shot" candidates survive full-text reads:
   - **ToolMisuseBench** (2604.01508): its "schema aware methods" are *rule-based repair loops*
     (drop unknown field / alias table / cast type) against the current schema — no LLM
     prompting, no diff, and its "schema drift" mutates the agent's *emitted call*, not the
     schema the agent believes.
   - **ToolBench-X** (2606.25819): its "targeted recovery hints" are GPT-5.4-written procedural
     prose delivered *after task failure* — never a machine-readable schema diff, never a
     new-schema re-injection, and its executor's silent payload mutations go unmeasured.

## Novelty delineation table

| Closest neighbor (arXiv id) | What it established | What of ours it does NOT cover |
|---|---|---|
| MCPEvol-Bench (2607.14642) | Agents degrade 13–14% under LLM-simulated, backward-compatible MCP server evolution; 12 models; judge-scored | Deterministic *breaking* parameter-level drift with minimal-pair per-class attribution; error-surfaced vs silent vs accepted-wrong ledger; any change-information recovery arm |
| ToolBench-X (2606.25819) | "Specification Drift" (doc vs runtime contract) as one of five hazards; post-failure NL hints recover 60–80% of lost accuracy | Frozen deterministic drift instances (theirs are GPT-5.4 tool rewrites); structured schema-diff or new-schema-in-context arms; silent-acceptance accounting (their own executor silently mutates payloads, unexamined) |
| ToolMisuseBench (2604.01508) | Deterministic replayable fault injection incl. call-level "schema drift"; rule-based schema-repair baselines | Schema-level drift (agent facing a genuinely changed contract); LLM prompt-conditioning arms; per-class attribution; wrong-semantics ledger |
| SilentProbe (2609.00035) | Silent (HTTP-200) failures of live production API tools; models detect 12%, repair 0% | Silent failure *caused by known, induced drift class*; the accepted-with-wrong-semantics cell per drift class; recovery-lever comparison |
| ToolMaze / When Tools Fail (2606.05806) | 2x2 runtime tool-perturbation taxonomy; over-trust in corrupted outputs | Schema-contract versioning; drift-class ledger; diff conditioning |
| LayerRAG-Bench (2607.27353) | System-side schema normalization lifts drift success 0.00→0.91 (9 models) | Agent-side in-context levers; taxonomy; silent accounting |
| Schema-First Tool APIs (2603.13404) | Interface format (prose vs schema vs schema+diagnostics) changes misuse rates | Any drift; any diff; scale beyond a one-model pilot |
| What a diff makes (2511.00160) | Diffs in context improve LLM *code migration* | The same lever for *tool-calling agents* at inference time, measured against re-injection and retry |
| Skill Drift Is Contract Violation (2605.10990) | Skill libraries silently decay as services evolve; localization enables repair | Live tool-calling task success under drift; ledger; lever comparison |
| Silent-failure wave (2606.09863, 2606.14589, 2606.09071, 2606.08162) | Silent failure / false success is common in agents generally | Attribution to schema drift as cause, per drift class |

**Direct search evidence for the C3 gap:** an arXiv full-text query for "schema diff" in cs.CL
returned zero results; no found paper conditions a tool-calling agent on a machine-readable
old-vs-new schema diff at inference time.

## What is ours alone (surviving claims)

1. **The recovery-lever comparison (C3) — now the headline.** Structured machine-readable
   schema-diff conditioning vs full new-schema re-injection vs one error-feedback retry vs
   nothing, under controlled drift, across families, with token-cost accounting. Untouched by
   every paper found. The nearest neighbor (2511.00160) is in code migration, another domain;
   2609.00072 explicitly documents that machine-actionable recovery information is missing in
   the MCP ecosystem — a setup pass for us.
2. **The drift-class-conditioned outcome ledger (C2).** For every drifted call: error surfaced
   / failed with no surfaced error / ACCEPTED with wrong semantics — per drift class, with a
   hand-audited sample of the wrong-semantics cell. "Silent failure" as a term is saturated;
   the ledger conditional on a known induced drift class is unclaimed. ToolBench-X's executor
   silently mutates payloads and never measures it; the MCP fault taxonomy (2606.05339)
   documents accepted-but-unenforced parameters in the wild as motivation.
3. **The instrument (C1, demoted from headline to method).** A frozen testbed with five
   deterministic, minimal-pair, parameter-level drift transforms (rename-via-synonym, enum
   tightening, optional→required, type change, default change) giving clean per-class
   attribution. MCPEvol-Bench's mutations are compound, LLM-generated, backward-compatible,
   and attributed by score-splitting; ToolBench-X's are LLM-generated rewrites. Nobody has the
   deterministic minimal-pair version. Claim it as the instrument, not as "first drift
   benchmark" — that framing is dead.
4. C4 (cross-family) is table stakes (MCPEvol-Bench and SilentProbe both run 12 models). Keep
   the families for generality; do not present as a contribution.

## Significance

Who is affected: anyone shipping tool-calling agents against MCP servers or OpenAPI backends
that version independently of the agent prompt. What changes: if the diff lever works, the
practitioner remedy is a one-line protocol addition (serve a machine-readable schema diff with
version bumps) instead of re-injecting full schemas every call; if the wrong-semantics cell is
nontrivial, silent drift is a correctness hazard that validators and retry loops structurally
miss, and the MCP version-negotiation spec (2026-07-28) has a concrete payload to carry.

## Verdict: ALIVE-BUT-CROWDED → GO, with mandatory reframing

- Dead: "first benchmark of tool-schema evolution", "agents degrade under drift" as headline,
  cross-family comparison as contribution.
- Alive and ours: the three-way recovery-lever comparison (C3) and the drift-class-conditioned
  silent/wrong-semantics ledger (C2), on a deterministic minimal-pair instrument (C1).
- Obligations: cite and delineate MCPEvol-Bench, ToolBench-X, ToolMisuseBench, SilentProbe
  prominently (delineation table above goes in the paper and site); move fast — five neighbors
  appeared within the last month of the sweep.
