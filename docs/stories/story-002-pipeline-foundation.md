# Story 002: Pipeline Foundation (Driver, Artifact Store, Schemas)

**Status**: To Do
**Created**: 2026-02-11
**Spec Refs**: 2.1 (Immutability), 2.2 (Versioning), 2.3 Layer 1 (Structural Invalidation), 2.4 (Non-AI Logic), 2.6 (Explanation/Audit), 2.7 (Cost Hooks), 2.8 (Structural QA), 3 (Pipeline Overview), 3.1 (Stage Progression), 20 (Metadata & Auditing)
**Depends On**: Story 001 (project scaffolding)

---

## Goal

Build the core infrastructure that every subsequent story depends on: the artifact store (immutable, versioned, dependency-tracked), the schema system (Pydantic models with structural validation), the module contract (how stages declare themselves), the recipe format (YAML workflow definitions), and the driver (orchestrator that executes recipes). This is the non-AI backbone described in spec Section 2.4 — artifact storage, versioning, dependency resolution, and scheduling.

This story produces a working but empty pipeline: no AI modules yet, but the skeleton can load a recipe, discover modules, execute them in order, produce versioned artifacts with audit metadata, track dependencies, validate schemas, record costs, and isolate runs. Story 007 (MVP smoke test) will wire real modules into this.

## Acceptance Criteria

### Artifact Store
- [ ] Artifact store API implemented (`src/cine_forge/artifacts/`):
  - [ ] `save_artifact(project, artifact_type, entity_id, data, metadata) → ArtifactRef` — saves a new immutable versioned snapshot.
  - [ ] `load_artifact(project, artifact_ref) → Artifact` — loads any version directly by reference.
  - [ ] `list_versions(project, artifact_type, entity_id) → list[ArtifactRef]` — returns full version history.
  - [ ] `diff_versions(ref_a, ref_b) → Diff` — computes diff on demand between any two versions.
- [ ] Every saved artifact is a complete immutable snapshot (spec 2.2). No diff-chains, no deltas.
- [ ] Every artifact version records:
  - [ ] Lineage: what it was derived from (parent artifact refs).
  - [ ] Audit metadata: intent, rationale, alternatives_considered, confidence, source (AI/human/hybrid) — per spec Section 20.
  - [ ] Timestamp, producing module/role, schema version.
  - [ ] Cost data: if produced by an AI call, the call's token usage and estimated cost (spec 2.7 hook).
- [ ] Artifacts stored on disk in the project folder (spec: "all artifacts for a project live in a single project folder").
- [ ] Artifacts are never modified in place. Any code path that attempts to overwrite an existing artifact version must error.

### Dependency Graph (Structural Invalidation — Layer 1)
- [ ] Every artifact records its upstream dependencies (what it was built from) as explicit artifact refs.
- [ ] When a new version of an artifact is created, all downstream artifacts that transitively depend on the previous version are automatically marked `stale`.
- [ ] This is deterministic graph traversal — no AI call, no heuristics.
- [ ] Artifact health status tracked per spec 2.3:
  - [ ] `valid` — current, no upstream changes.
  - [ ] `stale` — structurally invalidated by an upstream revision, not yet assessed.
  - [ ] `needs_revision` — placeholder for future AI assessment (Story 031).
  - [ ] `confirmed_valid` — placeholder for future AI assessment (Story 031).
- [ ] API to query: "what is stale?", "what depends on artifact X?", "what does artifact X depend on?"

### Schema System
- [ ] Base Pydantic models defined in `src/cine_forge/schemas/`:
  - [ ] `ArtifactMetadata` — the audit metadata envelope (intent, rationale, alternatives_considered, confidence, source, timestamp, producing_module, producing_role, cost_data, lineage).
  - [ ] `ArtifactRef` — unique reference to a specific artifact version (type, entity_id, version, path).
  - [ ] `ArtifactHealth` — enum: valid, stale, needs_revision, confirmed_valid.
  - [ ] `CostRecord` — per-call cost tracking (model, input_tokens, output_tokens, estimated_cost_usd).
- [ ] Schema validation function: given an artifact and a schema, validate and return structured errors.
- [ ] Schema registry: modules declare their input/output schemas; the driver can check compatibility.
- [ ] Validation is QA tier 1 (spec 2.8): automated structural check, no AI call required.

