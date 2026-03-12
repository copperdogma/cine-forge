---
type: research-prompt
topic: "codebase-improvement-skill"
created: "2026-03-12T19:52:29.403064+00:00"
---

# Research Prompt

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
