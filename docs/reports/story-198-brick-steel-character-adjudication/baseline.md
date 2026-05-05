# Story 198 Baseline Evidence

Captured during `/build-story 198` planning and implementation start.

This report is pre-fix baseline evidence only. It intentionally records the
duplicate artifact state and misleading proposal behavior that Round 1 set out
to fix; do not treat these observations as current post-fix validation.

## Baseline Brick & Steel Artifact State

- Project: `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired`
- Enriched scene index: `artifacts/scene_index/project/v2.json`
  - `unique_characters` includes both `BRICK` and `BRICK BRADDOCK`.
  - All inspected enriched entries have `characters_present_ids: []`.
- Entity discovery: `artifacts/entity_discovery_results/project/v1.json`
  - `characters` includes both `BRICK` and `BRICK BRADDOCK`.
  - `processing_metadata.character_source` is `scene_index`.
- Character bibles:
  - `artifacts/character_bible/brick/v1.json`
  - `artifacts/character_bible/brick_braddock/v1.json`
- Folder-backed bibles:
  - `artifacts/bibles/character_brick/master_v1.json` has `name: BRICK` and `aliases: ["Brick Braddock"]`.
  - `artifacts/bibles/character_brick_braddock/master_v1.json` has `name: BRICK BRADDOCK` and `aliases: ["Brick"]`.
  - `artifacts/bibles/character_brick_braddock/manifest_v2.json` owns `visual_reference_image: design_study_r1_img1.jpg`.
- Entity graph: `artifacts/entity_graph/project/v1.json`
  - `entity_count.character` is `15`.
  - Separate `brick` and `brick_braddock` edges exist, including a character co-occurrence edge between them.

## Candidate-Resolution Probe

Read-only baseline probe against the captured artifacts showed:

```text
[character_bible] Using 15 characters from discovery results.
[character_bible] Skipping second-pass adjudication for discovery-backed candidates.
aggregate contains brick variants: ['BRICK', 'BRICK BRADDOCK']
ranked brick variants: [{'name': 'BRICK', 'scene_count': 3, ...}, {'name': 'BRICK BRADDOCK', 'scene_count': 2, ...}]
prepared candidates brick variants: [{'name': 'BRICK', ...}, {'name': 'BRICK BRADDOCK', ...}]
rejected: []
decision_trace_len: 0 cost_model: mock
```

Classification: discovery-backed character candidates bypassed the existing adjudicator, so the merge-capable path never saw the alias pair.

## Chat-Edit Probe

Read-only probe of `build_artifact_edit_tool_result` with a merge-like edit showed:

```text
status: proposal_ready
artifact: bible_manifest/character_brick_braddock
diff: ~ aliases: [1 items] -> [1 items]
~ character_id: "brick_braddock" -> "brick"
~ name: "BRICK BRADDOCK" -> "BRICK"
action_endpoint: /api/projects/brick-steel-full-retired/artifacts/bible_manifest/character_brick_braddock/edit
```

Classification: the edit path could present a plausible single-bible proposal, but that would not merge/deprecate the duplicate group or repair downstream scene/graph references.
