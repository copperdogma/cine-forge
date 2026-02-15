# Story 011d: Operator Console — Design & Build

**Status**: To Do
**Created**: 2026-02-15
**Spec Refs**: 2.5 (Human Control), 3.1 (Stage Progression), 4–6 (Ingestion/Normalization/Config), 6–7 (Bibles/Entity Graph/Continuity), 8.7 (Human Interaction Model), 20 (Metadata & Auditing), 21 (Operating Modes)
**Depends On**: Story 011b (Research & Design Decisions — complete), Story 011 (Continuity Tracking)
**Replaces / Evolves**: Story 007b (Operator Console Lite — stopgap GUI)
**Design Docs**: `docs/design/decisions.md`, `docs/design/principles.md`, `docs/design/personas.md`, `docs/design/landscape.md`, `docs/design/ui-stack.md`

---

## Goal

Design and build the production CineForge Operator Console based on the research and decisions from Story 011b. The console must feel like a creative tool, not an admin panel. Fresh build from scratch using the chosen stack (shadcn/ui + React 19 + Vite + Tailwind + Zustand).

See `docs/design/decisions.md` for the full set of design decisions driving this work.

---

## Phases

### Phase 1: Design

Synthesize research decisions into a concrete UI plan. Design artifacts live in `docs/design/`.

- [ ] Bootstrap visual identity: AI generates 3–4 dark cinematic theme variations, Cam picks direction
- [ ] Create `DESIGN_SYSTEM.md` with design tokens (colors, spacing, typography, artifact type colors/icons)
- [ ] Define information architecture and navigation model
  - How does the user move between project overview, scenes, artifacts?
  - How does progressive disclosure work in practice (summary → detail → raw)?
- [ ] Define the golden path: drag-and-drop script → AI fills everything → user approves → artifacts appear
- [ ] Define artifact viewer patterns by type:
  - Text artifacts (scripts, canonical text) — screenplay-formatted viewer (CodeMirror)
  - Structured data (scenes, project config, bibles) — collapsible structured viewer
  - Health/status indicators — inline with clear visual language
- [ ] Define the inbox/review queue interaction model
- [ ] Define the override/drill-in interaction model
  - How does the user go from "OK" mode to "I want to change this"?
  - How do they return to autopilot?
- [ ] **Discuss with Cam**: Review design plan — IA, golden path, viewer patterns, wireframes
- [ ] Low-fidelity wireframes or v0 prototypes for key flows
- [ ] Document design plan in `docs/design/ui-plan.md`

### Phase 2: Build — Foundation

- [ ] Set up new UI project with chosen stack (React 19 + Vite + shadcn/ui + Tailwind + Zustand + TanStack Query)
- [ ] Move existing Operator Console Lite to `ui/operator-console-lite-archive/` for reference
- [ ] Implement design token system from `DESIGN_SYSTEM.md`
- [ ] Implement app shell: three-panel layout, navigation, project switching, responsive layout
- [ ] **Discuss with Cam**: Review app shell in browser — does it feel right?

### Phase 3: Build — Core Flows

- [ ] Implement new-project flow: drag-and-drop → AI parse → review draft config → confirm
- [ ] Implement inbox/review queue
- [ ] Implement pipeline run view: start run, vertical phase progress, progressive materialization
- [ ] Implement artifact browser: type-aware viewers, version history, metadata, provenance
- [ ] Implement artifact override/edit flows: inline editing → new version → stale propagation → inbox notification
- [ ] Implement stale artifact indicators (icon + hover + click-to-resolve)
- [ ] **Discuss with Cam**: Review core flows in browser — walkthrough the golden path

### Phase 4: Build — Specialized Viewers

- [ ] Screenplay format viewer (CodeMirror with screenplay mode)
- [ ] Structured data viewer (collapsible sections for bibles, configs)
- [ ] Scene strip / index card view
- [ ] StudioBinder-style color-coded element tagging in script view
- [ ] Backend API adjustments as needed to support new UI patterns

### Phase 5: Polish

- [ ] Visual polish: animations, transitions, loading states, empty states, error states
- [ ] Keyboard navigation for common actions
- [ ] Error handling: network failures, malformed artifacts, long-running pipelines
- [ ] Accessibility check (WCAG 2.1 AA minimum)
- [ ] Performance check with realistic artifact volumes
- [ ] End-to-end walkthrough of the golden path with a real screenplay
- [ ] Cross-browser testing (desktop primary, tablet secondary)

---

## Acceptance Criteria

### Design Quality
- [ ] A new user can go from "I have a script" to "pipeline running" in under 60 seconds.
- [ ] Progressive disclosure works: the autopilot user and the learning user both succeed without mode-switching.
- [ ] The UI looks like a creative tool, not a developer dashboard.

### Functional Completeness
- [ ] All Phase 1–2 artifact types have dedicated, type-appropriate viewers.
- [ ] Artifact version history is browsable.
- [ ] Pipeline runs can be started, monitored, and inspected entirely from UI.
- [ ] Project creation works via drag-and-drop with AI auto-fill.
- [ ] AI suggestions are presented with variational options for subjective decisions.
- [ ] User can override any AI decision and return to autopilot.
- [ ] Inbox/review queue surfaces stale artifacts, AI requests, and errors.
- [ ] Stale artifacts show inline indicators with hover explanation and click-to-resolve.

### Technical Quality
- [ ] Responsive layout (desktop-first, tablet-usable).
- [ ] Accessibility: WCAG 2.1 AA minimum.
- [ ] Performance: artifact browser loads within 1s for typical project sizes.
- [ ] Existing backend API contracts preserved or cleanly migrated.

---

## Constraints

- Fresh build. Do NOT migrate the existing Operator Console Lite. Reference it for URL layout and API client patterns only.
- The backend API (`src/cine_forge/operator_console/app.py`) should be evolved, not rewritten — the data model is sound.
- This story does NOT implement Phase 4+ features (role chat, creative sessions, collaborative review). It builds the foundation those features will plug into.
- Phase 3 stories (012 Timeline, 013 Tracks) will build their UI surfaces on top of whatever this story establishes — the UI architecture must accommodate timeline/track visualization even if it doesn't implement it.

---

## Out of Scope

- Multi-user collaboration and auth.
- Rich role-chat experiences (@agent creative sessions — Story 019).
- Full timeline editing UI (Stories 012–013 build on this foundation).
- Shot planning, storyboard, and render controls.
- Entity graph visualization (deferred, see `docs/ideas.md`).
- Story-to-screenplay conversion (deferred, see `docs/ideas.md`).
- Ghost-text inline suggestions (deferred, see `docs/ideas.md`).

---

## Tasks

Summary of all phases:

- [ ] **Phase 1**: Design — visual identity, design tokens, IA, golden path, wireframes
- [ ] **Phase 2**: Build foundation — project setup, app shell, design system
- [ ] **Phase 3**: Build core flows — intake, inbox, pipeline, artifacts, overrides
- [ ] **Phase 4**: Build viewers — screenplay, structured data, scene strips, tagging
- [ ] **Phase 5**: Polish — animations, keyboard nav, a11y, performance, e2e validation
- [ ] Update `README.md` with new UI launch instructions
- [ ] Run `make test-unit` and `make lint` with any backend changes
- [ ] Manual browser verification per AGENTS.md development workflow

---

## Work Log

*(append-only)*

### 20260215 — Story created
- **Result:** Story split from 011b.
- **Notes:** Story 011b completed Phase 1 (research). This story picks up from the reviewed design decisions in `docs/design/decisions.md` and carries through design, build, and polish.
- **Next:** Phase 1 — bootstrap visual identity and design tokens.
