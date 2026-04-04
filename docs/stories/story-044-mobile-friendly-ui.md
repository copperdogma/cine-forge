---
id: "044"
title: "Mobile-Friendly UI"
status: "Done"
priority: "Medium"
ideal_refs:
  - "Easy, fun, and engaging"
  - "Accessible by default"
spec_refs:
  - "spec:5"
  - "spec:5.4"
  - "spec:5.5"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "043"
category_refs:
  - "spec:5"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags: []
legacy_system: "2.5 — UI"
---

# Story 044 — Mobile-Friendly UI

**Phase**: 2.5 — UI
**Priority**: Medium
**Status**: Done
**Created**: 2026-02-16
**Ideal Refs**: Easy, fun, and engaging; accessible by default
**Spec Refs**: spec:5 (Operator Console & Interactive UX), spec:5.4 (Human Interaction Model), spec:5.5 (Readiness Indicators)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements and Scene Workspace), `docs/design/decisions.md` (desktop-first shell, mobile not blocked)
**Depends on**: Story 043 (Entity-First Navigation — Done)

## Goal

Make the Operator Console usable on mobile devices (phones and tablets). The current desktop-only layout — fixed sidebar, resizable right panel, multi-column views — is completely broken on small screens. After this story, a user can open their project on a phone, read the script, browse entities, and interact with the chat panel.

## Scope

### In Scope

- Responsive layout for all existing pages (and any added by Story 043)
- Mobile sidebar: off-canvas drawer with hamburger toggle
- Chat panel: full-screen overlay or bottom sheet on mobile
- Touch-friendly tap targets, spacing, and scrolling
- Viewport meta tag and mobile-safe CSS
- Breakpoint system (phone / tablet / desktop)
- Navigation that works with touch (no hover-dependent interactions)

### Out of Scope

- Native app or PWA (this is responsive web only)
- Offline support
- Mobile-specific features (camera, GPS, etc.)
- Performance optimization for low-end devices (separate concern)
- Full light/dark/auto theming or visual-direction changes unrelated to responsive usability

## Acceptance Criteria

- [x] App renders correctly at 375px width (iPhone SE) through 1440px+ (desktop)
- [x] Sidebar collapses to a hamburger menu on screens < 768px
- [x] Chat panel is accessible as a full-screen overlay or sheet on mobile, and the inspector remains reachable without a fixed right column
- [x] All list pages (scenes, characters, locations, props) are single-column and scrollable on mobile
- [x] All detail and workspace pages are readable without page-level horizontal scrolling
- [x] Long tab rows and dense toolbars (scene workspace, settings, similar surfaces) remain operable on mobile without forcing the whole page to overflow horizontally
- [x] Tap targets are minimum 44×44px per Apple HIG
- [x] No hover-only interactions — everything is tap-accessible
- [x] Script view is readable and scrollable on mobile
- [x] Breadcrumbs truncate gracefully on small screens
- [x] Desktop behavior remains intact at `md`+ widths, including the resizable right panel and persistent sidebar
- [x] Tested via Chrome DevTools device emulation at iPhone SE, iPhone 14, iPad, and desktop breakpoints

## Approach Evaluation

- **Simplification baseline**: This is UI shell and layout work, not an AI-reasoning problem. A single LLM call cannot replace responsive layout, touch-safe controls, and browser verification.
- **AI-only**: Wrong fit. Explaining the mobile failure would not make the operator surface usable.
- **Hybrid**: Limited value. Browser tooling is required for verification, but the implementation itself is still deterministic React and CSS work.
- **Pure code**: Correct fit. The repo already has the primitives needed for a responsive shell: Tailwind breakpoints, `Sheet`, existing right-panel state, and page-local layout classes.
- **Repo constraints / ADRs**: ADR-002 and ADR-003 both make the shell, scene workspace, and chat/inspector surfaces first-class. `docs/design/decisions.md` deferred detailed mobile design, but also said not to make choices that prevent it. The right move is to preserve the three-panel desktop experience while introducing a mobile presentation of the same control surfaces.
- **Existing patterns to reuse**: `ui/src/components/ui/sheet.tsx` for mobile drawers and sheets, `ui/src/lib/right-panel.tsx` for shell panel intent, `ChatPanel.tsx` for the shared chat surface, and Tailwind responsive utilities already used throughout the UI.
- **Eval / success measure**: UI static checks plus browser/device verification. Baseline from 2026-04-04 browser emulation at `375px`: the project route still renders the full desktop sidebar and inline chat panel simultaneously, which proves the shell is not mobile-safe today.

