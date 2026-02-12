# Story 004: Script Normalization Module

**Status**: Done
**Created**: 2026-02-11
**Spec Refs**: 4.2 (Script Normalization), 4.3 (Canonical Script Rule), 2.4 (AI-Driven), 2.6 (Explanation Mandatory), 2.7 (Cost Transparency), 2.8 (QA Tier 1 + Role-Level)
**Depends On**: Story 002 (pipeline foundation), Story 003 (story ingestion — provides `raw_input` artifact)

---

## HANDOFF (Read First)

This story is mid-flight and was actively updated from a deep-research synthesis in this conversation. The next model should continue from here without re-planning from scratch.

### Context from this conversation
- User commissioned multi-model deep research and consolidated report at `docs/research/story-004-long-doc/FINAL-research-report.md`.
- Decision: keep Story 004 hybrid architecture, harden it with parser-backed screenplay validation + deterministic checks, and defer breakdown/continuity/scheduling systems to Story 005+.
- User explicitly requested incremental execution due to quota constraints ("one thing at a time", short slices).
- User is now highly aligned with Fountain-first workflow and wants high ROI screenplay-tool integrations only for Story 004.

### What is already implemented
- Shared AI infrastructure:
  - `src/cine_forge/ai/llm.py`: structured output + strict schema compatibility, retry handling, cost metadata, `finish_reason`, max token controls.
  - `src/cine_forge/ai/long_doc.py`: strategy selection, scene-aware chunk helpers, overlap, running metadata utilities.
  - `src/cine_forge/ai/patching.py`: SEARCH/REPLACE parsing + layered apply (exact, whitespace-normalized, fuzzy).
  - `src/cine_forge/ai/fountain_validate.py`: deterministic screenplay normalization + lint checks.
  - `src/cine_forge/ai/qa.py`: QA check + QA repair-plan schema/function.
  - `src/cine_forge/ai/fountain_parser.py`: optional parser-backed validation (`fountain-tools`) with safe heuristic fallback.
- Normalization module hardening:
  - `src/cine_forge/modules/ingest/script_normalize_v1/main.py` now uses parser signal in screenplay-path routing, deterministic post-LLM validation, QA repair flow, runtime guardrails (`max_tokens`, cost ceiling, truncation fail-loud behavior).
  - `src/cine_forge/modules/ingest/script_normalize_v1/module.yaml` has new guardrail parameters.
- Story + docs updates:
  - Added "Post-Synthesis Hardening" and "High ROI Open-Source Integrations" acceptance sections here.
  - Added research artifacts/prompts under `docs/research/story-004-long-doc/`.
- Dependency:
  - `pyproject.toml` now includes `fountain-tools`.

### Tests currently in place
- Unit tests added/expanded:
  - `tests/unit/test_ai_llm.py`
  - `tests/unit/test_ai_qa.py`
  - `tests/unit/test_ai_long_doc.py`
  - `tests/unit/test_ai_patching.py`
  - `tests/unit/test_fountain_validate.py`
  - `tests/unit/test_fountain_parser.py`
  - `tests/unit/test_script_normalize_module.py`
- Integration:
  - `tests/integration/test_script_normalize_integration.py`
- Last verified commands in this session:
  - `make lint` (pass)
  - `make test-unit` (pass)
  - `make test-integration` (pass earlier in session; latest short slice re-ran lint+unit)

### Remaining Story 004 work (most important next)
1. Complete optional FDX interoperability requirement in Story 004:
   - detect valid FDX input and map to canonical Fountain text pre-normalization.
   - add export helper for FDX/PDF handoff (`screenplain` or equivalent).
2. Add parser-backed integration fixtures/tests:
   - valid screenplay
   - malformed screenplay
   - FDX sample
3. Keep Story 004 scope tight:
   - do NOT add Story 005+ systems (breakdown extraction, continuity graph intelligence, scheduling/budget pipelines) in this story.

### Recommended next single increment
- Implement FDX detect + conversion utility with one focused unit test and one integration assertion; then check off only the corresponding Story 004 checklist items.

### Notes on repository state
- Working tree contains other ongoing modifications from earlier story work; do not revert unrelated changes.
- Continue small, bounded commits-of-work (not git commits unless user asks), with checklist updates and evidence in Work Log after each increment.

## Goal

