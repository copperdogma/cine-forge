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
