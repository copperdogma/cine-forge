# Scout 002 — Dossier AI/Project Infrastructure

**Source:** `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-02-26
**Scope:** Full repo — AI/project infrastructure, ideal-first methodology, setup system, skills, runbooks, eval patterns
**Previous:** None (first scout of dossier)
**Status:** Complete

## Context

Dossier is a standalone Python library for extracting people, profiles, and relationships from text. It was bootstrapped using a new "ideal-first" methodology that formalizes how to think about requirements, compromises, and AI capabilities. The methodology is fully portable — designed to be applied to any project.

## Findings

### A. The Ideal-First Methodology (core innovation)

1. **`docs/ideal.md` — The North Star Document** — HIGH value
   What: A vivid, ≤1-page narrative describing what the system should be with ZERO limitations. The Ideal is the requirements. The spec is the compromises against it. The Ideal rarely changes; the spec shrinks over time as limitations are resolved.
   Us: CineForge has `docs/spec.md` (traditional requirements) but no Ideal. No north star that survives beyond current limitations.
   Recommendation: **Create story** — Run `/retrofit-ideal` pattern to create `docs/ideal.md` for CineForge. This is the single biggest methodology upgrade.

2. **Spec as organized compromises with detection mechanisms** — HIGH value
   What: Each compromise in `docs/spec.md` has: The Ideal / The Compromise / The Limitation / Limitation Type / Detection Mechanism / When It Resolves. AI compromises have runnable evals as detection — when the eval passes, delete the compromise. Limitation taxonomy: AI capability, Ecosystem, Legal, Physics/math, Human nature.
   Us: CineForge's `docs/spec.md` is a flat requirements doc. No compromise structure, no detection mechanisms, no lifecycle.
   Recommendation: **Create story** — Restructure spec.md. Large effort (spec is 168 sections). Could be done incrementally — start with the AI-capability compromises since those have the shortest lifecycle.

3. **"Baseline = Best Model Only" principle** — HIGH value
   What: Never conclude "AI can't do this" from a cheap model's failure. Always test SOTA first. Cheaper models tested AFTER capability ceiling is established. Stated as the single most expensive mistake in eval-first development.
   Us: CineForge already does this in benchmarking (Opus 4.6 as judge, test all providers). But it's not stated as a core principle in AGENTS.md.
   Recommendation: **Adopt inline** — Add to AGENTS.md principles. Small edit.

4. **`docs/prompts/ideal-app.md` — Reusable generator prompt** — MEDIUM value
   What: A detailed prompt template for creating an Ideal App document for any project. Guides the Socratic conversation to extract the north star. Includes the full limitation taxonomy and compromise structure.
   Us: No equivalent. Would be useful when running the retrofit.
   Recommendation: **Adopt inline** — Copy to `docs/prompts/` (possibly adapt for CineForge context). Used as input to the retrofit story.

### B. Skills & Process Improvements

5. **`/retrofit-ideal` skill** — HIGH value
   What: Skill designed specifically for existing projects. Reads current spec, AGENTS.md, stories, and codebase to derive what the Ideal should be. Creates `docs/ideal.md` without starting over. Designed for projects like CineForge that have stories and code but no formalized Ideal.
   Us: Don't have this skill.
   Recommendation: **Adopt inline** — Copy skill from dossier. It's a prompt, not code.

6. **`/reflect` skill** — HIGH value
   What: Read-only advisory tool that traces implications of any change across ideal.md, spec.md, stories, and evals. "If I change X, what else is affected?" Prevents cascade surprises.
   Us: Don't have this skill. Currently rely on manual impact analysis in `/build-story`.
   Recommendation: **Adopt inline** — Copy skill from dossier.

7. **Draft vs Pending story status** — MEDIUM value
   What: Stories start as Draft (scoped, has goal, but no detailed ACs/tasks). Must be explicitly promoted to Pending before building. Prevents premature execution of half-baked stories.
   Us: CineForge stories go straight to Pending or To Do. Some stories in the backlog have thin ACs because they were created early.
   Recommendation: **Adopt inline** — Add Draft status to story conventions in AGENTS.md. Update `/create-story` template.

8. **Ideal alignment in existing skills** — MEDIUM value
   What: Multiple skills reference ideal.md: `/validate` caps grade at C if evals fail; `/triage-stories` ranks by Ideal alignment; `/build-story` reads ideal.md first in Phase 1; `/check-in-diff` flags deleted evals; `/scout` compares against ideal.md.
   Us: Our skills don't reference an Ideal (because it doesn't exist yet).
   Recommendation: **Defer** — Update skills AFTER ideal.md exists (depends on item 1).

9. **`skills-sync` and `skills-check` Makefile targets** — MEDIUM value
   What: `make skills-sync` runs `scripts/sync-agent-skills.sh`. `make skills-check` runs it with `--check` flag for CI verification. Ensures skill symlinks and Gemini wrappers stay consistent.
   Us: CineForge has `scripts/sync-agent-skills.sh` but no Makefile targets for it.
   Recommendation: **Adopt inline** — Add two lines to Makefile.

10. **Story template with Spec Refs and AI Considerations** — MEDIUM value
    What: Story template includes `**Spec Refs**:` field linking to specific compromises, and a required `## AI Considerations` section asking "Can an LLM call solve this?" before writing complex code.
    Us: CineForge stories don't trace to spec sections. AI-first check is in `/build-story` Phase 2 but not in the story template itself.
    Recommendation: **Adopt inline** — Update `create-story` template. Small edit.

### C. Runbooks & Documentation Patterns

