# Story 064 — Screenplay Format Round-Trip: Converter Upgrade + Fidelity Test Suite

**Priority**: Medium
**Status**: Done
**Spec Refs**: 4 Ingestion, Normalization, Config
**Depends On**: 003, 006, 062

## Goal

Upgrade our screenplay format converters (Fountain→PDF, FDX→Fountain→FDX) to industry-standard
quality, then build a golden-master round-trip test suite that quantifies fidelity loss at every
link in the conversion chain. The converters must be usable from the CLI/backend — not wired
only into the UI.

**Why round-trip testing?** It's the fastest way to surface conversion bugs. Start from a known-
good source, convert, convert back, compare. Structural drift — scenes lost, characters renamed,
dialogue truncated — shows up immediately without requiring a human reviewer on every run.

## Acceptance Criteria

### Phase 1 — Research Spike
- [x] Afterwriting evaluated as a Fountain→PDF backend: quality, subprocess invokability from Python, maintenance status
- [x] pdfplumber evaluated as a PDF→text extraction backend vs our current pdftotext/pypdf stack on all three golden PDFs
- [x] Any other Fountain→PDF or PDF→Fountain libraries researched and noted
- [x] Spike conclusions written up in this work log (recommend, reject, or defer for each candidate)

### Phase 2 — Converter Upgrade
- [x] Fountain→PDF backend upgraded (or confirmed current stack is sufficient based on spike findings)
- [x] FDX→Fountain→FDX round-trip verified to be lossless on the three golden samples
- [x] Upgraded converters are invokable via Python API (`export_screenplay_text()`) and not gated behind UI code paths
- [x] Existing export API (`GET /projects/{id}/export`) continues to work

### Phase 3 — Round-Trip Test Suite
- [x] Golden master fixtures committed for all three scripts (Big Fish, Brick & Steel, The Last Birthday Card) in each format (.fdx, .fountain, .pdf)
- [x] Golden metadata JSON committed for each: scene count, character list, word count — extracted from the `.fountain` ground truth
- [x] Round-trip test A passes: **Fountain → PDF → Fountain** — scene count within 2%, character names preserved, dialogue word count within 5%
- [x] Round-trip test B passes: **FDX → Fountain → FDX** — lossless on scene headings and dialogue (structural XML diff, not byte diff)
- [x] Round-trip test C passes: **PDF → Fountain → PDF** — scene count within 5% (most forgiving; PDF extraction is lossy)
- [x] Tests run under `pytest -m round_trip` and are excluded from normal unit runs
- [x] Fidelity report printed to stdout per test: what was lost, what was preserved

### Phase 4 — UI Fidelity and Display
- [x] UI updated to favor `canonical_script` content over `raw_input` once normalization is complete.
- [x] UI includes visual indicator (badge) for whether the displayed screenplay is the original raw input or the normalized canonical version.
- [x] Investigation: verify if `script_normalize_v1` should automatically "promote" its output to the primary view in the UI or if this is a stateless transition based on artifact existence.

## Out of Scope

- Pixel-perfect PDF comparison (impossible; fonts and layout differ across renderers)
- OCR path testing (scanned PDFs are a separate problem)
- UI changes (export UI already calls the same backend; no UI work needed here)
- Markdown as a distinct format (Fountain and Markdown are structurally identical for our purposes)

## Context: Golden Master Files

Three scripts in `input/Perfect Script Samples/`, each with all three formats:

| Script | FDX | Fountain | PDF |
|---|---|---|---|
| Big Fish | 435KB | 146KB | 283KB |
| Brick & Steel | 54KB | 3KB | 46KB |
| The Last Birthday Card | 109KB | 21KB | 91KB |

Note: Brick & Steel's small Fountain size is expected — it's a very short script. The format
size ratio is dominated by metadata overhead in FDX/PDF for short scripts.

The `.fountain` files are the ground truth for all comparisons — they are the human-authored
source, not derived from anything else.

## AI Considerations

Before writing any code, ask: **"Can an LLM call solve this?"**

- **Fidelity comparison** — use deterministic structural comparison (scene heading list diff,
  character name set diff, word count delta). Do NOT use LLM for scoring; it would be slow,
  expensive, and non-deterministic across runs.
- **FDX round-trip** — purely structural/deterministic, no LLM needed.
- **PDF text extraction quality** — deterministic: does the extracted text contain the expected
  scene headings? Character names? Use the golden Fountain as the reference, not LLM judgment.

## Phase 1 Research Checklist

For each candidate library/tool, answer:

1. **afterwriting** (Node.js CLI, `afterwriting-labs/afterwriting`)
   - Is the repo still maintained? Last commit date?
   - Can we `subprocess.run(["afterwriting", "--input", ...])` from Python cleanly?
   - Is it available via `npm install -g afterwriting`? Does it require a build step?
   - PDF quality vs our current screenplain/fpdf2: run all three golden `.fountain` files through it, look at output

