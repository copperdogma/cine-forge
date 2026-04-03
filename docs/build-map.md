# Build Map

> Central dashboard for system progress. Organized by category matching
> `docs/spec.md` (`spec:1` through `spec:11`). Each category tracks product need,
> tech need, substrate status, story coverage, and the current phase of its live
> compromises or execution constraints.

## How to Read This Map

- **Product need**: what the category must deliver to the user or to the
  execution experience while the execution ideal still needs scaffolding.
- **Tech need**: what architectural substrate must exist in code or repo process.
- **Substrate**: `exists`, `partial`, `missing`, or `unplanned`.
- **Phase**:
  - `climb` — substrate is still incomplete, or current work should improve
    quality/capability
  - `hold` — substrate exists and the current focus is keeping it coherent,
    cheaper, faster, or simpler
  - `converge` — deletion gate passes; the compromise is ready to be removed
  - `unplanned` — no coherent build path exists yet

## 1. Foundation & Artifact Runtime                                           `spec:1`

**Product need:** Artifacts, decisions, and runtime operations stay immutable,
auditable, and safe to revise.
**Tech need:** Snapshot versioning, dependency-aware invalidation, AI/runtime
boundary discipline, and durable audit metadata.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 001, 002, 007, 031, 037, 040, 050, 052, 073, 074, 101, 114, 116, 117, 118, 122, 123, 124
**Spec:** spec:1 (spec:1.1, spec:1.2, spec:1.3, spec:1.4, spec:1.5, spec:1.6)
**ADR Refs:** None found after search
**Absorbs:** Foundation & Artifact Runtime (old 1)

### Phase Notes

- Core substrate exists. Current work here is mostly maintenance, decomposition,
  and verification hardening rather than a missing-system climb.

## 2. Story Intake & Understanding                                            `spec:2`

**Product need:** CineForge can accept story inputs in multiple formats and turn
them into a coherent, browsable understanding of the screenplay quickly enough
to start creative work.
**Tech need:** Ingestion, normalization, canonical script handling, project
configuration, script-bible extraction, and scene understanding.
**Substrate:** exists
**Phase:** climb

**Story coverage:** partial
**Stories:** 003, 003b, 004, 005, 006, 049, 061, 062, 063, 064, 065, 135
**Spec:** spec:2 (spec:2.1 through spec:2.7.2)
**ADR Refs:** ADR-003 (project is the story; two-lane architecture)
**Absorbs:** Script Understanding Pipeline (old 2)

### Compromise Progress

- **C4: Two-Tier Scene Architecture** (AI capability) — **climb**
  - Current: structural scene breakdown lands quickly, while slower narrative
    enrichment remains separate and user-triggered.
  - Converge signal: single-pass scene understanding that is both fast enough
    and good enough to replace the split.
  - Eval: `compromise-C4-two-tier-scenes` — latest local signal from
    `scripts/check-compromises.py` on 2026-03-15 still shows the best candidate
    below the quality/latency bar, so the split remains justified.

## 3. World Building & Continuity                                              `spec:3`

**Product need:** Characters, locations, props, and continuity states persist as
first-class world knowledge.
**Tech need:** Bible folders, relationship edges, and state snapshots over story
time.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 008, 009, 010, 011, 055, 060, 077, 080, 081, 092, 129
**Spec:** spec:3 (spec:3.1, spec:3.2, spec:3.3, spec:3.4)
**ADR Refs:** ADR-001 (shared entity extraction)
**Absorbs:** World Building & Continuity (old 3)

### Phase Notes

- Core substrate exists. Remaining work is mostly quality refinement, continuity
  detection depth, and better downstream reuse of the world model.

## 4. Role System & Creative Direction                                         `spec:4`

**Product need:** Creative roles and characters should feel like collaborators
who understand the story deeply and shape it across disciplines.
**Tech need:** Role hierarchy, style packs, transcripts, suggestion artifacts,
and concern-group direction artifacts.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 014, 015, 016, 017, 018, 019, 020, 021, 022, 023, 082, 083, 084, 093, 094, 095, 096, 097, 099, 100, 121
**Spec:** spec:4 (spec:4.1 through spec:4.10.7)
**ADR Refs:** ADR-002 (goal-oriented navigation), ADR-003 (film elements and concern-group structure)
**Absorbs:** Role System & Creative Direction (old 4)

### Compromise Progress

- **C5: Capability Gating** (AI capability) — **hold**
  - Current: roles declare modality limits and route around them instead of
    pretending to perceive media they cannot understand.
  - Converge signal: one broadly usable multimodal model makes per-role
    modality declarations unnecessary.
  - Eval: `compromise-C5-role-modality` — no passing deletion signal exists yet;
    wait for meaningful provider capability changes before pushing this toward
    convergence.