11. **Runbook system with conventions** — MEDIUM value
    What: `docs/runbooks/` with structured format: Context, Prerequisites, step-by-step tagged `[script]` (deterministic) or `[judgment]` (requires reasoning), three-tier boundaries (Always do / Ask first / Never do), Troubleshooting, Lessons learned. Rule: every runbook has a corresponding skill; every skill with 3+ procedural steps has a runbook.
    Us: CineForge has one runbook (`docs/runbooks/browser-automation-and-mcp.md`) but no conventions or skill↔runbook rule.
    Recommendation: **Adopt inline** — Add runbook conventions to AGENTS.md. Don't retroactively create runbooks — apply the convention going forward.

12. **Baseline results document** — MEDIUM value
    What: `evals/baseline-results.md` — structured capture of what SOTA can and can't do, organized by scale tier (toy/small/standard). Documents failure modes at each scale with specific evidence.
    Us: CineForge has the eval catalog in AGENTS.md and results in `benchmarks/results/` but no structured "what are the current AI limitations" doc.
    Recommendation: **Adopt inline** — Could be useful. But CineForge's eval setup is different (promptfoo-based, results in JSON). Lower priority.

13. **Scale-tiered golden references** — LOW value
    What: Golden references at three tiers: Toy (synthetic, for iteration), Standard (real data, for acceptance), Aspirational (larger scale, for detection of new capabilities).
    Us: CineForge has golden references but they're all one tier (real data from The Mariner). We don't have synthetic or aspirational tiers.
    Recommendation: **Skip** — CineForge's single-tier approach works. The Mariner is both iteration and acceptance.

14. **Feature map + coverage matrix pattern** — LOW value
    What: `docs/feature-map.md` decomposes spec into 13 feature systems. `docs/coverage.md` traces 78 requirements to stories. Ensures nothing falls through cracks.
    Us: CineForge has `docs/stories.md` with a spec coverage map table. Less formal but functional.
    Recommendation: **Skip** — Current approach is adequate.

15. **Golden build runbook (failure patterns)** — LOW value
    What: Detailed taxonomy of 5 golden reference failure patterns (truncated quotes, wrong-scene evidence, compound facts, tangential evidence, mention type confusion). Scale characteristics table.
    Us: CineForge golden refs are simpler (structured extraction outputs, not evidence-backed profiles). Different domain.
    Recommendation: **Skip** — Domain-specific to dossier's extraction problem.

## Approved

Items 3, 4, 5, 6, 7, 9, 10, 11 approved for inline adoption.

| # | Item | Evidence |
|---|------|----------|
| 3 | "Baseline = Best Model Only" principle | Added to `AGENTS.md` under General Agent Engineering Principles |
| 4 | `docs/prompts/ideal-app.md` generator prompt | Written to `docs/prompts/ideal-app.md` (225 lines) |
| 5 | `/retrofit-ideal` skill | Written to `.agents/skills/retrofit-ideal/SKILL.md` (169 lines), synced to `.claude/skills/` and `.gemini/commands/` |
| 6 | `/reflect` skill | Written to `.agents/skills/reflect/SKILL.md` (102 lines), synced to `.claude/skills/` and `.gemini/commands/` |
| 7 | Draft vs Pending story status | Added Story Conventions section to `AGENTS.md`, updated `create-story` template default status to Draft |
| 9 | `skills-sync` / `skills-check` Makefile targets | Already existed in Makefile — no change needed |
| 10 | Story template Spec Refs + AI Considerations | Already existed in `.agents/skills/create-story/templates/story.md` — no change needed |
| 11 | Runbook conventions | Added Runbook Conventions section to `AGENTS.md` with `[script]`/`[judgment]` tagging and skill↔runbook rule |

Additionally, the full setup-* skill chain was adopted:

| # | Item | Evidence |
|---|------|----------|
| 16 | `/setup-env-ai` skill | Written to `.agents/skills/setup-env-ai/SKILL.md` |
| 17 | `/setup-env-dev` skill | Written to `.agents/skills/setup-env-dev/SKILL.md` |
| 18 | `/setup-evals` skill | Written to `.agents/skills/setup-evals/SKILL.md` |
| 19 | `/setup-golden` skill | Written to `.agents/skills/setup-golden/SKILL.md` |
| 20 | `/setup-ideal` skill | Written to `.agents/skills/setup-ideal/SKILL.md` |
| 21 | `/setup-spec` skill | Written to `.agents/skills/setup-spec/SKILL.md` |
| 22 | `/setup-stories` skill | Written to `.agents/skills/setup-stories/SKILL.md` |

All skills verified: `skills-check: OK (26 skills, 26 gemini wrappers)`

## Deferred

| # | Item | Reason |
|---|------|--------|
| 1 | `docs/ideal.md` — The North Star | Story-sized — run `/retrofit-ideal` to create for CineForge |
| 2 | Spec as organized compromises | Story-sized — restructure `docs/spec.md` with limitation types and detection mechanisms |
| 8 | Ideal alignment in existing skills | Depends on items 1+2 (ideal.md must exist first) |

## Skipped

| # | Item | Reason |
|---|------|--------|
| 12 | Baseline results document | CineForge uses promptfoo JSON results + AGENTS.md eval catalog — different approach, adequate |
| 13 | Scale-tiered golden references | CineForge's single-tier (The Mariner) approach works for current scope |
| 14 | Feature map + coverage matrix | `docs/stories.md` spec coverage map is adequate |
| 15 | Golden build runbook (failure patterns) | Domain-specific to dossier's evidence-backed profile extraction |
