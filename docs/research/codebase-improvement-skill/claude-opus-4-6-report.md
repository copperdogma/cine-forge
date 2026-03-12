---
type: research-report
topic: codebase-improvement-skill
canonical-model-name: claude-opus-4-6
research-mode: standard
collected: '2026-03-12T20:01:17.704982+00:00'
---



# AI-Run Codebase-Improvement / Repo-Hygiene Skill: State of the Art Research

---

## 1. Landscape Scan

### 1.1 Autonomous Code Review & Refactoring Agents

**1. Sourcery (sourcery.ai)**
- AI-powered code review bot that integrates into GitHub PRs. Goes beyond linting to suggest refactorings: simplifying conditionals, extracting repeated logic, improving naming. Ships rules-as-code that can be customized per repo.
- **Why it matters:** Demonstrates a production-grade model of opinionated, auto-suggested refactoring that runs continuously with very low human overhead. Their "review on every PR" cadence is well-tested; their rule customization shows how to avoid fighting local conventions.

**2. CodeRabbit (coderabbit.ai)**
- LLM-powered PR review agent. Provides line-level comments, architectural observations, and security flags on every PR. Maintains a "learnings" store—per-repo memory of past review decisions and suppressed findings.
- **Why it matters:** The **learnings/memory** system is the most relevant innovation. CodeRabbit lets you tell it "we intentionally did X" and it remembers, preventing repeated low-value suggestions. This is the best production example of a suppression/convention memory for an AI code agent.

**3. Sweep AI (sweep.dev, now largely open-source patterns)**
- Was one of the first "GitHub issue → PR" agents. You file an issue, Sweep reads the repo, writes code, opens a PR with tests. Open-sourced its approach before pivoting.
- **Why it matters:** Demonstrated the **issue-to-branch-to-PR** pipeline for AI agents. Key lessons: (a) small, scoped changes land well; (b) large refactors fail without decomposition; (c) the agent needs a "planning" step before coding. The failure modes are as instructive as the successes.

**4. Cursor / Windsurf / Aider (AI coding assistants with repo-wide context)**
- Aider (paul-gauthier/aider on GitHub) is open-source, CLI-based, works with multiple LLMs, has a "architect" mode that plans before editing, and supports repo-map-based context gathering. Cursor and Windsurf are IDE-integrated equivalents.
- **Why it matters:** Aider's `--architect` mode and repo-map generation represent the best open-source pattern for "understand the whole repo, then make targeted edits." The repo-map (a condensed AST summary of every file) is a key artifact for any scheduled hygiene agent.

**5. Amazon CodeGuru Reviewer + Profiler**
- AWS service that runs ML-based code review on PRs (Java, Python). Profiler identifies runtime hotspots. The reviewer catches resource leaks, concurrency bugs, and API misuse patterns learned from Amazon's internal codebase.
- **Why it matters:** Shows the value of **anomaly detection against a learned baseline** rather than just static rules. The Profiler side demonstrates that runtime data can feed back into code-improvement suggestions.

### 1.2 Repository Maintenance / Hygiene Bots

**6. Dependabot + Renovate**
- Automated dependency update bots. Renovate (Mend/Renovate, open-source) is the more configurable one—supports grouped PRs, scheduling, auto-merge policies, and dashboard issues that summarize pending updates.
- **Why it matters:** Renovate's **dashboard issue** pattern is brilliant for hygiene agents: a single auto-updating issue that lists all pending work, grouped and prioritized, which humans can scan in 30 seconds. Its auto-merge-if-CI-passes policy is the gold standard for "safe auto-fix."

**7. Knip (github.com/webpro/knip)**
- Open-source tool specifically for finding unused files, dependencies, exports, and types in JS/TS projects. Very fast, very focused.
- **Why it matters:** This is the **best-in-class dead code/dead dependency finder** for the JS/TS ecosystem. It's exactly what a hygiene agent should invoke rather than trying to LLM-detect dead code. Its output is structured and diff-able.

**8. ts-prune / unimported / depcheck**
- Complementary tools for finding unused TypeScript exports, unused files not in the import graph, and unused npm dependencies respectively.
- **Why it matters:** Each is narrow and reliable. A hygiene agent should orchestrate these rather than reimplementing their logic.

