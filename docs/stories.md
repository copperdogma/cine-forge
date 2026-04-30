# Project Stories — cine-forge

> Generated from story metadata + `docs/methodology/state.yaml`. Do not edit manually.

## Status Key

- **Draft** — Worth preserving, but still incomplete or substrate-unverified
- **Pending** — Fully detailed and honestly buildable now
- **In Progress** — Active work
- **Blocked** — Concrete enough to preserve, but blocked by a named evidence-backed blocker
- **Deferred** — Intentionally parked
- **Cancelled** — Explicitly abandoned
- **Done** — Complete and validated

## Numbering Convention

Story IDs are identifiers, not sequencing proof. Legacy suffix IDs such as `003b` and `011f` remain valid historical identifiers. New stories should continue using the next available plain numeric ID.

## Current Execution Map

Phases 0–5 foundation are landed, the first three Phase 6 visualization layers are in place, and the first Phase 7 render substrate now includes runtime media validation for both generated-video and AI-previz outputs. Story 149 closed the AI-only previz truth slice, Story 150 closed the runtime-detector substrate, Story 153 closed the provider-floor measurement slice, Stories 164 and 165 closed the honest scene-render path plus refresh loop, Story 166 closed the project-level final-output playable-assembly slice, Story 167 closed the project-cut validation / trust follow-up, Story 168 closed the reference-conditioned scene-generation product-truth slice, Story 169 closed the final-render provider-floor decision on that representative reference-conditioned route, Story 170 closed the breadth-first scene-generation follow-up, Story 174 closed the bounded compact-previz compare, Story 175 closed the scene-ready prerequisite-collapse follow-up by keeping the honest one-pass previz-prep lane as the shipped route, Story 176 closed the one-pass xAI ship decision at `65514 ms` first playable with `47865 ms` of prerequisites, Story 152 revalidated the warmed regenerate loop at `17869 ms` first playable for `start_from=ai_previz` reuse versus `39325 ms` for full regenerate on the same shipped lane, and Story 177 closed the OTIO narrative-export follow-up that Story 130 explicitly deferred until the shared payload stabilized. The `spec:6` / `spec:7` lane is still runtime-blocking against the fast-previz detector, Story 190 is waiting for a realistic-reference fixture trigger, Story 191 closed the Brick & Steel final-render prompt compiler duplicate-dialogue and cadence repair, Story 192 closed the residual GPT-image design-study lifecycle truth work, Story 193 closed the render-clip planning artifact, and Story 194 closed the dependent multi-clip rendering slice.

### Pending — Ready To Build Now

No stories currently fit this lane.

### In Progress

No stories currently in progress.

### Pending — Ready, But Sequence-Sensitive

No stories currently need the sequence-sensitive lane.

### Draft — Scope Or Decision Needed First

| Story | Why |
|---|---|
| **102** Promptfoo Multi-Turn Conversational Evals | Worth keeping visible, but it is less immediately executable than the current product-facing pending lane. |
| **103** AGENTS.md Runbook Extraction (300-Line Cap) | Valid repo-hygiene draft, but still needs tighter scoping and remains secondary to the current product-facing backlog. |
| **104** Tiered Quality Metrics for Eval Scoring | Worth keeping visible, but it is less immediately executable than the current product-facing pending lane. |
| **105** Parallel Chunk Extraction via ThreadPoolExecutor | Worth keeping visible, but it is less immediately executable than the current product-facing pending lane. |
| **106** Disk-Backed Chunk-Level Extraction Cache | Worth keeping visible, but it is less immediately executable than the current product-facing pending lane. |
| **112** Continuity Tracking: First Principles Redesign | Valuable redesign candidate, but it still needs tighter scope before it should leave Draft. |
| **138** Cost Profiles, Model Comparison, and Stage Budget Controls | Deliberate follow-up from Story 032. It owns configurable cost profiles, predictive model-cost comparison, and optional per-stage budget caps, but still needs tighter design before it should move to Pending. |

### Deferred — Intentionally Parked

No stories currently deferred.

## Health Flags

### Blocked — Dependency Chain Not Ready Yet

No blocked lines currently need attention.

## UI Product Truth Scouting

> CineForge now keeps a dedicated internal UI-scout lane in `docs/ui-scout.md` and `docs/ui-scout/`.
> This is separate from external-source scouting in `docs/scout/`.
>
> The job of this lane is simple: periodically walk the canonical full-pipeline fixture through the real surfaced UI, record whether it still feels story-centric, polished, and honest, and spawn focused follow-up stories when it does not.
>
> During triage, stale or awaiting-recheck coverage here is a real methodology signal, not an optional polish note.

## Notes From Cam

- 20260212: Seeddance 2.0 released and it's insane: https://x.com/altryne/status/2021967972055842893?s=20
  - "Takes a TEXT STORYBOARD image + character ref + scene ref + prop ref -> coherent 15-second film."

## Phase Summary

- **Phase 0 — Foundation** (001–002): Project scaffolding and pipeline infrastructure. Artifact store with immutability, snapshot versioning, dependency graph, audit metadata, cost tracking hooks, and structural validation.
- **Phase 1 — MVP Pipeline** (003–007): First working pipeline: script in -> canonical script + scenes + project config out. End-to-end smoke test.
- **Phase 2 — World Building** (008–011): Folder-based bibles (characters, locations, props), entity relationship graph, continuity state tracking.
- **Phase 2.5 — UI** (011b–011c): Production-quality Operator Console and resource-oriented routing. Research-driven design, then build. Foundation for later UI surfaces.
- **Phase 3 — Timeline** (012–013): Timeline data artifact with scene/story ordering, stacked tracks, and always-playable rule.
- **Phase 4 — Role System** (014–019): Role hierarchy, Director + Canon Guardians, style pack loading, suggestion/decision lifecycle, inter-role communication, and human interaction modes.
- **Phase 5 — Creative Direction** (020–023, 093–097, 099–100): Intent-first director's vision model, concern groups, and scene workspace.
- **Phase 6 — Shot Planning & Visualization** (025–027, 137, 143, 144): Coverage strategy, storyboards, animatics, keyframes, and AI-previz.
- **Phase 7 — Generation** (028–030, 140): Render adapter, user asset injection, generated-output QA, and media validation.
- **Phase 8 — Cross-Cutting Polish** (031–034): Semantic impact assessment, cost dashboards and budget caps, memory model, and in-app style pack creator.

