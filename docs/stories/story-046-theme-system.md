---
id: "046"
title: "Theme System (Light/Dark/Auto + Palettes)"
status: "Done"
priority: "Medium"
ideal_refs: []
spec_refs: []
adr_refs: []
depends_on: []
category_refs:
  - "spec:5"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: "2.5 — UI"
---

# Story 046 — Theme System (Light/Dark/Auto + Palettes)

**Phase**: 2.5 — UI
**Priority**: Medium
**Status**: Done
**Updated**: 2026-04-07 — validation completed, methodology surfaces refreshed, and the story was closed via `/mark-story-done`.

## Goal

Give users control over the visual appearance of the Operator Console with light/dark/auto mode switching and multiple color palette choices for each mode. Build on the existing 4 dark palettes (Obsidian, Ember, Slate, Noir) and create corresponding light palettes. Persist the user's choice in project settings.

## Context

The ThemeShowcase page (`/theme`) already defines 4 dark theme palettes as CSS variable overrides and demonstrates live switching. However:

- The app is dark-only (hardcoded `.dark` class on root div)
- `next-themes` is installed but the `<ThemeProvider>` is never mounted
- No light mode CSS variables are defined (`:root` block has placeholder values)
- Theme preference is not persisted
- No production-accessible theme switcher exists

## Acceptance Criteria

- [x] User can switch between Light, Dark, and Auto (system preference) modes
- [x] At least 4 dark palettes available: Obsidian, Ember, Slate, Noir (existing)
- [x] At least 4 corresponding light palettes available
- [x] Theme preference (mode + palette) persists across sessions via project settings
- [x] Theme switcher is accessible from the app shell (e.g., settings menu or header)
- [x] Auto mode respects `prefers-color-scheme` and applies the user's chosen palette
- [x] Sonner toast component correctly inherits the active theme
- [x] ThemeShowcase page updated to preview both light and dark palettes
- [x] No flash of wrong theme on page load (SSR-safe or pre-render class injection)
- [x] All existing UI components render correctly in both light and dark modes

## Tasks

### Phase 1 — Theme Infrastructure

- [x] Wire up `next-themes` `<ThemeProvider>` in `ui/src/App.tsx` (or a focused theme wrapper imported there) with `attribute="class"` strategy
- [x] Remove the hardcoded `.dark` class from the app root in `ui/src/App.tsx`
- [x] Extract the existing ThemeShowcase palette definitions from `ui/src/pages/ThemeShowcase.tsx` into a shared theme module under `ui/src/lib/` or `ui/src/components/`
- [x] Define light mode CSS variables in `ui/src/index.css` (matching Slate as the default baseline palette)
- [x] Manage palette selection alongside mode using the current frontend architecture, not a stale `ui/operator-console` context path
- [x] Persist `theme_mode` + `theme_palette` through the existing project settings `ui_preferences` path instead of page-local state

### Phase 2 — Light Palettes

- [x] Design 4 light palettes corresponding to the dark ones:
  - **Obsidian Light** — Cool whites with blue-steel accents
  - **Ember Light** — Warm whites with amber/copper accents
  - **Slate Light** — Neutral whites with sage/teal accents (default)
  - **Noir Light** — Crisp whites with gold accents
- [x] Verify contrast ratios meet WCAG AA for all palette × mode combinations
- [x] Test all shadcn/ui component states (hover, focus, disabled) in each light palette

### Phase 3 — Theme Switcher UI

- [x] Add a theme switcher to the current shell/settings flow (`ui/src/components/AppShell.tsx` and/or `ui/src/components/ProjectSettings.tsx`)
- [x] Mode selector: Light / Dark / Auto toggle (sun/moon/auto icons)
- [x] Palette selector: visual swatches showing each palette's primary + accent colors
- [x] Preview palette on hover before committing
- [x] Persist selection through the existing `updateProjectSettings()` API path using `ui_preferences`

### Phase 4 — Polish & Verification

- [x] Update `ui/src/pages/ThemeShowcase.tsx` to display all palettes in both modes using the shared palette source
- [x] Fix Sonner toast integration in `ui/src/components/ui/sonner.tsx` so it follows the resolved theme
- [x] Audit all pages for light mode rendering issues (contrast, borders, shadows)
- [x] Handle edge case: project settings unavailable → fall back to system mode + Slate palette
- [x] Prevent FOUC by restoring the saved theme class/palette before React hydration (likely via `ui/index.html` or the earliest bootstrap point)

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Central Tenets

