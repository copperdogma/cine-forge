# Story 007: MVP Recipe and End-to-End Smoke Test

**Status**: To Do
**Created**: 2026-02-11
**Spec Refs**: 3 (High-Level Pipeline Overview), 3.1 (Stage Progression), 2.7 (Cost Transparency), 2.8 (QA)
**Depends On**: Story 002 (driver, artifact store, recipes), Story 003 (ingestion), Story 004 (normalization), Story 005 (scene extraction), Story 006 (project config)

---

## Goal

Wire Stories 002–006 together into a single end-to-end recipe that takes a raw story input file and produces: a `raw_input` artifact, a `canonical_script` artifact, individual `scene` artifacts + a `scene_index`, and a `project_config`. Run this recipe against a representative test screenplay and verify that every artifact is correct, every dependency is tracked, every cost is recorded, and every QA check runs.

This is the "it works" milestone — the first time the full MVP pipeline runs from start to finish. It proves that the driver orchestrates correctly, modules communicate through the artifact store, schemas validate, lineage chains are intact, and the user can inspect every artifact and its provenance.

This story produces no new modules or infrastructure. It is purely integration, testing, validation, and polish.

## Acceptance Criteria

### MVP Recipe
- [ ] A recipe file: `configs/recipes/recipe-mvp-ingest.yaml`
  ```yaml
  recipe_id: mvp_ingest
  description: "Full MVP ingestion pipeline: raw input → canonical script → scenes → project config."
  stages:
    - id: ingest
      module: story_ingest_v1
      params:
        input_file: "${input_file}"

    - id: normalize
      module: script_normalize_v1
      needs: [ingest]
      params:
        model: "${default_model}"

    - id: extract_scenes
      module: scene_extract_v1
      needs: [normalize]
      params:
        model: "${default_model}"

    - id: project_config
      module: project_config_v1
      needs: [normalize, extract_scenes]
      params:
        model: "${default_model}"
        accept_config: "${accept_config}"
  ```
- [ ] Recipe validates: all module_ids resolve, `needs` references are acyclic, schema compatibility between stages (e.g., `story_ingest_v1` outputs `raw_input`, `script_normalize_v1` expects `raw_input`).
- [ ] Recipe supports parameter substitution (`${input_file}`, `${default_model}`, etc.) from CLI args or a params file.

### Test Screenplay
- [ ] A representative test screenplay file: `tests/fixtures/sample_screenplay.fountain`
  - [ ] Written in Fountain format (the open-source screenplay standard).
  - [ ] At least 5 scenes with varied locations (interior/exterior, day/night).
  - [ ] At least 4 named characters with dialogue, including at least 1 who appears in multiple scenes.
  - [ ] At least 1 character referenced in action but without dialogue (tests character extraction completeness).
  - [ ] At least 1 transition and 1 parenthetical (tests element type coverage).
  - [ ] At least 1 tonal shift (e.g., a scene that starts light and turns dark, or a comedic scene followed by a dramatic scene).
  - [ ] Approximately 8–12 pages — long enough to be meaningful, short enough to keep AI costs low in tests.
  - [ ] Should tell a coherent (if simple) story so that genre, tone, and audience detection in Story 006 have something to work with.
- [ ] A second test file: `tests/fixtures/sample_prose.txt`
  - [ ] The same story written as prose fiction (not screenplay format).
  - [ ] Exercises the full prose → screenplay conversion path in Story 004.
  - [ ] Shorter (3–5 pages) to keep test costs down.

### End-to-End Smoke Test (Mocked AI)
- [ ] A test that runs the full MVP recipe with **mocked AI responses**:
  - [ ] Uses the test screenplay as input.
  - [ ] All LLM calls are intercepted and return pre-built fixtures.
  - [ ] Verifiable without API keys or internet access.
  - [ ] Runs in CI.
