# Whole story workspace consumer contract — read-only analysis

2026-11-09. Source inspected in the isolated story-236 worktree. No provider
calls, baseline modifications, implementation changes, or private inputs read.
This note specifies requirements; it is not evidence that a completed subject
bundle fits or meets semantic acceptance.

## Required boundary

The experiment ends at the story workspace produced by `mvp_ingest` plus
`world_building`, not at rendered media. Relevant owning sources:

- `configs/recipes/recipe-mvp-ingest.yaml`, `recipe-world-building.yaml`
- `src/cine_forge/schemas/{models,canonical_script,scene,script_bible,bible,graph,continuity}.py`
- `src/cine_forge/artifacts/store.py`, `driver/artifact_persister.py`
- `src/cine_forge/api/{service,artifact_manager}.py`
- `ui/src/lib/hooks/{projects,artifacts,entities}.ts`
- `ui/src/pages/ContinuityPage.tsx`, `components/EntityTimelineView.tsx`

ADR-001 shared entity extraction requires source-grounded evidence and explicitly
endorses testing “just ask the LLM.” It does not prescribe this bundle wire format.
No existing ADR directly specifies a whole-workspace bundle.

Fresh project directory must contain `artifacts/`, `graph/`, `project.json`, and
`inputs/<source filename>`. `OperatorConsoleService.open_project(str(path))`
accepts artifacts+graph alone but backfills project.json (a write). UI workspace
state remains `empty` without inputs even if artifacts exist; the `complete`
state requires inputs plus a bible manifest or entity graph. That UI flag alone
does not prove completeness. A fresh output avoids stage_cache.json filtering
away newly generated entity groups. If a cache is emitted, its current refs must
be correct; do not copy historical cache state.

## Lossless bundle map

Use existing Pydantic types as payload contracts. Project artifact entity IDs are
the literal `project`; per-scene IDs equal `Scene.scene_id`; bible direct IDs
equal character_id/location_id/prop_id. Scene, entity, graph, and continuity IDs
must refer to the same identities throughout.

| Bundle member / type | Required persisted consumer artifacts |
| --- | --- |
| raw_input / RawInput | raw_input/project |
| canonical_script / CanonicalScript | canonical_script/project |
| script_bible / ScriptBible | script_bible/project |
| project_config / ProjectConfig | project_config/project (confirmed) |
| scenes / list[Scene] | scene/<scene_id>, final enriched scene once each |
| scene_index / SceneIndex | scene_index/project, final enriched index |
| characters / list[CharacterBible] | character_bible/<id> plus character manifest/master |
| locations / list[LocationBible] | location_bible/<id> plus location manifest/master |
| props / list[PropBible] | prop_bible/<id> plus prop manifest/master |
| entity_graph / EntityGraph | entity_graph/project |
| continuity_states / list[ContinuityState] | continuity_state/<type>_<id>_<scene_id> |
| continuity_index / ContinuityIndex | continuity_index/project |
| entity_discovery_results / EntityDiscoveryResults | entity_discovery_results/project if preserving all recipe final types; intermediary rather than essential UI workspace data |

Full semantic fields, including schema-defaultable ones, should be explicitly
present in the subject contract. Omitted fields must not be silently completed
by Pydantic defaults. An explicitly empty list can be correct where the source
supports it; empty lists used to evade evidence/continuity completeness cannot.

- **RawInput:** content; source_info(original_filename, file_size_bytes,
  character_count, line_count, file_format); classification(detected_format,
  confidence, evidence). Source content and mechanical source_info may be copied
  from the supplied file; classification is a semantic judgment unless frozen
  as supplied context.
- **CanonicalScript:** title, script_text, line_count, scene_count,
  normalization(source_format, strategy, inventions[{description, location,
  rationale}], assumptions[{description, rationale, alternatives_considered}],
  overall_confidence, rationale).
- **Scene:** scene_id, scene_number, heading, location, time_of_day, int_ext,
  characters_present, characters_present_ids, props_mentioned,
  elements[{element_type, content}], narrative_beats[{beat_type, description,
  approximate_location, confidence}], tone_mood, tone_shifts,
  source_span{start_line,end_line}, inferences[{field_name,value,rationale,
  confidence}], provenance[{field_name,method,evidence,confidence}], confidence.
