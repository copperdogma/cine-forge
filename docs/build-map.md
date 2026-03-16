# Build Map — System Structure + Compromise Progress

> This file combines system structure (what exists, dependencies, story coverage)
> with compromise convergence tracking (how close each compromise is to resolution).
> Each compromise carries dual tracking: **Optimize** (improve the workaround) and
> **Eliminate** (detect when the limitation resolves and delete the code).
> See [docs/methodology-ideal-spec-compromise.md](methodology-ideal-spec-compromise.md)
> for the methodology and [Story 134](stories/story-134-compromise-convergence-tooling-migration.md)
> for the migration that introduced this document.

## How to Read Compromise Progress

Each system with an active compromise has a **Compromise Progress** subsection with two parts:

- **Optimize** — how CineForge is improving the current workaround while the limitation still exists
- **Eliminate** — the deletion gate, including the eval or external trigger that would let us remove the compromise

Not every system carries a compromise. Systems without one still matter here because the build map is also the repo's system-structure overview.

---

## 1. Foundation & Artifact Runtime
- [x] Stories cover this system

**Summary:** Project scaffolding, artifact store, schema discipline, driver orchestration, change propagation, progress events, and service/API decomposition. This is the core runtime substrate every other lane builds on.

**Spec Sections:** 2.1-2.6, 3, 20
**ADR Refs:** None found after search
**Dependencies:** None
**Story Coverage:** 001, 002, 007, 031, 037, 040, 050, 052, 073, 074, 101, 114, 116, 117, 118, 122, 123, 124

---

## 2. Script Understanding Pipeline
- [x] Stories cover this system

**Summary:** Story ingestion, script normalization, scene breakdown, scene analysis, project config detection, and the first-pass understanding path from raw script to structured screenplay artifacts.

**Spec Sections:** 4, 5, 5.1-5.3
**ADR Refs:** None found after search
**Dependencies:** Foundation & Artifact Runtime
**Story Coverage:** 003, 003b, 004, 005, 006, 049, 061, 062, 063, 064, 065

#### Compromise Progress

**C4 — Two-Tier Scene Architecture** (Limitation: AI capability)
- **Optimize**: The fast structural breakdown plus slower narrative enrichment split keeps the screenplay browsable immediately while deeper scene understanding stays optional. Current improvement work happens through scene extraction/enrichment evals, scene UX, and latency/cost tuning rather than by collapsing the split prematurely.
- **Eliminate**: Eval `compromise-C4-two-tier-scenes` in [docs/evals/registry.yaml](evals/registry.yaml). Target: combined quality >= `0.90` and latency <= `5000ms` per scene. Latest: no score entry on the compromise eval itself; `scripts/check-compromises.py` reported on `2026-03-15` that the best candidate was `Sonnet 4.6` at `0.885` combined quality and `35527ms`, still `7.1x` too slow. Retry when: scene extraction/enrichment benchmarks improve or a new SOTA model lands. When passes: merge `scene_breakdown_v1` and `scene_analysis_v1`, delete placeholder narrative fields and the separate "Analyze Scenes" step.

---

## 3. World Building & Continuity
- [x] Stories cover this system

**Summary:** Character, location, and prop bibles; entity graph; continuity tracking; discovery and adjudication loops that turn screenplay understanding into persistent world artifacts.

**Spec Sections:** 6, 7
**ADR Refs:** ADR-001 (shared entity extraction)
**Dependencies:** Script Understanding Pipeline
**Story Coverage:** 008, 009, 010, 011, 055, 060, 077, 080, 081, 092, 129

---

## 4. Role System & Creative Direction
- [x] Stories cover this system

**Summary:** Role hierarchy, style packs, inter-role communication, editorial/visual/sound direction, script bible, scene workspace, and the AI collaboration surface that turns analysis into creative exploration.

**Spec Sections:** 8, 9, 10, 11, 12
**ADR Refs:** ADR-002 (goal-oriented navigation), ADR-003 (film elements and creative-direction structure)
**Dependencies:** World Building & Continuity
**Story Coverage:** 014-023, 033, 082-100, 121, 131

#### Compromise Progress

**C5 — Capability Gating** (Limitation: AI capability)
- **Optimize**: Role capabilities remain explicitly scoped by modality so roles do not pretend to understand media they cannot actually perceive. Current role and scene-workspace work stays honest by routing around these limits instead of hiding them.
- **Eliminate**: Eval `compromise-C5-role-modality` in [docs/evals/registry.yaml](evals/registry.yaml). Target: one SOTA model reliably reasons across text, image, video, and audio in a single call. Latest: no scores recorded. Retry when: provider capability surface changes materially. When passes: delete role perception-capability declarations and modality routing logic.

---

## 5. Operator Console & Interactive UX
- [x] Stories cover this system

**Summary:** The screenplay-first app shell, chat-driven operator flow, entity pages, inbox, run views, search, settings, navigation, and all user-facing workflows that expose the pipeline as an enjoyable product instead of a DAG viewer.

**Spec Sections:** 2.5, 2.6, 12.7, 20, 21
**ADR Refs:** ADR-002 (goal-oriented navigation), ADR-003 (creative workspace structure)
**Dependencies:** Foundation & Artifact Runtime, Script Understanding Pipeline, Role System & Creative Direction
**Story Coverage:** 011b-011f, 042-048, 051, 057-059, 066-072, 075-079, 085-089, 096, 098, 099, 101, 108-111, 126-128, 130, 132

---

## 6. Shot Planning & Visualization
- [x] Stories cover this system

**Summary:** Shot planning, design studies, visual reference propagation, storyboards, animatics, previz, and the intermediate planning artifacts that bridge creative direction into generation-ready instructions.

