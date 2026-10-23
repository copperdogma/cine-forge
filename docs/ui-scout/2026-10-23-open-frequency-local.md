# UI Scout — 2026-10-23 — `open-frequency` — local

**Scenario:** FP1
**Date:** 2026-10-23
**Operator:** Codex
**Story:** 232; targeted next-action repair233
**Trigger:** 194-day overdue canonical product-truth recheck after185/201
**Fixture:** tests/fixtures/ingest_inputs/open_frequency_short.fountain
**Project:** open-frequency, freshly created through normal /new file chooser
**Environment:** API http://127.0.0.1:8000; UI http://127.0.0.1:5174
**Git:** dirty main at714802a; no commit/push
**Overall result:** Blocked — bounded execution stopped before media generation
**Functional reach:** Intake, complete script breakdown and scene Render preflight verified;
actual scene render and prompt/video/validation detail not exercised
**UX / trust:** Issues Found; targeted repairs tracked in233

## Environment Checks

- API health200; current checkout API/UI service ownership verified.
- CUA's normal file chooser successfully attached the real3447-byte fixture.
  Uploaded bytes exactly match SHA256
  81508ec3a2be376efbc8f8d720dea2784eec5dba3664372df3f65123f8684d95.
- Existing OpenAI key reuse explicitly approved by Cam. No key created or changed.
  Live provider catalogs succeeded for OpenAI/Anthropic/Google/xAI/Moonshot;
  generation access is proven only for the actual stages that ran.
- No seeded/copied project, manual recipe launch or raw-artifact starting point.
  Artifact reads below are diagnostic inspection after the surfaced workflow.
- Desktop1600x1100; mobile390x844 on this same project. Browser error log empty.

## Execution Envelope and Cost

