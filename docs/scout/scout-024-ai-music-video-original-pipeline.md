# Scout 024 — AI music video: original production pipeline

**Source:** [Entire available shared conversation](https://chatgpt.com/share/6ac28257-df28-83e8-98fb-9f08657328fc), independently checked against maker records and pinned public code.
**Scouted:** 2026-10-04
**Scope:** Full CLODYSSEY and ESCAPE VELOCITY Markdown production records; supplemental BLISS README; original precursor code and community reconstruction; live CineForge fit.
**Previous:** None for this production. Scouts 021–023 supply related source history, not current implementation truth.
**Status:** Complete — approved pilot deferred to Story 228; no runtime changes

[Detailed independent audit](../research/scout-024-ai-music-video/production-audit.md) · [Source manifest](../research/scout-024-ai-music-video/sources.json)

## Findings

### Recommended pilot and immediate ownership

1. **Authoritative song clock and master assembly** — HIGH value; M; propose owning pilot story.
   Original locked song/word/beat timing and preserved cuts through late audio changes. CineForge has timeline/clip artifacts but lacks an explicit musical timebase/master assembly. All shipped engine packs currently reject audio upload.
   **Exemplar:** Locked timeline and final-audio remap in CLODYSSEY Suno record.
   **Invariant:** Accepted edits name an audio version and reproducible clock; revisions cannot silently move cuts.
   **Adaptation:** Minimal immutable song/alignment contract through existing timeline/export seams; separate assembly from provider conditioning.
   **Proof target:** Normal API/driver export preserves the passage; preview/export agree within one frame; audio revisions explicitly map or invalidate dependants.

2. **Deterministic graphics as a narrow compositor lane** — HIGH value; S/M for title/super; L for full depth/WebGL engine.
   CineForge has no first-class timed-overlay contract. Start with one title/super using existing media tools; compare a specialised renderer only if justified.
   **Exemplar:** Time-pure maker chapters and MIT ClaudeAnimationBase's renderAt(t), per-element seeds and isolated pages.
   **Invariant:** A frame depends on declared time and pinned inputs, not seek history, wall clock or random call order.
   **Adaptation:** Schema-first overlay/track contract and smallest renderer with pinned fonts/assets; no copied creative media/private engine.
   **Proof target:** Sequential, out-of-order and resumed frames match in one pinned environment; preview/export text and timing agree.

3. **Review intent before a bounded generation batch** — HIGH value; M; extend cost ownership.
   Weak original prompts produced compliant but weak clips. Background generation continued after a stop. Current stage guard does not reserve each paid batch.
   **Exemplar:** Revised action/reaction prompts; BLISS three-clip pilot; original production-wide stop failure.
   **Invariant:** Every paid request names the current approved intent/version and available bounded spend authority.
   **Adaptation:** Readable manifest from existing compiler, explicit review state, reservations and immediate pre-submit revocation check; coordinate with Story 138.
   **Proof target:** Intent changes revoke all workers; concurrent submissions cannot exceed the cap; rejected calls reconcile provider charges.

4. **Explicit take selection and review coverage** — HIGH value; S/M; pilot slice.
   CineForge versions outputs, but regeneration updates active tracks without a separate video candidate-selection contract. Original null reviews sometimes skipped fixes.
   **Exemplar:** Take ledger and quota-exhausted review failures.
   **Invariant:** Missing, invalid, incomplete, quality-failed and passed reviews differ; selection names immutable evidence, not latest.
   **Adaptation:** Reuse artifact/validation schemas for candidate IDs, rejection reasons and selected references. Investigate coverage rather than assuming CineForge has the original bug.
   **Proof target:** Omitted expected IDs or quota loss prevent acceptance; selecting an older take preserves lineage.

### Conditional transfers after the pilot demonstrates need

5. **Selected-take post-processing and interruption-safe jobs** — HIGH when needed; M; defer.
   Original eager masks/depth jobs produced obsolete backlogs, duplicate work and stale corrected-plate derivatives.
   **Exemplar:** Cancelling 67 queued jobs to prioritise nine mattes; persisted job IDs and shared polling.
   **Invariant:** Work keys actual input/version and selected need; restarts adopt jobs; edits invalidate dependants.
   **Adaptation:** Extend lineage/job records before introducing a GPU scheduler.
   **Proof target:** Changed plate cannot use its old matte; restart does not resubmit; rejected takes avoid expensive post jobs.

6. **Audio diagnostics with honest visual acceptance** — MEDIUM/HIGH; M; conditional singing lane.
   Community AV checker is audio-only and synthetically calibrated. Maker percentages are not direct mouth-motion measurements.
   **Exemplar:** Audio lag and divergence-cut diagnostics.
   **Invariant:** Audio-copy success cannot substitute for visual phoneme/mouth judgment.
   **Adaptation:** Reuse media-QA evidence, test real sung vocals and pair diagnostics with temporal review.
   **Proof target:** Identical copied audio with deliberately wrong/frozen mouth fails visual acceptance.

7. **Stable grade and dependency-aware finishing** — MEDIUM; S/M; defer.
   Original multi-frame-derived LUT stayed constant over each clip and used a human-approved reference.
   **Exemplar:** Original 16-frame LUT import.
   **Invariant:** Grade is temporally stable and names source/reference versions.
   **Adaptation:** Focused finishing artifact only if pilot continuity requires it; no copied palette constants.
   **Proof target:** Preserve intentional accents without adaptive flicker; reference change invalidates finishing.

8. **Measure context and model roles on frozen material** — MEDIUM/HIGH; S investigation, bounded eval story if adopted.
   Original repeated context dominated tokens, but no Sol/Opus comparison establishes 70–90% savings. Existing work/verify/escalate configuration is sufficient.
   **Exemplar:** Mechanical submitters separated from creative authors and original context accounting.
   **Invariant:** Small sufficient authoritative context, measured quality and explicit escalation.
   **Adaptation:** Frozen candidate/comparator/judge arms within existing tier configuration; exact served IDs/raw usage.
   **Proof target:** Comparable accepted quality with lower observed total cost/quota burden, including reviews/retries. No default before qualification.

### Reuse existing architecture; skip unsupported additions

9. **Visual canon and reference promotion** — HIGH already present; reuse.
   Selected design-study results already promote canonical human-provenance bible versions and flow into references. Multi-view curation belongs to Story 197; no second canon manager.

10. **Intent IR, provider compiler and router** — LOW replacement value; reject.
    ScriptBible, Scene/NarrativeBeat, ShotPlan, RenderClipPlan, GeneratedVideo and Timeline/TrackManifest already cover most proposed layers. ADR-003 owns intent compilation and provider shaping. Original also had durable artifacts. Extend demonstrated gaps.

11. **Wholesale browser automation, custom engine and provider stack** — LOW copying value; skip.
    Published internal engine/checker implementations are absent. Browser flows depended on human CAPTCHA, quota/account state and brittle interaction. Public precursor code informs techniques; community reconstruction is not the original engine.

12. **Fixed labour/cash totals, guaranteed savings and feature-film conclusions** — LOW baseline value; reject.
    Human labour was unmeasured; OpenRouter costs estimated; Higgsfield conversion absent and waste accounting possibly overlapping. Missing reviews/residual defects shipped. Music-video success does not prove film-length performance or economics.

## Alignment and recommendation

Checked current Ideal/spec, methodology stack, canonical state, graph, generated dashboards and ADR/design sources. Music videos fit the Ideal; spec:6/spec:7 remain active and generation is in climb. ADR-003 owns intent/compiled-prompt separation. No dedicated graphics-renderer ADR selects JS. No planning priority or existing story was changed.

Recommend one **M-sized original pilot story** combining the smallest coherent slices of 1–4: 20–40 seconds, six to ten shots, one canon, one title/super, bounded takes, preserved song and explicit selection/review. Include singing only if the selected provider supports it. Items 5–8 remain conditional; 9 reuses existing ownership; 10–12 are rejected/skipped.

## Approved

2026-10-04: User approved creating the recommended pilot story. [Story 228 — Original Music Video Pilot](../stories/story-228-original-music-video-pilot.md) now owns the smallest coherent slices of items 1–4, with status Draft. This approval was for story creation; this scout did not execute the production or change runtime behavior.

- [x] 1–4: Create bounded original-pilot story — deferred to Story 228; story creation verified.
- [ ] 5–8: Conditional transfers — not selected.
- 9: Reuse current canon/reference flow.
- 10–12: Replacement architecture, wholesale port and unsupported baselines rejected.

## Verification and evidence

- All six CLODYSSEY and six ESCAPE Markdown records audited; BLISS README supplemental.
- Entire available conversation inspected; redacted outputs remain unavailable.
- Public source pins and rights distinctions recorded in the detailed audit.
- 13 focused existing CineForge unit tests passed.
- 75 distinct community fixture/synthetic extraction tests passed after resolving a missing-jsonschema skip using an existing environment.
- Live catalogs queried; no paid inference, model eval, adoption decisions or registry score changes.
- Final contact sheet inspected; no full-video playback, original-engine replay or real-song alignment check.
- Manifest, document links and scoped whitespace checks verified during close-out.
- Story 228 created with source/eval/ADR links, concrete acceptance criteria, Draft readiness gaps and shared cost/reference ownership. Planning surfaces compiled and checked.
- No dependencies installed, production state changed, commits or pushes made.

Research files are the deliverable. **No transfusion proof target above is claimed achieved:** those are future implementation acceptance criteria, not results of the synthetic source-tool checks.
