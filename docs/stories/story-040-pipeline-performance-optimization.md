# Story 040 — Pipeline Performance Optimization

**Phase**: Cross-Cutting
**Priority**: High
**Status**: In Progress
**Depends on**: Story 036 (Model Selection — Done), Story 038 (Multi-Provider Transport — To Do)

## Goal

Optimize every stage of the CineForge pipeline for quality, speed, and cost. A 5-page screenplay that's already in Fountain format currently takes **>9 minutes and >$0.70** to process through the ingest pipeline. Target: **<90 seconds and <$0.10** for a clean screenplay, with no quality regression.

This story investigates every LLM call point, identifies waste, implements fixes, and wires up the task-specific model selections from Story 036.

## Context

### The Problem (The Mariner — 5-page screenplay, already formatted)

| Stage | Duration | Cost | LLM Calls |
|-------|----------|------|-----------|
| Ingest | 2s | ~$0 | 0 |
| **Normalize** | **3.8 min** | **$0.25** | **6** (4 norm + 2 QA) |
| **Extract Scenes** | **5.0 min** | **$0.45** | **~28** (13 scenes × enrichment + QA) |
| Project Config | 32s | ~$0.03 | 2 |
| **Total** | **~9.4 min** | **~$0.73** | **~36** |

### Root Causes Identified

1. **Wrong models**: User's default model (Claude Sonnet 4.5) applied to ALL calls — including metadata extraction and QA, which should use cheap models
2. **Wrong strategy**: `edit_list_cleanup` chosen for a ~4500-token screenplay that should be `single_pass`
3. **Wasteful reroutes**: QA disagrees with normalization (false positive), triggers full retry that also fails — 100% wasted compute
4. **No short-circuit**: Already-valid Fountain text still goes through full LLM normalization
5. **Sequential calls**: All LLM calls are serial — no parallelization of independent work
6. **Model defaults hardcoded to expensive models**: `script_normalize` and `scene_extract` default to `gpt-4o` as work_model

### Story 036 Model Selections (to apply)

| Task | Try | Verify | Escalate |
|------|-----|--------|----------|
| Character extraction | Sonnet 4.5 | Haiku 4.5 | Opus 4.6 |
| Location extraction | Gemini 2.5 Pro | Haiku 4.5 | Sonnet 4.5 |
| Prop extraction | Sonnet 4.5 | Haiku 4.5 | Opus 4.6 |
| Relationship discovery | Haiku 4.5 | Code-based | Sonnet 4.5 |
| Config detection | Haiku 4.5 | Code-based | Sonnet 4.5 |
| Passthrough cleanup | Haiku 4.5 | Code-based | Sonnet 4.5 |
| Metadata extraction | Haiku 4.5 | Code-based | Sonnet 4.5 |
| Scene enrichment | Sonnet 4.5 | Haiku 4.5 | Opus 4.6 |
| Boundary validation | Haiku 4.5 | Code-based | Sonnet 4.5 |
| All QA passes | Haiku 4.5 | — | Sonnet 4.5 |

## Acceptance Criteria

- [ ] Every pipeline stage has correct model assignments per Story 036 triads
- [ ] Clean screenplay (already Fountain) processes in <90 seconds end-to-end
- [ ] Cost for clean screenplay <$0.10 end-to-end
- [ ] No quality regression on The Mariner screenplay (artifact quality ≥ current)
- [ ] Strategy selection correctly routes small screenplays to `single_pass`
- [ ] QA passes are productive (reduce false positive reroutes)
- [ ] Unit tests pass (`make test-unit`)
- [ ] End-to-end smoke test with The Mariner validates all changes

## Non-Goals

- Building the multi-provider transport layer (Story 038 — use Anthropic-native models that `call_llm()` already supports)
- Changing the try-validate-escalate architecture
- Parallel execution of LLM calls (architectural change, future story)
- Optimizing world-building stages (characters, locations, props — lower priority since they run less frequently)

---

## Investigation Sections — By LLM Call Point

Each section below covers one LLM call in the pipeline. We'll expand each with:
- Current behavior analysis
- Identified problems
- Proposed fix
- Evidence from The Mariner run

---

### 1. Normalize — Strategy Selection