One fresh intake and one Break Down Script CTA. Quick-scan uses the shipped
Sonnet4.6 title extractor (max2 attempts,256 output tokens, short ASCII fixture;
conservative USD0.10 envelope). Its metadata is discarded by the current app,
so its actual billing is unavailable. Published pricing checked at
[Anthropic's Sonnet4.6 documentation](https://platform.claude.com/docs/en/models/sonnet-4-6/overview).

Before breakdown, normal Advanced → Settings → Pipeline saved project and run
thresholds of USD5. The actual mvp_ingest run-fae39865 completed all five stages,
with recorded estimated cost USD0.0809394. Normalization was code-only;
breakdown cost0.014574, Bible0.045471, config0.0208944. These are app estimates,
not provider invoices. No breakdown retry, Deep Breakdown, Storyboard, Previz,
Render or final-output generation was launched for this run.

The envelope required inspecting render work/cost before allowing media.
Render preflight does not expose a clip count or cost before preparation; its
single media stage may generate multiple clips. BudgetGuard pauses after a
stage/wave, allowing within-stage overshoot. Thus the remaining USD5 could not
be qualified from the surfaced state. Stopped at preflight as declared. This
is an execution-envelope limit, not evidence of a provider failure, exhausted
account credit, or inability to render. No new strict-cap feature was added.

## Exact Path Walked

| Surface | Route / action | Result |
|---|---|---|
| Landing/intake | / → New Project → /new; canonical chooser upload; Create Project | Pass; detected Open Frequency; assigned /open-frequency |
| Initial Script | /open-frequency | Raw screenplay visible; Break Down Script CTA present |
| Budget controls | Advanced → Settings → Pipeline | Both USD5 thresholds saved through UI |
| Script pass | Break Down Script; stayed on Script | All5 stages done; all4 scenes and Bible available; details optional |
| Intent | /open-frequency/intent | Honest Deep Breakdown prerequisite and Run Deep Breakdown action |
| Scenes | /open-frequency/scenes | All4 headings in script order; scene cards open workspace |
| Characters | /open-frequency/characters | Empty; baseline pipeline instruction had no next-action button |
| Locations | /open-frequency/locations | Empty; same baseline dead end |
| Inbox | /open-frequency/inbox | All caught up; no fabricated attention items |
| Scene overview | Scenes → scene_001 | Script entities, tutorial and downstream tabs surfaced |
| Shots | scene_001?tab=shots | Runnable with auto-build/context warnings; not executed |
| Storyboard | scene_001?tab=storyboard | Runnable with shot-plan auto-build; not executed; template-grid provider transport untested |
| Render | scene_001?tab=render; Jump to selected panel | Reachable/runnable with warnings; no clip/cost estimate before prep; not executed |
| Mobile Script | /open-frequency,390x844 | Screenplay primary, controls fit; no document overflow |
| Mobile Render | same scene through Scenes and Render tab; Jump to selected panel | Action/scope/warnings fit; no document overflow; no generation clicked |

## Honest Current Boundary

Fresh normal intake → complete mvp_ingest → scene Render preflight is demonstrated.
Actual scene generation, automatic prep execution, template-grid image requests,
media quality, playback, Prompt Detail, Video Detail and Validation Detail are
**unverified here**. The last complete successful FP1 remains2026-04-12; this
partial run must not replace it with a new Pass. State uses its existing issues_found status with232/233 follow-ups, so triage
retains the blocked continuation;232 itself is Blocked.

## Findings

### 1. First-use next actions contradict the shipped route

- **Type:** Trust / functional guidance; owner233.
- Render preflight promises automatic shots, while Shot / Render Units says
  Run Shots first. Clip planning offers Open Render on the active Render tab.
- Characters/Locations empty states say run the world-building pipeline but
  offer no way forward, despite Intent already exposing Deep Breakdown.
- These are deterministic route/copy problems; no model-default decision is needed.
- Baseline is preserved in render-before.txt and screenshots08/09/14/17.
  Targeted follow-up evidence will be separate and will not rewrite this report's
  incomplete media coverage into a full Pass.

### 2. Media spend cannot be bounded from this fresh surfaced preflight

- **Type:** Execution/coverage limitation; continuation owner232.
- Clip count and cost emerge only after preparation; the current guard pauses
  after stage/wave completion. A USD5 setting is not a strict request ceiling.
- Next: establish a concrete bounded media execution route before the paid
  continuation. This observation alone does not prescribe a new budget system.

### 3. Artifact review found a hyphenated time-of-day split

- **Type:** Derived-data correctness; next triage candidate under ingest ownership.
- Scene003 heading remains INT. HIGH SCHOOL GYM SHELTER - PRE-DAWN, but its
  location is High School Gym Shelter - Pre and time_of_day is DAWN. The source
  says High School Gym Shelter and PRE-DAWN. All4 QA flags are green, so those
  flags do not establish semantic correctness. Preserve this failing canonical
  input and inspect the parser/QA owner before choosing a fix.
- The Bible broadly follows the storm/radio/community arc, but asserts an
  American town without explicit country evidence. That assertion is
  **model-wrong / non-runtime-blocking** on manual inspection, not a new numeric
  score (existing Script Bible owner093). The header split is deterministic pending source attribution, not
  evidence to change models. No scored eval was run or adopted.

## Evidence Summary

Evidence folder: docs/reports/story-232-canonical-ui/.

- intake-proof.json records fixture/upload identity and actual project settings.
- run-state.json and artifact-review.json preserve completed pipeline details
  and the observed semantic gaps; no secret values are retained.
- Screenshots01–17 cover intake, settings, Home, routes, downstream preflight
  and mobile. Shot/Storyboard screenshots are route evidence, not output proof.
- console.json contains[]; locator waits for an incorrect empty-page heading
  were automation setup mistakes, not browser/app errors.
- Temporary3-scene count during breakdown was resolved: scene003 saved18s after
  others; completed index/artifacts contain all4. Do not report scene loss.
- Smooth Jump scrolling needs a settled capture:17 is taken with the Render
  panel at y155.75. An earlier transition capture is not acceptance evidence.

## Next Action

Complete the bounded233 guidance repair, retaining this failed/partial baseline.
Then resume232 only with a declared media envelope that can actually be checked;
use a new dated full-path report for any subsequent complete walkthrough.

## Targeted follow-up — Story233

The three next-action defects above are repaired and independently reviewed.
Real same-project desktop/mobile button and copy checks pass; details are in
 docs/reports/story-233-first-use-guidance/report.md. No media was generated.
The blocked/partial FP1 result and unverified downstream steps above remain
unchanged. PRE-DAWN extraction remains a separate ingest candidate.

## Extraction follow-up — Story005

The PRE-DAWN delimiter regression is repaired and independently reviewed in the
existing extraction owner005. A deterministic run against this exact normalized
canonical input produces the correct scene/index location, time and spans, with
zero provider calls. Evidence: docs/reports/story-005-heading-delimiters/report.md.
The original v1 runtime artifacts remain unchanged, and no fresh media/full FP1
Pass is implied. The separate Bible country assertion remains uncorrected.


## Accounting and provider follow-up — Story032

Typed media costs, unknown charges and replay guards are repaired and validated.
Same normal Open Frequency and historical Brick runtime projects were inspected
on desktop1600x1100/mobile390x844 with empty warning/error console. Cost cards
qualify estimates and incomplete historical subtotals; saved media shows unknown
completeness without repricing immutable history. Current Scene and All Scenes
Render are now honestly disabled: the configured Veo3.1 preview endpoint retired
2026-10-22. API starts return422 before a new run; historical incomplete media
retry/resume return409. No new media or full FP1 Pass is implied. Evidence:
`docs/reports/story-032-media-accounting/validation.md`. The current media
qualification and inspectable-work continuation remain138/232.
