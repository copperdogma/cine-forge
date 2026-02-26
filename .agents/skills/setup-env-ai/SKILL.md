---
name: setup-env-ai
description: Set up AI agent environment — AGENTS.md, README, skills, and agent configuration
user-invocable: true
---

# /setup-env-ai

Set up the AI agent working environment for the project. This makes the repo
ready for AI agents to work in effectively.

## What This Skill Produces

- `AGENTS.md` — Project-wide agent instructions and engineering principles.
- `CLAUDE.md` — Thin Claude-specific adapter that loads AGENTS.md.
- `README.md` — Project overview for humans and agents.
- `.agents/skills/` — Canonical skills directory with core skills.
- `.claude/skills` — Symlink to .agents/skills.
- `.cursor/skills` — Symlink to .agents/skills.
- `scripts/sync-agent-skills.sh` — Skill sync script.

## Steps

### 1. Scaffold Agent Configuration

Create the directory structure:

```
.agents/skills/
.claude/
.cursor/
.gemini/commands/
scripts/
```

### 2. Create AGENTS.md

Read `docs/ideal.md` (if it exists from `/setup-ideal`). The AGENTS.md should:

- Start with a prominent reference to ideal.md:
  > **The Ideal (`docs/ideal.md`) is the most important document in this project.**
  > It defines what the system should be with zero limitations. Every architectural
  > decision should move toward the Ideal. Every compromise should carry an eval
  > that detects when it's no longer needed.

- Include the core mandates from the Ideal-first methodology:
  - Greenfield, no backwards compatibility
  - Critical pushback required
  - No implicit commits
  - Simplest-first engineering (AI-first for AI transformation projects)
  - Eval first, complexity second

- Include project-specific context:
  - What the project does (one paragraph)
  - Core stack
  - Key architectural decisions
  - Repo map

- Include operational commands (test, lint, eval).

### 3. Create CLAUDE.md

Thin adapter:

```markdown
@AGENTS.md

## Claude Code Bridge

Load `AGENTS.md` as the canonical instruction source for this repository.
```

### 4. Create README.md

Brief project overview:

- What the project does
- Link to `docs/ideal.md` — "The Ideal defines the north star for this project."
- Link to `docs/spec.md` — "The Spec describes current compromises against the Ideal."
- Getting started (dev setup, running tests)
- Project status

### 5. Copy Core Skills

Copy these skills from a reference project (or create fresh):

- `build-story` — Story execution
- `check-in-diff` — Pre-commit audit
- `create-cross-cli-skill` — Skill creation meta-skill
- `create-story` — Story scaffolding
- `mark-story-done` — Story completion validation
- `reflect` — Change impact propagation
- `triage-inbox` — Inbox processing
- `triage-stories` — Backlog prioritization
- `validate` — Quality validation

Adapt each to the new project's context (file paths, commands, conventions).

### 6. Run Sync

```bash
scripts/sync-agent-skills.sh
scripts/sync-agent-skills.sh --check
```

### 7. Update Checklist

Check off Phase 2a items in `docs/setup-checklist.md`.

## Guardrails

- AGENTS.md must reference ideal.md prominently — not buried, not optional.
- README must link to ideal.md and spec.md.
- Never duplicate skill content across tool-specific directories.
- Always run sync after creating or modifying skills.
- Update the setup checklist when done.
