# Story 099: Scene Workspace

**Status**: Done
**Created**: 2026-02-27
**Source**: ADR-003, Ideal R11
**Spec Refs**: 12.7 (Readiness Indicators)
**Ideal Refs**: R11 (production readiness per scene), R7 (iterative refinement)
**Depends On**: Story 094 (concern group schemas), Story 095 (intent/mood layer), Story 085 (pipeline graph)

---

## Goal

Build the **Scene Workspace** — the per-scene production control surface (View 2 in the two-view architecture from ADR-002). Shows five concern group tabs (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World) with red/yellow/green readiness indicators per group. This is where filmmakers do their creative work.

## Why (Ideal Alignment)

R11: "The system must show production readiness per scene." The Scene Workspace is the primary realization of this requirement — for every scene, users see what's specified, what AI has inferred, and what's completely missing. The five concern group tabs (from ADR-003) organize the ~87 creative elements into navigable groups.

The Ideal says CineForge should feel like a creative conversation. The Scene Workspace is where that conversation happens — each concern group is an invitation to explore, refine, or leave to AI.

## Acceptance Criteria

- [x] Per-scene view with five concern group tabs
- [x] Each tab shows: AI-inferred elements (red = missing, yellow = AI draft via DirectionAnnotation), generate button per group
- [x] Summary bar: five colored indicators per scene showing readiness at a glance
- [x] Intent/Mood controls at the top (project-wide or per-scene override via SceneIntentPanel)
- [x] "Let AI fill this" button per concern group (generates missing elements via creative_direction recipe)
- [~] "Generate scene" button — **scoped out**: film-lane pipeline (Story 028) doesn't exist yet. Per-group generation covers the use case.
- [x] Links to entity detail pages for characters/locations/props referenced in the scene (entity roster)
- [x] Preview panel: Overview tab with SceneViewer = text summary (best available representation)

## Relationship to ADR-002

ADR-002 defined the two-view architecture: Story Explorer (existing) + Scene Workspace (this story). The Scene Workspace was described as an inbox item; this story makes it concrete using the concern group structure from ADR-003.

---

## Design Notes (from inbox triage 2026-03-02)

### AI-Filled / Skip-Ahead State
When a user hits "generate" without completing all upstream steps, AI fills gaps from whatever exists. This creates a state beyond completed/not_started: **"AI-inferred."** Every AI-guessed element should be visibly labeled in the readiness indicators. Example: you have a script and bibles but no reference images — AI generates video but characters look different every scene because there's no visual anchor. Each element in the Scene Workspace should show this state. Ties into the preflight tiered response system (Story 087). Needs design: how to represent quality degradation, what the "AI guessed this" indicator looks like, whether users can retroactively upgrade (generate reference images, then re-render).

### ADR-002 Outstanding Items (relevant to this story)
- **Placeholder generation with visible marking**: For yellow-tier scenarios (AI has some data but not enough), generated placeholders should be visibly marked as "AI-inferred" vs "user-specified."
- **Quality estimates in preflight**: "★★★☆☆ estimated quality" per concern group before generation. Ties into readiness indicators.
- **Onboarding flow**: "I'm a [Screenwriter/Director/Producer/Explorer]" single question, skippable, defaults to Explorer. Not directly Scene Workspace but affects what's shown first. *(May warrant its own story.)*
- **Explorer demo project**: Pre-populated tutorial project (Notion pattern). *(May warrant its own story.)*

### Scene-First, Not Shot-First
Kling 3.0 can generate multi-shot sequences (up to 6 camera cuts per generation). The atomic unit for video gen is moving from "shot" toward "scene." Scene Workspace should be scene-first with shot detail as a drill-down, not shot-first. User preference: generate whole scene vs. shot-by-shot vs. whole scene with per-shot regeneration.

---

## Tasks

- [x] Add exploration notes and plan to story file
- [x] Create `ui/src/pages/SceneWorkspacePage.tsx` — main workspace component
- [x] Update `ui/src/App.tsx` — route `scenes/:entityId` to SceneWorkspacePage
- [x] Export `SceneIntentPanel` from `DirectionTab.tsx` for reuse
- [x] Run linter + tsc -b to verify type correctness (0 errors)
- [x] Smoke test in browser — scene renders with all tabs, readiness bar, entity roster, generate buttons
- [x] Mark ACs complete; update story status to Done

## Plan

### Scope Decisions

