from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from playwright.sync_api import Page, sync_playwright

DEFAULT_API_BASE = "http://127.0.0.1:8000/api"
DEFAULT_UI_BASE = "http://127.0.0.1:5188"
DEFAULT_SCENE_ID = "scene_001"
DEFAULT_SOURCE_PROJECT = Path("/Users/cam/Documents/Projects/cine-forge/output/the-mariner-50")
DEFAULT_PROJECT_COPY_ROOT = Path("/tmp/cineforge-story099-smoke")
DEFAULT_PROJECT_COPY_NAME = "the-mariner-50-readiness"
DEFAULT_DESKTOP_SHOT = Path("/tmp/story099-scene-workspace-desktop.png")
DEFAULT_MOBILE_SHOT = Path("/tmp/story099-scene-workspace-mobile.png")


def api_request(api_base: str, method: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(f"{api_base}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body}") from exc


def prepare_project_copy(source_project: Path, project_copy: Path) -> None:
    if project_copy.exists():
        shutil.rmtree(project_copy)
    project_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_project, project_copy)


def wait_for_character_readiness(
    api_base: str,
    project_id: str,
    scene_id: str,
    expected_value: str,
    timeout_seconds: float = 15,
) -> None:
    start = time.time()
    while time.time() - start < timeout_seconds:
        payload = api_request(
            api_base,
            "GET",
            f"/projects/{project_id}/scenes/{scene_id}/readiness",
        )
        if payload["character_and_performance"] == expected_value:
            return
        time.sleep(0.25)
    raise AssertionError("character_and_performance readiness did not settle")


def ensure_scene_character_performance(
    api_base: str,
    project_id: str,
    scene_id: str,
) -> None:
    artifacts = api_request(api_base, "GET", f"/projects/{project_id}/artifacts")
    existing = [
        group
        for group in artifacts
        if (
            group["artifact_type"] == "character_and_performance"
            and group.get("entity_id") == scene_id
        )
    ]
    if existing:
        wait_for_character_readiness(api_base, project_id, scene_id, "yellow")
        return

    inputs = api_request(api_base, "GET", f"/projects/{project_id}/inputs")
    latest_input = inputs[-1]["stored_path"]
    result = api_request(
        api_base,
        "POST",
        "/runs/start",
        {
            "project_id": project_id,
            "input_file": latest_input,
            "default_model": "claude-sonnet-4-6",
            "recipe_id": "creative_direction",
            "start_from": "character_and_performance",
            "end_at": "character_and_performance",
            "accept_config": True,
            "skip_qa": True,
            "force": True,
            "scene_scope": {"mode": "current_scene", "scene_ids": [scene_id]},
        },
    )
    run_id = result["run_id"]

    for _ in range(60):
        state = api_request(api_base, "GET", f"/runs/{run_id}/state")
        if state["state"].get("finished_at"):
            stage = state["state"]["stages"]["character_and_performance"]
            if stage["status"] != "done":
                raise AssertionError(
                    "character_and_performance run finished with "
                    f"{stage['status']}"
                )
            wait_for_character_readiness(api_base, project_id, scene_id, "yellow")
            return
        time.sleep(0.5)

    raise AssertionError("Timed out waiting for character_and_performance run to finish")


def tab_locator(page: Page, label: str):
    return page.get_by_role("tab", name=re.compile(re.escape(label)))


def tab_dot_class(page: Page, label: str) -> str:
    dot = tab_locator(page, label).locator("div.rounded-full").first
    class_name = dot.get_attribute("class")
    return class_name or ""


def wait_for_dot(page: Page, label: str, expected_token: str, timeout_seconds: float = 10) -> None:
    start = time.time()
    while time.time() - start < timeout_seconds:
        class_name = tab_dot_class(page, label)
        if expected_token in class_name:
            return
        time.sleep(0.2)
    raise AssertionError(
        f"Dot for {label} never reached {expected_token}: {tab_dot_class(page, label)}"
    )


def click_tab(page: Page, label: str) -> None:
    tab = tab_locator(page, label)
    tab.scroll_into_view_if_needed()
    tab.click()


def click_review_button(page: Page, label: str) -> None:
    page.get_by_role("button", name=label).click()


def assert_readiness(
    api_base: str,
    project_id: str,
    scene_id: str,
    expected: dict[str, str],
) -> None:
    payload = api_request(api_base, "GET", f"/projects/{project_id}/scenes/{scene_id}/readiness")
    summary = {key: payload[key] for key in expected}
    print("Readiness", summary)
    if summary != expected:
        raise AssertionError(f"Unexpected readiness: {summary} != {expected}")


def record_browser_errors(
    page: Page,
    console_errors: list[str],
    page_errors: list[str],
    response_errors: list[str],
    prefix: str,
) -> None:
    page.on(
        "console",
        lambda msg: console_errors.append(f"{prefix} console[{msg.type}]: {msg.text}")
        if msg.type == "error"
        else None,
    )
    page.on("pageerror", lambda exc: page_errors.append(f"{prefix} pageerror: {exc}"))
    page.on(
        "response",
        lambda response: response_errors.append(
            f"{prefix} response[{response.status}]: {response.url}"
        )
        if response.status >= 400
        else None,
    )


