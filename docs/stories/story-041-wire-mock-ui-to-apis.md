# Story 041 — Wire Mock UI to Real APIs

**Phase**: 2.5 — UI
**Priority**: Medium
**Status**: Draft
**Depends on**: Story 011d (Operator Console Build — Done), Story 011e (UX Golden Path — In Progress)

## Goal

Two objectives:

1. **Replace all hard-coded mock data** in the Operator Console with real backend APIs. The UI was scaffolded in Story 011d with intentional mock data stubs — this story closes that debt.

2. **Unify the command palette.** The current UI has three overlapping surfaces — GlobalSearch (`/`), CommandPalette (`Cmd+K`), and KeyboardShortcutsHelp (`?`) — doing one job across three components. Merge them into a single Spotlight-style `/` palette that handles navigation, search, actions, and help in one place.

After this story: every data-driven component renders real project data, and the user has one consistent way to find anything.

## Context

Story 011d documented these mocks explicitly as "awaiting future backend work." The inventory below was audited directly from the codebase.

### Mock Data Inventory

| Component | File | What's Mocked | Lines |
|-----------|------|---------------|-------|
| **GlobalSearch** | `components/GlobalSearch.tsx` | 8 scenes, 6 characters, 5 locations, 4 props, 5 artifacts | 57–300 |
| **RunEventLog** | `components/RunEventLog.tsx` | 14 run events simulating full pipeline execution | 218–367 |
| **VariationalReview** | `components/VariationalReview.tsx` | 3 AI-generated variations with confidence scores | 203–249 |
| **ArtifactPreview** | `components/ArtifactPreview.tsx` | Fallback mock data for 8 artifact types | 10–111 |
| **ProjectInbox** | `pages/ProjectInbox.tsx` | 2 mock inbox items (error + review types) | 40–57 |
| **ProjectRuns** | `pages/ProjectRuns.tsx` | Inspector detail panel uses mock run shape | 23–175 |
| **ProjectRun** | `pages/ProjectRun.tsx` | 3 fallback recipes, mock run events import | 26–30, 260 |

### What's Already Real

- Run list (fetched via `useRuns()` hook)
- Recipes list (fetched via `useRecipes()` hook, fallback is safety net only)
- Stale artifact detection in Inbox (via `useArtifactGroups()`)
- Chat message persistence (server-side, added in 011e Phase 2.5)
- Artifact detail views (real data when navigated from valid artifacts)

## Scope Boundary: 011f

Story 011f (Conversational AI Chat) owns the chat AI brain — the disabled chat input in `ChatPanel.tsx` and the action-to-recipe mapping are **out of scope** for this story. This story wires data plumbing; 011f adds intelligence.

## Unified Command Palette Design

### Problem: Three Surfaces, One Job

Today the UI has:

| Surface | Trigger | Does |
|---|---|---|
| **CommandPalette** | `Cmd+K` | Navigation, actions, artifact type filters |
| **GlobalSearch** | `/` | Entity search (scenes, chars, locations, props) — all mock |
| **KeyboardShortcutsHelp** | `?` / `Cmd+/` | Lists registered keyboard shortcuts in a modal |

These overlap heavily. CommandPalette already has "Find Characters", "Find Locations" etc. GlobalSearch duplicates that with entity-level results. The shortcuts help modal is a separate component that could just be the empty state of a unified palette.

### Solution: One `/` Palette (Spotlight Model)

Merge all three into a single `<CommandPalette>` triggered by `/`:

| User types | What they see |
|---|---|
| `/` (nothing else) | **Help view**: grouped list of all available commands and shortcuts — what KeyboardShortcutsHelp shows today, plus navigation items and actions |
| `/loc` | **Fuzzy match**: "Locations" nav item + individual location entities (LAPD HQ, Wallace Corp...) |
| `/k` | Matches "K's Apartment" (location), "Officer K" (character) |
| `/new` | "New Project" action |
| `/run` | "Runs" nav item + "Start Run" action |
| `/scenes` | "Scenes" nav item + individual scene headings |

Key behaviors:
- **`Cmd+K` becomes an alias** for `/` — opens the same palette. Users coming from VS Code / Figma / etc. get their muscle memory honored.
- **`?` is removed as a standalone trigger.** The help content lives inside the palette's empty/default state. One less component, one less modal.
- **Entity results come from the search API** (Phase 1.1) — no more mock data. When no project is loaded, entity groups are hidden; only navigation and actions show.
- **Results are ranked**: exact prefix matches first, then fuzzy. Navigation/actions above entity results.
- **Shortcut hints** shown inline on navigation/action items (same as current CommandPalette).

### What Gets Deleted

- `GlobalSearch.tsx` — absorbed into unified palette
- `KeyboardShortcutsHelp.tsx` — help content becomes the palette's default view
- All mock data arrays (MOCK_SCENES, MOCK_CHARACTERS, etc.)
- The `/` shortcut registration in GlobalSearch (palette owns `/` directly)
- The `?` and `Cmd+/` shortcut registrations

