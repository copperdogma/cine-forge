# Story 044 — Mobile-Friendly UI

**Phase**: 2.5 — UI
**Priority**: Medium
**Status**: To Do
**Created**: 2026-02-16
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

## Acceptance Criteria

- [ ] App renders correctly at 375px width (iPhone SE) through 1440px+ (desktop)
- [ ] Sidebar collapses to a hamburger menu on screens < 768px
- [ ] Chat panel is accessible as a full-screen overlay on mobile
- [ ] All list pages (scenes, characters, locations, props) are single-column and scrollable on mobile
- [ ] All detail pages are readable without horizontal scrolling
- [ ] Tap targets are minimum 44×44px per Apple HIG
- [ ] No hover-only interactions — everything is tap-accessible
- [ ] Script view is readable and scrollable on mobile
- [ ] Breadcrumbs truncate gracefully on small screens
- [ ] Inspector panel either hides or becomes a separate view on mobile
- [ ] Tested via Chrome DevTools device emulation at iPhone SE, iPhone 14, iPad, and desktop breakpoints

## Tasks

- [ ] Audit current layout for mobile breakage points
- [ ] Define breakpoint system (sm/md/lg) and add to Tailwind config if needed
- [ ] Refactor AppShell: sidebar → off-canvas drawer on mobile, hamburger toggle
- [ ] Refactor right panel: chat as full-screen overlay / bottom sheet on mobile
- [ ] Make all list pages responsive (single-column card layout on mobile)
- [ ] Make all detail pages responsive (stacked sections, no side-by-side on mobile)
- [ ] Make script view mobile-readable (font size, margins, scroll behavior)
- [ ] Fix breadcrumbs for small screens (truncation / back-arrow pattern)
- [ ] Touch-friendly: increase tap targets, remove hover-only states
- [ ] Screenshot-verify at each breakpoint with Chrome DevTools

## Notes

- Tailwind's responsive utilities (`sm:`, `md:`, `lg:`) should handle most of this without custom CSS.
- The resizable right panel drag handle is a desktop interaction — on mobile, chat should be a modal/overlay triggered by a floating button or nav item.
- Story 043 may add new pages; this story should be done after 043 so we're styling the final set of pages.

## Work Log

*(Updated during implementation)*