### Module Contract
- [ ] A module is a directory under `src/cine_forge/modules/{stage}/{module_id}/` containing:
  - [ ] `module.yaml` — manifest declaring: module_id, stage, description, input_schema(s), output_schema(s), parameters.
  - [ ] `main.py` — entry point with a standard interface (receives input artifacts + params, returns output artifacts).
- [ ] Module discovery: the driver scans `modules/` and builds a registry of available modules.
- [ ] At least one mock/stub module exists to exercise the pipeline end-to-end (e.g., `test/echo_v1` that copies input to output with metadata).

### Recipe Format
- [ ] Recipes are YAML files in `configs/recipes/` defining:
  - [ ] `recipe_id` and `description`.
  - [ ] `stages` — ordered list of stage entries, each specifying:
    - [ ] `id` — unique stage identifier within the recipe.
    - [ ] `module` — module_id to execute.
    - [ ] `params` — optional parameters passed to the module.
    - [ ] `needs` — list of stage ids this stage depends on (for DAG execution, not just linear).
  - [ ] `project` — default project configuration overrides (optional).
- [ ] Recipe validation: check all module_ids exist in registry, all `needs` references resolve, no cycles, schema compatibility between connected stages.
- [ ] At least one test recipe exists (using the mock module) to exercise the driver.

### Driver / Orchestrator
- [ ] Driver implemented in `src/cine_forge/driver/`:
  - [ ] Loads and validates a recipe.
  - [ ] Resolves execution order (topological sort of stage DAG).
  - [ ] For each stage: loads input artifacts, invokes the module, validates output against declared schema, saves output as a new artifact version with full metadata.
  - [ ] Run isolation: each run produces output under `output/runs/{run_id}/` with a unique run_id.
  - [ ] Run state tracking: `run_state.json` records per-stage status (pending, running, done, failed), artifact refs, timing, cost.
  - [ ] `--dry-run` flag: resolve and validate the plan without executing.
  - [ ] `--start-from {stage_id}` flag: resume from a specific stage (reuses upstream artifacts).
  - [ ] `--force` flag: re-execute even if artifacts exist.
  - [ ] Cost accumulation: driver sums per-stage costs into a run-level total, written to run state.
- [ ] Pipeline events log: `pipeline_events.jsonl` in the run directory, recording stage start/end, errors, warnings, cost data.
- [ ] Non-rigid ordering: the driver supports the stage progression model from spec 3.1. It can execute a subset of stages for a subset of entities (scenes, characters, etc.) — not forced to run everything linearly. Initial implementation may be simpler (full recipe execution) but the data model must support partial/selective runs.

### Testing
- [ ] Unit tests for artifact store: save, load, list versions, immutability enforcement (overwrite errors), dependency tracking, staleness propagation.
- [ ] Unit tests for schema validation: valid/invalid artifacts, missing required fields.
- [ ] Unit tests for recipe validation: valid recipes, cycle detection, missing modules, schema mismatches.
- [ ] Unit tests for driver: plan resolution, stage execution with mock module, run state tracking.
- [ ] Integration test: load test recipe → execute with mock module → verify artifacts in output/runs/, verify run_state.json, verify pipeline_events.jsonl.

## Design Notes

### Artifact Storage Layout

Artifacts live within the project folder. Suggested on-disk layout:

```
{project_dir}/
├── artifacts/
│   ├── scripts/
│   │   ├── script_v1.json
│   │   ├── script_v2.json
│   │   └── ...
│   ├── scenes/
│   │   ├── scene_1_v1.json
│   │   ├── scene_1_v2.json
│   │   ├── scene_7_v1.json
│   │   ├── scene_7_v2.json
│   │   └── ...
│   ├── bibles/
│   │   ├── character_jane/
│   │   │   ├── manifest_v1.json
│   │   │   ├── manifest_v2.json
│   │   │   ├── master_v1.json
│   │   │   ├── reference_photo_001.jpg
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── graph/
│   └── dependency_graph.json       # Maps artifact refs → upstream deps + health status
├── project_config.json              # Canonical project configuration artifact
└── runs/
    └── {run_id}/
        ├── run_state.json
        └── pipeline_events.jsonl
```

This is a starting point. The exact layout should be refined during implementation — the important constraint is that the artifact store API abstracts over the on-disk format so it can evolve without breaking modules.

### Artifact Reference Format

