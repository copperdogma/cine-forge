from __future__ import annotations

import json
import os
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas import ArtifactMetadata

ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = Path(__file__).resolve().parent / "browser"
API_BASE = "http://127.0.0.1:8123/api"
UI_BASE = os.environ.get("CINE_FORGE_VALIDATE_UI_BASE", "http://[::1]:5176")


def _metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        intent=intent,
        rationale="Story 192 validation browser fixture",
        confidence=1.0,
        source="human",
        producing_module="validate",
    )


def _api_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = body
        return {"status_code": exc.code, "body": payload}


def _seed_failure_fixture() -> str:
    project_path = Path("/tmp/cineforge-story-192-design-study-failure-validate")
    if project_path.exists():
        shutil.rmtree(project_path)

    created = _api_json("POST", "/projects/new", {"project_path": str(project_path)})
    project_id = created["project_id"]

    store = ArtifactStore(project_dir=project_path)
    store.save_bible_entry(
        entity_type="character",
        entity_id="test_subject",
        display_name="Test Subject",
        files=[
            {
                "filename": "master_definition.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "user_injected",
            }
        ],
        data_files={
            "master_definition.json": json.dumps(
                {
                    "name": "Test Subject",
                    "description": "A validation-only character for provider failure UI.",
                    "narrative_role": "browser validation fixture",
                    "inferred_traits": [{"trait": "silhouette", "value": "clear"}],
                }
            )
        },
        metadata=_metadata("validation bible"),
    )
    store.save_artifact(
        artifact_type="character_bible",
        entity_id="test_subject",
        data={
            "name": "Test Subject",
            "description": "A validation-only character for provider failure UI.",
            "narrative_role": "browser validation fixture",
            "scene_presence": [],
        },
        metadata=_metadata("validation character bible"),
    )

    failed = _api_json(
        "POST",
        f"/projects/{project_id}/design-study/character_test_subject/generate",
        {
            "entity_type": "character",
            "count": 1,
            "model": "not-a-real-image-model",
            "directive": "Exercise the failed-round operator surface.",
        },
    )
    if failed.get("status_code") != 502:
        raise AssertionError(f"Expected failed design-study generation, got {failed!r}")
    if failed["body"].get("code") != "design_study_generation_failed":
        raise AssertionError(f"Unexpected failure payload: {failed!r}")
    return project_id


def _attach_page_observers(page: Page, records: dict[str, list[str]]) -> None:
    page.on(
        "console",
        lambda msg: records["console_errors"].append(msg.text) if msg.type == "error" else None,
    )
    page.on("pageerror", lambda exc: records["page_errors"].append(str(exc)))

    def record_response(response: Any) -> None:
        if response.status < 400:
            return
        if response.url.endswith("/favicon.ico"):
            return
        records["http_errors"].append(f"{response.status} {response.url}")

    page.on("response", record_response)


def _verify_brick_route(page: Page) -> None:
    page.goto(f"{UI_BASE}/brick-steel-full-retired/characters/brick_braddock")
    page.wait_for_load_state("networkidle")
    design_study = page.get_by_text("Design Study").first
    design_study.wait_for(timeout=10_000)
    page.get_by_text("Round 1").first.wait_for(timeout=10_000)
    page.get_by_text("GPT-Image").first.wait_for(timeout=10_000)
    design_study.scroll_into_view_if_needed()
    page.wait_for_timeout(250)


def _verify_failure_route(page: Page, project_id: str) -> None:
    page.goto(f"{UI_BASE}/{project_id}/characters/test_subject")
    page.wait_for_load_state("networkidle")
    failed_status = page.get_by_text("Failed after 0 of 1 image").first
    failed_status.wait_for(timeout=10_000)
    page.get_by_text("Provider message").first.wait_for(timeout=10_000)
    page.get_by_text("not-a-real-image-model").first.wait_for(timeout=10_000)
    page.get_by_text("Prompt context").first.wait_for(timeout=10_000)
    page.get_by_text("Provider message").first.scroll_into_view_if_needed()
    page.wait_for_timeout(250)


def _shot(page: Page, filename: str) -> None:
    page.screenshot(path=str(REPORT_DIR / filename), full_page=False)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    project_id = _seed_failure_fixture()
    records: dict[str, Any] = {
        "console_errors": [],
        "page_errors": [],
        "http_errors": [],
        "screenshots": [],
        "failure_project_id": project_id,
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        _attach_page_observers(page, records)

        _verify_brick_route(page)
        _shot(page, "validate-brick-braddock-desktop.png")
        records["screenshots"].append("validate-brick-braddock-desktop.png")

        page.set_viewport_size({"width": 390, "height": 844})
        _verify_brick_route(page)
        _shot(page, "validate-brick-braddock-mobile.png")
        records["screenshots"].append("validate-brick-braddock-mobile.png")

        page.set_viewport_size({"width": 1440, "height": 1000})
        _verify_failure_route(page, project_id)
        _shot(page, "validate-provider-failure-desktop.png")
        records["screenshots"].append("validate-provider-failure-desktop.png")

        page.set_viewport_size({"width": 390, "height": 844})
        _verify_failure_route(page, project_id)
        _shot(page, "validate-provider-failure-mobile.png")
        records["screenshots"].append("validate-provider-failure-mobile.png")

        browser.close()

    summary_path = REPORT_DIR / "validate-browser-summary.json"
    summary_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(json.dumps(records, indent=2))

    if records["console_errors"] or records["page_errors"] or records["http_errors"]:
        raise SystemExit("Browser validation recorded errors")


if __name__ == "__main__":
    os.chdir(ROOT)
    main()
