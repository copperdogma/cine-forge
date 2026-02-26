# Story 085 — Pipeline Capability Graph & Navigation Bar

**Priority**: High
**Status**: Done
**Phase**: Cross-Cutting
**ADR**: ADR-002 (Goal-Oriented Project Navigation)
**Depends On**: Story 002 (artifact store), Story 011e (UX golden path), Story 011f (conversational AI chat), Story 082 (creative direction UX)

## Goal

Build the **pipeline capability graph** — a structured representation of CineForge's full pipeline that both the UI and the AI can read. Then surface it as a **persistent pipeline bar** that shows users where their project stands: what's done, what's available next, what's blocked, and what's not started.

This is the foundational infrastructure for goal-oriented navigation (ADR-002). Without it, every new pipeline stage is just another hidden button on a page somewhere. With it, users see the full picture and the AI can reason about what's missing when downstream output is bad.

## Acceptance Criteria

### Pipeline Capability Graph (Backend)
- [x] A structured graph schema defines every user-facing pipeline capability as a node
- [x] Each node has: id, label, phase, status (not_started / in_progress / completed / stale), dependencies (required upstream nodes), output artifact types, and an optional completion metric (e.g., "3/5 characters extracted")
- [x] Edges represent data dependencies between capabilities (scene extraction depends on script normalization, etc.)
- [x] Graph is computed from actual project state — reads the artifact store to determine what exists, what's stale, and what's complete
- [x] A project-level API endpoint returns the graph for a given project: `GET /api/projects/{pid}/pipeline-graph`
- [x] The graph correctly represents the current CineForge pipeline (ingestion through creative direction)
- [x] Nodes that have no unmet required dependencies are marked "available"; nodes with unmet dependencies are "blocked"

