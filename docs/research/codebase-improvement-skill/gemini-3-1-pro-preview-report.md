---
type: research-report
topic: codebase-improvement-skill
canonical-model-name: gemini-3.1-pro-preview
research-mode: standard
collected: '2026-03-12T20:01:17.705903+00:00'
---

Here is a comprehensive research report and system design for an AI-run codebase-improvement skill, tailored for a fast-moving, AI-assisted greenfield project.

---

### 1. Landscape Scan: State of the Art in Codebase Hygiene

To build this system, we must look at the intersection of autonomous agents, deterministic static analysis, and continuous refactoring tools. Here are the 15 most relevant systems and patterns:

**Autonomous AI Coding Agents & Workflows**
1. **Sweep.dev:** An AI junior developer that turns bugs/feature requests into PRs. *Why it matters:* Sweep pioneered the "search -> plan -> edit -> test -> self-correct" loop in a PR format. Their approach to blast-radius containment is industry-leading.
2. **Grit.io:** Combines AST (Abstract Syntax Trees) with LLMs for automated tech-debt migrations. *Why it matters:* Proves that LLMs shouldn't guess syntax; they should use deterministic AST tools to find patterns and apply AI only for the semantic translation.
3. **SWE-agent / OpenHands (formerly OpenDevin):** State-of-the-art open-source autonomous agents. *Why it matters:* They utilize a specialized "Agent-Computer Interface" (ACI) rather than raw bash, preventing the agent from getting stuck in pagination or massive file outputs.
4. **Aider (Headless/Scripted):** The premier CLI AI coding tool. *Why it matters:* Aider’s repository map (using tree-sitter) and its ability to be driven via shell scripts make it the perfect engine for a scheduled cron-job hygiene bot.
5. **CodeRabbit:** AI PR reviewer. *Why it matters:* Mastered the art of *not being annoying*. It aggregates findings, ignores cosmetic issues, and provides high-signal summaries.

**Deterministic Hygiene & Dead-Code Tools (The "Senses" for the AI)**
6. **Knip (JavaScript/TypeScript):** Finds unused files, dependencies, and exports. *Why it matters:* LLMs cannot reliably find dead code across a whole repo. An AI agent must run Knip (or equivalent like `cargo udeps` for Rust, `vulture` for Python) and act on its output.
7. **jscpd / PMD:** Copy-paste detectors. *Why it matters:* AI-assisted dev creates massive duplication. These tools give the AI exact coordinates of duplicated logic to refactor.
8. **Dependency Cruiser:** Validates architectural rules (e.g., "UI components cannot import database utilities"). *Why it matters:* Catches architectural drift caused by fast AI generation.

**Continuous Refactoring & Memory Patterns**
9. **Moderne (OpenRewrite):** Mass automated refactoring at scale. *Why it matters:* Demonstrates the value of the "recipe" pattern—running specific, narrow cleanup tasks rather than generic "make this better" prompts.
10. **Sourcery:** Automated refactoring bot for Python/JS. *Why it matters:* Excellent at simplifying complex boolean logic and extracting early returns.
11. **"Boy Scout" GitHub Actions:** Community workflows that run linters with `--fix` on a cron schedule. *Why it matters:* Establishes the baseline branch/PR strategy for automated maintenance.
12. **ADR (Architecture Decision Records) as AI Context:** *Why it matters:* Feeding a lightweight `CONVENTIONS.md` to the AI prevents it from "fixing" things that are actually intentional local patterns.

---

### 2. Pattern Synthesis: What Actually Works

#### Strongest Patterns Worth Stealing
*   **Tool-Augmented Discovery:** The AI should *never* read the whole codebase to look for dead code or duplication. It should run deterministic tools (`knip`, `jscpd`, `eslint`, `tsc`), parse the JSON output, and use the LLM to *resolve* the issues.
*   **The "Draft PR" as the UI:** Do not build a custom dashboard. The agent should create a Draft PR. The PR description is the report. The commits are the auto-fixes. The PR comments are the drafted stories for humans.
*   **Micro-Targeting (One PR per cluster):** If the agent finds dead code, duplicate utilities, and a massive file, it should *not* fix them all in one PR. It should create `chore/ai-remove-dead-code` and `chore/ai-dedupe-utils`.
*   **Self-Healing Test Loop:** The agent must be able to run `npm run test` or `cargo check`. If it fails, the agent gets the error and has *exactly two* attempts to fix it. If it fails again, it reverts the file and escalates to a story.
*   **Stateful Suppression:** The system needs an `.ai-ignore` or `hygiene-state.json` file. If a human closes an AI PR without merging, the AI must record "Do not suggest extracting `UserCard.tsx` again."