**File**: `src/cine_forge/ai/long_doc.py:48-72`
**Current behavior**: Chooses between `single_pass`, `edit_list_cleanup`, and `chunked_conversion` based on token count threshold (2000 tokens).

**The Mariner evidence**: 437-line screenplay (~16K chars, ~4500 tokens) → chose `edit_list_cleanup` even though it's a short screenplay. The 2000-token threshold is too low — a standard 5-page screenplay blows past it easily.

**Investigation findings**:
<!-- TODO: Investigate threshold calibration. What's the right token threshold for single_pass? How long can a single LLM call handle reliably? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 2. Normalize — Passthrough Cleanup (Single Pass)

**Files**: `src/cine_forge/modules/ingest/script_normalize_v1/main.py:313-320`
**Model param**: `work_model` → falls through to user's `default_model` via API service
**Current default**: `gpt-4o` (hardcoded in module), but overridden to user's selection (Sonnet 4.5 in this case)
**Story 036 recommendation**: Claude Haiku 4.5

**The Mariner evidence**: Used Claude Sonnet 4.5 for passthrough cleanup. 19s latency, $0.039 for the first normalization call. This is a "fix two typos and capitalize parentheticals" task — Haiku-tier work.

**Investigation findings**:
<!-- TODO: What does the passthrough cleanup actually change? Is the prompt appropriate for the task? Could we skip the LLM entirely for already-valid Fountain? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 3. Normalize — Passthrough Cleanup (Edit List)

**Files**: `src/cine_forge/modules/ingest/script_normalize_v1/main.py:293-311`
**Model param**: Same as #2
**Current default**: Same as #2

**The Mariner evidence**: The `edit_list_cleanup` strategy was used, generating SEARCH/REPLACE patches via LLM. This produced 4 normalization calls instead of 1 because the edit list approach generates patches in chunks.

**Investigation findings**:
<!-- TODO: How many patches were generated? Were they correct? What was the chunking behavior? Is there a simpler approach for already-clean screenplays? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 4. Normalize — Full Conversion

**Files**: `src/cine_forge/modules/ingest/script_normalize_v1/main.py:285-292, long_doc.py:136-181`
**Model param**: `work_model`
**Current default**: `gpt-4o`
**Story 036 recommendation**: Claude Sonnet 4.5 (high complexity task)

**The Mariner evidence**: Not triggered (screenplay was already formatted). This path activates for prose/notes input.

**Investigation findings**:
<!-- TODO: Investigate quality of full conversion with different models. What does the chunking look like for a full-length screenplay (120 pages)? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 5. Normalize — Metadata Extraction

**Files**: `src/cine_forge/modules/ingest/script_normalize_v1/main.py:322-337`
**Model param**: Same `work_model` as normalization (no separate tier)
**Current default**: Inherits from normalization model
**Story 036 recommendation**: Claude Haiku 4.5

**The Mariner evidence**: Used Claude Sonnet 4.5, took 16.2s, cost $0.020. Extracts `source_format`, `strategy`, `inventions`, `assumptions`, `confidence`. This is a simple classification/extraction task on already-processed text.

**Problem**: Uses the same (expensive) model as normalization even though this is a much simpler task. The input is truncated to 4000 chars anyway.

**Investigation findings**:
<!-- TODO: Does this call need to exist at all? Could we infer most of this metadata from the code path taken (we already know the strategy, source format, etc.)? The only AI-valuable fields are inventions, assumptions, and confidence. -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 6. Normalize — QA with Repairs

**Files**: `src/cine_forge/ai/qa.py:61-94`, `main.py:150-180`
**Model param**: `verify_model`
**Current default**: `gpt-4o-mini` (hardcoded), but overridden to user's model via API service
**Story 036 recommendation**: Claude Haiku 4.5

**The Mariner evidence**: Two QA calls, each ~20s and ~$0.07. First QA call found 3 "errors" (dialogue capitalization) and 3 "warnings" (parenthetical spacing). This triggered a reroute. Second QA call found the same issues. Result: `passed: false`, artifact stamped `needs_review`. **100% wasted compute on the reroute.**

