# Story 196 Evidence

Captured: 2026-05-04

## Inputs

- Historical Brick & Steel inbox batch: `raw-inbox-90a67ec-parent.md`, copied from `git show 90a67ec^:docs/inbox.md`.
- Current inbox before routing: `current-inbox-before-routing.md`.
- Representative local project: `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired`.
- Browser/API code under test: `/Users/cam/.codex/worktrees/d9ca/cine-forge`.

## Artifact Snapshot

See `artifact-snapshot.json`.

Key current facts:

- Project: `brick-steel-full-retired` / `Brick & Steel: Full Retired` / `live_action`.
- Current character entities still include duplicate/alias-like entries: `brick`, `brick_braddock`, `steel`, `dick`, and `dick_steel`.
- Brick Braddock design study exists with one `gpt-image-1` round, 4 images, and `design_study_r1_img1.jpg` selected.
- Dick Steel design study exists with one `gpt-image-1` round, 4 images, and `design_study_r1_img3.jpg` selected.
- Scene 001 has `render_clip_plan/scene_001/v2` and 8 generated-video render clips.
- Each render clip has a generated-video artifact and media file.
- Each render clip prompt has two resolved direct character reference images.
- Clip 001 prompt preserves exact dialogue bullets for `STEEL: Screw retirement.` and `BRICK: Screw retirement.` and does not contain the old `bear joke` summary phrase.
- Scene 001 has no current `keyframe` artifact.

## Browser Pass

The browser check used the worktree UI/API code against the primary checkout workspace root:

```bash
PYTHONPATH=/Users/cam/.codex/worktrees/d9ca/cine-forge/src \
/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -c 'from pathlib import Path; import uvicorn; from cine_forge.api.app import create_app; app = create_app(workspace_root=Path("/Users/cam/Documents/Projects/cine-forge"), enable_startup_dependency_checks=False); uvicorn.run(app, host="127.0.0.1", port=8123, log_level="warning")'
```

UI server:

```bash
cd /Users/cam/.codex/worktrees/d9ca/cine-forge/ui
CINE_FORGE_API_URL=http://127.0.0.1:8123 CINE_FORGE_UI_PORT=5178 \
/Users/cam/Documents/Projects/cine-forge/ui/node_modules/.bin/vite \
  --config /Users/cam/.codex/worktrees/d9ca/cine-forge/ui/vite.config.ts \
  --host 127.0.0.1
```

Environment note: this worktree has no local `.venv` or `ui/node_modules`; the pass used the primary checkout venv and an ignored `ui/node_modules` symlink to the primary checkout dependencies.

Browser script: `browser_check.py`

Summary: `browser/browser-summary.json`

Final browser result:

- Routes checked: 13
- Blank screens: 0
- Console errors: 0
- Page errors: 0
- HTTP errors: 0
- Video-count mismatches: 0
- Routes with non-fatal missing expected text: 2
  - `generated-video-detail-desktop` did not display the literal `scene_render.mp4` filename, but did show one video and loaded without errors.
  - `home-mobile` did not include the `Start Scene Work` CTA text, but loaded without errors. This is UI hierarchy/surface-placement pressure routed to Story 185, not a Scene Workspace runtime blocker.
- Desktop Scene Workspace Previz: 8 videos visible
- Desktop Scene Workspace Render: 8 videos visible
- Mobile Scene Workspace Previz: 8 videos visible
- Mobile Scene Workspace Render: 8 videos visible

Screenshots:

- `browser/home-desktop.png`
- `browser/characters-desktop.png`
- `browser/brick-braddock-desktop.png`
- `browser/dick-steel-desktop.png`
- `browser/previz-desktop.png`
- `browser/render-desktop.png`
- `browser/render-prompt-detail-desktop.png`
- `browser/generated-video-detail-desktop.png`
- `browser/media-validation-detail-desktop.png`
- `browser/home-mobile.png`
- `browser/characters-mobile.png`
- `browser/previz-mobile.png`
- `browser/render-mobile.png`

The first browser attempt captured skeleton states because the script did not wait long enough for artifact queries. The final `browser-summary.json` is the evidence source of record.

## Follow-Up Routing

- Story 185 received the current `UI Plan` note and the validation addendum that mobile Home currently loads but does not expose `Start Scene Work` text.
- Story 197 received the current `xAI images` note.
- Story 201 was created for the live keyframe affordance warning found during this scrub.
- `docs/inbox.md` now has no live items.
