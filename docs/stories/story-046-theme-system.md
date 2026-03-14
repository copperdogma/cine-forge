# Story 046 — Theme System (Light/Dark/Auto + Palettes)

**Phase**: 2.5 — UI
**Priority**: Medium
**Status**: Pending
**Updated**: 2026-03-14 — backlog cleanup refreshed the implementation notes against the current `ui/` architecture and promoted the story to `Pending`.

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

- [ ] User can switch between Light, Dark, and Auto (system preference) modes
- [ ] At least 4 dark palettes available: Obsidian, Ember, Slate, Noir (existing)
- [ ] At least 4 corresponding light palettes available
- [ ] Theme preference (mode + palette) persists across sessions via project settings
- [ ] Theme switcher is accessible from the app shell (e.g., settings menu or header)
- [ ] Auto mode respects `prefers-color-scheme` and applies the user's chosen palette
- [ ] Sonner toast component correctly inherits the active theme
- [ ] ThemeShowcase page updated to preview both light and dark palettes
- [ ] No flash of wrong theme on page load (SSR-safe or pre-render class injection)
- [ ] All existing UI components render correctly in both light and dark modes

## Tasks

### Phase 1 — Theme Infrastructure

- [ ] Wire up `next-themes` `<ThemeProvider>` in `ui/src/App.tsx` (or a focused theme wrapper imported there) with `attribute="class"` strategy
- [ ] Remove the hardcoded `.dark` class from the app root in `ui/src/App.tsx`
- [ ] Extract the existing ThemeShowcase palette definitions from `ui/src/pages/ThemeShowcase.tsx` into a shared theme module under `ui/src/lib/` or `ui/src/components/`
- [ ] Define light mode CSS variables in `ui/src/index.css` (matching Slate as the default baseline palette)
- [ ] Manage palette selection alongside mode using the current frontend architecture, not a stale `ui/operator-console` context path
- [ ] Persist `theme_mode` + `theme_palette` through the existing project settings `ui_preferences` path instead of page-local state

### Phase 2 — Light Palettes

- [ ] Design 4 light palettes corresponding to the dark ones:
  - **Obsidian Light** — Cool whites with blue-steel accents
  - **Ember Light** — Warm whites with amber/copper accents
  - **Slate Light** — Neutral whites with sage/teal accents (default)
  - **Noir Light** — Crisp whites with gold accents
- [ ] Verify contrast ratios meet WCAG AA for all palette × mode combinations
- [ ] Test all shadcn/ui component states (hover, focus, disabled) in each light palette

### Phase 3 — Theme Switcher UI

- [ ] Add a theme switcher to the current shell/settings flow (`ui/src/components/AppShell.tsx` and/or `ui/src/components/ProjectSettings.tsx`)
- [ ] Mode selector: Light / Dark / Auto toggle (sun/moon/auto icons)
- [ ] Palette selector: visual swatches showing each palette's primary + accent colors
- [ ] Preview palette on hover before committing
- [ ] Persist selection through the existing `updateProjectSettings()` API path using `ui_preferences`

### Phase 4 — Polish & Verification

- [ ] Update `ui/src/pages/ThemeShowcase.tsx` to display all palettes in both modes using the shared palette source
- [ ] Fix Sonner toast integration in `ui/src/components/ui/sonner.tsx` so it follows the resolved theme
- [ ] Audit all pages for light mode rendering issues (contrast, borders, shadows)
- [ ] Handle edge case: project settings unavailable → fall back to system mode + Slate palette
- [ ] Prevent FOUC by restoring the saved theme class/palette before React hydration (likely via `ui/index.html` or the earliest bootstrap point)

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

## Work Log

*(Entries added during implementation)*

20260314 — Backlog cleanup: refreshed the story against the current `ui/` tree (`App.tsx`, `ThemeShowcase.tsx`, `ProjectSettings.tsx`, `index.css`, existing `ui_preferences` settings path) and promoted it to `Pending`.
