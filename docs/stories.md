# Project Stories — cine-forge

## Recommended Build Order (updated 2026-02-27, post-ADR-003)

Phases 0–4 are Done. The pipeline runs script-to-entities with roles, chat, and a production UI. ADR-003 redesigned creative direction around five concern groups. The path forward: **land the concern group data model, build the Scene Workspace, then push toward generation.**

### Group 1 — ADR-003 Foundation (no blockers, start now)

| Story | Why |
|---|---|
| **093** Script Bible | First story-lane artifact after ingestion. Cheap, high-value — every downstream role references it. Promotes to Pending first. |
| **094** Concern Group Schemas | **Keystone.** Unblocks 095, 099, 100, and the entire concern group architecture. Must land before any creative direction work. |

These two are the critical path. Build them first, in this order (093 is independent; 094 is independent but unblocks more).

### Group 2 — Creative Direction Core (after 094)

| Story | Why |
|---|---|
| **095** Intent/Mood Layer | The primary interaction surface for all users. Depends on 094. This is what makes CineForge feel like a creative conversation instead of a form. |
| **021** Look & Feel ✅ | Done. First visual concern group — per-scene parallel analysis, Visual Architect persona, DirectionTab integration. |
| **022** Sound & Music | First audio concern group. Ready now. Can parallel with 021 and 095. |

021 and 022 are technically ready today, but building them *after* 094 lands means they can use the real concern group schemas instead of inventing their own. Start 095 as soon as 094 merges; 021/022 can overlap.

### Group 3 — Scene Workspace + Interaction (after 095)

| Story | Why |
|---|---|
| **101** Long-Running Action System | UI infrastructure: centralized hook + banner + chat for all async operations. Fixes broken feedback on direction generation, propagation, and pipeline runs. Should land *before* 099 — Scene Workspace will trigger many long-running actions and needs this foundation. |
| **099** Scene Workspace | The per-scene production surface — five concern tabs, readiness indicators, "let AI fill this." This is ADR-003's centerpiece UI. Depends on 094 + 095. |
| **096** "Chat About This" | Ready now. Generalizes the highlight-to-chat pattern from Story 082 to all artifacts. Natural companion to 099. |
| **100** Motif Tracking | Depends on 094. Motif annotations feed into Look & Feel and Sound & Music. Can parallel with 099. |

099 is the highest-impact UI story in the backlog. It's where filmmakers actually do their work.

### Group 4 — Upstream Infrastructure (ready now, build when needed)

| Story | Why |
|---|---|
| **092** Continuity AI Detection | Ready now. Strengthens the story-lane foundation that concern groups build on. |
| **031** Change Propagation (Semantic) | Ready now. R15 Layer 2 — makes upstream edits flow intelligently downstream. Becomes critical once concern groups generate artifacts that depend on each other. |
| **029** User Asset Injection | Ready now. Unblocks 056 (design studies) and 098 (R17 upload pipeline). |
| **097** AI Artifact Editing | Ready now. Roles proposing and executing edits is core to the read-only prompt model. |

These are independently valuable and have no undone deps. Slot them in alongside Groups 2–3 based on capacity.

### Group 5 — Shot Planning + Visualization (after 021, 022)

| Story | Why |
|---|---|
| **025** Shot Planning | Consumes concern group artifacts. Depends on 021 + 022. The bridge between creative direction and generation. |
| **023** Character & Performance | Draft — resolve whether formal artifacts are needed (may close as "Won't Do" if character bibles + chat suffice). Inform this during 025. |
| **056** Entity Design Studies | Depends on 029. Reference image generation loop — visual identity for characters/locations/props. |
| **026** Storyboard Generation | Depends on 025. Optional but high-value for previz workflows. |
| **027** Animatics & Previz | Depends on 025 + 026. |

### Group 6 — Generation (after Group 5)

