# Scout 010 — OpenAI Prompt Guidance (GPT-5.4)

**Source:** https://developers.openai.com/api/docs/guides/prompt-guidance/
**Scouted:** 2026-03-07
**Scope:** Full page — prompt engineering patterns for GPT-5.4, assessed for CineForge pipeline modules
**Previous:** None
**Status:** Complete

## Findings

1. **Output Contract pattern** — MEDIUM value
   What: Explicit constraints on verbosity, structure, format in system prompts. "Return exactly the sections requested. If a format is required, output only that format."
   Us: Our modules use Pydantic `response_schema` for structured output, which handles format enforcement at the API level. Some modules have ad-hoc "return only JSON" instructions in prompts.
   Recommendation: **Skip** — Pydantic structured output already enforces this more reliably than prompt-level instructions. No action needed.

2. **Completeness Contract pattern** — HIGH value
   What: "Keep an internal checklist of deliverables. For lists/batches: determine expected scope, track processed items, confirm coverage before finalizing." Prevents models from silently dropping items.
   Us: Our entity discovery and scene analysis modules process full screenplays. We've seen models drop entities or scenes silently (noted in AGENTS.md: "LLM resolution degrades from synthetic to real data"). No explicit completeness instructions in prompts.
   Recommendation: **Adopt inline** — Add completeness contract language to entity discovery, character bible, and scene analysis prompts. Low effort, high potential impact on recall.

3. **Verification Loop pattern** — MEDIUM value
   What: Mandatory self-check before finalizing: Does output satisfy every requirement? Are claims backed by context? Does output match schema?
   Us: We have QA models (`qa_model` param) that do post-hoc verification as a separate LLM call. This is a different approach — asking the *same* model to self-verify before responding.
   Recommendation: **Skip for now** — Our QA-model pattern is stronger (independent verification > self-verification). Could revisit if we find QA models missing things the work model could catch.

4. **Empty Result Recovery pattern** — MEDIUM value
   What: When lookups return sparse results, try alternate query wording, broader filters, or alternate sources.
   Us: Our `call_llm` has retry logic with token escalation on truncation, but no semantic retry (e.g., "you found 3 characters but the script mentions 12 — look again").
   Recommendation: **Create story** — A recall-verification loop (compare discovered count vs expected count, re-prompt on gaps) would be valuable for entity discovery. Too large for inline.

5. **Research Mode (Multi-Pass)** — HIGH value
   What: Plan sub-questions -> retrieve each -> synthesize with citations. Structured decomposition for complex analysis.
   Us: Our scene analysis and continuity tracking modules do single-pass extraction. The continuity module especially could benefit from a plan-then-extract pattern (plan what to track per scene, then extract).
   Recommendation: **Skip** — Interesting but would require significant module architecture changes. Our current single-pass + QA pattern works well enough. File in inbox for future consideration.

6. **Reasoning Effort Calibration** — HIGH value
   What: Treat reasoning effort as a tunable knob. Strengthen prompts (completeness contract, verification loop, tool persistence) BEFORE increasing reasoning/model size. "Prompt-first approach before reasoning escalation."
   Us: We already do value-optimized model selection (AGENTS.md module defaults table). But we don't systematically try prompt improvements before escalating to a more expensive model.
   Recommendation: **Adopt as principle** — Add to AGENTS.md eval methodology: "Before escalating to a more expensive model, try adding completeness contracts and verification instructions to the prompt first." Low effort, aligns with our cost-optimization culture.

7. **Action Safety Frame (Pre/Post-flight)** — LOW value
   What: Summarize intended action before executing, confirm outcome after.
   Us: Not applicable — our pipeline modules don't take destructive actions. They produce immutable artifacts.
   Recommendation: **Skip** — Immutable artifact pattern already handles this concern.

8. **Missing Context Gating** — MEDIUM value
   What: "If required context is missing, do NOT guess. Prefer lookup when retrievable; ask clarifying questions only when not retrievable."
   Us: Our modules sometimes hallucinate when screenplay data is ambiguous (e.g., inventing character backstories not in the text). Some prompts say "only use information from the screenplay" but it's inconsistent.
   Recommendation: **Adopt inline** — Audit module prompts for grounding language. Add "Base all claims strictly on the provided screenplay text. If information is not present, say so explicitly rather than inferring." Lightweight sweep.

