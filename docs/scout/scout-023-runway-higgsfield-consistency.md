# Scout 023 — runway-higgsfield-consistency

**Source:** Runway public docs/product pages; Higgsfield public docs/product pages
**Scouted:** 2026-04-30
**Scope:** How Runway and Higgsfield handle CineForge-adjacent film workflows, multi-shot consistency, and reusable character/prop/location design surfaces.
**Previous:** None
**Status:** Complete

## Findings

1. **Runway solves consistency mostly through reference-conditioned generation, not project memory** — MEDIUM value
   What: Runway Gen-4/Gen-4.5 emphasizes consistent characters, objects, locations, style, and world environments from visual references plus instructions. Gen-4 Video still works as short image-to-video generations with an input image, and Runway's own character guide recommends still-first workflows, short clips, and reference libraries.
   Us: CineForge already has the stronger upstream architecture: immutable bibles, continuity states, shot planning, and prompt compilation. We should treat Runway as a render engine/prompt target, not as the canonical source of story/world truth.
   Recommendation: Skip inline. Fold into render-adapter engine-pack knowledge when next touching Runway integration.

2. **Runway exposes useful prop/location workflows but not durable prop/location design modes** — MEDIUM value
   What: Gen-4 References and Aleph support objects, interiors, bounding-box/sketch composition guidance, style transfer, and adding elements into video while trying to preserve the rest of the scene.
   Us: CineForge has prop/location bibles and story-world baselines in spec, but the UI should keep these as durable design artifacts rather than one-off generation references.
   Recommendation: Create story only if Runway becomes an active target engine again: add an engine-pack checklist for character, prop, location reference input preparation.

3. **Runway multi-character dialogue remains a workflow assembly problem** — MEDIUM value
   What: Runway documents a multi-character dialogue workflow that combines Gen-4 Image References, Gen-4 Video, Act-Two, and a local editor. Act-Two supports single-character inputs, so multi-character dialogue is achieved by composing tools and editing.
   Us: CineForge's opportunity is to hide this choreography behind scene/shot artifacts and compiled prompts, especially for shot-reverse-shot dialogue and performance-state continuity.
   Recommendation: Create story later for a dialogue-sequence render adapter if dialogue rendering becomes the next video frontier.

4. **Higgsfield is converging on a CineForge-like scene workspace** — HIGH value
   What: Cinema Studio 3.5 positions itself as a production studio with characters, locations, props, AI co-director, per-shot camera/style control, color/camera panels, real-time collaboration, and an assistant that can break a script into shots.
   Us: This validates CineForge's Scene Workspace and ADR-003 concern-group direction, but Higgsfield appears more generation-first and less story-reasoning-first.
   Recommendation: Keep current direction. Use Higgsfield as a competitive pressure signal for making CineForge's scene workspace feel direct, visual, and generative rather than administrative.

5. **Higgsfield Elements directly mirror character/location/prop design modes** — HIGH value
   What: Cinema Studio 3.5 defines reusable Elements as characters, locations, and props created once, referenced across shots with @tags, and shared with teams. It also says locations regenerate when lighting/color changes to keep visual consistency.
   Us: CineForge has the same nouns as bibles and continuity state, but our differentiator is that Elements are derived from the story, carry provenance, and have scene-specific states.
   Transfusion:
   Exemplar: Reusable Elements with @tag insertion across shots.
   Invariant: The user should feel they can cast a character, pick a location, place props, and reuse them without re-explaining them.
   Adaptation: In CineForge, @tags should point to immutable bibles/state snapshots, not only saved visual references.
   Proof target: Scene render prompt detail shows `@character`, `@location`, and `@prop` chips resolved to the correct bible/state/version with visible provenance.
   Recommendation: Create story for "Story World chips in Scene Workspace" if not already covered by the active design-study work.

6. **Higgsfield Popcorn/Keyframes covers storyboard consistency up to a bounded sequence** — MEDIUM value
   What: Popcorn claims up to 8 matching scenes with aligned characters, lighting, and tone, then export to Sora 2; longer stories continue by using the last image as the next reference.
   Us: CineForge already has shot/storyboard artifacts; the useful pattern is a visible batch storyboard sequence with explicit reference carry-forward.
   Recommendation: Create story only if our storyboard UX does not already surface batch sequence continuity and reference carry-forward clearly.

7. **Higgsfield has stronger design-mode packaging; CineForge should not copy its center of gravity** — HIGH value
   What: Higgsfield packages Soul ID/Soul Cast for character consistency, Soul HEX for color, Moodboards/presets, Canvas graphs, and Cinema Studio panels. It is close to a full creative suite.
   Us: CineForge should not become just a better Higgsfield UI. The durable advantage remains story understanding: script bible, entity graph, continuity events, character psychology, actor agents, and explainable propagation.
   Recommendation: Keep design modes as Story World and scene-workspace surfaces, but lead with intent, story, and creative roles rather than raw asset management.

## Approved

- No implementation was requested or approved in this scouting pass.

## Skipped / Rejected

- Inline adoption skipped. The useful items are product/story recommendations, not safe text-only changes.

## Verification

- Read CineForge `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, generated `docs/build-map.md`, and ADR-003.
- Reviewed current public Runway sources: Gen-4, Gen-4.5, Gen-4 References, Gen-4 Video, Act-Two multi-character dialogue, Aleph reference edits, and Runway character guide.
- Reviewed current public Higgsfield sources: About, Soul 2.0/Soul ID, Soul Cast, Soul Cinema, Popcorn/Keyframes, Canvas, Kling 3.0 on Higgsfield, and Cinema Studio 3.5.

## Evidence

- Research-only scout captured here. No product/code changes landed.
- Key Runway sources:
  - https://runwayml.com/research/introducing-runway-gen-4
  - https://runwayml.com/research/introducing-runway-gen-4.5
  - https://help.runwayml.com/hc/en-us/articles/40042718905875-Creating-with-Gen-4-Image-References
  - https://help.runwayml.com/hc/en-us/articles/37327109429011-Creating-with-Gen-4-Video
  - https://help.runwayml.com/hc/en-us/articles/41748090660499-Creating-Multi-Character-Dialogues-with-Act-Two
  - https://help.runwayml.com/hc/en-us/articles/44609246167059-Controlling-Aleph-edits-with-a-Reference-Image
  - https://runwayml.com/resources/create-consistent-ai-characters
- Key Higgsfield sources:
  - https://higgsfield.ai/cinematic-video-generator
  - https://higgsfield.ai/about
  - https://higgsfield.ai/soul-intro
  - https://higgsfield.ai/blog/soul-cast-ai-filmmaking
  - https://higgsfield.ai/storyboard-generator
  - https://higgsfield.ai/canvas-intro
  - https://higgsfield.ai/kling-3.0
