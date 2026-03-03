# Story 118 — Service Layer Decomposition

**Priority**: Medium
**Status**: Pending
**Spec Refs**: None (architecture quality — enables every Ideal requirement)
**Depends On**: Story 116 (Event System Refactor — clean events before service refactor)

## Goal

`OperatorConsoleService` in `src/cine_forge/api/service.py` has grown to 1,775 lines across 11 distinct responsibility clusters. It acts as a god object: project lifecycle, run orchestration, chat persistence, artifact browsing, search, and more all live in one class with shared mutable state. Three confirmed bugs live in it today: a chat race condition (no lock on upsert path), an orphan-detection fix that never persists to disk, and a hardcoded project path in the export router that breaks for external projects. This story decomposes the god object into focused service classes, fixes all three bugs, and introduces a `RuntimeParams` Pydantic model to replace the stringly-typed `dict` that flows between the service and the engine. The result is a `OperatorConsoleService` facade of ≤ 800 lines that delegates to collaborators — easier to test, reason about, and extend.

## Acceptance Criteria

- [ ] `ChatStore` class extracted to `src/cine_forge/api/chat_store.py` with a `threading.Lock` protecting the upsert path — concurrent writes cannot drop messages
- [ ] `ChatStore.upsert_message()` is idempotent: calling it twice with the same message id produces one entry, not two
- [ ] Export router `get_store()` uses `service.require_project_path()` instead of hardcoded `Path(f"output/{project_id}")` — external projects and non-CWD launches work correctly
- [ ] `RunOrchestrator` class extracted to `src/cine_forge/api/run_orchestrator.py` and owns `_run_threads`, `_run_errors`, `_run_lock` — no run state scattered in `OperatorConsoleService`
- [ ] `RuntimeParams(BaseModel)` defined in `src/cine_forge/schemas/runtime_params.py` with all 15 keys typed; `__resume_artifact_refs_by_stage` is a proper typed field (not a magic string key)
- [ ] Orphan detection (`read_run_state`) writes the mutated state back to `run_state.json` after marking stages as failed — the file no longer permanently shows "running" for orphaned runs
- [ ] `OperatorConsoleService` is ≤ 800 lines after extraction (thin facade pattern)
- [ ] All intent/mood routes in `app.py` that currently construct `ArtifactStore` directly are consolidated into service method calls
- [ ] All existing API tests pass without modification to test code
- [ ] New unit tests cover: `ChatStore` upsert, idempotency, and concurrent writes; orphan persistence; `RuntimeParams` field validation

## Out of Scope

- `ProjectRegistry` extraction — the cluster works correctly today; decomposition would be for readability only. Deferred.
- `ProjectSearcher` extraction — single method, low urgency. Deferred.
- Recipe management extraction — trivial pass-through, not worth a phase. Deferred.
- Changing the chat data model (JSONL format, message schema) — separate story.
- `ProjectInputManager` and `ArtifactBrowser` / `ArtifactEditor` extraction — covered in Phase 7 (if time allows) but explicitly deferrable without blocking the story.

## Approach Evaluation

- **Pure code**: Yes — this is entirely orchestration and plumbing refactoring. No AI reasoning is involved. The decomposition is driven by dependency analysis (which methods share state) and the three confirmed bugs that need fixes.
- **AI-only / Hybrid**: Not applicable. Refactoring an existing Python module boundary is a structural code task.
- **Eval**: No eval needed. Validation is: (a) all existing API tests pass, (b) new `ChatStore` concurrency test passes, (c) manual smoke test of a pipeline run and export after the refactor confirms behavior is preserved.

## Tasks

- [ ] **Phase 1 — ChatStore extraction + `_chat_lock`** (fixes race condition)
  - [ ] Create `src/cine_forge/api/chat_store.py` with `ChatStore` class
  - [ ] Move all chat persistence methods from `OperatorConsoleService` into `ChatStore`: `get_chat_messages`, `append_chat_message`, `update_chat_message`
  - [ ] Add `self._lock = threading.Lock()` to `ChatStore.__init__`
  - [ ] Wrap the upsert path in `append_chat_message` with `with self._lock:` — read-scan-replace becomes atomic
  - [ ] Instantiate `ChatStore` inside `OperatorConsoleService.__init__` and delegate all chat calls to it
  - [ ] Write `tests/unit/test_chat_store.py`: upsert correctness, idempotency on duplicate id, concurrent write safety (two threads calling upsert simultaneously)

- [ ] **Phase 2 — Export router `get_store()` fix** (production bug)
  - [ ] In `src/cine_forge/api/routers/export.py`, replace the hardcoded `Path(f"output/{project_id}")` in `get_store()` with a call to `service.require_project_path(project_id)`
  - [ ] Verify the export router receives the `service` instance (inject via FastAPI dependency or module-level reference — match the existing pattern in `app.py`)
  - [ ] Smoke test: export from a project whose directory is not under CWD

