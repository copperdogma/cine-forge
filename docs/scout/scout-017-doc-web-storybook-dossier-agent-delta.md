# Scout 017 — doc-web-storybook-dossier-agent-delta

**Sources:** `/Users/cam/Documents/Projects/doc-web`, `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`, `/Users/cam/Documents/Projects/cine-forge`
**Scouted:** 2026-03-31
**Scope:** doc-web full AGENTS / skills / runbooks scan, Storybook and Dossier delta since Scouts 015-016, and verification that recent CineForge ideal-alignment skill commits were already present in this worktree
**Previous:** Scout 015 (Storybook & Dossier methodology delta, 2026-03-20) and Scout 016 (Storybook Playwright setup, 2026-03-20)
**Status:** Complete
**Alignment:** No local ADR directly governs these agent-process surface tweaks. The closest local anchors are `AGENTS.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, and the story lifecycle / runbook conventions already documented in this repo.

## Findings

1. **Validation should separate implementation completeness from close-out bookkeeping** — HIGH value
   What: doc-web's `/validate` no longer treats story-index flips, changelog updates, or other `/mark-story-done` / `/finish-and-push` responsibilities as implementation failures. If implementation is complete and only close-out remains, it recommends `Close now` instead of leaving the story in a fake "not done" state.
   Us: CineForge already says `/validate` cannot mark a story done, but the skill still leaves room to score close-out bookkeeping as a story gap. That muddies validation reports and works against the execution ideal's "easy and honest" close-out flow.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: `doc-web/.agents/skills/validate/SKILL.md`
   Invariant: validation should judge implementation truthfully, while close-out skills own closure bookkeeping
   Adaptation: keep CineForge's stricter UI/browser and eval requirements, but separate implementation gaps from close-out follow-up in the report template and guardrails
   Proof target: `/validate` defaults to `Close now` when implementation is complete and only closure bookkeeping remains

2. **Architecture-drift signals should be first-class in validation and hygiene scans** — HIGH value
   What: Dossier now explicitly scans for compatibility shims, duplicate ownership, dead wrappers, placeholder pass-throughs, and widened guards that preserve obsolete contracts. It uses those signals in both `/validate` and `/codebase-improvement-scout`, with an explicit rule that "tests still pass" is not enough to ignore drift.
   Us: CineForge already has a strong greenfield / no-backwards-compat stance, but the reusable process surfaces still do not force agents to name drift signals when reviewing or scouting. That makes it too easy to preserve bad seams under the cover of green tests.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: `dossier/.agents/skills/validate/SKILL.md`, `dossier/.agents/skills/codebase-improvement-scout/SKILL.md`, and `dossier/AGENTS.md`
   Invariant: obsolete seams are a bug, not a neutral implementation detail
   Adaptation: wire the drift scan into CineForge's validation template, repo-hygiene skill, and AGENTS principles without weakening any existing eval/browser checks
   Proof target: the reusable review surfaces ask for drift evidence explicitly and refuse to wave it away just because tests pass

3. **Subagent parallelism should be ownership-aware, not unconditional** — MEDIUM value
   What: Dossier tightened its AGENTS guidance so agents only parallelize edits when write ownership is already clear. When boundaries are fuzzy, it prefers one main execution path plus exploration/review sidecars instead of concurrent edits on overlapping areas.
   Us: CineForge's AGENTS still says to parallelize independent work, but it does not mention the write-boundary precondition. That omission encourages merge-conflict churn and accidental overlap, which is the opposite of the execution ideal.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: `dossier/AGENTS.md`
   Invariant: parallelism should reduce context pressure, not create edit contention
   Adaptation: keep CineForge's existing model-selection table and orchestration stance, but clarify the ownership gate in one line
   Proof target: AGENTS tells future agents to parallelize only when write boundaries are already clear

4. **Promptfoo freshness guidance should be documented as a user-level npm concern** — MEDIUM value
   What: doc-web added a small but useful note: npm's `min-release-age` can help slow global `promptfoo` updates, but because `promptfoo` is installed globally, that control must live in `~/.npmrc`, not in repo-local config.
   Us: CineForge already documents the global `promptfoo` install, but not where freshness gating belongs. That leaves room for false confidence that repo-local npm config can harden a user-level toolchain.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: `doc-web/AGENTS.md`
   Invariant: operator-facing toolchain guidance should be honest about which knobs the repo can and cannot enforce
   Adaptation: document the note in CineForge's AGENTS and promptfoo runbook, not as new installer machinery
   Proof target: promptfoo docs tell the truth about where release-age gating can be configured

5. **Late-March Storybook AGENTS changes were mostly repo-specific runtime pitfalls, not portable skill/process upgrades** — LOW value
   What: Storybook's recent AGENTS edits focus on Dossier pin drift, dev-auth/CORS caveats, and linked-worktree process quirks.
   Us: Those pitfalls are real for Storybook, but they are not CineForge patterns. Copying them over would add noise, not reusable process value.
   Recommendation: **Skip**

6. **The recent CineForge ideal-alignment skill commits are already present in this worktree** — LOW value
   What: I checked the main repo and this worktree at `HEAD`, plus `./scripts/sync-agent-skills.sh --check`.
   Us: The worktree is already on the same commit as `/Users/cam/Documents/Projects/cine-forge`, and the generated skill wrappers are clean. There was no missing "upgrade ours to match the recent CineForge commit" delta to pull over.
   Recommendation: **Skip**

## Approved

- [x] 1. Validation completeness vs close-out bookkeeping — Approved for inline implementation by user on 2026-03-31
- [x] 2. Drift-signal detection in validation and hygiene flows — Approved for inline implementation by user on 2026-03-31
- [x] 3. Ownership-aware subagent parallelism guidance — Approved for inline implementation by user on 2026-03-31
- [x] 4. Promptfoo freshness guidance for global installs — Approved for inline implementation by user on 2026-03-31

## Implementation Checklist

- [x] Update `AGENTS.md` with ownership-aware parallelism, drift-as-debt guidance, and promptfoo freshness note
- [x] Update `.agents/skills/validate/SKILL.md` to separate implementation gaps from close-out bookkeeping, add drift-signal review, and require fresh-verification honesty
- [x] Update `.agents/skills/codebase-improvement-scout/SKILL.md` and `docs/runbooks/codebase-improvement-scout.md` to scan for drift signals and run skill-sync checks when agent surfaces are in scope
- [x] Update `docs/runbooks/promptfoo.md` to document the user-level npm freshness boundary
- [x] Verify the changes, update evidence, and add Scout 017 to `docs/scout.md`

## Skipped / Rejected

- 5. Storybook repo-specific runtime/browser pitfall notes — not transferable to CineForge's general AGENTS or skill surface
- 6. Missing recent CineForge ideal-alignment skill changes — no delta existed; this worktree already matches the main repo `HEAD`

## Verification

- Ran `./scripts/sync-agent-skills.sh` after updating skill surfaces; sync completed cleanly
- Ran `./scripts/sync-agent-skills.sh --check`; result: `skills-check: OK (30 skills, 30 gemini wrappers)`
- Ran `git diff --check`; result: clean
- Re-read the modified sections of `AGENTS.md`, `.agents/skills/validate/SKILL.md`, `.agents/skills/codebase-improvement-scout/SKILL.md`, `docs/runbooks/codebase-improvement-scout.md`, and `docs/runbooks/promptfoo.md`
- Verified this worktree `HEAD` matches `/Users/cam/Documents/Projects/cine-forge` `HEAD`, confirming there was no missing local delta from the recent ideal-alignment commits

## Evidence

- Research evidence:
  - `/Users/cam/Documents/Projects/doc-web/AGENTS.md`
  - `/Users/cam/Documents/Projects/doc-web/.agents/skills/validate/SKILL.md`
  - `/Users/cam/Documents/Projects/dossier/AGENTS.md`
  - `/Users/cam/Documents/Projects/dossier/.agents/skills/validate/SKILL.md`
  - `/Users/cam/Documents/Projects/dossier/.agents/skills/codebase-improvement-scout/SKILL.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/AGENTS.md`
  - `/Users/cam/Documents/Projects/cine-forge/.agents/skills/*`
- CineForge files updated:
  - `AGENTS.md`
  - `.agents/skills/validate/SKILL.md`
  - `.agents/skills/codebase-improvement-scout/SKILL.md`
  - `docs/runbooks/codebase-improvement-scout.md`
  - `docs/runbooks/promptfoo.md`
- Proof notes:
  - Finding 1 proof target met: `/validate` now separates close-out follow-up from implementation gaps and prefers `Close now` when only close-out bookkeeping remains
  - Finding 2 proof target met: `AGENTS.md`, `/validate`, and `/codebase-improvement-scout` now all name drift signals explicitly and reject the "tests still pass" excuse
  - Finding 3 proof target met: `AGENTS.md` now requires clear write ownership before parallel edits
  - Finding 4 proof target met: both `AGENTS.md` and `docs/runbooks/promptfoo.md` document that global `promptfoo` freshness gating belongs in `~/.npmrc`
