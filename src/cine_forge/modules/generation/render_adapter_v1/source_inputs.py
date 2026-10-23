"""Render adapter input parsing and output selection (no paid operations)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cine_forge.modules.generation.render_adapter_v1.support import (
    optional_string as _optional_string,
)
from cine_forge.modules.generation.render_adapter_v1.support import slugify as _slugify
from cine_forge.pipeline.scene_actions import filter_scene_payloads
from cine_forge.schemas import (
    CharacterAndPerformance,
    CharacterBible,
    InjectedAssetManifest,
    IntentMood,
    KeyframeArtifact,
    LocationBible,
    LookAndFeel,
    ProjectConfig,
    RenderClipPlan,
    RhythmAndFlow,
    ShotPlan,
    SoundAndMusic,
    TrackManifest,
)
from cine_forge.schemas.scene_scope import SceneActionPreflight
from cine_forge.services.creative_brief import build_visual_creative_brief
from cine_forge.services.design_study_backfill import DEFAULT_DESIGN_STUDY_BACKFILL_MODEL


def _project_dir(context: dict[str, Any]) -> Path:
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("render_adapter_v1 requires context.project_dir")
    return Path(project_dir_raw)


def _runtime_params(context: dict[str, Any]) -> dict[str, Any]:
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    return runtime_params if isinstance(runtime_params, dict) else {}


def _selected_render_clip_ids(runtime_params: dict[str, Any]) -> set[str] | None:
    raw_ids = runtime_params.get("render_clip_ids")
    if not isinstance(raw_ids, list):
        return None
    clip_ids = {item.strip() for item in raw_ids if isinstance(item, str) and item.strip()}
    return clip_ids or None


def _scene_action_preflight(runtime_params: dict[str, Any]) -> SceneActionPreflight | None:
    raw = runtime_params.get("scene_action_preflight")
    if isinstance(raw, SceneActionPreflight):
        return raw
    if isinstance(raw, dict):
        try:
            return SceneActionPreflight.model_validate(raw)
        except Exception:
            return None
    return None


def _default_design_study_backfill_enabled(
    *,
    params: dict[str, Any],
    runtime_params: dict[str, Any],
) -> bool:
    raw = params.get("default_design_study_backfill")
    if raw is None:
        raw = runtime_params.get("default_design_study_backfill")
    if raw is None:
        return False
    return _bool_param(raw)


def _default_design_study_backfill_model(
    *,
    params: dict[str, Any],
    runtime_params: dict[str, Any],
    compiler_model: str,
) -> str:
    configured = _optional_string(
        params.get("default_design_study_backfill_model")
        or runtime_params.get("default_design_study_backfill_model")
    )
    if configured:
        return configured
    if compiler_model == "mock":
        return "mock"
    return DEFAULT_DESIGN_STUDY_BACKFILL_MODEL


def _bool_param(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _output_contract(
    *,
    params: dict[str, Any],
    runtime_params: dict[str, Any],
) -> dict[str, Any]:
    prompt_mode = (
        _optional_string(params.get("prompt_mode") or runtime_params.get("prompt_mode")) or "render"
    )
    if prompt_mode == "ai_previz":
        return {
            "prompt_mode": "ai_previz",
            "prompt_artifact_type": "ai_previz_prompt",
            "video_artifact_type": "ai_previz_video",
            "track_type": "ai_previz_video",
            "track_priority": 125,
            "track_note": "AI previz clip for render-unit blocking and camera review.",
            "media_root": "ai_previz_video_media",
            "media_filename": "ai_previz.mp4",
            "preview_mode": "ai_previz",
            "fidelity_intent": "blocking_review",
            "intended_use": ["human_review"],
            "consistency_strategy": _optional_string(
                params.get("consistency_strategy") or runtime_params.get("consistency_strategy")
            )
            or "prompt_only",
            "prompt_profile": _optional_string(
                params.get("prompt_profile") or runtime_params.get("prompt_profile")
            )
            or "standard",
            "default_engine_pack_id": "xai_grok_imagine_video",
            "default_compiler_model": "code",
            "prompt_intent": "Compiled low-fidelity AI previz prompt for scene blocking review.",
            "prompt_rationale": (
                "AI previz prompts stay reviewable so operators can inspect the non-final "
                "house-style instructions CineForge sent downstream."
            ),
            "video_intent": "AI previz clip for render-unit blocking, camera, and motion review.",
            "video_rationale": (
                "AI previz turns reviewed planning artifacts into low-fidelity planning clips "
                "without conflating previz with final render."
            ),
        }
    return {
        "prompt_mode": "render",
        "prompt_artifact_type": "render_prompt",
        "video_artifact_type": "generated_video",
        "track_type": "generated_video",
        "track_priority": 100,
        "track_note": "Scene-level generated video render.",
        "media_root": "generated_video_media",
        "media_filename": "scene_render.mp4",
        "preview_mode": "generated_render",
        "fidelity_intent": "render_preview",
        "intended_use": ["human_review", "ai_conditioning"],
        "consistency_strategy": None,
        "default_engine_pack_id": "google_veo31",
        "default_compiler_model": "gpt-5.4-mini",
        "prompt_intent": "Compiled, provider-ready generation prompt for a scene render.",
        "prompt_rationale": (
            "Prompt artifacts stay immutable and reviewable so operators can inspect "
            "what CineForge actually sent downstream."
        ),
        "video_intent": "Scene-level generated video derived from compiled upstream film intent.",
        "video_rationale": (
            "Render adapter turns reviewed planning artifacts into a playable high-fidelity "
            "preview without mutating upstream creative intent."
        ),
    }


def _track_manifest(inputs: dict[str, Any]) -> TrackManifest:
    payload = inputs.get("track_manifest")
    if not isinstance(payload, dict):
        raise ValueError("render_adapter_v1 requires track_manifest input")
    return TrackManifest.model_validate(payload)


def _shot_plans(
    inputs: dict[str, Any],
    *,
    runtime_params: dict[str, Any] | None = None,
) -> list[ShotPlan]:
    payloads = inputs.get("shot_plan")
    if not isinstance(payloads, list) or not payloads:
        raise ValueError("render_adapter_v1 requires one or more shot_plan inputs")
    payloads = filter_scene_payloads(payloads, runtime_params or {})
    plans = [ShotPlan.model_validate(item) for item in payloads if isinstance(item, dict)]
    if not plans:
        raise ValueError("render_adapter_v1 could not parse any shot_plan inputs")
    return plans


def _build_source_maps(inputs: dict[str, Any]) -> dict[str, Any]:
    project_config = (
        ProjectConfig.model_validate(inputs["project_config"])
        if isinstance(inputs.get("project_config"), dict)
        else None
    )
    intent_mood = (
        IntentMood.model_validate(inputs["intent_mood"])
        if isinstance(inputs.get("intent_mood"), dict)
        else None
    )
    look_and_feel = _scene_payload_map(
        inputs.get("look_and_feel"), LookAndFeel, scene_key="scene_id"
    )
    sound_and_music = _scene_payload_map(
        inputs.get("sound_and_music"), SoundAndMusic, scene_key="scene_id"
    )
    rhythm_and_flow = _scene_payload_map(
        inputs.get("rhythm_and_flow"), RhythmAndFlow, scene_key="scene_id"
    )
    keyframes = _scene_payload_map(inputs.get("keyframe"), KeyframeArtifact, scene_key="scene_id")
    render_clip_plan = _render_clip_plan_map(inputs)
    manifests = _manifest_payload_map(inputs.get("injected_asset_manifest"))
    return {
        "project_config": project_config,
        "intent_mood": intent_mood,
        "creative_brief": build_visual_creative_brief(
            project_config_data=project_config.model_dump(mode="json") if project_config else None,
            intent_mood_data=intent_mood,
            project_manifest=manifests.get(("project", "project")),
        ),
        "look_and_feel": look_and_feel,
        "sound_and_music": sound_and_music,
        "rhythm_and_flow": rhythm_and_flow,
        "render_clip_plan": render_clip_plan,
        "character_and_performance": _performance_by_scene(inputs.get("character_and_performance")),
        "character_bible": _entity_payload_map(
            inputs.get("character_bible"),
            schema=CharacterBible,
            id_keys=("character_id", "name"),
        ),
        "location_bible": _entity_payload_map(
            inputs.get("location_bible"),
            schema=LocationBible,
            id_keys=("location_id", "name"),
        ),
        "keyframes": keyframes,
        "injected_manifests": manifests,
    }


def _render_clip_plan_map(inputs: dict[str, Any]) -> dict[str, RenderClipPlan]:
    payloads: list[Any] = []
    raw_store_payloads = inputs.get("render_clip_plan")
    if isinstance(raw_store_payloads, list):
        payloads.extend(raw_store_payloads)
    raw_stage_payloads = inputs.get("render_clip_planning")
    if isinstance(raw_stage_payloads, list):
        payloads.extend(raw_stage_payloads)

    result: dict[str, RenderClipPlan] = {}
    for item in payloads:
        if not isinstance(item, dict):
            continue
        plan = RenderClipPlan.model_validate(item)
        result[plan.scene_id] = plan
    return result


def _scene_payload_map(
    payload: Any,
    schema: Any,
    *,
    scene_key: str,
) -> dict[str, Any]:
    if not isinstance(payload, list):
        return {}
    result: dict[str, Any] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        scene_id = item.get(scene_key)
        if not isinstance(scene_id, str) or not scene_id:
            continue
        result[scene_id] = schema.model_validate(item)
    return result


def _entity_payload_map(
    payload: Any,
    *,
    schema: Any,
    id_keys: tuple[str, ...],
) -> dict[str, Any]:
    if not isinstance(payload, list):
        return {}
    result: dict[str, Any] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        parsed = schema.model_validate(item)
        for key in id_keys:
            raw = getattr(parsed, key, None)
            if isinstance(raw, str) and raw.strip():
                result[_slugify(raw)] = parsed
    return result


def _performance_by_scene(payload: Any) -> dict[str, list[CharacterAndPerformance]]:
    if not isinstance(payload, list):
        return {}
    result: dict[str, list[CharacterAndPerformance]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        if "entries" in item and isinstance(item["entries"], list):
            scene_id = item.get("scene_id")
            if not isinstance(scene_id, str) or not scene_id:
                continue
            entries = [
                CharacterAndPerformance.model_validate(entry)
                for entry in item["entries"]
                if isinstance(entry, dict)
            ]
            if entries:
                result.setdefault(scene_id, []).extend(entries)
            continue
        parsed = CharacterAndPerformance.model_validate(item)
        result.setdefault(parsed.scene_id, []).append(parsed)
    return result


def _manifest_payload_map(payload: Any) -> dict[tuple[str, str], InjectedAssetManifest]:
    if not isinstance(payload, list):
        return {}
    result: dict[tuple[str, str], InjectedAssetManifest] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        manifest = InjectedAssetManifest.model_validate(item)
        result[(manifest.target_kind, manifest.target_id)] = manifest
    return result
