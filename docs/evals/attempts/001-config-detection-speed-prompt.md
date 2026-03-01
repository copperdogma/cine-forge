# Eval Attempt 001 — Config Detection: Speed via Prompt Improvement

**Status:** Succeeded
**Eval:** config-detection
**Date:** 2026-03-01
**Worker Model:** Opus 4.6
**Subject Model(s):** All 15 providers; winner = Gemini 3 Flash

## Mission

Improve config-detection from best 0.886 (Haiku 4.5 @ 10.1s) to target 0.920 at <15s latency.
This eval has an inverted quality-cost curve: cheap/fast models outperform SOTA because SOTA
models overthink format detection. Improvement vectors: prompt engineering for tone/genre
dimensions + testing untested fast models.

## Prior Attempts

First attempt on this eval.

## Plan

1. Improve the prompt — add tone vocabulary guidance and genre comprehensiveness instruction
2. Fix format detection — add guidance about Fountain formatting conventions vs page count
3. Add untested cheap models (GPT-5 Mini, GPT-5 Nano) to the eval config
4. Run full 15-provider eval, then verify top candidate

## Work Log

- **Step 0: Baseline analysis.** Analyzed per-dimension breakdowns from existing result files (13 models).
  Found format_accuracy (0.10 weight) and duration_accuracy (0.10 weight) are the binary cliff
  separating good models (1.00) from bad (0.30). SOTA models all fail format (call it "short film"
  instead of "feature film") while cheap models get it right. For already-good cheap models, the
  remaining gap is tone (0.40) and genre (0.75).

- **Step 1: Prompt improvement.** Edited `benchmarks/prompts/config-detection.txt`:
  - Format: added "Use one of: feature film, short film, pilot, limited series. Determine format
    from screenplay conventions rather than raw page count alone."
  - Genre: expanded to list 16 common genres and emphasized "include every genre with clear evidence"
  - Tone: expanded to list 6 dimensions (mood, intensity, visual style, violence level, atmosphere,
    pacing) with example keywords for each

- **Step 2: Added models.** Added GPT-5 Mini and GPT-5 Nano to `benchmarks/tasks/config-detection.yaml`.

- **Step 3: Full eval run** (15 providers, 1 test case each). Results file:
  `benchmarks/results/config-detection-2026-03-01.json`

  Initial top results (sorted by overall quality):
  | Model | Python | LLM | Overall | Latency | Cost |
  |-------|--------|-----|---------|---------|------|
  | GPT-4.1 | 0.980 | 0.950 | **0.965** | 12,407ms | $0.017 |
  | GPT-5 Mini | 0.960 | 0.950 | **0.955** | 26,102ms | $0.006 |
  | GPT-5 Nano | 0.960 | 0.850 | 0.905 | 42,495ms | $0.002 |

  **Format accuracy: 1.00 for ALL 15 models.** The format detection fix worked universally.
  Genre and tone also improved significantly across the board.

- **Step 4: CRITICAL — Manual golden audit.** Read the full 436-line Mariner screenplay
  (FADE IN to CUT TO BLACK) and cross-checked every golden field against the actual text.
  **Found the golden reference was wrong on 4 fields:**

  1. **Format**: Golden accepted "feature film" — **wrong**. The Mariner is a complete short
     film (FADE IN → CUT TO BLACK, ~10-15 pages, full narrative arc). Models saying "feature
     film" (GPT-4.1, GPT-5.2, etc.) were rewarded for incorrect answers.
  2. **Duration**: Range [8, 130] was absurdly wide. Models estimating 100+ min for a 10-15
     page screenplay were scored 1.00. Corrected to [8, 35].
  3. **Supporting characters**: Listed CONSIGLIERE and GIRL — neither exists in the screenplay.
     Missing MIKEY, CARLOS, ROSCO (all have dialogue). Corrected the list and raised min_count.
  4. **Tone**: Keyword list too narrow (5 words, min 1). Expanded to 10 keywords and raised
     must_include_at_least to 3 since all models should identify multiple tonal qualities.

  **Impact: The initial "winner" GPT-4.1 was winning on incorrect answers.** It said "feature
  film" (wrong) and "100 min" (wrong) — both scored 1.00 under the old golden. The pre-fix
  scores are ALL invalid.

- **Step 5: Scorer improvement.** Updated `benchmarks/scorers/config_detection_scorer.py`:
  - Added `audience_accuracy` dimension (previously unscored despite being in the golden)
  - Rebalanced all 10 dimensions to sum to 1.00

