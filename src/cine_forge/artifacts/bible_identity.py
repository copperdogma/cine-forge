"""Identity-edit guardrails for folder-backed bible artifacts."""

from __future__ import annotations

import re
from typing import Any

IDENTITY_FIELD_BY_ENTITY_TYPE = {
    "character": "character_id",
    "location": "location_id",
    "prop": "prop_id",
}
GENERIC_IDENTITY_FIELDS = {"entity_id"}

MERGE_OR_DEPRECATION_KEYS = {
    "canonical_character_id",
    "canonical_entity_id",
    "canonical_location_id",
    "canonical_prop_id",
    "deprecate",
    "deprecated",
    "deprecation",
    "merge",
    "merge_into",
    "merged_into",
    "supersede",
    "superseded_by",
}


def detect_unsupported_identity_edit(
    *,
    entity_type: str,
    entity_id: str,
    current_master: dict[str, Any],
    next_master: dict[str, Any],
    changes: dict[str, Any] | None = None,
) -> dict[str, str] | None:
    """Return an unsupported-action payload for identity merge/deprecation edits."""

    identity_field = IDENTITY_FIELD_BY_ENTITY_TYPE.get(entity_type)
    if identity_field:
        identity_fields = {identity_field, *GENERIC_IDENTITY_FIELDS}
        entity_labels = _identity_entity_labels(entity_type)
        current_ids = _identity_ids(
            current_master,
            identity_fields,
            entity_labels=entity_labels,
        )
        next_ids = _identity_ids(
            next_master,
            identity_fields,
            entity_labels=entity_labels,
        )
        current_id = current_ids[0] if current_ids else ""
        next_id = next_ids[0] if next_ids else ""
        manifest_id = _clean_id(entity_id)
        if manifest_id and not current_ids:
            return _unsupported_payload(entity_type)
        if _has_identity_drift(current_ids, manifest_id):
            return _unsupported_payload(entity_type)
        if next_ids and any(not value for value in next_ids):
            return _unsupported_payload(entity_type)
        if next_ids and manifest_id and any(value != manifest_id for value in next_ids):
            return _unsupported_payload(entity_type)
        if len(set(next_ids)) > 1:
            return _unsupported_payload(entity_type)
        if manifest_id and not next_id:
            return _unsupported_payload(entity_type)
        if current_id and not next_id:
            return _unsupported_payload(entity_type)
        if current_id and next_id and current_id != next_id:
            return _unsupported_payload(entity_type)
        if next_id and manifest_id and next_id != manifest_id:
            return _unsupported_payload(entity_type)

    if _contains_merge_or_deprecation_intent(current_master):
        return _unsupported_payload(entity_type)
    if _contains_merge_or_deprecation_intent(changes or {}):
        return _unsupported_payload(entity_type)
    if _contains_merge_or_deprecation_intent(next_master):
        return _unsupported_payload(entity_type)
    return None


def _identity_ids(
    master: dict[str, Any],
    identity_fields: set[str],
    *,
    entity_labels: set[str],
    key_path: tuple[str, ...] = (),
) -> list[str]:
    ids: list[str] = []
    for key, value in master.items():
        key_parts = (*key_path, *_normalized_key_parts(key))
        if _key_path_matches_identity_key(key_parts, identity_fields, entity_labels):
            ids.append(_clean_id(value))
        if isinstance(value, dict):
            ids.extend(
                _identity_ids(
                    value,
                    identity_fields,
                    entity_labels=entity_labels,
                    key_path=key_parts,
                )
            )
        elif isinstance(value, list):
            ids.extend(
                _identity_ids_from_list(
                    value,
                    identity_fields,
                    entity_labels=entity_labels,
                    key_path=key_parts,
                )
            )
    return ids


def _key_path_matches_identity_key(
    key_path: tuple[str, ...],
    identity_fields: set[str],
    entity_labels: set[str],
) -> bool:
    return bool(
        key_path
        and (
            key_path[-1] in identity_fields
            or _key_path_matches_split_identity(key_path, entity_labels)
        )
    )


def _has_identity_drift(ids: list[str], manifest_id: str) -> bool:
    if not manifest_id:
        return False
    return any(value != manifest_id for value in ids)


def _identity_entity_labels(entity_type: str) -> set[str]:
    labels = {_normalize_key(entity_type)}
    for field_name in {IDENTITY_FIELD_BY_ENTITY_TYPE.get(entity_type), *GENERIC_IDENTITY_FIELDS}:
        if not field_name:
            continue
        normalized = _normalize_key(field_name)
        if normalized.endswith("_id"):
            labels.add(normalized.removesuffix("_id"))
    return labels


def _key_path_matches_split_identity(
    key_path: tuple[str, ...],
    entity_labels: set[str],
) -> bool:
    return (
        len(key_path) >= 2
        and key_path[-1] == "id"
        and key_path[-2] in entity_labels
    )


def _identity_ids_from_list(
    values: list[Any],
    identity_fields: set[str],
    *,
    entity_labels: set[str],
    key_path: tuple[str, ...],
) -> list[str]:
    ids: list[str] = []
    for value in values:
        if isinstance(value, dict):
            ids.extend(
                _identity_ids(
                    value,
                    identity_fields,
                    entity_labels=entity_labels,
                    key_path=key_path,
                )
            )
        elif isinstance(value, list):
            ids.extend(
                _identity_ids_from_list(
                    value,
                    identity_fields,
                    entity_labels=entity_labels,
                    key_path=key_path,
                )
            )
    return ids


def _contains_merge_or_deprecation_intent(
    value: Any,
    key_path: tuple[str, ...] = (),
) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            nested_key_path = (*key_path, _normalize_key(key))
            if _key_matches_merge_or_deprecation_intent(nested_key_path):
                return True
            if _contains_merge_or_deprecation_intent(nested_value, nested_key_path):
                return True
    if isinstance(value, list):
        return any(_contains_merge_or_deprecation_intent(item, key_path) for item in value)
    return False


def _key_matches_merge_or_deprecation_intent(key_path: tuple[str, ...]) -> bool:
    normalized = "_".join(part for part in key_path if part)
    dotted = ".".join(part for part in key_path if part)
    key_forms = {key_path[-1], normalized, dotted}
    key_parts: set[str] = set()
    for part in key_path:
        key_parts.update(part.split("_"))
    return bool(
        (key_forms | key_parts) & MERGE_OR_DEPRECATION_KEYS
    )


def _normalize_key(key: Any) -> str:
    text = str(key).replace("-", "_").replace(".", "_")
    text = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", text)
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    return text.lower()


def _normalized_key_parts(key: Any) -> tuple[str, ...]:
    return tuple(
        part for part in (_normalize_key(part) for part in str(key).split(".")) if part
    )


def _unsupported_payload(entity_type: str) -> dict[str, str]:
    label = entity_type.replace("_", " ")
    return {
        "status": "unsupported_action",
        "error": (
            f"{label.title()} identity merge/deprecation is not supported through "
            "single-artifact edits."
        ),
        "hint": (
            "Fix upstream entity resolution or use a dedicated merge workflow that can "
            "version the canonical bible, preserve aliases/reference assets, and update "
            "downstream graph and scene references together."
        ),
    }


def _clean_id(value: Any) -> str:
    return str(value or "").strip()
