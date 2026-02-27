# CineForge — Retrofit Gap Analysis

> Generated during `/retrofit-ideal` — 2026-02-26.
> Identifies what's missing after applying the Ideal-first methodology.
> Items are prioritized by downstream impact. This is a diagnostic, not a mandate —
> the user decides what to tackle and when.

## 1. Missing Detection Evals (for AI Compromises)

Every AI compromise should have an eval that, when it passes, signals the compromise can be deleted.
These are ordered by architectural significance — which compromise elimination would simplify the most.

| Priority | Compromise | What's Missing | Proposed Eval |
|----------|-----------|----------------|---------------|
| **P0** | C4 — Two-tier scene architecture | No eval testing single-pass full enrichment | Submit full screenplay to SOTA model requesting complete scene analysis (structure + narrative beats + tone) in one call. Pass criteria: quality matches current two-pass output AND returns in <10s. |
| **P0** | C3 — Tiered model strategy | No "single model does everything" eval | Run all 9 existing evals with a single model. If one model scores ≥0.90 on all tasks, the tiering overhead is unjustified for that model. |
| **P1** | C2 — QA validation passes | No eval testing first-attempt reliability | Submit 20 diverse extraction tasks to SOTA. If all 20 pass structural + semantic validation without a QA retry, dedicated QA stages can be simplified. |
| **P1** | C5 — Capability gating | Not testable yet | Monitor: when SOTA model processes text + image + video + audio in a single call with high-quality output. Run multimodal eval when available. |
| **P2** | C7 — Working memory | Not testable yet | When context windows exceed 2M tokens: test full-project-context chat (all artifacts + all transcripts loaded) vs. current summarized context. Compare response quality. |
| **P2** | C6 — Render adapter engine packs | Not testable yet | Monitor video generation API ecosystem. When a dominant standard emerges, test single-adapter prompt against 3+ models. |
| **P2** | C1 — Cost transparency | Not testable (ecosystem monitoring) | Track inference cost per 1M tokens quarterly. When it drops below $0.01 across all providers, reassess cost tracking overhead. |

### Simplification Evals (highest leverage)

These test "can the dumbest possible approach work?" — the most important evals to create first.

| Eval | Tests | Current Answer | When to Re-run |
|------|-------|---------------|----------------|
| **Single-call screenplay understanding** | Give SOTA a full screenplay + "extract everything (scenes, characters, locations, props, relationships, config, continuity)" in one call. Grade against all existing goldens. | Unknown — never tested | Every major SOTA release |
| **Single-pass scene analysis** | Give SOTA a full screenplay + "extract scenes with full narrative enrichment in one pass." Grade against scene extraction + enrichment goldens. | Unknown — never tested | Every major SOTA release |
| **Zero-QA extraction** | Run all 9 extraction evals. Count how many pass on first attempt without any QA/retry. | Partially known from benchmarks (top models score 0.88-0.99) but not tested as a "no-retry" pipeline | Quarterly |

## 2. Missing Golden References

Golden references are hand-crafted ground truth that both validate the system AND detect when simplification is possible.

| Priority | Ideal Req | What's Missing | Proposed Golden |
|----------|----------|----------------|-----------------|
| **P0** | R3 — Continuity | No golden for continuity events or errors | Hand-curate continuity timeline for The Mariner: per-scene character state (costume, injuries, emotional state, possessions), flagged continuity issues (if any), state transitions with evidence quotes. |
| **P0** | R7 — Iterative refinement | No golden for iteration quality improvement | Create before/after pairs: initial generation output + user feedback + improved output. Measure: does iteration actually converge toward the stated intent? |
| **P1** | R4 — Character conversation | No golden for character chat quality | Hand-craft 5 character questions for Billy, Rose, and Dad (The Mariner). Grade: in-character voice, psychological grounding, subtext depth, evidence from script. |
| **P1** | R8 — Concern group artifacts (ADR-003) | No golden for concern group output (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World) | Hand-curate concern group artifacts for 3 key scenes in The Mariner. Cover: Look & Feel (visual concept, lighting, color), Sound & Music (soundscape, silence, music intent), Rhythm & Flow (pacing, transitions, coverage priority), Character & Performance notes per character. |
| **P2** | R9 — Export with narrative intelligence | No golden for narrative-aware timeline metadata | Define expected markers, regions, and notes for a The Mariner timeline export. |
| **P2** | R11 — Production readiness | No golden for per-scene readiness computation | Define expected readiness state for The Mariner at various pipeline completion points. |
| **P3** | R8 — Shot planning | No golden for shot list output | Hand-curate a shot list for 2-3 scenes of The Mariner. Cover: coverage strategy, individual shots, editorial rationale. |

