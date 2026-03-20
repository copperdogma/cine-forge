# Story 033: Memory Model and Transcript Retention

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: spec:9 (spec:9.1, spec:9.2, spec:9.3, spec:9.4), spec:4.6 (Conversation transcripts)
**ADR Refs**: None found after search; design context: `docs/design/011f-chat-audit.md` (existing chat persistence baseline)
**Depends On**: Story 018 (inter-role communication — conversation recording), Story 014 (role system — Director working memory)

---

## Goal

Implement the full **memory model**: canonical memory (artifacts, policies, decisions, suggestions, transcripts), working memory for long-running roles (Director, optionally Script Supervisor), and the transcript retention rule. Ensure that chats are accelerators, artifacts are truth, and transcripts are permanent.

---

## Acceptance Criteria

### Canonical Memory (Spec 9.1)
- [x] All canonical memory types properly stored and queryable:
  - [x] **Artifacts**: immutable, versioned (already implemented in Story 002).
  - [x] **Policies**: project configuration, control mode.
  - [x] **Decisions**: explicit decision artifacts with audit metadata (from Story 017).
  - [x] **Suggestions**: full backlog with lifecycle status (from Story 017).
  - [x] **Conversation transcripts**: raw turn-by-turn records (from Story 018).
- [x] Canonical memory is the source of truth — roles consult it, not chat history.

### Working Memory (Spec 9.2)
- [x] Long-running chat contexts for:
  - [x] Director (required).
  - [x] Script Supervisor (optional, configurable).
- [x] Working memory capabilities:
  - [x] Maintains running context across multiple interactions.
  - [x] Periodically summarized into canonical artifacts.
  - [x] Resettable (clear working memory, start fresh).
  - [x] Summary artifacts are immutable.
- [x] Raw transcripts always retained even when working memory is summarized or reset.
- [x] Script Supervisor working memory defaults off and is controlled by project-scoped settings rather than UI-only state.

### Transcript Retention
- [x] All conversation transcripts (role-to-role, human-to-role) retained permanently.
- [x] Transcripts searchable by:
  - [x] Participant roles.
  - [x] Time range.
  - [x] Related artifacts.
  - [x] Content (full-text search).
- [x] Transcripts linked to the decisions and artifacts they produced.

### Memory Query API
- [x] Roles can query canonical memory:
  - [x] "What decisions have been made about scene X?"
  - [x] "What is the current state of character Y's bible?"
  - [x] "What suggestions are deferred for location Z?"
  - [x] "What did the Director and Visual Architect discuss about act 2?"
- [x] Query results include provenance and timestamps.
- [x] Transcript search, memory query, and working-memory reset are available through backend APIs or direct service calls without depending on frontend-only state.

### Schema
- [x] `WorkingMemorySummary` schema.
- [x] `TranscriptIndex` schema (searchable index of all transcripts).
- [x] `MemorySettings` schema for project-scoped optional working-memory controls.
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for working memory lifecycle (accumulate, summarize, reset).
- [x] Unit tests for transcript retention and search.
- [x] Unit tests for memory query API.
- [x] Integration test: role conversations → transcript storage → search → retrieval.
- [x] Schema validation on all outputs.

---

## Design Notes

### The Memory Rule (Spec 9.3)
"Chats are accelerators. Artifacts are truth. Transcripts are permanent."

This means:
- Roles should not rely on chat history for decision-making — they should consult artifacts.
- Working memory (chat context) is a performance optimization, not a source of truth.
- If working memory is lost (summarized, reset, context limit hit), no information is permanently lost — it's all in transcripts and artifacts.

### Storage Considerations
Transcripts will accumulate significantly over a project's lifetime. For MVP, file-based storage is fine. For larger projects, consider indexing with SQLite or similar for search performance.