**Problems identified**:
1. QA prompt sends the FULL original input + FULL output + FULL prompt (16K+ input tokens for a 5-page script) — massively over-contextualized
2. QA flagged capitalization of `(QUIETLY)` parenthetical content in dialogue as an error, but the normalization prompt explicitly asked for this
3. Reroute triggered on QA errors that the normalization can't fix (contradicting instructions)
4. QA sees 16K input tokens even though the normalization only changed ~50 characters

**Investigation findings**:
<!-- TODO: What % of QA passes across real runs are productive (catch real errors vs false positives)? Is the QA prompt aligned with the normalization prompt? Should QA be diff-aware (only evaluate what changed)? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 7. Normalize — Reroute Logic

**Files**: `src/cine_forge/modules/ingest/script_normalize_v1/main.py:167-179`
**Not an LLM call itself, but orchestrates re-execution of calls 2-6.**

**The Mariner evidence**: `reroutes: 1`. The entire normalization + metadata + QA cycle ran twice. Second attempt made 2 more normalization calls + 1 more QA call, all using Sonnet 4.5. Total cost of reroute: ~$0.12 and ~66 seconds. Result: QA still failed. Artifact accepted as `needs_review` anyway.

**Problems**:
1. Reroute doubles cost/time but QA issues often can't be resolved by re-running the same prompt with feedback
2. No escalation to a stronger model on reroute — just reruns with the same model plus feedback text
3. No pre-check to see if the QA issues are actionable (e.g., "capitalization" issues on parentheticals are the normalization following its own instructions)

**Investigation findings**:
<!-- TODO: What % of reroutes actually improve the output? Should we differentiate between actionable vs non-actionable QA issues? Should reroute escalate the model? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 8. Scene Extract — Boundary Validation

**Files**: `src/cine_forge/modules/ingest/scene_extract_v1/main.py:199-207, 656-682`
**Model param**: `work_model`
**Current default**: `gpt-4o`
**Story 036 recommendation**: Claude Haiku 4.5
**Trigger**: Only when `boundary_uncertain=True` (no headings found)

**The Mariner evidence**: Not triggered (The Mariner has clear `INT./EXT.` headings). This is a fallback for unstructured input.

**Investigation findings**:
<!-- TODO: When does this trigger in practice? Is the 300-token max_tokens appropriate? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 9. Scene Extract — Scene Enrichment

**Files**: `src/cine_forge/modules/ingest/scene_extract_v1/main.py:209-222, 685-712`
**Model param**: `work_model`
**Current default**: `gpt-4o`
**Story 036 recommendation**: Claude Sonnet 4.5

**The Mariner evidence**: Triggered for most/all 13 scenes (whenever `unresolved_fields` is non-empty). Each call used the user's default model (Sonnet 4.5). With 13 scenes, this is likely ~13 sequential LLM calls.

**Problems**:
1. The deterministic parser may leave fields as UNKNOWN/UNSPECIFIED that are actually extractable from the heading (e.g., `time_of_day` from "CONTINUOUS")
2. Using Sonnet for simple field extraction from a scene heading + text is overpowered
3. Sequential per-scene calls — no batching or parallelization

**Investigation findings**:
<!-- TODO: What unresolved fields triggered enrichment for The Mariner scenes? Could better deterministic parsing eliminate most enrichment calls? What's the actual enrichment prompt per scene? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 10. Scene Extract — Scene QA

**Files**: `src/cine_forge/modules/ingest/scene_extract_v1/main.py:233-254, 787-807`
**Model param**: `verify_model`
**Current default**: `gpt-4o-mini`
**Story 036 recommendation**: Claude Haiku 4.5

**The Mariner evidence**: From `scene_index`: `scenes_need_review: 12`, `scenes_passed_qa: 1`. Only 1 of 13 scenes passed QA. The scene_index also shows garbage in characters_present (e.g., "CLEAN", "DIMLY LIT", "LUXURIOUS", "RUG", "RUSTY WEIGHTS", "WEEDS" listed as characters). This suggests either the enrichment or QA is producing poor results.

**Problems**:
1. 12/13 scenes failed QA — this is a red flag that either the QA bar is too high or the extraction quality is genuinely poor
2. Non-character entities leaking into `characters_present` (action-line words being parsed as character cues)
3. QA runs per-scene sequentially — 13 calls in series