### Pipeline Bar (Frontend)
- [x] A persistent horizontal bar at the top of content area shows pipeline phases as clickable segments
- [x] Each segment displays: phase name, icon, and status indicator (color-coded: completed/available/blocked/not_started)
- [x] Clicking a segment navigates to the relevant page (e.g., clicking "World" goes to the characters list)
- [x] The bar updates reactively when pipeline state changes (new artifacts created, stages completed)
- [x] The bar works on all pages (it's part of the app shell, not page-specific)
- [x] The bar shows completion badges where applicable (e.g., "4/4", "3/6")
- [x] Phases with no prerequisites met are visually dimmed but still clickable (not hard-blocked)

### AI Graph Reading (Chat Integration)
- [x] The chat AI can read the pipeline graph via a tool call
- [x] When a user asks "what should I do next?", the AI reasons about available nodes and recommends next steps (Story 086)
- [x] When a user triggers a downstream action with missing upstream, the AI can explain what's missing using the graph (Story 086)

### Testing
- [x] Unit tests for graph construction from artifact store state
- [x] Unit tests for node status computation (available/blocked/completed/stale)
- [x] API endpoint returns correct graph for a project with partial pipeline completion
- [x] Frontend renders pipeline bar with correct status indicators

## Out of Scope
- Full DAG visualization (Layer 3 in ADR-002 — future story)
- Persona-adaptive workspaces (Layer 4 in ADR-002 — future story)
- Pre-flight check UI for expensive operations (future story)
- Per-feature AI autonomy levels (future story)
- Onboarding flow / persona selection (future story)

## Tasks

- [x] Task 1: Design and implement the pipeline graph schema
- [x] Task 2: Build graph computation from artifact store state
- [x] Task 3: Create API endpoint `GET /api/projects/{pid}/pipeline-graph`
- [x] Task 4: Build the pipeline bar UI component
- [x] Task 5: Wire pipeline bar into the app shell
- [x] Task 6: Add AI graph-reading tool to the chat system
- [x] Task 7: Tests (backend + frontend)
- [x] Task 8: Runtime smoke test
- [x] Task 9: Update docs

## Plan

### Exploration Findings

**Backend:**
- `ArtifactStore` has `list_versions(type, entity_id)` and `list_entities(type)` for querying what exists. Health tracked via `ArtifactHealth` enum (valid/stale/needs_review/etc.) in the dependency graph (`graph/dependency_graph.json`).
- 25+ artifact types registered in schema registry. 15 modules across 5 stage groups (ingest, world_building, creative_direction, timeline, test).
- Cross-recipe chaining via `store_inputs` — recipes resolve latest valid artifact from store.
- Service layer: `OperatorConsoleService` is the facade. API pattern: `@app.get("/api/projects/{pid}/...")` → service method → return dict.
- Chat tools: dicts in `READ_TOOLS` list; `execute_tool()` dispatch. Adding a new tool = 3 steps (define dict, add execution branch, done).
- Existing `get_project_state` tool already provides artifact overview but no dependency/status reasoning.

**Frontend:**
- AppShell: sidebar (left, w-56) + main content (center, flex-1) + right panel (chat/inspector). NO bottom bar exists.
- Natural insertion point for pipeline bar: last child of `<main>`, below the content area, with `shrink-0`.
- Existing status indicators: `RunProgressCard` in chat (per-run stage checklist), `ProcessingView` on home page only. Nothing persistent or global.
- `useProjectState` hook already computes: `'empty' | 'fresh_import' | 'processing' | 'analyzed' | 'complete'`.
- `useArtifactGroups` returns `{artifact_type, entity_id, latest_version, health}` per artifact. Can be repurposed to compute node status.
- Data fetching pattern: `api.ts` fetch wrapper + `hooks.ts` React Query hooks. Standard.
- Status color patterns: green (completed), blue (running), amber (paused/stale), red (failed), muted (pending).

**Files that will change:**
- NEW: `src/cine_forge/pipeline/graph.py` — graph definition + status computation
- MODIFY: `src/cine_forge/api/service.py` — new `get_pipeline_graph()` method
- MODIFY: `src/cine_forge/api/app.py` — new endpoint
- MODIFY: `src/cine_forge/ai/chat.py` — new `read_pipeline_graph` tool
- NEW: `ui/src/components/PipelineBar.tsx` — the bar component
- MODIFY: `ui/src/components/AppShell.tsx` — mount the bar
- MODIFY: `ui/src/lib/api.ts` — new API function
- MODIFY: `ui/src/lib/hooks.ts` — new hook
- NEW: `tests/unit/test_pipeline_graph.py`

**Files at risk of breaking:** None — this is additive. No existing functionality changes.

### Architecture

**The graph has two levels:**

1. **Nodes** — individual pipeline capabilities (script_import, scene_extraction, character_bibles, editorial_direction, etc.). Each maps to one or more artifact types and has dependencies on other nodes.
2. **Phases** — user-facing groups of related nodes (Script, World, Direction, Shots, etc.). The pipeline bar shows phases; the AI and future DAG view use nodes.

**Graph structure is STATIC** (defined in code, same for all projects). **Node status is DYNAMIC** (computed from artifact store at query time). This means:
- The graph definition is a module constant — no per-project graph files
- Status computation queries the artifact store for what exists and what's stale
- Future unimplemented stages are included in the definition with `implemented: false` — they show as dimmed "coming soon" segments in the bar

**Six user-facing phases:**

| Phase | Nodes | Status = completed when... | Nav target |
|---|---|---|---|
| **Script** | script_import, normalization, scene_extraction, project_config | `scene_index` exists and valid | `/` (script page) |
| **World** | entity_discovery, characters, locations, props, entity_graph, continuity | All three bible types have entries | `/characters` |
| **Direction** | editorial_direction, visual_direction*, sound_direction* | `editorial_direction_index` exists | Scene direction tabs |
| **Shots** | shot_planning*, coverage* | Not implemented yet | — |
| **Storyboards** | storyboard_gen*, animatics* | Not implemented yet | — |
| **Production** | render*, final_output* | Not implemented yet | — |

*Future/unimplemented nodes

**Node status enum:**
- `completed` — output artifact(s) exist and are valid
- `stale` — artifacts exist but marked stale (upstream changed)
- `in_progress` — active run is processing this stage
- `available` — all upstream dependencies met, no output yet
- `blocked` — upstream dependencies not met
- `not_implemented` — module doesn't exist yet

**Phase status** derived from its nodes: completed if all implemented nodes are completed, partial if some are, available if upstream phases allow it, blocked otherwise.

### Task Details

**Task 1: Pipeline graph schema + definition** (`src/cine_forge/pipeline/graph.py`)
- Define `PipelineNode` dataclass: `id, label, phase_id, icon, artifact_types: list[str], entity_type: str | None, dependencies: list[str], nav_route: str | None, implemented: bool`
- Define `PipelinePhase` dataclass: `id, label, icon, node_ids: list[str], nav_route: str | None`
- Define `NodeStatus` enum: `completed, stale, in_progress, available, blocked, not_implemented`
- Define `PhaseStatus` enum: `completed, partial, available, blocked, not_started`
- Define `PIPELINE_NODES: list[PipelineNode]` and `PIPELINE_PHASES: list[PipelinePhase]` as module constants covering the full CineForge pipeline (current + future stages)
- Done when: importing `PIPELINE_NODES` gives a valid graph definition

**Task 2: Graph status computation** (`src/cine_forge/pipeline/graph.py`)
- Function `compute_pipeline_graph(store: ArtifactStore, active_run_stages: set[str] | None = None) -> dict`
- For each node: query `store.list_entities(artifact_type)` or `store.list_versions(artifact_type, "__project__")` to check existence
- For each node: check dependency graph health for staleness
- If `active_run_stages` provided: nodes matching active stages get `in_progress`
- Derive phase status from node statuses
- Include completion metrics: `artifact_count` (e.g., 5 characters found) and `artifact_total` where knowable (e.g., 5/5 characters have bibles)
- Return serializable dict: `{phases: [...], nodes: [...], edges: [...]}`
- Done when: given a real project's ArtifactStore, function returns correct status for all nodes

**Task 3: API endpoint** (`service.py` + `app.py`)
- `OperatorConsoleService.get_pipeline_graph(project_id) -> dict`
- Instantiates `ArtifactStore`, optionally checks for active run, calls `compute_pipeline_graph()`
- `GET /api/projects/{project_id}/pipeline-graph` → calls service method
- Done when: `curl localhost:8000/api/projects/the-mariner/pipeline-graph` returns the graph with correct statuses

**Task 4: Pipeline bar component** (`ui/src/components/PipelineBar.tsx`)
- Horizontal bar, ~48px tall, dark background with subtle top border
- Six phase segments: icon + label + status dot + optional completion badge
- Status colors: green (completed), blue-pulse (in_progress), white outline (available/partial), dimmed (blocked/not_implemented)
- Completed phases show a check icon; partial phases show a progress indicator; future phases show a lock icon
- Clicking a segment navigates via `useNavigate()` to the phase's nav route
- Tooltip on hover: shows node-level detail (e.g., "Characters: 12/12 ✓, Locations: 5/5 ✓, Props: 3/3 ✓")
- Responsive: labels hidden on narrow screens, icons only
- Done when: component renders with mock data

**Task 5: Wire into app shell** (`AppShell.tsx` + `api.ts` + `hooks.ts`)
- New API function: `getPipelineGraph(projectId) -> PipelineGraphResponse`
- New hook: `usePipelineGraph(projectId)` — polls at 2s while `activeRunId` is set, 30s otherwise
- Add `<PipelineBar>` as last child of `<main>` in AppShell, below content area
- Pass graph data + project ID + navigate function
- Bar renders on all project-scoped pages (it's in AppShell, which wraps all project routes)
- Done when: bar appears at bottom of app, updates when artifacts are created

**Task 6: AI graph-reading tool** (`chat.py`)
- Add `read_pipeline_graph` to `READ_TOOLS`: no inputs required, returns the full graph with status
- Add execution in `execute_tool()`: calls `service.get_pipeline_graph(project_id)`, returns as formatted text (phases with status, available next actions, nodes with dependencies)
- Format the output as structured natural language (not raw JSON) for LLM readability:
  ```
  Pipeline Status for "The Mariner":
  ✅ Script — complete (15 scenes, config detected)
  ✅ World — complete (12 characters, 5 locations, 3 props, relationships mapped)
  🔵 Direction — partial (editorial ✅, visual ❌, sound ❌)
  🔒 Shots — blocked (needs: visual direction, sound direction)
  🔒 Storyboards — blocked (needs: shot planning)
  🔒 Production — blocked (needs: storyboards)

  Available next actions:
  - Generate visual direction (all prerequisites met)
  - Generate sound direction (all prerequisites met)
  ```
- Done when: assistant tool call returns readable pipeline state

**Task 7: Tests**
- `tests/unit/test_pipeline_graph.py`:
  - Test node definition validity (all dependencies reference valid node IDs, no cycles)
  - Test status computation with empty store → all "available" or "blocked" appropriately
  - Test status computation with partial store (simulate: scenes exist, bibles don't) → correct available/blocked
  - Test phase status derivation from node statuses
  - Test active run detection marks nodes as "in_progress"
- Run `make test-unit PYTHON=.venv/bin/python` + `.venv/bin/python -m ruff check src/ tests/`
- Run `pnpm --dir ui run lint` + `cd ui && npx tsc -b` + `pnpm --dir ui run build`

**Task 8: Runtime smoke test**
- Start backend, hit `/api/projects/{pid}/pipeline-graph`, verify response
- Open UI, verify pipeline bar renders at bottom, check console for errors
- Verify clicking a phase segment navigates correctly
- Verify status updates when artifacts exist vs. don't

**Task 9: Update docs**
- Update AGENTS.md Repo Map if new directories added
- Update ADR-002 to reference this story as the Layer 1+2 implementation

### Impact Analysis
- **Purely additive** — no existing functionality changes
- New `src/cine_forge/pipeline/` package — init file needed
- API endpoint is read-only, no state mutations
- Pipeline bar is visual-only, no interaction side effects beyond navigation
- Chat tool is read-only

### What "done" looks like
- User opens any project page → sees pipeline bar at bottom showing where their project stands
- Completed phases are green with check marks; available phases are bright; blocked/future phases are dimmed
- Clicking a phase navigates to the relevant section
- User asks AI "what should I do next?" → AI uses the graph tool to give a grounded answer
- All checks pass, runtime verified

## Work Log

*(append-only)*

20260225 — Story created from ADR-002 decision. This is Layer 1 (Pipeline Bar) + partial Layer 2 (AI Navigator graph reading) from the four-layer architecture.

20260225-2345 — Phase 1 exploration complete. Key findings: (1) ArtifactStore has list_versions/list_entities for querying existence. (2) No bottom bar exists in AppShell — natural insertion point as last child of `<main>` with shrink-0. (3) Chat tools are plain dicts in READ_TOOLS/WRITE_TOOLS; adding a new one is 3 steps. (4) Frontend has `useProjectState` but it's coarse (5 states), need finer-grained per-node status. (5) Six user-facing phases: Script → World → Direction → Shots → Storyboards → Production. (6) Graph structure is static (defined in code); node status is dynamic (computed from artifact store). (7) Future unimplemented stages included in graph definition with `implemented: false` — renders as dimmed "coming soon" in the bar. Files to create: `src/cine_forge/pipeline/graph.py`, `ui/src/components/PipelineBar.tsx`, `tests/unit/test_pipeline_graph.py`. Files to modify: `service.py`, `app.py`, `chat.py`, `AppShell.tsx`, `api.ts`, `hooks.ts`.

20260226-0025 — Implementation complete. All 9 tasks done:

**Backend**: Created `src/cine_forge/pipeline/` package with `graph.py` containing 19 nodes across 6 phases, NodeStatus/PhaseStatus enums, static graph definition, and `compute_pipeline_graph()` function that queries ArtifactStore for dynamic status. Graph integrity validated (no cycles, all refs valid). Added `get_pipeline_graph()` to OperatorConsoleService and `GET /api/projects/{pid}/pipeline-graph` endpoint.

**Frontend**: Created `PipelineBar.tsx` component with phase segments showing icons, labels, status colors (green=completed, blue=partial, white=available, dimmed=blocked/unimplemented), completion badges, and tooltips with node-level detail. Wired into AppShell between header and content area. Added `usePipelineGraph` hook with 2s polling during active runs, 30s otherwise. Added types to `types.ts` and API function to `api.ts`.

**AI Tool**: Added `read_pipeline_graph` to READ_TOOLS in chat.py. Formats graph as structured natural language with emoji status icons and "Available next actions" section.

**Tests**: 21 unit tests in `test_pipeline_graph.py` covering graph integrity (unique IDs, valid deps, no cycles, phase coverage), empty store status, populated store status, bible node checking, in-progress detection, phase status derivation, and full graph computation. All pass. Full suite: 326 passed.

**Runtime verification**: Backend endpoint returns correct data for the-mariner project (Script: completed 4/4, World: partial 3/6, Direction: available, Shots/Storyboards/Production: not_started). Frontend pipeline bar renders correctly with tooltips and navigation. No console errors. Clicking "World" navigates to `/characters`.

**Remaining AC items** (deferred to future stories): AI reasoning about "what should I do next?" and downstream-missing-upstream diagnosis — these require prompt engineering in the chat system prompt, not infrastructure. The `read_pipeline_graph` tool is the foundation; the AI's reasoning quality depends on system prompt guidance which is a separate concern.