| Story | Why |
|---|---|
| **098** Real-World Asset Upload | Depends on 029. R17 upload pipeline — origin-agnostic asset system. |
| **028** Render Adapter | Depends on 025, 027, 022, 098. The prompt compiler — concern groups → model-ready generation prompts. Last major pipeline stage before video output. |
| **030** Generated Output QA | Depends on 028, 021, 022, 032. Quality gate on generated video. Deepest node in the dependency graph. |

### Group 7 — Polish & Infrastructure (ready now, lower priority)

| Story | Why |
|---|---|
| **032** Cost Tracking | Ready now. Budget caps and cost dashboards. Build when generation gets expensive. |
| **033** Memory Model | Ready now. Canonical/working/transcript memory tiers. Build when long conversations lose context. |
| **034** Style Pack Creator | Ready now. In-app style pack authoring. Nice-to-have, not blocking. |
| **044** Mobile-Friendly UI | Ready now. Responsive layout. Build when users need mobile access. |
| **046** Theme System | Ready now (Draft). Light/dark/auto + palettes. Build when visual polish matters. |

---

This index tracks stories in `/docs/stories/` for the cine-forge pipeline.

NOTES from Cam:
- 20260212: Seeddance 2.0 released and it's insane: https://x.com/altryne/status/2021967972055842893?s=20
  - "Takes a TEXT STORYBOARD image + character ref + scene ref + prop ref → coherent 15-second film."

## Story List