## 5. Operator Console & Interactive UX                                        `spec:5`

**Product need:** The operator should feel like they are working with their
story, not administering a pipeline.
**Tech need:** Control modes, explanation surfaces, stage-progression rules,
human interaction models, and readiness signals that keep the UI honest.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 011b, 011c, 011d, 011e, 011f, 042, 043, 044, 045, 046, 048, 051, 057, 058, 059, 066, 067, 068, 069, 070, 071, 072, 075, 076, 078, 079, 085, 086, 087, 088, 089, 096, 099, 101, 108, 109, 110, 111, 126, 127, 128, 130, 132
**Spec:** spec:5 (spec:5.1, spec:5.2, spec:5.3, spec:5.4, spec:5.5)
**ADR Refs:** ADR-002 (goal-oriented navigation), ADR-003 (scene workspace / prompt compilation UX)
**Absorbs:** Operator Console & Interactive UX (old 5)

### Phase Notes

- The app shell and user flows exist. Current work is about clarity, polish,
  transparency, and closing remaining UX holes rather than inventing the shell
  from scratch.

## 6. Shot Planning & Visualization                                            `spec:6`

**Product need:** Creative intent becomes concrete planning artifacts usable by
humans and generation models.
**Tech need:** Coverage strategy, shot definitions, storyboard/animatic assets,
and optional keyframes linked to upstream direction.
**Substrate:** exists
**Phase:** climb

**Story coverage:** partial
**Stories:** 025, 026, 027, 056, 119, 120, 121, 132, 137
**Spec:** spec:6 (spec:6.1 through spec:6.4)
**ADR Refs:** ADR-003 (shot planning consumes concern-group artifacts)
**Absorbs:** Shot Planning & Visualization (old 6)

### Phase Notes

- Shot planning and storyboard generation exist, but animatics/previz/keyframe
  coverage is still incomplete. This category is a true climb.

## 7. Generation & Export                                                      `spec:7`

**Product need:** CineForge can compile direction into generation requests and
carry user-provided assets through the same pipeline.
**Tech need:** Render-adapter compilation, engine-pack knowledge, error handling,
and origin-agnostic asset injection.
**Substrate:** partial
**Phase:** climb

**Story coverage:** partial
**Stories:** 028, 029, 030, 058, 130, 140
**Spec:** spec:7 (spec:7.1, spec:7.1.1, spec:7.1.2, spec:7.1.3, spec:7.2)
**ADR Refs:** ADR-003 (real-world assets as first-class inputs)
**Absorbs:** Generation & Export (old 7)

### Phase Notes

- Render-adapter compilation, engine-pack knowledge, error handling, origin-agnostic asset injection, and runtime generated-video validation now exist as real substrate.
- This category stays in `climb` because richer export fidelity and broader media-validation coverage remain unfinished, but the next work is quality/coverage follow-on rather than a missing render foundation.

### Compromise Progress

- **C6: Render Adapter Engine Packs** (Ecosystem / infrastructure) — **hold**
  - Current: heterogeneous video APIs still justify a render-adapter abstraction
    with model-specific engine-pack knowledge.
  - Converge signal: a dominant standard API, or one model that cleanly handles
    all required inputs.
  - Eval: no registry-backed deletion harness exists yet; this remains an
    ecosystem detector rather than an active convergence push.

## 8. AI Platform, Evaluation & Model Strategy                                 `spec:8`

**Product need:** AI cost, quality, and model tradeoffs are visible enough that
operators can trust the system.
**Tech need:** Cost tracking, QA patterns, current eval registry discipline, and
model-slot strategy.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 032, 035, 036, 039, 041, 047, 053, 060, 102, 104, 107, 109, 133
**Spec:** spec:8 (spec:8.1, spec:8.2, spec:8.3)
**ADR Refs:** None found after search
**Absorbs:** AI Platform, Model Selection & Validation (old 8)

### Compromise Progress

- **C1: Cost Transparency** (Ecosystem / infrastructure) — **hold**
  - Current: per-call and per-run cost tracking still matters because model
    pricing and tradeoffs are material.
  - Converge signal: per-call cost tracking becomes unnecessary when inference
    is cheap enough to stop shaping operator behavior.
  - Eval: no registry eval; detection remains pricing-watch based. Current
    threshold is still far away.

- **C2: Dedicated QA Validation Passes** (AI capability) — **hold**
  - Current: dedicated QA / verification remains the safest path for structured
    output quality.
  - Converge signal: first-attempt output becomes reliable enough to demote QA
    to lightweight assertions only.
  - Eval: `compromise-C2-qa-validation` — current registry and checker evidence
    does not justify deletion yet.

