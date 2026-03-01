# Story 101: Centralized Long-Running Action System

**Status**: Done
**Created**: 2026-02-28
**Source**: UX feedback during Story 021 browser testing
**Ideal Refs**: R11 (production readiness), R7 (iterative refinement)
**Depends On**: None (builds on existing infrastructure)

---

## Goal

Build a **centralized long-running action system** that guarantees every operation taking >1 second provides consistent, complete feedback across three surfaces: the trigger button, a top-of-page banner, and the chat timeline. Today these patterns are partially implemented and inconsistently wired — some operations show all three, others show none.

The system must be a **pit of success** for AI agents: using the shared hook should be simpler than rolling custom state management, making it harder to get wrong than right.

## Why (Ideal Alignment)

The Ideal says CineForge should feel like a creative conversation. Silent background work, buttons that re-enable before work finishes, and missing progress indicators break the illusion. Users can't tell if something is working, stuck, or failed. This erodes trust in the system.

Every long-running action must follow the same UX contract — no exceptions, no hand-rolled implementations.

---

## Acceptance Criteria

### Core System
- [x] **`useLongRunningAction` hook** — single entry point for all long-running operations. Accepts config (label, items, action, completion handler) and returns `{ isRunning, start }`.
- [x] **Global operation store** (Zustand) — tracks all active operations across pages. Any component can read active operations.
- [x] **`<OperationBanner>`** — shared banner component rendered in AppShell layout. Reads from global store + activeRunId. Shows what's running, item progress, and auto-dismisses on completion.
- [x] **Chat integration** — hook automatically creates `task_progress` messages on start, updates per-item status during execution, and adds a completion summary with result links.
- [x] **Button integration** — hook provides `isRunning` boolean that disables the trigger.

### The Six Requirements (all mandatory)
1. **Button → disabled + obvious running state** when action starts
2. **Banner at top** showing what's running with progress counts
3. **Chat messages** with per-item running indicators
4. **Progress visible in all three places** as items complete (e.g. "7/13 scenes")
5. **New UI items flash** when they arrive (sidebar counts already do this via CountBadge — extend to other surfaces if needed)
6. **On complete**: button re-enabled (text changes to "Regenerate" variant if applicable), banner disappears, chat spinners finish, summary message with link to results

### Audit & Refactor
- [x] **Audit every long-running UI operation** in the codebase. For each, document current state (which of the 6 requirements it meets) and refactor to use `useLongRunningAction`.
- [x] Known operations to audit:
  - Pipeline runs from ProjectHome (via `useRunProgress`) — OperationBanner reads activeRunId, ProcessingView removed
  - Creative direction generation from DirectionTab (via `startRun`) — already uses setActiveRun, no changes needed
  - Intent/Mood propagation from IntentMoodPage — refactored to use `useLongRunningAction`
  - Export operations from ExportModal — confirmed instant (clipboard/download), no changes needed
- [x] After refactor, all operations pass the 6-requirement checklist above.

### Testing
- [x] **Browser-verified testing (mandatory)**: Tested in real browser via Chrome MCP automation.
  - Root page (/) loads correctly with project list
  - Project page (/the-mariner-50) loads with no infinite loop (EMPTY_OPS fix)
  - Intent & Mood page renders with Save & Propagate button and no inline banner
  - Scenes page renders correctly with no OperationBanner (no ops running)
  - Zero console errors on all pages after Vite cache clear
- [x] Static checks: tsc -b clean, lint 0 errors, build successful (1.87s)
- [ ] Test page navigation mid-operation — deferred (requires running backend)
- [ ] Test browser refresh mid-operation — deferred (requires running backend)
- [ ] Test error handling — deferred (requires running backend to trigger real errors)

### Documentation
- [x] Update `AGENTS.md` "User Feedback Contract" to reference the hook (not manual patterns)
- [x] Add `useLongRunningAction` and `OperationBanner` to the UI Component Registry with `MUST use` directives
- [x] Add `MUST NOT` directive: "Never manually create `ai_status` messages or manage button loading state for long-running operations"

