---
id: "228"
title: "Original Music Video Pilot"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "R5 (human involvement), R6 (creative taste), R7 (iterative generation)"
  - "R8 (production artifacts), R9 (export), R10 (playable assembly)"
  - "R12 (transparency and control), R15 (change propagation)"
spec_refs:
  - "spec:4.10.3"
  - "spec:4.10.7"
  - "spec:5.1"
  - "spec:5.3"
  - "spec:6.1"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.1"
  - "spec:8.2"
  - "spec:10.1"
  - "spec:10.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "032"
  - "166"
  - "167"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:8"
  - "spec:10"
compromise_refs:
  - "C1"
  - "C2"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-generation"
  - "final-output"
  - "music-video"
  - "feature-completeness"
legacy_system: ""
---

# Story 228 — Original Music Video Pilot

**Priority**: Medium
**Status**: Draft
**Relative size**: M target for the smallest coherent pilot; reassess after baseline and extraction planning.
**Ideal Refs**: R5–R10, R12, R15; music videos explicitly belong to the Ideal.
**Spec Refs**: spec:4.10.3, spec:4.10.7, spec:5.1, spec:5.3, spec:6.1, spec:7.1, spec:7.2, spec:8.1, spec:8.2, spec:10.1–10.3.
**ADR Refs**: ADR-002 (existing navigation/readiness), ADR-003 (intent and compiled prompts).
**Depends On**: Stories 032, 166, 167 (landed cost, assembly and validation foundations).

## Goal

Produce and review one original 20–40-second music-video passage with six to ten shots through CineForge's normal project/API/driver workflow. Preserve the chosen song, use one visual canon and one timed title or super, retain selectable takes, and bound generation through reviewed intent and enforceable spending. The operator can watch, choose a different take and export the same passage through existing screens. This proves a useful creative loop and identifies the real quality/cost boundary before attempting a full song.

The source is [Scout 024](../scout/scout-024-ai-music-video-original-pipeline.md), items 1–4, and its [independent production audit](../research/scout-024-ai-music-video/production-audit.md). User approval on 2026-10-04 authorized creating this story. It did not authorize paid generation or implementation in the scouting session.

## Eval Ladder Context

- **Root / full-path golden:** No maintained original music-video passage eval was found. Establish a frozen brief, original audio span, intended shot actions, visual references and title timing before the first scored run. Its root outcome is a coherent playable/exportable passage that serves the brief, preserves the song and supports a deliberate take revision. A root result is deferred until those inputs and a numeric spending envelope are established; do not invent a score from external production records.
- **Parent evidence:** Existing `final-render-provider-floor` covers reference-conditioned scenes, not a musical passage. Its historical quality/runtime rows are marked contaminated/non-decision-grade and its default is provisional pending repaired-contract evidence. `runtime-media-validation` and `runtime-final-output-validation` also mark their historical scores non-decision-grade; their old 1.0 rows cannot establish current readiness. `video-understanding` covers ordered frames, not native audiovisual synchronization. Stories 166/167 provide assembly/validation plumbing, not proof of this musical outcome.
- **Observed local failure boundary:** Final assembly currently concatenates scene media without a selected song master; normalized mixed-audio inputs can drop all audio. Timeline uses estimated seconds, no explicit musical timebase. No first-class timed-overlay contract or explicit video candidate-selection decision was found. Budget checks occur between stages, without per-submit reservation. These are inspected contracts, not a measured claim that the best AI cannot direct a music video.
- **Next node:** First freeze the pilot and check current provider capabilities. After live model discovery, measure one capable model's single-call creative plan against the whole brief before decomposing creative authorship. Exercise the existing full path and classify only demonstrated failures. Add child timing/compositing, selection and spending checks where they explain that root failure.
- **Registry:** Create an owning pilot eval entry before any scored run; link relevant parent lanes. Record score, date, git SHA, input/output provenance and mismatch classification after every eval. Re-run the pilot root after child fixes. Re-run an existing parent only if its implementation/contract changed or it can decide provider adoption; never inherit its old score as a musical quality result.

## Acceptance Criteria