**9. jscpd (github.com/kucherenko/jscpd)**
- Copy-paste detector. Finds duplicated code blocks across a repo. Language-agnostic. Outputs structured JSON with exact locations and duplication percentages.
- **Why it matters:** Duplication detection is one of the highest-value hygiene checks. jscpd's structured output makes it automatable. The key insight from production use: filter by minimum token count (50+) to avoid false positives on boilerplate.

### 1.3 Continuous Refactoring & Tech Debt Systems

**10. Stepsize (acquired by Sonar) / CodeScene**
- CodeScene (codescene.com) does behavioral code analysis: identifies hotspots (files changed most frequently that are also complex), detects coordination bottlenecks, and tracks technical debt trends over time. Uses git history, not just static analysis.
- **Why it matters:** The **hotspot analysis** pattern—intersecting change frequency with complexity—is the single most validated method for prioritizing refactoring work. Files that are both complex AND frequently changed are where cleanup has the highest ROI. This should be core to any hygiene agent's prioritization.

**11. SonarQube / SonarCloud**
- Industry-standard static analysis platform. Tracks "technical debt" in time-to-fix estimates, maintains quality gates, trends over time.
- **Why it matters:** The **quality gate** concept (a set of conditions that must pass for a change to be acceptable) is directly applicable. SonarQube's weakness is that it's noisy and rule-based; its strength is the trend-tracking and debt-estimation model.

**12. Qodana (JetBrains)**
- Static analysis platform built on IntelliJ inspections. Runs in CI, provides a baseline mechanism (only flag new issues), and has a web dashboard.
- **Why it matters:** The **baseline mechanism** is critical for a hygiene agent—you need to distinguish "new debt introduced since last run" from "existing debt." Qodana's baseline file is a good artifact pattern.

### 1.4 AI Agent Skill/Workflow Patterns

**13. Claude Code's built-in capabilities and custom commands**
- Claude Code (Anthropic) supports custom slash commands via `.claude/commands/` markdown files, has `CLAUDE.md` for repo-level instructions, and can execute arbitrary shell commands, read/write files, and manage git branches.
- **Why it matters:** This is the **execution substrate** for the skill being designed. The custom command pattern means the hygiene skill can be a markdown file that Claude Code executes. The `CLAUDE.md` file is where conventions and suppression lists live.

**14. GitHub Actions + Scheduled Workflows**
- GitHub's native CI/CD supports cron-scheduled workflows that can check out code, run analysis, create branches, open PRs, and create issues.
- **Why it matters:** This is the **trigger mechanism**. A scheduled Action can invoke the hygiene agent on a cron schedule. The Action creates the branch, runs the agent, and opens the PR/issue.

**15. Devin / Factory AI / Cosine Genie (autonomous coding agents)**
- Commercial autonomous agents that take high-level tasks and produce PRs. Devin and Factory both emphasize "give it a Jira ticket, get back a PR."
- **Why it matters:** These demonstrate the pattern of **agent-as-worker-on-a-task**, but their lessons are mostly cautionary: large autonomous changes have low merge rates without human involvement. The most successful pattern is small, well-scoped, well-verified changes.

**16. Greptile (greptile.com)**
- AI-powered codebase understanding API. Indexes a repo semantically and answers questions about architecture, patterns, and relationships. Used as a building block for code review bots.
- **Why it matters:** Demonstrates that **semantic indexing of the repo** (beyond just text search) is valuable for detecting architectural drift and understanding intent.

### 1.5 Relevant Blog Posts, Papers, and Public Workflows

**17. "Continuous Refactoring" by Martin Fowler's team (martinfowler.com)**
- Articulates the philosophy that refactoring should be continuous and integrated into daily work, not a separate "refactoring sprint." The "boy scout rule" (leave code cleaner than you found it).
- **Why it matters:** The philosophical foundation. A hygiene agent is the automated boy scout.

