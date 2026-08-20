# Eval Attempt 027 — Script Bible: GLM-5.3 Bounded Runtime Evaluation

**Status:** Deferred — no Z.ai key configured
**Eval:** script-bible
**Date:** 2026-08-20
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** Z.ai GLM-5.3 (`glm-5.3`); Gemini 3.5 Flash-Lite comparator gated on complete candidate success

## Mission

Qualify exact Z.ai pay-as-you-go general API access and provider-enforced strict
`ScriptBible` output, then measure one frozen low-reasoning Open Frequency arm
only if the full transport contract qualifies. Advance to the incumbent and
The Mariner only after every absolute gate passes. No default change is
authorized.

## Prior Attempts

Attempts 020–023 and 025 establish the bounded exact-runtime ladder: a valid
response is insufficient when strict transport, latency, cost, reliability, or
privacy fails. Attempt 026 repaired a separate QA production contract and does
not change this lane. Do not reuse historical one-corpus rows as current truth,
weaken the schema, tune the scorer/golden, or expand after a hard gate failure.

## Plan

1. Preserve Story 214's decision contract and `$5` aggregate ledger.
2. Verify exact account access to `glm-5.3` on the pay-as-you-go general API.
3. Run tiny native access, exact strict-schema, and harness-parity probes.
4. Predeclare `low` primary and `max` ceiling on the same tiny calibration;
   omit sampling and freeze from contract/operational evidence before scoring.
5. If qualified, run one Open Frequency case at no cache/concurrency one,
   inspect all gates, and apply the progressive stop.
6. Record every executed and blocked stage without changing production code or
   defaults.

## Predeclared Matrix and Gates

- Candidate: direct Z.ai `glm-5.3`, `thinking.type=enabled`, sampling omitted.
- Calibration: `reasoning_effort=low` primary and `max` ceiling on identical
  tiny public input; max cannot advance independently to semantic scoring.
- First fixture: complete repo-authored synthetic Open Frequency screenplay.
- Comparator/second fixture: fresh Gemini 3.5 Flash-Lite and The Mariner only
  after every candidate gate and privacy eligibility passes.
- Quality: overall `>=0.90`; deterministic `>=0.70` plus all hard gates;
  frozen Opus 4.6 rubric `>=0.80`; every assertion passes.
- Operations: latency `<=30,000 ms`; subject cost `<=$0.01`; exact requested
  and served identity; terminal complete output; raw usage/cost; no fallback;
  provider-enforced strict `ScriptBible` JSON.
- Execution: no cache, concurrency one, one transient retry, one documented
  request-variable repair, no semantic retry after valid completion.
- Spend: `$0` before calls; `$5` aggregate hard cap.

## Work Log

- 20260820-0000: official Z.ai documentation and the Conductor handoff identify
  exact `glm-5.3`, general Chat Completions, forced thinking, low/high/max,
  1M context, 128K output, and list pricing. The API reference documents only
  `response_format.type=json_object`; its structured-output guide instructs
  callers to place a schema in the prompt and validate client-side. This is not
  provider-enforced strict JSON Schema. No paid call yet; ledger `$0`.
- 20260820-0001: the current and shared CineForge dotenvs, loaded only through
  `scripts/with_cine_forge_provider_env.py`, contain no `ZAI_API_KEY`,
  `CINE_FORGE_ZAI_API_KEY`, or `ZHIPUAI_API_KEY`. The connected General
  Reference document has no Z.ai/GLM/Zhipu entry. Exact authenticated account
  access is therefore not currently configured. No credential values were read
  or exposed.
- 20260820-1507: both available Z.ai API-key portal sessions were logged out.
  A credential-free POST to the exact general API endpoint returned HTTP 401,
  provider code `1001`, and “Authentication parameter not received in Header”.
  The model was not invoked and spend remained `$0`.
- 20260820-1508: required CineForge live discovery completed for every currently
  configured provider; Z.ai is not a configured lane. Repository search found
  no prior CineForge GLM subject row or attempt. Per Cam's close-out direction,
  the attempt stops as deferred-no-key. No strict-schema/parity/semantic,
  incumbent, judge, or Mariner call ran.

## Mismatch Classification

- **Access/provider-wrong, pre-response:** no Z.ai key or authenticated account
  session exists in CineForge's configured credential surfaces; the exact
  endpoint returned 401 without invoking the model.
- **Transport incompatibility, not model-wrong:** official Chat Completions
  documentation exposes `text` and `json_object`, not a `json_schema` response
  contract; the official structured-output example uses prompt instructions and
  client-side validation. This does not satisfy the mandatory provider-enforced
  strict `ScriptBible` gate. A live authenticated rejection/acceptance could not
  be measured without a key.
- **Capability:** not measured. No valid model response, scorer, golden, or judge
  mismatch exists to classify.

## Conclusion

**Result:** deferred — no Z.ai key configured; transport/capability not measured
**Score before:** N/A
**Score after:** N/A
**Latency before:** N/A
**Latency after:** N/A
**Cost before:** N/A
**Cost after:** N/A

**Access:** blocked. No configured credential or signed-in account surface.

**Transport:** blocked before authenticated native/strict/parity qualification;
provider-enforced strict JSON Schema is also absent from current official docs.

**Reliability/capability/economics:** not measured. List pricing is known, but no
subject call occurred. Total spend was `$0` of the approved `$5` cap.

**Adoption:** defer. Keep provisional `gemini-3.5-flash-lite`; no defaults or
production providers changed.

**What NOT to retry:** do not repeat credential-free probes, use Coding Plan or
a router as a silent substitute, score `json_object` plus Pydantic validation,
or send private fixtures.

**Retry state:** exhausted-until-new-trigger

**Retry when:** a CineForge-scoped pay-as-you-go Z.ai credential is explicitly
configured and current first-party or live native evidence can test provider-
enforced strict `ScriptBible` JSON. If strict schema remains unavailable, close
again at transport without semantic spend.

## Definition of Done Checklist

- [x] Read all previous exact-runtime script-bible attempts before starting
- [x] Ran an eval with `--no-cache`, or recorded the pre-scoring blocker
- [x] Recorded score/latency/cost or explicit not-measured values
- [x] Updated registry attempt history
- [x] Classified all significant mismatches or blockers
- [x] Set retry state and retry conditions honestly
- [x] Did not weaken the contract or silently accept a failure
