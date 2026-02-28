# Story 101: Centralized Long-Running Action System

**Status**: Pending
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
- [ ] **`useLongRunningAction` hook** — single entry point for all long-running operations. Accepts config (label, items, action, completion handler) and returns `{ isRunning, start, progress }`.
- [ ] **Global operation store** (Zustand) — tracks all active operations across pages. Any component can read active operations.
- [ ] **`<OperationBanner>`** — shared banner component rendered in AppShell layout. Reads from global store. Shows what's running, item progress (e.g. "4/13"), and auto-dismisses on completion.
- [ ] **Chat integration** — hook automatically creates `task_progress` messages on start, updates per-item status during execution, and adds a completion summary with result links.
- [ ] **Button integration** — hook provides `isRunning` boolean that disables the trigger. While running, button shows a spinner icon.

### The Six Requirements (all mandatory)
1. **Button → disabled + obvious running state** when action starts
2. **Banner at top** showing what's running with progress counts
3. **Chat messages** with per-item running indicators
4. **Progress visible in all three places** as items complete (e.g. "7/13 scenes")
5. **New UI items flash** when they arrive (sidebar counts already do this via CountBadge — extend to other surfaces if needed)
6. **On complete**: button re-enabled (text changes to "Regenerate" variant if applicable), banner disappears, chat spinners finish, summary message with link to results

### Audit & Refactor
- [ ] **Audit every long-running UI operation** in the codebase. For each, document current state (which of the 6 requirements it meets) and refactor to use `useLongRunningAction`.
- [ ] Known operations to audit:
  - Pipeline runs from ProjectHome (via `useRunProgress`) — currently the best implementation
  - Creative direction generation from DirectionTab (via `startRun`)
  - Intent/Mood propagation from IntentMoodPage (inline `TaskProgressCard` pattern)
  - Export operations from ExportModal (currently instant — verify)
  - Any future AI chat calls or tool invocations that take time
- [ ] After refactor, all operations must pass the 6-requirement checklist above.

### Testing
- [ ] **Browser-verified testing (mandatory)**: Every refactored operation must be tested in a real browser session using Chrome MCP automation. For each operation:
  - Screenshot before clicking the trigger button
  - Click the trigger, screenshot immediately (verify button disabled + banner appears)
  - Screenshot mid-progress (verify progress updating in banner + chat)
  - Screenshot on completion (verify button re-enabled, banner gone, chat summary present)
  - Check console for errors
- [ ] Test page navigation mid-operation (banner should persist across pages)
- [ ] Test browser refresh mid-operation (should recover gracefully)
- [ ] Test error handling (failed operation should show error state in all three surfaces)

### Documentation
- [ ] Update `AGENTS.md` "User Feedback Contract" to reference the hook (not manual patterns)
- [ ] Add `useLongRunningAction` and `OperationBanner` to the UI Component Registry with `MUST use` directives
- [ ] Add `MUST NOT` directive: "Never manually create `ai_status` messages or manage button loading state for long-running operations"

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

- [ ] **T1**: Design `useLongRunningAction` hook API — support both pipeline runs and direct API calls
- [ ] **T2**: Create operation store (`operation-store.ts`) — Zustand store tracking active operations with progress
- [ ] **T3**: Build `OperationBanner` component — reads from operation store, shows progress, auto-dismisses
- [ ] **T4**: Implement `useLongRunningAction` hook — manages button state, operation store, chat messages, completion
- [ ] **T5**: Wire `OperationBanner` into AppShell layout (replace inline ProcessingView pattern)
- [ ] **T6**: Audit all long-running operations — document current state per 6-requirement checklist
- [ ] **T7**: Refactor DirectionTab to use hook
- [ ] **T8**: Refactor IntentMoodPage propagation to use hook
- [ ] **T9**: Refactor ProjectHome pipeline runs to use hook (integrate with existing `useRunProgressChat`)
- [ ] **T10**: Browser-verified testing of every refactored operation (screenshots required)
- [ ] **T11**: Test edge cases: mid-operation navigation, browser refresh, error states
- [ ] **T12**: Update AGENTS.md — User Feedback Contract, Component Registry, MUST use directives
- [ ] **T13**: Run full check suite (tsc -b, pnpm lint, pnpm build)

---

## Work Log

*(append-only)*

20260228 — Story created from UX feedback during Story 021 browser testing. User identified that direction generation buttons put a message in chat but provide no other feedback — no banner, no progress, button re-enables immediately. Diagnosed root cause: DirectionTab's handleGenerate wasn't calling setActiveRun() so the existing run tracking system never activated. Quick fix applied to DirectionTab (wire into useRunProgressChat via setActiveRun). This story addresses the systemic issue: build a centralized hook so every future operation gets full feedback automatically.