- [x] **T0 — Data Safety:** Theme preferences stay in project-backed `ui_preferences`, and project routes still fall back safely to system mode + Slate when no saved preference exists.
- [x] **T1 — AI-Coded:** Theme ownership is explicit in `ui/src/lib/theme.ts`, `ui/src/lib/app-theme-context.ts`, `ui/src/components/AppThemeProvider.tsx`, and `ui/src/components/ProjectAppearanceSection.tsx` instead of being hidden in page-local state.
- [x] **T2 — Architect for 100x:** This change reuses `next-themes`, existing project settings persistence, and CSS variables instead of adding a parallel settings or schema system.
- [x] **T3 — Fewer Files:** The implementation added focused theme modules to keep `ProjectSettings.tsx` and `AppShell.tsx` from absorbing more inline state and preview logic.
- [x] **T4 — Verbose Artifacts:** The work log records exploration, the nested-button regression found during browser verification, the fix, and the verification evidence.
- [x] **T5 — Ideal vs Today:** The app no longer hardcodes dark mode; shared theme ownership and project-backed appearance controls move the operator surface closer to the product ideal of being easy and pleasant to use.

## Technical Notes

- **Color format**: OKLCH (perceptually uniform). All palettes use `oklch()` values for CSS variables.
- **Persistence**: Per AGENTS.md, user preferences go in project settings / `project.json`. In the current app this should flow through the existing `ui_preferences` settings path. Use `localStorage` only as a fast cache to prevent FOUC, synced from the backend-backed preference.
- **`next-themes` config**: Use `attribute="class"`, `defaultTheme="system"`, `storageKey="cineforge-mode"`.
- **Palette application**: CSS variable overrides via `document.documentElement.style.setProperty()` on the resolved theme element.
- **Existing code**: `ui/src/pages/ThemeShowcase.tsx` already contains the 4 dark palette definitions, `ui/src/App.tsx` still hardcodes `.dark`, `ui/src/components/ProjectSettings.tsx` already persists project settings, and `ui/src/components/ui/sonner.tsx` already reads `next-themes`.

## Dependencies

- `next-themes` (already installed, ^0.4.6)
- shadcn/ui CSS variable system (already in place)

## Files to Modify

- `ui/src/App.tsx` — remove hardcoded `.dark`, mount theme provider/wrapper
- `ui/src/index.css` — define light palettes and shared token defaults
- `ui/src/pages/ThemeShowcase.tsx` — consume shared palette definitions instead of page-local constants
- `ui/src/components/ProjectSettings.tsx` — expose appearance controls through the current settings surface
- `ui/src/components/AppShell.tsx` — optional quick-access affordance if the chosen UX needs it
- `ui/src/components/ui/sonner.tsx` — ensure toasts inherit the resolved theme
- `ui/src/lib/types.ts` — typed frontend support for appearance preferences if needed
- `ui/src/lib/api/projects.ts` — reuse or extend project settings persistence wiring
- `src/cine_forge/api/models.py` — only if typed backend support for appearance preferences is needed beyond free-form `ui_preferences`
- `src/cine_forge/api/service.py` — only if backend merge behavior for `ui_preferences` needs adjustment
- `ui/index.html` — optional pre-hydration theme bootstrap for FOUC prevention

## Plan

### Baseline / Success Measure

- This is pure UI/state plumbing, not an AI-reasoning problem. No eval or model-selection comparison is needed.
- Current baseline from exploration:
  - `ui/src/App.tsx` hardcodes a `.dark` wrapper around the entire app instead of mounting `next-themes`.
  - `ui/index.html` also hardcodes `<html class="dark">`, so theme choice cannot follow project settings or system preference.
  - `ui/src/pages/ThemeShowcase.tsx` contains the only palette definitions and mutates `.dark` manually, which makes it a demo page rather than shared app infrastructure.
  - `ui/src/lib/hooks/projects.ts` already exposes a repo-native `useStickyPreference()` seam backed by project `ui_preferences`, and `src/cine_forge/api/service.py` already merges `ui_preferences` updates into `project.json`.
  - `ui/src/components/ui/sonner.tsx` already reads `next-themes`, so once the provider is mounted it should inherit the resolved mode without backend work.
- Story success means:
  - Light / dark / auto mode plus four palette choices are available through the real app shell/settings flow.
  - Theme mode and palette persist through project-backed `ui_preferences`, with local storage used only as a cache for pre-hydration restore.
  - `/theme` previews both modes from the shared palette source.
  - Desktop and mobile verification both show correct application, clean console output, and no obvious FOUC.

### Repo-Fit / Chosen Approach