## Tasks

- [x] Capture baseline responsive failures and verify breakpoint targets against the current shell and route set
- [x] Add a shared mobile breakpoint seam and keep new responsive state out of page-level business logic where possible
- [x] Refactor `AppShell` so the sidebar becomes an off-canvas drawer under `md`, with a clear hamburger/open-close flow and preserved desktop sidebar behavior
- [x] Refactor right-panel behavior so chat and inspector surfaces open as mobile sheet/overlay views instead of occupying a fixed right column
- [x] Make tab-heavy and multi-column pages responsive, starting with scene workspace, entity detail, continuity, and project settings
- [x] Ensure breadcrumbs, script view, tap targets, and scroll containers remain usable without page-level horizontal scrolling
- [x] Run required UI checks:
  - [x] `pnpm --dir ui run lint`
  - [x] `cd ui && npx tsc -b`
  - [x] `pnpm --dir ui run build`
- [x] Browser-verify iPhone SE, iPhone 14, iPad, and desktop breakpoints; record screenshots, console status, and any remaining issues
- [x] Search related docs and update any responsive/mobile guidance affected by the implementation
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No project data or user edits are at risk; this is presentation-only
  - [x] **T1 — AI-Coded:** The responsive seams are understandable to a future AI session
  - [x] **T2 — Architect for 100x:** No unnecessary device-specific complexity that a simpler shell abstraction could avoid
  - [x] **T3 — Fewer Files:** New helper extraction is justified and oversized files do not grow blindly
  - [x] **T4 — Verbose Artifacts:** Work log captures decisions, verification, and residual risks
  - [x] **T5 — Ideal vs Today:** The operator surface feels more like working with the story and less like administrating desktop chrome

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning module**: `ui/src/components/AppShell.tsx` owns shell presentation and navigation. `ui/src/lib/right-panel.tsx` owns right-panel intent/state. Page components should only own their local grid/tab layout fixes.
- **Data contracts**: No API or schema changes are expected. This is a UI-only story unless implementation uncovers a real backend contract problem, which is unlikely from current exploration.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, ADR-002, ADR-003, `docs/design/decisions.md`, Story 011d, Story 043, and Story 126. No separate mobile ADR exists; the live decision docs point to preserving the story-first shell while finally making it usable on phones and tablets.
- **Large-file risk**: `AppShell.tsx`, `SceneWorkspacePage.tsx`, and `EntityDetailPage.tsx` are already oversized. The implementation should prefer small helper extraction and shared responsive primitives over adding more inline branch logic.

## Files to Modify

- `ui/src/components/AppShell.tsx` — responsive shell, mobile drawer, mobile panel triggers (`808`)
- `ui/src/lib/right-panel.tsx` — minimal mobile panel intent/state expansion if required (`63`)
- `ui/src/components/ChatPanel.tsx` — mobile-safe chat sheet/header sizing if shell changes expose issues (`395`)
- `ui/src/components/ui/tabs.tsx` — shared scrollable or narrow-screen tab behavior (`91`)
- `ui/src/pages/ProjectHome.tsx` — mobile-safe screenplay header, export trigger, and script container layout (`594`)
- `ui/src/components/ScreenplayEditor.tsx` — tighter mobile gutters and safe width constraints for the screenplay surface (`465`)
- `ui/src/components/PipelineBar.tsx` — tap-accessible mobile phase detail sheet (`347`)
- `ui/src/components/ExportModal.tsx` — scrollable mobile export dialog with stacked action grids (`381`)
- `ui/src/pages/IntentMoodPage.tsx` — flex-item width fixes and stacked mobile actions (`622`)
- `ui/src/pages/SceneWorkspacePage.tsx` — responsive tab-heavy workspace layout (`766`)
- `ui/src/pages/EntityDetailPage.tsx` — stack dense grids and sections on mobile (`890`)
- `ui/src/pages/ContinuityPage.tsx` — stack summary cards and controls on mobile (`206`)
- `ui/src/components/ProjectSettings.tsx` — responsive settings tabs/dialog layout (`458`)
- `ui/src/lib/use-mobile.ts` — shared breakpoint helper if no existing hook fits (new)

