# Story 141 Historical Creative-Brief Probe Audit

The retained `story-141-creative-brief-probe-20260331.json` report is valid as
historical evidence that one synthetic prompt comparison ran and that its paid
Claude judge preferred the new prompt in both lanes. It is not current
decision-grade evidence for creative quality:

- the fixture was authored specifically for the probe rather than sampled from
  a maintained corpus;
- the report contains one judge sample from one model;
- deterministic checks measured named-signal presence, not whether the resulting
  direction was coherent, tasteful, or useful in a conversation or render; and
- the report predates the v2 runner fingerprints and explicit paid-call opt-in.

The maintained v2 runner therefore defaults to deterministic-only execution,
records its narrow evidence scope and contract hashes, and requires
`--run-judge` for a paid live judge. A future adoption or default decision must
use current multi-case evidence plus an AI-as-tester conversation or equivalent
human/visual judgment; this historical report cannot carry that decision alone.
