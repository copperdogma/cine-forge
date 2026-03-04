# Scout 009 — Storybook & Dossier delta 4

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-03-03
**Scope:** Changes since Scout 008 (2026-03-02) + 4 unimplemented carry-forwards from Scout 008
**Previous:** Scout 008 (2026-03-02, Partial)
**Status:** Complete

## Carry-Forwards from Scout 008 (never implemented)

3. **Evidence failure taxonomy** — MEDIUM value
   What: Dossier documented specific failure patterns for adversarial golden verification: truncated quotes, wrong-scene refs, compound facts, tangential text, mention_type confusion. Named patterns with detection approaches.
   Us: `docs/runbooks/golden-build.md` is sparse on what to look for when auditing. No failure taxonomy.
   Recommendation: Inline — add "Common Evidence Failures" section to `docs/runbooks/golden-build.md`.

4. **Relationship bidirectionality validation** — MEDIUM value
   What: Complete relationship sets must include bidirectional links (A→child(B) means B→parent(A); all spouse/sibling pairs get both directions). Dossier's `fix_goldens.py` added 45 reciprocal relationships in one pass.
   Us: `benchmarks/golden/the-mariner-relationships.json` may have incomplete bidirectionality. No validator checks this — a model producing the correct one-way link would still fail scoring.
   Recommendation: Inline — add validation note to `docs/runbooks/golden-build.md` and note to check bidirectionality when auditing relationship goldens.

5. **Atmospheric login pattern** — MEDIUM value
   What: Storybook Story 033: login page with full-screen background image (day/night variants), frosted glass card overlay (`bg-white/50 dark:bg-slate-900/15 backdrop-blur-xl`), mobile-specific background-position shift, heading color gradient in dark mode.
   Us: CineForge has a simple auth page. The frosted glass pattern is CSS-minimal and gives a professional film-industry aesthetic.
   Recommendation: Inline — add "Atmospheric Auth Layout" pattern reference to `AGENTS.md > UI Development Workflow`.

6. **Date-grouped sidebar with dividers** — LOW-MEDIUM value
   What: Storybook Story 033: `groupConversations()` buckets items by Today/Yesterday/This week/Older. Section dividers use `flex items-center gap-2` + `flex-1 border-t` both sides with a centered label (`text-[10px] uppercase tracking-widest select-none`). Non-interactive dividers don't interfere with keyboard navigation.
   Us: CineForge sidebar shows projects without grouping. Pattern is reusable for entity list grouping (scenes by act, characters by role type).
   Recommendation: Inline — add "Grouped List Divider" pattern reference to `AGENTS.md > UI Development Workflow`.

## New Findings from Dossier (since 2026-03-02)

7. **`golden_fixture_helpers.py` — shared golden test helper module** — HIGH value
   What: Story 047 extracted a `golden_fixture_helpers.py` module containing:
   - `GoldenFixtureSpec` dataclass (slug + expected entity/relationship/evidence counts)
   - `GOLDEN_SPECS` registry listing all 14 golden fixtures with count expectations
   - `load_golden()` / `load_source_text()` — standardized loading with schema validation
   - `assert_cross_references()` — verifies all evidence_ids and entity_ids are internally consistent
   - `assert_evidence_quotes_non_empty()` — catches empty quote strings
   - `assert_evidence_spans_valid()` — validates span start/end boundaries
   - `assert_evidence_offsets_match_source()` — verifies exact source slice matches stored quote
   Tests split across `test_golden_fixtures.py` (structural, compact) and `test_golden_regressions.py` (semantic regressions).
   Us: CineForge has only 1 golden fixture (`tests/fixtures/golden/the_mariner_scene_entities.json`) with no shared helpers. Golden tests are ad-hoc and scattered across module test files. No structural integrity suite. No offset verification.
   Recommendation: Create story — adopt the helper module pattern, add count/integrity assertions for existing goldens, and document the approach so future golden files follow the same structure.

