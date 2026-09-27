# Attempt 041 — GPT-6 Sol and Luna ordered-frame first-case stop

Date: 2026-09-26. Owner: Story 222, `video-understanding` v3. Approved by Conductor Scout 076 item 3 and Cam's `yes`. Isolated worktree `/Users/cam/.codex/worktrees/gpt6-sol-luna-eval-20260926/cine-forge`, branch `codex/gpt6-sol-luna-eval-20260926`, current `origin/main` base `163bcb1ecd36de97b76e5ad83298048c9211a4d7`. Primary checkout was read-only. Total accounted spend **USD0.035800575 / USD1.50**: direct Sol USD0.0092935, direct Luna USD0.000548675, Sol harness parity USD0.0027934, and Opus 4.6 rubric judge **USD0.023165 estimated** from 743 input and 778 output tokens at $5/$25 per million. The subject estimates reconcile OpenAI's input, cache-read, cache-write and output token telemetry; the judge receipt does not expose a separately billed dollar amount or served model ID.

## Contract and zero-cost preflight

Both exact direct OpenAI models appeared in the owner's authenticated catalog (HTTP 200, exact IDs). The owner credential wrapper reported OpenAI, Gemini and Anthropic variables present by name. The six active v3 cases matched task and registry; each packet resolved to five hash-checked ordered JPEGs, opaque IDs and neutral timing, with no audio, video, transcript or title. The preflight resolved six independent test rows, unchanged prompt SHA-256 `53ea0b8ef7487d8dcaea352c0eb133100e18eb45d78b953f2007f14148beb6e2`, scorer `77c81f2b4eb086fc3c3e1a5d244a9200688d780f53611bb206932d3a2c2c5d27`, manifest `8022c2dffb4a4c8c856f92bf735b465f580c4a2545129788ee4883a8f7f6af7a`, explicit `anthropic:messages:claude-opus-4-6` judge, no subject output cache, and concurrency one. Focused source/scorer checks passed 52/52; the new direct Responses adapter checks passed 2/2. The old broad runbook quarantine warning did not put fourteen inactive cases into this run.