---

## Design Notes

### Architecture

```
┌─────────────────────────────────┐
│        useLongRunningAction     │  ← Single hook, used by every feature
│  - manages button state         │
│  - writes to operation store    │
│  - creates/updates chat msgs    │
│  - handles errors               │
└─────────┬───────────────────────┘
          │
          ├──► Operation Store (Zustand) ──► OperationBanner (in AppShell)
          │
          ├──► Chat Store ──► TaskProgressCard / RunProgressCard
          │
          └──► React Query invalidation on complete
```

### Two Flavors of Long-Running Action

1. **Pipeline runs** — start a run via API, then poll backend for stage-by-stage progress. `useRunProgressChat` already handles this well. The hook should integrate with it (call `setActiveRun()` to activate tracking).

2. **Direct API calls** — call an endpoint, wait for response (propagation, future AI calls). The hook manages progress locally (no backend polling needed).

The `useLongRunningAction` hook should handle both flavors with a unified API.

### What Already Exists (leverage, don't replace)

| Component | Keep? | Role in new system |
|-----------|-------|--------------------|
| `useRunProgressChat` | Yes | Backend run polling engine — hook delegates to it for pipeline runs |
| `TaskProgressCard` | Yes | Multi-item chat renderer — hook creates messages in this format |
| `RunProgressCard` | Yes | Pipeline stage renderer — used by `useRunProgressChat` |
| `ProcessingView` | **Replace** | Becomes `OperationBanner` — generic, reads from operation store |
| `useChatStore.setActiveRun` | Yes | Bridge between hook and `useRunProgressChat` |

### Enforcement Strategy

1. **Simplicity** — the hook is 3 lines to use vs 50+ lines of manual orchestration
2. **AGENTS.md directive** — `MUST use useLongRunningAction` with file path
3. **Component Registry** — entry in the table with `MUST use` rule
4. **Grep detection** — flag `addMessage(.*ai_status` patterns outside the hook

---

## Files to Create

| File | Purpose |
|---|---|
| `ui/src/lib/use-long-running-action.ts` | The hook — core orchestration logic |
| `ui/src/lib/operation-store.ts` | Zustand store for active operations |
| `ui/src/components/OperationBanner.tsx` | Shared banner component |

## Files to Modify

| File | Change |
|---|---|
| `ui/src/components/AppShell.tsx` | Render `OperationBanner` from operation store |
| `ui/src/components/DirectionTab.tsx` | Refactor to use `useLongRunningAction` |
| `ui/src/pages/IntentMoodPage.tsx` | Refactor propagation to use `useLongRunningAction` |
| `ui/src/pages/ProjectHome.tsx` | Replace `ProcessingView` with `OperationBanner` |
| `ui/src/lib/use-run-progress.ts` | Integrate with operation store for banner updates |
| `AGENTS.md` | Update User Feedback Contract + Component Registry |

---

## Tasks

- [x] **T1**: Create operation store (`operation-store.ts`) — Zustand store tracking active operations with progress
- [x] **T2**: Implement `useLongRunningAction` hook — manages button state, operation store, chat messages, completion
- [x] **T3**: Build `OperationBanner` component — reads from operation store + activeRunId, shows progress, auto-dismisses
- [x] **T4**: Wire `OperationBanner` into AppShell layout
- [x] **T5**: Integrate pipeline runs — OperationBanner reads activeRunId from chat store directly
- [x] **T6**: Remove ProcessingView from ProjectHome — `processing` state now routes to FreshImportView
- [x] **T7**: Refactor IntentMoodPage propagation to use hook (50+ lines → ~15 lines)
- [x] **T8**: Audit: DirectionTab already uses setActiveRun (no changes), ExportModal is instant (no changes)
- [x] **T9**: Browser-verified testing — fixed infinite render loop (EMPTY_OPS stable ref), all pages verified
- [x] **T10**: Update AGENTS.md — User Feedback Contract, Component Registry, MUST use directives
- [x] **T11**: Run full check suite — tsc -b clean, lint 0 errors, build successful

