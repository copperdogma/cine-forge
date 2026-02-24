# Story 070 — Script View Scene Dividers & Entity Hotlinks

**Priority**: Medium
**Status**: Done
**Phase**: 2.5 — UI
**Spec Refs**: None
**Depends On**: Story 045 (Entity Cross-Linking)

## Goal

Make the script view an interactive hub that connects screenplay text to the extracted structured data. There are two closely related improvements: first, inject visible scene dividers at each extraction boundary so users can immediately see how the pipeline split the script — miscuts become obvious at a glance and each divider bar is a natural future anchor for per-scene actions. Second, hotlink entity names inside the screenplay (character headings, scene headings, location text) to their corresponding entity detail pages (scenes, characters, locations, props), so navigating from "what the script says" to "what the AI extracted" is a single click rather than a multi-step hunt. Together these make the script view the connective tissue between raw text and the structured world built from it.

## Acceptance Criteria

- [x] Scene dividers are rendered in the script view at each scene boundary, using `source_span.start_line` from scene artifacts
- [x] Each divider shows the scene number and heading (e.g., "Scene 3 — INT. HARBOUR OFFICE - DAY") and is visually distinct from script text
- [x] Clicking a scene divider navigates to that scene's detail page (`/:projectId/scenes/:entityId`)
- [x] Character name lines in the script are rendered as clickable hotlinks to `/:projectId/characters/:entityId` when a matching character entity exists
- [x] Scene heading lines in the script are rendered as clickable hotlinks to `/:projectId/scenes/:entityId` (already partially wired — verify and complete)
- [x] Location name in scene headings links to `/:projectId/locations/:entityId` when a matching location entity exists — NOTE: implemented as scene heading click → scene detail page (which shows location in entity roster). Splitting click targets for location vs scene navigation deferred per plan decision.
- [x] Unmatched entity names (no extracted artifact) render as plain text, not broken links
- [x] Scene dividers and hotlinks are present in both `FreshImportView` (project home) and `ScriptViewer` (artifact detail page)
- [x] UI `Scene` interface in `hooks.ts` exposes `startLine` / `endLine` from `source_span`
- [x] `pnpm --dir ui run lint` passes and no TypeScript errors (`tsc -b`)

## Out of Scope

- Editing entity names or relationships from the script view (future interactive feature)
- Prop hotlinking — prop names appear in action lines as natural prose, requiring NLP-level span detection; this is a more complex follow-on
- Inline tooltips showing entity summaries on hover (a nice follow-on but out of scope here)
- Highlighting ALL occurrences of an entity name throughout the script text (a full-text annotation pass; left for a future story)
- Backend changes — all data needed (`source_span`, entity IDs, character names, location names) already exists in scene artifacts

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- Scene boundary detection from line numbers is pure arithmetic — no LLM needed.
- Matching character heading text to entity IDs: the existing `useEntityResolver` already does this for character names. Re-use it — don't re-invent.
- Matching location text in scene headings to location entity IDs: `useEntityResolver` handles this too (fuzzy + exact). Re-use.
- The only tricky part is injecting React elements between CodeMirror lines, which is a UI rendering problem, not a reasoning problem.

## Tasks