- **C3: Tiered Model Strategy** (AI capability + ecosystem) — **hold**
  - Current: value-optimized model selection is still justified because no single
    model dominates CineForge's full task surface.
  - Converge signal: one model meets all current default-driving quality bars at
    acceptable latency and cost.
  - Eval: `compromise-C3-tiered-models` — current checker signal still leaves the
    repo below the single-model bar.

## 9. Memory & Collaboration                                                   `spec:9`

**Product need:** Long-running collaboration should preserve context, transcripts,
and operating-mode intent without losing provenance.
**Tech need:** Canonical memory artifacts, working-memory summaries, and explicit
operating-mode rules.
**Substrate:** partial
**Phase:** climb

**Story coverage:** partial
**Stories:** 017, 018, 019, 033, 069, 083, 089, 101, 131
**Spec:** spec:9 (spec:9.1, spec:9.2, spec:9.3, spec:9.4)
**ADR Refs:** None found after search
**Absorbs:** Memory & Collaboration (old 9)

### Compromise Progress

- **C7: Working Memory Distinction** (AI capability) — **hold**
  - Current: canonical memory plus working-memory caches remain necessary while
    context windows are finite and expensive.
  - Converge signal: persistent, effectively unbounded memory makes the split
    unnecessary.
  - Eval: `compromise-C7-working-memory` — no deletion signal exists yet, so the
    current distinction remains the correct default.

## 10. Timeline & Playable Assembly                                            `spec:10`

**Product need:** Users can inspect pacing, order, and best-available playback
throughout the pipeline.
**Tech need:** Independent timeline artifacts, stacked tracks, and the
always-playable fallback rule.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 012, 013, 140
**Spec:** spec:10 (spec:10.1, spec:10.2, spec:10.3)
**ADR Refs:** None found after search
**Absorbs:** None — new explicit category extracted from existing spec/stories

### Phase Notes

- Timeline substrate exists but had no explicit home in the pre-ADR-021 build
  map. This category fixes that gap and makes future preview/export work legible.
- Story 140 strengthens the always-playable trust rule at the generated-video layer by surfacing validation-backed health and inspection paths instead of leaving broken outputs opaque.

## 11. Planning Infrastructure & Agent Tooling                                 `spec:11`

**Product need:** CineForge still needs explicit planning scaffolding while
current AI cannot yet build and verify large repo changes from the ideal in one
shot.
**Tech need:** Story lifecycle tracking, build-map substrate visibility, triage
skills, workflow gates, AGENTS instructions, runbooks, and verbose work logs.
**Substrate:** exists
**Phase:** hold

**Story coverage:** partial
**Stories:** 053, 103, 109, 125, 134, 136
**Spec:** spec:11 (spec:11.1, spec:11.2, spec:11.3, spec:11.4)
**ADR Refs:** None found after search in CineForge; external reference source is Storybook ADR-021
**Absorbs:** None — new execution category

### Compromise Progress

- **B1: Story files and tracked checklists** (AI capability) — **hold**
  - Current: story files remain the safest way to preserve scope, acceptance
    criteria, and work-log context across sessions.
  - Converge signal: long-horizon planning continuity is reliable enough that
    explicit story slicing is optional.
  - Eval: no automated harness; human capability detection remains the practical
    signal here.

- **B2: Build map and substrate tracking** (AI capability) — **hold**
  - Current: build-map substrate tracking is still required so triage can reason
    about architecture readiness instead of guessing from repo shape alone.
  - Converge signal: architectural readiness becomes inferable directly from the
    repo at triage time.
  - Eval: no automated harness; use repeated successful autonomous triage as the
    detector.

- **B3: Triage skills and routing runbooks** (AI capability) — **hold**
  - Current: explicit routing and domain-specific triage logic still produce
    better next-step choices than monolithic generic planning.
  - Converge signal: repo-aware prioritization becomes reliable without
    procedural scaffolding.
  - Eval: no automated harness; the detector is sustained autonomous prioritizer
    quality.

- **B4: Workflow gates and story-closure chain** (Human / trust) — **hold**
  - Current: `/build-story`, `/validate`, and `/mark-story-done` remain useful
    because human trust and AI self-verification are not yet strong enough to
    collapse the chain.
  - Converge signal: the chain shrinks to the level of review the operator
    actually wants.
  - Eval: human trust plus repeated correct autonomous closure is the detector.

- **B5: `AGENTS.md`, skills, and runbooks** (AI capability) — **hold**
  - Current: explicit repo conventions and procedural docs are still needed so
    future sessions do not re-learn the same rules from scratch.
  - Converge signal: project conventions become inferable from code and normal
    repo artifacts alone.
  - Eval: no automated harness; use reliable convention inference across fresh
    sessions as the detector.

---

*Last updated: 2026-03-19 (Story 032 done; no active stories in progress)*