#### Anti-Patterns to Avoid (Failure Modes)
*   **The "Make it Better" Prompt:** Asking an LLM to "refactor this repo to be cleaner" results in hallucinated abstractions, renamed variables that break APIs, and endless churn.
*   **Cosmetic Churn:** AI loves changing `if/else` to ternaries, or rewriting comments. This pollutes git history. **Rule:** The AI must be forbidden from making changes that only affect style.
*   **Re-litigating Architecture:** AI will often try to implement Clean Architecture or DDD in a simple CRUD app. It must be constrained to *local* entropy reduction.
*   **The "Big Bang" PR:** A PR with 45 changed files will never be reviewed by a fast-moving team. It will rot and be closed.

---

### 3. Recommended Skill Design for Your Repo

Given your context (fast iteration, AI-generated slop, low bureaucracy), here is the exact operating model.

#### A. Trigger Cadence
*   **Nightly (The Sweeper):** Runs fast, deterministic auto-fixes. (Dead code, unused imports, extracting inline types, deduplicating identical pure functions).
*   **Weekly (The Inspector):** Runs deep analysis on weekend. Generates the "Scout Report" and drafts stories for larger architectural drift.
*   **On-Demand:** Triggered via a GitHub comment (e.g., `@hygiene-bot clean path/to/folder`).

#### B. Branch & Artifact Strategy
1.  Agent creates a base branch: `ai-hygiene/weekly-summary`.
2.  Agent creates a **Scout Report** (`.ai/reports/YYYY-MM-DD.md`).
3.  For **Auto-fixes**, it branches off `main` into narrow branches (e.g., `ai-hygiene/fix-dead-code`), makes the fix, verifies, and opens a PR.
4.  For **Stories**, it appends them to a `TODO.md` or creates GitHub Issues, tagged `ai-drafted`.

#### C. Inspection Checklist (The "Senses")
The agent runs these tools and reads their output:
1.  **Dead Code:** Unused exports, files, dependencies (via `knip` or similar).
2.  **Duplication:** Identical or near-identical utility functions (via `jscpd`).
3.  **File Size:** Files > 400 lines (flag for potential split).
4.  **Complexity:** Functions with high cyclomatic complexity (AI-generated code often results in massive `switch` statements or deeply nested `if`s).
5.  **Stale Scaffolds:** Files named `*Draft`, `*Temp`, or files with empty exported interfaces.

#### D. Classification Rubric: Auto-fix vs. Story vs. Ignore

| Finding | Action | Verification Gate |
| :--- | :--- | :--- |
| Unused export / dead file | **Auto-fix** | Linter + Typechecker pass. |
| Exact duplicate pure functions | **Auto-fix** | Replace with shared import. Tests pass. |
| Unused dependency in `package.json` | **Auto-fix** | Build passes. |
| File > 400 lines (e.g., massive UI component) | **Draft Story** | Too risky to auto-split. Draft a plan. |
| Inconsistent naming (e.g., `getUser` vs `fetchUser`) | **Draft Story** | Requires human consensus. |
| Missing tests on critical path | **Draft Story** | AI can draft the test in the story for human review. |
| Cosmetic / Formatting | **Ignore** | Handled by Prettier/Ruff. |

#### E. Stop Conditions & Guardrails
*   **Max Files Changed:** Auto-fix PRs cannot touch more than 5 files.
*   **Max Retries:** If tests fail after an auto-fix, the agent can try to fix it *twice*. Then it must `git reset --hard` and convert the fix into a story.
*   **No Dependency Updates:** The hygiene bot does not bump versions (leave that to Dependabot/Renovate). It only *removes* unused ones.

