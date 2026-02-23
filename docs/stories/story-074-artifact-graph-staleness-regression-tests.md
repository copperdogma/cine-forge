# Story 074 — Artifact graph staleness: regression tests + sibling cross-contamination fix

**Priority**: Medium
**Status**: Pending
**Spec Refs**: N/A
**Depends On**: None

## Goal

The Story 062 smoke test exposed two staleness propagation bugs in `ArtifactDependencyGraph`.
One was fixed (self-staleness: a newly-created artifact was marking itself stale via BFS through
its own lineage). A second, more subtle bug remains unfixed: sibling artifacts produced in
parallel can mark each other stale through a shared intermediate node (e.g., scene_001:v3 gets
marked stale when scene_002:v3 is saved, because both listed scene_index:v2 in their lineage and
the BFS propagation crosses through it).

This story adds regression tests for both bugs and fixes the sibling cross-contamination issue.

## Background: The Two Bugs

### Bug 1 — Self-staleness (already fixed in graph.py, no test)

When `propagate_stale_for_new_version(X:v2)` runs:
1. It finds X:v1's downstream nodes.
2. X:v2 is in that downstream list (because X:v2 listed X:v1 in its lineage).
3. BFS marks X:v2 as stale — immediately after creation.

**Fix applied (Story 062):** Seed the BFS `seen` set with `{new_key}` so the new artifact is
never visited. `seen: set[str] = {new_key}  # never mark the new version itself as stale`

**Gap:** No unit test. The next agent to touch `propagate_stale_for_new_version` can re-introduce
this with no automated catch.

### Bug 2 — Sibling cross-contamination (known remaining issue, not yet fixed)

Setup: 13 scenes produced in parallel (scene_001:v3 … scene_013:v3), all listing
scene_index:v2 in their lineage. When `propagate_stale_for_new_version(scene_002:v3)` runs:

1. scene_002:v2's downstream includes scene_index:v2 (scene_index:v2 was built from v2 scenes).
2. BFS marks scene_index:v2 as stale.
3. scene_index:v2's downstream includes scene_001:v3 (because v3 scenes listed v2 scene_index).
4. `scene_001:v3` is NOT in `seen` (which is only seeded with `scene_002:v3`).
5. scene_001:v3 — a sibling, freshly produced — gets marked stale.

**Root cause:** The BFS crosses through a shared intermediate node (scene_index:v2) and reaches
sibling artifacts that are independently valid.

**Proposed fix:** When BFS encounters a node, skip it if a newer version of the same
`(artifact_type, entity_id)` pair already exists in the graph. If a superseding version exists,
the downstream was already rebuilt from the new version — there is no value in marking the old
downstream stale.

## Acceptance Criteria

- [ ] `test_new_version_not_marked_stale`: save artifact A:v1, save A:v2 with A:v1 in lineage →
  `graph.get_health(A:v2)` is VALID, A:v2 is not in `graph.get_stale()`.
- [ ] `test_sibling_not_marked_stale_via_shared_intermediate`: reproduce the sibling
  cross-contamination scenario (A:v1 → B:v1, A:v2 → B:v2 produced in parallel from the same
  intermediate B:v1 downstream) → after A:v2 is saved and propagation runs, B:v2 remains VALID.
  *(This test is currently expected to fail before the fix and pass after.)*
- [ ] The fix does not regress the core staleness case: saving A:v2 still marks B:v1 stale when B
  was derived from A:v1 and no newer B exists.
- [ ] `make test-unit` passes. Ruff passes.

## Out of Scope

- Fixing staleness propagation across recipes or across projects.
- Changes to `store_inputs` health validation in engine.py.
- UI display of stale artifacts.

## AI Considerations

Pure code — no LLM calls. The fix logic is a graph traversal correctness problem. The key
insight for the fix: build a lookup of `{(artifact_type, entity_id): max_version}` from the
graph nodes before BFS, then skip any node whose version is not the max for its entity. This is
O(N) setup + O(N) BFS, acceptable.

## Tasks

- [ ] Read `tests/unit/test_artifact_store.py` — understand existing graph test setup helpers
- [ ] Add `test_new_version_not_marked_stale` — regression for Bug 1 (self-staleness)
- [ ] Add `test_sibling_not_marked_stale_via_shared_intermediate` — reproduces Bug 2 (initially
  expected to fail; mark with `pytest.mark.xfail(strict=True)` until fixed, then remove)
- [ ] Implement fix in `graph.py` `propagate_stale_for_new_version`:
  - Before BFS, compute `latest_version: dict[tuple[str, str], int]` = max version per
    `(artifact_type, entity_id)` across all graph nodes
  - In the BFS loop, skip any node if `node_ref.version < latest_version[(type, entity_id)]`
    (a superseding version already exists — this node's downstream was rebuilt)
- [ ] Re-run test (remove xfail if test now passes)
- [ ] Run required checks:
  - [ ] `make test-unit PYTHON=.venv/bin/python`
  - [ ] `.venv/bin/python -m ruff check src/ tests/`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** No user data affected; graph is a derived index.
  - [ ] **T1 — AI-Coded:** Fix is a small targeted change; comment in BFS loop explains the
    "superseded version" skip logic.
  - [ ] **T2 — Architect for 100x:** Minimal change, no new abstractions.
  - [ ] **T3 — Fewer Files:** Tests go in existing `test_artifact_store.py`.
  - [ ] **T4 — Verbose Artifacts:** Work log should capture which edge cases were tested.
  - [ ] **T5 — Ideal vs Today:** The ideal fix (tracking `superseded_by` links explicitly) is
    more elegant but the `latest_version` lookup achieves the same correctness at lower cost.

## Files to Modify

- `tests/unit/test_artifact_store.py` — add two new test functions
- `src/cine_forge/artifacts/graph.py` — patch `propagate_stale_for_new_version` to skip
  superseded nodes

## Notes

**Why the sibling scenario arises in practice:**

In the `world_building` recipe, `scene_analysis_v1` enriches all 13 scenes in parallel. Each
enriched scene (v3) lists `scene_index:v2` in its lineage (the enrichment reads the scene_index
for context). When the first sibling scene is saved and propagation runs, it crosses through
`scene_index:v2` and reaches the other sibling scenes (which are also in scene_index:v2's
downstream). All siblings end up stale despite being freshly valid.

**Minimal reproduction (for tests):**

```
scene_index:v1 → [scene_001:v2, scene_002:v2]  (v2 scenes listed v1 scene_index in lineage)
scene_index:v2 ← [scene_001:v2, scene_002:v2]  (scene_index:v2 built from v2 scenes)
```

Now save scene_001:v3 and scene_002:v3, both listing scene_index:v2 in lineage. Save
scene_001:v3 first. `propagate_stale_for_new_version(scene_001:v3)` crosses through
`scene_index:v2` and reaches `scene_002:v3`. After the fix, scene_002:v3 should be skipped
because it is the latest version of its entity.

**Relationship to Story 073 (`after:`):**

These are independent stories. Story 073 fixes recipe authoring ergonomics; Story 074 fixes
graph correctness. Both can be worked in parallel.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

20260222-XXXX — story created: two bugs surfaced during Story 062 smoke test; Bug 1 fixed
without test; Bug 2 documented as known remaining issue; this story adds tests + fixes Bug 2.