def run_smoke(
    *,
    api_base: str,
    ui_base: str,
    source_project: Path,
    project_copy_root: Path,
    project_copy_name: str,
    scene_id: str,
    desktop_shot: Path,
    mobile_shot: Path,
) -> None:
    project_copy = project_copy_root / project_copy_name
    prepare_project_copy(source_project, project_copy)
    project = api_request(api_base, "POST", "/projects/open", {"project_path": str(project_copy)})
    project_id = project["project_id"]

    ensure_scene_character_performance(api_base, project_id, scene_id)

    assert_readiness(
        api_base,
        project_id,
        scene_id,
        {
            "look_and_feel": "yellow",
            "sound_and_music": "yellow",
            "rhythm_and_flow": "yellow",
            "character_and_performance": "yellow",
            "story_world": "yellow",
        },
    )

    console_errors: list[str] = []
    page_errors: list[str] = []
    response_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        desktop = browser.new_context(viewport={"width": 1440, "height": 1200})
        desktop_page = desktop.new_page()
        record_browser_errors(desktop_page, console_errors, page_errors, response_errors, "desktop")
        desktop_page.goto(f"{ui_base}/{project_id}/scenes/{scene_id}")
        desktop_page.wait_for_load_state("networkidle")

        desktop_page.locator("text=Historical run details are unavailable.").first.wait_for(
            timeout=10_000
        )

        for label in (
            "Look & Feel",
            "Sound & Music",
            "Rhythm & Flow",
            "Performance",
            "Story World",
        ):
            wait_for_dot(desktop_page, label, "bg-yellow-400")

        click_tab(desktop_page, "Look & Feel")
        desktop_page.locator("text=Draft").first.wait_for(timeout=10_000)
        click_review_button(desktop_page, "Mark Reviewed")
        wait_for_dot(desktop_page, "Look & Feel", "bg-emerald-500")
        assert_readiness(
            api_base,
            project_id,
            scene_id,
            {
                "look_and_feel": "green",
                "sound_and_music": "yellow",
                "rhythm_and_flow": "yellow",
                "character_and_performance": "yellow",
                "story_world": "yellow",
            },
        )
        click_review_button(desktop_page, "Mark Draft")
        wait_for_dot(desktop_page, "Look & Feel", "bg-yellow-400")

        click_tab(desktop_page, "Story World")
        desktop_page.locator("text=Draft").first.wait_for(timeout=10_000)
        click_review_button(desktop_page, "Mark Reviewed")
        wait_for_dot(desktop_page, "Story World", "bg-emerald-500")
        assert_readiness(
            api_base,
            project_id,
            scene_id,
            {
                "look_and_feel": "yellow",
                "sound_and_music": "yellow",
                "rhythm_and_flow": "yellow",
                "character_and_performance": "yellow",
                "story_world": "green",
            },
        )

        click_tab(desktop_page, "Performance")
        desktop_page.get_by_role("button", name="Add character direction").wait_for(timeout=10_000)
        desktop_page.locator("text=Draft").first.wait_for(timeout=10_000)
        click_review_button(desktop_page, "Mark Reviewed")
        wait_for_dot(desktop_page, "Performance", "bg-emerald-500")
        assert_readiness(
            api_base,
            project_id,
            scene_id,
            {
                "look_and_feel": "yellow",
                "sound_and_music": "yellow",
                "rhythm_and_flow": "yellow",
                "character_and_performance": "green",
                "story_world": "green",
            },
        )
        desktop_page.screenshot(path=str(desktop_shot), full_page=True)

        mobile = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True)
        mobile_page = mobile.new_page()
        record_browser_errors(mobile_page, console_errors, page_errors, response_errors, "mobile")
        mobile_page.goto(f"{ui_base}/{project_id}/scenes/{scene_id}?tab=story_world")
        mobile_page.wait_for_load_state("networkidle")
        wait_for_dot(mobile_page, "Story World", "bg-emerald-500")
        click_tab(mobile_page, "Performance")
        wait_for_dot(mobile_page, "Performance", "bg-emerald-500")
        mobile_page.screenshot(path=str(mobile_shot), full_page=True)

        desktop.close()
        mobile.close()
        browser.close()

    if console_errors or page_errors or response_errors:
        print("console_errors=", json.dumps(console_errors, indent=2))
        print("page_errors=", json.dumps(page_errors, indent=2))
        print("response_errors=", json.dumps(response_errors, indent=2))
        raise AssertionError("Browser/runtime errors detected")

    print(f"Desktop screenshot: {desktop_shot}")
    print(f"Mobile screenshot: {mobile_shot}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Representative browser smoke for Story 099 readiness honesty. "
            "Requires API and UI servers to already be running."
        )
    )
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--ui-base", default=DEFAULT_UI_BASE)
    parser.add_argument("--scene-id", default=DEFAULT_SCENE_ID)
    parser.add_argument("--source-project", type=Path, default=DEFAULT_SOURCE_PROJECT)
    parser.add_argument("--project-copy-root", type=Path, default=DEFAULT_PROJECT_COPY_ROOT)
    parser.add_argument("--project-copy-name", default=DEFAULT_PROJECT_COPY_NAME)
    parser.add_argument("--desktop-shot", type=Path, default=DEFAULT_DESKTOP_SHOT)
    parser.add_argument("--mobile-shot", type=Path, default=DEFAULT_MOBILE_SHOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_smoke(
        api_base=args.api_base,
        ui_base=args.ui_base,
        source_project=args.source_project,
        project_copy_root=args.project_copy_root,
        project_copy_name=args.project_copy_name,
        scene_id=args.scene_id,
        desktop_shot=args.desktop_shot,
        mobile_shot=args.mobile_shot,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