## Spec Coverage Map

| Spec Section | Phase |
|---|---|
| spec:1 Foundation & Artifact Runtime | 0 / Cross-Cutting |
| spec:2 Story Intake & Understanding | 1 |
| spec:3 World Building & Continuity | 2 |
| spec:4 Role System & Creative Direction | 4 / 5 |
| spec:5 Operator Console & Interactive UX | 2.5 |
| spec:6 Shot Planning & Visualization | 6 |
| spec:7 Generation & Export | 7 |
| spec:8 AI Platform, Evaluation & Model Strategy | Cross-Cutting |
| spec:9 Memory & Collaboration | Cross-Cutting |
| spec:10 Timeline & Playable Assembly | 3 |
| spec:11 Planning Infrastructure & Agent Tooling | Cross-Cutting |

## Active Focus

- Active categories: `spec:6`, `spec:7`
- UI scout freshness: attention needed — last run 2026-04-12 is 18 days old against a 14-day cadence
- Sequencing bias: `scene-generation-completion` — Keep `spec:6` / `spec:7` as the active product lane even after Story 164 closed the first surfaced real-scene render route. The next slice should deepen scene-generation completeness from that honest operator path instead of retreating to throughput-only or eval-polish work.
- Sequencing bias: `pipeline-throughput-efficiency` — Keep screenplay-throughput and per-stage efficiency measurement visible, but do not let it displace scene-generation completeness while the operator-facing render path is still not feature complete. Use measured hotspot truth when throughput work resumes.
- Sequencing bias: `ui-product-truth-scouting` — If CineForge has not been walked through recently on the canonical full-pipeline fixture, triage should treat stale or awaiting-recheck UI product-truth coverage as real execution risk rather than assuming the surfaced path still feels coherent.
- Active campaign `ui-product-truth-scouting`: Recurring UI-scout reports should keep the canonical full-pipeline fixture freshly inspected so triage can notice stale or awaiting-recheck product-truth coverage.

## Story Index

Grouped by primary `spec:N` category. Stories keep all category refs visible in the table.

### spec:1 — Foundation & Artifact Runtime

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 071 | Refine vs. Regenerate Pipeline Modes | Medium | Deferred | — | spec:1 | — | [story-071](stories/story-071-refine-vs-regenerate-pipeline.md) |
| 073 | Add `after:` ordering-only stage dependency to recipe DSL | Medium | Done | — | spec:1 | — | [story-073](stories/story-073-add-after-ordering-dependency.md) |
| 074 | Artifact graph staleness: regression tests + sibling cross-contamination fix | Medium | Done | — | spec:1 | — | [story-074](stories/story-074-artifact-graph-staleness-regression-tests.md) |
| 116 | Event System Refactor | Medium | Done | — | spec:1 | 115 | [story-116](stories/story-116-event-system-refactor.md) |
| 117 | Engine Decomposition | Medium | Done | — | spec:1 | 116 | [story-117](stories/story-117-engine-decomposition.md) |
| 118 | Service Layer Decomposition | Medium | Done | — | spec:1 | 116 | [story-118](stories/story-118-service-decomposition.md) |
| 127 | Artifact Health Semantics + Chat Model Disclosure | Medium | Done | — | spec:1 | 083, 088, 126 | [story-127](stories/story-127-artifact-health-semantics-chat-model-disclosure.md) |
| 128 | Provider Failure Chat Notifications | Medium | Done | — | spec:1 | 050, 083 | [story-128](stories/story-128-provider-failure-chat-notifications.md) |

