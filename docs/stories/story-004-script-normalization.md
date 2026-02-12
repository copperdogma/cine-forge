# Story 004: Script Normalization Module

**Status**: To Do
**Created**: 2026-02-11
**Spec Refs**: 4.2 (Script Normalization), 4.3 (Canonical Script Rule), 2.4 (AI-Driven), 2.6 (Explanation Mandatory), 2.7 (Cost Transparency), 2.8 (QA Tier 1 + Role-Level)
**Depends On**: Story 002 (pipeline foundation), Story 003 (story ingestion — provides `raw_input` artifact)

---

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
- [ ] Module reads the `raw_input` artifact (content + classification from Story 003).
- [ ] If classification is `screenplay` with high confidence (≥ 0.8):
  - [ ] AI validates the formatting, corrects minor issues (inconsistent cues, missing scene numbers, etc.), and outputs a clean canonical script.
  - [ ] No inventions are needed — this is a cleaning/validation pass.
  - [ ] Assumptions list is empty or minimal ("fixed inconsistent character name casing", etc.).
- [ ] If classification is NOT `screenplay` (prose, hybrid, notes, unknown, or screenplay with low confidence):
  - [ ] AI converts the input into screenplay format.
  - [ ] Conversion must preserve the author's intent (spec 4.2).
  - [ ] AI must explicitly label all inventions — anything added that was not in the original (e.g., "added scene heading INT. KITCHEN - NIGHT based on context clues", "invented character name WAITRESS for unnamed speaking role").
  - [ ] AI emits confidence per section/scene (how sure it is that the conversion captures the original intent).
  - [ ] AI emits assumptions — things it had to decide without clear guidance from the source (e.g., "assumed two characters are in the same room based on dialogue flow").
- [ ] The output is a complete, properly formatted **screenplay as text** (standard screenplay format — scene headings, action lines, character cues, dialogue, transitions). This is a text document, not a structured JSON breakdown.

### Canonical Script Artifact
- [ ] Output artifact type: `canonical_script`.
- [ ] Once saved, the canonical script is immutable (spec 4.3). Edits produce a new version (`canonical_script_v2`), never mutation.
- [ ] All downstream artifacts reference specific script spans (scene numbers, line ranges) within the canonical script.
- [ ] Artifact lineage: `canonical_script_v1` → derived from `raw_input_v1`.

### Explanation and Transparency (Spec 2.6)
- [ ] The normalization result includes structured metadata alongside the screenplay text:
  - [ ] `inventions`: list of creative decisions the AI made that were not in the original.
  - [ ] `assumptions`: list of interpretive choices with rationale.
  - [ ] `confidence`: overall confidence score (0.0–1.0) for the normalization.
  - [ ] `rationale`: high-level explanation of the normalization strategy.
- [ ] This metadata is stored alongside the artifact (part of the audit metadata envelope from Story 002).

### Cost Tracking (Spec 2.7)
- [ ] Every AI call made during normalization records:
  - [ ] Model used (e.g., `gpt-4o`, `claude-sonnet-4-20250514`).
  - [ ] Token counts (input, output).
  - [ ] Estimated cost (based on per-token pricing).
  - [ ] Latency.
- [ ] Cost data is attached to the artifact's audit metadata.
- [ ] Total module cost is computed and available in the run summary.

### QA Verification (Spec 2.8)
- [ ] Introduce a shared QA check utility (`src/cine_forge/ai/qa.py`):
  - [ ] `qa_check(original_input, prompt_used, output_produced, model) → QAResult`.
  - [ ] The QA model receives the same context the producing model had (original input + prompt) plus the output, and evaluates: did the output faithfully fulfill the prompt's requirements?
  - [ ] `QAResult` includes: `passed: bool`, `confidence: float`, `issues: list[QAIssue]`, `summary: str`.
  - [ ] Each `QAIssue` includes: `severity` (error, warning, note), `description`, `location` (where in the output).
  - [ ] This is a shared utility — all future AI modules use it. Built here, reused everywhere.
- [ ] For normalization specifically, the QA check evaluates:
  - [ ] **Intent preservation**: does the screenplay capture the original's meaning? (Especially critical for prose → screenplay conversion.)
  - [ ] **Invention reasonableness**: are the labeled inventions justified, or did the AI add unnecessary content?
  - [ ] **Format correctness**: is the output actually proper screenplay format?
  - [ ] **Completeness**: is anything from the original missing in the screenplay?
- [ ] QA behavior on failure:
  - [ ] If QA fails with errors: retry normalization with QA feedback injected into the prompt (up to `max_retries`).
  - [ ] If QA fails after retries: save the artifact but flag it as `needs_review` with the QA issues attached. The pipeline can continue, but the user/Director is alerted.
  - [ ] If QA passes with warnings: save the artifact as `valid`, attach warnings to audit metadata.
