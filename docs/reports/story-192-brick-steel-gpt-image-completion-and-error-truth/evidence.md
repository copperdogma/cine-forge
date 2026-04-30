# Story 192 Evidence

## Runtime State

- Existing project: `brick-steel-full-retired`
- Existing Brick design-study state: `output/brick-steel-full-retired/artifacts/bibles/character_brick_braddock/design_study_state.json`
- Existing Dick design-study state: `output/brick-steel-full-retired/artifacts/bibles/character_dick_steel/design_study_state.json`
- Both existing states now contain one completed `gpt-image-1` round with four images, so the older missing-Dick-state evidence from Story 191 is stale in this checkout.

## Browser Verification

Fresh dev servers:

- API: `PYTHONPATH=src .venv/bin/python -m cine_forge.api --port 8123`
- UI: `CINE_FORGE_UI_PORT=5176 CINE_FORGE_API_URL=http://127.0.0.1:8123 pnpm --dir ui run dev -- --host 127.0.0.1`

Build-pass routes checked:

- Desktop and mobile: `http://[::1]:5176/brick-steel-full-retired/characters/brick_braddock`
- Desktop and mobile synthetic provider-failure fixture: `http://[::1]:5176/cineforge-story-192-design-study-failure/characters/test_subject`

Screenshots and console summary:

- `browser/brick-braddock-design-study-section-desktop.png`
- `browser/brick-braddock-design-study-section-mobile.png`
- `browser/provider-failure-panel-desktop.png`
- `browser/provider-failure-panel-mobile.png`
- `browser/browser-summary.json`

Result: `0` console errors, `0` page errors, and `0` HTTP errors during browser checks.

The provider-failure browser fixture is a no-cost mechanical fixture created under `/tmp/cineforge-story-192-design-study-failure`; it uses the normal API and character detail route, but triggers the design-study failure state with an unsupported image model rather than a paid live-provider failure.

Validation-pass routes checked with `validate_browser_check.py`:

- Desktop and mobile: `http://[::1]:5176/brick-steel-full-retired/characters/brick_braddock`
- Desktop and mobile synthetic failed-round fixture: `http://[::1]:5176/cineforge-story-192-design-study-failure-validate/characters/test_subject`

Validation screenshots and console summary:

- `browser/validate-brick-braddock-desktop.png`
- `browser/validate-brick-braddock-mobile.png`
- `browser/validate-provider-failure-desktop.png`
- `browser/validate-provider-failure-mobile.png`
- `browser/validate-browser-summary.json`

Validation result: `0` console errors, `0` page errors, and `0` HTTP errors. The validation fixture remains a no-cost mechanical fixture, but it is created through the normal API/project path and exercises the same persisted failed-round UI state. The validation pass also corrected a sticky-composer overlap so the provider message and prompt context remain visible on desktop and mobile.

## Verification Commands

- `.venv/bin/python -m pytest tests/unit/test_provider_failures.py tests/unit/test_ai_image.py tests/integration/test_api_design_study.py -q` -> passed
- `node --test ui/tests/design-study-status.test.ts` -> `2 passed`
- `node --test ui/tests/*.test.ts` -> `21 passed`
- `.venv/bin/python -m ruff check src/ tests/` -> passed
- `make test-unit PYTHON=.venv/bin/python` -> `845 passed, 183 deselected, 1 known warning`
- `pnpm --dir ui run lint` -> passed
- `cd ui && npx tsc -b` -> passed
- `pnpm --dir ui run build` -> passed with the existing Vite chunk-size warning
- `pnpm methodology:compile` -> regenerated `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`
- `pnpm methodology:check` -> current, with expected architecture-audit and UI-scout freshness warnings
- `git diff --check` -> passed
