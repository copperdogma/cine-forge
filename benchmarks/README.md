# CineForge Model Benchmarking

Systematic evaluation of AI models across all pipeline tasks using [promptfoo](https://www.promptfoo.dev/).

## Quick Start

```bash
# Prerequisites: Node 24 LTS, promptfoo installed globally
source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1

# Run a benchmark
cd benchmarks/
promptfoo eval -c tasks/character-extraction.yaml --no-cache -j 3

# View results
promptfoo view
```

See `AGENTS.md > Model Benchmarking (promptfoo)` for full setup and pitfalls.

---

## Complete AI Task Map

Every AI call point in the CineForge pipeline, classified by module and try-validate-escalate role.

### Legend

- **Try (Work)**: Initial generation pass. Benchmark for quality/cost tradeoff.
- **Verify (QA)**: Validation pass. Benchmark for judgment accuracy.
- **Escalate**: Retry with stronger model after QA failure. Benchmark for recovery quality.
- **Code**: Deterministic step (no AI). Not benchmarked.

### Summary

| # | Module | Task | TVE Role | Input Shape | Output | Default Model | Eval Priority |
|---|--------|------|----------|-------------|--------|---------------|---------------|
| 1 | script_normalize | Full conversion | Try | Full script (chunked if long) | Fountain text | gpt-4o | HIGH |
| 2 | script_normalize | Passthrough cleanup | Try | Full screenplay | SEARCH/REPLACE patches | gpt-4o | MEDIUM |
| 3 | script_normalize | Metadata extraction | Try | Source + output (4000 chars each) | JSON envelope | gpt-4o | LOW |
| 4 | script_normalize | QA with repairs | Verify | Source + prompt + output | QARepairPlan | gpt-4o-mini | MEDIUM |
| 5 | scene_extract | Boundary validation | Verify | Single scene chunk | Boolean + confidence | gpt-4o | LOW |
| 6 | scene_extract | Scene enrichment | Try | Scene text + deterministic data | Enrichment JSON | gpt-4o | MEDIUM |
| 7 | scene_extract | Scene QA | Verify | Scene text + extraction output | QAResult | gpt-4o-mini | LOW |
| 8 | project_config | Config detection | Try | Full script + scene summary | 10-field config | gpt-4o | MEDIUM |
| 9 | project_config | Detection QA | Verify | Condensed metadata + output | QAResult | gpt-4o-mini | LOW |
| 10 | character_bible | Character extraction | Try | Full script + char metadata | CharacterBible | gpt-4o-mini | HIGH |
| 11 | character_bible | Character QA | Verify | Script (5000 chars) + output | QAResult | gpt-4o-mini | MEDIUM |
| 12 | character_bible | Character re-extract | Escalate | Full script + QA feedback | CharacterBible | gpt-4o | LOW |
| 13 | location_bible | Location extraction | Try | Full script + loc metadata | LocationBible | gpt-4o-mini | HIGH |
| 14 | location_bible | Location QA | Verify | Script (5000 chars) + output | QAResult | gpt-4o-mini | LOW |
| 15 | location_bible | Location re-extract | Escalate | Full script + QA feedback | LocationBible | gpt-4o | LOW |
| 16 | prop_bible | Prop discovery | Try | Script (5000 chars) | Plain text list | gpt-4o-mini | MEDIUM |
| 17 | prop_bible | Prop extraction | Try | Full script + prop name | PropBible | gpt-4o-mini | HIGH |
| 18 | prop_bible | Prop QA | Verify | Script (5000 chars) + output | QAResult | gpt-4o-mini | LOW |
| 19 | prop_bible | Prop re-extract | Escalate | Full script + QA feedback | PropBible | gpt-4o | LOW |
| 20 | entity_graph | Relationship discovery | Try | Entity name lists | EdgeList | gpt-4o-mini | MEDIUM |
| 21 | continuity_tracking | State snapshots | Try | **STUBBED** | ContinuityState | — | SKIP |

**21 total AI call points. 20 active, 1 stubbed.**

---

## Detailed Task Descriptions

### 1. Script Normalization — Full Conversion (HIGH)

**Module**: `script_normalize_v1` | **Role**: Try

Converts raw prose or non-standard screenplay text into canonical Fountain format. This is the most complex AI task — it must preserve author voice while reformatting into screenplay structure.

- **Input**: Full source text. For long docs (>2000 tokens), chunked with 350-token overlap and running metadata (characters, locations, style notes, narrative summary).
- **Output**: Raw Fountain screenplay text (not JSON).
- **Prompt**: System message establishes "professional script supervisor" role. Strategy-specific instructions for `full_conversion` vs `passthrough_cleanup`.
- **Params**: `max_tokens=16000`, escalates to 1.5x on truncation. `temperature=0.0`.
- **Escalation**: Attempt 0 uses `work_model`, attempt 1+ uses `escalate_model` with feedback from prior failure.

**Eval approach**: Compare normalized output against hand-validated Fountain reference. Score on: structural correctness (heading format, cue format), content preservation (no hallucinated lines), completeness (no dropped scenes/dialogue).

### 2. Script Normalization — Passthrough Cleanup (MEDIUM)

**Module**: `script_normalize_v1` | **Role**: Try (alternative path)

For input already in screenplay format (confidence >= 0.8), generates minimal SEARCH/REPLACE patches rather than full rewrite.

- **Input**: Full screenplay text.
- **Output**: SEARCH/REPLACE patch blocks.
- **Post-processing**: Patches applied with fuzzy matching (threshold 0.85).

**Eval approach**: Measure patch precision (correct edits only, no regressions). Harder to benchmark — need known-imperfect screenplay inputs with known-correct fixes.

### 3. Normalization Metadata Extraction (LOW)

**Module**: `script_normalize_v1` | **Role**: Try (auxiliary)

Documents the AI's interpretive choices during normalization: inventions, assumptions, confidence.

- **Input**: Source content (4000 chars) + produced screenplay (4000 chars).
- **Output**: JSON with `inventions[]`, `assumptions[]`, `overall_confidence`, `rationale`.
- **Params**: `max_tokens=1200`.

**Eval approach**: Verify metadata accuracy against known normalization decisions. Lower priority — transparency feature, not core quality.

### 4. Normalization QA with Repairs (MEDIUM)

**Module**: `script_normalize_v1` | **Role**: Verify

Reviews normalization output for errors and generates targeted SEARCH/REPLACE repair patches.

- **Input**: Original source + normalization prompt + produced output.
- **Output**: `QARepairPlan` with `qa_result` (pass/fail + issues) and `edits[]` (search/replace/rationale).
- **Params**: `max_tokens=1800`.

**Eval approach**: Seed with known-good and known-bad normalization outputs. Score on: true positive rate (catches real errors), false positive rate (doesn't flag correct output), repair quality (patches actually fix the issue).

### 5. Scene Boundary Validation (LOW)

**Module**: `scene_extract_v1` | **Role**: Verify (conditional)

Only called for scenes with uncertain boundaries (no proper heading). Assesses whether a chunk represents a sensible scene break.

- **Input**: Single scene chunk text + scene number.
- **Output**: `{is_sensible: bool, confidence: float, rationale: str}`.
- **Params**: `max_tokens=300`.

**Eval approach**: Create test set of correct and incorrect scene splits. Binary classification task — score on accuracy, precision, recall.

### 6. Scene Enrichment (MEDIUM)

**Module**: `scene_extract_v1` | **Role**: Try (conditional)

Fills in metadata that deterministic extraction couldn't resolve: narrative beats, tone/mood, missing locations, characters.

- **Input**: Scene text + current deterministic payload + list of unresolved fields.
- **Output**: `_EnrichmentEnvelope` with narrative_beats, tone_mood, tone_shifts, heading, location, time_of_day, int_ext, characters_present.
- **Params**: `max_tokens=900`. QA feedback appended on retry.

**Eval approach**: Provide scenes with known metadata. Score on field accuracy (location, time_of_day match reference), narrative beat quality (LLM rubric), character completeness.

### 7. Scene QA (LOW)

**Module**: `scene_extract_v1` | **Role**: Verify

Per-scene QA checking character completeness, location accuracy, element fidelity, inference quality.

- **Input**: Scene source + extraction approach + scene artifact JSON.
- **Output**: `QAResult`.
- **Criteria**: `["character completeness", "location accuracy", "element fidelity", "inference quality"]`.

**Eval approach**: Same QA seeding pattern — known-good and known-bad scene extractions.

### 8. Project Config Detection (MEDIUM)

**Module**: `project_config_v1` | **Role**: Try

Auto-detects project metadata: title, format, genre, tone, duration, characters, locations, audience.

- **Input**: Full script text + condensed scene index summary.
- **Output**: 10-field `_DetectedConfigEnvelope`, each field with value + confidence + rationale.
- **Params**: `max_tokens=1800`.

**Eval approach**: Use known screenplays with verified metadata. Score on field accuracy per-field (title exact match, genre overlap, duration within 10%).

### 9. Project Config QA (LOW)

**Module**: `project_config_v1` | **Role**: Verify

Checks detection plausibility: confidence scores align with certainty, rationales are non-fabricated.

- **Input**: Condensed metadata + detection prompt + detection output.
- **Output**: `QAResult`.

### 10. Character Bible Extraction (HIGH) ★ Benchmark exists

**Module**: `character_bible_v1` | **Role**: Try

Extracts comprehensive character definition from full screenplay.

- **Input**: Full script text + character metadata (scene count, dialogue count, scene presence).
- **Output**: `CharacterBible` with traits, evidence, relationships, narrative role, confidence.
- **Schema fields**: character_id, name, aliases, description, explicit_evidence[], inferred_traits[], scene_presence[], dialogue_summary, narrative_role, narrative_role_confidence, relationships[], overall_confidence.

**Eval approach**: ★ Already built in Story 035. Python scorer (10 dimensions) + LLM rubric. Golden references for The Mariner characters.

### 11. Character Bible QA (MEDIUM)

**Module**: `character_bible_v1` | **Role**: Verify

Reviews character extraction for accuracy, depth, vividness.

- **Input**: Script (first 5000 chars) + CharacterBible JSON.
- **Output**: `QAResult`.
- **Criteria**: `["accuracy", "depth", "vividness"]`.

### 12-15. Bible Extraction Pattern (Location, Prop) (HIGH / LOW)

Location and prop bibles follow the exact same try-verify-escalate pattern as character bibles. See tasks 13, 14, 15 (location) and 17, 18, 19 (prop).

**Key structural similarity**: All bible modules use:
- Same `qa_check()` function from `cine_forge.ai.qa`
- Same escalation pattern (work → QA → escalate with feedback)
- Same model defaults (work=gpt-4o-mini, verify=gpt-4o-mini, escalate=gpt-4o)
- Same prompt structure ("You are a {role} analyst. Extract a master definition for {entity}...")

### 16. Prop Discovery (MEDIUM)

**Module**: `prop_bible_v1` | **Role**: Try (discovery)

Identifies significant props from script excerpt. Unlike other bible tasks, this is a discovery/enumeration task, not extraction.

- **Input**: First 5000 chars of script.
- **Output**: Plain text list (one prop per line).

**Eval approach**: Score on recall (finds all significant props) and precision (doesn't include noise). Compare against hand-curated prop list.

### 20. Entity Relationship Discovery (MEDIUM)

**Module**: `entity_graph_v1` | **Role**: Try (single-pass, no QA)

Finds narrative relationships missed by individual bible extractions. Explicitly limited to 3-5 high-impact relationships.

- **Input**: Comma-separated lists of character, location, and prop names.
- **Output**: `EdgeList` (list of `EntityEdge` with source/target, relationship type, evidence, confidence).
- **Prompt**: Focuses on familial links, secret rivalries, prop ownership, character-location associations.

**Eval approach**: Score on relationship validity (evidence-grounded), novelty (not already in bible stubs), and graph coherence.

### 21. Continuity State Snapshots (SKIP)

**Module**: `continuity_tracking_v1` | **Role**: STUBBED

Not implemented — returns empty data in production mode. Skip until module is built.

---

## Shared Scorer Opportunities

### 1. Bible Extraction Scorer (character, location, prop)

All three bible modules produce structurally similar output. A parameterized scorer can handle all three:

- **JSON validity** (0.10): Valid JSON, no markdown fences needed
- **Field completeness** (0.10): All required schema fields present and non-empty
- **Entity identification** (0.10): Correct name, aliases, ID
- **Evidence grounding** (0.15): Claims supported by specific script references
- **Scene coverage** (0.10): Scene presence matches reference
- **Quality dimensions** (0.15): Task-specific — traits for characters, physical attributes for locations, narrative significance for props
- **Relationship accuracy** (0.10): For characters; skip for locations/props
- **Confidence calibration** (0.05): Confidence scores correlate with actual accuracy
- **Semantic depth** (0.15): LLM rubric for insight quality

The existing `character_extraction_scorer.py` can be generalized.

### 2. QA Task Scorer (all verify passes)

All QA tasks use the same `qa_check()` function and produce `QAResult`. A shared QA scorer would:

- Seed known-good outputs → verify QA passes them (true negative rate)
- Seed known-bad outputs → verify QA catches them (true positive rate)
- Score on: detection accuracy, issue severity calibration, false positive rate, repair quality (for normalization QA)

### 3. Normalization Scorer (unique)

Script normalization produces text output, not JSON. Needs custom scorer:

- **Structural validity**: Scene headings, character cues, dialogue blocks properly formatted
- **Content preservation**: No hallucinated lines, no dropped scenes/dialogue
- **Completeness**: All source content represented in output
- **Fountain compliance**: Parseable by fountain-tools

### 4. Classification Scorer (boundary validation, config detection)

Simple classification/detection tasks. Score on accuracy, precision, recall, confidence calibration.

---

## Golden Reference Strategy

### Available Test Input

Currently: `input/the-mariner.md` (full screenplay, The Mariner)

### Golden References Needed

| Task Group | Golden File | Source | Status |
|------------|-------------|--------|--------|
| Character extraction | `golden/the-mariner-characters.json` | Hand-crafted | DONE (Story 035) |
| Location extraction | `golden/the-mariner-locations.json` | Hand-crafted | DONE |
| Prop extraction | `golden/the-mariner-props.json` | Hand-crafted | DONE |
| Entity relationships | `golden/the-mariner-relationships.json` | Hand-crafted | DONE |
| Scene enrichment | `golden/the-mariner-scenes-enriched.json` | Hand-craft sample scenes | TODO |
| Normalization | `golden/the-mariner-normalized.fountain` | Validated Fountain output | TODO |
| Project config | `golden/the-mariner-config.json` | Hand-crafted | DONE (needs calibration — see notes) |
| Prop discovery | `golden/the-mariner-prop-list.json` | Hand-craft list | TODO |
| QA tasks | `golden/qa-seeds/` directory | Known-good + known-bad pairs | TODO |

### Golden Reference Quality Standard

- Hand-crafted or expert-validated (never AI-generated without human review)
- Include both "must have" items (recall targets) and "must not have" items (precision targets)
- Document reasoning for each golden item
- Version-controlled alongside benchmark configs

---

## Eval Priority and Ordering

### Phase 2A — High Priority (build first)

These tasks have the most model variance and highest production impact:

1. **Character extraction** (already done) — extend with all 10 models
2. **Location extraction** — reuse bible scorer pattern
3. **Prop extraction** — reuse bible scorer pattern
4. **Script normalization** — unique scorer, highest complexity

### Phase 2B — Medium Priority

5. **Scene enrichment** — conditional task, needs varied test scenes
6. **Project config detection** — multi-field scoring
7. **Prop discovery** — enumeration task
8. **Entity relationship discovery** — graph quality scoring
9. **Normalization QA** — seeded good/bad pairs

### Phase 2C — Low Priority / Deferred

10. **Character/location/prop QA** — shared QA scorer
11. **Scene boundary validation** — binary classification
12. **Scene QA** — shared QA scorer
13. **Config QA** — shared QA scorer
14. **Metadata extraction** — transparency feature
15. **Escalation passes** — only measure if try-model fails frequently

---

## Model Matrix

All evals run across these models (as of Feb 2026):

**OpenAI** (`openai:` prefix):
| Model ID | Tier | Notes |
|----------|------|-------|
| `openai:gpt-4.1-nano` | Cheapest | May truncate on long outputs |
| `openai:gpt-4.1-mini` | Budget | Good quality/cost ratio |
| `openai:gpt-4.1` | Mid | Strong general purpose |
| `openai:gpt-5.2` | SOTA | Highest quality, expensive |

**Anthropic** (`anthropic:messages:` prefix):
| Model ID | Tier | Notes |
|----------|------|-------|
| `anthropic:messages:claude-haiku-4-5-20251001` | Budget | Fast, may struggle with complex JSON |
| `anthropic:messages:claude-sonnet-4-5-20250929` | Mid | Strong reasoning |
| `anthropic:messages:claude-opus-4-6` | SOTA | Best reasoning, expensive |

**Google** (`google:` prefix, uses `GEMINI_API_KEY`):
| Model ID | Tier | Notes |
|----------|------|-------|
| `google:gemini-2.5-flash-lite` | Cheapest | Lightweight, fast |
| `google:gemini-2.5-flash` | Mid | Good speed/quality |
| `google:gemini-2.5-pro` | Mid-High | Strong reasoning |
| `google:gemini-3-flash-preview` | Mid | Latest generation, preview |
| `google:gemini-3-pro-preview` | SOTA | Latest generation, preview |

**Judge model**: `anthropic:messages:claude-opus-4-6` (for all LLM rubric assertions).

---

## Workspace Structure

```
benchmarks/
├── README.md              # This file
├── .gitignore             # __pycache__/, *.pyc
├── tasks/                 # promptfoo YAML configs (one per eval task)
│   ├── character-extraction.yaml   # 12 providers × 3 tests
│   ├── location-extraction.yaml    # 12 providers × 3 tests
│   ├── prop-extraction.yaml        # 12 providers × 3 tests
│   ├── relationship-discovery.yaml # 12 providers × 1 test
│   ├── config-detection.yaml       # 12 providers × 1 test
│   └── scene-extraction.yaml       # Story 035 reference only
├── prompts/               # Prompt templates with {{variable}} placeholders
│   ├── character-extraction.txt
│   ├── location-extraction.txt
│   ├── prop-extraction.txt
│   ├── relationship-discovery.txt
│   ├── config-detection.txt
│   └── scene-extraction.txt        # Reference only
├── golden/                # Hand-crafted reference data
│   ├── the-mariner-characters.json
│   ├── the-mariner-locations.json
│   ├── the-mariner-props.json
│   ├── the-mariner-relationships.json
│   ├── the-mariner-config.json
│   └── the-mariner-scenes.json     # Reference only
├── scorers/               # Python scoring scripts
│   ├── bible_extraction_scorer.py  # Generalized for character/location/prop
│   ├── character_extraction_scorer.py
│   ├── relationship_scorer.py
│   ├── config_detection_scorer.py
│   └── scene_extraction_scorer.py  # Reference only
├── input/                 # Test input files
│   └── the-mariner.md     # Full screenplay (436 lines)
├── results/               # JSON output from eval runs (multiple runs per task)
│   ├── character-extraction-run{1,2,3}.json
│   ├── location-extraction-run{1,2}.json
│   ├── prop-extraction-run{1,2}.json
│   ├── relationship-discovery-run1.json
│   └── config-detection-run1.json
└── scripts/               # Analysis helpers
    ├── analyze-all-results.mjs
    ├── analyze-run.mjs
    ├── investigate.mjs
    └── check-grader.mjs
```

---

## Adding a New Eval

When a new AI-powered module lands or you're building a new eval:

1. Copy test input to `input/` (if new)
2. Create golden reference in `golden/` (hand-crafted, expert-validated)
3. Write prompt template in `prompts/` (use `{{var}}` placeholders, avoid `---` delimiter)
4. Write Python scorer in `scorers/` (implement `get_assert(output, context)`)
5. Create promptfoo config in `tasks/` (all providers x test cases x dual assertions)
6. Run: `promptfoo eval -c tasks/<name>.yaml --no-cache -j 3`
7. Analyze results, pick models, update defaults in `src/cine_forge/schemas/models.py`

**Always use dual evaluation**: Python scorer (structural) + LLM rubric (semantic). Both must pass.

---

## Results Summary (Feb 2026)

5 eval types × 12 models = 60 evaluations. All results in `results/` directory.

### Model Rankings by Task

**Character Extraction** (3 test cases per model, hardest discriminator: DAD flashback character):

| Rank | Model | Avg Py Score | LLM Pass |
|------|-------|-------------|----------|
| 1 | Claude Opus 4.6 | 0.916 | 3/3 |
| 2 | GPT-5.2 | 0.885 | 2/3 |
| 3 | Claude Sonnet 4.5 | 0.859 | 3/3 |
| 4 | Gemini 3 Pro | 0.848 | 3/3 |
| 5 | GPT-4.1 | 0.829 | 3/3 |
| 12 | GPT-4.1 Nano | 0.590 | 0/3 |

**Location Extraction** (3 test cases, discriminator: COASTLINE dual-presentation):

| Rank | Model | Avg Py Score | LLM Pass |
|------|-------|-------------|----------|
| 1 | Gemini 2.5 Pro | 0.847 | 3/3 |
| 2 | Claude Sonnet 4.5 | 0.833 | 3/3 |
| 3 | Claude Opus 4.6 | 0.830 | 3/3 |

**Prop Extraction** (3 test cases, discriminator: FLARE GUN least prominent):

| Rank | Model | Avg Py Score | LLM Pass |
|------|-------|-------------|----------|
| 1 | Claude Sonnet 4.5 | 0.861 | 3/3 |
| 2 | Claude Opus 4.6 | 0.826 | 3/3 |
| 3 | Gemini 2.5 Pro | 0.806 | 3/3 |

**Relationship Discovery** (1 test case, 7 must-find relationships):

| Rank | Model | Py Score | LLM Score |
|------|-------|----------|-----------|
| 1 | 6-way tie (Haiku, Sonnet, Opus, Gemini 2.5 Flash/Pro, Gemini 3 Flash) | 0.990 | 0.95-1.00 |
| 7 | GPT-4.1 | 0.977 | 0.95 |
| 12 | Gemini 2.5 Flash Lite | 0.000 | 0.30 |

**Config Detection** (1 test case, 10 metadata fields):

| Rank | Model | Py Score | LLM Score | Notes |
|------|-------|----------|-----------|-------|
| 1 | Gemini 2.5 Flash Lite | 0.912 | 0.85 | ⚠ Inverted ranking — see notes |
| 2 | GPT-4.1 Nano | 0.882 | 0.68 | |
| 3 | Claude Haiku 4.5 | 0.873 | 0.90 | Best LLM rubric score |

⚠ **Config detection golden reference needs calibration**: The 436-line screenplay is ~10-15 formatted pages, not a full-length feature. SOTA models correctly identify it as "short film" but score lower because our golden expects "feature film". Cheap models naively match the golden and score higher. This inverted ranking reflects a golden reference issue, not model quality.

### Task-Specific Model Selections

Each task gets its own try-validate-escalate triad based on actual benchmark data:

| Task | Try (work_model) | Verify (QA) | Escalate |
|------|-------------------|-------------|----------|
| Character extraction | Claude Sonnet 4.5 (#3, 0.859) | Claude Haiku 4.5 | Claude Opus 4.6 (#1, 0.916) |
| Location extraction | **Gemini 2.5 Pro** (#1, 0.847) | Claude Haiku 4.5 | Claude Sonnet 4.5 (#2, 0.833) |
| Prop extraction | Claude Sonnet 4.5 (#1, 0.861) | Claude Haiku 4.5 | Claude Opus 4.6 (#2, 0.826) |
| Relationship discovery | Claude Haiku 4.5 (#1 tied, 0.990) | Code-based | Claude Sonnet 4.5 |
| Config detection | Claude Haiku 4.5 (best LLM: 0.90) | Code-based | Claude Sonnet 4.5 |

See `docs/stories/story-036-model-selection.md` for full task-specific rationale and inferred selections for unbenchmarked tasks.

### Key Findings

1. **Anthropic dominates the CineForge workload**: Top spots across 4/5 eval types.
2. **Gemini 2.5 Pro is a strong alternative**: #1 on locations, #3 on props.
3. **Extended thinking is a reliability risk**: Gemini Flash models truncate JSON output even with `maxOutputTokens: 16384`.
4. **GPT-4.1 Nano is insufficient for all tasks**: Last or near-last on every eval.
5. **Dual evaluation is essential**: GPT-4.1 Mini passes Python scorers but fails LLM rubric — structural quality without semantic depth.
6. **Gemini 3 preview models are NOT better than 2.5 Pro**: Preview quality may improve at GA.