| ID | Title | Phase | Priority | Status | Link |
|----|-------|-------|----------|--------|------|
| 001 | Project Setup and Scaffolding | 0 — Foundation | High | Done | [story-001](stories/story-001-project-setup.md) |
| 002 | Pipeline Foundation (Driver, Artifact Store, Schemas) | 0 — Foundation | High | Done | [story-002](stories/story-002-pipeline-foundation.md) |
| 003 | Story Ingestion Module | 1 — MVP Pipeline | High | Done | [story-003](stories/story-003-story-ingestion.md) |
| 003b | DOCX Ingestion Support | 1 — MVP Pipeline | Medium | Done | [story-003b](stories/story-003b-docx-support.md) |
| 004 | Script Normalization Module | 1 — MVP Pipeline | High | Done | [story-004](stories/story-004-script-normalization.md) |
| 005 | Scene Extraction Module | 1 — MVP Pipeline | High | Done | [story-005](stories/story-005-scene-extraction.md) |
| 006 | Project Configuration (Auto-Initialized) | 1 — MVP Pipeline | High | Done | [story-006](stories/story-006-project-configuration.md) |
| 007 | MVP Recipe and End-to-End Smoke Test | 1 — MVP Pipeline | High | Done | [story-007](stories/story-007-mvp-recipe-smoke-test.md) |
| 007b | Operator Console Lite (Stopgap GUI) | 1 — MVP Pipeline | High | Done | [story-007b](stories/story-007b-operator-console-lite.md) |
| 007c | MVP Reality Validation and Remediation | 1 — MVP Pipeline | High | Done | [story-007c](stories/story-007c-mvp-reality-remediation.md) |
| 008 | Bible Infrastructure and Character Bible | 2 — World Building | High | Done | [story-008](stories/story-008-character-bible.md) |
| 009 | Location and Prop Bibles | 2 — World Building | High | Done | [story-009](stories/story-009-location-prop-bibles.md) |
| 010 | Entity Relationship Graph | 2 — World Building | Medium | Done | [story-010](stories/story-010-entity-graph.md) |
| 011 | Asset State Tracking (Continuity) | 2 — World Building | Medium | Done | [story-011](stories/story-011-continuity-tracking.md) |
| 011b | Operator Console — Research & Design Decisions | 2.5 — UI | High | Done | [story-011b](stories/story-011b-operator-console.md) |
| 011c | Resource-oriented Routing | 2.5 — UI | Medium | Done | [story-011c](stories/story-011c-resource-oriented-routing.md) |
| 011d | Operator Console — Design & Build | 2.5 — UI | High | Done | [story-011d](stories/story-011d-operator-console-build.md) |
| 011e | Operator Console — UX Golden Path | 2.5 — UI | High | Done | [story-011e](stories/story-011e-ux-golden-path.md) |
| 011f | Operator Console — Conversational AI Chat | 2.5 — UI | High | Done | [story-011f](stories/story-011f-conversational-ai-chat.md) |
| 012 | Timeline Data Artifact | 3 — Timeline | Medium | Done | [story-012](stories/story-012-timeline-artifact.md) |
| 013 | Track System and Always-Playable Rule | 3 — Timeline | Medium | Done | [story-013](stories/story-013-track-system.md) |
| 014 | Role System Foundation | 4 — Role System | High | Done | [story-014](stories/story-014-role-system-foundation.md) |
| 015 | Director and Canon Guardians | 4 — Role System | High | Done | [story-015](stories/story-015-director-canon-guardians.md) |
| 016 | Style Pack Infrastructure | 4 — Role System | Medium | Done | [story-016](stories/story-016-style-pack-infrastructure.md) |
| 017 | Suggestion and Decision Tracking | 4 — Role System | Medium | Done | [story-017](stories/story-017-suggestion-decision-tracking.md) |
| 018 | Inter-Role Communication Protocol | 4 — Role System | Medium | Done | [story-018](stories/story-018-inter-role-communication.md) |
| 019 | Human Control Modes and Creative Sessions | 4 — Role System | High | Done | [story-019](stories/story-019-human-interaction.md) |
| 020 | Editorial Architect and Editorial Direction | 5 — Creative Direction | Medium | Done | [story-020](stories/story-020-editorial-architect.md) |
| 021 | Look & Feel — Visual Direction | 5 — Creative Direction | Medium | Done | [story-021](stories/story-021-visual-architect.md) |
| 022 | Sound & Music — Sound Direction | 5 — Creative Direction | Medium | To Do | [story-022](stories/story-022-sound-designer.md) |
| 023 | Character & Performance — Performance Direction | 5 — Creative Direction | Medium | Draft | [story-023](stories/story-023-actor-agents.md) |
| ~~024~~ | ~~Direction Convergence and Review~~ | ~~5 — Creative Direction~~ | ~~Medium~~ | Cancelled | ~~[story-024](stories/story-024-direction-convergence.md)~~ — Eliminated by ADR-003. Intent/Mood layer handles cross-group coherence. |
| 025 | Shot Planning | 6 — Shot Planning & Viz | Medium | To Do | [story-025](stories/story-025-shot-planning.md) |
| 026 | Storyboard Generation (Optional) | 6 — Shot Planning & Viz | Low | To Do | [story-026](stories/story-026-storyboard-generation.md) |
| 027 | Animatics, Keyframes, and Previz (Optional) | 6 — Shot Planning & Viz | Low | To Do | [story-027](stories/story-027-animatics-previz.md) |
| 028 | Render Adapter Module | 7 — Generation | Low | To Do | [story-028](stories/story-028-render-adapter.md) |
| 029 | User Asset Injection | 7 — Generation | Medium | To Do | [story-029](stories/story-029-user-asset-injection.md) |
| 030 | Generated Output QA | 7 — Generation | Medium | To Do | [story-030](stories/story-030-generated-output-qa.md) |
| 031 | Change Propagation (Semantic Impact Layer) | 8 — Cross-Cutting Polish | Medium | To Do | [story-031](stories/story-031-change-propagation.md) |
| 032 | Cost Tracking and Budget Management | 8 — Cross-Cutting Polish | Medium | To Do | [story-032](stories/story-032-cost-tracking.md) |
| 033 | Memory Model and Transcript Retention | 8 — Cross-Cutting Polish | Low | To Do | [story-033](stories/story-033-memory-model.md) |
| 034 | In-App Style Pack Creator | 8 — Cross-Cutting Polish | Low | To Do | [story-034](stories/story-034-style-pack-creator.md) |
| 035 | Model Benchmarking Tooling (promptfoo) | Cross-Cutting | High | Done | [story-035](stories/story-035-model-benchmarking.md) |
| 036 | Model Selection and Eval Framework | Cross-Cutting | High | Done | [story-036](stories/story-036-model-selection.md) |
| 037 | Production Deployment to cineforge.copper-dog.com | Cross-Cutting | High | Done | [story-037](stories/story-037-production-deployment.md) |
| 038 | Multi-Provider LLM Transport | Cross-Cutting | High | Done | [story-038](stories/story-038-multi-provider-transport.md) |
| 039 | Apply Model Selections to Production | Cross-Cutting | Medium | Done | [story-039](stories/story-039-apply-model-selections.md) |
| 040 | Pipeline Performance Optimization | Cross-Cutting | High | Done | [story-040](stories/story-040-pipeline-performance-optimization.md) |
| 041 | Artifact Quality Improvements | Cross-Cutting | Medium | Done | [story-041](stories/story-041-artifact-quality-improvements.md) |
| 042 | Wire Mock UI to Real APIs | 2.5 — UI | Medium | Done | [story-042](stories/story-042-wire-mock-ui-to-apis.md) |
| 043 | Entity-First Navigation | 2.5 — UI | High | Done | [story-043](stories/story-043-entity-first-navigation.md) |
| 044 | Mobile-Friendly UI | 2.5 — UI | Medium | To Do | [story-044](stories/story-044-mobile-friendly-ui.md) |
| 045 | Entity Cross-Linking | 2.5 — UI | Medium | Done | [story-045](stories/story-045-entity-cross-linking.md) |
| 046 | Theme System (Light/Dark/Auto + Palettes) | 2.5 — UI | Medium | Draft | [story-046](stories/story-046-theme-system.md) |
| 047 | Benchmark Sonnet 4.6 Across All Evals | Cross-Cutting | High | Done | [story-047](stories/story-047-sonnet-46-benchmarks.md) |
| 048 | PDF Input Preview Decode Fix | 2.5 — UI/API | High | Done | [story-048](stories/story-048-pdf-input-preview-decode.md) |
| 049 | Import Normalization Format Suite | 1 — MVP Pipeline | High | Done | [story-049](stories/story-049-import-normalization-format-suite.md) |
| 050 | Provider Resilience: Retries, Fallbacks, and Stage Resume | Cross-Cutting | High | Done | [story-050](stories/story-050-provider-resilience-retry-fallback.md) |
| 051 | Chat UX Polish: Ordering, Naming, and Progress Card | 2.5 — UI | High | Done | [story-051](stories/story-051-chat-ux-polish.md) |
| 052 | Streaming Artifact Yield: Live Per-Entity Progress | Cross-Cutting | Medium | Done | [story-052](stories/story-052-streaming-artifact-yield.md) |
| 053 | Cross-CLI Skills/Prompts Unification | Cross-Cutting | High | Done | [story-053](stories/story-053-cross-cli-skills-unification.md) |
| 054 | Liberty Church Character Artifact Cleanup Inventory | Cross-Cutting | High | Done | [story-054](stories/story-054-liberty-church-character-artifact-cleanup-inventory.md) |
| 055 | LLM-First Entity Adjudication for Character, Location, and Prop | Cross-Cutting | High | Done | [story-055](stories/story-055-llm-first-entity-adjudication-for-character-location-prop.md) |
| 056 | Entity Design Studies (Reference Image Generation Loop) | 6 — Shot Planning & Viz | High | Blocked | [story-056](stories/story-056-entity-design-study-reference-images.md) |
| 057 | Entity Prev/Next Navigation | 2.5 — UI | High | Done | [story-057](stories/story-057-entity-prev-next-navigation.md) |
| 058 | Comprehensive Export & Share | 2.5 — UI | High | Done | [story-058](stories/story-058-comprehensive-export-share.md) |
| 059 | Pipeline UI Refinement | 2.5 — UI | High | Done | [story-059](stories/story-059-pipeline-ui-refinement.md) |
| 060 | Entity Quality Regression | Cross-Cutting | High | Done | [story-060](stories/story-060-entity-quality-regression.md) |
| 061 | Optimize Scene Extraction | Cross-Cutting | High | Done | [story-061](stories/story-061-optimize-scene-extraction.md) |
| 062 | 3-Stage Ingestion: Intake, Breakdown, Analysis | Cross-Cutting | High | Done | [story-062](stories/story-062-refactor-ingestion-three-stage.md) |
| 063 | Automatic Project Title Extraction from Script | 1 — MVP Pipeline | High | Done | [story-063](stories/story-063-automatic-project-title-extraction.md) |
| 064 | Screenplay Format Round-Trip: Converter Upgrade + Fidelity Test Suite | Cross-Cutting | Medium | Done | [story-064](stories/story-064-screenplay-format-round-trip.md) |
| 065 | Parallel Bible Extraction: Performance Optimization for Entity-Heavy Scripts | Cross-Cutting | High | Done | [story-065](stories/story-065-parallel-bible-extraction.md) |
| 066 | UI Component Deduplication & Template Consolidation | 2.5 — UI | High | Done | [story-066](stories/story-066-ui-component-deduplication.md) |
| 067 | Chat Navigation Message Deduplication | 2.5 — UI | High | Done | [story-067](stories/story-067-chat-duplicate-nav-dedup.md) |
| 068 | History-Aware Back Button Navigation | 2.5 — UI | High | Done | [story-068](stories/story-068-back-button-history-navigation.md) |
| 069 | Inbox Item Read/Complete State | 2.5 — UI | High | Done | [story-069](stories/story-069-inbox-read-state.md) |
| 070 | Script View Scene Dividers & Entity Hotlinks | 2.5 — UI | Medium | Done | [story-070](stories/story-070-script-view-scene-dividers-and-hotlinks.md) |
| 071 | Refine vs. Regenerate Pipeline Modes | Cross-Cutting | Medium | Deferred | [story-071](stories/story-071-refine-vs-regenerate-pipeline.md) |
| 072 | Live Entity Discovery Feedback | 2.5 — UI | Medium | Done | [story-072](stories/story-072-live-entity-discovery-feedback.md) |
| 073 | Add `after:` ordering-only stage dependency to recipe DSL | Engine | Medium | Done | [story-073](stories/story-073-add-after-ordering-dependency.md) |
| 074 | Artifact graph staleness: regression tests + sibling fix | Engine | Medium | Done | [story-074](stories/story-074-artifact-graph-staleness-regression-tests.md) |
| 075 | Entity Detail Page Polish | 2.5 — UI | High | Done | [story-075](stories/story-075-entity-detail-page-polish.md) |
| 076 | Entity Detail: Cross-Reference Layout & Narrative Role Polish | 2.5 — UI | High | Done | [story-076](stories/story-076-entity-detail-cross-ref-layout.md) |
| 077 | Character Coverage & Prominence Tiers | World Building / UI | Medium | Done | [story-077](stories/story-077-character-coverage-and-prominence-tiers.md) |
| 078 | Entity Detail: Scroll-to-Top, Cross-Ref Ordering & Props Metadata | 2.5 — UI | Medium | Done | [story-078](stories/story-078-entity-detail-enhancements.md) |
| 079 | Chat & Nav Bugs + Polish Bundle | 2.5 — UI | Medium | Done | [story-079](stories/story-079-chat-nav-bugs-and-polish.md) |
| 080 | LLM-Powered Action Line Entity Extraction | World Building | High | Done | [story-080](stories/story-080-llm-action-line-entity-extraction.md) |
| 081 | Scene Index as Canonical Character Source | World Building | High | Done | [story-081](stories/story-081-scene-index-canonical-characters.md) |
| 082 | Creative Direction UX | 5 — Creative Direction | High | Done | [story-082](stories/story-082-creative-direction-ux.md) |
| 083 | Group Chat Architecture | 5 — Creative Direction | High | Done | [story-083](stories/story-083-group-chat-architecture.md) |
| 084 | Character Chat Agents & Story Editor Rename | 5 — Creative Direction | High | Done | [story-084](stories/story-084-character-chat-agents.md) |
| 085 | Pipeline Capability Graph & Navigation Bar | Cross-Cutting | High | Done | [story-085](stories/story-085-pipeline-capability-graph.md) |
| 086 | AI Navigation Intelligence | Cross-Cutting | High | Done | [story-086](stories/story-086-ai-navigation-intelligence.md) |
| 087 | Pre-flight Summary Cards | Cross-Cutting | Medium | Done | [story-087](stories/story-087-preflight-summary-cards.md) |
| 088 | Staleness UX | Cross-Cutting | Medium | Done | [story-088](stories/story-088-staleness-ux.md) |
| 089 | Interaction Mode Selection | Cross-Cutting | Low | Done | [story-089](stories/story-089-interaction-mode-selection.md) |
| ~~090~~ | ~~Persona-Adaptive Workspaces~~ | ~~Cross-Cutting~~ | ~~Low~~ | Cancelled | ~~[story-090](stories/story-090-persona-adaptive-workspaces.md)~~ — Superseded by two-view architecture (Story Explorer + Scene Workspace) + interaction mode (Story 089). See ADR-003. |
| 092 | Continuity AI Detection & Gap Analysis | World Building | Medium | Pending | [story-092](stories/story-092-continuity-ai-detection.md) |
| 093 | Script Bible Artifact | 5 — Creative Direction | High | Done | [story-093](stories/story-093-script-bible.md) |
| 094 | Concern Group Artifact Schemas | 5 — Creative Direction | High | Done | [story-094](stories/story-094-concern-group-schemas.md) |
| 095 | Intent / Mood Layer | 5 — Creative Direction | High | Done | [story-095](stories/story-095-intent-mood-layer.md) |
| 096 | "Chat About This" Interaction Pattern | 5 — Creative Direction | Medium | Draft | [story-096](stories/story-096-chat-about-this.md) |
| 097 | AI Artifact Editing | 5 — Creative Direction | Medium | Draft | [story-097](stories/story-097-ai-artifact-editing.md) |
| 098 | Real-World Asset Upload Pipeline | 7 — Generation | Medium | Draft | [story-098](stories/story-098-real-asset-upload.md) |
| 099 | Scene Workspace | 5 — Creative Direction | High | Pending | [story-099](stories/story-099-scene-workspace.md) |
| 100 | Motif Tracking System | 5 — Creative Direction | Medium | Draft | [story-100](stories/story-100-motif-tracking.md) |
| 101 | Centralized Long-Running Action System | 2.5 — UI | High | Pending | [story-101](stories/story-101-long-running-action-system.md) |

