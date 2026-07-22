# Eval Attempt 016 - Independent Closeout Adversarial Review

**Status:** Succeeded with documented limitations
**Eval:** repository-eval-decision-contracts
**Date:** 2026-07-22
**Worker Model:** GPT-5.6 plus independent GPT-5.6 reviewers
**Subject Model(s):** No subject, judge, image, video, or paid provider call

## Mission

Run an independent adversarial review after the main Story 208 repairs, reproduce
every residual false-green claim with offline fixtures, and close decision-path
gaps before freezing the contract manifest. This pass treats report aggregation,
runtime/benchmark alignment, token billing, and registry provenance as part of
the eval contract rather than administrative follow-up.

## Baseline Reproduction and Classification

- Real-AI-previz accepted a decision-grade append containing only a subset of
  the base cases and could rank cases with unequal sample counts.
  **Classification:** harness-wrong and provider-decision-blocking.
- Video, previz, and final-render reports trusted an LLM-rubric `pass: true`
  below their explicit `>=0.8` floor. Previz could also promote from a partial
  cost mean or above its registry cost ceiling; video and final-render omitted
  maintained latency/cost/quality adoption limits.
  **Classification:** scorer/report-wrong and default-decision-blocking.
- Final-render trusted a filtered manifest, independent stored aggregate scores,
  missing subject output, and summary runtime/reference means that were not
  recomputed from raw runs.
  **Classification:** evidence-contract-wrong and default-decision-blocking.
- Canonical video reporting was absent from its registry command. Previz and
  final-render chained the report with `&&`, so Promptfoo's normal assertion
  failure exit code 100 skipped the diagnostic report.
  **Classification:** runner-control-flow-wrong and mismatch-classification-blocking.
- Entity acceptance used bidirectional substrings (`OAR` matched `BOARD`), PDF
  reflow could convert an ordinary two-column table into dialogue, and
  round-trip dialogue search could satisfy one speaker from a later speaker's
  line. **Classification:** deterministic-test false greens; runtime-impacting
  only at the owning ingest/interchange boundaries.
- Gemini usage accounting priced visible candidate tokens while omitting billed
  hidden thinking. The adopted ScriptBible configuration used a 4,096-token,
  `temperature: 0` runtime request even though its benchmark used 65,536 output
  tokens with sampling controls omitted.
  **Classification:** cost/provenance-wrong plus runtime/benchmark mismatch;
  adoption proof blocked until exact-runtime evidence exists.
- Registry metric extraction matched only eval/model, allowing fresh latency
  and cost to be inserted into an older score row while retaining its result
  file, date, SHA, and quality provenance.
  **Classification:** evidence-lineage-wrong and decision-blocking.
- Registry extraction did not prove that the retained result used the current
  task's exact provider membership, model configuration, prompt bytes,
  assertions, rubric, grader, cases, and row-level test contract. A filtered
  one-model result could therefore be confused with an arbitrary label, and a
  full task config could be cited for a provider absent from the result.
  **Classification:** task-provenance-wrong and decision-blocking.
- Production and custom eval transports did not consistently retain or compare
  the provider-returned model and response ID. In particular, Anthropic model
  identity was dropped, OpenAI/xAI metadata trusted the requested model, custom
  labels could conceal a different returned model, and visual Gemini evidence
  omitted `responseId`.
  **Classification:** call-identity-wrong and decision-blocking.
- Non-Gemini token metadata accepted strings, booleans, negative counts, and
  unreconciled totals in paths that produced normalized usage or cost.
  **Classification:** accounting-contract-wrong and decision-blocking.
- JSON result loading used the standard last-key-wins decoder, so duplicate
  nested keys could silently replace model, usage, score, or test identity.
  **Classification:** evidence-parser-wrong and decision-blocking.
- The generated methodology graph could resurrect registry rows already marked
  contaminated, while broad story category references could make narrow evals
  appear to own unrelated methodology categories.
  **Classification:** planning-lineage-wrong and decision-blocking.
- A shared editable virtualenv could import the canonical checkout while tests
  ran in this worktree, and the inherited `PYTHONPATH` could defeat the intended
  local-source boundary.
  **Classification:** test-environment-wrong and regression-blocking.
- Retained final-render packets lacked immutable prompt/video envelopes, direct
  input bytes, source-manifest linkage, and runtime response identity. The live
  runner also read request notes from the wrong artifact field.
  **Classification:** retained-evidence-wrong and provider-decision-blocking.

