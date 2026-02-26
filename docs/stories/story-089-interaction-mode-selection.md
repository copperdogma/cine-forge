# Story 089 — Interaction Mode Selection

**Priority**: Low
**Status**: Done
**Phase**: Cross-Cutting
**ADR**: ADR-002 (Goal-Oriented Project Navigation) — Step 8 (Lightweight)
**Depends On**: Story 085 (pipeline capability graph)

## Goal

Let users pick an interaction mode that adjusts AI verbosity and autonomy level. This is a lightweight version of ADR-002's Layer 4 (Persona-Adaptive Workspaces) — just a mode toggle, not full persona selection.

Three modes:
- **Guided** — Verbose explanations, step-by-step walkthrough, proactive suggestions. For users new to the pipeline.
- **Balanced** — Default. Clear but concise responses. Explains when relevant.
- **Expert** — Terse, minimal hand-holding. Assumes user knows the pipeline. Focuses on actions, not explanations.

## Acceptance Criteria

### Project Settings
- [x] `interaction_mode` field added to project settings (guided / balanced / expert)
- [x] Default is `balanced`
- [x] Mode persists in project.json (not localStorage)

### System Prompt Adaptation
- [x] System prompt includes a tone/detail section that varies by mode
- [x] Guided mode: longer explanations, proactive "here's what this means" context, step-by-step suggestions
- [x] Balanced mode: standard behavior (current default)
- [x] Expert mode: terse responses, skip explanations of familiar concepts, focus on actionable output

### UI
- [x] Mode selector in chat header (small dropdown or segmented control)
- [x] Mode change takes effect on next message (no reload required)
- [x] Current mode is visually indicated

### Testing
- [x] Unit test for system prompt variation per mode
- [x] Manual test: switch modes and verify tone difference in AI responses

## Out of Scope
- Full persona selection (different AI personalities/roles)
- Per-feature autonomy levels
- Onboarding flow based on persona
- Custom mode creation

## Tasks

- [x] Task 1: Add `interaction_mode` to project settings schema
- [x] Task 2: Add mode-aware system prompt layer in chat.py
- [x] Task 3: Add API endpoint for get/set interaction mode
- [x] Task 4: Build mode selector UI in chat header
- [x] Task 5: Tests
- [x] Task 6: Runtime smoke test

## Work Log

*(append-only)*

20260226 — Story created from ADR-002 step 8 (lightweight). Full persona-adaptive workspaces deferred to future story.

20260226-0300 — Implementation complete.

**Backend**: Added `interaction_mode` field (guided/balanced/expert, default balanced) to `ProjectSettingsUpdate` and `ProjectSummary` Pydantic models in `models.py`. Updated `_write_project_json`, `update_project_settings`, and `project_summary` in `service.py` to read/write/return the field. Updated `app.py` PATCH endpoint to pass it through. Mode persists in `project.json`.

**System prompt**: Added `INTERACTION_MODE_PROMPTS` dict in `chat.py` with guided and expert prompt sections. Balanced has no extra section (default behavior). Injected into `build_role_system_prompt()` after ASSISTANT_EXTRA — applies to all roles, not just assistant. Guided mode: step-by-step, educational, proactive. Expert mode: terse, action-oriented, skip explanations.

**Frontend types**: Added `InteractionMode` type alias. Added `interaction_mode` to `ProjectSummary`. Added `interaction_mode` to `updateProjectSettings` API function.

**Frontend UI**: Built `InteractionModeSelector` segmented control in `ChatPanel.tsx` — 3-button toggle (Guided/Balanced/Expert) with tooltips, rendered above ScrollArea. Uses optimistic update via `useQueryClient` + fire-and-forget `updateProjectSettings`. Mode change takes effect on next message (no reload).

**Tests**: 6 new tests in `test_interaction_mode.py` — guided injects section, expert injects section, balanced has no extra, default is balanced, mode applies to non-assistant roles, mode prompts dict structure.

All checks pass: 344 unit tests, ruff clean, tsc -b clean, pnpm build clean. Runtime smoke: health 200, PATCH sets mode, GET returns persisted mode.
