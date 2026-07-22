from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

DEFAULT_API_BASE = "http://127.0.0.1:8000/api"
DEFAULT_UI_BASE = "http://127.0.0.1:5174"
DEFAULT_SCENE_ID = "scene_001"
DEFAULT_PROJECT_COPY_ROOT = Path("/tmp/cineforge-story180-smoke")
DEFAULT_PROJECT_COPY_NAME = "the-mariner-13-entry"
DEFAULT_HOME_SHOT = Path("/tmp/story180-home-desktop.png")
DEFAULT_SHOTS_SHOT = Path("/tmp/story180-shots-desktop.png")
DEFAULT_RENDER_SHOT = Path("/tmp/story180-render-desktop.png")
DEFAULT_MOBILE_RENDER_SHOT = Path("/tmp/story180-render-mobile.png")


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


def open_representative_project(api_base: str, source_project: Path, project_copy: Path) -> str:
    prepare_project_copy(source_project, project_copy)
    project = api_request(api_base, "POST", "/projects/open", {"project_path": str(project_copy)})
    return project["project_id"]


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


def wait_for_network_idle(page: Page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except PlaywrightTimeoutError:
        pass


def any_visible(locator) -> bool:
    for index in range(locator.count()):
        if locator.nth(index).is_visible():
            return True
    return False


def ensure_chat_visible(page: Page, *, mobile: bool) -> None:
    if mobile:
        open_chat = page.get_by_role("button", name="Open chat")
        if open_chat.count() and open_chat.first.is_visible():
            open_chat.first.click()
        return

    show_panel = page.get_by_role("button", name="Show panel")
    if show_panel.count() and show_panel.first.is_visible():
        show_panel.first.click()


def assert_focus_banner(
    page: Page,
    expected_label: str,
    *,
    require_jump_button: bool = True,
) -> None:
    banner = page.locator("div").filter(has_text="Focused workspace").filter(
        has_text=expected_label
    ).first
    banner.wait_for(state="visible", timeout=15_000)
    if require_jump_button:
        jump_button = banner.get_by_role("button", name="Jump to selected panel")
        jump_button.wait_for(state="visible", timeout=10_000)


def assert_pipeline_bar_copy(page: Page) -> None:
    storyboards_trigger = page.get_by_role("button", name="Storyboards").first
    storyboards_trigger.hover()
    page.wait_for_timeout(250)
    if any_visible(page.get_by_text("Run now", exact=True)):
        raise AssertionError("Pipeline bar still renders misleading 'Run now' copy")


def verify_route(
    page: Page,
    *,
    ui_base: str,
    project_id: str,
    scene_id: str,
    tab: str,
    expected_banner: str,
    screenshot_path: Path | None = None,
) -> None:
    page.goto(f"{ui_base}/{project_id}/scenes/{scene_id}?tab={tab}")
    wait_for_network_idle(page)
    if f"?tab={tab}" not in page.url:
        raise AssertionError(f"Scene workspace route lost tab target for {tab}: {page.url}")
    assert_focus_banner(page, expected_banner)
    if screenshot_path is not None:
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshot_path), full_page=True)


def run_desktop(
    *,
    ui_base: str,
    project_id: str,
    scene_id: str,
    console_errors: list[str],
    page_errors: list[str],
    response_errors: list[str],
    home_shot: Path,
    shots_shot: Path,
    render_shot: Path,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1200})
        page = context.new_page()
        record_browser_errors(page, console_errors, page_errors, response_errors, "desktop")

        page.goto(f"{ui_base}/{project_id}")
        wait_for_network_idle(page)
        ensure_chat_visible(page, mobile=False)
        assert_pipeline_bar_copy(page)
        home_shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(home_shot), full_page=True)

        verify_route(
            page,
            ui_base=ui_base,
            project_id=project_id,
            scene_id=scene_id,
            tab="shots",
            expected_banner="Shots",
            screenshot_path=shots_shot,
        )
        verify_route(
            page,
            ui_base=ui_base,
            project_id=project_id,
            scene_id=scene_id,
            tab="storyboard",
            expected_banner="Storyboard",
        )
        verify_route(
            page,
            ui_base=ui_base,
            project_id=project_id,
            scene_id=scene_id,
            tab="render",
            expected_banner="Production",
            screenshot_path=render_shot,
        )

        context.close()
        browser.close()


