"""Whole-workspace eval contract and mechanical fanout; never generates semantics.

The complete schema is intentionally stricter than the host schemas: every field,
including nullable/defaultable fields, is required and unknown keys are rejected.
Native provider support must be checked separately with native_schema_issues().
Passing these checks proves structure/references, not source comprehension.
"""

from __future__ import annotations

import copy
import hashlib
import json
import types
from datetime import UTC, datetime
from functools import reduce
from pathlib import Path
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, create_model
from pydantic_core import PydanticUndefined

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.schema_registry import build_schema_registry
from cine_forge.schemas import (
    ArtifactMetadata,
    BibleManifest,
    CanonicalScript,
    CharacterBible,
    ContinuityIndex,
    ContinuityState,
    EntityGraph,
    FormatClassification,
    LocationBible,
    ProjectConfig,
    PropBible,
    RawInput,
    Scene,
    SceneIndex,
    ScriptBible,
)

_STRICT_MODELS: dict[type[BaseModel], type[BaseModel]] = {}


def _strict_annotation(annotation: Any) -> Any:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return required_model(annotation)
    origin, args = get_origin(annotation), get_args(annotation)
    if not args:
        return annotation
    if origin in (Union, types.UnionType):
        return reduce(lambda left, right: left | right, map(_strict_annotation, args))
    if origin in (list, dict, tuple, set):
        return origin[tuple(_strict_annotation(arg) for arg in args)]
    return annotation


def required_model(original: type[BaseModel]) -> type[BaseModel]:
    """Keep host validators/constraints, require all fields, reject extra keys."""
    if original in _STRICT_MODELS:
        return _STRICT_MODELS[original]
    fields = {}
    for name, original_field in original.model_fields.items():
        field = copy.deepcopy(original_field)
        field.default = PydanticUndefined
        field.default_factory = None
        fields[name] = (_strict_annotation(field.annotation), field)
    model = create_model(f"Required{original.__name__}", __base__=original, **fields)
    model.model_config = ConfigDict(**{**original.model_config, "extra": "forbid"})
    model.model_rebuild(force=True)
    _STRICT_MODELS[original] = model
    return model


WholeStoryWorkspaceBundle = create_model(
    "WholeStoryWorkspaceBundle",
    __config__=ConfigDict(extra="forbid"),
    raw_input=(required_model(RawInput), ...),
    canonical_script=(required_model(CanonicalScript), ...),
    script_bible=(required_model(ScriptBible), ...),
    project_config=(required_model(ProjectConfig), ...),
    scenes=(list[required_model(Scene)], ...),
    scene_index=(required_model(SceneIndex), ...),
    characters=(list[required_model(CharacterBible)], ...),
    locations=(list[required_model(LocationBible)], ...),
    props=(list[required_model(PropBible)], ...),
    entity_graph=(required_model(EntityGraph), ...),
    continuity_states=(list[required_model(ContinuityState)], ...),
    continuity_index=(required_model(ContinuityIndex), ...),
)

_canonical_fields = {}
for _name, _field in required_model(CanonicalScript).model_fields.items():
    if _name not in ("line_count", "scene_count"):
        _canonical_fields[_name] = (_field.annotation, copy.deepcopy(_field))
SubjectCanonicalScript = create_model(
    "SubjectCanonicalScript", __config__=ConfigDict(extra="forbid"), **_canonical_fields,
)
_subject_fields = {}
for _name, _field in WholeStoryWorkspaceBundle.model_fields.items():
    if _name not in ("raw_input", "canonical_script"):
        _subject_fields[_name] = (_field.annotation, copy.deepcopy(_field))
SubjectWorkspaceBundle = create_model(
    "SubjectWorkspaceBundle", __config__=ConfigDict(extra="forbid"),
    source_classification=(required_model(FormatClassification), ...),
    canonical_script=(SubjectCanonicalScript, ...), **_subject_fields,
)


def subject_payload(consumer_payload: dict[str, Any]) -> dict[str, Any]:
    """Remove only byte-identical raw source and mechanical count fields."""
    result = copy.deepcopy(consumer_payload)
    result["source_classification"] = result.pop("raw_input")["classification"]
    for key in ("line_count", "scene_count"):
        result["canonical_script"].pop(key)
    return SubjectWorkspaceBundle.model_validate(result).model_dump(mode="json")


