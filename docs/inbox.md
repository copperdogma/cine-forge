Ideas, links, and resources captured for triage. Newest first.
Triaged via `/triage-inbox` skill. Processed items are deleted — the inbox is a queue, not an archive.

## Untriaged

- 2026-05-28 — From Conductor Scout 043: Anthropic's `claude-opus-4-8`
  is a strong CineForge challenger for long-form script understanding, creative
  direction quality, prompt compilation, character/continuity reasoning, and
  codebase-scale agentic work. It is not a render-video or still-image model.
  First run live provider discovery/smoke and pricing checks, then add one or
  two bounded model-slot evals where the tiered model strategy is still below
  a single-model bar. Compare quality, latency, and cost before touching any
  default creative, analysis, or prompt-compiler lane. Source:
  `/Users/cam/.codex/worktrees/1375/conductor/docs/scout/scout-043-claude-opus-48-api-eval-opportunities.md`

- 2026-05-06 - From Conductor inbox: OpenAI's 2026-05-05 GPT-5.5
  Instant release says the ChatGPT default now uses GPT-5.5 Instant and the
  API exposure is `chat-latest`. Treat this as a cheap/default-lane challenger,
  not a repeat of the April GPT-5.5 frontier sweep. First pass: run
  `scripts/discover-models.py` to confirm the callable slug and pricing, then
  add it only to fast/default text lanes where GPT-5.4 mini/nano or GPT-5.4
  currently compile, normalize, or judge pipeline outputs. Compare quality,
  latency, and cost before touching defaults; do not rerun the full GPT-5.5
  Pro/frontier matrix unless the default-lane screen wins. Source:
  https://openai.com/index/gpt-5-5-instant/

- Default Design Study and Image Prompt Compiler: Looking at the look and feel of the characters, locations, and props is critical for consistency. So I know we have a lane where the user can basically skip most everything just to get to the rendering if they want, but we still have to backfill a bunch of stuff to make sure that the AI model gets all of the information it needs to do that render in a way that's possibly going to be satisfying. Likely, it's not going to look like they imagined because they didn't put any work into specifying what the character should look like by working their way through the design study, but that's fine. We're allowing them that path. But in doing so, we need to make sure that when we backfill all of the stuff, the world details, the direction, stuff like that, we also need to generate the visual design studies for the characters, locations, and props. Otherwise, they're going to end up being very inconsistent throughout the render, which isn't great. So I think we need to add that to our backfilling pipeline, and we just want to use basically the absolute cheapest, quickest image generator we have. To generate something, it needs to have a consistent style, so anything we generate visually needs a prompt compiler built into it. So for the final render, we have a prompt compiler where it takes all of the various details that we or the user have specified and compiles them down into a prompt to make sure that the look and feel of everything is consistent and aligned. That's for the AI video generations, but for the design studies, for the stills that we generate, we need to do the exact same thing. We need a prompt compiler to make sure that the characters are going to look more or less the same every time. Not visually identical, obviously. If it says Brick Braddock is a retired detective and that's the only description, he's going to look quite different each time. But we need to make sure we have that information in there. And we need, in that prompt compiler for any of the visual renderings, to have a strong description of how we want these things generated in the first place so they come out in a format that's easy and useful for the AI video generator to use as an input reference, which is mostly what these are for.

- Scout: https://www.bilibili.com/video/BV1FFRQB2Eqw/?share_source=copy_web&vd_source=1895a0980329837a670140ed16f23619
  - This Chinese guy made a brilliant short movie entirely with AI. We need to investigate his entire workflow with special attention to his prompts for video AI direction and take inspiration from that for our own generator.

- Scout: https://pjace.beehiiv.com/p/gossip-goblin-s-crazy-workflow-for-building-original-worlds-200m-views?utm_source=pjace.beehiiv.com&utm_medium=newsletter&utm_campaign=gossip-goblin-s-crazy-workflow-for-building-original-worlds-200m-views&_bhlid=2bb219fadcf9f15a7da8df4462f69971d521cc63
  - Incredibly movie with a super in-depth X thread on how it was made. It's a LOT of work. It actually makes me second guess attempting to get CineForge to do this. HOWEVER, our ideal.md approach + continual improvement of the AI models (that we expect when building CineForge) means our foundation should still be good as AI improves, eventually letting us create something like this movie even if we can't do it today.
  - But pull out their process in the scout. We need to know this as it will help inform what failure modes we should expect and we can start thinking of how to address them.