- [ ] **Bounded original fixture:** One 20–40-second song passage and six to ten shots, with original/authorized assets and provenance, enter through normal intake and asset injection. A short screenplay/treatment expresses the story using supported intake; raw lyrics do not masquerade as a verified screenplay ingest capability. Persist the selected audio version/span, brief, visual canon, shot actions, title text/timing, output frame rate and explicit success rubric.
- [ ] **Song is authoritative:** Typed sample/frame timing and explicit rounding rules map the selected passage to the edit. Preview and exported cut preserve the same intended audio span and agree on declared boundaries within one output frame. No unexpected silence, duplicate song, hidden time stretch or source-clip audio replaces it. Lossy export need not be byte-identical; any gain/resampling/mix transformation is explicit. Audio changes produce a new version with explicit remap or stale-dependency invalidation.
- [ ] **One deterministic graphic:** Render one title/super with pinned font/assets and declared start/end timing in both preview and export. Sequential rendering, seeked frames and resumed rendering agree in a pinned environment; no wall-clock/random-history dependence. A larger animation engine is not required for acceptance.
- [ ] **Reviewed intent and bounded spending:** A readable manifest names upstream intent, immutable source refs, compiled prompts, candidate/provider identity, estimated upper cost, allowed take count and approval scope. Edits go upstream per ADR-003. A numeric cap and retry ceiling are frozen before paid requests. Every pilot submitter checks current authority and reserves a conservative bound; concurrent/late submits cannot exceed available authority. Unknown pricing or indeterminate submission outcome pauses new spending rather than assuming zero or blindly retrying. Stop/revision revokes unsubmitted work; in-flight charges remain accounted for. Costs distinguish estimates, reservations, confirmed charges and uncertainty.
- [ ] **Take selection is explicit:** Generate at least two candidates for one shot within the cap; retain all candidates/reviews and select by immutable reference. Select an earlier take and reassemble without regenerating accepted shots. Changing selection invalidates/rebuilds the appropriate downstream assembly. A provider job ID or unresolved request identity survives interruption and prevents duplicate submission.
- [ ] **Acceptance coverage is complete:** Expected shot/take/review IDs reconcile. Missing, invalid, incomplete, failed and passed reviews remain distinct; quota exhaustion cannot become a clean result. Review dramatic sufficiency, provider compliance and finished-passage coherence separately. Exact-version matching reuses the existing media-validation trust surface.
- [ ] **Creative result is inspected:** Use a frozen rubric covering shot action, identity/style continuity, musical phrasing, graphic legibility and overall coherence. Define numeric thresholds before outputs are seen; every required dimension and hard constraint must pass independently. An independent agent personally probes the creative result/context, and the operator can watch the whole cut. Sampled frames/audio correlation are labeled with their limits. A failed or capped run is useful evidence but does not satisfy this successful-output criterion.
- [ ] **Singing remains conditional and honest:** Use a visible singing window only when current provider access/capabilities are verified and it fits the approved envelope. Require temporal mouth-motion review, not just copied-audio correlation. A non-singing passage is valid if declared in the frozen brief; silently substituting stills for a required performance is not a pass.
- [ ] **Complete operator path:** Existing project/scene/artifact surfaces let the user attach/select the master, inspect the bounded plan, select a take, play and export. Headless API/CLI offers the same operations. Desktop and mobile browser checks use a normal pipeline-produced project, record screenshots and clean console output, and verify take change plus re-export. No manually seeded impossible artifact combination counts as product proof.
- [ ] **Measured handoff:** Persist accepted cost per shot/second, active human work separately from elapsed waits, provider/raw usage, exact model/response IDs, failures and retry counts. Classify significant eval mismatches as model-wrong, golden-wrong or ambiguous, with runtime impact where relevant. Report what this one passage proves and what remains unknown.

## Out of Scope