def consumer_payload(subject: dict[str, Any], *, source_bytes: bytes,
                     source_filename: str) -> dict[str, Any]:
    """Stamp only supplied raw provenance/counts. No semantic completion."""
    result = SubjectWorkspaceBundle.model_validate(subject).model_dump(mode="json")
    source_text = source_bytes.decode("utf-8")
    source_name = _safe_component(source_filename)
    result["raw_input"] = {
        "content": source_text,
        "source_info": {"original_filename": source_name, "file_size_bytes": len(source_bytes),
                        "character_count": len(source_text),
                        "line_count": len(source_text.splitlines()),
                        "file_format": Path(source_name).suffix.lstrip(".").lower()},
        "classification": result.pop("source_classification"),
    }
    result["canonical_script"]["line_count"] = len(
        result["canonical_script"]["script_text"].splitlines())
    result["canonical_script"]["scene_count"] = len(result["scenes"])
    return validate_bundle(result, source_bytes=source_bytes).model_dump(mode="json")


class NativeWorkspaceEnvelope(BaseModel):
    """Native strict transport projection, NOT native domain-schema enforcement.

    Supply SubjectWorkspaceBundle.model_json_schema() in the prompt. Decode
    bundle_json and run validate_bundle() before any consumer write. The server
    guarantees one required string; local host validation guarantees its domain
    structure. This split must be disclosed in every result.
    """

    model_config = ConfigDict(extra="forbid")
    bundle_json: str


def decode_native_envelope(payload: dict[str, Any], *, source_bytes: bytes,
                           source_filename: str) -> BaseModel:
    envelope = NativeWorkspaceEnvelope.model_validate(payload)
    full = consumer_payload(json.loads(envelope.bundle_json), source_bytes=source_bytes,
                            source_filename=source_filename)
    return validate_bundle(full, source_bytes=source_bytes)


def native_schema_issues(schema: dict[str, Any] | None = None) -> list[str]:
    """Report open objects/Any; do not silently weaken the native guarantee.

    This is a conservative unsupported-surface inventory, not a replacement for
    the selected SDK/provider's authoritative schema check. JSON-string fields
    would only provide a transport-level strict guarantee, not this domain one.
    """
    schema = schema or WholeStoryWorkspaceBundle.model_json_schema()
    issues = []

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            issues.append(f"{path}: dynamic/open object; strict-native support unproven")
        if not any(key in node for key in ("type", "$ref", "anyOf", "allOf", "oneOf", "enum")):
            if (path.endswith(".items") or path.endswith(".additionalProperties")
                    or ".properties." in path):
                issues.append(f"{path}: unconstrained Any")
        for key in ("$defs", "properties"):
            for name, child in node.get(key, {}).items():
                walk(child, f"{path}.{key}.{name}")
        for key in ("items", "additionalProperties"):
            walk(node.get(key), f"{path}.{key}")
        for key in ("anyOf", "allOf", "oneOf"):
            for i, child in enumerate(node.get(key, [])):
                walk(child, f"{path}.{key}[{i}]")

    walk(schema, "$")
    return issues


