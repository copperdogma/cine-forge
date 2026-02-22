# Scout 001 — storybook-repo

**Source:** `/Users/cam/Documents/Projects/Storybook/storybook` (also https://github.com/copperdogma/storybook)
**Scouted:** 2026-02-22
**Scope:** AGENTS.md, skills, story patterns — full repo (first scout)
**Previous:** None
**Status:** Complete

## Context

Storybook was bootstrapped FROM CineForge's patterns (3 scout expeditions adopted CineForge's cross-CLI skills, scaffolding, and conventions). Since then, Storybook has evolved several patterns further — particularly the build-story workflow, story template, and spec decomposition tooling. This expedition identifies what evolved in Storybook that CineForge should adopt back.

## Findings

1. **Build-story 3-phase structure with human gate** — HIGH value
   What: Storybook restructured build-story into explicit phases: Phase 1 (Explore — read-only, no file writes), Phase 2 (Plan — writes a "## Plan" section to the story file, then presents to user for approval), Phase 3 (Implement — only after human gate). Key additions: "Exploration Notes" in work log, explicit "never write code before human gate" guardrail, separate static verification (10a) and runtime smoke test (10b) steps with "Never mark Done if runtime smoke test was skipped."
   Us: CineForge's build-story had 11 flat steps with no phase structure, no read-only enforcement, no written plan artifact, and no explicit human gate.
   Recommendation: **Adopt inline**

2. **Story template with Plan section** — HIGH value
   What: Storybook's story template includes a `## Plan` section ("Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers, definition of done"). This creates an auditable plan artifact that persists in the story file.
   Us: CineForge's template had no Plan section. Plans existed only in conversation context and were lost between sessions.
   Recommendation: **Adopt inline**

3. **`/decompose-spec` skill** — MEDIUM value
   What: Systematic pipeline: spec.md + ADRs → Feature Map (`docs/feature-map.md`) → Coverage Matrix (`docs/coverage.md`) → Story skeletons. Key concept: "Systems Own Stories" — a feature map system is NOT a story, it owns vertical-slice stories. Coverage matrix is append-only, tracks every spec item to a story ID.
   Us: CineForge has `docs/spec.md` and 66 stories but no feature map or coverage matrix. No systematic way to verify all spec items are tracked.
   Recommendation: **Adopt inline**

4. **`/webapp-testing` skill (Playwright)** — MEDIUM value
   What: Playwright-based web testing with `with_server.py` helper for server lifecycle management. Reconnaissance-then-action pattern (screenshot → identify selectors → act). Adapted from Anthropic's skills repo.
   Us: CineForge uses Chrome MCP for browser verification but had no Playwright-based automated testing.
   Recommendation: **Adopt inline**

5. **`/frontend-design` skill** — LOW value
   What: Design identity guidelines (typography, color, motion, spatial composition) with Storybook-specific aesthetics.
   Us: CineForge has comprehensive UI Development Workflow in AGENTS.md already.
   Recommendation: **Skip**

6. **Explicit session protocol** — LOW value
   What: Standalone start/end checklist in AGENTS.md.
   Us: Already covered by build-story skill steps.
   Recommendation: **Skip**

7. **AGENTS.md 300-line mandate** — LOW value
   What: Keep AGENTS.md under 300 lines.
   Us: CineForge's ~380-line AGENTS.md density is intentional (eval catalog, deployment, worktrees).
   Recommendation: **Skip**

## Approved

- [x] 1. Build-story 3-phase structure — Adopted
- [x] 2. Story template Plan section — Adopted
- [x] 3. `/decompose-spec` skill — Adopted
- [x] 4. `/webapp-testing` skill — Adopted

## Evidence

1. **Build-story**: `.agents/skills/build-story/SKILL.md` rewritten with Phase 1 (Explore, steps 1-5), Phase 2 (Plan, steps 6-8 with human gate), Phase 3 (Implement, steps 9-14). Runtime smoke test (10b) with hard guardrail. 7 guardrails including "Never write implementation code before human gate."
2. **Story template**: `.agents/skills/create-story/templates/story.md` — `## Plan` section added between `## Notes` and `## Work Log`.
3. **Decompose-spec**: `.agents/skills/decompose-spec/SKILL.md` created with CineForge-adapted examples. Frontmatter: `user-invocable: true`. Appears in skill listing.
4. **Webapp-testing**: `.agents/skills/webapp-testing/SKILL.md` created with CineForge ports (8642/5188). `scripts/with_server.py` helper copied. Not user-invocable (toolkit skill). Appears in skill listing.
5. **Sync**: `scripts/sync-agent-skills.sh` ran successfully — 16 skills synced (Gemini wrappers updated for new user-invocable skills).

## Skipped / Rejected

- 5. `/frontend-design` skill — CineForge already has project-specific UI workflow in AGENTS.md
- 6. Explicit session protocol — Already covered by build-story skill
- 7. AGENTS.md 300-line mandate — CineForge's density is intentional
