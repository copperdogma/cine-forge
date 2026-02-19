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