def state_artifact_id(state: dict[str, Any]) -> str:
    return f"{state['entity_type']}_{state['entity_id']}_{state['scene_id']}"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_bundle(payload: dict[str, Any], *, source_bytes: bytes) -> BaseModel:
    """Validate complete fields, host schemas and referential/source integrity.

    Does not invent missing semantic fields, canonicalize IDs, repair quotes,
    resolve aliases, infer state coverage, or substitute a semantic judge.
    """
    bundle = WholeStoryWorkspaceBundle.model_validate(payload)
    data = bundle.model_dump(mode="json")
    source_text = source_bytes.decode("utf-8")
    raw = data["raw_input"]
    _require(raw["content"] == source_text, "raw_input must preserve exact source")
    info = raw["source_info"]
    _require(info["file_size_bytes"] == len(source_bytes), "source byte count mismatch")
    _require(info["character_count"] == len(source_text), "source character count mismatch")
    _require(info["line_count"] == len(source_text.splitlines()), "source line count mismatch")
    canonical = data["canonical_script"]
    _require(canonical["script_text"] == source_text,
             "selected authored Fountain canonical must preserve exact original source")
    lines = canonical["script_text"].splitlines()
    _require(canonical["line_count"] == len(lines), "canonical line count mismatch")
    _require(canonical["scene_count"] == len(data["scenes"]), "canonical scene count mismatch")
    _require(data["scenes"] != [], "workspace requires source scenes")
    scenes = {scene["scene_id"]: scene for scene in data["scenes"]}
    _require(len(scenes) == len(data["scenes"]), "duplicate scene IDs")
    numbers = [scene["scene_number"] for scene in data["scenes"]]
    _require(numbers == list(range(1, len(scenes) + 1)), "scene order/number mismatch")
    index = data["scene_index"]
    _require(index["total_scenes"] == len(scenes), "index scene count mismatch")
    _require(len(index["entries"]) == len(scenes), "index entries incomplete")
    for scene, entry in zip(data["scenes"], index["entries"], strict=True):
        _require(all(scene[k] == v for k, v in entry.items()), "scene/index fields disagree")
        span = scene["source_span"]
        _require(span["end_line"] <= len(lines), "scene source span exceeds canonical source")
        text = "\n".join(lines[span["start_line"] - 1:span["end_line"]])
        _require(bool(text.strip()), "scene has empty source span")
        _require(scene["heading"] in text, "scene heading absent from source span")
    _require(index["scenes_passed_qa"] + index["scenes_need_review"] == len(scenes),
             "index QA counts do not cover scenes")
    _require(data["project_config"]["confirmed"], "workspace config must be confirmed")

    entities: dict[tuple[str, str], dict[str, Any]] = {}
    for kind, member in (("character", "characters"), ("location", "locations"), ("prop", "props")):
        for entity in data[member]:
            entity_id = entity[f"{kind}_id"]
            _require(bool(entity_id), "empty entity ID")
            _require((kind, entity_id) not in entities, "duplicate entity ID")
            entities[kind, entity_id] = entity
            _require(set(entity["scene_presence"]) <= scenes.keys(), "dangling scene_presence")
    for scene in scenes.values():
        _require(all(("character", cid) in entities for cid in scene["characters_present_ids"]),
                 "scene contains dangling character ID")
    for entity in data["characters"]:
        for evidence in entity["explicit_evidence"]:
            sid, span = evidence["source_scene"], evidence["source_span"]
            _require(sid in scenes, "character evidence source_scene must be a scene ID")
            scene_span = scenes[sid]["source_span"]
            _require(scene_span["start_line"] <= span["start_line"] <= span["end_line"]
                     <= scene_span["end_line"], "evidence span outside cited scene")
            quote_source = "\n".join(lines[span["start_line"] - 1:span["end_line"]])
            _require(bool(evidence["quote"]) and evidence["quote"] in quote_source,
                     "character quote absent from cited exact source span")
        for relation in entity["relationships"]:
            _require(("character", relation["target_character"]) in entities,
                     "character relationship target must be a character ID")
    for prop in data["props"]:
        _require(all(("character", cid) in entities for cid in prop["associated_characters"]),
                 "prop character association does not resolve")
    graph = data["entity_graph"]
    _require(graph["edge_count"] == len(graph["edges"]), "graph edge count mismatch")
    _require(graph["entity_count"] == {
        kind: sum(key[0] == kind for key in entities) for kind in ("character", "location", "prop")
    }, "graph entity counts mismatch")
    for edge in graph["edges"]:
        _require((edge["source_type"], edge["source_id"]) in entities, "dangling graph source")
        _require((edge["target_type"], edge["target_id"]) in entities, "dangling graph target")
        _require(set(edge["scene_refs"]) <= scenes.keys(), "dangling graph scene reference")

    states = {state_artifact_id(state): state for state in data["continuity_states"]}
    _require(len(states) == len(data["continuity_states"]), "duplicate continuity state ID")
    positions = {sid: pos for pos, sid in enumerate(scenes)}  # host pipeline uses zero-based
    for state in states.values():
        _require((state["entity_type"], state["entity_id"]) in entities, "dangling state entity")
        _require(state["scene_id"] in scenes, "dangling state scene")
        _require(state["story_time_position"] == positions[state["scene_id"]],
                 "state story_time_position must match zero-based scene order")
    ci = data["continuity_index"]
    listed = []
    for key, timeline in ci["timelines"].items():
        identity = (timeline["entity_type"], timeline["entity_id"])
        _require(key == ":".join(identity) and identity in entities, "invalid timeline identity")
        _require(set(timeline["gaps"]) <= scenes.keys(), "dangling continuity gap")
        timeline_positions = []
        for state_id in timeline["states"]:
            _require(state_id in states, "dangling timeline state")
            state = states[state_id]
            _require((state["entity_type"], state["entity_id"]) == identity,
                     "timeline references another entity's state")
            timeline_positions.append(state["story_time_position"])
            listed.append(state_id)
        _require(timeline_positions == sorted(set(timeline_positions)), "unordered/repeated states")
    _require(len(listed) == len(set(listed)) and set(listed) == states.keys(),
             "continuity index does not cover every state exactly once")
    _require(ci["total_gaps"] == sum(len(t["gaps"]) for t in ci["timelines"].values()),
             "continuity gap count mismatch")
    return bundle