**18. Google's "Tricorder" system (paper: "Lessons from Building Static Analysis Tools at Google", CACM 2018)**
- Google's internal code analysis platform. Key finding: developers ignore more than 80% of analysis findings unless they are (a) presented at the right time, (b) high confidence, and (c) actionable with a concrete fix. Led to the design principle: **"not actionable, not shown."**
- **Why it matters:** This is the most important empirical finding for designing a hygiene agent. Noisy findings destroy trust. The agent must be high-precision or it becomes ignored.

**19. "Large-Scale Automated Refactoring Using ClangMR" (Google, 2013) and Rosie (internal large-scale change system)**
- Google's system for making sweeping, automated refactoring changes across millions of lines of code. Key pattern: small mechanical transforms, applied broadly, verified by existing tests.
- **Why it matters:** Validates that **narrow, mechanical, well-verified changes can be safely automated at scale**. The critical constraint is: the change must be semantically equivalent (behavior-preserving), not "probably fine."

**20. The "Pit of Success" pattern from Microsoft / .NET team**
- Design systems so the easy path is the correct path. Applied to hygiene: the agent should make the clean pattern easier than the messy one.
- **Why it matters:** The hygiene agent shouldn't just clean up after developers—it should identify where the repo's structure makes it easy to do the wrong thing and suggest structural fixes.

---

## 2. Pattern Synthesis

### 2.1 Strongest Patterns Worth Stealing

**Pattern 1: Hotspot-Prioritized Inspection (from CodeScene)**
- Don't treat all files equally. Rank files by `change_frequency × complexity`. Focus hygiene work on files that are both messy AND actively being worked on. A complex file nobody touches is low priority. A simple file touched every day is fine. A complex file touched every day is where cleanup has 10x ROI.
- **Implementation:** `git log --format='%H' --since='30 days' -- '*.ts' | xargs -I{} git diff-tree --no-commit-id --name-only -r {} | sort | uniq -c | sort -rn` gives you change frequency. Combine with a complexity metric (lines of code, cyclomatic complexity, or simply file length as a proxy).

**Pattern 2: Structured Finding → Classification → Action Pipeline (from Google Tricorder + Renovate)**
- Every finding goes through: Detection → Confidence scoring → Classification (auto-fix / story / suppress / ignore) → Action. The classification rubric is explicit and tunable.
- Auto-fix criteria: mechanical, behavior-preserving, high confidence, verifiable by existing tests.
- Story criteria: high value but requires judgment, structural change, or new tests.
- Suppress criteria: known intentional pattern, previously reviewed and accepted.
- Ignore criteria: low value, cosmetic only, or below confidence threshold.

**Pattern 3: The Dashboard Issue / Scout Report (from Renovate)**
- A single, auto-updating artifact that summarizes the current state of the codebase's hygiene. Humans read this one artifact to understand what's happening. It replaces dozens of noisy notifications with one concise summary.
- The report is idempotent: running the agent again updates the same report rather than creating a new one.

**Pattern 4: Memory / Learnings Store (from CodeRabbit)**
- The agent maintains a persistent file (in-repo or in a side artifact) that records:
  - Suppressed findings ("we know about X, it's intentional")
  - Conventions ("we use pattern Y for Z, not the textbook pattern")
  - Previous findings and their outcomes (was it acted on? dismissed? deferred?)
- This prevents the agent from re-raising the same issue every run and allows it to learn what the team values.

**Pattern 5: Repo Map + Semantic Understanding (from Aider)**
- Before inspecting anything, build a condensed representation of the entire repo: file tree, module boundaries, key exports, dependency graph, and architectural intent (from CLAUDE.md or similar).
- This prevents the agent from making suggestions that conflict with the repo's architecture or from missing cross-cutting concerns.

**Pattern 6: One PR Per Finding Cluster, Not One Mega-PR (from Sweep, Dependabot)**
- Atomic, reviewable, independently mergeable PRs. Each addresses one coherent cluster of related findings (e.g., "remove 5 unused exports in the auth module" not "fix 47 things across the repo").
- Mega-PRs are never reviewed, never merged, and waste agent compute.

**Pattern 7: Baseline + Delta (from Qodana, SonarQube)**
- Track the state of findings over time. Each run compares against the previous baseline. The report highlights:
  - New debt introduced since last run
  - Debt resolved since last run
  - Persistent debt (unchanged)
  - Trends (is the codebase getting cleaner or dirtier?)