Build the first AI-powered module in the pipeline. Script normalization takes the `raw_input` artifact from Story 003 and, if it is not already a screenplay, converts it into proper screenplay format. If it is already a screenplay, the module validates/cleans it and passes it through. The output — `canonical_script_v1` — is a properly formatted **screenplay text document**, not a structured JSON breakdown. The structured per-scene decomposition happens in Story 005 (Scene Extraction).

The canonical script is the human-readable screenplay that the user can read, print, and hand to an actor. It is also the immutable canon that every downstream artifact references (spec 4.3).

This is the system's first real AI call, so it also proves out:
- The AI call interface (prompt construction → LLM call → response parsing).
- Cost tracking for AI calls (spec 2.7).
- Explanation metadata (spec 2.6 — what, why, tradeoffs, confidence).
- Artifact lineage (canonical_script depends on raw_input).
- Structural invalidation (if raw_input is later re-ingested, canonical_script becomes `stale`).
- **QA verification** (spec 2.8) — a second AI call that reviews the first AI's work.
- **Long document handling** — strategies for editing/generating screenplays that may be 100+ pages.

## Acceptance Criteria

### Normalization Logic
- [x] Module reads the `raw_input` artifact (content + classification from Story 003).
- [x] If classification is `screenplay` with high confidence (≥ 0.8):
  - [x] AI validates the formatting, corrects minor issues (inconsistent cues, missing scene numbers, etc.), and outputs a clean canonical script.
  - [x] No inventions are needed — this is a cleaning/validation pass.
  - [x] Assumptions list is empty or minimal ("fixed inconsistent character name casing", etc.).
- [x] If classification is NOT `screenplay` (prose, hybrid, notes, unknown, or screenplay with low confidence):
  - [x] AI converts the input into screenplay format.
  - [x] Conversion must preserve the author's intent (spec 4.2).
  - [x] AI must explicitly label all inventions — anything added that was not in the original (e.g., "added scene heading INT. KITCHEN - NIGHT based on context clues", "invented character name WAITRESS for unnamed speaking role").
  - [x] AI emits confidence per section/scene (how sure it is that the conversion captures the original intent).
  - [x] AI emits assumptions — things it had to decide without clear guidance from the source (e.g., "assumed two characters are in the same room based on dialogue flow").
- [x] The output is a complete, properly formatted **screenplay as text** (standard screenplay format — scene headings, action lines, character cues, dialogue, transitions). This is a text document, not a structured JSON breakdown.

### Canonical Script Artifact
- [x] Output artifact type: `canonical_script`.
- [x] Once saved, the canonical script is immutable (spec 4.3). Edits produce a new version (`canonical_script_v2`), never mutation.
- [x] All downstream artifacts reference specific script spans (scene numbers, line ranges) within the canonical script.
  - Ownership moved to Story 005 implementation scope (Scene Extraction source-span outputs); tracked in `docs/stories/story-005-scene-extraction.md` under Tasks as a Story 004 dependency closure item.
- [x] Artifact lineage: `canonical_script_v1` → derived from `raw_input_v1`.

### Explanation and Transparency (Spec 2.6)
- [x] The normalization result includes structured metadata alongside the screenplay text:
  - [x] `inventions`: list of creative decisions the AI made that were not in the original.
  - [x] `assumptions`: list of interpretive choices with rationale.
  - [x] `confidence`: overall confidence score (0.0–1.0) for the normalization.
  - [x] `rationale`: high-level explanation of the normalization strategy.
- [x] This metadata is stored alongside the artifact (part of the audit metadata envelope from Story 002).

### Cost Tracking (Spec 2.7)
- [x] Every AI call made during normalization records:
  - [x] Model used (e.g., `gpt-4o`, `claude-sonnet-4-20250514`).
  - [x] Token counts (input, output).
  - [x] Estimated cost (based on per-token pricing).
  - [x] Latency.
- [x] Cost data is attached to the artifact's audit metadata.
- [x] Total module cost is computed and available in the run summary.

### QA Verification (Spec 2.8)
- [x] Introduce a shared QA check utility (`src/cine_forge/ai/qa.py`):
  - [x] `qa_check(original_input, prompt_used, output_produced, model) → QAResult`.
  - [x] The QA model receives the same context the producing model had (original input + prompt) plus the output, and evaluates: did the output faithfully fulfill the prompt's requirements?
  - [x] `QAResult` includes: `passed: bool`, `confidence: float`, `issues: list[QAIssue]`, `summary: str`.
  - [x] Each `QAIssue` includes: `severity` (error, warning, note), `description`, `location` (where in the output).
  - [x] This is a shared utility — all future AI modules use it. Built here, reused everywhere.
