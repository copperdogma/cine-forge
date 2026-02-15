# Story 011b: Operator Console — Research & Design Decisions

**Status**: Done
**Created**: 2026-02-13
**Completed**: 2026-02-15
**Spec Refs**: 2.5 (Human Control), 3.1 (Stage Progression), 4–6 (Ingestion/Normalization/Config), 6–7 (Bibles/Entity Graph/Continuity), 8.7 (Human Interaction Model), 20 (Metadata & Auditing), 21 (Operating Modes)
**Depends On**: Story 011 (Continuity Tracking — completes Phase 2 artifact model)
**Continued By**: Story 011c (Operator Console — Design & Build)
**Design Docs**: `docs/design/principles.md`, `docs/design/personas.md`, `docs/design/landscape.md`, `docs/design/ui-stack.md`, `docs/design/decisions.md`

---

## Goal

Research and establish the design direction, technology stack, and interaction patterns for the production CineForge Operator Console. This story produces the research artifacts and reviewed decisions that Story 011c will implement.

---

## Deliverables

All complete:

- [x] Run deep research: app landscape and design inspiration → `docs/design/landscape.md`
  - 3 providers (GPT-5.2, Claude Opus 4.6, Gemini 3), synthesized into final report
  - Research: `docs/research/011b-landscape-inspiration/final-synthesis.md`
- [x] **Discuss with Cam**: Review landscape findings — visual personality direction, artifact browser mental model, which patterns to steal vs. skip
- [x] Run deep research: UI stack evaluation → `docs/design/ui-stack.md`
  - 3 providers (GPT-5.2, Claude Opus 4.6, Gemini 3), synthesized into final report
  - Research: `docs/research/011b-ui-stack-evaluation/final-synthesis.md`
- [x] **Discuss with Cam**: Review UI stack findings — component library choice, framework decision, viewer library picks
- [x] Synthesize final reports and update `docs/design/landscape.md` and `docs/design/ui-stack.md` with decisions
- [x] **Discuss with Cam**: Final sign-off on research conclusions
- [x] Capture all reviewed decisions in `docs/design/decisions.md`
- [x] Create `docs/ideas.md` for deferred features and future concepts

---

## Key Decisions Made

See `docs/design/decisions.md` for the full set. Highlights:

- **Story-centric UI**, not pipeline-centric — scenes, characters, locations as primary objects
- **shadcn/ui + React 19 + Vite + Tailwind + Zustand + TanStack Query**
- **Dark, warm, cinematic theme** (Arc Studio Pro, Frame.io, Linear references)
- **Inbox/review queue** as the "what do I do next?" surface
- **Variational presentation** for subjective AI decisions (unlimited rounds with feedback)
- **Implicit acceptance** for objective extractions (edit-in-place)
- **Script is source of truth** — derived artifacts enrich but don't rename upstream
- **Fresh build** from scratch (not migration of Operator Console Lite)
- **AI-driven visual identity** — AI generates theme variations, Cam steers with taste feedback
- **v0.dev for component prototyping** — generated code transfers directly into codebase

---

## Work Log

*(append-only)*

### 20260213 — Restructured story from first principles
- **Result:** Success.
- **Notes:** Original 011b mixed product-level design foundations with build work. Extracted design principles, personas, and research scope into project-level docs under `docs/design/`. Research stubs created for deep-research execution. Story now focuses on research → design → build → polish with clear phase gates.
- **Evidence:** `docs/design/principles.md`, `docs/design/personas.md`, `docs/design/landscape.md`, `docs/design/ui-stack.md`.
- **Next:** Run deep research for landscape and UI stack before design phase.

### 20260214 — Deep research completed (landscape + UI stack)
- **Result:** Success.
- **Notes:** Ran both research topics through 3 AI providers (GPT-5.2, Claude Opus 4.6, Gemini 3). Patched deep-research Anthropic provider to use streaming API for long-running calls. All 6 reports formatted and synthesized into final reports.
- **Evidence:** `docs/research/011b-landscape-inspiration/final-synthesis.md`, `docs/research/011b-ui-stack-evaluation/final-synthesis.md`.
- **Next:** Review findings with Cam at discussion checkpoints.

### 20260215 — Research review and design decisions finalized
- **Result:** Success.
- **Notes:** Reviewed both research syntheses with Cam. Captured all decisions in `docs/design/decisions.md`. Created `docs/ideas.md` for deferred features (ghost-text suggestions, AI preference learning, entity graph viz, story-to-screenplay conversion). Updated `docs/design/landscape.md` and `docs/design/ui-stack.md` to reference decisions. Added Ideas Backlog section to `AGENTS.md`. Split remaining work (design, build, polish) into Story 011c.
- **Evidence:** `docs/design/decisions.md`, `docs/ideas.md`, updated `AGENTS.md`.
- **Next:** Story 011c — design and build the production UI.
