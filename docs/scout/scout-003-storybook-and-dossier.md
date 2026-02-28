# Scout 003 — Storybook & Dossier (delta)

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-02-28
**Scope:** Changes since last scouts (Storybook: 2026-02-22, Dossier: 2026-02-26)
**Previous:** Scout 001 (Storybook, 2026-02-22), Scout 002 (Dossier, 2026-02-26)
**Status:** Complete

## Findings

### From Storybook (18 commits since 2026-02-22)

1. **`/improve-skill` retrospective skill** — HIGH value
   What: After running any skill, invoke `/improve-skill` to evaluate how well the skill's instructions held up. Reads the full interaction, identifies where instructions fell short, proposes generic improvements (must be cross-project portable), and applies approved ones.
   Us: No equivalent. Skills only improved when we manually noticed failures.
   Recommendation: **Adopt inline**

2. **"Fold into existing story" + "What if we don't do this?" in `/triage-inbox`** — HIGH value
   What: Before creating a new story from an inbox item, first check existing stories for a natural home. Challenge question gates story creation.
   Us: CineForge's `/triage-inbox` lacked both patterns. Items reflexively became stories.
   Recommendation: **Adopt inline**

3. **Delete-not-archive inbox policy** — MEDIUM value
   What: Once an inbox item lands in a story/ADR/spec, delete it from `docs/inbox.md`. The inbox is a queue, not an archive.
   Us: CineForge had a "Triaged" section that accumulated noise.
   Recommendation: **Adopt inline**

4. **AI-as-Tester philosophy** — HIGH value
   What: AI agents default to deterministic scripts even when the problem requires judgment. When verifying AI persona behavior, have a conversation personally. Subagent pattern for focused probes.
   Us: CineForge roles tested only via structural validation. No philosophy for qualitative testing.
   Recommendation: **Adopt inline**

5. **ADR Integration Checklist + "Settled — DO NOT Suggest Alternatives" marker** — MEDIUM value
   What: Every ADR has integration checklist. Key decisions marked "Settled" to prevent relitigating.
   Us: CineForge ADRs lacked both.
   Recommendation: **Adopt inline**

6. **Promptfoo multi-turn conversational evals** — MEDIUM value
   What: Uses promptfoo `_conversation` + `conversationId` for multi-turn eval test cases.
   Us: All 9 CineForge evals are single-turn. Roles are conversational.
   Recommendation: **Create story**

7. **AGENTS.md 300-line cap with runbook extraction** — MEDIUM value
   What: Keep AGENTS.md compact, move detail to docs/runbooks.
   Us: AGENTS.md is 545+ lines.
   Recommendation: **Create story**

### From Dossier (18 commits since 2026-02-26)

8. **Tiered quality metrics (ImportanceTier + tiered_recall)** — HIGH value
   What: Per-tier recall thresholds instead of flat metrics. Revealed 0.67 flat recall = 1.00 major + 0.93 supporting.
   Us: CineForge uses flat metrics. A 0.82 score doesn't tell us if we're missing protagonists or extras.
   Recommendation: **Create story**

9. **Parallel chunk extraction via ThreadPoolExecutor** — HIGH value
   What: 28-42x speedup via concurrent API calls on independent chunks.
   Us: CineForge module execution is sequential within stages.
   Recommendation: **Create story**

10. **Eval mismatch investigation mandate** — HIGH value
    What: Every eval mismatch classified as model-wrong, golden-wrong, or ambiguous before story closes.
    Us: CineForge's validate/build-story/mark-story-done didn't gate on this.
    Recommendation: **Adopt inline**

11. **Disk-backed chunk-level extraction cache** — MEDIUM value
    What: SHA256 cache key per chunk. Sub-second reruns when only downstream code changes.
    Us: CineForge has driver-level caching but not inner-loop chunk-level caching.
    Recommendation: **Create story**

## Approved

### Inline (adopted)

- [x] 1. `/improve-skill` skill — Created `.agents/skills/improve-skill/SKILL.md`, synced (27 skills)
- [x] 2. Fold + challenge patterns in `/triage-inbox` — Updated SKILL.md with "What if we don't do this?" and "Check for existing homes" steps
- [x] 3. Delete-not-archive inbox policy — Updated SKILL.md step 5, cleaned out Triaged section from `docs/inbox.md`
- [x] 4. AI-as-Tester philosophy — Added to AGENTS.md General Agent Engineering Principles
- [x] 5. ADR Integration Checklist + Settled marker — Updated `.agents/skills/create-adr/templates/adr.md`
- [x] 10. Eval mismatch investigation mandate — Added to AGENTS.md Definition of Done #5, updated `/validate` (step 5b), `/build-story` (step 10b), `/mark-story-done` (validation checkpoint)

### Stories created (deferred)

- [x] 6. → Story 102 (Promptfoo Multi-Turn Conversational Evals) — Draft
- [x] 7. → Story 103 (AGENTS.md Runbook Extraction) — Draft
- [x] 8. → Story 104 (Tiered Quality Metrics for Eval Scoring) — Draft
- [x] 9. → Story 105 (Parallel Chunk Extraction via ThreadPoolExecutor) — Draft
- [x] 11. → Story 106 (Disk-Backed Chunk-Level Extraction Cache) — Draft

## Skipped / Rejected

(None — all findings either adopted or deferred to stories)