- This creates a "ratchet" effect: the team can set a policy that new debt shouldn't increase.

**Pattern 8: Guard Rails via Verification Stack (from Google's large-scale refactoring)**
- Auto-fixes must pass: (a) the existing test suite, (b) type checking, (c) linting, (d) a build. If any fail, the change is downgraded from "auto-fix" to "story" or discarded.
- For UI changes: optionally, screenshot comparison or a lightweight Playwright check.
- The verification stack is the agent's "immune system" against harmful changes.

**Pattern 9: Graduated Trust Model (practical wisdom from multiple sources)**
- Start with reporting only (no auto-fixes). Build trust over 2-4 weeks.
- Graduate to auto-fixes for the narrowest, safest categories (unused imports, dead exports, trivially-dead code).
- Graduate further to auto-fix + auto-merge for changes where CI passes.
- Never auto-merge structural changes or anything touching business logic.

**Pattern 10: Cooldown / Deduplication (anti-churn pattern)**
- If a finding was raised in the last N runs and not acted on, stop raising it (or move it to a "backlog" section of the report with lower prominence).
- If a file was changed by the agent in the last run, don't touch it again this run unless the previous change was merged.
- Rate-limit auto-fix PRs: no more than 2-3 open at once.

### 2.2 Patterns to Avoid

**Anti-Pattern 1: The Style Police Agent**
- An agent that primarily flags formatting, naming style, and cosmetic issues generates enormous churn with near-zero value in a fast-moving repo. Formatting should be handled by an autoformatter (Prettier, Black), not a hygiene agent. The agent should focus on structural and semantic issues.

**Anti-Pattern 2: The Architecture Astronaut**
- An agent that suggests refactoring to design patterns, introducing abstractions, or reorganizing module boundaries based on textbook software engineering. These suggestions require deep domain context and are almost always wrong when made by an automated system.

**Anti-Pattern 3: The Mega-PR Bot**
- An agent that accumulates dozens of changes into one massive PR. Nobody reviews it. It bitrot within days. It creates merge conflicts with active work. Always prefer small, atomic PRs.

**Anti-Pattern 4: The Boy Who Cried Wolf**
- An agent that reports the same 50 findings every week, most of which are low-priority or intentional. Trust degrades to zero within 2-3 runs. Aggressive filtering, suppression, and confidence scoring are essential.

**Anti-Pattern 5: Refactoring Without Tests**
- An agent that makes "refactoring" changes to code that has no tests. These are not refactorings; they are behavioral changes with no safety net. The agent should flag untested complex code as a story ("add tests to X"), not refactor it directly.

**Anti-Pattern 6: Fighting the Framework**
- An agent that doesn't understand the frameworks in use (Next.js, React, etc.) and suggests changes that break framework conventions (e.g., moving files out of the `app/` directory in Next.js, or renaming a `page.tsx` file).

**Anti-Pattern 7: Ignoring Git History**
- An agent that looks only at the current snapshot and misses context like "this file was just created yesterday and is still in progress" or "this seemingly-dead code is used by a feature branch that hasn't merged yet."

---

## 3. Recommended Skill Design

### 3.1 Trigger Cadence

| Mode | When | What |
|---|---|---|
| **Weekly deep scan** | Sunday night or Monday morning (cron) | Full repo analysis, report generation, optional auto-fix PRs |
| **On-demand** | Human or agent invokes `/project:hygiene` | Same as weekly but triggered manually, useful after a big push |
| **Post-merge hook** (future) | After significant PRs merge | Lightweight delta check — "did this merge introduce new debt?" |
| **Pre-milestone** | Before a release or milestone | Comprehensive scan with higher bar — focus on risks |

**Recommended starting cadence:** Weekly + on-demand. Don't over-trigger. The value compounds over weeks, not hours.

### 3.2 Branch Strategy

```
main
 └── hygiene/scan-2025-01-15       ← analysis branch (ephemeral, never merged)
      ├── hygiene/fix-dead-exports  ← auto-fix branch (PR against main)
      ├── hygiene/fix-unused-deps   ← auto-fix branch (PR against main)
      └── [report committed as artifact or issue]
```

**Rules:**
- The scan branch is created fresh each run, used as workspace, and deleted after the report is produced.
- Each auto-fix cluster gets its own branch off `main` (not off the scan branch).
- Auto-fix PRs are labeled `hygiene` and `auto` for easy filtering.
- Maximum 3 auto-fix PRs open at once. If 3 are already open and unmerged, the agent creates stories instead.
- Stories are created as GitHub issues (or a structured file in `.hygiene/stories/`).

### 3.3 Inspection Checklist

The agent runs these inspections in order, from most mechanical/reliable to most judgment-dependent:

#### Tier 1: Mechanical (high confidence, automatable)
| Check | Tool/Method | Output |
|---|---|---|
| Unused dependencies | `knip`, `depcheck` | List of removable deps |
| Unused exports | `knip`, `ts-prune` | List of removable exports |
| Unused files | `knip`, `unimported` | List of deletable files |
| Duplicate code blocks | `jscpd` (min 50 tokens) | Pairs of duplicated blocks |
| Dead imports | TypeScript compiler, ESLint | List of removable imports |
| Type errors / build failures | `tsc --noEmit` | Broken type contracts |
| Dependency vulnerabilities | `npm audit`, `osv-scanner` | Security findings |

#### Tier 2: Heuristic (medium confidence, needs LLM judgment)
| Check | Method | Output |
|---|---|---|
| Oversized files (>400 lines) | File length scan + LLM review of whether decomposition is warranted | Split candidates with rationale |
| Stale/misleading comments and docs | LLM comparison of code behavior vs comment/doc text | Misaligned docs |
| Half-finished scaffolds | LLM detection of TODO, FIXME, stub functions, placeholder text | Incomplete work inventory |
| Inconsistent patterns | LLM comparison of similar constructs across the repo | Pattern violations |
| Weak naming | LLM review of exported identifiers for clarity | Rename candidates |
| Missing error handling | LLM review of async/try-catch patterns | Uncovered error paths |

#### Tier 3: Architectural (low confidence, requires human judgment)
| Check | Method | Output |
|---|---|---|
| Hotspot analysis | `git log` change frequency × file size/complexity | Priority-ranked files |
| Architectural drift | LLM comparison of actual module dependencies vs intended architecture in CLAUDE.md | Drift report |
| Abstraction health | LLM review of key interfaces/types for cohesion | Weak abstraction candidates |
| Missing test coverage for critical paths | LLM identification of complex untested logic | Test gap inventory |
| Risky complexity growth | Delta analysis of complexity metrics since last run | Complexity trend alerts |

### 3.4 Classification Rubric

Each finding is classified into one of four actions:

```
┌─────────────────────────────────────────────────────────┐
│                    CLASSIFICATION RUBRIC                  │
├──────────┬──────────────────────────────────────────────┤
│ AUTO-FIX │ ALL of:                                       │
│          │ • Mechanical / behavior-preserving             │
│          │ • High confidence (tool-detected, not LLM-only)│
│          │ • Verifiable (tests + typecheck + build pass)  │
│          │ • No business logic touched                    │
│          │ • <50 lines changed                            │
│          │ • Not in a file modified in last 48h on main   │
│          │                                                │
│          │ Examples: remove unused import, delete dead     │
│          │ export, remove unused dependency, fix trivial   │
│          │ type error                                      │
├──────────┼──────────────────────────────────────────────┤
│ STORY    │ ANY of:                                        │
│          │ • Requires judgment or design decision          │
│          │ • Structural change (file split, module move)   │
│          │ • Touches business logic                        │
│          │ • Needs new tests to verify                     │
│          │ • >50 lines would change                        │
│          │ • LLM-detected (not tool-confirmed)             │
│          │                                                │
│          │ Examples: decompose oversized file, fix          │
│          │ architectural drift, add missing error handling, │
│          │ resolve duplicate utility pattern                │
├──────────┼──────────────────────────────────────────────┤
│ SUPPRESS │ ANY of:                                        │
│          │ • Previously raised and explicitly dismissed     │
│          │ • Matches a convention in CLAUDE.md             │
│          │ • Known intentional pattern                     │
│          │ • In suppression list                           │
├──────────┼──────────────────────────────────────────────┤
│ IGNORE   │ ANY of:                                        │
│          │ • Below confidence threshold                    │
│          │ • Purely cosmetic / formatting                  │
│          │ • De minimis impact                             │
│          │ • In a file not touched in 90+ days (low ROI)  │
│          │   AND complexity is moderate                    │
└──────────┴──────────────────────────────────────────────┘
```

### 3.5 Stop Conditions / Guardrails

1. **Never modify files with uncommitted changes on `main`** (check `git status` and recent commit timestamps).
2. **Never auto-fix if the test suite doesn't pass on `main` first** (don't pile fixes on a broken base).
3. **Never auto-fix code that has no test coverage** — downgrade to story.
4. **Maximum 3 auto-fix PRs open simultaneously.** Beyond that, create stories.
5. **Maximum 200 total lines changed across all auto-fix PRs in one run.** Forces atomicity.
6. **If the agent is uncertain about whether a change is behavior-preserving, it must create a story instead.**
7. **Never rename publicly-exported identifiers as an auto-fix** (too risky for cross-module breakage that tests might not catch).
8. **Never touch configuration files (CI configs, deployment configs, env files) as auto-fix.**
9. **Never modify or delete test files as auto-fix.**
10. **Abort the entire run if the repo is in a state that suggests active large-scale work** (e.g., more than 10 files changed in the last 24 hours on `main`).

