# Runbook: Golden Reference Build & Maintenance

Step-by-step procedure for building, validating, and maintaining golden reference files used by promptfoo evals and acceptance tests. Derived from building golden references for The Mariner screenplay across 10 eval tasks.

## Context

Golden references are hand-curated ground truth files that define "correct" for each eval. They live in two locations:

| Location | Purpose | Used by |
|---|---|---|
| `benchmarks/golden/` | promptfoo eval references (character, location, prop, scene, config, relationship extraction, normalization, enrichment, continuity, QA) | `promptfoo eval -c tasks/*.yaml` |
| `tests/fixtures/golden/` | Unit test fixtures (scene entity extraction) | `pytest -m unit` |

If a model disagrees with the golden, one of them is wrong — and it's not always the model.

## The Core Lesson

**Structural validation catches ~20% of issues. Semantic review catches ~80%.**

A golden file can pass JSON schema validation, have all required fields, and match expected counts — while having significant content errors (wrong entity names, missing aliases, incorrect relationships, shallow descriptions). Don't trust structural validation alone.

## Prerequisites

- Source screenplay text (The Mariner is in `benchmarks/input/`)
- Existing promptfoo eval configs in `benchmarks/tasks/`
- Python scorers in `benchmarks/scorers/`
- Access to SOTA model for draft generation (see AGENTS.md "Baseline = Best Model Only")
- Node.js 24+ with promptfoo installed (see AGENTS.md "Model Benchmarking")

## Build Phases

### Phase 1: Identify What Needs a Golden `[judgment]`

For each eval task (extraction, analysis, etc.), determine:
- What's the input? (screenplay text, scene excerpt, etc.)
- What's the correct output? (character list, scene boundaries, config fields, etc.)
- Can a domain expert verify the golden in under 30 minutes?

If verification takes longer, decompose into smaller goldens.

### Phase 2: Generate Draft with SOTA `[script]` + `[judgment]`

Use the best available model to generate a draft golden:

```bash
# Example: run the eval with SOTA model, capture output
source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1
cd benchmarks
promptfoo eval -c tasks/<eval-name>.yaml --no-cache --filter-providers "claude-opus" -j 1 --output results/golden-draft.json
```

**Never use a cheap model for golden generation.** The draft is your starting point, not your finished product.

### Phase 3: Structural Review `[script]`

Validate the draft against expected structure:

1. **JSON validity** — parse the output, check schema compliance
2. **Field completeness** — all required fields populated (no placeholders, no "UNKNOWN")
3. **Count sanity** — entity counts, scene counts, relationship counts match manual expectations
4. **Cross-reference integrity** — relationship endpoints reference real entities, scene IDs are valid

Run the Python scorer against the draft as a self-check:
```bash
# The scorer validates structural quality
promptfoo eval -c tasks/<eval-name>.yaml --no-cache --filter-first-n 1
```

### Phase 4: Semantic Review `[judgment]`

**Review EVERY entry. Do not sample.**

For each entity/scene/config field in the golden:

1. Read the golden entry (name, description, traits, relationships, etc.)
2. Read the source screenplay
3. Ask: "Is this factually correct? Is it complete? Would a domain expert agree?"
4. Check for:
   - **Missing entries** — entities/scenes the source supports but the golden doesn't include
   - **Phantom entries** — entries in the golden that aren't in the source (hallucinations from draft generation)
   - **Name inconsistencies** — aliases missing, canonical name wrong, case issues
   - **Shallow descriptions** — technically correct but missing the character's arc, motivation, or significance
   - **Wrong relationships** — relationship exists but type is wrong, or evidence doesn't support the specific dynamic

**Expected first-pass failure rate: 15-30%.** This is normal. The failures cluster into patterns (see Common Failure Patterns below).

### Phase 5: Fix and Re-review `[script]` + `[judgment]`

