# Attempt 051 — Nemotron 3.5 Super VL ordered-frame screen

Date: 2026-10-16. Owner Story226, approved Scout096 item4; inclusive USD3 hard cap.
Worker: Codex GPT6.1 owner; root independently inspected dialogue source frames.

**Reject the tested router-enabled Nemotron configuration for this task; retain Sol as the quality research reference and Luna as its economical control.** Nemotron reports an unchanged scene while the figures visibly enlarge. Cheap, quick, schema-valid output did not preserve the source change. No product analyzer/default exists and no autonomous-QA qualification follows.

| Fresh matched dialogue subject | Deterministic | Full-source Opus rubric | Combined | Latency | Subject USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nemotron router-enabled/32768 | .1719 | .38 | .27595 | 5.642s | .00125455 reported |
| GPT6.1 Sol low/4096 | .7364 | .72 | .7282 | 8.773s | .0031447 estimate |
| GPT6 Luna low/1400 | .7500 | .50 | .6250 | 5.999s | .00022267 estimate |

All three fail the .80 overall/rubric gate. Nemotron is 60.1% cheaper and35.7% faster than Sol on this one case, but fails source fidelity; it costs5.63x Luna. N=1 cannot estimate latency distributions or broad capability. Candidate prop/motion cases were stopped, not failed. Fresh controls completed all three independent v4 cases: source-adjudicated combined Sol.596067 and Luna.566933, both0/3 passes; means9.348s/.00753723 and5.603s/.00043767. Those n3 control averages are not a matched ranking against the n1 candidate. Original pre-repair control aggregates.612733/.5636 are preserved separately.

## Decision contract and sources

Frozen maintained `video-understanding` v4 dialogue/prop/storm, five original640x360 JPEGs each, opaque IDs, neutral timing, full13-key strict schema, unchanged prompt/scorer/targets. Deterministic >=.70, rubric/overall >=.80, <=15s and <=USD.02 per subject. Subject caches bypassed; direct foreground OpenAI Responses and pinned Together router, serial concurrency. Independent fixed native Opus4.6 strict1024 sees all five original source frames for every subject, same rubric/boundaries, blind to arm names. No other levels, tuning or six-case expansion. All fixtures are repo-authored synthetic; no private uploads, rawMP4/audio, defaults, account changes, commits/pushes.

Exact candidate request `nvidia/nemotron-3.5-super-vl`, public canonical checkpoint `nvidia/nemotron-3.5-super-vl-20261015`, paid Together, no fallback, max_price .15/.50M. Native and maintained `call_api` parity first-case bodies match exactly for all three arms; all terminal identities, strict schema, complete five-image content and usage reconcile. Routerenabled uses `reasoning.enabled:true` and32768 combined budget; native1351 and scored1561 reasoning tokens observed. It does **not** prove native regular-versus-medium equivalence. Off/medium and other levels remain unmeasured; no effort sweep was selected.

