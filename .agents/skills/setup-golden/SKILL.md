---
name: setup-golden
description: Bootstrap a golden reference testing workspace — explore the project, generate all workspace files, present for user approval.
user-invocable: true
---

# /setup-golden

Set up a golden reference testing workspace for this project. Golden fixtures are
the ground truth for extraction/generation evals — verified input/output pairs that
the system must reproduce correctly.

This skill explores the project, makes opinionated decisions about the golden
format, generates all workspace files, and presents a summary for user approval.
The ideal run: the user says `/setup-golden`, reviews the summary, says "yes."

**Usage:**
```
/setup-golden                    # full setup
/setup-golden --refresh          # regenerate workspace files (schema changed, etc.)
```

## What Gets Created

```
benchmarks/golden/
  README.md                      # format spec — the canonical schema reference
  _verify-golden-outputs.md      # adversarial verification protocol
  validate-golden.py             # structural validator (self-contained, no imports beyond stdlib)
  _verification-checklist.md     # tracking table (starts empty)
  _coverage-matrix.json          # dimension coverage tracking (starts empty)
  _inbox/
    README.md                    # inbox drop-zone docs
```

## How It Works

### 1. Explore the project autonomously

Dig through the codebase to understand what this project extracts or generates.
Look for:
- Entity models, data schemas, Pydantic types, ADRs defining output structure
- Existing extraction/generation code that shows what the system produces
- Test fixtures, example outputs, anything that shows the shape of results
- Input formats (screenplays, documents, structured data)
- AGENTS.md, README, docs/ for project context
- Existing golden files in `benchmarks/golden/` and `tests/fixtures/golden/`

Don't ask the user where things are. Find them. Only ask if you genuinely can't
locate the entity model after a thorough search.

### 2. Generate everything

Based on what you found, generate all workspace files. Make opinionated decisions:

**README.md** — Canonical format spec covering:
- Self-healing eval philosophy (every discrepancy investigated, not auto-failed)
- Three-tier system (T1 = verified ground truth, T2 = input only, T3 = stubs)
- Complete golden output format tailored to the project's entity types
- Ref conventions, cross-referencing rules
- Fixture ID category prefixes (derived from the project's input types)
- Dimension enums for coverage tracking
- Input format conventions

**_verify-golden-outputs.md** — Adversarial verification protocol tailored to
the project's entity types. The generic principles (read input first, be adversarial,
verify evidence grounding) apply everywhere, but the entity-specific checklists need
to match what this project actually extracts.

**validate-golden.py** — Structural validator with SCHEMA CONFIG at the top as
plain data (no imports from project source). Entity types, enum values, required
fields, ref conventions, metadata count fields — all derived from the schemas you
found. Validation logic below the config is generic: ref consistency, required
fields, metadata count accuracy, enum compliance, orphan detection.
Design to run as `.venv/bin/python benchmarks/golden/validate-golden.py [fixture-id]`.

**Tracking files** — Empty checklist table and coverage matrix.

**_inbox/README.md** — Brief inbox drop-zone docs.

### 3. Validate and summarize

Run the validator to confirm it parses cleanly (should pass with zero fixtures).

Then present a concise summary to the user:
- What entity types you found and how you mapped them to the golden format
- Category prefixes you chose and why
- Any decisions where you weren't sure (flag these explicitly)
- Next steps: "Drop an input in `_inbox/` and run `/golden-create`"

The user reviews and either approves or gives feedback. Iterate if needed.

## If the workspace already exists

- With `--refresh`: re-read existing workspace and project schemas, identify
  what's drifted, regenerate affected files. Summarize what changed.
- Without `--refresh`: tell the user the workspace exists and what `/golden-verify`
  or `--refresh` would do.

## Principles

- **Be opinionated.** You have the project's schemas — make decisions. The user
  will correct you if something's wrong. That's faster than 20 questions.
- **README.md is the single source of truth.** The verification protocol, validator
  config, and creation skill all point to it.
- **The validator must be self-contained.** No imports from project source. All
  schema config is plain data at the top. Portable and easy to update.
- **Design for autonomous agents.** Everything you create will be consumed by AI
  agents running with zero prior context. Make the format spec and verification
  protocol clear enough that they can produce and verify goldens without asking anyone.

## Guardrails

- Never create golden references you can't verify. If it's too complex, decompose.
- Never accept AI-generated golden outputs without multiple review passes.
- Golden references are NOT sacred — they're the current best answer. Update them
  when the system proves them wrong.
- Every golden reference must trace back to a requirement in ideal.md.
- Include at least one adversarial/edge-case input per capability.
- Store golden files in version control — they're test fixtures, not ephemeral.

## Operational Playbook

See `docs/runbooks/golden-build.md` for the detailed build methodology, including:
- Phase-by-phase build process (identify → draft with SOTA → structural review → semantic review → fix → dual eval baseline)
- Common failure patterns and how to fix them (missing aliases, shallow descriptions, phantom entries, wrong relationship types, convention inconsistencies)
- Eval-driven golden improvement protocol (ties into `/verify-eval`)
- Periodic golden audit process and enforcement across lifecycle skills
- Inbox → create → verify → validate lifecycle

**Key insight**: Structural validation catches ~20% of issues. Full semantic review
(checking every entry, not a sample) catches the other ~80%.
Never skip the semantic review pass.
