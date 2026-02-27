# Story 098: Real-World Asset Upload Pipeline

**Status**: Draft
**Created**: 2026-02-27
**Source**: ADR-003, Decision #9, Ideal R17
**Spec Refs**: 18 (User Asset Injection)
**Ideal Refs**: R17 (real-world assets as first-class inputs)
**Depends On**: Story 029 (user asset injection — lock system, validation, manifest)

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

## Relationship to Story 029

Story 029 (User Asset Injection) covers the lock system, validation, manifest tracking, and downstream integration hooks. This story focuses on the upload UX and the origin-agnostic pipeline guarantee. They may be combined during implementation planning.

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