- Full three-minute production, feature-film claims or a promised savings percentage.
- New film/sequence/shot IR, global model router, parallel artifact store or replacement project navigation.
- General NLE, rich JS/WebGL renderer, karaoke editor, arbitrary time-warp editor, depth/matte GPU farm or colour-grading platform.
- Automated Suno/Midjourney/Higgsfield browser/account setup or copying the maker's assets.
- Model-role tournament/default changes or new provider integration unless baseline evidence establishes a small necessary extension and scope is reviewed.
- Story 138's broad cost profiles/comparison UI and Story 197's multi-view reference-pack programme.

## Approach Evaluation

- **Simplification baseline:** Can one currently capable model author sufficient creative intent for the complete passage from brief, song evidence and canon? Untested; measure first after discovery. Do not infer AI limits from a cheap model or the source production's failures. Exact media assembly, immutable state and atomic spend enforcement remain operational contracts even if creative planning succeeds in one call.
- **AI-only candidate:** One model produces the complete shot/graphic plan; a directly callable whole-passage video model may reduce subdivision if current access supports all frozen requirements. Verify capabilities and output fidelity before building around it.
- **Hybrid candidate:** One creative plan compiled through existing shot/render contracts; deterministic audio/overlay assembly and accounting; model-assisted semantic review plus direct temporal inspection. Select only after baseline evidence.
- **Code baseline:** Existing media/FFmpeg tools compose supplied media and declared timings. This can establish timing/export truth and the simplest overlay implementation, but cannot establish creative-generation quality by itself.
- **Discriminating test:** Same frozen passage, intent and acceptance rubric; count every review/retry and require all hard constraints. Prefer the smallest approach that passes. If baseline collapses the need for a proposed helper or workflow layer, remove that task rather than preserving it.
- **Constraints/reuse:** ADR-003 read-only compiled prompts; ADR-002 established navigation; versioned artifacts; selected design-study references; render capability shaping; final-output recipe; project settings; existing cost and media-QA seams. No dedicated overlay-renderer ADR selects a framework today.
- **Budget ownership:** Story 228 owns the minimum batch-authority/reservation slice required to safely run this pilot, within existing cost services/guard. Story 138 remains owner of profiles, comparisons and broad stage controls; consume any landed implementation before adding code. Coordinate its notes when this shared slice is implemented, without making the whole Draft story a blocking dependency.
- **Reference ownership:** Reuse the current canonical selection path. Story 197 is related, not a prerequisite for one supported canon.

## Tasks

- [ ] Resolve Draft inputs and freeze brief, original song/source provenance, exact span, output format, numeric rubric, spend cap, take/retry allowance and stop rule. Verify current normal intake route; do not request a model/API spend until covered by actual authorization.
- [ ] Run live discovery and capability qualification; establish root/child eval registry ownership. Measure the best-model single-call creative baseline and existing full-path result, classify gaps, then select the minimum approach.
- [ ] Refresh affected file/class/method sizes. Extract focused responsibilities from oversized owners before adding behavior; write the concrete build plan with measured class sizes and no new god objects.
- [ ] Define Pydantic contracts for the missing master/timing, overlay, take selection and batch-authority boundaries before call sites. Prefer additions to coherent existing contracts; introduce event schemas first if events are necessary.
- [ ] Implement headless song preservation and one deterministic graphic through existing assembly/track seams; cover timing, seek history, source-audio mixing and revision invalidation.
- [ ] Implement the minimum selection/review coverage and per-submit authority/reservation seam. Test concurrent limits, revocation, unknown result/cost, omitted review IDs and interrupted job adoption.
- [ ] Surface the coherent operator loop through focused components in existing project/scene/artifact views; persist settings in project artifacts/config, not localStorage.
- [ ] Run the bounded original passage and personally inspect the whole export; conduct independent creative probe, record timing/cost/labour evidence, investigate all significant mismatches and rerun root after fixes.
- [ ] Verify desktop and mobile normal-workflow playback, earlier-take selection and export with screenshots/console evidence; use the browser runbook if the environment blocks verification.
- [ ] Remove any obsolete active-track replacement, audio-dropping assembly branch or duplicated approval/selection path actually superseded by this work. Preserve valid non-music assembly behavior through the coherent current API, not compatibility shims.
- [ ] Backend checks: `make test-unit PYTHON=.venv/bin/python`; `PYTHONPATH=src .venv/bin/python -m ruff check src/ tests/`; relevant schema and service-boundary tests.
- [ ] UI checks: `pnpm --dir ui run lint`, `pnpm --dir ui exec tsc -b`, `pnpm --dir ui run build`.
- [ ] Run `/improve-eval` or equivalent mismatch investigation; update registry scores/date/SHA and acceptance decisions. No arithmetic average can override a failed hard constraint.
- [ ] Update related docs, Scout 024 disposition and work log; compile/check methodology. Run `make skills-check` only if agent tooling/instructions change.
- [ ] Verify Central Tenets:
  - [ ] T0 — Data Safety: immutable original assets/takes, selections and lineage.
  - [ ] T1 — AI-Coded: focused, typed, discoverable responsibilities.
  - [ ] T2 — Architect for 100x: measured baseline prevents speculative infrastructure.
  - [ ] T3 — Fewer Files: reuse contracts and extract only cohesive oversized responsibility.
  - [ ] T4 — Verbose Artifacts: replayable run/eval/approval evidence and useful work log.
  - [ ] T5 — Ideal vs Today: easy creative iteration; simplify scaffolding when the detector passes.