Apply fixes to the golden JSON:
- For < 5 changes: individual edits are fine
- For > 5 changes: use a batch Python script (atomic, verifiable, reproducible)

After fixing:
1. Re-run the Python scorer to verify structural integrity
2. Do a second semantic review pass on changed entries
3. The second pass should find < 5% issues

### Phase 6: Dual Eval Baseline `[script]`

Run the full eval with the finalized golden to establish baseline scores:

```bash
cd benchmarks
promptfoo eval -c tasks/<eval-name>.yaml --no-cache -j 3
```

Record both scorer results:
- **Python scorer** — structural quality (JSON validity, field completeness, entity matching)
- **LLM rubric** — semantic quality (coherence, insight depth, evidence grounding)

Update `docs/evals/registry.yaml` with baseline scores.

## Boundaries

### Always do
- Review ALL entries in semantic review — never sample during initial build
- Run the Python scorer after every batch of changes
- Use SOTA model for draft generation
- Record baseline scores in `docs/evals/registry.yaml`
- Store golden files in version control

### Ask first
- Before adding/removing entities from the golden entity list (affects all downstream scoring)
- Before changing naming conventions (affects matching logic in scorers)
- Before changing golden structure (may require scorer updates)

### Never do
- Accept a golden that only passed structural validation — semantic review is mandatory
- Use a cheap model for golden generation — it produces shallow, incomplete drafts
- Trust first-pass semantic review as final — expect 15-30% failure rate; always do a second pass
- Modify a golden without re-running the eval to verify the change improves scores

## Common Failure Patterns

These are recurring issues found during semantic review, ranked by frequency:

### 1. Missing Aliases (~30% of failures)

The golden has a canonical name but is missing common aliases used in the screenplay (nicknames, titles, abbreviations).

**Example**: Golden has "CAPTAIN KARL" but screenplay also uses "Karl", "the Captain", "Cap". Models that output any of these variants score as mismatches.

**Fix**: Add all name variants as aliases in the golden.

### 2. Shallow Descriptions (~25% of failures)

The entry is structurally valid but semantically shallow — correct facts but missing the character's significance, arc, or thematic role.

**Example**: Golden says "A fisherman" for a character who is actually "The town's aging patriarch who represents the dying fishing industry and serves as Karl's moral compass."

**Fix**: Enrich the description with evidence from the source. This is why LLM rubric scoring catches what Python scorers miss.

### 3. Phantom Entries (~15% of failures)

SOTA model hallucinated an entity during draft generation that doesn't exist in the source, or inflated a minor mention into a full entity.

**Example**: Golden includes "THE BARTENDER" as a character with traits and relationships, but the screenplay only mentions "a bartender" once in a scene direction with no dialogue or characterization.

**Fix**: Remove the phantom entry or demote to a minimal mention if warranted.

### 4. Wrong Relationship Types (~15% of failures)

Relationship exists between the entities but the type is wrong or too specific.

**Example**: Golden says "mentor" but the source shows a peer relationship with occasional advice, not a structured mentorship.

**Fix**: Correct the relationship type to match what the source actually demonstrates.

### 5. Convention Inconsistencies (~15% of failures)

Different golden files use different conventions for the same concept.

**Example**: `the-mariner-characters.json` uses "father_son" as a relationship type while `the-mariner-relationships.json` uses "parent_child" for the same relationship.

**Fix**: Standardize conventions across ALL golden files, not just the one being reviewed.

## Eval-Driven Golden Improvement

Goldens are not write-once artifacts. Every eval run is a chance to discover golden errors.

### When to trigger

Any time an eval shows a mismatch between model output and golden reference:
- Entity name mismatches
- Entity count differences
- Relationship type differences
- Field content differences
- Score regressions after pipeline changes

### The investigation protocol

Use `/verify-eval` for the structured 5-phase investigation. For each mismatch:

