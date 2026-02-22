# Changelog

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
