# Story 098: Real-World Asset Upload Pipeline

**Status**: Cancelled — merged into Story 029 so asset upload ships as one end-to-end user feature instead of a backend/UI split.
**Created**: 2026-02-27
**Source**: ADR-003, Decision #9, Ideal R17
**Updated**: 2026-03-14 — merged into Story 029 after user review rejected backend-only completion.
**Cancelled**: 2026-03-14
**Spec Refs**: 18 (User Asset Injection)
**Ideal Refs**: R17 (real-world assets as first-class inputs)
**Depends On**: Story 029 (user asset injection — lock system, validation, manifest)
**Merged Into**: Story 029 (User Asset Injection)

---

## Goal

Build the **upload pipeline** for real-world production assets — the R17 requirement that CineForge works for partial workflows where users bring their own actors, locations, props, and audio.

## Why (Ideal Alignment)

R17: "The system must accept real-world production assets as first-class inputs at any point in the workflow." A filmmaker using CineForge only for previz while shooting a real film needs to upload headshots of real actors, photos of real locations, and recordings of real audio. These must slot seamlessly into the same reference systems that AI-generated assets use.

This is a core design principle, not a feature. The entire pipeline must be origin-agnostic.

## Acceptance Criteria

- [ ] Upload UI: drag-and-drop or file picker for images, video, audio, documents
- [ ] Uploaded assets automatically associated with the correct entity (character, location, prop) or concern group
- [ ] Uploaded assets appear in the same reference image / audio browsers as AI-generated assets
- [ ] No pipeline stage distinguishes between uploaded and AI-generated assets
- [ ] Supported formats: common image (JPEG, PNG, WEBP), video (MP4, MOV), audio (WAV, MP3, AAC), document (PDF, TXT)
- [ ] Asset thumbnailing and preview generation
- [ ] Bulk upload support (e.g., 20 location scout photos at once)

## Notes

20260313 inbox triage folded three ADR-003 Decision #9 ideas into this story instead of keeping them as separate backlog items:
- AI enhancement of minimal inputs: headshot → fuller character reference set, phone video → cleaned location stills
- Location lookup from web: fetch public exterior/reference images as raw inputs to the same asset pipeline
- Mood-board synthesis: multiple inspiration images used together as reference input for design generation

These are extensions of the same origin-agnostic asset pipeline, not separate product tracks. Implementation planning should evaluate whether they belong in Story 098 directly, Story 029's injection layer, or as a render/design-study follow-up once the upload foundation exists.

## Relationship to Story 029

Story 029 (User Asset Injection) now covers the lock system, validation, manifest tracking, downstream integration hooks, and the Operator Console upload/manage UX. Keeping this as a separate story would recreate the exact backend/UI split that made the feature unusable.

**Merge note (2026-03-14):** This story is cancelled as a standalone backlog item and preserved only as historical record. Its acceptance criteria now live in Story 029.

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.

20260314 — Backlog cleanup: clarified that Story 098 is not an independent near-term pick; it remains downstream of Story 029's injection layer and may be merged with that work when implementation starts.

20260314-1305 — merged: user review rejected the backend/UI split for a user-facing feature, so Story 098 was merged into Story 029 and cancelled as a standalone story; next=`track all remaining upload UX work in Story 029 only`.