### spec:2 — Story Intake & Understanding

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 185 | Project Home Script Hierarchy and Supporting Surface Placement | High | Draft | — | spec:2, spec:5, spec:10 | 093, 142, 166, 167 | [story-185](stories/story-185-project-home-script-hierarchy-and-supporting-surface-placement.md) |
| 048 | PDF Input Preview Uses Binary Decode Instead of Text Extraction | High | Done | — | spec:2, spec:5 | — | [story-048](stories/story-048-pdf-input-preview-decode.md) |
| 049 | Import Normalization Format Suite | High | Done | — | spec:2, spec:8 | — | [story-049](stories/story-049-import-normalization-format-suite.md) |
| 054 | Liberty Church Character Artifact Cleanup Inventory | High | Done | — | spec:2, spec:3, spec:5, spec:8 | 008, 041 | [story-054](stories/story-054-liberty-church-character-artifact-cleanup-inventory.md) |
| 061 | Optimize Scene Extraction | High | Done | — | spec:2 | — | [story-061](stories/story-061-optimize-scene-extraction.md) |
| 062 | 3-Stage Ingestion: Intake, Breakdown, Analysis | High | Done | — | spec:2 | 061 | [story-062](stories/story-062-refactor-ingestion-three-stage.md) |
| 063 | Automatic Project Title Extraction from Script | High | Done | — | spec:2 | — | [story-063](stories/story-063-automatic-project-title-extraction.md) |
| 080 | LLM-Powered Action Line Entity Extraction | High | Done | — | spec:2, spec:3 | — | [story-080](stories/story-080-llm-action-line-entity-extraction.md) |
| 081 | Scene Index as Canonical Character Source | High | Done | — | spec:2, spec:3 | — | [story-081](stories/story-081-scene-index-canonical-characters.md) |
| 132 | Shot Planning UI and Shot List Exports | High | Done | — | spec:2, spec:5, spec:6 | 025, 058, 099, 101 | [story-132](stories/story-132-shot-planning-ui-and-shot-list-exports.md) |
| 133 | Model Refresh, Eval Verification, and Project Model Defaults | High | Done | — | spec:2, spec:8 | 107, 124 | [story-133](stories/story-133-model-refresh-eval-verification-and-project-defaults.md) |
| 135 | Brick & Steel PDF Normalization Regression | High | Done | — | spec:2, spec:8 | 004, 064 | [story-135](stories/story-135-screenplay-normalization-brick-steel-pdf-regression.md) |
| 142 | Initial Intake Should Not Self-Stale | High | Done | — | spec:1, spec:2, spec:5 | 031, 062, 127 | [story-142](stories/story-142-intake-onboarding-should-not-self-stale.md) |
| 148 | Scene-Scoped Planning and Honest Downstream Generation | High | Done | — | spec:2, spec:5, spec:6, spec:7, spec:10 | 025, 028, 099, 132, 143, 144 | [story-148](stories/story-148-scene-scoped-planning-and-honest-downstream-generation.md) |
| 189 | GPT-5.5 Frontier Eval Refresh | High | Done | — | spec:2, spec:3, spec:8 | 035 | [story-189](stories/story-189-gpt-55-frontier-eval-refresh.md) |
| 064 | Screenplay Format Round-Trip: Converter Upgrade + Fidelity Test Suite | Medium | Done | — | spec:2 | — | [story-064](stories/story-064-screenplay-format-round-trip.md) |
| 070 | Script View Scene Dividers & Entity Hotlinks | Medium | Done | — | spec:2, spec:3, spec:5 | 045 | [story-070](stories/story-070-script-view-scene-dividers-and-hotlinks.md) |
| 072 | Live Entity Discovery Feedback | Medium | Done | — | spec:2, spec:5 | 062 | [story-072](stories/story-072-live-entity-discovery-feedback.md) |
| 119 | Design Study Prompt Compiler + Visual Reference Propagation | Medium | Done | — | spec:2, spec:6 | 056, 120 | [story-119](stories/story-119-design-study-prompt-compiler.md) |
| 120 | Production Format Setting | Medium | Done | — | spec:2, spec:6 | 056 | [story-120](stories/story-120-production-format-setting.md) |
| 121 | Design Study Composition UX | Medium | Done | — | spec:2, spec:4, spec:6 | 056, 119, 120 | [story-121](stories/story-121-design-study-composition-ux.md) |
| 155 | End-to-End Throughput Detector and Stage Efficiency Budgets | Medium | Done | — | spec:2, spec:8 | 032, 150 | [story-155](stories/story-155-end-to-end-throughput-detector-and-stage-efficiency-budgets.md) |
| 161 | Long-Form Scene Analysis Throughput Reduction | Medium | Done | — | spec:2, spec:8 | 040, 155 | [story-161](stories/story-161-long-form-scene-analysis-throughput-reduction.md) |
| 163 | Scene Analysis Ownership Decomposition | Medium | Done | — | spec:2 | 161 | [story-163](stories/story-163-scene-analysis-ownership-decomposition.md) |
| 183 | Representative Deep Breakdown Runtime Truth Refresh | Medium | Done | — | spec:2, spec:3, spec:8 | 155, 159, 160, 161, 162 | [story-183](stories/story-183-representative-deep-breakdown-runtime-truth-refresh.md) |
| 187 | Long-Form Scene Analysis Runtime Regression | Medium | Done | — | spec:2, spec:8 | 155, 161, 183 | [story-187](stories/story-187-long-form-scene-analysis-runtime-regression.md) |
| 003 | Story Ingestion Module | Unknown | Done | — | spec:2 | 002 | [story-003](stories/story-003-story-ingestion.md) |
| 003b | DOCX Ingestion Support | Unknown | Done | — | spec:2 | 003, 007b | [story-003b](stories/story-003b-docx-support.md) |
| 004 | Script Normalization Module | Unknown | Done | — | spec:1, spec:2, spec:5, spec:8 | 002, 003 | [story-004](stories/story-004-script-normalization.md) |
| 005 | Scene Extraction Module | Unknown | Done | — | spec:2, spec:5, spec:8 | 002, 004 | [story-005](stories/story-005-scene-extraction.md) |
| 006 | Project Configuration (Auto-Initialized) | Unknown | Done | — | spec:2, spec:5, spec:8 | 002, 004, 005 | [story-006](stories/story-006-project-configuration.md) |
| 007b | Operator Console Lite (GUI for Project Start, Open, Run, and Artifact Review) | Unknown | Done | — | spec:1, spec:2, spec:5, spec:9 | 002, 003, 004, 005, 006, 007 | [story-007b](stories/story-007b-operator-console-lite.md) |
| 007c | MVP Reality Validation and Remediation (Post-UI Real-Run Findings) | Unknown | Done | — | spec:1, spec:2, spec:5, spec:8 | 003, 004, 005, 006, 007, 007b | [story-007c](stories/story-007c-mvp-reality-remediation.md) |
| 011b | Operator Console — Research & Design Decisions | Unknown | Done | — | spec:1, spec:2, spec:3, spec:5, spec:9 | 011 | [story-011b](stories/story-011b-operator-console.md) |
| 011d | Operator Console — Design & Build | Unknown | Done | — | spec:1, spec:2, spec:3, spec:5, spec:9 | 011, 011b | [story-011d](stories/story-011d-operator-console-build.md) |
| 093 | Script Bible Artifact | Unknown | Done | — | spec:2 | 003, 004 | [story-093](stories/story-093-script-bible.md) |

