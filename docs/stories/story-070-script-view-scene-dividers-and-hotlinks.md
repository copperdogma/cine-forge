# Story 070 — Script View Scene Dividers & Entity Hotlinks

**Priority**: Medium
**Status**: Pending
**Phase**: 2.5 — UI
**Spec Refs**: None
**Depends On**: Story 045 (Entity Cross-Linking)

## Goal

Make the script view an interactive hub that connects screenplay text to the extracted structured data. There are two closely related improvements: first, inject visible scene dividers at each extraction boundary so users can immediately see how the pipeline split the script — miscuts become obvious at a glance and each divider bar is a natural future anchor for per-scene actions. Second, hotlink entity names inside the screenplay (character headings, scene headings, location text) to their corresponding entity detail pages (scenes, characters, locations, props), so navigating from "what the script says" to "what the AI extracted" is a single click rather than a multi-step hunt. Together these make the script view the connective tissue between raw text and the structured world built from it.

## Acceptance Criteria

- [ ] Scene dividers are rendered in the script view at each scene boundary, using `source_span.start_line` from scene artifacts
- [ ] Each divider shows the scene number and heading (e.g., "Scene 3 — INT. HARBOUR OFFICE - DAY") and is visually distinct from script text
- [ ] Clicking a scene divider navigates to that scene's detail page (`/:projectId/scenes/:entityId`)
- [ ] Character name lines in the script are rendered as clickable hotlinks to `/:projectId/characters/:entityId` when a matching character entity exists
- [ ] Scene heading lines in the script are rendered as clickable hotlinks to `/:projectId/scenes/:entityId` (already partially wired — verify and complete)
- [ ] Location name in scene headings links to `/:projectId/locations/:entityId` when a matching location entity exists
- [ ] Unmatched entity names (no extracted artifact) render as plain text, not broken links
- [ ] Scene dividers and hotlinks are present in both `FreshImportView` (project home) and `ScriptViewer` (artifact detail page)
- [ ] UI `Scene` interface in `hooks.ts` exposes `startLine` / `endLine` from `source_span`
- [ ] `pnpm --dir ui run lint` passes and no TypeScript errors (`tsc -b`)

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

- [ ] **Expose `source_span` in the UI `Scene` type**: Update `Scene` interface in `ui/src/lib/hooks.ts` to include `startLine?: number` and `endLine?: number`. Populate from `data?.source_span?.start_line` / `data?.source_span?.end_line` in both `transformArtifactToScene` and the `scene_breakdown` branch of `useScenes`.
- [ ] **Build scene divider overlay for `ScreenplayEditor`**: The CodeMirror editor in `ui/src/components/ScreenplayEditor.tsx` renders plain text. The dividers are best added as a React layer on top of (or injected via CodeMirror line decorations below) the editor. Preferred approach: keep CodeMirror as-is and render scene divider bars in a sibling element that scrolls in sync, OR use CodeMirror's `Decoration.line` API to inject a widget between lines. Evaluate: line widgets are cleanest if CodeMirror scroll position can be tracked; otherwise use a transparent overlay with absolute-positioned bars. Add an optional `scenes` prop to `ScreenplayEditorProps` accepting `Array<{ entityId: string; heading: string; sceneNumber: number; startLine: number }>` and render a slim divider bar with scene label at each `startLine`.
- [ ] **Wire scene dividers into `FreshImportView`**: In `ui/src/pages/ProjectHome.tsx`, pass the loaded `scenes` array to `ScreenplayEditor` via the new `scenes` prop so dividers appear in the primary script view.
- [ ] **Wire scene dividers into `ScriptViewer`**: In `ui/src/components/ArtifactViewers.tsx`, `ScriptViewer` currently passes only `content` and `readOnly`. It does not have access to scenes. Either accept an optional `scenes` prop and thread it from the artifact detail page, or fetch scenes internally via a new hook call (`useScenes(projectId)`). The simpler path: add an optional `projectId` prop to `ScriptViewer` and call `useScenes` inside it when provided.
- [ ] **Hotlink character names in the editor**: `ScreenplayEditor` already detects character lines (all-caps, short, not a scene heading). Add an optional `onCharacterNameClick?: (name: string) => void` callback to `ScreenplayEditorProps`, analogous to the existing `onSceneHeadingClick`. In the CodeMirror `domEventHandlers`, check if the clicked line is a character line and fire the callback. In `FreshImportView`, implement `handleCharacterNameClick` using `useEntityResolver` to look up the entity ID and `navigate` to `/:projectId/characters/:entityId`.
- [ ] **Hotlink location names via scene heading clicks**: The existing `onSceneHeadingClick` fires when a scene heading is clicked. Currently it navigates to the scene detail page. Extend: after navigating to the scene, users can already reach the location from there. Alternatively, split the click target: clicking the INT/EXT prefix or the location portion navigates to the location, clicking anywhere else on the line navigates to the scene. This is a UX decision — keep simple for now (scene heading click → scene detail page, as today) and just ensure it works correctly; the scene detail page already has a "View in Script" back-link and entity roster.
- [ ] **Visual styling for dividers**: Dividers should be visually unobtrusive — a thin horizontal rule with a small pill badge showing "Scene N — HEADING". Use `oklch` tokens from the existing dark theme (`border-border`, `text-muted-foreground`, `bg-muted/30`). On hover, tint to `bg-accent/30` to indicate interactivity. Keep font size smaller than the script text (`text-xs` or `text-[11px] font-mono`).
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI: `pnpm --dir ui run lint` and `pnpm --dir ui exec tsc -b`
  - [ ] Visual verification: open the app with a processed project, confirm dividers appear at correct scene boundaries, confirm scene heading clicks navigate to scene detail pages, confirm character name clicks navigate to character detail pages
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** No user data is at risk — read-only rendering change only.
  - [ ] **T1 — AI-Coded:** New props and callbacks are clearly named; future sessions can extend.
  - [ ] **T2 — Architect for 100x:** Scene dividers via CodeMirror line widgets are the right pattern; don't invent a custom scroll-sync system.
  - [ ] **T3 — Fewer Files:** Changes are concentrated in 3–4 existing files; no new files needed unless divider component warrants extraction.
  - [ ] **T4 — Verbose Artifacts:** Work log must document which scene boundary approach was chosen and why.
  - [ ] **T5 — Ideal vs Today:** Skip prop hotlinking for now — that requires NLP span extraction and belongs in a later story.

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

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
