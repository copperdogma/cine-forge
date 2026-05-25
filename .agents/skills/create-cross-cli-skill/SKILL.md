---
name: create-cross-cli-skill
description: Create a new project skill in canonical Agent Skills format and refresh compatibility links.
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
2. Treat `description` as model-visible routing inventory, not documentation:
   - keep it to one focused sentence by default, roughly 250-300 characters unless trigger specificity truly needs more
   - put trigger nouns up front: domain, action, artifact, tool, or surface
   - include only cues that decide when this skill should activate
   - move examples, policy detail, long workflow explanation, and validation matrices into the body, `references/`, or templates
   - preserve trigger nouns when shortening an existing description
3. Keep instructions implementation-oriented and testable.
4. Every project skill must include an alignment check telling the agent to consult `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, generated dashboards, and `docs/decisions/` / `docs/design/` when architecture, workflow, schema, or UX questions arise; if no ADR or methodology guidance applies, the skill should say to state that explicitly.
5. Avoid tool-specific primary sources (`.cursor/commands`, `.claude/commands`, `.gemini/commands`) for skill content.
6. After creating or changing skills, run: `scripts/sync-agent-skills.sh`
7. Validate with: `scripts/sync-agent-skills.sh --check`
8. Generate provider-specific command aliases only when this repo explicitly keeps slash-command aliases: `scripts/sync-agent-skills.sh --sync-aliases`; validate them with `scripts/sync-agent-skills.sh --check-aliases`.

## Validation Checklist

- New skill exists at canonical path.
- `.claude/skills`, `.cursor/skills`, and `skills` still point to `.agents/skills`.
- No matching Gemini wrapper is required for standard skill discovery.
- Optional command aliases are generated and checked only when intentionally retained.

## Guardrails

- Do not duplicate the same instruction text across tool-specific files.
- Do not commit/push unless user explicitly requests.
