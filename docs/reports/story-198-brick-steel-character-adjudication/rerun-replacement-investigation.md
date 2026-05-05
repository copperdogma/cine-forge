# Story 198 Rerun / Replacement Investigation

Captured: 2026-05-05T13:41:26Z

## Scope

Owned shard: decide whether the remaining Brick & Steel gate can be closed by a
bounded repo-native rerun or deterministic artifact replacement without
mutating immutable artifact history.

Materiality gate: only live artifact truth, artifact-store immutability, helper
contracts, recipe/run-state behavior, or evidence needed to close the Story 198
gate counts as material.

## Files And Surfaces Inspected

- `docs/stories/story-198-brick-steel-character-adjudication.md`
- `docs/reports/story-198-brick-steel-character-adjudication/baseline.md`
- `docs/reports/story-198-brick-steel-character-adjudication/browser/route-evidence.md`
- `configs/recipes/recipe-world-building.yaml`
- `configs/recipes/recipe-mvp-ingest.yaml`
- `src/cine_forge/artifacts/store.py`
- `src/cine_forge/artifacts/graph.py`
- `src/cine_forge/artifacts/bible_identity.py`
- `src/cine_forge/api/artifact_manager.py`
- `src/cine_forge/api/artifact_editing.py`
- `src/cine_forge/api/run_orchestrator.py`
- `src/cine_forge/driver/engine.py`
- `ui/src/lib/hooks/entities.ts`
- `ui/src/pages/EntityListPage.tsx`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/project.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/stage_cache.json`
- `/Users/cam/Documents/Projects/cine-forge/output/runs/run-94103c1a/run_state.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/scene_index/project/v2.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/entity_discovery_results/project/v1.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/character_bible/brick/v1.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/character_bible/brick_braddock/v1.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/bibles/character_brick/manifest_v1.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/bibles/character_brick_braddock/manifest_v2.json`
- `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/entity_graph/project/v1.json`

## Findings

1. The remaining live gate is real.

   The primary checkout project still exposes both `BRICK` and `BRICK BRADDOCK`
   in `scene_index/project/v2.json` and `entity_discovery_results/project/v1.json`.
   The current artifact groups list has both `character_bible/brick` and
   `character_bible/brick_braddock`, both with `health=valid`. It also has both
   `bible_manifest/character_brick` and
   `bible_manifest/character_brick_braddock`, both with `health=valid`.

2. A normal in-place world-building rerun preserves immutable history, but does
   not by itself remove the live duplicate from the Characters surface.

   `ArtifactStore.save_artifact(...)` and `save_bible_entry(...)` only append
   new versions. They do not tombstone, hide, delete, or retire old artifact
   groups. The Characters route reads artifact groups from the folder layout:
   `ui/src/lib/hooks/entities.ts` filters all groups with
   `artifact_type == "character_bible"`, and
   `src/cine_forge/api/artifact_manager.py` lists every versioned entity folder.
   Therefore a fresh `character_bible/brick/v2` would not remove the old
   `character_bible/brick_braddock/v1` group from the live list.

3. The repo intentionally rejects single-artifact identity merge/deprecation.

   `src/cine_forge/artifacts/bible_identity.py` says this requires a dedicated
   merge workflow that can version the canonical bible, preserve
   aliases/reference assets, and update downstream graph/scene references
   together. The current Story 198 helper/API fix is therefore honest: it blocks
   a fake single-artifact edit instead of creating a partial merge.

4. The safe close path is not a bounded deterministic local fix in this shard.

   Closing the live route requires one of:

   - a live paid world-building rerun into a clean replacement project, followed
     by human acceptance/promotion of that project as the live
     `brick-steel-full-retired` project; or
   - a new dedicated character-merge/tombstone workflow, which is source/product
     work outside this shard.

   I did not move, delete, or rewrite production artifacts.

## Exact Commands / Conditions

### Verify The Current Blocker

```bash
cd /Users/cam/.codex/worktrees/5967/cine-forge
PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python - <<'PY'
from pathlib import Path
from cine_forge.api.service import OperatorConsoleService

service = OperatorConsoleService(workspace_root=Path("/Users/cam/Documents/Projects/cine-forge"))
groups = service.list_artifact_groups("brick-steel-full-retired")
for artifact_type in ("character_bible", "bible_manifest"):
    matches = [
        g for g in groups
        if g["artifact_type"] == artifact_type
        and "brick" in str(g.get("entity_id") or "")
    ]
    print(artifact_type, matches)
PY
```

Expected current blocker: both `brick` and `brick_braddock` groups are present.

### Paid Rerun Command For A Clean Replacement Project

Condition: run only after accepting that this spends live model calls and
produces a clean replacement project for human review, not an in-place close.

```bash
cd /Users/cam/.codex/worktrees/5967/cine-forge
PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python - <<'PY'
from pathlib import Path
import json
import shutil

from cine_forge.driver.engine import DriverEngine

root = Path("/Users/cam/Documents/Projects/cine-forge")
source_project = root / "output" / "brick-steel-full-retired"
replacement = root / "output" / "brick-steel-full-retired-story198-rerun"
source_input = source_project / "inputs" / "4679ff2e_Brick-_-Steel.pdf"
replacement_input = replacement / "inputs" / source_input.name

replacement.mkdir(parents=True, exist_ok=True)
(replacement / "inputs").mkdir(parents=True, exist_ok=True)
shutil.copy2(source_input, replacement_input)
(replacement / "project.json").write_text(json.dumps({
    "slug": "brick-steel-full-retired-story198-rerun",
    "display_name": "Brick & Steel: Full Retired Story 198 Rerun",
    "production_format": "live_action",
}, indent=2), encoding="utf-8")

params = {
    "input_file": str(replacement_input),
    "accept_config": True,
    "human_control_mode": "autonomous",
    "default_model": "claude-sonnet-4-6",
    "model": "claude-sonnet-4-6",
    "work_model": "claude-sonnet-4-6",
    "verify_model": "gpt-4.1-mini",
    "qa_model": "gpt-4.1-mini",
    "skip_qa": True,
}
engine = DriverEngine(workspace_root=root, project_dir=replacement)
engine.run(
    recipe_path=root / "configs" / "recipes" / "recipe-mvp-ingest.yaml",
    run_id="story-198-brick-steel-replacement-ingest",
    force=True,
    runtime_params=params,
)
engine.run(
    recipe_path=root / "configs" / "recipes" / "recipe-world-building.yaml",
    run_id="story-198-brick-steel-replacement-world",
    force=True,
    runtime_params=params,
)
PY
```

Acceptance condition before promotion: the replacement project must have no
`character_bible/brick_braddock` or `bible_manifest/character_brick_braddock`
group, and canonical `brick` must preserve `Brick Braddock` as an alias or
equivalent evidence. A browser check should then open the replacement
Characters route before any promotion.

### Promotion Condition

Promotion of the clean replacement to the live slug requires human judgment
because the current live project includes user-visible design-study/reference
assets, generated videos, chat history, and run history. A blind directory swap
would close the duplicate gate but could discard or detach those other
operator-facing artifacts from the live route.

Do not promote automatically from this shard.

## Checks Run

- `git status --short`
- `rg` searches for Story 198, Brick/Brick Braddock, recipes, run-state refs,
  artifact helpers, merge/tombstone/deprecation support.
- `jq` inspections of current Brick & Steel scene index, entity discovery,
  character bibles, bible manifests, entity graph, stage cache, and
  `run-94103c1a/run_state.json`.
- Python read-only service probe against the primary checkout project output
  using this worktree's code.

## Result

Blocked. No production artifact mutation was safe inside this shard.