### spec:3 — World Building & Continuity

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 112 | Continuity Tracking: First Principles Redesign | Medium | Draft | — | spec:3 | — | [story-112](stories/story-112-continuity-redesign-first-principles.md) |
| 043 | Entity-First Navigation | High | Done | — | spec:3, spec:5 | — | [story-043](stories/story-043-entity-first-navigation.md) |
| 045 | Entity Cross-Linking | High | Done | — | spec:3, spec:5 | — | [story-045](stories/story-045-entity-cross-linking.md) |
| 055 | LLM-First Entity Adjudication for Character, Location, and Prop | High | Done | — | spec:1, spec:3, spec:5, spec:8 | 008, 009, 041, 054 | [story-055](stories/story-055-llm-first-entity-adjudication-for-character-location-prop.md) |
| 056 | Entity Design Studies (Reference Image Generation Loop) | High | Done | — | spec:1, spec:3, spec:4, spec:6, spec:7 | 008, 009, 011f, 029 | [story-056](stories/story-056-entity-design-study-reference-images.md) |
| 057 | Entity Prev/Next Navigation | High | Done | — | spec:3, spec:5 | — | [story-057](stories/story-057-entity-prev-next-navigation.md) |
| 060 | Entity Quality Regression | High | Done | — | spec:3, spec:8 | — | [story-060](stories/story-060-entity-quality-regression.md) |
| 065 | Parallel Bible Extraction: Performance Optimization for Entity-Heavy Scripts | High | Done | — | spec:3, spec:8 | — | [story-065](stories/story-065-parallel-bible-extraction.md) |
| 108 | Continuity UI Page | High | Done | — | spec:3 | — | [story-108](stories/story-108-continuity-ui-page.md) |
| 041 | Artifact Quality Improvements | Medium | Done | — | spec:3, spec:8 | — | [story-041](stories/story-041-artifact-quality-improvements.md) |
| 077 | Character Coverage & Prominence Tiers | Medium | Done | — | spec:3 | — | [story-077](stories/story-077-character-coverage-and-prominence-tiers.md) |
| 092 | Continuity AI Detection & Gap Analysis | Medium | Done | — | spec:3 | — | [story-092](stories/story-092-continuity-ai-detection.md) |
| 124 | Recall Verification Loop for Entity Discovery | Medium | Done | — | spec:3, spec:8 | — | [story-124](stories/story-124-recall-verification-loop.md) |
| 129 | Entity Discovery Taxonomy Tightening | Medium | Done | — | spec:3 | 081, 124 | [story-129](stories/story-129-entity-discovery-taxonomy-tightening.md) |
| 159 | Continuity Tracking Throughput and Output Budget Reduction | Medium | Done | — | spec:3, spec:8 | 011, 032, 155 | [story-159](stories/story-159-continuity-tracking-throughput-and-output-budget-reduction.md) |
| 160 | Long-Form Character and Location Bible Output Budget Recovery | Medium | Done | — | spec:3, spec:8 | 008, 009, 129, 155 | [story-160](stories/story-160-long-form-character-and-location-bible-output-budget-recovery.md) |
| 162 | Long-Form Continuity Tracking Stall Recovery | Medium | Done | — | spec:3, spec:8 | 011, 155, 159, 160 | [story-162](stories/story-162-long-form-continuity-tracking-stall-recovery.md) |
| 008 | Bible Infrastructure and Character Bible | Unknown | Done | — | spec:1, spec:3, spec:5, spec:8 | 002, 005 | [story-008](stories/story-008-character-bible.md) |
| 009 | Location and Prop Bibles | Unknown | Done | — | spec:3, spec:5 | 005, 008 | [story-009](stories/story-009-location-prop-bibles.md) |
| 010 | Entity Relationship Graph | Unknown | Done | — | spec:1, spec:3, spec:5 | 005, 008, 009 | [story-010](stories/story-010-entity-graph.md) |
| 011 | Asset State Tracking (Continuity) | Unknown | Done | — | spec:1, spec:3 | 005, 008, 009, 010 | [story-011](stories/story-011-continuity-tracking.md) |
| 016 | Style Pack Infrastructure | Unknown | Done | — | spec:3, spec:4 | 014 | [story-016](stories/story-016-style-pack-infrastructure.md) |
| 029 | User Asset Injection | Unknown | Done | — | spec:1, spec:3, spec:7 | 008, 009, 014, 017 | [story-029](stories/story-029-user-asset-injection.md) |