An `ArtifactRef` uniquely identifies a specific version of an artifact:

```python
class ArtifactRef(BaseModel):
    artifact_type: str          # e.g., "script", "scene", "character_bible"
    entity_id: str | None       # e.g., "scene_7", "character_jane" (None for project-level)
    version: int                # monotonically increasing per artifact_type + entity_id
    path: str                   # relative path within project folder
```

### Audit Metadata Envelope

Every artifact is wrapped in metadata:

```python
class ArtifactMetadata(BaseModel):
    ref: ArtifactRef                           # This artifact's unique reference
    lineage: list[ArtifactRef]                 # What this was built from (parent artifacts)
    intent: str                                # What this artifact is meant to accomplish
    rationale: str                             # Why it was created / why this approach
    alternatives_considered: list[str] | None  # Other approaches that were weighed
    confidence: float                          # 0.0–1.0, how confident the producer is
    source: Literal["ai", "human", "hybrid"]   # Who produced this
    producing_module: str | None               # Module ID that created this (if pipeline)
    producing_role: str | None                 # Role ID that created this (if role-driven)
    cost: CostRecord | None                    # AI call cost data (if applicable)
    health: ArtifactHealth                     # valid, stale, needs_revision, confirmed_valid
    schema_version: str                        # Schema version this artifact conforms to
    created_at: datetime
```

### Module Contract Interface

```python
# Simplified interface — modules implement this pattern
class ModuleResult(BaseModel):
    artifacts: list[tuple[ArtifactRef, Any]]   # Output artifact refs + data
    metadata: list[ArtifactMetadata]           # Metadata for each output
    cost: CostRecord | None                    # Aggregated cost of this module run

def run_module(
    inputs: dict[str, Any],          # Named input artifacts (resolved by driver)
    params: dict[str, Any],          # Recipe-defined parameters
    project_config: ProjectConfig,   # Project-level configuration
) -> ModuleResult:
    ...
```

### Driver Execution Flow

```
1. Load recipe YAML
2. Discover modules (scan modules/ directory, build registry)
3. Validate recipe (modules exist, dependencies resolve, no cycles, schemas compatible)
4. Resolve execution plan (topological sort)
5. For each stage in plan:
   a. Resolve input artifacts (from upstream stages or existing project artifacts)
   b. Check if stage can be skipped (artifacts exist + valid + not --force)
   c. Invoke module with inputs + params
   d. Validate output against declared schema (QA tier 1)
   e. Save output artifacts via artifact store (immutable, versioned, with metadata)
   f. Update dependency graph (new artifact → upstream refs)
   g. Propagate staleness to downstream artifacts (Layer 1 invalidation)
   h. Record stage completion in run_state.json
   i. Log events to pipeline_events.jsonl
6. Summarize run (total cost, stages completed, errors, stale downstream artifacts)
```

### What This Story Does NOT Include

- **AI modules**: No AI calls. All modules in this story are mocks/stubs. Real modules start in Story 003.
- **Role system**: No roles, no hierarchy, no review gates. That's Story 014+.
- **Semantic impact assessment**: Layer 2 of change propagation (AI-driven) is Story 031. This story only implements Layer 1 (structural/deterministic).
- **Human interaction**: No approve/reject, no creative sessions. That's Story 019.
- **Cost dashboards/budgets**: Only cost recording hooks. Full dashboards and budget caps are Story 032.
- **Timeline**: No timeline artifact. That's Story 012.

## Tasks

