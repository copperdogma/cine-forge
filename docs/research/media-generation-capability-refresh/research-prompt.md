---
type: research-prompt
topic: "media-generation-capability-refresh"
created: "2026-03-13T16:52:15.213571+00:00"
---

# Research Prompt

Research the current 2026 landscape for media-generation capabilities relevant to CineForge's generation stack.

Context:
- CineForge is a film-reasoning and production pipeline with a render-adapter architecture.
- We care about practical integration value, not hype.
- Existing backlog items point to new capabilities across image, video, and music generation:
  - Grok Imagine supporting up to 7 reference videos
  - Runway Character Rendered App
  - Google's latest image-generation model(s)
  - Gemini / Nano Banana 2 templates for global style transfer
  - ElevenLabs music generation
  - Gemini Lyria 3 music generation and music-video style synchronization
- We also want a competitive scan of other current SOTA tools/models, not just the named ones.

Questions to answer:
1. What are the strongest currently available image, video, and music-generation models/tools for CineForge-relevant use cases?
2. For each serious candidate, what inputs does it support today?
   - reference images
   - reference video(s)
   - audio / music conditioning
   - style transfer / template systems
   - character consistency controls
   - multi-shot or scene-level generation
3. Which tools are strongest for these use cases specifically?
   - character-consistent video generation
   - global style transfer across a scene or sequence
   - music / soundtrack generation
   - video generation guided by timing, motion, or music reference
   - turning weak real-world inputs into stronger reference assets
4. What are the operational realities for each candidate?
   - API availability vs app-only
   - pricing / rate limits if known
   - licensing / usage constraints if material
   - maturity / reliability / integration risk
5. How should CineForge map the best options onto its roadmap?
   - Story 028 Render Adapter
   - Story 056/119/121 design-study pipeline
   - Story 098 real-world asset upload pipeline
6. Recommend a shortlist of:
   - immediate trials worth running now
   - watchlist items that are promising but not yet integration-ready
   - items to ignore despite hype

Output expectations:
- Produce a comparison matrix by provider/model/tool.
- Separate findings by use case rather than by marketing category.
- Call out which claims are confirmed by official docs vs secondary sources.
- End with a concrete recommendation list for CineForge:
  - top 3 near-term experiments
  - top 3 roadmap implications
  - top risks / unknowns
