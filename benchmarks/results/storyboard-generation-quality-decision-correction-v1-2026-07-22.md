# Storyboard Generation Quality Decision Correction

This addendum corrects one imprecise rationale in the immutable v3 decision
report. It does not change retained media, provider output, scores, latency,
cost, the hard-gate outcome, or the default decision.

- Source decision: `storyboard-generation-quality-v3-decision-2026-07-22.json`
- Source SHA-256: `b9f38ae27685f5fa631d41f99da5ff39535bdda75144e69c429d569d078388d7`
- Retained manifest SHA-256: `6bf488777cd23f374204ac273ba2dcd114eb18c9b24ee039f52da65909dceef6`
- Runtime contract: pass for both candidates
- Evidence dimension: `1.0` for both candidates
- Actual failed hard dimensions: `identity_consistency`,
  `story_specificity`

The v3 phrase “packet/evidence hard constraints” was too broad. Packet identity,
frame/reference accounting, retained-media provenance, and evidence grounding
all passed. The maintained hard gate also requires story specificity and
identity consistency; both candidates failed those dimensions, so `overall`
correctly remains unreported.

Manual inspection separates the attribution:

- Image-generation model misses, non-runtime-blocking: material per-frame
  identity drift, subdued storm cues, and unclear receiver/lantern/boot staging.
- GPT-5.4 packet-analysis misses, non-runtime-blocking: under-reading some
  visible tower/catwalk, receiver, and comparatively coherent template-grid
  identity evidence.
- Ambiguous, non-runtime-blocking: the final ON AIR state, some blocking, and
  one antenna depiction.
- Golden correction: none. Abstract reference cards prove transport only; their
  glyphs and colors are not quality targets.

Decision unchanged: no quality promotion and no default change. Template-grid
remains only the faster, cheaper value hold.