- [ ] Design and implement `ArtifactRef`, `ArtifactMetadata`, `ArtifactHealth`, `CostRecord` Pydantic models in `src/cine_forge/schemas/`.
- [ ] Implement artifact store (`src/cine_forge/artifacts/store.py`): save, load, list_versions, diff_versions, with immutability enforcement.
- [ ] Implement dependency graph (`src/cine_forge/artifacts/graph.py`): add edges, query upstream/downstream, propagate staleness on new artifact version.
- [ ] Implement schema registry and validation (`src/cine_forge/schemas/registry.py`): register schemas, validate artifacts, check module compatibility.
- [ ] Define module manifest format (`module.yaml`) and implement module discovery (`src/cine_forge/driver/discovery.py`).
- [ ] Define recipe YAML format and implement recipe loader + validator (`src/cine_forge/driver/recipe.py`): load, validate modules exist, check cycles, check schema compatibility.
- [ ] Implement driver core (`src/cine_forge/driver/engine.py`): plan resolution (topo sort), stage execution loop, run state tracking, pipeline events logging.
- [ ] Implement CLI entry point (`src/cine_forge/driver/__main__.py`): `--recipe`, `--run-id`, `--dry-run`, `--start-from`, `--force`, `--instrument`.
- [ ] Create mock module (`src/cine_forge/modules/test/echo_v1/`): copies input to output with metadata, for testing.
- [ ] Create test recipe (`configs/recipes/recipe-test-echo.yaml`): exercises mock module through the driver.
- [ ] Write unit tests for artifact store (save, load, list, immutability, deps, staleness).
- [ ] Write unit tests for schema validation and registry.
- [ ] Write unit tests for recipe validation (cycles, missing modules, schema mismatches).
- [ ] Write unit tests for driver (plan resolution, execution with mock, run state).
- [ ] Write integration test: full recipe execution with mock module, verify all outputs.
- [ ] Verify: `make test-unit` passes with all new tests.
- [ ] Verify: driver can execute test recipe end-to-end: `python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --run-id test-001`.
- [ ] Update `AGENTS.md` with pipeline architecture section, common driver commands, and any lessons learned.

## Notes

### Modules vs. Roles (Architectural Decision)

The system has two distinct layers:

- **Modules** = pipeline stages. They define *what* happens: take input artifacts, produce output artifacts, validate schemas, track costs. Modules are stateless, declarative, and orchestrated by the driver.
- **Roles** = AI personas. They define *who does the thinking*: prompt persona, style pack, hierarchy position, permissions, capability gating. Roles are invoked *by* modules (or by the creative session system directly).

A module may invoke one role (e.g., Script Normalization invokes Script Supervisor), multiple roles (e.g., Direction Convergence invokes Director + all advisors for review), or no roles (e.g., Render Adapter is purely a stateless module). The Render Adapter is explicitly "not a role" per spec — everything else that involves creative reasoning uses the role layer.

The pipeline metaphor holds end-to-end: story in → script → scenes → bibles → direction → shots → storyboards → video. Each step is a module taking inputs and producing outputs. Roles are the intelligence inside those modules. Creative sessions (human ↔ role chat) sit alongside the pipeline and feed results back in as suggestions/artifact updates.

The module contract in this story should anticipate that modules will eventually receive a `role_context` dependency for invoking roles. For now it's a placeholder — the role system is built in Stories 014–019.

### Inspiration from codex-forge

The codex-forge driver provides a proven pattern: recipes define stage sequences, modules are discoverable by convention, the driver handles execution/resume/validation, and artifacts are stamped with schemas. Key adaptations for CineForge:

- **Not rigidly linear**: codex-forge is batch-sequential (pages → portions → sections → ...). CineForge needs to support per-entity processing (run one scene through multiple stages while others wait), partial runs, and user-directed progression. The driver's data model must support this even if the initial implementation is simpler.
- **Versioned artifacts, not replacement**: codex-forge overwrites stage outputs on re-run. CineForge never overwrites — every run produces new versions. The artifact store is the core differentiator.
- **Dependency graph is first-class**: codex-forge tracks stage dependencies for execution ordering. CineForge also tracks artifact-level dependencies for change propagation (staleness).
- **Audit metadata is richer**: codex-forge has basic stamping. CineForge requires intent, rationale, alternatives, confidence, source, cost — on every artifact.

### Performance Considerations

- The dependency graph will grow as projects accumulate artifacts. For MVP, a JSON file is fine. If performance becomes an issue, consider SQLite.
- Artifact storage is file-based. Large binary artifacts (images, video) should be stored as files referenced by the JSON metadata, not embedded in JSON.
- Staleness propagation should be efficient even for large graphs (breadth-first traversal from the changed node).

### Open Questions (to resolve during implementation)

- **Artifact naming convention**: `{type}_{entity}_{version}.json` vs. directory-per-entity with version files? The store API should abstract this.
- **Locking**: Should the artifact store support file locking for concurrent access? Probably not for MVP — single-user, single-process. Note in AGENTS.md if this assumption is made.
- **Large binary artifacts**: How are images, audio, video stored? Probably as files in the bible/entity folder, referenced by manifest. Defer details to Story 008 (Bible Infrastructure).

## Work Log

(entries will be added as work progresses)