- Chosen approach: mount a focused app theme provider around the existing router, extract shared palette definitions into a dedicated theme module, persist `theme_mode` and `theme_palette` through project `ui_preferences`, and expose controls through Project Settings.
- Why this is the right fit here:
  - It uses the repo's existing persistence pattern instead of inventing a second client-only settings store.
  - It keeps project-scoped preferences in `project.json`, matching AGENTS guidance.
  - It removes duplicated theme logic (`App.tsx`, `index.html`, `ThemeShowcase`) instead of layering more page-local state on top.
  - It treats the settings dialog as the shell entry point, which already satisfies the operator-surface requirement without inventing a new header control.
- Rejected alternatives:
  - LocalStorage-only theming: wrong persistence layer for anything the user would miss across machines or sessions.
  - Leaving theme logic inside `ThemeShowcase`: wrong ownership; that page is a demo surface, not the source of truth.
  - Extending backend schema/models just for theme keys: unnecessary because `ui_preferences` already supports this exact shape.

### Structural Health Check

- `make check-size` run during planning on 2026-04-07.
- Likely touch points and current line counts:
  - `ui/src/App.tsx` — `81`
  - `ui/src/index.css` — `165`
  - `ui/src/pages/ThemeShowcase.tsx` — `363`
  - `ui/src/components/ProjectSettings.tsx` — `458`
  - `ui/src/components/AppShell.tsx` — `836`
  - `ui/src/components/ui/sonner.tsx` — `40`
  - `ui/src/lib/types.ts` — `671`
  - `ui/src/lib/api/projects.ts` — `109`
  - `src/cine_forge/api/models.py` — `510`
  - `src/cine_forge/api/service.py` — `1145`
- Plan risks:
  - `AppShell.tsx` and `ProjectSettings.tsx` are already large enough that more inline appearance UI would be a boundary mistake.
  - `ui/src/lib/types.ts` and the backend model/service files are already oversized; avoid touching them unless exploration later proves a typed API gap that `ui_preferences` cannot cover.
- Structural response:
  - Extract a focused theme module and a focused settings section/component instead of adding more inline logic to `ProjectSettings.tsx` or `AppShell.tsx`.
  - Keep backend and API types untouched unless implementation proves that generic `ui_preferences` is insufficient.
  - No new cross-layer schema or event type is expected.

### Recommended Scope Adjustment

- `XS`, already folded into this story: add a focused appearance settings section/component and a focused app-theme provider/module instead of embedding all theme state, swatch rendering, and DOM synchronization directly into `ProjectSettings.tsx` or `AppShell.tsx`.
- This is not a new feature. It is the smallest repo-fit extraction needed to keep the existing large files from getting worse while still delivering the story honestly.

### Task 1 — Establish Shared Theme Ownership

- Files:
  - `ui/src/App.tsx`
  - `ui/index.html`
  - new focused theme module under `ui/src/lib/` or `ui/src/components/`
  - `ui/src/index.css`
- Change:
  - Mount `next-themes` once at app level and remove the hardcoded `.dark` wrapper from `App.tsx`.
  - Replace the hardcoded `<html class="dark">` bootstrap with a pre-hydration restore path that reads cached mode/palette and applies the right class/attribute before React mounts.
  - Move palette definitions and DOM-application helpers out of `ThemeShowcase` into a shared module.
  - Define light and dark palette token sets in CSS using a real palette attribute or equivalent shared contract.
- Impact / risk:
  - Global theme ownership changes affect every page, so this is the highest blast-radius step.
  - The FOUC path must be handled at bootstrap time, not after React hydration.
- Done:
  - The app root no longer hardcodes dark mode.
  - Shared palette definitions exist outside the showcase page.
  - Light/dark/auto mode can be resolved globally with a cached pre-hydration restore.

### Task 2 — Persist Project-Backed Appearance Preferences

- Files:
  - new focused appearance settings section/component
  - `ui/src/components/ProjectSettings.tsx`
  - shared theme module/provider from Task 1
- Change:
  - Reuse the existing `ui_preferences` persistence seam for `theme_mode` and `theme_palette`.
  - Expose mode controls and palette swatches through Project Settings, reachable from the shell's existing settings entry point.
  - Keep local storage as a mirror/cache only for bootstrap restore, not the source of truth.
  - Fall back cleanly to system mode + Slate when no project-backed preference exists yet or when project settings are unavailable.
- Impact / risk:
  - The settings dialog already owns multiple save flows; adding more inline save code would worsen an already-large file.
  - The theme provider must stay in sync with project changes as the active project loads or changes.
