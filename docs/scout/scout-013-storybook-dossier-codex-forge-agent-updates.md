# Scout 013 — storybook-dossier-codex-forge-agent-updates

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`, `/Users/cam/Documents/Projects/codex-forge`
**Scouted:** 2026-03-13
**Scope:** Changes since Scout 009 for Storybook/Dossier and since Scout 012 for codex-forge, limited to AGENTS, skills, runbooks, and agent-process guidance
**Previous:** Scout 009 (Storybook & Dossier delta 4, 2026-03-03) and Scout 012 (codex-forge agent updates, 2026-03-13)
**Status:** Complete

## Findings

1. **`/build-story` should explicitly absorb small, coherent scope deltas instead of punting them as "out of scope"** — HIGH value
   What: Storybook and codex-forge added a scope-coherence rule: if exploration uncovers small, tightly coupled work that is necessary to satisfy the story goal, expand the current story inline and update the story file/work log. Larger deltas should be surfaced as a recommended scope expansion for user approval, not silently absorbed or silently split out.
   Us: CineForge's [`build-story`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/build-story/SKILL.md) does strong exploration and planning, but it does not tell the agent what to do when necessary adjacent work appears. That creates needless "that's another story" churn or half-fixes.
   Recommendation: **Adopt inline** — add scope-coherence guidance to `AGENTS.md` and `/build-story`; optionally add relative effort labels (`XS`..`XL`) for scope-expansion recommendations instead of human time estimates.

2. **Story closure should end with a firm disposition, not just a blocker list** — HIGH value
   What: codex-forge and Storybook now require `/mark-story-done` to recommend exactly one of `Close now`, `Rescope then close`, `Keep open`, or `Mark blocked`. When the right answer is `Rescope then close`, the skill must propose the exact edits first. Storybook also tightened `/validate` so follow-up stories do not leave the current story in an ambiguous "not done" limbo.
   Us: CineForge's [`mark-story-done`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/mark-story-done/SKILL.md) still says "If not complete, stop and list blockers." [`validate`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/validate/SKILL.md) gives next steps but no single closure recommendation.
   Recommendation: **Adopt inline** — update `/mark-story-done` and `/validate` so incomplete stories always get one explicit disposition plus concrete next edits.

3. **`/scout` should treat broad explicit inline authorization as approval for the recommended inline items** — MEDIUM value
   What: Dossier and Storybook updated `/scout` so replies like "port everything relevant" or "pull the worthwhile bits" count as approval for the inline items the scout explicitly recommended, while still requiring the scout doc to record what was adopted, adapted, and skipped.
   Us: CineForge's [`scout`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/scout/SKILL.md) only documents numbered approval patterns (`yes`, item numbers, `story for X`). Broad approval language is common in practice but currently unspecified.
   Recommendation: **Adopt inline** — this is a small skill-only clarification that reduces unnecessary permission back-and-forth without weakening the approval guardrail.

4. **Compromise/detection evals need explicit "expected fail" semantics in AGENTS** — HIGH value
   What: Dossier added a clear rule for capability-detector evals: red results are acceptable process-wise when the harness ran correctly, mismatches were classified, and runtime impact was recorded. Only runtime-blocking outcomes or a story whose goal is to remove that compromise should block closure.
   Us: CineForge has compromise gates in [`docs/spec.md`](/Users/cam/Documents/Projects/cine-forge/docs/spec.md), a central registry in [`docs/evals/registry.yaml`](/Users/cam/Documents/Projects/cine-forge/docs/evals/registry.yaml), and DoD language requiring mismatch classification, but no explicit guidance for when a still-red detector eval should or should not block a story. That leaves room for agents to treat every red capability detector as a failure to ship.
   Recommendation: **Adopt inline** — add a CineForge-specific "expected-fail semantics" note to `AGENTS.md` and reference it from lifecycle skills if needed.

5. **A short AGENTS "working norms" block would make day-to-day agent behavior more consistent** — MEDIUM value
   What: Dossier added a compact working-norms section: keep the work log live, make impact-first progress notes, debug from artifacts before editing code, and reuse existing working patterns before inventing new helpers.
   Us: CineForge already expresses most of this implicitly across AGENTS, skills, and project culture, but not in one concise operational block. That matters for new skills, cross-CLI agents, and future syncs where the high-level mandates are already crowded.
   Recommendation: **Adopt inline** — port an adapted version into `AGENTS.md` without duplicating broader mandates already covered elsewhere.

6. **Cheap eval-gap diagnosis should likely be a separate skill from expensive eval execution** — MEDIUM value
   What: Dossier split "diagnose the next quality gap from existing benchmark data" from "actually run fresh benchmarks." The read-only diagnosis pass checks score staleness, inspects existing artifacts, and proposes the next story; benchmark execution stays in `/refresh-model-evals` or story verification.
   Us: CineForge has `/improve-eval`, `/verify-eval`, `scripts/check-compromises.py`, and the registry, but nothing that cheaply answers "which eval or compromise gap should we attack next?" without immediately running promptfoo again. The concept fits, but it needs CineForge-specific design because our eval landscape is broader than Dossier's extraction loop.
   Recommendation: **Create story** — useful, but bigger than an inline wording tweak.

7. **Most March 12-13 Storybook/Dossier/codex-forge agent-sync changes are already in CineForge** — LOW value
   What: The other repos added `codebase-improvement-scout`, worktree landing runbooks, Draft/Pending clarity in `/triage-stories`, stronger `Where to verify` guidance, and scout-history/bootstrap improvements.
   Us: CineForge already has these patterns in [`AGENTS.md`](/Users/cam/Documents/Projects/cine-forge/AGENTS.md), [`check-in-worktree-landing.md`](/Users/cam/Documents/Projects/cine-forge/docs/runbooks/check-in-worktree-landing.md), [`codebase-improvement-scout`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/codebase-improvement-scout/SKILL.md), [`triage-stories`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/triage-stories/SKILL.md), and [`scout`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/scout/SKILL.md).
   Recommendation: **Skip** — no value in bulk-porting already-landed syncs.

8. **Bulk-porting codex-forge's current `/validate` rewrite would be a regression for CineForge** — LOW value
   What: codex-forge's March 13 `/validate` rewrite moved toward a generic graded review template and away from its earlier explicit lifecycle handoff structure.
   Us: CineForge's current [`validate`](/Users/cam/Documents/Projects/cine-forge/.agents/skills/validate/SKILL.md) is more repo-specific and better aligned with our story/eval/browser verification workflow.
   Recommendation: **Skip** — steal the closure-disposition idea only, not the full template.

## Approved

- [x] 1. Scope-coherence rule in `AGENTS.md` + `/build-story` — Adopted. Evidence: `AGENTS.md` now defines `Coherent Scope Expansion` and relative-effort guidance; `.agents/skills/build-story/SKILL.md` now adds a scope-coherence check plus plan/human-gate instructions for folded vs recommended scope expansion.
- [x] 2. Closure dispositions in `/mark-story-done` + `/validate` — Adopted. Evidence: `.agents/skills/mark-story-done/SKILL.md` and `.agents/skills/validate/SKILL.md` now require a single closure recommendation (`Close now`, `Rescope then close`, `Keep open`, `Mark blocked`) instead of stopping at blocker lists.
- [x] 3. Broad explicit inline approval in `/scout` — Adopted. Evidence: `.agents/skills/scout/SKILL.md` now treats broad explicit approval language as approval for the explicitly recommended inline items.
- [x] 4. Expected-fail semantics for compromise/detection evals — Adopted. Evidence: `AGENTS.md` now adds an `Expected-Fail Semantics` subsection and updates Definition of Done; `.agents/skills/validate/SKILL.md` and `.agents/skills/mark-story-done/SKILL.md` now call out `runtime-blocking` vs `non-runtime-blocking` handling for remaining detector failures.
- [x] 5. AGENTS working norms block — Adopted. Evidence: `AGENTS.md` now includes a `Working Norms` section covering live work logs, impact-first reporting, artifact-first debugging, and reuse of proven local patterns.
- [x] 6. Inline eval-gap diagnosis workflow — Adopted inline per user request. Evidence: new `.agents/skills/triage-evals/SKILL.md`, `docs/runbooks/triage-evals.md`, `docs/evals/README.md` mention, `AGENTS.md` runbook/eval references, and generated `.gemini/commands/triage-evals.toml`.

## Skipped / Rejected

- 7. Bulk-port already-landed Storybook/Dossier/codex-forge sync items — already present in CineForge
- 8. Bulk-port codex-forge's generic `/validate` rewrite — weaker than CineForge's current repo-specific validation flow