- **Step 6: LLM rubric fix.** Discovered the LLM rubric in `config-detection.yaml` had the
  same errors as the golden — it said "Did it identify this as a feature film?" and "85-130
  minutes." This meant models correctly saying "short film" were penalized by the LLM judge.
  Fixed the rubric to specify short film, 10-25 min duration, and corrected character lists.

- **Step 7: Full eval run with ALL corrections** (golden + scorer + rubric). Results file:
  `benchmarks/results/config-detection-golden-fix2.json`

  Corrected results (sorted by overall quality):
  | Model | Python | LLM | Overall | Latency | Cost |
  |-------|--------|-----|---------|---------|------|
  | Claude Sonnet 4.5 | 0.962 | 0.950 | **0.956** | 26,860ms | $0.034 |
  | Gemini 3 Flash | 0.906 | 1.000 | **0.953** | 12,970ms | $0.009 |
  | Gemini 3 Pro | 0.889 | 1.000 | **0.945** | 34,706ms | $0.040 |
  | Claude Opus 4.6 | 0.909 | 0.950 | **0.930** | 30,928ms | $0.062 |
  | Gemini 2.5 Flash | 0.895 | 0.820 | 0.857 | 15,867ms | $0.011 |
  | GPT-4.1 Mini | 0.900 | 0.550 | 0.725 | 14,692ms | $0.003 |
  | GPT-4.1 | 0.820 | 0.450 | **0.635** | 10,317ms | $0.018 |

  **Rankings completely reshuffled.** GPT-4.1 dropped from 0.965 to 0.635 (format+duration
  now correctly penalized). Models that correctly identify "short film" dominate.

  **Format detection split:**
  - Correct ("short film"): Sonnet 4.5, Opus 4.6, Gemini 3 Flash/Pro, Gemini 2.5 Flash
  - Incorrect ("feature film"): All OpenAI models, Sonnet 4.6, Haiku 4.5, Gemini 2.5 Pro

- **Step 8: Verification — Gemini 3 Flash.**
  - Run 1: Python=0.906, LLM=1.000, Overall=0.953 (12,970ms)
  - Run 2: Python=0.906, LLM=0.950, Overall=0.928 (13,128ms)
  - Run 3: Python=0.906, LLM=1.000, Overall=0.953 (13,291ms)
  - **3-run average: Python=0.906, LLM=0.983, Overall=0.945.** Exceeds 0.920 target.
  - Python score perfectly stable across all 3 runs (identical dimension breakdowns).

## Conclusion

**Result:** succeeded
**Score before:** 0.886 (Haiku 4.5, but measured against incorrect golden)
**Score after:** 0.953 (Gemini 3 Flash, single run) / 0.945 (3-run average, corrected golden)
**Latency before:** 10,142ms (Haiku 4.5)
**Latency after:** 12,970ms (Gemini 3 Flash)
**Cost before:** $0.0103 (Haiku 4.5)
**Cost after:** $0.0089 (Gemini 3 Flash)

**What worked:**
- **Golden audit was critical.** The initial "success" (GPT-4.1 at 0.965) was entirely invalid —
  the model was rewarded for saying "feature film" and "100 minutes" when the screenplay is
  clearly a complete short film at ~10-15 pages. Without the manual audit, we would have shipped
  a fundamentally wrong model recommendation.
- **Prompt engineering for tone and genre** lifted both dimensions across all models. Tone went
  from 0.40-0.60 to 0.50-0.90; genre went from 0.50-0.75 to 0.75-1.00.
- **LLM rubric alignment** was essential. Fixing the rubric to match the corrected golden
  ensured the LLM judge rewards correct answers (short film) instead of penalizing them.
- **Gemini 3 Flash** emerged as the clear speed champion — meets quality target (0.953), latency
  target (13.0s < 15s), and costs only $0.009/call. It's the only model meeting ALL three targets.

**What failed:**
- **Golden reference had 4 errors** that distorted all previous scores. This is a fundamental
  risk of eval-first development — the eval can only be as good as its golden reference.
- Models split on format detection: all OpenAI models + Sonnet 4.6 + Haiku 4.5 still say
  "feature film" despite explicit prompt guidance. This seems to be a training data bias.

**What NOT to retry:**
- Don't trust eval results without manually cross-checking the golden against the source material.
- Don't optimize for models that get format/duration wrong — those are binary errors, not partial.

**Retry when:** N/A — this attempt succeeded.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [x] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [x] If approach succeeded: verified improvement holds across multiple runs
- [ ] If approach failed: classified the failure and set retry_when conditions
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [x] Updated registry.yaml scores with latency_ms and cost_usd (run: python scripts/extract-eval-metrics.py --result-file <path>)
- [x] If optimizing for speed/cost: verified quality didn't regress below target