## Workflow Gates

- [ ] Build complete: implementation, representative output inspection and required checks recorded; human summary shared.
- [ ] Validation complete through `/validate`, or explicitly skipped by user.
- [ ] Story marked Done through `/mark-story-done` only after acceptance criteria pass.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owners:** Existing render adapter owns provider execution and selected output lineage; final-output module owns export assembly; shared cost services/guard own authority/accounting; media-validation owns review evidence. Focused new helpers are justified for frame/audio composition or reservation state, not a new production orchestrator.
- **Contracts:** New inter-layer payloads are Pydantic schemas before API/UI code. Define rational output frame rate, source audio sample rate and rounding policy; do not require every floating timestamp to be perfectly representable as a frame.
- **Size discipline:** `make check-size` ran 2026-10-04. Relevant large files are acknowledged below. File counts are not class counts: before changing any >500-line class, measure it and add the required decomposition plan. Methods >100 lines must be decomposed before new logic unless an explicit reviewed exception applies.
- **Decision context:** Read ADR-002, ADR-003, `docs/design/principles.md`, `docs/design/decisions.md`, Ideal/spec and canonical methodology state/graph. Use current screenplay-centred intake and artifact-first review. No dedicated timed-graphics ADR exists; create one only if choosing a durable new framework/architecture warrants it.
- **Phase:** Primary generation work advances spec:7 climb with spec:6 planning support. Timeline/UX and cost/QA changes extend existing hold-phase infrastructure for this demonstrated use; no category reprioritization or convergence claim.

## Files to Modify

Candidate touch points, verified 2026-10-04; the baseline chooses the final set.

| Path | Lines | Responsibility / size action |
|---|---:|---|
| `src/cine_forge/schemas/timeline.py` | 36 | Typed musical timing/selected master reference, or focused companion schema |
| `src/cine_forge/schemas/final_output.py` | 109 | Song/graphic/selection provenance |
| `src/cine_forge/schemas/render.py` | 298 | Candidate/selected-take refs if this is the coherent home |
| `src/cine_forge/schemas/cost_tracking.py` | 190 | Batch authority/reservations |
| `src/cine_forge/schemas/media_validation.py` | 145 | Coverage/result contract only where missing |
| `src/cine_forge/modules/timeline/final_output_v1/main.py` | 697 | Extract assembly/composition responsibility first |
| `src/cine_forge/modules/timeline/track_system_v1/main.py` | 600 | Focused extraction before adding song/overlay track behavior |
| `src/cine_forge/modules/generation/render_adapter_v1/outputs.py` | 364 | Retain candidates; explicit selected refs |
| `src/cine_forge/modules/generation/render_adapter_v1/orchestration.py` | 227 | Submission authority/job recovery hook |
| `src/cine_forge/modules/generation/render_adapter_v1/request_shaping.py` | 304 | Existing capability checks; extend only if necessary |
| `src/cine_forge/services/cost_tracking.py` | 789 | Extract focused reservation/accounting owner before additions |
| `src/cine_forge/driver/budget_guard.py` | 76 | Reuse common authority/status, avoid parallel budget rules |
| `ui/src/components/GeneratedVideoPanel.tsx` | 660 | Extract selection/review component before adding UI |
| `ui/src/components/FinalOutputViewer.tsx` | 432 | Host focused master/graphic review controls; acknowledge >400 |
| `src/cine_forge/api/routers/` and focused UI API/types modules | New/touch set selected at build | Thin typed endpoints and client contracts; no inline growth of service/page god objects |
| `configs/recipes/`, `tests/unit/`, `benchmarks/`, `docs/evals/registry.yaml` | Scope selected at baseline | Existing recipe/fixtures/eval patterns |

