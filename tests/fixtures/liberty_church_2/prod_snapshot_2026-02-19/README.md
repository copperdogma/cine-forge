# Liberty Church 2 Production Snapshot

This directory is a historical forensic capture, not an active test fixture or
semantic golden.

- Source: production project `liberty-church-2`, captured through the normal API
  on 2026-02-19 for Story 054.
- Capture contents: project, run, artifact, input, and per-character payloads.
- Authoritative investigation record:
  `docs/reports/liberty-church-2-artifact-inventory.md`.
- Known defects: the capture intentionally preserves semantic contamination,
  including false character identities, location fragmentation, and prop
  under-extraction.

The snapshot is quarantined to historical regression investigation. Do not use
its `valid` health labels, character payloads, or aggregate artifact counts as
current quality evidence. A maintained test may extract a narrowly documented
regression case from it, but must state the exact source facts and expected
behavior rather than treating the snapshot itself as ground truth.
