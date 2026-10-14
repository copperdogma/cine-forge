# Attempt 050 — Argon v4 three-case ordered-frame screen

Date: 2026-10-13. Owner: Story 226 continuation; approved Conductor Scout 092 item 3. Inclusive hard cap: USD5, with no transfers.

**Do not adopt Argon medium for this ordered-frame lane.** It correctly observes the core source changes but demonstrates no qualified quality, latency or cost win. Retain the maintained references. This is headless research; no shipped analyzer/default exists.

| Fresh subject | Deterministic | Original Opus | Original combined | Source-adjudicated combined | Dual passes | Mean subject latency | Mean subject cost estimate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Argon native medium / 32768 | .53733 | .64000 | .58867 | .59533 | 0/3 | 15.592s | $.01687417 |
| Sol 6.1 direct low / 4096 | .53340 | .68667 | .61003 | .61003 | 0/3 | 9.071s | $.00777057 |
| Luna 6 direct low / 1400 | .59997 | .63000 | .61498 | .61498 | 0/3 | 5.833s | $.00043234 |

The three independent cases are dialogue, prop continuity and storm motion, each with five original 640×360 ordered JPEGs, opaque identifiers and neutral timing. The maintained v4 prompt, scorer and targets stayed frozen. Remaining full-six cases are not measured. Opus 4.6 strict1024 reviewed all nine scored answers independently of the subjects' providers. A symmetric source-assisted repair of prop reviews is reported separately from the original rubric totals.

Argon passed 3/3 hard constraints, 2/3 latency gates and 1/3 cost gates. Its dialogue call took 24.381s, above 15s; prop and motion cost $.021038 and $.020278, above $.02. All subjects failed the dual quality gate. Controls passed all latency and cost gates. Sol's recorded 2/3 hard-constraint result includes a documented scorer false failure. These are bounded, uncommitted, hash-frozen research scores; they do not replace current six-case evidence or prove semantic superiority.

## Source findings and score limits

An independent GPT-6 Luna high reviewer personally inspected all 15 original JPEGs, manifest hashes and nine saved answers. Argon recognizes dialogue body enlargement, the exact red0–1/blue2–4 transition with broken continuity, rightward runner motion and shifting diagonal lines in its evidence. Its dialogue push-in mechanism is unsupported/ambiguous, not a source-proven false fact: the prop and background do not scale. The motion summary understates changing streaks but the evidence recognizes them. No unequivocal Argon contradiction justified stopping the remaining approved cases.

Luna observes the prop color transition but calls continuity intact: **model-wrong** against the declared visual continuity contract. Tone, emotion, tempo, color interpretation and physical mechanisms remain **ambiguous**.

Preserved **golden/scorer-wrong** limitations include camera-alias summary credit despite excluded camera, inconsistent enlargement synonyms, prop plaque/rectangle wording, source-supported stillness/red tag penalties, storm icon/arch/line synonyms, and a false hard failure on Sol's visibly grounded third motion cue. They are non-runtime-blocking research limitations. Aggregate rankings cannot establish absolute source fidelity or superiority. A separate source-backed scoring-validity repair is required before later capability qualification; no C2/C3/C5 deletion signal follows.

Original prop reviews incorrectly call visible stillness invented, request extra frame1 evidence beyond the 2–4-entry contract, and contain color-enum confusion. One symmetric Opus source-image repair on unchanged saved answers changed Argon .78→.82; Sol .72 and Luna .55 stayed unchanged. Original judgments, instructions and charges remain retained. No further rejudging or tuning occurred. The repair waives none of the .70 deterministic, .80 rubric/overall, 15s or $.02 gates. The first repair envelope survived a local Decimal/float cost-parsing error; the fixed parser reused that raw response without another paid call. Its receipt1ms measures parsing; provider latency is unknown.

## Transport and economics

Native and maintained `call_api` parity passed for all three arms with identical per-arm request bodies. Google requested/served exact `gemini-4-argon`, medium thinking, 32768 output including thinking, all-fields-required schema, one STOP candidate and reconciled usage. Native input7534 comprised image5500 and text2034 tokens. OpenAI used direct foreground Responses low, default tier, strict schema and storefalse. Complete synthetic envelopes were saved before parsing; retained requests exclude headers and secrets. This qualifies only the five-JPEG contract, not native MP4/audio or throughput/variance.

Twenty-four calls settled at **estimated USD.278644895 / 5**, billed dollars unavailable; unknown exposure0 and subject retries0. Qualification: .030758675; scored subjects: .07523122; original judges: .109355; source review repairs: .063300. Candidate total: .0707505; controls total: .035239395. Before every POST, the ledger reserved conservative maximum charges; unknown calls remained reserved. Serial settlement released reservations. Argon reserved2.424832 using the full1048576 input window plus32768 output at USD2/10 per million; original Opus .0756; repair Opus1.0256 using the full200K context. One symmetric three-call repair round superseded the agent-selected two-call soft allowance; the hardUSD5 cap stayed unchanged.

Natural implicit caches are reported separately: Argon scored dialogue read5485/7534 cached input tokens; first Sol/Luna parity calls were warmed by native qualification. Subject outputs were fresh. Argon's cold-normalized mean subject cost is $.020348 at launch rates, versus observed warm mean $.01687417. December1 doubling yields $.040696 cold-normalized or $.03374833 at the observed cache shape. No adoption argument relies on launch discounts or warm input caching.

## Custody and validation

Worktree: `/Users/cam/.codex/worktrees/scout092-argon-cineforge-20261013`; branch `codex/scout092-argon-cineforge-20261013`; freshly fetched base `1a38bbae97382abdffe99b2abe959154b02dace6`. Primary eight dirty entries stayed untouched. Existing owner Google/OpenAI/Anthropic credentials came only through the normal wrapper; no injection, copying or cleanup. Existing owner Python was reused with `PYTHONPATH=src`, with no dependency copy. Only repo-authored synthetic images were submitted. No private uploads, other CineForge lanes, raw MP4/audio, default/account/deployment changes, commit or push.

Official sources checked2026-10-13: [model](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon), [migration](https://ai.google.dev/gemini-api/docs/generate-content/latest-model), [pricing](https://ai.google.dev/gemini-api/docs/pricing). Owner discovery listed Argon; native calls separately proved callability. Sampling, explicit caching and automatic continuations were omitted. Paid Google retention includes55-day abuse monitoring; no ZDR claim.

Durable [result](../../../benchmarks/results/video-understanding-argon-vs-sol-luna-v4-20261013.json), [source review](../story-226-argon20261013-source-review.json), [freeze](../story-226-argon20261013-argon-freeze.json) and [evidence manifest](../story-226-argon20261013-evidence.json). Complete safe requests/envelopes/ledger are under `docs/evals/evidence/story-226-argon20261013/`; producing runner/adapter snapshots and both repair-helper versions are under `docs/evals/snapshots/story-226-argon20261013/`. The manifest separates call-time bytes from later formatting. Registry Attempt050 records history without score promotion.

Offline verification: `PYTHONPATH=src <ownerpython> benchmarks/scripts/report_argon_video_comparison.py --verify`. It reconstructs nine maintained scores, validates retained hashes,24 settled ledger rows and native/parity bodies without inference. Paid reproduction requires a new authorized immutable identity; duplicate ledger names prohibit replaying paid calls. Focused tests and registry/manifest/methodology checks are recorded in Story226's work log.