Avoid growing known oversized `api/service.py` (1321), `api/models.py` (645), `driver/engine.py` (1353), `render_adapter_v1/main.py` (910), `render_clip_plan_v1/main.py` (976), `SceneWorkspacePage.tsx` (1030), `ProjectHome.tsx` (612) or `ui/src/lib/types.ts` (777). If required, extract first and list exact impact in the build plan.

## Redundancy / Removal Targets

- Implicit latest-generated-take selection in the path replaced by explicit selection.
- Any assembly branch that silently substitutes/drops the declared song master.
- Duplicate prompt edits, approval flags or budget math outside authoritative upstream/schema/service owners.
- Experimental compositor code once the simplest passing implementation is selected.

## Notes

Draft readiness: freeze the original inputs, numeric spend/rubric envelope and callable route, then record the single-call/full-path baseline and minimal implementation size before promoting to Pending. No failed current musical-passage run demonstrates a capability blocker. Unsupported audio conditioning affects optional singing, not post-production song assembly. If a real blocker emerges, record it in the canonical fields and reframe the plan.

No original maker media or lyrics are required. A caller-supplied original song is acceptable; automatic composition/provider account integration is not required to prove this loop. Full beat/word alignment is only needed to the precision actually used by the frozen passage; do not build a karaoke subsystem for one timed title.

Scope is end to end: a headless-only demo cannot close this operator-facing story. M is a pilot target, not a claim that four independent general-purpose subsystems are M. If the measured minimum becomes L, document the cause and propose a coherent boundary adjustment before broadening.

## Plan

Draft preparation and implementation order are captured above. The next `/build-story` pass first resolves the frozen fixture/envelope, runs the capability/baseline gate, and turns the candidate touch points into an evidence-backed per-task plan. It may delete unnecessary proposed machinery. It must not start broad framework/provider work merely to reproduce the original maker's stack.

## Work Log

20261004-1110 — story creation: preserved the approved Scout 024 pilot as one end-to-end Draft story, with existing assembly/cost/QA ownership, explicit musical acceptance and bounded-spend requirements. This gives the next build a concrete success surface without claiming current provider or creative quality proof. Evidence: source audit, live local schemas/modules, Stories 032/138/140/166/167/197, current registry's provisional final-render evidence, ADR-002/003 and `make check-size`. Next: freeze original inputs/envelope and measure the baseline before selecting implementation.

20261004-1120 — initial planning verification: independent read-only review found no scope/readiness/eval-ownership issue. In the original stale checkout, this pilot temporarily used local ID 215; its links, generated inclusion, methodology compile/check and whitespace checks passed. Compilation required moving an existing local Story 213 note from frontmatter to its work log and reconciling local history counters. That unrelated note remains local and is excluded from the landed change set. Active focus/category phases were preserved. Next: integrate with current origin/main before check-in.

20261004-1132 — check-in integration: origin/main advanced 25 commits and already owns Story 215, so renumbered this pilot to 228 in an isolated current-main checkout and updated all scout/research links. Regenerated planning state/views from clean upstream sources, excluding unrelated primary-checkout eval and deployment notes. The audit retains its original 9486191 source baseline. Methodology compile/check, 21 planning-graph unit tests, links/hash/numbering checks and scoped whitespace validation pass. Next: commit and fast-forward land the documentation-only change set.
