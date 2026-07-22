# Golden Reference Files — CineForge

Ground truth for CineForge's promptfoo eval suite. These files define "correct" —
if the model disagrees with the golden, one of them is wrong (and it's not always
the model).

## Self-Healing Eval Mandate

**When system output does not match a golden reference, EVERY discrepancy MUST be
investigated individually.**

- **Model is wrong** → the eval fails, the pipeline must be fixed
- **Golden is wrong** → update the golden, document the correction
- **Ambiguous** → flag for human review, do not auto-update

This makes the eval suite self-correcting. Golden references improve with every
eval run. No discrepancy is ever silently ignored or bulk-accepted.

See `/improve-eval` for the structured mismatch-classification and golden-fix protocol.

## Architecture: Scorer Reference Files

CineForge goldens are **scorer-side references**, not output schema mirrors. Each
golden contains evaluation criteria that the Python scorer checks against model
output. For example, the character golden has `key_traits` and `must_have_evidence`
— the scorer checks whether the model's output covers these criteria.

This means:
- Golden field names (`key_traits`, `must_mention_scenes`) differ from model output
  field names (`inferred_traits`, `scene_presence`)
- The scorer is the bridge between golden format and model output format
- When editing a golden, check the corresponding scorer to understand how each
  field is used: `benchmarks/scorers/{eval_name}_scorer.py`

## Golden Types

| File | Eval | Scorer | Schema Shape |
|------|------|--------|-------------|
| `the-mariner-characters.json` | character-extraction | `character_extraction_scorer.py` | Object keyed by character name |
| `the-mariner-locations.json` | location-extraction | `bible_extraction_scorer.py` | Object keyed by location name |
| `the-mariner-props.json` | prop-extraction | `bible_extraction_scorer.py` | Object keyed by prop name |
| `the-mariner-relationships.json` | relationship-discovery | `relationship_scorer.py` | `{must_find_relationships: [...]}` |
| `the-mariner-scenes.json` | scene-extraction | `scene_extraction_scorer.py` | `{scenes: [...], scene_count: N}` |
| `the-mariner-config.json` | config-detection | `config_detection_scorer.py` | `{fields: {field_name: criteria}}` |
| `continuity-extraction-golden.json` | continuity-extraction | `continuity_extraction_scorer.py` | Object keyed by scene key |
| `enrich-scenes-golden.json` | scene-enrichment | `scene_enrichment_scorer.py` | Object keyed by scene key |
| `normalize-signal-golden.json` | normalization | `normalization_scorer.py` | Flat object with structural rules |
| `qa-pass-golden.json` | qa-pass | `qa_pass_scorer.py` | Object keyed by test case key |
| `the-mariner-entity-discovery.json` | entity-discovery | `entity_discovery_scorer.py` | `{characters, locations, props}` category contracts |
| `the-mariner-script-bible.json` | script-bible | `script_bible_scorer.py` | Script-bible criteria object |
| `open-frequency-maya-character.json` | character-extraction | `character_extraction_scorer.py` | Focused object keyed by character name |
| `open-frequency-scenes.json` | scene-extraction | `scene_extraction_scorer.py` | `{title, scene_count, scenes}` |
| `open-frequency-entity-discovery.json` | entity-discovery | `entity_discovery_scorer.py` | `{characters, locations, props}` category contracts |
| `open-frequency-script-bible.json` | script-bible | `script_bible_scorer.py` | Script-bible criteria object |
| `normalize-open-frequency-corrupted-golden.json` | normalization | `normalization_scorer.py` | Flat structural and source-fidelity rules |

A separate unit test golden lives at `tests/fixtures/golden/the_mariner_scene_entities.json`.

## Per-Type Schemas

### Character Extraction (`the-mariner-characters.json`, `open-frequency-maya-character.json`)

Object keyed by character name (ALL CAPS). Each entry:

| Field | Type | Purpose |
|-------|------|---------|
| `character_id` | string | Slug ID, e.g. `"the-mariner"` |
| `name` | string | ALL CAPS name |
| `aliases` | string[] | Alternative names used in script |
| `narrative_role` | string | `"protagonist"` or `"supporting"` |
| `key_traits` | string[] | Trait descriptors the model must surface |
| `must_have_relationships` | object[] | `{target, type}` pairs |
| `must_mention_scenes` | string[] | Scene heading keywords |
| `must_have_evidence` | string[] | Direct textual evidence |
| `key_facts` | string[] | Narrative facts the model must recall |

**Relationship type enum:** `"sibling"`, `"parent"`, `"adversary"`,
`"romantic_ex"`, plus `"family"` when that relationship is stated directly in
the second-corpus source. Do not force a relationship into a golden when the
source leaves it ambiguous.