**Spec Sections:** 13, 14, 15, 16
**ADR Refs:** ADR-003 (film elements)
**Dependencies:** Role System & Creative Direction, Operator Console & Interactive UX
**Story Coverage:** 025-027, 056, 119, 120, 121, 132

---

## 7. Generation & Export
- [x] Stories cover this system

**Summary:** Render adapter, engine-pack mediation, user asset injection, generated-output QA, and export fidelity for carrying CineForge's narrative intelligence into downstream tools.

**Spec Sections:** 17, 18
**ADR Refs:** ADR-003 (real-world assets as first-class inputs)
**Dependencies:** Shot Planning & Visualization, Operator Console & Interactive UX
**Story Coverage:** 028-030, 058, 098, 130

#### Compromise Progress

**C6 — Render Adapter Engine Packs** (Limitation: Ecosystem/Infrastructure)
- **Optimize**: The render-adapter abstraction remains the right workaround while model APIs, input capabilities, and duration limits stay fragmented. The lane is mostly still ahead of us, so optimization work is chiefly about keeping the architecture ready for heterogeneous providers rather than pretending a single backend already exists.
- **Eliminate**: No registry eval exists yet. Detection remains the ecosystem trigger from [docs/spec.md](spec.md): a dominant standardized video API or a single model that cleanly handles all required inputs. Latest: no scores recorded. Retry when: provider/API landscape shifts materially. When passes: delete engine-pack tuning, model-specific prompt synthesis, and per-model capability UI.

---

## 8. AI Platform, Model Selection & Validation
- [x] Stories cover this system

**Summary:** Promptfoo benchmarking, model discovery, default selection, compromise checks, cost/latency tracking, and the reliability infrastructure that decides how CineForge uses AI models responsibly.

**Spec Sections:** 2.7, 2.8, 2.9
**ADR Refs:** None found after search
**Dependencies:** Foundation & Artifact Runtime
**Story Coverage:** 032, 035, 036, 039, 041, 047, 053, 060, 102, 104, 107, 109, 133, 134

#### Compromise Progress

**C1 — Cost Transparency** (Limitation: Ecosystem/Infrastructure)
- **Optimize**: CineForge already records cost and latency in run/eval artifacts, and Story 032 is still the live path for fuller budget surfaces. This workaround remains useful because provider pricing and quality tradeoffs are still material.
- **Eliminate**: No registry eval exists. Detection remains the pricing watch from [docs/spec.md](spec.md): when inference drops below `$0.001 / 1M tokens` across the providers we use. Latest: no scores recorded. Retry when: provider pricing changes materially. When passes: delete per-call cost tracking, budget caps, and cost-quality tiering UI.

**C2 — Dedicated QA Validation Passes** (Limitation: AI capability)
- **Optimize**: QA-pass evaluation and lighter-weight validator patterns improve reliability without pretending first-pass outputs are already safe. Story 133 tightened defaults and verification discipline, but the dedicated QA concept still stands.
- **Eliminate**: Eval `compromise-C2-qa-validation` in [docs/evals/registry.yaml](evals/registry.yaml). Target: `10` diverse extraction tasks pass structural + semantic checks on the first attempt with no QA retry. Latest: no score entry on the compromise eval itself; `scripts/check-compromises.py` reported on `2026-03-15` that `GPT-4.1 Mini` scored `1.000` on the existing QA eval, but the full first-attempt harness does not exist yet. Retry when: the dedicated compromise harness is implemented or broader first-pass benchmarks are recorded. When passes: delete dedicated QA pass stages, the verify model tier, and QA-specific schemas.

**C3 — Tiered Model Strategy** (Limitation: AI capability + Ecosystem)
- **Optimize**: Registry-backed model selection, per-module defaults, and targeted triage keep the current multi-model strategy defensible instead of ad hoc. This is a legitimate investment while no single model wins across the whole surface.
- **Eliminate**: Eval `compromise-C3-tiered-models` in [docs/evals/registry.yaml](evals/registry.yaml), computed from existing quality evals. Target: one model meets all quality targets at acceptable latency/cost. Latest: `scripts/check-compromises.py` on `2026-03-15` reported `Sonnet 4.6` as the best candidate, meeting `5/12` targets and still missing `scene-extraction`, `config-detection`, and several extraction quality bars. Retry when: any default-driving eval score changes, new providers/models land, or stale scores are refreshed. When passes: delete work/verify/escalate slots, subsumption hierarchy, and per-stage model override infrastructure.

---

## 9. Memory & Collaboration
- [x] Stories cover this system

**Summary:** Suggestion/decision tracking, long-running collaboration, preference learning, working-memory management, and eventual multi-human collaboration behavior.

**Spec Sections:** 19, 21
**ADR Refs:** None found after search
**Dependencies:** Role System & Creative Direction, Operator Console & Interactive UX
**Story Coverage:** 017, 018, 019, 033, 069, 083, 089, 101, 131

#### Compromise Progress

**C7 — Working Memory Distinction** (Limitation: AI capability)
- **Optimize**: The canonical-vs-working-memory split remains a necessary compromise while context windows are finite and expensive. Story 033 is still the main execution path for building the durable version of this workaround.
- **Eliminate**: Eval `compromise-C7-working-memory` in [docs/evals/registry.yaml](evals/registry.yaml). Target: context windows exceed `10M` tokens at negligible cost or native persistent cross-session memory becomes available. Latest: no scores recorded. Retry when: provider memory capabilities change materially. When passes: delete summarization/compaction controls, memory budgets, and the working-memory distinction itself.

---

*Last updated: 2026-03-15 (Story 134)*
