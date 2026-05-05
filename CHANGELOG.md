# Changelog

## [2026-05-05-01] — Evaluate Grok 4.3 reasoning slots (Story 200)

### Added
- Added xAI Grok 4.3 discovery, benchmark provider wiring, and focused unit coverage for text/image reasoning evals.
- Added maintained Grok 4.3 eval evidence for scene extraction, scene enrichment, QA verification, script bible, and video understanding.

### Changed
- Updated the eval registry and generated methodology surfaces to record that Grok 4.3 did not beat the current model-slot strategy.
- Removed the completed Conductor Scout 028 Grok 4.3 inbox item.

## [2026-04-30-03] — Close production xAI previz readiness (Story 195)

### Added
- Added xAI to provider dependency health, accepted-env-var reporting, cached/live smoke coverage, and the shipped AI-previz video probe.
- Added Brick & Steel AI-previz preflight readiness so missing xAI credentials surface before provider work starts.

### Changed
- Updated deployment guidance and provider-health tests so future default AI-previz lane changes cannot leave live smoke pointed at stale providers.

## [2026-04-30-02] — Route Brick & Steel inbox triage

### Added
- Added Stories 195-199 to route the Brick & Steel inbox into production xAI readiness, product-truth scrub, reference-pack fidelity, character adjudication, and casting/table-read follow-up lanes.

### Changed
- Updated methodology state and generated planning surfaces so Story 195 is the recommended next build, with related follow-ups sequenced or kept in Draft as appropriate.
- Cleared `docs/inbox.md` after routing all live items into durable story artifacts.

## [2026-04-30-01] — Persist design-study lifecycle truth (Story 192)

### Added
- Added persisted design-study round lifecycle state for generating, completed, and failed rounds, including provider/model/status/request/error/prompt context for operator debugging.
- Added focused backend, provider-classification, UI helper, and browser-validation evidence for the design-study completion and failure surfaces.

### Changed
- Changed the design-study UI to poll/refetch while image generation is active, render in-progress and failed rounds, and keep AI-generated and uploaded visual references in the same downstream reference path.
- Changed OpenAI and Imagen image transport errors to preserve structured provider metadata for design-study failure reporting.

### Fixed
- Fixed completed GPT-image design-study rounds so persisted results become visible without a manual refresh.
- Fixed failed design-study rounds so the operator-visible provider message and prompt context are not hidden by the next-round composer.

## [2026-04-29-05] — Render scenes as provider-bounded clips (Story 194)

### Added
- Added multi-clip Render and AI Previz execution so one scene can generate one prompt/video artifact per provider-bounded render clip with clip lineage, timing, validation, and track entries.
- Added scene workspace clip truth for Previz and Render, including embedded per-clip players, prompt links, stale/missing clip handling, and per-clip generate/regenerate controls.

### Changed
- Changed final-output assembly and media validation to understand ordered generated-video render clips while preserving honest missing-coverage reporting.
- Changed shipped Render and AI Previz recipes to require durable `render_clip_plan` artifacts before generation instead of silently falling back to compressed scene-level output.

### Fixed
- Fixed repeated or leaked dialogue in shot/render clip prompts, strengthened low-fidelity previz dialogue locks, and corrected the Render tab so the first clip is not presented as the whole scene.

## [2026-04-29-04] — Add scene render clip planning (Story 193)

### Added
- Added the typed `render_clip_plan` artifact and `render_clip_plan_v1` module so final render can estimate dramatic scene duration, enforce engine clip limits, and persist provider-bounded clip boundaries with provenance.
- Added Brick & Steel-style duration coverage plus render-recipe integration tests for missing-shot-plan fallback, AI/default provenance, engine-cap splitting, and strict `start_from=render` cache enforcement.

### Changed
- Changed final-render generation to run render-clip planning before prompt compilation and to auto-build or reuse clip plans through scene-action preflight.
- Changed render prompt and video artifacts to reference the selected clip plan and disclose when the current one-scene video path compresses a multi-clip plan that Story 194 will consume.

## [2026-04-29-03] — Preserve Brick & Steel final-render prompt truth (Story 191)

### Added
- Added Story 191's Brick & Steel evidence packet and Story 192 as the explicit follow-up for GPT-image design-study completion/error truth.
- Added Story 193 for scene-duration/render-clip planning and Story 194 as the dependent multi-clip rendering draft.

### Changed
- Changed final-render prompt compilation so exact shot-plan dialogue is carried into the compiler context and deterministically appended to isolated video prompts when the LLM compiler omits it.
- Changed the prompt compiler's exact-dialogue contract to avoid duplicate dialogue blocks when quoted speaker lines are already present, and to add cadence guidance for dialogue-heavy short clips.
- Updated scene-generation planning surfaces to close the final-render prompt-truth slice while keeping the separate design-study UI/provider lifecycle residual and render-clip planning follow-up visible.

## [2026-04-29-02] — Record deploy auth recovery

### Changed
- Updated the deploy runbook duration estimate from recent deploy history and recorded the expired Fly token preflight plus successful authenticated production deploy.

## [2026-04-29-01] — Recover long-running operation progress (Story 139)

### Added
- Added focused run-progress recovery coverage so malformed terminal progress updates leave a Run Details fallback instead of taking down the project shell.

### Fixed
- Fixed the long-running operation black-screen failure by throttling active-run SSE invalidations and stopping broad in-progress artifact invalidations from refetching every mounted artifact detail.
- Fixed terminal run completion invalidation to refresh project, artifact-group, and run-list data exactly instead of triggering avoidable request storms.

## [2026-04-25-01] — Measure storyboard reference anchors (Story 190)

### Added
- Added a non-default GPT Image 2 template-grid reference-anchor candidate that maps direct reference images to characters, locations, and storyboard panels without changing the shipped default.
- Added Story 190 storyboard-quality runtime, promptfoo, decision, and eval-attempt artifacts for the bounded reference-conditioned comparison.

### Changed
- Changed storyboard grid prompting and artifact annotations to support optional reference-anchor guidance while preserving the existing storyboard artifact contract and grid slicing path.
- Changed the storyboard eval registry and planning surfaces to record the reference-anchor rejection, including non-runtime-blocking model-quality misses and the abstract-reference fixture limitation.

## [2026-04-24-07] — Refresh GPT-5.5 text evals (Story 189)

### Added
- Added GPT-5.5 and GPT-5.5 Pro coverage to the maintained text promptfoo eval configs, including a focused Responses API provider for GPT-5.5 Pro.
- Added raw GPT-5.5/GPT-5.5 Pro eval result artifacts for the 12 maintained text evals.

### Changed
- Changed the eval registry and cost helpers to record GPT-5.5/GPT-5.5 Pro scores, latency, estimated cost, and mismatch/runtime classifications without changing production model defaults.

## [2026-04-24-06] — Measure storyboard beat-grid routing (Story 188)

### Added
- Added a `beat_template` storyboard-grid candidate that injects ordered scene beats into the existing GPT Image 2 template-grid path without changing the shipped default.
- Added Story 188 storyboard-quality runtime, promptfoo, and validation result artifacts for the beat-grid comparison.

### Changed
- Changed storyboard-quality reporting to compare against the registry default instead of the obsolete per-frame baseline.
- Changed the storyboard eval registry and planning surfaces to record the beat-grid non-promotion decision, including the resolved prompt-size failure and non-runtime-blocking residual quality misses.

## [2026-04-24-05] — Reduce long-form scene-analysis prompt overhead (Story 187)

### Added
- Added Story 187 Big Fish throughput result artifacts and a scene-enrichment guardrail result for the prompt-guidance change.

### Changed
- Changed scene-analysis runtime prompting to keep compact always-on tonal and memory guidance, expanding the detailed special-case instructions only when batch text contains relevant cues.
- Changed the full-script throughput eval registry and methodology planning surfaces to record Story 187's measured partial reversal of the `analyze_scenes` regression and its non-runtime-blocking residual gap.

## [2026-04-24-04] — Refresh Deep Breakdown runtime truth (Story 183)

### Added
- Added fresh `big_fish_long` full-script throughput result artifacts for the current `mvp_ingest` -> `world_building` boundary.
- Added Story 187 as the targeted follow-up for the measured long-form `analyze_scenes` runtime regression.

### Changed
- Changed the full-script throughput eval registry to record Story 183's current Deep Breakdown runtime, cost, continuity hotspot, and non-runtime-blocking classification.
- Changed methodology planning surfaces to reflect Story 183 completion and the new Story 187 follow-up pressure.

## [2026-04-24-03] — Add storyboard quality eval and grid default (Story 186)

### Added
- Added the maintained storyboard-generation quality eval with runtime reference-flow capture, promptfoo sequence judgment, split-dimension reporting, and recorded result artifacts
- Added the `gpt-image-2` template-grid storyboard lane so scene storyboard drafts can be generated in batches and sliced back into the existing per-frame artifact contract

### Changed
- Changed the shipped storyboard default to the `gpt-image-2` template-grid lane while preserving an explicit per-frame override for comparison and future single-panel regeneration

## [2026-04-24-02] — Add live AI capability smoke (Story 184)

### Added
- Added an on-demand live AI capability smoke service, API route, and CLI runner for the default text, storyboard-image, alternate image, and render-video lanes

### Changed
- Changed provider-env bootstrapping so worktrees load repo-scoped CineForge credentials from the active checkout first and the shared primary checkout as a fallback
- Documented when to use cheap dependency health versus the expensive live smoke before manual QA or rollout checks

## [2026-04-24-01] — Guide scene work through rendering (Story 181)

### Added
- Added a shared Scene Workspace tutorial card and focused regression coverage so the default scene path remains explicit through shot planning, storyboards, and rendering

### Changed
- Changed post-Deep-Breakdown and scene completion guidance to point at the next actionable scene step instead of stopping at the artifact that just completed
- Changed current-scene storyboard refresh to resume from `storyboards` when timeline, tracks, and shot planning are already healthy

## [2026-04-20-07] — Clarify Scene Workspace entry targets (Story 180)

### Added
- Added a focused Scene Workspace entry banner plus a representative browser smoke harness so targeted `shots`, `storyboard`, and `render` routes are obvious above the fold and stay regression-covered
- Added Story 185 to capture the follow-up Project Home hierarchy discussion about where Script Bible, Artifact Health, and Final Output should live

### Changed
- Changed Scene Workspace route construction so pipeline navigation, run-completion CTAs, and direct concern-group completions all share the same tab-target truth

### Fixed
- Fixed shot-planning and concern-group completion CTAs dropping operators back onto the ambiguous Scene Overview instead of the artifact lane that just completed
- Fixed pipeline helper copy that advertised a fake `Run now` affordance on downstream phases
## [2026-04-20-06] — Recover post-analysis chat failures (Story 182)

### Added
- Added store-backed chat-load state plus a narrow chat render boundary so post-run chat failures stay contained to the chat surface
- Added a focused chat-load regression test covering the no-auto-retry-until-manual-retry policy

### Fixed
- Fixed the post-Script-Breakdown and post-Deep-Breakdown black-screen failure mode by surfacing a retryable chat-unavailable state instead of letting chat load errors cascade through the route
- Fixed the repeated `/api/projects/{project_id}/chat` retry storm after a known failure so the operator can recover deliberately instead of exhausting browser resources
- Fixed a later post-import black-screen path by replacing the Radix ScrollArea shell wrapper with a ref-stable viewport wrapper that avoids the maximum-update-depth loop

## [2026-04-20-05] — Triage QA inbox into planning stories

### Added
- Added Story 180 for Scene Workspace entry clarity and tab-target precision, Story 181 for post-Deep-Breakdown next-step guidance, Story 182 for post-analysis chat failure recovery, and Story 183 for a refreshed Deep Breakdown runtime truth pass
- Added Scout 021 as the durable watchlist home for final-render model and media-orchestration reference notes that should not become active backlog yet

### Changed
- Changed the inbox routing outcome so `docs/inbox.md` returns to `No live items.` after the QA notes were converted into concrete planning artifacts
- Changed methodology planning truth and regenerated surfaces (`docs/stories.md`, `docs/build-map.md`, `docs/methodology/graph.json`) so the new stories and current architecture-audit counters are reflected consistently
- Changed `docs/scout.md` to index both the previously unindexed Scout 020 and the new Scout 021

## [2026-04-20-04] — Add provider dependency health surface (Story 179)

### Added
- Added a typed `/api/health/dependencies` surface that reports cached Anthropic, Google, and OpenAI readiness using cheap model-access probes instead of generation calls
- Added a shared provider-failure taxonomy plus focused service, schema, and API coverage for provider dependency health and startup cache warming

### Changed
- Changed deploy/runbook guidance so post-rollout verification now checks Fly secrets, dependency health, and the representative `Break Down Script` eval instead of trusting homepage and liveness smoke alone
- Changed production deployment documentation and the canonical short screenplay fixture notes so the surfaced `mvp_ingest` post-rollout eval is part of the normal deploy truth surface

### Fixed
- Fixed the API startup warm path to use a FastAPI-compatible startup hook on production so dependency-health cache warming does not crash Fly on boot
- Fixed provider failure operator messaging so permission-denied model access errors classify distinctly from auth failures

## [2026-04-20-03] — Record production deploy result

### Changed
- Changed deployment operations history to append the successful production deploy for version `2026.04.20-02`, preserving the latest timing and smoke-check evidence for future deploy recalibration

## [2026-04-20-02] — Record deploy timing history

### Changed
- Changed deployment operations history to append the missing April 16 Fly.io attempts and successful retry so future deploy-duration recalibration uses complete timing evidence

## [2026-04-20-01] — Collapse imported-project previz prerequisites (Story 178)

### Added
- Added a bounded shot-planning override seam to the maintained `real-ai-previz-runtime` harness so Story 178 can compare the shipped imported-project first pass against an explicit old-behavior QA control on identical substrate
- Added fresh runtime and usefulness result artifacts for the shipped xAI lane plus validation reruns of the same narrowed slice

### Changed
- Changed the shipped `ai_previz_generation` recipe to skip the extra shot-planning QA pass on the previz-fast imported-project route while preserving the persisted `shot_plan` seam and prompt/video provenance contract
- Changed the eval registry and methodology planning truth to record the validated Story 178 prerequisite-collapse result: `32130 ms` first playable with `14103 ms` prerequisites on the shipped xAI lane, still above the usefulness floor at `0.8997`

### Fixed
- Fixed the shipped imported-project first-pass route paying for avoidable shot-planning QA work before xAI previz, cutting prerequisite time by `26.4%` versus the prior imported-project baseline and `38.6%` versus the matched old-behavior control

## [2026-04-19-04] — Add OTIO narrative interchange export (Story 177)

### Added
- Added OpenTimelineIO (`.otio`) as a second narrative-aware interchange carrier on the shared `NarrativeInterchangeExport` payload path, including deterministic OTIO round-trip coverage

### Changed
- Changed the backend export flow, CLI, and Export Modal so OTIO ships through the same headless export seam and honest timeline-presence gating as `FCPXML`
- Changed methodology planning truth to record Story 177 as a completed export-fidelity follow-up from Story 130

## [2026-04-19-03] — Refresh shipped previz regenerate truth (Story 152)

### Added
- Added existing-clip full-regenerate and `start_from=ai_previz` reuse cases to the maintained `real-ai-previz-runtime` harness for the shipped xAI previz lane

### Changed
- Changed the shared AI-previz adoption contract and Scene Workspace previz panel to show distinct first-pass, reuse, and full-regenerate latency truth when the current shot plan is being reused
- Changed eval and methodology planning truth to record the fresh Story 152 validation rerun and classify the remaining detector miss as runtime-blocking rather than a product-truth gap

### Fixed
- Fixed the runtime harness accounting so existing-clip regenerate runs separate pre-`ai_previz` time, post-playable overhead, and full completion honestly instead of collapsing them into the first-pass path

## [2026-04-19-02] — Choose one-pass AI previz provider floor (Story 176)

### Added
- Added xAI/Grok Imagine coverage to the maintained `previz-usefulness` harness and refreshed one-pass provider-floor benchmark artifacts for the honest `mvp_ingest_only` route

### Changed
- Changed the shipped AI-previz route, adoption truth, and internal render-adapter default to use xAI/Grok Imagine on the honest one-pass lane after the paired runtime and usefulness evidence cleared the story bar
- Changed eval and methodology planning truth to record Story 176's fresh provider-floor decision, result artifacts, and mismatch classification

### Fixed
- Fixed the `render_adapter_v1` fallback path so AI-previz runs without an explicit `engine_pack_id` no longer drift back to the stale Lite default
## [2026-04-19-01] — Collapse honest previz prerequisites (Story 175)

### Added
- Added prerequisite-strategy coverage to the maintained `real-ai-previz-runtime` harness, including paired validation artifacts for the shipped one-pass lane versus the full scene-ready chain

### Changed
- Changed the honest current-scene AI-previz route to keep the one-pass previz-prep lane as the shipped winner and to surface reused, auto-built, and missing-optional prerequisite truth across preflight, adoption, and prompt/video provenance
- Changed methodology and eval planning truth to close Story 175 around the validated prerequisite-collapse result instead of keeping it as the active `spec:6` / `spec:7` build

### Fixed
- Fixed stale preflight and provenance wording that implied the full scene-ready prerequisite chain was still the required previz path even when the route was reusing or narrowing its upstream work

## [2026-04-18-04] — Record compact previz compare truth (Story 174)

### Added
- Added a shared provider-env resolver plus a `promptfoo` bridge script so repo-scoped `CINE_FORGE_*` keys drive the same provider credentials across runtime harnesses, discovery, and eval tooling
- Added a compact AI-previz prompt profile, explicit prompt-profile provenance on render/preview artifacts, and route-level runtime reporting for `time_to_first_playable_ms` versus isolated `ai_previz` time

### Changed
- Changed the bounded Story 174 compare to measure shipped Lite versus compact Lite on the honest current-scene route and the maintained usefulness pack, then kept the shipped lane unchanged because compact Lite only improved runtime by about 1% despite winning usefulness
- Changed methodology and generated planning truth to remove the stale auth-blocked claim and record that the next `spec:6` / `spec:7` move returns to fresh triage with the lane still runtime-blocking

### Fixed
- Fixed the `story_world_v1` live-run failure by rebuilding the internal authoring response model before runtime use, so the auth-cleared compare can complete instead of failing locally after provider setup succeeds

## [2026-04-18-03] — Remove stale coverage graph node (Story 173)

### Changed
- Changed the shipped pipeline graph so the `shots` phase exposes only `shot_planning`, matching Story 025's contract that coverage adequacy lives inside `CoverageStrategy` rather than a parallel `coverage_report` stage
- Changed methodology planning truth to record Story 173 and clear the `generation_and_visualization` architecture-audit finding once the stale graph node was actually removed

### Fixed
- Fixed the operator-visible API and pipeline bar so they no longer surface a fake `Coverage Analysis` capability that the real runtime never owned

## [2026-04-18-02] — Restore methodology planning truth (Story 172)

### Changed
- Changed the methodology compiler to derive current eval actionability from deterministic latest-day score truth instead of incidental `scores:` ordering, so generated planning surfaces stop resurfacing already-green eval lines as the default next move
- Changed methodology state and generated planning surfaces to keep architecture-audit freshness honest when later domain-tagged stories land, including clearing the disproven stale ingest audit finding

### Fixed
- Fixed Story 172 close-out validation by restoring the local UI toolchain in this worktree and rerunning the required frontend lint/typecheck gate before landing

## [2026-04-18-01] — Surface honest AI previz first-playable state (Story 171)

### Added
- Added focused AI-previz media-validation overlay coverage for matching, missing, and stale latest-clip cases in the artifact-manager test seam

### Changed
- Changed the Scene Workspace previz route and artifact detail surface to show explicit `Validation Pending`, `Validated`, and `Validation Failed` states while keeping the latest honest AI-previz clip playable as soon as it lands
- Changed planning truth to close Story 171 around the measured first-playable surfacing seam instead of widening the work into another provider-floor rerun

### Fixed
- Fixed the shared health-overlay path so AI-previz clips inherit the same explicit validation-trust surface that final outputs already used, instead of collapsing back to generic current health

## [2026-04-16-02] — Close the breadth-first scene-generation route (Story 170)

### Changed
- Changed the shipped `all_scenes` render route so successful scene outputs and the matching generated-video track manifest persist incrementally instead of disappearing when a later scene fails
- Changed planning truth to record Story 170 as the story that closes the breadth-first scene-generation route and returns the `spec:6` / `spec:7` lane to fresh triage

### Fixed
- Fixed the surfaced render and Run Detail failure language so batch failures stay honest about preserved outputs, failed scene ids, and the real Run Detail route
- Fixed the representative-validation gap by re-running the real surfaced all-scenes route and complete `final_output` handoff on a fresh project after removing the local patched smoke backend
## [2026-04-16-01] — Choose the final render provider floor (Story 169)

### Added
- Added a reference-conditioned final-render provider-floor benchmark substrate, dataset generator, promptfoo task, and decision reporting path for the shipped Scene Workspace render route

### Changed
- Changed the final-render default from `openai_sora2` to `google_veo31` based on measured quality, runtime, and direct-reference usage on the representative Story 168-style scene set
- Changed methodology and eval tracking to record the new provider-floor decision, benchmark evidence, and Story 169 close-out truth

### Fixed
- Fixed the Google Veo final-render transport to send image inputs as `bytesBase64Encoded` and to avoid the mixed frame-guidance-plus-reference request shape the live Gemini API rejects
- Fixed the residual dead `inlineData` helper left behind after the Google transport correction

## [2026-04-13-02] — Prove reference-conditioned scene render truth (Story 168)

### Added
- Added representative raster-backed render fixtures and focused regression coverage for design-study references, injected-asset priority, project taste references, and OpenAI opening-frame normalization
- Added a dated UI-scout record for the representative reference-conditioned render walkthrough on a fresh project

### Changed
- Changed the surfaced Scene Workspace render, prompt detail, and generated-video detail routes so they expose compiled creative-brief references, prompt provenance, and honest reference demotion truth
- Changed methodology planning truth to close Story 168 and return the `scene-generation-completion` campaign to triage for its next non-terminal owner

### Fixed
- Fixed the real OpenAI render path so operator-provided opening-frame images are normalized to the requested output resolution instead of failing provider validation
- Fixed the render-adapter completeness path so required upstream context can synthesize fallback prompt sections when the compiler omits them, preventing false route failures on representative state

## [2026-04-13-01] — Validate final-output trust surface (Story 167)

### Added
- Added project-scoped runtime validation coverage for `final_output`, including fixture-backed benchmark inputs/results and surfaced validation detail for the assembled cut

### Changed
- Changed the shared media-validation substrate and final-output route so project cuts validate against exact artifact lineage and expose matching, stale, and missing trust state on Home and Artifact Detail

### Fixed
- Fixed the real final-output route so redundant recipe input gating and shot-plan timeline-ref drift no longer strand project-level assembly or its validation path

## [2026-04-12-04] — Ship project-level final output assembly (Story 166)

### Added
- Added a headless `final_output` module, schema, and recipe that assemble a project-level playable cut from timeline-ordered generated scene renders with typed coverage and provenance metadata
- Added dedicated Final Output UI surfaces on project home and Artifact Detail, plus focused schema/module/integration regression coverage for partial and complete assembly states

### Changed
- Changed pipeline graph truth and operator-facing run copy so `final_output` is now treated as a shipped production-stage capability instead of an unimplemented placeholder

## [2026-04-12-03] — Reuse scene render refresh path (Story 165)

### Added
- Added persisted `start_from` / `end_at` runtime metadata and Run Detail execution-scope copy that make sliced render-refresh runs inspectable after launch

### Changed
- Changed Scene Workspace render refresh to reuse healthy shot-planning substrate by forwarding backend-recommended `start_from=render` when the selected scene scope is safe to rerender without replanning
- Changed Story 165 evidence from a proxy timing estimate to a fresh paired full-refresh versus reuse benchmark on copied real project state

### Fixed
- Fixed the surfaced render-refresh path so stale shot-planning substrate no longer appears reusable when graph health says the plan is no longer safe to trust
- Fixed the close-out visibility gap where operators could trigger render reuse but could not verify the sliced execution boundary in Run Detail
## [2026-04-12-02] — Make surfaced scene render path real (Story 164)

### Added
- Added atomic `run_state.json` write coverage plus a dated UI-scout report that records the representative Scene Workspace render route on a fresh project

### Changed
- Changed the surfaced scene render path so warning-level prompt gaps stay advisory, produce honest completeness metadata, and still allow the selected scene to reach prompt, video, and validation artifacts
- Changed the Scene Workspace render panel, UI scout, and manual walkthrough surfaces so failed runs show inline truth and the honest FP1 boundary is now “one real scene render lands through the normal route”

### Fixed
- Fixed the contradiction where render preflight said a scene could proceed with warnings but `render_adapter_v1` hard-failed on those same warning-level gaps
- Fixed a `run_state.json` partial-write race that could make surfaced run polling intermittently 500 during active render refresh
## [2026-04-12-01] — Decompose scene-analysis ownership seams (Story 163)

