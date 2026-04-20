Ideas, links, and resources captured for triage. Newest first.
Triaged via `/triage-inbox` skill. Processed items are deleted — the inbox is a queue, not an archive.

## Untriaged

- From Conductor Scout 017 (2026-04-11): the current media-automation bundle is
  worth keeping only as a narrow future reference for CineForge, not as a new
  shared substrate. If a future CineForge story opens around post-generation
  video cleanup/editing or long-running vendor-backed media orchestration,
  revisit three specific ideas: `VOID` for interaction-aware object removal,
  OpenClaw-style background-task/provider-failover orchestration for external
  video jobs, and MultiMedia-Agent-style plan/tool decomposition for complex
  multimodal creation. Do **not** treat HeyGen or editor-driving demos as proof
  that CineForge's current previz bottleneck is solved; the live repo truth is
  still that AI-previz usefulness is plausible while runtime remains blocked.

- Veo 3.1 Fast and Veo 3.1 both take multiple input images as reference, which will be useful when we start eval'ing final video models for final render.

- Good full production approach using Higgsfield we may be able to glean from: https://x.com/PJaccetturo/status/2045180107971805578?s=20

20260420 manual QA by Cam: https://cineforge.copper-dog.com/the-mariner-13/characters
- Deep Breakdown still SUPER slow. How much have we dug into speeding up each phase? Can we do any (more) of it in parallel?
- Continuity tracking ran almost twice as long as anything else in Deep Breakdown. Does is just take that long or is there an issue?
- When it finished Script Breakdown and Deep Breakdown the screen just goes black as soon as it's done. When I open web console I see this but I'm not sure if it's related: api/projects/the-mariner-13/chat:1  Failed to load resource: net::ERR_INSUFFICIENT_RESOURCES. If I refresh the screen it seems fine. LATER: It went black after 
- When I click Shots/Storyboards/Production it all takes me to the same screen: https://cineforge.copper-dog.com/the-mariner-13/scenes/scene_001?tab=shots ... Does this imply we're missing a bunch of functionality? Or maybe it just means we need to do shot planning first but that's not obvious when you hover over Shots/Storyboards/Production. LATER: Oh I see what's happening. It's taking you to scenes/storyboard but there's so much frontmatter (SCene Reference Stack + Intent and Mood) BEFORE the tabs that you can't see that it's changed the tab. Should Scene Reference Stack and Intent & Mood simply by more tabs?
  - Also when you hover over, say, Storybords it shows you: Storyboards - Run Now, PreViz - Run Now, Keyframes - Run Now. But you can't actuall hover over any of those things and "Run Now" sounds like something you can click which probably isn't the purpose there.
  - The tab thing is a little out of control, too. We already have to scroll we have so many. We need to have a discussion to rethink this a bit. This is really the core of the app: digging into the details of every scene to get it rendering correctly in the end.
- We need to lead the user through what to do a little better.
  - We start off with the AI leading you through, telling you to run a Script Breakdown, and once done, telling you to run a Deep Breakdown. Then it just says "Deep Breakdown complete! etc etc" but doesn't give you direction on what to do next. Likely there's a clear path forward if we assume "render script to final film" so the AI should either ask what you want to do next with OPTION or just suggest what to do next.
  - Even when it's done Script and Deep Breakdowns it clearly shows the progression, with green checks next to Script/World/Direction and Shots/Storyboard/Production in white, indicating they're next, but when I click Shots I get the first scene, a "Scene reference stack", then Intent and Mood, then Overview. 
- We also may need to ASK after the import the script what they want to do. There are many use cases for this app. A user may not WANT to take it all the way the final film and just want to do previz, or prop management, or script work, or who knows. We might need to think about the broad categories of what peopel may want to do with this app and help peopel through it. For NOW, thoguh, we may want to assume they want to do the ENTIRE thing (script to film) and just proactively lead them through that.
- After running Create Shot Plan for Current Scene the AI says "Open Scene Workspace" but that takes you to Scene/OVerview which is NOT what it just generated (it generated Scene/Shots).