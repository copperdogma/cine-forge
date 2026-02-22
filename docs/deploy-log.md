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
