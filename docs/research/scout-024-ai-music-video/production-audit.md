# Scout 024 — independent production-pipeline audit

Date: 2026-10-04. Local baseline: `94861914623fff237ffb4ab379fa9f995a58da1e`.
Decision: recommend one bounded original music-video pilot using existing CineForge contracts. Do not adopt a new global IR, renderer, provider stack, model default, or savings target from this conversation.

Follow-up disposition (2026-10-04): user approved creating [Story 228 — Original Music Video Pilot](../../stories/story-228-original-music-video-pilot.md). It is Draft pending frozen original inputs, spend/rubric envelope and current baseline/capability evidence. The research evidence below remains the pre-implementation audit.

## Scope and evidence boundary

The supplied [shared conversation](https://chatgpt.com/share/6ac28257-df28-83e8-98fb-9f08657328fc) was recovered from its public response because the ordinary text reader returned no conversation. The linear conversation contains 99 nodes, including five user/text, 25 assistant/text and 27 tool/text nodes; 35 text outputs are redacted. All available substantive user/assistant text was inspected, covering replication, human work and costs, a CineForge experiment, deterministic graphics, and subscription/model allocation. Private or redacted tool results cannot be recovered from the share. An initial decoder duplicated mapping and linear entries; the final linear extraction removes that duplication.

Independent research inspected all six maker-authored Markdown records for CLODYSSEY and all six for ESCAPE VELOCITY: README, direction log, orchestration, Midjourney, Seedance and Suno prompt books. Making-of text supplied corroboration, not independent testimony. BLISS's README was inspected as a later production comparison; this is not a complete BLISS package audit. The six documents per production share an author and production provenance.

The [maker's production root](https://drive.google.com/drive/folders/1OKYaR5Kv5lOeIROUtigpPZtCWauUJ01y) is distinct from community reconstructions. [sources.json](sources.json) records retrieved document metadata and SHA-256 hashes of fetched text, repository pins, and local baseline. Full lyrics, prompt books and media are not redistributed here.

A published CLODYSSEY final-frame contact sheet was viewed: 24 stills, spaced roughly eight seconds apart. The sample shows a consistent teal/grey palette with orange accents and a mixture of cinematic images, typography and interface graphics. It cannot establish motion quality, lip synchronization, transition quality, or musical timing. No full master video was played, original full production replayed, provider invoices reconciled, or paid generation performed.

## What the original pipeline actually did

| Production | Maker-recorded shape | Important boundary |
|---|---|---|
| ESCAPE VELOCITY | 5:06.4; 141 shots, nine chapters; 188 image prompts, 159 completed jobs and 636 images; 130 plates; 47 motion clips plus 30 continuations; 91 submissions, 421 seconds of video | About 19 hours and 50 messages are elapsed workflow/message counts, not measured active labour. Maker reports roughly 86% of sung seconds matching reference audio, with repeated continuations and LatentSync fallback. |
| CLODYSSEY | Locked song 3:09.7, final 3:11.6; 94 shots, 11 sections, nine chapter files; 161 Midjourney prompts, 644 images, 116 plates; 99 final prompt-book entries and 101 clip records; 189 take/submission records, 183 returned videos | Final book has 27 singing windows, 67 motion clips and five V clips; two continuations create extra clip records. Six submissions returned no video. These counts describe different entities. |
| BLISS | 3:01.3; 44 shots at 130 BPM; 138 Midjourney prompts, 315 images; 35 Animate jobs, 70 videos; 50 Seedance clip records, 54 submissions, 267 seconds | Later strategy used cheaper background motion and a three-clip precision pilot. About 19 hours to v1 included nine hours awaiting permission. This is not an equivalent-quality controlled benchmark. |

Primary sources: [ESCAPE README](https://drive.google.com/file/d/1gVbLBH1PComXzu1ND8z-YLdjnd1-gZQn/view), [CLODYSSEY README](https://drive.google.com/file/d/1gjofYJQjHxMRBYotmUfXdzYboY5iyc_5/view), [CLODYSSEY take ledger](https://drive.google.com/file/d/10aBDkLVlxd2cJmfkUq1jHobHx3cPwhcZ/view), [BLISS README](https://drive.google.com/file/d/182X1dY2bgycH04-S61jfTzZlnzsDSqbu/view).

### 1. Human taste, song and a locked clock

The director supplied subject, emotional direction, artist/voice decisions, listening judgments, reference preferences, budget changes and final acceptance. Human tasks also included account setup, CAPTCHA clearing, retrieving audio, and quota recovery. The final CLODYSSEY song was generated independently by the human after the agent's Suno rounds; the agent did not autonomously make every final source.

Lyrics were iterated against scansion and sung performance. One numerical groove improvement from 94 to 98 made the lyrics worse to the director. The later metric used actual performance timings and human-ranked sections. This is evidence to calibrate musical metrics against perception, not evidence to adopt those scores as universal quality.

Locked audio then supplied sections, beats, word timing, singing windows and musical hits. Vocal isolation conditioned singing clips; ordinary motion clips used different audio treatment. BLISS initially followed hi-hats and placed its beat grid 214 ms early, then corrected to the kick. A timing tool must still be checked against the music.

### 2. Canon, storyboard and plate selection

The original already kept bibles, character/wardrobe rules, shot/clip JSON, edit data, take histories and run manifests. It was not merely one oversized chat. Midjourney generated plates through account/browser workflows with personal style settings. Human rankings promoted or rejected results and established the visual direction.

CLODYSSEY records 70 ranking rows on 68 plates: 43 picks, 13 rejects and 14 comments. Expanded rows sometimes represented one note covering several plates. Neither 68 messages nor 70 ranking rows equals that many distinct creative decisions.

ESCAPE's paper/canon tricks worked in that particular production and model setup. Overconditioning with face sheets and generating monochrome inputs caused problems there. Generate in full colour and grade later is a promising local experiment; do not treat it as a provider-independent law.

### 3. Compile actual shot action before generation

The first CLODYSSEY prompts often described weak poses. QA accepted some because the clips complied with weak specifications. Revised prompts specified changing belief, blocking, action, exact vocal delivery, and reaction rather than generic motion or camera instructions.

One concrete contrast in the Seedance book is M-s029: the revision turns a static pose into calculation, relaxation and surrender. W07 specifies action, whisper and reaction. Review dramatic sufficiency before checking provider compliance. Timestamp precision in prose remains requested control; the record does not benchmark actual rendered timing fidelity.

Prompt books and job payloads made submission mechanical. Helpers were instructed to submit lead-authored JSON verbatim and retry only failed items without assigned job IDs. A deterministic submitter can preserve this boundary with less context and ambiguity.

### 4. Generate takes, reconcile results and select

Reference plates, per-window audio, duration, continuity and provider constraints fed generation. Continuations were needed when sung audio diverged. Multiple attempts, moderation retries, reference repairs and human review were normal, not exceptional. Some first-round clips remained; V-s077 never produced footage and fell back to stills.

Stopping the main spending workflow did not stop a separate 3D spending stage. Later inspection had to find every generation call. This demonstrates the need for one production-wide spend permission checked immediately before every submission, including background workers.

BLISS's complete prompt book and three-clip pilot before the batch are a better starting pattern than a whole-video burn. The director sometimes granted blanket permission, so the invariant is explicit bounded authority, not compulsory manual reading of every prompt.

### 5. Inspect media and derive only needed post-production assets

CLODYSSEY's defect scan sampled six frames per selected take at 8%, 25%, 42%, 58%, 75% and 92%, at 640-pixel width. It covered 96 selected takes and then 23 remakes. This is useful sparse visual inspection, not frame-by-frame video or temporal validation.

Lip-sync checks largely compared generated audio with the reference. CLODYSSEY reports 16 windows checked through correlation, two partially, and seven more accepted visually. ESCAPE reports 86% of sung seconds; BLISS reports 7.4/11.9 seconds, 62%. These are maker measurements and mixed acceptance methods. Audio similarity is a proxy: it cannot measure whether a mouth follows phonemes.

Imported remakes eagerly queued depth/matte work. Roughly 80 remakes created about 20 hours of obsolete GPU work; cancelling 67 queued jobs prioritized nine selected takes needing mattes. Many SSH pollers overloaded CPU; one shared cached listing helped. Killing waiters left jobs alive, and reruns submitted duplicates. Persist external job identity and adopt existing jobs on restart.

Fifteen corrected plates shipped with masks/depth derived from their pre-edit images. A changed source must invalidate dependants. This was a concrete production compromise, despite the record's stated provenance principles.

### 6. Code the edit, graphics and grade

Chapter scripts combined footage, stills, mattes, captions, beat graphics and typography. A shared kit provided rendering/visual rules. Slow media preparation delayed kit review; chapter work began before that review. Specification review should not wait for all expensive derived media.

Rendering was designed as a function of requested time, with deterministic hashing and history checks. A frame should look the same after a seek, restart, or another frame's render. A per-clip LUT built from sampled frames kept grade stable rather than changing it frame by frame.

The original makers' full renderer and AV checker are referenced as internal files but are not published in these packages. Published orchestration scripts reveal interfaces and operations; they are not the complete engine.

### 7. Audio revisions, export and acceptance

A late CLODYSSEY audio change retained the approved edit clock through a time map instead of redistributing every cut. Added beats used slowed/replayed visuals; caption fades needed adjustment to avoid reappearing during replay. The record describes an initially drifting export and a later corrected one, with a loudness change; “sample-exact” cannot mean byte-identical audio.

Null reviews under quota exhaustion were treated as no fixes. The kit reviewer never ran, some chapter reviews returned nothing, and most final chapter scores remained around 7–7.5 against an eight-point bar. Human acceptance was positive, but it does not establish that every automated gate passed.

The maker's flash scan used small downsampled frames and simplified luminance/area rules. [W3C's three-flash guidance](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html) also concerns red flashes, area, viewing conditions and rolling intervals. Preserve the diagnostic; do not label it complete accessibility certification.

Sources for phases: [CLODYSSEY orchestration](https://drive.google.com/file/d/1Km3e1BemclCdZTJBhCOMK-yYwlQEjVar/view), [direction log](https://drive.google.com/file/d/1UL219t8Nl2vvmcMLQnzEeckm4hkRQJOO/view), [Suno record](https://drive.google.com/file/d/1oEtgG16lQxk9HL8FUsVcMdEknaDg1CqZ/view), [Midjourney record](https://drive.google.com/file/d/1l8VjxOO3NbTQCIVKFurj-zsT05i2rv3n/view), and [Seedance record](https://drive.google.com/file/d/10aBDkLVlxd2cJmfkUq1jHobHx3cPwhcZ/view). Specific anchors: orchestration's budget/queue/review postmortem around lines 830–924; Seedance totals around 29–49 and final assessment around 1526–1571; Suno final remap around 357–379.

## Corrections to the shared conversation

| Claim | Audit verdict |
|---|---|
| Roughly 41 hours, 68 messages; 94 shots; 644 images; 189 takes | Broadly supported, with entity/endpoint qualifications. Direction log's 41h23m ends at the making-of request and includes thumbnail/album work. 189 counts submissions; 183 returned video. |
| Seven to fourteen human hours, midpoint ten | Not measured. Active work, waiting and overlapping reviews are not reconstructed reliably. Wage totals inherit this uncertainty. |
| About $1,007 in LLM cost and 2.37 billion tokens | Maker's API-equivalent calculation over internal transcripts, not a cash invoice. Roughly 97% of tokens are cached rereads; cache reads still cost money. |
| About $107 OpenRouter video spending | Unreconciled ledger estimate at the recorded rate, including no-video submissions. Earlier ledger was $37.89 versus $36.38 at the provider endpoint; rejected submissions consumed the local budget incorrectly. |
| 2,436 useful Higgsfield credits plus 830 wasted; 20 credits per dollar | 2,436 recorded credits are not proven useful credits. Ledger includes 287 first-round credits while another passage calls about 830 all first-round spending; README says additional dropped takes. Additive accounting may overlap. No actual dollar-per-credit rate is recorded. |
| Around $1,350 AI spend / $2,500 all-in | Scenario estimates, not recovered total cash expenditure. Music/image subscription assumptions and labour estimates do not establish original costs. |
| Opus for taste, Sol for implementation; 70–90% LLM savings | Untested role and savings hypotheses. Original workflow agents already used Opus 5.5; weak prompts demonstrate missing intent/context/review rather than proof of a cheap-model problem. |
| New film/sequence/scene/beat/shot/take IR needed | Original already had durable production artifacts, and CineForge already has typed contracts for most layers. Extend demonstrated gaps. |
| Frame-by-frame checks and validated synchronization | Sampled frames and audio proxies; missing reviews and residual defects. Neither establishes complete temporal/mouth accuracy. |
| Music-video success makes feature-film scaling mainly engineering | Unsupported. Long dialogue, performance, continuity and long-horizon economics remain separate capability questions. |

A GitHub link embedded in the share, [escapewithpolly/escape-velocity-prompt-library](https://github.com/escapewithpolly/escape-velocity-prompt-library/tree/6daaf823712412e252c1afb82efec8740cf2d355), is an unrelated product/idea-to-revenue prompt library. Its name is not production provenance. Redacted tool results prevent proving exactly how the prior model used it.

Remaining primary-source inconsistencies are retained rather than averaged away: 24 versus 30 outside-workflow agents; first audio drift reported as 0.7 seconds versus up to 1.6 seconds of cut misalignment; a W15 continuation heading precedes its parent's time despite prose saying later. None changes the recommendation, but none should be used as precise baseline data.

## Public code: actual reuse boundaries

[Dracowyn's community skill](https://github.com/Dracowyn/ai-music-video-skill/tree/3d76b56945bb450e56fe79e4562498eb7558eb28) is a reconstruction. Its AV checker explicitly says it is an independent reconstruction of diagnostic plots. It never reads video pixels. An unchanged audio pass-through can score as aligned while a mouth is wrong. Synthetic thresholds, a ±1-second global lag range, downmix cancellation and full-mix ambiguity constrain applicability. Real sung-vocal alignment, Demucs stems and GPU/MPS behaviour remain untested according to its own README.

The community package's code/templates are MIT, with quoted prompt/lyric/source fragments excluded. It does not contain the original ESCAPE/BLISS engine.

The actual precursor [ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase/tree/0ac8bf2b31942376cb6b8c4074715595d512acd2) contains MIT-licensed renderer code: `src/core.js:284–301` resets frame state and exposes `renderAt(t)`; `core.js:21–26` and `clawd.js:64–67` seed individual elements; `render.mjs:116–136` uses isolated browser pages, a shared frame queue, resumable outputs and atomic renames. These mechanisms support deterministic rendering but do not prove history independence or cross-machine identical bytes. Remote fonts and conventional rather than enforced scene purity remain concerns.

[PDoomVideo](https://github.com/JohnHeibel/PDoomVideo/tree/fa546a38092e75f2b079e6a86d6abc54dd525d17) has real predecessor code, approximate character-rate karaoke and fixed BPM/offset. It has no LICENSE file, while package metadata declares ISC; record that weaker licensing evidence rather than claiming no declaration at all. Neither repository is the later makers' full engine. Media rights are separate from code licenses.

No renderer was run: its Node dependencies were not installed. Resume based on file size alone and logged browser errors should not be copied as acceptance gates.

The bounded general-technique pass also checked [Remotion's frame-function model](https://www.remotion.dev/docs/the-fundamentals) and [Anthropic's dynamic-workflow pattern](https://platform.claude.com/cookbook/claude-agent-sdk-08-dynamic-workflows). Decision: preserve frame purity and explicit workflow state, start with CineForge's existing media tools, and compare a specialised renderer only when richer graphics justify a dependency. No external framework was adopted.

## Subscription and model claims

Live discovery ran with `scripts/discover-models.py --check-new --yaml`: all five configured catalog queries succeeded. Exact `gpt-6.1-sol`, `gpt-6-astra` and `claude-opus-5-5` were API-listed. Catalog listing is not a served-response identity check, qualification run, consumer quota guarantee, or model-role evaluation. Discovery's heuristic tier labels were not used to rank capability.

The proposed Claude $20 / ChatGPT $200 setup is a possible operating arrangement, not a production-capacity guarantee. [OpenAI pricing documentation](https://learn.chatgpt.com/docs/pricing) separates subscriptions and API usage and describes shared usage/limits. [Anthropic's Claude Code plan guidance](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) says Code and chat share plan limits; an API-key environment can switch execution to separately billed API use.

The [Claude Agent SDK plan article](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan) has a top notice pausing its earlier credits rollout: SDK, `claude -p` and third-party integration usage currently continue to draw from subscription usage. Do not apply the superseded lower-page rules. Direct [Claude API/Console billing remains separate](https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-do-i-have-to-pay-separately-to-use-the-claude-api-and-console).

Measure exact served identities, quality, repeated context, wall time, quota interruptions and chargeable usage in a pilot. A model judged better at aesthetics should earn that role on frozen material; no automatic default change follows from this scout.

## Fit with current CineForge

Alignment checked against Ideal, spec, methodology/state, graph, build map and stories dashboard. Music videos are in the Ideal; an exportable original creative result fits the product direction. Canonical state keeps `spec:6` and `spec:7` active, generation partial/climb and timeline exists/hold. This research does not change priority or canonical planning state.

[ADR-003](../../decisions/adr-003-film-elements/adr.md) already separates intent-bearing film elements from compiled provider instructions. Compiled prompts remain read-only: change intent upstream. No dedicated overlay-renderer ADR currently decides a JS implementation.

| Existing local substrate | Consequence |
|---|---|
| `ScriptBible`, `Scene/NarrativeBeat`, `ShotPlan`, `RenderClipPlan`, `GeneratedVideoArtifact`, `Timeline/TrackManifest` | Reuse; do not replace with a new IR. See `schemas/scene.py:40`, `shot_plan.py:43`, `render_clip_plan.py:21`, `render.py:151`. |
| Render prompt compiler and capability-aware request shaping | Reuse `modules/generation/render_adapter_v1/prompting.py` and `request_shaping.py`. Provider constraints belong at this seam. |
| Selected design-study results become a human-provenance canonical bible version | Reuse promotion; multi-view/reference-pack improvements already belong to [Story 197](../../stories/story-197-reference-pack-visual-fidelity.md). |
| Existing project/run budget status and stage-boundary guard | Extend [Story 138](../../stories/story-138-cost-profiles-model-comparison-stage-budgets.md)'s ownership. Current guard does not reserve a paid batch before every submit. |
| Existing work/verify/escalate tiers | Test narrow roles within existing configuration; avoid another global model router. |
| Versioned generated video with active-track replacement after regeneration | Add explicit candidate/selection decisions rather than a new artifact store. |
| Probe + sampled-frame media validation | Reuse evidence schemas; temporal/audio synchronization is a genuine detector gap. |

The strongest missing contracts are an authoritative selected audio master and alignment/timebase, deterministic timed graphics, and explicit video take selection. Current final assembly concatenates source clips; it does not lay a selected project song over the edit. Its normalized path omits all audio if any input lacks audio (`final_output_v1/main.py:476–498`). All shipped video engine packs declare `supports_audio_upload: false`. Post-production song preservation and provider audio conditioning are separate requirements.

Existing timing is floating-point seconds and estimated durations, not an explicit musical sample/frame clock. Exact preview/export timing needs a tested contract, not more timestamp fields.

## Recommended first experiment

Create one M-sized story for a 20–40-second original passage with six to ten shots, one visual canon, one timed title/super, one on-camera singing window only if the chosen provider supports it, and a deliberately small take allowance. This is a proposal, not an implemented capability.

Use normal API/driver-produced state and current artifacts. Add only missing song/timebase, overlay and selection contracts. Freeze the song passage, human intent, quality bar, candidate/comparator model arms, spend cap, retry limit and stop rule before paid calls. Do not assume a browser subscription provider has a production API.

Separate three judgments: specification quality, clip compliance, and finished musical/visual coherence. Have an independent agent conduct a focused creative probe and the human optionally assess the export. Missing/incomplete reviews are unresolved states.

Record:

- Exact served model/provider IDs, response IDs, raw usage, estimated/reserved/actual costs, external job IDs and every rejection.
- Human active work separately from waiting; context volume and quota interruptions separately from generation spending.
- Accepted cost per second/shot and quality against the frozen bar, rather than token totals alone.
- Song-span preservation and preview/export agreement; overlay boundaries within one output frame; seek-history consistency.
- Review coverage by expected IDs; take selection lineage; stale derivative invalidation; safe interrupted-job recovery.

For role comparisons, use identical frozen inputs and maintained comparator/judge contracts. Marginal same-provider judgments need independent corroboration. A scored comparison belongs in the eval registry and owning story; this scout ran no model eval and changed no scores.

Stop at the cap or when a required provider capability is absent. Label a stills fallback or unsupported singing lane honestly. A successful pilot proves this slice, not full-video economics or feature-film capability.

## Verification performed

Read-only research agents audited original records, local contracts and precursor/community code. Local checks passed 13 focused unit tests for budget guard, render clip planning, final-output schema and media-validation schema. These are existing-contract checks, not full application acceptance.

Community fixture checks: 69 passed / one environment skip in CineForge's virtualenv; the missing-schema test then passed in the existing Miniconda environment. Five further synthetic CFR/contact-sheet cases passed, including audio-bearing GOP seeks and cut-boundary frames: 75 distinct selected tests passed in total. No dependencies installed.

Reproduction commands (pins above; temporary paths must be recreated if removed):

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q \
tests/unit/test_budget_guard.py \
tests/unit/test_render_clip_plan_module.py \
tests/unit/test_final_output_schema.py \
tests/unit/test_media_validation_schema.py

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/cineforge-scout-024-skill/skills/ai-music-video/scripts:/tmp/cineforge-scout-024-skill/tests:src \
.venv/bin/python -m pytest -p no:cacheprovider -q \
/tmp/cineforge-scout-024-skill/tests/test_cut_stats.py \
/tmp/cineforge-scout-024-skill/tests/test_resolve_shots.py \
/tmp/cineforge-scout-024-skill/tests/test_validate_shots.py

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/tmp/cineforge-scout-024-skill/skills/ai-music-video/scripts:/tmp/cineforge-scout-024-skill/tests:src \
/Users/cam/miniconda3/bin/python -m pytest -p no:cacheprovider -q \
/tmp/cineforge-scout-024-skill/tests/test_resolve_shots.py::test_resolved_fixture_matches_schema \
/tmp/cineforge-scout-024-skill/tests/test_contact_sheet.py::test_extract_frames_is_frame_accurate \
/tmp/cineforge-scout-024-skill/tests/test_contact_sheet.py::test_extract_frames_is_frame_accurate_with_an_audio_track \
/tmp/cineforge-scout-024-skill/tests/test_contact_sheet.py::test_handoff_frames_around_a_cut \
/tmp/cineforge-scout-024-skill/tests/test_contact_sheet.py::test_handoff_sheet_cli_pillow
```

The schema and contact-sheet checks originally ran separately. Dependencies available in CineForge include pytest/Pillow; audio-analysis dependencies needed by the reconstruction are absent. Synthetic correctness does not establish real-song alignment, mouth accuracy, original-engine reproduction or creative quality. No implementation, production-state changes, commits or pushes occurred.
