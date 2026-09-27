# Attempt 043 — source-truth v4 headless ordered-frame qualification

Date: 2026-09-26. Owner: Story 222, `video-understanding`. The work remains in isolated `codex/gpt6-sol-luna-eval-20260926` from `origin/main` `163bcb1ecd36de97b76e5ad83298048c9211a4d7`; the primary CineForge checkout was not edited. Cam approved the source-backed benchmark repair and actual ordered-frame integration qualification under the existing USD1.50 all-provider cap. [Attempt 041](041-gpt6-sol-luna-video-understanding-first-case-stop.md) and [Attempt 042](042-gpt6-luna-repaired-six-case-comparison.md) remain historical, with their original outputs and scores preserved. This attempt made **no new subject calls**.

## Runtime boundary and source truth

The actual maintained ordered-frame path is the headless Promptfoo task `benchmarks/tasks/video-understanding.yaml`. `src/` and `configs/` contain `VideoAnalysis` schema and registry references but no product inference call that consumes five ordered frames. Story 030 explicitly replaced the proposed QA module with the Promptfoo-only harness. There is therefore no production provider to swap and no autonomous video QA behavior to claim.

The [v4 truth overlay](../../../benchmarks/video_understanding_truth_v4/README.md) is the maintained task target source. It preserves every v3 JPEG, neutral metadata item, opaque evaluation ID, subject prompt, and both six-case subject outputs. Three references are byte-identical to v3. The source-reviewed corrections are:

- Rooftop: the yellow figure's pixel bounding box is 123 × 125 at frames 00 and 04 (8,552 versus 8,554 yellow pixels); horizontal movement is constant speed. The v3 growth and escalation requirements were false, so v4 removes them.
- Bedside: one circle-on-post and one circle-on-rounded-body flank a horizontal block. A lamp/bed reading is plausible, but a single hidden object identity is not compelled by these abstract pixels. V4 scores visible geometry and static temporal behavior.
- Dialogue: two bodies visibly enlarge at fixed centers, but the prop and background do not scale. A specific camera push-in is not physically established. V4 describes body enlargement and excludes the camera dimension from the deterministic aggregate for this case only. Schema, unsupported tags and all hard constraints remain enforced.

The scorer also recognizes affirmative temporal growth, including “figures grow slightly,” and static/no-motion equivalents. Negation and static relative-size adversarial tests prevent those aliases from crediting contrary statements. The [call-time freeze](../story-222-truth-v4-freeze.json) pins all targets, scorer/schema, task, builder, saved result bytes, and judge script **before** paid judging. The generated v4 overlay manifest pins source-frame and target hashes. The original v3 generator remains the historical pixel/target producer; the v4 overlay builder is the current reference producer and checks the unchanged pixels.

## Symmetric saved-subject comparison

The [derived result](../../../benchmarks/results/video-understanding-truth-v4-saved-subject-regrade-20260926.json) reapplies the same v4 deterministic scorer to the twelve saved full-six outputs. Opus 4.6 rejudged both arms for only the three changed references, six calls total, with exact `claude-opus-4-6` identity, `end_turn`, Standard tier, unique IDs, returned usage, and zero cache reads/writes. The three unchanged references retain their original Opus 4.6 judgments; all original subject and judgment artifacts remain untouched. These are derived scores, not a fresh v4 subject run.

| Saved arm | Structural mean | Rubric mean | Combined mean | Case passes at 0.80 | Mean subject latency | Mean subject cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-6 Luna, direct Responses low | 0.6239 | 0.5733 | **0.5986** | 0/6 | 3,675 ms | USD0.000481 |
| Gemini 3.5 Flash-Lite, fresh matched control | 0.4709 | 0.3917 | **0.4313** | 0/6 | 2,470 ms | USD0.002731 |

Luna leads by 0.1673 in aggregate and wins all six paired combined case scores. It is about 5.7 times cheaper per subject; Gemini is about 1.5 times faster. Both remain below the unchanged 0.80 quality gate in every case. Luna's visible prop change is described as red-to-blue while `continuity_status` remains `intact`: a concrete task-contract miss. Gemini misses visible dialogue body growth and calls static-background lateral scenes camera tracking. Sol's retained first-case owner result misses dialogue body enlargement and remains stopped; no Sol six-case inference was made.

