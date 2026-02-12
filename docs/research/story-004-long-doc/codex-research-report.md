# Long Document AI Editing Research (Codex Report, Feb 2026)

## Scope

This note summarizes practical options for handling screenplay-scale document normalization (25k-40k tokens, sometimes higher) with modern LLM APIs while preserving fidelity and avoiding long-output drift.

## Findings

### API-Level Support

- OpenAI and Anthropic both support large-context prompting and structured JSON outputs, which helps with metadata extraction and edit-list outputs.
- Streaming output is widely available, but it does not solve coherence drift by itself; it only improves UX and timeout resilience.
- Native "document diff" APIs are still limited. The common production pattern remains: ask for structured edits and apply them in code.
- Tool/function calling is useful for controlled outputs (edit operations, QA issues), but screenplay text itself should remain plain text output.

### Libraries and Framework Patterns

- LangChain/LlamaIndex provide chunking orchestration and map-reduce style transforms, but teams still implement domain-specific reassembly and consistency checks.
- Most reliable implementations keep "planning" and "generation" separate:
  1) identify transformations/edits per segment,
  2) apply deterministically in code,
  3) run QA pass for omissions/hallucinations.
- For screenplay tasks, generic document frameworks help with chunk scheduling, but not with screenplay-format correctness rules; module-level logic is still required.

### Chunking Strategies

- Best baseline: semantic chunking at section boundaries plus overlap windows to preserve continuity.
- For screenplay cleanup, "edit list over original text" is preferred over full regeneration to avoid unnecessary rewrites.
- For prose-to-screenplay conversion, chunked conversion is acceptable if each chunk carries continuity context (previous chunk summary + cast/location memory).
- Add deterministic seam checks after reassembly (duplicate headings, dropped transitions, abrupt character renames).

### Edit-List vs Regeneration

- Edit-list is strong for already-screenplay inputs and high-confidence cleanup workflows.
- Full regeneration remains necessary for prose/notes conversion, but should be chunked for long inputs.
- Reliability improves when the model returns strict JSON edit operations (`replace`, `insert_after`, `delete`) with location hints and rationale.

### Screenplay-Specific Tooling

- Fountain parsers are useful for heading/cue validation and scene counting.
- Existing AI screenplay tools are product-oriented and not easily embeddable as infrastructure dependencies.
- Practical approach: use lightweight screenplay heuristics + LLM normalization, then parse structured scenes in Story 005.

### Token Economics (Practical Guidance)

- Large-context calls are feasible but expensive; per-stage multi-call strategies are easier to budget and retry.
- A 100-page script can require multiple calls (normalization + metadata + QA), so cost tracking must aggregate sub-call costs.
- QA can be optional (`skip_qa`) for iteration loops, but should default to enabled for quality-sensitive runs.

## Recommendation

Use a hybrid strategy:

1. **Short docs (<~5k tokens):** single-pass normalization + structured metadata extraction + QA.
2. **Long, already-screenplay docs (high confidence):** edit-list cleanup, apply edits programmatically.
3. **Long prose/notes docs:** chunked conversion with overlap, deterministic reassembly, then QA.
4. **Always** collect per-call token/cost metadata and attach QA results to artifact audit metadata.

This gives low operational complexity now, keeps behavior auditable, and provides reusable utilities for future AI modules.

---

Canonical source copy: `docs/research/long-doc-editing.md`.
