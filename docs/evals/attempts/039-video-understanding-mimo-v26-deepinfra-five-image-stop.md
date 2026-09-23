# Eval Attempt 039 — MiMo V2.6 DeepInfra Five-Image Transport Stop

**Status:** inconclusive — both requested models are incompatible with the maintained five-JPEG packet on the pinned route
**Date:** 2026-09-22
**Scope:** `video-understanding` v3 only; ScriptBible excluded
**Candidates:** `xiaomi/mimo-v2.6-flash` and `xiaomi/mimo-v2.6-pro` through OpenRouter, provider order `DeepInfra`, no fallback

## Frozen Contract

The only eligible inputs were six maintained repo-owned synthetic controls with five ordered JPEGs each, neutral timing facts, no audio, MP4, transcript, semantic title, or quarantined case. The requests selected provider `DeepInfra` and disabled fallback. The contemporaneous endpoint catalog listed its FP8 tag, but the requests did not enforce quantization and responses did not prove a specific endpoint. Required: provider-enforced strict `VideoAnalysisPrediction` JSON, exact served model/provider, terminal completion, reconciled usage and provider-reported cost. Gates: overall >=0.80, average subject latency <=15,000 ms, and average subject cost <=US$0.02.

The ladder was native five-JPEG strict probe, harness-parity probe, then six serial controls. A fresh Gemini 3.5 Flash-Lite comparison would run only if a candidate cleared all absolute gates. No default change, commit, or push is authorized.

## Current Route Evidence

OpenRouter endpoint metadata checked 2026-09-22 listed both exact models as `text+image+audio+video->text`, DeepInfra FP8 endpoints, `structured_outputs`, and list input/output pricing of US$0.14/US$0.28 per M tokens (Flash) and US$0.435/US$0.87 per M tokens (Pro). The metadata exposed Flash DeepInfra status `-2` and Pro status `0`; undocumented values were not treated as availability or quality evidence.

## Native Strict Probes

Each native request submitted the same public/synthetic five-JPEG packet with OpenRouter `provider.order=["DeepInfra"]`, `allow_fallbacks=false`, `require_parameters=true`, and strict JSON Schema. Both received HTTP 400 before inference. OpenRouter identified DeepInfra as upstream and returned the safe detail: `Too many images in request: 5 > 4`.

| Candidate | Served identity / usage / cost | Result |
| --- | --- | --- |
| `xiaomi/mimo-v2.6-flash` | absent | rejected before inference: DeepInfra maximum is four images |
| `xiaomi/mimo-v2.6-pro` | absent | rejected before inference: DeepInfra maximum is four images |

No four-image truncation, fallback provider, relaxed schema call, harness parity, six-case subject run, judge, or Gemini reference run was performed. A four-image result would answer a different task contract.

## Spend and Verdict

The failures had no response ID, terminal model, usage, or provider receipt. No inference charge is confirmed. Because missing usage is not proof of zero billing, the full US$1.50 approved cap is reserved as unresolved upper exposure and no additional provider or judge call is authorized in this attempt.

- **Access:** configured central OpenRouter credential; the exact route accepted the request then rejected its image cardinality.
- **Transport:** blocked for both candidates on the maintained five-JPEG contract.
- **Reliability, capability, and economics:** not measured.
- **Adoption:** defer; retain the Gemini 3.5 Flash-Lite reference unchanged.

Do not retry either unchanged DeepInfra arm. Reopen only with a new approved route-specific source proving that a specifically identified DeepInfra endpoint accepts five images, or with separate approval for a different maintained benchmark contract.

## Reproducibility

- Base: `5d40a20ed3ead9a97938469a47eb379ab4eecb43`
- Worktree: `/Users/cam/.codex/worktrees/mimo26-eval-20260922/cine-forge`
- Branch: `codex/mimo26-eval-20260922`
- Credential: temporary ignored `.env`, variable `OPENROUTER_API_KEY`, removed after the attempt.
- Exact source and patch hashes: `docs/evals/story-221-mimo-v26-video-contract-manifest.json`.
