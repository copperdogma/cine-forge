# Story 011b: Operator Console — Production UI

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 2.5 (Human Control), 3.1 (Stage Progression), 4–6 (Ingestion/Normalization/Config), 6–7 (Bibles/Entity Graph/Continuity), 8.7 (Human Interaction Model), 20 (Metadata & Auditing), 21 (Operating Modes)
**Depends On**: Story 011 (Continuity Tracking — completes Phase 2 artifact model)
**Replaces / Evolves**: Story 007b (Operator Console Lite — stopgap GUI)
**Design Docs**: `docs/design/principles.md`, `docs/design/personas.md`, `docs/design/landscape.md`, `docs/design/ui-stack.md`

---

## Goal

Replace the stopgap Operator Console Lite with a production-quality UI for CineForge. The console must feel like a creative tool, not an admin panel. The primary user is a storyteller with scripts who knows nothing about film production — the UI should make their default path effortless.

See `docs/design/principles.md` for the interaction philosophy and `docs/design/personas.md` for user modes.

---

## Phases

### Phase 1: Research (Deep Research)

Produce the two research artifacts that inform design and build decisions. These are project-level docs, not story-scoped deliverables.

- [ ] Run deep research: app landscape and design inspiration → `docs/design/landscape.md`
  - Creative tool UX patterns, pipeline visualization, artifact browsing, film tool patterns
  - Focus on interaction paradigms worth stealing, not competitive positioning
- [ ] Run deep research: UI stack evaluation → `docs/design/ui-stack.md`
  - Component library selection optimized for AI-assisted development quality
  - Viewer library recommendations for screenplay, structured data, graphs, timelines
- [ ] Review and finalize both docs before proceeding to design

### Phase 2: Design

Synthesize research into a concrete UI plan. Design artifacts live in `docs/design/`.

- [ ] Define information architecture and navigation model
  - How does the user move between project overview, pipeline stages, artifact inspection?
  - How does progressive disclosure work in practice (summary → detail → raw)?
- [ ] Define the golden path: drag-and-drop script → AI fills everything → user approves → artifacts appear
- [ ] Define artifact viewer patterns by type:
  - Text artifacts (scripts, canonical text) — script-formatted viewer
  - Structured data (scenes, project config, bibles) — collapsible structured viewer
  - Graph data (entity relationships, dependency graphs) — graph visualization
  - Timeline / temporal data — track-based visualization (future-proof for Phase 3)
  - Health/status indicators — inline with clear visual language
- [ ] Define the override/drill-in interaction model
  - How does the user go from "OK" mode to "I want to change this"?
  - How do they return to autopilot?
- [ ] Low-fidelity wireframes or screen sketches for key flows
- [ ] Document design plan in `docs/design/ui-plan.md`

### Phase 3: Build

Iterative implementation. Each flow is built, browser-verified (per AGENTS.md), and validated before moving to the next.

- [ ] Set up new UI project (or migrate 007b) with chosen stack from `docs/design/ui-stack.md`
- [ ] Implement app shell: navigation, project switching, responsive layout
- [ ] Implement new-project flow: drag-and-drop → AI parse → review draft config → confirm
- [ ] Implement pipeline run view: start run, stage progress, success/failure summary
- [ ] Implement artifact browser: type-aware viewers, version history, metadata, lineage
- [ ] Implement artifact override/edit flows: inline editing → new version → stale propagation feedback
- [ ] Implement pipeline events and run history views
- [ ] Backend API adjustments as needed to support new UI patterns
- [ ] Cross-browser and responsive testing (desktop primary, tablet secondary)

### Phase 4: Polish

- [ ] Visual polish: animations, transitions, loading states, empty states, error states
- [ ] Error handling: network failures, malformed artifacts, long-running pipelines
- [ ] Accessibility check (WCAG 2.1 AA minimum)
- [ ] Performance check with realistic artifact volumes
- [ ] End-to-end walkthrough of the golden path with a real screenplay

---

## Acceptance Criteria

### Design Quality
- [ ] A new user can go from "I have a script" to "pipeline running" in under 60 seconds.
- [ ] Progressive disclosure works: the autopilot user and the learning user both succeed without mode-switching.
- [ ] The UI looks like a creative tool, not a developer dashboard.

### Functional Completeness
- [ ] All Phase 1–2 artifact types have dedicated, type-appropriate viewers.
- [ ] Artifact version history is browsable with visual diffs.
- [ ] Pipeline runs can be started, monitored, and inspected entirely from UI.
- [ ] Project creation works via drag-and-drop with AI auto-fill.
- [ ] AI suggestions are presented with one-click approval.
- [ ] User can override any AI decision and return to autopilot.

### Technical Quality
- [ ] Responsive layout (desktop-first, tablet-usable).
- [ ] Accessibility: WCAG 2.1 AA minimum.
- [ ] Performance: artifact browser loads within 1s for typical project sizes.
- [ ] Existing backend API contracts preserved or cleanly migrated.

### Research Deliverables (preconditions for build)
- [ ] `docs/design/landscape.md` completed via deep research.
- [ ] `docs/design/ui-stack.md` completed via deep research with recommended stack.

---

## Constraints

- The current Operator Console Lite (React 18 + Vite + TypeScript, no component library) may be migrated or replaced depending on `docs/design/ui-stack.md` findings.
- The backend API (`src/cine_forge/operator_console/app.py`) should be evolved, not rewritten — the data model is sound.
- This story does NOT implement Phase 4+ features (role chat, creative sessions, collaborative review). It builds the foundation those features will plug into.
- Phase 3 stories (012 Timeline, 013 Tracks) will build their UI surfaces on top of whatever this story establishes — the UI architecture must accommodate timeline/track visualization even if it doesn't implement it.

---

## Out of Scope

- Multi-user collaboration and auth.
- Rich role-chat experiences (@agent creative sessions — Story 019).
- Full timeline editing UI (Stories 012–013 build on this foundation).
- Shot planning, storyboard, and render controls.

---

## Tasks

Summary of all phases:

- [ ] **Phase 1**: Deep research — landscape inspiration and UI stack evaluation
- [ ] **Phase 2**: Design — IA, golden path, artifact viewers, wireframes
- [ ] **Phase 3**: Build — shell, project flow, pipeline view, artifact browser, overrides
- [ ] **Phase 4**: Polish — visual, accessibility, performance, end-to-end validation
- [ ] Update `README.md` with new UI launch instructions
- [ ] Run `make test-unit` and `make lint` with any backend changes
- [ ] Manual browser verification per AGENTS.md development workflow

---

## Work Log

*(append-only)*

### 20260213 — Restructured story from first principles
- **Result:** Success.
- **Notes:** Original 011b mixed product-level design foundations with build work. Extracted design principles, personas, and research scope into project-level docs under `docs/design/`. Research stubs created for deep-research execution. Story now focuses on research → design → build → polish with clear phase gates.
- **Evidence:** `docs/design/principles.md`, `docs/design/personas.md`, `docs/design/landscape.md`, `docs/design/ui-stack.md`.
- **Next:** Run deep research for landscape and UI stack before design phase.
