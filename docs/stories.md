# Project Stories — cine-forge

## Recommended Order (next up)

Guiding priorities: **get a working pipeline fast** (MVP: script in → structured scenes + project config out), then layer on world-building, temporal structure, roles, and creative tooling. Build the foundation right — immutable artifacts, dependency tracking, audit metadata, modular architecture — so everything after Phase 1 slots in cleanly.


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
| 020 | Editorial Architect and Editorial Direction | 5 — Creative Direction | Medium | To Do | [story-020](stories/story-020-editorial-architect.md) |
| 021 | Visual Architect and Visual Direction | 5 — Creative Direction | Medium | To Do | [story-021](stories/story-021-visual-architect.md) |
| 022 | Sound Designer and Sound Direction | 5 — Creative Direction | Medium | To Do | [story-022](stories/story-022-sound-designer.md) |
| 023 | Actor Agents and Performance Direction | 5 — Creative Direction | Medium | To Do | [story-023](stories/story-023-actor-agents.md) |
| 024 | Direction Convergence and Review | 5 — Creative Direction | Medium | To Do | [story-024](stories/story-024-direction-convergence.md) |
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
| 039 | Apply Model Selections to Production | Cross-Cutting | Medium | To Do | [story-039](stories/story-039-apply-model-selections.md) |
| 040 | Pipeline Performance Optimization | Cross-Cutting | High | Done | [story-040](stories/story-040-pipeline-performance-optimization.md) |
| 041 | Artifact Quality Improvements | Cross-Cutting | Medium | Done | [story-041](stories/story-041-artifact-quality-improvements.md) |
| 042 | Wire Mock UI to Real APIs | 2.5 — UI | Medium | Done | [story-042](stories/story-042-wire-mock-ui-to-apis.md) |
| 043 | Entity-First Navigation | 2.5 — UI | High | Done | [story-043](stories/story-043-entity-first-navigation.md) |
| 044 | Mobile-Friendly UI | 2.5 — UI | Medium | Draft | [story-044](stories/story-044-mobile-friendly-ui.md) |
| 045 | Entity Cross-Linking | 2.5 — UI | Medium | Draft | [story-045](stories/story-045-entity-cross-linking.md) |
| 046 | Theme System (Light/Dark/Auto + Palettes) | 2.5 — UI | Medium | Draft | [story-046](stories/story-046-theme-system.md) |
| 047 | Benchmark Sonnet 4.6 Across All Evals | Cross-Cutting | High | Done | [story-047](stories/story-047-sonnet-46-benchmarks.md) |
| 048 | PDF Input Preview Decode Fix | 2.5 — UI/API | High | Done | [story-048](stories/story-048-pdf-input-preview-decode.md) |
| 049 | Import Normalization Format Suite | 1 — MVP Pipeline | High | Done | [story-049](stories/story-049-import-normalization-format-suite.md) |
| 050 | Provider Resilience: Retries, Fallbacks, and Stage Resume | Cross-Cutting | High | Done | [story-050](stories/story-050-provider-resilience-retry-fallback.md) |
| 051 | Chat UX Polish: Ordering, Naming, and Progress Card | 2.5 — UI | High | Done | [story-051](stories/story-051-chat-ux-polish.md) |
| 052 | Streaming Artifact Yield: Live Per-Entity Progress | Cross-Cutting | Medium | Draft | [story-052](stories/story-052-streaming-artifact-yield.md) |
| 053 | Cross-CLI Skills/Prompts Unification | Cross-Cutting | High | Done | [story-053](stories/story-053-cross-cli-skills-unification.md) |
| 054 | Liberty Church Character Artifact Cleanup Inventory | Cross-Cutting | High | Done | [story-054](stories/story-054-liberty-church-character-artifact-cleanup-inventory.md) |
| 055 | LLM-First Entity Adjudication for Character, Location, and Prop | Cross-Cutting | High | Done | [story-055](stories/story-055-llm-first-entity-adjudication-for-character-location-prop.md) |
| 056 | Entity Design Studies (Reference Image Generation Loop) | 6 — Shot Planning & Viz | High | To Do | [story-056](stories/story-056-entity-design-study-reference-images.md) |
| 057 | Entity Prev/Next Navigation | 2.5 — UI | High | Done | [story-057](stories/story-057-entity-prev-next-navigation.md) |
| 058 | Comprehensive Export & Share | 2.5 — UI | High | To Do | [story-058](stories/story-058-comprehensive-export-share.md) |
| 059 | Pipeline UI Refinement | 2.5 — UI | High | Done | [story-059](stories/story-059-pipeline-ui-refinement.md) |
| 060 | Entity Quality Regression | Cross-Cutting | High | Done | [story-060](stories/story-060-entity-quality-regression.md) |

## Phase Summary

- **Phase 0 — Foundation** (001–002): Project scaffolding and pipeline infrastructure. Artifact store with immutability, snapshot versioning, dependency graph (structural invalidation), audit metadata, cost tracking hooks, and structural validation.
- **Phase 1 — MVP Pipeline** (003–007): First working pipeline: script in → canonical script + scenes + project config out. End-to-end smoke test.
- **Phase 2 — World Building** (008–011): Folder-based bibles (characters, locations, props), entity relationship graph, continuity state tracking.
- **Phase 2.5 — UI** (011b–011c): Production-quality Operator Console and resource-oriented routing. Research-driven design (AI tooling, app landscape, persona workflows), then build. Replaces stopgap 007b console. Foundation for Phase 3+ UI surfaces.
- **Phase 3 — Timeline** (012–013): Timeline data artifact with scene/story ordering, stacked tracks, always-playable rule.
- **Phase 4 — Role System** (014–019): Role hierarchy, Director + Canon Guardians, style pack loading, suggestion/decision lifecycle, inter-role communication, human interaction (control modes, creative sessions with @agent, direct artifact editing).
- **Phase 5 — Creative Direction** (020–024): Each creative role produces structured direction artifacts (editorial, visual, sound, performance). Direction convergence review before shot planning.
- **Phase 6 — Shot Planning & Visualization** (025–027): Coverage strategy, individual shot definitions, export compatibility, optional storyboards/animatics/keyframes/previz.
- **Phase 7 — Generation** (028–030): Render adapter (two-part prompt + engine packs), user asset injection (soft/hard locks), generated output QA with media perception.
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
| 9 Editorial Architect, 12.1 Editorial Direction | 5 (020) |
| 9 Visual Architect, 12.2 Visual Direction | 5 (021) |
| 11 Sound Design, 12.3 Sound Direction | 5 (022) |
| 10 Actor Agents, 12.4 Performance Direction | 5 (023) |
| 12.5 Direction Convergence | 5 (024) |
| 13 Shot Planning | 6 (025) |
| 14 Storyboards | 6 (026) |
| 15 Animatics, 16 Keyframes | 6 (027) |
| 17 Render Adapter | 7 (028) |
| 18 User Asset Injection | 7 (029) |
| 19 Memory Model | 8 (033) |
| 20 Metadata & Auditing | 0 (002, baked in) |
| 21 Operating Modes | 4 (019) |