- **SceneIndex:** total_scenes, unique_locations, unique_characters,
  estimated_runtime_minutes, scenes_passed_qa, scenes_need_review,
  entries[{scene_id,scene_number,heading,location,time_of_day,characters_present,
  characters_present_ids,props_mentioned,source_span,tone_mood}]. It is safe to
  serialize common entry fields once in Scene and project them exactly during
  fanout when the wire contract explicitly defines this shared representation.
  Runtime estimate and QA semantics cannot be invented from omitted output.
- **ScriptBible:** title, logline, synopsis, act_structure[{act_number,title,
  start_scene,end_scene,summary,turning_points}], themes[{theme,description,
  evidence}], narrative_arc, genre, tone, protagonist_journey, central_conflict,
  setting_overview, confidence.
- **ProjectConfig:** title, format, genre, tone, estimated_duration_minutes,
  primary_characters, supporting_characters, location_count, locations_summary,
  target_audience, aspect_ratio, production_mode, production_format,
  storyboard_style, human_control_mode, style_packs, budget_cap_usd,
  model_strategy{work,verify,escalate}, default_model,
  detection_details[field -> {value,confidence,rationale,source}], confirmed,
  confirmed_at. Frozen runtime/user settings can be supplied context. Story
  title/genre/tone/cast/audience/format judgments must not be completed in code.
- **CharacterBible:** character_id, name, aliases, description, prominence,
  explicit_evidence[{trait,quote,source_scene,source_span}],
  inferred_traits[{trait,value,confidence,rationale}], scene_presence,
  dialogue_summary, narrative_role, narrative_role_confidence,
  relationships[{target_character,relationship_type,evidence,confidence}],
  overall_confidence.
- **LocationBible:** location_id, name, aliases, description, physical_traits,
  scene_presence, narrative_significance, overall_confidence.
- **PropBible:** prop_id, name, description, scene_presence,
  associated_characters, narrative_significance, overall_confidence.
- **EntityGraph:** edges[{source_type,source_id,target_type,target_id,
  relationship_type,direction,evidence,scene_refs,confidence}], entity_count,
  edge_count, extraction_confidence. Counts may be exact mechanical lengths;
  relationships/evidence/direction/confidence are subject judgments.
- **ContinuityState:** entity_type, entity_id, scene_id, story_time_position,
  properties[{key,value,confidence}], change_events[{property_key,
  previous_value,new_value,reason,evidence,is_explicit,confidence}],
  overall_confidence.
- **ContinuityIndex:** timelines["<type>:<id>" -> {entity_type,entity_id,states,
  gaps}], total_gaps, overall_continuity_score. states are continuity artifact
  IDs, convention `<type>_<id>_<scene_id>`, not direct entity IDs. gaps are scene
  IDs. Do not let code infer absent state snapshots, gaps, or confidence.
- **EntityDiscoveryResults:** characters, locations, props, script_title,
  processing_metadata.

Existing enum/bounds details remain authoritative in the models: SourceSpan is
1-based inclusive; confidence values are [0,1]; scene number >=1; int_ext is
`INT`, `EXT`, or `INT/EXT`; elements have the exact
eight element_type enum values in scene.py; entity types are character,
location, prop. Graph direction is symmetric/source_to_target/target_to_source.

## Bible and store fanout

For each entity, persist direct typed bible data with `save_artifact`, then use
`save_bible_entry(entity_type, entity_id, display_name=name, files=[...],
data_files={"master_v1.json": exact_same_bible_json}, metadata=...)`.

Manifest ref entity_id is `<type>_<id>`, path
`artifacts/bibles/<type>_<id>/manifest_v1.json`. Manifest data entity_id remains
the unprefixed ID. File entry: filename=master_v1.json,
purpose=master_definition, version=1, provenance=ai_extracted, created_at=run
timestamp. Manifest has entity_type/entity_id/display_name/files/version and
created_at; visual_reference_image=null for this story-only boundary.
`read_artifact` loads referenced JSON/text sidecars into `bible_files`; the UI
also loads direct entity bible artifacts independently. Both representations
must exist and be equal. Model emits bible semantics once, code duplicates it.

`ArtifactMetadata` requires intent, rationale, confidence, source; source enum
is ai/human/hybrid/code. Store adds ref/version/path and registers dependency
graph. Keep actual call metadata/cost, producer, timestamps, frozen execution
fingerprint and semantic-source provenance in the appropriate envelope; no need
to make the model emit repeated path/version/timestamp/lineage objects. Fixed
administrative descriptions can describe copying/fanout, while semantic
judgments must come from supplied model output. Save raw -> canonical -> scenes
-> index and downstream dependencies in forward order. Include no nonexistent
historical refs and no self-dependency. Do not manufacture old intermediate
versions merely to match historical file counts.