- [ ] **Phase 3 — `RuntimeParams` Pydantic model**
  - [ ] Create `src/cine_forge/schemas/runtime_params.py` with `RuntimeParams(BaseModel)` containing all 15 typed fields (see Notes for the complete key inventory)
  - [ ] `resume_artifact_refs_by_stage: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)` — replaces the `__resume_artifact_refs_by_stage` magic key
  - [ ] Update `start_run` and `resume_run` in `OperatorConsoleService` to construct a `RuntimeParams` instance and pass `.model_dump()` to the engine (backward-compatible handoff for now — engine still receives a dict)
  - [ ] Write `tests/unit/test_runtime_params.py`: required field presence, optional field defaults, round-trip `model_dump()` preserves types

- [ ] **Phase 4 — Orphan detection persistence fix**
  - [ ] In `OperatorConsoleService.read_run_state` (lines 1695–1707), after mutating stage statuses to `"failed"` for orphaned runs, write the updated `run_state` dict back to `run_state.json`
  - [ ] Add a unit test (in the existing run state test file or a new one) that confirms the file on disk reflects `"failed"` after `read_run_state` detects an orphan

- [ ] **Phase 5 — `RunOrchestrator` extraction**
  - [ ] Create `src/cine_forge/api/run_orchestrator.py` with `RunOrchestrator` class
  - [ ] Move `_run_threads: dict`, `_run_errors: dict`, `_run_lock: threading.Lock` into `RunOrchestrator.__init__`
  - [ ] Move run lifecycle methods into `RunOrchestrator`: `start_run`, `resume_run`, `retry_run`, `cancel_run`, `_execute_run_thread`, `_preload_upstream_reuse`, `resolve_runtime_params`
  - [ ] Instantiate `RunOrchestrator` inside `OperatorConsoleService.__init__` and delegate
  - [ ] `RunOrchestrator` receives the `ArtifactStore` factory and `ChatStore` instance in its constructor — no hidden global state
  - [ ] Confirm all existing run lifecycle tests pass unchanged

- [ ] **Phase 6 — Intent/mood route consolidation**
  - [ ] For each of the 5 `app.py` routes that construct `ArtifactStore` directly (`GET /intent-mood`, `POST /intent-mood`, `POST /intent-mood/propagate`, `GET /script-context`, `POST /intent-mood/suggest`), extract the artifact I/O logic into a corresponding service method on `OperatorConsoleService`
  - [ ] Routes become thin: validate input, call service method, return response
  - [ ] The inline LLM call in `POST /intent-mood/suggest` moves into the service method (still calls `call_llm` directly — no module abstraction needed here)
  - [ ] Confirm intent/mood UI flows work end-to-end after consolidation (browser smoke test)

- [ ] **Phase 7 — `ArtifactBrowser` + `ArtifactEditor` extraction** (deferrable)
  - [ ] Create `src/cine_forge/api/artifact_browser.py` with `ArtifactBrowser` class — move `list_artifacts`, `get_artifact`, `get_artifact_raw` into it
  - [ ] Create `src/cine_forge/api/artifact_editor.py` with `ArtifactEditor` class — move `update_artifact_field`, `revert_artifact` into it
  - [ ] Delegate from `OperatorConsoleService`
  - [ ] Confirm existing artifact browse/edit tests pass unchanged

- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [ ] Search all docs and update any related to what we touched
- [ ] Runtime smoke test (browser): Start dev servers, open the UI in Chrome via browser tools, upload the toy script, trigger a pipeline run, and visually confirm: (a) the run starts and progress updates appear, (b) stage cards tick through started → finished, (c) no JS console errors, (d) the run completes successfully. Then verify chat and export flows still work — these touch the decomposed service classes directly.
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `src/cine_forge/api/service.py` — extract classes, slim to ≤ 800-line facade
- `src/cine_forge/api/chat_store.py` — NEW: `ChatStore` with `threading.Lock`
- `src/cine_forge/api/run_orchestrator.py` — NEW: `RunOrchestrator` owns run lifecycle
- `src/cine_forge/schemas/runtime_params.py` — NEW: `RuntimeParams(BaseModel)` with 15 typed fields
- `src/cine_forge/api/routers/export.py` — fix `get_store()` hardcoded path
- `src/cine_forge/api/app.py` — consolidate intent/mood routes into service method calls
- `tests/unit/test_chat_store.py` — NEW: upsert, idempotency, concurrent writes
- `tests/unit/test_runtime_params.py` — NEW: field validation, round-trip

## Notes

### Export Router Production Bug (Phase 2)

`src/cine_forge/api/routers/export.py` contains:

```python
def get_store(project_id: str) -> ArtifactStore:
    return ArtifactStore(Path(f"output/{project_id}"))
```

This hardcodes the artifact store path relative to the process CWD. It breaks in two confirmed scenarios:

1. **External projects**: any project whose `project_dir` is outside `output/` (e.g., a project opened from an arbitrary filesystem path) silently resolves to the wrong directory. The export appears to succeed but produces empty or wrong artifacts.
2. **Non-CWD launches**: when the API server is started from a directory other than the workspace root (e.g., `uvicorn cine_forge.api.app:app` from `src/`), the relative path resolves incorrectly.

