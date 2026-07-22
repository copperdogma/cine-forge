#!/usr/bin/env python3
"""Representative post-rollout eval for the surfaced Script Breakdown flow.

Creates a fresh project via the normal API, uploads the canonical short
`open_frequency_short.fountain` fixture, starts `mvp_ingest`, and fails on any
stage error or missing required artifact. This is intentionally small and cheap
enough to run after every production deploy.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError as exc:  # pragma: no cover - operator-facing dependency error
    raise SystemExit("httpx is required; run with the repo virtualenv.") from exc

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.post_rollout_breakdown_contract import (  # noqa: E402
    EvalFailure,
    build_fixture_contract,
    build_project_identity,
    evaluate_semantic_payloads,
    fetch_latest_artifact_payloads,
    request_json,
)

DEFAULT_BASE_URL = "https://cineforge.copper-dog.com"
DEFAULT_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "ingest_inputs" / "open_frequency_short.fountain"
)
DEFAULT_MODEL = "claude-sonnet-4-6"
REQUIRED_STAGE_IDS = (
    "ingest",
    "normalize",
    "breakdown_scenes",
    "script_bible",
    "project_config",
)
SUCCESS_STATUSES = {"done", "skipped_reused"}
IN_PROGRESS_STATUSES = {"pending", "running"}
REQUIRED_ARTIFACT_TYPES = ("canonical_script", "scene", "script_bible", "project_config")
MISSING_STAGE_DETAIL = "no stage error message recorded"


def _request_json(
    client: httpx.Client,
    method: str,
    path: str,
    **kwargs: Any,
) -> dict[str, Any] | list[Any]:
    return request_json(client, method, path, **kwargs)


def _required_stage_statuses(run_state: dict[str, Any]) -> dict[str, str]:
    stages = run_state.get("stages")
    if not isinstance(stages, dict):
        raise EvalFailure("Run state did not include stages")
    statuses: dict[str, str] = {}
    for stage_id in REQUIRED_STAGE_IDS:
        stage_state = stages.get(stage_id)
        if not isinstance(stage_state, dict):
            statuses[stage_id] = "missing"
            continue
        statuses[stage_id] = str(stage_state.get("status") or "unknown")
    return statuses


def _failed_stage_entries(run_state: dict[str, Any]) -> list[tuple[str, str, str]]:
    stages = run_state.get("stages")
    if not isinstance(stages, dict):
        return [("run_state", "missing", "run state missing stages")]
    failures: list[tuple[str, str, str]] = []
    for stage_id in REQUIRED_STAGE_IDS:
        stage_state = stages.get(stage_id)
        if not isinstance(stage_state, dict):
            failures.append((stage_id, "missing", "missing from run state"))
            continue
        status = str(stage_state.get("status") or "unknown")
        if status in SUCCESS_STATUSES or status in IN_PROGRESS_STATUSES:
            continue
        detail = (
            stage_state.get("error")
            or stage_state.get("failure_message")
            or stage_state.get("message")
            or stage_state.get("detail")
            or MISSING_STAGE_DETAIL
        )
        failures.append((stage_id, status, str(detail)))
    return failures


def _has_in_progress_stages(statuses: dict[str, str]) -> bool:
    return any(status in IN_PROGRESS_STATUSES for status in statuses.values())


def _run_succeeded(run_state: dict[str, Any]) -> bool:
    statuses = _required_stage_statuses(run_state)
    return all(status in SUCCESS_STATUSES for status in statuses.values())


def _wait_for_run_success(
    client: httpx.Client,
    project_id: str,
    run_id: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        payload = _request_json(client, "GET", f"/api/runs/{run_id}/state")
        if not isinstance(payload, dict):
            raise EvalFailure("Run state response had unexpected shape")
        last_payload = payload
        background_error = payload.get("background_error")
        run_state = payload.get("state")
        if not isinstance(run_state, dict):
            raise EvalFailure(
                "Run state payload missing state object",
                project_id=project_id,
                run_id=run_id,
            )
        statuses = _required_stage_statuses(run_state)
        failures = _failed_stage_entries(run_state)
        if background_error:
            failed_stage_id = failures[0][0] if len(failures) == 1 else None
            if failed_stage_id:
                message = (
                    "Representative Script Breakdown eval failed in "
                    f"{failed_stage_id}: {background_error}"
                )
            else:
                message = (
                    "Representative Script Breakdown eval hit background error: "
                    f"{background_error}"
                )
            raise EvalFailure(
                message,
                project_id=project_id,
                run_id=run_id,
                failing_stage_id=failed_stage_id,
                stage_statuses=statuses,
            )
        if failures:
            waiting_for_error_detail = _has_in_progress_stages(statuses) and all(
                detail == MISSING_STAGE_DETAIL for _, _, detail in failures
            )
            if waiting_for_error_detail:
                time.sleep(poll_interval_seconds)
                continue
            failed_stage_id = failures[0][0] if len(failures) == 1 else None
            failure_lines = [
                f"- {stage_id}: {status} — {detail}"
                for stage_id, status, detail in failures
            ]
            raise EvalFailure(
                "Representative Script Breakdown eval failed:\n" + "\n".join(failure_lines),
                project_id=project_id,
                run_id=run_id,
                failing_stage_id=failed_stage_id,
                stage_statuses=statuses,
            )
        if _run_succeeded(run_state):
            return run_state
        time.sleep(poll_interval_seconds)
    last_state = last_payload.get("state") if isinstance(last_payload, dict) else None
    summary = _required_stage_statuses(last_state) if isinstance(last_state, dict) else {}
    raise EvalFailure(
        f"Timed out waiting for run {run_id} to finish. Last stage statuses: "
        + ", ".join(f"{stage}={status}" for stage, status in summary.items()),
        project_id=project_id,
        run_id=run_id,
        stage_statuses=summary,
    )


def _verify_required_artifacts(
    client: httpx.Client, project_id: str, run_id: str
) -> list[dict[str, Any]]:
    payload = _request_json(client, "GET", f"/api/projects/{project_id}/artifacts")
    if not isinstance(payload, list):
        raise EvalFailure(
            "Artifact list response had unexpected shape",
            project_id=project_id,
            run_id=run_id,
        )
    artifact_types = {
        str(item.get("artifact_type"))
        for item in payload
        if isinstance(item, dict) and item.get("artifact_type")
    }
    missing = [
        artifact_type
        for artifact_type in REQUIRED_ARTIFACT_TYPES
        if artifact_type not in artifact_types
    ]
    if missing:
        raise EvalFailure(
            "Rollout eval finished without required artifacts: " + ", ".join(sorted(missing)),
            project_id=project_id,
            run_id=run_id,
        )
    return [item for item in payload if isinstance(item, dict)]


def run_eval(
    *,
    base_url: str,
    fixture_path: Path,
    default_model: str,
    project_prefix: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
) -> dict[str, Any]:
    if not fixture_path.exists():
        raise EvalFailure(f"Fixture not found: {fixture_path}")
    fixture_bytes = fixture_path.read_bytes()
    if not fixture_bytes:
        raise EvalFailure(f"Fixture is empty: {fixture_path}")
    try:
        fixture_contract = build_fixture_contract(fixture_path)
    except (UnicodeDecodeError, ValueError) as exc:
        raise EvalFailure(f"Fixture semantic contract is invalid: {exc}") from exc

    slug, display_name = build_project_identity(project_prefix)
    timeout = httpx.Timeout(30.0, connect=30.0, read=30.0, write=30.0)
    with httpx.Client(
        base_url=base_url.rstrip("/"),
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        created = _request_json(
            client,
            "POST",
            "/api/projects/new",
            json={"slug": slug, "display_name": display_name},
        )
        if not isinstance(created, dict) or "project_id" not in created:
            raise EvalFailure("Project create response did not include project_id")
        project_id = str(created["project_id"])

        uploaded = _request_json(
            client,
            "POST",
            f"/api/projects/{project_id}/inputs/upload",
            files={"file": (fixture_path.name, fixture_bytes, "text/plain")},
        )
        if not isinstance(uploaded, dict) or "stored_path" not in uploaded:
            raise EvalFailure(
                "Upload response did not include stored_path",
                project_id=project_id,
            )
        stored_path = str(uploaded["stored_path"])

        started = _request_json(
            client,
            "POST",
            "/api/runs/start",
            json={
                "project_id": project_id,
                "input_file": stored_path,
                "default_model": default_model,
                "recipe_id": "mvp_ingest",
                "accept_config": True,
            },
        )
        if not isinstance(started, dict) or "run_id" not in started:
            raise EvalFailure(
                "Run start response did not include run_id",
                project_id=project_id,
            )
        run_id = str(started["run_id"])

        run_state = _wait_for_run_success(
            client,
            project_id=project_id,
            run_id=run_id,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
        )
        artifact_groups = _verify_required_artifacts(client, project_id, run_id)
        try:
            artifact_payloads = fetch_latest_artifact_payloads(
                client=client,
                project_id=project_id,
                groups=artifact_groups,
                request_json=_request_json,
            )
            semantic_evidence = evaluate_semantic_payloads(
                fixture_contract,
                artifact_payloads,
            )
        except ValueError as exc:
            raise EvalFailure(
                f"Script Breakdown semantic contract failed: {exc}",
                project_id=project_id,
                run_id=run_id,
            ) from exc
        artifact_types = sorted(
            {
                str(group.get("artifact_type"))
                for group in artifact_groups
                if group.get("artifact_type")
            }
        )

    return {
        "base_url": base_url.rstrip("/"),
        "project_id": project_id,
        "project_url": f"{base_url.rstrip('/')}/{project_id}",
        "run_id": run_id,
        "fixture": str(fixture_path),
        "stage_statuses": _required_stage_statuses(run_state),
        "artifact_types": artifact_types,
        "semantic_evidence": semantic_evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the representative post-rollout Script Breakdown eval."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--default-model", default=DEFAULT_MODEL)
    parser.add_argument("--project-prefix", default="post-rollout-eval")
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=1.0)
    parser.add_argument("--json-output", default=None)
    args = parser.parse_args()

    try:
        summary = run_eval(
            base_url=args.base_url,
            fixture_path=Path(args.fixture).resolve(),
            default_model=args.default_model,
            project_prefix=args.project_prefix,
            timeout_seconds=args.timeout_seconds,
            poll_interval_seconds=args.poll_interval_seconds,
        )
    except EvalFailure as exc:
        print(exc.render(), file=sys.stderr)
        return 1

    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("POST-ROLLOUT-EVAL PASSED")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
