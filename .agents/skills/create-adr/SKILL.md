---
name: create-adr
description: Create a new Architecture Decision Record with research scaffolding
user-invocable: true
---

# /create-adr <number> <short-name> "<title>"

Create a new ADR with proper structure, research scaffolding, and setup.md tracking.

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

3. **Write the research prompt** — Fill in `research/research-prompt.md`:
   - Copy context from the ADR
   - Break research into numbered sections with specific questions
   - Be concrete — tell the researcher exactly what to evaluate

4. **Update setup.md** — Add the ADR to the ADR Bootstrap Sequence section:
   ```
   ### ADR-NNN: Title
   - [ ] **Status: PENDING** — Needs deep research
   - [x] Stub created: `docs/decisions/adr-NNN-name/adr.md`
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
- See `docs/runbooks/deep-research.md` for how to run the multi-provider research.
- See `docs/runbooks/adr-creation.md` for the full ADR lifecycle.