- [ ] QA cost is tracked separately from the normalization cost (both are in the artifact's cost metadata).
- [ ] QA can be disabled per-run via a parameter (`skip_qa: true`) for cost-sensitive or iterative workflows.

### Schema
- [ ] `CanonicalScript` Pydantic schema:
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
- [ ] `QAResult` Pydantic schema (shared — in `src/cine_forge/schemas/qa.py`):
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
- [ ] The `script_text` field contains the full screenplay in standard format — readable, printable, ready for a human.
- [ ] The structured per-scene breakdown (SceneBlock, ScriptElement, etc.) is deferred to Story 005 (Scene Extraction), which parses this text into structured JSON.
- [ ] Schema registered in the schema registry.
- [ ] Structural validation (QA tier 1) passes on all outputs.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/ingest/script_normalize_v1/`
- [ ] `module.yaml`:
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
- [ ] `main.py` implementing the standard module contract.

### AI Call Interface
- [ ] Introduce a thin AI call wrapper (`src/cine_forge/ai/`):
  - [ ] `call_llm(prompt, model, response_schema=None) → (response_text_or_parsed, call_metadata)`.
  - [ ] When `response_schema` is provided, uses structured output (JSON mode) to get Pydantic-parseable responses. When omitted, returns raw text.
  - [ ] Records call metadata: model, tokens, cost, latency, request_id.
  - [ ] Handles retries on transient failures (rate limits, timeouts).
  - [ ] This is a shared utility — all future AI modules will use it.
- [ ] For MVP, support at least one LLM provider (OpenAI recommended — best structured output support).
- [ ] API key configuration via environment variable (`OPENAI_API_KEY` or similar).
- [ ] The wrapper does NOT contain creative logic — it's infrastructure. The prompt is constructed by the module.
- [ ] Normalization uses the wrapper in two ways: one call for the screenplay text (raw text output), and the metadata (inventions, assumptions) either extracted from the same call or a follow-up structured call. Implementation can decide — both approaches work.

### Long Document Strategy

**Prerequisite: Deep Research task (must complete before implementation).**

Screenplays can be 100+ pages (~25,000–40,000 tokens). The module must handle long documents without drift or context limit issues. Before building our approach, we need to research the current state of the art.

#### Deep Research: Large Document AI Editing (Feb 2026)

- [ ] Research task: survey the current SOTA for AI-driven large document editing. Produce a short decision document (`docs/research/long-doc-editing.md`) covering:
  - [ ] **API-level support**: Do current LLM APIs (OpenAI, Anthropic, Google) offer built-in features for long document editing? (e.g., extended output modes, streaming generation, document diffing APIs, edit/patch modes, "fill in the middle" capabilities.)
  - [ ] **Libraries and frameworks**: Are there established open-source libraries for chunked AI document editing? (e.g., LangChain document transformers, LlamaIndex, custom tooling.) What patterns do they use?
  - [ ] **Chunking strategies**: What are proven approaches for splitting, processing, and reassembling long documents while maintaining coherence? (Overlapping context windows, hierarchical summarization, etc.)
  - [ ] **Edit-list vs. regeneration**: Is the "ask for a list of edits and apply programmatically" pattern well-supported by current models? How reliable is it at scale?
  - [ ] **Screenplay-specific tooling**: Are there any AI tools specifically for screenplay editing/conversion that we could integrate or learn from? (Fountain parsers, screenwriting AI tools, etc.)
  - [ ] **Token economics**: What are the practical context window limits and output token limits for current models? What's the cost profile for processing a 100-page screenplay?
  - [ ] **Recommendation**: Based on findings, recommend our approach — build from scratch, adopt a library, use a specific API feature, or some combination.

#### Implementation Requirements (details TBD by research)

The research will inform the final design. The following are the **problems to solve** regardless of approach:

- [ ] Screenplays that are already properly formatted should NOT be fully regenerated — changes should be surgical (edits, patches, corrections only).
- [ ] Prose-to-screenplay conversion of long documents must maintain narrative continuity across the full document without drift.
- [ ] Short documents (under ~5,000 tokens) should use single-pass — no unnecessary complexity.
- [ ] The solution should be a shared utility (`src/cine_forge/ai/long_doc.py` or equivalent) reusable by any future module that processes long documents.
- [ ] Strategy selection (single-pass vs. chunked vs. edit-list) should be automatic based on input characteristics.

### Testing
- [ ] Unit tests for the AI call wrapper (mock LLM responses):
  - [ ] Successful call → parsed response + metadata.
  - [ ] Retry on transient failure → eventual success.
  - [ ] Max retries exceeded → graceful failure with error details.
  - [ ] Cost calculation from token counts.
- [ ] Unit tests for normalization prompt construction:
  - [ ] Screenplay input → cleanup prompt.
  - [ ] Prose input → full conversion prompt.
  - [ ] Notes input → full conversion prompt (with extra guidance for sparse input).
- [ ] Integration tests (with mocked AI responses):
  - [ ] Screenplay in → cleaned screenplay text out (minimal changes, no inventions).
  - [ ] Prose in → converted screenplay text out (inventions labeled, assumptions documented).
  - [ ] Output validates against `CanonicalScript` schema (script_text + normalization metadata).
  - [ ] Artifact saved with lineage (depends on `raw_input_v1`).
  - [ ] Cost metadata present in artifact.
- [ ] Unit tests for QA check utility (mocked):
  - [ ] QA pass → artifact saved as valid.
  - [ ] QA fail with errors → retry with feedback → eventual pass.
  - [ ] QA fail after max retries → artifact saved with `needs_review` flag and issues attached.
  - [ ] QA pass with warnings → artifact saved as valid, warnings in audit metadata.
  - [ ] QA disabled (`skip_qa`) → no QA call made, artifact saved directly.
- [ ] Unit tests for long document handling (test specifics TBD by research):
  - [ ] Surgical edit strategy: given a screenplay + set of changes → correct result, unchanged text preserved.
  - [ ] Long conversion: given a long prose input → correctly processed without drift.
  - [ ] Short document: single-pass, no unnecessary chunking triggered.
- [ ] (Optional) Live integration test with real LLM call against a short sample — gated behind an env var (`CINE_FORGE_LIVE_TESTS=1`) so CI doesn't burn money.

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

- [ ] **RESEARCH FIRST**: Complete deep research on SOTA large document AI editing → produce `docs/research/long-doc-editing.md` with findings and recommendation.
- [ ] Create AI call wrapper: `src/cine_forge/ai/llm.py` — `call_llm()` with structured output, retries, cost tracking.
- [ ] Create AI config: model selection, API key loading, retry policy.
- [ ] Create QA check utility: `src/cine_forge/ai/qa.py` — `qa_check()` with configurable criteria per module.
- [ ] Define `QAResult`, `QAIssue` schemas in `src/cine_forge/schemas/qa.py`.
- [ ] Create long document utilities (approach TBD by research): `src/cine_forge/ai/long_doc.py` or integration with identified library/API.
- [ ] Define `CanonicalScript`, `Invention`, `Assumption`, `NormalizationMetadata` schemas.
- [ ] Register all schemas in the schema registry.
- [ ] Create module directory: `src/cine_forge/modules/ingest/script_normalize_v1/`.
- [ ] Write `module.yaml` manifest.
- [ ] Implement prompt construction (two variants: cleanup via edit-list vs. full conversion via chunked transform).
- [ ] Implement `main.py`: load raw_input → detect strategy → select long-doc approach → build prompt(s) → call LLM → extract screenplay text + normalization metadata → QA check → validate schema → save artifact with lineage + cost metadata.
- [ ] Write unit tests for AI call wrapper (mocked).
- [ ] Write unit tests for QA check utility (mocked).
- [ ] Write unit tests for long document utilities (edit-list application, chunked transform, reassembly).
- [ ] Write unit tests for prompt construction.
- [ ] Write integration tests for normalization flow (mocked AI responses, including QA pass/fail scenarios).
- [ ] Add sample AI responses to test fixtures (realistic mocked outputs for screenplay and prose inputs, plus QA responses).
- [ ] (Optional) Write live integration test gated behind `CINE_FORGE_LIVE_TESTS`.
- [ ] Verify end-to-end: recipe with ingest + normalize → two artifacts in store, lineage correct, cost recorded, QA result attached.
- [ ] Update AGENTS.md with any lessons learned.

## Notes

- This is the first AI-calling module. Three shared utilities are built here and reused everywhere: the **AI call wrapper** (`llm.py`), the **QA check** (`qa.py`), and the **long document editor** (`long_doc.py`). Get them right — they're foundational infrastructure.
- Mock-first testing is essential. Real LLM calls are slow and expensive. The integration tests should use realistic mocked responses that exercise the full parsing/validation path, including QA pass and fail scenarios.
- The canonical script text is one of the most important artifacts in the system — nearly everything downstream depends on it. Make sure the screenplay formatting is clean and consistent, because Story 005 will parse it into structured data.
- Source span mapping (canonical script lines → raw input lines) is deferred. For MVP, the inventions and assumptions list is sufficient for traceability. Line-level mapping can be added later when it's needed for change propagation.
- The QA utility built here is intentionally simple: one AI call, pass/fail with issues. The role-based review gates (Canon Guardian, etc.) come later in Story 014+. This QA is the "automated second opinion" tier from spec 2.8.

## Work Log

(entries will be added as work progresses)
