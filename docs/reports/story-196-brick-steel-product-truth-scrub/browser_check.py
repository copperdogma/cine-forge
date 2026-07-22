from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

REPORT_DIR = Path(__file__).resolve().parent
BROWSER_DIR = REPORT_DIR / "browser"
BASE_URL = os.environ.get("CINE_FORGE_UI_BASE_URL", "http://127.0.0.1:5174").rstrip("/")


ROUTES: list[dict[str, Any]] = [
    {
        "id": "home-desktop",
        "path": "/brick-steel-full-retired",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["Brick & Steel", "Start Scene Work"],
    },
    {
        "id": "characters-desktop",
        "path": "/brick-steel-full-retired/characters",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["Characters", "Brick Braddock", "Dick Steel"],
    },
    {
        "id": "brick-braddock-desktop",
        "path": "/brick-steel-full-retired/characters/brick_braddock",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["BRICK BRADDOCK", "Reference Library", "Design Study"],
    },
    {
        "id": "dick-steel-desktop",
        "path": "/brick-steel-full-retired/characters/dick_steel",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["DICK STEEL", "Reference Library", "Design Study"],
    },
    {
        "id": "previz-desktop",
        "path": "/brick-steel-full-retired/scenes/scene_001?tab=previz",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["Focused workspace", "Previz", "AI Previz Clips", "scene_001_clip_008"],
        "jump": True,
        "min_videos": 8,
    },
    {
        "id": "render-desktop",
        "path": "/brick-steel-full-retired/scenes/scene_001?tab=render",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["Focused workspace", "Production", "Render Clips", "scene_001_clip_008"],
        "jump": True,
        "min_videos": 8,
    },
    {
        "id": "render-prompt-detail-desktop",
        "path": "/brick-steel-full-retired/artifacts/render_prompt/scene_001_clip_001/1",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": [
            "render_prompt",
            "Exact Dialogue Timing",
            "STEEL: Screw retirement",
            "BRICK: Screw retirement",
        ],
    },
    {
        "id": "generated-video-detail-desktop",
        "path": "/brick-steel-full-retired/artifacts/generated_video/scene_001_clip_001/1",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["generated_video", "Scene 1", "scene_render.mp4"],
        "min_videos": 1,
    },
    {
        "id": "media-validation-detail-desktop",
        "path": "/brick-steel-full-retired/artifacts/media_validation/scene_001_clip_001/4",
        "viewport": {"width": 1440, "height": 1100},
        "expect_text": ["media_validation", "Runtime trust report", "pass"],
    },
    {
        "id": "home-mobile",
        "path": "/brick-steel-full-retired",
        "viewport": {"width": 390, "height": 844, "is_mobile": True},
        "expect_text": ["Brick & Steel", "Start Scene Work"],
    },
    {
        "id": "characters-mobile",
        "path": "/brick-steel-full-retired/characters",
        "viewport": {"width": 390, "height": 844, "is_mobile": True},
        "expect_text": ["Characters", "Brick Braddock", "Dick Steel"],
    },
    {
        "id": "previz-mobile",
        "path": "/brick-steel-full-retired/scenes/scene_001?tab=previz",
        "viewport": {"width": 390, "height": 844, "is_mobile": True},
        "expect_text": ["Focused workspace", "Previz", "AI Previz Clips"],
        "jump": True,
        "min_videos": 8,
    },
    {
        "id": "render-mobile",
        "path": "/brick-steel-full-retired/scenes/scene_001?tab=render",
        "viewport": {"width": 390, "height": 844, "is_mobile": True},
        "expect_text": ["Focused workspace", "Production", "Render Clips"],
        "jump": True,
        "min_videos": 8,
    },
]


def normalize_error(message: str) -> str:
    return " ".join(message.split())


def visible_text(page: Page) -> str:
    return page.locator("body").inner_text(timeout=5_000)