def run_mobile(
    *,
    ui_base: str,
    project_id: str,
    scene_id: str,
    console_errors: list[str],
    page_errors: list[str],
    response_errors: list[str],
    render_shot: Path,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
        )
        page = context.new_page()
        record_browser_errors(page, console_errors, page_errors, response_errors, "mobile")

        page.goto(f"{ui_base}/{project_id}/scenes/{scene_id}?tab=render")
        wait_for_network_idle(page)
        ensure_chat_visible(page, mobile=True)
        assert_focus_banner(page, "Production", require_jump_button=False)
        render_shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(render_shot), full_page=True)

        context.close()
        browser.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Focused browser smoke for Story 180 scene workspace entry clarity. "
            "Requires the local API/UI servers and an explicit source project produced "
            "through the normal pipeline."
        )
    )
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--ui-base", default=DEFAULT_UI_BASE)
    parser.add_argument("--scene-id", default=DEFAULT_SCENE_ID)
    parser.add_argument("--source-project", type=Path, required=True)
    parser.add_argument("--project-copy-root", type=Path, default=DEFAULT_PROJECT_COPY_ROOT)
    parser.add_argument("--project-copy-name", default=DEFAULT_PROJECT_COPY_NAME)
    parser.add_argument("--mode", choices=("desktop", "mobile", "both"), default="both")
    parser.add_argument("--home-shot", type=Path, default=DEFAULT_HOME_SHOT)
    parser.add_argument("--shots-shot", type=Path, default=DEFAULT_SHOTS_SHOT)
    parser.add_argument("--render-shot", type=Path, default=DEFAULT_RENDER_SHOT)
    parser.add_argument("--mobile-render-shot", type=Path, default=DEFAULT_MOBILE_RENDER_SHOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_copy = args.project_copy_root / args.project_copy_name
    try:
        project_id = open_representative_project(args.api_base, args.source_project, project_copy)
    except Exception as exc:  # pragma: no cover - smoke-script failure path
        print(str(exc), file=sys.stderr)
        return 1

    console_errors: list[str] = []
    page_errors: list[str] = []
    response_errors: list[str] = []

    try:
        if args.mode in {"desktop", "both"}:
            run_desktop(
                ui_base=args.ui_base,
                project_id=project_id,
                scene_id=args.scene_id,
                console_errors=console_errors,
                page_errors=page_errors,
                response_errors=response_errors,
                home_shot=args.home_shot,
                shots_shot=args.shots_shot,
                render_shot=args.render_shot,
            )
        if args.mode in {"mobile", "both"}:
            run_mobile(
                ui_base=args.ui_base,
                project_id=project_id,
                scene_id=args.scene_id,
                console_errors=console_errors,
                page_errors=page_errors,
                response_errors=response_errors,
                render_shot=args.mobile_render_shot,
            )
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if console_errors or page_errors or response_errors:
        print("console_errors=", json.dumps(console_errors, indent=2))
        print("page_errors=", json.dumps(page_errors, indent=2))
        print("response_errors=", json.dumps(response_errors, indent=2))
        return 1

    print(f"project_id={project_id}")
    print(f"desktop_home={args.home_shot}")
    print(f"desktop_shots={args.shots_shot}")
    print(f"desktop_render={args.render_shot}")
    print(f"mobile_render={args.mobile_render_shot}")
    print("console_errors=[]")
    print("page_errors=[]")
    print("response_errors=[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