- [ ] After the run completes, verify:
  - [ ] **Artifact existence**: `raw_input_v1`, `canonical_script_v1`, `scene_001_v1` through `scene_N_v1`, `scene_index_v1`, `project_config_v1` all exist in the artifact store.
  - [ ] **Schema validation**: every artifact validates against its declared Pydantic schema.
  - [ ] **Lineage chain**: `canonical_script_v1` depends on `raw_input_v1`. Each `scene_NNN_v1` depends on `canonical_script_v1`. `scene_index_v1` depends on all scenes. `project_config_v1` depends on `canonical_script_v1` and `scene_index_v1`.
  - [ ] **Artifact health**: all artifacts are `valid` (no upstream changes since creation).
  - [ ] **Cost tracking**: every AI-produced artifact has cost metadata (model, tokens, estimated cost). The run state includes a total cost summary.
  - [ ] **QA results**: normalization artifact has a QA result attached. Each scene has a QA result. All pass (since we control the mocked responses).
  - [ ] **Run state**: `run_state.json` shows all stages completed successfully with timing data.
  - [ ] **Pipeline events**: `pipeline_events.jsonl` has entries for each stage start/end.
  - [ ] **Project config**: draft was auto-confirmed (via `accept_config: true`), contains plausible values for the test screenplay.

### End-to-End Smoke Test (Live AI) — Optional
- [ ] A test that runs the full MVP recipe with **real AI calls**:
  - [ ] Gated behind `CINE_FORGE_LIVE_TESTS=1` environment variable.
  - [ ] Uses the test screenplay as input.
  - [ ] Requires `OPENAI_API_KEY` (or equivalent) to be set.
  - [ ] Does NOT run in CI — manual execution only.
- [ ] After the run completes, verify the same artifact existence, schema, lineage, and cost checks as the mocked test.
- [ ] Additionally verify:
  - [ ] The canonical script is a readable, properly formatted screenplay.
  - [ ] Scene extraction produced reasonable scenes (characters match, locations match headings).
  - [ ] Project config auto-detected plausible values (genre, tone, format).
  - [ ] QA results are meaningful (not just rubber-stamped passes).
- [ ] Record the total cost of the live run in the test output — this is the first real data point for "what does it cost to run the MVP pipeline on a short screenplay?"

### CLI Invocation
- [ ] The MVP pipeline can be invoked from the command line:
  ```bash
  python -m cine_forge.driver \
    --recipe configs/recipes/recipe-mvp-ingest.yaml \
    --run-id smoke-test-001 \
    --param input_file=tests/fixtures/sample_screenplay.fountain \
    --param default_model=gpt-4o \
    --param accept_config=true
  ```
- [ ] Clear output: the driver prints progress to stdout (stage starting, stage complete, cost so far).
- [ ] On success: prints a summary (artifacts produced, total cost, any QA warnings).
- [ ] On failure: prints the error, which stage failed, and what artifacts were successfully produced before the failure.
- [ ] Exit code: 0 on success, non-zero on failure.

### Staleness Propagation Test
- [ ] A focused test that verifies the dependency graph works across the full chain:
  - [ ] Run the MVP recipe → all artifacts `valid`.
  - [ ] Re-run ingestion with a modified input file → `raw_input_v2` created.
  - [ ] Verify: `canonical_script_v1` is now `stale`, all scenes are `stale`, `scene_index_v1` is `stale`, `project_config_v1` is `stale`.
  - [ ] Re-run normalization → `canonical_script_v2` created.
  - [ ] Verify: `canonical_script_v2` is `valid`, scenes (still referencing v1) remain `stale`, etc.
  - [ ] This proves the structural invalidation layer (Story 002) works correctly in practice.

### Documentation
- [ ] `README.md` updated with:
  - [ ] Quick start: how to run the MVP pipeline on a sample file.
  - [ ] What the pipeline produces (list of artifacts with descriptions).
  - [ ] How to inspect artifacts in the project folder.
  - [ ] Environment setup (API keys, dependencies).

## Design Notes

