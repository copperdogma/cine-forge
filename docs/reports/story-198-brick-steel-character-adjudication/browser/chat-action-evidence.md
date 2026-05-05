# Story 198 Chat / Artifact-Edit Browser Evidence

Captured: 2026-05-05T13:41:51Z

## Scope

- Route: Characters surface plus ChatPanel action button.
- Source project copied from `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired`.
- Disposable project copy: `/tmp/story198-chat-action-smoke-20260505-074141`.
- Local UI/API route: `http://127.0.0.1:5198/story198-chat-action-smoke-20260505-074141/characters`.
- This probe did not call a live model. It seeded a synthetic AI suggestion through the existing chat API, then clicked the real in-browser chat action so the real artifact-edit endpoint handled the request.

## Result

- Direct API control returned `422` with code `unsupported_artifact_edit`.
- Desktop browser action surfaced the unsupported identity-edit error: `True`.
- Mobile browser action surfaced the unsupported identity-edit error: `True`.
- Bible manifest versions before: `[1, 2]`.
- Bible manifest versions after: `[1, 2]`.
- No new bible-manifest version was created by the rejected browser actions: `True`.
- Unexpected page errors: `[]`.
- Unexpected 4xx/5xx responses excluding the expected edit rejection: `[]`.
- Browser console included the expected `Failed to load resource: ... 422`
  message for the rejected edit request; no unexpected console/page failure was
  observed.

## Screenshots

- `chat-action-desktop-before.png` - desktop Characters route with seeded chat action visible before clicking.
- `chat-action-desktop-after.png` - desktop route after clicking, showing the UI-level unsupported edit message.
- `chat-action-mobile-before.png` - mobile route/chat sheet with seeded chat action visible before clicking.
- `chat-action-mobile-after.png` - mobile route/chat sheet after clicking, showing the UI-level unsupported edit message.

## Interpretation

At capture time, the source Brick & Steel production artifacts still showed both `Brick` and `Brick Braddock`, so this probe must not be read as post-rerun Characters-route proof. It does show that the local ChatPanel confirm-action path can be exercised safely and that a duplicate-character merge/deprecation attempt reaches the real artifact-edit API, returns the Story 198 `unsupported_artifact_edit` blocker, and does not create a misleading new artifact version.

Post-refresh verification on 2026-05-05T13:59:57Z confirmed the later live route evidence owns the post-fix Characters-route truth. This existing chat-action evidence remains valid for the unsupported identity-merge path because it records the real browser action, expected `422 unsupported_artifact_edit` response, unchanged manifest versions, no unexpected browser failures, and no production artifact mutation. It did not exercise live LLM tool selection; the suggestion was seeded so the browser could test the concrete action path deterministically.