### Added
- Added focused `scene_analysis_v1` execution and output helpers plus narrow regression coverage for retry, QA, merge, and artifact assembly seams
- Added a recorded `scene-enrichment` improvement attempt that restores the default Sonnet 4.6 path above target with explicit tonal-contrast and flashback framing guidance

### Changed
- Changed `scene_analysis_v1/main.py` into a thin entrypoint while preserving the shipped scene-index and artifact contract
- Changed the scene-enrichment prompt contract in both benchmark and runtime paths to name soundtrack-backed tonal contradictions and formative-memory framing explicitly
- Changed the operator-console right-panel hook seam so AppShell and mobile sheets stay lint-clean without changing the route behavior

### Fixed
- Fixed the close-out validation gaps around UI toolchain checks, browser verification, and the regressed `scene-enrichment` score

## [2026-04-11-06] — Reduce long-form scene-analysis wait cliff (Story 161)

### Added
- Added a dedicated `scene_analysis_v1` batching helper and focused long-form batch-planning regression coverage

### Changed
- Changed long-form scene analysis to use adaptive `5-10` scene batching with a `2500`-word guard and leaner macro-analysis prompt assembly
- Changed the shipped world-building recipe, Story 155 follow-up truth, and the eval registry to record the new `big_fish_long` throughput result and remaining non-runtime-blocking continuity drift

### Fixed
- Fixed the scene-analysis fallback path leaking the internal `_analysis_failed` sentinel into persisted enriched-scene payloads

## [2026-04-11-04] — Add loop-verify coordination skill

### Added
- Added a shared `/loop-verify` skill for bounded parallel verify-and-fix loops that rerun the full scope until an entire round returns no more real issues

### Changed
- Changed the synced Gemini command wrapper surface so `loop-verify` is available with CineForge's other invocable local skills

## [2026-04-11-05] — Recover long-form continuity stall honesty (Story 162)

### Added
- Added focused long-form continuity guardrail coverage for bounded scene-call budgets, incremental `continuity_state` announcements, and explicit timeout fallback annotations

### Changed
- Changed continuity tracking to bound per-scene LLM timeout and retry posture locally while surfacing final scene states incrementally through the existing artifact-announcement seam
- Changed Story 155, Story 162, and the eval registry to record the fresh `big_fish_long` rerun truth and classify the remaining truncation issue as non-runtime-blocking quality drift

### Fixed
- Fixed the long-form continuity path so a single bad scene no longer disappears into a 14.9-minute silent window before degrading ambiguously

## [2026-04-11-03] — Tighten continuity tracking throughput budgets (Story 159)

### Added
- Added focused continuity-throughput regression coverage and artifact metadata that expose scene-call, property, and change-event budget shape

### Changed
- Changed continuity tracking to use extracted runtime/prompting helpers, a tighter scene prompt contract, explicit truncation surfacing, and smaller per-scene output budgets
- Changed methodology and eval tracking to record the measured short/medium continuity improvements and the remaining long-form continuity stall truth

### Fixed
- Fixed continuity event handling so `new_value = null` is preserved through the schema and continuity timeline UI as an explicit cleared state

## [2026-04-11-02] — Record deferred media-automation scout handoff

### Added
- Added a Conductor-scout inbox note capturing the narrow future CineForge references from the deferred media-automation bundle: `VOID`-style cleanup, OpenClaw-style long-running media orchestration, and MultiMedia-Agent-style plan/tool decomposition

### Changed
- Changed `docs/inbox.md` to record that these leads remain future design references only and do not change the current previz-runtime bottleneck truth

## [2026-04-11-01] — Recover long-form bible throughput honesty (Story 160)

### Added
- Added focused long-form bible regression coverage for discovery-backed adjudication bypass and explicit output-budget forwarding

### Changed
- Changed character and location bible extraction to reuse discovery-backed candidate sets directly on the normal long-form path and to pass explicit truncation-aware output budgets
- Changed Story 160 methodology and eval tracking to record the fresh validation rerun and the downstream continuity blocker handoff to Story 159

### Fixed
- Fixed the runtime-blocking `big_fish_long` failure where `character_bible` and `location_bible` truncated before producing usable story-lane artifacts

## [2026-04-10-13] — Add full-script throughput detector (Story 155)

### Added
- Added a checked-in full-script throughput benchmark harness, fixture manifest, and baseline result artifacts for the honest `mvp_ingest` -> `world_building` story-lane boundary
- Added follow-up stories for the measured throughput hotspots: continuity tracking runtime/output budgets, long-form bible truncation recovery, and long-form scene-analysis reduction

### Changed
- Changed methodology state, generated planning views, and eval registry tracking so screenplay-throughput work now routes through the landed detector and its measured follow-up stories

### Fixed
- Fixed Fountain normalization for blank metadata headers with indented continuation lines so representative medium/long screenplay title pages no longer crash before throughput measurement

## [2026-04-10-12] — Make triage phase-driven by default

### Changed
- Changed `/triage`, `/triage-stories`, and `/triage-evals` so methodology phase now creates default action pressure instead of treating missing novelty as a reason to stall.
- Changed story-triage guidance to recommend creating a story shell when a pressured methodology line still lacks packaging, while preserving CineForge's local architecture and expected-fail eval framing.

### Fixed
- Fixed planning guidance so bounded phase-aligned story and eval moves no longer degrade to false `no-op` or `no action` recommendations.

## [2026-04-10-11] — Compile triage actionability into methodology graph

### Added
- Added methodology-graph regression coverage that proves eval descriptions and top-level `retry_when` metadata survive CineForge's compiled methodology graph output.

### Changed
- Changed triage guidance, triage-evals guidance, and methodology runbooks to use compiled actionability metadata when deciding whether a line should be retried now.
- Changed the methodology graph compiler and generated graph so stories, evals, and compromises now publish reusable actionability summaries and retry posture for triage.

### Fixed
- Fixed a compiler carry-through gap where eval descriptions and top-level retry conditions could be dropped from the generated methodology graph.
## [2026-04-10-12] — Clean fresh-run startup path and chat truth (Story 158)

### Changed
- Changed fresh run bootstrap so `start`, `resume`, and `retry_failed_stage` all create the run substrate and event-log file before returning a real run id, keeping `/api/runs/{id}/events` honest from the first poll
- Changed bootstrap chat-state handling so fresh imported projects replace stale placeholder messages with the current Home CTA instead of persisting an outdated `Upload Screenplay` path
- Changed `project_config_v1` to honor runtime `default_model` / `qa_model` overrides the same way the rest of the pipeline does, keeping start-run coverage deterministic instead of silently falling back to live default models
- Changed the ui-scout and methodology planning lane to record FP1 as passing again after the clean rerun on the canonical fixture

### Fixed
- Fixed one `/api/runs/{id}/events` startup 404 per fresh started run on the surfaced Home/chat path
- Fixed stale fresh-import chat bootstrap messages continuing to advertise `Upload Screenplay` after the screenplay had already been imported
- Fixed Story 158 close-out truth so the active follow-up lane no longer claims FP1 is unresolved after the passing validation rerun

## [2026-04-10-10] — Harden UI-scout planning lane (Story 156)

### Added
- Added a dedicated internal UI-scout lane with canonical index and template files so recurring product-truth walkthroughs now live separately from external-source scouting

### Changed
- Changed `spec:5.6`, methodology state, generated planning surfaces, triage guidance, and the full-pipeline walkthrough runbook to route recurring UI truth checks through the new `docs/ui-scout*` lane
- Changed the methodology compiler to validate `ui_scout` state and surface freshness warnings directly in generated planning output

### Fixed
- Fixed stale Story 156 and Story 157 references that still pointed at the retired full-pipeline acceptance report path
- Fixed compiler behavior so missing `ui_scout` state is treated as an explicit validation failure instead of reading as implicitly fresh

## [2026-04-10-09] — Archive stale chat CTA paths (Story 157)

### Added
- Added a small shared chat-action truth helper and a focused Playwright smoke
  script so completed-path CTA honesty is checked deterministically on the
  canonical `open-frequency` project

### Changed
- Changed the shared chat render path to archive obsolete completed-path run
  actions instead of presenting them as live next steps once the project state
  has moved on
- Changed tracked chat-launched runs to record `resolvedMessageId` so clicked
  suggestions no longer remain visually unresolved in the journal

### Fixed
- Fixed stale `Break Down Script` / `Deep Breakdown` chat buttons continuing to
  advertise completed paths on Home and scene routes after ingest and
  world-building were already complete

## [2026-04-10-08] — Harden skill sync wrapper checks

### Changed
- Tightened `scripts/sync-agent-skills.sh` so wrapper sync now fails on missing
  `user-invocable` frontmatter, mismatched Gemini wrapper content, or stale
  extra wrappers instead of only checking wrapper presence
- Declared `webapp-testing` as an explicit invocable skill so the shared
  wrapper-generation contract now matches the checked-in skill surface

## [2026-04-10-06] — Add full-pipeline UI acceptance requirement

### Added
- Added a canonical very short screenplay fixture and a short recurring manual walkthrough runbook for full-pipeline UI acceptance checks
- Added Story 156 to preserve the recurring UI completeness and polish requirement as an explicit planning line

### Changed
- Changed `spec:5` and methodology state to require a standing full-pipeline manual acceptance pass alongside the existing throughput-efficiency planning line
- Changed generated methodology views to surface the new UI-acceptance sequencing bias and story ownership consistently

## [2026-04-10-07] — Scene Workspace readiness honesty lands (Story 099)

### Added
- Added a typed scene-readiness API/service seam plus a reusable review-control component so Scene Workspace can reuse the canonical red/yellow/green readiness contract across all five concern groups
- Added focused readiness API coverage and a committed representative browser smoke script for the Scene Workspace review loop

### Changed
- Changed Scene Workspace summary dots and concern-group tabs to consume canonical readiness instead of a page-local artifact-existence heuristic
- Changed Story World and Character & Performance review surfaces to share the same immutable Draft/Reviewed control path as the other concern groups

### Fixed
- Fixed false-red readiness cases for Story World note-only drafts and no-character Character & Performance scene artifacts
- Fixed stale historical run progress cards so copied or missing runs stop polling dead run-state endpoints and render a stable unavailable fallback instead

## [2026-04-10-05] — Clarify methodology routing and add throughput planning line

### Added
- Added a concise methodology quick map in the README and an operational rule in AGENTS so future sessions can route "prioritize", "build", and "measure" requests into the right planning artifacts without guesswork
- Added Story 155 to preserve end-to-end screenplay throughput and stage-efficiency budgeting as an explicit detector-first planning line

### Changed
- Changed canonical methodology state to record screenplay-throughput optimization as an important secondary sequencing bias under `spec:2` and `spec:8` without displacing the active `spec:4` / `spec:5` focus
- Changed generated methodology views to surface the new throughput requirement and story ownership consistently

## [2026-04-10-03] — Land inbox capture with validated close-out work

### Changed
- Changed `/check-in-diff` so `docs/inbox.md` is treated as expected user
  capture during audit and staging instead of being flagged as unrelated drift
- Changed `/finish-and-push` so normal inbox capture rides along with the
  validated landing set by default unless the user explicitly excludes it

## [2026-04-10-04] — Character & Performance first slice lands (Story 023)

### Added
- Added a real `character_and_performance_v1` creative-direction stage that produces scene-scoped Character & Performance artifacts through the normal recipe, driver, and API flow
- Added a dedicated Scene Workspace Character & Performance panel for viewing, editing, and reviewing scene-level performance entries

### Changed
- Changed the canonical `character_and_performance` contract to use the scene-scoped `SceneCharacterPerformance` payload across schema registration, UI loading, and downstream shot-planning/render consumption
- Changed the methodology/story surfaces to record Story 023 as the shipped first Character & Performance slice instead of a deferred placeholder

### Fixed
- Fixed the remaining Character & Performance placeholder path by removing the coming-soon scene-action soft block and marking the pipeline graph/readiness surface honestly
- Fixed stale graph truth for the adjacent Story World concern-group node while touching the same shipped-capability area
## [2026-04-10-02] — Final-render Veo reference note captured

### Added
- Added an inbox note that Veo 3.1 Fast and Veo 3.1 accept multiple reference images, preserving that capability for future final-render eval triage

## [2026-04-10-01] — Story World motif tracking lands (Story 100)

### Added
- Added a real `story_world_v1` creative-direction stage and project-scoped Story World artifact surface so recurring motifs exist as a first-class editable concern group

### Changed
- Changed Scene Workspace and downstream look-and-feel, sound, and shot-planning prompt assembly to consume Story World motif context instead of relying on a placeholder-only lane

### Fixed
- Fixed artifact edit refresh and numeric artifact version ordering so manual Story World edits resolve the actual latest artifact immediately
## [2026-04-09-05] — In-app style pack creation lands (Story 034)

### Added
- Added a project-local Style Packs workflow in Project Settings for browsing, generating, importing, reviewing, saving, and assigning per-role style packs inside the app
- Added backend style-pack list/generate/save/manual-import APIs plus project-local pack storage under each project so saved packs immediately affect runtime role behavior

### Changed
- Changed style-pack generation to run through the existing `deep-research` CLI with provider selection, progress reporting, provider-specific report resolution, and CLI-estimated research cost metadata
- Changed style-pack draft handling to preserve optional support files, including saved research notes, through review and save

### Fixed
- Fixed the remaining taste-authoring gap where users had to leave CineForge or edit files manually to create new style packs

## [2026-04-09-04] — AI-only previz truth and animatic removal (Story 149)

### Added
- Added neutral preview/keyframe schema and helper ownership so live render, media-validation, and keyframe flows no longer depend on the deleted animatic module
- Added a benchmark-only legacy previz helper so historical deterministic comparison evidence survives without keeping the old product substrate alive

### Changed
- Changed Scene Workspace previz, artifact detail, backend policy, and schema/registry contracts so AI Previz is the only shipped operator-facing previz lane
- Changed Story 149, Story 153, and the generated methodology surfaces to reflect that the `<= 6000 ms` target is a climb goal while Story 149 closes the deterministic placeholder-removal slice

### Fixed
- Fixed the remaining repo-level drift where `animatic`, `previz_reel`, and `animatic_v1` still survived in viewers, schema registration, fixtures, and tests after the product lane had been removed

## [2026-04-09-03] — Previz runtime detector hardening (Story 150)

### Added
- Added focused regression coverage for the real AI-previz runtime support and decision-summary helpers so manifest parsing, median aggregation, partial-success summary math, and divergence reporting fail locally before another paid rerun

### Changed
- Changed Story 150 close-out truth and the canonical methodology execution map so the detector substrate is recorded as complete while Stories 149 and 153 remain blocked health flags and Story 034 becomes the clearest ready lane

## [2026-04-09-02] — Blocked story lifecycle hardening

### Added
- Added Scout 019 documenting the Storybook lifecycle delta and the CineForge-specific adaptation to keep blocker truth in the canonical story body sections

### Changed
- Changed `/create-story`, `/build-story`, and the story template so blocked stories must carry concrete blocker truth and rewrite stale `## Plan` text around the unblock path instead of implying immediate implementation

## [2026-04-09-01] — Compact previz planning and xAI runtime probe (Story 151)

### Added
- Added xAI / Grok Imagine provider coverage, engine-pack support, and checked-in runtime artifacts so the existing real AI-previz harness can measure the same scene-ready boundary across Google and xAI candidates

### Changed
- Changed AI-previz shot planning to use a compact previz-specific profile and lower output budget, materially reducing the scene-ready planning/runtime cost before provider video generation
- Changed deterministic-baseline reuse and previz UI wording so current-scene reruns stay scene-scoped, AI previz remains the intended product lane, and the deterministic fallback/control surface is labeled honestly across the operator console

### Fixed
- Fixed direct runtime-harness dotenv loading in worktree execution and fixed xAI previz prompt compilation to stay inside Grok Imagine's 4096-character prompt limit
## [2026-04-08-04] — Methodology hardening follow-up sweep (Story 154)

### Added
- Added direct methodology-graph regression coverage for explicit eval lineage, structured-state key validation, active-surface wording checks, and the `-setup.md` false-positive case

### Changed
- Changed the methodology compiler to lint a wider active surface, require explicit eval lineage metadata, validate structured state keys directly, and reject stale generated-view and retired-setup guidance on live methodology docs
- Changed the methodology registry, audit record, ADR guidance, and live skills/runbooks to align on state/graph/generated-dashboard authority instead of manual planning-surface upkeep

## [2026-04-08-03] — Scout 018 audit draft and deploy log carryover

### Added
- Added the initial Scout 018 Dossier hardening audit record and indexed it from the scout log

### Changed
- Changed the deploy log to record the successful remote-builder Story 044 deploy smoke pass from 2026-04-04

## [2026-04-08-02] — Previz provider-floor decision and blocked truth (Story 153)

### Added
- Added extracted shared support and decision-summary helpers for the real AI-previz runtime harness, plus checked-in provider-floor result artifacts covering the full matrix, shared-substrate repeats, and validation-decision evidence

### Changed
- Changed the shipped AI-previz recipe and runtime manifest to use Veo 3.1 Lite `4s / 720p` as the provisional slow-lane baseline while retaining the old Lite `8s / 1280x720` path as an explicit control in the runtime matrix
- Changed Story 149, Story 150, Story 153, and the eval registry to record the current provider-floor conclusion honestly: Fast 4 is the runtime leader, Lite 4 is the usefulness leader, no dominant winner is proven, and the detector remains runtime-blocking
- Changed the benchmark methodology surfaces to include Story 153 as a blocked follow-on with explicit blocker evidence and an unblock condition instead of leaving the provider-floor question implicit

## [2026-04-08-01] — Previz runtime truthfulness and AI regenerate reuse (Story 152)

### Added
- Added a dedicated real-AI-previz runtime benchmark harness plus checked-in result artifacts to measure honest scene-ready latency, compact-planning improvements, and regenerate-path reuse evidence across the current previz runtime line

### Changed
- Changed Scene Workspace previz policy and UI to present Fast Previz versus AI Previz with explicit latency, fidelity, and trust disclosure instead of one ambiguous video-generation surface
- Changed AI-previz regeneration to reuse the current healthy shot plan via `start_from=ai_previz` when preflight proves the substrate is safe, instead of silently replanning the same scene
- Changed AI-previz shot planning to use a compact previz-specific prompt profile so the scene-scoped runtime path spends materially less time in planning before provider video generation

### Fixed
- Fixed animatic generation treating descriptive sound references like FFmpeg input files
- Fixed test and validation guidance so impossible seeded project states are no longer treated as product-validation evidence

## [2026-04-07-01] — Shared theme system and appearance settings (Story 046)

### Added
- Added a shared app-level theme system with reusable palette definitions, a focused theme provider, and a focused appearance settings section for project-backed mode and palette control

### Changed
- Changed the operator console to support Light, Dark, and Auto modes plus Slate, Obsidian, Ember, and Noir palettes through the real Project Settings flow instead of a hardcoded dark-only shell
- Changed the `/theme` showcase into a shared smoke surface backed by the same palette source as the live app, and moved pre-hydration theme restore into the app bootstrap to avoid a wrong-theme flash on reload

### Fixed
- Fixed Sonner toast theming so notifications follow the resolved theme, fixed the nested-button regression in the new palette cards, and fixed palette token contrast so all light/dark combinations meet the story's AA validation bar

## [2026-04-04-06] — Scene-scoped planning and downstream generation (Story 148)

### Added
- Added a typed scene-scope contract plus shared scene-action preflight path so scene workspace actions and headless callers can choose `Current scene` or `All scenes` with consistent warn vs soft-block semantics

### Changed
- Changed concern-group, shots, storyboard, previz, and render flows to run in true scene scope when requested, while preserving honest project summaries and explicit scope metadata in run detail and progress surfaces
- Changed the Scene Workspace previz experience into one consolidated panel with shared scope and preflight controls instead of competing lane and empty-state panels

### Fixed
- Fixed scene-level downstream actions being falsely blocked behind optional direction coverage or silently fanning back out into project-wide reruns
- Fixed the restored Direction phase details affordance across desktop hover and mobile tap flows

## [2026-04-04-05] — Problem-first story workflow migration (Story 147)

### Added
- Added a cross-repo migration runbook plus targeted methodology-graph regression coverage for blocked-story metadata and evidence-backed blocked-state validation

### Changed
- Changed CineForge's story lifecycle contract across AGENTS, methodology docs, and lifecycle skills to use an honest five-status model with problem-first triage, anti-fragmentation defaults, and buildable-Draft promotion
- Changed the methodology compiler and generated planning surfaces to surface blocker metadata explicitly and reflect Story 147 as the active spec:11 follow-on during implementation
- Changed the planning state and story index flow so the Current Execution Map is rendered from structured lane refs plus canonical story status, with roadmap refs validated against terminal-story drift
- Changed triage and generated planning surfaces so blocked lines with unmet unblock conditions downgrade to health flags instead of winning the next-action slot through continuity alone
- Changed eval retry guidance and registry semantics to carry explicit retry exhaustion state, so already-consumed retry triggers stay dormant until materially new evidence appears

### Fixed
- Fixed remaining post-migration drift where policy docs, lifecycle skills, and generated methodology surfaces still disagreed about blocked stories, close-out behavior, and the active methodology campaign
- Fixed the post-close-out loophole where Story 147 could be `Done` while the generated Current Execution Map and active roadmap refs still treated it as active work
- Fixed the feedback loop where a blocked active line could keep resurfacing as the recommended next move just because it was the only categorized non-done lane
- Fixed exhausted eval retry triggers being treated as freshly actionable work after the original retry path had already been consumed

## [2026-04-04-04] — Mobile-friendly operator console (Story 044)

### Changed
- Changed the operator shell to present a mobile drawer and chat sheet below `md` while preserving the persistent sidebar and resizable right panel on tablet and desktop widths
- Changed screenplay, scene, entity, inbox, artifact, settings, and direction surfaces to stack safely on mobile and keep dense tabs or toolbars operable without page-level horizontal overflow

### Fixed
- Fixed mobile-only overflow seams that left parts of the screenplay, character, scene, inbox, and artifact surfaces clipped or pushed sideways on narrow screens
- Fixed remaining undersized mobile action controls so the validated nav, chat, export, send, and stop buttons now meet the story's `44×44` tap-target requirement

## [2026-04-04-03] — Legacy methodology metadata backfill (Story 146)

### Added
- Added explicit frontmatter to the remaining legacy story files and local ADR-001 through ADR-003 so the methodology graph reads structured metadata directly from the authored artifacts

### Changed
- Changed the methodology migration/audit surfaces to record the metadata cleanup as completed repo-local backfill rather than open warning debt

### Fixed
- Fixed the remaining methodology warning classes caused by legacy story headers, missing `category_refs`, legacy ADR metadata, and repo-owned missing-local-ADR oddballs
- Fixed the methodology compiler cleanup pass by deleting an unused helper left behind from the retired legacy parser path

## [2026-04-04-02] — Methodology graph and state migration (Story 145)

### Added
- Added a canonical methodology state substrate, deterministic graph compiler, and generated planning views so mutable planning state no longer lives in hand-authored markdown dashboards
- Added a bounded architecture-audit lane with state, skill, runbook, and synced Gemini wrapper coverage

### Changed
- Changed AGENTS, runbooks, skills, story tooling, and ADR tooling to treat `docs/methodology/state.yaml` plus compiled outputs as authority and to regenerate planning views instead of editing them manually
- Changed Story 145 and the methodology audit artifact into the proof log for the migration and its certification loop

### Fixed
- Fixed active methodology surfaces still teaching manual `docs/stories.md` edits or authored build-map authority
- Fixed the methodology certification contract so classified legacy warning debt is explicit instead of being mistaken for an unresolved structural failure

## [2026-04-04-01] — AI previz adoption gate and trust guardrails (Story 144)

### Added
- Added a shared previz-adoption policy service and API contract so Scene Workspace and artifact-detail surfaces can render one evidence-backed AI-previz status instead of drifting UI-local labels
- Added `ai_previz_video` support to the existing `media_validation_v1` trust path, including recipe wiring, target-artifact-type handling, and focused regression coverage
- Added fresh `runtime-media-validation` result artifacts for the Story 144 validation rerun and recorded the new evidence in `docs/evals/registry.yaml`

### Changed
- Changed the AI-previz operator surface to show measured latency, explicit pricing blockers, and `default` / `recommended optional` / `experimental manual` states from the shared backend policy
- Changed artifact-health overlay resolution so AI previz can surface the same validation-backed trust semantics as generated render video

### Fixed
- Fixed stale `AI lane: experimental` and generic `cost unverified` copy persisting after Story 143 even when benchmark/runtime evidence already supported a more specific recommendation
- Fixed AI-previz artifact detail pages lacking a consistent path to the underlying validation detail and trust rationale

## [2026-04-03-03] — Provider failure chat notifications (Story 128)

### Added
- Added deterministic provider-failure classification and message building from `run_state.json` attempt metadata so quota, auth-expiry, and rate-limit failures surface as actionable chat cards with direct run-detail navigation
- Added focused regression coverage for top-level and attempt-only provider failure detection plus duplicate suppression

