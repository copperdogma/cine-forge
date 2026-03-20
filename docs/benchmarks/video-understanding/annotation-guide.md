# Video Understanding Annotation Guide

## Goal

Create target files that are specific enough for deterministic scoring without collapsing the benchmark into OCR or metadata parroting.

## Per-Clip Files

Each clip directory must contain:

- `clip.mp4`
- `frames/`
- `meta.json`
- `target.md`
- `target.json`

## How To Author `target.md`

`target.md` is for the semantic judge. Keep it short and concrete:

- one summary sentence
- one line each for tone, emotion, color/grade, camera language, motion, continuity, and audio intent
- one transcript line if speech exists

Do not paste the entire JSON target into markdown form. It should read like a compact film note, not a schema dump.

## How To Author `target.json`

`target.json` is the deterministic contract. Fill these carefully:

- `required_keywords`
  - 2-4 words or short phrases the summary should not miss
  - avoid fragile phrasing; prefer robust cues like `confession`, `whip pan`, `continuity`
- controlled vocab tag lists
  - only use tags present in `VideoAnalysisTarget`
- `continuity_status`
  - `intact` when the clip preserves object/spatial continuity
  - `broken` when the clip visibly violates continuity
  - `ambiguous` only when the clip truly does not provide enough evidence
- `continuity_notes`
  - describe the one concrete continuity fact that matters most
- `audio_tags`
  - use `silent` only when the clip truly has no audio
  - do not fake lip-sync claims
- `anchor_subset`
  - `true` for the smaller calibration set used before full-matrix runs

## Keyword Rule

If a keyword is not required for a good director-facing read, do not put it in `required_keywords`. The scorer should reward the essential shot read, not every decorative object.

## Continuity Rule

Only mark `broken` when the clip packet makes the mismatch obvious. A weak or debatable continuity clue should stay `ambiguous`, not become benchmark noise.

## Audio Rule

V1 scores:

- speech presence / absence
- audio intent
- contrast between sound and image

V1 does **not** score:

- precise lip-sync
- phoneme-to-mouth alignment
- subtle off-screen ADR quality

## Weighting Rule

Use the default weights unless a clip is intentionally stress-testing one dimension. If you change weights, write a one-line reason in the story work log.

## Review Checklist

Before adding or changing a clip:

- Can another agent understand the target without asking you what you meant?
- Does the target reward director-facing interpretation rather than literal scene transcription?
- Is the continuity state honest?
- Is the audio annotation honest?
- Would the target still make sense six months from now without oral context?