- [x] For normalization specifically, the QA check evaluates:
  - [x] **Intent preservation**: does the screenplay capture the original's meaning? (Especially critical for prose → screenplay conversion.)
  - [x] **Invention reasonableness**: are the labeled inventions justified, or did the AI add unnecessary content?
  - [x] **Format correctness**: is the output actually proper screenplay format?
  - [x] **Completeness**: is anything from the original missing in the screenplay?
- [x] QA behavior on failure:
  - [x] If QA fails with errors: retry normalization with QA feedback injected into the prompt (up to `max_retries`).
  - [x] If QA fails after retries: save the artifact but flag it as `needs_review` with the QA issues attached. The pipeline can continue, but the user/Director is alerted.
  - [x] If QA passes with warnings: save the artifact as `valid`, attach warnings to audit metadata.
- [x] QA cost is tracked separately from the normalization cost (both are in the artifact's cost metadata).
- [x] QA can be disabled per-run via a parameter (`skip_qa: true`) for cost-sensitive or iterative workflows.

### Schema
- [x] `CanonicalScript` Pydantic schema:
  ```python
  class Invention(BaseModel):
      """Something the AI added that was not in the original."""
      description: str
      location: str                      # Approximate location in the script (e.g., "near line 45, scene INT. KITCHEN")
      rationale: str                     # Why this was needed

  class Assumption(BaseModel):
      """An interpretive choice the AI made."""
      description: str
      rationale: str
      alternatives_considered: list[str]  # What else it could have done

  class NormalizationMetadata(BaseModel):
      """Transparency metadata for the normalization process."""
      source_format: str                  # What was detected in raw_input
      strategy: str                       # "passthrough_cleanup" or "full_conversion"
      inventions: list[Invention]
      assumptions: list[Assumption]
      overall_confidence: float
      rationale: str

  class CanonicalScript(BaseModel):
      """The canonical screenplay — a properly formatted screenplay text document."""
      title: str
      script_text: str                    # The complete screenplay as formatted text
      line_count: int
      scene_count: int                    # Approximate count from scene headings (INT./EXT.)
      normalization: NormalizationMetadata
  ```
- [x] `QAResult` Pydantic schema (shared — in `src/cine_forge/schemas/qa.py`):
  ```python
  class QAIssue(BaseModel):
      severity: Literal["error", "warning", "note"]
      description: str
      location: str                       # Where in the output (approximate)

  class QAResult(BaseModel):
      passed: bool                        # True if no errors (warnings OK)
      confidence: float                   # QA model's confidence in its assessment
      issues: list[QAIssue]
      summary: str                        # One-paragraph assessment
  ```
- [x] The `script_text` field contains the full screenplay in standard format — readable, printable, ready for a human.
- [x] The structured per-scene breakdown (SceneBlock, ScriptElement, etc.) is deferred to Story 005 (Scene Extraction), which parses this text into structured JSON.
- [x] Schema registered in the schema registry.
- [x] Structural validation (QA tier 1) passes on all outputs.

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/ingest/script_normalize_v1/`
- [x] `module.yaml`:
  ```yaml
  module_id: script_normalize_v1
  stage: ingest
  description: "Normalizes raw input to canonical screenplay format using AI."
  input_schemas: ["raw_input"]
  output_schemas: ["canonical_script"]
  parameters:
    model:
      type: string
      required: false
      default: "gpt-4o"
      description: "LLM model to use for normalization."
    max_retries:
      type: integer
      required: false
      default: 2
      description: "Max retries on parse failure or low-confidence output."
  ```
- [x] `main.py` implementing the standard module contract.

### AI Call Interface
- [x] Introduce a thin AI call wrapper (`src/cine_forge/ai/`):
  - [x] `call_llm(prompt, model, response_schema=None) → (response_text_or_parsed, call_metadata)`.
  - [x] When `response_schema` is provided, uses structured output (JSON mode) to get Pydantic-parseable responses. When omitted, returns raw text.
  - [x] Records call metadata: model, tokens, cost, latency, request_id.
  - [x] Handles retries on transient failures (rate limits, timeouts).
  - [x] This is a shared utility — all future AI modules will use it.
- [x] For MVP, support at least one LLM provider (OpenAI recommended — best structured output support).
- [x] API key configuration via environment variable (`OPENAI_API_KEY` or similar).
- [x] The wrapper does NOT contain creative logic — it's infrastructure. The prompt is constructed by the module.
- [x] Normalization uses the wrapper in two ways: one call for the screenplay text (raw text output), and the metadata (inventions, assumptions) either extracted from the same call or a follow-up structured call. Implementation can decide — both approaches work.

### Long Document Strategy

**Prerequisite: Deep Research task (must complete before implementation).**

Screenplays can be 100+ pages (~25,000–40,000 tokens). The module must handle long documents without drift or context limit issues. Before building our approach, we need to research the current state of the art.

#### Deep Research: Large Document AI Editing (Feb 2026)

- [x] Research task: survey the current SOTA for AI-driven large document editing. Produce a short decision document (`docs/research/long-doc-editing.md`) covering:
  - [x] **API-level support**: Do current LLM APIs (OpenAI, Anthropic, Google) offer built-in features for long document editing? (e.g., extended output modes, streaming generation, document diffing APIs, edit/patch modes, "fill in the middle" capabilities.)
  - [x] **Libraries and frameworks**: Are there established open-source libraries for chunked AI document editing? (e.g., LangChain document transformers, LlamaIndex, custom tooling.) What patterns do they use?
  - [x] **Chunking strategies**: What are proven approaches for splitting, processing, and reassembling long documents while maintaining coherence? (Overlapping context windows, hierarchical summarization, etc.)
  - [x] **Edit-list vs. regeneration**: Is the "ask for a list of edits and apply programmatically" pattern well-supported by current models? How reliable is it at scale?
  - [x] **Screenplay-specific tooling**: Are there any AI tools specifically for screenplay editing/conversion that we could integrate or learn from? (Fountain parsers, screenwriting AI tools, etc.)
  - [x] **Token economics**: What are the practical context window limits and output token limits for current models? What's the cost profile for processing a 100-page screenplay?
  - [x] **Recommendation**: Based on findings, recommend our approach — build from scratch, adopt a library, use a specific API feature, or some combination.

#### Implementation Requirements (details TBD by research)

The research will inform the final design. The following are the **problems to solve** regardless of approach:

- [x] Screenplays that are already properly formatted should NOT be fully regenerated — changes should be surgical (edits, patches, corrections only).
- [x] Prose-to-screenplay conversion of long documents must maintain narrative continuity across the full document without drift.
- [x] Short documents (under ~5,000 tokens) should use single-pass — no unnecessary complexity.
- [x] The solution should be a shared utility (`src/cine_forge/ai/long_doc.py` or equivalent) reusable by any future module that processes long documents.
- [x] Strategy selection (single-pass vs. chunked vs. edit-list) should be automatic based on input characteristics.

### Post-Synthesis Hardening (Final Research Alignment)
- [x] Add screenplay-path routing based on parseability, not classification confidence alone.
- [x] Add scene-native chunking for long prose/notes conversion with 300-500 token overlap.
- [x] Carry a compressed running metadata document across chunk conversions to preserve continuity.
- [x] Replace naive patch application with SEARCH/REPLACE block application and layered matching:
  - [x] exact
  - [x] whitespace-normalized
  - [x] fuzzy fallback (`SequenceMatcher` threshold)
- [x] Add deterministic post-LLM screenplay normalization/validation utility:
  - [x] normalize heading/cue casing
  - [x] enforce screenplay spacing rules
  - [x] detect malformed/orphaned blocks via lint checks
- [x] Extend QA flow to support targeted repair operations (patch-first fixes before declaring `needs_review`).
- [x] Add operational guardrails:
  - [x] explicit token/output caps per call
  - [x] truncation (`finish_reason`) detection and fail-loud handling
  - [x] retry budgets and bounded reroute behavior
  - [x] per-script cost ceiling with fail-safe `needs_review`

### High ROI Open-Source Integrations (Story 004 Scope Only)
- [x] Integrate a production-grade Fountain parser/validator (`fountain-tools` or equivalent) as a hard gate for screenplay-path detection and post-normalization structural validation.
- [x] Add deterministic Fountain lint checks driven by parser output (not regex-only), including:
  - [x] malformed scene headings
  - [x] orphaned character cues/dialogue anomalies
  - [x] inconsistent character cue casing
- [x] Add optional FDX interoperability path for normalization input/output:
  - [x] detect valid FDX XML input and map to canonical Fountain text before normalization
  - [x] provide export helper for normalized canonical script to FDX/PDF (`screenplain` or equivalent) for downstream production handoff
- [x] Add integration tests using parser-backed validation fixtures (valid screenplay, malformed screenplay, FDX sample) to ensure normalization emits parser-valid canonical screenplay.
- [x] Keep all other screenplay ecosystem integrations (breakdown systems, continuity intelligence, scheduling/budget outputs) explicitly out of Story 004 and deferred to Story 005+.

### Testing
- [x] Unit tests for the AI call wrapper (mock LLM responses):
  - [x] Successful call → parsed response + metadata.
  - [x] Retry on transient failure → eventual success.
  - [x] Max retries exceeded → graceful failure with error details.
  - [x] Cost calculation from token counts.
- [x] Unit tests for normalization prompt construction:
  - [x] Screenplay input → cleanup prompt.
  - [x] Prose input → full conversion prompt.
  - [x] Notes input → full conversion prompt (with extra guidance for sparse input).
- [x] Integration tests (with mocked AI responses):
  - [x] Screenplay in → cleaned screenplay text out (minimal changes, no inventions).
  - [x] Prose in → converted screenplay text out (inventions labeled, assumptions documented).
  - [x] Output validates against `CanonicalScript` schema (script_text + normalization metadata).
  - [x] Artifact saved with lineage (depends on `raw_input_v1`).
  - [x] Cost metadata present in artifact.
- [x] Unit tests for QA check utility (mocked):
  - [x] QA pass → artifact saved as valid.
  - [x] QA fail with errors → retry with feedback → eventual pass.
  - [x] QA fail after max retries → artifact saved with `needs_review` flag and issues attached.
  - [x] QA pass with warnings → artifact saved as valid, warnings in audit metadata.
  - [x] QA disabled (`skip_qa`) → no QA call made, artifact saved directly.
- [x] Unit tests for long document handling (test specifics TBD by research):
  - [x] Surgical edit strategy: given a screenplay + set of changes → correct result, unchanged text preserved.
  - [x] Long conversion: given a long prose input → correctly processed without drift.
  - [x] Short document: single-pass, no unnecessary chunking triggered.
- [x] (Optional) Live integration test with real LLM call against a short sample — gated behind an env var (`CINE_FORGE_LIVE_TESTS=1`) so CI doesn't burn money.

## Design Notes

### Prompt Strategy

The normalization prompt should be structured in sections:

1. **System context**: "You are a professional script supervisor normalizing a creative work into standard screenplay format."
2. **Input format**: Tell the AI what format was detected and at what confidence.
3. **The content**: The raw input text.
4. **Output requirements**: Two parts — (a) the screenplay text in standard format, and (b) structured JSON for the normalization metadata (inventions, assumptions, confidence). The screenplay itself is plain text, not JSON.
5. **Quality bar**: "Preserve the author's voice. When in doubt, stay faithful to the original rather than inventing."

For prose/notes conversion, the prompt needs additional guidance:
- "Scene boundaries may need to be inferred from location/time changes."
- "Character names should be extracted from context; if unnamed, invent a name and label it as an invention."
- "Dialogue in prose should be extracted into proper dialogue format."

### Output is Text, Not Structure

The canonical script is a **text document** — a properly formatted screenplay you could print and hand to someone. The AI's job here is to get the text right: proper scene headings, character cues in caps, dialogue formatted correctly, transitions placed properly, etc.

The structured breakdown (which characters are in which scene, what props are mentioned, what the scene boundaries are in JSON) is Story 005's job. This separation is intentional:
- Story 004 focuses on **"is this a proper screenplay?"** — a text transformation task.
- Story 005 focuses on **"what's in this screenplay?"** — a structural analysis task.

Inventions and assumptions are still tracked in structured metadata alongside the text, because the user needs to review what the AI added or assumed before the pipeline proceeds.

### Long Documents: The Core Problem

A 100-page screenplay is ~25,000–40,000 tokens. Asking an AI to *regenerate* that entire document in one shot will produce drift — the model loses coherence over very long outputs, the style shifts, details get dropped. This is a well-known problem in AI-assisted writing.

**The deep research task (see acceptance criteria above) will determine our specific approach.** Some candidate strategies to investigate:

- **Edit-list / patch mode**: AI reads the full document and returns a list of specific corrections applied programmatically. Cheap, faithful, auditable — but only works for the "cleanup" case, not full conversion.
- **Chunk-and-reassemble**: Split at natural boundaries, process each chunk with surrounding context, reassemble. Works for conversion but requires careful continuity management at the seams.
- **API-level features**: Some providers may offer extended output modes, streaming generation, or document-level operations that solve this at the API layer.
- **Existing libraries**: There may be mature open-source tooling that already handles this well.

For short documents (under ~5K tokens), single-pass is always fine. The strategy only matters for long inputs.

### QA as a Second Opinion

Every AI-generated artifact gets a QA check: a separate AI call that reviews the work. The QA model receives the same context the producing model had — the original input, the prompt, and the output — and asks: "Did this output faithfully achieve what the prompt asked for?"

This catches:
- **Hallucination**: the AI invented content not justified by the input.
- **Omission**: the AI dropped something from the original.
- **Format errors**: the output isn't proper screenplay format.
- **Drift**: in long documents, the style or content shifted partway through.

On failure, the module retries with the QA feedback injected into the prompt ("The QA check found these issues: ... Please fix them."). After `max_retries`, the artifact is saved but flagged `needs_review`.

The QA check is itself an AI call, so it has its own cost. For cost-sensitive workflows, it can be disabled per-run.

### Why Not Use a Role Here?

This module uses an AI call but does not (yet) invoke a formal "Role" from the role system (Story 014). That's intentional:
- The role system doesn't exist yet in the MVP.
- Normalization is a relatively mechanical AI task — it doesn't need a creative persona.
- When the role system is built, this module can optionally invoke the "Script Supervisor" role for the normalization. The module contract stays the same; only the prompt changes.

### Handling Poor Input

Some inputs will be genuinely hard to normalize (a napkin sketch, a stream-of-consciousness outline, etc.). The module should:
- Never refuse. Always produce a best-effort canonical script.
- Use low confidence scores to signal uncertainty.
- Use inventions and assumptions liberally to document what it had to make up.
- The driver/user can then decide whether to accept, re-run with a stronger model, or manually edit the raw input first.

### Future Enhancements (Not This Story)
- Role-based normalization (Script Supervisor persona).
- Multi-pass normalization (rough conversion → refinement → polish).
- Interactive normalization (AI proposes, human confirms section by section).
- Support for screenplay variants (BBC format, European format, etc.).
- Fountain output format as an alternative text representation.
- Source span mapping (line-level mapping from canonical script back to raw input).

## Tasks

- [x] **RESEARCH FIRST**: Complete deep research on SOTA large document AI editing → produce `docs/research/long-doc-editing.md` with findings and recommendation.
- [x] Create AI call wrapper: `src/cine_forge/ai/llm.py` — `call_llm()` with structured output, retries, cost tracking.
- [x] Create AI config: model selection, API key loading, retry policy.
- [x] Create QA check utility: `src/cine_forge/ai/qa.py` — `qa_check()` with configurable criteria per module.
- [x] Define `QAResult`, `QAIssue` schemas in `src/cine_forge/schemas/qa.py`.
- [x] Create long document utilities (approach TBD by research): `src/cine_forge/ai/long_doc.py` or integration with identified library/API.
- [x] Define `CanonicalScript`, `Invention`, `Assumption`, `NormalizationMetadata` schemas.
- [x] Register all schemas in the schema registry.
- [x] Create module directory: `src/cine_forge/modules/ingest/script_normalize_v1/`.
- [x] Write `module.yaml` manifest.
- [x] Implement prompt construction (two variants: cleanup via edit-list vs. full conversion via chunked transform).
- [x] Implement `main.py`: load raw_input → detect strategy → select long-doc approach → build prompt(s) → call LLM → extract screenplay text + normalization metadata → QA check → validate schema → save artifact with lineage + cost metadata.
- [x] Write unit tests for AI call wrapper (mocked).
- [x] Write unit tests for QA check utility (mocked).
- [x] Write unit tests for long document utilities (edit-list application, chunked transform, reassembly).
- [x] Write unit tests for prompt construction.
- [x] Write integration tests for normalization flow (mocked AI responses, including QA pass/fail scenarios).
- [x] Add sample AI responses to test fixtures (realistic mocked outputs for screenplay and prose inputs, plus QA responses).
- [x] (Optional) Write live integration test gated behind `CINE_FORGE_LIVE_TESTS`.
- [x] Verify end-to-end: recipe with ingest + normalize → two artifacts in store, lineage correct, cost recorded, QA result attached.
- [x] Implement post-synthesis hardening set from `docs/research/story-004-long-doc/FINAL-research-report.md` (scene chunking, running metadata, robust search/replace patching, deterministic Fountain linting, and guardrails).
- [x] Integrate high cost/benefit screenplay tooling for Story 004 only (Fountain parser hard-gate + parser-backed linting + optional FDX interop), with tests and explicit defer of Story 005+ concerns.
- [x] Update AGENTS.md with any lessons learned.

## Notes

- This is the first AI-calling module. Three shared utilities are built here and reused everywhere: the **AI call wrapper** (`llm.py`), the **QA check** (`qa.py`), and the **long document editor** (`long_doc.py`). Get them right — they're foundational infrastructure.
- Mock-first testing is essential. Real LLM calls are slow and expensive. The integration tests should use realistic mocked responses that exercise the full parsing/validation path, including QA pass and fail scenarios.
- The canonical script text is one of the most important artifacts in the system — nearly everything downstream depends on it. Make sure the screenplay formatting is clean and consistent, because Story 005 will parse it into structured data.
- Source span mapping (canonical script lines → raw input lines) is deferred. For MVP, the inventions and assumptions list is sufficient for traceability. Line-level mapping can be added later when it's needed for change propagation.
- The QA utility built here is intentionally simple: one AI call, pass/fail with issues. The role-based review gates (Canon Guardian, etc.) come later in Story 014+. This QA is the "automated second opinion" tier from spec 2.8.

## Work Log

- Timestamp: `20260212-1044`
  - Action performed: Implemented Story 004 foundations end-to-end: added `CanonicalScript` and QA schemas, created shared AI utilities (`llm.py`, `qa.py`, `long_doc.py`), added `script_normalize_v1` module + manifest, registered new schemas in the driver, and added ingest+normalize recipe wiring.
  - Result: `Success`
  - Evidence: files `src/cine_forge/schemas/canonical_script.py`, `src/cine_forge/schemas/qa.py`, `src/cine_forge/ai/llm.py`, `src/cine_forge/ai/qa.py`, `src/cine_forge/ai/long_doc.py`, `src/cine_forge/modules/ingest/script_normalize_v1/*`, `configs/recipes/recipe-ingest-normalize.yaml`, `docs/research/long-doc-editing.md`.
  - Next step: Validate with lint/unit/integration and confirm artifact metadata contents from integration run.

- Timestamp: `20260212-1044`
  - Action performed: Added Story 004 test coverage for LLM wrapper retries/costing, QA utility, long-document strategy helpers, normalization prompts, QA retry/failure/warning behavior, and driver integration for ingest+normalize with mocked model mode.
  - Result: `Success`
  - Evidence: files `tests/unit/test_ai_llm.py`, `tests/unit/test_ai_qa.py`, `tests/unit/test_ai_long_doc.py`, `tests/unit/test_script_normalize_module.py`, `tests/integration/test_script_normalize_integration.py`; commands `make lint`, `make test-unit`, `make test-integration` all passing.
  - Next step: Decide whether to mark Story 004 fully done now or keep in-progress until downstream span-reference acceptance item is formally deferred.

- Timestamp: `20260212-1355`
  - Action performed: Implemented post-synthesis architecture hardening from the combined final research report: scene-aware chunking and running continuity metadata, robust SEARCH/REPLACE patch parsing/application with fuzzy fallback, deterministic Fountain normalization/lint checks, QA repair-plan support, parseability-based screenplay routing, and runtime guardrails (`max_tokens`, truncation fail-loud, reroute/cost annotations).
  - Result: `Success`
  - Evidence: files `src/cine_forge/ai/long_doc.py`, `src/cine_forge/ai/patching.py`, `src/cine_forge/ai/fountain_validate.py`, `src/cine_forge/ai/qa.py`, `src/cine_forge/ai/llm.py`, `src/cine_forge/modules/ingest/script_normalize_v1/main.py`, `src/cine_forge/modules/ingest/script_normalize_v1/module.yaml`; tests `tests/unit/test_ai_long_doc.py`, `tests/unit/test_ai_patching.py`, `tests/unit/test_fountain_validate.py`, `tests/unit/test_ai_qa.py`, `tests/unit/test_ai_llm.py`, `tests/unit/test_script_normalize_module.py`; commands `make lint`, `make test-unit`, `make test-integration`.
  - Next step: Add a live-gated normalization test (`CINE_FORGE_LIVE_TESTS`) and evaluate whether to move Story 004 status to `Done` with explicit Story 005 span-reference deferral.

- Timestamp: `20260212-1403`
  - Action performed: Added optional `fountain-tools` integration hooks and parser-backed screenplay hard-gate wiring for Story 004: new parser abstraction (`src/cine_forge/ai/fountain_parser.py`), screenplay path routing now consumes parser signal, and post-normalization parser validation issues are attached to deterministic lint annotations; added focused unit coverage.
  - Result: `Success`
  - Evidence: files `pyproject.toml`, `src/cine_forge/ai/fountain_parser.py`, `src/cine_forge/ai/__init__.py`, `src/cine_forge/modules/ingest/script_normalize_v1/main.py`, tests `tests/unit/test_fountain_parser.py`, `tests/unit/test_script_normalize_module.py`; commands `make lint`, `make test-unit`.
  - Next step: Implement optional FDX interoperability path and parser-backed integration fixtures (valid, malformed, FDX sample).

- Timestamp: `20260212-1428`
  - Action performed: Implemented optional FDX interoperability for Story 004: added FDX detection + XML paragraph mapping into canonical Fountain pre-normalization, added screenplay export helpers for FDX/PDF handoff status, wired export annotations into `script_normalize_v1`, and added parser-backed fixture coverage for valid screenplay, malformed screenplay, and FDX sample cases.
  - Result: `Success`
  - Evidence: files `src/cine_forge/ai/fdx.py`, `src/cine_forge/ai/__init__.py`, `src/cine_forge/modules/ingest/script_normalize_v1/main.py`, `src/cine_forge/modules/ingest/script_normalize_v1/module.yaml`, `tests/unit/test_fdx.py`, `tests/unit/test_script_normalize_module.py`, `tests/integration/test_script_normalize_integration.py`, `tests/fixtures/normalize_inputs/*`.
  - Next step: Run lint + unit + integration suites and then decide whether to mark Story 004 as done or keep in-progress for optional live test only.

- Timestamp: `20260212-1443`
  - Action performed: Added a live-gated normalization integration test (`CINE_FORGE_LIVE_TESTS=1`) that executes `script_normalize_v1` against a short prose sample with a real model and validates parser-parseable screenplay output while keeping QA disabled to limit spend.
  - Result: `Success`
  - Evidence: file `tests/integration/test_script_normalize_integration.py` (`test_normalization_live_llm_short_sample`), env gates `CINE_FORGE_LIVE_TESTS`, `OPENAI_API_KEY`, optional model override `CINE_FORGE_LIVE_MODEL`.
  - Next step: Decide whether to run the live test now (requires API key/cost) and then close Story 004 remaining deferred acceptance items tied to Story 005.

- Timestamp: `20260212-1518`
  - Action performed: Closed practical FDX interoperability gaps by adding native `.fdx` ingest support (`story_ingest_v1` + schema format literal), adding an ingest fixture/integration path for `.fdx`, and replacing PDF export stub behavior with a real `screenplain` CLI execution path (with graceful fallback when unavailable).
  - Result: `Success`
  - Evidence: files `src/cine_forge/modules/ingest/story_ingest_v1/main.py`, `src/cine_forge/modules/ingest/story_ingest_v1/module.yaml`, `src/cine_forge/schemas/models.py`, `src/cine_forge/ai/fdx.py`, `tests/unit/test_story_ingest_module.py`, `tests/integration/test_story_ingest_integration.py`, `tests/unit/test_fdx.py`, `tests/fixtures/ingest_inputs/sample_script.fdx`; commands `make lint`, `make test-unit`, `make test-integration`.
  - Next step: Move downstream span-reference ownership into Story 005 with explicit linkage and close Story 004.

- Timestamp: `20260212-1532`
  - Action performed: Formally closed Story 004 by transferring downstream span-reference implementation ownership to Story 005 (scene extraction outputs), and linking the dependency explicitly across story docs.
  - Result: `Success`
  - Evidence: files `docs/stories/story-004-script-normalization.md`, `docs/stories/story-005-scene-extraction.md`, `docs/stories.md`.
  - Next step: Implement Story 005 scene source-span extraction and line-range propagation to satisfy the moved dependency in execution.
