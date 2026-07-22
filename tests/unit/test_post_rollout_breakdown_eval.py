from __future__ import annotations

import pytest
from scripts import post_rollout_breakdown_contract, post_rollout_breakdown_eval

pytestmark = pytest.mark.unit


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


def _semantic_payloads() -> dict[str, list[dict[str, object]]]:
    return {
        "canonical_script": [
            {
                "title": "Open Frequency",
                "scene_count": 4,
                "script_text": "\n".join(
                    [
                        "INT. COMMUNITY RADIO STUDIO - NIGHT",
                        "EXT. WATER TOWER CATWALK - NIGHT",
                        "INT. HIGH SCHOOL GYM SHELTER - PRE-DAWN",
                        "INT. COMMUNITY RADIO STUDIO - MORNING",
                    ]
                ),
            }
        ],
        "scene": [
            {
                "scene_number": number,
                "heading": heading,
            }
            for number, heading in enumerate(
                [
                    "INT. COMMUNITY RADIO STUDIO - NIGHT",
                    "EXT. WATER TOWER CATWALK - NIGHT",
                    "INT. HIGH SCHOOL GYM SHELTER - PRE-DAWN",
                    "INT. COMMUNITY RADIO STUDIO - MORNING",
                ],
                start=1,
            )
        ],
        "script_bible": [
            {
                "title": "Open Frequency",
                "logline": "Aria and Noah restore a radio signal during a storm.",
                "synopsis": "June uses the station to route insulin to a shelter.",
                "central_conflict": "The bridge and road closures isolate the town.",
                "setting_overview": "A radio studio, tower, and school gym.",
            }
        ],
        "project_config": [
            {
                "title": "Open Frequency",
                "location_count": 3,
                "primary_characters": ["Aria", "June", "Noah"],
                "supporting_characters": ["Kell", "Maya"],
            }
        ],
    }


def test_post_rollout_semantic_contract_matches_source_fixture() -> None:
    contract = post_rollout_breakdown_contract.build_fixture_contract(
        post_rollout_breakdown_eval.DEFAULT_FIXTURE
    )

    evidence = post_rollout_breakdown_contract.evaluate_semantic_payloads(
        contract,
        _semantic_payloads(),
    )

    assert evidence["expected_title"] == "Open Frequency"
    assert evidence["expected_scene_count"] == 4
    assert len(evidence["fixture_sha256"]) == 64


def test_post_rollout_semantic_contract_rejects_placeholder_bible() -> None:
    contract = post_rollout_breakdown_contract.build_fixture_contract(
        post_rollout_breakdown_eval.DEFAULT_FIXTURE
    )
    payloads = _semantic_payloads()
    payloads["script_bible"][0]["logline"] = "A generic story."
    payloads["script_bible"][0]["synopsis"] = "UNKNOWN"
    payloads["script_bible"][0]["central_conflict"] = "UNKNOWN"
    payloads["script_bible"][0]["setting_overview"] = "UNKNOWN"

    with pytest.raises(ValueError, match="source-grounded story fact"):
        post_rollout_breakdown_contract.evaluate_semantic_payloads(contract, payloads)


def test_post_rollout_semantic_contract_requires_shelter_response_fact() -> None:
    contract = post_rollout_breakdown_contract.build_fixture_contract(
        post_rollout_breakdown_eval.DEFAULT_FIXTURE
    )
    payloads = _semantic_payloads()
    payloads["script_bible"][0]["synopsis"] = (
        "June uses the station to coordinate updates during the storm."
    )
    payloads["script_bible"][0]["setting_overview"] = (
        "A radio studio and water tower in severe weather."
    )

    with pytest.raises(ValueError, match="source-grounded story fact"):
        post_rollout_breakdown_contract.evaluate_semantic_payloads(contract, payloads)


def test_post_rollout_semantic_contract_rejects_scene_heading_drift() -> None:
    contract = post_rollout_breakdown_contract.build_fixture_contract(
        post_rollout_breakdown_eval.DEFAULT_FIXTURE
    )
    payloads = _semantic_payloads()
    payloads["scene"][1]["heading"] = "EXT. SOMEWHERE ELSE - DAY"

    with pytest.raises(ValueError, match="scene artifact headings mismatch"):
        post_rollout_breakdown_contract.evaluate_semantic_payloads(contract, payloads)