### 3.6 Output Artifacts

The agent produces these artifacts each run:

**1. Scout Report (primary human-facing artifact)**
```markdown
# 🔍 Repo Hygiene Scout Report — 2025-01-15

## Executive Summary
- Overall health: 🟡 (3 new concerns since last week, 2 resolved)
- Auto-fix PRs created: 2
- Stories created: 3
- Findings suppressed: 7
- Trend: complexity slightly up, dead code slightly down

## 🔧 Auto-Fix PRs Created
1. **Remove 4 unused exports in `src/lib/`** → PR #142
2. **Remove `lodash.debounce` unused dependency** → PR #143

## 📋 Stories Created
1. **Split `src/components/Dashboard.tsx` (487 lines)**
   - This file has been edited 12 times in 30 days and contains 3 distinct responsibilities.
   - Suggested decomposition: DashboardLayout, DashboardFilters, DashboardDataGrid
   - [Story link or file path]

2. **Consolidate duplicate `formatCurrency` implementations**
   - Found in `src/utils/format.ts` (line 45) and `src/components/PriceDisplay.tsx` (line 12)
   - 87% token similarity. Suggest extracting to shared utility.
   - [Story link or file path]

3. **Add error handling to `src/api/fetchUser.ts`**
   - No try/catch around network call. No error boundary in calling component.
   - [Story link or file path]

## 📊 Hotspots (files most worth improving)
| File | Changes (30d) | Lines | Complexity | Recommendation |
|---|---|---|---|---|
| src/components/Dashboard.tsx | 12 | 487 | High | Split (story created) |
| src/lib/api-client.ts | 8 | 234 | Medium | OK for now |
| src/hooks/useAuth.ts | 7 | 156 | Medium | OK for now |

## 📈 Trends
- Dead exports: 23 → 19 (improving ✅)
- Avg file size (src/): 142 → 148 lines (slightly growing ⚠️)
- Duplicate blocks (>50 tokens): 7 → 8 (slightly growing ⚠️)
- Unused dependencies: 1 → 0 (improving ✅)

## 🔇 Suppressed (not raised again)
- 7 findings matching suppression rules (see `.hygiene/suppressions.yaml`)
```