### Location Extraction (`the-mariner-locations.json`)

Object keyed by location name. Each entry:

| Field | Type | Purpose |
|-------|------|---------|
| `location_id` | string | Slug ID |
| `name` | string | Full scene-heading form |
| `aliases` | string[] | Alternate names |
| `physical_traits` | string[] | Expected physical descriptors |
| `must_mention_scenes` | string[] | Scene heading keywords |
| `key_facts` | string[] | Narrative facts |
| `narrative_significance_must_mention` | string[] | Required thematic keywords |

### Prop Extraction (`the-mariner-props.json`)

Object keyed by prop name. Same schema as locations plus `prop_id` and
`associated_characters`. Associations are exact source-verified lists of runtime
lowercase-underscore character IDs for persistent, continuity-critical owners or
wielders; brief contact does not qualify.

### Relationship Discovery (`the-mariner-relationships.json`)

Top-level: `{description, must_find_relationships, min_must_find, max_total_edges, false_positive_examples}`

Each relationship in `must_find_relationships`:

| Field | Type | Enum values |
|-------|------|-------------|
| `relationship_id` | string | Unique slug |
| `source_type` | string | `"character"`, `"prop"`, `"location"` |
| `source_id` | string | Entity slug |
| `target_type` | string | `"character"`, `"prop"`, `"location"` |
| `target_id` | string | Entity slug |
| `relationship_type_keywords` | string[] | Acceptable type labels |
| `direction` | string | `"symmetric"`, `"source_to_target"` |
| `must_mention_evidence` | string[] | Evidence strings |
| `min_confidence` | float | 0.0–1.0 |
| `importance` | string | `"critical"`, `"important"`, `"secondary"` |

### Scene Extraction (`the-mariner-scenes.json`, `open-frequency-scenes.json`)

Top-level: `{title, scene_count, scenes}`

Each scene:

| Field | Type | Enum values |
|-------|------|-------------|
| `scene_number` | int | 1-based |
| `heading` | string | Full heading |
| `int_ext` | string | `"INT"`, `"EXT"` |
| `location` | string | Location portion |
| `time_of_day` | string | Exact explicit heading value, such as `"DAY"`, `"NIGHT"`, `"PRE-DAWN"`, or `"MORNING"`; use `"UNSPECIFIED"` only when no supported direct inheritance exists |
| `summary` | string | Scene summary |
| `characters` | string[] | ALL CAPS names |

### Config Detection (`the-mariner-config.json`)

Top-level: `{description, fields}`

Each field entry has varying structure based on `match_type`:
- `"substring"` — `expected_value` string
- `"any_keyword"` — `expected_values` string[]
- `"keyword_overlap"` — `expected_keywords` string[], `must_include_at_least` int
- `"numeric_range"` — `expected_range` [min, max]
- `"list_contains"` — `must_include` string[]
- `"list_overlap"` — `should_include_any` string[], `min_count` int
- `"text_contains"` — `must_mention` string[]

Common fields: `match_type`, `min_confidence`, `importance` (`"critical"`, `"important"`, `"secondary"`)

### Entity Discovery (`the-mariner-entity-discovery.json`, `open-frequency-entity-discovery.json`)

Top-level: `{characters, locations, props}`. Each category contains:

| Field | Type | Purpose |
|-------|------|---------|
| `required` | string[] | Source-grounded entities every trustworthy inventory must find |
| `acceptable_aliases` | object | Canonical entity name to accepted source or normalization variants |
| `optional` | string[] | Source-supported borderline entities that may be included without a precision penalty |
| `excluded` | string[] | Explicit source nouns that this eval's category contract must reject |

Every alias-map key must appear in `required` or `optional`. Optional means
genuinely acceptable, not an unverified noun or an excuse to reward a noun dump.
Excluded entries are category-specific: for example, Open Frequency treats the
named dog COMET as scene presence rather than a person in its people-only character
inventory. `NORTH SHELTER` and the `OPEN FREQUENCY` door sign are documented
optional classifications; neither broadens the required inventory.

### Script Bible (`the-mariner-script-bible.json`, `open-frequency-script-bible.json`)

These scorer-side criteria define the exact title, required output fields, act
count bounds, supported genre/tone alternatives, source-specific logline,
protagonist, conflict, setting, and journey concepts, thematic keyword groups,
length bounds, and explicit exclusions. Keyword lists are alternatives unless the
corresponding scorer says otherwise; they must not encode a single preferred
wording as the only correct analysis.