### spec:4 — Role System & Creative Direction

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 023 | Character & Performance — First Shipped Slice | High | Done | — | spec:4, spec:5 | 005, 008, 010, 011, 084, 094, 097 | [story-023](stories/story-023-actor-agents.md) |
| 082 | Creative Direction UX | High | Done | — | spec:4, spec:5 | — | [story-082](stories/story-082-creative-direction-ux.md) |
| 083 | Group Chat Architecture | High | Done | — | spec:4, spec:5, spec:9 | — | [story-083](stories/story-083-group-chat-architecture.md) |
| 084 | Character Chat Agents & Story Agent Rename | High | Done | — | spec:4, spec:5 | — | [story-084](stories/story-084-character-chat-agents.md) |
| 099 | Scene Workspace — Readiness Honesty | High | Done | — | spec:4, spec:5 | 023, 085, 094, 095, 097, 144 | [story-099](stories/story-099-scene-workspace.md) |
| 100 | Story World Motif Tracking | High | Done | — | spec:4 | 008, 009, 011, 094 | [story-100](stories/story-100-motif-tracking.md) |
| 126 | Frontend Chat and Data-Layer Decomposition | High | Done | — | spec:4, spec:5, spec:9 | — | [story-126](stories/story-126-frontend-chat-data-layer-decomposition.md) |
| 141 | Intent Taste Stack and Transparent Creative Brief | High | Done | — | spec:4, spec:7 | 029, 095, 119, 120 | [story-141](stories/story-141-intent-taste-stack-and-transparent-creative-brief.md) |
| 175 | AI Previz Scene-Ready Prerequisite Collapse | High | Done | — | spec:4, spec:5, spec:6, spec:7, spec:8, spec:10 | 151, 171, 174 | [story-175](stories/story-175-ai-previz-scene-ready-prerequisite-collapse.md) |
| 178 | AI Previz First-Pass xAI Prerequisite Collapse | High | Done | — | spec:4, spec:5, spec:6, spec:7, spec:8, spec:10 | 152, 175, 176 | [story-178](stories/story-178-ai-previz-first-pass-runtime-collapse.md) |
| 096 | \"Chat About This\" Interaction Pattern | Medium | Done | — | spec:4 | 011f, 082, 099, 126 | [story-096](stories/story-096-chat-about-this.md) |
| 131 | Preference Learning from User Choices | Medium | Done | — | spec:1, spec:4, spec:9 | 017 | [story-131](stories/story-131-preference-learning-from-user-choices.md) |
| 014 | Role System Foundation | Unknown | Done | — | spec:1, spec:4, spec:5 | 002, 006 | [story-014](stories/story-014-role-system-foundation.md) |
| 015 | Director and Canon Guardians | Unknown | Done | — | spec:4, spec:5 | 011, 014 | [story-015](stories/story-015-director-canon-guardians.md) |
| 017 | Suggestion and Decision Tracking | Unknown | Done | — | spec:1, spec:4, spec:5 | 014, 015 | [story-017](stories/story-017-suggestion-decision-tracking.md) |
| 018 | Inter-Role Communication Protocol | Unknown | Done | — | spec:1, spec:4, spec:9 | 014, 015, 017 | [story-018](stories/story-018-inter-role-communication.md) |
| 020 | Editorial Architect and Editorial Direction | Unknown | Done | — | spec:4 | 005, 014, 015 | [story-020](stories/story-020-editorial-architect.md) |
| 021 | Look & Feel — Visual Direction | Unknown | Done | — | spec:4 | 008, 009, 011, 014, 015 | [story-021](stories/story-021-visual-architect.md) |
| 022 | Sound & Music — Sound Direction | Unknown | Done | — | spec:4 | 005, 014, 015 | [story-022](stories/story-022-sound-designer.md) |
| 033 | Memory Model and Transcript Retention | Unknown | Done | — | spec:4, spec:9 | 014, 018 | [story-033](stories/story-033-memory-model.md) |
| 034 | In-App Style Pack Creator | Unknown | Done | — | spec:4 | 011b, 016 | [story-034](stories/story-034-style-pack-creator.md) |
| 094 | Concern Group Artifact Schemas | Unknown | Done | — | spec:4 | 002 | [story-094](stories/story-094-concern-group-schemas.md) |
| 095 | Intent / Mood Layer | Unknown | Done | — | spec:4 | 014, 094 | [story-095](stories/story-095-intent-mood-layer.md) |
| 097 | AI Artifact Editing | Unknown | Done | — | spec:1, spec:4, spec:5 | 014, 019, 031, 083 | [story-097](stories/story-097-ai-artifact-editing.md) |
| 090 | Persona-Adaptive Workspaces | Low | Cancelled | — | spec:4, spec:5 | 085, 089 | [story-090](stories/story-090-persona-adaptive-workspaces.md) |
| 024 | Direction Convergence and Review | Unknown | Cancelled | — | spec:4 | 015, 020, 021, 022, 023 | [story-024](stories/story-024-direction-convergence.md) |