- [x] **Expose `source_span` in the UI `Scene` type**: Update `Scene` interface in `ui/src/lib/hooks.ts` to include `startLine?: number` and `endLine?: number`. Populate from `data?.source_span?.start_line` / `data?.source_span?.end_line` in both `transformArtifactToScene` and the `scene_breakdown` branch of `useScenes`.
- [x] **Build scene divider overlay for `ScreenplayEditor`**: Used CodeMirror `StateEffect` + `StateField` + `WidgetType` (idiomatic CM6) with block decoration widgets. Dispatched via separate `useEffect([scenes])` to avoid view recreation. Key discovery: `WidgetType.ignoreEvent()` defaults to `true` (not false as comment assumed) — CodeMirror never calls `domEventHandlers` for widget clicks. Fixed by catching widget clicks in a React `onClick` on the wrapper div (events bubble naturally since CM doesn't stop them).
- [x] **Wire scene dividers into `FreshImportView`**: In `ProjectHome.tsx`, added `useEntityResolver`, `handleCharacterNameClick` (resolve → navigate), `handleSceneDividerClick` (navigate to scene), and pass to `ScreenplayEditor`.
- [x] **Wire scene dividers into `ScriptViewer`**: Added `projectId?` prop to `ScriptViewer` in `ArtifactViewers.tsx`; calls `useScenes`, `useEntityResolver`, `useNavigate` internally.
- [x] **Hotlink character names in the editor**: Added `isCharacterLine()` helper and `onCharacterNameClick` callback. Extended `handleClick` in `domEventHandlers` to detect character lines. Verified: clicking "ROSE" navigates to `/the-mariner-40/characters/rose`.
- [x] **Hotlink location names via scene heading clicks**: Scene heading → scene detail page (scene detail shows location in entity roster). Split-click for location linking deferred per plan decision.
- [x] **Visual styling for dividers**: `oklch` tokens matching dark theme; hover state; scene number + heading label; `↗` arrow indicator.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI: `pnpm --dir ui run lint` (0 errors, 7 pre-existing warnings) and `tsc -b` (clean)
  - [x] Visual verification: dividers at all 13 scene boundaries in both FreshImportView and ScriptViewer; scene_002 divider click → `/the-mariner-40/scenes/scene_002`; ROSE character click → `/the-mariner-40/characters/rose`; ScriptViewer in ArtifactDetail shows "380 lines · 13 scenes" with dividers visible
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data is at risk — read-only rendering change only.
  - [x] **T1 — AI-Coded:** New props and callbacks are clearly named; future sessions can extend.
  - [x] **T2 — Architect for 100x:** Scene dividers via CodeMirror line widgets are the right pattern; don't invent a custom scroll-sync system.
  - [x] **T3 — Fewer Files:** Changes concentrated in 5 existing files; no new files created.
  - [x] **T4 — Verbose Artifacts:** Work log documents widget click bug discovery, fix, and verification evidence.
  - [x] **T5 — Ideal vs Today:** Prop hotlinking skipped — NLP span extraction belongs in a later story.

## Files to Modify

- `ui/src/lib/hooks.ts` — Add `startLine?: number` and `endLine?: number` to the `Scene` interface; populate in `transformArtifactToScene` and `useScenes` from `data?.source_span?.start_line` / `data?.source_span?.end_line`
- `ui/src/components/ScreenplayEditor.tsx` — Add optional `scenes` prop (array of `{ entityId, heading, sceneNumber, startLine }`), add `onCharacterNameClick` callback; render scene divider widgets at `startLine` positions using CodeMirror line decorations or a positioned overlay
- `ui/src/pages/ProjectHome.tsx` — In `FreshImportView`, pass `scenes` array to `ScreenplayEditor`; add `handleCharacterNameClick` using `useEntityResolver` + `navigate`
- `ui/src/components/ArtifactViewers.tsx` — In `ScriptViewer`, add optional `projectId` prop and fetch `useScenes(projectId)` when provided; pass resulting scene list to `ScreenplayEditor`

## Notes

### Scene Boundary Data

`source_span` already exists in the `Scene` Python schema (`src/cine_forge/schemas/scene.py`):
```python
class SourceSpan(BaseModel):
    start_line: int  # 1-indexed line in canonical_script
    end_line: int

class Scene(BaseModel):
    source_span: SourceSpan
    ...
```

The `Scene` interface in `ui/src/lib/hooks.ts` currently exposes:
```ts
interface Scene {
  entityId: string
  index: number     // scene_number
  heading: string
  // ... but NOT startLine/endLine
  data?: Record<string, unknown>  // raw payload — source_span is in here
}
```
`startLine` and `endLine` need to be promoted out of `data` into first-class fields.

### CodeMirror Divider Approach

Two options:
1. **Line decoration widgets** (`Decoration.widget` at a specific position): inserted via a CodeMirror `ViewPlugin` that reads the `scenes` prop and adds a widget DOM element before the first character of each `startLine`. This is clean but requires the scene list to be passed into the CodeMirror `EditorState` as a compartment or effect, which is slightly more involved. The existing `ScreenplayEditor` already tears down and recreates the view on `content` change — passing scenes in the same effect would work.
2. **Overlay layer**: A sibling `<div>` absolutely positioned over the editor, with divider bars at computed pixel offsets (retrieved from `view.lineBlockAt(pos).top`). Simpler React-side but requires polling or ResizeObserver to stay in sync as the editor scrolls.

Prefer option 1 (line decoration widgets) — it is the idiomatic CodeMirror approach and stays in sync automatically. The existing `EditorView.theme` and `StreamLanguage.define` calls in `ScreenplayEditor.tsx` show the pattern.

### Entity Resolver Re-use

`useEntityResolver` in `ui/src/lib/hooks.ts` already resolves character names and scene headings to entity detail URLs. The `handleCharacterNameClick` in `FreshImportView` should mirror the existing `handleSceneHeadingClick` pattern:
```ts
const handleCharacterNameClick = (name: string) => {
  const resolved = resolve(name, 'character')
  if (resolved) navigate(resolved.path)
}
```

### Dependency on Story 045

Story 045 (Entity Cross-Linking) will improve the quality of `characters_present` (using entity IDs instead of display names) and `scene_presence` (scene entity IDs instead of heading text). This story's hotlinking will work today with the fuzzy resolver as a fallback, and automatically improve when 045 lands — no changes needed here after 045.

### URL Routes for Linking Targets (from `ui/src/App.tsx`)

```
/:projectId/scenes/:entityId      → EntityDetailPage section="scenes"
/:projectId/characters/:entityId  → EntityDetailPage section="characters"
/:projectId/locations/:entityId   → EntityDetailPage section="locations"
/:projectId/props/:entityId       → EntityDetailPage section="props"
```

The "View in Script" button already exists on scene detail pages:
```ts
// EntityDetailPage.tsx line ~558
<Button onClick={() => navigate(`/${projectId}?scene=${encodeURIComponent(displayName)}`)}>
  View in Script
</Button>
```
Scene dividers and character hotlinks in this story complete the reverse journey: Script → Entity.

## Plan

### Exploration Notes

**Files that will change:**
- `ui/src/lib/hooks.ts` — Add `startLine?` / `endLine?` to `Scene` interface; populate in `transformArtifactToScene` and `useScenes` `scene_breakdown` branch
- `ui/src/components/ScreenplayEditor.tsx` — Add `scenes` prop, `onCharacterNameClick` / `onSceneDividerClick` callbacks; add CodeMirror `StateEffect` + `StateField` + `WidgetType` for dividers; extend `handleClick`
- `ui/src/pages/ProjectHome.tsx` — Import `useEntityResolver`; add character + divider click handlers; pass to `ScreenplayEditor`
- `ui/src/components/ArtifactViewers.tsx` — Add `projectId?` to `ScriptViewer`; call `useScenes` + `useEntityResolver` + `useNavigate` inside it
- `ui/src/pages/ArtifactDetail.tsx` — Pass `projectId` to `ScriptViewer` at line 266

**Files at risk of breaking:**
- None — all changes are additive (optional props). Existing callers are unaffected.

**Patterns to follow:**
- `onClickRef` pattern (already in ScreenplayEditor) — store callback in a ref to avoid recreating the view on each parent render
- Separate `useEffect([scenes])` to dispatch `setScenesEffect` after view creation, avoiding view recreation when scenes load
- `useEntityResolver(projectId)` already exists and handles fuzzy + exact character/scene/location matching — re-use it

**Key implementation decisions:**
1. **Divider approach**: `StateEffect` + `StateField` + `WidgetType` — idiomatic CodeMirror 6. Block decoration widget inserted at `line.from` of each scene's `startLine`. Click bubbles to `domEventHandlers` which checks `target.closest('.cm-scene-divider')`.
2. **Character click**: Extend existing `handleClick` — add `isCharacterLine()` helper parallel to `isSceneHeading()`. Fire `onCharacterNameClickRef` when line matches.
3. **No view recreation for scenes**: scenes dispatched via effect, not deps of the main view-creation `useEffect`.

---

### Task Plans

**Task 1 — Expose `source_span` in `Scene` type** (`hooks.ts`)
- Add `startLine?: number; endLine?: number` to `Scene` interface after `summary`
- `transformArtifactToScene`: add `startLine: data?.source_span?.start_line ?? undefined`
- `useScenes` `scene_breakdown` branch: add same from `sceneData?.source_span?.start_line`
- No breaking changes — optional fields

**Task 2 — Dividers + character clicks in `ScreenplayEditor`**
New imports: `Decoration, DecorationSet, WidgetType` from `@codemirror/view`; `StateEffect, StateField` from `@codemirror/state`

New props:
```ts
scenes?: Array<{ entityId: string; heading: string; sceneNumber: number; startLine: number }>
onCharacterNameClick?: (name: string) => void
onSceneDividerClick?: (entityId: string) => void
```

New code:
- `isCharacterLine(line)`: all-caps, length 1–40, not a scene heading, no `.:`
- `SceneDividerWidget extends WidgetType`: renders `<div class="cm-scene-divider" data-entity-id="...">` pill label. `ignoreEvent()` not overridden (returns false = events propagate to editor)
- `setScenesEffect = StateEffect.define<...>()` and `sceneDividersField = StateField.define<DecorationSet>(...)`
- Refs: `onCharacterNameClickRef`, `onSceneDividerClickRef`
- `handleClick`: extend to also fire char click on character lines
- `domEventHandlers click`: check `.cm-scene-divider` first, then fall through to existing scene heading logic
- Add `sceneDividersField` to extensions
- CSS in theme: `.cm-scene-divider` styles
- New `useEffect([scenes, onSceneDividerClick])`: dispatch `setScenesEffect.of(...)` when `scenes` prop changes

**Task 3 — Wire FreshImportView** (`ProjectHome.tsx`)
- Import `useEntityResolver`
- `handleCharacterNameClick(name)`: `resolve(name, 'character')` → `navigate(resolved.path)` if found
- `handleSceneDividerClick(entityId)`: `navigate(`/${projectId}/scenes/${entityId}`)`
- Pass `scenes`, `onCharacterNameClick`, `onSceneDividerClick` to `ScreenplayEditor`

**Task 4 — Wire ScriptViewer** (`ArtifactViewers.tsx`)
- Add `projectId?: string` to props
- Import `useScenes`, `useEntityResolver` from `@/lib/hooks`; `useNavigate` from `react-router-dom`
- Call hooks inside component; build same handlers as FreshImportView
- Pass to `ScreenplayEditor`

**Task 5 — Thread projectId** (`ArtifactDetail.tsx`)
- `<ScriptViewer data={data} projectId={projectId} />`

### Impact Analysis
- Backend: none required (data already in `source_span`)
- Tests: no new unit tests needed (pure UI rendering change); visual verification required
- Approval blockers: none

### Definition of Done
- Dividers visible at scene boundaries in both FreshImportView and ScriptViewer
- Clicking a divider navigates to `/:projectId/scenes/:entityId`
- Clicking a character name line navigates to `/:projectId/characters/:entityId` when entity exists
- Unmatched names render as plain text, no broken links
- `pnpm --dir ui run lint` + `tsc -b` pass
- Runtime smoke test: pages load, no console errors, dividers visible with correct scene numbers

## Work Log

20260223-1945 — Phase 1-2 complete: explored codebase, wrote plan. Files confirmed: hooks.ts (Scene interface, transformArtifactToScene, useScenes scene_breakdown branch), ScreenplayEditor.tsx (new StateEffect+StateField+WidgetType for dividers, extend handleClick for char names), ProjectHome.tsx (FreshImportView: useEntityResolver, char+divider handlers), ArtifactViewers.tsx (ScriptViewer: useScenes+useEntityResolver+useNavigate), ArtifactDetail.tsx (pass projectId). No backend changes. Plan presented to user for approval.

20260223-2030 — Phase 3 complete: all 5 files implemented. Critical bug discovered and fixed: `WidgetType.ignoreEvent()` defaults to `true` (not false), meaning CodeMirror's `handleEvent` returns early for any event on block decoration widgets and NEVER calls `domEventHandlers`. Fix: removed scene divider check from `domEventHandlers`; added React `onClick` to the `.screenplay-editor` wrapper div — widget clicks bubble naturally through DOM since CodeMirror doesn't stop them. Also discovered DPR=2 coordinate issue: MCP screenshot coordinates ≠ CSS pixels (scale ~1.119). Checks: `pnpm --dir ui run lint` (0 errors), `tsc -b` (clean). Runtime smoke tests: (1) FreshImportView — scene dividers at all 13 boundaries, clicking Scene 2 divider → `/the-mariner-40/scenes/scene_002` ✓; clicking "ROSE" character line → `/the-mariner-40/characters/rose` ✓; (2) ArtifactDetail ScriptViewer — "380 lines · 13 scenes" with dividers visible ✓. Story marked Done.
