# Build Map

> Generated from `docs/methodology/state.yaml` + `docs/methodology/graph.json`. Do not edit manually.
> Canonical planning state lives in `docs/methodology/state.yaml`; this file is a human-readable dashboard view.

## How to Read This Map

- **Product need**: what the category must deliver to the user or the execution experience.
- **Tech need**: what architectural or workflow substrate must exist.
- **Substrate** and **Phase** come from structured operational state.
- **Stories / ADR Refs / Evals** are compiled from canonical sources.

## spec:1 — Foundation & Artifact Runtime

**Product need:** Artifacts, decisions, and runtime operations stay immutable, auditable, and safe to revise.
**Tech need:** Snapshot versioning, dependency-aware invalidation, AI/runtime boundary discipline, and durable audit metadata.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 001, 002, 004, 007, 007b, 007c, 008, 010, 011, 011b, 011d, 012, 014, 017, 018, 029, 031, 032, 037, 038, 040, 050, 052, 055, 056, 071, 073, 074, 088, 097, 101, 105, 106, 113, 114, 115, 116, 117, 118, 127, 128, 131, 139, 142
**ADR Refs:** ADR-002, ADR-003
**Spec:** spec:1 (spec:1.1, spec:1.2, spec:1.3, spec:1.4, spec:1.5, spec:1.6)
**Absorbs:** Foundation & Artifact Runtime (old 1)

### Phase Notes

- Core substrate exists. Current work here is mostly maintenance, decomposition, and verification hardening rather than a missing-system climb.

## spec:2 — Story Intake & Understanding

**Product need:** CineForge can accept story inputs in multiple formats and turn them into a coherent, browsable understanding quickly enough to start creative work.
**Tech need:** Ingestion, normalization, canonical script handling, project configuration, script-bible extraction, and scene understanding.
**Substrate:** exists
**Phase:** climb

**Story coverage:** partial
**Stories:** 003, 003b, 004, 005, 006, 007b, 007c, 011b, 011d, 048, 049, 054, 061, 062, 063, 064, 070, 072, 080, 081, 093, 119, 120, 121, 132, 133, 135, 142, 148, 155, 161, 163
**ADR Refs:** ADR-003
**Spec:** spec:2 (spec:2.1, spec:2.2, spec:2.3, spec:2.4, spec:2.5, spec:2.6, spec:2.7, spec:2.7.1, spec:2.7.2)
**Absorbs:** Script Understanding Pipeline (old 2)

### Phase Notes

- The two-tier scene split remains justified while single-pass scene understanding is still below the required quality/latency bar.
- Long-form screenplay throughput is a standing climb requirement: measure the honest story-lane boundary and use detector-backed stage budgets instead of anecdotal 'the pipeline feels slow' tuning.

### Compromise Progress

- **C4: Two-Tier Scene Architecture** — **climb**
  - Current: Structural scene breakdown lands quickly, while slower narrative enrichment remains separate and user-triggered.
  - Converge signal: Single-pass scene understanding becomes both fast enough and good enough to replace the split.
  - Evidence: `compromise-C4-two-tier-scenes` still shows the best candidate below the quality/latency bar.

## spec:3 — World Building & Continuity

**Product need:** Characters, locations, props, and continuity states persist as first-class world knowledge.
**Tech need:** Bible folders, relationship edges, and state snapshots over story time.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 008, 009, 010, 011, 011b, 011d, 016, 029, 041, 043, 045, 054, 055, 056, 057, 060, 065, 070, 077, 080, 081, 092, 108, 112, 124, 129, 159, 160, 162
**ADR Refs:** ADR-001, ADR-002, ADR-003
**Spec:** spec:3 (spec:3.1, spec:3.2, spec:3.3, spec:3.4)
**Absorbs:** World Building & Continuity (old 3)

### Phase Notes

- Core substrate exists. Remaining work is mostly quality refinement, continuity detection depth, and better downstream reuse of the world model.

## spec:4 — Role System & Creative Direction