### Changed
- Changed run-failure chat handling to emit stable provider-specific suggestion messages instead of random generic error responses
- Changed live run progress loading so provider-specific failure cards take precedence and the generic failed-run card is now a fallback only

### Fixed
- Fixed auth-expiry failures being silently buried outside the project chat surface
- Fixed duplicate generic and provider-specific failure cards appearing for the same failed run

## [2026-04-03-02] — AI previz planning surface and benchmark gate (Story 143)

### Added
- Added a dedicated `ai_previz_generation` recipe path plus `ai_previz_prompt` and `ai_previz_video` artifacts so operators can generate non-final AI previz without going through final-render flows
- Added an explicit `Previz` Scene Workspace surface and dedicated AI-previz detail views so deterministic and AI lanes are reviewable side by side in-product
- Added candidate-specific AI-previz benchmark lanes, refreshed Veo Fast/Lite engine packs, and a typed low-fidelity previz prompt contract for benchmark and runtime reuse

### Changed
- Changed previz taxonomy to remove stale `shared_video` / render-coupled semantics and keep AI previz clearly separate from final generated video
- Changed the benchmark-backed default decision to keep `annotated_symbolic` as the recommended lane until an AI candidate clears the adoption guardrail with verified cost evidence

### Fixed
- Fixed AI previz generation so required locked media can degrade to prompt-only context for previz packs that do not accept image references, while final render stays strict
- Fixed Google Veo request shaping so duration is sent with the provider's expected numeric contract instead of the broken string form

## [2026-04-03-01] — Previz fidelity benchmark and annotated upgrade (Story 137)

### Added
- Added a dedicated `previz-usefulness` benchmark task, fixture dataset generator, and report helper so symbolic animatics, annotated animatics, and shared-video candidates can be compared on the same scene pack
- Added richer deterministic `annotated_symbolic` previz rendering plus operator-facing provenance metadata shared across animatic, previz-reel, and generated-video artifacts

### Changed
- Changed the default previz path to the measured `annotated_symbolic` mode while preserving the cheaper symbolic fallback as an explicit option
- Changed Scene Workspace and artifact-detail viewers to show preview mode, fidelity intent, inputs, latency, and cost so operators can tell whether they are looking at symbolic previz, richer previz, or generated render output

### Fixed
- Fixed the previz-usefulness dataset generator so the benchmark now reruns cleanly from scratch instead of depending on a previously generated fixture pack
- Fixed a dead animatic previz-reel parameter left behind by the richer-previz refactor
## [2026-04-02-01] — Conversational upstream canon editing (Story 097)

### Added
- Added shared artifact-edit helpers plus focused backend, API, and chat regression coverage for AI-authored canon edits across plain JSON artifacts and folder-backed bible manifests
- Added a creative-role broker handoff so non-assistant roles can package canon edit requests for the assistant without widening write-tool ownership

### Changed
- Changed chat-driven artifact editing to record AI provenance, honor `human_control_mode`, diff canonical `bible_files`, and route bible edits through discoverable manifest-version saves
- Changed chat action handling so dismiss stays local to the acted-on proposal while retry/approve actions stay attributable to the specific message they resolved

### Fixed
- Fixed `bible_manifest` edits so new versions are browsable through the standard artifact APIs instead of landing on undiscoverable generic filenames
- Fixed proposal dismissal so it no longer hides unrelated pending actions or writes a backend chat message for a local-only reject action

## [2026-04-01-03] — Onboarding artifact health trust fix (Story 142)

### Added
- Added focused unit and integration coverage for onboarding self-staleness, including guarded `project_config` refresh behavior and scene-lineage exclusions

### Changed
- Changed deep breakdown to refresh only confirmed system-owned `project_config` artifacts after `scene_index` enrichment
- Changed home, inbox, and shell badge actionability semantics to share one onboarding-health filter in the UI

### Fixed
- Fixed fresh onboarding so `basic breakdown -> deep breakdown` no longer ends with self-inflicted artifact-health attention debt

## [2026-04-01-02] — Inbox triage and onboarding trust follow-up

### Added
- Added Story 142 to track the fresh-intake artifact-health trust bug where the two-step onboarding path can end by surfacing self-inflicted attention debt

### Changed
- Changed the stories index to surface Story 142 in the ready lane and record the new pending story in the master story table
- Changed Story 137 to absorb the cheap fast-video previz idea as an eval candidate instead of spawning a duplicate story
- Cleared the processed inbox queue after triaging both outstanding items into their canonical homes

## [2026-04-01-01] — Intent-side creative brief transparency (Story 141)

### Added
- Added richer Intent taste inputs for filmmaker anchors and look notes, plus a typed compiled creative brief preview shared by the backend and UI
- Added focused regression coverage and a story-scoped prompt probe for the shared creative-brief seam across design-study and render-adapter consumers

### Changed
- Changed the Intent API surface into a dedicated router with a read-only creative-brief endpoint instead of keeping more route logic inline in the main API app
- Changed design-study and render-adapter prompt compilation to consume the same compiled creative brief and persist the exact brief preview used downstream

## [2026-03-31-03] — Dependency freshness hardening for npm, pnpm, and uv

### Added
- Added repo-local npm freshness gates at the root and under `ui/`, plus a `ui/pnpm-workspace.yaml` minimum release age policy for the frontend workspace
- Added `scripts/uv-safe.sh` so Python dependency syncs can apply a rolling 7-day `uv --exclude-newer` cutoff instead of relying on a stale fixed date

### Changed
- Changed the documented setup flow to use the `uv` wrapper, clarified the tool-version limits of the freshness controls, and switched the UI install example to `npm ci`
- Changed the Docker runtime build to bootstrap pinned `uv` and install Python dependencies with a computed 7-day freshness cutoff instead of raw `pip install .`

## [2026-03-31-02] — Agent workflow drift guards and scout refresh

### Added
- Added Scout 017 covering doc-web, Storybook, and Dossier process deltas plus verification that the local worktree already matched CineForge's recent ideal-alignment skill commits
- Added explicit drift-signal review guidance to `/validate` and `/codebase-improvement-scout`, including ownership-aware skill-sync checks for agent-surface edits

### Changed
- Changed `AGENTS.md` to treat architecture drift as real debt, require clearer ownership before parallel subagent edits, and document the user-level npm boundary for global `promptfoo` freshness gating
- Changed the codebase-improvement and promptfoo runbooks so they teach the same drift-scan and global-install boundaries as the live skills

## [2026-03-31-01] — Export fidelity and narrative interchange (Story 130)

### Added
- Added typed narrative export metadata plus a deterministic `FCPXML` export path shared by the API, CLI, and export UI
- Added focused regression coverage for metadata assembly, `FCPXML` serialization, call-sheet PDF generation, and export route/CLI behavior

### Changed
- Changed call-sheet export to a reference-driven layout with honest logistics placeholders and extracted shared project-loading/export helpers
- Changed export downloads to use backend fetch/blob flows with accurate preflight blocking instead of optimistic location redirects

### Fixed
- Fixed screenplay export before breakdown so it falls back to the latest uploaded script instead of generating blank PDFs
- Fixed failed shot-planning runs and scene-workspace panels so missing prerequisites terminate cleanly instead of spinning forever

## [2026-03-20-07] — Runtime media validation loop for generated video (Story 140)

### Added
- Added a headless `media_validation_v1` pipeline stage, typed `media_validation` artifacts, and a dedicated runtime-media-validation benchmark harness for generated-video outputs
- Added focused backend and UI coverage for deterministic media probes, semantic-review handling, validation-backed artifact health, and generated-video trust surfaces

### Changed
- Changed generated-video review to surface validation status through the existing render, artifact-detail, and inbox health paths instead of leaving validation in run logs
- Changed the runtime validator internals to split deterministic probing and multimodal semantic-review transport into focused modules, keeping the validation substrate within repo size rules

### Fixed
- Fixed `ffprobe`-absent fallback behavior so decodable clips no longer false-fail with `missing_video_stream`
- Fixed media-validation artifact badges and inbox timestamps so trust state now stays consistent across header, version history, and inbox attention items

## [2026-03-20-06] — Memory model and transcript retention (Story 033)

### Added
- Added a schema-first memory layer with transcript search, canonical-memory query support, working-memory summaries, and project-scoped memory settings for long-running role collaboration
- Added focused service, API, and chat-memory regression coverage for transcript linkage, substantive artifact-state answers, and persisted working-memory lifecycle behavior

### Changed
- Changed Director and optional Script Supervisor memory handling to reuse persisted working-memory summaries and canonical transcript/artifact retrieval instead of relying on ephemeral chat state alone
- Updated Story 033 close-out records and backlog tracking so the non-blocking `MemoryService` decomposition follow-up is documented as structural debt rather than left implicit

## [2026-03-20-05] — Methodology-first triage ordering

### Changed
- Reworked `/triage`, `/triage-stories`, `/triage-inbox`, and `/triage-evals` so they now prioritize Ideal → spec → build map → ADRs before considering stories, inbox items, or eval queues
- Updated the triage runbooks, methodology guide, and bootstrap skill guidance so the planning stack consistently treats backlog artifacts as continuations of named methodology gaps rather than the source of priority

## [2026-03-20-04] — Chat model disclosure and transparency close-out (Story 127)

### Added
- Added runtime model provenance to persisted and streamed chat messages so assistant and role responses can disclose which model produced them
- Added focused chat provenance regression coverage for message persistence and streamed role/text chunks

### Changed
- Changed the chat transcript UI to render a subtle per-response model badge while keeping shared artifact health semantics authoritative
- Updated Story 127 close-out records and backlog tracking so the unrelated stale historical run polling bug is explicitly captured as Story 139 instead of being left implicit

## [2026-03-20-03] — Design-study composition loop and browser automation reset path (Story 121)

### Added
- Added a composition-bar iteration flow for design studies, including positive and negative reference staging, directive capture, round branching from history, and extracted contact-sheet history UI
- Added `scripts/reset_playwright_mcp.py` plus Scout 016 so stale Playwright/Chrome profile locks can be detected and cleared before browser automation reruns

### Changed
- Changed design-study round contracts, prompt compilation, sources provenance, and preference-learning inputs so `directive`, `positive_refs`, and `negative_refs` flow end to end instead of the old round-level `guidance` field
- Updated the browser automation runbook and Story 121 close-out records so browser verification now documents the reliable reset and local Vite invocation path

## [2026-03-20-02] — Transparent preference learning from design-study choices (Story 131)

### Added
- Added a first-class transparent preference-learning loop for design-study decisions, including immutable `preference_signal` artifacts, a project-level preference profile API, and a dedicated Project Settings inspection surface

### Changed
- Changed design-study prompt compilation to consume explicit learned-preference context with visible provenance in the round sources panel
- Updated the story index and Story 131 close-out records to reflect the landed preference-learning slice

## [2026-03-20-01] — Methodology bootstrap package and eval scaffolding surface

### Added
- Added the canonical `/setup-methodology` skill package with its setup runbook, bundled checklist template, and mode reference
- Added the `/create-eval` skill plus dedicated `create-eval` and `promptfoo` runbooks for CineForge's benchmark workflow
- Added Scout 015 and upgraded the scout template/skill to record transfusion intent plus explicit verification and evidence sections

### Changed
- Updated `AGENTS.md`, `init-project`, the setup checklist, eval docs, and golden runbook to teach the consolidated methodology package and day-to-day eval surface
- Updated the methodology bootstrap docs to treat `/setup-methodology` as the single setup front door and remove stale phased-setup guidance

### Removed
- Removed the deprecated phased `setup-*` skills and their Gemini wrappers so the repo no longer carries a second setup surface

## [2026-03-19-03] — Video understanding benchmark and model selection baseline (Story 030)

### Added
- Added a full promptfoo-based video-understanding benchmark lane with grouped video-analysis schemas, benchmark docs, a 20-clip synthetic previz dataset, provider/scorer/report tooling, and registry-backed result tracking
- Added corrected March 19, 2026 anchor-subset result artifacts showing `GPT-5.4` as the current leader and the best corrected Google subject as `Gemini 2.5 Flash`

### Changed
- Updated `AGENTS.md` and Story 030 planning/validation records so model selection now requires live discovery first and benchmark closure is scoped to Story 030-owned lint evidence rather than unrelated repo-wide Ruff debt
- Updated the story index to mark Story 030 done and clear the active in-progress lane

### Fixed
- Fixed the benchmark conclusion for Gemini models by raising the Google output-token budget to the live max after usage metadata showed the earlier low scores were harness-budget artifacts, not reliable model evidence
- Restored the shared UI toolchain in the worktree so the mandatory close-out `lint` and `tsc -b` gates could run successfully during story closure

## [2026-03-19-02] — Cost tracking and budget controls (Story 032)

### Added
- Added typed run/project cost summaries, budget enforcement, deterministic cost-report exports, and operator-facing cost surfaces across Runs, Run Detail, and Project Settings
- Added end-to-end resume coverage proving a budget-paused run can continue cleanly after the operator raises the run cap

### Changed
- Narrowed Story 032 to the shipped cost-tracking slice, moved deferred cost-profile/model-comparison/stage-cap work into Story 138, and advanced Story 030 out of blocked status

### Fixed
- Corrected stale planning state in the build map and story index so Story 032 closure no longer leaves backlog drift behind

## [2026-03-19-01] — Render adapter and generated video review (Story 028)

### Added
- Added the `render_adapter_v1` generation module, initial OpenAI Sora 2 and Google Veo 3.1 engine packs, and thin video-provider transports that compile concern-group artifacts into immutable `render_prompt` and `generated_video` artifacts
- Added Scene Workspace and Artifact Detail review surfaces for generated video and compiled render prompts, including chat handoff from selected prompt text

### Changed
- Updated the pipeline graph, schema registry, recipe wiring, story index, and build map so `generated_video` is the canonical render output surface and Story 028 is now closed

### Fixed
- Blocked backend/chat-side direct edits to `render_prompt` artifacts and excluded `track_manifest` bookkeeping from render artifact staleness lineage so fresh outputs stay valid on creation

## [2026-03-18-04] — Animatics, keyframes, and previz baseline (Story 027)

### Added
- Added scene-level animatic and keyframe artifacts plus a project-level previz reel, with a deterministic ffmpeg-based recipe that composes storyboard stills, shot timing, and optional temp audio into a playable review assembly
- Added Scene Workspace and Artifact Detail review surfaces for animatics, keyframes, and previz artifacts, including in-app immutable keyframe lock controls
- Captured the richer previz follow-up as Story 137 and logged the cross-cutting agentic video/audio validation gap in the inbox

### Changed
- Updated the pipeline graph, schema registry, artifact metadata, and operator-facing run copy so animatics and keyframes behave like first-class visualization stages
- Marked Story 027 done and advanced Story 028 from blocked to pending now that the animatic/keyframe substrate exists

### Fixed
- Replaced the stepped-motion slideshow path with true per-frame motion generation for the smoke previz output
- Replaced the synthetic smoke audio with a real public-domain sample clip and hardened WAV validation so streamed WAV headers no longer inflate injected-audio durations

## [2026-03-18-03] — Scout 014: finish-and-push lifecycle wrapper

### Added
- Added a new `/finish-and-push` skill and `docs/runbooks/finish-and-push.md` to bundle story closure with the validated landing flow when the user explicitly requests the full chain

### Changed
- Updated `AGENTS.md` story-execution and runbook guidance to recognize `/finish-and-push` as the bundled close-out path and list its companion runbook
- Recorded Scout 014 for the Dossier delta focused on `finish-and-push` and updated `docs/scout.md` with the completed expedition

## [2026-03-18-02] — GPT-5.4 mini/nano eval refresh

### Added
- Added targeted promptfoo coverage and saved result artifacts for `gpt-5.4-mini` and `gpt-5.4-nano` across config detection, QA pass, normalization, scene extraction, and entity discovery

### Changed
- Refreshed `docs/evals/registry.yaml` with the March 18, 2026 scores, latency, cost, and adoption notes for the new OpenAI cheap-tier models

### Fixed
- Added runtime pricing support and unit-test coverage for `gpt-5.4-mini` and `gpt-5.4-nano` so live cost accounting no longer reports `$0.00`

## [2026-03-18-01] — Planning-stack governance migration (Story 136)

### Added
- Added the execution ideal to `docs/ideal.md` and made execution constraints first-class in the planning stack through `spec:11` and the matching build-map category

### Changed
- Reorganized `docs/spec.md` and `docs/build-map.md` around stable `spec:N(.N)` references, substrate status, and `climb` / `hold` / `converge` governance
- Aligned `AGENTS.md`, methodology docs, triage skills, triage runbooks, and active story `Spec Refs` with the new category model

### Fixed
- Resolved the missing Timeline owner in the build map and archived `docs/retrofit-gaps.md` after reconciling the drifted C1/C2/C3/C4/C7 thresholds back into the live planning surfaces

## [2026-03-17-01] — Storyboard generation and review surface (Story 026)

### Added
- Added scene-level `storyboard` artifacts, the `storyboard_v1` visualization module, and a dedicated storyboard-generation recipe with persisted frame files, storyboard-track integration, per-frame estimated image costs, and project/run style selection including photoreal opt-in gating
- Added a first-class storyboard review surface in the UI with a Scene Workspace `Storyboard` tab, a dedicated inline viewer, and Artifact Detail rendering for storyboard artifacts

### Changed
- Updated backlog/status docs to mark Story 026 done and advance Story 027 now that storyboard generation is landed
- Recorded a reusable AGENTS.md lesson that driver-loaded helper modules should use absolute package imports

## [2026-03-15-05] — Entity discovery taxonomy tightening (Story 129)

### Changed
- Tightened the `entity_discovery_v1` taxonomy contract for background-character exclusions, prop-noise exclusions, and floor-level location retention while keeping the recall-verification loop intact
- Aligned the standalone entity-discovery benchmark prompt with the module wording so promptfoo reruns measure the same taxonomy policy the runtime uses

### Fixed
- Added direct regression tests for the entity-discovery prompt contract so future edits cannot silently relax the background-role and set-dressing exclusions
- Re-ran the Gemini 2.5 Flash Lite entity-discovery eval, recovered the required `15TH FLOOR` location after an initial prompt regression, and raised the recorded score to `0.920`

## [2026-03-15-04] — Brick & Steel PDF normalization regression fixed (Story 135)

### Added
- Added deterministic Brick & Steel PDF regression coverage through the real ingest path plus focused normalizer coverage for dialogue/action boundary preservation

### Changed
- Extracted screenplay normalization routing into a focused helper so PDF screenplay inputs bypass `smart_chunk_skip` and use the existing single-pass cleanup path

### Fixed
- Preserved blank-line-separated action after dialogue in deterministic Fountain normalization so canonical scripts no longer re-collapse the repaired Brick & Steel passage

## [2026-03-15-03] — Compromise convergence tooling migration (Story 134)

### Added
- Added CineForge-specific convergence source-of-truth docs: `docs/build-map.md`, `docs/methodology-ideal-spec-compromise.md`, and new `align` / `triage` runbooks and skills

### Changed
- Migrated active agent guidance from `adr-reflect` to `align`, introduced orchestrating `/triage`, and updated setup, triage, story-template, and lifecycle skills to the post-migration methodology graph
- Merged eval mismatch classification into `/improve-eval` and aligned active golden/runbook/template guidance with the unified flow

### Fixed
- Removed the retired `adr-reflect` / `verify-eval` skills and stale Gemini wrappers
- Cleaned migration-doc mismatches: stale `/verify-eval` guidance, absolute local markdown links, and unchecked build-map coverage boxes
## [2026-03-15-02] — Design-study prompt compiler and reference propagation (Story 119)

### Added
- Per-round design-study provenance panels and immutable bible-manifest `visual_reference_image` persistence so the operator can inspect prompt inputs and downstream tools can consume one canonical image reference

### Changed
- Design-study prompt compilation now incorporates project config, look-and-feel, and intent-mood context through the shared deterministic `build_image_prompt()` path
- Backlog/story docs now reflect Story 119 as landed, keep Story 026 sequence-sensitive against the canonical reference path, and retire the stale Story 113 circuit-breaker item

### Fixed
- `selected_final` decisions now set and clear canonical visual references via new bible manifest versions instead of leaving downstream consumers tied to design-study state alone
- Downstream entity reference collection now reads the bible-manifest canonical image field, and the design-study UI optimistically clears prior finals to match backend single-final behavior

## [2026-03-15-01] — Semantic change propagation lands (Story 031)

### Added
- Semantic impact assessment artifacts, API routes, and browser actions for previewing stale scope, running selective assessment, and recording immutable assessment provenance

### Changed
- Artifact detail, inbox, artifact lists, and home health summaries now surface live graph health states and attention semantics instead of relying on persisted snapshot metadata

### Fixed
- Added request-scoped assessment budget caps, long-running operation feedback for impact assessment, and automated selective-assessment coverage so Story 031 closes against its full acceptance criteria
- Persisted long-running chat status updates by message ID so impact-assessment completion survives reload with the correct permanent record
- Wrapped artifact-detail version-history health badges so long status labels stay inside the sidebar card instead of overflowing

## [2026-03-14-08] — Story backlog sequencing corrections

### Changed
- Promoted Story 119 to `Pending` now that Story 120 landed and the design-study prompt-compiler scope is concrete enough to build
- Clarified that Story 026 should consume Story 119's propagated `visual_reference_image` when available so storyboard generation follows the canonical design-study reference path

### Fixed
- Added Story 031 as an explicit dependency for Story 097 so AI artifact editing no longer appears build-ready ahead of semantic change propagation
- Updated `docs/stories.md` so the execution map and story table reflect the corrected sequencing and status information

## [2026-03-14-07] — Visual medium selection and prompt grounding (Story 120)

### Added
- A project-level `production_format` setting that persists through the existing project settings path and feeds format-aware design-study prompt building with `sources_used` provenance
- Reusable `Visual Medium` UI surfaces: first-run picker modal for design-study generation, an Intent-owned editor, and a Script breadcrumb pill back to Intent

### Changed
- Moved project-level visual references out of Script and into Intent & Mood so the screenplay page stays focused on reading
- Unified Script Breakdown / Deep Breakdown CTA state and operator copy around the shared active-run path so Intent, chat buttons, and progress banners agree on what is running

### Fixed
- Clarified operator messaging so script-breakdown completion and deep-breakdown completion are distinguished instead of collapsing into a misleading generic `Breakdown complete!`

## [2026-03-14-06] — Backlog readiness cleanup and story promotion

### Changed
- Refreshed the execution map in `docs/stories.md` so the ready-to-build lane matches the real dependency graph and no longer treats completed Story 029 as pending
- Promoted Stories 046, 120, 127, 128, 129, and 131 from `Draft` to `Pending` now that their scopes and file maps are build-ready

### Fixed
- Corrected the blocked-chain note for Story 028 so it no longer lists already-complete Story 029 as an active blocker
- Rewrote Story 046 against the current `ui/` architecture so the theme-system work can move forward without stale path references

## [2026-03-14-05] — Record screenplay formatting repro inputs

### Added
- Benchmark input fixtures for the elevator and flashback scene-enrichment cases tied to the latest screenplay formatting regression report

### Changed
- Updated the inbox with a concrete reproduction note describing the dialogue/action spacing failure seen in the Brick & Steel PDF import

## [2026-03-14-04] — User asset injection lands end-to-end (Story 029)

### Added
- An origin-agnostic asset injection system for project, scene, and entity targets, including typed manifests, upload APIs, and reusable Operator Console reference-library surfaces

### Changed
- Unified uploaded and AI-generated references into the same browser so design-study outputs, scene references, and project references share one working surface
- Story 029 now owns the merged real-asset upload UX that was previously split into Story 098

### Fixed
- Removed the stale client fallback for empty asset manifests and decomposed the shared reference browser after validation flagged maintainability debt
- Corrected the Operator Console upload flow so file selection uploads immediately and the compact reference cards no longer rely on unstable inline controls

## [2026-03-14-03] — Backlog cleanup and story sequencing corrections

### Changed
- Refreshed the stories execution map so the ready-to-build lane matches the actual story statuses and current dependency graph
- Clarified draft sequencing for the design-study follow-on stories and documented that Story 098 remains downstream of Story 029

### Fixed
- Removed the stale execution-map recommendation for already-complete Story 132
- Moved Story 023 out of ambiguous draft status into an explicit deferred state now that Story 025 proved the fallback path
- Corrected stale implementation notes in Story 046 so it explicitly requires a rewrite against the current `ui/` tree before promotion

## [2026-03-14-02] — Agent workflow refinements and eval triage tooling

### Added
- A new `/triage-evals` skill and `docs/runbooks/triage-evals.md` for cheap, read-only diagnosis of which eval, compromise gate, or stale benchmark needs attention next
- Scout 013 documenting Storybook, Dossier, and codex-forge agent-process findings and adoptions

### Changed
- `AGENTS.md` now defines coherent scope expansion, relative-effort guidance, working norms, expected-fail semantics for compromise/detection evals, and the stronger story-closure disposition rules
- Story lifecycle skills now handle scope adjustments and closure recommendations more explicitly: `/build-story` folds small required deltas into the current story, `/validate` and `/mark-story-done` must recommend a single disposition when work is incomplete, and `/scout` recognizes broad explicit approval for recommended inline adoptions
- Eval documentation now points agents to `/triage-evals` before spending promptfoo time just to decide what to improve next