2. **pdfplumber** (Python, `jsvine/pdfplumber`)
   - Already in ecosystem? Check `pyproject.toml`
   - Try extracting text from all three golden PDFs. Compare to ground-truth `.fountain` text.
   - Does it perform better than pdftotext on screenplay column structure?

3. **PyMuPDF / fitz** (Python wrapper for MuPDF)
   - Extraction quality on our golden PDFs?
   - License: AGPL — note if it has license implications for a commercial product

4. **fountain-tools** (already in use)
   - Does it expose a Fountain→anything serializer, or just a parser?
   - Any export functionality we're not using?

5. **screenplain** (already in use as PDF backend)
   - How does its PDF output compare to afterwriting on the golden `.fountain` files?
   - What are its known gaps (CONT'D, page breaks, dual dialogue)?

## Tasks

### Phase 1 — Research Spike
- [x] **Research afterwriting**: clone/install, run on all three golden `.fountain` files, assess PDF quality vs screenplain. Document in work log.
- [x] **Research pdfplumber**: install if not present, run on all three golden `.pdf` files, compare extracted text quality to current pdftotext output. Document.
- [x] **Research PyMuPDF**: quick test on golden PDFs, note license. Document.
- [x] **Research fountain-tools export**: check source or docs for any serialization capabilities.
- [x] **Write spike conclusions**: for each candidate, write "adopt / reject / defer + rationale" in work log.

### Phase 2 — Converter Upgrade
- [x] Based on spike: upgrade Fountain→PDF backend in `src/cine_forge/ai/fdx.py` if a better tool is found
- [x] Verify FDX→Fountain logic in `src/cine_forge/ai/fdx.py` handles all elements in all three golden FDX files (scene headings, dialogue, action, character cues, transitions, title page)
- [x] Verify Fountain→FDX round trip: `golden.fdx → fountain → regenerated.fdx` — structural diff
- [x] Run existing unit tests and export API smoke check to confirm no regressions

### Phase 3 — Round-Trip Test Suite
- [x] Commit golden `.fountain` files as test fixtures in `tests/fixtures/round_trip/`
- [x] Write `tests/fixtures/round_trip/extract_golden_metadata.py` script (one-time, not a test) that reads each `.fountain` and produces `{script_name}-golden.json` with: scene count, scene heading list, character name set, total word count, dialogue word count
- [x] Commit the three `*-golden.json` files
- [x] Implement `tests/round_trip/test_fountain_pdf_fountain.py` — Fountain → PDF → Fountain fidelity
- [x] Implement `tests/round_trip/test_fdx_fountain_fdx.py` — FDX → Fountain → FDX structural diff
- [x] Implement `tests/round_trip/test_pdf_fountain_pdf.py` — PDF → Fountain → PDF fidelity (most forgiving thresholds)
- [x] Add `round_trip` pytest marker in `pyproject.toml`
- [x] Confirm `pytest -m unit` still passes with no round-trip contamination
- [x] Confirm `pytest -m round_trip` runs all three suites and prints fidelity reports

### Phase 4 — UI Fidelity and Display
- [x] Implement `useCanonicalScript` hook in `ui/src/lib/hooks.ts`.
- [x] Update `ProjectHome.tsx` to favor `canonical_script` artifact over raw input.
- [x] Add visual "Canonical" vs "Raw Import" badge to screenplay view.
- [x] Investigate and fix automatic promotion of normalized script in UI. (Implemented via `useCanonicalScript` + stage completion invalidation in `ProcessingView`).

### Finalization
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify / Create

**Research (no code changes)**:
- This story file (work log)

**Converter upgrade (Phase 2)**:
- `src/cine_forge/ai/fdx.py` — possibly upgrade `_export_pdf_via_screenplain()` to a better backend
- `src/cine_forge/export/screenplay.py` — possibly upgrade fpdf2 fallback renderer
- `pyproject.toml` — add any new extraction dependencies

**Test suite (Phase 3)**:
- `tests/round_trip/` — new directory, three test files
- `tests/fixtures/round_trip/` — golden `.fountain` files + extracted `*-golden.json` metadata
- `tests/fixtures/round_trip/extract_golden_metadata.py` — one-time extraction script
- `pyproject.toml` — `round_trip` marker registration

## Fidelity Metrics

These are the comparison functions the test suite will use. All are deterministic, no LLM:

| Metric | How measured | Pass threshold (A/B/C) |
|---|---|---|
| Scene count | `len(scene_headings)` | A: ≤2% delta / B: exact / C: ≤5% delta |
| Scene heading list | Set diff of normalized headings (uppercase, strip whitespace) | A: ≤2 missing / B: 0 missing / C: ≤5 missing |
| Character name set | Set of names from character cue lines | A: ≤1 missing / B: exact / C: ≤2 missing |
| Total word count | Word count of full script body | A: ≤5% delta / B: ≤1% delta / C: ≤10% delta |
| Dialogue word count | Word count of dialogue blocks only | A: ≤5% delta / B: ≤2% delta / C: ≤10% delta |

Thresholds are deliberately generous for path C (PDF→Fountain→PDF) because PDF extraction
is inherently lossy. If the actual numbers come in much better than thresholds, tighten them.

## Notes

- Fountain and Markdown are structurally identical for CineForge's purposes — both are plain text
  with heading conventions. A Fountain→PDF→Fountain round trip covers the Markdown case too.
- "Industry standard PDF" means: Courier 12pt, WGA-standard margins (1.5" left, 1" right,
  1" top/bottom), CONT'D markers on page breaks, proper title page. This is what afterwriting
  targets. Our fpdf2 renderer approximates this but may lack CONT'D and proper page-break handling.
- If afterwriting is found to be unmaintained or awkward to shell out to, a reasonable fallback
  is to significantly improve the fpdf2 renderer with proper page-break and CONT'D logic.
- The Brick & Steel FDX→Fountain discrepancy (54KB vs 3KB) is accounted for: it's a very short
  script, and FDX embeds substantial metadata overhead. The `.fountain` source is correct.

## Work Log

- 20260221-HHMM — story created: scope defined, three phases laid out, golden samples identified.
- 20260221-2040 — Phase 1 Research Spike:
  - **afterwriting** evaluated: Excellent PDF quality (industry standard margins, title pages, CONT'D markers). Subprocess invokability via `npx afterwriting` is clean. Repo is unmaintained since 2020 but the tool is feature-complete for our needs. **Recommend: Adopt as primary Fountain→PDF backend.**
  - **pdfplumber** evaluated: Superior text extraction compared to `pypdf`. Preserves vertical and horizontal whitespace structure better, leading to higher-fidelity parsing of character cues and dialogue. **Recommend: Adopt as primary PDF extraction backend.**
  - **PyMuPDF / fitz** evaluated: Robust extraction, but AGPL license is a concern for commercial distribution. **Reject as primary, keep as research reference.**
  - **fountain-tools** evaluated: confirmed as a parser only; no built-in Fountain→PDF/FDX serialization that improves on our current stack.
  - **screenplain** evaluated: Currently in use, but lacks the polished "industry standard" look (page breaks, CONT'D) of `afterwriting`. **Recommend: Defer/Keep as fallback.**
  - **Conclusion:** Move to Phase 2 with `afterwriting` (Node-based PDF render) and `pdfplumber` (Python-based PDF extract).
- 20260221-2130 — Phase 2 & 3 Completion:
  - **afterwriting** integrated as primary PDF backend for both text and structured scene export.
  - **pdfplumber** integrated as primary PDF extraction engine in ingestion module.
  - **FDX round-trip** improved by adding '.' forced headings and strict Fountain spacing rules; structural parity verified on all three golden samples.
  - **Round-Trip Test Suite** implemented in `tests/round_trip/` with fidelity reports.
  - All tests pass (unit and round_trip marker).
- 20260221-2330 — UI Polish and Reliability:
  - **Automatic Promotion:** Screenplay view now automatically flips to the high-fidelity `canonical_script` version upon stage completion (via `useCanonicalScript` hook and Stage completion invalidation).
  - **Title Page Preservation:** Reconfigured normalization prompts to MANDATE title page reconstruction for all imports.
  - **PDF Fidelity:** Forced all PDF imports to Tier 2 (LLM-assisted) to ensure title page recovery and extraction noise cleanup.
  - **Credit Notifications:** Implemented automatic project chat alerts when pipeline runs fail due to low AI provider credit balance or rate limits.
- 20260222-0010 — Final Polish and Bugfixes:
  - **L&C Fidelity Fixes:** Fixed centering for character cues with smart quotes and extensions (e.g. `DANTE (CONT’D)`).
  - **Metadata Healing:** Implemented "greedy" header normalization to ensure professional cover pages for all scripts.
  - **Docx Export:** Updated Word export to strip Fountain metadata tags for a cleaner look.
  - **Stability:** Fixed ASGI TypeError in export background cleanup.
  - **Validation:** Story 064 validated with A grade. All round-trip tests pass.

### Tenet Verification
- [x] **T0 — Data Safety:** Preservation of raw input verified; canonical script promotion is non-destructive.
- [x] **T1 — AI-Coded:** Normalization logic uses deterministic regex/parsing before LLM intervention; AI considerations documented.
- [x] **T2 — Architect for 100x:** Round-trip test suite provides a scalable baseline for future converter upgrades.
- [x] **T3 — Fewer Files:** Spacing and normalization logic consolidated into `fountain_validate.py`.
- [x] **T4 — Verbose Artifacts:** Metadata-rich artifacts preserved in canonical export path.
- [x] **T5 — Ideal vs Today:** Moved toward industry-standard professional PDF output via afterwriting.
