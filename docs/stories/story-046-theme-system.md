# Story 046 — Theme System (Light/Dark/Auto + Palettes)

**Architecture Note (2026-02-19)**
- Needs update due to architectural changes since story was written: UI was flattened from ui/operator-console to ui/, so referenced paths and implementation touchpoints should be updated to current structure.

**Phase**: 2.5 — UI
**Priority**: Medium
**Status**: Draft

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

- [ ] Wire up `next-themes` `<ThemeProvider>` in App.tsx with `attribute="class"` strategy
- [ ] Remove hardcoded `.dark` class from root div
- [ ] Define light mode CSS variables in `:root` block of `index.css` (matching Slate palette as default)
- [ ] Create a `ThemeContext` or Zustand slice to manage palette selection alongside mode
- [ ] Create palette definitions file (`src/lib/themes.ts`) with all light + dark palettes as structured objects
- [ ] Implement palette application logic (apply CSS variable overrides when palette changes)

### Phase 2 — Light Palettes

- [ ] Design 4 light palettes corresponding to the dark ones:
  - **Obsidian Light** — Cool whites with blue-steel accents
  - **Ember Light** — Warm whites with amber/copper accents
  - **Slate Light** — Neutral whites with sage/teal accents (default)
  - **Noir Light** — Crisp whites with gold accents
- [ ] Verify contrast ratios meet WCAG AA for all palette × mode combinations
- [ ] Test all shadcn/ui component states (hover, focus, disabled) in each light palette

### Phase 3 — Theme Switcher UI

- [ ] Add theme switcher component to AppShell (header area or settings dropdown)
- [ ] Mode selector: Light / Dark / Auto toggle (sun/moon/auto icons)
- [ ] Palette selector: visual swatches showing each palette's primary + accent colors
- [ ] Preview palette on hover before committing
- [ ] Persist selection to project settings via API (not localStorage)

### Phase 4 — Polish & Verification

- [ ] Update ThemeShowcase to display all palettes in both modes side by side
- [ ] Fix Sonner toast integration (pass resolved theme from `next-themes`)
- [ ] Audit all pages for light mode rendering issues (contrast, borders, shadows)
- [ ] Handle edge case: project settings unavailable → fall back to system dark + Slate
- [ ] Prevent FOUC: inject theme class before React hydration via `<script>` in index.html

## Technical Notes

- **Color format**: OKLCH (perceptually uniform). All palettes use `oklch()` values for CSS variables.
- **Persistence**: Per AGENTS.md, user preferences go in `project.json`, not `localStorage`. Use `localStorage` only as a fast cache to prevent FOUC, synced from project settings.
- **`next-themes` config**: Use `attribute="class"`, `defaultTheme="system"`, `storageKey="cineforge-mode"`.
- **Palette application**: CSS variable overrides via `document.documentElement.style.setProperty()` on the resolved theme element.
- **Existing code**: ThemeShowcase at `ui/operator-console/src/pages/ThemeShowcase.tsx` has the 4 dark palette definitions — extract and normalize into `src/lib/themes.ts`.

## Dependencies

- `next-themes` (already installed, ^0.4.6)
- shadcn/ui CSS variable system (already in place)

## Work Log

*(Entries added during implementation)*
