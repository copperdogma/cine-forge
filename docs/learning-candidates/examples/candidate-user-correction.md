# Example - Candidate Warranted From User Correction

## Episode

During a project closeout, Cam corrected the agent for claiming a story was fixed from stale evidence without rerunning the relevant checks after the final patch.

## Learning Review Output

```text
RESULT: candidate-warranted
Target surface: .agents/skills/validate/SKILL.md
Trigger class: user-correction
Evidence: Project closeout thread with stale-evidence correction; Cam corrected the fixed/passing claim after final checks had not been rerun; validate or finish-and-push fresh-evidence wording was missing or not prominent enough.
Proposed change: Add or sharpen a fresh-verification gate in /validate or /finish-and-push so final fixed, passing, or done claims are backed by checks from the current pass.
Promotion gate: Cam accepts that this should become a validate or finish-and-push rule rather than remaining a one-off correction.
Confidence: high
Next step: run /learning-candidate to draft the candidate; do not promote during
the same closeout.
```

## Draft Shape

A candidate file would be created under `docs/learning-candidates/` with
`status: "Proposed"` if the correction is explicit enough to ask for an
accept/dismiss decision immediately. It would not edit `/validate` until
promotion is explicitly approved. Its review cadence would be "review now"
because the trigger is a direct user correction with a concrete target surface.

Candidate storage would include the target surface, source run, correction
summary, evidence summary, proposed change, review cadence, and promotion gate
before asking for a decision. Promotion remains a separate approved action: this
example can create or update a `Proposed` candidate, but it cannot edit
`/validate` until Cam first accepts the evidence and then separately approves
promotion from `Accepted` to `Promoted`. After promotion, the candidate is
terminal and re-running promotion must report no live changes.
