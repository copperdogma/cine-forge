"""Shared helpers for transcript indexing and deterministic memory lookup."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cine_forge.api.chat_store import ChatStore
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactRef, Conversation, Decision, Suggestion, TranscriptIndexEntry

CHAT_TRANSCRIPT_TYPES: frozenset[str] = frozenset(
    {"user_message", "user_action", "ai_response", "ai_welcome", "ai_suggestion"}
)
ROLE_ALIASES: dict[str, str] = {
    "director": "director",
    "script supervisor": "script_supervisor",
    "visual architect": "visual_architect",
    "editorial architect": "editorial_architect",
    "sound designer": "sound_designer",
    "story editor": "story_editor",
    "assistant": "assistant",
}
SUMMARY_FAILURE_PREFIX = "[Earlier conversation summary unavailable"

_PAGE_CONTEXT_RE = re.compile(r"User is viewing (\w+)/([\w-]+)")


def build_transcript_entries(
    *,
    store: ArtifactStore,
    chat_store: ChatStore,
    project_dir: Path,
) -> list[TranscriptIndexEntry]:
    entries = _chat_entries(store=store, chat_store=chat_store, project_dir=project_dir)
    entries.extend(_conversation_entries(store=store))
    return sorted(entries, key=lambda entry: (entry.timestamp, entry.entry_id))


def transcript_lineage(store: ArtifactStore) -> list[ArtifactRef]:
    lineage: list[ArtifactRef] = []
    for entity_id in store.list_entities("conversation"):
        ref = store.latest_ref("conversation", entity_id)
        if ref is not None:
            lineage.append(ref)
    return lineage


def iter_decisions(store: ArtifactStore) -> list[tuple[ArtifactRef, Decision, datetime | None]]:
    items: list[tuple[ArtifactRef, Decision, datetime | None]] = []
    for entity_id in store.list_entities("decision"):
        ref = store.latest_ref("decision", entity_id)
        if ref is None:
            continue
        artifact = store.load_artifact(ref)
        items.append((ref, Decision.model_validate(artifact.data), artifact.metadata.created_at))
    items.sort(key=lambda item: item[2] or datetime.min.replace(tzinfo=UTC), reverse=True)
    return items


def iter_suggestions(store: ArtifactStore) -> list[tuple[ArtifactRef, Suggestion, datetime | None]]:
    items: list[tuple[ArtifactRef, Suggestion, datetime | None]] = []
    for entity_id in store.list_entities("suggestion"):
        ref = store.latest_ref("suggestion", entity_id)
        if ref is None:
            continue
        artifact = store.load_artifact(ref)
        items.append((ref, Suggestion.model_validate(artifact.data), artifact.metadata.created_at))
    items.sort(key=lambda item: item[2] or datetime.min.replace(tzinfo=UTC), reverse=True)
    return items


def entry_matches_artifact(
    entry: TranscriptIndexEntry,
    *,
    artifact_type: str | None,
    entity_id: str | None,
) -> bool:
    if artifact_type is None and entity_id is None:
        return True
    for ref in entry.related_artifacts:
        if artifact_type is not None and ref.artifact_type != artifact_type:
            continue
        if entity_id is not None and ref.entity_id != entity_id:
            continue
        return True
    if entity_id and (entity_id in entry.scene_ids or entity_id in entry.entity_ids):
        return True
    return False


def classify_query(question: str) -> str:
    lowered = question.lower()
    if "decision" in lowered:
        return "decisions"
    if "current state" in lowered or "state of" in lowered:
        return "artifact_state"
    if "deferred" in lowered or "suggestion" in lowered:
        return "suggestions"
    if "discuss" in lowered or "conversation" in lowered:
        return "conversations"
    return "transcript_search"


def infer_scene_id(question: str) -> str | None:
    match = re.search(r"\bscene\s+(\d+)\b", question.lower())
    if not match:
        return None
    return f"scene_{int(match.group(1))}"


def resolve_scene_id(scene_id: str | None, store: ArtifactStore) -> str | None:
    if scene_id is None:
        return None
    if store.latest_ref("scene", scene_id) is not None:
        return scene_id

    match = re.search(r"(\d+)$", scene_id)
    if not match:
        return scene_id
    target_number = int(match.group(1))

    for entity_id in store.list_entities("scene"):
        candidate_match = re.search(r"(\d+)$", entity_id)
        if candidate_match and int(candidate_match.group(1)) == target_number:
            return entity_id
    return scene_id


def infer_entity_id(question: str, store: ArtifactStore) -> str | None:
    lowered = normalize_text(question)
    candidates: list[tuple[int, str]] = []

    for entity_id in store.list_entities("bible_manifest"):
        for alias in _entity_aliases(entity_id):
            if alias in lowered:
                candidates.append((len(alias), entity_id))

    for entity_id in store.list_entities("scene"):
        alias = normalize_text(entity_id.replace("_", " "))
        if alias in lowered:
            candidates.append((len(alias), entity_id))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def infer_participants(question: str) -> list[str]:
    lowered = question.lower()
    participants = [role_id for alias, role_id in ROLE_ALIASES.items() if alias in lowered]
    ordered: list[str] = []
    for participant in participants:
        if participant not in ordered:
            ordered.append(participant)
    return ordered


def extract_focus_text(question: str) -> str:
    lowered = question.lower()
    for marker in ("about ", "for ", "of "):
        if marker in lowered:
            return question[lowered.index(marker) + len(marker):].strip(" ?.")
    return ""


def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def messages_signature(messages: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        [{"role": message.get("role"), "content": message.get("content")} for message in messages],
        sort_keys=True,
        ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def entries_signature(entries: list[TranscriptIndexEntry]) -> str:
    payload = json.dumps(
        [entry.model_dump(mode="json") for entry in entries],
        sort_keys=True,
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def timestamp_from_chat(raw_timestamp: Any) -> datetime:
    if isinstance(raw_timestamp, (int, float)):
        return datetime.fromtimestamp(raw_timestamp / 1000.0, UTC)
    return datetime.now(UTC)


def speaker_from_chat_type(message_type: str) -> str:
    if message_type.startswith("user"):
        return "user"
    return "assistant"


def context_metadata_from_page_context(
    page_context: Any,
    *,
    store: ArtifactStore,
) -> tuple[list[ArtifactRef], list[str], list[str]]:
    if not isinstance(page_context, str):
        return [], [], []
    match = _PAGE_CONTEXT_RE.search(page_context)
    if not match:
        return [], [], []

    section, identifier = match.groups()
    entity_id = identifier.replace("-", "_")
    refs = _context_refs(store=store, section=section, entity_id=entity_id)
    if section == "scenes":
        scene_ids = [ref.entity_id for ref in refs if ref.entity_id] or [entity_id]
        return refs, scene_ids, []
    entity_ids = [ref.entity_id for ref in refs if ref.entity_id] or [entity_id]
    return refs, [], entity_ids


def chat_message_metadata(
    message: dict[str, Any],
    *,
    store: ArtifactStore,
) -> tuple[list[ArtifactRef], list[str], list[str]]:
    related_artifacts, scene_ids, entity_ids = context_metadata_from_page_context(
        message.get("pageContext"),
        store=store,
    )

    structured_refs = _chat_message_refs(message, store=store)
    if structured_refs:
        related_artifacts = _dedupe_refs([*related_artifacts, *structured_refs])
        scene_ids = sorted({*scene_ids, *scene_ids_from_refs(related_artifacts)})
        entity_ids = sorted({*entity_ids, *entity_ids_from_refs(related_artifacts)})

    return related_artifacts, scene_ids, entity_ids


def scene_ids_from_refs(refs: list[ArtifactRef]) -> list[str]:
    return sorted(
        {ref.entity_id for ref in refs if ref.entity_id and ref.entity_id.startswith("scene_")}
    )


def entity_ids_from_refs(refs: list[ArtifactRef]) -> list[str]:
    return sorted(
        {ref.entity_id for ref in refs if ref.entity_id and not ref.entity_id.startswith("scene_")}
    )


def _chat_entries(
    *,
    store: ArtifactStore,
    chat_store: ChatStore,
    project_dir: Path,
) -> list[TranscriptIndexEntry]:
    entries: list[TranscriptIndexEntry] = []
    for message in chat_store.list_messages(project_dir):
        message_type = str(message.get("type") or "")
        if message_type not in CHAT_TRANSCRIPT_TYPES:
            continue
        text = str(message.get("content") or "").strip()
        if not text:
            continue

        related_artifacts, scene_ids, entity_ids = chat_message_metadata(message, store=store)
        entries.append(
            TranscriptIndexEntry(
                entry_id=str(message.get("id") or f"chat-{uuid.uuid4().hex[:12]}"),
                source_kind="chat_message",
                source_id=str(message.get("id") or "chat-message"),
                speaker=str(message.get("speaker") or speaker_from_chat_type(message_type)),
                text=text,
                timestamp=timestamp_from_chat(message.get("timestamp")),
                related_artifacts=related_artifacts,
                scene_ids=scene_ids,
                entity_ids=entity_ids,
            )
        )
    return entries


def _conversation_entries(*, store: ArtifactStore) -> list[TranscriptIndexEntry]:
    entries: list[TranscriptIndexEntry] = []
    for entity_id in store.list_entities("conversation"):
        ref = store.latest_ref("conversation", entity_id)
        if ref is None:
            continue
        artifact = store.load_artifact(ref)
        conversation = Conversation.model_validate(artifact.data)
        outcome_refs = _conversation_outcome_refs(store=store, conversation=conversation)
        for index, turn in enumerate(conversation.turns):
            related_artifacts = _dedupe_refs(
                [*turn.references, *conversation.related_artifacts, *outcome_refs]
            )
            entries.append(
                TranscriptIndexEntry(
                    entry_id=f"{conversation.conversation_id}:{index}",
                    source_kind="conversation_turn",
                    source_id=conversation.conversation_id,
                    speaker=turn.role_id,
                    text=turn.content,
                    timestamp=turn.timestamp,
                    related_artifacts=related_artifacts,
                    scene_ids=scene_ids_from_refs(related_artifacts),
                    entity_ids=entity_ids_from_refs(related_artifacts),
                )
            )
    return entries


def _conversation_outcome_refs(
    *,
    store: ArtifactStore,
    conversation: Conversation,
) -> list[ArtifactRef]:
    refs: list[ArtifactRef] = []
    for decision_id in conversation.outcome_decisions:
        ref = store.latest_ref("decision", decision_id)
        if ref is not None:
            refs.append(ref)
    for suggestion_id in conversation.outcome_suggestions:
        ref = store.latest_ref("suggestion", suggestion_id)
        if ref is not None:
            refs.append(ref)
    return _dedupe_refs(refs)


def _context_refs(
    *,
    store: ArtifactStore,
    section: str,
    entity_id: str,
) -> list[ArtifactRef]:
    ref: ArtifactRef | None = None
    if section == "scenes":
        ref = store.latest_ref("scene", entity_id)
    elif section == "characters":
        prefixed = entity_id if entity_id.startswith("character_") else f"character_{entity_id}"
        ref = store.latest_ref("bible_manifest", prefixed)
    elif section == "locations":
        prefixed = entity_id if entity_id.startswith("location_") else f"location_{entity_id}"
        ref = store.latest_ref("bible_manifest", prefixed)
    elif section == "props":
        prefixed = entity_id if entity_id.startswith("prop_") else f"prop_{entity_id}"
        ref = store.latest_ref("bible_manifest", prefixed)
    return [ref] if ref is not None else []


def _chat_message_refs(message: dict[str, Any], *, store: ArtifactStore) -> list[ArtifactRef]:
    refs: list[ArtifactRef] = []

    raw_refs = message.get("relatedArtifacts") or message.get("related_artifacts") or []
    if isinstance(raw_refs, list):
        for raw_ref in raw_refs:
            if not isinstance(raw_ref, dict):
                continue
            try:
                refs.append(ArtifactRef.model_validate(raw_ref))
            except Exception:
                continue

    raw_decision_ids = message.get("decisionIds") or message.get("decision_ids") or []
    if isinstance(raw_decision_ids, list):
        for decision_id in raw_decision_ids:
            if not isinstance(decision_id, str) or not decision_id:
                continue
            ref = store.latest_ref("decision", decision_id)
            if ref is not None:
                refs.append(ref)

    raw_suggestion_ids = message.get("suggestionIds") or message.get("suggestion_ids") or []
    if isinstance(raw_suggestion_ids, list):
        for suggestion_id in raw_suggestion_ids:
            if not isinstance(suggestion_id, str) or not suggestion_id:
                continue
            ref = store.latest_ref("suggestion", suggestion_id)
            if ref is not None:
                refs.append(ref)

    return _dedupe_refs(refs)


def _entity_aliases(entity_id: str) -> set[str]:
    aliases = {normalize_text(entity_id.replace("_", " "))}
    if "_" in entity_id:
        aliases.add(normalize_text(entity_id.split("_", 1)[1].replace("_", " ")))
    return {alias for alias in aliases if alias}


def _dedupe_refs(refs: list[ArtifactRef]) -> list[ArtifactRef]:
    seen: set[tuple[str, str | None, int, str]] = set()
    ordered: list[ArtifactRef] = []
    for ref in refs:
        key = (ref.artifact_type, ref.entity_id, ref.version, ref.path)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(ref)
    return ordered