### Context Window Summarization Reference
Storybook Story 006 (commit f42fb55) implements a clean `trimHistoryIfNeeded()` pattern for AI conversations:
- Threshold: 100k chars (char-based, not token-based — avoids tokenizer dependency)
- When exceeded: summarize oldest 50% via a single LLM call (Haiku — cheap, fast)
- Summary is a factual digest, not interpretive — "just facts, people, events, dates, locations"
- Full history preserved in DB; only the active LLM context is trimmed
- User never sees the summary; AI continuity is maintained

This is directly applicable to CineForge's working memory summarization task above. Reference: `/Users/cam/Documents/Projects/Storybook/storybook/src/lib/summarize-context.ts`

---

## Tasks

- [x] Implement canonical memory query interface.
- [x] Implement working memory for Director role.
- [x] Implement working memory summarization (periodic → canonical artifact).
- [x] Implement working memory reset with transcript preservation.
- [x] Implement transcript indexing and search.
- [x] Implement memory query API for roles.
- [x] Implement headless memory APIs for transcript search, memory query, and working-memory reset/settings.
- [x] Design and implement `WorkingMemorySummary`, `TranscriptIndex` schemas.
- [x] Register schemas in schema registry.
- [x] Write unit tests.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

---

## Central Tenets Check

- [x] **Tenet 0 — Preserve user data / capture-first**: Raw transcripts and summaries remain immutable and reset never destroys source history.
- [x] **Tenet 1 — AI-friendly architecture**: Memory query/search contracts are schema-first and obvious to future agents.
- [x] **Tenet 2 — Avoid over-engineering**: Reuse existing transcript stores and artifact metadata instead of adding a new database prematurely.
- [x] **Tenet 3 — Keep files manageable / types centralized**: New memory logic lives in focused schema/service/router files, not inside oversized general modules.
- [x] **Tenet 4 — Verbose handoff log**: Work log records exploration, implementation, verification, and any remaining gaps.
- [x] **Tenet 5 — Simplify toward ideal**: The memory layer moves CineForge toward durable collaboration while keeping AI-capability compromises explicit.

---

## Plan

### Eval / Baseline

- Success will be measured by deterministic unit/integration tests covering:
  - transcript indexing/search across `chat.jsonl` plus `conversation` artifacts
  - working-memory summary lifecycle (summarize, reuse, reset)
  - headless memory query/reset endpoints and role-side query access
- Current baseline: there are no Story 033-specific tests yet, and the existing chat/conversation baseline could not be run in this worktree because `.venv` is absent and system `python3` does not have `pytest`.

### Repo-Fit / Chosen Approach

- Choose a **pure code, schema-first** implementation. This story is storage/query/orchestration work, not a model-selection problem. The missing gap is durable memory artifacts, deterministic search/query, and reset semantics.
- Reuse the repo's existing transcript sources:
  - `chat.jsonl` for human-to-role chat (`docs/design/011f-chat-audit.md`)
  - immutable `conversation` artifacts from Story 018 for inter-role transcripts
  - existing `decision`, `suggestion`, and latest artifact snapshots for canonical memory answers
- Rejected alternatives:
  - **LLM-mediated memory query**: worse for trust and provenance; deterministic retrieval is the correct default here.
  - **New database/search subsystem**: premature for current repo scale; file-backed index artifacts plus focused service logic are enough.
  - **More inline logic in `ai/chat.py` or `api/app.py`**: both files are already oversized and should only get thin integration points.

### Structural Health Check

- `src/cine_forge/ai/chat.py` — 2243 lines, oversized. Keep edits to thin integration points and move memory logic into a new focused service/helper.
- `src/cine_forge/api/app.py` — 1045 lines, oversized. Only add router import/setup; put endpoint logic in a new router module.
- `src/cine_forge/api/service.py` — 1090 lines, oversized. Avoid adding memory business logic here; use it only for project-path resolution if needed.
- `src/cine_forge/roles/runtime.py` — 471 lines. Keep any new memory hook narrow (`query_memory` delegation only).
- `src/cine_forge/api/models.py` — 480 lines. Prefer dedicated memory schemas and a focused router to avoid further generic API-model bloat unless a shared request/response model is clearly cleaner.
- `src/cine_forge/driver/schema_registry.py` — 116 lines.
- `src/cine_forge/api/chat_store.py` — 89 lines.
- `src/cine_forge/schemas/conversation.py` — 50 lines.
- New cross-layer memory contracts must land in a schema file before service/API code uses them.