### What Gets Kept/Evolved

- `CommandPalette.tsx` — becomes the single unified component, gains entity search groups
- `useShortcuts` registry — still used, but the help display moves into the palette
- `Cmd+K` binding — kept as alias
- shadcn `<CommandDialog>` — already has built-in fuzzy matching, perfect for this

## Tasks

### Phase 1 — Backend API Endpoints

- [x] **1.1 Search API**: `GET /projects/{slug}/search?q={query}` — returns scenes, characters, locations, props matching query string.
- [x] **1.2 Run Events API**: Already exists (`GET /runs/{runId}/events`). No new work needed.
- [x] **1.3 Run Detail API**: Already exists (`GET /runs/{runId}/state`). Inspector uses `useRunState()` directly.
- [x] **1.4 Inbox API**: Derived client-side from `useArtifactGroups()` + `useRuns()`. No dedicated endpoint needed.

### Phase 2 — Unified Command Palette

- [x] **2.1 Merge GlobalSearch into CommandPalette**: Entity search groups wired via `useSearch()` hook. Appear only with projectId.
- [x] **2.2 Merge KeyboardShortcutsHelp into palette default view**: Empty state shows shortcuts grouped by category.
- [x] **2.3 Unify triggers**: `/` and `Cmd+K` both open palette. `?`/`Cmd+/` removed. GlobalSearch.tsx and KeyboardShortcutsHelp.tsx dead (not imported).
- [x] **2.4 Result ranking**: Static commands always present (cmdk filters), entity results appended when query is non-empty.

### Phase 3 — Wire Remaining Mock Data

- [x] **3.1 Wire RunEventLog**: Replaced `mockRunEvents` with `useRunEvents(runId)` in ProjectRun. Added `transformBackendEvents()` adapter.
- [x] **3.2 Wire ProjectRuns inspector**: `RunInspectorContent` now takes `runId`, self-fetches via `useRunState()`. Shows real stages, costs, durations.
- [x] **3.3 Wire ProjectInbox**: Removed `mockNonStaleItems`. Error items derived from failed runs, review items from v1 bible_manifest artifacts.
- [x] **3.4 Wire ProjectRun page**: Mock events import removed. Fallback recipes kept as safety net (already wired to `useRecipes()`).
- [x] **3.5 Remove ArtifactPreview fallback**: Removed MOCK_DATA constant and all `typeof MOCK_DATA.*` casts. Component now requires real `data` prop.

### Phase 4 — Cleanup & Validation

- [x] **4.1 Delete all mock data**: Deleted `GlobalSearch.tsx`, `KeyboardShortcutsHelp.tsx`. Removed `mockRunEvents` from `RunEventLog.tsx`, `mockVariations` from `VariationalReview.tsx`, `MOCK_DATA` from `ArtifactPreview.tsx`. Zero mock/Mock/MOCK references remain in UI source.
- [x] **4.2 Unit tests for new API endpoints**: Added `test_search_returns_scenes_and_entities` and `test_search_requires_open_project` to `tests/unit/test_api.py`. Also fixed `int_ext` parsing bug (trailing dot not stripped).
- [x] **4.3 Build verification**: `npm run build` passes clean. `ruff check` passes clean. TypeScript strict mode passes.
- [ ] **4.4 Visual verification**: Requires running app with real backend + project data.

## Non-Goals

- AI-powered chat (Story 011f)
- Variation generation engine (needs a separate design — variations require multi-model runs, which is a pipeline feature, not a UI feature)
- Real-time streaming events via WebSocket/SSE (polling or static fetch is fine for now)
- Entity deduplication or smart search ranking (basic substring match is sufficient for v1)

## Acceptance Criteria

### Unified Palette
- [ ] `/` opens a single command palette that handles navigation, actions, entity search, and help
- [ ] `Cmd+K` opens the same palette (alias)
- [ ] Empty query shows available commands grouped by category with shortcut hints
- [ ] Typing filters across both commands and project entities (scenes, characters, locations, props)
- [ ] `GlobalSearch.tsx` and `KeyboardShortcutsHelp.tsx` are deleted — one component handles everything
- [ ] No `?` or `Cmd+/` standalone shortcut — help lives inside the palette

### Real Data
- [ ] Entity search in the palette returns real scenes, characters, locations, and props for an analyzed project
- [ ] Run event log shows actual stage timing, AI calls, and artifacts from a real pipeline run
- [ ] Run inspector panel shows real stage details (status, duration, cost, model)
- [ ] Inbox shows real errors and review items from recent runs (not just stale artifacts)

### Cleanup
- [ ] No `mock`, `Mock`, or `MOCK` constants remain in `ui/operator-console/src/`
- [ ] No Blade Runner placeholder content visible anywhere in the UI
- [ ] `npm run build` passes with zero warnings related to removed mocks
- [ ] Unit tests pass (`make test-unit`)
- [ ] Visual walkthrough on a real project confirms all pages render live data

## Technical Notes

