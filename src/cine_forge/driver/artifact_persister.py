"""ArtifactPersister — replaces the _announce_artifact closure and batch persistence loop."""

from __future__ import annotations

import threading
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.event_emitter import EventEmitter
from cine_forge.driver.retry_policy import StageRetryPolicy
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    CostRecord,
    EventType,
    ProgressEvent,
    SchemaRegistry,
)


class ArtifactPersister:
    """Handles artifact validation, persistence, state updates, and event emission for a stage."""

    def __init__(
        self,
        store: ArtifactStore,
        schemas: SchemaRegistry,
        module_id: str,
        output_schemas: list[str],
        upstream_refs: list[ArtifactRef],
        stage_id: str,
        stage_state: dict[str, Any],
        run_state: dict[str, Any],
        state_lock: threading.Lock,
        emitter: EventEmitter,
        write_run_state: Any,
    ) -> None:
        self.store = store
        self.schemas = schemas
        self.module_id = module_id
        self.output_schemas = output_schemas
        self.upstream_refs = upstream_refs
        self.stage_id = stage_id
        self.stage_state = stage_state
        self.run_state = run_state
        self.state_lock = state_lock
        self.emitter = emitter
        self.write_run_state = write_run_state

    def announce(self, artifact_dict: dict[str, Any]) -> None:
        """Save an artifact mid-stage (live sidebar).

        Called per entity as its LLM call completes.
        """
        output_data = artifact_dict["data"]
        a_schema_names = self._schema_names_for_artifact(
            artifact=artifact_dict,
            output_schemas=self.output_schemas,
        )
        for a_schema_name in a_schema_names:
            a_validation = self.schemas.validate(
                schema_name=a_schema_name, data=output_data
            )
            if not a_validation.valid:
                raise ValueError(
                    f"announce_artifact schema validation failed: {a_validation}"
                )
        a_source_meta = artifact_dict.get("metadata", {})
        a_metadata = ArtifactMetadata.model_validate(
            {
                **a_source_meta,
                "lineage": _merge_lineage(
                    module_lineage=a_source_meta.get("lineage", []),
                    upstream_refs=self.upstream_refs,
                    stage_refs=[],
                ),
                "producing_module": self.module_id,
            }
        )
        a_ref = self.store.save_artifact(
            artifact_type=artifact_dict["artifact_type"],
            entity_id=artifact_dict.get("entity_id"),
            data=output_data,
            metadata=a_metadata,
        )
        with self.state_lock:
            self.stage_state["artifact_refs"].append(a_ref.model_dump())
            self.write_run_state()
        self.emitter.emit(ProgressEvent(
            event=EventType.artifact_saved,
            stage_id=self.stage_id,
            artifact_type=artifact_dict["artifact_type"],
            entity_id=artifact_dict.get("entity_id"),
            display_name=output_data.get("display_name")
            if isinstance(output_data, dict)
            else None,
        ))
        artifact_dict["pre_saved"] = True
        artifact_dict["pre_saved_ref"] = a_ref.model_dump()

    def persist_batch(
        self,
        outputs: list[dict[str, Any]],
        cost_record: CostRecord | None,
    ) -> list[dict[str, Any]]:
        """Persist all stage outputs, returning a list of {ref, data} dicts."""
        persisted_outputs: list[dict[str, Any]] = []
        for artifact in outputs:
            output_data = artifact["data"]

            if artifact.get("pre_saved"):
                artifact_ref = ArtifactRef.model_validate(artifact["pre_saved_ref"])
                persisted_outputs.append({"ref": artifact_ref, "data": output_data})
                continue

            schema_names = self._schema_names_for_artifact(
                artifact=artifact,
                output_schemas=self.output_schemas,
            )
            for schema_name in schema_names:
                validation = self.schemas.validate(
                    schema_name=schema_name,
                    data=output_data,
                )
                if not validation.valid:
                    raise ValueError(
                        f"Stage '{self.stage_id}' failed schema validation: {validation}"
                    )

            stage_lineage_refs = (
                [item["ref"] for item in persisted_outputs]
                if artifact.get("include_stage_lineage")
                else []
            )
            source_metadata = artifact.get("metadata", {})
            source_annotations = source_metadata.get("annotations", {})
            if not isinstance(source_annotations, dict):
                source_annotations = {}
            metadata = ArtifactMetadata.model_validate(
                {
                    **source_metadata,
                    "lineage": _merge_lineage(
                        module_lineage=source_metadata.get("lineage", []),
                        upstream_refs=self.upstream_refs,
                        stage_refs=stage_lineage_refs,
                    ),
                    "producing_module": self.module_id,
                    "cost_data": cost_record,
                    "annotations": {
                        **source_annotations,
                        "final_stage_model_used": self.stage_state["model_used"],
                        "final_stage_provider_used": StageRetryPolicy.provider_from_model(
                            str(self.stage_state["model_used"])
                        ),
                    },
                }
            )
            if artifact["artifact_type"] == "bible_manifest":
                artifact_ref = self.store.save_bible_entry(
                    entity_type=output_data["entity_type"],
                    entity_id=output_data["entity_id"],
                    display_name=output_data["display_name"],
                    files=output_data["files"],
                    data_files=artifact.get("bible_files", {}),
                    metadata=metadata,
                )
            else:
                artifact_ref = self.store.save_artifact(
                    artifact_type=artifact["artifact_type"],
                    entity_id=artifact.get("entity_id"),
                    data=output_data,
                    metadata=metadata,
                )
            with self.state_lock:
                self.stage_state["artifact_refs"].append(artifact_ref.model_dump())
            extra_event_fields: dict[str, Any] = {}
            if artifact["artifact_type"] == "entity_discovery_results" and isinstance(
                output_data, dict
            ):
                extra_event_fields = {
                    "character_count": len(output_data.get("characters", [])),
                    "location_count": len(output_data.get("locations", [])),
                    "prop_count": len(output_data.get("props", [])),
                }
            self.emitter.emit(ProgressEvent(
                event=EventType.artifact_saved,
                stage_id=self.stage_id,
                artifact_type=artifact["artifact_type"],
                entity_id=artifact.get("entity_id"),
                display_name=output_data.get("display_name")
                if isinstance(output_data, dict)
                else None,
                **extra_event_fields,
            ))
            persisted_outputs.append(
                {
                    "ref": artifact_ref,
                    "data": output_data,
                }
            )
        return persisted_outputs

    @staticmethod
    def _schema_names_for_artifact(
        artifact: dict[str, Any], output_schemas: list[str]
    ) -> list[str]:
        schema_name = artifact.get("schema_name")
        if isinstance(schema_name, str):
            return [schema_name]
        if len(output_schemas) <= 1:
            return output_schemas
        artifact_type = artifact.get("artifact_type")
        if isinstance(artifact_type, str) and artifact_type in output_schemas:
            return [artifact_type]
        return output_schemas


def _merge_lineage(
    module_lineage: list[dict[str, Any]],
    upstream_refs: list[ArtifactRef],
    stage_refs: list[ArtifactRef],
) -> list[dict[str, Any]]:
    merged: list[ArtifactRef] = [ArtifactRef.model_validate(ref) for ref in module_lineage]
    known = {ref.key() for ref in merged}
    for upstream in upstream_refs:
        if upstream.key() not in known:
            merged.append(upstream)
            known.add(upstream.key())
    for stage_ref in stage_refs:
        if stage_ref.key() not in known:
            merged.append(stage_ref)
            known.add(stage_ref.key())
    return [ref.model_dump() for ref in merged]
