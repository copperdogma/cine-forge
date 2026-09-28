# Attempt 045 — Sonnet 5.5 versus fresh Luna, v4 ordered-frame comparison

Date: 2026-09-28. Owner: [Story225](../../stories/story-225-sonnet55-ordered-frame-evaluation.md), `video-understanding`. The approved all-provider USD3 cap covers every qualification, subject and judge call. The isolated worktree is `/Users/cam/.codex/worktrees/sonnet55-eval-20260928/cine-forge`, branch `codex/sonnet55-eval-20260928`, from current remote base `a3ac35743c94e253e0406fafe6ee4964a0330bf3`. No primary-checkout modification, commit, push, runtime default, deployment or provider account change occurred.

**Retain GPT-6 Luna as the preferred headless frame-reference model. Do not adopt Sonnet5.5 for this task or promote either model to autonomous QA.** Sonnet was faster, but its larger cost did not buy higher measured quality or better contract reliability. This task has no product ordered-frame inference call: it is the maintained headless benchmark Python adapter, not an integrated video analyzer.

| Fresh arm | Revised deterministic | Revised Opus rubric | Revised combined | Independent Sol combined | >=0.80 case passes | Mean subject latency | Mean subject cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| exact `claude-sonnet-5-5`, adaptive medium, native strict schema | 0.46303 | 0.61167 | **0.53735** | 0.61402 | 0/6 | 4,390ms | USD0.013724 |
| exact `gpt-6-luna`, Responses Standard low, native strict schema | 0.61358 | 0.63000 | **0.62179** | 0.69263 | 1/6 | 8,119ms | USD0.000488341 |

Sonnet's slowest subject was4,711ms and highest costUSD0.014224; Luna's slowest was10,570ms and highest costUSD0.000585175. Both meet the per-call15s/USD0.02 value limits. Sonnet is about1.85x faster, Luna about28.1x cheaper at observed cache billing. The native Luna qualification warmed the identical first-case prompt: first cohort had2,887 cache-read tokens, otherfive had2,887 cache-write tokens each. Every subject output is fresh, with no harness output cache, unique provider response IDs and distinct native/parity content. Charging first-case Luna input at uncached cache-write rates gives meanUSD0.000543675, still about25.2x cheaper. Provider prompt-cache reuse is disclosed; it is not a saved output reuse. Qualifier calls are included in campaign spend, outside subject averages.

## Qualification and frozen topology

Only the current six project-owned synthetic v4 cases were used; each supplies five original640x360 JPEGs, neutral timing and an opaque evaluation ID. No ScriptBible, private screenplay, audio, transcript, native video, semantic case title or target reached subjects. Standard API retention/no-training defaults apply; ZDR is unverified. `store:false` does not establish ZDR. Official verified current provider notes are [retained locally](../story-225-sonnet55-provider-notes.md); worker web/urllib fetching returned403, while live owner catalog discovery listed exact Sonnet5.5, Luna, Sol and pinned Opus4.6.

Two native direct-dispatch probes and twelve cohort calls were run through owner-configured credentials and the normal env launcher. For each arm, native and maintained `call_api` parity requests were byte-identical, with five image blocks, native schema, complete response, exact served identity and returned usage. The parity response is cohort case001. Sonnet uses adaptive medium and4096 output tokens; Luna retains low/1400. No sampling, subject tuning, fallback or additional configuration arm occurred. Case conversations are independent, concurrencyone. The [call-time freeze](../story-225-sonnet55-freeze.json) pins63 source/config/media files before inference. The owner comparison uses the maintained adapter directly, rather than executing Promptfoo's JavaScript runner; assertions use the maintained Python scorer and the frozen task's rendered rubric, with explicit paid judge selection. This is headless adapter evidence, not proof of Promptfoo UI behavior.

## Source verification and evaluator recovery

The [original result](../../../benchmarks/results/video-understanding-sonnet55-vs-luna-v4-original-20260928.json) preserves unmodified v4 scores: Sonnet0.47725/Luna0.58390 combined; deterministic0.39783/0.55947. The [derived final result](../../../benchmarks/results/video-understanding-sonnet55-vs-luna-v4-20260928.json) applies narrow source-backed scorer fixes identically to both saved arms. Subjects and v4 targets are unchanged.

- **Golden-wrong (scorer)**: affirmative temporal “grow taller” was not credited as observable enlargement; “unchanging composition” and “Nothing visibly moves or changes” were missed as static equivalents. General temporal/static aliases now recognize these statements, with the existing negation and relative-size adversarial checks retained.
- **Golden-wrong (scorer)**: visible abstract figure/arch evidence was hard-failed because the reference said runner/tunnel. The cue lexicon now permits coarser visible figure and arch descriptors when those target concepts exist. This changes evidence grounding only; summary/action/tag requirements remain unchanged. Pixel inspection confirms the actual curved arch, figure and slanted lines. An invented police/helicopter/explosion cue remains rejected.
- **Golden-wrong (judge)**: original text-only Opus called the red scene's visible rectangle/triangle invented, treated bedside head/color wording as unsupported, and asked for a blue color tag that is absent from the allowed vocabulary. A source-backed clarification was frozen, then the same Opus rejudged both arms on cases002/003/004 (six calls), retaining all original judgments. Its new scores are used only for those six reviews. Independent predeclared GPT-6 Sol reviewed all twelve original subject outputs against the actual five JPEGs and frozen reference. Neither judge received subject model names.
- **Ambiguous**: exact subjective tone, speed-tag and lexical continuity-note requirements still penalize reasonable alternate phrasing. One revised Opus Luna prop review again mentioned the unavailable blue tag despite the clarification; preserve this residual evaluator defect rather than tuning for a passing score. Independent Sol does not make that deduction. The absolute aggregates remain bounded benchmark measurements, not clean universal visual-comprehension scores.

