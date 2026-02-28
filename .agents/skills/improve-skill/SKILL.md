---
name: improve-skill
description: Retrospective on the last skill interaction — identify and apply generic process improvements
user-invocable: true
---

# /improve-skill

Evaluate the interaction that just happened with the most recently used skill. Identify where the skill's instructions fell short, propose improvements, and apply approved ones.

## Philosophy

You are a SOTA model. Use your judgment. This skill gives you framing and constraints, not a step-by-step checklist. Read the conversation, think about what went well and what didn't, and propose thoughtful improvements. Don't mechanically fill in a template.

## How to approach it

1. **Figure out which skill was just used.** Read its SKILL.md.

2. **Evaluate the interaction.** Look at the full conversation from invocation through completion. Where did the user have to correct course? Where did the skill produce low-value output? Where did the agent go off-script in a way that actually worked better? Where were instructions missing, too rigid, or misleading? Use your intelligence — you watched the whole thing happen.

3. **The hard filter: generic over specific.** Every proposed improvement must pass this test: *would a different project using this same skill benefit from this change?* If it only helps because of our specific app, domain, or stack — note it for the user's awareness but don't propose editing the skill for it. Skills are portable. App-specific knowledge belongs in AGENTS.md, not in skills.

4. **Present a numbered list of recommendations.** For each: what went wrong, why, and what to change. Be concrete — quote the current wording and propose the replacement. Ask the user to approve all, pick specific items, or skip.

5. **Implement approved changes.** Edit the SKILL.md. Run `scripts/sync-agent-skills.sh`. Re-read the file to confirm.

## Guardrails

- Don't add app-specific knowledge to skills — they're portable across projects
- Don't bloat a skill for a one-off edge case — improve for patterns, not incidents
- Don't weaken existing guardrails unless they actively caused harm
- Get approval before editing anything
