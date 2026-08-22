# Eval Attempt 029 — Script Bible: Ox Alpha Public/Synthetic Rerun

**Status:** Deferred — strict schema unavailable and diagnostic returned Markdown
**Eval:** script-bible
**Date:** 2026-08-22
**Worker Model:** Codex (GPT-5.6)
**Subject Model:** Ox Alpha (`stealth/ox-alpha`) via OpenRouter

## Mission

Rerun Ox Alpha after correcting Attempt 028's over-broad privacy and route
requirements. The owner approved Open Frequency and The Mariner even when the
anonymous Stealth provider may retain or train on them. No account setting,
runtime default, prompt, scorer, golden, commit, push, or deployment is
authorized.

## Corrected Decision Contract

- Request exact `stealth/ox-alpha`; validate the exact served model and never
  provide a fallback model list.
- Do not pin the sole Stealth endpoint. Record the resolved provider instead.
- Omit ZDR and denied-data-collection routing filters for these approved
  public/owner-controlled fixtures.
- First require provider-enforced strict `ScriptBible` JSON with
  `require_parameters=true`.
- If that fails before an answer, use one diagnostic arm which changes only
  parameter enforcement. It may measure raw capability but cannot establish
  drop-in transport or adoption.
- Start with Open Frequency. Require overall `>=0.90`, deterministic `>=0.70`
  plus every hard assertion, rubric `>=0.80`, latency `<=30s`, and cost
  `<=$0.01`. Advance to The Mariner and a fresh incumbent only after every
  absolute first-case gate passes.
- No cache, concurrency one, US$0.75 aggregate ceiling.

## Work Log

- The endpoint snapshot still exposed exact `stealth/ox-alpha` through one
  Stealth endpoint at zero list price. It advertised `response_format`, but not
  a distinct strict-structured-output capability.
- The corrected strict request removed provider pinning, ZDR, and
  data-collection denial while retaining `require_parameters=true` and strict
  JSON Schema. OpenRouter returned HTTP 404 before invocation because no
  endpoint could handle the requested parameters.
- The one allowed diagnostic disabled only `require_parameters`; it kept the
  strict `response_format`, exact model, production prompt/schema, low
  reasoning, and omitted privacy filters. The model returned terminal content
  after 21,629 ms and passed exact served-model validation, but the content was
  a Markdown script bible rather than JSON. Pydantic rejected it at the first
  byte, so it could not enter the maintained structural or semantic scorer.
- The progressive absolute transport gate stopped Open Frequency scoring. The
  Mariner, incumbent, and Opus judge were not invoked. Spend remained `$0`.
- The adapter validated before persistence, so the raw Markdown body was not
  retained; only its sanitized `# SCRIPT BIBLE` prefix and `*End of Bible.*`
  suffix survived in the validation traceback. There is therefore no honest
  offline fenced-JSON extraction or local diagnostic score for this response.
- Final bounded follow-up added ignored raw-body persistence before parsing and
  a tracked hash/pointer, without changing the production route. One fresh
  Open Frequency diagnostic omitted `response_format`, `require_parameters`,
  privacy filters, and provider pinning; it appended an explicit JSON-only
  diagnostic instruction and allowed only whole-response Markdown-fence
  removal before normal Pydantic validation.
- The exact model returned a complete 7,041-byte fenced response in 47,799 ms.
  Fence removal succeeded, but the JSON was malformed at line 11 because a
  quoted screenplay line inside `end_scene` was not escaped. No repair beyond
  fence removal was permitted, so the scorer and judge did not run. The raw
  body remains ignored at
  `output/evals/ox-alpha-script-bible-20260822/open-frequency-raw.md`, recorded
  by SHA-256 and size in the tracked evidence manifest.
- The final diagnostic independently missed the 30,000 ms latency gate. The
  Mariner and incumbent therefore remained correctly unrun even if the JSON
  syntax had been valid.

## Classification and Verdict

- **Access:** available on the approved relaxed route; one model completion was
  received.
- **Transport:** blocked for production parity. Strict parameter enforcement
  rejected the route, and the bounded diagnostic did not return a valid
  `ScriptBible` artifact.
- **Reliability:** two diagnostic completions, neither produced a valid
  ScriptBible artifact.
- **Capability:** not scored. The diagnostic shows instruction-following toward
  the subject matter, but Markdown cannot be treated as a semantic miss or a
  valid ScriptBible result under this eval.
- **Economics:** provider spend `$0` of `$0.75`; the final diagnostic took
  47,799 ms and missed the 30-second gate.
- **Adoption:** defer for exact-runtime script bible. The result supports an
  adapter-required exploratory hypothesis, not a drop-in replacement.

## Mismatch Classification

The first diagnostic format miss is **ambiguous and runtime-blocking** for the exact
structured-output boundary: parameter enforcement was intentionally disabled,
so the evidence cannot distinguish a model JSON miss from the endpoint ignoring
the requested schema. No screenplay facts were scored, so there is no
source-content mismatch to classify. The final JSON-only diagnostic is
**model-wrong and runtime-blocking** for diagnostic instruction following: the
whole fence was validly removed, but an embedded quotation remained unescaped.

## Evidence

- Sanitized run record:
  `docs/evals/story-215-ox-alpha-public-synthetic-rerun-evidence.json`
- Base: `94861914623fff237ffb4ab379fa9f995a58da1e`
- Candidate and judge calls: two and zero, respectively
- Spend: `$0`

## Retry State

`exhausted-until-new-trigger`. Retry the exact-runtime lane when the endpoint
supports required strict schema, or propose a separately approved adapter lane
with prompt-level JSON and deterministic repair. Do not represent such an
adapter lane as native strict-schema parity.