## Redundancy / Removal Targets

- Any desktop-only shell affordance that remains visible but unusable on mobile
- Any one-off page-level breakpoint hacks that should be centralized in a shared shell or tabs helper
- Any duplicate mobile detection logic if a shared helper lands

## Notes

- Tailwind's responsive utilities (`sm:`, `md:`, `lg:`) should handle most of this without custom CSS.
- The resizable right panel drag handle is a desktop interaction — on mobile, chat should be a modal or overlay triggered by a visible mobile control.
- Story 043 added the final route set this work needs to cover.
- Baseline browser evidence on 2026-04-04: at `375px` on `/story-144-ui-check`, the shell still renders the full left sidebar and the inline chat panel simultaneously. That is the primary breakage to fix first.
- Exploration found an `XS` scope expansion that should stay folded into this story: shared tab-row/mobile overflow handling for scene workspace and settings. A shell-only fix would still leave key routes failing the acceptance criteria.

## Plan

### Baseline / Success Measure

- This is a UI-only story, so the proof surface is:
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
  - browser verification at iPhone SE, iPhone 14, iPad, and desktop widths
- Current measured baseline from browser emulation on 2026-04-04:
  - At `375px`, the shell still shows the full desktop sidebar and fixed inline chat panel on the same screen.
  - `ui/src/components/ui/tabs.tsx` currently renders `TabsList` as `inline-flex w-fit`, which is a likely cause of tab overflow on scene workspace/settings at narrow widths.
  - Current code already hides the keyboard shortcut hint on small screens, but there is no mobile navigation/chat affordance replacing the missing desktop controls.
- Story success means the same routes work across mobile/tablet/desktop without page-level horizontal overflow, and the desktop shell/resizer behavior still works at `md`+ widths.

### Repo-Fit / Chosen Approach

- Choose **pure code using existing shell primitives**.
- Why this is the right fit here:
  - `ui/src/components/ui/sheet.tsx` already exists and is the repo-native primitive for an off-canvas drawer or mobile chat/inspector sheet. No new dependency is needed.
  - ADR-002 and ADR-003 treat the shell, chat, and scene workspace as the real product surface. A route split or separate "mobile mode" would move away from that shared story workspace.
  - `docs/design/decisions.md` resolves the desktop right panel as fixed-width and desktop-first, but explicitly says not to block mobile. This supports a branch in presentation, not a second interaction model.
  - Story 126 already identified `AppShell.tsx` as a decomposition hotspot, so the implementation should add a small shared seam instead of compounding inline conditionals.
- Rejected alternatives:
  - **Theme/story 046 work first**: wrong priority. That is cosmetic relative to the current mobile usability failure.
  - **Route-level mobile fork**: too heavy and would duplicate shell behavior across device classes.
  - **Pure CSS-only retrofit**: insufficient because the right panel and sidebar have real interaction/state differences on mobile.

### Recommended Scope Adjustment

- **XS, already folded into this story**: add shared tab-row/mobile overflow handling in `ui/src/components/ui/tabs.tsx` and patch the most affected routes (`SceneWorkspacePage`, `ProjectSettings`, `EntityDetailPage`, `ContinuityPage`). Without this, the shell could become mobile-friendly while key routes still fail the no-horizontal-scroll acceptance criteria.

### Task 1 — Add a Shared Mobile Shell Seam

- **Files**: `ui/src/lib/use-mobile.ts` (new, if needed), `ui/src/components/AppShell.tsx`, `ui/src/lib/right-panel.tsx`
- **Change**:
  - Add a small breakpoint helper instead of scattering `window.matchMedia` logic across pages.
  - Keep desktop shell behavior intact while introducing a mobile-specific presentation path inside `AppShell`.
  - Extend right-panel state only if needed to open chat or inspector intentionally on mobile.