### Task 1 — Schema-First Memory Substrate

Files:
- `src/cine_forge/schemas/memory.py` (new)
- `src/cine_forge/schemas/__init__.py`
- `src/cine_forge/driver/schema_registry.py`

Changes:
- Add typed models for `TranscriptIndex`, `TranscriptIndexEntry`, `WorkingMemorySummary`, query filters/results, and project-scoped `MemorySettings`.
- Register any new artifact types so transcript indexes and working-memory summaries remain first-class immutable artifacts.

Done looks like:
- Schemas validate, export cleanly, and have focused unit coverage.

### Task 2 — Memory Service and Canonical Query Path

Files:
- `src/cine_forge/services/memory.py` (new)
- `src/cine_forge/roles/runtime.py`
- `src/cine_forge/api/chat_store.py` only if a tiny helper is needed

Changes:
- Build a focused service that reads `chat.jsonl`, `conversation` artifacts, and latest canonical artifacts to:
  - materialize transcript-index snapshots
  - search by participant, time range, related artifact, and text
  - answer deterministic canonical-memory queries with provenance/timestamps
  - expose a narrow `RoleContext.query_memory(...)` hook for backend role use
- Infer related-artifact links from existing transcript context (`conversation.related_artifacts`, chat `pageContext`) instead of inventing a third transcript store.

Done looks like:
- Query/search works without frontend-only state and role-side access is testable.

### Task 3 — Working-Memory Lifecycle for Long-Running Chat

Files:
- `src/cine_forge/services/memory.py` (new)
- `src/cine_forge/ai/chat.py`

Changes:
- Replace ad hoc in-memory-only compaction with service-managed working-memory summaries for `director`, plus optional `script_supervisor`.
- Persist summaries as immutable artifacts and keep raw transcript sources untouched.
- Add reset semantics that create a new checkpoint instead of mutating prior summaries.

Done looks like:
- Repeated long chats reuse persisted summaries, resets start fresh, and raw chat history remains intact.

### Task 4 — Headless API Surface

Files:
- `src/cine_forge/api/routers/memory.py` (new)
- `src/cine_forge/api/app.py`
- `src/cine_forge/api/models.py` only if shared request/response models are clearly worth the extra line count

Changes:
- Add transcript-search and canonical-memory query endpoints plus a reset/settings endpoint for working memory.
- Keep the router thin and avoid new memory logic in `api/app.py` or `api/service.py`.
- Store optional Script Supervisor enablement as project-scoped configuration, default off.

Done looks like:
- Operators or agents can inspect/query/reset memory through backend calls alone.

### Task 5 — Tests, Docs, and Redundancy

Files:
- `tests/unit/test_memory_service.py` (new)
- `tests/unit/test_chat_memory.py` (new)
- `tests/integration/test_api_memory.py` (new)
- `docs/stories/story-033-memory-model.md`

Changes:
- Add focused tests instead of enlarging `tests/unit/test_api.py`.
- Update the story log/checklists with actual evidence and any follow-up.
- Remove or minimize duplicate compaction state once the memory service owns working-memory behavior.

Done looks like:
- Targeted tests cover indexing, search, summary lifecycle, reset, and API behavior, and docs reflect the landed path.

### Risks / Scope Notes

