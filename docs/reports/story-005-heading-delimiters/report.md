# Story005 reopened slice — heading delimiter validation

No material source or evidence findings remain after independent review. The
parser preserves intra-word hyphens and recognizes PRE-DAWN, so the canonical
shelter scene no longer invents a location ending in Pre.

## Baseline and repair

The fresh229 runtime scene003/v1 has location High School Gym Shelter - Pre and
time DAWN. baseline.json now replays that exact failure from Git714802a's
original function/constants, retained in baseline-parser-source.py.txt, and
matches the unchanged real v1 artifact hash. A later parent verification probe
accidentally overwrote the first capture with current code; the correction is
explicit in baseline.json. Independent review verified the old source, replay
and original-artifact match. No historical runtime artifact was edited.

Five new regression cases failed before the repair (four compound/delimiter
cases plus the canonical module fixture). All36 module tests now pass. The
focused grammar/constants moved out of893-line main.py into58-line heading.py;
main is836 lines and uses an absolute import suitable for driver loading.
There is no old wrapper or fallback parser path.

## Actual input and semantic inspection

normal-canonical-proof.json and normal-canonical-module-output.json use the
exact normalized canonical_script/project/v1 from fresh normal Open Frequency,
not a hand-seeded project. The installed Fountain parser ran. The module was
loaded with spec_from_file_location/exec_module, then executed in mock AI mode
with call_llm explicitly forbidden. This is deterministic extraction evidence;
it does not evaluate entity-model quality or claim fresh UI/full FP1 acceptance.

Four Scene payloads and the SceneIndex validate. Scene003 and its index entry
both have High School Gym Shelter / PRE-DAWN, source lines68–102, and preserve
the original heading. Its first action still describes the shelter cots and
medicine/meals/messages signs; location/time provenance remains rule-based.
The aggregate locations are Community Radio Studio, High School Gym Shelter,
and Water Tower Catwalk. Cost and call count are zero. Original canonical
artifact bytes and all earlier v1 scene artifacts remain unchanged.

The separate unit-fixture probe uses the raw short fixture as module input,
with a mocked parser confidence signal, and therefore reports source lines63–95.
These are positions in two different supplied texts, not contradictory spans.
The real-normalized proof above establishes the actual current artifact boundary.

## Validation

- 50 focused tests passed: test_scene_breakdown_module.py,
  test_scene_breakdown_model_selection.py, test_scene_breakdown_telemetry.py,
 and test_scene_schema.py. Full source/test Ruff passed.
- Real-parser dynamic import/execution and Scene/SceneIndex validation passed.
- Driver recipe dry-run passed for recipe-mvp-ingest, canonical input,
 default_model=mock and --accept-config, run story-005-heading-dry-run-2.
 The first dry-run omitted required accept_config and failed before any stage;
 the corrected run uses a new ID and produced no artifacts/provider calls.
- Strong independent source/evidence review cleared after the baseline repair.
 Additional scoped Codex CLI review found no regressions; it independently ran
 module tests, Ruff and dynamic-import checks. Raw transcript remains under
 output/story-005-codex-review.txt.
- Methodology compile/check and current immutable contract validation are
 recorded in the story close-out; no paid eval or numeric model score changed.
- No UI source changed in this slice. Earlier229/230 browser evidence remains
 separate; this parser fix does not claim a completed scene render.

## Scope and remaining uncertainty

Reused005's deterministic-first parser decision and checked official Fountain
heading examples. Spaced dashes separate fields; intra-word hyphens remain
content. Fountain does not prescribe this whole location/time grammar. Unknown
suffixes keep existing conservative unspecified-time behavior, while narrative
modifiers and multi-segment locations retain their meaning. Informal unspaced
separators and arbitrary time phrases are outside this bounded grammar claim.
No new AI/decision model, schema or provider default was introduced.

The Bible's unsupported American-country assertion from229 remains a separate
model-wrong/non-runtime-blocking observation. This repair addresses literal
heading extraction only and does not turn green QA-count fields into semantic
proof. No scored acceptance eval was run.

Learning review considered: the baseline overwrite was a local violation of
existing fixture-first/provenance discipline. Corrected the record using exact
old bytes and independent replay; no new live workflow or memory was changed.

All current-slice ACs are met. Grade A; close this reopened slice. Optional
verification: inspect normal-canonical-proof.json or run the focused module
unit tests. The old UI project's v1 output intentionally retains its before
state; newly extracted outputs use the repaired parser.
