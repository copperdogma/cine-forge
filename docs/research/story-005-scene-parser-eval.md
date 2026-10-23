# Story 005 Scene Parser Evaluation

Date: 2026-02-12

## Goal

Pick a deterministic-first parser strategy for `scene_extract_v1` that maximizes stability and minimizes AI cost.

## Candidates

| Candidate | License / Fit | Observed Benefit | Observed Risk | Decision |
| --- | --- | --- | --- | --- |
| `fountain-tools` (existing dependency) | Python package; already present in project dependencies | Provides parser-backed structural confidence signal (`parseable`, coverage) used as confidence gate before AI enrichment | Parse API is not yet a full scene-element AST contract in our code path | **Use as confidence signal now** |
| Regex/rule splitter (in-module) | Native code, no extra dependency | Deterministic scene splits, spans, element typing, and character normalization with predictable runtime | Lower fidelity on malformed headings and unusual screenplay formatting | **Primary extraction path with fallback guarantees** |
| `screenplain` parser path | CLI-first and currently used for export interoperability, not stable as direct Python parser API in this repo | Could improve cross-format interoperability in future | Additional integration complexity and unclear ROI for Story 005 scope | **Defer** |

## Selected Strategy

1. Use deterministic regex/rule extraction as the default scene parser path.
2. Use `fountain-tools` parse validation output as a confidence signal for provenance/health decisions.
3. Reserve AI calls for unresolved fields and ambiguity handling only.

## Acceptance Evidence

- Module: `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/ingest/scene_extract_v1/main.py`
- Validation signal: `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/ai/fountain_parser.py`
- Tests:
  - `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_extract_module.py`
  - `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_extract_benchmarks.py`
  - `/Users/cam/Documents/Projects/cine-forge/tests/integration/test_scene_extract_integration.py`


## 2026-10-23 — Compound tokens and heading separators

Problem class: parsing delimited fields without destroying punctuation inside
field values. The canonical Open Frequency run split PRE-DAWN into a location
suffix and DAWN, and the same regex splits hyphenated location names.

Reused the existing deterministic-first decision above and checked the primary
[Fountain syntax](https://fountain.io/syntax/): its scene-heading
examples use whitespace around structural dashes and preserve heading content.
Fountain defines heading recognition, not our location/time decomposition;
these examples support a conservative local delimiter choice, not a claim that
Fountain prescribes our finite time vocabulary.

Decision: keep punctuation inside tokens, split whitespace-delimited dashes,
retain the existing recognized-time and narrative-modifier rules, and recognize
the observed PRE-DAWN token explicitly. Unknown labels remain unspecified;
no model should infer over an exact source-copy task. Do not add legacy parsing
branches for the old destructive split. Reproduce on the existing canonical
fixture plus a compound-location regression, then validate actual module scene
and index outputs. Remaining uncertainty: informal unspaced separators and
nonstandard time phrases are ambiguous; this bounded repair does not claim a
complete screenplay-heading grammar.

Baseline and local verification: docs/reports/story-005-heading-delimiters/.

Local result: all50 focused tests passed; dynamic execution against the actual
normal canonical artifact produced the corrected scene/index with source span
68–102, no provider calls and unchanged historical artifacts. Exact before/after
provenance and the corrected baseline capture are documented in the report.