- The story's current spec refs were still using pre-ADR numbering; this plan updates them now so later validation is unambiguous.
- Human-chat related-artifact linkage is currently best-effort via `pageContext`. If that proves too weak during implementation, the smallest coherent scope expansion is adding structured related-artifact refs to persisted chat messages.
- Local Python validation is currently blocked until a test environment exists: `.venv` is absent and system `python3` lacks `pytest`.

### Redundancy Plan

- Do not create a third transcript store.
- If the new memory service fully owns compaction, remove or minimize `ai/chat.py`'s local summary-cache logic instead of keeping two working-memory mechanisms alive.

### Human-Approval Blockers

- No architectural blocker found.
- Practical blocker only: if the worktree stays without a Python test environment, implementation will need a dependency bootstrap step before required checks can pass.

---

## Work Log

*(append-only)*

20260320-1634 — exploration: confirmed Story 033 still targets the live `spec:9` climb and is the clean continuation of existing transcript infrastructure. Read `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, Story 014, Story 018, `docs/design/011f-chat-audit.md`, and the current code paths in `src/cine_forge/api/chat_store.py`, `src/cine_forge/schemas/conversation.py`, `src/cine_forge/roles/communication.py`, `src/cine_forge/roles/runtime.py`, `src/cine_forge/ai/chat.py`, `src/cine_forge/api/app.py`, and `src/cine_forge/api/service.py`. Existing transcript sources are `chat.jsonl` plus immutable `conversation` artifacts; ad hoc working-memory compaction currently lives only in `src/cine_forge/ai/chat.py`. Likely change set is a new memory schema/service/router with thin integrations into `ai/chat.py`, `roles/runtime.py`, `api/app.py`, and the schema registry. Risk files are `src/cine_forge/ai/chat.py` (2243 lines), `src/cine_forge/api/app.py` (1045), and `src/cine_forge/api/service.py` (1090), so the plan explicitly avoids stuffing new logic there. Baseline validation is currently environment-blocked: `.venv` is absent and system `python3` lacks `pytest`. Redundancy target: the current in-memory-only transcript compaction path if the new memory service supersedes it. Next step: human plan approval before implementation.
20260320-1704 — implementation: added `src/cine_forge/schemas/memory.py` plus schema-registry exports for `transcript_index` and `working_memory_summary`; built `src/cine_forge/services/memory.py` and `src/cine_forge/services/memory_support.py` to index `chat.jsonl` + immutable `conversation` artifacts, answer deterministic canonical-memory queries with provenance, persist/reset working-memory summaries, and keep Script Supervisor memory project-scoped in `project.json`. Added role-side access via `RoleContext.query_memory(...)`, headless APIs in `src/cine_forge/api/routers/memory.py`, thin app wiring in `src/cine_forge/api/app.py`, and chat integration in `src/cine_forge/ai/chat.py` so Director (and optional Script Supervisor) reuse persisted working-memory summaries before falling back to ephemeral compaction. Also made `src/cine_forge/api/__init__.py` lazy after a real import-cycle surfaced during repo-wide unit collection. Next step: run the required checks and runtime smoke, then hand off to `/validate`.
20260320-1704 — verification: targeted tests passed (`tests/unit/test_memory_service.py`, `tests/unit/test_chat_memory.py`, `tests/integration/test_api_memory.py`, `tests/unit/test_schema_registry.py`: 17 passed); repo-wide unit suite passed via `make test-unit PYTHON=.venv/bin/python` (609 passed, 140 deselected, 1 existing acceptance-mark warning); touched-file Ruff passed via `.venv/bin/python -m ruff check ...`; backend smoke passed with a real uvicorn process (`GET /api/health` returned `{"status":"ok","version":"2026.03.20-05"}` and live `GET`/`PATCH` calls to `/api/projects/cineforge-memory-smoke.9nZ9vW/memory/settings` returned 200 with the expected payloads). `make lint PYTHON=.venv/bin/python` still fails, but the remaining failures are pre-existing repo-wide lint debt outside Story 033 (`.agents/skills/webapp-testing/scripts/with_server.py`, benchmark scorers, `scripts/check-compromises.py`, `scripts/discover-models.py`, `scripts/reset_playwright_mcp.py`). Touched files are lint-clean. Next step: `/validate` should confirm the story is clean aside from that unrelated repo lint debt and decide whether it is runtime-blocking.
20260320-1736 — validation: reran the required validation suite. `make test-unit PYTHON=.venv/bin/python` passed (609 passed, 140 deselected, 1 existing acceptance-mark warning), `.venv/bin/python -m ruff check src/ tests/` passed, targeted Story 033 pytest passed (17 passed), `pnpm --dir ui run lint` passed with 5 pre-existing `react-refresh/only-export-components` warnings, and `npx --prefix ui tsc -b ui/tsconfig.json` passed after installing the checked-in UI lockfile dependencies. Browser verification was not required because no UI files changed. Validation found two remaining acceptance gaps: human chat transcript entries are only linked via `pageContext`, so searches by produced `decision`/`suggestion` artifacts still miss human-to-role turns; and artifact-state answers currently return generic field lists (for example `Latest bible_manifest/character_mariner is version 1 with fields: ...`) rather than substantive current-state summaries. Story remains open. Next step: fix those two gaps, extend tests to cover them, then rerun `/validate`.
20260320-1812 — follow-up implementation: fixed the two validation gaps in the memory layer. `src/cine_forge/services/memory.py` now resolves prefixed entity IDs onto the substantive bible artifacts, summarizes character/location/prop/scene state with meaningful content instead of field introspection, and broadens decision/suggestion transcript filters to include structurally related chat turns. `src/cine_forge/services/memory_support.py` and `src/cine_forge/api/models.py` now support structured persisted chat refs (`relatedArtifacts`, `decisionIds`, `suggestionIds`) so human chat can carry explicit outcome links when available. Evidence: targeted Story 033 pytest now passes with the expanded cases (`18 passed`), `.venv/bin/python -m ruff check src/ tests/` passes, and the full unit suite passes via `make test-unit PYTHON=.venv/bin/python` (`610 passed, 140 deselected, 1 existing acceptance-mark warning`). Next step: rerun `/validate` and, if clean, move to `/mark-story-done`.
20260320-1828 — validation: reran the full required suite after the follow-up fixes. `make test-unit PYTHON=.venv/bin/python` passed (`610 passed, 140 deselected, 1` existing acceptance-mark warning), `.venv/bin/python -m ruff check src/ tests/` passed, targeted Story 033 pytest passed (`18 passed`), `pnpm --dir ui run lint` passed with the same 5 pre-existing `react-refresh/only-export-components` warnings, and `npx --prefix ui tsc -b ui/tsconfig.json` passed. Browser verification remained unnecessary because no UI files changed. The previously open acceptance gaps are now covered by code and tests. Structural note: `src/cine_forge/services/memory.py` is now 727 lines; if future story work touches it, first extract transcript filtering / artifact-state formatting collaborators rather than continuing to grow the class. Current validation treats that as a documented follow-up, not a correctness blocker, because behavior is covered at the service/API boundary and the logic is already partially split into `memory_support.py`, dedicated schemas, and a thin API router. Next step: `/mark-story-done`.
20260320-1850 — closure: marked Story 033 done after confirming all acceptance criteria and tasks are complete, workflow gates are satisfied, and the required close-out suite remains green (`make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, targeted Story 033 pytest, `pnpm --dir ui run lint`, `npx --prefix ui tsc -b ui/tsconfig.json`). Alignment check: this work advances `docs/ideal.md` and `spec:9` / `spec:4.6` by formalizing durable collaboration memory on top of the existing chat-persistence baseline in `docs/design/011f-chat-audit.md`; no governing ADR was found after searching `docs/decisions/` and `docs/design/`. Next step: `/check-in-diff`.