**Product need:** Creative roles and characters should feel like collaborators who understand the story deeply and shape it across disciplines.
**Tech need:** Role hierarchy, style packs, transcripts, suggestion artifacts, and concern-group direction artifacts.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 014, 015, 016, 017, 018, 020, 021, 022, 023, 024, 033, 034, 056, 082, 083, 084, 090, 094, 095, 096, 097, 099, 100, 121, 126, 131, 141
**ADR Refs:** ADR-002, ADR-003
**Spec:** spec:4 (spec:4.1, spec:4.2, spec:4.3, spec:4.4, spec:4.5, spec:4.6, spec:4.7, spec:4.7.1, spec:4.7.2, spec:4.8, spec:4.8.1, spec:4.8.2, spec:4.9, spec:4.9.1, spec:4.9.2, spec:4.10, spec:4.10.1, spec:4.10.2, spec:4.10.3, spec:4.10.4, spec:4.10.5, spec:4.10.6, spec:4.10.7)
**Absorbs:** Role System & Creative Direction (old 4)

### Phase Notes

- Capability gating remains an honest hold-state compromise until one broadly usable multimodal model removes the need for per-role modality declarations.

### Compromise Progress

- **C5: Capability Gating** — **hold**
  - Current: Roles declare modality limits and route around them instead of pretending to perceive media they cannot understand.
  - Converge signal: One broadly usable multimodal model makes per-role modality declarations unnecessary.
  - Evidence: `compromise-C5-role-modality` has no passing deletion signal.

## spec:5 — Operator Console & Interactive UX

**Product need:** The operator should feel like they are working with their story, not administering a pipeline.
**Tech need:** Control modes, explanation surfaces, stage-progression rules, interaction models, and readiness signals that keep the UI honest.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 001, 002, 004, 005, 006, 007, 007b, 007c, 008, 009, 010, 011b, 011c, 011d, 011e, 011f, 012, 014, 015, 017, 019, 023, 042, 043, 044, 045, 046, 048, 051, 052, 054, 055, 057, 058, 059, 066, 067, 068, 069, 070, 072, 075, 076, 078, 079, 082, 083, 084, 085, 086, 087, 088, 089, 090, 097, 099, 101, 110, 111, 114, 126, 132, 142, 144, 148, 149, 150, 151, 152, 153, 156, 157, 158, 164, 165, 166, 167, 168, 169, 170, 171
**ADR Refs:** ADR-002, ADR-003
**Spec:** spec:5 (spec:5.1, spec:5.2, spec:5.3, spec:5.4, spec:5.5, spec:5.6)
**Absorbs:** Operator Console & Interactive UX (old 5)

### Phase Notes

- The app shell and user flows exist. Current work is about clarity, polish, transparency, and closing remaining UX holes.
- A standing requirement now exists to keep a canonical short screenplay plus recurring full-pipeline manual walkthrough in the dedicated internal ui-scout lane so UI completeness and polish stay inspectable on the honest current product path.

## spec:6 — Shot Planning & Visualization

**Product need:** Creative intent becomes concrete planning artifacts usable by humans and generation models.
**Tech need:** Coverage strategy, shot definitions, storyboard and animatic assets, and optional keyframes linked to upstream direction.
**Substrate:** exists
**Phase:** climb

**Story coverage:** partial
**Stories:** 025, 026, 027, 056, 119, 120, 121, 130, 132, 137, 143, 144, 148, 149, 150, 151, 152, 153, 164, 165, 168, 169, 170, 171, 173
**ADR Refs:** ADR-002, ADR-003
**Spec:** spec:6 (spec:6.1, spec:6.1.1, spec:6.1.2, spec:6.1.3, spec:6.1.4, spec:6.2, spec:6.2.1, spec:6.2.2, spec:6.3, spec:6.3.1, spec:6.3.2, spec:6.3.3, spec:6.3.4, spec:6.3.5, spec:6.4)
**Absorbs:** Shot Planning & Visualization (old 6)

### Phase Notes

- Shot planning, storyboard generation, deterministic previz baseline, and the operator-facing AI-previz surface now exist as real substrate.
- This category stays in climb because deterministic previz is still only fallback/control while fast useful AI previz remains unfinished.

## spec:7 — Generation & Export