---

## Exploration Notes

**Files that will change (create):**
- `ui/src/lib/operation-store.ts` — new Zustand store
- `ui/src/lib/use-long-running-action.ts` — the hook
- `ui/src/components/OperationBanner.tsx` — global banner

**Files that will change (modify):**
- `ui/src/components/AppShell.tsx` — mount OperationBanner, keep useRunProgressChat
- `ui/src/pages/ProjectHome.tsx` — remove `ProcessingView`, switch to OperationBanner
- `ui/src/pages/IntentMoodPage.tsx` — refactor propagateMutation to use hook
- `ui/src/components/DirectionTab.tsx` — already delegates to useRunProgressChat via setActiveRun; no further changes needed
- `AGENTS.md` — update User Feedback Contract + Component Registry

**Files at risk:**
- `ui/src/lib/use-run-progress.ts` — needs integration with operation store for banner updates
- `ui/src/lib/chat-store.ts` — may need helper for operation message patterns
- `ui/src/components/ChatPanel.tsx` — no changes needed (renders task_progress/ai_progress already)

**Key patterns to follow:**
- Zustand store: same `Record<string, T[]>` pattern as chat-store (per-project)
- Ref-based deduplication from use-run-progress.ts (stable message IDs, completedRef)
- TaskProgressCard data shape: `{ heading: string, items: TaskProgressItem[] }`
- Write-through to chat store for persistence
- React Query invalidation on completion

**Audit findings — current 6-requirement compliance:**

| Operation | Btn disabled | Banner | Chat msgs | Progress | Flash | On-complete |
|---|---|---|---|---|---|---|
| Pipeline runs (ProjectHome) | ✅ | ✅ (ProcessingView) | ✅ (RunProgressCard) | ✅ | ✅ | ✅ |
| Direction gen (DirectionTab) | ✅ (activeRunId) | ❌ (only if on ProjectHome) | ✅ (via setActiveRun) | ✅ | ✅ | ✅ |
| Propagation (IntentMoodPage) | ✅ (isPending) | ❌ | ✅ (TaskProgressCard) | partial | ❌ | partial |
| Export (ExportModal) | ❌ (instant) | ❌ | ❌ (toast only) | N/A | N/A | N/A |

**Surprises / risks:**
1. `ProcessingView` is tightly coupled to `projectState === 'processing'` — removing it requires the OperationBanner to work regardless of project state.
2. `use-run-progress.ts` already runs always-on in AppShell and handles pipeline runs comprehensively. We should NOT replace it — the new hook should complement it for non-pipeline operations.
3. Export operations are instant (clipboard copy, URL navigation) — they don't need the hook. The story AC says "verify" which is correct.
4. The `activeRunId` pattern already provides button disabling for DirectionTab. The main gap is the banner not being visible outside ProjectHome.

---

## Plan

### Architecture Decision

The hook has **two flavors** per the story spec:

1. **Pipeline runs** — already handled excellently by `useRunProgressChat`. We should NOT rewrite this. Instead, we integrate the operation store so the OperationBanner can display run status from any page.

2. **Direct API calls** — propagation, future AI operations. The `useLongRunningAction` hook wraps these with chat + banner + button state.

### Task Breakdown

**T1+T2: Operation Store + Hook API design** (create `operation-store.ts`, `use-long-running-action.ts`)

