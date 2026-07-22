# Eval Attempt 013 - Visual Modality Truth

**Status:** Succeeded with documented limitations
**Eval:** video-understanding, previz-usefulness, final-render-provider-floor, and storyboard-generation-quality
**Date:** 2026-07-21
**Worker Model:** GPT-5.6
**Subject Model(s):** No new subject call during fixture and harness repair

## Mission

Determine what the maintained "video understanding" lane actually exposes to a
subject, personally inspect all 20 generated clips and their audio-bearing
streams before editing them, and repair or quarantine claims that cannot be
observed from the evaluated payload. The same fixture family is reused by
previz and final-render evidence, so contamination here propagates beyond one
benchmark.

## Baseline Reproduction and Classification

- The provider sends five JPEG analysis frames. It does not send `clip.mp4` or
  any audio bytes.
- The subject text supplies the authored clip title, tags, transcript, and
  `audio_description`; these fields contain much of the answer being scored.
- The generator prints an overlay label, title, selected camera labels, prop
  labels, and any transcript directly into the rendered image.
- Eight frame packets are byte-static and two more contain only two unique
  sampled frames. Static packets are nevertheless scored for cuts, reveals,
  drifts, or other temporal behavior.
- The generator's non-speech audio is one sine tone chosen by the first matching
  tag. It cannot substantiate authored descriptions such as strings, rain,
  breath, piano, cheerful store music, or percussion patterns.
- The deterministic scorer measures required-tag recall but does not penalize
  extra tags. Its evidence check requires only non-empty timestamped text, not a
  cue grounded in the submitted images.
- **Classification:** fixture/golden-wrong and harness-wrong, with some
  historical model-wrong results still possible but inseparable from leakage
  and modality mismatch. This is non-runtime-blocking for current text defaults,
  but decision-blocking for video, previz, and final-render model claims.

## Personal Pre-Edit Inspection

The orchestrator inspected contact sheets containing five evenly spaced frames
from every clip and decoded the embedded audio streams into spectrogram contact
sheets. The tool interface did not provide literal acoustic playback, so this
record does not claim human listening; stream presence, duration, generated
waveform structure, and dominant tone behavior were inspected directly, and
the generator implementation was checked against them.

| Clip | Unique sampled frames | Audio | Direct observation |
|---|---:|---:|---|
| `alarm_chase_whip_pan` | 5 | yes | Red runner and bag move diagonally; `ALARM`, `WHIP`, and prop labels reveal intended tags. Alarm tone is synthetic. |
| `countdown_control_room` | 5 | yes | Operator/screens and T-30 to T-06 text change; full dialogue is printed as a subtitle and synthesized as speech. |
| `dialogue_confession_push_in` | 5 | yes | Two figures and envelope scale across frames; confession text is printed and synthesized. |
| `flashback_sepia_drift` | 5 | yes | Sepia figures/oar/circle with subtitle and `FLASHBACK` overlay; motion is a simple diagrammatic drift. |
| `golden_memory_orbit` | 5 | yes | Figures, circle, and lantern change position/scale; audio is a single tone, not a demonstrated musical arrangement. |
| `hallway_standoff_crosscut` | 2 | yes | Repeated symbolic figures/knife/subtitle; five frames do not demonstrate a meaningful cross-cut sequence. |
| `handheld_panic_stairwell` | 5 | yes | Runner and labeled scarf move diagonally; audio is a low tone and does not expose authored breath/percussion detail. |
| `match_cut_envelope` | 1 | yes | Static table/envelope/subtitle packet; a match cut is unobservable. |
| `mirror_isolation_profile` | 1 | no | Static figures/divider diagram; no temporal or audio claim is observable. |
| `muzak_aftermath_tableau` | 1 | yes | Two abstract brown rectangles; tipped chair, broken glass, and aftermath detail are absent; audio is a 440 Hz tone. |
| `neon_crosswalk_reveal` | 1 | yes | Static grid/triangle/rectangles; no crosswalk reveal or drift is visible; audio is a 110 Hz tone. |
| `prop_swap_continuity_break` | 2 | no | Folder label changes red to blue, so the color swap is visible; answer-bearing labels make the task trivial. |
| `quiet_bedside_vigil` | 1 | yes | Static bed/figure diagram; the target's seated pose is not shown; audio is a 60 Hz tone rather than authored room tone, heartbeat, and piano layers. |
| `radio_hold_tracking` | 5 | yes | Figures/light/subtitle move diagonally; transcript is printed and synthesized. |
| `rooftop_escape_crash_zoom` | 5 | yes | Runner and cable label scale/move; `crash_zoom` intent is exposed by title/metadata; audio is a 110 Hz tone rather than demonstrated percussion. |
| `storm_tunnel_lateral_run` | 5 | yes | Figures and labeled flare move laterally; audio is a 110 Hz tone, not authored rain/percussion detail. |
| `sunset_reunion_pullback` | 5 | yes | Figures/circle shrink in a simple pull-back diagram; 330 Hz tone does not demonstrate warm strings. |
| `surveillance_green_monitor` | 1 | yes | Static green box/bar composition; a low electronic tone is present, but temporal claims are unavailable. |
| `violet_dream_percussion` | 1 | yes | Static violet circles; audio is a 110 Hz tone despite a percussion claim. |
| `warehouse_drone_wide` | 1 | yes | Static columns/light wide diagram; a low tone is present, with no motion evidence. |

