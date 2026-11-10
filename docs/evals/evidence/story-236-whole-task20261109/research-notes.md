# Research and execution framing — 2026-11-09

General problem: conservative reservation inflation in a nested retry/rescue
workflow with data-dependent entity counts. Reserving every maximum branch
as if simultaneously paid makes the historical USD5 control estimate invalid;
using average old cost would hide possible charges. Neither is a model-quality
finding.

Bounded primary-source review:
- https://platform.claude.com/docs/en/build-with-claude/token-counting — native
  pre-counting can bound current request inputs; estimates may differ from
  actual billed usage. Reserve explicit overhead and all requested output.
- https://platform.claude.com/docs/en/about-claude/pricing — current native
  pricing/cached buckets; bills reflect actual usage, so settle only validated
  usage and release unused reservations. Unknown HTTP exposure retains its
  full reservation. Owner cached pricing tables are not authoritative.
- https://platform.claude.com/docs/en/build-with-claude/structured-outputs —
  native strict JSON supports a subset and has grammar compilation limits;
  use a strict outer JSON-string projection plus complete original host schema
  and source/consumer validation, not a silent reduction of semantic fields.

Root strategic review approved sequential physical-HTTP admission as routine
staging within the same hardUSD20, preserving unchanged control models, output
allowances, nested retry/rescue topology, and fixed OpenFrequency→LastFerry→
Matinee order. It does not guarantee three paired cases will be funded.
Every physical send is independently admitted before dispatch, including
inner retries. Raw request/response saved before parse; actual known usage
settles, unknown holds; denied budget halts all later fallback sends. A partial
control is inconclusive, never a passing baseline or a Fable quality failure.
No paid call until root/Astra approve consumer representability and concrete
first-pair/review/recovery reservations. No semantic retry or effort sweep.

Local evidence: worker control-preflight records source/script-free offline
normalization across all3 authored fixtures,4 scenes each,0 normalization
inference. Source inventories are useful expected sizes, not hard limits on
baseline entity invention. Historical570388 bytes includes stale versions and
metadata but omits sidecars;23297 API tokens is not a representability proof.
The actual complete bundle and fanout dry-run must supply that evidence.
