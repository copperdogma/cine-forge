# Scout 011 — codebase-improvement-skill

**Source:** External landscape scan — autonomous code review agents, repo hygiene bots, continuous refactoring workflows, and AI skill patterns
**Scouted:** 2026-03-12
**Scope:** Research best-in-class patterns for a scheduled codebase-improvement skill that can inspect this repo, reduce junk accumulation, and either draft a story or safely make narrow cleanup changes on a side branch
**Previous:** None
**Status:** Complete

## Findings

1. **Context-aware review with custom rules is table stakes** — HIGH value
   What: Qodo, Graphite, Greptile, CodeRabbit, and GitHub Copilot all emphasize full-repo context plus team-specific rules / standards rather than generic review comments. The strongest products explicitly optimize for high signal and low noise.
   Us: We already care about repo-specific patterns, ADRs, and reuse rules, but we do not yet have a recurring skill that turns those into a standing codebase-improvement audit.
   Recommendation: Create story

2. **Planning should be a first-class artifact, separate from coding** — HIGH value
   What: CodeRabbit Issue Planner turns an issue into a grounded coding plan with codebase-aware tasks and agent-ready prompts before implementation. The planning artifact is conversational and revisable.
   Us: Our story workflow is strong, but the future codebase-improvement skill should probably output a scout/report + story rather than jump directly to code most of the time.
   Recommendation: Create story

3. **Noise control requires scope filters** — HIGH value
   What: reviewdog filters findings to the diff; Greptile supports manual triggers and branch/label filters; Sonar's Clean as You Code focuses on new code; Graphite lets teams target critical PRs and skip routine updates.
   Us: We need this. A recurring repo-improvement agent that comments on everything will become spam immediately.
   Recommendation: Create story

4. **Prioritize hotspots and trends, not raw issue counts** — HIGH value
   What: CodeScene argues that technical debt should be prioritized where low code health overlaps with high change frequency. It tracks trends and exposes hotspots instead of overwhelming teams with undifferentiated issue lists.
   Us: We currently lack a durable way to rank "important mess" over "cosmetic mess."
   Recommendation: Create story

5. **Auto-fix should be narrow and deterministic by default** — HIGH value
   What: OpenRewrite, Semgrep autofix, Knip, and deptry all show the same pattern: use explicit recipes/rules/config for safe mechanical cleanup; use AI for guidance or scoped suggestions where ambiguity remains.
   Us: This matches the repo's bias toward safe automation. The recurring skill should not do free-form large refactors unattended.
   Recommendation: Create story

6. **Suppression and memory are essential** — HIGH value
   What: Greptile learns from comments, Semgrep uses code and triage history, CodeScene supports directives/config, and Knip/deptry expose ignore and mapping config. Mature systems all provide a way to stop re-flagging accepted exceptions.
   Us: We do not yet have a "known acceptable debt / ignore / deferred rationale" memory for recurring improvement runs.
   Recommendation: Create story

7. **Low-risk branch automation can reduce human review load** — MEDIUM value
   What: Renovate's branch automerge model is useful: create a branch, run checks, merge automatically only for narrow safe cases, and raise a PR only when review is actually needed.
   Us: This could map well to dependency or mechanical cleanup classes, but only after the finding classifier is trustworthy.
   Recommendation: Create story

8. **Project-specific review chores should be codified** — MEDIUM value
   What: Danger JS codifies repetitive review rules in a project-owned rules file so humans can focus on harder judgment calls.
   Us: Our AGENTS/skills encode some of this in prose, but not as a recurring operational checklist for repo hygiene.
   Recommendation: Adopt inline

9. **Headless interfaces matter for agent adoption** — MEDIUM value
   What: Greptile MCP and GitHub Copilot CLI both expose review flows directly to agents and terminals. Headless operation makes recurring automation practical.
   Us: This aligns perfectly with our Headless Operation mandate.
   Recommendation: Adopt inline

## Approved

- [x] Build `codebase-improvement-scout` skill with report-first workflow, narrow autofix lane, and a corresponding runbook

## Skipped / Rejected

- None yet

## Implementation

- Created `.agents/skills/codebase-improvement-scout/SKILL.md`
- Added bootstrap script and report/state templates under `.agents/skills/codebase-improvement-scout/`
- Added `docs/runbooks/codebase-improvement-scout.md`
- Research-backed design anchored in `docs/research/codebase-improvement-skill/final-synthesis.md`