**Investigation findings**:
<!-- TODO: What QA issues are flagged for each scene? Are they real quality issues or false positives? Is the character extraction heuristic producing garbage that the LLM then has to clean up? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 11. Scene Extract — Reroute Logic

**Files**: `src/cine_forge/modules/ingest/scene_extract_v1/main.py:243-254`
**Not an LLM call — orchestrates retry of calls 8-10 per scene.**

**The Mariner evidence**: Unknown how many per-scene reroutes occurred. Given 12/13 QA failures, there may have been up to 24 rerouted enrichment+QA cycles (12 scenes × 2 retries).

**Investigation findings**:
<!-- TODO: Check if scene_extract stores reroute count in the scene artifacts. Calculate worst-case call count for The Mariner. -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 12. Project Config — Config Detection

**Files**: `src/cine_forge/modules/ingest/project_config_v1/main.py:100-104, 206-225`
**Model param**: `model` (no work/verify/escalate split)
**Current default**: `gpt-4o`
**Story 036 recommendation**: Claude Haiku 4.5

**The Mariner evidence**: Took ~32 seconds total (detection + QA). Single pass, no reroute. Cost not individually tracked but likely ~$0.03.

**Problems**:
1. Uses `gpt-4o` by default for a task that Haiku handles well (per Story 036 benchmarks)
2. No `work_model`/`verify_model`/`escalate_model` parameter split — uses single `model` param

**Investigation findings**:
<!-- TODO: What did the config detection produce for The Mariner? Was it accurate? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 13. Project Config — Detection QA

**Files**: `src/cine_forge/modules/ingest/project_config_v1/main.py:105-111, 228-268`
**Model param**: `qa_model`
**Current default**: `gpt-4o-mini`
**Story 036 recommendation**: Code-based (no LLM needed)

**Investigation findings**:
<!-- TODO: What does the config QA actually check? Could this be replaced with deterministic validation (field presence, value ranges)? -->

**Proposed fix**:
<!-- TODO: Fill in after investigation -->

---

### 14. Character Bible — Character Extraction

**Files**: `src/cine_forge/modules/world_building/character_bible_v1/main.py:117-127, 283-305`
**Model param**: `work_model`
**Current default**: `gpt-4o-mini`
**Story 036 recommendation**: Claude Sonnet 4.5

**Note**: Character bible runs in the world-building recipe (not the ingest pipeline analyzed above). Lower priority for this story but included for completeness.

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. Record any issues found during testing. -->

---

### 15. Character Bible — Character QA

**Files**: `src/cine_forge/modules/world_building/character_bible_v1/main.py:130-140, 308-322`
**Model param**: `verify_model`
**Current default**: `gpt-4o-mini`
**Story 036 recommendation**: Claude Haiku 4.5

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. -->

---

### 16. Character Bible — Re-extraction (Escalation)

**Files**: `src/cine_forge/modules/world_building/character_bible_v1/main.py:143-154`
**Model param**: `escalate_model`
**Current default**: `gpt-4o`
**Story 036 recommendation**: Claude Opus 4.6

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. -->

---

### 17. Location Bible — Location Extraction

**Files**: `src/cine_forge/modules/world_building/location_bible_v1/main.py:54-60, 192-214`
**Model param**: `work_model`
**Current default**: `gpt-4o-mini`
**Story 036 recommendation**: Gemini 2.5 Pro

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. Requires Story 038 transport for Gemini. -->

---

### 18. Location Bible — Location QA + Re-extraction

**Files**: `main.py:66-89`
**Model params**: `verify_model` / `escalate_model`
**Story 036 recommendation**: Haiku 4.5 / Sonnet 4.5

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. -->

---

### 19. Prop Bible — Prop Discovery

**Files**: `src/cine_forge/modules/world_building/prop_bible_v1/main.py:30, 158-170`
**Model param**: `work_model`
**Current default**: `gpt-4o-mini`
**Story 036 recommendation**: Claude Haiku 4.5

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. -->

---

### 20. Prop Bible — Prop Extraction + QA + Re-extraction

