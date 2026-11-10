# Whole-task maintained control preflight — 2026-11-09

Read-only source audit plus offline normalization checks. No provider calls, credentials,
runtime code edits, commits, or changes to another checkout. This document is the only
worker-owned edit. The US$5 control allocation is provisional; the parent owns the
US$20 aggregate authorization and candidate/judge/recovery reservations.

## Admission verdict

The unchanged maintained control cannot honestly be certified to complete all three
scripts within US$5. Nor can the first complete paired case plus judge and recovery
be guaranteed within US$20 from source entity counts alone. A physical-request guard
can enforce the aggregate spending stop, but a denied request makes the case
**inconclusive**, not a completed control or quality pass. Release settled reservation
only after retaining raw usage; an unresolved charge keeps its full reservation.

Two project-configuration extractions per control alone allow 6 physical requests
and 155,648 generated tokens, costing US$2.33472 for output. Across three controls
that is US$7.00416 before script bibles, analysis, entity extraction, input, or QA.
This is a ceiling allowance, not a prediction that the outputs will be that large.

## Maintained settings and prices

`benchmarks/scripts/full_script_throughput_eval.py:38-41,187-196,240-248` explicitly
sets default Sonnet 4.6, work Haiku 4.5 dated 20251001, verify/QA GPT-4.1-mini,
and escalate Opus 4.6. These runner settings, not API UI defaults or module manifests,
define this control. `ModelStrategy` schema defaults differ (`schemas/models.py:107`).

| Model | Current native input/output USD per million | Owner llm.py table |
|---|---:|---:|
| claude-haiku-4-5-20251001 | 1 / 5 | 0.80 / 4 (stale) |
| claude-sonnet-4-6 | 3 / 15 | 3 / 15 |
| claude-opus-4-6 | 5 / 25 | 15 / 75 (stale) |
| gpt-4.1-mini | 0.40 / 1.60 | 0.40 / 1.60 |

