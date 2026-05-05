# Story 198 Characters Route Evidence

Captured: 2026-05-05T14:07:57.989239+00:00

- Route: `http://127.0.0.1:5199/brick-steel-full-retired/characters`.
- Desktop screenshot: `characters-desktop.png` (1440x1000 viewport).
- Mobile screenshot: `characters-mobile.png` (390x844 viewport).
- API artifact groups now expose `character_bible/brick:v2` and `bible_manifest/character_brick:v2` as current Brick character groups.
- API artifact groups no longer expose any `brick_braddock` current group, including character bibles, bible manifests, or continuity states.
- Desktop and mobile entity-card headings include `Brick` and do not include a separate `Brick Braddock` card.
- Raw page text may still include `Brick Braddock` as alias/descriptive canon under canonical Brick; that is expected.
- Console, page-error, and >=400 response captures were clean for both viewports.