- Done:
  - A user can choose Light, Dark, or Auto and select one of the four palettes from Project Settings.
  - The choice survives reload through project-backed settings.
  - The app still has a sensible fallback outside project-scoped routes.

### Task 3 — Align Showcase, Toasts, and Real UI Surfaces

- Files:
  - `ui/src/pages/ThemeShowcase.tsx`
  - `ui/src/components/ui/sonner.tsx`
  - any small theme-view helper files created in earlier tasks
- Change:
  - Update `/theme` to preview both modes from the shared palette source rather than its own local constants and direct DOM mutation.
  - Ensure Sonner toasts use the resolved theme and current CSS variables cleanly once the provider is mounted.
  - Do a targeted light-mode audit of the main shell/settings/showcase surfaces and fix obvious contrast, border, and shadow regressions.
- Impact / risk:
  - This is where hidden assumptions about dark-only styling will surface.
  - The showcase must stop being special-case infrastructure and become a consumer of the same shared theme source as the app.
- Done:
  - `/theme` is a real preview surface for the shared theme system.
  - Toasts follow the resolved theme.
  - Core shell/settings surfaces render cleanly in both modes.

### Verification Plan

- Static checks:
  - `make test-unit PYTHON=.venv/bin/python`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
- Runtime/browser checks:
  - Desktop:
    - open `/theme`, switch through all palettes and both light/dark previews
    - open a real project route, open Project Settings, change mode/palette, confirm shell + toast styling updates
  - Mobile:
    - repeat the settings flow in a narrow viewport and verify the settings dialog/tab layout stays usable
  - Inspect browser console in both views and confirm no theme-related errors
  - Verify reload behavior to confirm cached pre-hydration restore prevents visible theme flash
