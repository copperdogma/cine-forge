# Eval Attempt 038 — Grok 4.7 Bounded Video and Script-Bible Lanes

**Status:** completed — both bounded lanes rejected; no comparator or expansion run
**Date:** 2026-09-22
**Subject:** direct xAI Responses `grok-4.7`, low reasoning, `store=false`
**Owner:** Story 220

## Frozen Lanes and Bounds

| Lane | Eligible input | First decision run | Gate | Cap |
| --- | --- | --- | --- | --- |
| video-understanding | six repo-owned synthetic controls, five ordered JPEGs each | all six v3 frame packets | overall >=0.80; <=15s; <=$0.02/subject | $0.75 |
| script-bible | repo-authored synthetic Open Frequency | one exact-runtime ScriptBible | overall >=0.90; <=30s; <=$0.01/subject | $0.35 |

The video and Script-Bible lanes are independent. Neither sends audio, MP4,
transcript, semantic titles, quarantined cases, a private screenplay, or a
private fixture. Each uses direct xAI Responses strict JSON Schema, requires
exact served identity, terminal completion, reconciled raw usage, and no cache
before semantic scoring. The Script-Bible second corpus and fresh Gemini
control, and the video fresh Gemini control, require the candidate to clear the
corresponding lane's hard gates first.

## Prior Evidence

- Attempt 019 established the currently maintained v3 ordered-JPEG schema and
  six active controls. Its Gemini rows are decision-grade holds, but do not
  qualify video/audio-native claims.
- Attempt 023 found Grok 4.6 passed its one synthetic Script-Bible case on
  quality and latency (`0.92665`, `23,699 ms`) but failed the $0.01 subject-cost
  gate (`$0.011548`). This run does not assume a new win from family similarity.

## Spend Ledger

| Lane | Probe | Candidate subjects | Judges | Fresh control | Accounted | Remaining cap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| video-understanding | $0.018496 actual | $0.051006 actual | $0.432825 estimated | $0.00 | $0.502327 | $0.247673 |
| script-bible | $0.020886 actual | $0.015042 actual | $0.132765 estimated | $0.00 | $0.168693 | $0.181307 |
| total | $0.039382 actual | $0.066048 actual | $0.565590 estimated | $0.00 | $0.671020 | $0.428980 |

`actual` is xAI's completed-call `cost_in_usd_ticks` accounting. `estimated` is
the maintained cross-provider Opus 4.6 judge pricing calculation; it is
accounted conservatively but is not a provider-reported charge. All executed
calls reached terminal completion, so unresolved upper exposure is $0.00.

## Pre-Declared Stops

- Stop the affected lane before semantic scoring on access, strict schema,
  identity, terminal, image-packet parity, usage, or topology failure.
- Stop after its first candidate stage on any quality, assertion, latency, cost,
  reliability, safety, or eligibility failure.
- Do not turn a provider or adapter failure into a model-quality claim.

## Results and Decision

### Video-understanding

- Native and harness five-JPEG strict-schema probes returned exact `grok-4.7`,
  terminal completion, reconciled raw usage, five supplied ordered JPEGs, and
  no audio. The harness-parity probe took 6,029 ms and cost $0.009164 actual.
- The six maintained synthetic v3 controls were all valid and complete. The
  candidate averaged **0.4816 overall** (0.4982 deterministic, 0.465 rubric),
  **8,608 ms**, and **$0.008501 actual subject cost**. Quality is below 0.80;
  the per-case failures are semantic video-analysis misses, not a transport or
  schema failure. The prop-swap case was also 15,714 ms, although the lane's
  frozen latency gate is the average.
- Stop: no fresh Gemini comparator and no additional visual corpus. Result
  evidence is `benchmarks/results/video-understanding-grok47-v3-2026-09-22.json`
  and its paired report files.

### Script-Bible

- Native and repaired harness strict-schema probes returned exact `grok-4.7`,
  terminal completion, provider-strict `ScriptBible` JSON, reconciled raw
  usage, and `store=false`. The first harness probe was fully valid except for
  an adapter metadata omission; the marker repair was validated before one
  changed-evidence parity probe, not treated as a model retry.
- The one eligible synthetic Open Frequency subject returned in **25,533 ms**
  at **$0.015042 actual**, failing the $0.01 cost gate. Its aggregate was
  **0.80995** (deterministic hard score 0.6999; raw deterministic 0.8967;
  Opus rubric 0.92), also below 0.90. The deterministic journey/theme keyword
  misses conflict with a source-faithful cross-provider rubric reading and are
  retained as scorer-contract ambiguity. The recorded maintained hard score is
  below the gate, while the raw deterministic-plus-rubric average would clear
  it; the provider-reported subject-cost miss independently and decisively
  rejects the lane. There was no schema, source-eligibility, identity, or
  terminal failure.
- Stop: no fresh Gemini comparator and no second corpus. Result evidence is
  `benchmarks/results/script-bible-grok47-low-open-frequency-2026-09-22.json`.

### Offline scorer adjudication

The unchanged scorer replayed the saved response as `0.6999` hard / `0.8967`
raw, confirming that the original result is reproducible. Four failed theme
citations are source-faithful paraphrases or source-supported compression, but
the one relational compression cannot safely be distinguished from an invented
relation by a general lexical relaxation. The journey text is partly
source-backed and partly interpretive, with none of the frozen keyword anchors.
It remains an ambiguous weighted dimension, not a semantic model-loss claim.
No scorer or golden repair was applied; the original subject and judge
measurements remain immutable. See
`docs/evals/story-220-grok47-script-bible-offline-adjudication-v1.json` for
the source citations, hashes, and no-call replay record. The actual $0.015042
subject-cost failure remains the decisive rejection.

## Work Log

20260922-0000 — created isolated worktree `codex/grok47-eval-20260922` from
`origin/main` at `bdcea8d5b9fafe9f358274ee57ccf3987a07f49f`. The primary
checkout was left untouched because it is dirty and behind origin. Read the
maintained v3 video contract and Attempts 019/023. Added benchmark-only direct
xAI Responses strict-schema adapters for Grok 4.7.

20260922-0015 — focused adapter/unit validation passed (46 tests) before any
provider call. Resolved zero-cost one-provider topologies: six maintained
video controls and one exact-runtime Open Frequency control, all `--no-cache`
and serial.

20260922-0025 — completed video strict probes and the six-case candidate run.
All six result records were exact identity/schema/image-parity valid; quality
failed, so the video lane stopped before its Gemini comparator.

20260922-0045 — completed Script-Bible strict probes and the one-case
candidate. Repaired the observable provider-strict metadata marker, reran only
the affected parity probe after focused tests, then ran Open Frequency once.
The recorded hard score and actual subject cost stopped this independent lane
before a Gemini comparator or second corpus; the cost rejection is decisive
regardless of the scorer-contract ambiguity.

20260922-0115 — source-reviewed the saved Script-Bible output offline. The
unchanged deterministic scorer reproduced `0.6999` hard / `0.8967` raw. No
safe general evidence matcher repair could preserve the existing
source-grounding boundary, so no code, golden, subject, judge, or runtime change
was made. Recorded the versioned adjudication artifact; the $0.015042 actual
cost miss remains decisive.
