---
name: create-cross-cli-skill
description: Create a new project skill in canonical format and sync it for Codex, Claude, Cursor, and Gemini CLI.
user-invocable: true
---

# /create-cross-cli-skill

Use this skill whenever the user asks to create a new skill.

## Required Output

Create only:
- `.agents/skills/<skill-name>/SKILL.md`

Optional colocated resources:
- `.agents/skills/<skill-name>/scripts/`
- `.agents/skills/<skill-name>/templates/`
- `.agents/skills/<skill-name>/references/`
- `.agents/skills/<skill-name>/assets/`

## Rules

1. Use frontmatter with `name`, `description`, and `user-invocable: true` (or `false` for scaffolds not yet ready).
2. Keep instructions implementation-oriented and testable.
3. Every project skill must include an alignment check telling the agent to consult `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, generated dashboards, and `docs/decisions/` / `docs/design/` when architecture, workflow, schema, or UX questions arise; if no ADR or methodology guidance applies, the skill should say to state that explicitly.
4. Avoid tool-specific primary sources (`.cursor/commands`, `.claude/commands`) for skill content.
5. After creating or changing skills, run: `scripts/sync-agent-skills.sh`
6. Validate with: `scripts/sync-agent-skills.sh --check`

## Validation Checklist

- New skill exists at canonical path.
- `.claude/skills` and `.cursor/skills` still point to `.agents/skills`.
- Matching Gemini wrapper exists in `.gemini/commands/<skill-name>.toml`.

## Guardrails

- Do not duplicate the same instruction text across tool-specific files.
- Do not commit/push unless user explicitly requests.