Important: `ArtifactStore.save_artifact` validates the envelope, not data
against its domain schema. Validate every typed payload separately before
persisting. `SchemaRegistry.validate` validates without returning a normalized
payload. Existing models may ignore unknown fields and supply defaults; reject
unknown fields and absent semantic fields explicitly rather than claiming
losslessness after a successful parse.

## Referential and source checks

- Canonical line_count must equal the chosen exact `script_text.splitlines()`
  convention; source spans must fit its length. Pydantic checks positive ordered
  spans but does not check upper bounds. Scene heading must align to its span;
  entries and scene payloads must agree. Preserve complete source coverage,
  scene ordering, exact dialogue/action, and source fidelity independently of
  structural validation. Canonical content differs from raw source only where
  explicit normalization/assumption/invention contract permits.
- Character explicit quote must occur in the cited canonical scene/span.
  source_scene must resolve, and no inferred trait may masquerade as an explicit
  quotation. Relationship evidence and continuity evidence need semantic
  acceptance even though their models do not require numeric source spans.
- Every scene_presence, graph scene_refs, continuity scene_id/gap must resolve
  to a scene. Every graph endpoint/prop association resolves to typed entity.
  Character names/aliases/IDs and relationship targets require consistent
  identity resolution; code may check consistency but may not infer identity.
- Every continuity timeline state reference resolves to a persisted state of
  that timeline's entity; order and story_time_position agree. Check complete
  material entity coverage and explicit source-supported changes, not just
  existence of one arbitrary state per entity.

## Historical volume and output-budget decision

The retained historical result
`benchmarks/results/full-script-throughput-story-159-short-medium-2026-04-11.json`
has open_frequency_short, 3447 input bytes, 75 artifact refs, 570388 output bytes,
23297 summed API output tokens. Its project_dir was
`output/eval-full-script-throughput-open_frequency_short-2ebc7f`; parent reports
this directory is absent across registered worktrees. Primary
`output/open-frequency` has only MVP outputs (9 final groups), so is not a
consumer-complete exemplar. It was inspected as JSON files only, without opening
it in the service or reading inputs. Its canonical declared line_count=133 but
splitlines length=132; do not inherit that inconsistent count.

Historical 75 refs include 8 scenes (4 original+4 enriched), 2 scene indexes,
2 configs, 18 direct bibles+18 manifests, and 21 continuity states. The volume
helper sums artifact-ref JSON paths, including repeated envelopes/lineage and
superseded versions; it does NOT count master sidecar bytes. Therefore 570388
is neither the required final wire payload nor a complete workspace disk total.
23297 historical API tokens is not proof of new output feasibility.

Before any paid subject call, serialize a complete semantic exemplar for the
full source using precisely the selected wire format and deterministic fanout.
Dry-run all domain/schema/reference checks and actual consumer reads. Measure
whole response bytes and subject tokenizer tokens, not a shortened excerpt.
Demonstrate an explicit bound: visible structured output + all subject thinking
<=65536, including any subject retries/rescue if the selected arm allows them.
An exemplar's measured token count is evidence about that exemplar, not a hard
bound on unconstrained future generation. Reserve a stated thinking allowance
or disable/minimize thinking through a verified supported setting; enforce the
provider total cap and fail truncation. If a conservative upper bound cannot be
justified, defer that selected configuration before paying. Do not substitute
empty placeholders, semantic defaults, omitted consumer fields, or unsupported
token/byte conversions to make it fit.

## Actual final consumer smoke interface

After fanout in a new experiment project (already containing project.json), run
under the repository interpreter with PYTHONPATH=src:

