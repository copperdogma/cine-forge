# Scout 008 — Storybook & Dossier delta 3

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-03-02
**Scope:** Changes since Scout 007 (2026-03-02 morning)
**Previous:** Scout 007 (2026-03-02, Partial)
**Status:** Complete

## Findings

### From Dossier

1. **Progress event emission (Story 028)** — HIGH value
   What: Structured `ProgressEvent` callbacks in the engine. `EventType` enum covers 7 discrete stages (pipeline_start, chunk_start, chunk_complete, extraction_complete, resolution_start, resolution_complete, pipeline_complete). Optional `on_progress` callback on Engine.__init__(). Thread-safe via `threading.Lock` for parallel chunk extraction. Each event carries structured `detail` dict (index, counts, timing). CLI wires to stderr for real-time output.
   Us: CineForge driver (`src/cine_forge/driver/engine.py`) has no structured progress emission. The UI's `OperationBanner` and `useLongRunningAction` hook are ready to consume progress signals, but the backend has nothing to emit them. Pipeline runs show spinner-only feedback — no per-stage granularity.
   Recommendation: Create story — requires defining event schema, wiring 5+ emission points into the driver, and bridging to the API layer (SSE or polling).

2. **Compound entity splitting (Story 040)** — MEDIUM value
   What: Pre-adjudication filter that decomposes "Alice and Bob" compound mentions into individual entities before scoring. Short-part guard prevents false splits (filters single-character fragments). Wired as a stage between extraction and adjudication. Impact: minor character recall 0.47→0.62 on Big Fish test corpus.
   Us: CineForge's `entity_discovery_v1` processes full screenplay text. Compound references likely occur ("ALICE and BOB enter"). No splitting stage currently. We don't have data on how often this causes misses.
   Recommendation: Conditional inline — adopt only if golden eval on a real screenplay shows compound-reference misses. Low priority until we have evidence.

3. **Evidence failure taxonomy (adversarial verification)** — MEDIUM value
   What: Dossier documented specific failure patterns found during adversarial golden verification: truncated quotes (quote cuts off mid-sentence), wrong-scene refs (evidence from different scene than claimed), compound facts (one evidence blob claims two facts), tangential text (only weakly supports the claim), mention_type confusion (cameo miscoded as supporting). Each pattern has a name and detection approach.
   Us: Our `benchmarks/golden/` has no VERIFICATION_REPORT.md files and no documented failure taxonomy. The `golden-build.md` runbook is sparse on what to actually look for.
   Recommendation: Inline — add failure taxonomy to `docs/runbooks/golden-build.md` as a "Common Failures" section.

4. **Relationship bidirectionality validator (adversarial verification)** — MEDIUM value
   What: Verification revealed that "complete" relationship sets must include bidirectional links: if A→child(B), then B→parent(A); all spouse pairs get both directions; sibling matrices get all pairs. Dossier's `scripts/fix_goldens.py` automated this (added 45 reciprocal relationships in one fixture).
   Us: CineForge's `benchmarks/golden/the-mariner-relationships.json` may have incomplete bidirectionality. No validator checks this. If a model produces the correct one-way link, it still fails scoring.
   Recommendation: Inline — add validation predicate to golden-build runbook and note to check bidirectionality when auditing relationship golden files.

### From Storybook

5. **Atmospheric login + frosted card (Story 033)** — MEDIUM value
   What: Login page with full-screen background image (day/night variants), frosted glass card overlay (`bg-white/50 dark:bg-slate-900/15 backdrop-blur-xl`), mobile-specific background-position shift to frame image correctly, heading color in light mode / gradient in dark mode.
   Us: CineForge has a simple auth page. The frosted glass pattern is CSS-minimal and gives a professional film-industry aesthetic without adding dependencies.
   Recommendation: Inline — add pattern to `AGENTS.md > UI Development Workflow` as "Atmospheric Auth Layout" reference. No immediate implementation needed.

6. **Date-grouped sidebar with dividers (Story 033)** — LOW-MEDIUM value
   What: `groupConversations()` helper buckets items by Today/Yesterday/This week/Older. Section dividers use `flex items-center gap-2` + `flex-1 border-t` on both sides with a centered label (`text-[10px] uppercase tracking-widest select-none`). Non-interactive dividers don't interfere with keyboard navigation.
   Us: CineForge sidebar shows projects. No grouping currently. The pattern is reusable for entity list grouping (scenes by act, characters by role type).
   Recommendation: Inline — add snippet to `AGENTS.md > UI Development Workflow` as "Grouped List Divider" pattern.

7. **Dual-mode color system (Story 034)** — MEDIUM value
   What: Tailwind v4 `@custom-variant dark (&:where(.dark, .dark *))` enables clean light/dark variants. Light palette anchored to warm parchment (`warm-50` through `warm-200`). All existing dark classes prefixed with `dark:` variant — no parallel CSS files. Contrast verified ≥ 4.5:1 both modes.
   Us: CineForge has a dark-only theme. If we ever add light mode, this is the proven pattern. Low urgency.
   Recommendation: Reference only — add note to AGENTS.md UI section. No implementation needed now.

8. **Story 037: Voice pause detection** — LOW value
   What: Luna AI detects mid-sentence pauses and waits before triggering response. Turn-taking specific to voice chat mode.
   Us: CineForge has no voice interface. Not applicable.
   Recommendation: Skip.

## Approved

- [x] 1. Progress event emission — Story 114 created (Draft, Medium priority)
- [x] triage-stories — Draft stories now first-class candidates (adopted inline)
- [ ] 3. Evidence failure taxonomy — add to `docs/runbooks/golden-build.md`
- [ ] 4. Relationship bidirectionality — add validation note to golden-build runbook
- [ ] 5. Atmospheric login pattern — add reference to AGENTS.md UI section
- [ ] 6. Date-grouped divider — add reference to AGENTS.md UI section

## Skipped / Rejected

- 2. Compound entity splitting — no evidence of need in CineForge data
- 7. Dual-mode color system — reference only, not needed now
- 8. Story 037 voice pause detection — voice-only, not applicable
