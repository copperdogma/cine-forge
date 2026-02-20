# Liberty Church 2 Artifact Inventory and Character Cleanup Investigation

Date: 2026-02-19
Scope: Production project `liberty-church-2` (https://cineforge.copper-dog.com/liberty-church-2/characters)

## Evidence Snapshot

Primary fixture path:
- `tests/fixtures/liberty_church_2/prod_snapshot_2026-02-19/`

Captured artifacts include:
- Project/runs metadata: `project.json`, `runs.json`, `run-*_state.json`, `run-*_events.json`
- Artifact inventory: `artifact_groups.json`, `artifact_versions.json`, `artifact_details_latest.json`
- Per-character details: `character_details/*.json`
- Input payload capture: `input_content.txt` (text content read via project input endpoint)

## Run Context

| Run ID | Recipe | Started (epoch) | Finished (epoch) | Total Cost USD | Stage Summary |
|---|---|---:|---:|---:|---|
| `run-83dc50a6` | `mvp_ingest` | 1771528748.533674 | 1771529592.7232223 | 1.3631372 | `ingest` (1 ref), `normalize` (1), `extract_scenes` (29), `project_config` (1) |
| `run-b4d5ef1a` | `world_building` | 1771529724.7990286 | 1771530488.0087388 | 1.5039990 | `character_bible` (68 refs), `location_bible` (56), `prop_bible` (4) |

Local reproducibility runs executed:
- `lc2-local-ingest-actual-20260219` (`recipe-ingest-only.yaml`) completed successfully.
- `lc2-local-mvp-dryrun-20260219` (`recipe-mvp-ingest.yaml`) dry-run validated.
- `lc2-local-world-dryrun-20260219` (`recipe-world-building.yaml`) dry-run validated.
- `lc2-local-mvp-20260219` (full local mvp) stalled at `normalize` due network call with no request timeout in transport; terminated and recorded as blocker.

## Artifact Inventory

Total latest artifacts in prod snapshot: **160**

| Artifact Type | Count | Health (group API) | Health (payload metadata) | Lineage Pattern | Quick Quality Verdict |
|---|---:|---|---|---|---|
| `raw_input` | 1 | valid | valid | root (no lineage) | Good capture of source text |
| `canonical_script` | 1 | valid | needs_review | 1 upstream (`raw_input`) | Usable; marked needs review |
| `scene` | 28 | valid | 18 valid / 10 needs_review | 1 upstream (`canonical_script`) | Structurally present; quality mixed |
| `scene_index` | 1 | valid | needs_review | 29 upstream refs (all scenes + script) | Major source of character noise |
| `project_config` | 1 | valid | needs_review | 2 upstream (`canonical_script`, `scene_index`) | Usable draft; review needed |
| `character_bible` | 34 | valid | valid | 2 upstream (`canonical_script`, `scene_index`) | **Contaminated with non-characters** |
| `location_bible` | 28 | valid | valid | 2 upstream (`canonical_script`, `scene_index`) | Over-segmented location variants |
| `prop_bible` | 2 | valid | valid | 2 upstream (`canonical_script`, `scene_index`) | Likely under-extracted |
| `bible_manifest` | 64 | valid | valid | 2 upstream | Mirrors upstream quality issues |

### Inventory Notes

- Group-level health reports everything as `valid`, but payload metadata records `needs_review` for `canonical_script`, `scene_index`, `project_config`, and 10 scene artifacts. This mismatch can hide risk in list views.
- Character extraction quality is poor despite `health=valid`, so current health semantics are not sufficient for semantic correctness.

## Character Defect Catalog (False Positives)

The following entities were imported as characters but are not characters in narrative terms.

| Entity ID | Artifact Path | Why Incorrect | Likely Root Stage | Severity |
|---|---|---|---|---|
| `act_one` | `artifacts/character_bible/act_one/v1.json` | Act marker/structure token | `scene_extract_v1` cue/mention extraction | High |
| `act_two` | `artifacts/character_bible/act_two/v1.json` | Act marker/structure token | `scene_extract_v1` cue/mention extraction | High |
| `act_three` | `artifacts/character_bible/act_three/v1.json` | Act marker/structure token | `scene_extract_v1` cue/mention extraction | High |
| `act_four` | `artifacts/character_bible/act_four/v1.json` | Act marker/structure token | `scene_extract_v1` cue/mention extraction | High |
| `client_entertaining_outfit` | `artifacts/character_bible/client_entertaining_outfit/v1.json` | Wardrobe phrase treated as person | `scene_extract_v1` uppercase mention regex | High |
| `don_t_tell` | `artifacts/character_bible/don_t_tell/v1.json` | Dialogue fragment (“DON'T TELL”) | `scene_extract_v1` cue parsing + punctuation normalization | High |
| `memorize_this` | `artifacts/character_bible/memorize_this/v1.json` | Stage/dialogue phrase | `scene_extract_v1` cue parsing | High |
| `mmmmmm` | `artifacts/character_bible/mmmmmm/v1.json` | Vocalization/sound token | `scene_extract_v1` cue parsing | Medium |
| `nice_try` | `artifacts/character_bible/nice_try/v1.json` | Dialogue interjection | `scene_extract_v1` cue parsing | Medium |
| `obvious` | `artifacts/character_bible/obvious/v1.json` | Stylistic text token | `scene_extract_v1` mention extraction | Medium |
| `okay` | `artifacts/character_bible/okay/v1.json` | Dialogue interjection | `scene_extract_v1` cue parsing | Medium |
| `one` | `artifacts/character_bible/one/v1.json` | Numeric/dialogue token; payload describes Liliane (entity merge error) | `character_bible_v1` candidate sanitation + extraction prompt grounding | High |
| `shhhhhhhhhh` | `artifacts/character_bible/shhhhhhhhhh/v1.json` | Hushing sound, not person | `scene_extract_v1` cue parsing | Medium |
| `that_is_tennessee` | `artifacts/character_bible/that_is_tennessee/v1.json` | Full sentence fragment, not canonical character name | `scene_extract_v1` mention extraction | High |
| `together` | `artifacts/character_bible/together/v1.json` | Imperative dialogue token | `scene_extract_v1` cue parsing | Medium |
| `wait` | `artifacts/character_bible/wait/v1.json` | Interjection, not character identity | `scene_extract_v1` cue parsing | Medium |

Additional risk indicators:
- `scene_index.unique_characters` contains **54** values, many clearly non-character tokens (`COMPUTERS`, `PRINTERS`, `XIII CRYSTAL BOTTLE`, etc.).
- 34 character bibles were generated from that set, so upstream noise directly propagates into final character artifacts.

## Other Artifact Issues Found

1. Location fragmentation:
- Same narrative place is split by time/modifier into separate entities (e.g., `gemini_s_bar_1pm`, `gemini_s_bar_8_35am`, `gemini_s_bar_8_45pm`, `gemini_s_bar_street`).
- Likely over-segmentation from heading parsing without location normalization.

2. Prop under-extraction:
- Only 2 prop artifacts (`fiery_painting`, `motorola_cellphone`) despite a script with many tangible objects.
- Indicates high precision but low recall in prop extraction.

3. Health signaling mismatch:
- API artifact groups show all `valid`, while payload metadata embeds `needs_review` on core upstream artifacts.
- UI and operators can incorrectly assume semantic quality is green.

## Root-Cause Mapping by Stage

1. `scene_extract_v1` (primary root cause)
- `_looks_like_character_cue()` is too permissive for all-caps interjections/phrases.
- `_extract_character_mentions()` regex captures uppercase phrases in action lines that are not entities.
- `CHARACTER_STOPWORDS` is insufficient for script-specific noise.

2. `character_bible_v1` (secondary propagation)
- Candidate filter allows any entry with dialogue_count >= 1, preserving noisy cues.
- QA criteria (`accuracy`, `depth`, `vividness`) do not include identity validity (“is this a real character entity?”).
- Output can self-describe “not a character” yet still pass and persist as `character_bible`.

3. QA/health layer
- Health remains `valid` for semantically invalid character artifacts.
- No deterministic post-check exists to reject obvious non-character tokens before artifact write.

## Fix-Options Matrix

| Option | Approach | Pros | Cons | Recommended Order |
|---|---|---|---|---|
| A | Prompt/role hardening: strengthen scene + character prompts with explicit exclusions (act markers, interjections, props, set dressing) and canonicalization rules | Fastest to ship; low code churn | LLM compliance drift; brittle across scripts | 1 (quick guardrail) |
| B | Deterministic candidate filtering: tighten `_looks_like_character_cue`, expand stopword/phrase filters, reject sentence-like cues, and require evidence in scene_presence | Repeatable and cheap; blocks obvious garbage before LLM | Needs careful tuning to avoid false negatives | 1 (in parallel with A) |
| C | Semantic QA gate + reject/retry: add binary QA check `is_valid_character_entity`, auto-drop/repair failing entities, and mark health `needs_review` on uncertainty | Strongest correctness control; explicit quality signal | Higher latency/cost; QA prompt engineering needed | 2 (after A/B baseline) |

## Recommended Phased Remediation

Phase 1 (Immediate quality floor)
- Implement Option B deterministic guards in `scene_extract_v1` and `character_bible_v1`.
- Implement minimal Option A prompt constraints for both modules.
- Add unit fixtures from this snapshot (`scene_index.unique_characters` polluted set).

Phase 2 (Semantic gate)
- Add Option C QA contract for character identity validity.
- If QA says non-character, suppress artifact emit and log rejected candidate list.

Phase 3 (Health/reporting alignment)
- Align group-level health with payload metadata health.
- Expose rejected-candidate diagnostics in run artifacts for operator review.

## Implementation-Ready Follow-up Tasks

1. Add fixture regression test for Liberty Church polluted candidates
- Input: `scene_index.unique_characters` from fixture snapshot.
- Assert: explicit reject list includes act markers and dialogue interjections.

2. Tighten scene extraction candidate logic
- File: `src/cine_forge/modules/ingest/scene_extract_v1/main.py`
- Update `_looks_like_character_cue` and `_extract_character_mentions` with stricter boundaries.

3. Add deterministic identity gate before character bible generation
- File: `src/cine_forge/modules/world_building/character_bible_v1/main.py`
- Reject candidates matching phrase/interjection patterns; require stronger scene evidence.

4. Add QA criterion for entity validity and retry/drop logic
- Files: `src/cine_forge/modules/world_building/character_bible_v1/main.py`, `src/cine_forge/ai/qa.py`
- Criterion: “is this output actually a character entity?”

5. Reconcile health status surfacing
- Files: `src/cine_forge/api/service.py`, relevant UI readers in `ui/src/pages/`
- Ensure list views reflect effective health used by payload metadata.
