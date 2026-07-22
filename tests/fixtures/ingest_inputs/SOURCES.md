# Ingest Input Fixture Sources

This directory mixes public-source samples with repo-authored regression fixtures.
Every direct fixture file must have an entry here; provenance and intended scope
are part of the test contract.

- `owl_creek_bridge.txt`
  - URL: `https://www.gutenberg.org/cache/epub/375/pg375.txt`
  - Work: *An Occurrence at Owl Creek Bridge* by Ambrose Bierce
  - Notes: Project Gutenberg public-domain distribution in the U.S. (see Gutenberg license header in file).

- `owl_creek_bridge_excerpt.md`
  - Derived from: `owl_creek_bridge.txt`
  - Notes: Markdown-formatted excerpt generated locally from the downloaded public-domain text.

- `run_like_hell_teaser.fountain`
  - URL: `https://www.slugline.co/s/RLHteaser_130820b.fountain`
  - Work: *Run Like Hell* teaser sample script by Stu Maschwitz
  - Notes: Publicly posted Fountain sample for download on Slugline's samples page.

- `open_frequency_short.fountain`
  - Source: Repo-authored fixture
  - Work: *Open Frequency*
  - Notes: Canonical very short screenplay for the recurring full-pipeline UI
    manual walkthrough and post-rollout `Break Down Script` eval. Intentionally
    short enough for occasional end-to-end runs, but rich enough to exercise
    intake, world understanding, scene workspace, and downstream
    planning/visualization surfaces.

- `pit_and_pendulum.pdf`
  - URL: `https://ibiblio.org/ebooks/Poe/Pit_Pendulum.pdf`
  - Work: *The Pit and the Pendulum* by Edgar Allan Poe
  - Notes: Public-domain short story PDF download.

- `patent_registering_votes_us272011_scan_5p.pdf`
  - URL: `https://upload.wikimedia.org/wikipedia/commons/f/fc/Patent_for_Apparatus_for_Registering_Votes_US272011.pdf`
  - Work: *Patent for Apparatus for Registering Votes (US272,011)* by H. Zimmer
  - Notes: Wikimedia Commons scan of historical U.S. patent (public domain). Short scanned PDF fixture (~5 pages) used to exercise OCR-oriented ingestion behavior.

- `run_like_hell_teaser_scanned_5p.pdf`
  - Source text: `run_like_hell_teaser.fountain` (Slugline public sample)
  - Generation method: rendered into 5 grayscale image pages with ImageMagick, then packaged into an image-based PDF using `img2pdf`.
  - Notes: Deterministic screenplay-like scanned fixture used to validate OCR fallback and extractor diagnostics (`pdf_extractor_selected=ocrmypdf`).

- `sample_script.fdx`
  - Source: Repo-authored synthetic fixture (Story 004).
  - Work: Minimal safehouse screenplay fragment.
  - Notes: Mechanical Final Draft XML ingestion fixture; not a semantic quality golden.

- `sample_script.docx`
  - Source: Repo-authored synthetic fixture added with DOCX ingestion support.
  - Work: Minimal lab screenplay fragment.
  - Notes: Mechanical DOCX extraction/classification fixture; not a semantic quality golden.

- `the_signal.docx`
  - Source: Repo-authored synthetic fixture (Story 003b).
  - Work: *Signal in the Rain*.
  - Notes: Multi-scene DOCX screenplay used to exercise realistic DOCX ingestion.

- `the_mariner_degraded.txt`
  - Source: Repo-authored degraded-text fixture (Story 007c), derived from local
    *The Mariner* sample material.
  - Notes: Upstream publication/licensing provenance was not recorded. Keep this
    fixture confined to local remediation regression tests; it is not a public
    benchmark corpus or decision-grade semantic golden.
