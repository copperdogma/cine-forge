# Scout 012 — codex-forge-agent-updates

**Source:** /Users/cam/Documents/Projects/codex-forge
**Scouted:** 2026-03-13
**Scope:** AGENTS.md plus story-lifecycle skills and templates, with emphasis on AI approach scoping, story status handling, and planning prompts
**Previous:** None
**Status:** Complete

## Findings

1. **`/create-story` should default to `Draft` explicitly and stop implying new stories are `Pending`** — HIGH value
   What: codex-forge's `create-story` skill makes the default `Draft` status explicit and aligns the example story-index row with that default.
   Us: CineForge's story conventions already say "use Draft liberally" and `/build-story` refuses Draft stories, but `.agents/skills/create-story/SKILL.md` still implies a `Pending` row example and never states the default clearly.
   Recommendation: Adopt inline.

2. **Story templates should ask the simplification-baseline question up front** — HIGH value
   What: codex-forge added a dedicated "Simplification baseline" prompt to story planning so new logic is forced to answer "Can a single LLM call already do this?" before the repo builds machinery around it.
   Us: CineForge's `build-story` already enforces the eval-first gate, but the story template does not prompt authors to capture that baseline in the story itself.
   Recommendation: Adopt inline.

3. **The story template should precompute agent-tooling and eval follow-through tasks** — HIGH value
   What: codex-forge's story template explicitly reminds authors to add `make skills-check` when agent tooling changes and `/verify-eval` + registry updates when evals or goldens move.
   Us: CineForge's lifecycle skills require those checks, but the story template still nudges authors mostly toward backend/UI checks only.
   Recommendation: Adopt inline, using CineForge's existing commands.

4. **CineForge has a local Draft/Pending contradiction in `/triage-stories`** — HIGH value
   What: While comparing story-scope guidance, the scout surfaced that CineForge's `triage-stories` skill says `/build-story` will flesh out Draft stories.
   Us: That is false in this repo. `AGENTS.md` and `/build-story` both require Draft stories to be promoted to `Pending` before build execution.
   Recommendation: Adopt inline as a local cleanup discovered during the scout.

5. **Broader "Decision Refs" wording from codex-forge should not be ported wholesale** — MEDIUM value
   What: codex-forge generalizes story decision context from ADR-specific references to a broader runbooks/scout/notes bucket.
   Us: CineForge intentionally has stronger ADR discipline (`docs/decisions/` + `docs/design/`). Renaming the canonical story field right now would create mixed conventions across existing stories and lifecycle skills.
   Recommendation: Skip the field rename. Only borrow the useful reminder to cite supporting runbooks/scout docs when they materially constrain execution.

6. **Most codex-forge AGENTS and lifecycle wording is codex-forge-specific or weaker than CineForge's current version** — MEDIUM value
   What: codex-forge's AGENTS and some skill text swap CineForge's ADR-specific checks, repo-specific validation commands, and UI/browser requirements for codex-forge's pipeline-centric equivalents.
   Us: CineForge is already ahead here. Blindly porting those blocks would regress validation rigor or erase CineForge-specific constraints.
   Recommendation: Skip.

## Approved

- [x] 1. `create-story` Draft-default alignment — Adopted. Evidence: `.agents/skills/create-story/SKILL.md` now states `Draft` as the default and uses a Draft row example in `docs/stories.md`.
- [x] 2. Simplification-baseline prompt in story creation — Adopted. Evidence: `.agents/skills/create-story/SKILL.md` and `.agents/skills/create-story/templates/story.md` now require a "Simplification baseline" entry.
- [x] 3. Story-template prompts for `make skills-check` and eval follow-through — Adopted. Evidence: `.agents/skills/create-story/templates/story.md` now adds explicit tasks for `make skills-check` and `/verify-eval` + registry updates.
- [x] 4. `/triage-stories` Draft/Pending consistency fix — Adopted. Evidence: `.agents/skills/triage-stories/SKILL.md` now says Draft stories may be recommended but must be promoted to `Pending` before `/build-story`.

## Skipped / Rejected

- 5. Rename `ADR Refs` to `Decision Refs` — Skip. Useful idea, wrong timing for CineForge's current conventions.
- 6. Bulk-port codex-forge AGENTS / lifecycle wording — Skip. Mostly already present here or weaker than CineForge's existing repo-specific rules.