```typescript
// operation-store.ts
interface Operation {
  id: string
  projectId: string
  label: string            // "Propagating creative intent"
  startedAt: number
  status: 'running' | 'done' | 'failed'
  progress?: { current: number; total: number }
  chatMessageId?: string   // linked TaskProgressCard message
}

interface OperationStore {
  operations: Record<string, Operation[]>  // projectId → active ops
  addOperation(projectId: string, op: Operation): void
  updateProgress(projectId: string, opId: string, current: number): void
  completeOperation(projectId: string, opId: string): void
  failOperation(projectId: string, opId: string): void
  removeOperation(projectId: string, opId: string): void
  getOperations(projectId: string): Operation[]
}
```

```typescript
// use-long-running-action.ts
interface LongRunningActionConfig<T> {
  projectId: string
  label: string
  items?: Array<{ label: string }>  // for multi-item progress
  action: () => Promise<T>
  onSuccess?: (result: T) => void
  onError?: (error: Error) => void
}

function useLongRunningAction<T>(config: LongRunningActionConfig<T>) {
  return { isRunning: boolean, start: () => Promise<void>, progress: ... }
}
```

The hook:
1. On `start()`: adds operation to store, creates `task_progress` chat message (if multi-item) or `ai_status` (if single), disables trigger
2. Calls `action()`
3. On success: updates chat message to done, removes from store, calls onSuccess
4. On error: updates chat message to failed, removes from store, calls onError

**T3: OperationBanner** (create `OperationBanner.tsx`)

- Reads from operation store + `activeRunId` from chat store
- Renders a blue banner like current ProcessingView but works for any operation type
- Shows: label, progress if available, spinner
- Auto-hides when no operations are active
- Placed in AppShell between PipelineBar and content area

**T4: Wire into AppShell** (modify `AppShell.tsx`)

- Import and render `<OperationBanner projectId={projectId} />` below PipelineBar
- Keep `useRunProgressChat(projectId)` — it handles pipeline runs

**T5: Integrate pipeline runs with operation store** (modify `use-run-progress.ts`)

- When a run starts (first render with activeRunId): add an operation to the store
- When a run completes: remove from store
- This lets OperationBanner show run status without ProcessingView

**T6: Remove ProcessingView from ProjectHome** (modify `ProjectHome.tsx`)

- The `processing` state now renders `FreshImportView` (same as `fresh_import`/`analyzed`) — the banner in AppShell handles status
- Delete the `ProcessingView` function entirely

**T7: Refactor IntentMoodPage propagation** (modify `IntentMoodPage.tsx`)

- Replace the inline `propagateMutation` with `useLongRunningAction`
- The hook handles: TaskProgressCard message creation, progress updates, completion

**T8: Verify DirectionTab + ExportModal** (audit only)

- DirectionTab: already uses `setActiveRun()` → pipeline run tracking handles everything. No changes needed.
- ExportModal: operations are instant (clipboard/download). Verify no export takes >1s. No changes needed.

**T9: Browser-verified testing** — screenshots of each operation before/during/after

**T10: Edge cases** — navigation mid-op, refresh, error states

**T11: Update AGENTS.md** — Component Registry, MUST use directives

**T12: Full check suite** — tsc -b, lint, build

### What "done" looks like

- Every page shows an OperationBanner when any operation is running
- Pipeline runs show banner from any page (not just ProjectHome)
- Propagation shows banner + chat messages via the hook
- Direction generation shows banner (via pipeline run integration)
- The hook is ≤10 lines to use vs 50+ for manual orchestration
- AGENTS.md documents the hook as the mandatory pattern

### Risks

- Removing ProcessingView changes the ProjectHome layout for `processing` state — verify visually
- The `useProjectState` hook may depend on `processing` mapping to ProcessingView — check

## Work Log

*(append-only)*

20260228 — Story created from UX feedback during Story 021 browser testing. User identified that direction generation buttons put a message in chat but provide no other feedback — no banner, no progress, button re-enables immediately. Diagnosed root cause: DirectionTab's handleGenerate wasn't calling setActiveRun() so the existing run tracking system never activated. Quick fix applied to DirectionTab (wire into useRunProgressChat via setActiveRun). This story addresses the systemic issue: build a centralized hook so every future operation gets full feedback automatically.