Official Standard prices checked on 2026-09-26: [Sol](https://developers.openai.com/api/docs/models/gpt-6-sol) $2/$0.20/$2.50/$10 per million input/cache-read/cache-write/output; [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) $0.10/$0.01/$0.125/$0.50; [Opus 4.6](https://platform.claude.com/docs/en/models/opus-4-6/overview) $5/$25; [Gemini 3.5 Flash-Lite](https://ai.google.dev/gemini-api/docs/pricing) $0.30/$2.50. Before each subject request, full five-image input plus 1,400 output was reserved at 20,000 input tokens and the cache-write rate: Sol USD0.064, Luna USD0.0032. The judge reserve was USD0.0756 (10,000 input and 1,024 output). The fresh Gemini control would reserve USD0.16984 with its existing 65,536-output policy, but the quality stop never admitted it. Unused reservations were released on complete usage. No automatic retries, model substitution, new key, or account-setting change.

## Observed first case

Both direct native requests sent the same v3 prompt and all five ordered JPEGs for `vfp_active_001`, direct foreground Responses, `service_tier=default`, `store=false`, `reasoning.effort=low`, provider strict JSON Schema, 1,400 output cap and no hosted tools. Complete raw envelopes were saved in ignored owner `output/` before parsing. Both returned exact identity, terminal `completed`, one complete assistant `output_text`, provider schema-valid output and reconciled usage.

| Arm | Native latency | Input tokens | Output tokens | Direct subject cost | Native deterministic | Next stage |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `gpt-6-sol` | 6,827 ms | 2,890 (2,887 cache-write) | 207 | $0.0092935 | 0.4917 | owner parity + frozen rubric |
| `gpt-6-luna` | 4,081 ms | 2,890 (2,887 cache-write) | 375 (161 reasoning) | $0.000548675 | 0.5983 | stopped before duplicate subject call |

Sol's one owner Promptfoo parity call returned exact `gpt-6-sol`, Standard/default, the five expected frame hashes, complete usage and USD0.0027934 subject cost (2,887 cached-read input tokens and 221 output); it took 3,980 ms. The maintained Opus 4.6 rubric ran on this same first case. Deterministic score **0.4383**, rubric **0.35**, combined **0.39415**, zero of one passed. The candidate misses the first-case quality gate, so the six-case run and fresh Gemini reference did not proceed. Before this successful parity run, a zero-provider-call CLI attempt with an explicit `--grader` flag failed in Promptfoo's SQLite serialization of a circular Anthropic client; no subject raw or result was created. Removing that redundant flag used the task's explicit `defaultTest.options.provider` for the successful run. No paid retry occurred after a model response.

Luna's native deterministic first-case score was 0.5983 with hard constraints true. Under the maintained equal-weight structural/rubric aggregate, even rubric 1.0 yields 0.79915, below the 0.80 entry gate. A second subject or judge call could not make this native first-case response pass; Luna stopped without harness parity or rubric. This is a **maintained-scorer progressive stop**, not a full semantic or production-harness verdict.

Source review of `frame_00.jpg` and `frame_04.jpg` confirmed visibly larger abstract figures at nearly fixed centers. Sol's native response noticed enlargement and tagged `slow_push_in`, but its parity response said approximately unchanged scale and tagged `static`/`stillness`: the parity scale/motion miss is **model-wrong**, runtime-blocking for this first-case quality gate. Luna described enlargement but tagged camera `static`, a narrower grounded inconsistency. The authored target's `intimate` tone versus models' `detached` is interpretive on featureless shapes; the lexical summary scorer also missed descriptions of enlargement because they omit the target word `closer`. Those deductions are **ambiguous** and should not be presented as unqualified model errors. No golden or scorer was changed to rescue either arm. The maintained rubric's low Sol score partly reflects those target-bound interpretations, so broad capability remains unmeasured.

## Provenance and reproduction

[Manifest](../story-222-gpt6-sol-luna-video-evidence.json) records call-time code/fixture hashes, ignored raw paths/hashes/sizes, exact model parameters, usage, reservations, result path and ledger. `benchmarks/results/video-understanding-gpt6-sol-first-20260926.json` is the tracked one-case owner result. The native requests were made once per model through the owner wrapper using `video_understanding_transport.load_clip_packet` and `build_user_text` for `dialogue_confession_push_in`, then `video_understanding_provider_vision.call_openai_responses_strict` with `max_tokens=1400`, `reasoning_effort=low` and a separate `native-vfp_active_001-raw-envelope.json` path under each model's ignored `output/evals/gpt6-sol-luna-20260926/` directory. This describes regeneration, not permission to re-call.

The two native invocations were the following same command shape from the worktree root, once with `MODEL=gpt-6-sol` and once with `MODEL=gpt-6-luna`; the call-time shell used the corresponding literal model and `sol` or `luna` path in each invocation. This normalized reproduction command contains the same request fields and refuses duplicate raw output:

```bash
MODEL=gpt-6-sol /Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/with_cine_forge_provider_env.py /Users/cam/Documents/Projects/cine-forge/.venv/bin/python - <<'PY'
import os, sys
from pathlib import Path
sys.path[:0] = [str(Path('benchmarks/providers').resolve()), str(Path('benchmarks/scripts').resolve())]
import video_understanding_provider as provider
import video_understanding_transport as transport
model = os.environ['MODEL']
slug = model.removeprefix('gpt-6-')
packet = transport.load_clip_packet(
    Path('benchmarks/video_understanding/dialogue_confession_push_in'), max_frames=5
)
text = transport.build_user_text(
    Path('benchmarks/prompts/video-understanding.txt').read_text(), packet['meta'],
    evaluation_id='vfp_active_001', prompt_version='video-understanding-frame-packet-v3',
    frame_count=5, sample_times=packet['sample_times_seconds'],
)
raw = Path(f'output/evals/gpt6-sol-luna-20260926/{slug}/native-vfp_active_001-raw-envelope.json').resolve()
if raw.exists():
    raise SystemExit('Refusing duplicate native call')
provider._vision.call_openai_responses_strict(
    vars(provider), model=model, user_text=text, frames=packet['frames'],
    max_tokens=1400, reasoning_effort='low', raw_output_path=raw,
)
PY
```

Exact owner parity command from `benchmarks/` (completed once; do not rerun under this approval):

```bash
source ~/.nvm/nvm.sh && nvm use 24 >/dev/null 2>&1 && PROMPTFOO_PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python /Users/cam/Documents/Projects/cine-forge/.venv/bin/python ../scripts/with_cine_forge_provider_env.py promptfoo eval -c tasks/video-understanding.yaml --filter-providers 'GPT-6 Sol / direct Responses low' --filter-first-n 1 --no-cache -j 1 --output results/video-understanding-gpt6-sol-first-20260926.json --no-table
```

No control, full six, private corpus, audio, native video, ScriptBible, QA, default change, commit or push occurred. Sol access and native/owner transport are qualified; first-case reliability was 2/2 successful subject calls, but broader reliability was not measured. Sol capability is below the maintained first-case gate with the grounded scale miss and stated scorer caveats; adoption **do not advance at this gate**. Luna access and native transport are qualified, owner parity/reliability and rubric capability **not measured**; adoption **defer/inconclusive** after scorer-bound stop. The fresh comparative advantage question remains unanswered. Reopen only on a source-verified scorer/target correction or a separately approved changed evaluation plan; do not rerun unchanged calls automatically.
