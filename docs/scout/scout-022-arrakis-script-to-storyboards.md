# Scout 022 - Arrakis Script-to-Storyboards

**Source:** https://x.com/arrakis_ai/status/2046821264535556143?s=12&t=uFZE-MuhgWdh1YErEZzLtQ; https://www.atlascloud.ai/blog/guides/ultimate-drama-workflow-gpt-image-2-seedance-2-0; https://github.com/kianaliang-dev/drama-director-skill
**Scouted:** 2026-04-24
**Scope:** Script/story/manuscript to 3x3 storyboard page plus image-to-video handoff as a possible new-approach trigger for the Story 186 storyboard-quality line.
**Previous:** Story 186 (`storyboard-generation-quality`) made `gpt-image-2` template grid storyboards the shipped fast batch default, but the maintained eval still shows lower story specificity and identity consistency for the grid lane.
**Status:** Complete

## Findings

1. **Fixed 9-beat storyboard routing is useful, but not as a wholesale replacement** - HIGH value

   What: The source condenses a script, novel passage, or story outline into nine key visual moments, orders them left-to-right/top-to-bottom in a fixed 3x3 page, and asks GPT Image 2 to draw the full page in one image call. The prompt explicitly gives each panel one story beat and asks for consistent character appearance across all panels.

   Us: CineForge already has a template-grid storyboard route that renders one grid image and slices it back into the existing per-frame storyboard artifact contract. The current grid prompt is shot-derived and cheap, but the latest split eval says the grid lane loses quality mainly in `story_specificity` and `identity_consistency`, not in style or text cleanliness.

   Recommendation: Create a focused follow-up story. Do not copy the source's comic-drama deliverable; test whether a beat-router/template-grid candidate improves CineForge's measured grid weaknesses while preserving the existing shot-plan, storyboard artifact, reference transport, and eval boundaries.

   Transfusion:
   Exemplar: One coherent prompt asks for a "3x3 comic book page with 9 panels" and lists panel 1 through panel 9 as ordered story beats.
   Invariant: The image model gets a complete scene-level narrative plan for the full grid before it draws the page.
   Adaptation: CineForge should derive the grid beats from scene and shot-plan artifacts, keep film storyboard styling instead of social comic-drama styling, and continue slicing the output into normal storyboard frames with lineage.
   Proof target: `storyboard-generation-quality` adds a measured candidate that improves grid `story_specificity` and/or `identity_consistency` without regressing style consistency, text cleanliness, reference flow, latency, or cost.

2. **Grid-to-motion as "visual DNA" is a good previz research note, not immediate provider work** - MEDIUM value

   What: The source passes the 9-panel image to Seedance 2.0 I2V and stresses that the grid is a reference for characters, wardrobe, locations, lighting, and color, not the literal object being filmed. The motion prompt must describe the scene action in the world, not a camera moving across a comic page.

   Us: CineForge has storyboard, previz, and final-render lanes, but the current storyboard grid is not yet a direct video-conditioning contract. ADR-003 already treats storyboards and blocking as plausible inputs to video generation, so the concept aligns with the design direction, but the local proof target still belongs in the existing eval ladder before adding a provider path.

   Recommendation: Preserve the pattern in Story 188 as a handoff design constraint or future previz/render follow-up. Do not add Atlas Cloud or Seedance-specific coupling in this scout pass.

   Transfusion:
   Exemplar: The source tells operators that the storyboard page is "visual DNA + storyboard reference" and warns against prompts that film the page itself.
   Invariant: If storyboard grids feed video generation, the prompt must state that the grid conditions the world and staging; it must not direct the model to shoot a paper storyboard.
   Adaptation: Apply this as a provider-agnostic render/previz prompt contract if the local video lane later consumes storyboard grids.
   Proof target: A future previz/render story can show a real video lane uses storyboard grids as conditioning without degrading into page-pan videos.

3. **Atlas Cloud scripts are provider glue, not a CineForge architecture target** - LOW value

   What: The source scripts are thin Atlas Cloud wrappers around `generateImage`, `generateVideo`, and a polling endpoint, with environment setup for one Atlas API key.

   Us: CineForge already has provider adapters, model discovery/live-smoke surfaces, runtime params, cost capture, and an OpenAI `gpt-image-2` storyboard lane. A new Atlas wrapper would duplicate transport concerns and distract from the measured storyboard-quality gap.

   Recommendation: Skip. Revisit only if a provider-floor story proves Atlas exposes a materially better or cheaper lane than direct providers.

4. **Seedance prompt-hardening rules mostly overlap local constraints** - LOW value

   What: The source includes practical constraints for I2V prompts: keep tracked characters limited, avoid reflection-heavy shots, make cuts change multiple dimensions, avoid slop words, and describe microexpressions physically.

   Us: CineForge already has style, text, reference, identity, and scene-context constraints in storyboard prompts, plus provider-specific render engine pack patterns. These rules are useful as a reference, but they are not yet grounded in a local failure for the storyboard-grid eval.

   Recommendation: Do not add another generic rule list now. If Story 188 or a future previz story finds a concrete failure, port the relevant rule with an eval-backed reason.

## Approved

- [x] 1. Fixed 9-beat storyboard routing - routed into Story 188.
- [x] 2. Grid-to-motion handoff constraint - preserved as future previz/render context in Story 188.

## Skipped / Rejected

- 3. Atlas Cloud scripts - skipped because CineForge should not add a provider wrapper without provider-floor evidence.
- 4. Generic Seedance prompt-hardening rules - skipped until tied to a local measured failure.

## Verification

- Created `docs/stories/story-188-storyboard-grid-beat-router-and-motion-handoff-scout.md`.
- Updated `docs/scout.md` index.
- Removed the processed Arrakis/X item from `docs/inbox.md`.
- Direct X retrieval was attempted but connector reads failed (`Error: 'urls'` for tweet search; duplicate `__cf_bm` cookie for user lookup), so this scout used the linked Atlas article and cloned GitHub source as primary inspectable evidence.
- Updated the `generation_and_visualization` architecture-audit story counter in `docs/methodology/state.yaml` so the new domain-tagged story is canonical.
- Ran `pnpm methodology:compile`; Story 188 appears in generated story surfaces.
- Ran `pnpm methodology:check`; outputs are current with only the existing `api_service_and_operator_console` architecture-audit warning.
- Ran `git diff --check`; no whitespace errors.

## Evidence

- Local source checkout inspected at `/tmp/cineforge-scout-arrakis`.
- Source skill: `/tmp/cineforge-scout-arrakis/SKILL.md`.
- Source article: https://www.atlascloud.ai/blog/guides/ultimate-drama-workflow-gpt-image-2-seedance-2-0.
- Source repo: https://github.com/kianaliang-dev/drama-director-skill.
- Follow-up story: `docs/stories/story-188-storyboard-grid-beat-router-and-motion-handoff-scout.md`.
