---
type: synthesis-prompt
topic: "story-053-cross-cli-skills"
created: "2026-02-19T15:43:09.188579+00:00"
auto-generated: true
---

# Synthesis Prompt

You are acting as lead research editor. Your task is to read multiple independent research reports on the same topic, reconcile them, and produce one final, implementation-ready synthesis.

## Research Context

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

## Reports to Synthesize

You will receive 2 research reports, each produced by a different AI model. Each report covers the same research question from the instructions above.

## Your Synthesis Goals

1. Grade each source report on quality: evidence density, practical applicability, specificity, and internal consistency (0–5 scale for each, with a one-paragraph critique).
2. Extract key claims by topic area.
3. Identify where reports agree (high confidence) vs. disagree (needs adjudication).
4. Resolve contradictions with explicit reasoning — evaluate the strength of each report's evidence, not majority vote.
5. Separate "proven / high confidence" from "promising but uncertain."
6. Produce one concrete recommendation, not a menu of options.
7. If one report is clearly higher quality, weight it accordingly and say why.

## Required Output Format

Begin your response with:

---
canonical-model-name: "{the product name you are — e.g., chatgpt, claude, gemini, grok — lowercase, no version numbers}"
report-date: "{today's date in ISO 8601}"
research-topic: "story-053-cross-cli-skills"
report-type: "synthesis"
---

Then produce the following sections:

1. **Executive Summary** (8–12 bullets)
2. **Source Quality Review** (table with scores + short commentary per report)
3. **Consolidated Findings by Topic**
4. **Conflict Resolution Ledger** (claim, conflicting views, final adjudication, confidence level)
5. **Decision Matrix** (if applicable — weighted, with scoring rationale)
6. **Final Recommendation** (concrete, with rationale)
7. **Implementation Plan / Next Steps** (if applicable)
8. **Open Questions & Confidence Statement**

## Quality Instructions

- Be concrete and specific, not generic.
- Clearly label assumptions and uncertainty.
- Prefer practical reliability over novelty.
- If evidence is weak across all reports, say so — do not manufacture false confidence.
- Do not simply merge or average — adjudicate.
- Note which report(s) contributed each key finding.