All 20 clips are exactly four seconds. Eighteen contain an audio stream;
`mirror_isolation_profile` and `prop_swap_continuity_break` do not.

## Reusable Failure Classes

1. **Answer leakage:** title, overlay, labels, tags, transcript, and authored
   descriptions disclose expected concepts to the subject.
2. **Modality mislabeling:** a five-image packet is described and interpreted as
   native video/audio understanding.
3. **Unobservable temporal targets:** static or near-static packets require
   motion, reveals, cuts, or camera behavior they cannot show.
4. **Visible-content mismatch:** targets name objects, poses, or scene details
   absent from the generated images.
5. **Audio-description mismatch:** a synthetic speech-plus-tone generator is
   described as richer diegetic sound or music.
6. **Scorer bypass:** recall-only tags and ungrounded prose evidence reward
   overprediction and invention.
7. **Taint propagation:** previz and final-render lanes reuse the same metadata,
   targets, or provider assumptions and inherit the false evidence.

## Planned Repair Contract

- Rename/reclassify the existing evaluator as frame-packet comprehension and
  state explicitly that it cannot measure native video or audio.
- Submit neutral identifiers and observable technical facts only; remove
  authored title/tags/transcript/audio descriptions from the subject packet.
- Produce clean analysis frames without answer-bearing overlays or quarantine a
  fixture until a clean observable target exists.
- Score only dimensions exposed by the packet. Add extra-tag penalties and
  evidence-grounding controls.
- Keep native video/audio capability as a separate future lane that actually
  transmits those modalities.
- Reconcile previz and final-render tasks after the base contract is green.

## Previz Inherited-Lane Repair

The maintained `previz-usefulness` lane had a distinct truth defect after the
base frame-packet repair: its retained AI clips were generated from the older
Story 143 shot briefs preserved in each `prompt_contract.json`, while the task
now pointed at mutable base-video targets. The most material example was
`radio_hold_tracking`: the retained candidate prompts require a lateral track,
but the repaired base control target is intentionally static. Reusing that base
target would punish a provider for following the prompt that actually generated
its retained clip.

Repair applied without any provider call:

- Added `benchmarks/previz_usefulness/cases.json` plus three dedicated visual
  target/markdown pairs. The case contract recovers the authored shot, tone,
  color, camera, motion, continuity, dialogue, and audio cues from the retained
  prompts. Scoring projects only frame-observable intent; audio is unavailable
  to the subject and carries zero score.
- The task now evaluates only the three retained provider-generated candidates.
  `symbolic` is `control_only_non_comparable`; `annotated_symbolic` is
  `control_only_answer_leaking` because its frames visibly contain title, shot
  intent, character, camera, and edit annotations. Neither can enter provider
  ranking or recommendation logic.
- Split the 665-line generator into four files of 181, 216, 361, and 231 lines;
  every function is at most 100 lines. The default command rebuilds only local
  deterministic controls, validates retained candidates, and refreshes hashes.
  Paid generation requires the explicit `--generate-ai` flag.
- Preserved all nine AI clip bytes and all 63 AI frame/prompt artifacts exactly.
  Pre/post hash-list comparisons both returned `0`; the clip hash-list digest is
  `097ca3c55afd4b3d358e8e2747b41f9d3c215415dabe53c48d4a340a5807580a`
  and the frame/prompt hash-list digest is
  `7284b90bc00c76c0547b5c2381e842c41ab66baf1319991c34191a2aa02234ab`.
