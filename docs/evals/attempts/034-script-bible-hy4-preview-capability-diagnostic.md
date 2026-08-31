# Eval Attempt 034 — Script Bible: Hy4 Preview Capability Diagnostic

**Status:** Complete — diagnostic transport failure; production adoption deferred
**Eval:** script-bible
**Date:** 2026-08-31
**Worker Model:** Codex (GPT-5.6)
**Subject Model:** Hy4 preview (`tencent/hy4-preview`) via OpenRouter/Tencent

## Mission

Complete the missing bounded capability diagnostic after Attempts 031–033 failed
the provider-enforced strict production contract. Relax exactly one transport
constraint—omit provider `response_format` / strict JSON Schema—on approved
synthetic data, retain the complete raw envelope before parsing, and determine
whether raw Hy4 capability can be measured. This diagnostic cannot establish
production parity or adoption.

## Prior Attempts

- Attempt 031: exact strict route returned two pre-invocation Tencent shared-pool
  capacity 429s.
- Attempt 032: exact strict request returned no terminal response in more than
  115 seconds.
- Attempt 033: Tencent-pinned strict request began a chunked response but had no
  complete body at the absolute 30-second production latency gate.

No valid strict production answer exists. Capability, schema behavior, semantic
quality, and subject economics remain unmeasured.

## Frozen Diagnostic Contract

- Exact `tencent/hy4-preview`, Tencent provider pin, model fallback disabled.
- Same production `script_bible_v1.EXTRACTION_PROMPT`, source, reasoning low and
  hidden, omitted sampling, 64,000 maximum output tokens, parameter enforcement,
  no cache, concurrency one, and synthetic-data privacy posture.
- Relax only provider-enforced `response_format` / JSON Schema. Do not append a
  JSON-only instruction or otherwise change the prompt.
- Retain the raw response envelope in ignored/protected `output/` before parsing;
  record safe hash, size, and pointer in durable evidence.
- Start with the same tiny repo-authored synthetic radio-studio source. A 180-
  second diagnostic deadline may exceed the production 30-second latency gate
  only to isolate raw capability; production latency remains failed.
- Continue to a one-case Open Frequency diagnostic only after terminal exact
  identity, complete output, valid usage/cost, and cumulative cap checks.
- If continued, inspect a zero-cost one-cell topology first and use the frozen
  structural scorer and Opus 4.6 rubric. Any scores remain diagnostic-only.
- Original US$0.75 cumulative ceiling: confirmed spend `$0`; conservative prior
  exposure `<=US$0.324`; remaining conservative exposure `<=US$0.426`.
- No private/second corpus, comparator, prompt/golden/scorer/reasoning/token/route
  change, default change, commit, push, merge, or deploy.

## Plan

1. Refresh owner discovery and the exact OpenRouter endpoint catalog.
2. Run the tiny one-variable diagnostic and retain the raw envelope before parse.
3. If it qualifies and the ledger allows, inspect the resolved one-cell Open
   Frequency diagnostic topology before any additional paid call.
4. Run only that one case, then apply the frozen deterministic and rubric
   contracts offline to retained output.
5. Record exact provenance, costs/exposure, layered verdict, registry, story,
   and validation. Keep production adoption deferred regardless of diagnostic
   quality because strict production transport failed.

## Work Log

- 20260831-0928: re-read the complete owner evaluation and companion skill
  contracts, current alignment/ADR/eval/runbook surfaces, Story 217, Attempts
  031–033, and frozen runtime task/prompt/schema/scorer/golden/provider. Owner
  discovery completed against configured native providers; public OpenRouter
  metadata still exposed the sole Tencent 20260827 route with unchanged pricing
  and advertised structured-output controls. Prepared an ignored diagnostic
  runner that writes the raw envelope before parsing and enforces a 180-second
  total deadline. No provider call or new spend yet.
- 20260831-0937: submitted one exact Tencent-pinned diagnostic request with only
  `response_format` / JSON Schema omitted. OpenRouter returned HTTP 200 headers,
  `X-Generation-Id: gen-1788190415-zAmnrXHfWcL1fbYk8NZ6`, and chunked transfer,
  but zero body bytes arrived before the 180.006-second client stop. The empty
  partial raw envelope was retained before any parse attempt (0 bytes, SHA-256
  `e3b0c442...b855`). No served identity, finish reason, usage, cost, schema,
  semantic content, or score exists. Stopped before Open Frequency and judge.
  Confirmed spend remains `$0`; conservative cumulative unreconciled exposure is
  now `<=US$0.486`, leaving `US$0.264` under the owner ceiling.

## Mismatch Classification

- Access/transport/reliability: exact route accepted the request at HTTP 200 but
  failed both the 30-second production gate and 180-second diagnostic deadline.
- Strict-mode isolation: not isolated. Omitting the strict provider contract did
  not produce a terminal response, so this evidence does not attribute the
  failure specifically to structured output.
- Identity/finish/schema/parsing/semantics: unmeasured; zero body bytes existed.
- Cost: provider-reported cost and usage unavailable; confirmed spend `$0`;
  conservative current exposure `<=US$0.162`, cumulative `<=US$0.486`.
- Scoring: correctly not run because the terminal exact-identity prerequisite
  failed.

## Conclusion

Attempt 034 closes the missing capability diagnostic honestly: Hy4 did not
produce a terminal response even after the only relaxation and extended bounded
wait. Raw capability remains unmeasured, the decision-bearing Open Frequency
lane was ineligible, and exact-runtime Script Bible adoption remains **defer**.
No diagnostic result can repair the already-failed strict production transport.

## Definition of Done Checklist

- [x] Read every prior Hy4 attempt and current frozen contract
- [x] Predeclared the one-variable diagnostic before spending
- [x] Retained complete or partial raw envelope before parsing
- [x] Recorded identity, finish, schema/parsing, latency, usage, and cost
- [x] Scored only if the progressive diagnostic gate qualified
- [x] Updated registry, story, and durable provenance
- [x] Validated proportionately
- [x] Preserved diagnostic-only and production-defer truth
