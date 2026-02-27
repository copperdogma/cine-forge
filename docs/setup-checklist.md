# CineForge — Retrofit Checklist

Retrofitting Ideal-first methodology onto existing project. Generated 2026-02-26.

## Completed

- [x] Existing docs, stories, code, inbox, and ADRs reviewed (Phase 1)
- [x] `docs/ideal.md` created — 16 requirements across 7 themes (Phase 2)
- [x] Socratic conversation with user — refined Ideal with key insights:
  - "Easy, fun, and engaging" as primary design test
  - Iterative refinement (generate→react→refine) as core creative loop
  - Voice-first as ultimate expression of the Ideal
  - Multi-human collaboration in scope
  - Roles serve the Ideal through engagement even if technically compromise
  - Versioning reduces anxiety, makes experimentation fearless
- [x] Existing `docs/spec.md` annotated with limitation types and detection mechanisms (Phase 3)
  - 7 indexed compromises (C1–C7) with full templates
  - 7 additional compromise elements noted in mixed sections
  - Compromise Index table added
  - Untriaged Ideas section added (12 items from inbox)
- [x] Gap analysis written to `docs/retrofit-gaps.md` (Phase 4)
  - 7 missing detection evals for AI compromises
  - 3 simplification evals proposed (highest leverage)
  - 7 missing golden references
  - Second screenplay gap identified
  - 4 untraceable stories flagged (1 questionable)
  - 6 Ideal requirements under-covered by stories
  - 6 eval infrastructure gaps
- [x] Retrofit checklist created (Phase 5)
- [x] AGENTS.md updated with Ideal reference (Phase 6)

## Remaining (prioritized)

### P0 — Highest leverage

- [ ] ~~Create simplification eval: "single-call screenplay understanding"~~ — **Dossier will handle extraction** (see `docs/retrofit-gaps.md` §6)
- [ ] ~~Create simplification eval: "single-pass scene analysis"~~ — **Dossier will handle extraction**
- [ ] Create golden reference for continuity events (R3) — The Mariner per-scene character state
- [ ] Create golden reference for character conversation quality (R4) — 5 questions for Billy/Rose/Dad
- [ ] Story 092 (Continuity AI) — highest-value pending story, directly implements R3
- [ ] Create Dossier adapter story — intake path that accepts Dossier structured output → CineForge artifacts

### P1 — Fill critical gaps

- [ ] Create golden reference for concern group artifacts (R8, ADR-003) — Look & Feel, Sound & Music, Rhythm & Flow for 3 scenes
- [ ] Create promptfoo eval for concern group generation (Rhythm & Flow / editorial direction first)
- [ ] ~~Create promptfoo eval for scene_breakdown entity extraction~~ — **Dossier will handle extraction** (see `docs/retrofit-gaps.md` §6)
- [ ] ~~Add Gemini providers to `scene-extraction.yaml`~~ — **Dossier will handle extraction**
- [ ] ~~Create simplification eval: "zero-QA extraction"~~ — **Dossier will handle extraction**
- [ ] Add `ideal_refs` field to all Pending/Draft stories
- [ ] Create story for R13 (preference learning) — data model + feedback loop + transparency
- [ ] Create story for R9 (narrative-aware timeline export)
- [ ] Create story for R11 (Scene Workspace — per-scene production readiness surface)

### P2 — Important but not urgent

- [ ] Create story for R10 (video preview/assembly view)
- [ ] Create story for R7 (explicit iterative generation UX story)
- [ ] Create story for R16 (multi-human collaboration) — likely needs ADR first
- [ ] Create `evals/baseline-results.md` — structured "what AI can and can't do" document
- [ ] Run baseline: "can a single model call do this?" for each AI compromise
- [ ] Record baseline results in `evals/baseline-results.md`
- [ ] Get a second test screenplay with golden references (Liberty Church 2 or Big Fish)
- [x] ~~Decide on Story 046 (Theme System) — Ideal-traceable or demote to inbox?~~ — Keeping as Draft, low priority, easy win
- [x] ~~Story 090 (Persona-Adaptive Workspaces)~~ — Cancelled, superseded by two-view architecture + interaction mode (Story 089)
- [ ] ADR-003 (Film Elements) — resolve element grouping before building Stories 021-024

### P3 — Polish and ongoing

- [ ] Update `docs/stories.md` with Ideal-alignment notes per story
- [ ] Create golden references for shot planning, export metadata, production readiness
- [ ] Create evals for continuity detection, chat quality (after goldens exist)
- [ ] Review and update Ideal annually or when fundamental capabilities shift