- Manually inspected one 25-frame contact sheet per case after repair. The
  provider candidates visibly correspond to the intended two-person envelope
  push-in, warm bedside hold, and blue-corridor flashlight tracking brief. This
  inspection also reconfirmed the annotated control's answer overlays.
- Updated report policy so it can recommend only `decision_eligible` AI rows and
  uses each opaque `evaluation_id` when reapplying the deterministic scorer.
  Every historical registry row is now explicitly contaminated and
  non-decision-grade.

Focused evidence: 22 previz dataset/report unit tests pass, Ruff passes over all
touched previz Python files, the Promptfoo configuration validates, and the
safe canonical generator refresh preserved every retained AI byte. A fresh
subject and Opus regrade was deliberately not run; it is the remaining evidence
step after all inherited visual lanes are green.

### Previz report decision-contract hardening

A later orchestrator review found that the first repaired report could still
false-green provider evidence even though the task and dataset were honest. It
preferred Promptfoo's retained Python component over a current-scorer regrade,
averaged whichever score components happened to exist, treated three duplicate
copies of one case as complete three-case coverage, ignored stale prompt
versions, and loaded registry rows already marked contaminated.

The report now regrades every raw output with the current deterministic scorer;
requires exactly one Python assertion and one numeric LLM-rubric assertion;
requires the exact three-candidate by three-case matrix with no missing, extra,
or duplicate pair; enforces the opaque case IDs, v3 prompt version, declared
target, candidate metadata, analysis latency/cost, and generation latency; and
filters contaminated registry history. Invalid subject JSON is a scored model
failure, while target/scorer failures are explicit harness errors. Generation
cost availability is reported separately: a complete quality ranking may be
formed without reconstructing an unknown historical charge, but a fast winner
cannot be promoted while that cost detector is unmeasured. The report was kept
below the architecture threshold by extracting focused contract, row, and
rendering modules, all below 400 lines with functions below 100 lines.

Adversarial coverage proves that a duplicated case, missing candidate, missing
assertion, stale prompt, target failure, and missing generation cost cannot
produce a promotion. Reprocessing the retained Story 176 result produces
`regrade_required`, uses no contaminated previous score, and makes no provider
call.

Previz contract identities at this checkpoint:

- task: `a86059b009d25a95559e5224064f3f4cbfa0fc8e87dbd53b0710aea3bd14d01a`
- cases: `3ad9ed4eeedeaf82174f53096a619346d21be00292f0e5edc386b4704689b60c`
- manifest: `e7b01d8c85bd83824433451e5b172e740e644a808ca41783a34869de0f4b7612`
- generator entrypoint: `ac812bb39c072002155f1279282b2ea1df2dfe4a6bf6de026869617d5ff3bc4c`
- report entrypoint: `22d36a33991160afc27c95870ef5245ae48bdddb11faf1cf35dd91807f3a46fc`
- report contract: `537a039a5162550701d1c14dce72d79e7200e6489a1ffb22cbd630f78e4e4ab5`
- report rows: `02f05a38ead9d252b718c886e09dd170ebecd6e7cb90a4cd0289f45f905f6313`
- report rendering/policy: `cc176b9c118a48cc52413ab84754d189fff3c41ce35924fcd0eaf895999552eb`

## Storyboard Inherited-Lane Repair

The inherited `storyboard-generation-quality` lane had a separate visual-truth
failure. Its multimodal subject did receive storyboard images, but both the
packet and the scoring path supplied enough semantic structure to reward a
plausible report without proving what the pixels showed.

### Baseline reproduction and classification

- A deliberately fabricated v2 response copied target cue words, used invalid
  frame ids, declared every style/character/reference status positive, and said
  only `trust me` as evidence. The old deterministic scorer returned `1.0` and
  a hard pass.
- The old provider exposed `Open Frequency`, semantic case and scene ids,
  ARIA/NOAH, reference labels, semantic frame filenames, and runtime reference
  counts/status. It then sampled at most eight generated frames rather than
  analyzing the exact sequence it purported to score.
- The old report trusted retained aggregate/Python values. A synthetic result
  with stored top-level and Python values of `0.99` surfaced those values
  without applying the current scorer to the raw response.
- The configured generated root is ignored and absent from this audit
  worktree. Across 14 retained runtime JSON files, 30 of 36 run rows and 20 of
  26 distinct project paths no longer exist. The six surviving project paths
  cover only the Story 188/190 local outputs.
