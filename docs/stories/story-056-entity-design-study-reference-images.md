# Story 056 — Entity Design Studies (Reference Image Generation Loop)

**Priority**: High
**Status**: To Do
**Spec Refs**: 6.3 (Bible Artifact Structure), 12.2 (Visual Direction — reference imagery), 14 (Storyboards), 17 (Render Adapter inputs), 18 (User Asset Injection), 20 (Metadata and Auditing)
**Depends On**: Story 008 (character bibles), Story 009 (location/prop bibles), Story 011f (chat UI), Story 021 (visual direction), Story 029 (user asset injection)

## Goal

Add a first-class **Design Study** workflow that generates and iterates reference images for each character, location, and prop. After bibles exist, the AI offers to generate image studies, starts with a single initial candidate per entity, and supports iterative rounds where users can select winners, request more-like-this variants with comments, reject undesired directions, and favorite candidates. All generated images remain versioned and browseable so users can revisit earlier attempts. Once a design is chosen, the system generates an entity-specific multi-angle reference pack for downstream AI video generation and/or IRL production use.

## Acceptance Criteria

- [ ] Design Study offer is only available after required bible artifacts exist (`character_bible`, `location_bible`, `prop_bible` as applicable).
- [ ] Visual-detail enrichment pass is an explicit manual trigger only (never automatic).
- [ ] Design Study can be launched in two modes:
  - [ ] Per-entity (hand-crafted flow).
  - [ ] Bulk mode (queue multiple entities for users who want minimal step-by-step interaction).
- [ ] Bulk mode executes entity jobs in parallel by default, with configurable concurrency limits for provider rate/cost control.
- [ ] Initial generation creates exactly 1 candidate image per entity.
- [ ] Subsequent rounds are user-selectable per round (`1`, `2`, `4`, or `8` candidates).
- [ ] User iteration actions are supported per image:
  - [ ] Mark as `selected_final`.
  - [ ] Mark as `favorite`.
  - [ ] Mark as `rejected` with optional free-text reason.
  - [ ] Mark as `seed_for_variants` with optional guidance text.
- [ ] Variant regeneration uses selected seeds + user guidance + accumulated rejected-pattern constraints.
- [ ] Regeneration includes explicit control `Use favorites as style anchors` with influence levels `low|medium|high` (default off).
- [ ] Selecting a new `selected_final` supersedes prior final choice without mutation; prior final remains in decision history.
- [ ] Every generated image and every decision event is immutable and persisted (no destructive overwrite).
- [ ] Generated Design Study images are stored as children of their source entity bible artifact with full lineage links.
- [ ] Entity detail UI supports browsing full history of rounds and filtering by `favorites`, `selected`, and `rejected`.
- [ ] Entity UI thumbnail behavior:
  - [ ] Use `selected_final` as entity thumbnail when present.
  - [ ] Otherwise use most recent `favorite` as thumbnail fallback.
  - [ ] Otherwise use a neutral default placeholder.
- [ ] Optional visual mode supports entity-image tile/background treatments while preserving text legibility (contrast-safe overlay rules).
- [ ] Story includes a research-backed policy for final multi-angle packs:
  - [ ] Typical film concept design angle/view standards by entity type.
  - [ ] Recommended view counts/angles for current SOTA video models that support image references.
  - [ ] Chosen defaults documented with rationale and still user-adjustable before generation.
- [ ] Generated references are emitted as artifact(s) consumable by storyboard and render adapter stages.
- [ ] Audit metadata captures prompt lineage, source bible versions, model/provider, cost, and decision rationale.
- [ ] Bible text synchronization rules are explicit:
  - [ ] User feedback can be stored as `visual_direction_notes` immediately without mutating canonical description fields.
  - [ ] Canonical bible description updates require explicit apply action (or approval flow), producing a new bible version with provenance.
- [ ] Unit + integration coverage includes the iterative loop and persistence guarantees.

## Out of Scope

- Training custom LoRA/embedding models for identity consistency.
- Replacing storyboard generation or render adapter logic; this story only provides better reference inputs.
- Automatic “best image” finalization without user decision.
- Real-time collaborative voting workflows for multiple reviewers.

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- LLM-native tasks:
  - Visual detail enrichment from script + bible evidence.
  - Candidate prompt synthesis and iterative prompt adaptation from user feedback.
  - Constraint extraction from rejected images/comments.
- Deterministic code tasks:
  - Artifact persistence/versioning and immutable round history.
  - Decision state machine (`selected`, `favorite`, `rejected`, `seed_for_variants`).
  - API/UI orchestration, pagination/filtering, and lineage metadata.
