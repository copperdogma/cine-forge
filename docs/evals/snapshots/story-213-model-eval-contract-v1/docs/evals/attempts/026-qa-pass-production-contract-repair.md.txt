# Eval Attempt 026 — QA Pass Production-Contract Repair

**Status:** Succeeded as an eval-validity repair; final fresh parity not measured
**Eval:** qa-pass
**Date:** 2026-08-13
**Worker Model:** Codex (GPT-5.6)
**Subject Models:** GPT-4.1 Mini (`gpt-4.1-mini`) and Gemini 3.7 Flash (`gemini-3.7-flash`)

## Mission

Audit and repair the QA lane after Attempt 024 rejected a correct Gemini verdict because its positive summary did not recite three selected source details. Separate source/golden truth, production prompt/scorer agreement, selection contamination, runtime identity/parity, semantic capability, and latency/cost. Preserve DeepSeek V4 Pro's separate operational stop from Attempt 025.

## Independent truth verification

A blind source-first verifier found that the positive extraction is faithful and the negative extraction contains eight genuine defects. It removed the golden's three exact `required_in_summary` phrases because neither `QAResult` nor the production consumer requires positive summaries to recite selected scene anchors. A second independent source-first pass resolved source authority to the task-supplied excerpt (`RUDDY & GREEN`) and ended CLEAN with validator PASS, zero errors, and zero warnings.

## Production contract audit

- `cine_forge.ai.qa._build_qa_prompt` requests a QA judgment against supplied criteria and the `QAResult` schema; it does not require anchor recitation, one-to-one issue splitting, or six error-severity findings.
- Scene analysis consumes only `qa_result.passed` on success. Other QA consumers use `summary` as retry feedback after failure, so a failed judgment needs grounded actionable feedback; a passed judgment needs a substantive positive rationale, not selected source facts.
- The actual scene-analysis default is `gpt-4.1-mini`. The historical 1.0 row came from the old contract and is contaminated, not current-runtime parity evidence.
- The benchmark's full extraction is a source-fidelity capability proxy. Scene-analysis runtime actually submits a compact enrichment summary, so this two-case result is not complete payload parity or broad default evidence.

## Repair

- Removed hidden positive-summary anchor recall. A positive result now needs a substantive, non-negated positive judgment across at least three reviewed QA dimensions; generic approval adjectives, `Looks good`, negation, and anchor stuffing fail.
- Allowed semantically equivalent `heading metadata` issue grouping across heading, location, and time fields.
- Retained all eight source defects. Candidate-blind review ultimately replaced the unsafe numeric threshold with six canonical repair families. Each issue belongs to the family selected by its exact field, and must identify both the candidate defect and source fact/correction using flexible canonical concept alternatives.
- Added an isolated provider that imports the production QA prompt builder and `QAResult` schema, preserves served identity/terminal status/usage/cost, and leaves the production default and shared runtime untouched.
- Regraded Attempt 024's frozen Gemini output: deterministic `0.5999` became `1.0`; its frozen Opus score remained `0.82`, for repaired aggregate `0.91`. Classification changes from model-wrong to scorer/golden-wrong.

## Pre-final-contract identical two-case comparison

Both subjects ran no-cache at concurrency one against the same repaired source/golden/scorer/rubric through the exact shared QA prompt/schema boundary.

| Model | Served identity | Deterministic | Opus rubric | Aggregate | Mean latency | Mean subject cost |
|---|---|---:|---:|---:|---:|---:|
| GPT-4.1 Mini | `gpt-4.1-mini-2025-04-14` | 0.94375 | 0.865 | 0.904375 | 3,148 ms | $0.000955 |
| Gemini 3.7 Flash | `gemini-3.7-flash` | 0.9578 | 0.87 | 0.9139 | 2,340 ms | $0.003323625 |

Every subject returned strict schema, exact/allowed served identity, terminal stop, valid usage, the correct good/bad verdict, a substantive summary, and grounded issues. Opus passed all four judgments. Both models omitted the unsupported `DAY` defect in the bad extraction; Opus independently described that as a minor omission. Gemini's heading finding was a warning, while the remaining four findings were errors.

## Classification and decision

- **Source/golden truth:** repaired and independently CLEAN.
- **Prompt/scorer agreement:** repaired. The prior exact-anchor and issue-splitting gates were not production requirements.
- **Selection contamination:** the two-case matrix and its formerly selected anchors make historical scores non-decision-grade. Current results support only this bounded source-fidelity comparison.
- **Runtime identity/parity:** incumbent is GPT-4.1 Mini; shared prompt/schema parity is exact, but scene-analysis payload parity is limited.
- **Semantic capability:** both models correctly handled both cases. Gemini is directionally stronger by `0.009525`, but that margin is too small for a promotion claim on two selected cases.
- **Latency/cost:** both pass the `10,000 ms` and `$0.02/call` gates. Gemini is `808 ms` faster but costs about `3.48x` as much per subject call.
- **Adoption:** no default change. Neither reached the registry's exact `1.0` target, the sample is too narrow/selected, and Gemini's small quality/latency edge does not justify its higher cost.