## Repairs

- Require exact, unique, balanced case matrices before runtime aggregation.
- Recompute score and runtime aggregates from raw retained evidence; enforce
  numeric rubric and registry adoption floors independently of stored pass flags.
- Preserve reports on Promptfoo exit 100 and prove each maintained command invokes
  its current report.
- Make deterministic matchers stop at true semantic boundaries and add direct
  adversarial regressions for every reproduced false green.
- Align Gemini runtime requests and billed-token accounting with the evaluated
  contract, while retaining visible-token telemetry separately.
- Permit registry metric updates only when the selected result file is the exact
  provenance identity already recorded by the unique score row and proves the
  current task's exact provider configuration, prompt/rendered bytes,
  assertions, rubric, grader, cases, and row-level contract.
- Require live provider responses to retain a non-empty response ID and returned
  model, preserve both identities in production and eval evidence, and reject
  substitution. OpenAI alone permits an undated alias to resolve to its exact
  same-base dated snapshot; Anthropic permits only the enumerated legacy 4.5
  alias mapping, while Anthropic 4.6+, Gemini, and xAI remain exact. Custom text
  providers now require an explicit `config.model`.
- Apply strict nonnegative integer and total-reconciliation rules to provider
  usage before normalized telemetry, scoring, or billing; preserve visible and
  hidden/reasoning tokens separately.
- Reject duplicate keys at every depth when loading retained result JSON.
- Exclude contaminated/non-decision-grade history from generated planning views
  and derive eval methodology ownership only from direct declared references.
- Force the active checkout's `src` tree ahead of inherited environment paths and
  test that the imported package belongs to the current worktree.
- Snapshot and hash typed final-render artifacts, every resolved direct input,
  generated media, source manifests, and runtime identities. Historical media-
  only packets are explicit context, never reproducible runtime evidence.

## Validation

Final combined validation is recorded in Story 208's work log and the frozen
contract manifest. The honest unit gate passed `2,011`; the full suite passed
`2,096` with `5` explicit skips; independent identity/accounting/provenance
review passed `404` focused controls. Repository Ruff, `21` UI tests plus UI
lint/build, all `16` offline Promptfoo task validations, all `19` textual
goldens with `38` explicit warnings, all `272` retained JSON files through the
duplicate-key loader, registry consistency, and all `165/165` terminal ledger
rows passed. Methodology compile/check, 39-skill synchronization, compromise
reporting, size reporting, final-render hash verification (`36` media files;
`6` retained-media-only packets), contract-manifest rebuild/check, and
`git diff --check` also passed. Only the documented architecture-audit and UI-
scout freshness warnings remain. No subject, judge, image, or video provider was
called during this closeout attempt.

## Conclusion

The adversarial replay found and closed additional false-green paths after the
initial audit appeared structurally green. Current contracts fail closed on
partial matrices, stale aggregates, mismatched model identity, malformed usage,
duplicate JSON keys, stale task bytes, contaminated history, wrong-checkout
imports, and retained-media-only final-render claims.

All historical model scores remain diagnostic context because the goldens,
prompts, scorers, rubrics, cases, or runtime contracts changed. Fresh paid
subject-plus-Opus evidence is deliberately deferred until this provisional
contract bundle has an immutable commit identity and a bounded run can change a
runtime decision. One earlier offline test diagnosis accidentally reached Haiku
before live-call isolation was repaired (estimated cost `$0.00748`); it is not
eval evidence. Story 208 remains open under `/mark-story-done` because repaired
golden-wrong evals have not yet received that fresh decision-grade rerun.

During the wider audit, a contact-sheet command also overwrote ten ignored
historical Story 186 storyboard outputs in the canonical checkout. Eight were
restored byte-for-byte; one panel and its only full grid were unrecoverable and
are quarantined by the local `AUDIT_CORRUPTION.md`. No tracked source, benchmark
media, or retained result was damaged. Story 208's final work-log disclosure
records both original/current hashes and exact paths.

**Recovery postscript (2026-07-22):** Backblaze later restored the remaining
panel and full grid byte-for-byte; both match their recorded original SHA-256
values. The local corruption is resolved. Historical v2 results remain
contaminated and non-decision-grade for the independent failures above.
