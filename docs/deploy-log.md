# Deploy Log

Append-only deploy timing memory for AI recalibration.

Format:
`YYYYMMDD-HHMM | duration_s | status(success|failed) | cache_hit(yes|no|unknown) | note`

Entries:
`20260218-1712 | 109 | success | no | Fly deploy with smoke checks; warm builder and mostly cached layers`
`20260218-1715 | 53 | success | yes | Cache-hit deploy with all key layers reused; API+UI smoke checks passed`
