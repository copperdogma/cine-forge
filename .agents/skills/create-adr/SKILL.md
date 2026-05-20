---
name: create-adr
description: Create a new Architecture Decision Record with research scaffolding
user-invocable: true
---

# /create-adr <number> <short-name> "<title>"

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Create a new ADR with proper structure, research scaffolding, and generated planning-surface integration.

Use `/ideation` before decision closure when the considered options are thin, all
options are same-neighborhood variants, or the sticky choice needs a stronger
divergent option set. If the user has explicitly authorized delegation, a
bounded ideation subagent is a good fit for generating the option packet.
`/create-adr` still owns the decision, ADR text, and follow-up route.

## Example

```
/create-adr 008 auth-session "Session Management Strategy"
```

## Steps

1. **Run the bootstrap script:**

   ```bash
   .agents/skills/create-adr/scripts/start-adr.sh <number> <short-name>
   ```

   This creates the full ADR directory structure from templates:
   - `docs/decisions/adr-NNN-<name>/adr.md`
   - `docs/decisions/adr-NNN-<name>/research/research-prompt.md`
   - `docs/decisions/adr-NNN-<name>/research/final-synthesis.md`

2. **Fill in the ADR file** — Replace all placeholder text with real content:
   - Title (human-readable, not the slug)
   - Context, ideal, options, research needed, legacy context, dependencies
   - frontmatter references (`spec_refs`, `ideal_refs`, `story_refs`,
     `compromise_refs`, `related_adrs`, `supersedes`, `superseded_by`)

3. **Write the research prompt** — Fill in `research/research-prompt.md`:
   - Copy context from the ADR
   - Break research into numbered sections with specific questions
   - Be concrete — tell the researcher exactly what to evaluate

4. **Refresh generated planning surfaces when needed** — If the ADR metadata is
   usable and should appear in methodology outputs, run:

   ```bash
   pnpm methodology:compile
   ```

5. **Show the user** the created files for review.

## Guardrails

- Never overwrite an existing ADR directory — the script will error if it exists
- ADR numbers are explicitly assigned, not auto-incremented — check existing ADRs before assigning
- Never commit or push without explicit user request
- The research prompt must stand alone — any AI model should produce useful output without additional context

## Notes

- ADR numbers are sequential. Check existing ADRs before assigning.
- The research prompt should be detailed enough that any AI model can produce useful output without additional context.
- The synthesis prompt is generated automatically by `deep-research` — no template needed.
- See the `Deep Research` section in `AGENTS.md` for the repo's current multi-provider research workflow.
- If the ADR metadata changes planning surfaces, rerun `pnpm methodology:compile` instead of trying to track it in a retired setup doc.
