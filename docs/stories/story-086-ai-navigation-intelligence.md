# Story 086 — AI Navigation Intelligence

**Priority**: High
**Status**: Done
**Phase**: Cross-Cutting
**ADR**: ADR-002 (Goal-Oriented Project Navigation) — Steps 3+4
**Depends On**: Story 085 (pipeline capability graph)

## Goal

Make the AI actually reason about the pipeline graph. When a user asks "what should I do next?", the AI should call the graph tool and give a grounded recommendation. When the AI proposes a run that has missing upstream, it should warn or soft-block instead of blindly proceeding.

This is the intelligence layer on top of Story 085's infrastructure.

## Acceptance Criteria

### AI Reasoning About Pipeline State
- [x] When a user asks "what should I do next?", the AI calls `read_pipeline_graph` and recommends available nodes by priority
- [x] The AI explains WHY a node is blocked (names the missing upstream artifacts)
- [x] The AI suggests the most impactful next action (not just any available node)

### Tiered Response in propose_run
- [x] When propose_run is triggered and all prerequisites are met: proceed normally (green)
- [x] When propose_run is triggered with stale upstream: warn the user and offer to rerun upstream first (yellow)
- [x] When propose_run is triggered with missing critical upstream: soft-block with explanation of what's needed (red)
- [x] The tiered response is visible in the chat as clear, actionable guidance

### Graph Helper Functions
- [x] `get_available_actions(graph_result)` returns a prioritized list of actionable next steps
- [x] `check_prerequisites(node_id, graph_result)` returns what's met and what's unmet for a specific node
- [x] Both functions are tested

### Testing
- [x] Unit tests for `get_available_actions` with various graph states
- [x] Unit tests for `check_prerequisites` with met/unmet/stale scenarios
- [x] Unit tests for tiered response logic
- [x] Manual test: ask AI "what should I do next?" on a project with partial pipeline

## Out of Scope
- Full DAG visualization (Story 087+ or future)
- Automatic execution of recommended actions (user must confirm)
- Staleness explanation detail (Story 088)

## Tasks

- [x] Task 1: Add `get_available_actions()` and `check_prerequisites()` to `graph.py`
- [x] Task 2: Add pipeline navigation guidance to system prompt
- [x] Task 3: Add tiered preflight check in `_execute_propose_run`
- [x] Task 4: Update `_format_pipeline_graph` to include actionable recommendations
- [x] Task 5: Tests
- [x] Task 6: Runtime smoke test
- [x] Task 7: Update docs

## Work Log

*(append-only)*

20260226 — Story created from ADR-002 steps 3+4. Builds on Story 085 pipeline graph infrastructure.

20260226-0130 — Implementation complete. Changes:

**graph.py**: Added `get_available_actions(graph)` — returns prioritized list of actionable next steps, sorting partial-phase nodes first (finish what you started). Added `check_prerequisites(node_id, graph)` — returns met/unmet dependencies with human-readable reasons.

**chat.py — System prompt**: Added "Pipeline Navigation" section to ASSISTANT_EXTRA instructing the AI to: (1) call read_pipeline_graph when asked about next steps, (2) recommend highest-priority available action, (3) explain blocked nodes, (4) check graph before proposing runs.

**chat.py — Preflight**: Added `_check_recipe_preflight()` with tiered response. Maps recipe_id to required upstream pipeline nodes. Returns "ready" (green), "warn_stale" (yellow), or "block_missing" (red). Modified `_execute_propose_run` to check preflight before proposing — blocks with explanation if upstream missing, adds warning if upstream stale.

**chat.py — Graph formatting**: Enhanced `_format_pipeline_graph()` with prioritized action list, blocked node explanations showing which upstream is missing, and stale node section.

**Tests**: 9 new tests (30 total) covering: available actions with empty/partial/full stores, priority ordering, prerequisite checking for met/unmet/no-deps/unknown/unimplemented scenarios. All 335 unit tests pass. Lint clean.
