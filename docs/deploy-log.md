# Deploy Log

Append-only deploy timing memory for AI recalibration.

Format:
`YYYYMMDD-HHMM | duration_s | status(success|failed) | cache_hit(yes|no|unknown) | note`

Entries:
`20260218-1712 | 109 | success | no | Fly deploy with smoke checks; warm builder and mostly cached layers`
`20260218-1715 | 53 | success | yes | Cache-hit deploy with all key layers reused; API+UI smoke checks passed`
`20260219-1220 | 0 | failed | no | tsc -b build failure: unused variable in RunProgressCard.tsx (tsc --noEmit didn't catch it)`
`20260219-1222 | 142 | success | partial | Second attempt after fix; src/ layer cache miss, apt+npm cached; API+UI smoke passed`
`20260219-0746 | 103 | success | partial | Deploy from local main working tree (uncommitted Story 049 files); API+Playwright UI smoke checks passed`
`20260219-0835 | 80 | success | yes | Cache-hit Fly deploy; API+Playwright UI smoke checks passed`
`20260219-1214 | 396 | success | partial | Deploy after project_not_opened fix; remote builder wait + pip install layer rebuild; API+Playwright UI smoke passed`
`20260219-1731 | 140 | success | partial | Deploy 0.1.3; pip layer rebuilt, frontend cached; API+Playwright UI smoke passed`
2026-02-20T21:29:11Z | 94 | success | false | feat: Story 019
2026-02-20T21:41:02Z | 98 | success | false | chore: deploy v2026.02.20-02
2026-02-20T22:04:24Z | 102 | success | partial | feat: Story 057 (Entity Navigation) + ruff fix; v2026.02.20-03; frontend rebuilt, pip reinstalled
20260221-0130 | 150 | success | partial | Story 041 completion; entity_discovery module live; UI width + crash fixes; v2026.02.20-04; API/UI smoke checks passed
2026-02-21T14:00:52Z | 126 | success | true | Pipeline UI and Quality Fixes
2026-02-22T01:04:00Z | 181 | success | partial | Story 058 complete; backend-driven export system live; PDF/DOCX/Fountain support; CLI export enabled; v2026.02.21-02
2026-02-22T02:19:47Z | 117 | success | unknown | Story 061 performance optimizations
2026-02-21T19:35:11Z | 99 | success | true | Automatic Project Title Extraction (Story 063)
2026-02-22T01:02:04 | 105 | success | partial | Story 064 high-fidelity rendering
2026-02-22T10:54:00 | 135 | success | partial | Story 066 UI deduplication + lockfile sync fix; v2026.02.22-02; API+browser UI smoke passed
20260222-1508 | 106 | success | partial | Stories 067-069 UI polish bundle; v2026.02.22-05; API+browser UI smoke passed
20260222-1410 | 93 | success | partial | Story 065 parallel bible extraction; v2026.02.22-08; src/ layer rebuilt, frontend fully cached; API+browser UI smoke passed
20260222-2005 | 90 | success | partial | Story 062 3-stage ingestion + UI fixes; v2026.02.22-10; src/ layer rebuilt (new modules), frontend rebuilt; API+browser UI smoke passed
20260223-1033 | 113 | success | partial | Story 074 graph staleness fix + tests; v2026.02.23-01; src/ layer rebuilt, frontend rebuilt; API smoke passed; browser UI passed (fresh MCP tab required — detached tab fix)
20260223-1222 | 83 | success | partial | Story 052 streaming yield + nav row glow; v2026.02.23-02; src/ layer rebuilt, frontend rebuilt (new CSS/JS); API smoke passed; browser unavailable (HTTP fallback)
20260223-2115 | 86 | success | partial | Stories 045+075-078 entity detail polish + graph edges; v2026.02.23-04; src/ layer rebuilt, frontend rebuilt; API smoke passed; browser UI smoke passed (no app errors)
20260223-2335 | 102 | success | partial | Story 079 chat/nav polish bundle; v2026.02.23-05; src/ layer rebuilt, frontend rebuilt; API smoke passed; browser UI smoke passed (no app errors)
20260224-0237 | 80 | success | partial | Story 070 scene dividers + entity hotlinks + hover states; v2026.02.23-06; CHANGELOG+frontend rebuilt; API smoke passed; browser unavailable (HTTP fallback)
20260224-0400 | 106 | success | partial | Story 077 character prominence tiers + minor extraction; v2026.02.23-07; src/ rebuilt (new schema+extraction), frontend rebuilt (new component+badges); API smoke passed; browser disconnected (HTTP fallback, console no app errors)
20260224-0550 | 200 | success | partial | Story 081 scene index canonical characters + prominence sort; v2026.02.24-02; src/ rebuilt (entity_discovery changes), frontend rebuilt (sort fix); API smoke passed; browser disconnected (HTTP fallback)
20260224-1400 | 218 | success | partial | Story 083 group chat architecture + UX polish; v2026.02.24-06; src/ rebuilt (chat streaming), frontend rebuilt (ChatPanel overhaul); API smoke passed; browser unavailable (HTTP fallback — title OK, bundle 200)
20260225-1630 | 238 | success | partial | Story 084 character chat agents + chat persistence + story editor rename; v2026.02.25-01; src/ rebuilt (chat.py, app.py, roles rename), frontend rebuilt (ChatPanel sections, character bubbles); API smoke passed (health/recipes/projects 200); browser unavailable (HTTP fallback — title OK, bundle 200)
20260227-2230 | 100 | success | partial | Stories 085-089+093 batch deploy; v2026.02.27-03; src/ rebuilt, frontend rebuilt; API smoke passed (health/recipes/projects/changelog 200); browser UI smoke passed (no app errors)
20260302-0052 | 149 | success | partial | Eval verification deploy; v2026.03.02-01; src/ rebuilt (pip reinstall), frontend rebuilt; API smoke passed (health/recipes/projects/changelog 200); browser UI smoke passed (no app errors)
20260302-1530 | 123 | success | partial | Story 111 hash-based "View in Script" scroll fix; v2026.03.02-04; frontend rebuilt (4 UI files changed), src/ cached; API smoke passed (health 200 version confirmed); browser disconnected (HTTP fallback — title OK, bundle 200)
2026-03-14T04:43:58Z | 14 | failed | unknown | Fly remote builder transport failure before image build: unable to upgrade to h2c, received 500
2026-03-14T04:46:14Z | 12 | failed | unknown | Second remote deploy retry hit the same Fly builder h2c 500 before Docker build
2026-03-14T04:50:33Z | 247 | success | no | Local-only deploy after remote builder failures; API smoke passed (health/recipes/projects/recent/changelog 200); UI HTTP fallback passed (title OK, bundle 200); browser unavailable in-session
2026-04-03T22:55:16Z | 29 | failed | unknown | Remote Fly builder heartbeat failed before image build: failed to parse daemon host "unix:///var/run/docker.sock": missing hostname
2026-04-03T23:34:26Z | 3 | failed | unknown | Local-only deploy hit Dockerfile parse error at line 30: unknown instruction ")" while parsing the multi-line CUTOFF RUN block
2026-04-03T23:54:09Z | 186 | success | no | Local-only deploy after remote builder heartbeat failure, Dockerfile parse fix, and Docker builder cache prune; API smoke passed (health/recipes/projects/recent/changelog 200); UI HTTP fallback passed (title OK, bundle 200); browser unavailable in-session
2026-04-04T20:48:38Z | 168 | success | partial | Remote-builder deploy for Story 044 mobile operator console; health version 2026.04.04-04; API smoke passed (health/recipes/projects/recent/changelog 200); browser UI smoke passed (home + /the-mariner, screenshots captured, no console/page errors)
2026-04-16T17:19:26Z | 463 | failed | unknown | Remote-builder deploy stalled after image build/push start; no new Fly release appeared, old image remained active, attempt terminated after bounded wait
2026-04-16T17:20:12Z | 4 | failed | unknown | Local-only retry failed immediately because Docker daemon was unavailable at unix:///Users/cam/.docker/run/docker.sock
2026-04-16T17:30:10Z | 92 | success | partial | Remote-builder retry succeeded with heavily cached layers; production advanced to v2026.04.13-02; API smoke passed (health/recipes/projects/recent/changelog 200); browser UI smoke passed on home + /the-mariner-11 with 0 console errors and 1 CodeMirror warning
2026-04-20T16:06:51Z | 158 | success | no | Remote-builder deploy from clean main after check-in; health version 2026.04.20-02; API smoke passed (health/recipes/projects/recent/changelog 200); browser UI smoke passed on home + /the-mariner-11 with 0 console errors and 1 CodeMirror warning
