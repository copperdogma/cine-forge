---
name: golden-verify
description: Orchestrate golden fixture verification — launch parallel subagents, record results, loop until everything is CLEAN.
user-invocable: true
---

# /golden-verify [fixture-id]

Orchestrate verification of all golden reference test fixtures. This is a pure
orchestrator — it never reads fixture content. It reads the checklist, launches
subagents to do the work, records their verdicts, and loops.

Because the orchestrator stays lean (no fixture content in context), it can run
for hours processing dozens of fixtures.

**Usage:**
```
/golden-verify                  # run until everything is CLEAN
/golden-verify character        # verify one specific fixture (partial match)
```

## The Loop

Repeat until there's no work left:

### 1. Check inbox

Scan `benchmarks/golden/_inbox/` for new input directories. For each one,
launch an opus subagent to run `/golden-create`.

### 2. Find work

Read `benchmarks/golden/_verification-checklist.md`.

Work items:
- **PENDING** — need first verification pass
- **PASS N** (had issues last time) — need another clean pass

If nothing needs work, report done and stop.

### 3. Launch subagents

Use your judgment on parallelism — one fixture per subagent, all `model: "opus"`.

**For new inbox items:**
> Run `/golden-create` for fixture `{FIXTURE-ID}`.

**For verifications:**
> Adversarially verify golden fixture `{FIXTURE-ID}`. Your job is to find bugs,
> not confirm correctness.
>
> The verification protocol is at `benchmarks/golden/_verify-golden-outputs.md`
> and the format spec is at `benchmarks/golden/README.md`. Read the INPUT
> first — build your own mental model before looking at the golden output, then
> compare ruthlessly. Fix any issues directly in the files.
>
> Run the validator after edits:
> `.venv/bin/python benchmarks/golden/validate-golden.py {FIXTURE-ID}`
>
> Report: VERDICT (CLEAN or FIXED), what you changed if anything, validator result.

### 4. Update checklist and loop

Collect all verdicts. Update `_verification-checklist.md` yourself (not the
subagents — one writer avoids conflicts):
- CLEAN → `CLEAN (pass N)`
- FIXED → `PASS N (issues found: X)` with notes
- New golden → add row as `PENDING`

Report batch results, then loop back to step 1.

## Guardrails

- **Never read fixture content.** Subagents do the work. You stay lean.
- **All subagents use opus.** Golden work requires SOTA judgment.
- **Don't verify what you just created.** New goldens get PENDING status; a
  different subagent verifies them next iteration. This is how we get context
  isolation — the verifier has zero memory of how the golden was written.
- **You own the checklist.** Subagents report; you write. One writer, no conflicts.
- **Run the structural validator.** Every subagent must run it after edits.
  Structural errors are a hard stop — don't mark CLEAN with validator failures.
