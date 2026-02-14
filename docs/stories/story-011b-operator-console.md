# Story 011b: Operator Console — Production UI

**Status**: To Do
**Created**: 2026-02-13
**Spec Refs**: 2.5 (Human Control), 3.1 (Stage Progression), 4–6 (Ingestion/Normalization/Config), 6–7 (Bibles/Entity Graph/Continuity), 8.7 (Human Interaction Model), 20 (Metadata & Auditing), 21 (Operating Modes)
**Depends On**: Story 011 (Continuity Tracking — completes Phase 2 artifact model)
**Replaces / Evolves**: Story 007b (Operator Console Lite — stopgap GUI)

---

## Goal

Replace the stopgap Operator Console Lite with a **production-quality, public-releasable UI** for CineForge. The console must be beautiful, intuitive, and designed around the principle that **AI does everything by default — the user only says OK until they want to dig in.**

This is the UI that ships. It must feel like a world-class creative tool, not an admin panel.

### Design Philosophy

- **AI-first, human-guided**: Every step defaults to AI filling in and suggesting. The user's primary action is approval, not configuration.
- **Progressive disclosure**: Simple by default, infinitely deep on demand. A "vibe film" user sees a drag-and-drop experience. A cinematographer sees the controls they care about.
- **Artifact-centric**: Every pipeline artifact is inspectable and editable at any point, with elegant inline viewers tailored to artifact type (text, structured data, graphs, timelines, media).
- **Override anywhere**: At any step, the user can jump in, override AI decisions and defaults, and dig as deep as they want — then step back and let AI continue.

---

## Phased Approach

This story is structured as a research → design → build pipeline. Each phase produces artifacts that feed the next.

### Phase R1: Research — AI-Driven UI Tooling

**Goal**: Find the best tools, frameworks, and approaches for getting AI to produce beautiful, functional UIs.

- [ ] Deep research: current state of AI-assisted UI generation (2026 landscape)
  - Tools: Cursor, Claude Code, Codex, Antigravity, v0, Bolt, Lovable, etc.
  - Approaches: component library selection, design system prompting, screenshot-driven iteration
  - Key question: what produces the best *visual quality* with AI assistance, not just functional correctness?
- [ ] Evaluate component library / design system options for the CineForge aesthetic
  - Candidates: shadcn/ui, Radix, Ark UI, Park UI, Mantine, custom Tailwind system, etc.
  - Criteria: AI-generation friendliness, visual polish ceiling, accessibility, bundle size, composability