The fix is one line: replace `Path(f"output/{project_id}")` with `service.require_project_path(project_id)`, which already correctly resolves project directories from the registered project registry.

### Chat Race Condition (Phase 1)

`append_chat_message` has two code paths depending on whether the message id already exists in the chat file:

- **Append path** (new message): opens the file in append mode (`"a"`). OS-level atomicity for small writes makes this safe under concurrent access.
- **Upsert path** (existing message id): reads the entire file, scans line-by-line for a matching id, replaces the matching line, then writes the entire file back. This is a read-modify-write cycle with no lock. If a background thread (e.g., run failure notification) and an HTTP handler (e.g., user sending a message) both enter the upsert path simultaneously, one write silently overwrites the other, dropping a message.

The fix: add `self._lock = threading.Lock()` to `ChatStore.__init__` and wrap the entire upsert path with `with self._lock:`. The append path is already safe and does not need the lock.

### Orphan Detection Bug (Phase 4)

`read_run_state` (around lines 1695–1707) detects runs that are still marked `"running"` but whose thread is no longer alive — i.e., the process was killed mid-run. It correctly mutates the in-memory dict to set stage statuses to `"failed"`. But it never writes the mutated dict back to `run_state.json`. On every subsequent API call that triggers `read_run_state`, the file is re-read from disk (still showing `"running"`), re-detected as orphaned, and re-mutated in memory. The file permanently shows the run as `"running"` to any external observer (CLI, other API processes, tests). Fix: call `json.dump(run_state, ...)` into `run_state.json` after the mutation, before returning.

### RuntimeParams Key Inventory (Phase 3)

All 15 keys that currently flow through the `runtime_params` dict between service and engine:

| Field | Type | Required | Purpose |
|---|---|---|---|
| `input_file` | `str` | Yes | Path to source script |
| `default_model` | `str` | Yes | Base model for all stages |
| `model` | `str` | Yes | Alias for `default_model` (substitution target) |
| `utility_model` | `str` | Yes | Mid-tier model |
| `sota_model` | `str` | Yes | Top-tier model |
| `work_model` | `str \| None` | No | Work-tier model |
| `verify_model` | `str \| None` | No | QA model (alias: `qa_model`) |
| `qa_model` | `str \| None` | No | QA model (alias: `verify_model`) |
| `escalate_model` | `str \| None` | No | Escalation model for retries |
| `human_control_mode` | `str` | Yes | Canon review gating (`"off"`, `"review"`, `"approve"`) |
| `accept_config` | `bool` | No | Skip config confirmation stage |
| `skip_qa` | `bool` | No | Skip QA stages |
| `config_file` | `str \| None` | No | Path to config overrides YAML |
| `user_approved` | `bool` | No | Human approved a pending review |
| `style_packs` | `dict[str, str]` | No | Role → style pack selections |
| `resume_artifact_refs_by_stage` | `dict[str, list[dict[str, Any]]]` | No | Replaces `__resume_artifact_refs_by_stage` magic key — upstream artifact refs for run continuity |

### Responsibility Cluster Reference

For the implementer's orientation — all 11 clusters audited from the current 1,775-line `service.py`:

| Cluster | Methods (approx.) | This Story |
|---|---|---|
| A: Project Registry & Discovery | 19 methods, ~350 lines | Out of scope (deferred) |
| B: Input File Management | 4 methods, ~60 lines | Out of scope (deferred) |
| C: Role Management | 2 methods, ~20 lines | Out of scope (thin wrappers, trivial) |
| D: Run Management | 11 methods, ~450 lines | Phase 5 → `RunOrchestrator` |
| E: Artifact Browsing | 3 methods, ~135 lines | Phase 7 → `ArtifactBrowser` (deferrable) |
| F: Artifact Editing | 2 methods, ~95 lines | Phase 7 → `ArtifactEditor` (deferrable) |
| G: Chat Persistence | 3 methods, ~75 lines | Phase 1 → `ChatStore` |
| H: Review/Approval | 1 method, ~45 lines | Stays in facade (borderline) |
| I: Search | 1 method + helpers, ~140 lines | Out of scope (deferred) |
| J: Recipe Management | 1 method, ~40 lines | Out of scope (free function, trivial) |
| K: Pipeline Graph | 1 method, ~25 lines | Out of scope (thin pass-through) |

### Testing Coverage Gaps

The audit identified which clusters currently lack test coverage. New tests in this story address the highest-risk gaps:

- **Covered by existing tests**: project lifecycle, uploads, artifact browse, run start/polling, retry, search, artifact edit
- **Not covered (adding tests this story)**: `ChatStore` concurrency, orphan detection persistence, `RuntimeParams` validation
- **Not covered (deferred)**: `resume_run`, `respond_to_review`, export router paths, intent/mood routes

## Plan

{Written by build-story Phase 2}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
