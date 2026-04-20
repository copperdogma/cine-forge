from __future__ import annotations

import pytest
from scripts import post_rollout_breakdown_eval


class _FakeResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> object:
        return self._payload


class _FakeClient:
    def __init__(self, payloads: list[object]) -> None:
        self._payloads = list(payloads)

    def request(self, method: str, path: str, **_: object) -> _FakeResponse:
        if not self._payloads:
            raise AssertionError("No fake payloads remaining")
        return _FakeResponse(self._payloads.pop(0))


def test_failed_stage_entries_ignore_running_and_pending_states() -> None:
    run_state = {
        "stages": {
            "ingest": {"status": "done"},
            "normalize": {"status": "done"},
            "breakdown_scenes": {"status": "running"},
            "script_bible": {"status": "failed", "error": "bad key"},
            "project_config": {"status": "pending"},
        }
    }

    assert post_rollout_breakdown_eval._failed_stage_entries(run_state) == [
        ("script_bible", "failed", "bad key")
    ]


def test_wait_for_run_success_reports_project_run_and_failed_stage_on_background_error() -> None:
    client = _FakeClient(
        [
            {
                "background_error": "Gemini HTTP error 400: API key not valid",
                "state": {
                    "stages": {
                        "ingest": {"status": "done"},
                        "normalize": {"status": "done"},
                        "breakdown_scenes": {"status": "done"},
                        "script_bible": {"status": "failed"},
                        "project_config": {"status": "pending"},
                    }
                },
            }
        ]
    )

    with pytest.raises(post_rollout_breakdown_eval.EvalFailure) as exc_info:
        post_rollout_breakdown_eval._wait_for_run_success(
            client,
            project_id="proj-123",
            run_id="run-456",
            timeout_seconds=1.0,
            poll_interval_seconds=0.0,
        )

    failure = exc_info.value
    assert failure.project_id == "proj-123"
    assert failure.run_id == "run-456"
    assert failure.failing_stage_id == "script_bible"
    rendered = failure.render()
    assert "POST-ROLLOUT-EVAL FAILED" in rendered
    assert "project_id: proj-123" in rendered
    assert "run_id: run-456" in rendered
    assert "failing_stage: script_bible" in rendered
    assert "script_bible=failed" in rendered


def test_wait_for_run_success_waits_for_background_error_after_blank_stage_failure() -> None:
    client = _FakeClient(
        [
            {
                "state": {
                    "stages": {
                        "ingest": {"status": "done"},
                        "normalize": {"status": "done"},
                        "breakdown_scenes": {"status": "running"},
                        "script_bible": {"status": "failed"},
                        "project_config": {"status": "pending"},
                    }
                }
            },
            {
                "background_error": "Gemini HTTP error 400: API key not valid",
                "state": {
                    "stages": {
                        "ingest": {"status": "done"},
                        "normalize": {"status": "done"},
                        "breakdown_scenes": {"status": "done"},
                        "script_bible": {"status": "failed"},
                        "project_config": {"status": "pending"},
                    }
                },
            },
        ]
    )

    with pytest.raises(post_rollout_breakdown_eval.EvalFailure) as exc_info:
        post_rollout_breakdown_eval._wait_for_run_success(
            client,
            project_id="proj-123",
            run_id="run-456",
            timeout_seconds=1.0,
            poll_interval_seconds=0.0,
        )

    failure = exc_info.value
    assert "API key not valid" in failure.message
    assert failure.failing_stage_id == "script_bible"