- **Scoped out**: "Generate scene" button (film-lane pipeline, Story 028, doesn't exist). Replaced by per-group "Let AI fill this" buttons which call the existing `creative_direction` recipe per concern group.
- **Scoped out**: Preview panel animatic/video (no media generation yet). Implemented as text summary only (the existing `SceneViewer` output).
- **Character & Performance tab**: Renders as a placeholder/coming-soon state (Story 023 is contingent on Story 025). The tab still shows, just without generation capability.
- **Story World tab**: Project-scoped (entity_id = projectId), not per-scene. Shows the project-wide StoryWorld artifact and links to character/location/prop bibles as "design baselines."

### Readiness Computation (client-side)

No backend endpoint exists. Compute readiness from `useArtifactGroups`:
- RED = no artifact of that type exists for this scene
- YELLOW = artifact exists (AI-generated or user-partially-filled)
- GREEN = artifact exists with `user_approved: true` (not yet exposed in group summaries — defer to full artifact fetch per tab or treat as YELLOW)

For the summary bar: RED/YELLOW only (GREEN deferred until we expose `user_approved` in the groups summary endpoint). This is semantically correct: the readiness schema in `readiness.py` defines GREEN as "user explicitly reviewed and approved" — that gate doesn't exist in the UI yet.

### Files Changed

| File | Change |
|------|--------|
| `ui/src/pages/SceneWorkspacePage.tsx` | **CREATE** — full workspace page |
| `ui/src/App.tsx` | **MODIFY** — change `scenes/:entityId` route to SceneWorkspacePage |

No backend changes. All data available via existing hooks.

### SceneWorkspacePage Structure

```
SceneWorkspacePage
├── Back button + prev/next scene navigation (reuse from EntityDetailPage)
├── Scene header (name, health badge, RolePresenceIndicators)
├── "View in Script" button
├── ReadinessSummaryBar — 5 colored dots (one per concern group)
├── SceneEntityRoster — characters, location, props links (port from EntityDetailPage)
├── SceneIntentPanel (reuse from DirectionTab.tsx)
└── Tabs (shadcn Tabs, line variant)
    ├── Overview — SceneViewer (scene data + text summary = "preview panel")
    ├── Look & Feel — DirectionAnnotation + generate button
    ├── Sound & Music — DirectionAnnotation + generate button
    ├── Rhythm & Flow — DirectionAnnotation + generate button
    ├── Character & Performance — placeholder (coming soon)
    └── Story World — StoryWorld artifact (project-scoped)
```

Each concern group tab:
- Readiness indicator in the TabsTrigger (colored dot: red/yellow)
- If artifact exists: DirectionAnnotation renders it
- If no artifact: EmptyState with "Let AI fill this" button
- Generate button always visible (regenerate if exists, generate if not)

### Concern Group → Artifact Type Mapping

| Tab | artifact_type | entity_id | status |
|-----|--------------|-----------|--------|
| Look & Feel | `look_and_feel` | sceneId | active |
| Sound & Music | `sound_and_music` | sceneId | active |
| Rhythm & Flow | `rhythm_and_flow` | sceneId | active |
| Character & Performance | `character_and_performance` | sceneId | placeholder |
| Story World | `story_world` | projectId | active (project-scoped) |

### Key Reuses (per AGENTS.md mandatory reuse directives)

- `useEntityNavigation` — prev/next scene nav (existing hook)
- `useArtifactGroups` — readiness computation (existing)
- `useArtifact` — fetch concern group artifact per tab (existing)
- `DirectionAnnotation` — render concern group fields (existing component)
- `SceneIntentPanel` — extracted from DirectionTab and re-exported or inline-reimplemented
- `EmptyState` from `StateViews.tsx` — missing artifact state
- `HealthBadge`, `RolePresenceIndicators` — reused from EntityDetailPage pattern
- `useLongRunningAction` — NOT used here (generation uses `useStartRun` pattern from DirectionTab)

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation. Scene Workspace concept from inbox + ADR-002 + ADR-003 concern groups.

20260301 — Phase 1/2 exploration + plan. Codebase read: EntityDetailPage (830 lines), DirectionTab, DirectionAnnotation, AppShell, IntentMoodPage, concern_groups.py, readiness.py. No backend changes needed — all data available via existing hooks. Readiness computation will be client-side (GREEN deferred, RED/YELLOW only). Scoped out: Generate scene button, media preview panel. SceneIntentPanel and DirectionAnnotation already exist and cover the core rendering needs. Plan approved; ready to implement after human gate.

20260301 — Phase 3 implementation complete. Created SceneWorkspacePage.tsx (550 lines). Exported SceneIntentPanel from DirectionTab.tsx. Updated App.tsx route. ESLint: 0 errors. tsc -b: 0 errors. Build: clean. Smoke test: scene_001 and scene_002 render correctly with 5 concern group tabs, readiness bar showing correct RED/YELLOW dots, entity roster with clickable location/prop links, SceneIntentPanel, Overview tab with SceneViewer content. No app console errors. Duplication: 2.65% (under 5% threshold). Scoped out: "Generate scene" button (film-lane doesn't exist), GREEN readiness state (requires user_approved in group summary endpoint). Story World tab shows project-scoped artifact correctly. Character & Performance tab shows placeholder state with clear "coming in future update" message. All ACs met except the intentionally scoped-out Generate Scene button.

20260302 — Post-ship UI polish (user feedback). Removed redundant ReadinessSummaryBar (dots in tab triggers already show readiness). Removed group icons from tab triggers (too busy with dot + icon + text). Replaced generic Sparkles empty-state icon with each concern group's own colored icon. Redesigned empty states: button moved inside dashed box, layout improved to py-12 flex-col items-center. Fixed layout width bug: max-w-5xl mx-auto in a flex-col context shrinks to max-content of visible children — SceneViewer on Overview forced a wider width than the empty states on other tabs, causing content width to visibly differ per tab. Root fix: added w-full to page container root div (forces explicit width: 100% rather than shrink-to-content, then max-w-5xl caps + mx-auto centers correctly). Secondary fix: added min-w-full to AppShell's ScrollArea inner wrapper (belt-and-suspenders for orientation=both scroll areas). ESLint: 0 errors. tsc -b: 0 errors. Duplication: 3.09% (under 5%). DOM measurements confirm all elements (roster, tabs, dashed box) now consistently 1024px wide at wide viewports.