```python
from pathlib import Path
from cine_forge.api.service import OperatorConsoleService
from cine_forge.schemas import ArtifactRef

repo = Path('/Users/cam/.codex/worktrees/fable-whole-task-20261109/cine-forge')
project = repo / 'output' / '<new-experiment-slug>'
service = OperatorConsoleService(workspace_root=repo)
pid = service.open_project(str(project))
summary = service.project_summary(pid)
assert summary['has_inputs']
groups = service.list_artifact_groups(pid)
assert groups
for group in groups:
    kind, entity, version = group['artifact_type'], group['entity_id'], group['latest_version']
    entity_arg = entity or '__project__'
    versions = service.list_artifact_versions(pid, kind, entity_arg)
    assert any(v['version'] == version for v in versions)
    detail = service.read_artifact(pid, kind, entity_arg, version)
    assert detail['payload']['data']
    assert detail['health'] not in ('stale', 'needs_revision')
    if kind == 'bible_manifest':
        assert 'master_v1.json' in detail['bible_files']
assert service.search_entities(pid, 'scene')['scenes']
pipeline = service.get_pipeline_graph(pid)
```

Add exact expected type/group counts and equality checks against the bundle;
test every scene and every entity rather than one arbitrary example. Type
validation, quote/reference checks, semantic review, and direct-bible/sidecar
equality remain separate assertions. This is zero-provider consumer checking.

HTTP equivalents from the actual app: POST `/api/projects/open` body
`{"project_path":"<absolute experiment path>"}`, GET `/api/projects/{id}`,
GET `/api/projects/{id}/artifacts`, GET
`/api/projects/{id}/artifacts/{type}/{entity}/{version}`, GET
`/api/projects/{id}/search?q=scene`, GET
`/api/projects/{id}/pipeline-graph`. A loadable API workspace is stronger evidence
than JSON validity; browser verification is additionally needed before claiming
actual UI acceptance.

## Implemented zero-provider representability example

After the analysis, the owner authorized the new bounded contract module
`benchmarks/scripts/whole_story_workspace_contract.py` and independently authored
`benchmarks/fixtures/whole_story_workspace_v1/open_frequency-consumer-example.json`.
The complete example is solely a representability artifact, not a baseline run
or subject answer, and must never be included in a subject prompt. Its semantic
content was authored from the complete original source plus the source-only
oracle. It contains 4 scenes, 7 characters (including unnamed remote caller and
animal Comet), 9 locations, 22 props, 30 relationship edges, and 62 continuity
states. Remote/mentioned presence and the source's unresolved identities and
offscreen reports are stated explicitly. Referenced entities need not be staged.

The selected subject contract differs only mechanically from the initial full
consumer inventory above: `SubjectWorkspaceBundle` asks for source_classification
and full semantic artifacts; exact raw source/source_info and canonical
line_count/scene_count are stamped by `consumer_payload`. Every other original
field remains required, including nested lists otherwise defaultable by the
host schema. Unknown nested keys are forbidden. `subject_payload` followed by
`consumer_payload` is exact for the authored example.

Native grammar is intentionally projected to strict
`NativeWorkspaceEnvelope{bundle_json:string}`. Supply the full
`SubjectWorkspaceBundle.model_json_schema()` separately in the prompt, decode
the JSON string, then require the complete local original-domain validation and
source/reference checks. The server's native guarantee is structural transport
only; it does not enforce nested domain correctness. This is an explicit
disclosed configuration choice, not a claim that the host schema was natively
enforced. Direct host schemas contain dynamic maps and unconstrained Any in
DetectedValue.value; `native_schema_issues()` reports them without silently
deleting constraints.

Observed zero-provider results:

- Full consumer compact UTF-8 JSON: **74022 bytes**; pretty fixture: 105012 bytes.
- Subject semantic compact JSON: **70250 bytes**.
- Compact native outer JSON envelope including string escaping: **77611 bytes**.
- Fresh materialized project:
  `output/story-237-open-frequency-consumer-example-001` (inside this isolated
  worktree, retained for the owner to inspect, no old project changed).
- **149 artifact groups** read through actual OperatorConsoleService; every
  nonmanifest data payload equaled the full example, all 38 bible master
  sidecars equaled their direct bible, all health values were valid, source
  input was visible, scene search returned all 4 scenes, and pipeline graph
  loaded. This is API consumer smoke, not browser or semantic acceptance.
- Six negative checks rejected a missing defaultable nested semantic field,
  extra deeply nested key, source span beyond canonical text, fabricated exact
  character quote, dangling continuity reference, and dangling graph endpoint.
  Ruff passed the new contract module. No provider/token-count calls were made
  by this worker; an actual selected-provider free tokenizer/count operation and
  explicit total output/thinking allocation remain with the owner before payment.

The first smoke used `all scenes`, which is not the host's special search syntax;
inspection showed the service accepts bare `scene` or `sc`. The smoke and command
above now use `scene`; no application code or retry behavior was modified.