**Product need:** CineForge can compile direction into generation requests and carry user-provided assets through the same pipeline.
**Tech need:** Render-adapter compilation, engine-pack knowledge, error handling, and origin-agnostic asset injection.
**Substrate:** partial
**Phase:** climb

**Story coverage:** partial
**Stories:** 028, 029, 030, 056, 058, 098, 130, 137, 140, 141, 143, 144, 148, 149, 150, 151, 152, 153, 164, 165, 166, 167, 168, 169, 170, 171
**ADR Refs:** ADR-002, ADR-003
**Spec:** spec:7 (spec:7.1, spec:7.1.1, spec:7.1.2, spec:7.1.3, spec:7.2)
**Absorbs:** Generation & Export (old 7)

### Phase Notes

- Render-adapter compilation, engine-pack knowledge, error handling, origin-agnostic asset injection, runtime media validation, and AI-previz generation exist as real substrate.
- This category stays in climb because richer export fidelity and broader media-validation coverage remain unfinished.

### Compromise Progress

- **C6: Render Adapter Engine Packs** — **hold**
  - Current: Heterogeneous video APIs still justify a render-adapter abstraction with model-specific engine-pack knowledge.
  - Converge signal: A dominant standard API or one model cleanly handles all required generation inputs.
  - Evidence: No registry-backed deletion harness exists yet; this remains an ecosystem detector.

## spec:8 — AI Platform, Evaluation & Model Strategy

**Product need:** AI cost, quality, and model tradeoffs are visible enough that operators can trust the system.
**Tech need:** Cost tracking, QA patterns, current eval registry discipline, and model-slot strategy.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 001, 002, 004, 005, 006, 007, 007c, 008, 030, 031, 032, 035, 036, 037, 038, 039, 040, 041, 047, 049, 050, 054, 055, 060, 065, 102, 104, 105, 106, 107, 113, 122, 123, 124, 133, 135, 136, 138, 140, 144, 155, 159, 160, 161, 162, 167, 169, 171
**ADR Refs:** ADR-001, ADR-002, ADR-003
**Spec:** spec:8 (spec:8.1, spec:8.2, spec:8.3)
**Absorbs:** AI Platform, Model Selection & Validation (old 8)

### Phase Notes

- Current work here is primarily value maintenance, benchmark refresh, and compromise monitoring rather than missing substrate.
- Throughput and output-volume optimization should be driven by runtime detectors and measured stage budgets, not one-off model or prompt tweaks.

### Compromise Progress

- **C1: Cost Transparency** — **hold**
  - Current: Per-call and per-run cost tracking still matters because model pricing and tradeoffs are material.
  - Converge signal: Per-call cost tracking becomes unnecessary when inference is cheap enough to stop shaping operator behavior.
  - Evidence: No registry eval; detection remains pricing-watch based.
- **C2: Dedicated QA Validation Passes** — **hold**
  - Current: Dedicated QA / verification remains the safest path for structured output quality.
  - Converge signal: First-attempt output becomes reliable enough to demote QA to lightweight assertions only.
  - Evidence: `compromise-C2-qa-validation` does not justify deletion yet.
- **C3: Tiered Model Strategy** — **hold**
  - Current: Value-optimized model selection remains justified because no single model dominates CineForge's full task surface.
  - Converge signal: One model meets all current default-driving quality bars at acceptable latency and cost.
  - Evidence: `compromise-C3-tiered-models` still leaves the repo below the single-model bar.

## spec:9 — Memory & Collaboration

**Product need:** Long-running collaboration should preserve context, transcripts, and operating-mode intent without losing provenance.
**Tech need:** Canonical memory artifacts, working-memory summaries, and explicit operating-mode rules.
**Substrate:** partial
**Phase:** climb

**Story coverage:** partial
**Stories:** 007b, 011b, 011d, 011f, 018, 019, 030, 033, 067, 069, 083, 086, 102, 126, 131
**ADR Refs:** ADR-002, ADR-003
**Spec:** spec:9 (spec:9.1, spec:9.2, spec:9.3, spec:9.4)
**Absorbs:** Memory & Collaboration (old 9)

### Phase Notes

