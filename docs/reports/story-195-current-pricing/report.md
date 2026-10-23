# Story195 current-price readiness — 2026-10-23

Result: **validated and closed**. Readiness now uses the same exact current video
price contract as execution. The active recipe yields a4-second480p video-only
example ofUSD.20 atUSD.05/second, with provider/model/resolution/source/check-date.
The example excludes compiler, reference backfill, validation and extra clips;
it is not a scene/run quote and actual prepared clip durations can differ.

Red fixture: `service-red.txt` captured the real configured xAI pack being marked
unpriced because its obsolete benchmark-rate field was absent. The service now
ignores benchmark rates, including the deliberately bogus99 fixture, and uses
canonical `resolve_video_price` plus shared duration normalization. Missing,
bool, zero, negative, nonfinite duration; unsupported resolution; retired and
unqualified targets all return blocked with no numeric amount. No price changes,
provider/default adoption or quality/latency-gate changes were made.

Evidence:61 affected service/schema/API tests (`affected-green.txt`),15 focused
service cases (`service-green.txt`),26 UI helper cases and lint/TypeScript/build
(`ui-checks.txt`). No model quality eval ran, so no registry score changed. Full
merged-tree checks are recorded in the batch integration report. Typed price
and duration evidence precedes cross-layer use; previz TS contracts were
extracted from the oversized central type file, which keeps canonical exports.
No new ledger, dashboard, event or reservation framework was added.

API restarted cleanly; `live-api-status.json` shows experimental_manual and no
quality score despite available pricing. Actual normally produced historical
Brick & Steel artifact inspected at desktop1600x1100 andmobile390x844: scoped
current-recipe price/source/date/exclusions are separate from the old saved
video’s unverified cost. Screenshots/DOM are `desktop.*` and `mobile.*`;
`console.json` is empty. This is representative rendering evidence, not fresh
provider quality or actual billing. No live provider or credential call occurred.

Strong read-only reviewer found no material issue in the sole producer and its
consumers; Codex advisory output is `codex-review.txt`. The schema requires
estimate evidence; arithmetic is deterministic in the current producer. Source
hashes and inspected service output are in `source-hash-summary.json`.

ADR002 preflight and003 demand-driven Film lane apply. This repairs an existing
readiness contradiction before larger prepare/inspect work in138. The canonical
FP1 continuation remains blocked (renumbered232 after incoming main claimed229).
No deployment, secret rotation, current media quality, or completed FP1 is
claimed. Operator rotation of the previously exposed xAI key remains necessary
before live xAI use; the incident is recorded in032’s report.

Optional verification: open the normal Brick AI-previz artifact or scene Previz
panel and inspect the current-recipe example and source link. Saved artifact
cost remains separately qualified. User authorized check-in/push of the batch,
then stopping the goal. No new triage work follows landing.
