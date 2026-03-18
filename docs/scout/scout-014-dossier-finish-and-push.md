# Scout 014 — dossier-finish-and-push

**Source:** `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-03-18
**Scope:** Changes since Scout 013, focused on the new `/finish-and-push` lifecycle skill added in Dossier commit `5848786`
**Previous:** Scout 013 (Storybook, Dossier, codex-forge agent updates, 2026-03-13)
**Status:** Complete

## Findings

1. **`/finish-and-push` bundles story closure with validated landing without inventing a second workflow** — HIGH value
   What: Dossier added `.agents/skills/finish-and-push/SKILL.md` as a thin orchestrator over `/mark-story-done` then `/check-in-diff`. The value is the bundled-permission contract plus explicit minor-vs-major triage when a close-out request turns up small issues.
   Us: CineForge already had `.agents/skills/mark-story-done/SKILL.md`, `.agents/skills/check-in-diff/SKILL.md`, and `docs/runbooks/check-in-worktree-landing.md`, but no single "close this story and land it" entry point. No relevant ADR or design doc currently governs lifecycle-skill composition, so this is a workflow adaptation rather than an architectural decision. CineForge's runbook rule also means the port needs a companion runbook, not just the skill file.
   Recommendation: **Adopt inline** — add the wrapper skill, add the companion runbook, update `AGENTS.md` lifecycle/runbook guidance, and sync generated wrappers.

## Approved

- [x] 1. `/finish-and-push` orchestrator adaptation — Adopted. Evidence: `.agents/skills/finish-and-push/SKILL.md`, `docs/runbooks/finish-and-push.md`, `AGENTS.md` lifecycle/runbook updates, and wrapper regeneration via `./scripts/sync-agent-skills.sh` plus `./scripts/sync-agent-skills.sh --check`.

## Skipped / Rejected

- None
