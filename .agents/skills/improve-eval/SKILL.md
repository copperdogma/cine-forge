---
name: improve-eval
description: Autonomously pick an eval and attempt to improve its score
user-invocable: true
---

# /improve-eval [eval-id] [--autonomous]

Pick an eval from the registry, study past attempts, and try to improve its score.

**Default behavior:** Propose which eval to work on and the approach, wait for user approval.
**Autonomous mode:** If the user says something like "you choose and just do it", pick the best
candidate and execute without asking. Also activated by passing `--autonomous`.

## Phase 0 — Situational Awareness

1. **Record the worker model.** Note which AI model is executing this skill (you, the agent).
   Write it down — it goes into the attempt record.

2. **Discover available models.** Run the summary view first for a quick glance:

```bash
.venv/bin/python scripts/discover-models.py --summary 2>/dev/null
```

This shows models grouped by tier (SOTA/mid/cheap/reasoning/legacy) with untested counts.
If you need full detail on specific tiers, run with `--check-new` for the complete list.

Parse the output to understand:
- What models are available across providers
- What's new since our last eval run (marked `[NEW]` or listed as untested)
- Are there new SOTA models that might invalidate past "model-insufficient" failures?
- Are there new cheap models worth testing for cost optimization?

3. **Read the eval registry:**

```bash
cat docs/evals/registry.yaml
```

4. **Check for staleness.** Compare each eval's `git_sha` against current HEAD:

```bash
git rev-parse --short HEAD
```

If any scores are from a significantly older commit, flag them as potentially stale.

## Phase 1 — Pick a Candidate

Rank candidates using this priority order:

### Priority 1: Retry-ready attempts
Scan the `attempts` section of each eval. Look for failed attempts where `retry_when` conditions
are now met:
- `new-worker-model`: Is the current worker model newer/better than the attempt's `worker_model`?
- `new-subject-model`: Are there new models available (from Phase 0) that weren't tested before?
- `cheaper-subject-model`: Have pricing conditions changed?

### Priority 2: Biggest gap to target
For quality evals: `target.value - best_score` = gap. Rank by largest gap.

### Priority 3: Stale scores
Evals with git_sha far from HEAD might already be better (or worse) from code changes.
Re-measure first before attempting improvements.

### Priority 4: Compromise evals
Compromise evals with no attempts yet — worth probing to establish a baseline.
Run the compromise gate checker to see current status:

```bash
.venv/bin/python scripts/check-compromises.py
```

This shows which compromises are closest to being eliminable. C3 (single model)
is computed directly from registry scores — if any model is close on all evals,
improving those specific eval scores could eliminate an entire compromise.

**Present the ranked list** to the user with a 1-sentence rationale for each.
Let the user pick (unless `--autonomous`, in which case pick #1).

## Phase 2 — Study Past Attempts

For the chosen eval:

1. **Read ALL previous attempt stories.** Every file referenced in the eval's `attempts` list:

```
docs/evals/attempts/{id}-*.md
```

2. **Synthesize lessons:**
   - What approaches have been tried?
   - What worked (even partially)?
   - What is definitively a dead end? (check "What NOT to retry" sections)
   - What retry conditions were set?
   - What worker models were used? (A smarter model might succeed where a weaker one failed)

3. **Read the eval config, scorer, and golden reference** to understand exactly what's being measured:
   - Eval config: the `config` field in registry.yaml
   - Scorer: the `scorer` field
   - Golden: the `golden` field

## Phase 3 — Plan the Attempt

1. **Create the attempt file.** Find the next available attempt number:

```bash
ls docs/evals/attempts/ | sort -n | tail -1
```

Copy the template:
```bash
cp docs/evals/attempt-template.md docs/evals/attempts/{NNN}-{eval-id}-{short-title}.md
```

2. **Fill in the header fields:**
   - Eval ID, date, worker model, subject model(s)
   - Mission: what score are we trying to improve, from what to what
   - Prior attempts: summary of what was learned from Phase 2

3. **Write the plan.** Consider these improvement vectors:
   - **Prompt engineering:** Can the extraction/analysis prompt be improved?
   - **Output format:** Is the model struggling with the expected output structure?
   - **Golden reference:** Is the golden reference wrong or incomplete? (Sometimes the eval is the problem)
   - **Scorer calibration:** Is the scorer penalizing correct-but-different answers?
   - **Model selection:** Would a different model score better at acceptable cost?
   - **Architecture:** Can the task be decomposed differently?

4. **Human gate.** Present the plan to the user and wait for approval.
   (Skip this gate in `--autonomous` mode.)

## Phase 4 — Execute

1. **Make changes** according to the plan. This might involve:
   - Editing prompt templates in `benchmarks/prompts/`
   - Modifying scorers in `benchmarks/scorers/`
   - Updating golden references in `benchmarks/golden/`
   - Changing promptfoo configs in `benchmarks/tasks/`
   - Modifying pipeline module code in `src/cine_forge/modules/`

2. **Run the eval with `--no-cache`** to get clean measurements:

```bash
cd benchmarks && source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1 && promptfoo eval -c tasks/{eval}.yaml --no-cache -j 3
```

3. **Record the score** in the work log immediately.

4. **If the score improved:** Verify it holds. Run again to check consistency.

5. **If the score didn't improve or got worse:** Decide whether to iterate or stop.
   - If you have a clear next idea, iterate (up to 3 attempts within one session).
   - If you're out of ideas, stop and record the failure.

## Phase 5 — Record (MANDATORY — never skip)

Regardless of success or failure:

1. **Complete the attempt story:**
   - Fill in the Work Log with everything tried and every score measured
   - Write the Conclusion section
   - Set the result (succeeded/failed/inconclusive)
   - Fill in score_before and score_after
   - If failed: set retry_when conditions and "What NOT to retry"
   - Complete the Definition of Done checklist

2. **Update the registry.** Edit `docs/evals/registry.yaml`:

   a. **Update scores** — Add or update score entries with new measurements:
   ```yaml
   scores:
     - model: "Sonnet 4.6"
       metrics:
         overall: 0.XXX  # new score
       measured: YYYY-MM-DD
       git_sha: "{current HEAD}"
       result_file: benchmarks/results/{result-file}.json
   ```

   b. **Add attempt summary** — Append to the eval's `attempts` list:
   ```yaml
   attempts:
     - id: "{NNN}"
       story: attempts/{NNN}-{eval-id}-{title}.md
       date: YYYY-MM-DD
       status: failed  # or succeeded/inconclusive
       approach: "One-line summary of what was tried"
       worker_model: "{your model, e.g. Opus 4.6}"
       worker_model_date: YYYY-MM-DD
       subject_model: "{model being evaluated}"
       score_before: 0.XXX
       score_after: 0.XXX
       retry_when:
         - condition: new-worker-model
           note: "Why this condition"
   ```

3. **Report results** to the user with a clear summary:
   - What eval was targeted
   - What was tried
   - What the score change was
   - What the next steps are (if any)

## Boundaries

### Always do
- Read ALL past attempts before starting
- Run evals with `--no-cache`
- Record the attempt even if it fails
- Update registry.yaml even if nothing improved (scores might have changed)
- Note both the worker model AND subject model in the attempt record

### Ask first
- Before modifying golden references (they're hand-curated ground truth)
- Before changing scorer logic (changes what "correct" means)
- Before making architectural changes to pipeline modules
- Before running expensive evals (full 13-provider matrix)

### Never do
- Silently accept score regressions
- Skip the recording phase
- Modify the registry without actually running the eval
- Claim success without verification
- Retry an approach that a previous attempt explicitly marked as "do NOT retry"