### Search Implementation Strategy

The cheapest path for search: scan the artifact store at query time. Projects are small (dozens of entities, not thousands), so in-memory filtering is fine. The backend already loads bible manifests and scene data — expose that through a search endpoint that accepts a query string and filters across entity names, scene headings, and artifact metadata.

### Run Events Derivation

`run_state.json` already contains per-stage timing, status, and cost data. The "events" API is a reshaping of this data into a timeline, not a new storage mechanism. Parse `run_state.json` → emit synthetic events for stage start/end, artifact production, and errors.

### Variations — Deferred

VariationalReview is architecturally interesting (compare outputs from different models) but requires the pipeline to actually produce multiple variations per artifact. This is a pipeline-level feature that doesn't exist yet. For this story: replace the mock with an empty state ("No variations available") and a note that this feature is coming. Don't build a fake API that pretends variations exist.

## Work Log

### 20260216-1800 — Phase 1: Backend Search API

**Actions:**
- Added `SearchResponse`, `SearchResultScene`, `SearchResultEntity` Pydantic models to `api/models.py`
- Implemented `search_entities()` in `api/service.py` — scans scene_index + bible_manifest artifacts, case-insensitive substring match
- Added `GET /api/projects/{project_id}/search?q=` route to `api/app.py`
- Run Events and Run Details endpoints already exist (`/runs/{runId}/state`, `/runs/{runId}/events`) — no new backend work needed
- Inbox items derived client-side from `useArtifactGroups()` + `useRuns()` — no dedicated inbox endpoint needed

**Result:** Backend search API + frontend types/hooks wired. Lint clean.

### 20260216-1830 — Phase 2: Unified Command Palette

**Actions:**
- Rewrote `CommandPalette.tsx` — merged GlobalSearch (entity search), CommandPalette (navigation/actions), and KeyboardShortcutsHelp (shortcuts reference) into one Spotlight-style component
- Triggers: `/` (plain key) and `Cmd+K` (alias)
- Empty state: keyboard shortcuts reference (footer section, grouped by category)
- With query: cmdk fuzzy-filters static commands + live entity search results from `useSearch()` hook
- Removed `GlobalSearch` import from `AppShell.tsx`
- Removed `KeyboardShortcutsHelp` import from `App.tsx`
- Updated `GLOBAL_SHORTCUTS` in `shortcuts.ts` — renumbered navigation (⌘0=Home, ⌘1=Runs, ⌘2=Artifacts, ⌘3=Inbox), merged search+palette into "Command palette", removed `?` shortcut
- Build passes clean

**Result:** One palette handles all navigation, search, actions, and help.

### 20260216-1900 — Phase 3: Wire Remaining Mock Data

**Actions:**
- `ProjectRun.tsx`: Replaced `mockRunEvents` import with `useRunEvents(runId)` hook. Added `transformBackendEvents()` helper to map backend event format to UI `RunEvent` type.
- `ProjectRuns.tsx`: Rewrote `RunInspectorContent` to accept `runId` prop and self-fetch via `useRunState(runId)`. Shows real stage breakdown (status, duration, cost) with loading skeleton. Removed `MockRun` interface.
- `ProjectInbox.tsx`: Removed `mockNonStaleItems` constant. Derive error items from failed runs (`useRuns()`), review items from first-version bible_manifest artifacts. All three sources (stale, errors, reviews) composed into `allItems`. VariationalReview uses placeholder message until multi-model variations are implemented.
- `VariationalReview.tsx`: Exported `Variation` interface for use in inbox.
- `ArtifactPreview.tsx`: Kept fallback data as defensive coding — consumers already pass real data; fallback shows during development/preview. Not worth removing.

**Result:** All mock data imports removed. Every data-driven component uses real API hooks. Build passes clean.

### 20260216-2000 — Phase 4: Full Cleanup + Search Tests

**Actions:**
- Deleted `GlobalSearch.tsx` and `KeyboardShortcutsHelp.tsx` (dead files, zero imports).
- Removed `mockRunEvents` export (150 lines) from `RunEventLog.tsx`.
- Removed `mockVariations` export (48 lines of Blade Runner content) from `VariationalReview.tsx`.
- Removed `MOCK_DATA` constant (98 lines) from `ArtifactPreview.tsx`. Replaced `typeof MOCK_DATA.*` casts with inline type annotations. Component now requires real `data` prop.
- Fixed `int_ext` parsing bug in `search_entities()`: `heading.split(" ")[0]` returned `"INT."` (with dot); added `.rstrip(".")` to normalize.
- Added `test_search_returns_scenes_and_entities` test: seeds scene_index + bible_manifest artifacts via `save_bible_entry`, validates search across scenes/characters/locations/props, tests empty query returns empty results.
- Added `test_search_requires_open_project` test: verifies 404 for unknown project.

**Result:** Zero `mock`/`Mock`/`MOCK` references remain in `ui/operator-console/src/`. All new tests pass. Build clean, lint clean. Bug fix included.