**2. Debt Registry (`.hygiene/debt-registry.yaml`)**
```yaml
# Auto-generated by hygiene agent. Do not edit auto-fix entries.
# Add manual suppressions in suppressions.yaml.

last_run: 2025-01-15T03:00:00Z
baseline_commit: abc123

findings:
  - id: dead-export-001
    type: unused-export
    file: src/lib/helpers.ts
    export: formatDate
    confidence: high
    source: knip
    first_seen: 2025-01-08
    status: auto-fixed
    pr: 142

  - id: hotspot-001
    type: oversized-file
    file: src/components/Dashboard.tsx
    lines: 487
    change_frequency: 12/30d
    confidence: high
    source: git-analysis + llm
    first_seen: 2025-01-08
    status: story-created
    story: .hygiene/stories/split-dashboard.md

  - id: dup-001
    type: duplication
    file_a: src/utils/format.ts:45
    file_b: src/components/PriceDisplay.tsx:12
    similarity: 0.87
    confidence: high
    source: jscpd
    first_seen: 2025-01-15
    status: story-created
    story: .hygiene/stories/consolidate-format-currency.md
```

**3. Suppressions File (`.hygiene/suppressions.yaml`, human-editable)**
```yaml
# Add entries here to suppress findings permanently.
# The hygiene agent will not raise these again.

suppressions:
  - pattern: "unused-export:src/lib/test-helpers.ts:*"
    reason: "Exports used by test files outside src/"
  - pattern: "oversized-file:src/generated/*"
    reason: "Generated files, not manually maintained"
  - pattern: "duplication:src/components/*/styles.ts"
    reason: "Intentional co-located styles, not worth extracting"
```

