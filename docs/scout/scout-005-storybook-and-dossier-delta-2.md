# Scout 005 — Storybook & Dossier (delta 2)

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-03-01
**Scope:** Changes since Scout 004 (2026-02-28)
**Previous:** Scout 004 (Storybook & Dossier delta, 2026-02-28)
**Status:** Complete

## Findings

### From Dossier

1. **`/verify-eval` skill — structured mismatch investigation** — HIGH value
   What: New 5-phase skill for investigating every eval mismatch: enumerate in table format, classify each as model-wrong/golden-wrong/ambiguous, apply golden fixes, re-run eval, document raw→verified score delta. Hard boundary: fixes goldens only, code bugs go back to the calling story. Key principle: "Raw eval scores are meaningless. Only verified scores count."
   Us: CineForge inlines the mismatch classification protocol in build-story 11b, validate 5b, and mark-story-done. No dedicated skill. Missing: table format, user-consultation thresholds (>5% entity change), raw-vs-verified reporting, scope boundary.
   Recommendation: **Adopt inline** — create the skill, then wire into existing skills

2. **"Eval First at Every Scale" — eval gate before approach selection** — HIGH value
   What: Broadened AGENTS.md mandate: eval-first applies to individual story tasks, not just pipeline stages. Before choosing between AI and code, measure both. Root cause: Story 035 pre-decided "pure code" without measuring the AI alternative.
   Us: CineForge has pipeline-level "Baseline = Best Model Only" and build-story step 7 "AI-first check" as a question-prompt. Not a gate with measured baselines. Doesn't require creating an eval before choosing an approach.
   Recommendation: **Adopt inline** — update build-story step 7

3. **"AI Considerations" → "Approach Evaluation" in story template** — HIGH value
   What: Story template section renamed and expanded. Instead of "Can an LLM call solve this?" (binary question), lists candidate approaches (AI-only, hybrid, pure code) and identifies what eval would distinguish them. Prevents pre-deciding approach without evidence.
   Us: CineForge uses "AI Considerations" with the old binary framing.
   Recommendation: **Adopt inline** — update create-story SKILL.md + story template

4. **`create-story` convention: add `/verify-eval` task to eval-touching stories** — MEDIUM value
   What: New convention: "If the story will involve running evals, add a task: 'Run /verify-eval after eval — classify all mismatches, fix golden if needed, document verified scores.'"
   Us: CineForge has no equivalent. Eval investigation is implicit.
   Recommendation: **Adopt inline** — one bullet in create-story conventions (after #1 lands)

5. **`build-story` guardrail: only verified scores determine ACs** — HIGH value
   What: New guardrail in step 11: "Re-assess acceptance criteria against verified scores. Golden fixes from /verify-eval change the real scores. Only verified scores determine whether acceptance criteria are met."
   Us: CineForge's build-story never distinguishes raw vs. verified scores.
   Recommendation: **Adopt inline** — one sentence in build-story step 11b

6. **`mark-story-done` checklist: /verify-eval report required** — MEDIUM value
   What: Updated checklist: "If evals were run: /verify-eval report exists in work log." Updated guardrail: "Never mark Done if evals were run without a /verify-eval report."
   Us: CineForge requires mismatch classification but not a formal report artifact.
   Recommendation: **Adopt inline** (after #1 lands)

7. **AGENTS.md Lesson: eval-first for implementation decisions** — HIGH value
   What: "Story 035 pre-decided 'pure code' for relational descriptor resolution without measuring the AI alternative. Five deterministic resolvers were planned when a single LLM judge call handles all patterns."
   Us: CineForge has related lessons but not this specific one about approach pre-decision.
   Recommendation: **Adopt inline** — add to Lessons Learned

8. **AGENTS.md Pitfall: LLM resolution degrades from synthetic to real data** — MEDIUM value
   What: "Story 035's relational descriptor resolution achieved P=1.00, R=0.91 on a 16-entity synthetic fixture but struggled on Big Fish's 89-entity list. Synthetic eval passes ≠ production readiness."
   Us: CineForge evaluates on The Mariner (small cast) but production screenplays have 40-80 characters. This is a directly relevant gotcha.
   Recommendation: **Adopt inline** — add to Known Pitfalls

### From Storybook

9. **System-order insertion in `/create-story`** — LOW value
   What: "Insert the row in System order (not at the bottom). IDs will be out of numeric order — that is expected and correct."
   Us: CineForge says "Add a row to the table" without ordering guidance.
   Recommendation: **Adopt inline** — one sentence

10. **`/triage-stories` Arguments section** — LOW value
    What: Moved single-story evaluation mode from buried guardrail to a proper `## Arguments` section with description.
    Us: CineForge has this in a guardrail at the bottom: "If the user passes a story ID as an argument, evaluate that specific story's readiness."
    Recommendation: **Adopt inline** — restructure into dedicated section

11. **`golden-build.md` runbook with enforcement cross-references** — MEDIUM value
    What: Dossier has a runbook documenting golden fixture build process, semantic review phases, failure patterns, and cross-references to every lifecycle skill that enforces the protocol.
    Us: CineForge has no golden-build runbook. The process is described inline in AGENTS.md.
    Recommendation: **Create story** — meaningful runbook + enforcement wiring

## Approved

### Inline (adopted)

- [x] 1. `/verify-eval` skill — Created `.agents/skills/verify-eval/SKILL.md` with 5-phase protocol adapted for CineForge's promptfoo eval structure
- [x] 2. Eval-first approach gate — Replaced build-story step 7 "AI-first check" with "Eval-first approach gate" requiring baseline measurement and candidate enumeration
- [x] 3. "Approach Evaluation" template — Renamed "AI Considerations" to "Approach Evaluation" in create-story SKILL.md and story template with AI-only/Hybrid/Pure code/Eval subsections
- [x] 4. `/verify-eval` convention in create-story — Added bullet requiring `/verify-eval` task for eval-touching stories
- [x] 5. Verified scores guardrail — Added "Re-assess acceptance criteria against verified scores" to build-story step 11b
- [x] 6. `/verify-eval` report in mark-story-done — Updated checklist and guardrails to require `/verify-eval` report
- [x] 7. AGENTS.md lesson — Added "Eval-first applies to implementation decisions" to Lessons Learned
- [x] 8. AGENTS.md pitfall — Added "LLM resolution degrades from synthetic to real data" to Known Pitfalls
- [x] 9. System-order insertion — Added ordering guidance to create-story step 3
- [x] 10. Arguments section — Added `## Arguments` section to triage-stories with `[story-number]` parameter

### Deferred to story

- [x] 11. Golden-build runbook → Story 109

All items verified: skill sync successful (31 skills), all file changes confirmed by re-read.

## Skipped / Rejected

(None — all findings adopted)