- **Impact / risk**:
  - `AppShell.tsx` is already `684` lines, so any state or layout extraction should happen before adding more branches.
  - Avoid moving page-specific layout concerns into the shell.
- **Done**:
  - The shell can tell whether it is in mobile mode through one shared seam.
  - Desktop shell behavior is unchanged.

### Task 2 — Convert Desktop Chrome into Mobile Drawer + Panel Sheet

- **Files**: `ui/src/components/AppShell.tsx`, `ui/src/components/ChatPanel.tsx`, `ui/src/lib/right-panel.tsx`
- **Change**:
  - Sidebar becomes an off-canvas drawer below `md`.
  - Chat and inspector surfaces become a mobile sheet or overlay instead of a fixed right column.
  - Remove or hide the desktop drag affordance on mobile while preserving it on desktop.
  - Ensure breadcrumbs and header controls remain reachable with touch-sized buttons.
- **Impact / risk**:
  - The shell is the highest-leverage fix, but it is also the easiest place to introduce regressions in route switching and panel state.
  - Reuse `ChatPanel` rather than creating a mobile-only chat implementation.
- **Done**:
  - At `375px`, only the main content is persistent by default; nav and chat or inspector are reachable via intentional mobile controls.

### Task 3 — Patch Page-Level Overflow Hotspots

- **Files**: `ui/src/components/ui/tabs.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/EntityDetailPage.tsx`, `ui/src/pages/ContinuityPage.tsx`, `ui/src/components/ProjectSettings.tsx`
- **Change**:
  - Make shared tabs horizontally scroll or otherwise remain usable on narrow screens without blowing out the page width.
  - Stack known multi-column hotspots and dense control bars on mobile.
  - Keep the fixes targeted; do not do a blanket visual redesign.
- **Impact / risk**:
  - `SceneWorkspacePage.tsx` (`766`) and `EntityDetailPage.tsx` (`890`) are already oversized, so prefer class-level surgery or small extracted subcomponents over inline sprawl.
  - Shared `tabs.tsx` changes can affect many routes, so verify both workspace/settings and unaffected desktop tabs.
- **Done**:
  - Known hotspot pages are readable and operable on mobile without whole-page horizontal scroll.

### Task 4 — Static Checks and Browser Verification

- **Files**: changed UI files only
- **Change**:
  - Run lint, typecheck, and production build.
  - Run browser verification at iPhone SE, iPhone 14, iPad, and desktop widths.
  - Check console output and capture screenshots for the changed golden paths.
- **Golden paths**:
  - project home or script route
  - open and close mobile nav
  - open and close mobile chat or inspector
  - scene workspace tab navigation
  - entity detail page
  - project settings
- **Fallback runbook**: `docs/runbooks/browser-automation-and-mcp.md` if browser tooling is blocked.
- **Done**:
  - All acceptance criteria have direct evidence from static checks and browser verification.

### Structural Health Check

- Planned touch points and current sizes:
  - `ui/src/components/AppShell.tsx` — `684`
  - `ui/src/lib/right-panel.tsx` — `63`
  - `ui/src/components/ChatPanel.tsx` — `395`
  - `ui/src/components/ui/tabs.tsx` — `91`
  - `ui/src/pages/SceneWorkspacePage.tsx` — `766`
  - `ui/src/pages/EntityDetailPage.tsx` — `890`
  - `ui/src/pages/ContinuityPage.tsx` — `206`
  - `ui/src/components/ProjectSettings.tsx` — `458`
  - `ui/src/lib/use-mobile.ts` — new
- Oversized-file rule:
  - `AppShell.tsx`, `SceneWorkspacePage.tsx`, and `EntityDetailPage.tsx` need surgical edits or extraction-first changes.
  - No new cross-layer contracts or schema/event changes are expected.

### Redundancy Plan

- Remove any mobile-only branch that duplicates existing shell or chat rendering unnecessarily.
- If a shared mobile hook lands, do not leave inline `window.innerWidth` conditionals scattered across multiple files.
- Keep the desktop resizer logic desktop-only instead of letting dead mobile guards accumulate around it.

### Human-Approval Blockers

- None expected:
  - no new dependency
  - no backend/API/schema change
  - no public route redesign
