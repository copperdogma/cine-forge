# Eval Attempt 004 — Storyboard Generation Quality: Template Grid Render

**Status:** Inconclusive
**Eval:** storyboard-generation-quality
**Date:** 2026-04-23
**Worker Model:** GPT-5
**Subject Model(s):** gpt-image-2

## Mission

Measure whether a scene-level grid render can reduce storyboard latency and cost
without dropping below the maintained `0.75` usefulness floor. The current
per-frame `gpt-image-2` default is quality-strong at `0.8562`, but it remains
too slow and expensive at `672297ms` mean total runtime, `410166ms`
storyboard-stage runtime, and `$0.447` mean cost.

## Prior Attempts

No previous attempt file existed for this eval. The registry already recorded
inline Story 186 attempts: reference transport was fixed, the first `gpt-image-2`
quality score was corrected after promptfoo frame sampling was fixed, and the
`1024x1024` square candidate cleared quality but did not solve latency enough
because it still generated one image per frame.

## Plan

1. Add a runtime-selectable `template` grid mode that renders a blank storyboard
   grid template and passes it to `gpt-image-2` as a direct reference image.
2. Generate one grid image per scene chunk, then slice the output back into the
   existing per-frame storyboard artifact contract so the UI and downstream
   evals do not need a schema fork.
3. Add the template-grid candidate to the Story 186 runtime and promptfoo
   benchmark surfaces.
4. Run the live runtime harness and promptfoo scorer/judge with `--no-cache`.
5. Record the result without changing the default unless quality is competitive
   with the per-frame default.

## Work Log

- 2026-04-23: Added `storyboard_v1/grid.py`, `grid_mode`, `grid_max_panels`,
  template rendering, grid prompt assembly, grid slicing, runtime metadata, and
  a `gpt_image_2_template_grid_storyboards` benchmark candidate.
- 2026-04-23: Live reference-image probe confirmed `gpt-image-2` can accept a
  blank grid template as an image reference through CineForge's image wrapper.
- 2026-04-23: First full grid attempts exposed OpenAI edit parameter
  compatibility failures around `quality` and `output_format`; added retry
  fallback coverage in `src/cine_forge/ai/image.py`.
- 2026-04-23: First successful styled grid run scored `0.729` at `$0.278` mean
  cost and `89630ms` mean storyboard-stage runtime. Classification: promising
  speed/cost result, but below quality floor because prompt-only frames copied
  readable text into whiteboards/signs.
- 2026-04-23: Added text-display sanitization and stronger grid prompt
  instructions. Fresh run scored `0.670`; readable-text hard constraints passed,
  but the vision judge still under-read storm/water-tower/lantern specificity.
- 2026-04-23: Added explicit location and environment anchor instructions for
  grid renders. First anchored scoring pass reached `0.757` overall (`python
  0.780`, `rubric 0.735`) with `2/2` runtime success, `$0.275` mean cost,
  `326228ms` mean total runtime, and `94511.5ms` mean storyboard-stage runtime.
- 2026-04-23: Reran the promptfoo judge/scorer with `--no-cache` on the same
  final generated images to check judge variance without paying for more image
  generation. The score dropped to `0.666` (`python 0.757`, `rubric 0.575`), so
  the grid lane is not quality-stable enough to replace the per-frame default.

## Conclusion

**Result:** inconclusive
**Score before:** 0.8562
**Score after:** 0.666
**Latency before:** 672297ms mean total runtime; 410166ms storyboard-stage runtime
**Latency after:** 326228ms mean total runtime; 94511.5ms storyboard-stage runtime
**Cost before:** $0.447 mean total cost
**Cost after:** $0.275 mean total cost

**What worked:** The user's grid hypothesis was correct on mechanics and
performance. Generating one image per scene chunk and slicing panels cut
storyboard-stage latency by about 77% and mean cost by about 38% versus the
per-frame default. Passing a blank grid template as a reference image worked and
helped layout control.

**What failed:** The first grid prompts copied readable text into generated
whiteboards/signs. After that was fixed, the candidate still trailed the
per-frame default on quality, especially on reference-conditioned fidelity and
storm/lantern specificity. A second no-cache judge pass on the same generated
images dropped below the initial quality floor, so the apparent `0.757` pass was
not stable enough to promote. The benchmark's abstract reference cards also
limit how much the direct-reference path can prove about real character
fidelity.

**What NOT to retry:** Do not promote a text-only or under-anchored grid prompt.
Do not flip the production default merely because the grid is faster; it needs
either per-frame-default quality or a deliberate product decision to trade
quality for latency/cost.

**Retry state:** open

**Retry when:**
new-approach — retry when grid prompts can use stronger scene-level visual
anchors, generated character/location reference images instead of abstract
fixture cards, or a multi-image-grid API feature that returns separated panels
without template residue.

**Product default addendum (2026-04-23):** The production default was promoted to
the template-grid lane after a separate product decision to optimize storyboards
as a fast batch first pass. The quality caveat remains real: grid still trails
per-frame generation on story specificity and identity consistency. The tradeoff
is acceptable for the current workflow because the generated panels are review
drafts, style/text consistency is stronger, storyboard-stage latency and cost are
much lower, and individual failed panels can be regenerated later through the
per-frame path.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [x] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [x] If approach succeeded: verified improvement holds across multiple runs
- [x] If follow-on work remains: set `retry_state` and `retry_when` honestly
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [x] Updated registry.yaml scores with latency_ms and cost_usd
- [ ] If optimizing for speed/cost: verified quality didn't regress below target