## Phase Summary

- **Phase 0 — Foundation** (001–002): Project scaffolding and pipeline infrastructure. Artifact store with immutability, snapshot versioning, dependency graph (structural invalidation), audit metadata, cost tracking hooks, and structural validation.
- **Phase 1 — MVP Pipeline** (003–007): First working pipeline: script in → canonical script + scenes + project config out. End-to-end smoke test.
- **Phase 2 — World Building** (008–011): Folder-based bibles (characters, locations, props), entity relationship graph, continuity state tracking.
- **Phase 2.5 — UI** (011b–011c): Production-quality Operator Console and resource-oriented routing. Research-driven design (AI tooling, app landscape, persona workflows), then build. Replaces stopgap 007b console. Foundation for Phase 3+ UI surfaces.
- **Phase 3 — Timeline** (012–013): Timeline data artifact with scene/story ordering, stacked tracks, always-playable rule.
- **Phase 4 — Role System** (014–019): Role hierarchy, Director + Canon Guardians, style pack loading, suggestion/decision lifecycle, inter-role communication, human interaction (control modes, creative sessions with @agent, direct artifact editing).
- **Phase 5 — Creative Direction** (020–023, 093–097, 099–100): Three-layer director's vision model (ADR-003): Intent/Mood layer sets global tone, five concern groups (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World) organize ~87 creative elements, prompts are read-only compiled artifacts. Scene Workspace is the per-scene production surface. Script bible, motif tracking, "chat about this," and AI artifact editing support the creative conversation.
- **Phase 6 — Shot Planning & Visualization** (025–027): Coverage strategy, individual shot definitions, export compatibility, optional storyboards/animatics/keyframes/previz.
- **Phase 7 — Generation** (028–030, 098): Render adapter (concern group → compiled prompt + engine packs), user asset injection (soft/hard locks, R17 real-world asset pipeline), generated output QA with media perception.
- **Phase 8 — Cross-Cutting Polish** (031–034): AI-powered semantic impact assessment, cost dashboards and budget caps, memory model (canonical/working/transcript), in-app style pack creator via deep research APIs.