def materialize_workspace(
    payload: dict[str, Any], *, source_bytes: bytes, project_dir: Path,
    run_context: dict[str, Any],
) -> dict[str, Any]:
    """Write a new immutable workspace via host store; no provider calls.

    Caller owns source/model privacy approval and semantic acceptance. Destination
    must not exist; no historical project or artifact is overwritten.
    """
    data = validate_bundle(payload, source_bytes=source_bytes).model_dump(mode="json")
    project_dir = project_dir.resolve()
    _require(not project_dir.exists(), "refusing to overwrite an existing project")
    for scene in data["scenes"]:
        _safe_component(scene["scene_id"])
    for kind, member in (("character", "characters"), ("location", "locations"), ("prop", "props")):
        for entity in data[member]:
            _safe_component(entity[f"{kind}_id"])
    source_name = _safe_component(data["raw_input"]["source_info"]["original_filename"])
    registry = build_schema_registry()
    refs, expected = [], {}
    project_dir.mkdir(parents=True)
    (project_dir / "inputs").mkdir()
    (project_dir / "inputs" / source_name).write_bytes(source_bytes)
    (project_dir / "project.json").write_text(json.dumps({
        "slug": project_dir.name, "display_name": data["canonical_script"]["title"],
        "human_control_mode": data["project_config"]["human_control_mode"],
    }, indent=2), encoding="utf-8")
    store = ArtifactStore(project_dir=project_dir)
    timestamp = datetime.now(UTC).isoformat()

    def metadata(kind: str, confidence: float, upstream: list[Any]) -> ArtifactMetadata:
        return ArtifactMetadata(
            intent=f"Materialize supplied whole-workspace {kind} payload",
            rationale="Lossless fanout of validated subject output; no semantic field completion",
            confidence=confidence, source="human" if kind == "raw_input" else "ai",
            producing_module="whole_story_workspace_eval", lineage=upstream,
            annotations={"run_context": run_context,
                         "source_sha256": hashlib.sha256(source_bytes).hexdigest()},
        )

    def save(kind: str, entity_id: str, value: dict[str, Any], upstream: list[Any],
             confidence: float) -> Any:
        validation = registry.validate(kind, value)
        _require(validation.valid, f"host {kind} schema failed: {validation}")
        ref = store.save_artifact(kind, entity_id, value, metadata(kind, confidence, upstream))
        refs.append(ref)
        expected[kind, entity_id] = value
        return ref

    raw_ref = save("raw_input", "project", data["raw_input"], [],
                   data["raw_input"]["classification"]["confidence"])
    canonical_ref = save("canonical_script", "project", data["canonical_script"], [raw_ref],
                         data["canonical_script"]["normalization"]["overall_confidence"])
    save("script_bible", "project", data["script_bible"], [canonical_ref],
         data["script_bible"]["confidence"])
    scene_refs = {scene["scene_id"]: save("scene", scene["scene_id"], scene,
                  [canonical_ref], scene["confidence"]) for scene in data["scenes"]}
    index_ref = save("scene_index", "project", data["scene_index"],
                     [canonical_ref, *scene_refs.values()],
                     data["canonical_script"]["normalization"]["overall_confidence"])
    save("project_config", "project", data["project_config"], [canonical_ref, index_ref],
         data["canonical_script"]["normalization"]["overall_confidence"])
    entity_refs = {}
    for kind, member in (("character", "characters"), ("location", "locations"), ("prop", "props")):
        for entity in data[member]:
            entity_id = entity[f"{kind}_id"]
            ref = save(f"{kind}_bible", entity_id, entity,
                       [canonical_ref, index_ref], entity["overall_confidence"])
            entity_refs[kind, entity_id] = ref
            manifest_ref = store.save_bible_entry(
                entity_type=kind, entity_id=entity_id, display_name=entity["name"],
                files=[{"filename": "master_v1.json", "purpose": "master_definition",
                        "version": 1, "provenance": "ai_extracted", "created_at": timestamp}],
                data_files={"master_v1.json": json.dumps(entity, ensure_ascii=False)},
                metadata=metadata("bible_manifest", entity["overall_confidence"], [ref]),
                visual_reference_image=None,
            )
            manifest = store.load_artifact(manifest_ref).data
            BibleManifest.model_validate(manifest)
            refs.append(manifest_ref)
            expected["bible_manifest", f"{kind}_{entity_id}"] = manifest
    save("entity_graph", "project", data["entity_graph"],
         [index_ref, *entity_refs.values()], data["entity_graph"]["extraction_confidence"])
    state_refs = []
    for state in data["continuity_states"]:
        state_refs.append(save("continuity_state", state_artifact_id(state), state,
                               [canonical_ref, scene_refs[state["scene_id"]],
                                entity_refs[state["entity_type"], state["entity_id"]]],
                               state["overall_confidence"]))
    save("continuity_index", "project", data["continuity_index"], state_refs,
         data["continuity_index"]["overall_continuity_score"])
    return {"project_dir": str(project_dir), "artifact_refs": [r.model_dump() for r in refs]}


