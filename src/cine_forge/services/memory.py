"""Transcript indexing, canonical memory query, and working-memory persistence."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cine_forge.api.chat_store import ChatStore
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    Decision,
    MemoryQueryEvidence,
    MemoryQueryRequest,
    MemoryQueryResult,
    MemorySettings,
    MemorySettingsUpdate,
    Suggestion,
    TranscriptIndex,
    TranscriptSearchRequest,
    TranscriptSearchResponse,
    WorkingMemoryResetRequest,
    WorkingMemoryResetResponse,
    WorkingMemorySummary,
)
from cine_forge.services.memory_support import (
    SUMMARY_FAILURE_PREFIX,
    build_transcript_entries,
    classify_query,
    entries_signature,
    entry_matches_artifact,
    extract_focus_text,
    infer_entity_id,
    infer_participants,
    infer_scene_id,
    iter_decisions,
    iter_suggestions,
    messages_signature,
    normalize_text,
    resolve_scene_id,
    transcript_lineage,
)


class MemoryService:
    """Project-scoped transcript indexing, search, and working-memory persistence."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.store = ArtifactStore(project_dir=project_dir)
        self.chat_store = ChatStore()

    def get_settings(self) -> MemorySettings:
        project_json = self._read_project_json()
        raw_settings = project_json.get("memory_settings", {})
        if not isinstance(raw_settings, dict):
            return MemorySettings()
        return MemorySettings.model_validate(raw_settings)

    def update_settings(self, update: MemorySettingsUpdate) -> MemorySettings:
        current = self.get_settings().model_dump(mode="json")
        for key, value in update.model_dump(exclude_unset=True).items():
            if value is not None:
                current[key] = value
        settings = MemorySettings.model_validate(current)
        project_json = self._read_project_json()
        project_json["memory_settings"] = settings.model_dump(mode="json")
        self._write_project_json(project_json)
        return settings

    def is_working_memory_enabled(self, role_id: str) -> bool:
        if role_id == "director":
            return True
        if role_id == "script_supervisor":
            return self.get_settings().script_supervisor_enabled
        return False

    def ensure_transcript_index(self) -> tuple[ArtifactRef | None, TranscriptIndex]:
        entries = build_transcript_entries(
            store=self.store,
            chat_store=self.chat_store,
            project_dir=self.project_dir,
        )
        source_signature = entries_signature(entries)
        latest_ref = self.store.latest_ref("transcript_index", "project")
        if latest_ref is not None:
            latest_artifact = self.store.load_artifact(latest_ref)
            latest_index = TranscriptIndex.model_validate(latest_artifact.data)
            if latest_index.source_signature == source_signature:
                return latest_ref, latest_index

        index = TranscriptIndex(
            index_id=f"transcript-index-{uuid.uuid4().hex[:12]}",
            source_signature=source_signature,
            entry_count=len(entries),
            entries=entries,
        )
        metadata = ArtifactMetadata(
            lineage=transcript_lineage(self.store),
            intent="Materialize a searchable index over project transcripts.",
            rationale="Deterministic search over chat and inter-role conversation history.",
            confidence=1.0,
            source="code",
            producing_module="memory_service_v1",
        )
        ref = self.store.save_artifact(
            artifact_type="transcript_index",
            entity_id="project",
            data=index.model_dump(mode="json"),
            metadata=metadata,
        )
        return ref, index

    def search_transcripts(self, request: TranscriptSearchRequest) -> TranscriptSearchResponse:
        index_ref, index = self.ensure_transcript_index()
        entries = index.entries

        if request.query:
            needle = normalize_text(request.query)
            entries = [entry for entry in entries if needle in normalize_text(entry.text)]
        if request.participants:
            allowed = {
                participant.strip().lower()
                for participant in request.participants
                if participant.strip()
            }
            entries = [entry for entry in entries if entry.speaker.strip().lower() in allowed]
        if request.scene_id:
            entries = [entry for entry in entries if request.scene_id in entry.scene_ids]
        if request.entity_id:
            entries = [entry for entry in entries if request.entity_id in entry.entity_ids]
        if request.artifact_entity_id or request.artifact_type:
            entries = [
                entry
                for entry in entries
                if self._entry_matches_artifact_request(
                    entry,
                    artifact_type=request.artifact_type,
                    entity_id=request.artifact_entity_id,
                )
            ]
        if request.start_at:
            entries = [entry for entry in entries if entry.timestamp >= request.start_at]
        if request.end_at:
            entries = [entry for entry in entries if entry.timestamp <= request.end_at]

        entries = sorted(entries, key=lambda entry: entry.timestamp, reverse=True)
        return TranscriptSearchResponse(
            index_ref=index_ref,
            total_results=len(entries),
            entries=entries[: request.limit],
        )

    def query_memory(self, request: MemoryQueryRequest) -> MemoryQueryResult:
        question = request.question.strip()
        scene_id = resolve_scene_id(request.scene_id or infer_scene_id(question), self.store)
        entity_id = request.entity_id or infer_entity_id(question, self.store)
        query_type = classify_query(question)

        if query_type == "decisions":
            return self._query_decisions(question=question, scene_id=scene_id, entity_id=entity_id)
        if query_type == "artifact_state":
            return self._query_artifact_state(
                question=question,
                artifact_type=request.artifact_type,
                entity_id=entity_id,
            )
        if query_type == "suggestions":
            return self._query_suggestions(
                question=question,
                scene_id=scene_id,
                entity_id=entity_id,
            )
        if query_type == "conversations":
            participants = request.participants or infer_participants(question)
            focus = extract_focus_text(question)
            search = self.search_transcripts(
                TranscriptSearchRequest(
                    query=focus or None,
                    participants=participants,
                    scene_id=scene_id,
                    entity_id=entity_id,
                    limit=request.max_results,
                )
            )
            return MemoryQueryResult(
                query_type="conversations",
                question=question,
                answer=self._conversation_answer(search, participants, focus),
                evidences=[
                    MemoryQueryEvidence(
                        source_kind="transcript",
                        summary=entry.text,
                        timestamp=entry.timestamp,
                    )
                    for entry in search.entries
                ],
            )

        search = self.search_transcripts(
            TranscriptSearchRequest(
                query=extract_focus_text(question) or question,
                participants=request.participants,
                scene_id=scene_id,
                entity_id=entity_id,
                limit=request.max_results,
            )
        )
        return MemoryQueryResult(
            query_type="transcript_search",
            question=question,
            answer=self._transcript_search_answer(search),
            evidences=[
                MemoryQueryEvidence(
                    source_kind="transcript",
                    summary=entry.text,
                    timestamp=entry.timestamp,
                )
                for entry in search.entries
            ],
        )

    def compact_messages(
        self,
        *,
        role_id: str,
        messages: list[dict[str, Any]],
        keep_recent: int,
        summarizer: Callable[[list[dict[str, Any]], str | None], str],
    ) -> list[dict[str, Any]]:
        if not self.is_working_memory_enabled(role_id):
            return messages
        if len(messages) <= keep_recent:
            return messages

        prefix = messages[:-keep_recent]
        recent = messages[-keep_recent:]
        prefix_hash = messages_signature(prefix)

        latest_ref, latest_summary = self.latest_working_memory_summary(role_id)
        base_summary: str | None = None
        base_count = 0
        lineage: list[ArtifactRef] = [latest_ref] if latest_ref is not None else []

        if latest_summary and latest_summary.summary_text and latest_summary.reset_at is None:
            if latest_summary.source_message_count <= len(prefix):
                covered = prefix[: latest_summary.source_message_count]
                if messages_signature(covered) == latest_summary.covered_through_hash:
                    base_summary = latest_summary.summary_text
                    base_count = latest_summary.source_message_count

        if base_summary is not None and base_count == len(prefix):
            summary_text = base_summary
        else:
            delta = prefix[base_count:]
            summary_text = summarizer(delta, base_summary)
            if summary_text and not summary_text.startswith(SUMMARY_FAILURE_PREFIX):
                self._save_working_memory_summary(
                    WorkingMemorySummary(
                        summary_id=f"wmem-{uuid.uuid4().hex[:12]}",
                        role_id=role_id,  # type: ignore[arg-type]
                        summary_text=summary_text,
                        source_message_count=len(prefix),
                        covered_through_hash=prefix_hash,
                        recent_message_count=len(recent),
                    ),
                    lineage=lineage,
                    rationale=f"Persist working-memory summary for role '{role_id}'.",
                )

        if not summary_text:
            return messages
        return [
            {
                "role": "user",
                "content": "[Conversation summary — earlier messages condensed]\n\n" + summary_text,
            },
            *recent,
        ]

    def reset_working_memory(
        self,
        request: WorkingMemoryResetRequest,
    ) -> WorkingMemoryResetResponse:
        latest_ref, _ = self.latest_working_memory_summary(request.role_id)
        summary = WorkingMemorySummary(
            summary_id=f"wmem-{uuid.uuid4().hex[:12]}",
            role_id=request.role_id,
            summary_text="",
            source_message_count=0,
            covered_through_hash="",
            recent_message_count=0,
            reset_at=datetime.now(UTC),
        )
        ref = self._save_working_memory_summary(
            summary,
            lineage=[latest_ref] if latest_ref else [],
            rationale=(
                request.reason
                or f"Reset working-memory checkpoint for role '{request.role_id}'."
            ),
        )
        return WorkingMemoryResetResponse(summary_ref=ref, summary=summary)

    def latest_working_memory_summary(
        self,
        role_id: str,
    ) -> tuple[ArtifactRef | None, WorkingMemorySummary | None]:
        ref = self.store.latest_ref("working_memory_summary", role_id)
        if ref is None:
            return None, None
        artifact = self.store.load_artifact(ref)
        return ref, WorkingMemorySummary.model_validate(artifact.data)

    def _query_decisions(
        self,
        *,
        question: str,
        scene_id: str | None,
        entity_id: str | None,
    ) -> MemoryQueryResult:
        matches = []
        for ref, decision, created_at in iter_decisions(self.store):
            if scene_id and not any(
                artifact.entity_id == scene_id for artifact in decision.affected_artifacts
            ):
                continue
            if entity_id and not any(
                artifact.entity_id == entity_id for artifact in decision.affected_artifacts
            ):
                continue
            matches.append((ref, decision, created_at))

        if not matches:
            return MemoryQueryResult(
                query_type="decisions",
                question=question,
                answer="No matching decisions were found in canonical memory.",
                evidences=[],
            )

        evidences = [
            MemoryQueryEvidence(
                source_kind="artifact",
                summary=f"{decision.summary} Rationale: {decision.rationale}",
                artifact_ref=ref,
                timestamp=created_at,
            )
            for ref, decision, created_at in matches[:5]
        ]
        answer = "; ".join(decision.summary for _, decision, _ in matches[:3])
        return MemoryQueryResult(
            query_type="decisions",
            question=question,
            answer=f"Found {len(matches)} decision(s): {answer}",
            evidences=evidences,
        )

    def _query_artifact_state(
        self,
        *,
        question: str,
        artifact_type: str | None,
        entity_id: str | None,
    ) -> MemoryQueryResult:
        if not entity_id:
            return MemoryQueryResult(
                query_type="artifact_state",
                question=question,
                answer="Artifact-state queries need an entity_id or a more specific focus.",
                evidences=[],
            )

        latest_match: tuple[ArtifactRef, dict[str, Any], datetime | None] | None = None
        candidate_types = (
            [artifact_type]
            if artifact_type
            else self._candidate_artifact_types(entity_id)
        )
        for candidate_type in candidate_types:
            if candidate_type is None:
                continue
            ref = self.store.latest_ref(
                candidate_type,
                self._resolve_artifact_entity_id(candidate_type, entity_id),
            )
            if ref is None:
                continue
            artifact = self.store.load_artifact(ref)
            created_at = artifact.metadata.created_at
            previous_at = latest_match[2] if latest_match is not None else None
            latest_seen = previous_at or datetime.min.replace(tzinfo=UTC)
            if latest_match is None or (created_at and created_at > latest_seen):
                latest_match = (ref, artifact.data, created_at)

        if latest_match is None:
            return MemoryQueryResult(
                query_type="artifact_state",
                question=question,
                answer=f"No matching artifact state found for '{entity_id}'.",
                evidences=[],
            )

        ref, data, created_at = latest_match
        summary = self._artifact_state_summary(ref, data)
        return MemoryQueryResult(
            query_type="artifact_state",
            question=question,
            answer=summary,
            evidences=[
                MemoryQueryEvidence(
                    source_kind="artifact",
                    summary=summary,
                    artifact_ref=ref,
                    timestamp=created_at,
                )
            ],
        )

    def _query_suggestions(
        self,
        *,
        question: str,
        scene_id: str | None,
        entity_id: str | None,
    ) -> MemoryQueryResult:
        matches = []
        for ref, suggestion, created_at in iter_suggestions(self.store):
            if suggestion.status.value != "deferred":
                continue
            if scene_id and suggestion.related_scene_id != scene_id:
                continue
            if entity_id and suggestion.related_entity_id != entity_id:
                continue
            matches.append((ref, suggestion, created_at))

        if not matches:
            return MemoryQueryResult(
                query_type="suggestions",
                question=question,
                answer="No deferred suggestions matched that query.",
                evidences=[],
            )

        evidences = [
            MemoryQueryEvidence(
                source_kind="artifact",
                summary=f"{suggestion.proposal} Rationale: {suggestion.rationale}",
                artifact_ref=ref,
                timestamp=created_at,
            )
            for ref, suggestion, created_at in matches[:5]
        ]
        answer = "; ".join(suggestion.proposal for _, suggestion, _ in matches[:3])
        return MemoryQueryResult(
            query_type="suggestions",
            question=question,
            answer=f"Found {len(matches)} deferred suggestion(s): {answer}",
            evidences=evidences,
        )

    @staticmethod
    def _candidate_artifact_types(entity_id: str) -> list[str]:
        if entity_id == "project":
            return ["project_config", "scene_index", "script_bible"]
        if entity_id.startswith("scene_"):
            return ["scene", "scene_index"]
        if entity_id.startswith("character_"):
            return ["character_bible", "bible_manifest"]
        if entity_id.startswith("location_"):
            return ["location_bible", "bible_manifest"]
        if entity_id.startswith("prop_"):
            return ["prop_bible", "bible_manifest"]
        return [
            "character_bible",
            "location_bible",
            "prop_bible",
            "bible_manifest",
            "scene",
            "scene_index",
            "project_config",
        ]

    @staticmethod
    def _resolve_artifact_entity_id(artifact_type: str, entity_id: str) -> str:
        prefix_map = {
            "character_bible": "character_",
            "location_bible": "location_",
            "prop_bible": "prop_",
        }
        prefix = prefix_map.get(artifact_type)
        if prefix and entity_id.startswith(prefix):
            return entity_id.removeprefix(prefix)
        return entity_id

    @staticmethod
    def _conversation_answer(
        search: TranscriptSearchResponse,
        participants: list[str],
        query: str,
    ) -> str:
        if not search.entries:
            return "No matching conversation transcript turns were found."
        participant_label = (
            ", ".join(participants) if participants else "the requested participants"
        )
        focus = f" about {query}" if query else ""
        return (
            "Found "
            f"{search.total_results} matching transcript turn(s) for "
            f"{participant_label}{focus}. "
            f"Most recent: {search.entries[0].text}"
        )

    @staticmethod
    def _transcript_search_answer(search: TranscriptSearchResponse) -> str:
        if not search.entries:
            return "No matching transcript entries were found."
        suffix = "y" if search.total_results == 1 else "ies"
        return (
            f"Found {search.total_results} matching transcript entr{suffix}. "
            f"Most recent: {search.entries[0].text}"
        )

    @staticmethod
    def _artifact_state_summary(ref: ArtifactRef, data: dict[str, Any]) -> str:
        if ref.artifact_type == "character_bible":
            return MemoryService._character_bible_summary(ref, data)
        if ref.artifact_type == "location_bible":
            return MemoryService._location_bible_summary(ref, data)
        if ref.artifact_type == "prop_bible":
            return MemoryService._prop_bible_summary(ref, data)
        if ref.artifact_type == "bible_manifest":
            return MemoryService._bible_manifest_summary(ref, data)
        if ref.artifact_type == "scene":
            return MemoryService._scene_summary(ref, data)

        keys = [key for key in sorted(data.keys()) if key not in {"created_at", "version"}]
        preview_keys = ", ".join(keys[:5]) if keys else "no fields"
        return (
            f"Latest {ref.artifact_type}/{ref.entity_id or '__project__'} is version {ref.version} "
            f"with fields: {preview_keys}."
        )

    def _entry_matches_artifact_request(
        self,
        entry: Any,
        *,
        artifact_type: str | None,
        entity_id: str | None,
    ) -> bool:
        if entry_matches_artifact(entry, artifact_type=artifact_type, entity_id=entity_id):
            return True
        if artifact_type == "decision" and entity_id:
            return self._entry_matches_decision_scope(entry, entity_id)
        if artifact_type == "suggestion" and entity_id:
            return self._entry_matches_suggestion_scope(entry, entity_id)
        return False

    def _entry_matches_decision_scope(self, entry: Any, decision_id: str) -> bool:
        ref = self.store.latest_ref("decision", decision_id)
        if ref is None:
            return False
        artifact = self.store.load_artifact(ref)
        decision = Decision.model_validate(artifact.data)

        for affected_ref in decision.affected_artifacts:
            if entry_matches_artifact(
                entry,
                artifact_type=affected_ref.artifact_type,
                entity_id=affected_ref.entity_id,
            ):
                return True
        for suggestion_id in decision.informed_by_suggestions:
            if self._entry_matches_suggestion_scope(entry, suggestion_id):
                return True
        return False

    def _entry_matches_suggestion_scope(self, entry: Any, suggestion_id: str) -> bool:
        ref = self.store.latest_ref("suggestion", suggestion_id)
        if ref is None:
            return False
        artifact = self.store.load_artifact(ref)
        suggestion = Suggestion.model_validate(artifact.data)

        if suggestion.related_artifact_ref and entry_matches_artifact(
            entry,
            artifact_type=suggestion.related_artifact_ref.artifact_type,
            entity_id=suggestion.related_artifact_ref.entity_id,
        ):
            return True
        if suggestion.related_scene_id and suggestion.related_scene_id in entry.scene_ids:
            return True
        if suggestion.related_entity_id and suggestion.related_entity_id in entry.entity_ids:
            return True
        return False

    @staticmethod
    def _character_bible_summary(ref: ArtifactRef, data: dict[str, Any]) -> str:
        name = str(data.get("name") or ref.entity_id or "Unknown character")
        parts = [f"Latest character bible for {name} is version {ref.version}."]
        description = str(data.get("description") or "").strip()
        if description:
            parts.append(description)
        details: list[str] = []
        narrative_role = str(data.get("narrative_role") or "").strip()
        if narrative_role:
            details.append(f"Role: {narrative_role}.")
        dialogue_summary = str(data.get("dialogue_summary") or "").strip()
        if dialogue_summary:
            details.append(f"Voice: {dialogue_summary}")
        scene_presence = data.get("scene_presence") or []
        if isinstance(scene_presence, list) and scene_presence:
            details.append(f"Appears in {len(scene_presence)} scene(s).")
        if details:
            parts.append(" ".join(details))
        return " ".join(parts)

    @staticmethod
    def _location_bible_summary(ref: ArtifactRef, data: dict[str, Any]) -> str:
        name = str(data.get("name") or ref.entity_id or "Unknown location")
        parts = [f"Latest location bible for {name} is version {ref.version}."]
        description = str(data.get("description") or "").strip()
        if description:
            parts.append(description)
        significance = str(data.get("narrative_significance") or "").strip()
        if significance:
            parts.append(f"Narrative significance: {significance}")
        scene_presence = data.get("scene_presence") or []
        if isinstance(scene_presence, list) and scene_presence:
            parts.append(f"Appears in {len(scene_presence)} scene(s).")
        return " ".join(parts)

    @staticmethod
    def _prop_bible_summary(ref: ArtifactRef, data: dict[str, Any]) -> str:
        name = str(data.get("name") or ref.entity_id or "Unknown prop")
        parts = [f"Latest prop bible for {name} is version {ref.version}."]
        description = str(data.get("description") or "").strip()
        if description:
            parts.append(description)
        significance = str(data.get("narrative_significance") or "").strip()
        if significance:
            parts.append(f"Narrative significance: {significance}")
        associated = data.get("associated_characters") or []
        if isinstance(associated, list) and associated:
            parts.append(
                f"Associated characters: {', '.join(str(item) for item in associated[:3])}."
            )
        return " ".join(parts)

    @staticmethod
    def _bible_manifest_summary(ref: ArtifactRef, data: dict[str, Any]) -> str:
        entity_type = str(data.get("entity_type") or "entity")
        display_name = str(data.get("display_name") or ref.entity_id or "Unknown entity")
        files = data.get("files") or []
        file_count = len(files) if isinstance(files, list) else 0
        parts = [
            f"Latest {entity_type} bible manifest for {display_name} is version {ref.version} "
            f"with {file_count} file(s)."
        ]
        if isinstance(files, list) and files:
            file_labels: list[str] = []
            for item in files[:3]:
                if not isinstance(item, dict):
                    continue
                filename = str(item.get("filename") or "unknown")
                purpose = str(item.get("purpose") or "file")
                file_labels.append(f"{filename} ({purpose})")
            if file_labels:
                parts.append(f"Files: {', '.join(file_labels)}.")
        visual_reference = str(data.get("visual_reference_image") or "").strip()
        if visual_reference:
            parts.append(f"Visual reference: {visual_reference}.")
        return " ".join(parts)

    @staticmethod
    def _scene_summary(ref: ArtifactRef, data: dict[str, Any]) -> str:
        heading = str(data.get("heading") or ref.entity_id or "Unknown scene")
        parts = [f"Latest scene state for {heading} is version {ref.version}."]
        characters = data.get("characters_present") or []
        if isinstance(characters, list) and characters:
            parts.append(f"Characters present: {', '.join(str(item) for item in characters[:5])}.")
        tone = str(data.get("tone_mood") or "").strip()
        if tone:
            parts.append(f"Tone: {tone}.")
        return " ".join(parts)

    def _save_working_memory_summary(
        self,
        summary: WorkingMemorySummary,
        *,
        lineage: list[ArtifactRef],
        rationale: str,
    ) -> ArtifactRef:
        metadata = ArtifactMetadata(
            lineage=lineage,
            intent=f"Persist working-memory checkpoint for role '{summary.role_id}'.",
            rationale=rationale,
            confidence=0.9,
            source="hybrid",
            producing_module="memory_service_v1",
            producing_role=summary.role_id,
        )
        return self.store.save_artifact(
            artifact_type="working_memory_summary",
            entity_id=summary.role_id,
            data=summary.model_dump(mode="json"),
            metadata=metadata,
        )

    def _read_project_json(self) -> dict[str, Any]:
        project_json_path = self.project_dir / "project.json"
        if not project_json_path.exists():
            return {}
        try:
            return json.loads(project_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_project_json(self, payload: dict[str, Any]) -> None:
        project_json_path = self.project_dir / "project.json"
        project_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
