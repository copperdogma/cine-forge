from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

DEFAULT_UI_BASE = "http://127.0.0.1:5174"
DEFAULT_SCENE_ID = "scene_001"
DEFAULT_HOME_SHOT = Path("/tmp/story157-chat-home-desktop.png")
DEFAULT_SCENE_SHOT = Path("/tmp/story157-chat-render-desktop.png")
DEFAULT_MOBILE_HOME_SHOT = Path("/tmp/story157-chat-home-mobile.png")
DEFAULT_MOBILE_SCENE_SHOT = Path("/tmp/story157-chat-render-mobile.png")
STALE_CTA_LABELS = ("Break Down Script", "Deep Breakdown", "Refine World Model")
ARCHIVED_TEXT = re.compile(r"Completed path archived|Completed paths archived")


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
        page.get_by_role("button", name="Close chat").first.wait_for(
            state="visible",
            timeout=10_000,
        )
        page.wait_for_timeout(300)
        return

    show_panel = page.get_by_role("button", name="Show panel")
    if show_panel.count() and show_panel.first.is_visible():
        show_panel.first.click()


def assert_no_stale_ctas(page: Page, *, route_label: str) -> None:
    for label in STALE_CTA_LABELS:
        locator = page.get_by_role("button", name=label)
        if any_visible(locator):
            raise AssertionError(f"{route_label}: stale CTA still rendered as a button: {label}")

    if not any_visible(page.get_by_text(ARCHIVED_TEXT)):
        raise AssertionError(f"{route_label}: archived CTA indicator did not render")


def verify_home(
    page: Page,
    *,
    ui_base: str,
    project_id: str,
    mobile: bool,
    screenshot_path: Path,
) -> None:
    page.goto(f"{ui_base}/{project_id}")
    wait_for_network_idle(page)
    page.get_by_text("All 67 artifacts are current").first.wait_for(timeout=15_000)
    ensure_chat_visible(page, mobile=mobile)
    assert_no_stale_ctas(page, route_label="home")
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=not mobile)


def verify_scene_render(
    page: Page,
    *,
    ui_base: str,
    project_id: str,
    scene_id: str,
    mobile: bool,
    screenshot_path: Path,
) -> None:
    page.goto(f"{ui_base}/{project_id}/scenes/{scene_id}?tab=render")
    wait_for_network_idle(page)
    page.get_by_role("button", name="Run Render for Current Scene").first.wait_for(timeout=15_000)
    ensure_chat_visible(page, mobile=mobile)
    assert_no_stale_ctas(page, route_label="scene_render")
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(screenshot_path), full_page=not mobile)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Focused browser smoke for Story 157 chat CTA honesty. "
            "Requires the local UI server and an explicit representative project "
            "produced through the normal pipeline."
        )
    )
    parser.add_argument("--ui-base", default=DEFAULT_UI_BASE)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--scene-id", default=DEFAULT_SCENE_ID)
    parser.add_argument("--mode", choices=("desktop", "mobile", "both"), default="both")
    parser.add_argument("--home-shot", type=Path, default=DEFAULT_HOME_SHOT)
    parser.add_argument("--scene-shot", type=Path, default=DEFAULT_SCENE_SHOT)
    parser.add_argument("--mobile-home-shot", type=Path, default=DEFAULT_MOBILE_HOME_SHOT)
    parser.add_argument("--mobile-scene-shot", type=Path, default=DEFAULT_MOBILE_SCENE_SHOT)
    return parser.parse_args()


def run_mode(
    *,
    mobile: bool,
    ui_base: str,
    project_id: str,
    scene_id: str,
    home_shot: Path,
    scene_shot: Path,
    console_errors: list[str],
    page_errors: list[str],
    response_errors: list[str],
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 390, "height": 844} if mobile else {"width": 1440, "height": 1200},
            is_mobile=mobile,
        )
        page = context.new_page()
        prefix = "mobile" if mobile else "desktop"
        record_browser_errors(page, console_errors, page_errors, response_errors, prefix)
        verify_home(
            page,
            ui_base=ui_base,
            project_id=project_id,
            mobile=mobile,
            screenshot_path=home_shot,
        )
        verify_scene_render(
            page,
            ui_base=ui_base,
            project_id=project_id,
            scene_id=scene_id,
            mobile=mobile,
            screenshot_path=scene_shot,
        )
        context.close()
        browser.close()


def main() -> int:
    args = parse_args()
    console_errors: list[str] = []
    page_errors: list[str] = []
    response_errors: list[str] = []

    try:
        if args.mode in {"desktop", "both"}:
            run_mode(
                mobile=False,
                ui_base=args.ui_base,
                project_id=args.project_id,
                scene_id=args.scene_id,
                home_shot=args.home_shot,
                scene_shot=args.scene_shot,
                console_errors=console_errors,
                page_errors=page_errors,
                response_errors=response_errors,
            )
        if args.mode in {"mobile", "both"}:
            run_mode(
                mobile=True,
                ui_base=args.ui_base,
                project_id=args.project_id,
                scene_id=args.scene_id,
                home_shot=args.mobile_home_shot,
                scene_shot=args.mobile_scene_shot,
                console_errors=console_errors,
                page_errors=page_errors,
                response_errors=response_errors,
            )
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if console_errors or page_errors or response_errors:
        print("console_errors=", json.dumps(console_errors, indent=2))
        print("page_errors=", json.dumps(page_errors, indent=2))
        print("response_errors=", json.dumps(response_errors, indent=2))
        return 1

    print(f"desktop_home={args.home_shot}")
    print(f"desktop_scene={args.scene_shot}")
    print(f"mobile_home={args.mobile_home_shot}")
    print(f"mobile_scene={args.mobile_scene_shot}")
    print("console_errors=[]")
    print("page_errors=[]")
    print("response_errors=[]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