def _safe_component(value: str) -> str:
    _require(bool(value) and value not in (".", "..") and Path(value).name == value
             and "/" not in value and "\\" not in value and "\x00" not in value,
             "unsafe or empty file/entity component")
    return value


def consumer_smoke(*, repo_root: Path, project_dir: Path,
                   payload: dict[str, Any], source_bytes: bytes) -> dict[str, Any]:
    """Read every final artifact through the real service; compare exact data."""
    from cine_forge.api.service import OperatorConsoleService

    data = validate_bundle(payload, source_bytes=source_bytes).model_dump(mode="json")
    _require((project_dir / "project.json").is_file(), "project metadata missing")
    service = OperatorConsoleService(workspace_root=repo_root)
    pid = service.open_project(str(project_dir))
    summary = service.project_summary(pid)
    _require(summary["has_inputs"], "consumer sees no source input")
    expected = {("raw_input", "project"): data["raw_input"],
                ("canonical_script", "project"): data["canonical_script"],
                ("script_bible", "project"): data["script_bible"],
                ("project_config", "project"): data["project_config"],
                ("scene_index", "project"): data["scene_index"],
                ("entity_graph", "project"): data["entity_graph"],
                ("continuity_index", "project"): data["continuity_index"]}
    expected.update({("scene", s["scene_id"]): s for s in data["scenes"]})
    expected.update({("continuity_state", state_artifact_id(s)): s
                     for s in data["continuity_states"]})
    bibles = {}
    for kind, member in (("character", "characters"), ("location", "locations"), ("prop", "props")):
        for entity in data[member]:
            entity_id = entity[f"{kind}_id"]
            expected[f"{kind}_bible", entity_id] = entity
            bibles[f"{kind}_{entity_id}"] = entity
    groups = service.list_artifact_groups(pid)
    keys = {(g["artifact_type"], g["entity_id"]) for g in groups}
    _require(keys == set(expected) | {("bible_manifest", bid) for bid in bibles},
             "consumer artifact group inventory differs from bundle")
    for group in groups:
        kind, entity_id = group["artifact_type"], group["entity_id"]
        versions = service.list_artifact_versions(pid, kind, entity_id)
        _require(len(versions) == 1, "fanout unexpectedly produced historical versions")
        detail = service.read_artifact(pid, kind, entity_id, group["latest_version"])
        _require(detail["health"] == "valid", "consumer artifact health is not valid")
        if kind == "bible_manifest":
            _require(detail.get("bible_files", {}).get("master_v1.json") == bibles[entity_id],
                     "consumer master sidecar differs from direct bible")
        else:
            _require(detail["payload"]["data"] == expected[kind, entity_id],
                     f"consumer payload differs from bundle: {kind}/{entity_id}")
    search = service.search_entities(pid, "scene")
    _require(len(search["scenes"]) == len(data["scenes"]), "consumer scene search incomplete")
    service.get_pipeline_graph(pid)
    return {"project_id": pid, "artifact_groups": len(groups), "has_inputs": True,
            "all_payloads_equal": True, "all_health_valid": True,
            "scene_search_count": len(search["scenes"]),
            "claim": "mechanical consumer smoke only; semantic acceptance remains separate"}