- The retained target cards are four colored abstract glyphs. They can prove
  that four bytes entered a transport path; they cannot prove realistic person
  identity or location fidelity. The source fixture also lacks authored
  per-frame shot roles, so a close object image cannot be classified as an
  improper non-insert rather than an intended insert from source truth alone.
- **Classification:** harness-wrong and golden-wrong. The retained pixels also
  contain genuine model-wrong identity drift and occasional prop collapse, but
  historical numerical attribution is inseparable from packet leakage,
  sampling, mutable assets, and self-report scoring. This is non-runtime-
  blocking for the configured storyboard generator and decision-blocking for
  every historical storyboard quality/default claim.

### Personal retained-artifact inspection

The initial local inventory contained 214 storyboard/reference image rows: 176
under historical `output/**/storyboard*` roots and 38 under the ignored
`benchmarks/storyboard_generation_quality` root. Those rows contained 148
unique image byte hashes. The ignored benchmark subset contains 30 generated
frames plus eight copies of four unique abstract reference cards. Personal
visual review covered all 38 benchmark rows (34 unique hashes) and 146 of the
148 unique visuals across the combined pre-inspection corpus. Two historical
originals were overwritten before they could be viewed and could not be
recovered, as recorded below.

Direct observations across the inspected corpus:

- The generated sequences are strongly cohesive as monochrome pencil/charcoal
  storyboards, and the radio-studio, mixer/tape equipment, storm-night,
  water-tower/catwalk, antenna/receiver, and lantern intent is recognizable.
- Recurring people drift materially across panels and retained runs: hair,
  facial geometry, apparent age, and even which person occupies a subject slot
  change. Historical positive identity statuses were not trustworthy.
- A retained template-grid panel collapses an intended two-person beat to a
  receiver close-up. Other historical output artifacts include blank grid
  templates and schematic/slate-like frames with small authored text. These
  observations are useful QA notes but cannot become a prop/text golden without
  a source-authored frame/shot map.
- The abstract reference cards share only colored glyphs with one another and
  do not encode a realistic face, wardrobe, studio, or catwalk. Reference
  quality is therefore transport-only.
- Retained benchmark filenames disclose names and shot intent such as
  `aria_noah_two_shot`, `noah_reaction_close`, and `on_air_sign_flicker`, even
  though those facts are not visible in every associated frame.

### Inspection incident and recovery

An incorrectly ordered contact-sheet command used the final source image in
each of ten batches as the output path, overwriting ten ignored historical
output images. Hash comparison detected the mutation. Eight files were then
restored byte-for-byte from unchanged benchmark copies or by rerunning the
project's deterministic grid slicer against an untouched full grid; all eight
restored SHA-256 values exactly match the pre-inspection inventory. These two
originals in one ignored Story 186 project were not recoverable because the
panel and its only full-grid source were overwritten in separate batches:

- `output/story-186-gpt_image_2_template_grid_storyboards-open_frequency_sequence_prompt_only-d26fe7/artifacts/storyboard_frames/scene_002/v1/frame_08_002_008.jpg`
  - original: `cd06f9f5c89d5c2bbf8361ddb5d1fcc0c9129fc4d976697f5f35b8a82ab5bcc6`
  - post-incident: `c9e57dd8a5396e80f062342700e0eaef0fb2bf23b7f6e98e5828d3d5b7513185`
- `output/story-186-gpt_image_2_template_grid_storyboards-open_frequency_sequence_prompt_only-d26fe7/artifacts/storyboard_frames/scene_002/v1/grid_01_full.jpg`
  - original: `96fa23c8f729b48f87b75f2a2bd64067b9d59a4cd75599c339c0e82b9ffecb6a`
  - post-incident: `07b9643199beef589c9ab2c13690e9369549e0867c4254826d5dad8151938dd1`

The ignored project now contains `AUDIT_CORRUPTION.md` with the same warning
and must not be used as evaluation or product evidence. Ordered
relative-path/hash-list digests make the remaining difference explicit:

