---
type: research-prompt
topic: "story-053-cross-cli-skills"
created: "2026-02-19T16:40:00+00:00"
---

# Research Prompt

You are researching practical, up-to-date best practices for unifying reusable agent workflows across four local AI coding CLIs/tools:

1) OpenAI Codex CLI / Codex app
2) Anthropic Claude Code
3) Gemini CLI
4) Cursor

## Objective

Find the best architecture to let all four tools share one canonical set of reusable automation assets (skills/prompts/commands/workflows) with minimal duplication and low maintenance overhead.

## Required Deliverables

Provide a report with:

1. Tool-by-tool capability matrix
- Discovery paths and precedence for reusable workflow assets
- Supported asset formats (skills, prompts, slash commands, templates, scripts)
- Invocation methods (slash, explicit tag, implicit selection)
- Whether symlinks are supported/recommended
- Project-scoped vs user-scoped behavior
- Known limitations/gotchas

2. Compatibility strategy
- What can be fully shared across all four
- What must be adapted per tool
- Suggested canonical intermediate format (if any)
- Tradeoffs: “all-skills”, “all-prompts”, hybrid, generated wrappers

3. Recommended repo layout (concrete)
- Folder structure proposal
- Naming conventions
- How to wire each tool to the canonical source (symlinks, generated files, etc.)
- Version-control guidance (what to commit vs keep local)

4. Migration playbook for this repository state
Current state assumptions:
- `skills/` contains canonical SKILL.md workflows
- `.claude/skills/` contains symlinks to `skills/`
- `.cursor/commands/` contains markdown prompt-command files
- Codex currently sees only system skills in `~/.codex/skills/.system`

Provide step-by-step migration from this state to the recommended unified setup.

5. Validation checklist
- Practical tests to confirm each tool is using the shared assets correctly
- Fast smoke checks and deeper checks

6. Risk register
- Top failure modes (drift, broken symlinks, tool updates, path assumptions)
- Mitigations and monitoring routine

## Constraints
- Prefer primary sources: official docs, vendor repos, maintained references.
- Include exact URLs for every major claim.
- Distinguish confirmed facts vs inference.
- Focus on actionable engineering guidance, not generic AI tooling commentary.

## Output Quality Bar
- Must be specific enough that an engineer can implement in under 1 hour.
- Must include at least one concrete “recommended default architecture” and one “fallback architecture”.
- Must clearly state what is likely to break with future vendor updates.