- Main implementation risk:
  - preserving desktop shell behavior while extracting enough mobile state to make the shell usable. If the shell wants a deeper decomposition than this story can safely absorb, stop and surface it rather than blindly growing `AppShell.tsx`.

## Work Log

20260404-1048 — exploration: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, `docs/design/decisions.md`, Story 011d, Story 043, and Story 126 before tracing the current UI. Files most likely to change=`ui/src/components/AppShell.tsx`, `ui/src/lib/right-panel.tsx`, `ui/src/components/ui/tabs.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/pages/EntityDetailPage.tsx`, `ui/src/pages/ContinuityPage.tsx`, `ui/src/components/ProjectSettings.tsx`, and possibly `ui/src/components/ChatPanel.tsx`. Key risks=`AppShell.tsx` is 684 lines, `SceneWorkspacePage.tsx` is 766, and `EntityDetailPage.tsx` is 890, so the work must stay surgical. Next=`capture one real mobile baseline and write the implementation plan before any code changes`.
20260404-1054 — baseline: started the local backend and Vite app, then ran browser emulation at `375px` against `/story-144-ui-check`. Result=`mobile shell is still desktop-only`: the full left sidebar and the inline fixed chat panel render simultaneously, leaving too little room for the story surface. Code trace also showed `ui/src/components/ui/tabs.tsx` uses `inline-flex w-fit`, making long tab rows a likely second mobile failure point. Next=`fold shared tab overflow handling into scope and present the plan for approval`.
20260404-1102 — planning: chose a repo-fit responsive-shell approach using the existing `Sheet` primitive instead of a route fork or theme rewrite. Added missing workflow gates, explicit file and risk inventory, and an `XS` scope expansion for shared tab overflow handling plus the worst page-level layout hotspots. Main constraint=`preserve desktop three-panel behavior at `md`+ while introducing a mobile drawer and mobile chat or inspector sheet under `md``. Next=`human approval to begin implementation`.
20260404-1111 — implementation-start: user approved the plan, so Story 044 moved to `In Progress` and the baseline-capture task was marked complete. Next=`extract a shared mobile breakpoint seam, convert the desktop sidebar/chat chrome into mobile drawer + sheet behavior, then patch the worst page-level overflow hotspots before running checks`.
20260404-1128 — implementation: added `ui/src/lib/use-mobile.ts` plus an `initialOpen` seam in `ui/src/lib/right-panel.tsx`, then rewired `ui/src/components/AppShell.tsx` so mobile uses a left navigation drawer and right chat sheet while desktop keeps the persistent sidebar and resizable right panel. Extracted shared sidebar and panel content inside the shell to avoid duplicating the route tree, tightened breadcrumb truncation, and reduced page padding on small screens. Patched `ui/src/components/ui/tabs.tsx` with an opt-in `scrollable` mode, then applied targeted responsive fixes to `SceneWorkspacePage`, `EntityDetailPage`, `ContinuityPage`, and `ProjectSettings` so dense grids, toolbars, and tab rows stop forcing page-level overflow. Next=`run static checks and browser verification across the target breakpoints`.
20260404-1138 — verification: `pnpm --dir ui run lint` passed with the same 5 pre-existing `react-refresh/only-export-components` warnings in unrelated/shared files, `cd ui && npx tsc -b` passed, `pnpm --dir ui run build` passed with the existing Vite chunk-size warning only, and `pnpm methodology:compile` plus `pnpm methodology:check` both passed after the story/status updates. Runtime smoke passed: `GET /api/health -> {"status":"ok","version":"2026.04.04-03"}` and `GET http://localhost:5174/story-144-ui-check` returned HTTP `200`. Browser verification passed on `story-144-ui-check` and `the-mariner`: mobile first-load at `375px` showed a closed-by-default chat sheet plus hamburger drawer, the drawer opened and navigated correctly, the chat sheet opened without current console warnings, character detail and scene workspace no longer caused page-level horizontal overflow, the main scene tab row remained operable on mobile, the settings dialog fit within the viewport, `390px` iPhone-14 width still avoided overflow, `820px` iPad width restored the persistent sidebar + chat column, and `1440px` desktop preserved the original three-panel shell. Captured browser screenshots confirmed the mobile shell and scene-workspace layouts visually. Residual note=`character detail on the sample project still triggered a pre-existing design-study 404 during one verification pass, and the real screenplay view on the-mariner still logs an existing CodeMirror \"Unknown highlighting tag transition\" warning; neither was introduced by this responsive pass`. Related docs=`story file plus regenerated methodology surfaces only; no broader design-doc changes were required`. Next=`/validate`.
20260404-1210 — refinement: user-reported follow-up issues on mobile exposed three additional seams after the first pass: `/the-mariner-65` still allowed sideways movement inside the screenplay route, pipeline phase details were effectively hover-only because touch taps only flashed the tooltip, and the export dialog clipped at the top on long mobile content. Traced the script-page issue to a combination of the shared shell content wrapper and the screenplay header/container sizing, then patched `AppShell`, `ProjectHome`, and `ScreenplayEditor` so the route shrinks cleanly at `375px`. Replaced the mobile-only `PipelineBar` tooltip interaction with a bottom-sheet phase detail view that keeps sub-items readable and still exposes explicit navigation. Rebuilt `ExportModal` as a max-height, scrollable mobile dialog with stacked single-column action grids. A subsequent route sweep found one more real offender on `IntentMoodPage`, so that page now uses `w-full min-w-0` plus stacked mobile action rows. Verification=`pnpm --dir ui run lint` (same 5 pre-existing warnings), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, targeted browser checks for `/the-mariner-65`, the phase sheet, and the export dialog, plus mobile sweeps across top-level routes on `the-mariner-65`. Sample detail routes on `story-144-ui-check` still showed offscreen pipeline-phase buttons inside the bar itself, but `document.body.scrollWidth` and `document.documentElement.scrollWidth` both remained `375`, so that is internal horizontal bar content rather than renewed page-level overflow. Next=`/validate`, unless we want to continue polishing lower-priority mobile visuals before validation.
20260404-1317 — polish: user asked for a tighter screenplay header on mobile and a broader usability pass. `ProjectHome` now keeps the script icon and title on the same row, moves the mobile export control into the metadata row as an icon action next to the import-status pill, and hides the larger text export button below `sm`. `PipelineBar` also got a compact mobile trigger treatment so phones no longer spend as much horizontal space on completion badges that are nonessential once the phase sheet is tap-accessible. Verification=`pnpm --dir ui run lint` (same 5 pre-existing warnings), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, targeted browser verification on `/the-mariner-65` confirming the new header layout, export icon placement, export dialog, chat sheet, and nav drawer, plus an automated mobile sweep across top-level routes on `the-mariner-65` and representative detail routes on `story-144-ui-check`. Result=`no page-level horizontal overflow and no off-screen interactive controls outside intentional horizontal scrollers were found in that sweep`. Residual note=`the real screenplay route still logs the same pre-existing CodeMirror warning`. Next=`/validate` unless we want another cosmetic/mobile polish pass before handing it to validation.
20260404-1326 — full mobile audit: user asked for a detailed check on every known page using an older, artifact-heavy project. Audit target=`the-mariner-60` because it is an older project with `156` artifact groups, `2` runs, `12` character pages, `11` location pages, `21` prop pages, stale pipeline nodes, and real artifact/run detail routes. Audited route surface=`/`, `/new`, `/theme`, project home, intent, scenes list, scene detail (`scene_001`), characters list, character detail (`mariner`), locations list, location detail (`city_centre`), props list, prop detail (`airtag`), continuity, inbox, run, runs, run detail (`run-48df7665`), artifacts list, and artifact details for `scene`, `script_bible`, and `character_bible`. Also re-checked nav drawer, chat sheet, export modal, and header controls at `375px`. Findings=`no page-level horizontal overflow and no off-screen interactive controls outside intentional horizontal scrollers on any audited route after the previous fixes`; the one usability inconsistency still visible was that list/detail/workspace pages kept the large desktop-style Export button on mobile even after the screenplay home was compacted. Fix=`EntityListPage`, `EntityDetailPage`, and `SceneWorkspacePage` now use the same mobile icon-only export treatment as `ProjectHome`, while desktop keeps the text button`. Verification=`pnpm --dir ui run lint` (same 5 pre-existing warnings), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, plus automated route sweeps across the full route set named above. Residual note=`the older real-data audit project still logs the existing CodeMirror warning on screenplay/editor surfaces, but no new mobile layout issues surfaced in the audited pages`. Next=`/validate`.
20260404-1408 — deep mobile cleanup: user reported that the Characters screen still felt cut off on the right and that completed phases in the mobile pipeline strip had become visually identical green checkmarks. Root cause split into two layers. Page-level fixes=`EntityListControls` now stacks control groups on phones instead of forcing a single desktop toolbar row, `PipelineBar` keeps the original phase icons in compact/mobile mode and uses the existing status dot as the completion signal, `SceneWorkspacePage`/`EntityDetailPage`/`ProjectInbox`/`ProjectRun`/`ArtifactDetail` all got narrower mobile header and action-row layouts, and the scene/entity reference-library controls now use mobile-safe stacking plus scrollable filter tabs. Shell-level fix=`ui/src/components/ui/scroll-area.tsx` now forces the Radix viewport content wrapper to stay block-level, full-width, and `min-w-0`; before this, one internal horizontal scroller could silently expand the entire app shell’s scrollable content area to ~`1024px`, which is why some routes still looked desktop-wide on mobile even after local patches. Verification=`pnpm --dir ui run lint` (same 5 pre-existing fast-refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `.venv/bin/python -m pytest -m unit` (`660 passed, 144 deselected`), and a route sweep at `375px` across `/`, `/new`, `/theme`, plus the full `the-mariner-60` project surface: home, intent, scenes, `scene_001`, characters, `mariner`, locations, `city_centre`, props, `airtag`, continuity, inbox, run, runs, `run-48df7665`, artifacts, `scene/scene_001/2`, `script_bible/project/1`, and `character_bible/mariner/1`. The sweep used the actual inner shell scroll container, scrolled each route end-to-end, and ignored intentional horizontal scrollers when checking for off-screen controls. Result=`all audited routes are now clean for full-length mobile use on the verified surface`. Tooling note=`make test-unit` still resolves to a system Python without `pytest` in this shell, so the documented project-venv command remains the reliable validation path`. Residual note=`the pre-existing CodeMirror highlighting warning is still present on screenplay/editor surfaces and was not changed by this work`. Next=`/validate`.
20260404-1418 — validation: reread Story 044 against `docs/ideal.md`, `docs/spec.md` (`spec:5`, `spec:5.4`, `spec:5.5`), `docs/methodology/state.yaml`, ADR-002, ADR-003, and `docs/design/decisions.md`, then reran the required gates fresh from validation: `make test-unit PYTHON=.venv/bin/python` (`660 passed, 144 deselected`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (same 5 pre-existing fast-refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check`. Fresh browser validation used Playwright at `375px`, `390px`, `820px`, and `1440px`: manually verified the mobile shell’s nav drawer and chat sheet on `/the-mariner-60`, captured a fresh scene-workspace mobile screenshot, and reran an automated route sweep at `375px` across home, intent, scenes, `scene_001`, characters, `mariner`, `city_centre`, `airtag`, continuity, inbox, run, `run-48df7665`, and `artifacts/scene/scene_001/2`, scrolling each route end-to-end while ignoring intentional horizontal scrollers. Validation result=`mobile layout and responsive behavior are broadly correct on the audited route surface, but the explicit 44×44 tap-target acceptance criterion is still unmet`. Evidence=`several mobile icon buttons remain below the stated minimum: chat toggle is 32×32 in ui/src/components/AppShell.tsx, the screenplay home export button is 32×32 in ui/src/pages/ProjectHome.tsx, and the scene/entity list/detail export buttons are 40×40 in ui/src/pages/SceneWorkspacePage.tsx, ui/src/pages/EntityDetailPage.tsx, and ui/src/pages/EntityListPage.tsx`. Residual note=`browser console still shows the pre-existing CodeMirror highlighting warnings on screenplay surfaces and pre-existing `design-study/*` 404s on some entity pages; these were observed in validation but are outside the mobile-responsive change itself`. Next=`keep Story 044 open for a targeted tap-target pass, then rerun focused mobile validation`.
20260404-1529 — tap-target pass: fixed the remaining mobile hit-area gap by raising every story-relevant mobile icon control to at least `44×44px` without bloating desktop chrome. Updated controls=`ui/src/components/AppShell.tsx` (mobile nav toggle, mobile chat toggle, chat-sheet close), `ui/src/components/chat/Composer.tsx` (send and stop buttons, plus explicit aria labels), `ui/src/pages/ProjectHome.tsx` (project export), `ui/src/pages/SceneWorkspacePage.tsx` (scene export), `ui/src/pages/EntityDetailPage.tsx` (entity export), and `ui/src/pages/EntityListPage.tsx` (list export). Verification=`make test-unit PYTHON=.venv/bin/python` (`660 passed, 144 deselected`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (same 5 pre-existing fast-refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm methodology:compile`, and `pnpm methodology:check`. Focused browser verification=`direct Python Playwright script at `375px` against `/the-mariner-60`, `/the-mariner-60/scenes/scene_001`, `/the-mariner-60/characters`, and `/the-mariner-60/characters/mariner` measured the updated buttons directly; all tested controls now report `44×44` (`Open navigation`, `Open chat`, `Close chat`, `Send message`, `Export project`, `Export scene`, `Export characters`, `Export entity`). Screenshots captured under `/tmp/cineforge-mobile-verify/``. Residual note=`the pre-existing CodeMirror warning is still present on screenplay/editor surfaces, and the character-detail route still emits the earlier 404 for a missing design-study resource; neither changed in this pass`. Next=`/validate`.
20260404-1542 — revalidation: reviewed the tap-target pass against the same Story 044 acceptance criteria and decision context, then accepted the implementation as clean. Fresh evidence reused the rerun commands from the tap-target pass because they were executed after the last code changes: `make test-unit PYTHON=.venv/bin/python` (`660 passed, 144 deselected`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (same 5 pre-existing fast-refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm methodology:compile`, and `pnpm methodology:check`. Browser evidence=`focused Playwright verification at `375px` measured the affected controls directly and confirmed they are all `44×44``. Validation result=`all Story 044 acceptance criteria are now met on the verified route surface; only story closure bookkeeping remains`. Residual note=`the pre-existing CodeMirror warning and missing design-study-resource 404 still appear on some existing routes, but neither was introduced or worsened by this story`. Next=`/mark-story-done`.
20260404-1602 — validation: reran the full validation suite from the current worktree rather than relying on the earlier pass: `make test-unit PYTHON=.venv/bin/python` (`660 passed, 144 deselected`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (same 5 pre-existing fast-refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm methodology:check`. Fresh browser verification used a direct Python Playwright script because MCP browser transport has been unstable in this environment; it rechecked `/the-mariner-60` at `375px`, `390px`, `820px`, and `1440px`, confirmed the expected mobile-vs-desktop shell transition, measured all affected mobile controls at `44×44`, and verified no page-level horizontal overflow on `/the-mariner-60`, `/the-mariner-60/scenes/scene_001`, `/the-mariner-60/characters`, `/the-mariner-60/characters/mariner`, `/the-mariner-60/inbox`, and `/the-mariner-60/artifacts/scene/scene_001/2`. Validation result=`Story 044 implementation remains clean; all acceptance criteria are met and only close-out bookkeeping remains`. Residual note=`console still shows the pre-existing CodeMirror warning and one existing 404 for a missing design-study resource; neither appears newly introduced by this story`. Next=`/mark-story-done`.
20260404-1608 — closure: marked Story 044 Done after the fresh validation pass confirmed the mobile shell, dense route layouts, and touch targets are clean on the audited route surface. Completion evidence=`make test-unit PYTHON=.venv/bin/python` (`660 passed, 144 deselected`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (same 5 pre-existing fast-refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm methodology:check`, and direct Playwright verification at `375px`, `390px`, `820px`, and `1440px``. Residual note=`pre-existing CodeMirror warning and one existing design-study 404 remain outside the Story 044 change scope`. Next=`/check-in-diff`.