### spec:5 — Operator Console & Interactive UX

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 114 | Driver Progress Events | Medium | Deferred | — | spec:1, spec:5 | 115, 116 | [story-114](stories/story-114-driver-progress-events.md) |
| 011e | Operator Console — UX Golden Path | Unknown | Deferred | — | spec:5 | 011d | [story-011e](stories/story-011e-ux-golden-path.md) |
| 051 | Chat UX Polish: Ordering, Naming, Progress Card, and Live Counts | High | Done | — | spec:5 | — | [story-051](stories/story-051-chat-ux-polish.md) |
| 058 | Comprehensive Export & Share | High | Done | — | spec:5, spec:7 | — | [story-058](stories/story-058-comprehensive-export-share.md) |
| 059 | Pipeline UI Refinement | High | Done | — | spec:5 | — | [story-059](stories/story-059-pipeline-ui-refinement.md) |
| 066 | UI Component Deduplication & Template Consolidation | High | Done | — | spec:5, spec:11 | — | [story-066](stories/story-066-ui-component-deduplication.md) |
| 067 | chat-duplicate-nav-dedup | High | Done | — | spec:5, spec:9 | — | [story-067](stories/story-067-chat-duplicate-nav-dedup.md) |
| 068 | History-Aware Back Button Navigation | High | Done | — | spec:5 | — | [story-068](stories/story-068-back-button-history-navigation.md) |
| 069 | Inbox Item Read/Complete State | High | Done | — | spec:5, spec:9 | — | [story-069](stories/story-069-inbox-read-state.md) |
| 075 | Entity Detail Page Polish | High | Done | — | spec:5 | — | [story-075](stories/story-075-entity-detail-page-polish.md) |
| 076 | Entity Detail: Cross-Reference Layout & Narrative Role Polish | High | Done | — | spec:5 | — | [story-076](stories/story-076-entity-detail-cross-ref-layout.md) |
| 085 | Pipeline Capability Graph & Navigation Bar | High | Done | — | spec:5 | 002, 011e, 011f, 082 | [story-085](stories/story-085-pipeline-capability-graph.md) |
| 086 | AI Navigation Intelligence | High | Done | — | spec:5, spec:9 | 085 | [story-086](stories/story-086-ai-navigation-intelligence.md) |
| 139 | Long-Running Operation Black-Screen Recovery | High | Done | — | spec:1, spec:5 | 127 | [story-139](stories/story-139-historical-run-progress-cards-stop-polling-missing-runs.md) |
| 144 | AI Previz Adoption Gate and Trust Guardrails | High | Done | — | spec:5, spec:6, spec:7, spec:8, spec:10 | 032, 140, 143 | [story-144](stories/story-144-ai-previz-adoption-gate-and-trust-guardrails.md) |
| 149 | Fast AI Previz and Latency Budget | High | Done | — | spec:5, spec:6, spec:7, spec:10 | 028, 143, 144, 148 | [story-149](stories/story-149-previz-fast-lane-and-latency-budget.md) |
| 150 | Fastest Real AI Previz Runtime Eval | High | Done | — | spec:5, spec:6, spec:7, spec:10 | 143, 144, 148, 149 | [story-150](stories/story-150-fastest-real-ai-previz-runtime-eval.md) |
| 151 | Previz Shot Planning Compact Mode | High | Done | — | spec:5, spec:6, spec:7, spec:10 | 149, 150 | [story-151](stories/story-151-previz-shot-planning-compact-mode.md) |
| 152 | Previz AI Regenerate Reuse Path | High | Done | — | spec:5, spec:6, spec:7, spec:8, spec:10 | 149, 151, 171, 175, 176 | [story-152](stories/story-152-previz-ai-regenerate-reuse-path.md) |
| 153 | Previz Minimal AI Clip Mode and Provider Floor | High | Done | — | spec:5, spec:6, spec:7, spec:10 | 143, 149, 150, 151, 152 | [story-153](stories/story-153-previz-minimal-ai-clip-provider-floor.md) |
| 164 | Real Scene Generation Product Truth | High | Done | — | spec:5, spec:6, spec:7, spec:10 | 028, 140, 148 | [story-164](stories/story-164-real-scene-generation-product-truth.md) |
| 165 | Scene Render Refresh Reuse Path | High | Done | — | spec:5, spec:6, spec:7, spec:10 | 164 | [story-165](stories/story-165-scene-render-refresh-reuse-path.md) |
| 166 | Final Output Playable Assembly | High | Done | — | spec:5, spec:7, spec:10 | 013, 027, 028, 130, 148, 164, 165 | [story-166](stories/story-166-final-output-playable-assembly.md) |
| 167 | Final Output Validation and Trust Surface | High | Done | — | spec:5, spec:7, spec:8, spec:10 | 140, 166 | [story-167](stories/story-167-final-output-validation-and-trust-surface.md) |
| 168 | Reference-Conditioned Scene Generation Product Truth | High | Done | — | spec:5, spec:6, spec:7 | 029, 056, 119, 141, 164 | [story-168](stories/story-168-reference-conditioned-scene-generation-product-truth.md) |
| 169 | Reference-Conditioned Final Render Provider Floor | High | Done | — | spec:5, spec:6, spec:7, spec:8 | 028, 030, 164, 168 | [story-169](stories/story-169-reference-conditioned-final-render-provider-floor.md) |
| 170 | Breadth-First Scene Generation Product Truth | High | Done | — | spec:5, spec:6, spec:7, spec:10 | 148, 164, 165, 166, 167, 168, 169 | [story-170](stories/story-170-breadth-first-scene-generation-product-truth.md) |
| 171 | AI Previz First-Playable Latency Reduction | High | Done | — | spec:5, spec:6, spec:7, spec:8, spec:10 | 149, 150, 151, 152, 153 | [story-171](stories/story-171-ai-previz-first-playable-latency-reduction.md) |
| 174 | Fast Useful AI Previz on Honest Current-Scene Route | High | Done | — | spec:5, spec:6, spec:7, spec:8, spec:10 | 143, 153, 171 | [story-174](stories/story-174-fast-useful-ai-previz-current-scene-route.md) |
| 176 | AI Previz Provider Floor on Honest One-Pass Route | High | Done | — | spec:5, spec:6, spec:7, spec:8, spec:10 | 151, 153, 174, 175 | [story-176](stories/story-176-ai-previz-one-pass-provider-floor.md) |
| 180 | Scene Workspace Entry Clarity and Tab Target Precision | High | Done | — | spec:5, spec:6, spec:7 | 099, 170 | [story-180](stories/story-180-scene-workspace-entry-clarity.md) |
| 181 | Post-Deep-Breakdown Next-Step Guidance | High | Done | — | spec:5, spec:6, spec:7 | 156, 157 | [story-181](stories/story-181-post-deep-breakdown-next-step-guidance.md) |
| 182 | Post-Analysis Chat Resource Failure Recovery | High | Done | — | spec:1, spec:5, spec:9 | — | [story-182](stories/story-182-post-analysis-chat-resource-failure-recovery.md) |
| 184 | Live AI Capability Smoke for Default Text Image and Video Lanes | High | Done | — | spec:5, spec:7, spec:8 | 179 | [story-184](stories/story-184-live-ai-capability-smoke.md) |
| 186 | Storyboard Generation Quality Eval for Reference Fidelity and Identity Consistency | High | Done | — | spec:5, spec:6, spec:7, spec:8 | 169 | [story-186](stories/story-186-storyboard-generation-quality-eval.md) |
| 191 | Brick & Steel Final-Render Prompt Truth | High | Done | — | spec:5, spec:6, spec:7, spec:8 | 168, 169, 190 | [story-191](stories/story-191-brick-steel-scene-media-product-truth.md) |
| 192 | Brick & Steel GPT-Image Completion and Error Truth | High | Done | — | spec:5, spec:7, spec:8 | 191 | [story-192](stories/story-192-brick-steel-gpt-image-completion-and-error-truth.md) |
| 011c | Resource-oriented Routing | Medium | Done | — | spec:5 | — | [story-011c](stories/story-011c-resource-oriented-routing.md) |
| 042 | Wire Mock UI to Real APIs | Medium | Done | — | spec:5 | — | [story-042](stories/story-042-wire-mock-ui-to-apis.md) |
| 044 | Mobile-Friendly UI | Medium | Done | — | spec:5 | 043 | [story-044](stories/story-044-mobile-friendly-ui.md) |
| 046 | Theme System (Light/Dark/Auto + Palettes) | Medium | Done | — | spec:5 | — | [story-046](stories/story-046-theme-system.md) |
| 052 | Streaming Artifact Yield: Live Per-Entity Progress | Medium | Done | — | spec:1, spec:5 | — | [story-052](stories/story-052-streaming-artifact-yield.md) |
| 078 | Entity Detail: Scroll-to-Top, Cross-Ref Ordering & Props Metadata | Medium | Done | — | spec:5 | — | [story-078](stories/story-078-entity-detail-enhancements.md) |
| 079 | Chat & Nav Bugs + Polish Bundle | Medium | Done | — | spec:5 | — | [story-079](stories/story-079-chat-nav-bugs-and-polish.md) |
| 087 | Pre-flight Summary Cards | Medium | Done | — | spec:5 | 086 | [story-087](stories/story-087-preflight-summary-cards.md) |
| 088 | Staleness UX | Medium | Done | — | spec:1, spec:5 | 074, 086 | [story-088](stories/story-088-staleness-ux.md) |
| 110 | Improve Search: Fuzzy Matching + Scene Shorthand | Medium | Done | — | spec:5 | — | [story-110](stories/story-110-search-scenes-fuzzy.md) |
| 111 | Fix \"View In Script\" Scroll-to-Scene | Medium | Done | — | spec:5 | — | [story-111](stories/story-111-scene-script-jump.md) |
| 156 | Full-Pipeline UI Acceptance Walkthrough | Medium | Done | — | spec:5, spec:11 | — | [story-156](stories/story-156-full-pipeline-ui-acceptance-walkthrough.md) |
| 157 | Chat Suggestions Stop Advertising Completed Paths | Medium | Done | — | spec:5 | — | [story-157](stories/story-157-chat-suggestions-stop-advertising-completed-paths.md) |
| 158 | Fresh Run Event Polling Stops Racing Missing Event Logs | Medium | Done | — | spec:5 | — | [story-158](stories/story-158-fresh-run-event-polling-stops-racing-missing-event-logs.md) |
| 179 | Provider Dependency Health and Credential Readiness Surface | Medium | Done | — | spec:5, spec:8 | 037, 038 | [story-179](stories/story-179-provider-dependency-health-and-credential-readiness.md) |
| 089 | Interaction Mode Selection | Low | Done | — | spec:5 | 085 | [story-089](stories/story-089-interaction-mode-selection.md) |
| 001 | Project Setup and Scaffolding | Unknown | Done | — | spec:1, spec:5, spec:8 | — | [story-001](stories/story-001-project-setup.md) |
| 002 | Pipeline Foundation (Driver, Artifact Store, Schemas) | Unknown | Done | — | spec:1, spec:5, spec:8 | 001 | [story-002](stories/story-002-pipeline-foundation.md) |
| 007 | MVP Recipe and End-to-End Smoke Test | Unknown | Done | — | spec:1, spec:5, spec:8 | 002, 003, 004, 005, 006 | [story-007](stories/story-007-mvp-recipe-smoke-test.md) |
| 011f | Operator Console — Conversational AI Chat | Unknown | Done | — | spec:5, spec:9 | 011e | [story-011f](stories/story-011f-conversational-ai-chat.md) |
| 012 | Timeline Data Artifact | Unknown | Done | — | spec:1, spec:5, spec:10 | 005, 011, 011c, 050 | [story-012](stories/story-012-timeline-artifact.md) |
| 019 | Human Control Modes and Creative Sessions | Unknown | Done | — | spec:5, spec:9 | 011b, 014, 015, 017, 018 | [story-019](stories/story-019-human-interaction.md) |
| 101 | Centralized Long-Running Action System | Unknown | Done | — | spec:1, spec:5 | — | [story-101](stories/story-101-long-running-action-system.md) |