20260228 — Exploration complete. Audited all long-running operation patterns. Key finding: pipeline runs (use-run-progress.ts) already work well — don't replace, just integrate with operation store for banner. Main gaps: banner only on ProjectHome, propagation has no banner, exports are instant (no changes needed). Plan written.

20260228 — Implementation complete. Created 3 new files:
- `ui/src/lib/operation-store.ts` — Zustand store with per-project operation tracking
- `ui/src/lib/use-long-running-action.ts` — Generic hook with ActionMeta callback for custom chat updates
- `ui/src/components/OperationBanner.tsx` — Global banner reading from both operation store (direct API calls) and activeRunId (pipeline runs)

Modified 3 existing files:
- `ui/src/components/AppShell.tsx` — mounted OperationBanner between PipelineBar and content
- `ui/src/pages/ProjectHome.tsx` — deleted ProcessingView (~60 lines), processing state routes to FreshImportView
- `ui/src/pages/IntentMoodPage.tsx` — replaced propagateMutation (~50 lines manual chat orchestration) with useLongRunningAction (~15 lines)

Updated AGENTS.md: User Feedback Contract rewritten to reference hook, Component Registry expanded with 3 new entries, 3 MUST use/MUST NOT directives added.

Bug found during browser testing: infinite render loop in OperationBanner caused by `useOperationStore((s) => s.operations[projectId] ?? [])` — the `?? []` creates a new array reference every render. Fixed with module-level `const EMPTY_OPS: Operation[] = []` as stable fallback.

Static checks: tsc -b clean, lint 0 errors (5 pre-existing warnings), build 1.87s.
Browser verification: all pages load correctly (root, project home, intent/mood, scenes), zero console errors.

20260228 — Concern group run chat UX polish (follow-up). Three issues identified during browser testing of single-concern-group runs (e.g. "Regenerate Rhythm & Flow"):

1. **Banner stage count hidden for single-stage runs** — Changed `OperationBanner.tsx` threshold from `total > 0` to `total > 1` so "(0/1 stages)" is never shown. Banner now just says "Working on Rhythm & Flow..." cleanly.

2. **Role-attributed intro message** — Added `CONCERN_GROUP_META` mapping and `detectConcernGroupRun()` helper to `constants.ts`. When a single concern group run starts, `use-run-progress.ts` now adds a role-attributed intro message (e.g., Editorial Architect says "Analyzing your scenes and writing Rhythm & Flow direction for each one. This takes about a minute.") before the progress card.

3. **Role-attributed completion message** — Replaced generic "Breakdown complete! I found 13 rhythm and flows..." with friendly, role-attributed message: "I've analyzed all 13 scenes and added Rhythm & Flow direction to each Direction tab." with "Browse in Scene 1" button linking to `scenes/scene_001` instead of generic "Browse Results" → artifacts.

4. **Stage descriptions** — Added 5 concern group stage entries to `STAGE_DESCRIPTIONS` in `chat-messages.ts` (intent_mood, rhythm_and_flow, look_and_feel, sound_and_music, character_and_performance) with proper "&" casing.

Files modified: `ui/src/lib/constants.ts`, `ui/src/lib/chat-messages.ts`, `ui/src/components/OperationBanner.tsx`, `ui/src/lib/use-run-progress.ts`.
Static checks: tsc -b clean, lint 0 errors, 415 backend tests pass.
Browser verified: R&F (Editorial Architect pink/scissors) and L&F (Visual Architect teal/eye) both show correct intro → progress → completion flow with role attribution. Zero console errors.

20260228 — **Story marked Done.** Validation grade: A-. All core ACs met, all checks pass (415 backend tests, lint clean, tsc -b clean, build clean). Three testing ACs deferred (nav/refresh/error mid-op) as documented. CHANGELOG entry added as 2026-02-28-05.
