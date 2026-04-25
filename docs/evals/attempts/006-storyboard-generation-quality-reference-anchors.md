# Eval Attempt 006 - Storyboard Generation Quality: Reference Anchors

**Status:** Rejected
**Eval:** storyboard-generation-quality
**Date:** 2026-04-25
**Worker Model:** GPT-5
**Subject Model(s):** gpt-image-2

## Mission

Measure whether a non-default template-grid candidate can improve recurring
character identity and reference fidelity by explicitly mapping attached
reference images to named characters, locations, and storyboard panels in the
grid prompt.

The current shipped default, `gpt_image_2_template_grid_storyboards`, is fast
and structurally green, but Story 188 left it below the `0.75` usefulness floor.
The measured gap is no longer reference transport. The conditioned case carries
reference images into prompt metadata and direct provider inputs, while the
generated grids still drift character identity.

## Prior Attempts

Attempt 004 proved the scene-level template grid can cut storyboard-stage
latency and cost while preserving the existing per-frame artifact contract.
Attempt 005 split storyboard quality into product-readable dimensions, which
showed that the remaining grid weakness is concentrated in story specificity,
identity consistency, and reference fidelity rather than style consistency.
Story 188 then measured beat-grid routing and rejected it because it worsened
identity and prop discipline.

## Plan

1. Add a runtime-selectable reference-anchor packet for template-grid prompts.
2. Keep the existing template-grid default unchanged.
3. Preserve the storyboard artifact contract, grid slicing path, prompt-source
   lineage, reference transport fields, and benchmark boundary.
4. Add focused unit coverage for prompt construction, runtime annotations, and
   benchmark candidate wiring.
5. Run a bounded reference-conditioned subset first: current template-grid
   baseline versus `gpt_image_2_template_grid_reference_anchors`.
6. Promote nothing unless the subset improves the targeted identity/reference
   dimensions.

## Work Log

- 2026-04-24: Added `storyboard_v1/reference_anchors.py`, optional
  `Reference-image anchors:` grid prompt lines, runtime parameter wiring, prompt
  source lineage, artifact annotation, and benchmark provider support for
  `gpt_image_2_template_grid_reference_anchors`.
- 2026-04-24: Focused unit tests passed for grid prompt construction, runtime
  module wiring, and benchmark support. Full backend unit and Ruff checks also
  passed.
- 2026-04-24: Bounded paid runtime succeeded for both candidates on the
  reference-conditioned case. Current template-grid produced `success=1/1`,
  `15` frames, `35` direct refs, `$0.2730` cost, and `84651ms`
  storyboard-stage latency. Reference anchors produced `success=1/1`, `15`
  frames, `31` direct refs, `$0.2760` cost, and `82554ms` storyboard-stage
  latency.
- 2026-04-24: Promptfoo quality scoring completed with `2/2` passing assertion
  rows. The decision report scored current template-grid at `0.700` and
  reference anchors at `0.685`.
- 2026-04-24: Manual contact-sheet inspection found no local-code transport
  regression. The generated reference cards remain abstract, and the generated
  grids still show recurring ARIA/NOAH identity drift.

## Conclusion

**Result:** rejected
**Score before:** 0.700 bounded reference-conditioned subset
**Score after:** 0.685 bounded reference-conditioned subset
**Latency before:** 84651ms storyboard-stage runtime
**Latency after:** 82554ms storyboard-stage runtime
**Cost before:** $0.273
**Cost after:** $0.276

**What worked:** The implementation preserved the existing storyboard contract
and kept runtime structurally healthy. Reference anchors made the prompt's
intended subject-to-reference mapping explicit without changing production
defaults.

**What failed:** The candidate did not improve the measured target dimensions.
Both candidates stayed at `identity_consistency=0.5` and
`reference_fidelity=0.5`, while aggregate quality regressed from `0.700` to
`0.685`. The likely limit is not local-code reference transport; it is a mix of
image-model identity drift and benchmark fixture weakness because the current
reference assets are abstract cards, not realistic portraits or locations.

**What NOT to retry:** Do not run a full maintained comparison or promote this
candidate without a materially stronger reference substrate. More prompt text
alone did not move the target dimensions.

**Retry state:** open

**Retry when:**
realistic-reference-fixture - retry after replacing abstract reference cards
with realistic user-like character/location reference images, or after the
image model's reference-adherence behavior changes enough to warrant another
bounded probe.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [ ] Updated `docs/evals/registry.yaml` - scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` - attempts section with summary entry
- [x] If approach succeeded: verified improvement holds across multiple runs
- [x] If follow-on work remains: set `retry_state` and `retry_when` honestly
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [ ] Updated registry.yaml scores with latency_ms and cost_usd
- [ ] If optimizing for speed/cost: verified quality did not regress below target