### Second Screenplay Gap

All 9 existing evals use only The Mariner. A single test screenplay risks overfitting. Need:
- A second screenplay with different characteristics (different genre, longer/shorter, different structure)
- Corresponding golden references for at least: character extraction, scene extraction, and config detection
- Candidate: Liberty Church 2 (already has production data in test fixtures) or one of the round-trip screenplays (Big Fish — 190 scenes)

## 3. Untraceable Stories

Stories that don't clearly trace back to an Ideal requirement or spec compromise. These are either scope creep, missing documentation, or correctly categorized as infrastructure/polish.

| Story ID | Title | Status | Issue | Recommendation |
|----------|-------|--------|-------|----------------|
| 046 | Theme System (Light/Dark/Auto) | Draft | No Ideal requirement. "Easy and fun" is too loose a justification. | Either add a specific UX-quality requirement to the Ideal, or demote to inbox as low-priority polish. |
| 037 | Production Deployment | Done | Operational necessity, not derived from any requirement. | Acceptable — infrastructure stories don't need Ideal tracing. Note in stories.md. |
| 040 | Pipeline Performance Optimization | Done | Engineering quality improvement. | Acceptable — performance enables R7 (iteration speed) but isn't directly derived from it. |
| 053 | Cross-CLI Skills Unification | Done | Developer tooling. | Acceptable — agent infrastructure. |

**Verdict:** Only Story 046 is questionable. The Done stories are legitimate infrastructure/engineering work that doesn't need Ideal tracing.

## 4. Missing Ideal Requirements in Stories

These Ideal requirements have no dedicated story or are under-covered:

| Ideal Req | Coverage | Gap |
|-----------|----------|-----|
| **R7 — Iterative refinement** | Partially: 082 (direction chat loop), 071 (deferred). Full loop needs 026-028. | No dedicated "iterative generation UX" story. The generate→react→refine loop is implicitly spread across storyboard (026), animatics (027), and render (028) but never explicitly owned. Consider creating a story. |
| **R9 — Export with narrative intelligence** | Partially: 058 (export/share). | No story for narrative-aware timeline export (OpenTimelineIO with markers, regions, clip notes). This is in the inbox but not storied. |
| **R10 — Playable assembly** | Partially: 012-013 (timeline data). | No story for the video preview/assembly view (scene strip player with drag-to-reorder). This is in the inbox but not storied. |
| **R11 — Production readiness per scene** | Partially: 085-087 (pipeline bar, preflight). | No story for the Scene Workspace — the per-scene production readiness control surface. This is in the inbox but not storied. |
| **R13 — Learn from user choices** | No story. | Preference learning is entirely missing from the story backlog. Needs a story covering: data model for preference signals, feedback loop into role behavior, transparency UI. |
| **R16 — Multi-human collaboration** | No story. | Multi-user collaboration is absent from the story backlog. This is a large architectural undertaking (real-time sync, shared state, conflict resolution). Likely needs an ADR first. |

## 5. Eval Infrastructure Gaps

| Gap | Impact | Fix |
|-----|--------|-----|
| ~~`scene-extraction.yaml` missing Gemini providers~~ | ~~Gemini models untested on scene extraction~~ | **Dossier will handle extraction** — see §6 |
| ~~No eval for `scene_breakdown_v1` entity extraction~~ | ~~Action-line entity extraction has golden ref but no eval~~ | **Dossier will handle extraction** — see §6 |
| No eval for creative direction generation | Direction quality is entirely untested | Create eval for editorial direction first (Story 020 is Done, has working module) |
| No eval for continuity detection | R3 has no automated quality gate | Create eval after golden reference for continuity events exists |
| No eval for chat/conversation quality | R4 character/role conversations untested | Create eval for character chat: 5 questions, grade on voice/grounding/subtext |
| No baseline results document | AGENTS.md has eval catalog but no structured "what AI can and can't do" document | Create `evals/baseline-results.md` with current capabilities by task |
| No eval for Dossier→CineForge transformation | Bible quality after Dossier intake is untested | Create eval after Dossier adapter exists — validate transformation from Dossier output to CineForge bible format |