**Files**: `main.py:43-79`
**Model params**: `work_model` / `verify_model` / `escalate_model`
**Story 036 recommendation**: Sonnet 4.5 / Haiku 4.5 / Opus 4.6

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. -->

---

### 21. Entity Graph — Relationship Discovery

**Files**: `src/cine_forge/modules/world_building/entity_graph_v1/main.py:77-82, 188-221`
**Model param**: `work_model`
**Current default**: `gpt-4o-mini`
**Story 036 recommendation**: Claude Haiku 4.5

**Investigation findings**:
<!-- TODO: Not in scope for initial optimization. -->

---

## Tasks

### Phase 1 — Model Wiring (Immediate wins)

- [ ] Update model defaults in `script_normalize_v1/main.py` — `work_model` → Haiku for passthrough, Sonnet for full conversion; `verify_model` → Haiku; `escalate_model` → Sonnet
- [ ] Update model defaults in `scene_extract_v1/main.py` — `work_model` → Haiku for boundary/enrichment; `verify_model` → Haiku; `escalate_model` → Sonnet
- [ ] Update model defaults in `project_config_v1/main.py` — `model` → Haiku; `qa_model` → Haiku
- [ ] Update API service model resolution to not override module defaults with user's `default_model` for every call
- [ ] Verify `call_llm()` Anthropic transport works for Haiku and Sonnet models

### Phase 2 — Strategy and Logic Fixes

- [ ] Fix `long_doc.py` strategy threshold — raise `short_doc_threshold` so 5-page screenplays use `single_pass`
- [ ] Add Fountain validation short-circuit: if input passes Fountain lint AND structure validation, skip normalization LLM call entirely (just run metadata extraction)
- [ ] Fix metadata extraction to derive `source_format`, `strategy` from code path (only use LLM for inventions/assumptions/confidence)
- [ ] Fix QA prompt alignment — ensure QA evaluates against the actual normalization instructions (not contradicting them)
- [ ] Reduce QA input context — send diff or summary instead of full original+output for passthrough cleanup
- [ ] Add reroute pre-check: classify QA issues as actionable vs non-actionable before triggering retry

### Phase 3 — Scene Extract Optimization

- [ ] Investigate and fix character parsing — why are action-line words ("CLEAN", "DIMLY LIT", "RUG") appearing in `characters_present`?
- [ ] Improve deterministic parsing to resolve more fields without LLM enrichment
- [ ] Investigate QA failure rate — why do 12/13 scenes fail QA?
- [ ] Consider batching scene enrichment (send multiple scenes in one LLM call)

### Phase 4 — Validation

- [ ] End-to-end smoke test: The Mariner through full ingest pipeline with new settings
- [ ] Compare output quality: diff artifacts before/after optimization
- [ ] Measure timing: confirm <90 second target for clean screenplay
- [ ] Measure cost: confirm <$0.10 target
- [ ] Unit tests pass

## Work Log

### 20260216-1000 — Story Created: Investigation Phase

**Action**: Created story from investigation of The Mariner run (`output/the-mariner-2`). Cataloged all 21 LLM call points across 7 modules with exact file locations, model parameters, retry logic, and strategy selection.

**Evidence from The Mariner run**:
- Normalize: 6 LLM calls, 49K input tokens, $0.25, 3.8 minutes (Claude Sonnet 4.5)
- Scene extract: ~28 LLM calls, 82K input tokens, $0.45, 5 minutes (Claude Sonnet 4.5)
- Project config: 2 LLM calls, ~$0.03, 32 seconds
- Total: ~36 LLM calls, $0.73, 9.4 minutes
- QA false positive rate: very high (reroute produced zero improvement, 12/13 scene QA failures)
- Strategy misselection: `edit_list_cleanup` for a document that should be `single_pass`

**Key artifacts examined**:
- `output/the-mariner-2/artifacts/canonical_script/project/v1.json` — full cost telemetry, QA results
- `output/the-mariner-2/artifacts/scene_index/project/v1.json` — QA pass/fail per scene, character extraction quality
- `output/the-mariner-2/chat.jsonl` — timestamps for each stage

**Next**: Begin investigation of each call point, starting with normalize strategy selection and passthrough cleanup (highest impact).
