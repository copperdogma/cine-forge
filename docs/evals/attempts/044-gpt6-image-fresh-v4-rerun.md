# Attempt 044 — fresh GPT-6 image v4 comparison

Date: 2026-09-27. Owner: Story 224, `video-understanding`. Fresh user-authorized USD1.50 cap, independent of yesterday's receipts. Isolated branch `codex/gpt6-image-rerun-20260927` at `origin/main` f4a0decd9b89a18756bfcf4a78b44fba5e71e58d. No commits/pushes/default changes or product inference integration.

**Luna remains the value choice for inspected headless reference analysis. Sol has a small raw aggregate lead and a useful observed size-change example, but its 17.4x subject cost and ambiguous rubric gap do not establish a replacement win. Both beat the fresh Gemini control; Luna wins all six paired cases at about 5x lower subject cost. Hold autonomous continuity/pass-fail QA.**

The [official September 25 image-encoding fix](https://developers.openai.com/api/docs/changelog) is verified. September 26's prior results already postdate it; these are fresh replications, not causal pre-/post-fix evidence.

The unchanged maintained six v4 synthetic cases each submit five JPEGs. Both OpenAI arms use `detail:high`, direct strict Responses, low reasoning, Standard tier, `store:false`, maximum output 1,400. Gemini retains 65,536 output cap and native schema. Opus 4.6 independently judges all 18 outputs, cap 1,024. All 36 requests completed with exact identity, terminal state and valid usage. No SDK/automatic retries, no cached subjects or further calls. Native outputs pass the maintained schema and exact owner entrypoint offline parity replay.

| Arm | Structural | Rubric | Combined | Mean subject latency | Mean subject cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| sol | 0.5994 | 0.6167 | 0.6080 | 7,221 ms | USD0.009523500 |
| luna | 0.6138 | 0.5667 | 0.5902 | 3,876 ms | USD0.000546342 |
| gemini | 0.3922 | 0.3800 | 0.3861 | 2,637 ms | USD0.002731483 |

| Case | Sol combined | Luna combined | Gemini combined |
| --- | ---: | ---: | ---: |
| dialogue_confession_push_in | 0.68010 | 0.58215 | 0.35620 |
| alarm_chase_whip_pan | 0.51250 | 0.57750 | 0.56250 |
| quiet_bedside_vigil | 0.77315 | 0.75915 | 0.29460 |
| prop_swap_continuity_break | 0.54415 | 0.53415 | 0.36835 |
| rooftop_escape_crash_zoom | 0.60915 | 0.54915 | 0.43250 |
| storm_tunnel_lateral_run | 0.52915 | 0.53915 | 0.30250 |

None of the 18 combined case scores reaches 0.80. Sol's bedside result passes the maintained structural >=0.70 and rubric >=0.80 assertions, but its combined 0.77315 still misses the registry's quality target. Aggregate means are also below 0.80; all subject calls meet the 15s/$0.02 limits.

Source inspection confirms Sol catches dialogue body growth but adds an unsupported camera mechanism; Luna misses that growth yet captures the rooftop arc. Gemini invents camera tracking and misses the body growth. All three explicitly see the red-to-blue rectangle but label continuity intact: a concrete model-wrong autonomous-QA blocker. [Source review](../gpt6-image-rerun-20260927-source-review.md) classifies every case; detached/intimate tone, permitted bedside object readings and measured/fast vocabulary are ambiguous, non-runtime-blocking for inspected analysis. The Opus bedside score difference despite similar tone deductions limits fine-grained ranking. No goldens/scorer/prompt were changed, no failures were tuned away. Sol's observed scale advantage is an example, not a validated automatic routing rule. No native video/audio/private inputs or ScriptBible were evaluated.

Total token-derived upper/estimated cost is **USD0.505742950**, subjects USD0.076807950 plus judges USD0.428935; unknown reservations USD0, remaining USD0.994257050. All requests were admitted under full maximum reservations (Sol .064, Luna .0032, Gemini .16984, judge .0756) before dispatch. Provider invoices are unavailable.

[Evidence manifest](../gpt6-image-rerun-20260927-evidence.json) pins the original freeze, exact archived call-time runner, active postrun runner, immutable full result, raw receipts and commands. Safe raw receipts remain in ignored `output/evals/gpt6-image-rerun-20260927/`; the tracked result retains every normalized subject and rubric judgment. Prior Attempts 041–043 and their receipts/results remain untouched. The original call-time run is hash-pinned dirty-contract evidence retained as registry attempt history; committing its closeout does not retroactively change that producing identity or promote current score evidence.

Executed from this worktree with owner Python `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`:

```bash
PYTHONPATH=src <python> benchmarks/scripts/build_video_understanding_truth_v4.py --check
<python> scripts/with_cine_forge_provider_env.py <python> scripts/discover-models.py --check-new
<python> benchmarks/scripts/gpt6_image_rerun_20260927.py preflight
<python> scripts/with_cine_forge_provider_env.py <python> benchmarks/scripts/gpt6_image_rerun_20260927.py subjects
<python> scripts/with_cine_forge_provider_env.py <python> benchmarks/scripts/gpt6_image_rerun_20260927.py judges
<python> benchmarks/scripts/gpt6_image_rerun_20260927.py report
```

The completed run identity cannot dispatch the same calls again or overwrite freeze/result. A separately authorized future fresh run needs a new identity.

Validation: focused transport/benchmark/adversarial scorer checks passed 44 tests with sockets disabled. V4 builder checked all 13 generated files and media hashes. Active runner passes Ruff; offline archive freeze verification, all 36 settled receipts and hard-cap rejection passed. Registry and generated methodology checks are recorded in Story 224. No broad product suites or live smoke runs were used. Initial nonexistent test filename and preformat lint warnings were local-only and corrected; call-time code is archived before cleanup. No subject/judge fault required recovery.

Retry state: exhausted-until-new-trigger. No further same-slice calls are recommended. A new source-backed corpus or separately scoped product integration with owner acceptance would be the next distinct task.

Commit preparation: [Retention manifest v2](../gpt6-image-rerun-20260927-evidence-v2.json) preserves all 36 exact native terminal receipts and the settled ledger in tracked synthetic evidence. Original v1 manifest, call-time freeze, archived script, result and ignored receipts remain unchanged. The active runner now rejects subjects/judges when the immutable result exists, including in a fresh clone without ignored ledger state. This guard was checked offline with provider access disabled; no calls were added. Owner inbox was reviewed with no primary-checkout capture diff to reconcile. Origin/main stayed at f4a0dec, so no integration changed frozen validation inputs.