8. **Anthropic prompt caching (ADR-015 research finding)** — HIGH value
   What: Storybook's ADR-015 deep research consensus: "prompt caching is the single highest-ROI optimization — 90% cost reduction on cached tokens, up to 85% latency reduction." Anthropic's API supports `cache_control: {"type": "ephemeral"}` on system messages and large user messages. Active conversations maintain near-100% hit rate (5-min TTL refreshes on each use).
   Us: CineForge's `src/cine_forge/ai/llm.py` has no prompt caching logic at all. Multiple modules pass the full screenplay text (200KB+ for a feature film) in every call. `scene_analysis_v1`, `script_bible_v1`, `entity_discovery_v1`, `entity_graph_v1` all process the full script repeatedly. At current costs, caching the screenplay system prompt across module calls would dramatically reduce costs.
   Recommendation: Create story — add `cache_control` header support to `_build_anthropic_payload()` in `llm.py`, expose as an optional `enable_caching: bool` param in `call_llm()`, enable it for all Anthropic calls with large system prompts.

9. **`prompt_versions: dict[str, str]` in run metadata** — LOW value
   What: Dossier Story 048 replaced `RunMetadata.prompt_version` (single string) with `prompt_versions: dict[str, str]` so each stage hashes its own prompt and contributes a key. Engine populates all stage hashes.
   Us: CineForge already has `recipe_fingerprint` and `stage_fingerprint` for caching. These fingerprint recipe structure (YAML + params), but don't hash actual prompt *content* separately. If a module's prompt text changes within the same recipe YAML, the stage_fingerprint wouldn't detect it.
   Recommendation: Low priority — CineForge's architecture bakes prompt content into modules, not recipes. Stage fingerprints cover recipe + module identity, which is sufficient. Skip unless prompt drift becomes a real debugging problem.

## New Findings from Storybook (since 2026-03-02)

10. **Simplification baselines pattern** — LOW value
    What: Story 027 formalized "run the simplest possible approach before building the pipeline" with dedicated eval scripts (`c1-extraction-baseline.ts`, `c3-identity-baseline.ts`) and named compromise gates in the eval registry. Result: C1 (multi-step extraction) still needed; C3 (identity resolution) found over-engineered by 3-tier pipeline.
    Us: CineForge's AGENTS.md already states "Baseline = Best Model Only" and "Never conclude AI can't do this from a cheap model's failure." The methodology is captured. No gaps.
    Recommendation: Skip — already in AGENTS.md.

11. **Story 029: Local audio capture** — NOT applicable
    Voice interface feature. CineForge has no voice interface. Skip.

12. **Component substitution ADRs 002-004 (local NER/IE stack)** — NOT applicable
    Dossier ADRs about replacing cloud models with local GLiNER/GliREL/embedding models. Dossier-specific ML infrastructure. CineForge uses cloud AI APIs throughout. Skip.

13. **ADR-015 Two-Speed Extraction architecture** — LOW-MEDIUM reference value
    What: ACCEPTED ADR for per-turn fast lane (embedding RAG + session buffer) vs post-conversation slow lane (full extraction pipeline). Key technical finding: per-turn tool-calling agent (Option C) not viable — Haiku TTFT ~530ms consumes entire per-turn budget for voice. Local ONNX embedding <22ms vs API embedding 200-350ms.
    Us: CineForge is a batch pipeline — no per-turn latency concerns. The two-speed concept isn't directly applicable. The prompt caching insight is captured in Finding 8 above.
    Recommendation: Reference only. The ADR content is interesting context for future real-time features but nothing actionable now.

## Approved

- [x] 7. `golden_fixture_helpers.py` — Story 122 created
- [x] 8. Anthropic prompt caching — Story 123 created

## Skipped / Rejected

- 3. Evidence failure taxonomy — deferred per user
- 4. Relationship bidirectionality — deferred per user
- 5. Atmospheric login pattern — deferred per user
- 6. Date-grouped divider — deferred per user
- 9. prompt_versions metadata — already covered by recipe_fingerprint + stage_fingerprint
- 10. Simplification baselines — already in AGENTS.md
- 11. Story 029 local audio capture — voice-only, not applicable
- 12. Component substitution ADRs — ML infrastructure, not applicable
- 13. ADR-015 two-speed extraction — voice/conversation specific, not applicable
