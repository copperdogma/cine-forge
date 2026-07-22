"""Source-derived semantic contract for the post-rollout breakdown probe."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

_SCENE_HEADING = re.compile(r"^(?:\.)?(?:INT\.?|EXT\.?|INT\.?/EXT\.?|I/E\.?|EST\.?)\s", re.I)
_STORY_TERM_GROUPS = (
    {"radio", "station", "broadcast", "signal", "frequency"},
    {"storm", "rain", "weather", "road", "bridge"},
    {"shelter", "gym", "insulin"},
    {"aria", "june", "noah", "kell", "maya"},
)
_EXPECTED_CHARACTERS = {"aria", "june", "noah", "kell", "maya"}


class EvalFailure(RuntimeError):
    """Raised when the rollout eval finds a product failure."""

    def __init__(
        self,
        message: str,
        *,
        project_id: str | None = None,
        run_id: str | None = None,
        failing_stage_id: str | None = None,
        stage_statuses: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.project_id = project_id
        self.run_id = run_id
        self.failing_stage_id = failing_stage_id
        self.stage_statuses = stage_statuses or {}

    def render(self) -> str:
        lines = ["POST-ROLLOUT-EVAL FAILED", self.message]
        if self.project_id:
            lines.append(f"project_id: {self.project_id}")
        if self.run_id:
            lines.append(f"run_id: {self.run_id}")
        if self.failing_stage_id:
            lines.append(f"failing_stage: {self.failing_stage_id}")
        if self.stage_statuses:
            statuses = ", ".join(
                f"{stage}={status}" for stage, status in self.stage_statuses.items()
            )
            lines.append(f"stage_statuses: {statuses}")
        return "\n".join(lines)


def request_json(
    client: object,
    method: str,
    path: str,
    **kwargs: Any,
) -> dict[str, Any] | list[Any]:
    response = client.request(method, path, **kwargs)
    if response.status_code >= 400:
        raise EvalFailure(f"{method} {path} failed: {_format_response_error(response)}")
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise EvalFailure(f"{method} {path} returned non-JSON response") from exc


def _format_response_error(response: object) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return response.text.strip() or f"HTTP {response.status_code}"
    detail = payload.get("detail")
    if isinstance(detail, dict):
        message = detail.get("message") or detail.get("code") or json.dumps(
            detail, sort_keys=True
        )
        hint = detail.get("hint")
        return f"{message} ({hint})" if hint else message
    if isinstance(detail, str):
        return detail
    if "message" in payload:
        return str(payload["message"])
    return json.dumps(payload, sort_keys=True)


def build_project_identity(prefix: str) -> tuple[str, str]:
    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    slug = re.sub(r"[^a-z0-9]+", "-", prefix.lower()).strip("-")
    return f"{slug or 'post-rollout-eval'}-{timestamp}", f"Post-rollout Eval {timestamp}"


def build_fixture_contract(path: Path) -> dict[str, Any]:
    raw_bytes = path.read_bytes()
    text = raw_bytes.decode("utf-8")
    title = next(
        (
            line.split(":", 1)[1].strip()
            for line in text.splitlines()
            if line.lower().startswith("title:")
        ),
        "",
    )
    headings = [
        line.strip().lstrip(".")
        for line in text.splitlines()
        if _SCENE_HEADING.match(line.strip())
    ]
    if not title or not headings:
        raise ValueError("Fixture must contain a title and at least one Fountain scene heading")
    return {
        "fixture_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "title": title,
        "scene_count": len(headings),
        "scene_headings": headings,
    }


def fetch_latest_artifact_payloads(
    *,
    client: object,
    project_id: str,
    groups: list[dict[str, Any]],
    request_json: Callable[..., dict[str, Any] | list[Any]],
) -> dict[str, list[dict[str, Any]]]:
    payloads: dict[str, list[dict[str, Any]]] = {}
    for group in groups:
        artifact_type = str(group.get("artifact_type") or "")
        if artifact_type not in {"canonical_script", "scene", "script_bible", "project_config"}:
            continue
        entity_id = str(group.get("entity_id") or "__project__")
        version = int(group.get("latest_version") or 0)
        if version < 1:
            raise ValueError(f"{artifact_type}/{entity_id} has no valid latest_version")
        detail = request_json(
            client,
            "GET",
            f"/api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/{version}",
        )
        if not isinstance(detail, dict) or not isinstance(detail.get("payload"), dict):
            raise ValueError(f"{artifact_type}/{entity_id} detail had unexpected shape")
        data = detail["payload"].get("data")
        if not isinstance(data, dict):
            raise ValueError(f"{artifact_type}/{entity_id} detail omitted payload.data")
        payloads.setdefault(artifact_type, []).append(data)
    return payloads


def evaluate_semantic_payloads(
    contract: dict[str, Any],
    payloads: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    errors: list[str] = []
    canonical = _only(payloads, "canonical_script", errors)
    bible = _only(payloads, "script_bible", errors)
    config = _only(payloads, "project_config", errors)
    scenes = sorted(payloads.get("scene", []), key=lambda row: int(row.get("scene_number") or 0))

    if canonical:
        _expect_equal(errors, "canonical title", canonical.get("title"), contract["title"])
        _expect_equal(
            errors,
            "canonical scene_count",
            canonical.get("scene_count"),
            contract["scene_count"],
        )
        canonical_headings = [
            line.strip().lstrip(".")
            for line in str(canonical.get("script_text") or "").splitlines()
            if _SCENE_HEADING.match(line.strip())
        ]
        _expect_equal(
            errors,
            "canonical scene headings",
            canonical_headings,
            contract["scene_headings"],
        )

    scene_headings = [str(scene.get("heading") or "") for scene in scenes]
    _expect_equal(errors, "scene artifact headings", scene_headings, contract["scene_headings"])

    if bible:
        _expect_equal(errors, "script bible title", bible.get("title"), contract["title"])
        story_text = " ".join(
            str(bible.get(field) or "")
            for field in ("logline", "synopsis", "central_conflict", "setting_overview")
        ).lower()
        for term_group in _STORY_TERM_GROUPS:
            if not any(term in story_text for term in term_group):
                errors.append("script bible omitted a required source-grounded story fact group")

    if config:
        _expect_equal(errors, "project config title", config.get("title"), contract["title"])
        if int(config.get("location_count") or 0) < 3:
            errors.append(
                "project config location_count did not preserve the three source locations"
            )
        names = {
            str(name).strip().lower()
            for field in ("primary_characters", "supporting_characters")
            for name in (config.get(field) or [])
        }
        if len(names & _EXPECTED_CHARACTERS) < 3:
            errors.append("project config omitted most named source characters")

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "fixture_sha256": contract["fixture_sha256"],
        "expected_title": contract["title"],
        "expected_scene_count": contract["scene_count"],
        "expected_scene_headings": contract["scene_headings"],
        "verified_artifact_types": sorted(payloads),
    }


def _only(
    payloads: dict[str, list[dict[str, Any]]],
    artifact_type: str,
    errors: list[str],
) -> dict[str, Any] | None:
    rows = payloads.get(artifact_type, [])
    if len(rows) != 1:
        errors.append(f"expected exactly one {artifact_type} artifact, found {len(rows)}")
        return None
    return rows[0]


def _expect_equal(errors: list[str], label: str, actual: object, expected: object) -> None:
    if actual != expected:
        errors.append(f"{label} mismatch: expected {expected!r}, got {actual!r}")