[The retained source contact sheet](../evidence/story-225/source-contact-sheet.png) shows all30 original JPEGs. Individual source images remain repository-resolvable under `benchmarks/video_understanding/{case}/frames/`; the frozen hashes pin their bytes. The earlier Story222 freeze/results remain unchanged. Exact predecessor task/scorer bytes were separately archived so its paid runner continues to reject evolved active contracts while historical frozen inputs remain verifiable. Call-time and post-run runner/scorer identities are separate in [the archive map](../story-225-calltime-archives.json) and the final evidence manifest.

## Subject mismatch classification

- **Model-wrong, task-blocking**: both arms explicitly observe the red-to-blue rectangle change while declaring `continuity_status:"intact"`; the maintained source-backed task requires `broken`. The observation is correct; the classification is wrong.
- **Model-wrong, contract-blocking**: Sonnet rooftop emits duplicate `tone_tags:["tense","tense"]`. JSON-schema shape validation succeeds, but the maintained exact-key/unique-tag contract rejects it. It remains an invalid strict output with deterministic assertion0; no normalization or subject repeat was used. Sonnet strict contract5/6, Luna6/6.
- **Model-wrong, task-blocking**: Sonnet tunnel claims `lateral_track` although its own notes and source pixels show fixed arch/background and a moving figure. Luna returns `static`. Their camera-mechanism claims are evaluated separately from the v4 dialogue camera exclusion.
- **Model-wrong / ambiguous**: Luna alarm says diagonal lines remain fixed despite shifting line positions; both miss the reference's illumination/motion labels. Independent source reviews also flag rooftop final-position/landing wording. Exact “urgent/intimate/measured/fast” labels and some prop-note overlap remain interpretive/lexical; they are not all factual hallucinations.

The corrected deterministic gate passes all six Luna outputs and five Sonnet outputs; Sonnet duplicate tags still fail. Passing hard shape/grounding is insufficient: quality aggregates remain below0.80. Only Luna's static bedside case passes the combined0.80 gate; no broad QA capability or C2/C3/C5 movement is inferred.

## Cost, custody and reproduction

All44 paid requests settled:14 subject/native,24 initial judge,6 source-clarified judge recovery. Total estimated ledger cost **USD0.38597572 / 3.00**, remainingUSD2.61402428, unresolved exposureUSD0. Provider billed dollars are unavailable. Full original conservative reservations wereUSD2.672, with an initialUSD0.328 recovery allowance; released settled reservations funded the six judge recovery calls. No cap transfer or increase occurred.

Complete safe synthetic requests, raw receipts, exact outputs and parsed reviews are retained under ignored `output/evals/sonnet55-20260928/` and byte-for-byte repository-resolvable copies in `docs/evals/evidence/story-225/`. No authorization headers or credentials are retained. The [evidence manifest](../story-225-sonnet55-evidence.json) pins all files, ledger, sources, commands and executed-code identities. This worktree remains uncommitted: records are bounded comparison history, not commit-identified promotion-grade current evidence.

Commands from the isolated root use `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`:

```bash
python scripts/with_cine_forge_provider_env.py python scripts/discover-models.py --check-new
python scripts/with_cine_forge_provider_env.py python benchmarks/scripts/run_sonnet55_video_comparison.py preflight
python scripts/with_cine_forge_provider_env.py python benchmarks/scripts/run_sonnet55_video_comparison.py qualify
python scripts/with_cine_forge_provider_env.py python benchmarks/scripts/run_sonnet55_video_comparison.py subjects
python scripts/with_cine_forge_provider_env.py python benchmarks/scripts/run_sonnet55_video_comparison.py judges
python scripts/with_cine_forge_provider_env.py python benchmarks/scripts/review_sonnet55_source_audit.py
python benchmarks/scripts/report_sonnet55_video_comparison.py
```

The paid runners refuse duplicate ledger names; they do not silently rerun calls. Original-score reproduction requires the archived call-time scorer/dimensions, not the corrected active scorer. Final report reproduction is offline and reuses all saved outputs/judgments.

Validation:83/83 focused schema, native transport, dataset, scorer/adversarial, report and predecessor archive checks passed. Full unit/registry/methodology validation and final provenance checks are recorded in Story225. No further unchanged subject run is recommended; a useful future evaluation requires a new checkpoint or materially broader source-backed scene set.