- 176 historical output images before inspection: `2828cd722975a44fff9289906d9318ca83b5f3ef85af8e1217cf40538f0a3826`
- 176 historical output images after recovery: `3a76194f2b86b96e7d7d726f7efc1b60e4c33ae904cd96b26caeb62beb974118`
- all 214 image rows before inspection: `4b188e79d80ab6d665d90e19e62623cd3035fdf01e1e43c3419f42ef289d3c71`
- all 214 image rows after recovery: `724ceaaeabb6139b033c3c5b71e3a9f288495dee62b17e374320c9b5f4c81327`
- unchanged 38 ignored benchmark images: `31b3efa9a1bf98bc6a3d6257315c6bedcba21e3646a9cc657f158813a5a346e6`
- unchanged 45 ignored benchmark dataset files: `db878d1dcab001829eb9db80a91ae3870049e23cfee7a2f3de5fba37f36f5cf1`
- unchanged 83 retained storyboard result files: `91ce9f87c9ebf82c26661ea352c33fa13dd4a2014567f8092c8473b52e0af541`

The contact sheets, hash lists, and a sheet of the eight recovered originals
are local audit aids under `/tmp/cine-forge-storyboard-audit/` for this work
session only. The two unavailable originals and the inspection incident
further disqualify this historical corpus from numerical/default evidence;
they do not affect the repaired v3 contract, which requires a fresh staged
dataset.

### Repaired v3 contract

- Source-hash-locked two opaque cases to
  `open_frequency_short.fountain` (`81508ec3a2be376efbc8f8d720dea2784eec5dba3664372df3f65123f8684d95`)
  and replaced answer-bearing subject labels with `sbq_case_###`,
  `frame_###`, `reference_###`, and `subject_###` slots.
- Split the 455-line provider before behavioral edits. The entrypoint is now
  161 lines, packet loader 130, and transport helper 231; all functions are at
  most 100 lines. Every meta-declared image is sent in ordinal order. Count
  mismatch, configured ceiling overflow, requested-case mismatch, silent
  sampling, and model-owned packet counts fail closed.
- Replaced pass/status fields with strict observations: early/late medium
  traits, early/late recurring-subject traits and frame ids, per-reference
  observable similarities, readable-text/prop-only frame ids, and four to eight
  opaque frame-bound cues. The provider, not the model, injects trusted packet
  counts.
- The current scorer derives source-cue, medium, recurring-subject, text, and
  evidence scores; rejects old/fenced/extra-key JSON, invalid ids, semantic
  leakage, negated evidence, and generic-subject domination; and assigns zero
  weight to unsupported reference fidelity and prop discipline. The downstream
  Opus rubric is explicitly only a semantic cross-check of the multimodal
  analyst report because it does not receive the images itself.
- The dataset generator now requires an exact successful candidate-by-case
  runtime matrix, verifies the source hash, rejects contradictory reference
  metadata and path escape, stages replacement, copies bytes exactly, records
  per-asset hashes, and fingerprints the runtime, case manifest, and seven
  quality-contract files.
- The report now requires exact runtime and Promptfoo matrices, v3 metadata,
  one finite Python plus one finite rubric component, complete non-negative
  latency/cost measurements, current-scorer regrading of raw output, and
  per-case reference checks. Stored aggregate/Python values cannot select a
  candidate.

Focused offline evidence: 20 storyboard provider/scorer/generator/report/runtime
unit tests pass and targeted Ruff is clean. No subject, Opus, image-provider,
or paid call was made. Every historical registry row is now
`contaminated-non-decision-grade`; the configured template-grid default remains
provisional until a fresh exact two-case v3 default-versus-one-ceiling run is
manually inspected.

Storyboard contract identities at this checkpoint:

- task: `e0c68f6dd2645b671c97f101ddc3ae6013382887e6a2ccd6d58ed4bd56b1da48`
- prompt: `f4572741b9c30fc26c548397cd95ff4cc35521b179de007fdc5ad7f7a5153b40`
- cases: `7bbef0a706303aa568ee223c483b7ac865e303ba39c325560200932f85da0955`
- provider entrypoint: `b9819ab0176753b047df0758b09e03cfa30532096dfd36b9d90f1264c491b396`
- packet helper: `9ebb79534f6c49240c389747afdec3b1d023d5494c1e523dcbbbb5552dfacbcc`
- transport helper: `bd8aad6fc42d9af271620a14c2484d9d230273acdfadc9d684e2e08e9d4ed342`
- scorer entrypoint: `75f333f9dd78515f288b31e72b97aa3d23aa1f1056def1a77e3f1dcfdfedcc7c`
- scorer dimensions: `13439cf54b404dedb70807d854db93b8f7c80b85b37575209f07bb9e7d2f6aef`
- dataset generator: `f7b5256b3aeb62ac66353f1425f3e4b3bcfdd2dd4b67b5e94a293d0aa753632c`
- report entrypoint: `dcf6e108a3c0c43dae0743d1f258067f3f562ed197d4c20a5f2435516ed923ab`
- report support: `a51ee89dd5571430ad320cab012bd9359734b5ee988d8a38d2d253dfebcc0004`
- schema: `1ce988e61464eda54179418bf60a7cddeaa8b2eaf738bcbdf662f7b781e7252d`
- retained Story 188 raw quality/decision:
  `db0085fd55629bb6ed714a879be5115e888ce3b5ef7692b22731de045f1d9310` /
  `b4301594d126e86b8e8c80ceed98109faefd67a1dd044d32da2dab0c0e38eb2b`