## Candidate-blind threshold review and final contract

An independent reviewer rejected both the old six-error count and the interim
four-finding count. The count scorer could triple-credit one combined metadata
issue and pass metadata-plus-confidence feedback while omitting cast identity,
fabricated plot, and conflict. It also accepted a generic failed summary.

The final repair replaces counts with six non-duplicating repair families:
metadata, cast/identity, summary/plot, beats/events, tone, and candidate
confidence. Every family needs actionable error-severity coverage, and the
failed summary must name a source-specific critical defect. The production
prompt now asks for every distinct material defect, calibrates severity, and
requires source-specific failure feedback. The golden README and validator
define and fail closed on this exact schema; malformed, missing, duplicated,
unknown, unmapped, empty-anchor, and legacy-count variants fail validation.
It also closes two later adversarial false greens: `Accurate complete faithful
grounded.` no longer passes the positive case, and six sparse keyword findings
such as `wrong building`, `invent plan`, and `wrong tone` cannot satisfy the
negative families. Flexible paraphrases still pass through canonical per-family
concept groups; whole-sentence matching and positive fixture recitation remain
forbidden.

A final systemic semantic-polarity audit then mapped every maintained text
matching path: family issue claims, location/severity ownership, failure-summary
anchors, positive judgment/dimensions, negation, and contrast clauses. Unordered
concept presence is no longer treated as entailment. Each family contract now
requires an affirmative candidate-error term plus defect relation and a
source-correction term. Negated defects, source-correct/correction-only claims,
double negation, and anchor stuffing fail closed. Positive summaries tolerate
clear no-fault denials such as `no errors` or `zero hallucinations`, but an
affirmative material fault after `but`, `however`, or `except` invalidates the
pass. This is an honest bounded deterministic contract for the maintained
fixture vocabulary, not a claim of general natural-language entailment; agents
must phrase findings directly or the scorer fails closed.
The frozen contract also treats maintained uncertainty/modal language (`may`,
`might`, `could`, `perhaps`, `possibly`, `appears to`, `seems to`, `suggests`,
and equivalents) as non-affirmative. A hedged candidate defect or source
correction earns neither family nor failure-summary anchor credit. This rule is
clause-scoped, so a direct finding that candidate confidence is overconfident
still passes; only uncertainty about the asserted defect/correction fails.
Finally, defect and correction roles are matched independently at clause scope.
The scorer does not flatten affirmative terms across clauses: an unhedged
candidate-defect clause cannot borrow a source correction from a hedged clause,
and an unhedged correction cannot rescue a hedged defect. Separate unhedged
clauses and a single unhedged clause containing both explicit relations remain
valid. A six-family structural matrix covers both directions and overlapping
token bridge attacks.
The source-relation taxonomy is also disjoint from candidate-defect verbs.
`omits`, `claims`, `adds`, `replaces`, and similar candidate relations cannot
serve as source authority merely because a correction name occurs in the same
clause. Source roles require explicit `source`/`script` authority, an explicit
bounded comparison such as `instead of`/`rather than`/`should be`, or an
explicit confidence basis such as `given`/`despite`/`because`. The exact cast
bridge (`omits Mariner; source may have Mariner`) now fails, and validator plus
per-family invariants prevent the relation sets from overlapping again.

Because this production prompt changed after the paid runs, the table above is
pre-final-contract evidence. Frozen outputs regrade to `0.832475` for GPT-4.1
Mini and `0.834975` for Gemini 3.7; both fail the final bad-case family gate.
Latency, cost, identity, terminal status, and schema evidence remain valid, but
fresh final-contract semantic parity is unmeasured. No additional provider call
was made after the independent contract froze. This strengthens, rather than
weakens, the no-adoption decision.

Every QA score predating this final contract is now explicitly non-decision-grade,
including the former Gemini 3.6 and Gemini 3.5 Flash-Lite rows. The methodology
graph therefore exposes no QA `latestScore` or winner. GPT-4.1 Mini remains the
runtime default by inertia only, not because the registry contains current
decision-grade superiority evidence.

## Spend

Known total evaluation spend remains safely below the `$5` ceiling. The QA follow-up used about `$0.58` including subject calls and Opus grading; combined with Attempts 024/025's bounded ledger and the interrupted DeepSeek maximum, the overall invocation remains below about `$0.64`.

## DeepSeek separation

Attempt 025 remains unchanged: DeepSeek V4 Pro strict transport qualified on Together/ZDR, but the lower-cost Baidu route produced no terminal response beyond 60 seconds. Full-script semantic quality is unmeasured; latency/reliability/value fail and adoption remains rejected.
