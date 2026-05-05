# Story 198 Live Refresh Evidence

Captured: 2026-05-05T14:07:57Z

## Scope

The stale Brick & Steel production project was refreshed in place without deleting
historical artifact folders. The run used this worktree's Story 198 code and the
primary project output directory:

- Project: `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired`
- Source code: `/Users/cam/.codex/worktrees/5967/cine-forge`
- Input: `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/inputs/4679ff2e_Brick-_-Steel.pdf`

## Runs

- `story198-brick-steel-character-refresh-20260505`
  - Stage range: `character_bible` only.
  - Upstream inputs were resumed from existing `analyze_scenes` and
    `entity_discovery` refs.
  - Result: `character_bible` done in 39.114s, 22 artifacts, model
    `claude-sonnet-4-6`, cost `$0.181206`.
- `story198-brick-steel-graph-refresh-20260505`
  - Stage range: `entity_graph` only.
  - Inputs were resumed from refreshed `character_bible` refs and existing
    `location_bible` / `prop_bible` refs.
  - Result: `entity_graph` done in 13.1925s, 1 artifact, model
    `claude-sonnet-4-6`, cost `$0.014307`.
- `story198-brick-steel-continuity-refresh-20260505`
  - Stage range: `continuity_tracking` only.
  - Inputs were resumed from refreshed `character_bible` refs and existing
    `location_bible` / `prop_bible` refs.
  - Result: `continuity_tracking` done in 70.7621s, 22 artifacts, model
    `claude-sonnet-4-6`, cost `$0.126057`.

## Current Artifact Truth

- Current stage-cache Brick refs:
  - `character_bible/brick:v2`
  - `bible_manifest/character_brick:v2`
  - `entity_graph/project:v2`
  - `continuity_index/project:v2`
  - `continuity_state/character_brick_scene_001:v2`
  - `continuity_state/character_brick_scene_004:v2`
  - `continuity_state/character_brick_scene_005:v2`
- Current `character_bible/brick:v2` keeps `character_id="brick"`,
  `name="BRICK"`, and `aliases=["BRICK BRADDOCK"]`.
- Current API artifact groups no longer expose any `brick_braddock` group,
  including character bibles, bible manifests, or continuity states.
- Historical duplicate artifacts are still present on disk, including
  `artifacts/character_bible/brick_braddock/v1.json` and
  `artifacts/bibles/character_brick_braddock/manifest_v2.json`.
- Refreshed graph `entity_graph/project:v2` contains no `brick_braddock`
  edge/source/target/entity ids.
- Refreshed continuity index `continuity_index/project:v2` contains no
  `brick_braddock` entity ids.

## Browser Evidence

- Route: `http://127.0.0.1:5199/brick-steel-full-retired/characters`
- Desktop screenshot: `browser/characters-desktop.png`
- Mobile screenshot: `browser/characters-mobile.png`
- Evidence JSON: `browser/cdp-console.json`
- Desktop and mobile entity-card headings both include `Brick` and do not
  include a separate `Brick Braddock` card.
- Raw page text can still include `Brick Braddock` as alias/descriptive canon
  under canonical Brick; that is expected and not a duplicate entity card.
- Console, page-error, and >=400 response captures were clean for both
  viewports.

## Reset Shard B Verification

Verified: 2026-05-05T13:59:57Z

- Live API group check on port `5199` exposed only
  `character_bible/brick:v2` and `bible_manifest/character_brick:v2` for Brick
  character/bible current groups.
- Current stage cache also points only to
  `artifacts/character_bible/brick/v2.json` and
  `artifacts/bibles/character_brick/manifest_v2.json` for Brick
  character/bible outputs.
- `rg -n 'brick_braddock' artifacts/entity_graph/project/v2.json` returned no
  matches for the refreshed graph.
- Historical duplicate artifacts were still present on disk:
  `artifacts/character_bible/brick_braddock/v1.json` and
  `artifacts/bibles/character_brick_braddock/manifest_v2.json`.
- `browser/cdp-console.json` records desktop and mobile entity-card headings
  containing `Brick` and not containing a separate `Brick Braddock` heading,
  with no console, page, or response errors.
- Existing chat-action browser evidence remains valid for the unsupported
  identity-merge path: `browser/chat-action-browser-api-evidence.json` records
  direct API `422 unsupported_artifact_edit`, unchanged manifest versions
  `[1, 2]`, desktop/mobile UI error surfacing, no unexpected browser failures,
  and no production artifact mutation.

## Continuity Refresh Verification

Verified: 2026-05-05T14:07:57Z

- `continuity_tracking` was refreshed after the character/graph refresh.
- Current stage cache points to `continuity_state/character_brick_scene_001:v2`,
  `character_brick_scene_004:v2`, and `character_brick_scene_005:v2`, with no
  `character_brick_braddock_*` continuity refs.
- Live API groups expose no `brick_braddock` current group after restarting the
  backend with this worktree's source.
- Browser route evidence was regenerated after the continuity refresh; desktop
  and mobile still show canonical `Brick` only as the entity card heading.