- retained Story 190 raw quality/decision:
  `deb294399fdc63dbafebf4d18c45156d32cf7ce74070d1b85621d551e5220c5b` /
  `a573e6cadf169a02f0bd412b26a221fcd91895e4e99e581fc684d797564c16e3`

## Evidence Identity

- Base git SHA: `a5b5c88`
- Task SHA-256: `ab29162d5198a6b4e95c319598b015b25469ea5b650c38a6c2a6bf986aa39229`
- Prompt SHA-256: `154428fce3c6f34f46d09b8f158fc98f45fabe3ddeddbf2d6f9f193de917cb33`
- Provider SHA-256: `fcb7a0103baf6f7c3c7971449450a6809606c4ee6d1a82739a4296d234e0097f`
- Scorer SHA-256: `6f039d8d1b17afeb2fed88a8a69f854405e2129b4407a302bfba9cc9a3c8f595`
- Generator SHA-256: `782da37366fc840c35f4cf5ff034fb3db8ca0028818a95c89f33677c065f5afa`
- Manifest SHA-256: `8844bd25932d73820ff0a68d3fced7d431027b354ba79f3dbb24c75648d299a9`
- Pre-edit visual evidence: `/tmp/cineforge-visual-audit.pPO48G/contact-group-1.png`
  through `contact-group-5.png`; audio spectra `audio-group-1.png` through
  `audio-group-5.png`.
- Working-tree state: uncommitted and provisional.
- Paid calls: none.

## Conclusion

**Result:** succeeded with documented limitations - the maintained lane is now
an honest ordered-frame-packet comprehension contract, not a native video/audio
eval. Previz, final-render, and storyboard inherited evidence has been repaired
or quarantined and all historical rows are non-decision-grade.
**Quality before:** materially leaked and partially unobservable
**Quality after:** observable, source/hash-bound frame evidence with precision,
grounding, exact-matrix, and current-scorer regrade gates; no fresh subject score
is claimed
**Latency before/after:** not applicable during offline harness repair
**Cost before/after:** `$0.00` incremental

Remaining limits are deliberate and decision-blocking: no native MP4/audio
transport is measured, literal acoustic playback was unavailable, fresh subject
plus Opus evidence has not been purchased, realistic reference/identity and
prop-shot fidelity still require manual review, and the configured visual
defaults remain provisional. The two unrecoverable ignored Story 186 images and
their original hashes are recorded above and quarantined by the local
`AUDIT_CORRUPTION.md`; they are not current benchmark assets.

**Recovery postscript (2026-07-22):** Backblaze later restored both exact Story
186 originals, and their SHA-256 values match the hashes recorded above. The
local corruption is resolved. The ignored v2 evidence remains contaminated,
non-durable, and non-decision-grade for the independent contract defects this
attempt records.

---

## Definition of Done Checklist

- [x] All 20 frame packets personally inspected before edits
- [x] All audio streams decoded and spectrally inspected; playback limitation recorded honestly
- [x] Static/near-static frame counts and stream presence reproduced
- [x] Leakage and generator mismatch classified before repair
- [x] Oversized provider/scorer/generator responsibilities extracted before added logic
- [x] Frame-packet subject payload contains no answer-bearing metadata or overlays
- [x] Targets contain only packet-observable claims or are quarantined
- [x] Extra tags and invented evidence fail direct scorer controls
- [x] All 20 rebuilt packets (100 frames) and representative inherited controls were personally reinspected
- [x] Previz/final-render/storyboard inherited contracts are reconciled
- [x] Comparable retained outputs are current-scorer regraded; incompatible history is explicitly non-comparable before any paid rerun
- [x] Ledger and registry evidence are terminal and hash-complete