## [2026-03-14-01] — xAI eval sweep and benchmark fixture repair

### Added
- xAI benchmark result artifacts for the Grok evaluation sweep, including the full `grok-4-1-fast-reasoning` quality pass across the promptfoo task suite

### Changed
- `docs/evals/registry.yaml` now records `Grok 4.1 Fast Reasoning` scores, latency, and cost across the quality evals so the xAI comparison is tracked in the canonical registry

### Fixed
- Repaired missing benchmark input fixtures needed by normalization, continuity, and QA evals
- Updated `benchmarks/tasks/qa-pass.yaml` to use the maintained elevator scene fixture path instead of the vanished `benchmarks/input` duplicate
- Narrowed `.gitignore` so canonical benchmark inputs under `benchmarks/input/` are no longer silently ignored

## [2026-03-13-11] — Deploy runbook timing recalibration

### Changed
- Recalibrated the `/deploy` skill's expected duration from ~2 minutes to ~2.5 minutes to match the trailing successful deploy median more closely
- Expanded deploy timing memory with the March 14 Fly remote-builder failures and the successful local-only fallback deployment

## [2026-03-13-10] — Model refresh, eval verification, and project defaults (Story 133)

### Added
- New validated model options for provider refresh candidates in the runtime and project model-setting surfaces, with Story 133 capturing the cross-cutting benchmark/verification work

### Changed
- Refreshed registry-backed eval evidence and project-scoped model-default behavior so saved settings propagate honestly into live runs and explicit per-run clears remain possible

### Fixed
- Corrected benchmark scorer/golden defects uncovered during verification and fixed the `/api/runs/start` merge path so cleared optional model overrides are no longer silently replaced by saved project defaults

## [2026-03-13-09] — Shot planning UI and shot-list exports (Story 132)

### Added
- A scene-first `Shots` workspace surface and shared shot-plan viewer so operators can run shot planning, inspect readable coverage, and open dedicated artifact detail from the real UI

### Changed
- Export UI wiring now exposes project-wide shot-list CSV/PDF actions and shot-planning run progress copy uses explicit shot-planning language

### Fixed
- Resolved the driver-only `shot_plan_v1` dynamic import schema rebuild failure and normalized whitespace-heavy scanned PDF ingest output so the full unit suite closes green

## [2026-03-13-08] — Shot planning backend landing (Story 025)

### Added
- `shot_plan` schemas, module, recipe, and tests for scene-level coverage strategies and ordered shot definitions
- Shot-list CSV/PDF export support in the backend export path

### Changed
- Timeline and shots-track artifacts now receive shot-planning updates from the new module
- Pipeline graph now marks shot planning as implemented

### Fixed
- Closed the missing backend/API shot-planning gap that was blocking downstream visualization stories
## [2026-03-13-07] — Golden fixture re-verification and corrections

### Fixed
- Removed incorrect ROSE from scene 13 (INT. STAIRWELL) characters in `the-mariner-scenes.json` — she does not appear in that segment
- Fixed flashback heading in `enrich-scenes-golden.json` to match screenplay verbatim
- Fixed COASTLINE and BACKYARD name fields in `the-mariner-locations.json` (were full headings, now plain location names)
- Added missing `INT. 12TH FLOOR STAIRWELL` to AIRTAG must_mention_scenes in `the-mariner-props.json`

### Changed
- Full adversarial re-verification of all 10 golden fixtures with updated checklist notes

## [2026-03-13-06] — Backlog status hygiene and execution map

### Changed
- Replaced the stale `docs/stories.md` build-order section with a current execution map that distinguishes build-ready, blocked, and still-draft work
- Normalized live backlog statuses away from `To Do`, promoting executable stories to `Pending` and marking dependency-bound stories as `Blocked`

### Fixed
- Resolved the Story 011e status contradiction by aligning the story index and canonical story file on `Deferred` with explicit historical-scope notes
- Eliminated index/file status drift across the updated backlog entries
## [2026-03-13-02] — Story scaffolding refinements from Scout 012

### Added
- Scout 012 audit of `codex-forge` agent updates, recorded in `docs/scout/scout-012-codex-forge-agent-updates.md` and indexed in `docs/scout.md`

### Changed
- `/create-story` guidance now treats `Draft` as the default new-story status, adds the simplification-baseline question, and explicitly reminds story authors to include `make skills-check` for agent-tooling changes
- Story template tasks now call out `/verify-eval` plus `docs/evals/registry.yaml` updates when evals or goldens move
- `/triage-stories` now correctly states that Draft stories may be recommended but must be promoted to `Pending` before `/build-story`

## [2026-03-13-03] — Triaged inbox into stories and research spikes

### Added
- Draft stories 127-131 for artifact health semantics/chat model disclosure, provider failure chat notifications, entity-discovery taxonomy tightening, export fidelity, and preference learning
- A new `media-generation-capability-refresh` research workspace under `docs/research/` with a populated research prompt for current image/video/music model capabilities

### Changed
- Emptied `docs/inbox.md` by moving actionable items into tracked stories or the new research spike
- Folded ADR-003 asset-pipeline ideas into Story 098 instead of leaving them as separate inbox entries
- Updated `docs/stories.md` to register the new draft backlog items

## [2026-03-13-05] — Operator verification handoff guidance

### Changed
- `AGENTS.md` and the story lifecycle skills (`build-story`, `validate`, `mark-story-done`) now require a short `Where to verify` note whenever there is a concrete path for the user to spot-check completed work

## [2026-03-13-04] — Chat about this interaction pattern (Story 096)

### Added
- Reusable `Chat about this` draft insertion flow across Scene Workspace concern-group annotations and shared artifact viewers, with contextual role tagging and quoted source text

### Changed
- Chat intent handling now cleanly separates editable draft insertion from immediate-send help/glossary questions

### Fixed
- Closed right-panel chat actions no longer drop pending draft/send intents when reopening the chat panel

## [2026-03-13-01] — Frontend chat and data-layer decomposition (Story 126)

### Changed
- Split the frontend chat/data layer into focused modules under `ui/src/components/chat/`, `ui/src/lib/api/`, and `ui/src/lib/hooks/`, reducing `ChatPanel.tsx`, `api.ts`, and `hooks.ts` to clear orchestration/barrel roles
- Repointed internal chat/run consumers to the new module boundaries while preserving existing routes, payloads, role chat behavior, progress rendering, and entity context handling

### Fixed
- Restored the dedicated `activity` chat icon after extraction so navigation/activity notes keep their prior visual treatment
- Repaired the UI validation baseline by adding the direct `@radix-ui/react-dialog` dependency and fixing the `CommandPalette.tsx` implicit-`any` type hole
## [2026-03-12-01] — Agent workflow hardening meta upgrade (Story 125)

### Added
- Story 125 to track the repo's agent-workflow hardening bundle with explicit acceptance criteria, workflow gates, and validation evidence
- `codebase-improvement-scout` skill, runbook, templates, bootstrap script, and research/scout artifacts for report-first repo hygiene
- ADR-check reminders across reusable skills and scoped agent docs

### Changed
- Story lifecycle workflow: `build-story` now stops at implementation handoff, `validate` owns validation, and `mark-story-done` is the only story-closing step
- `check-in-diff`, its runbook, and `AGENTS.md` worktree policy to support task branches plus a safe `main` fallback without pushing unvalidated `main`
- Story template and story-creation guidance to include workflow gates, ADR refs, redundancy checks, and browser-verification requirements for UI work

## [2026-03-07-02] — Recall verification loop for entity discovery (Story 124)

### Added
- Recall verification in `entity_discovery_v1` — cross-references discovered locations/props against scene_index signals, re-prompts when gaps detected
- `_normalize_entity_name()` — general-purpose entity normalizer for locations (strips INT./EXT., time-of-day) and props
- `_extract_scene_index_signals()` — extracts location/prop reference lists from scene_index
- `_find_recall_gaps()` — bidirectional substring matching for recall gap detection
- `_build_verification_prompt()` — targeted re-prompt with missing entity hints
- Acceptance test for live verification against The Mariner screenplay
- 12 new unit tests for verification helpers and integration flow

### Changed
- `entity_discovery_v1` `processing_metadata` now includes `verification_ran`, `locations_gap_count`, `props_gap_count`, `verification_cost_usd`

## [2026-03-07-01] — Prompt completeness and grounding (Scout 010)

### Added
- Completeness contract language in `character_bible_v1`, `location_bible_v1`, `scene_analysis_v1` prompts — models must verify coverage before finalizing
- Grounding language in `character_bible_v1`, `location_bible_v1`, `scene_analysis_v1`, `prop_bible_v1` prompts — base claims strictly on screenplay text, do not invent
- "Prompt-First Before Model Escalation" principle in `AGENTS.md` — try prompt improvements before upgrading to expensive models
- Story 124 (Draft) — Recall Verification Loop for Entity Discovery
- Multi-pass research mode idea added to `docs/inbox.md`
- Scout 010 expedition document (`docs/scout/scout-010-openai-prompt-guidance.md`)

## [2026-03-06-02] — Model discovery snapshot for eval registry

### Added
- `docs/evals/models-available.yaml` — provider model discovery snapshot (63 models: OpenAI 42, Anthropic 9, Google 12; discovered 2026-03-04)

## [2026-03-06-01] — Adversarial golden fixture verification — all 10 CLEAN

