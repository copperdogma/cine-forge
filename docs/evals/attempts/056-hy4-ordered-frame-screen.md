# Attempt 056 — Hy4 ordered-frame screen

2026-11-05; [Story 235](../../stories/story-235-hy4-ordered-frame-evaluation.md),
Conductor Scout105, inclusive US$5 cap. Isolated current remote base
`a66e6834ecb98f2a656e34aa37fde0015d11c3af`; branch
`codex/hy4-20261105-cine-forge`, retained uncommitted at
`/Users/cam/.codex/worktrees/hy4-ripple-20261105/cine-forge`.

**Retain Sol/Luna research references; reject tested Hy4 high32768 replacement.**
The candidate invents gaps between the figures' heads and bodies and misses the
15-second latency gate. No model qualifies on the complete quality contract.

| Fresh dialogue case, n=1 each | Structural | Blind Opus | Combined | Dual passes | Seconds | Subject USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Hy4 high32768 | .3688 | .55 | .4594 | 0/1 | 128.072 | .0133283345 |
| Sol6.1 low4096 | .7733 | .72 | .74665 | 0/1 | 8.717 | .0029447 |
| Luna6 low1400 | .7919 | .72 | .75595 | 0/1 | 5.043 | .00022267 |

Hy4 costs 4.53 times Sol and takes 14.69 times as long; versus Luna it costs
59.86 times as much and takes 25.40 times as long. These are paired single-case
stage measurements, with no p95 or whole-workflow savings claim. The scored
128.072-second call was unpaused. Its native qualification's 242.893 seconds
includes an operator storage pause and is excluded from model latency evidence.

## Frozen contract and source review

Current maintained `video-understanding` v4 truth, prompt, source pixels, schema,
scorer and rubric are unchanged. This is a headless research comparator with no
shipped ordered-frame analyzer or autonomous QA integration. Ideal R12/R18,
spec7/8/9, state/graph and ADR003 were inspected; no architecture or compromise
change is proposed. Current v4 source repair supersedes historical v3 quarantine.

Exact official November4 `tencent/hy4`, canonical `tencent/hy4-20261104`, Tencent
FP4 through OpenRouter, explicit high effort and 32768 total output allowance.
Fresh Sol6.1 low4096 and Luna6 low1400 retain their maintained settings. All
subjects receive the same five original 640x360 JPEGs, opaque ID and neutral
timing facts. Only authored synthetic fixtures are eligible; retention/training
may apply. No audio, MP4, private screenplay, generation, resizing or new fixture.

Prospective gates: structural >=.70, rubric/combined >=.80, mean latency <=15s,
subject cost <=$.02. Serial independent cases, no subject-output cache. All three
native/adapter outgoing bodies are identical per arm, strict13-key schema,
terminal exact served identity, sane usage and cost. Wire `reasoning.effort=high`
and `max_completion_tokens=32768` are preserved. Hy4's scored call reports
10206 reasoning tokens. Natural provider input-cache reuse after qualification
is disclosed in complete raw usage; no fresh-cache claim.

**Model-wrong:** Hy4's frame3 evidence says “visibly wider gaps separate their
circular heads from the torsos.” Direct inspection of original frames0/3/4
shows heads touching or overlapping torsos, with no gaps. Both bodies grow
upward and sideways at fixed centers while the rectangle/background stay fixed.
Hy4 partially describes higher upper edges but calls the event slight shift or
drift; controls explicitly describe growth. The false gap claim is an observable
source error independent of lexical scoring. Continuity and rectangle retention
are correctly described. No prompt/golden/scorer repair is warranted.

**Ambiguous:** intimate/detached/surreal tone, isolation, gold/teal/desaturated
colors and closer/figures keyword penalties are interpretive or lexical. Opus's
stronger hallucination wording for those dimensions is not an independent fact.
Preserve every original score. The visible source error and latency suffice for
rejection without declaring these subjective penalties factual errors. No
`golden-wrong` finding. Red quality results are non-runtime-blocking because no
product caller or default changed.

Stop after this valid source failure. Prop/tunnel and the other three cases are
unmeasured. Lower/none efforts are unmeasured: the conditional lower-effort arm
required high to pass quality first. No within-task effort comparison or rescue.
No model earns promotion, no inferred mixed-model routing policy. Reopen only
for a material checkpoint/route/owner-contract change or an explicitly selected
new configuration; no unchanged paid repeat is recommended.

## Accounting, custody and durable evidence

All9 paid calls settled, **US$.102450684/5**, unknown exposure0:

- Scored subjects: $.0164957045 total (Hy4 .0133283345, Sol .0029447, Luna .00022267).
- Native qualification: $.0270099795.
- Independent full-source Opus4.6 judging: $.058945.
- Overhead above scored subjects: $.0859549795; no paid retries or post-stop calls.

OpenRouter cost is provider-reported. OpenAI/Anthropic costs are token-price
estimates using explicit usage/cache buckets, not invoices. Full-window Hy4
$.478225024 reservations safely admitted calls; settled usage released reserves.
Opus counts the actual complete source/output packet before dispatch under a
20K-input/8192-output reserve. Preflight rendered9 independent packets; saved
reference judge packets counted2509/2437/2417 tokens. No omitted source text.

The first native call was SIGSTOP-paused during root's shared disk ENOSPC
incident. The server request stayed live; root authorized resume after writable
space recovered. Complete raw output was saved before parsing and its settled
charge preserved. No evidence deletion or storage-induced retry. Existing owner
credentials loaded through the sanctioned wrapper; no injection, copy, new key
or temporary-variable cleanup. No private payloads or account changes.

[Immutable result](../../../benchmarks/results/video-understanding-hy4-vs-sol-luna-v4-20261105.json),
[manifest](../story-235-hy420261105-evidence.json),
[freeze](../story-235-hy420261105-hy4-freeze.json),
[source review](../evidence/story-235-hy420261105/source-review.json),
[validation](../evidence/story-235-hy420261105/validation.md).
Full safe requests/raw envelopes/receipts/ledger remain under
`docs/evals/evidence/story-235-hy420261105/`; producing code snapshots under
`docs/evals/snapshots/story-235-hy420261105/`. The immutable result closes the
paid runner; per-case admission prevents automatic later-case expansion.

Reproduction uses the owner wrapper around
`benchmarks/scripts/run_hy4_video_comparison.py preflight`, `qualify --first`,
then `judges --case vfp_active_001` with the retained first-case admission.
A later authorized run requires a new identity. Offline verification:
`PYTHONPATH=src <cineforge-python> benchmarks/scripts/report_hy4_video_comparison.py --verify`.
The verifier initially checked `max_tokens` instead of actual
`max_completion_tokens`; this offline-only check was repaired without inference
or changing subject outputs. Story frontmatter was also corrected to the local
multiline format before successful generation.

Validation: 65 focused tests, Ruff, offline evidence replay, registry consistency,
new immutable v35 contract manifest, methodology build/check and whitespace pass.
Existing architecture/UI freshness warnings remain. Product/frontend suites are
unrelated to this eval-only change. The worktree is retained for review, with no
commit, push, merge, deployment, default change or implicit cleanup.

Cam can skip this slow, source-inaccurate high configuration while retaining
both compatibility evidence and the inexpensive research references.