### This Story Is Integration, Not New Code

Stories 002–006 build the pieces. This story wires them together and proves they work. The bulk of the work is:
1. Writing good test fixtures (the sample screenplay and prose).
2. Writing comprehensive integration tests with mocked AI.
3. Debugging the inevitable issues that surface when modules actually talk to each other through the real artifact store and driver.
4. Polishing the CLI output to be clear and informative.

Expect to find and fix bugs in earlier stories during this integration. That's the point — better to find them now than after building 20 more modules on top.

### The Test Screenplay Is a Project Asset

The sample screenplay isn't throwaway — it will be used throughout the project:
- Phase 2 stories (bibles, entity graph) will process it further.
- Phase 3 stories (creative direction, shot planning) will use it.
- It's the "hello world" of CineForge.

Invest time making it a good, coherent short screenplay that exercises all the features. It should be genuinely interesting to read — if the test data is boring, testing will be boring, and bugs will hide in the boredom.

### Mocked AI Responses as Living Fixtures

The mocked AI responses for the smoke test need to be realistic — they should look like what the real models would produce. When we later run the live test and see what the models actually return, we should update the mocked fixtures to match. This keeps the mocked tests honest.

### The Prose Test Is Equally Important

The `sample_prose.txt` file exercises the hardest path: prose → screenplay conversion. This is where Story 004's long document strategy, QA checks, and invention labeling are most critical. Even though it's shorter than the screenplay, it's a more demanding test of the normalization module.

### What This Story Does NOT Include

- **Performance benchmarking** — we note costs and timing but don't set performance targets.
- **Parallel execution** — the driver may execute stages sequentially for MVP. Parallelism (e.g., extracting scenes concurrently) is a future optimization.
- **Error recovery** — if a stage fails, the run stops. Partial recovery (skip the failed scene, continue with others) is an enhancement.
- **UI** — all interaction is CLI. Web UI and interactive modes are later stories.

## Tasks

- [ ] Write the sample screenplay: `tests/fixtures/sample_screenplay.fountain` (5+ scenes, 4+ characters, varied elements).
- [ ] Write the sample prose: `tests/fixtures/sample_prose.txt` (same story in prose form).
- [ ] Write mocked AI response fixtures for:
  - [ ] Normalization (screenplay cleanup path).
  - [ ] Normalization (prose conversion path).
  - [ ] Normalization QA check.
  - [ ] Per-scene extraction (one fixture per scene in the sample screenplay).
  - [ ] Per-scene QA checks.
  - [ ] Project config auto-detection.
- [ ] Create the MVP recipe: `configs/recipes/recipe-mvp-ingest.yaml`.
- [ ] Write the mocked end-to-end smoke test.
- [ ] Write the staleness propagation test.
- [ ] Write the live end-to-end test (gated behind `CINE_FORGE_LIVE_TESTS`).
- [ ] Polish CLI output: progress messages, success summary, failure reporting.
- [ ] Run the mocked smoke test, fix all issues found.
- [ ] (If API keys available) Run the live smoke test, record cost, update mocked fixtures if real responses differ significantly.
- [ ] Update `README.md` with quick start and artifact descriptions.
- [ ] Update `Makefile` with `make smoke-test` target (mocked) and `make live-test` target (real AI).
- [ ] Update AGENTS.md with lessons learned from integration.

## Notes

- This is the most satisfying story to complete — it's the first time the whole thing works. Take time to celebrate and document what was learned.
- Budget roughly 30% of this story's time for debugging integration issues. Things that worked in isolation will break when connected. That's normal and valuable.
- The live test is optional but highly recommended when feasible. Seeing real AI output is essential for calibrating expectations and improving prompts. The cost should be low — a short screenplay through 4 modules is probably under $1.
- After this story, we have a working MVP that can ingest a screenplay, normalize it, extract scenes, and produce a project config. That's the foundation everything else builds on.

## Work Log

(entries will be added as work progresses)
