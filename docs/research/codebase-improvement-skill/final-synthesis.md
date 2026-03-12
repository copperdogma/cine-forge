---
type: synthesis-report
topic: "codebase-improvement-skill"
synthesis-model: "manual-codex-synthesis"
source-reports:
  - "claude-opus-4-6-report.md"
  - "gemini-3-1-pro-preview-report.md"
  - "gpt-5-2-pro-report.md (error artifact)"
synthesized: "2026-03-12T20:15:00+00:00"
---

# Final Synthesis

## Bottom Line

The best version of this is **not** a generic “look around and improve the repo” agent.

That approach produces churn, architecture relitigation, and low-trust cleanup PRs. The best systems in the landscape all converge on a hybrid pattern:

1. deterministic tools discover concrete problems
2. AI prioritizes and classifies them using repo context, ADRs, and conventions
3. AI only auto-fixes narrow, behavior-preserving classes
4. everything else becomes a high-signal story or report

In other words: the winning design is a **scheduled repo hygiene scout**, not a free-form autonomous refactoring bot.

## Strongest Patterns Worth Stealing

### 1. Discovery should be tool-first, not LLM-first

The recurring theme from the landscape is that mature systems do not rely on the model to *find* dead code, duplication, or dependency drift from raw repo reading alone.

Use deterministic detectors first, then let the model reason over their output:

- Python/backend:
  - `ruff`
  - `pytest`
  - file-size / complexity scans
  - optional: `vulture` for unused Python code
- UI/TypeScript:
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - optional: `knip` for unused TS exports / files / dependencies
  - `jscpd` for duplication
- Repo-wide:
  - `rg`-based scans for TODO/stub/temp markers
  - git-history hotspot ranking
  - docs-vs-code drift checks

### 2. One concise report beats many noisy comments

Renovate’s dashboard issue, CodeRabbit’s learnings/memory, and review tools with strong filtering all point to the same lesson: humans will ignore this if it becomes noisy.

The skill should produce one primary artifact per run:

- a scout-style report summarizing:
  - auto-fix candidates
  - story candidates
  - ignored / suppressed items
  - trends vs previous run

### 3. Auto-fix only narrow, behavior-preserving classes

This should start with a deliberately tiny auto-fix surface:

- remove unused imports
- remove unused dependencies
- delete provably dead files / exports
- collapse exact duplicate pure helpers when references are obvious
- update clearly stale docs/comments only when code behavior is verified

Everything else should draft a story instead:

- splitting large files
- renames
- abstraction changes
- architectural drift
- test strategy changes
- anything touching core logic or prompt behavior

### 4. Memory / suppression is mandatory

Without a suppression memory, the skill will annoy you by rediscovering the same accepted weirdness forever.

The skill needs a durable state file, something like:

`memory/codebase-improvement-state.yaml`

With entries for:

- suppressed findings
- rationale / owner
- ADR references for intentional exceptions
- cooldown windows
- previously drafted stories
- previously opened hygiene branches / PRs

### 5. Prioritization should use hotspots, not raw issue count

CodeScene-style hotspot logic is more important than another linter.

A file is high priority when it is:

- large or complex
- changed frequently
- repeatedly mentioned by detectors
- involved in recent bugs or fix churn

This prevents the agent from wasting cycles on cold, ugly files nobody touches while missing the messy files that actually slow the team down.

## Recommended Operating Model

### Cadence

Start with:

- Weekly deep scan
  - long-running
  - report + story drafting only
- On-demand manual run
  - same logic, useful after big bursts of AI coding

Only later add:

- nightly narrow auto-fix runs for safe mechanical classes

Do **not** start with daily broad auto-refactoring. That is how you get junk churn faster, not less.

### Branch Strategy

Use a side-branch-first model:

1. create a temporary analysis branch for the run
2. generate the report there
3. if there are safe auto-fixes, create separate tiny fix branches from `main`
4. cap open hygiene branches / PRs to a small number

Recommended limits:

- max 3 auto-fix branches per run
- max 5 files changed per auto-fix branch
- max 2 self-repair attempts if checks fail

If a fix fails checks twice, downgrade it to a story.

### Output Artifacts

Each run should produce:

1. a dated report under `docs/reports/` or `docs/scout/`
2. optional drafted story/stories for higher-risk cleanup
3. optional narrow fix branch(es) for safe cleanup
4. an updated suppression / memory state file

### Human Interface

The human summary should stay short:

- `Auto-fix ready`
- `Stories drafted`
- `Ignored / suppressed`
- `Trend since last run`
- `Recommended next step`

The whole point is to let you skim it in under a minute.

## Classification Rubric

### Auto-fix

Only if all are true:

- mechanical
- behavior-preserving
- repo-local conventions are clear
- checks can prove safety
- blast radius is small

Examples:

- dead imports
- dead dependencies
- dead files with no references
- exact duplicate helper consolidation

### Draft Story

If any of these are true:

- structural / architectural judgment required
- new abstraction would be introduced
- many files would change
- naming or API decisions are subjective
- tests need to be designed, not just run
- ADRs or conventions may need to change

Examples:

- split `chat.py`
- remove a stale abstraction layer
- unify two competing patterns
- redesign a service boundary

### Ignore / Suppress

If the finding is:

- cosmetic only
- already accepted intentionally
- too low value
- likely to conflict with active work
- below confidence threshold

## Guardrails That Matter

The anti-patterns were very consistent across sources:

- never run “make this repo better” as an unconstrained prompt
- never let the agent do style churn
- never let it re-litigate settled architecture
- never let it open one mega-PR
- never let it keep re-raising suppressed findings
- never let it auto-refactor untested logic

Concrete guardrails for this repo:

- ADR check required before any structural suggestion
- no auto-fix that introduces a new abstraction
- no auto-fix across more than one subsystem at once
- browser verification required for any UI-affecting change
- do not touch files modified in the last few days unless the finding is mechanical and high-confidence
- prefer deletion over new code

## What To Build First

### Phase 1: Reporting-only skill

Build the recurring skill as a reporting engine first.

It should:

- run stack-appropriate detectors
- rank findings
- classify each one
- draft one concise report
- draft stories for the top few non-mechanical improvements

No auto-edits yet.

### Phase 2: Safe auto-fix lane

After a few successful reporting runs:

- allow dead import / dead dependency / dead file cleanup
- only on a side branch
- only with full checks passing
- only for tiny clusters

### Phase 3: Memory + trend tracking

Then add:

- suppression memory
- cooldown logic
- per-run comparison against previous runs
- hotspot scoring

This is what turns the skill from “one-off janitor” into a recurring hygiene system.

## Recommended Product Shape

For this repo, the best end state looks like:

- a new skill dedicated to recurring codebase improvement scouting
- optional automation that runs it weekly on a side branch
- output defaults to report + drafted story
- auto-fixes are a narrow opt-in lane, not the default

That fits your preference exactly: build fast, inspect lightly, and still avoid letting the codebase turn into garbage.

## Research Notes

- Anthropic and Gemini both independently converged on the same core design: deterministic discovery, AI triage, tiny auto-fix scope, strong memory/suppression, and report-first operation.
- The OpenAI provider run failed due a tooling endpoint mismatch (`gpt-5.2-pro` sent to chat completions). The failure artifact was preserved, but the synthesis above is still well-supported by the two successful provider reports plus direct source review.