def inspect_route(page: Page, route: dict[str, Any]) -> dict[str, Any]:
    route_id = route["id"]
    url = f"{BASE_URL}{route['path']}"
    page.set_viewport_size(
        {
            "width": route["viewport"]["width"],
            "height": route["viewport"]["height"],
        }
    )
    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except PlaywrightTimeoutError:
        pass
    expected = route.get("expect_text", [])
    for _ in range(20):
        text_now = visible_text(page)
        if not expected or any(item in text_now for item in expected):
            break
        page.wait_for_timeout(1_000)

    before_jump_y = page.evaluate("() => window.scrollY")
    jump_clicked = False
    after_jump_y = before_jump_y
    if route.get("jump"):
        jump_button = page.get_by_role("button", name="Jump to selected panel")
        if jump_button.count() > 0:
            jump_button.first.click()
            jump_clicked = True
            page.wait_for_timeout(700)
            after_jump_y = page.evaluate("() => window.scrollY")

    text = visible_text(page)
    screenshot_name = f"{route_id}.png"
    page.screenshot(path=str(BROWSER_DIR / screenshot_name), full_page=True)

    links = page.locator("a").evaluate_all(
        "(nodes) => nodes.map((node) => ({text: node.innerText, href: node.href}))"
        ".filter((item) => item.href.includes('/artifacts/')).slice(0, 20)"
    )
    facts = {
        "id": route_id,
        "url": url,
        "screenshot": f"browser/{screenshot_name}",
        "body_text_length": len(text),
        "h1": page.locator("h1").all_inner_texts(),
        "h2": page.locator("h2").all_inner_texts()[:20],
        "buttons": page.locator("button").all_inner_texts()[:40],
        "video_count": page.locator("video").count(),
        "image_count": page.locator("img").count(),
        "artifact_links": links,
        "jump_clicked": jump_clicked,
        "jump_scroll_y": {"before": before_jump_y, "after": after_jump_y},
        "missing_expected_text": [
            item for item in route.get("expect_text", []) if item not in text
        ],
        "min_video_expected": route.get("min_videos"),
    }
    min_videos = route.get("min_videos")
    if min_videos is not None:
        facts["video_count_ok"] = facts["video_count"] >= min_videos
    facts["blank_screen"] = len(text.strip()) < 100
    return facts


def main() -> int:
    BROWSER_DIR.mkdir(parents=True, exist_ok=True)
    console_errors: list[dict[str, str]] = []
    page_errors: list[dict[str, str]] = []
    response_errors: list[dict[str, Any]] = []
    route_facts: list[dict[str, Any]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.on(
            "console",
            lambda message: (
                console_errors.append({"type": message.type, "text": normalize_error(message.text)})
                if message.type == "error"
                else None
            ),
        )
        page.on(
            "pageerror",
            lambda exc: page_errors.append({"message": normalize_error(str(exc))}),
        )
        page.on(
            "response",
            lambda response: (
                response_errors.append({"status": response.status, "url": response.url})
                if response.status >= 400
                else None
            ),
        )

        for route in ROUTES:
            route_facts.append(inspect_route(page, route))

        browser.close()

    summary = {
        "base_url": BASE_URL,
        "routes": route_facts,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "response_errors": response_errors,
        "totals": {
            "routes": len(route_facts),
            "blank_screens": sum(1 for item in route_facts if item["blank_screen"]),
            "routes_with_missing_expected_text": sum(
                1 for item in route_facts if item["missing_expected_text"]
            ),
            "routes_with_video_count_mismatch": sum(
                1 for item in route_facts if item.get("video_count_ok") is False
            ),
            "console_errors": len(console_errors),
            "page_errors": len(page_errors),
            "response_errors": len(response_errors),
        },
    }
    (BROWSER_DIR / "browser-summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    fatal_blank = any(item["blank_screen"] for item in route_facts)
    return 2 if fatal_blank else 0


if __name__ == "__main__":
    raise SystemExit(main())