### spec:6 — Shot Planning & Visualization

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 143 | AI-Generated Low-Fidelity Previz | High | Done | — | spec:6, spec:7, spec:10 | 028, 029, 030, 056, 119, 137, 140 | [story-143](stories/story-143-ai-generated-low-fidelity-previz.md) |
| 177 | OpenTimelineIO Narrative Interchange Export | High | Done | — | spec:6, spec:7, spec:10 | 130 | [story-177](stories/story-177-otio-narrative-interchange-export.md) |
| 188 | Storyboard Grid Beat Router and Motion-Handoff Scout | High | Done | — | spec:6, spec:7, spec:8 | 186 | [story-188](stories/story-188-storyboard-grid-beat-router-and-motion-handoff-scout.md) |
| 190 | Storyboard Identity and Reference Stability | High | Done | — | spec:6, spec:7, spec:8 | 186, 188 | [story-190](stories/story-190-storyboard-identity-reference-stability.md) |
| 193 | Scene Render Clip Plan | High | Done | — | spec:6, spec:7, spec:10 | 191 | [story-193](stories/story-193-scene-render-clip-plan.md) |
| 194 | Multi-Clip Scene Rendering | High | Done | — | spec:6, spec:7, spec:10 | 193 | [story-194](stories/story-194-multi-clip-scene-rendering.md) |
| 130 | Export Fidelity: Narrative Metadata + Callsheets | Medium | Done | — | spec:6, spec:7, spec:10 | 012, 013, 058 | [story-130](stories/story-130-export-fidelity-narrative-metadata-callsheets.md) |
| 173 | Stale Coverage Graph Node Removal | Medium | Done | — | spec:6 | 025 | [story-173](stories/story-173-stale-coverage-graph-node-removal.md) |
| 137 | Previz Fidelity Upgrade | Low | Done | — | spec:6, spec:7, spec:10 | 027, 028, 030 | [story-137](stories/story-137-previz-fidelity-upgrade.md) |
| 025 | Shot Planning | Unknown | Done | — | spec:6 | 011, 012, 013, 020, 021, 022 | [story-025](stories/story-025-shot-planning.md) |
| 026 | Storyboard Generation (Optional) | Unknown | Done | — | spec:6, spec:10 | 013, 025 | [story-026](stories/story-026-storyboard-generation.md) |
| 027 | Animatics, Keyframes, and Previz (Optional) | Unknown | Done | — | spec:6, spec:10 | 013, 025, 026 | [story-027](stories/story-027-animatics-previz.md) |

### spec:7 — Generation & Export

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 140 | Agentic Media Validation Loop | High | Done | — | spec:7, spec:8, spec:10 | 027, 028, 030, 127 | [story-140](stories/story-140-agentic-media-validation-loop.md) |
| 028 | Render Adapter Module | Unknown | Done | — | spec:7, spec:10 | 013, 022, 025, 027, 029 | [story-028](stories/story-028-render-adapter.md) |
| 030 | Generated Output QA (Video Understanding Benchmark) | Unknown | Done | — | spec:7, spec:8, spec:9 | 005, 012, 021, 022, 028, 032 | [story-030](stories/story-030-generated-output-qa.md) |
| 098 | Real-World Asset Upload Pipeline | Unknown | Cancelled | — | spec:7 | 029 | [story-098](stories/story-098-real-asset-upload.md) |