Official sources checked2026-10-16: [router endpoints](https://openrouter.ai/api/v1/models/nvidia/nemotron-3.5-super-vl/endpoints), [router reasoning controls](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens), [provider card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-BF16), [Together catalog](https://docs.together.ai/docs/serverless/models). Authenticated parameter listing and owner catalog discovery retained. Router Together quantization remains unknown; Together's public catalog calls its native route NVFP4, not evidence of router precision. Retention/training/ZDR remains unverified as disclosed; only eligible synthetic payloads submitted.

## Source taxonomy and repair

**Model-wrong:** Nemotron native and scored dialogue summaries/evidence explicitly claim unchanged/identical figures through frame4. Original frame0 and4 show larger heads/bodies while prop/background remain fixed; owner, root and independent full-source Opus agree. This valid decisive contradiction stops the candidate. It is distinct from the ambiguous physical camera mechanism. Both fresh controls observe growth; Luna's slow_push_in mechanism is unsupported/ambiguous. Both controls observe prop's red0–1/blue2–4 change yet label continuity intact: model-wrong under the declared visual continuity contract. Storm controls track rightward motion but omit changes in background streaks: source-completeness limits, not proof of invented motion.

**Golden/scorer-wrong or ambiguous, non-runtime-blocking:** preserved lexical false misses, mandatory subjective tone/emotion/tempo, camera aliases, prop plaque/rectangle terminology and stillness/red-tag penalties. Do not use raw ranking as source-validated absolute quality or promote current score rows. Nemotron's hard-gate failure also includes omitted pale rectangle; the physically verified growth miss supplies the decision independently.

Original Luna prop review invents a required frame1 entry despite the2–4 evidence contract, infers gradual interpolation from 'changes red to blue', and penalizes visible stillness. One predeclared symmetric saved-answer repair on both controls retains the real continuity error and removes these review-contract faults. Original Sol/Luna prop rubrics.62/.50; repaired both.52. All originals, corrections, complete image packets and costs retained. No subject rerun, scorer/golden weakening or judge shopping. Subjective tone/tempo differences elsewhere remain caveated; candidate first-case verdict is unaffected.

## Economics and custody

19 settled calls, total **USD.219046495 / 3**, unknown exposure0. Qualification.011732225; scored subjects.02517927; original judges.140410; two prop review repairs.041725. Candidate total.00241710 including nativequalification; separate subject comparison above excludes judge/probe overhead. Router charges are reported usage.cost; OpenAI/Anthropic are token-price estimates, not billed-dollar claims. OpenAI implicit input caching is retained in complete receipts. Every POST reserved a conservative ceiling before spend; unknown requests remain reserved. Router POST holds campaign flock through settlement. No subject operational retries.

Worktree `/Users/cam/.codex/worktrees/scout096-cine-20261016`, branch `codex/scout096-cine-20261016`, freshly fetched base `3a029014d252fabfa41d21008cefa471080706be`. Primary dirty entries unchanged. All credentials were preexisting through the normal owner wrapper, no injection/copy/cleanup. Executed input freeze and call-time runner snapshot retained; final runner adds a fail-closed stopped-arm guard plus formatting. Original freeze metadata accidentally retained2026-10-13/shortSHA from runner template; this attempt, receipts, manifest and final result correct execution date/base. Input byte inventory remains valid and is not rewritten.

[Final immutable result](../../../benchmarks/results/video-understanding-nemotron-vs-sol-luna-v4-20261016-v2.json), [original pre-repair result](../../../benchmarks/results/video-understanding-nemotron-vs-sol-luna-v4-20261016.json), [freeze](../story-226-nemotron20261016-nemotron-freeze.json), [evidence manifest](../story-226-nemotron20261016-evidence.json). Complete safe requests/envelopes/ledger live under `docs/evals/evidence/story-226-nemotron20261016/`; producing and final tooling identities are retained. Offline reproduction:

```bash
PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python benchmarks/scripts/report_nemotron_video_comparison.py --verify
```

Paid reproduction requires a new authorized immutable identity; current receipts/ledger refuse duplicates. Final runner skips stopped candidate cases and rejects direct later-case calls. Reuse source/adapter64 focused passing checks; final offline replay reconstructs all7 scores,19calls, native/parity body equality and retained hashes without provider access. Ruff and registry/methodology validation recorded in Story226. No UI or product suite needed for isolated evidence tooling.

Layered verdict: access available; transport qualified for five-JPEG strict schema; router-enabled reasoning observed/native finer-level mapping unverified; reliability acceptable on two candidate calls but variance unmeasured; capability worse on the single physical-growth obligation; economics cheaper thanSol but costlier thanLuna on that case; adoption do not adopt tested configuration for this ordered-frame lane. No conclusion about untested candidate cases or levels. Retry only a new checkpoint or materially changed source/contract; do not rerun this unchanged configuration to seek a favorable answer. Source-backed scoring-validity repair is the best prerequisite for broader qualification.
