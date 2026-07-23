# Eval Attempt 017 - Storyboard Generation Quality: Retained Media Provenance

**Status:** Succeeded with fresh retained v3 evidence; no candidate promoted
**Eval:** storyboard-generation-quality
**Date:** 2026-07-22
**Worker Model:** GPT-5.6
**Subject Model(s):** GPT Image 2 template-grid and per-frame generation; GPT-5.4 packet analysis; Claude Opus 4.6 rubric

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
- Final no-call preflight found that the named per-frame comparator inherited
  the shipped `template` grid default, so the planned matrix would have compared
  two stochastic samples of one implementation. The v7 contract explicitly
  sets `gpt_image_2_storyboards` to `storyboard_grid_mode=off` and retains
  `template` for the shipped candidate, with direct runtime-resolution coverage.
- The first fully authorized runtime stopped before image generation when the
  exact Haiku 4.5 endpoint rejected `max_tokens=65536` against its live `64000`
  maximum. The failed MVP and completed parallel world prerequisite recorded
  `$0.1436622` total before interruption; no runtime-result or storyboard image
  was produced. Contract v8 caps only that exact model at its provider limit,
  preserves lower caller requests, and adds direct payload regression coverage.
- The authorized v8 retry completed the exact two-candidate by two-case matrix
  at `4/4` runtime success. Template-grid produced `15` frames in each case;
  per-frame produced `15` and `14`. The successful runtime matrix cost
  `$1.3825646`.
- The first retained-dataset materialization exposed one direct gate defect:
  the non-empty string `storyboard_grid_mode=off` was treated as an active grid
  mode. The narrow predicate repair accepts `off` without source grids, retains
  active-grid enforcement, and has focused regression coverage.
- The checked-in packet contains four sequences, `59` generated frames, eight
  reference-card copies, four full source grids, eight storyboard artifacts,
  generated targets/metadata, and complete hashes. Its `91`-file inventory is
  `12,368,207` bytes; manifest SHA-256 is
  `6bf488777cd23f374204ac273ba2dcd114eb18c9b24ee039f52da65909dceef6`.
- The initial four-row quality pass had zero transport errors, but one Opus
  rubric response was unparseable. A bounded no-cache retry of only that
  candidate/case produced a valid `0.72` rubric result. Both raw runs remain
  retained; the provenance-stamped decision matrix replaces only that failed
  judge row.
- Manual inspection covered every generated frame plus all source grids and
  reference cards. All required source cue groups are materially represented,
  crops match their full grids, and no retained media is corrupt. Significant
  misses are model-wrong and non-runtime-blocking: recurring identity drift
  (materially worse per-frame), subdued storm cues, uncertain lantern/boot
  blocking, and incomplete receiver/location recognition. Abstract cards are
  transport-only; penalizing absent glyph/color reproduction would be
  golden-wrong. No source golden requires correction.

## Conclusion

**Result:** succeeded
**Score before:** no decision-grade v3 score
**Score after:** template-grid `python=0.6962`, `rubric=0.615`,
`identity=0.3972`; per-frame `python=0.6331`, `rubric=0.770`,
`identity=0.1871`; neither clears the hard quality floor
**Latency before:** not decision-grade
**Latency after:** template-grid mean total `366,968ms` and storyboard stage
`110,761.5ms`; per-frame mean total `645,751ms` and storyboard stage `413,651ms`
**Cost before:** no decision-grade retained matrix
**Cost after:** successful runtime `$1.3825646`; initial quality pass
`$0.21309`; bounded judge retry `$0.09016`; final-run total `$1.6858146`
(`$1.8294768` including the earlier aborted prerequisite attempt)

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

**Retry state:** closed

**Retry when:**

- Trigger satisfied. The fresh exact packet is complete and manually inspected.
  Keep template-grid as the value default without a quality-pass claim; any
  future retry belongs to an identity/reference-stability improvement, not this
  provenance repair.

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
- [x] Completed the exact fresh two-case/two-candidate runtime matrix
- [x] Retained and hash-validated every scored visual byte outside `output/`
- [x] Manually inspected every generated frame, source grid, and reference card
- [x] Classified every significant mismatch and recorded runtime impact
- [x] Preserved the initial judge parse failure and bounded retry provenance