## 6. Dossier Integration Plan

> **Added 2026-02-26.** The user is building a separate project, [Dossier](../), that will
> replace most of CineForge's text analysis and extraction pipeline. Dossier will provide
> pre-extracted structured data (characters, locations, props, relationships, scenes, config)
> that CineForge receives and converts into its final bible format.

**What this changes:**

| Area | Current State | After Dossier |
|------|--------------|---------------|
| Character/Location/Prop extraction | CineForge LLM pipeline (modules in `src/cine_forge/modules/`) | Dossier extracts → CineForge transforms to bible format |
| Scene extraction & enrichment | CineForge two-tier architecture (C4) | Dossier extracts → CineForge consumes structured scenes |
| Entity relationship discovery | CineForge LLM pipeline | Dossier extracts → CineForge consumes |
| Config detection | CineForge LLM pipeline | Dossier extracts → CineForge consumes |
| 9 existing promptfoo evals | Test CineForge's own extraction | Become Dossier's responsibility; CineForge evals shift to transformation quality (bible format, continuity, direction) |
| Extraction golden references | Validate CineForge extraction | Still valuable — validate Dossier output quality |
| Simplification evals (§1) | Test whether CineForge can simplify | C3 (tiered models) and C4 (two-tier scenes) become moot for extraction; still relevant for direction/generation |

**What NOT to invest in (given Dossier):**
- New extraction evals for CineForge's pipeline (character, location, prop, scene extraction)
- Extraction quality improvements in CineForge modules
- Adding Gemini providers to `scene-extraction.yaml` (Dossier handles this)

**What's still CineForge's domain:**
- Bible format and presentation (how extracted data becomes character/location/prop bibles)
- Continuity detection and gap analysis (R3 — Story 092)
- Creative direction generation (editorial, visual, sound, performance)
- Shot planning, storyboard, animatic, render pipeline
- Chat/conversation quality (R4)
- All downstream generation and production artifacts

**Architecture implication:** CineForge needs a Dossier adapter — a module or intake path that
accepts Dossier's structured output and maps it to CineForge's artifact schemas. The existing
ingestion pipeline (Stories 003-007, 062) becomes a fallback for users without Dossier access.

## 7. Inbox Items Status After Retrofit

Items from `docs/inbox.md` that are now captured in the Ideal or spec (see also §6 for Dossier impact on extraction items):

| Inbox Item | Captured In | Action |
|-----------|-------------|--------|
| Narrative-aware timeline export | Ideal R9, Spec Untriaged | Needs story |
| Video preview/assembly view | Ideal R10, Spec Untriaged | Needs story |
| Scene Workspace (View 2) | Ideal R11, Spec Untriaged | Needs story |
| Two-view architecture | Ideal Vision Preferences | Documented |
| Kill pipeline DAG view | Ideal (pipeline invisible) | Decision already made (Story 091 killed) |
| No built-in NLE | Ideal Vision ("export-first") | Documented |
| Quality intelligence differentiator | Ideal R11, R12 | Documented |
| "AI-filled" / skip-ahead | Ideal R11, Spec Untriaged | Needs spec detail on "AI-inferred" state |
| Prompt transparency | Ideal R12, Spec Untriaged | Needs spec section |
| Voice specification | Ideal R8, Spec Untriaged | Needs spec section under Performance |
| Scene-level video generation | Spec Untriaged | Needs spec update to Shot Planning / Render Adapter |
| Ghost-text inline suggestions | Spec Untriaged | Backlog — no Ideal mapping, UX pattern |
| AI preference learning | Ideal R13 | Needs story |
| Onboarding flow | Spec Untriaged, Story 090 partial | Story 090 covers some |
| Explorer demo project | Spec Untriaged | Needs story |
| Per-feature autonomy levels | Spec Untriaged, Story 090 partial | Story 090 covers some |
| Quality estimates in preflight | Spec Untriaged | Extends Story 087 |
