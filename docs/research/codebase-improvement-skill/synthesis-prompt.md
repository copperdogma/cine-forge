---
type: synthesis-prompt
topic: "codebase-improvement-skill"
created: "2026-03-12T20:05:22.416112+00:00"
auto-generated: true
---

# Synthesis Prompt

You are acting as lead research editor. Your task is to read multiple independent research reports on the same topic, reconcile them, and produce one final, implementation-ready synthesis.

## Research Context

Research the state of the art for an **AI-run codebase-improvement / repo-hygiene skill** that can be scheduled periodically (daily / weekly / on demand) to inspect a software repository, identify high-value cleanup or improvement work, and either:

1. draft a concrete implementation story / task for humans or other agents, or
2. safely implement narrow low-risk cleanup work on a side branch with strong verification.

Context:

- Repo type: active greenfield software project, AI-assisted development, fast iteration, low tolerance for bureaucracy.
- Pain point: rapid AI implementation tends to accumulate codebase junk: duplicate utilities, stale abstractions, oversized files, dead paths, weak naming, poor docs alignment, half-finished scaffolds, inconsistent patterns.
- Human preference: move fast, do only brief real-world QA, do not manually inspect every agent-produced change. The system should reduce entropy without creating heavy process overhead.
- Desired operating model: the skill can run in a side branch, spend a long time analyzing the repo, then produce a concise high-signal summary and a recommended next step. In some cases it may create a story instead of changing code directly.

Research goals:

1. Find the best existing patterns from across:
   - autonomous code review agents
   - repository maintenance / hygiene bots
   - continuous refactoring workflows
   - scheduled engineering excellence jobs
   - AI coding-agent skills / prompts / playbooks
   - technical-debt discovery systems
   - PR review / static-analysis / lint-fix / duplication / dead-code cleanup systems
2. Identify concrete open-source projects, commercial tools, blog posts, papers, or public workflows that are especially relevant.
3. Distinguish **what actually works in practice** from generic aspirational agent designs.
4. Focus on workflows that minimize human review burden while still preventing codebase rot.

Questions to answer:

1. What are the strongest recurring design patterns for scheduled codebase-improvement agents?
2. What should such a system inspect each run?
   - examples: duplication, dead code, stale docs, oversized files, architectural drift, broken conventions, missing tests, weak abstractions, inconsistent naming, risky complexity growth, unused dependencies, flaky workflows
3. Which findings should be auto-fixed vs escalated into a story vs ignored?
4. What branch / PR / artifact strategy works best?
   - side branch only?
   - one branch per finding cluster?
   - story file + report + optional patch?
5. What verification stack is most effective?
   - static checks
   - targeted runtime checks
   - browser checks for UI
   - semantic / architectural review gates
6. How do the best systems avoid harmful churn?
   - repeated low-value suggestions
   - re-litigating settled architecture
   - noisy cosmetic changes
   - fighting local conventions
7. What memory / tracking artifacts are useful?
   - debt registry, scout report, story queue, suppression list, recurring findings log, scorecard, trend metrics
8. What prompts / operational instructions make the agent substantially better?
9. What anti-patterns or failure modes show up repeatedly?
10. If you were designing the best version for this repo, what exact workflow would you recommend?

Required output structure:

1. **Landscape scan**:
   - 10-20 of the most relevant sources / systems / tools / workflows
   - brief description of each
   - why it matters
2. **Pattern synthesis**:
   - strongest patterns worth stealing
   - patterns to avoid
3. **Recommended skill design** for this repo:
   - trigger cadence options (daily / weekly / manual)
   - branch strategy
   - inspection checklist
   - classification rubric for findings
   - stop conditions / guardrails
   - output artifacts
   - summary format for the human
   - when to auto-edit vs create a story
4. **Prompt / skill blueprint**:
   - concrete skill sections or prompt blocks to include
   - important checklists or gates
5. **Implementation plan**:
   - what to build first
   - what can wait
   - what should be evaluated before trusting automation

Strong preference:

- Prioritize systems and patterns that are concrete, repeatable, and already field-tested.
- Give specific examples and source names whenever possible.
- Optimize for high leverage and low human attention cost.
- Do not default to “just run lint and tests.” That is table stakes, not the interesting part.
- Do not optimize for backwards compatibility or enterprise process overhead.

## Reports to Synthesize

You will receive 3 research reports, each produced by a different AI model. Each report covers the same research question from the instructions above.

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
research-topic: "codebase-improvement-skill"
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
- Score each source report on its merits regardless of which AI model produced it. Do not assume the most detailed report is the most accurate — weight verifiable citations over unverified claims.