**4. Story Files (`.hygiene/stories/YYYY-MM-DD-<slug>.md`)**
```markdown
# Split Dashboard.tsx

## Context
`src/components/Dashboard.tsx` is 487 lines and has been edited 12 times
in the last 30 days. It contains layout, filtering, and data grid logic
in a single component.

## Suggested Approach
1. Extract `DashboardFilters` (lines 89-167)
2. Extract `DashboardDataGrid` (lines 168-390)
3. Keep `DashboardLayout` as the orchestrator

## Complexity: Medium
## Estimated Scope: ~2 hours of focused work
## Priority: High (hotspot)
## Created: 2025-01-15 by hygiene-agent
```

### 3.7 Summary Format for the Human

The human should receive:
1. A **Slack message / terminal output / notification** with 3-5 lines:
   ```
   🔍 Weekly hygiene scan complete.
   2 auto-fix PRs ready for merge (CI passing ✅).
   3 new improvement stories created.
   Top hotspot: Dashboard.tsx (split recommended).
   Full report: .hygiene/reports/2025-01-15.md
   ```
2. The **Scout Report** (described above) for those who want detail.
3. The **auto-fix PRs** with minimal descriptions (the PR is the description).

### 3.8 When to Auto-Edit vs Create a Story

```
                    ┌──────────────┐
                    │ Finding found │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ In suppression│──Yes──► SUPPRESS (log & skip)
                    │ list?         │
                    └──────┬───────┘
                           │No
                    ┌──────▼───────┐
                    │ Tool-detected │──No──► Is it high-confidence
                    │ (not LLM-only)│        LLM finding?
                    └──────┬───────┘        │
                           │Yes             ├─No──► IGNORE
                           │                ├─Yes─► STORY
                    ┌──────▼───────┐
                    │ Mechanical &  │──No──► STORY
                    │ behavior-     │
                    │ preserving?   │
                    └──────┬───────┘
                           │Yes
                    ┌──────▼───────┐
                    │ <50 lines     │──No──► STORY
                    │ changed?      │
                    └──────┬───────┘
                           │Yes
                    ┌──────▼───────┐
                    │ Tests exist   │──No──► STORY (with note:
                    │ for affected  │        "add tests first")
                    │ code?         │
                    └──────┬───────┘
                           │Yes
                    ┌──────▼───────┐
                    │ Tests + build │──No──► Discard fix,
                    │ pass after    │        create STORY with
                    │ applying fix? │        failure details
                    └──────┬───────┘
                           │Yes
                           ▼
                       AUTO-FIX PR
```

---

## 4. Prompt / Skill Blueprint

### 4.1 Skill Structure

The skill should be implemented as a Claude Code custom command (`.claude/commands/hygiene.md`) that orchestrates the full workflow. Here is the blueprint:

```markdown
# Repo Hygiene Scan

You are a codebase hygiene agent performing a scheduled inspection of this repository.
Your goal is to identify high-value cleanup work and either implement safe auto-fixes
or create well-scoped improvement stories.

## Phase 1: Orient (do this first, before any analysis