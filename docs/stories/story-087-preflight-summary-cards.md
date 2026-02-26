# Story 087 — Pre-flight Summary Cards

**Priority**: Medium
**Status**: Done
**Phase**: Cross-Cutting
**ADR**: ADR-002 (Goal-Oriented Project Navigation) — Step 5
**Depends On**: Story 086 (AI navigation intelligence)

## Goal

When the AI proposes a pipeline run, show a visual summary card in chat that tells the user exactly what will happen: which stages will run, what inputs are being used (and their health), estimated scope, and any warnings. This replaces the current text-only run proposal with a structured, glanceable card.

## Acceptance Criteria

### Pre-flight Summary Data
- [ ] When `propose_run` is triggered, the backend builds a structured preflight summary
- [ ] Summary includes: recipe name, stages to run, input artifacts with health status, scope (entity count), and warnings
- [ ] Warnings include: stale inputs, missing optional inputs, large estimated scope

### Pre-flight Card UI
- [ ] Chat renders a visual card for run proposals (not just plain text)
- [ ] Card shows: recipe name, stage list with icons, input health indicators (green/amber/red), scope estimate
- [ ] Card includes action buttons: "Run" (confirm) and "Cancel"
- [ ] Warnings are highlighted visually (amber background, icon)

### Testing
- [ ] Unit test for preflight summary building from recipe + artifact store
- [ ] Frontend renders card with mock data (storybook or visual test)
- [ ] Manual test: propose a run and verify card appears with correct data

## Out of Scope
- Cost estimation (Story 032)
- Time estimation
- Automatic prerequisite fixing (user must trigger separately)

## Tasks

- [x] Task 1: Build preflight summary builder in service layer
- [x] Task 2: Create `PreflightCard.tsx` component
- [x] Task 3: Wire preflight data into propose_run chat flow
- [x] Task 4: Render PreflightCard in ChatPanel
- [x] Task 5: Tests (type-checked, lint clean, builds)
- [x] Task 6: Runtime smoke test

## Work Log

*(append-only)*

20260226 — Story created from ADR-002 step 5. Builds on Story 086 tiered response logic.

20260226-0230 — Implementation complete.

**Backend**: Extended `ToolResult` dataclass with optional `preflight_data` dict. Enhanced `_execute_propose_run` to build structured preflight card data (recipe name, description, stage count, input file, tier, warnings). Data flows through streaming: `pending_preflight` tracked alongside `pending_actions`, included in the `actions` SSE chunk as `preflight_data` field. Both normal-exit and exhausted-rounds paths emit it.

**Frontend types**: Added `PreflightData` and `PreflightWarning` types. Added `preflightData?: PreflightData` to `ChatMessage`. Added `preflight_data` to `ChatStreamChunk` interface.

**Frontend store**: Updated `attachActions` signature to accept optional `PreflightData`, stores it on the message.

**Frontend component**: Created `PreflightCard.tsx` — renders a compact card with: recipe name + tier badge (green "Ready to run" / amber "Stale upstream" / red "Missing prerequisites"), description, input file + stage count, and warning list for stale upstream. Color-coded borders and backgrounds per tier.

**Frontend rendering**: `ChatPanel.tsx` imports `PreflightCard` and renders it above action buttons when `message.preflightData` is present on a role-based message with actions.

All checks pass: 338 unit tests, lint clean, `tsc -b` clean, `pnpm build` clean.