- Fallback if browser tooling is blocked:
  - use `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log instead of claiming completion without evidence

### Redundancy / Cleanup Plan

- Remove the hardcoded app-level `.dark` class in `ui/src/App.tsx`
- Remove the hardcoded `<html class="dark">` bootstrap from `ui/index.html`
- Remove `ThemeShowcase`'s page-local palette source of truth and direct `.dark` mutation helper
- Avoid adding new backend theme fields if `ui_preferences` remains sufficient

### Human-Approval Blockers

- None expected:
  - no new dependency
  - no public API change
  - no schema-first boundary change if `ui_preferences` remains the persistence path
- If implementation proves that project-level theme state cannot be kept coherent through `ui_preferences`, stop and re-evaluate before adding dedicated API fields.

### Done Looks Like

- Shared theme ownership exists and the app no longer hardcodes dark mode.
- Mode + palette are configurable from Project Settings and persist through project-backed settings.
- `/theme` and Sonner both consume the same shared theme state.
- Static checks pass, browser verification is captured for desktop and mobile, and the work log records evidence plus any residual issues.

## Work Log

*(Entries added during implementation)*

20260314 — Backlog cleanup: refreshed the story against the current `ui/` tree (`App.tsx`, `ThemeShowcase.tsx`, `ProjectSettings.tsx`, `index.css`, existing `ui_preferences` settings path) and promoted it to `Pending`.
20260407-2139 — exploration + planning: re-read `docs/ideal.md`, `docs/spec.md` (`spec:5`, especially `spec:5.3` and `spec:5.5`), `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/design/decisions.md`, Story 044, and the current Story 046 scaffold. Traced the live implementation through `ui/src/App.tsx`, `ui/index.html`, `ui/src/pages/ThemeShowcase.tsx`, `ui/src/components/ProjectSettings.tsx`, `ui/src/components/AppShell.tsx`, `ui/src/components/ui/sonner.tsx`, `ui/src/lib/hooks/projects.ts`, `ui/src/lib/types.ts`, `ui/src/lib/api/projects.ts`, and backend project-settings merge support in `src/cine_forge/api/models.py` and `src/cine_forge/api/service.py`. Key findings: the app still hardcodes dark mode in both `App.tsx` and `index.html`; the only palette source lives inside `ThemeShowcase`; `next-themes` is installed and Sonner already reads it but no provider is mounted; project-backed `ui_preferences` already provide the correct persistence seam; backend merge behavior already supports theme keys without schema expansion. Ran `make check-size` plus `wc -l` on likely touch points and recorded large-file risks (`AppShell.tsx` 836, `ProjectSettings.tsx` 458, `ui/src/lib/types.ts` 671). Small repo-fit scope expansion folded into the plan: extract a focused appearance section/provider instead of bloating existing large shell/settings files. Next step: human approval on the plan before implementation.
20260407-2208 — implementation: mounted a real app-level theme system and removed the dark-only bootstrap. Added shared theme ownership in `ui/src/lib/theme.ts`, `ui/src/lib/app-theme-context.ts`, and `ui/src/components/AppThemeProvider.tsx`; wrapped the router in `AppThemeProvider` from `ui/src/App.tsx`; replaced the hardcoded `<html class="dark">` with a pre-hydration mode/palette restore in `ui/index.html`; expanded `ui/src/index.css` to ship light + dark token sets for Slate, Obsidian, Ember, and Noir; rewrote `ui/src/pages/ThemeShowcase.tsx` to consume the shared theme source; added `ui/src/components/ProjectAppearanceSection.tsx` and an `Appearance` tab in `ui/src/components/ProjectSettings.tsx`; updated `ui/src/components/ui/sonner.tsx` to use the resolved theme. Kept backend/API schema untouched because existing `ui_preferences` merge behavior already handled `theme_mode` and `theme_palette`. Next step: run browser verification on `/theme` and a real project route, then finish required checks.
20260407-2219 — runtime/browser verification: created disposable project `theme-smoke` through `POST /api/projects/new`, started backend (`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m uvicorn cine_forge.api.app:app --host 127.0.0.1 --port 8000`) and frontend (`pnpm --dir ui dev --host 127.0.0.1 --port 5174`), and verified `GET /api/health` returned `{\"status\":\"ok\",\"version\":\"2026.04.04-06\"}`. Desktop: `/theme` rendered the shared palette matrix cleanly, switching Light/Dark/Auto and palette selection updated `document.documentElement` + local cache correctly, and console output stayed clean. Initial pass on project settings exposed a real bug: palette preview cards nested shadcn `Button` elements inside an outer `<button>`, which caused React nested-button console errors; fixed by converting the preview chips to non-interactive spans in `ui/src/components/ProjectAppearanceSection.tsx`, then restarted the dev server to clear stale HMR state. Re-test after the fix: project settings `Appearance` tab opened without errors, fallback for a project with no saved preference resolved to Auto + Slate, changing desktop settings to Dark + Ember updated the live shell and persisted through `GET /api/projects/theme-smoke` (`ui_preferences.theme_mode=\"dark\"`, `theme_palette=\"ember\"`), and a reload restored the same mode/palette immediately from the bootstrap cache. Mobile: at `390x844`, the `Appearance` tab remained usable, switching to Light + Slate updated the live shell and persisted through the same API endpoint (`ui_preferences.theme_mode=\"light\"`, `theme_palette=\"slate\"`), and console output stayed clean. Evidence captured with Playwright screenshots for desktop showcase, desktop project settings, desktop reload state, mobile settings, and mobile shell.
20260407-2232 — static verification: `pnpm --dir ui run lint` passed with only pre-existing warnings in `AppShell.tsx`, `StatusBadge.tsx`, `ui/badge.tsx`, `ui/button.tsx`, `ui/tabs.tsx`, and `ui/src/lib/right-panel.tsx`; `cd ui && npx tsc -b` passed; `pnpm --dir ui run build` passed with the existing large-chunk Vite warning; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`665 passed, 151 deselected, 1 pre-existing pytest mark warning`). Residual validation gaps kept explicit for `/validate`: WCAG contrast is not yet measured palette-by-palette, and the broad “all existing UI components in both modes” sweep still needs a wider route audit beyond shell/settings/showcase.
20260407-2257 — close-out verification + completion: reran the full required checks on the final diff: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`665 passed, 151 deselected, 1 pre-existing pytest mark warning`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (same pre-existing warnings only), `cd ui && npx tsc -b`, and `pnpm --dir ui run build` (same pre-existing large-chunk warning only). Completed the missing theme-specific validation in browser: an OKLCH token audit across Slate, Obsidian, Ember, and Noir in both light and dark confirmed AA contrast for the primary, secondary, accent, and muted foreground pairs; the `/theme` preview surface was used to exercise hover, focus, and disabled component treatments across all four light palettes; and a wider desktop/mobile route sweep stayed clean with HTTP 200 responses and clean console output for `/`, `/new`, `/theme`, and project routes under `theme-closeout-light` and `theme-closeout-dark` including `intent`, `scenes`, `characters`, `locations`, `props`, `inbox`, `runs`, and `artifacts`. With those gaps closed, all acceptance criteria and story tasks are satisfied, validation is complete, and the story is ready to land. Next step: `/check-in-diff`.