### spec:8 — AI Platform, Evaluation & Model Strategy

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 104 | Tiered Quality Metrics for Eval Scoring | High | Draft | — | spec:8 | — | [story-104](stories/story-104-tiered-quality-metrics.md) |
| 105 | Parallel Chunk Extraction via ThreadPoolExecutor | High | Draft | — | spec:1, spec:8 | — | [story-105](stories/story-105-parallel-extraction.md) |
| 102 | Promptfoo Multi-Turn Conversational Evals | Medium | Draft | — | spec:8, spec:9 | — | [story-102](stories/story-102-promptfoo-multi-turn-evals.md) |
| 106 | Disk-Backed Chunk-Level Extraction Cache | Medium | Draft | — | spec:1, spec:8 | — | [story-106](stories/story-106-chunk-level-extraction-cache.md) |
| 138 | Cost Profiles, Model Comparison, and Stage Budget Controls | Medium | Draft | — | spec:8 | 032 | [story-138](stories/story-138-cost-profiles-model-comparison-stage-budgets.md) |
| 035 | AI Model Benchmarking System | High | Done | — | spec:8 | — | [story-035](stories/story-035-model-benchmarking.md) |
| 036 | Model Selection and Eval Framework | High | Done | — | spec:8 | — | [story-036](stories/story-036-model-selection.md) |
| 037 | Production Deployment to cineforge.copper-dog.com | High | Done | — | spec:1, spec:8 | — | [story-037](stories/story-037-production-deployment.md) |
| 038 | Multi-Provider LLM Transport | High | Done | — | spec:1, spec:8 | — | [story-038](stories/story-038-multi-provider-transport.md) |
| 040 | Pipeline Performance Optimization | High | Done | — | spec:1, spec:8 | — | [story-040](stories/story-040-pipeline-performance-optimization.md) |
| 047 | Benchmark Sonnet 4.6 Across All Evals | High | Done | — | spec:8 | — | [story-047](stories/story-047-sonnet-46-benchmarks.md) |
| 050 | Provider Resilience: Retries, Fallbacks, and Stage Resume | High | Done | — | spec:1, spec:8 | — | [story-050](stories/story-050-provider-resilience-retry-fallback.md) |
| 107 | Value-Optimized Model Selection Across All Modules | High | Done | — | spec:8 | — | [story-107](stories/story-107-value-optimized-model-selection.md) |
| 136 | ADR-021 Execution-Ideal and Phase-Governance Migration | High | Done | — | spec:8, spec:11 | 134 | [story-136](stories/story-136-adr-021-execution-planning-migration.md) |
| 039 | Apply Model Selections to Production | Medium | Done | — | spec:8 | — | [story-039](stories/story-039-apply-model-selections.md) |
| 122 | Golden Fixture Helpers | Medium | Done | — | spec:8 | — | [story-122](stories/story-122-golden-fixture-helpers.md) |
| 123 | Anthropic Prompt Caching | Medium | Done | — | spec:8 | — | [story-123](stories/story-123-anthropic-prompt-caching.md) |
| 031 | Change Propagation (Semantic Impact Layer) | Unknown | Done | — | spec:1, spec:8 | 002, 010, 014 | [story-031](stories/story-031-change-propagation.md) |
| 032 | Cost Tracking and Budget Management | Unknown | Done | — | spec:1, spec:8 | 002, 014 | [story-032](stories/story-032-cost-tracking.md) |
| 113 | Per-Provider LLM Circuit Breaker | Medium | Cancelled | — | spec:1, spec:8 | 050 | [story-113](stories/story-113-llm-circuit-breaker.md) |

### spec:10 — Timeline & Playable Assembly

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 013 | Track System and Always-Playable Rule | Unknown | Done | — | spec:10 | 011, 012, 050 | [story-013](stories/story-013-track-system.md) |

### spec:11 — Planning Infrastructure & Agent Tooling

| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |
|---|---|---|---|---|---|---|---|
| 103 | AGENTS.md Runbook Extraction (300-Line Cap) | Medium | Draft | — | spec:11 | — | [story-103](stories/story-103-agents-md-runbook-extraction.md) |
| 053 | Cross-CLI Skills/Prompts Unification | High | Done | — | spec:11 | — | [story-053](stories/story-053-cross-cli-skills-unification.md) |
| 125 | Agent Workflow Hardening Meta Upgrade | High | Done | — | spec:11 | — | [story-125](stories/story-125-agent-workflow-hardening-meta-upgrade.md) |
| 134 | Compromise Convergence Tooling Migration | High | Done | — | spec:11 | 053, 125 | [story-134](stories/story-134-compromise-convergence-tooling-migration.md) |
| 145 | Methodology Graph + State Migration | High | Done | — | spec:11 | 134, 136 | [story-145](stories/story-145-methodology-graph-state-migration.md) |
| 146 | Legacy Methodology Metadata Backfill | High | Done | — | spec:11 | 145 | [story-146](stories/story-146-legacy-methodology-metadata-backfill.md) |
| 147 | Problem-First Triage and Story Workflow Migration | High | Done | — | spec:11 | 145, 146 | [story-147](stories/story-147-problem-first-triage-and-story-workflow-migration.md) |
| 154 | Methodology Hardening Follow-up Sweep | High | Done | — | spec:11 | 145, 146, 147 | [story-154](stories/story-154-methodology-hardening-follow-up-sweep.md) |
| 172 | Methodology Actionability Truth and Audit Freshness | High | Done | — | spec:11 | 154 | [story-172](stories/story-172-methodology-actionability-truth-and-audit-freshness.md) |
| 109 | Golden Build Runbook | Medium | Done | — | spec:11 | — | [story-109](stories/story-109-golden-build-runbook.md) |
| 115 | Pipeline Architecture Refactor Plan | Medium | Done | — | spec:1, spec:11 | — | [story-115](stories/story-115-pipeline-architecture-refactor-plan.md) |
