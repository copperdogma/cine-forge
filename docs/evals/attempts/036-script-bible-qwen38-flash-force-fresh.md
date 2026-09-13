# Eval Attempt 036 — Script Bible: Qwen3.8 Flash Force-Fresh Retry

**Status:** Inconclusive — Alibaba shared-pool access constrained before inference
**Eval:** script-bible
**Date:** 2026-09-13
**Worker Model:** Codex (GPT-5.6)
**Subject Model:** Qwen3.8 Flash (`qwen/qwen3.8-flash`) via OpenRouter / Alibaba

## Mission and Frozen Contract

Retry the exact production-shaped transport gate that blocked Attempt 031, then
run one force-fresh, public/synthetic Open Frequency case only if native strict
transport and harness parity qualify. Require exact returned model identity,
Alibaba pinning with no fallback, terminal completion, provider-enforced strict
`ScriptBible` JSON, reconciled raw usage, and provider-reported cost before
semantic scoring.

Frozen settings were the production `script_bible_v1.EXTRACTION_PROMPT`,
production `ScriptBible` schema, low hidden reasoning excluded from output,
omitted sampling controls, 65,536 output-token ceiling, maintained deterministic
scorer, cross-provider Opus 4.6 rubric, no cache, concurrency one, and a US$0.75
aggregate cap. Any miss against overall `0.90`, deterministic `0.70` plus every
hard assertion, rubric `0.80`, latency 30 seconds, or subject cost US$0.01 would
stop expansion. No private payload, default change, deployment, commit, or push
was authorized.

## Route Choice

OpenRouter now lists two endpoints for the exact route. Alibaba still advertises
the canonical `qwen/qwen3.8-flash-20260826` checkpoint with 1M context and
unknown quantization. Makora advertises the same checkpoint label but fp4
quantization and 262,144 context. Because this run was a force-fresh retry of
Attempt 031's Alibaba transport blocker, changing to Makora after observing a
failure would alter a decision-bearing route variable. Makora was recorded but
not called.

## Spend Ledger

| Stage | Calls | Spend (USD) | Cumulative (USD) |
| --- | ---: | ---: | ---: |
| Preflight | 0 | 0 | 0 |
| Native strict probe | 1 attempted, 0 invoked | 0 | 0 |
| One transient retry | 1 attempted, 0 invoked | 0 | 0 |
| Harness parity / subject / judge | 0 | 0 | 0 |

## Result

Current public OpenRouter evidence dated 2026-09-13 confirmed the exact route,
structured outputs, and list prices of US$0.15/M input and US$0.47/M output.
The focused request-shape suite passed nine tests before live execution.

The first native strict-schema request returned HTTP 429 before inference.
OpenRouter attributed the limit to the Alibaba upstream shared pool rather than
the client account. After the one predeclared 20-second wait, the retry returned
the same pre-inference 429. Neither attempt produced a response ID, served model,
usage, cost, or `ScriptBible` output. Provider spend was US$0.

The ladder stopped before harness parity, Open Frequency, deterministic scoring,
Opus judging, The Mariner, or an incumbent rerun.

## Layered Verdict

- **Access:** constrained. The exact catalog route exists, but the pinned
  Alibaba managed endpoint rejected both authorized requests before inference.
- **Transport:** blocked before invocation; strict-schema behavior was not
  observed live.
- **Reliability:** failed for the managed Alibaba route in this bounded attempt;
  model reliability is not measured.
- **Capability:** not measured. No semantic output existed.
- **Economics:** listed pricing qualified; measured spend US$0; subject latency
  and cost were not measured.
- **Privacy:** only the tiny synthetic probe was sent. Open Frequency was not
  sent; `data_collection=deny` was requested and ZDR was not claimed.
- **Adoption:** defer. No evidence supports a CineForge default change.

## Classification and Retry State

Both failures are provider-capacity/access evidence, not `model-wrong` semantic
evidence. This is the second dated campaign in which the managed Alibaba shared
pool rejected the exact strict request before inference. Do not repeat unchanged
catalog-driven probes. Retry the Alibaba arm only after authorized Alibaba BYOK
or direct evidence that the shared pool accepts the exact request. A future
Makora fp4 evaluation must be predeclared as a separate configuration and cannot
be used retroactively as evidence about Alibaba.

## Evidence and Commands

- Evidence: `docs/evals/story-219-qwen38-flash-force-fresh-evidence.json`
- Focused request-shape test:
  `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_openrouter_script_bible_provider.py -q`
- Discovery:
  `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/with_cine_forge_provider_env.py /Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/discover-models.py --check-new`
- Native strict probe: repository provider
  `_call_openrouter_strict(model='qwen/qwen3.8-flash', upstream_provider='Alibaba', max_tokens=4096, reasoning_effort='low', require_parameters=True, data_collection='deny', zdr=False)`

The native command was executed twice only: the initial request and one retry
after 20 seconds. Both stopped before inference.

## Definition of Done Checklist

- [x] Read prior attempts and current owner contracts
- [x] Ran force-fresh transport probes only at concurrency one
- [x] Recorded exact route, error class, zero spend, and unmeasured layers
- [x] Updated registry attempt history without inventing a score
- [x] Preserved sanitized evidence and contract hashes
- [x] Applied the progressive stop without hidden retries
