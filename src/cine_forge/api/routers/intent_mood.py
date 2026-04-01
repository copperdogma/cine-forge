"""Intent / Mood router and creative-brief preview endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter

from cine_forge.api.exceptions import ServiceError
from cine_forge.api.models import (
    IntentMoodInput,
    IntentMoodResponse,
    IntentMoodSuggestion,
    PropagatedGroupResponse,
    PropagateRequest,
    PropagationResponse,
    ScriptContextResponse,
    StylePresetResponse,
)
from cine_forge.artifacts import ArtifactStore
from cine_forge.presets import list_presets, load_preset
from cine_forge.schemas import ArtifactMetadata, IntentMood, VisualCreativeBrief
from cine_forge.services.creative_brief import build_visual_creative_brief
from cine_forge.services.injected_assets import InjectedAssetService
from cine_forge.services.intent_mood import propagate_intent

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}", tags=["intent-mood"])

_service: OperatorConsoleService | None = None


def set_service(svc: OperatorConsoleService) -> None:
    global _service  # noqa: PLW0603
    _service = svc


def _get_project_path(project_id: str) -> Path:
    if _service is None:
        raise ServiceError(
            code="intent_router_uninitialized",
            message="Intent router not initialized.",
            status_code=500,
        )
    return _service.require_project_path(project_id)


def _get_store(project_id: str) -> ArtifactStore:
    return ArtifactStore(project_dir=_get_project_path(project_id))


def _intent_response(intent: IntentMood, *, version: int) -> IntentMoodResponse:
    return IntentMoodResponse(
        scope=intent.scope,
        scene_id=intent.scene_id,
        mood_descriptors=intent.mood_descriptors,
        reference_films=intent.reference_films,
        filmmaker_anchors=intent.filmmaker_anchors,
        style_preset_id=intent.style_preset_id,
        natural_language_intent=intent.natural_language_intent,
        look_notes=intent.look_notes,
        user_approved=intent.user_approved,
        version=version,
    )


def _load_current_intent(
    store: ArtifactStore, *, scene_id: str | None
) -> tuple[IntentMood, int] | None:
    entity_id = scene_id or "project"
    refs = store.list_versions(artifact_type="intent_mood", entity_id=entity_id)
    if not refs:
        return None
    latest = refs[-1]
    artifact = store.load_artifact(latest)
    return IntentMood.model_validate(artifact.data), latest.version


def _project_creative_brief(store: ArtifactStore, project_id: str) -> VisualCreativeBrief | None:
    project_config_ref = store.latest_ref("project_config", "project")
    project_config_data = (
        store.load_artifact(project_config_ref).data if project_config_ref is not None else None
    )
    current = _load_current_intent(store, scene_id=None)
    intent = current[0] if current is not None else None
    project_manifest = InjectedAssetService(_get_project_path(project_id)).get_manifest(
        target_kind="project",
        target_id="project",
    )
    return build_visual_creative_brief(
        project_config_data=project_config_data if isinstance(project_config_data, dict) else None,
        intent_mood_data=intent,
        project_manifest=project_manifest,
    )


@router.get("/style-presets", response_model=list[StylePresetResponse])
async def list_style_presets(project_id: str) -> list[StylePresetResponse]:
    _get_project_path(project_id)
    return [
        StylePresetResponse(
            preset_id=p.preset_id,
            display_name=p.display_name,
            description=p.description,
            mood_descriptors=p.mood_descriptors,
            reference_films=p.reference_films,
            thumbnail_emoji=p.thumbnail_emoji,
            concern_group_ids=list(p.concern_group_hints.keys()),
        )
        for p in list_presets()
    ]


@router.get("/intent-mood", response_model=IntentMoodResponse | None)
async def get_intent_mood(
    project_id: str, scene_id: str | None = None
) -> IntentMoodResponse | None:
    current = _load_current_intent(_get_store(project_id), scene_id=scene_id)
    if current is None:
        return None
    intent, version = current
    return _intent_response(intent, version=version)


@router.post("/intent-mood", response_model=IntentMoodResponse)
async def save_intent_mood(project_id: str, request: IntentMoodInput) -> IntentMoodResponse:
    store = _get_store(project_id)
    entity_id = request.scene_id or "project"

    intent = IntentMood(
        scope=request.scope,
        scene_id=request.scene_id,
        mood_descriptors=request.mood_descriptors,
        reference_films=request.reference_films,
        filmmaker_anchors=request.filmmaker_anchors,
        style_preset_id=request.style_preset_id,
        natural_language_intent=request.natural_language_intent,
        look_notes=request.look_notes,
        user_approved=False,
    )

    refs = store.list_versions(artifact_type="intent_mood", entity_id=entity_id)
    lineage = [refs[-1]] if refs else []
    metadata = ArtifactMetadata(
        lineage=lineage,
        intent="Set creative intent and mood",
        rationale="User-authored project taste inputs and prompt-transparent brief inputs.",
        confidence=1.0,
        source="human",
        producing_module="operator_console.intent_mood",
    )
    ref = store.save_artifact(
        artifact_type="intent_mood",
        entity_id=entity_id,
        data=intent.model_dump(mode="json"),
        metadata=metadata,
    )
    return _intent_response(intent, version=ref.version)


@router.get("/intent-mood/creative-brief", response_model=VisualCreativeBrief | None)
async def get_creative_brief(project_id: str) -> VisualCreativeBrief | None:
    return _project_creative_brief(_get_store(project_id), project_id)


@router.post("/intent-mood/propagate", response_model=PropagationResponse)
async def propagate_mood(project_id: str, request: PropagateRequest) -> PropagationResponse:
    store = _get_store(project_id)
    current = _load_current_intent(store, scene_id=request.scene_id)
    if current is None:
        raise ServiceError(
            code="no_intent_mood",
            message="No intent/mood set. Save intent/mood before propagating.",
            status_code=400,
        )
    intent, _version = current

    preset = load_preset(intent.style_preset_id) if intent.style_preset_id else None

    script_context = None
    bible_refs = store.list_versions(artifact_type="script_bible", entity_id="project")
    if bible_refs:
        script_context = store.load_artifact(bible_refs[-1]).data.get("summary", "")

    model = request.model or "claude-sonnet-4-6"
    result, _cost = propagate_intent(
        intent=intent,
        script_context=script_context,
        scene_id=request.scene_id,
        preset=preset,
        model=model,
    )

    artifacts_created: list[str] = []
    concern_groups = {
        "look_and_feel": result.look_and_feel,
        "sound_and_music": result.sound_and_music,
        "rhythm_and_flow": result.rhythm_and_flow,
        "character_and_performance": result.character_and_performance,
        "story_world": result.story_world,
    }

    for group_id, group_data in concern_groups.items():
        if group_data is None:
            continue

        artifact_data = dict(group_data.fields)
        artifact_data["user_approved"] = False
        if request.scene_id:
            artifact_data["scope"] = "scene"
            artifact_data["scene_id"] = request.scene_id
        else:
            artifact_data["scope"] = "project"

        artifact_entity = request.scene_id or "project"
        existing = store.list_versions(artifact_type=group_id, entity_id=artifact_entity)
        metadata = ArtifactMetadata(
            lineage=[existing[-1]] if existing else [],
            intent="Propagated from intent/mood layer",
            rationale=group_data.rationale,
            confidence=result.confidence,
            source="ai",
            producing_module="intent_mood.propagation",
        )
        store.save_artifact(
            artifact_type=group_id,
            entity_id=artifact_entity,
            data=artifact_data,
            metadata=metadata,
        )
        artifacts_created.append(group_id)

    response_groups: dict[str, PropagatedGroupResponse | None] = {}
    for group_id, group_data in concern_groups.items():
        response_groups[group_id] = (
            PropagatedGroupResponse(fields=group_data.fields, rationale=group_data.rationale)
            if group_data is not None
            else None
        )

    return PropagationResponse(
        **response_groups,
        overall_rationale=result.overall_rationale,
        confidence=result.confidence,
        artifacts_created=artifacts_created,
    )


@router.get("/script-context", response_model=ScriptContextResponse | None)
async def get_script_context(project_id: str) -> ScriptContextResponse | None:
    store = _get_store(project_id)
    refs = store.list_versions(artifact_type="script_bible", entity_id="project")
    if not refs:
        return None
    data = store.load_artifact(refs[-1]).data
    raw_themes = data.get("themes", [])
    theme_names = [t.get("theme", str(t)) if isinstance(t, dict) else str(t) for t in raw_themes]
    return ScriptContextResponse(
        title=data.get("title", "Untitled"),
        logline=data.get("logline", ""),
        genre=data.get("genre", ""),
        tone=data.get("tone", ""),
        themes=theme_names[:8],
    )


@router.post("/intent-mood/suggest", response_model=IntentMoodSuggestion)
async def suggest_intent_mood(project_id: str) -> IntentMoodSuggestion:
    from cine_forge.ai.llm import call_llm

    store = _get_store(project_id)
    refs = store.list_versions(artifact_type="script_bible", entity_id="project")
    if not refs:
        raise ServiceError(
            code="no_script_bible",
            message="No script bible found. Run ingest first.",
            status_code=400,
        )

    artifact = store.load_artifact(refs[-1])
    data = artifact.data
    preset_catalog = "\n".join(
        (
            f"- {preset.preset_id}: {preset.display_name} — {preset.description} "
            f"Moods: {', '.join(preset.mood_descriptors)}. "
            f"Films: {', '.join(preset.reference_films)}."
        )
        for preset in list_presets()
    )
    raw_themes = data.get("themes", [])
    theme_names = [t.get("theme", str(t)) if isinstance(t, dict) else str(t) for t in raw_themes]

    prompt = f"""\
You are a creative film director. Given a script's metadata, suggest the best creative mood and
style for this project.

SCRIPT CONTEXT:
- Title: {data.get("title", "Untitled")}
- Genre: {data.get("genre", "Unknown")}
- Tone: {data.get("tone", "Unknown")}
- Themes: {', '.join(theme_names[:5]) or 'None specified'}
- Logline: {data.get("logline", "")}

AVAILABLE STYLE PRESETS:
{preset_catalog}

Return JSON matching the IntentMoodSuggestion schema. Keep filmmaker_anchors and look_notes
empty unless the script context strongly supports them.
"""

    result, _meta = call_llm(
        prompt=prompt,
        model="claude-haiku-4-5-20251001",
        response_schema=IntentMoodSuggestion,
        max_tokens=600,
        temperature=0.2,
    )
    return IntentMoodSuggestion.model_validate(result)