Both screenplay contracts additionally list the exact source headings,
full-source story events, and forbidden unsupported claim patterns. Those fields
gate complete source coverage, real act boundaries, source-grounded theme evidence,
and absence of source-specific invented claims; they do not require the golden's
prose wording. For The Mariner, this includes the unresolved cut-to-black fight and
excludes absent dock or Newfoundland settings. Open Frequency excludes invented
deaths, romances, disaster causes, or complete recovery.

### Continuity Extraction (`continuity-extraction-golden.json`)

Object keyed by scene key. Each entry:

| Field | Type | Purpose |
|-------|------|---------|
| `expected_entities` | string[] | Entity keys in `"type:id"` format |
| `expected_properties` | object | Keyed by entity key → property specs |
| `expected_changes` | object | Keyed by entity key → change specs |
| `key_evidence` | string[] | Direct quotes from scene |
| `expected_confidence_range` | [float, float] | Expected confidence range |

### Scene Enrichment (`enrich-scenes-golden.json`)

Object keyed by scene key. Each entry:

| Field | Type | Enum values |
|-------|------|-------------|
| `heading` | string | Scene heading |
| `location` | string | Location string |
| `time_of_day` | string | `"DAY"`, `"NIGHT"`, `"UNSPECIFIED"` when the heading supplies no time |
| `int_ext` | string | `"INT"`, `"EXT"` |
| `characters_present` | string[] | Character names |
| `expected_tone` | string[] | Tone descriptors |
| `expected_beat_types` | string[] | Beat types (see enum below) |
| `key_details` | string[] | Key narrative details |

**Beat type enum:** `"character_introduction"`, `"revelation"`, `"conflict"`, `"comic_relief"`, `"thematic_statement"`, `"character_development"`, `"foreshadowing"`

### Normalization (`normalize-signal-golden.json`, `normalize-open-frequency-corrupted-golden.json`)

Flat object:

| Field | Type | Purpose |
|-------|------|---------|
| `description` | string | Human label |
| `expected_scenes` | string[] | Scene headings in output |
| `expected_characters` | string[] | Character names |
| `required_dialogue` | object[] | `{character, fragment}` pairs |
| `forbidden_patterns` | string[] | Regex patterns that must NOT appear |
| `structural_rules` | object | Boolean flags for Fountain compliance |

`preserve_source_action_order` and `preserve_source_transitions` opt a fixture into
strict source-token sequence checks after presentation corruption is normalized.
They are appropriate for a source-faithful cleanup fixture, not for prose-to-script
conversion where action may legitimately be rewritten.

### QA Pass (`qa-pass-golden.json`)

Object keyed by test case key (`"good_scene"`, `"bad_scene"`). Each entry:

| Field | Type | Purpose |
|-------|------|---------|
| `expected_passed` | bool | Expected pass/fail judgment |
| `max_errors` | int | (good only) Max acceptable errors |
| `max_warnings` | int | (good only) Max acceptable warnings |
| `required_in_summary` | string[] | (good only) Expected summary keywords |
| `min_errors` | int | (bad only) Min errors model must detect |
| `required_issues` | object[] | (bad only) `{field, reason}` pairs |

## Conventions

- **Slug IDs**: lowercase-hyphenated, no spaces or special chars (`"the-mariner"`, `"15th-floor"`)
- **Entity keys**: `"{type}:{id}"` format for continuity (`"character:billy"`, `"prop:oar"`)
- **Character names**: ALL CAPS in scene/character references
- **Confidence values**: float in `[0.0, 1.0]` everywhere
- **Source screenplay**: every golden must name a repo-owned source through its
  checklist and provenance record; do not assume all fixtures use The Mariner

## Second-Corpus Provenance

`open-frequency-corpus.provenance.json` records the canonical source path and
SHA-256 for the Open Frequency goldens. The benchmark tasks read the canonical
repo-authored source directly from
`tests/fixtures/ingest_inputs/open_frequency_short.fountain`, so a duplicate
benchmark copy cannot silently drift away from source truth.

The difficult normalization case is a deliberately corrupted, source-faithful
excerpt at `benchmarks/input/normalize-open-frequency-corrupted.fountain`. Its
provenance record lists each intentional formatting failure. The corruption may
change presentation only; dialogue wording, speakers, story facts, and event order
remain source truth.

## Workflow

- **Create golden**: `/golden-create` or manual (see `docs/runbooks/golden-build.md`)
- **Verify golden**: `/golden-verify` (adversarial, parallel subagents)
- **Validate structure**: `.venv/bin/python benchmarks/golden/validate-golden.py`
- **Reset for re-check**: `/golden-verify-reset`
- **Investigate mismatches**: `/improve-eval`