## Spec Coverage Map

Quick reference showing which spec sections each phase addresses:

| Spec Section | Phase |
|---|---|
| 2.1–2.2 Immutability, Versioning | 0 (002) |
| 2.3 Change Propagation — Layer 1 (structural) | 0 (002) |
| 2.3 Change Propagation — Layer 2 (semantic) | 8 (031) |
| 2.4 AI-Driven | 1+ (all AI modules) |
| 2.5 Human Control | 4 (019) |
| 2.6 Explanation Mandatory | 0 (002, audit metadata) |
| 2.7 Cost Transparency — hooks | 0 (002) |
| 2.7 Cost Transparency — dashboards/budgets | 8 (032) |
| 2.8 QA — structural validation | 0 (002) |
| 2.8 QA — dedicated QA pass | 7 (030) |
| 3 Pipeline Overview, 3.1 Stage Progression | 0 (002), 1 (007) |
| 4 Ingestion, Normalization, Config | 1 (003–006) |
| 5 Scene Extraction | 1 (005) |
| 6 Bibles, Entity Graph, Continuity | 2 (008–011) |
| 7 Timeline | 3 (012–013) |
| 8.1–8.2 Role Hierarchy, Capability Gating | 4 (014–015) |
| 8.3–8.4 Style Packs, Creation | 4 (016), 8 (034) |
| 8.5 Suggestion System | 4 (017) |
| 8.6 Inter-Role Communication | 4 (018) |
| 8.7 Human Interaction Model | 4 (019) |
| 4.5 Script Bible | 5 (093) |
| 4.6 Two-Lane Architecture | 5 (093, 094) |
| 9 Editorial Architect, 12.4 Rhythm & Flow | 5 (020) |
| 9 Visual Architect, 12.2 Look & Feel | 5 (021) |
| 11 Sound Design, 12.3 Sound & Music | 5 (022) |
| 10 Actor Agents, 12.5 Character & Performance | 5 (023) |
| 12.1 Intent / Mood Layer | 5 (095) |
| 12.6 Story World | 5 (100) |
| 12.7 Readiness Indicators | 5 (099) |
| 12.8 Prompt Compilation Model | 5 (094, 028) |
| 13 Shot Planning | 6 (025) |
| 14 Storyboards | 6 (026) |
| 15 Animatics, 16 Keyframes | 6 (027) |
| 17 Render Adapter | 7 (028) |
| 18 User Asset Injection (R17) | 7 (029, 098) |
| 19 Memory Model | 8 (033) |
| 20 Metadata & Auditing | 0 (002, baked in) |
| 21 Operating Modes | 4 (019) |
