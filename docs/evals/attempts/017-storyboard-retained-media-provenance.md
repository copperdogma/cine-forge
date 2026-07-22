# Eval Attempt 017 - Storyboard Generation Quality: Retained Media Provenance

**Status:** Succeeded with historical evidence quarantined
**Eval:** storyboard-generation-quality
**Date:** 2026-07-22
**Worker Model:** GPT-5.6
**Subject Model(s):** No subject, judge, or image-provider call

## Mission

Close the provenance gap exposed when one historically scored storyboard panel
and its only full-grid parent were accidentally overwritten under ignored
runtime output. Preserve the distinction between checked-in source/target truth
and nondeterministic candidate output while making exact candidate media a
mandatory, recoverable input to any future decision-grade visual score.

## Prior Attempts

Attempts 004-006 optimized and compared storyboard candidates but retained only
result JSON plus ignored local media. Attempt 013 later invalidated those rows
for leakage, sampling, scorer, and modality defects. Story 208's first v3 repair
hashed copied panels but still ignored the packet and did not validate its
hashes before judging or registry promotion.

## Plan

1. Keep general project `output/` ignored and keep every historical row
   contaminated/non-decision-grade.
2. Make the small v3 storyboard evidence directory visible to Git.
3. Retain every scored panel, supplied reference, source grid, storyboard JSON,
   generated target, metadata file, and raw runtime input under one exact file
   inventory.
4. Validate the inventory before provider dispatch, bind packet hashes into raw
   Promptfoo rows and the decision report, and require the checked-in manifest
   plus SHA-256 before a registry row can be decision-grade. Require a real Git
   commit and prove every evidence byte is tracked and unchanged from it.

## Work Log

- Reproduced that the tracked Story 188 runtime and judge results reference the
  corrupted panel, while neither result embeds the image bytes.
- Confirmed the panel is candidate evidence rather than a golden; the
  authoritative source/target manifest remains checked in and source-hash
  locked.
- Added exact retained-media inventory, source-grid and storyboard-artifact
  capture, provider/report digest checks, and a generic registry promotion gate.
- Added adversarial controls for changed, missing, extra, or wrong-packet media.
- Independent adversarial review then found that a missing `evidence_status`, a
  `working-tree` pseudo-SHA, untracked-but-present files, a stale schema label,
  or a symlink could still evade part of the first gate. Closed each path: the
  registry now requires an explicit classification, exact v3 schema, a real
  commit, Git-tracked evidence unchanged from that commit, and regular files
  wholly contained by the packet/repository. The per-run contract fingerprint
  now includes direct scoring, identity, usage, JSON-loader, and schema
  dependencies, with an independent required-set regression.
- Kept all old Story 186/188/190 measurements quarantined. No damaged or
  contaminated byte was promoted into the repository evidence packet.

## Conclusion

**Result:** succeeded
**Score before:** no decision-grade v3 score
**Score after:** no decision-grade v3 score; historical rows remain quarantined
**Latency before:** not measured
**Latency after:** not measured
**Cost before:** $0.000 during this repair
**Cost after:** $0.000 during this repair

**What worked:** Ordinary Git is sufficient for this lane: the existing local
packet is about 1.4 MiB, while the repository already retains larger visual
evidence sets. Hashes now both detect mutation and point to bytes that a clean
checkout must contain before promotion. Presence alone is not enough: promotion
also proves the files are tracked and byte-identical to the declared commit.

**What failed:** A hash manifest under an ignored directory was not durable;
it could diagnose loss but could not recover the exact stochastic output.

**What NOT to retry:** Do not promote the restored historical run. Backblaze
recovered the two accidentally overwritten JPEGs byte-for-byte, but a rerun
would still be new evidence and the v2 contract was independently contaminated.

**Retry state:** open

**Retry when:**

- `architecture-change` - after the repaired Story 208 contract is committed,
  run one fresh exact v3 packet comparing the shipped
  `gpt_image_2_template_grid_storyboards` default with the per-frame
  `gpt_image_2_storyboards` quality ceiling, inspect it manually, check in the
  retained media, and only then consider a decision-grade row.

---

## Definition of Done Checklist

- [x] Read all previous storyboard attempts before starting
- [x] Preserved historical results without treating them as current evidence
- [x] Updated `docs/evals/registry.yaml` with the new provenance policy
- [x] Added deterministic and adversarial retained-media controls
- [x] Rejected missing classification, dirty/untracked evidence, stale schema,
      and symlink substitution
- [x] Recorded latency and cost as not measured / zero-provider-call
- [x] Did not run or silently accept a score change
- [x] Recorded an explicit retry trigger