- [ ] Document findings in `docs/research/story-011b-ui-tooling/`
  - Recommended stack and rationale
  - Recommended AI workflow (which tools for which tasks)
  - Anti-patterns discovered (what doesn't work for AI-generated UI)

### Phase R2: Research — App Landscape and Inspiration

**Goal**: Survey the competitive/adjacent app landscape and gather visual inspiration from the best creative tools.

- [ ] Identify and evaluate apps in adjacent spaces:
  - Film/video production tools (e.g., Frame.io, Shotgrid, Celtx, StudioBinder, Arc Studio Pro)
  - AI creative tools (e.g., Runway, Pika, Kling, Midjourney, Kaiber)
  - Storyboarding / previz tools (e.g., Storyboarder, Boords, Plot)
  - Writing / screenwriting tools (e.g., Highland, Final Draft, WriterSolo)
  - Pipeline / DAG visualization tools (e.g., Dagster, Prefect, n8n)
  - General creative workspace tools (e.g., Figma, Notion, Linear)
- [ ] Gather screenshots and annotate what works well in each
- [ ] Synthesize a mood board / design direction document
  - Visual language, color palette direction, typography feel, interaction patterns
  - What to steal, what to avoid, what's unique to CineForge
- [ ] Document in `docs/research/story-011b-app-landscape/`

### Phase R3: Research — Persona Workflows

**Goal**: Map the full space of user personas and their workflows through the app.

Known personas (non-exhaustive — the research should deeply consider whether major personas are missing):

1. **Vibe Filmmaker**: Drags in a basic story idea, eagerly awaits what comes out. Minimal interaction. Wants magic.
2. **Film Student**: Digs into every step. Wants to understand how a film is made. Learns from AI agents' reasoning. Inspects every artifact and decision chain.
3. **Storywriter**: Has a story they desperately want to see on screen. Zero film experience/resources. Wants to learn the process. Deeply invested in character development and guided creative choices.
4. **Low-Budget Auteur**: Deep filmmaking knowledge, no budget. Uses the tool to realize visions that would otherwise be impossible. Wants fine-grained creative control.
5. **IRL Filmmaker (Pre-production)**: Uses CineForge for early stages (script breakdown, shot planning, previz) but films it themselves. Cherry-picks the tools where they lack skill or time.
6. **Domain Expert** (e.g., cinematographer, production designer, sound designer): Expert in one craft, wants AI to handle everything else. Deep control over their domain, hands-off everywhere else.

For each persona:
- [ ] Map the end-to-end workflow from "I have an idea" to "I have a film"
- [ ] Identify where they want control vs. where they want AI to handle it
- [ ] Identify the artifact types they care most about inspecting/editing
- [ ] Identify friction points and delight opportunities
- [ ] Document in `docs/research/story-011b-personas/`

### Phase D1: Design — UI Architecture and Interaction Plan

**Goal**: Synthesize research into a concrete UI plan.

- [ ] Define the core navigation model and information architecture
  - How does a user move between project overview, pipeline stages, artifact inspection, and creative decisions?
  - How does progressive disclosure work in practice?
- [ ] Define the "golden path" — the simplest possible workflow:
  1. Drag & drop a script/story → AI parses it → fills in all project details → user clicks OK
  2. AI runs pipeline stages → user sees progress → approves or overrides at each checkpoint
  3. Artifacts appear and are browsable/editable at every step
  4. Final output delivered
- [ ] Define artifact viewer patterns by type:
  - Text artifacts (scripts, canonical text)
  - Structured data (scenes, project config, bibles)
  - Graph data (entity relationships, dependency graphs)
  - Timeline / temporal data (timeline artifact, tracks)
  - Media (storyboards, previz, rendered output — future-proofing)
- [ ] Define the override/drill-in interaction model
  - How does a user go from "OK" mode to "I want to control this"?
  - How do they get back to autopilot?
- [ ] Wireframes or low-fidelity mockups for key screens
- [ ] Document in `docs/research/story-011b-ui-plan/`

### Phase B1: Build — Foundation and Core Screens

**Goal**: Implement the new UI shell, navigation, and core artifact browsing.

- [ ] Set up new UI project (or migrate existing console) with chosen stack
- [ ] Implement app shell: navigation, project switching, responsive layout
- [ ] Implement new-project flow (drag-and-drop → AI parse → confirm)
- [ ] Implement pipeline run view with stage progress
- [ ] Implement artifact browser with type-aware viewers
- [ ] Implement artifact editor/override flows
- [ ] Implement artifact version history and diff views
- [ ] Backend API adjustments as needed to support new UI patterns
- [ ] Cross-browser and responsive testing (desktop primary, tablet secondary)

### Phase B2: Build — Polish and Release Readiness

- [ ] Visual polish pass: animations, transitions, loading states, empty states
- [ ] Error handling and edge cases (network failures, malformed artifacts, long-running pipelines)
- [ ] Accessibility audit and remediation
- [ ] Performance audit (large artifact sets, many versions)
- [ ] User testing with at least 2 persona scenarios end-to-end
- [ ] Documentation: user-facing help/onboarding if needed

---

## Acceptance Criteria

### Design Quality
- [ ] The UI is visually polished enough for public release — not a dev tool aesthetic.
- [ ] A new user can go from "I have a script" to "pipeline running" in under 60 seconds with zero prior knowledge.
- [ ] Progressive disclosure works: simple by default, deep on demand.

### Functional Completeness
- [ ] All Phase 1–2 artifact types have dedicated, type-appropriate viewers.
- [ ] Artifact version history is browsable with visual diffs.
- [ ] Pipeline runs can be started, monitored, and inspected entirely from UI.
- [ ] Project creation works via drag-and-drop with AI auto-fill.
- [ ] AI suggestions are clearly presented with one-click approval at every step.
- [ ] User can override any AI decision and return to autopilot.

### Technical Quality
- [ ] Responsive layout (desktop-first, tablet-usable).
- [ ] Passes accessibility audit (WCAG 2.1 AA minimum).
- [ ] Performance: artifact browser loads within 1s for typical project sizes.
- [ ] Existing backend API contracts preserved or cleanly migrated.

### Research Deliverables (preconditions for build)
- [ ] AI UI tooling research documented with recommended stack.
- [ ] App landscape survey with annotated screenshots and design direction.
- [ ] Persona workflows documented and validated.
- [ ] UI architecture plan with wireframes approved by user.

---

## Constraints and Notes

- The current Operator Console Lite (React 18 + Vite + TypeScript, no component library) may be migrated or replaced depending on Phase R1 findings.
- The backend API (`src/cine_forge/operator_console/app.py`) should be evolved, not rewritten — the data model is sound.
- This story deliberately does NOT implement Phase 4+ features (role chat, creative sessions, collaborative review). It builds the foundation those features will plug into.
- Phase 3 stories (012 Timeline, 013 Tracks) will build their UI surfaces on top of whatever this story establishes — the UI architecture must accommodate timeline/track visualization even if it doesn't implement it.

---

## Tasks

See phased breakdown above. Summary:

- [ ] **R1**: AI UI tooling research
- [ ] **R2**: App landscape and inspiration research
- [ ] **R3**: Persona workflow mapping
- [ ] **D1**: UI architecture and interaction plan
- [ ] **B1**: Foundation build (shell, nav, artifact browsing, project flow, pipeline view)
- [ ] **B2**: Polish and release readiness

---

## Work Log

*(append-only)*