| Finding | Action |
|---------|--------|
| **Model-wrong** — hallucination, over-extraction, naming error | Golden stands. Document as a real failure mode. |
| **Golden-wrong** — missing entity, wrong name, missing alias, inconsistent convention | Fix the golden, re-run eval. |
| **Ambiguous** — insufficient evidence to decide | Note in work log. Defer until more evidence. |

**Raw eval scores are meaningless. Only verified scores count.** See `/verify-eval` for the full protocol.

### Convention consistency across goldens

When a mismatch reveals an inconsistency across golden files, fix ALL goldens to use the same convention. Don't just fix the one that failed.

**Known convention issues to watch for:**
- Relationship type format (noun vs verb phrase)
- Canonical name fullness (short form vs fullest available)
- How unnamed/minor characters are handled

## Periodic Golden Audit

Goldens degrade silently. A golden built weeks ago may have conventions that diverge from current pipeline expectations.

### When to audit

- **Before any model benchmark** — wrong goldens produce wrong winners. CineForge discovered their "winning" model (GPT-4.1 at 0.965) was measured against a golden with 4 incorrect fields. After fixing, a different model won.
- **After pipeline changes** that alter extraction, filtering, or scoring behavior
- **After adding a new provider/model** to the eval suite

### Audit process

1. **Convention consistency check** `[script]` — Compare all goldens for consistent naming, relationship types, field formats
2. **Source re-read** `[judgment]` — Re-read the source text. Are there missing entities? Entities that should be removed per current filtering conventions?
3. **Run evals against goldens** `[script]` — For every mismatch, classify via `/verify-eval`
4. **Structural re-validation** `[script]` — Run Python scorers on all goldens. Verify pass.
5. **Spot-check semantic review** `[judgment]` — Unlike initial build, audit spot-checks: all relationships, any changed entries, 20% random sample. If spot-check finds >10% failure rate, do full semantic review.
6. **Document** `[judgment]` — Record in story work log: date, goldens audited, issues found, fixes applied

## Enforcement Across Skills

This protocol is enforced at every gate in the story lifecycle:

- **AGENTS.md Definition of Done #5**: Every eval mismatch must be classified as model-wrong, golden-wrong, or ambiguous with evidence. Silently accepting mismatches is a hard stop.
- **`/build-story`** (Phase 3, step 11b): Must prompt user to run `/verify-eval`. Cannot close story with unclassified mismatches. Only verified scores determine whether acceptance criteria are met.
- **`/validate`** (step 5b): Must run `/verify-eval` for structured investigation. Unclassified mismatches are a priority-high finding that caps grade at B.
- **`/mark-story-done`** (validation checklist): `/verify-eval` report must exist in work log with every mismatch classified. Golden-wrong findings must be fixed and evals re-run before closing.
- **`/verify-eval`** skill: The structured execution path for the investigation protocol. 5 phases: locate results → enumerate mismatches → classify → fix golden → report verified scores.

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Python scorer passes but LLM rubric fails | Golden is structurally correct but semantically shallow | Enrich descriptions, add missing context |
| Model scores well on one golden but poorly on another | Convention inconsistency across goldens | Standardize conventions, re-run |
| New model scores worse than expected | Golden may have evolved since last benchmark | Run a golden audit before concluding model is worse |
| Eval scores improved but output looks worse | Golden-wrong entries were being "correctly" matched by bad output | Re-audit the golden, check for phantom entries |
| Scorer reports extra entities that look valid | Golden is missing entities the source supports | Add missing entities after user confirmation |

## Lessons Learned

- 2026-03-01 — Created. CineForge adapted from Dossier's EntityGraph-specific runbook. Key difference: CineForge uses dual scoring (Python structural + LLM rubric) via promptfoo, not acceptance tests with P/R/F1.
- 2026-03-01 — Golden audit before model benchmark is non-negotiable. Discovered GPT-4.1's "winning" config-detection score was measured against 4 incorrect golden fields. After golden fix, Gemini 3 Flash won instead.