- The canonical vs working-memory split remains justified while context windows and memory persistence are still constrained.

### Compromise Progress

- **C7: Working Memory Distinction** — **hold**
  - Current: Canonical memory plus working-memory caches remain necessary while context windows are finite and expensive.
  - Converge signal: Persistent, effectively unbounded memory makes the split unnecessary.
  - Evidence: `compromise-C7-working-memory` has no deletion signal yet.

## spec:10 — Timeline & Playable Assembly

**Product need:** Users can inspect pacing, order, and best-available playback throughout the pipeline.
**Tech need:** Independent timeline artifacts, stacked tracks, and the always-playable fallback rule.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 012, 013, 026, 027, 028, 130, 137, 140, 143, 144, 148, 149, 150, 151, 152, 153, 164, 165, 166, 167, 170, 171
**ADR Refs:** ADR-003
**Spec:** spec:10 (spec:10.1, spec:10.2, spec:10.3)
**Absorbs:** None — new explicit category extracted from existing spec/stories

### Phase Notes

- Timeline substrate exists but still relies on continued trust/readiness work as generated-video and previz lanes evolve.

## spec:11 — Planning Infrastructure & Agent Tooling

**Product need:** CineForge still needs explicit planning scaffolding while current AI cannot yet build and verify large repo changes from the ideal in one shot.
**Tech need:** Story lifecycle tracking, methodology state, compiled graph joins, generated planning views, triage skills, workflow gates, AGENTS instructions, runbooks, and verbose work logs.
**Substrate:** exists
**Phase:** climb

**Story coverage:** partial
**Stories:** 053, 066, 103, 109, 115, 125, 134, 136, 145, 146, 147, 154, 156, 172
**ADR Refs:** None found after search
**Spec:** spec:11 (spec:11.1, spec:11.2, spec:11.3, spec:11.4)
**Absorbs:** Planning Infrastructure & Agent Tooling (legacy authored build-map/story-index package)

### Phase Notes

- Story 134 and Story 136 established the current authored build-map/spec stack.
- Story 145 landed the graph+state migration, replacing the authored planning surface with structured state, compiled joins, generated views, and hard linting.
- Blocked lines with unmet unblock conditions should surface as health flags rather than the recommended next move, and eval retry triggers stay dormant until materially new evidence appears.

### Compromise Progress

- **B1: Story files and tracked checklists** — **hold**
  - Current: Story files remain the safest way to preserve scope, acceptance criteria, and work-log context across sessions.
  - Converge signal: Long-horizon planning continuity becomes reliable enough that explicit story slicing is optional.
  - Evidence: No automated harness; human capability detection remains the practical signal.
- **B2: Methodology state and substrate tracking** — **climb**
  - Current: Structured methodology state and generated planning views are still required so triage can reason about architecture readiness without guessing from repo shape alone.
  - Converge signal: Architectural readiness and planning state become inferable directly from the repo and normal artifacts without an explicit state layer.
  - Evidence: Story 145 replaced the authored build-map with methodology state plus generated views rather than deleting the responsibility.
- **B3: Triage skills and routing runbooks** — **hold**
  - Current: Explicit routing and domain-specific triage logic still produce better next-step choices than monolithic generic planning.
  - Converge signal: Repo-aware prioritization becomes reliable without procedural scaffolding.
  - Evidence: No automated harness; the detector is sustained autonomous prioritizer quality.
- **B4: Workflow gates and story-closure chain** — **hold**
  - Current: `/build-story`, `/validate`, and `/mark-story-done` remain useful because human trust and AI self-verification are not yet strong enough to collapse the chain.
  - Converge signal: The chain shrinks to the level of review the operator actually wants.
  - Evidence: Human trust plus repeated correct autonomous closure remains the practical detector.
- **B5: `AGENTS.md`, skills, and runbooks** — **hold**
  - Current: Explicit repo conventions, skills, and runbooks are still needed so future sessions do not re-learn the same rules from scratch.
  - Converge signal: Project conventions become inferable from code and normal repo artifacts alone.
  - Evidence: No automated harness; use reliable convention inference across fresh sessions as the detector.

---

*Last generated: 2026-04-19*