- Quality gates:
  - Reject schema-valid but semantically weak outputs (“generic portrait”, “empty location”) through QA predicates.
  - Store prompts, model params, and negative constraints explicitly in run artifacts for replay.

## Tasks

- [ ] Design schemas:
  - [ ] `DesignStudyRound`
  - [ ] `DesignStudyImage`
  - [ ] `DesignStudyDecisionEvent`
  - [ ] `EntityReferencePack`
- [ ] Register new schemas and artifact types in schema/artifact registries.
- [ ] Implement module `design_study_v1` for initial batch and iterative variant generation.
- [ ] Implement optional `visual_detail_enrichment_v1` pass (script evidence top-up before first generation).
- [ ] Add research note/ADR input on recommended reference angle sets and counts per entity type.
- [ ] Implement API endpoints for:
  - [ ] create round
  - [ ] submit image decisions
  - [ ] generate next round from seeds/comments
  - [ ] finalize and generate multi-angle pack
  - [ ] bulk-create design study rounds for selected entity sets
- [ ] Implement bulk execution concurrency controls and progress reporting for parallel runs.
- [ ] Implement bible-child artifact linking + retrieval for Design Study galleries on entity pages.
- [ ] Implement thumbnail selection policy (`selected_final` > latest `favorite` > placeholder).
- [ ] Implement explicit “Apply visual feedback to bible text” action that writes a new bible version.
- [ ] Update UI entity pages for Design Study workflow (offer, rounds, feedback controls, favorites, finalization).
- [ ] Wire resulting references into storyboard + render adapter input selectors.
- [ ] Add unit tests for state transitions, lineage, and immutable persistence.
- [ ] Add integration test: bible ready -> round1 -> user feedback -> round2 -> finalize -> multi-angle pack artifact.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and `pnpm --dir ui run build`
- [ ] Search all docs and update any related to what we touched.
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Capture-first history of every generated image and decision event.
  - [ ] **T1 — AI-Coded:** Prompts, schemas, and module boundaries are explicit and agent-readable.
  - [ ] **T2 — Architect for 100x:** Keep provider abstraction flexible; no single-model lock-in.
  - [ ] **T3 — Fewer Files:** Co-locate schema/model helpers where practical.
  - [ ] **T4 — Verbose Artifacts:** Persist full context (prompts, params, upstream versions, costs).
  - [ ] **T5 — Ideal vs Today:** Prefer simple iterative loop first; defer advanced ranking/retrieval.

## Files to Modify

- `src/cine_forge/schemas/` — add Design Study and reference pack schemas.
- `src/cine_forge/artifacts/` — register/store new artifact types and manifests.
- `src/cine_forge/modules/visualization/` — add `design_study_v1` and optional enrichment module.
- `src/cine_forge/api/` — expose Design Study endpoints and DTOs.
- `ui/src/` — entity detail experience for rounds, feedback, favorites, and finalization.
- `configs/recipes/` — hook module(s) into the appropriate pipeline path.
- `tests/unit/` and `tests/integration/` — cover loop behavior and persistence guarantees.
- `docs/spec.md` and related docs — align terminology and flow where needed.

## Notes

- Terminology: use **Design Study** as the user-facing term for iterative concept/reference image rounds.
- This story should support two operator intents:
  - AI-video-first users who need robust multi-angle reference packs for generation.
  - IRL production users who mainly need polished concept designs and variant sets.
- Favorite semantics should remain explicit and non-ambiguous:
  - `selected_final`: canonical image chosen as the entity's active design.
  - `favorite`: user-curated bookmark only; not final by itself.
  - Automatic prompt weighting from favorites is opt-in via explicit control (default off) to avoid hidden behavior.
- Research is required before locking multi-angle defaults; include both film concept practice and current video-model reference needs.
- Parallel bulk generation is preferred UX for low-friction workflows; apply provider-aware concurrency caps to avoid burst failures.
- Bible update recommendation:
  - Keep image-loop feedback and canonical bible text decoupled by default.
  - Capture raw user feedback as structured notes linked to the entity immediately.
  - Update canonical descriptive fields only through explicit apply/approve step to avoid accidental canon drift.
- UI visual treatment:
  - Entity image backgrounds should be opt-in style mode with fixed contrast overlays and typography constraints so legibility is never degraded.

## Work Log

20260219-2208 — story scaffolded and drafted: created Story 056 with Design Study loop scope, acceptance criteria, and implementation tasks, evidence=`docs/stories/story-056-entity-design-study-reference-images.md`, next=validate alignment with user and begin implementation when scheduled.