Primary sources checked on 2026-11-09: [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing)
and [GPT-4.1-mini model pricing](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
Anthropic ephemeral five-minute cache writes cost 1.25 times base input; do not assume
cache hits. GPT-4.1-mini is marked deprecated on its current model page; account
availability was not checked. No paid model discovery or provider entitlement query
was authorized in this preflight. The maintained model choices are unchanged.

Runtime precedence matters: entity discovery's runtime work model wins over the
recipe's Gemini discovery model; it therefore uses Haiku. Conversely scene analysis
only reads stage params and defaults to Sonnet, ignoring runtime work/escalate values.
Its semantic retry repeats Sonnet. The full control's tier-one normalization and
recipe `skip_qa: true` on entity bibles mean no Opus sends on this validated route.

## Offline local evidence

Ran current worktree `src` with the existing owning-repo Python interpreter and
`PYTHONDONTWRITEBYTECODE=1`. Replaced all four provider transport globals with a
function that raises `AssertionError('Network forbidden')`. Called maintained ingest
and normalization directly, then deterministic scene splitting. All checks passed:

| Fixture | Words / characters | Normalization | Scenes / uncertain boundaries |
|---|---:|---|---:|
| open_frequency.fountain | 597 / 3447 | Tier 1, code passthrough, US$0 | 4 / 0 |
| last_ferry.fountain | 553 / 3142 | Tier 1, code passthrough, US$0 | 4 / 0 |
| matinee_echo.fountain | 555 / 3121 | Tier 1, code passthrough, US$0 | 4 / 0 |

Every stage in both current recipes yields `build_stage_model_attempt_plan(...) == []`:
the retry planner reads only stage `work_model`/`model`, absent in these recipes.
Thus recipe `max_attempts_per_stage: 4` does **not** multiply these controls. Driver
`module_execution.py` has no alternate attempt when the plan is empty.

## Physical-call matrix, per control

All counts below include native helper retries. Define C = approved characters,
L = approved locations, P = approved props. Full-character limits conservatively
cover minor-character extraction too. Intended source counts are not execution caps.
The matrix assumes these locally validated fixtures remain unchanged, four scenes,
one discovery chunk (<12,000 characters), one analysis batch (<2,500 words), and the
autonomous runner's skipped canon review gate.

`call_llm` (`ai/llm.py:112-265`) defaults to two retries, hence at most three physical
sends per invocation. Structured truncation is rejected even where the caller omits
`fail_on_truncation`; positive explicit token caps grow 1.5 times per truncation.
Thus explicit cap x reserves x + floor(1.5x) + floor(2.25x). Unspecified Anthropic
caps stay 16,384 on all three attempts because active_max_tokens remains None.

| Stage/helper | Model | Invocation ceiling | Physical sends | Output tokens over all sends |
|---|---|---:|---:|---:|
| ingest / normalize | code | 0 | 0 | 0 |
| breakdown action entities | Haiku | 4 | 12 | 7,600 (400/600/900 per scene) |
| breakdown boundary validation | Haiku | 0, proven offline | 0 | 0 |
| script bible | Haiku | 1 | 3 | 192,000 (64,000 each; requested 65,536 clipped by transport) |
| ingest project-config detection | Sonnet | 1 | 3 | 77,824 (16,384/24,576/36,864) |
| ingest project-config QA | GPT-4.1-mini | 1 | 3 | 5,700 (1,200/1,800/2,700) |
| analyze scenes, including its semantic retry | Sonnet | 2 | 6 | 38,912 (4,096/6,144/9,216, twice) |
| refresh config detection | Sonnet | 1 | 3 | 77,824 |
| refresh config QA | GPT-4.1-mini | 1 | 3 | 5,700 |
| discovery location + prop passes | Haiku | 2 | 6 | 98,304 |
| discovery location + prop recall-gap rescue | Haiku | 2 | 6 | 98,304 |
| character candidate adjudication | Haiku | 1 | 3 | 11,400 (2,400/3,600/5,400) |
| character extraction, conservatively all full | Haiku | C | 3C | 38,912C (8,192/12,288/18,432) |
| location adjudication fallback | Haiku | 1 | 3 | 11,400 |
| location extraction | Haiku | L | 3L | 19,456L (4,096/6,144/9,216) |
| prop discovery fallback if discovery props empty | Haiku | 1 | 3 | 49,152 |
| prop candidate adjudication | Haiku | 1 | 3 | 11,400 |
| prop extraction | Haiku | P | 3P | 49,152P |
| entity graph | Haiku | 1 | 3 | 49,152 |
| continuity all scenes | Haiku | 8 | 8 | 19,200 (2 attempts/scene, wrapper retries explicitly zero) |

Conservative conditional totals: physical sends `68 + 3(C+L+P)`. Haiku output
`547,912 + 38,912C + 19,456L + 49,152P`; Sonnet output 194,560; GPT QA output 11,400.
All-location adjudication and prop rediscovery may not coexist with each respective
largest discovery success, so these deliberately overreserve rather than predict.

| Conditional admitted entities | Physical requests | Output-only reserve, current native prices |
|---|---:|---:|
| C=5, L=3, P=5 | 107 | US$8.16964 |
| C=7, L=4, P=25 | 176 | US$13.57124 |

These are **conditional output ceilings, not all-in guaranteed run budgets**.
Input tokens include generated intermediary context and schemas, which must be
rendered and reserved before every physical send. The first script contains the
five named humans plus UNKNOWN VOICE and COMET, and many handled objects. A blanket
five-character/five-prop admission assumption would undercount its possible output.
Prop discovery truncates candidates to 25 before adjudication; characters have no
equivalent source-oracle cap. Location candidates are selected from the scene index,
at most four distinct locations here. Analysis/action-entity outputs can introduce
unsupported character names; discovery source counts cannot bound that branch without
an extra operational admission rule. Denying at such a rule must remain inconclusive.

## Existing boundary for metering and raw retention

Wrap the existing native globals in `cine_forge.ai.llm`: `_anthropic_transport`
(`:652`), `_openai_transport` (`:477`), `_gemini_transport` (`:797`), and
`_xai_transport` (`:511`). `call_llm` resolves these globals on each invocation,
including invocations through modules' imported function aliases. Each transport
makes one urllib HTTP send and contains no SDK retry. This captures inner retries,
scene-analysis semantic retries, recall-gap rescue, prop rediscovery, and continuity
retries without changing prompts, settings, parsing, or retry policy.

Do not pass `transport=` to call_llm for live controls: that bypasses native payload
construction, normalizers, and provider-identity requirements. Do not count only
successful call_llm returns: discarded attempts, swallowed entity failures, analysis
fallbacks, and failed continuity can be absent from aggregate reported cost.

For each physical send, under one shared lock: inspect the *actual* provider payload,
require a priced allowed model and finite output limit; assign a monotonically unique
request id; render/persist the full request body and model before sending; reserve
conservative input plus maximum output against aggregate remaining authorization and
already held reservations. Save native raw response before normalization and parsing;
save sanitized exception information on failure. Settle only from native usage,
including cache writes/read categories, returned model, and request identity. On
timeout or missing usage keep the whole reservation and stop further sends. No request
headers or key-bearing URL may enter evidence. Copy Gemini payload before forwarding
because its native transport pops `_model`.

The existing `benchmarks/scripts/run_haiku55_bible.py:70-90` demonstrates wrapping a
native transport to retain request/raw payloads; its byte-count-plus-overhead reserve
is an operational conservative estimate, not a provider-issued exact token count.
Do not promote that heuristic to a proved all-input upper bound without documenting
its tokenizer/serialization assumptions. Exact future payloads cannot all be rendered
before the first call because they depend on model outputs.

A permanent exhausted/uncertain flag must be checked by every transport wrapper;
ordinary exceptions can be caught by semantic helper fallbacks. After runner return,
the parent must inspect that flag and raw ledger independently of run-state success.
Keep the maintained token caps and native retry topology; a failed admission is
evidence of insufficient remaining budget, not permission to lower baseline limits.

## Owning source pointers

- Recipes: `configs/recipes/recipe-mvp-ingest.yaml`, `recipe-world-building.yaml`.
- Tier-one normalization: `modules/ingest/script_normalize_v1/main.py:93-133`.
- Scene actions/boundaries: `modules/ingest/scene_breakdown_v1/main.py:273-324,675-764`.
- Script-bible limit/model: `modules/ingest/script_bible_v1/main.py:18-20,72-104`.
- Config detection/QA and refresh guard: `modules/ingest/project_config_v1/main.py:99-151,244-298,302-358`.
- Analysis ignores runtime settings: `modules/ingest/scene_analysis_v1/main.py:86-106`; semantic retry `execution.py:144-184`.
- Discovery precedence/recall: `modules/world_building/entity_discovery_v1/main.py:153-229,251-294`.
- Adjudication: `ai/entity_adjudication.py:45-50`.
- Character/locations: corresponding `main.py` extraction defaults and call sites;
  location discovery-backed candidates skip adjudication unless matching fails.
- Prop cap/discovery and uncapped-per-call extraction: `modules/world_building/prop_bible_v1/main.py:68-85,300-319,350-377`.
- Continuity: `modules/world_building/continuity_tracking_v1/prompting.py:16-18,64-105`.
- No outer retry plan: `driver/retry_policy.py:77-112`; execution `driver/module_execution.py:33-91`.
- Native pricing/dispatch/limits: `ai/llm.py:33-74,112-265,576-609`.

Paths in source pointers are relative to `src/cine_forge/` unless explicitly prefixed
with `benchmarks/`, `configs/`, or `docs/`.