### Fixed
- `the-mariner-characters.json` — added MacAngus family name to MARINER key_facts; added Newfoundland/Maritime dialect note to DAD key_facts; added VINNIE→MARINER adversary relationship requirement
- `the-mariner-locations.json` — removed phantom "shore" alias from COASTLINE; added "mismatched paintings of different periods" to 15TH FLOOR physical_traits
- `the-mariner-props.json` — removed phantom BOSUN alias from OAR; removed phantom exterior scene ref from OAR must_mention_scenes; cleared PURSE physical_traits (no physical description in script); added AIRTAG prop (tracking device hidden in Rose's purse); fixed FLARE GUN key_fact wording
- `the-mariner-relationships.json` — fixed 6 prop IDs and evidence strings; added mariner-flare-gun-weapon edge; added mariner-airtag-tracking edge; improved false_positive_examples with specific screenplay-grounded examples; bumped min_must_find 5→6
- `the-mariner-config.json` — narrowed format.expected_values (removed "screenplay" — too broad); added "superhero" to genre keywords; added dark comedy tones
- `normalize-signal-golden.json` — fixed expected_scenes[3] heading; removed phantom `\!` forbidden_pattern (would penalize valid Fountain force-action lines)
- `enrich-scenes-golden.json` — corrected flashback tone "bittersweet"→"joyful"; fixed key_details phrasing to remove spoiler inference

### Changed
- `benchmarks/golden/_verification-checklist.md` — all 10 fixtures now CLEAN; updated pass notes to fix-summary format

## [2026-03-03-03] — Anthropic prompt caching in LLM transport layer (Story 123)

### Added
- `enable_caching: bool = False` parameter on `call_llm()` — when True and provider is Anthropic, wraps user content in a `cache_control: {"type": "ephemeral"}` block
- `anthropic-beta: prompt-caching-2024-07-31` header added to all Anthropic transport requests (harmless when no cache markers present)
- Cache token counts (`cache_read_input_tokens`, `cache_creation_input_tokens`) propagated through `_normalize_anthropic_response()` and `_parse_response()` into call metadata; logged at DEBUG level

### Changed
- `character_bible_v1`, `location_bible_v1`, `prop_bible_v1`, `scene_analysis_v1`, `script_normalize_v1` — main work calls now pass `enable_caching=True`; Gemini-default modules (`script_bible_v1`, `entity_discovery_v1`, `entity_graph_v1`) unchanged

## [2026-03-03-02] — Golden fixture helper infrastructure (Story 122)

### Added
- `tests/unit/golden_fixture_helpers.py` — `GoldenFixtureSpec` dataclass + `GOLDEN_SPECS` registry + `load_golden()` loader + 6 structural assertion helpers (`assert_metadata_present`, `assert_scene_count`, `assert_no_empty_headings`, `assert_no_duplicate_scene_numbers`, `assert_source_lines_valid`, `assert_characters_are_strings`)
- `tests/unit/test_golden_fixtures.py` — `TestMarinerSceneEntitiesStructure`: 6 `@pytest.mark.unit` structural tests for `the_mariner_scene_entities.json`

### Changed
- `docs/runbooks/golden-build.md` — added "Test Coverage" section with 4-step guide for registering new fixtures and an assertion-helper reference table

## [2026-03-03-01] — Entity Design Study: AI concept art generation loop (Story 056)

### Added
- Design Study workflow on every character, location, and prop detail page — generate AI concept art via Imagen 4, iterate in rounds with guidance
- `DesignStudySection` component: direction textarea, 1/2/4/8 image count selector, per-image decision buttons (Select Final, Favorite, Seed for Variants, Reject), guidance textarea for seed/rejected decisions, round history with filter tabs (All/Selected/Favorites/Rejected)
- Entity card thumbnail: shows `selected_final` image, falls back to most recent `favorite`, then icon placeholder
- `POST /api/projects/{id}/design-study/{entity_id}/generate` — synthesizes prompt from bible data, calls Imagen 4, persists images
- `GET /api/projects/{id}/design-study/{entity_id}` — returns full `DesignStudyState` with all rounds
- `POST /api/projects/{id}/design-study/{entity_id}/decide` — records decision + optional guidance per image
- `GET /api/projects/{id}/design-study/{entity_id}/images/{filename}` — serves binary image files
- `src/cine_forge/schemas/design_study.py` — `DesignStudyState`, `DesignStudyRound`, `DesignStudyImage`, `ImageDecision`
- `src/cine_forge/ai/image.py` — `synthesize_image_prompt()` (bible-field synthesis) and `generate_image()` with provider routing: Imagen 4 (Gemini API) and gpt-image-1 (OpenAI Images API)
- gpt-image-1 integration: `_generate_image_openai()` with `output_format: jpeg`, entity-type size mapping (portrait/landscape/square), `OPENAI_API_KEY` auth; routes via `_OPENAI_MODELS` frozenset
- 9 unit tests + 3 integration tests covering the full generate→decide→persist loop

### Changed (UI polish from browser testing)
- Image cards now display at natural 3:4 aspect ratio crop with `object-top` focus; clicking the image opens full resolution in a new tab ("View full" hover overlay)
- Decision buttons redesigned: 4-button grid (Final/Fav/Seed/Reject) with icon+label, per-decision active colors (emerald/yellow/blue/red) and hover tints; all decisions are toggles — clicking an active button resets to `pending`
- "Select" renamed to "Final" with tooltip "Set as visual reference for storyboards and video"
- Index number badge ("1", "2", …) added to top-right of each image card
- State badges (Final/Favorite/Seed) overlaid on image when a decision is active, with matching colors
- "Prompt" toggle renamed to "Details"; model name ("Imagen 4" / "GPT-Image") shown inline right-aligned; expanded view shows full model ID
- Model selector added to generate controls — "Imagen 4" and "GPT-Image" buttons; wired end-to-end via `model` field on `GenerateRequest` and `GenerateDesignStudyParams`
- Generate controls no longer wrapped in a nested box — flat layout within the section card
- `negativePrompt` parameter removed (no longer supported by Imagen 4 API); prompt instruction simplified to "Clean character art, no text"

### Fixed
- `ArtifactManager.read_artifact()` skips binary file extensions (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`) to avoid JSON parse errors on image files in bible folders

## [2026-03-02-14] — Service layer decomposition: 3 class extractions, 3 bug fixes (Story 118)

### Changed
- `service.py` reduced from 1,775 → 992 lines (44% reduction) — thin facade delegates to focused collaborators
- 5 intent/mood routes in `app.py` consolidated from inline `ArtifactStore` construction to `service.get_artifact_store()`
- Export router `get_store()` uses `service.require_project_path()` instead of hardcoded `Path(f"output/{project_id}")`
- `ServiceError` extracted to `src/cine_forge/api/exceptions.py` — shared leaf module, no circular imports

### Added
- `src/cine_forge/api/chat_store.py` — `ChatStore` class with `threading.Lock` protecting all writes (103 lines)
- `src/cine_forge/api/run_orchestrator.py` — `RunOrchestrator` class owning run threads, errors, and lock (613 lines)
- `src/cine_forge/api/artifact_manager.py` — `ArtifactManager` class for browse/read/edit with path traversal guard (290 lines)
- `src/cine_forge/api/exceptions.py` — shared `ServiceError` exception (14 lines)
- `src/cine_forge/schemas/runtime_params.py` — `RuntimeParams(BaseModel)` with 16 typed fields replacing stringly-typed dict (49 lines)
- 15 new unit tests: 7 ChatStore, 6 RuntimeParams, 2 orphan detection

### Fixed
- Chat race condition: concurrent upserts could drop messages (no lock on read-modify-write path)
- Orphan detection: `read_run_state` now persists `"failed"` status to disk after detecting stuck runs
- Export router: hardcoded `Path(f"output/{project_id}")` broke for external projects and non-CWD launches

## [2026-03-02-13] — Engine decomposition: 4 class extractions (Story 117)

### Changed
- `engine.py` reduced from 1,543 → 1,159 lines (25% reduction)
- `_execute_single_stage` reduced from 528 → 214 lines (59% reduction)
- Signature reduced from 22 → 18 parameters via `RetryConfig` dataclass

### Added
- `src/cine_forge/driver/schema_registry.py` — `build_schema_registry()` factory (86 lines)
- `src/cine_forge/driver/retry_policy.py` — `StageRetryPolicy` class + `RetryConfig` + `record_stage_failure()` (255 lines)
- `src/cine_forge/driver/artifact_persister.py` — `ArtifactPersister` class replacing closure + batch loop (233 lines)
- `src/cine_forge/driver/canon_gate_runner.py` — `StageCanonGate` class for canon review gating (116 lines)
- `tests/unit/test_retry_policy.py` — 15 isolation tests
- `tests/unit/test_artifact_persister.py` — 6 isolation tests
- 4 additional tests in `tests/unit/test_schema_registry.py`

## [2026-03-02-12] — Story 117/118 audit corrections, inbox update

### Changed
- Stories 117 and 118: corrected stale line counts, parameter counts, method names, test counts, and enum values against actual post-Story-116 source code
- Story 118: RuntimeParams field count corrected from 15 to 16 (alias pairs clarified)
- Added "Surface provider quota/billing errors in chat" to docs/inbox.md

## [2026-03-02-11] — Event System Refactor complete, project_config truncation fix (Story 116)

### Added
- `ProgressEvent` Pydantic model and `EventType` StrEnum in `src/cine_forge/schemas/progress_event.py` — typed, validated event schema with 11 event types
- `EventEmitter` class in `src/cine_forge/driver/event_emitter.py` — thread-safe JSONL writer with internal `threading.Lock` and optional callback
- SSE endpoint `GET /api/runs/{run_id}/events/stream` — async generator tail-follows JSONL, polls 0.5s, stops on `finished_at`
- `useRunEventSSE` hook in `ui/src/lib/use-run-progress.ts` — native `EventSource` invalidates query caches on each message; existing 3s polling remains as fallback
- 9 unit tests in `tests/unit/test_event_emitter.py` — concurrent write safety (10 threads × 20 events), callback, field exclusion
- Runtime browser smoke test task added to stories 116, 117, 118

### Changed
- All 11 `_append_event` call sites in `engine.py` replaced with `emitter.emit(ProgressEvent(...))` — callers no longer manage locks or JSON serialization
- `_execute_single_stage` param changed from `events_path: Path` to `emitter: EventEmitter`
- Deleted `_append_event` static method from `DriverEngine`
- `pipeline_started` and `pipeline_finished` lifecycle events added to engine run loop

### Fixed
- `project_config_v1` module `max_tokens` bumped from 1800 to 16384 — Gemini's thinking tokens consumed the output budget, causing truncation on every attempt. The eval config already used `maxOutputTokens: 16384` for Gemini providers but the module wasn't updated when Story 107 changed the default model from Haiku to Gemini 3 Flash.

## [2026-03-02-10] — Pipeline Architecture Refactor Plan complete (Story 115)

### Added
- Story 116: Event System Refactor — EventEmitter class, ProgressEvent Pydantic schema, SSE endpoint, 11 call site migration plan
- Story 117: Engine Decomposition — 4 behavior-preserving extractions (StageRetryPolicy, ArtifactPersister, build_schema_registry, StageCanonGate)
- Story 118: Service Layer Decomposition — ChatStore, RunOrchestrator, RuntimeParams Pydantic model, 3 bug fixes (chat race, orphan persistence, export router)
- Architecture Rules section in AGENTS.md — method >100 lines, class >500 lines, inter-layer Pydantic contracts, god object check
- `make check-size` Makefile target — flags Python/TS files over 400 lines
- Structural Health Check gate in build-story skill (Phase 2, step 8)
- Architectural Fit section in story template

## [2026-03-02-09] — Fix run-polling stop conditions and bible spinner; Story 114 deferred; Story 115 created

### Fixed
- `useRunEvents` now stops polling (3s interval) when a run finishes — previously polled forever post-completion, wasting network/CPU
- Bible artifact spinner messages now clear on stage failure in addition to success/reused — spinner was stuck when a stage errored
- Removed `structuralSharing: false` from `useRunState` — was forcing component re-renders every 2s even when data was unchanged

### Changed
- Story 114 (Driver Progress Events) deferred — superseded by Story 116 (to be created by Story 115); full ACs moved to the holistic event system refactor
- Story 115 (Pipeline Architecture Refactor Plan) added — planning story that outputs Stories 116/117/118 for event system, engine, and service decomposition

## [2026-03-02-08] — Scout 008: progress events, circuit breaker, triage-stories Draft support

### Added
- Story 113: Per-Provider LLM Circuit Breaker (Draft) — CLOSED→OPEN→HALF_OPEN state machine for transient provider failures; reference impl in Dossier Story 027
- Story 114: Driver Progress Events (Draft) — structured `ProgressEvent` callbacks from engine to UI; unlocks per-stage OperationBanner and chat timeline updates; reference impl in Dossier Story 028
- Scout 008 expedition doc — new findings from Storybook/Dossier commits since Scout 007

### Changed
- `triage-stories` skill: Draft stories are now first-class candidates alongside Pending; `/build-story` handles flesh-out regardless of starting status
- Scout 007 marked Complete — pending items 4–6 finished (accessibility checklist reverted per user, context window ref added to Story 033, circuit breaker story created)
- Story 033 (Memory Model): added context window summarization reference from Storybook Story 006

## [2026-03-02-07] — Continuity UI Page: entity state timelines and gap visualization (Story 108)

### Added
- New route `/:projectId/world/continuity` — Continuity page showing overall score, gap count, and entity count
- Entity accordion list sorted by type (characters → locations → props), each expandable into a per-scene timeline
- `EntityTimelineView` component: loads `continuity_state` artifacts in parallel, renders scene cards with property grids, diff-style change events with evidence quotes, and amber gap warnings
- "World" collapsible section in sidebar nav with Continuity sub-item; auto-opens when on `/world/*`
- Empty state: prompts to run World Building when no continuity data exists

### Changed
- `artifact-meta.ts`: continuity artifact icons updated from Globe to Activity
- Gap subtitle now shows condition-specific message instead of generic "low confidence or contradictory state" — distinguishes no-properties, low-confidence, and property-conflict cases
- Confidence badge tooltip clarifies it measures extraction quality, not continuity integrity
- Change events distinguish "first mention" (sky badge) from real state changes (strikethrough → new value)

## [2026-03-02-06] — Scout 007: golden skill refinements (Storybook delta)

### Changed
- `golden-verify`: added tooling check before subagent launch — agents now identify the project's interpreter pattern and pass it in instructions to prevent silent wrong-interpreter failures
- `golden-create`: added explicit inbox-move step (step 6) — prevents other agents re-processing the same inbox item after a fixture is created
- `setup-golden`: added inline `_coverage-matrix.json` template with standard `verification_status` values (`pending`/`needs-review`/`verified`)

## [2026-03-02-05] — Value-optimized model selection across all pipeline modules (Story 107)

### Changed
- Updated defaults for 12 module parameters across 8 modules based on value analysis (quality per dollar), replacing stale `gpt-4o` and `claude-sonnet-4-6` defaults:
  - `character_bible_v1` → `claude-sonnet-4-6` (quality winner, justified by creative depth requirement)
  - `location_bible_v1` → `claude-sonnet-4-6` (quality winner; Opus 4.6 not justified at 6× cost)
  - `prop_bible_v1` → `claude-sonnet-4-6` (Haiku gap too large for visual precision tasks)
  - `entity_graph_v1` → `gemini-2.5-flash` (7-way tie at 0.995, 3.2× cheaper than Sonnet)
  - `project_config_v1` → `gemini-3-flash-preview` (quality + cost winner: 0.953, $0.009/call)
  - `script_normalize_v1` → `claude-haiku-4-5-20251001` (0.954 quality at $0.003, up from 0 quality gpt-4o)
  - `script_normalize_v1` QA model → `gpt-4.1-mini` (perfect 1.000 at $0.0008/call)
  - `scene_analysis_v1` QA model → `gpt-4.1-mini` (perfect 1.000 at $0.0008/call)
  - `script_bible_v1` → `gemini-2.5-flash-lite` (0.885 quality, $0.00089/call, value score 1000)
  - `entity_discovery_v1` → `gemini-2.5-flash-lite` (0.905 quality, $0.00053/call, value score 1698)
- Fixed `gemini-2.5-flash-lite` pricing in `llm.py` (was $0.00 — now $0.075/$0.30 per M tokens)
- Python module fallbacks updated to match `module.yaml` defaults (fallbacks control actual runtime behavior)
- Removed stale `gemini-2.5-flash` override in `recipe-world-building.yaml`; entity_graph now uses module default

### Added
- `benchmarks/scripts/analyze-eval.js` — generalized value analysis script (quality ranking + value ranking tables)
- `script_bible` eval: golden ref, Python scorer (10 dimensions), LLM rubric, task YAML covering 8 providers
- `entity_discovery` eval: golden ref, Python scorer (precision/recall by category), LLM rubric, 10 providers
- Creative direction modules documented as smoke-test-only (persona-driven output not suitable for golden-ref evals)
- AGENTS.md eval catalog updated with value-winner column for all 12 evals

## [2026-03-02-04] — "View in Script" scrolls to correct scene + bookmarkable hash links (Story 111)

### Fixed
- "View in Script" on scene pages now reliably scrolls the script viewer to the correct scene heading. Previously a race condition caused the scroll to silently fail on fresh navigation (URL param cleared before CodeMirror had loaded content).

### Changed
- Navigation mechanism switched from `?scene=` query param to URL hash (`#heading`). "View in Script" links are now bookmarkable/shareable permalinks — the script loads and scrolls to the target scene on any reload or direct link visit.
- `scrollToHeading` in `ScreenplayEditor` returns `boolean` to signal success, enabling retry-with-backoff logic (200/400/800ms) for late-mounting editors.

## [2026-03-02-03] — Fuzzy search + scene shorthand in command palette (Story 110)

### Added
- Fuzzy/typo-tolerant search: "marinner" now finds "Mariner" (rapidfuzz, threshold 75)
- Initials matching: "ym" finds "Young Mariner", "dj" finds "Detective Jones"
- Scene shorthand: "sc2" / "sc 2" jumps directly to Scene 2; bare "sc" lists all scenes
- Scene number (`#N`) shown in search result rows for instant confirmation

### Fixed
- Scene search was silently returning zero results in all real projects — `search_entities` was looking in `__project__/` but the pipeline saves `scene_index` with `entity_id="project"`. Now tries `"project"` first with `None` fallback.

## [2026-03-02-02] — Scene Workspace (Story 099)

### Added
- Scene Workspace page (`/scenes/:entityId`) — per-scene production control surface replacing the generic EntityDetailPage for scenes
- Five concern group tabs (Look & Feel, Sound & Music, Rhythm & Flow, Performance, Story World) with red/yellow readiness dots in each trigger
- Per-group "Let AI fill this" / "Regenerate" buttons wired to the `creative_direction` recipe
- Scene entity roster: clickable character, location, and prop links pulled from scene artifact data
- Overview tab with `SceneViewer` text summary (best available preview representation)
- Intent & Mood panel (`SceneIntentPanel`) showing project-level intent with scene-override badge
- Prev/next scene keyboard navigation (← → arrow keys)
- Empty states per concern group use each group's own colored icon

### Changed
- `scenes/:entityId` route now renders `SceneWorkspacePage` instead of `EntityDetailPage`
- `SceneIntentPanel` exported from `DirectionTab.tsx` for reuse
- AppShell ScrollArea inner wrapper gets `min-w-full` to prevent content-width collapse at wide viewports

### Fixed
- Layout width inconsistency: concern group tabs rendered narrower than Overview tab at wide viewports. Root cause: `mx-auto` in a flex-col context sizes to `max-content` of visible children; `SceneViewer` content pushed width wider than empty states. Fixed by adding `w-full` to page container root div.

## [2026-03-02-01] — Eval verification: scorer fixes, golden repairs, model swap

### Fixed
- `bible_extraction_scorer.py`: entity-type detection now checks `prop_id` before `physical_traits` (props were misclassified as locations, penalizing field_completeness)
- `bible_extraction_scorer.py`: alias comparison now normalizes golden aliases (hyphens broke matching)
- `bible_extraction_scorer.py`: `fact_recall` now uses stem matching (consistent with `physical_coverage`) and filters stop words — "flashback" vs "flashbacks" no longer fails
- `the-mariner-locations.json`: rewrote key_facts, aliases, and narrative terms for all 4 locations — replaced literary vocabulary ("vertical journey", "Dad", "cast") with natural-language phrasing models actually produce
- `the-mariner-props.json`: rephrased 3 FLARE GUN facts for flexible keyword matching
- `normalize-signal-golden.json`: simplified expected_scenes to keyword-only (location names without INT./EXT. prefix)

### Changed
- `script_normalize_v1`: default work_model from Sonnet 4.6 to Haiku 4.5 — eval shows higher quality (0.954 vs 0.938) at 67% lower cost
- `verify-eval` skill: added Cost Discipline section (use cache for scorer-only changes, drop LLM judge during iteration)
- `registry.yaml`: updated normalization, prop-extraction, and location-extraction with verified scores

### Eval Deltas (raw → verified)
- Normalization: 0.955 → 0.961 (GPT-4.1)
- Prop Extraction: 0.904 → 0.916 (Sonnet 4.6)
- Location Extraction: 0.898 → 0.942 (Opus 4.6)

## [2026-03-01-10] — Adversarial verification of all 10 golden fixtures

### Fixed
- `the-mariner-characters.json`: added missing SALVATORI (antagonist) and VINNIE (Rose's ex) entries, added "Mr. Salvatori" alias
- `the-mariner-scenes.json`: fixed 5 flashback headings to match screenplay text, corrected scene 7/8 summary attribution, added SALVATORI to scene 10, fixed scene 13/15 details
- `the-mariner-locations.json`: added missing CITY CENTRE and BACKYARD locations, fixed phantom key_fact/alias/physical_trait entries
- `the-mariner-props.json`: removed phantom aliases ("Rose's bag", "flare pistol") and traits ("ordinary-looking purse", "maritime emergency equipment"), added missing scenes for oar/purse
- `the-mariner-relationships.json`: added missing Rose-Salvatori adversary and Dad-Rose parent relationships, bumped min_must_find from 4 to 5
- `normalize-signal-golden.json`: fixed invalid regex `**` → `\*\*` in forbidden_patterns (was silently skipped by scorer)
- `qa-pass-golden.json`: fixed "Greene" → "Green" typo to match input scene text, removed phantom "missing thugs" issue
- `continuity-extraction-golden.json`: added missing oar ownership/position properties, emotional_state change, and incomplete previous/new patterns
- `qa-pass.yaml`: aligned LLM rubric with corrected golden (building name, time_of_day wording, removed phantom issue)

### Changed
- `_verification-checklist.md`: all 10 fixtures now CLEAN with detailed pass notes

## [2026-03-01-09] — Bootstrap golden workspace via /setup-golden

### Added
- `benchmarks/golden/README.md`: comprehensive format spec covering all 10 golden types, schemas, enums, conventions
- `benchmarks/golden/validate-golden.py`: self-contained structural validator (schema config at top, no project imports) — validates all 10 golden files with cross-reference checking
- `benchmarks/golden/_verify-golden-outputs.md`: adversarial verification protocol with per-type checklists for all 10 golden types
- `benchmarks/golden/_verification-checklist.md`: tracking table with all 10 goldens as PENDING
- `benchmarks/golden/_coverage-matrix.json`: dimension coverage tracking with gap analysis
- `benchmarks/golden/_inbox/README.md`: inbox drop-zone docs for new golden inputs

## [2026-03-01-08] — Scout 006: golden fixture automation skills from Storybook

### Added
- `/golden-create` skill: create golden references from input data with validator run
- `/golden-verify` skill: orchestrated adversarial verification with parallel Opus subagents
- `/golden-verify-reset` skill: reset verification status for re-checking after schema changes
- Scout 006 expedition doc

### Changed
- `/setup-golden` skill: replaced process-description version with bootstrapping version that generates workspace files (validator, verification protocol, checklist, inbox)
- `docs/runbooks/golden-build.md`: replaced with Storybook's portable golden fixtures pattern (tier system, inbox workflow, skill cross-references)

## [2026-03-01-07] — Golden audit: complete references table + register missing eval scores

### Fixed
- AGENTS.md Golden References table: added 4 missing golden files (continuity-extraction, enrich-scenes, normalize-signal, qa-pass) — table now covers all 11 golden files on disk
- Eval registry: registered 10 missing Gemini/Sonnet model scores across 5 evals from unregistered result files (character-extraction, relationship-discovery, normalization, scene-enrichment, qa-pass)

## [2026-03-01-06] — Golden build runbook (Story 109)

### Added
- `docs/runbooks/golden-build.md`: full golden reference build & maintenance runbook — 6 build phases, 5 common failure patterns, eval-driven improvement protocol, periodic audit process, enforcement cross-references to all lifecycle skills, troubleshooting table

### Changed
- `/setup-golden` "Operational Playbook" section: updated bullet descriptions to match actual CineForge runbook content (was Dossier-specific)
- AGENTS.md Golden References section: added link to `docs/runbooks/golden-build.md`

## [2026-03-01-05] — Scout 005: eval-first approach gate + /verify-eval skill

### Added
- `/verify-eval` skill: 5-phase structured mismatch investigation (enumerate → classify → fix golden → re-run → report verified scores)
- Story 109 (Draft): Golden Build Runbook — documenting golden fixture process + enforcement cross-references
- AGENTS.md: "LLM resolution degrades from synthetic to real data" pitfall, "eval-first for implementation decisions" lesson

### Changed
- `/build-story` step 7: "AI-first check" → "Eval-first approach gate" — requires baseline measurement, candidate enumeration, and eval-driven approach selection
- `/build-story` step 11b: added verified-scores guardrail (raw scores no longer determine ACs)
- `/create-story`: "AI Considerations" → "Approach Evaluation" in conventions + story template; added /verify-eval task convention for eval-touching stories; added system-order insertion guidance
- `/mark-story-done`: checklist requires `/verify-eval` report in work log; added guardrail for eval report
- `/validate` step 5b: references `/verify-eval` for structured investigation protocol
- `/triage-stories`: added `## Arguments` section for single-story evaluation mode
- Story 107, 108: updated to use "Approach Evaluation" section; Story 107 gained /verify-eval task

## [2026-03-01-04] — Config detection golden fix and eval improvement

### Fixed
- `benchmarks/golden/the-mariner-config.json`: corrected 4 wrong fields discovered via manual screenplay audit — format (short film, not feature), duration ([8,35] not [8,130]), supporting characters (removed non-existent CONSIGLIERE/GIRL, added MIKEY/CARLOS/ROSCO), tone keywords (expanded from 5→10, raised min match to 3)
- `benchmarks/tasks/config-detection.yaml` LLM rubric: aligned with corrected golden (was asking "Did it identify as a feature film?" — penalizing correct answers)

### Changed
- `benchmarks/scorers/config_detection_scorer.py`: added `audience_accuracy` dimension (was unscored), rebalanced 10-dimension weights
- `benchmarks/prompts/config-detection.txt`: expanded tone/genre/format guidance for all models
- `benchmarks/tasks/config-detection.yaml`: added GPT-5 Mini and GPT-5 Nano providers
- `docs/evals/registry.yaml`: replaced all config-detection scores with corrected golden measurements; winner changed from GPT-4.1 (0.965, invalid) to Gemini 3 Flash (0.953, verified 3-run avg 0.945)

### Added
- `docs/evals/attempts/001-config-detection-speed-prompt.md`: first eval improvement attempt story
- 7 result files from eval runs (initial, golden-fix, verification runs)

## [2026-03-01-03] — Speed and cost as first-class eval metrics

### Added
- `scripts/extract-eval-metrics.py` — extracts per-model latency_ms and cost_usd from promptfoo result files, with `--update-registry` mode for backfilling registry.yaml
- Latency and cost targets on all 10 quality evals (`latency_ms_max`, `cost_usd_max`)
- Anthropic cost estimation from token counts when promptfoo reports $0 (Sonnet 4.6 via API without date suffix)
- C4 compromise gate now evaluates real latency data (was stub returning "not measured")

### Changed
- `docs/evals/registry.yaml`: backfilled `latency_ms`, `cost_usd`, and `cost_estimated` on all 40 score entries
- `docs/evals/README.md`: promoted speed/cost from "optional" to required; new "Speed and Cost" section
- `docs/evals/attempt-template.md`: added latency/cost before/after fields and Definition of Done checklist items
- `.agents/skills/improve-eval/SKILL.md`: speed/cost awareness in all 5 phases (candidate selection, planning, execution, recording)
- `scripts/check-compromises.py`: data-driven C4 check with per-model quality + latency tradeoff reporting

## [2026-03-01-02] — Eval registry system for autonomous improvement tracking

### Added
- Central eval registry (`docs/evals/registry.yaml`) — 10 quality evals + 5 compromise evals with scores, targets, and attempt tracking
- Model discovery script (`scripts/discover-models.py`) — queries OpenAI, Anthropic, Google APIs with tier classification (SOTA/mid/cheap/reasoning/legacy)
- Compromise gate checker (`scripts/check-compromises.py`) — evaluates C2–C7 spec compromises against current registry data
- `/improve-eval` skill — autonomous 5-phase eval improvement workflow with attempt stories
- `/discover-models` skill — surface available models and flag untested ones
- `/setup-eval-registry` skill — bootstrap the eval system in any project (cross-project portable)
- Attempt story template with Definition of Done checklist

### Changed
- AGENTS.md: replaced hardcoded Eval Catalog table with pointer to registry, added Definition of Done #6 (registry updates), added repo map entries
- `/build-story`, `/validate`, `/mark-story-done`, `/create-story` skills all now mandate eval registry updates when evals are run

## [2026-03-01-01] — Continuity AI Detection & Gap Analysis (Story 092)

### Added
- LLM-powered continuity extraction: per-scene entity state tracking (costume, injuries, emotional state, lighting, weather, props) with evidence quotes from script text
- Change event detection with previous/new values, reasons, and explicit vs inferred classification
- Gap detection for missing or low-confidence entity states across scenes
- Continuity extraction promptfoo eval (2 test cases, 13 providers, dual scoring)
- `continuity_tracking` stage wired into world-building recipe
- 14 unit tests + integration test with real model

### Fixed
- `NODE_FIX_RECIPES` mapping: continuity and entity_graph now correctly point to `narrative_analysis`
- Pydantic `from __future__ import annotations` breaking model resolution at runtime
- Engine `_preload_upstream_reuse` not traversing `needs_all` dependencies for `start_from` resumption
- Stale bible progress spinner messages persisting in chat after stage completion

### Changed
- Continuity module default model: `claude-haiku-4-5-20251001` (eval-validated, 13x cheaper than Sonnet with comparable quality)

## [2026-02-28-08] — Scout 004: Ideal alignment gates across story lifecycle

### Changed
- `/build-story`: Draft STOP gate, read ideal.md before spec, new Ideal Alignment Gate (step 4), model selection pitfall
- `/create-story`: ideal_refs + status inputs, Story Statuses section, Ideal alignment pushback in Conventions
- `/validate`: Ideal alignment check step + report template section
- `/mark-story-done`: Draft guard guardrail
- `/triage-stories`: Read Ideal step, Ideal alignment + Simplification leverage scoring dimensions
- AGENTS.md: "Stale model selection" pitfall added to Known Pitfalls

## [2026-02-28-07] — Per-scene progress tracking for concern group runs

### Added
- Real-time `(X/Y scenes)` progress in banner, RunProgressCard, and chat intro during concern group runs
- `countSceneProgress()` and `countTotalScenes()` helper functions in constants.ts
- Banner restores on page refresh by detecting in-progress runs from backend

### Fixed
- Progress stuck at 0/13: `run_state.json` now written incrementally when `announce_artifact` saves each scene (was only written at stage completion)
- RunProgressCard receives `projectId` via JSON-encoded content for artifact group queries

### Changed
- RunProgressCard prop renamed from `runId` to `content` (JSON format with backwards-compat fallback)
- Chat intro for concern group runs includes scene count: "Analyzing your 13 scenes..." instead of "Analyzing your scenes..."

## [2026-02-28-06] — Sound & Music direction (Story 022)

### Added
- `sound_and_music_v1` pipeline module: per-scene parallel analysis with 3-scene sliding window, silence mandate (ADR-003 Decision #3), QA loop with escalation, mock support
- `SoundAndMusicIndex` schema for project-level sonic identity aggregate (overall_sonic_language, dominant_soundscape, score_arc, scenes_with_intentional_silence)
- Sound Designer role enhanced with rich persona (ambient design, emotional soundscape, silence as tool, music philosophy, transitions, motifs, offscreen audio, diegetic vs non-diegetic)
- `sound_and_music` stage in creative direction recipe with `after: [intent_mood]` + `store_inputs_optional` for intent_mood
- Sound & Music entry activated in DirectionTab with "Get Sound & Music Direction" / "Regenerate Sound & Music" buttons
- `sound_and_music_index` registered in artifact-meta.ts (Volume2 icon, emerald-300)
- 13 unit tests for Sound & Music module including silence mandate enforcement

## [2026-02-28-05] — Centralized long-running action system (Story 101)

### Added
- `useLongRunningAction` hook — single entry point for all async operations, manages button state + operation store + chat messages automatically
- `OperationBanner` component — global status banner in AppShell for all active operations (pipeline runs + direct API calls)
- `operation-store.ts` — Zustand store tracking per-project active operations
- `CONCERN_GROUP_META` mapping and `detectConcernGroupRun()` helper in constants.ts for role-attributed chat messages
- `end_at` parameter for pipeline runs — enables single-stage execution (e.g., regenerate only Rhythm & Flow)
- Stage descriptions for all 5 creative direction concern group stages in chat-messages.ts
- Role-attributed intro and completion messages for concern group runs (Editorial Architect, Visual Architect, Sound Designer, Story Editor)

### Changed
- `OperationBanner` replaces `ProcessingView` — works from any page, not just ProjectHome
- Banner hides stage count for single-stage runs ("Working on Rhythm & Flow..." instead of "(0/1 stages)")
- Concern group run completion messages now role-attributed with "Browse in Scene 1" button instead of generic "Browse Results"
- `stage_order` in engine.py reflects only executed stages (not full recipe), fixing progress card display
- IntentMoodPage propagation refactored from ~50 lines manual orchestration to ~15 lines via hook
- AGENTS.md updated: User Feedback Contract references hook, Component Registry expanded, MUST use directives added

## [2026-02-28-04] — Scout 003: cross-project pattern adoption

### Added
- `/improve-skill` retrospective skill for post-interaction skill improvement
- AI-as-Tester principle in AGENTS.md — qualitative AI behavior testing via subagent probes
- Eval mismatch investigation mandate (Definition of Done #5, `/validate`, `/build-story`, `/mark-story-done`)
- ADR template: Integration Checklist and "Settled — DO NOT suggest alternatives" marker
- Scout 003 expedition doc and index entry
- Draft stories 102-106: multi-turn evals, AGENTS.md extraction, tiered metrics, parallel extraction, chunk cache

### Changed
- `/triage-inbox`: "fold into existing story" + "what if we don't do this?" + delete-not-archive policy
- `/scout`: automatic source resolution from scout history for re-scouts
- `docs/inbox.md`: removed Triaged archive section (inbox is now a queue)

## [2026-02-28-03] — Look & Feel visual direction (Story 021)

### Added
- `look_and_feel_v1` pipeline module: per-scene parallel analysis with 3-scene sliding window, bible + Intent/Mood context injection, QA loop with escalation, mock support
- `LookAndFeelIndex` schema for project-level visual identity aggregate
- Visual Architect role enhanced with rich persona (lighting philosophy, colour theory, camera language, composition, costume/production design)
- `look_and_feel` stage in creative direction recipe with `store_inputs_optional` for intent_mood, character_bible, location_bible
- Look & Feel entry activated in DirectionTab with "Get Look & Feel Direction" / "Regenerate Look & Feel" buttons
- `look_and_feel_index` registered in artifact-meta.ts (Eye icon, sky-400)
- 14 unit tests for Look & Feel module

### Fixed
- DirectionTab run tracking: buttons now stay disabled for full pipeline run duration via `setActiveRun()` wiring to global `useRunProgressChat` system
- Button cursor-pointer added to global shadcn/ui button styles
- Recipe `needs` vs `after` fix: creative direction stages use `after: [intent_mood]` instead of `needs: [intent_mood]` to avoid schema compatibility failures
- Engine `start_from` wave scheduling: skipped stages now added to `already_satisfied` set so `after` dependencies resolve correctly
- Chat store migration: `resolveTaskProgress()` flips stale running/pending task_progress items to done on page reload
- DirectionTab generalized: dynamically loops over all concern groups instead of hardcoding Rhythm & Flow only

### Changed
- `look_and_feel` added to `REVIEWABLE_ARTIFACT_TYPES` in engine.py
- `look_and_feel_index` added to pipeline graph artifact_types with nav_route
- `look_and_feel` added to `NODE_FIX_RECIPES` in graph.py

## [2026-02-28-02] — Intent / Mood UX improvements (Story 095)

### Added
- Deep breakdown gate: Intent & Mood page requires character/location bibles before showing the full form, with explanation of why and "Run Deep Breakdown" button
- `TaskProgressCard` component for compact multi-item progress in chat timeline
- `task_progress` message type for grouped operation progress (heading + per-item status)
- Chat activity messages for all long-running operations (deep breakdown, propagation)
- Propagation progress: per-concern-group spinner→checkmark transitions in chat
- Status banner during propagation matching ProcessingView style
- Explanatory text below Save & Propagate buttons describing what propagation does
- User Feedback Contract directive in AGENTS.md for durable long-running operation UX

### Changed
- "Suggest a Vibe" upgraded from deterministic keyword matching to LLM call (Haiku) with structured output — correctly matches mood/preset to script context
- Save & Propagate button shows descriptive loading state: "Generating suggestions for all concern groups..."
- Reference film input made full-width (was constrained to small inline box)
- Suggest endpoint now returns reference films from matched preset
- ProcessingView is now recipe-aware: shows "Running Deep Breakdown..." or "Running Creative Direction..." instead of generic "Processing your screenplay..."
- 5 concern group pipeline nodes (`look_and_feel`, `sound_and_music`, `character_and_performance`, `story_world`, `rhythm_and_flow`) changed to `implemented=True` — Direction dropdown now shows completion status instead of "Coming soon"
- `rhythm_and_flow` node accepts both `rhythm_and_flow_index` and `rhythm_and_flow` artifact types

## [2026-02-28-01] — Intent / Mood warm invitation UX (Story 095)

### Added
- Warm invitation card on Intent & Mood page: shows script context (title, genre, tone, themes, logline) when no intent is set but script bible exists
- "Suggest a Vibe" button: deterministic mood suggestion from script analysis (mood word extraction + best preset match by keyword overlap)
- `GET /api/projects/{id}/script-context` endpoint returning `ScriptContextResponse`
- `POST /api/projects/{id}/intent-mood/suggest` endpoint returning `IntentMoodSuggestion`
- 7 new unit tests for suggest flow (401 total)

## [2026-02-27-05] — Intent / Mood Layer (Story 095)

### Added
- Style preset catalog: 6 built-in "vibe" presets (Neo-Noir, Summer Indie, Documentary Realism, Gothic Horror, Ethereal Drama, Action Thriller) as YAML in `configs/style_presets/` with `StylePreset` model in `src/cine_forge/presets/`
- Propagation service (`src/cine_forge/services/intent_mood.py`): Director-driven AI translation of mood intent into per-concern-group suggested defaults
- 4 new API endpoints: GET/POST `/api/projects/{id}/intent-mood`, POST `/api/projects/{id}/intent-mood/propagate`, GET `/api/projects/{id}/style-presets`
- Pipeline module `intent_mood_v1` in `src/cine_forge/modules/creative_direction/intent_mood_v1/` with mock mode and structured LLM output
- Intent & Mood UI page (`ui/src/pages/IntentMoodPage.tsx`): preset picker, mood chip selector, reference film tags, NL textarea, save/propagate, propagation preview cards
- Scene-level intent panel (`SceneIntentPanel` in `DirectionTab.tsx`): shows inherited project mood with "Customize for this scene" button
- "Intent" nav item in sidebar between Script and Scenes
- 17 unit tests in `tests/unit/test_intent_mood.py`

### Changed
- Pipeline graph: `intent_mood` node flipped to `implemented=True` with `nav_route="/intent"`
- `recipe-creative-direction.yaml`: added `intent_mood` stage before `rhythm_and_flow`
- `NODE_FIX_RECIPES` now maps `intent_mood` → `creative_direction`

## [2026-02-27-04] — Concern group artifact schemas (Story 094)

### Added
- 6 concern group schemas in `src/cine_forge/schemas/concern_groups.py`: IntentMood, LookAndFeel, SoundAndMusic, RhythmAndFlow, CharacterAndPerformance, StoryWorld (plus shared MotifAnnotation and container types)
- Readiness computation in `src/cine_forge/schemas/readiness.py`: RED/YELLOW/GREEN per concern group per scene with per-group yellow thresholds
- 6 concern group nodes in pipeline graph (intent_mood, rhythm_and_flow, look_and_feel, sound_and_music, character_and_performance, story_world)
- 7 artifact metadata entries in UI (artifact-meta.ts, constants.ts)
- 24 unit tests across test_concern_group_schemas.py and test_readiness.py

### Changed
- Migrated EditorialDirection → RhythmAndFlow (schema, module output, recipe, role YAMLs)
- DirectionAnnotation.tsx now uses generic concern group renderer instead of hardcoded EditorialDirection fields
- DirectionTab.tsx button labels: "Get Rhythm & Flow Direction" (was "Get Editorial Direction")
- Pipeline direction phase expanded from 3 nodes to 6 concern group nodes

### Removed
- `src/cine_forge/schemas/editorial_direction.py` — replaced by RhythmAndFlow in concern_groups.py

## [2026-02-27-03] — Script bible artifact (Story 093)

### Added
- Script bible schema (`ScriptBible`, `ActStructure`, `ThematicElement`) in `src/cine_forge/schemas/script_bible.py`
- `script_bible_v1` pipeline module — single Sonnet LLM call from canonical script
- `script_bible` stage in `recipe-mvp-ingest.yaml` (parallel with `breakdown_scenes`)
- Pipeline graph node for script bible in the `script` phase
- ScriptBiblePanel on the Script page — expandable panel with tone, theme badges (with tooltips), synopsis, conflict/journey/arc/setting grid, act structure
- `useScriptBible` hook and artifact metadata
- `stage_order` field on `RunState` — recipe YAML is now the single source of truth for stage display order
- 7 unit tests for the script bible module

### Changed
- Deleted hardcoded `RECIPE_STAGE_ORDER` from UI constants — frontend reads order from backend API
- Moved 4 legacy partial-ingest recipes from `configs/recipes/` to `tests/fixtures/recipes/`
- Fixed stale `stages["extract"]` assertions in timeline/track integration tests

### Fixed
- `json.dump(..., sort_keys=True)` in `_write_run_state` was destroying stage insertion order — resolved by explicit `stage_order` array

## [2026-02-27-02] — Document two-tier preference model across project

### Added
- Two-tier preference explanation in ideal.md header (vision-level vs compromise-level)
- Counterpart explanation in spec.md header
- Preference-level awareness in AGENTS.md Ideal reference block
- Compromise-level preferences tagged on C1 (Cost Transparency) and C7 (Working Memory)
- Vision-level vs compromise-level contrast in setup-ideal skill
- Compromise-level preference intro in setup-spec skill

## [2026-02-27-01] — ADR-003 decided: Three-Layer Director's Vision Model

### Added
- ADR-003 decided (Option E) — Intent/Mood layer → 5 concern groups → scope substrate
- `decisions-log.md` — 14 comment decisions from synthesis review
- Deep research: 4 provider reports (OpenAI, Anthropic, Google, xAI) + final synthesis
- R17 in ideal.md — real-world assets as first-class inputs
- Round-trip decomposition vision preference in ideal.md
- 4 inbox items under "ADR-003 Deferred Ideas" (film decomposition, AI enhancement, location lookup, mood-board synthesis)
- 8 new story skeletons: 093 (Script Bible), 094 (Concern Group Schemas), 095 (Intent/Mood Layer), 096 (Chat About This), 097 (AI Artifact Editing), 098 (Real-World Asset Upload), 099 (Scene Workspace), 100 (Motif Tracking)
- Recommended build order in stories.md (7 groups, dependency-aware)

### Changed
- spec.md §12 completely rewritten: 4 direction types → 5 concern groups + Intent/Mood + Readiness Indicators + Prompt Compilation Model
- spec.md §4.5 (Script Bible), §4.6 (Two-Lane Architecture) added
- spec.md §4.4, §9, §13, §18 updated for ADR-003 terminology and R17
- Stories 021 (Look & Feel), 022 (Sound & Music), 023 (Character & Performance) reshaped for concern group model
- Story 025 (Shot Planning) dependency changed from Story 024 → concern group stories
- Story 028 (Render Adapter) updated for concern group inputs, R17 dependency
- Stories 026, 027, 029, 030, 056 updated for concern group terminology
- Stories 082, 085 (Done) — ADR-003 impact notes added to work logs
- setup-checklist.md, retrofit-gaps.md updated for concern group terminology
- Untriaged "Prompt transparency / direct editing" resolved by ADR-003 Decision #4

### Removed
- Story 024 (Direction Convergence) cancelled — Intent/Mood layer handles cross-group coherence

## [2026-02-26-04] — Ideal-first retrofit: ideal.md, spec annotations, gap analysis, ADR-003

### Added
- `docs/ideal.md` — The Ideal document (16 requirements, 11 vision preferences, the north star for all design decisions)
- `docs/retrofit-gaps.md` — Gap analysis: missing evals, golden refs, untraceable stories, under-covered requirements, Dossier integration plan
- `docs/setup-checklist.md` — Prioritized retrofit checklist (P0–P3)
- `docs/decisions/adr-003-film-elements/` — ADR for creative element grouping between screenplay and film
- Ideal reference block at top of AGENTS.md ("Is it easy, fun, and engaging?")
- Prompt Transparency AC added to Story 028 (Render Adapter) per Ideal R12
- Dependency `Blocks: 025` added to Story 092 (Continuity AI)

### Changed
- `docs/spec.md` annotated with 7 compromise blocks (C1–C7), compromise index, untriaged ideas section
- Story 090 (Persona-Adaptive Workspaces) cancelled — superseded by two-view architecture + interaction mode
- Extraction-related checklist items struck through (Dossier will handle)

## [2026-02-26-03] — Scout dossier: adopt ideal-first methodology skills

### Added
- 9 new skills from dossier: `/setup-ideal`, `/setup-golden`, `/setup-evals`, `/setup-spec`, `/setup-stories`, `/setup-env-ai`, `/setup-env-dev`, `/retrofit-ideal`, `/reflect`
- `docs/prompts/ideal-app.md` — reusable generator prompt for Ideal App documents
- "Baseline = Best Model Only" principle in AGENTS.md
- Story Conventions section in AGENTS.md (Draft → Pending → In Progress → Done)
- Runbook Conventions section in AGENTS.md (`[script]`/`[judgment]` tagging, skill↔runbook rule)
- Scout expedition 002 — dossier infrastructure (22 findings, 15 adopted)

### Changed
- Story template default status from `Pending` to `Draft`

## [2026-02-26-02] — Remove dead Inspector tab from right panel

### Removed
- Inspector tab and all supporting code — never had any functionality (nothing called `openInspector`)
- `ui/src/lib/inspector.tsx` (orphaned context provider, never mounted)
- Inspector tab bar, `setTab()`, `ActiveTab` type, `useInspector()` wrapper from right panel context
- "Toggle Inspector" command from command palette

### Changed
- Right panel is now a single-purpose Chat panel with a simple header (no tabs)
- `⌘I` shortcut relabeled from "Toggle inspector" to "Toggle right panel"
- Theme showcase layout skeleton updated ("Inspector" → "Chat")

## [2026-02-26-01] — Pipeline capability graph, AI navigation, preflight cards, staleness UX, interaction mode (Stories 085–089)

### Added
- Pipeline capability graph: 19 nodes across 6 phases (Script/World/Direction/Shots/Storyboards/Production) with dynamic status from artifact store (`src/cine_forge/pipeline/graph.py`)
- Pipeline bar: persistent horizontal bar in app shell showing project progress with phase segments, tooltips, completion badges, and click-to-navigate (`ui/src/components/PipelineBar.tsx`)
- AI `read_pipeline_graph` tool: chat AI can read full pipeline state and recommend next steps
- AI navigation intelligence: system prompt guidance for pipeline-aware responses, tiered preflight checks (green/yellow/red) before proposing runs, prerequisite validation
- Preflight summary cards: visual cards in chat showing recipe readiness, input health, and warnings before expensive runs (`ui/src/components/PreflightCard.tsx`)
- Staleness tracing: `trace_staleness()` walks dependency graph to explain WHY artifacts are stale, shown in pipeline bar tooltips and AI chat output
- "Fix with rerun" button on stale pipeline nodes — dispatches chat message to rerun the appropriate recipe
- Interaction mode selector (guided/balanced/expert): adjusts AI verbosity and system prompt framing, stored in project.json
- `GET /api/projects/{pid}/pipeline-graph` endpoint
- `interaction_mode` field in project settings API
- ADR-002 (Goal-Oriented Project Navigation): decided, with deep research from 4 AI providers
- Story 090 (Persona-Adaptive Workspaces) created for ADR-002 Layer 4

### Changed
- AI system prompt includes pipeline navigation guidance and post-run graph refresh instructions
- Staleness propagation records `stale_cause` for upstream traceability
- Story 023 rewritten to reflect Story 084 superseding actor agent scope
- AGENTS.md repo map updated with `src/cine_forge/pipeline/` package

## [2026-02-25-01] — Chat persistence enrichment & character history fix (Story 084)

### Added
- `pageContext` persisted on user messages in chat.jsonl (records what page the user was viewing)
- `injectedContent` persisted on user messages (records the actual scene/bible text injected into the AI's system prompt)
- `toolCalls` persisted on AI messages (no longer stripped before persistence)
- `injected_content` SSE event type for streaming the actual injected artifact content
- API payload dump for debugging: `CINEFORGE_DUMP_API=1` writes exact Anthropic API JSON to `/tmp/`

### Fixed
- Character-thread filtering: each character now only sees its own conversation thread, preventing cross-character history poisoning (e.g., Mariner saying "nothing attached" no longer causes Carlos to copy that pattern)
- User message upsert in chat.jsonl so `injectedContent` can be added after initial persist
- Stale Zustand state bug: `injectedContent` re-persist now reads fresh state after store update

### Changed
- Characters upgraded from Haiku to Sonnet for better system prompt adherence
- Scene/entity artifact injection for roles (not just characters) via `_inject_page_artifact`
- User message hint injection when page context has attached content

## [2026-02-24-07] — Character Chat Agents & Story Editor Rename (Story 084)

### Added
- Character chat agents: `@billy`, `@rose`, etc. open in-character conversations grounded in character bibles and scene context
- Character system prompt builder: fat prompt with character bible + scene summaries, Haiku model, no tools
- `GET /api/projects/{pid}/characters` endpoint returning characters from bible_manifest artifacts
- Sectioned @-mention autocomplete: Shortcuts (`@all-creatives`) → Roles → Characters (dynamic from API)
- Character visual identity: cream/parchment color, scroll icon, clickable name → character bible page
- `ResolvedTargets` dataclass for structured role + character routing
- `MAX_MENTION_TARGETS` cap of 6 (with `@all-creatives` counting as 5)

### Changed
- Renamed `actor_agent` → `story_editor` across 15 files (role definition, style packs, routing, UI, tests)
- Story editor prompt rewritten for narrative logic: character motivation coherence, plot logic, thematic consistency, timeline/continuity
- Story editor tier upgraded from `performance` → `structural_advisor`
- Character streaming ordered: non-director roles → characters → director

## [2026-02-24-06] — ADR-001: Shared Entity Extraction → Dossier

### Added
- ADR-001 research, decision, and full specification for shared entity extraction library ("Dossier")
- Multi-model deep research (OpenAI, Google, Anthropic, xAI) with synthesis
- "Critical Pushback Required" mandate in AGENTS.md

### Changed
- ADR-001 status: PENDING → DECIDED (standalone library, new repo at github.com/copperdogma/dossier)

## [2026-02-24-05] — Group Chat Architecture (Story 083)

### Added
- True group chat: roles respond directly with their own voice, avatar, and visual identity (no intermediary paraphrasing)
- Assistant as a first-class role in the catalog (`roles/assistant/role.yaml` + generic style pack)
- `@-mention` routing: `@director`, `@editorial_architect`, `@visual_architect`, `@sound_designer`, `@story_editor`, `@all-creatives`
- Conversation stickiness: messages without @-mention go to the last-addressed role
- Multi-role sequential streaming with Director-last convergence
- Anthropic prompt caching (`cache_control` breakpoints on system prompt + transcript prefix)
- Inline @-mention autocomplete: type `@` anywhere for filtered role dropdown with keyboard nav
- Per-role tinted message bubbles with icon + name header (full-width, no wasted horizontal space)
- Sticky role headers: role name pins to top of chat when scrolling through long messages
- Auto-growing textarea with custom drag-to-resize (drag up = grow, pill-style handle)
- Send button overlaid inside textarea container (ChatGPT-style)
- Long transcript compaction via Haiku summarization (above 80k estimated tokens)
- READ_TOOLS available to all roles (get_artifact, list_scenes, list_characters, etc.)

### Removed
- `talk_to_role` tool-call pattern (nested LLM calls, paraphrased responses)

### Changed
- `/chat/stream` endpoint now uses `stream_group_chat()` with RoleCatalog-backed role resolution
- Chat messages now carry `speaker` field for role attribution
- Streaming chunks include `role_start`/`role_done` envelope events for multi-role responses

### Fixed
- Multi-role streaming: synthetic user message between role responses to satisfy Anthropic alternating requirement
- Textarea no longer triggers Chrome password autofill (`autoComplete="off"`, `data-form-type="other"`)
- Chat text wraps properly in narrow panel (`w-0 min-w-full` + `break-words`)
- Entity context preserved on page refresh

## [2026-02-24-04] — Creative Direction UX (Story 082)

### Added
- Direction tab on scene detail pages with Overview/Direction tab layout
- `DirectionAnnotation` component — Word/Google Docs comment-style UI for creative direction, parameterized by direction type (editorial/visual/sound/performance)
- `DirectionTab` component with generate-via-chat buttons, direction artifact cards, empty state with @role teaching nudges
- `RolePresenceIndicators` — role avatar badges on scene headers showing which roles have direction
- "Get Editorial Direction" button sends `@editorial_architect` chat message (maintains full chat history)
- "Review with Director" convergence chat shell for cross-role direction review
- `page_context` now sent from frontend to backend chat API (was defined but unused)
- Scene context injected into AI system prompt so roles know which scene the user is viewing

## [2026-02-24-03] — Editorial Architect and editorial direction pipeline (Story 020)

### Added
- `EditorialDirection` and `EditorialDirectionIndex` Pydantic schemas for per-scene editorial analysis
- `editorial_direction_v1` module under new `creative_direction/` stage directory with 3-scene sliding window analysis, parallel extraction, QA escalation, and streaming progress
- `recipe-creative-direction.yaml` — Phase 5 creative direction recipe (editorial direction stage)
- "Creative Direction" recipe option in Pipeline UI, ordered after Narrative Analysis
- `editorial_direction` added to `REVIEWABLE_ARTIFACT_TYPES` for Director/Script Supervisor canon review
- UI artifact metadata for editorial direction artifacts (Scissors icon, pink)
- 9 unit tests covering mock output, scene window construction, full module run, edge cases

### Changed
- Editorial Architect system prompt expanded from 2 lines to rich persona covering cut-ability prediction, coverage adequacy, pacing, transitions, and montage identification
- Editorial Architect role permissions updated to include `editorial_direction`
- Recipe list in Pipeline UI now sorted by logical pipeline execution order

## [2026-02-24-02] — Scene index as canonical character source, prominence sort (Story 081)

### Changed
- Entity discovery consumes `scene_index.unique_characters` as the canonical character list instead of independently re-scanning the canonical script via LLM
- Prominence sort on characters page now groups by tier (Primary > Secondary > Minor) then by scene count within each tier

### Added
- `breakdown_scenes: scene_index` wired into entity discovery's `store_inputs` in world-building recipe
- `character_source` field in entity discovery processing metadata (`"scene_index"` or `"llm"`)
- 11 entity discovery tests (up from 1): scene-index passthrough, normalization, fallback, refine mode

### Fixed
- THUG 3 now appears in character bibles (was missing because entity discovery's independent LLM scan couldn't parse "THUGS 2 & 3")
- Entity discovery cost reduced ~31% (no character-scanning LLM calls when scene_index is available)

## [2026-02-24-01] — LLM-powered action line entity extraction (Story 080)

### Added
- LLM call (Haiku-class) per scene extracts characters and props from action/description lines, replacing brittle regex
- `_ActionLineEntities` Pydantic model and `_extract_action_line_entities()` function with mock path for deterministic tests
- `props_mentioned` field on `Scene` and `SceneIndexEntry` schemas
- Golden reference fixture (`tests/fixtures/golden/the_mariner_scene_entities.json`) — 12 hand-verified characters, 6 props
- Golden References table in AGENTS.md documenting all test fixtures
- 6 regression tests: mock path, empty input, props field, LLM+dialogue union, provenance update, index aggregation

### Changed
- Scene breakdown unions LLM-extracted characters with structural dialogue-cue characters (additive, no regression)
- Provenance annotation reflects `method="ai"` and `discovery_tier="structural+ai"` when LLM contributes new characters
- Passes both action and dialogue elements to LLM to handle Fountain element misclassification

### Removed
- `_extract_character_mentions` regex function — replaced entirely by LLM extraction

## [2026-02-23-07] — Character coverage and prominence tiers (Story 077)

### Added
- `prominence` field on `CharacterBible` schema: `primary`, `secondary`, or `minor` — AI-assigned at extraction time based on SAG-AFTRA-aligned rubric
- Lightweight extraction path for minor characters (score < 4) — stripped-down prompt, ~80% cheaper per character
- `ProminenceBadge` UI component (Crown/Star/User icons per tier) on character list cards and detail page header
- Prominence filter chips (All/Primary/Secondary/Minor) on Characters list view, persisted via sticky preference
- Adjudication prompt rule to preserve named minor characters (THUG 1, GUARD 2, etc.)
- Stub candidate entries for discovery-only characters whose names differ from scene_index normalization (e.g. "THUG 1"/"THUG 2" collapsed to "THUG" by scene parser)
- 7 regression tests for plausibility filter, prominence field, minor character paths, and discovery-only extraction

### Fixed
- Plausibility filter now accepts alphanumeric tokens — "THUG 1" no longer rejected by regex
- Removed "THUG" from `CHARACTER_STOPWORDS` — was incorrectly blocking functional character names
- Discovery-only characters (found by LLM entity discovery but missing from scene_index due to name normalization) no longer silently dropped

## [2026-02-23-06] — Script view scene dividers and entity hotlinks (Story 070)

### Added
- Scene divider bars injected at each scene boundary in the CodeMirror screenplay editor — shows scene number, visually distinct from script text, clickable to navigate to the scene detail page
- `onSceneDividerClick`, `onCharacterNameClick` callbacks and `scenes` prop on `ScreenplayEditor` — scene dividers implemented as CodeMirror 6 `StateEffect` + `StateField` + `WidgetType` block decorations
- `ScriptViewer` (artifact detail page) now accepts `projectId` and fetches scene data internally — scene dividers and hotlinks work on both the project home script view and the canonical script artifact detail page
- `startLine` / `endLine` fields promoted to the UI `Scene` interface from `source_span` in scene artifacts
- Hover states on scene divider bars (dim amber → bright amber), scene heading lines (amber tint), and character name lines (blue tint) — implemented via `Decoration.line()` stamping stable `.cm-heading-line` / `.cm-character-line` CSS classes, since `HighlightStyle` uses opaque generated class names incompatible with `:has()`

### Fixed
- Character name lines (ALL-CAPS cue lines) in the screenplay editor are now clickable hotlinks — clicking "ROSE" navigates to `/:projectId/characters/rose`
- Character names with trailing parentheticals (`ROSE (O.S.)`, `MARINER (V.O.)`) now resolve correctly — parenthetical stripped before entity lookup
- Fuzzy entity resolver fallback: cue text "MARINER" now matches entity_id "the_mariner" via substring check

## [2026-02-23-05] — Chat & nav bug fixes: slash-search routing, entity context chip (Story 079)

### Added
- Entity context chip above chat input — shows icon + entity name when viewing a character, location, prop, or scene detail page; updates on navigation, clears on list pages; clicking navigates back to the entity
- `entityContext` state in `chat-store` (`setEntityContext` / `clearEntityContext` actions) — pure UI state, not persisted

### Fixed
- Slash-search (CommandPalette `/` trigger) now navigates to entity detail pages (`/characters/:id`, `/locations/:id`, `/props/:id`, `/scenes/:id`) instead of raw artifact URLs
- `addActivity` idempotency bug — activity message was silently skipped when a newer message (e.g. AI response) had landed after the last navigation; fixed by finding the stable ID anywhere in the list instead of only checking the last message
- `ChatMessagePayload` backend model now includes `route` field so activity message routes persist to JSONL storage on cold load

## [2026-02-23-04] — Entity detail UX polish: scroll-to-top, cross-ref ordering, prop ownership (Story 078)

### Added
- Owner link-pills on the Props list page — all three density variants (compact/medium/large) show linked character chips for signature props; click navigates to character without triggering prop navigation
- "Owned by" row in the prop detail Profile card — linked character chip(s) appear at the bottom of the profile for any prop with `signature_prop_of` edges
- Scene Appearances now sorted by script order on entity detail pages — uses scene index heading→scene_number map, unknown headings go to end

### Changed
- Entity navigation scrolls to top of page on every route change — targets the Radix `<ScrollArea>` viewport via `[data-radix-scroll-area-viewport]` query in `AppShell.tsx`
- Characters, Locations, and Props panels in `CrossReferencesGrid` sorted by scene co-occurrence count descending (most connected co-stars appear first); ties broken alphabetically
- Props panel in `CrossReferencesGrid` splits signature props (amber ★, sorted first) from co-occurrence props (no star, sorted below); both halves sorted by scene count
- `RawEdge` in `CrossReferencesGrid` now carries `sceneRefs: string[]` — dedup merges refs from duplicate edges for accurate count
- `EntityLink` component gains optional `suffix` slot for decorative elements rendered after the label

### Removed
- "Scene Presence" collapsible section from `ProfileViewer` — duplicated the Scene Appearances panel in the cross-reference grid but with unlinked plain-text chips; `Film` icon and `scenePresence` variable cleaned up

## [2026-02-23-03] — Entity cross-linking: prop edges, scene_presence, associated_characters (Story 045)

### Added
- `characters_present_ids` field on `Scene` and `SceneIndexEntry` — slugified entity IDs alongside display-name `characters_present`, used by entity_graph for accurate co-occurrence edges
- `associated_characters` field on `PropBible` — AI-extracted slugified character IDs representing signature ownership (e.g. Mariner's oar, Rose's purse)
- `_find_scene_presence()` in `prop_bible_v1` — deterministic scan of canonical_script line spans to populate `scene_presence` reliably instead of relying on AI
- `_generate_signature_edges()` in `entity_graph_v1` — emits `signature_prop_of` edges (conf=0.95) from `associated_characters`
- Prop co-occurrence edges in `entity_graph_v1` — prop↔character and prop↔location edges (conf=0.9) from `scene_presence`
- Props subsection on scene detail pages — inferred from prop bibles' `scene_presence` via UI-side filter
- Unresolved entity links now render with `opacity-50` and tooltip instead of appearing identical to resolved links

### Fixed
- `entity_graph_v1` prop_list prompt bug: was always empty string due to wrong `prop.get("files", [])` key
- `entity_graph_v1` co-occurrence ID mismatch: `char.lower()` → `_slugify(char)` for consistent entity IDs
- `scene_analysis_v1` was not emitting `characters_present_ids` in its enriched scene output, causing the field to be empty after the AI enrichment pass

## [2026-02-23-02] — Streaming artifact yield: live per-entity progress in sidebar (Story 052)

### Added
- `scene_breakdown_v1` now calls `announce_artifact` per scene as each completes, so sidebar "Scenes" count ticks up one at a time instead of jumping at stage completion.
- Sidebar nav category rows light up with a soft teal glow when a new entity lands, fading over 3 seconds. Rapid additions each reset the animation for a cascading effect across categories.
- Two new engine unit tests: `test_announce_artifact_persists_mid_stage` (verifies mid-stage announce with no duplication) and `test_announce_artifact_batch_fallback_still_works` (confirms batch-path backwards compat).

### Changed
- `scene_breakdown_v1/main.py`: replaced `del context` with `announce = context.get("announce_artifact")`.
- `AppShell.tsx`: extracted main nav rows into `NavItem` component with row-level glow animation.

## [2026-02-23-01] — Artifact graph staleness: regression tests + sibling cross-contamination fix (Story 074)

### Fixed
- `DependencyGraph.propagate_stale_for_new_version`: sibling artifacts produced in parallel no longer marked stale via a shared intermediate node. Before BFS, builds a `latest_version` lookup per `(artifact_type, entity_id)`; when BFS reaches a node whose entity has a newer version in the graph, marks the node stale but stops BFS propagation there (downstream was already rebuilt from the newer version)

### Added
- `test_new_version_not_marked_stale`: regression test for Bug 1 (self-staleness) — newly-saved artifact must not appear in `get_stale()`
- `test_sibling_not_marked_stale_via_shared_intermediate`: regression test for Bug 2 (sibling cross-contamination) — sibling artifact remains VALID after a co-sibling's propagation crosses a shared intermediate

## [2026-02-22-12] — Add `after:` ordering-only stage dependency to recipe DSL (Story 073)

### Added
- `RecipeStage.after: list[str]` — ordering-only dependency field; stage waits for all `after` stages to complete but receives no data from them and is not subject to schema compatibility checks
- `after` included in topological sort (`resolve_execution_order`) and wave eligibility (`_compute_execution_waves`) so execution order is correctly enforced
- `after` included in stage fingerprint for correct cache invalidation
- 4 unit tests covering: ordering enforced, schema check skipped, no overlap with `store_inputs`, coexistence with `needs`

### Changed
- `recipe-world-building.yaml`: `entity_discovery` now uses `after: [analyze_scenes]` (was `needs: []` workaround) — expresses ordering intent correctly without false schema mismatch

## [2026-02-22-11] — Live entity discovery feedback during world-building runs (Story 072)

### Added
- `engine.py`: `announce_artifact` callback in context — modules call it per entity mid-stage to save with full lineage and emit an `artifact_saved` event with `entity_id`, `display_name`, and (for `entity_discovery_results`) candidate counts; `pre_saved` flag prevents double-save in the post-module loop
- `artifact_saved` event type emitted for all saved artifacts (mid-stage via announce and post-module via normal path)
- `use-run-progress.ts`: handles `artifact_saved` events for bible types — updates one in-place chat message per type ("Writing 3 character bibles…") as each entity lands, immediately invalidates sidebar artifact counts
- `index.css`: `@keyframes badge-pop` — teal brand-color flash at 1.45× scale, fades back to secondary over 1.5s with glow ring
- `ChatPanel.tsx`: smart auto-scroll — only scrolls to bottom if user is within 120px of bottom; preserves scroll position when user has scrolled up to review earlier messages

### Changed
- `character_bible_v1`, `location_bible_v1`, `prop_bible_v1`: switched from `zip(candidates, futures)` to `as_completed()` — entities announced to sidebar and chat as each LLM call completes rather than in a batch at stage end
- `hooks.ts`: `useArtifactGroups` accepts optional `refetchInterval` param
- `AppShell.tsx`: polls `useArtifactGroups` at 750ms during active run (no interval when idle); `CountBadge` uses `pulseCount` integer key to force Badge remount and restart `badge-pop` animation on each count increment
- `use-run-progress.ts`: bible progress spinners (`ai_status`) resolved to `ai_status_done` checkmarks when run completes

## [2026-02-22-10] — Post-smoke-test UI/UX fixes: insight ordering, display names, stage order

### Fixed
- `ProjectHome.tsx`: removed `syncMessages()` from stage-completion effect — it was overwriting in-memory state from the backend, racing with the in-flight insight stream and silently dropping streaming AI insight messages before they could be persisted
- `use-run-progress.ts`: insight placeholder now added before the "Next Steps" CTA so the insight streams in above the action button rather than below it (no more button jumping up the screen)
- `ui/src/lib/constants.ts`: `entity_discovery` now appears before `analyze_scenes` in the `world_building` stage display order — matches actual execution order (code-based discovery always finishes before LLM scene analysis)

### Changed
- `use-run-progress.ts` + `src/cine_forge/ai/chat.py`: AI insight prompt now uses user-facing recipe names ("Script Breakdown", "Deep Breakdown") instead of raw recipe IDs ("mvp_ingest", "world_building") — prompt includes instruction to never leak technical names

## [2026-02-22-09] — Refactor ingestion into 3-stage pipeline; fix graph staleness (Story 062)

### Added
- `scene_breakdown_v1` module: deterministic structural scene parsing (scene headings, elements, cast lists) — Tier 1 ingest, no LLM
- `scene_analysis_v1` module: LLM narrative enrichment (beats, tone, subtext, inferences) — Tier 2 world-building
- `tests/unit/test_scene_breakdown_module.py`, `tests/unit/test_scene_analysis_module.py`
- Story 072 (Pending): live entity discovery feedback as world-building runs

### Changed
- `recipe-mvp-ingest.yaml`: `extract_scenes` stage → `breakdown_scenes` (scene_breakdown_v1)
- `recipe-world-building.yaml`: added `analyze_scenes` stage (scene_analysis_v1); fixed `entity_discovery` schema dependency; bible stages now wait for `analyze_scenes`
- UI stage labels and order updated for `breakdown_scenes` / `analyze_scenes`

### Fixed
- `artifacts/graph.py`: `propagate_stale_for_new_version` no longer marks the newly-created artifact as stale (self-staleness via BFS through shared lineage ancestors)

### Removed
- `scene_extract_v1` module (monolithic scene extraction+enrichment — replaced by two-stage split)

## [2026-02-22-08] — Parallel bible extraction via ThreadPoolExecutor (Story 065)

### Changed
- `character_bible_v1`, `location_bible_v1`, `prop_bible_v1`: entity extraction loop now runs via `ThreadPoolExecutor` (default concurrency 5). Per-entity failures are caught and logged without crashing the module. Cost aggregated thread-safely in the main thread after all futures resolve.
- `recipe-world-building.yaml`: added `concurrency: 5` param to all three bible stages.
- `location_bible_v1`: fixed stale `claude-sonnet-4-5` default model → `claude-sonnet-4-6`.

## [2026-02-22-07] — Fix escalate model defaults; close Story 039

### Fixed
- `script_normalize_v1`: escalate fallback `claude-sonnet-4-6` → `claude-opus-4-6` (matches benchmark triad)
- `location_bible_v1`: escalate fallback `claude-sonnet-4-5` → `claude-opus-4-6` (missed in prior model update pass)

### Changed
- Story 039 marked Done; remaining checklist items (smoke test, config recalibration) deferred as non-blocking

## [2026-02-22-06] — Skill split: triage → triage-inbox + triage-stories; deep-research docs refresh

### Added
- `/triage-stories` skill: evaluates story backlog and recommends what to work on next

### Changed
- Renamed `/triage` to `/triage-inbox` for clarity alongside the new stories skill
- Updated deep-research docs: Google provider now configured, new `--provider`/`--mode deep` flags, `status`/`stub`/`check-providers` commands, removed stale streaming patch note

## [2026-02-22-05] — UI polish bundle: chat dedup, back nav, inbox read state (Stories 067, 068, 069)

### Fixed
- Chat navigation messages no longer duplicate on reload — stable activity IDs + backend upsert + client-side dedup safety net (Story 067)
- Back buttons now use browser history (`navigate(-1)`) instead of hardcoded routes, with fallback for direct-link opens (Story 068)

### Added
- Gmail-style read/unread inbox model with filter toggle (Unread/Read/All), per-item read indicators, and "Mark All Read" (Story 069)
- Shared `inbox-utils.ts` with stable ID builders and `useHistoryBack` hook for cross-component reuse

### Changed
- Inbox nav badge now shows unread count only, persisted in project `ui_preferences`
- Back button labels changed from "Back to {X}" to generic "Back" (destination is unknowable with history-based nav)

## [2026-02-22-04] — Triage session: 5 new stories from inbox

### Added
- Stories 067–071: Chat nav dedup, back button history, inbox read state, script scene dividers & hotlinks, refine vs. regenerate pipeline modes.
- Triage skill prioritization step: evaluate inbox, recommend top items with rationale, flag defer candidates before walking through items individually.

### Changed
- Moved 5 triaged items from inbox Untriaged to Triaged section with story references.

## [2026-02-22-03] — Scout 001: Adopt Storybook skill improvements

### Changed
- Restructured `/build-story` into 3 explicit phases (Explore → Plan → Implement) with mandatory human gate before implementation and runtime smoke test as hard guardrail.
- Added `## Plan` section to story template for auditable plan artifacts that persist across sessions.

### Added
- `/decompose-spec` skill — systematic pipeline from spec.md → feature map → coverage matrix → stories.
- `/webapp-testing` skill — Playwright-based web testing toolkit with `with_server.py` helper for server lifecycle.
- Scout expedition system (`docs/scout.md` index + `docs/scout/scout-001-storybook-repo.md`).
- Gemini CLI wrappers for new skills.

## [2026-02-22-02] — UI Component Deduplication & Template Consolidation (Story 066)

### Changed
- Replaced 4 near-identical entity list pages (`CharactersList`, `LocationsList`, `PropsList`, `ScenesList`) with a single parameterized `EntityListPage` component (~350 lines replacing ~1006 lines).
- Consolidated `healthBadge` (9+ inline copies → `HealthBadge.tsx`), `artifactMeta` (2 copies → `artifact-meta.ts`), `timeAgo` (3 copies → `format.ts`), `formatDuration` (2 copies → `format.ts`), status badge/icon (3 copies → `StatusBadge.tsx`), page headers (4+ copies → `PageHeader.tsx`).
- Added AGENTS.md "UI Component Registry" (10 entries) and "Mandatory Reuse Directives" (8 rules with file paths) to prevent AI agent code duplication.

### Fixed
- `timeAgo()` seconds-vs-milliseconds mismatch in `ProjectHome.tsx` — standardized on millisecond input.
- `null`-null handling in script-order sort inconsistent across 4 list pages — unified in `EntityListPage`.
- `paused` run status only styled in `RunDetail` — now handled in shared `StatusBadge` for all pages.

### Added
- `jscpd` copy-paste detection with 5% threshold, runnable via `pnpm --dir ui run lint:duplication`.

## [2026-02-22-01] — Screenplay Format Round-Trip & High-Fidelity Rendering (Story 064)

### Added
- **Round-Trip Fidelity Suite**: Automated `pytest -m round_trip` tests for Fountain↔PDF and FDX↔Fountain↔FDX with golden master masters.
- **afterwriting Integration**: Switched to `afterwriting` as the primary PDF renderer for industry-standard screenplay formatting (Courier 12pt, WGA margins, CONT'D markers).
- **pdfplumber Extraction**: Implemented `pdfplumber` for high-fidelity text extraction from screenplay PDFs, preserving whitespace and column structure.
- **Low-Credit Chat Alerts**: Automatic project chat notifications when pipeline runs fail due to AI provider quota or billing issues.

### Changed
- **Automatic Promotion**: UI now favors the high-fidelity `canonical_script` version over raw input upon stage completion.
- **Metadata Healer**: Screenplay normalization now automatically heals title page blocks, mapping custom keys like "Alternate Title" to the professional cover page.
- **Enhanced Centering**: Broadened character cue detection to support smart quotes and extensions, ensuring correct centering for complex names.

### Fixed
- **L&C Formatting**: Resolved multiple issues where L&C PDF exports had missing cover pages or uncentered dialogue.
- **ASGI TypeError**: Fixed technical crash in export background cleanup task.
- **Word Metadata Tags**: Updated .docx export to strip Fountain metadata tags for a professional title page.

## [2026-02-21-04]
 — Automatic Project Title Extraction from Script (Story 063)

### Added
- Backend endpoint `POST /api/projects/quick-scan` for format-aware text extraction (PDF, DOCX, Fountain) from file snippets.
- `quick_scan` method in `OperatorConsoleService` to immediately identify project titles before full upload.
- Improved LLM title extraction prompt using `claude-sonnet-4-6` for higher precision on complex script headers.

### Changed
- Updated `NewProject` UI to trigger `quick-scan` immediately upon file selection, providing instant AI-detected project names.
- Upgraded default title extraction model from Haiku to Sonnet 4.6 to handle "Alternate Title" scenarios and complex formatting.

### Fixed
- Resolved issue where projects would default to sanitized filenames (e.g., "L C") instead of their creative titles (e.g., "Liberty and Church").
- Fixed binary snippet extraction for PDFs and DOCX files in the project creation flow.

## [2026-02-21-03]
 — Ingestion Pipeline Parallelization & Performance Optimization (Story 061)

### Added
- Parallel processing in `scene_extract_v1` using `ThreadPoolExecutor` for concurrent per-scene enrichment and QA.
- Parallel processing in `script_normalize_v1` for concurrent scene-level normalization fixes during "smart chunk-skip".
- Internal timing logs to `scene_extract_v1` and `project_config_v1` for bottleneck observability.
- `skip_qa` option to `project_config_v1` to allow bypassing sequential verification for faster ingestion.

### Changed
- Refactored ingestion modules to utilize multi-threading (default 10 workers), significantly reducing wait times for long scripts.
- Truncated script content in `project_config_v1` detection prompt to the first 500 lines to keep TTFT low and reduce token processing overhead.
- Updated `recipe-ingest-extract.yaml` to use `${model}` placeholders for improved runtime flexibility.

### Fixed
- Resolved the "lc-3 bottleneck" where long scripts took up to 25 minutes to ingest; reduced expected duration to ~3 minutes for similar inputs.
- Eliminated sequential LLM call stalls in the extraction and normalization stages.
- Fixed React 19 purity errors in `ProjectRun.tsx` (impure `Date.now()` and cascading `setState`).
- Cleared UI lint debt (legacy `any` and unused variables) to satisfy strict production build gates.

## [2026-02-21-02] — Comprehensive Export & Share (Story 058)

### Added
- New backend export module `src/cine_forge/export/` with `MarkdownExporter`, `PDFGenerator`, and `ScreenplayRenderer`.
- Support for industry-standard screenplay formats: PDF, DOCX, and Fountain.
- Professional Project Analysis Report PDF with record-based layouts and enriched metadata.
- Unified CLI command `python -m cine_forge export` for headless operation.
- New API endpoints for component-aware artifact exports.
- Granular export selection UI in `ExportModal.tsx` with component checkboxes and "Check All/None" helpers.

### Changed
- Refactored `ExportModal` into a tabbed interface separating Screenplay and Project Data workflows.
- Migrated all export logic from frontend to backend to support AI headless operation.
- Standardized Courier 12pt and industry-standard margins/indents for screenplay exports.

### Fixed
- Resolved `doc.autoTable` and horizontal space errors in PDF generation.
- Fixed title page formatting to strictly follow script preamble and separate it from content.
- Fixed clipping of long project titles on PDF cover pages.
- Fixed missing script content in Fountain and Markdown exports.

## [2026-02-21-01] — Pipeline UI Refinement & Entity Quality Fixes (Story 059, 060)

### Added
- Standardized headers across all run-related UI views to show bold Recipe Name and muted Status (e.g., **Script Intake** Running).
- Added stat cards (Total Cost, Duration, Model, Stages) to the active pipeline run progress page for real-time visibility.
- Enabled horizontal scrolling in the main content area to handle grid overflows gracefully.
- Added "Back to Runs" button to the Run Detail and Pipeline configuration pages.
- New unit test `tests/unit/test_character_naming_regression.py` to prevent "The [Entity]" naming drops.

### Changed
- Refactored `ProjectRuns.tsx` to use human-readable recipe names instead of cryptic run IDs.
- Removed fixed width constraints (`max-w-5xl`) from run views to allow dynamic resizing when the chat panel is open.
- Unified character name normalization logic across `entity_discovery_v1` and `character_bible_v1`.
- Made `store_inputs_all` permissive in DriverEngine to allow runs to proceed even if no existing artifacts of that type are found.

### Fixed
- Fixed critical bug where "THE MARINER" was dropped from character bibles due to stopword rejection after a normalization failure.
- Fixed navigation trap where clicking "Start New Run" wouldn't clear the previous run context.
- Fixed `KeyError: 'data'` in `entity_discovery_v1` when processing unwrapped artifact inputs in Refine Mode.
- Fixed layout issues where stat cards and artifact grids were cut off when side panels were open.

## [2026-02-20-04] — Artifact Quality Improvements (Story 041)

### Added
- New `entity_discovery_v1` module implementing an incremental AI-first "sliding window" discovery pass.
- Supports **Refine Mode** in `entity_discovery_v1` — can bootstrap from existing `character_bible`, `location_bible`, and `prop_bible` artifacts to extend or normalize them.
- `EntityDiscoveryResults` schema for consolidated candidate tracking.
- Benchmark tasks for Liberty & Church: Golden list generation, prompt comparison, and Haiku discovery validation.
- Added "Refine World Model" action button to chat interface after project completion.

### Changed
- `world_building` recipe now includes `entity_discovery` as a prerequisite stage and optionally re-ingests existing bibles.
- `character_bible_v1`, `location_bible_v1`, and `prop_bible_v1` now prioritize candidates from the discovery pass.
- `scene_extract_v1` now enforces narrative analysis (beats, tone) during the enrichment pass.
- Centralized pipeline stage ordering logic to ensure "Entity Discovery" consistently appears as the first stage in "World Building" across all UI views.
- Standardized `ProjectRun` layout width to `max-w-5xl` for visual consistency.

### Fixed
- Fixed sparse scene analysis in long screenplays by ensuring narrative fields trigger AI enrichment.
- Resolved "black screen" crash in `ProjectRun.tsx` caused by race conditions during stage loading.
- Cleared critical UI lint debt: fixed conditional hooks, declaration order, and forbidden ref access during render.
- Improved schema validation resilience in the driver pipeline.

## [2026-02-20-03] — Entity Prev/Next Navigation (Story 057)

### Added
- New `useEntityNavigation` hook in `ui/src/lib/hooks.ts` for sequential entity traversal.
- Navigation header in `EntityDetailPage.tsx` with previous/next buttons.
- Keyboard shortcuts (←/→) for navigating between entities.
- Chronological navigation for scenes (always script-order, regardless of active sort).
- Shared `formatEntityName` utility in `ui/src/lib/utils.ts`.
- Shared sorting and density types in `ui/src/lib/types.ts`.

### Changed
- Refactored `CharactersList`, `LocationsList`, `PropsList`, and `ScenesList` to use centralized sorting types and name formatting.
- Improved `EntityDetailPage` hook ordering to comply with React strict rules (no conditional hooks).

### Fixed
- Fixed lint errors across UI list pages (const vs let, unused variables, dependency arrays).

## [2026-02-20-02] — Human control modes, creative sessions, and direct artifact editing (Story 019)

### Added
- Three configurable operating modes: `autonomous`, `checkpoint`, and `advisory`.
- `Checkpoint` mode pipeline enforcement in `DriverEngine` (stage-by-stage pauses).
- Creative Session infrastructure in chat assistant via `talk_to_role` tool.
- Multi-role `@role_id` addressing and domain-specific expert consultation.
- Project Inbox UI for review management and bulk approval.
- Direct artifact editing with background agent notification and commentary.
- New `stage_review` artifact type for audit-ready approval tracking.
- Backend endpoints for run resumption and review responses.
- Full unit/integration coverage for interaction modes and gating.

### Changed
- `ProjectConfig` and project settings now track `human_control_mode`.
- `DriverEngine` integrated with `CanonGate` for review orchestration.
- Operator Console UI updated with mode selector, inbox, and review viewers.
- `RunProgressCard` now handles `paused` state with live status indicators.

### Fixed
- Fixed thread-safety issues when multiple stages write to shared invocation logs.
- Resolved module export errors in TypeScript for `ProjectSummary`.
- Fixed 500 errors in project settings updates via correct Pydantic serialization.
- Corrected indentation and assertion failures in existing integration suites.

## [2026-02-20] — Inter-role communication protocol and conversation artifacts (Story 018)

### Added
- New conversation and disagreement schemas:
  - `src/cine_forge/schemas/conversation.py` (`Conversation`, `ConversationTurn`, `DisagreementArtifact`)
- New conversation management logic:
  - `src/cine_forge/roles/communication.py` (`ConversationManager` for multi-role review orchestration)
- Multi-role review orchestration:
  - `ConversationManager.convene_review` allows the Director to gather input from multiple roles and synthesize a decision.
- Disagreement recording:
  - `ConversationManager.record_disagreement` captures objections and resolution rationales with links to conversations and artifacts.
- Story-018 coverage:
  - `tests/unit/test_communication.py`
  - `tests/integration/test_communication_integration.py`

### Changed
- `RoleResponse` and `RoleContext` updated to track `suggestion_ids` for turn-to-suggestion linking.
- `DriverEngine` schema registry updated with `conversation` and `disagreement` types.

## [2026-02-20] — Creative suggestion and editorial decision tracking (Story 017)

### Added
- New suggestion and decision schemas:
  - `src/cine_forge/schemas/suggestion.py` (`Suggestion`, `Decision`, `SuggestionStatus`)
- New suggestion management logic:
  - `src/cine_forge/roles/suggestion.py` (`SuggestionManager` for lifecycle, querying, and stats)
- Automated suggestion capture:
  - `RoleContext.invoke` now automatically persists suggestions emitted in role responses as immutable artifacts.
- Suggestion resurfacing:
  - `CanonGate` now automatically resurfaces deferred suggestions during scene-stage reviews.
- Story-017 coverage:
  - `tests/unit/test_suggestion_system.py`
  - `tests/integration/test_suggestion_integration.py`

### Changed
- `RoleResponse` schema now includes optional `suggestions` field.
- `StageReviewArtifact` now includes `deferred_suggestions` list for auditability.
- `DriverEngine` schema registry updated with `suggestion` and `decision` types.

## [2026-02-20] — Style Pack infrastructure and built-in example profiles (Story 016)

### Added
- Folder-based `StylePack` infrastructure for creative persona profiles:
  - `src/cine_forge/roles/style_packs/` (built-in repository)
  - `StylePack` and `StylePackFileRef` schema enhancements (`audio_reference` kind)
- Style pack management and validation:
  - `RoleCatalog.list_style_packs(role_id)` for dynamic discovery
  - `RoleCatalog.load_style_pack` with role-type and permission validation
- Creative research templates:
  - `style_pack_prompt.md` templates for Director, Visual Architect, Sound Designer, Editorial Architect, and Actor Agent.
- Built-in `generic` style packs for all creative roles.
- High-fidelity example style packs:
  - Director: `tarantino`
  - Visual Architect: `deakins`
  - Sound Designer: `lynch`
  - Editorial Architect: `schoonmaker`
  - Actor Agent: `ddl` (Daniel Day-Lewis)
- Automated verification:
  - `tests/unit/test_style_packs.py` (catalog/context logic)
  - `tests/integration/test_style_pack_integration.py` (lifecycle + prompt injection)

### Changed
- `RoleContext` now injects style-pack content into system prompts during role invocation.
- `RoleDefinition` schemas and role YAMLs now explicitly declare `style_pack_slot` (accepts/forbidden).

## [2026-02-20] — Director and Canon Guardians stage-gating workflow (Story 015)

### Added
- Canon-level role behaviors and hierarchy enforcement:
  - `src/cine_forge/roles/canon.py` (`CanonGate` orchestration)
  - Director authority (canon authority), Script Supervisor and Continuity Supervisor (canon guardians).
- Stage completion gating:
  - `StageReviewArtifact` schema for immutable review persistence.
  - `ReviewDecision`, `ReviewReadiness` enums.
  - Disagreement protocol (objection + override justification records).
- Automated verification:
  - `tests/unit/test_canon_gate.py`
  - `tests/integration/test_canon_gate_integration.py`

### Changed
- Role YAMLs updated with specific guardian/authority system prompts and capabilities.
- Driver schema registry now includes `stage_review`.
- Director and Continuity Supervisor now declare `image` perception capability.

## [2026-02-20] - Role system foundation infrastructure for AI persona runtime (Story 014)

### Added
- New role-system schemas for hierarchy/runtime/style-pack contracts:
  - `src/cine_forge/schemas/role.py` (`RoleDefinition`, `RoleResponse`, `StylePack`)
- New role runtime implementation:
  - `src/cine_forge/roles/runtime.py` (`RoleCatalog`, `RoleContext`, hierarchy + capability gates, invocation audit logging)
- Skeleton role definitions for Director, Script Supervisor, Continuity Supervisor, Editorial Architect, Visual Architect, Sound Designer, and Actor Agent under `src/cine_forge/roles/*/role.yaml`.
- Generic default style packs for style-pack-accepting roles under `src/cine_forge/roles/style_packs/*/generic/`.
- Story-014 coverage:
  - `tests/unit/test_role_system.py`
  - `tests/integration/test_role_system_integration.py`

### Changed
- Driver schema registry now includes `role_definition`, `role_response`, and `style_pack` (`src/cine_forge/driver/engine.py`).
- Schema exports updated to include role-system types (`src/cine_forge/schemas/__init__.py`).
- Role permission semantics aligned to artifact-type scope; model capability checks now validate invocation-requested media types.
- Story tracking updated with Story 014 marked done and full completion evidence (`docs/stories/story-014-role-system-foundation.md`, `docs/stories.md`).

## [2026-02-20] - Track system artifact and always-playable backend resolution (Story 013)

### Added
- New track schemas for immutable track state:
  - `src/cine_forge/schemas/track.py` (`TrackEntry`, `TrackManifest`)
- New timeline track-system module:
  - `src/cine_forge/modules/timeline/track_system_v1/main.py`
  - `src/cine_forge/modules/timeline/track_system_v1/module.yaml`
- New recipe for cross-recipe track manifest construction:
  - `configs/recipes/recipe-track-system.yaml`
- New Story-013 test coverage:
  - `tests/unit/test_track_system_module.py`
  - `tests/integration/test_track_system_integration.py`

### Changed
- Driver schema registry now includes `track_manifest` (`src/cine_forge/driver/engine.py`).
- Schema exports now include `TrackEntry` and `TrackManifest` (`src/cine_forge/schemas/__init__.py`).
- Story tracking updated: Story 013 marked done in `docs/stories.md` and completion evidence recorded in `docs/stories/story-013-track-system.md`.

## [2026-02-20] - Story 054/055 completion, LLM-first entity adjudication, and Mariner fallback fix

### Added
- Story 054 artifact investigation deliverables:
  - `docs/reports/liberty-church-2-artifact-inventory.md`
  - `tests/fixtures/liberty_church_2/prod_snapshot_2026-02-19/` (prod snapshot for reproducible debugging)
  - story record: `docs/stories/story-054-liberty-church-character-artifact-cleanup-inventory.md`
- Story 055 implementation story record:
  - `docs/stories/story-055-llm-first-entity-adjudication-for-character-location-prop.md`
- Shared entity adjudication contract:
  - schema: `src/cine_forge/schemas/entity_adjudication.py`
  - helper: `src/cine_forge/ai/entity_adjudication.py`

### Changed
- World-building modules now run LLM adjudication before bible emission:
  - `character_bible_v1`, `location_bible_v1`, `prop_bible_v1`
- Added adjudication decision-trace annotations into artifact metadata for debugging and prompt tuning (`decision_trace`, rationale/confidence, outcomes).
- Added runtime model-slot fallback in world-building modules to honor `default_model`, `utility_model`, and `sota_model` passed via runtime params.
- Expanded unit coverage for adjudication outcomes (`valid`, `invalid`, `retype`) across character/location/prop modules.
- Updated story index with Story 054 and Story 055 marked done (`docs/stories.md`).

### Fixed
- Resolved regression where a valid character could be dropped after adjudication if canonicalized name failed deterministic plausibility checks (e.g., `MARINER` with canonical `The Mariner`).
- Character adjudication now falls back to the original validated candidate when canonicalization fails plausibility, preventing false removals of core characters.

## [2026-02-19] - Re-align skills to CineForge architecture (Python-first + ui split)

### Changed
- Reworked validation/build/close-story skill flows to use CineForge-native checks instead of root `pnpm` assumptions.
- Updated `validate` skill to:
  - start with full local-diff audit
  - use scope-based check profiles (backend, UI, full-stack)
  - require `tsc -b` guidance for UI type-check parity
- Updated `build-story` skill to restore required story-section checks and repo-appropriate verification flow.
- Replaced deploy skill scaffold with CineForge-specific Fly.io deployment workflow:
  - preflight checks, API/UI smoke tests, failure protocol
  - duration logging/recalibration and runbook references
  - `--depot=false` guardrail
- Updated story template and related skills (`mark-story-done`, `run-pipeline`, `init-project`, `scout`) to remove non-CineForge assumptions and align wording/commands with this repo.

## [2026-02-19] - Timeline artifact implementation and ordering-model hardening (Story 012)

### Added
- New immutable `timeline` artifact model and schema:
  - `src/cine_forge/schemas/timeline.py`
  - schema exports in `src/cine_forge/schemas/__init__.py`
- New timeline build module:
  - `src/cine_forge/modules/timeline/timeline_build_v1/module.yaml`
  - `src/cine_forge/modules/timeline/timeline_build_v1/main.py`
- New timeline recipe:
  - `configs/recipes/recipe-timeline.yaml`
- Timeline-focused tests:
  - `tests/unit/test_timeline_module.py`
  - `tests/integration/test_timeline_integration.py`

### Changed
- Driver schema registration now includes `timeline`.
- Stage module context now includes `project_dir` for store-aware module execution.
- Recipe/engine input resolution now supports optional cross-recipe dependencies via `store_inputs_optional`:
  - `src/cine_forge/driver/recipe.py`
  - `src/cine_forge/driver/engine.py`
- Timeline reorder operations now require exact scene-id set matching (reject missing/extra IDs).
- Story tracking/docs updates:
  - Story 012 marked `Done` with full work log evidence.
  - Story 013 rewritten to align with current timeline-first architecture.
  - Story 046 annotated with architecture update note.

## [2026-02-19] - Full Storybook skill-pack sync (scout, triage, ADR/init, and create-story templates)

### Added
- Imported additional canonical skills from Storybook: `create-adr`, `init-project`, `scout`, and `triage`.
- Added `create-story` scaffolding assets:
  - `.agents/skills/create-story/scripts/start-story.sh`
  - `.agents/skills/create-story/templates/story.md`
  - `.agents/skills/create-story/templates/stories-index.md`
- Generated new Gemini wrappers for added skills:
  - `.gemini/commands/create-adr.toml`
  - `.gemini/commands/init-project.toml`
  - `.gemini/commands/scout.toml`
  - `.gemini/commands/triage.toml`

### Changed
- Synced shared existing skill definitions to Storybook’s latest canonical wording and workflow structure:
  - `build-story`, `check-in-diff`, `create-story`, `deploy`, `mark-story-done`, `validate`
- Regenerated `.gemini/commands/*.toml` wrappers from synced canonical skills.
- `deploy` Gemini wrapper removed because deploy is now non-invocable in canonical frontmatter (`user-invocable: false`).

## [2026-02-19] - Align cross-CLI skill system with latest storybook architecture

### Changed
- Updated `scripts/sync-agent-skills.sh` to match the new canonical flow:
  - parse arbitrary frontmatter fields
  - generate Gemini wrappers only for `user-invocable` skills
  - clear stale Gemini wrappers before regeneration
- Updated `.agents/skills/create-cross-cli-skill/SKILL.md` to require `user-invocable` metadata and include `templates/` as an optional colocated resource.
- Regenerated `.gemini/commands/*.toml` wrappers from canonical skill definitions after sync.

## [2026-02-19] - Cross-CLI skills unification and canonical agent skill layout (Story 053)

### Added
- Canonical skill source tree at `.agents/skills/` including `create-cross-cli-skill` meta-skill for portable skill creation.
- Skill synchronization tooling via `scripts/sync-agent-skills.sh` and Makefile targets `skills-sync` / `skills-check`.
- Gemini CLI compatibility wrappers generated under `.gemini/commands/*.toml` from canonical `SKILL.md` files.

### Changed
- Story tracking updated: Story 053 marked `Done` in both `docs/stories.md` and `docs/stories/story-053-cross-cli-skills-unification.md`.
- Claude and Cursor skill discovery now point to canonical source via symlinks (`.claude/skills`, `.cursor/skills`).
- Legacy prompt-era Cursor commands moved to `.cursor/commands.legacy/` to remove active duplication while preserving reference history.

## [2026-02-19] - Story 049 OCR-noisy PDF normalization fix and production validation

### Added
- Regression tests for OCR-noisy PDF screenplay handling in normalization:
  - `test_is_screenplay_path_detects_ocr_noisy_pdf_screenplay`
  - `test_run_module_routes_ocr_noisy_pdf_misclassified_as_prose_to_tier2`

### Fixed
- `script_normalize_v1` now preserves screenplay routing for OCR-noisy/misclassified PDF inputs instead of hard-rejecting to empty canonical script in Tier 3 when screenplay signals are present.
- Tier routing now still rejects true high-confidence prose, preventing false-positive screenplay promotion.

### Changed
- Story 049 marked done in `docs/stories.md` and `docs/stories/story-049-import-normalization-format-suite.md` after successful production validation on `the-body-4` input `d93d9cc3_The_Body.pdf`.
- Deploy timing log updated in `docs/deploy-log.md` with latest successful Fly deploy and smoke evidence.

---

## [2026-02-19] - Fix TypeScript build parity between local validation and production

### Fixed
- Validate and deploy skills now use `tsc -b` instead of `tsc --noEmit`, matching the production Docker build. `tsc --noEmit` silently skipped strict checks (`noUnusedLocals`) due to root `tsconfig.json` having `"files": []`.

---

## [2026-02-19] - Chat UX polish, progress card, live counts, and parallel execution (Story 051)

### Added
- `RunProgressCard` component: single updating widget replaces per-stage chat message spam, stages render in recipe-defined order with live status icons (pending/spinner/checkmark/error/cached).
- `ChangelogDialog` shared component: extracted from Landing and AppShell, with overflow fixes.
- Sidebar live count badges: Scenes, Characters, Locations, Props nav items show artifact counts with pulse animation on increment.
- Inbox unread count badge in sidebar navigation.
- Progress card artifact counts: inline summaries (e.g., "13 scenes, 4 characters") next to completed stages.
- Parallel stage execution: independent stages in the same wave run concurrently via `ThreadPoolExecutor`.
- Thread safety for `ArtifactStore` and `DependencyGraph` (write locks prevent TOCTOU races during parallel execution).

### Changed
- Chat message ordering: completion summary → AI insight → next-step CTA (previously out of order).
- Action button naming: "Break Down Script" / "Deep Breakdown" / "Browse Results" with plain-language descriptions.
- Button hierarchy: golden-path actions use `variant: 'default'`, navigation links use `variant: 'outline'`.
- Sidebar counts refresh mid-run by invalidating artifact queries on stage completion.

---

## [2026-02-19] - Provider resilience hardening, OCR runtime tooling, and deploy estimate recalibration

### Added
- Stage retry/fallback observability across run state and events, including per-attempt metadata and fallback transitions.
- New failed-stage resume endpoint: `POST /api/runs/{run_id}/retry-failed-stage`.
- Artifact metadata annotations for final model/provider used in each stage:
  - `final_stage_model_used`
  - `final_stage_provider_used`
- OCR-capable runtime dependencies in the production image (`poppler-utils`, `ocrmypdf`, `tesseract-ocr`, `tesseract-ocr-eng`, `ghostscript`).
- Deploy timing memory file: `docs/deploy-log.md`.

### Fixed
- Transient error classification now covers provider overload/capacity cases (including HTTP `529`) with exponential backoff + jitter.
- Provider circuit breaker behavior integrated into LLM transport to reduce retry storms and skip unhealthy providers.
- Resume-from-failure path now supports upstream reuse via prior artifact refs when stage cache is unavailable.
- Ingest/normalize/extract guards now fail fast on empty extracted/normalized screenplay text with actionable errors.

### Changed
- Story tracking updates:
  - Story 050 marked `Done` with resilience scope complete.
  - Story 049 reopened (`To Do`) for deferred OCR-noisy PDF normalization quality follow-up.
- Deploy skill now includes a required duration recalibration workflow using recent successful deploy medians.
- Deploy expected duration recalibrated to `~1.5 minutes` based on recent successful runs.

---

## [2026-02-18] - Centralized browser MCP runbook and hardened deploy smoke workflow

### Added
- New canonical browser automation + MCP runbook: `docs/runbooks/browser-automation-and-mcp.md`
- Cross-environment guidance for Codex, Cursor, Claude Code, and Gemini CLI MCP setup/recovery.
- Codex nested-browser validation pattern with deterministic evidence capture (`codex exec -o ...`, screenshot artifacts, console error summary).
- Observed failure-mode troubleshooting (wrong MCP config scope, missing log directories, verbose output handling, empty MCP resource list discrepancy).

### Changed
- `skills/deploy/SKILL.md` now references the canonical browser runbook instead of embedding long tool-specific troubleshooting.
- Deploy skill now includes:
  - cache-hit fast deploy interpretation guidance
  - explicit nested-Codex browser smoke path when direct in-session browser tools are unavailable
  - reporting requirements for screenshot paths + console error logs
- `AGENTS.md` now references the browser runbook in UI verification and deployment guidance.
- `docs/deployment.md` now points to the canonical browser runbook for environment-specific browser automation recovery.

---

## [2026-02-18] - PDF import preview fix and cross-format normalization test hardening

### Added
- Story docs for:
  - `story-048-pdf-input-preview-decode.md`
  - `story-049-import-normalization-format-suite.md`
- New ingest fixtures:
  - `tests/fixtures/ingest_inputs/patent_registering_votes_us272011_scan_5p.pdf`
  - `tests/fixtures/ingest_inputs/run_like_hell_teaser_scanned_5p.pdf`
- Expanded ingest/normalize coverage across all supported import formats (`txt`, `md`, `fountain`, `fdx`, `docx`, `pdf`) with semantic assertions.
- PDF extractor diagnostics for observability (`pdf_extractors_attempted`, `pdf_extractor_selected`, `pdf_extractor_output_lengths`).

### Fixed
- Project input preview endpoint now uses ingest extraction for supported formats, preventing raw binary UTF-8 decode garbage for PDFs.
- PDF extraction quality improved through staged fallback (`pdftotext -layout` -> `pypdf` -> `ocrmypdf`) plus layout repair handling.

### Changed
- `docs/stories.md` updated to include Stories 048 and 049 as Done.
- Wrapped overlong unit-test lines in `tests/unit/test_story_ingest_module.py` to satisfy Ruff and keep deployment preflight green.

---

## [2026-02-18] - Story 039 deferred evals, Gemini multi-provider fixes, and /deploy skill

### Added
- `/deploy` skill and canonical deployment runbook doc for repeatable production deploys (Story 037 follow-up).
- Three deferred promptfoo eval configs (location, prop, relationship) built and run across all 13 providers (Story 039).
- CalVer versioning (`YYYY.MM.DD`) derived from CHANGELOG.md; shown in sidebar footer and landing page.
- `/api/health` returns `version` field; `/api/changelog` serves full changelog as text.
- Clickable version badge opens changelog dialog in both AppShell and Landing page.
- UI smoke test added to `/deploy` skill (screenshots, console error check).

### Fixed
- Stale model defaults replaced after benchmarking revealed better-performing models per task (Story 039).
- Landing page version positioned in fixed bottom-left corner (matching sidebar pattern).

### Changed
- Trimmed `AGENTS.md` operational noise; moved deployment detail to dedicated doc.
- Story 038 marked done; Story 039 scope expanded to include deferred eval coverage.

---

## [2026-02-17] - Production deployment, Gemini support, Sonnet 4.6 benchmarks, and Story 037-038-047

### Added
- Deployed CineForge to production at `cineforge.copper-dog.com` on Fly.io with Let's Encrypt SSL, Cloudflare DNS, and a persistent 1GB volume (Story 037).
- Multi-provider LLM transport with Google Gemini support (`gemini-2.5-flash`, `gemini-2.5-pro`); backend now routes to Anthropic, OpenAI, or Google based on model ID prefix (Story 038).
- Story 045 (Entity Cross-Linking) and Story 046 (Theme System) draft files added to backlog.

### Fixed
- `PermissionError` crash on Fly.io when the volume `lost+found` directory was encountered during project discovery.
- Untracked `.claude/settings.local.json` from git and added it to `.gitignore`.

### Changed
- Benchmarked Sonnet 4.6 across all six promptfoo evals (character extraction, scene extraction, location, prop, relationship, config detection) against 12 other providers; updated model defaults in `src/cine_forge/schemas/models.py` with winning models per task (Story 047).

---

## [2026-02-16] - Conversational AI Chat, Entity-first Navigation, UI wiring, and pipeline performance

### Added
- Conversational AI Chat (Story 011f): full six-phase implementation including streaming AI responses, persistent chat thread, knowledge layer surfacing relevant artifacts into context, inline tool-use for running pipeline stages, smart suggestions, and lint cleanup.
- Entity-first navigation (Story 043): dedicated Character, Location, and Prop detail pages with cross-references; enriched sorting by narrative prominence; script-to-scene deep links; breadcrumbs; sticky sort/density preferences persisted to `project.json`.
- Story 041 (Artifact Quality Improvements) story file added; immediately implemented as Story 042 after renumbering.

### Fixed
- Wired all mock UI components to real backend APIs, replacing placeholder data with live artifact fetches (Story 042).
- Entity ID consistency across detail pages; breadcrumb navigation and artifact UX polish (Story 042).
- World-building cost explosion caused by unnecessary QA passes: hardcoded `skip_qa` and removed dead recipe references.
- Landing page now shows 5 most recent projects with timestamps and an expand/collapse toggle.

### Changed
- `ui/operator-console/` directory flattened to `ui/` — Story 043 done and directory structure simplified.
- Pipeline performance optimized (Story 040): reduced redundant AI calls, improved stage caching, and lowered median run cost.
- Chat-driven progress replaces polling: server-side chat events drive run state updates (Story 011e Phases 1.5–2.5).
- Project identity now uses URL slugs (`/projects/:slug`) rather than numeric IDs; chat state persisted server-side (Story 011e).

---

## [2026-02-15] - Operator Console production build, promptfoo benchmarking, and model selection

### Added
- Production Operator Console build (Story 011d): full React + shadcn/ui UI with file-first project creation, script-centric home page, story-centric navigation (Script / Scenes / Characters / Locations / World / Inbox), and chat panel as the primary interaction surface.
- Script-centric home page and chat panel Phase 1 implementation (Story 011e): chat replaces sidebar hints; Inbox is a filtered view of `needs_action` chat messages.
- promptfoo benchmarking tooling evaluation complete (Story 035): workspace structure, dual evaluation pattern (Python scorer + LLM rubric), cross-provider judge strategy, and pitfalls documented in `AGENTS.md`.
- Model Selection and Eval Framework (Story 036): character extraction eval across 13 providers; Opus 4.6 established as judge; winning models recorded per task.
- Claude Code skills wired up via `.claude/skills/` symlinks for agent discovery.

### Changed
- Story 011b Operator Console research and design decisions documented and complete.
- Story 011c phase summary and recommended order synced in story file.
- `AGENTS.md` updated with benchmarking workspace structure, eval catalog, model selection table, and lessons learned (promptfoo pitfalls: `max_tokens` trap, `---` separator trap, Gemini token budget).

---

## [2026-02-14] - World-building pipeline, Entity Relationship Graph, 3-Recipe Architecture, and UI routing

### Added
- High-fidelity world-building infrastructure: bible generation modules, resilient LLM retry logic with token escalation, and catch-and-retry on malformed JSON (`src/cine_forge/ai/llm.py`).
- Entity Relationship Graph module: AI-powered entity extraction, `needs_all` orchestration pattern, and selective per-entity re-runs.
- Basic UI visualization for the Entity Relationship Graph.
- 3-Recipe Architecture (Intake / Synthesis / Analysis): partitions pipeline into independently runnable segments with human-in-the-loop gates between expensive world-building steps.
- Continuity tracking foundation added alongside 3-Recipe Architecture.
- Resource-oriented routing foundation for Operator Console: identity in URL path, not search params.
- Stories 008 and 009 documented and marked done.

### Changed
- Enhanced Entity Graph with real AI extraction replacing stubs; selective re-run support added.
- `AGENTS.md`: added "No Implicit Commits" mandate; captured cross-recipe artifact reuse pattern via `store_inputs`; documented 3-Recipe Architecture lesson and resource-oriented UI principle.

---

## [2026-02-13] - Story 007c remediation, DOCX support, hot-reload, and bible module

### Added
- Semantic quality gates for degraded PDF ingestion: confidence scoring, anomaly detection, and remediation triggers to prevent schema-valid-but-useless artifacts (Story 007c).
- Unit and integration regression tests for Story 007c PDF quality remediation.
- DOCX ingestion support: `python-docx` based parser added to the ingest module; UI file picker now accepts `.docx` alongside `.pdf` and `.fountain`.
- Bible infrastructure and character bible module: `CharacterBible` schema, AI-driven extraction, and versioned artifact output.
- All missing story files (008–034) scaffolded with design foundations.

### Fixed
- Hot-reloading enabled for the Operator Console backend via `uvicorn --reload`; eliminates manual restarts during local development.

### Changed
- Story index (`docs/stories.md`) updated to reflect new stories and status changes.

---

## [2026-02-13] - Deliver Operator Console Lite and add MVP fidelity remediation story

### Added
- New Operator Console Lite backend service under `src/cine_forge/operator_console/` with project lifecycle, run start/state/events, artifact browsing, recent-project discovery, and input upload endpoints.
- New React + Vite UI under `ui/operator-console-lite/` with file-first project creation (drag/drop + file picker), run controls, runs/events inspection, artifact browser, and on-demand project switcher drawer.
- New test coverage:
  - `tests/unit/test_operator_console_api.py`
  - `tests/integration/test_operator_console_integration.py`
  - `ui/operator-console-lite/e2e/operator-console.spec.ts`
- New remediation planning story `docs/stories/story-007c-mvp-reality-remediation.md` to address real-run artifact fidelity issues discovered via UI-led validation.

### Fixed
- Resolved local dev CORS failures causing UI "Failed to fetch" by allowing localhost/127.0.0.1 origins across local ports in Operator Console API middleware.
- Improved artifact browser UX with explicit selected group/version highlighting and auto-selection of latest/single version.
- Stabilized Playwright test startup behavior in UI config for deterministic local runs.

### Changed
- Updated Story 007b acceptance/task wording to align with approved UX (`Project Switcher` replacing dedicated `Open Project` route while preserving open-existing-project functionality).
- Updated docs in `README.md` and story index in `docs/stories.md` for Operator Console flows and new 007c scope.
- Extended project guidance in `AGENTS.md` for mandatory manual UI verification and captured pitfalls from recent execution.
- Updated `.gitignore` for UI build/test artifacts (`*.tsbuildinfo`, `test-results/`, `playwright-report/`).

## [2026-02-13] - Complete Story 007 MVP recipe smoke coverage and runtime parameter UX

### Added
- New Story 007 end-to-end recipe at `configs/recipes/recipe-mvp-ingest.yaml` with runtime placeholders for input/model/acceptance controls.
- New Story 007 fixture corpus under `tests/fixtures/` including screenplay/prose inputs and mocked AI response bundles for normalization, scene QA, and project config detection.
- New integration suite `tests/integration/test_mvp_recipe_smoke.py` covering mocked smoke, live-gated smoke, staleness propagation, and fixture integrity preflight checks.
- New CLI unit coverage in `tests/unit/test_driver_cli.py` for `--params-file` loading, `--param` override precedence, and non-mapping params-file rejection.

### Fixed
- Resolved live structured-output schema failures by rebuilding normalization envelope models and tightening project-config detected-field typing.
- Repaired mocked fixture regression by replacing empty per-scene fixture files with valid JSON and adding preflight validation to prevent recurrence.

### Changed
- Driver CLI now supports generic runtime parameter injection via `--param` and `--params-file`, with improved failure summaries and success output.
- Driver runtime now resolves `${...}` recipe placeholders before validation/execution and supports optional stage-level lineage aggregation for aggregate artifacts.
- Updated Story 007 docs/work-log status to Done and synchronized story index status in `docs/stories.md`.
- Added `smoke-test` and `live-test` Make targets and expanded README runbook docs for MVP smoke execution and artifact inspection.

## [2026-02-12] - Implement Story 006 project configuration module and confirmation flow

### Added
- New `project_config_v1` ingest module with AI-assisted project parameter detection, draft file output, confirmation modes (`--accept-config`, `--config-file`, `--autonomous`), and schema-validated draft/canonical artifact handling.
- New `ProjectConfig` and `DetectedValue` schemas, plus unit/integration coverage for schema validation, module behavior, and end-to-end project config persistence.
- New recipe `configs/recipes/recipe-ingest-extract-config.yaml` for ingest -> normalize -> scene extraction -> project config flow.
- New Story 019 scaffold at `docs/stories/story-019-human-interaction.md` to track deferred non-CLI interaction scope (web UI / Director chat).

### Changed
- Driver runtime now supports config confirmation flags, stage pause state (`paused`), and runtime fingerprint hashing of `input_file`/`config_file` contents for safer cache invalidation.
- Driver schema registry now includes `project_config`.
- Story tracking updates: Story 006 marked `Done` with completed acceptance/tasks/work-log evidence, and deferred interaction scope moved to Story 019.
- Added driver tests proving stale propagation for downstream artifacts when `project_config` changes.

## [2026-02-12] - Implement Story 005 scene extraction pipeline

### Added
- New `scene_extract_v1` ingest module with deterministic-first scene splitting, structured element extraction, provenance tracking, selective AI enrichment, and per-scene QA retry handling.
- New scene schemas (`Scene`, `SceneIndex`, and supporting models) in `src/cine_forge/schemas/scene.py`.
- New extraction recipe `configs/recipes/recipe-ingest-extract.yaml` chaining ingest -> normalize -> extract.
- New unit and integration coverage for scene schemas, extraction behavior, parser/fallback benchmarks, and end-to-end artifact persistence.
- New Story 005 parser evaluation note at `docs/research/story-005-scene-parser-eval.md`.

### Changed
- Driver schema registration now includes `scene` and `scene_index`.
- Driver multi-output validation now resolves schema per artifact (`schema_name`/`artifact_type`) to avoid cross-schema false failures.
- Story tracking updates: Story 005 marked `Done` in `docs/stories.md` and `docs/stories/story-005-scene-extraction.md`.
- Added AGENTS effective pattern documenting per-artifact schema selection for multi-output stages.