#### F. Summary Format for the Human (The PR Body)
```markdown
## 🧹 Weekly Hygiene Report

I analyzed the repo to clean up AI-generated entropy. 

**✅ Auto-fixes ready for review (Low Risk):**
* [PR #102] Removed 4 unused files and 12 dead exports (Verified via Typecheck).
* [PR #103] Deduplicated `formatDate` and `parseDate` utilities across 3 files.

**📝 High-Value Stories Drafted (Requires Human):**
* **Split `DashboardView.tsx`**: It has grown to 650 lines with 4 mixed concerns. [View Drafted Story](#)
* **Stale Abstraction**: `BaseDataFetcher` is only used by one class now. Consider inlining. [View Drafted Story](#)

**🛑 Suppressed / Ignored:**
* Ignored duplication in `tests/mocks` (expected behavior).
```

---

### 4. Prompt / Skill Blueprint

To make this work, you need a highly structured system prompt. Do not use a generic coding prompt.

**System Prompt: The Repo Janitor**
```text
You are an elite Staff Engineer focused exclusively on repository hygiene and entropy reduction.
Your goal is to clean up "AI slop" (duplicate utilities, dead code, stale scaffolds) in a fast-moving project.

CRITICAL RULES:
1. DO NOT change application behavior.
2. DO NOT touch formatting or style.
3. DO NOT invent new architectural patterns (no new Base classes, Factories, or Managers).
4. Optimize for deleting code. Deleting code is your highest priority.

OPERATING PHASES:
Phase 1: Discovery
- Run `npm run find-dead-code` (or equivalent). Read the JSON output.
- Run `npm run find-duplicates`. Read the output.
- Identify files over 400 lines.

Phase 2: Triage & Execution
For each finding, apply the Rubric:
- If it is DEAD CODE: Delete it. Run `npm run typecheck`. If it passes, commit.
- If it is EXACT DUPLICATION of a pure function: Extract to the existing `utils` folder, update imports. Run tests. If they pass, commit.
- If it is COMPLEX (e.g., splitting a large React component, refactoring state management): DO NOT FIX IT. Write a concrete, step-by-step implementation story in `TODO-hygiene.md`.

Phase 3: Verification
If you modify code, you MUST run the linter and typechecker. 
If the check fails, read the error, and attempt a fix. 
If it fails twice, `git checkout -- <file>` and convert the task to a story.

Phase 4: Reporting
Summarize your actions in a concise, high-signal format. Do not list every minor detail. Group by "Auto-fixed" and "Stories Drafted".
```

---

### 5. Implementation Plan

Do not build the fully autonomous loop on day one. Build it in three stages to build trust.

#### Stage 1: The "Crawl" (Scripted Discovery)
*   **What to build:** A bash/python script that runs `knip` (dead code) and `jscpd` (duplication), pipes the output into a headless LLM (like `aider --message "Read these findings and draft a markdown report of what we should do"`).
*   **Goal:** See if the AI can accurately identify the "AI slop" without hallucinating.
*   **Human effort:** Run manually, read the markdown report.

#### Stage 2: The "Walk" (Safe Auto-Fixes)
*   **What to build:** Wrap the script in a GitHub Action that runs nightly. Give the agent permission to *only* execute dead-code removal and unused-dependency removal.
*   **Workflow:** Agent creates a branch, deletes code, runs typechecker. If green, opens a PR.
*   **Goal:** Establish the automated PR workflow and verify the agent doesn't break the build.

#### Stage 3: The "Run" (Full Hygiene Loop)
*   **What to build:** Implement the full prompt blueprint. Allow the agent to deduplicate code and draft stories for large files. Implement the `.ai-ignore` memory file so the agent learns what the humans don't care about.
*   **Evaluation before trusting:** You must evaluate the agent's ability to *revert its own changes* when tests fail. Inject a deliberate error into an auto-fix and ensure the agent catches it, reverts, and drafts a story instead of force-pushing broken code.

### Summary of the "Secret Sauce"
The reason most AI refactoring bots fail is that they rely on the LLM's context window to *find* the problems. **The state-of-the-art approach is to use deterministic, traditional CLI tools to find the coordinates of the tech debt, and only use the LLM to execute the surgical fix or write the human-readable ticket.** This guarantees high signal, zero hallucinations in discovery, and respects the fast-moving nature of your team.