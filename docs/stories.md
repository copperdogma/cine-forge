# Project Stories — cine-forge

## Recommended Order (next up)

Guiding priorities: **get a working pipeline fast** (MVP: script in → structured scenes + project config out), then layer on world-building, temporal structure, roles, and creative tooling. Build the foundation right — immutable artifacts, dependency tracking, audit metadata, modular architecture — so everything after Phase 1 slots in cleanly.

1. **001 — Project Setup and Scaffolding**: Make the workspace AI-ready. Git, structure, AGENTS.md, cursor skills, story tracking.
2. **002 — Pipeline Foundation**: Driver, artifact store (immutability, versioning, dependency graph), schemas, module contracts, run isolation. Skeleton pipeline that executes.
3. **003 — Story Ingestion Module**: Accept screenplay/prose/notes, detect format, store as artifact.
4. **004 — Script Normalization Module**: AI converts input to canonical screenplay format with confidence and labeled inventions.
5. **005 — Scene Extraction Module**: AI extracts structured scenes from canonical script.
6. **006 — Project Configuration**: Auto-initialize project parameters from ingested story; user confirms/modifies.
7. **007 — MVP Recipe and Smoke Test**: Wire 003–006 into a recipe, run end-to-end, verify artifacts. First "it works" milestone.
8. **008 — Bible Infrastructure and Character Bible**: Folder-based bible model with manifest, character extraction from script.
9. **009 — Location and Prop Bibles**: Same pattern as characters for locations and props.
10. **010 — Entity Relationship Graph**: Cross-entity typed relationship edges extracted from script and bibles.

This index tracks stories in `/docs/stories/` for the cine-forge pipeline.

## Story List

| ID | Title | Phase | Priority | Status | Link |
|----|-------|-------|----------|--------|------|
| 001 | Project Setup and Scaffolding | 0 — Foundation | High | Done | [story-001](stories/story-001-project-setup.md) |
| 002 | Pipeline Foundation (Driver, Artifact Store, Schemas) | 0 — Foundation | High | To Do | [story-002](stories/story-002-pipeline-foundation.md) |
| 003 | Story Ingestion Module | 1 — MVP Pipeline | High | To Do | [story-003](stories/story-003-story-ingestion.md) |
| 004 | Script Normalization Module | 1 — MVP Pipeline | High | To Do | [story-004](stories/story-004-script-normalization.md) |
| 005 | Scene Extraction Module | 1 — MVP Pipeline | High | To Do | [story-005](stories/story-005-scene-extraction.md) |
| 006 | Project Configuration (Auto-Initialized) | 1 — MVP Pipeline | High | To Do | [story-006](stories/story-006-project-configuration.md) |
| 007 | MVP Recipe and End-to-End Smoke Test | 1 — MVP Pipeline | High | To Do | [story-007](stories/story-007-mvp-recipe-smoke-test.md) |
| 008 | Bible Infrastructure and Character Bible | 2 — World Building | High | To Do | [story-008](stories/story-008-character-bible.md) |
| 009 | Location and Prop Bibles | 2 — World Building | High | To Do | [story-009](stories/story-009-location-prop-bibles.md) |
| 010 | Entity Relationship Graph | 2 — World Building | Medium | To Do | [story-010](stories/story-010-entity-graph.md) |
| 011 | Asset State Tracking (Continuity) | 2 — World Building | Medium | To Do | [story-011](stories/story-011-continuity-tracking.md) |
| 012 | Timeline Data Artifact | 3 — Timeline | Medium | To Do | [story-012](stories/story-012-timeline-artifact.md) |
| 013 | Track System and Always-Playable Rule | 3 — Timeline | Medium | To Do | [story-013](stories/story-013-track-system.md) |
| 014 | Role System Foundation | 4 — Role System | High | To Do | [story-014](stories/story-014-role-system-foundation.md) |
| 015 | Director and Canon Guardians | 4 — Role System | High | To Do | [story-015](stories/story-015-director-canon-guardians.md) |
| 016 | Style Pack Infrastructure | 4 — Role System | Medium | To Do | [story-016](stories/story-016-style-pack-infrastructure.md) |
| 017 | Suggestion and Decision Tracking | 4 — Role System | Medium | To Do | [story-017](stories/story-017-suggestion-decision-tracking.md) |
| 018 | Inter-Role Communication Protocol | 4 — Role System | Medium | To Do | [story-018](stories/story-018-inter-role-communication.md) |
| 019 | Human Control Modes and Creative Sessions | 4 — Role System | High | To Do | [story-019](stories/story-019-human-interaction.md) |
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

## Phase Summary

- **Phase 0 — Foundation** (001–002): Project scaffolding and pipeline infrastructure. Artifact store with immutability, snapshot versioning, dependency graph (structural invalidation), audit metadata, cost tracking hooks, and structural validation.
- **Phase 1 — MVP Pipeline** (003–007): First working pipeline: script in → canonical script + scenes + project config out. End-to-end smoke test.
- **Phase 2 — World Building** (008–011): Folder-based bibles (characters, locations, props), entity relationship graph, continuity state tracking.
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