9. **Personality/Writing Controls separation** — LOW value
   What: Separate persistent persona from per-response writing constraints (channel, register, formatting, length).
   Us: Our role system (`src/cine_forge/roles/`) already separates persona (role definition) from style (style packs) from task (module prompts). Well ahead of this pattern.
   Recommendation: **Skip** — Already implemented more thoroughly via roles + style packs.

10. **Flat List Formatting (No Nesting)** — LOW value
    What: "Never use nested bullets. Keep lists flat."
    Us: Not relevant to our structured JSON output pipeline. Could apply to creative direction text output.
    Recommendation: **Skip** — Our outputs are structured JSON, not prose lists.

11. **Prompt-First Before Reasoning Escalation** — HIGH value (same as #6, reinforced)
    What: Explicit precedence order: (1) completeness contract, (2) verification loop, (3) tool persistence, (4) initiative nudge, (5) THEN increase reasoning_effort. "Add structure to the prompt before throwing compute at it."
    Us: Our `/improve-eval` skill currently jumps to trying different models. Should try prompt-level improvements first.
    Recommendation: **Adopt as methodology update** — Update improve-eval skill and eval improvement docs to mandate prompt-level improvements as step 1 before model escalation.

## Summary

| # | Finding | Value | Recommendation |
|---|---------|-------|----------------|
| 1 | Output Contract | MEDIUM | Skip (Pydantic handles) |
| 2 | Completeness Contract | HIGH | Adopt inline |
| 3 | Verification Loop | MEDIUM | Skip (QA model is better) |
| 4 | Empty Result Recovery | MEDIUM | Create story |
| 5 | Research Mode (Multi-Pass) | HIGH | Skip (inbox for later) |
| 6 | Reasoning Effort Calibration | HIGH | Adopt as principle |
| 7 | Action Safety Frame | LOW | Skip |
| 8 | Missing Context Gating | MEDIUM | Adopt inline |
| 9 | Personality/Writing Controls | LOW | Skip (already have roles) |
| 10 | Flat List Formatting | LOW | Skip |
| 11 | Prompt-First Methodology | HIGH | Adopt as methodology |

## Approved

- [x] 2. Completeness Contract — Added to character_bible, location_bible, scene_analysis prompts
  - Evidence: `character_bible_v1/main.py:792` "verify that every field...has been considered"
  - Evidence: `location_bible_v1/main.py:521` "verify that every scene set at this location has been considered"
  - Evidence: `scene_analysis_v1/main.py:352` "MUST return an entry for every scene...verify output count matches"
- [x] 6+11. Prompt-First Before Model Escalation — Added to AGENTS.md General Principles
  - Evidence: `AGENTS.md:47` new bullet "Prompt-First Before Model Escalation"
- [x] 8. Missing Context Gating / Grounding — Added to character_bible, location_bible, scene_analysis, prop_bible prompts
  - Evidence: `character_bible_v1/main.py:778` "Base every field strictly on evidence"
  - Evidence: `character_bible_v1/main.py:816` "Do not invent backstory"
  - Evidence: `location_bible_v1/main.py:517` "Base every field strictly on evidence"
  - Evidence: `scene_analysis_v1/main.py:351` "Do not infer...from general film knowledge"
  - Evidence: `prop_bible_v1/main.py:520` "Base every field strictly on evidence"
- [x] 4. Empty Result Recovery — Deferred to Story 124
  - Evidence: `docs/stories/story-124-recall-verification-loop.md` (Draft)
- [x] 5. Research Mode — Added to inbox for future consideration
  - Evidence: `docs/inbox.md` Workflow section — "Multi-pass research mode"

## Skipped / Rejected

- 1. Output Contract — Pydantic structured output already enforces this at API level
- 3. Verification Loop — Our QA-model pattern (independent verifier) is stronger than self-verification
- 5. Research Mode — Interesting but too large; would require module architecture changes. Add to inbox.
- 7. Action Safety Frame — Immutable artifact pattern eliminates the concern
- 9. Personality/Writing Controls — Already implemented via roles + style packs
- 10. Flat List Formatting — Outputs are structured JSON, not prose
