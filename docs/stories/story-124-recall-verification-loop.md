# Story 124 — Recall Verification Loop for Entity Discovery

**Priority**: Medium
**Status**: Draft
**Spec Refs**: None (entity discovery quality improvement)
**Depends On**: None
**Scout Ref**: Scout 010 (`docs/scout/scout-010-openai-prompt-guidance.md`) — "Empty Result Recovery" pattern

## Goal

Add a post-extraction verification pass to entity discovery that compares discovered entities against expected counts and screenplay evidence, re-prompting the model when recall gaps are detected.

## Context

Scout 010 (OpenAI GPT-5.4 Prompt Guidance) identified "Empty Result Recovery" as a valuable pattern. Our entity discovery module processes full screenplays in chunks but has no mechanism to detect when it silently drops entities. AGENTS.md notes: "LLM resolution degrades from synthetic to real data" — small test fixtures pass but real screenplays with 40-80+ entities show recall gaps.

The current entity discovery pipeline (`src/cine_forge/modules/world_building/entity_discovery_v1/main.py`) runs a single extraction pass and trusts the result. There is no cross-referencing against other available signals (dialogue speakers from scene extraction, INT/EXT headings for locations, etc.) to detect missing entities.

## Rough Notes

These are draft-level notes. Full Acceptance Criteria and detailed Tasks will be written when this story is promoted to Pending.

- After entity discovery completes, run a lightweight verification pass
- Compare discovered count against heuristic expectations (e.g., character count vs dialogue-speaker count from scene extraction)
- If significant gap detected (>20% missing), re-prompt with specific guidance: "The screenplay mentions these speakers who are not in your list: X, Y, Z"
- Consider cross-referencing scene_index character lists against discovered characters
- Apply to characters first (highest signal), then locations, then props
- Must not increase cost by more than ~20% on average (verification pass should be cheap model)
- Track recall improvement in eval registry

## Approach Evaluation

Candidates — to be distinguished by eval during `build-story`:

- **Candidate A: Post-hoc verification LLM call** — A second LLM pass comparing entity list against raw speaker/heading lists extracted from the screenplay. Flexible, can catch semantic aliases. More expensive.
- **Candidate B: Rule-based gap detection** — Regex-extract speaker names from dialogue blocks, diff against discovered characters. Extract INT/EXT headings, diff against discovered locations. Zero LLM cost for detection, but brittle on aliases and non-standard formatting.
- **Candidate C: Hybrid** — Rule-based detection (cheap, fast) to identify specific gaps, then LLM re-prompt only when gaps are found. Best cost profile on average — zero overhead when discovery is complete, targeted re-prompt when it isn't.

**Eval to distinguish**: Run entity discovery on 3+ real screenplays, measure recall with and without each verification approach. Compare cost delta and recall improvement.

## Links

- Scout 010: `docs/scout/scout-010-openai-prompt-guidance.md`
- Entity discovery module: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py`
- Entity discovery eval: `benchmarks/tasks/entity-discovery.yaml`
- Entity discovery golden: `benchmarks/golden/the-mariner-entity-discovery.json`
- Eval registry: `docs/evals/registry.yaml`

## Work Log

*(Entries added during implementation)*
