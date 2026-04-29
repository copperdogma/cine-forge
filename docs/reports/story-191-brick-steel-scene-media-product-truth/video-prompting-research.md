# Story 191 Video Prompting Research

Date: 2026-04-28
Project route: https://cineforge.copper-dog.com/brick-steel-full-retired/scenes/scene_001?tab=render

## Question

The current final-render prompt for `Brick & Steel: Full Retired` includes exact dialogue twice and still encourages an 8-second model to rush every spoken line. The compiler needs a prompt pattern that is more provider-friendly and more truthful about timing pressure.

## Source Findings

- OpenAI Sora guidance frames prompts around subject/setting, camera/motion, look/pacing, and audio intent. Its prompting tips emphasize starting from the core intent, iterating, describing timing, and limiting moving parts for fidelity, especially with lip-sync or character scenes. Source: https://help.openai.com/en/articles/12460853-creating-videos-on-the-sora-app
- Google Veo's prompt guide breaks video prompts into subject, action, style, camera, composition, ambiance, temporal elements, and audio. It explicitly treats temporal pacing and rhythm as promptable controls, and recommends separate audio sentences for sound effects, ambience, and dialogue. Source: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide
- Google Veo best practices emphasize clear specific prompts, single-scene focus for short videos, and avoiding redundant visual re-description when an image input already carries the visual basis. Source: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/best-practice
- Runway Gen-4 guidance is the strongest warning against overstuffed prompts: start simple, use direct physical language, focus on motion, avoid conversational prompt prose, and treat 5-10 second generations as single scenes. Source: https://help.runwayml.com/hc/en-us/articles/39789879462419-Gen-4-Video-Prompting-Guide
- Runway Academy's prompt guide says structure is less important than reducing ambiguity, but recommends a practical order for text-to-video prompts: camera shot, subject/action, environment, then supporting components. Its sequential prompting section allows natural-language order or timestamps, while warning that more complex sequences may need higher durations. Source: https://academy.runwayml.com/guides/prompting-guide

## Compiler Rules To Apply

1. Use one canonical dialogue section.
   Do not let final prompts contain dialogue once in prose and again in a footer. Exact lines should appear in a single `Dialogue timing / exact lines` section.

2. Keep exact dialogue as speaker-label lines.
   Use `SPEAKER: line` bullets rather than wrapping each utterance in extra quotes. This keeps exact-line matching stable and is easier for the postprocessor to dedupe.

3. Put timing where it affects behavior.
   The prompt should include action timing and dialogue cadence, not just a paragraph saying "hold the beat." For this story, the important controls are one speaker at a time, breath/reaction beats after each line, and a visibly held silence after the toast.

4. Surface duration pressure.
   Seven short lines plus a long silence in an 8-second clip is dense. The compiler should say so in the prompt and artifact notes instead of letting the video model compress all dialogue back-to-back.

5. Prefer concrete observable behavior over editorial abstraction.
   "Steel's energy drains and he goes still" is better than "Steel feels dissatisfied." "Locked-off two-shot" is better than vague cinematic intent.

6. Avoid multi-scene montage language for one short render.
   The current Brick & Steel prompt asks for a wide, frontal two-shot, looser handoff two-shot, tighter two-shot, and final wide in 8 seconds. That can be valid as an edit plan, but the compiler should express it as compact beats in one scene and avoid too many competing shot changes.

## Recommended Prompt Order

1. Format and scope: live-action, aspect ratio, duration, single-scene constraint.
2. Reference usage: which uploaded image is a face/look guide, and for whom.
3. Scene frame: location, subjects, props, time of day.
4. Camera/blocking/motion: locked camera or compact beat progression.
5. Action timing: visible sequence of entry, handoff, toast, silence, release line.
6. Dialogue timing / exact lines: one canonical ordered list with cadence instructions.
7. Lighting/color: concrete daylight and palette constraints.
8. Audio: separate sentences for ambience, dialogue, silence thinning, and cut behavior.

## Story 191 Patch Implication

The previous deterministic footer was too blunt. It fixed missing dialogue, but treated quoted inline dialogue as missing because the shot plan stores `STEEL: Beer's ready!` while the compiler wrote `STEEL: "Beer's ready!"`. The postprocessor now needs normalized dialogue matching, a single dialogue timing fallback, and cadence guidance. The compiler prompt also needs to tell the LLM to produce one dialogue section rather than a prose mention plus a second block.
