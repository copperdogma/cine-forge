# Story 004 Meta-Synthesis Prompt (Opus 4.6)

Use this prompt with Opus 4.6 to synthesize all five research reports into one final decision report.

```text
You are acting as lead research editor and principal architect for CineForge Story 004 (Script Normalization).
Your task is to read five existing reports, reconcile them, and produce one final, implementation-ready recommendation.

## Inputs to Synthesize

Use all five reports below as source material:

1) docs/research/story-004-long-doc/codex-research-report.md
2) docs/research/story-004-long-doc/gpt5-2-research-report.md
3) docs/research/story-004-long-doc/grok4-1-research-report copy.md
4) docs/research/story-004-long-doc/opus4-6-research-report copy 2.md
5) docs/research/story-004-long-doc/gemini3-research-report copy 3.md

If any file appears malformed, truncated, or low quality, do NOT ignore it silently:
- explicitly note data quality issues,
- use only credible portions,
- and explain what was discarded and why.

## Project Context (CineForge)

- Story 004 objective: normalize screenplay/prose/notes into canonical screenplay text.
- Existing implementation baseline includes:
  - short docs: single-pass
  - long screenplay cleanup: edit-list / patch
  - long prose/notes conversion: chunked conversion + overlap
  - QA second-pass AI check with retries and `needs_review` on persistent QA errors
  - per-call cost tracking
- Existing code location context:
  - docs/research/long-doc-editing.md
  - src/cine_forge/ai/llm.py
  - src/cine_forge/ai/qa.py
  - src/cine_forge/ai/long_doc.py
  - src/cine_forge/modules/ingest/script_normalize_v1/main.py

## Your Synthesis Goals

1) Merge the strongest evidence across reports.
2) Resolve contradictions with explicit reasoning.
3) Separate "proven now" vs "promising but uncertain".
4) Produce one concrete v1 recommendation for immediate implementation.
5) Produce one clear v2 roadmap for follow-up iteration.

## Required Method

### Step 1: Source quality grading
For each of the five reports:
- Assign quality score (0-5) on:
  - evidence density
  - practical applicability
  - specificity
  - internal consistency
- Provide a one-paragraph critique.

### Step 2: Claim extraction and conflict resolution
- Extract key claims by topic:
  - API/model capabilities
  - frameworks/libraries
  - chunking/coherence strategies
  - edit-list vs regeneration
  - screenplay-specific tooling
  - token economics
- Where claims conflict, resolve with:
  - confidence level (high/medium/low),
  - rationale,
  - tie-break criteria used.

### Step 3: Decision framework
- Build a weighted decision matrix comparing at least 3 candidate architectures:
  A) mostly single-pass
  B) hybrid strategy (single-pass + edit-list + chunking)
  C) fully chunked/multi-pass pipeline
- Include explicit weights and scoring rationale.

### Step 4: Final recommendation
- Provide:
  - recommended v1 architecture (implement now),
  - recommended v2 enhancements (next milestone),
  - explicit non-goals (what not to build yet).

### Step 5: Operational plan
- Give a "this week" execution checklist tied to CineForge files/modules.
- Include test plan and acceptance checks.
- Include cost-control and safety guardrails.

## Output Format (strict)

Produce markdown with these sections:

1. Executive Summary (8-12 bullets)
2. Source Quality Review (table + short commentary)
3. Consolidated Findings by Topic
4. Conflict Resolution Ledger (claim, conflicting views, final adjudication, confidence)
5. Decision Matrix (weighted table)
6. Final Architecture Recommendation
   - v1 (now)
   - v2 (next)
   - non-goals
7. Implementation Plan for CineForge
   - exact file-level changes to prioritize
   - testing strategy
   - rollout/risk controls
8. Open Questions & Validation Experiments
9. Final Confidence Statement

## Constraints

- Be concrete and codebase-oriented, not generic.
- Clearly label assumptions and uncertainty.
- Prefer practical reliability over novelty.
- If evidence is weak, say so explicitly.
- Keep recommendations realistic for an MVP pipeline.
```