The revised Opus rubric is **not fully truth-clean**. It penalizes Gemini's bedside bed/headboard wording even though the reference permits that reading, and penalizes Luna's “block-shaped” description despite the rounded body below the circular top. Dialogue ground-line mention is visible but was treated as possible invention. `intimate`/`detached` tone is interpretive in abstract frames. These deductions weaken absolute score and fine-grained failure labels; they do not erase the repeated relative Luna lead or the real prop-continuity error. Do not tune or repeat this same slice merely to chase 0.80.

## Decision, cost and reproduction

**Select Luna as the preferred model for inspected headless five-JPEG ordered-frame reference analysis. Hold autonomous pass/fail QA and any runtime/default promotion.** This is a concrete current task preference, not a production integration. A future product call would be new feature work with its own validation; it is not part of this attempt. The six abstract cases do not establish broad video comprehension or audio/native-video capability.

The exact cumulative campaign ledger is USD**0.531629095 / 1.50**, leaving USD0.968370905. Prior attempts accounted USD0.390639095; six new judge-only calls add USD0.140990 **estimated** at Opus 4.6 Standard USD5/M input and USD25/M output, with returned cache buckets zero. Provider billed dollars are unavailable. Full maximum reservations were USD0.0756 per judge, USD0.4536 for all six, and fit the remaining cap. One initial execution attempt failed locally on a missing SDK import before any provider call; the frozen urllib runner then completed once for each case/arm. The [evidence manifest](../story-222-truth-v4-evidence.json) pins all six raw receipts, exact costs, identities, source and derived result hashes, and the freeze. Raw receipts live under ignored `output/evals/gpt6-sol-luna-20260926/truth-v4-judge/`. Attempt 042's overwritten initial Luna parity envelope caveat remains; its saved metadata and the full-six raw are preserved. This uncommitted worktree is hash-pinned but lacks a commit identity.

From the isolated repository root, the executed commands were:

```bash
PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python benchmarks/scripts/build_video_understanding_truth_v4.py --check
/Users/cam/Documents/Projects/cine-forge/.venv/bin/python benchmarks/scripts/rejudge_video_understanding_truth_v4.py --preflight
/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/with_cine_forge_provider_env.py /Users/cam/Documents/Projects/cine-forge/.venv/bin/python benchmarks/scripts/rejudge_video_understanding_truth_v4.py --run
PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python benchmarks/scripts/regrade_video_understanding_truth_v4.py
```

For a **new paid** inspected headless Luna run after separately deciding to rerun, use the current task from `benchmarks/` with Node 24 and the configured owner wrapper:

```bash
PROMPTFOO_PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python /Users/cam/Documents/Projects/cine-forge/.venv/bin/python ../scripts/with_cine_forge_provider_env.py promptfoo eval -c tasks/video-understanding.yaml --filter-providers 'GPT-6 Luna / direct Responses low' --no-cache -j 1 --output results/video-understanding-luna-v4-new-run.json --no-table
```

No private data, audio, native video, ScriptBible, QA subsystem, provider account change, runtime default, commit, push or deployment was involved.

Post-run code cleanup archived the two paid-call script versions byte-for-byte at `docs/evals/snapshots/story-222-v4-calltime-*.py.txt` before formatting their active copies. The [post-run provenance manifest](../story-222-truth-v4-postrun-provenance.json) maps the original freeze paths to those exact archived hashes and pins the cleaned active hashes separately. The active judge's freeze check verifies the archived versions for those two paths and the unchanged live versions for the other 21 files. The original freeze, evidence manifest, saved outputs, judge receipts and derived result are unchanged. The active scripts made no additional provider calls. This separates call-time identity from subsequent lint cleanup without suggesting the cleaned scripts produced the paid receipts.

Validation: the focused dataset, benchmark, scorer, report, transport, archive and contract-manifest suite passed **73/73**. The overlay builder `--check` verified 13 generated files and source-media hashes; archive-aware verification rechecked all 23 call-time frozen files. Offline regrade with the cleaned active scripts regenerated a byte-identical derived result (SHA-256 `ff2a5ae0da2444b0ea76ad3faa6eb115f8511eee95cc102dba44d4536428217f`). `make check-evals` passed registry, truth ledger and current v15 contract checks; `pnpm methodology:compile` regenerated methodology views; `git diff --check` passed. Ruff passed on all changed Python, including both cleaned active scripts. These local validation results do not turn an uncommitted worktree into a landed production integration.
