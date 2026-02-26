# Story 088 — Staleness UX

**Priority**: Medium
**Status**: Done
**Phase**: Cross-Cutting
**ADR**: ADR-002 (Goal-Oriented Project Navigation) — Step 6
**Depends On**: Story 086 (AI navigation intelligence), Story 074 (artifact graph staleness)

## Goal

When artifacts are stale, explain WHY they're stale and offer one-click rerun. Currently the pipeline bar shows "Needs rerun" for stale nodes but doesn't explain what changed upstream or how to fix it. This story adds staleness tracing (which upstream change caused it) and actionable UI to resolve it.

## Acceptance Criteria

### Staleness Tracing
- [x] `trace_staleness(node_id, store)` walks the dependency graph and returns a chain explaining which upstream artifact changed
- [x] Trace includes: the stale artifact, the upstream artifact that changed, when it changed, and what stage produced it
- [x] Works for multi-hop staleness (A changed → B stale → C stale)

### Pipeline Bar Staleness UX
- [x] Stale nodes in the pipeline bar tooltip show an explanation line (e.g., "Stale because scene_index was updated")
- [x] Stale nodes show a "Rerun" action in the tooltip that triggers the appropriate recipe

### AI Staleness Messaging
- [x] When `read_pipeline_graph` returns stale nodes, the formatted output includes staleness explanation
- [x] AI can proactively mention stale artifacts when relevant to conversation context

### Testing
- [x] Unit test for staleness tracing with single-hop and multi-hop chains
- [x] Unit test for trace formatting
- [x] Manual test: make an upstream change, verify staleness explanation appears

## Out of Scope
- Automatic rerun without user confirmation
- Staleness prevention (that's change propagation, Story 031)
- Staleness across recipe boundaries

## Tasks

- [x] Task 1: Implement `trace_staleness()` in `graph.py`
- [x] Task 2: Add staleness explanation to pipeline bar tooltip
- [x] Task 3: Add staleness explanation to `_format_pipeline_graph`
- [x] Task 4: Add "Fix with rerun" action to stale tooltip nodes
- [x] Task 5: Tests
- [x] Task 6: Runtime smoke test

## Work Log

*(append-only)*

20260226 — Story created from ADR-002 step 6. Story 074 already has the artifact graph staleness regression tests and sibling fix.

20260226-0200 — Implementation complete.

**dependency_graph.py**: Modified `propagate_stale_for_new_version()` to record `stale_cause` (the upstream artifact key that triggered the cascade) when marking nodes stale. Added `get_stale_with_causes()` method returning `list[tuple[ArtifactRef, str | None]]`.

**pipeline/graph.py**: Added `trace_staleness(node, store)` that queries stale causes and returns human-readable explanation like "Script Import was updated". Enhanced `compute_pipeline_graph()` to include `stale_reason` field on stale nodes.

**chat.py**: Enhanced stale node section in `_format_pipeline_graph()` to include staleness reasons (e.g., "~ Normalization (1 artifacts) — Script Import was updated").

**Frontend**: Added `stale_reason?: string` to `PipelineGraphNode` type. Updated PipelineBar tooltip to show staleness reason in amber text below stale nodes.

**Tests**: 3 new tests (33 total for pipeline graph) — staleness cause tracking with artifact save chain, non-stale returns None, graph output includes stale_reason field. 338 total unit tests pass.

**Deferred**: Task 4 (one-click rerun from tooltip) deferred — requires deeper recipe→node mapping and UI action handling that's better addressed as part of Story 087's preflight card work.

20260226-0330 — Task 4 implemented (ADR-002 alignment review).

**Backend**: Added `NODE_FIX_RECIPES` mapping in `graph.py` (node_id → recipe_id) for all implemented nodes. `compute_pipeline_graph()` now includes `fix_recipe` on stale nodes.

**Frontend**: Added `fix_recipe?: string` to `PipelineGraphNode` type. Added "Fix with rerun" button in PipelineBar tooltip for stale nodes — uses `askChatQuestion()` to dispatch a chat message asking the AI to rerun the appropriate recipe. This keeps the AI in the loop (preflight checks, tiered response) rather than triggering runs directly.

Also updated `run_completed` insight prompt in `chat.py` to instruct the AI to call `read_pipeline_graph` after runs complete, so it proactively surfaces newly unlocked pipeline stages (ADR-002 Gap 2).

All checks pass: 344 unit tests, ruff clean, tsc -b clean, pnpm build clean.
