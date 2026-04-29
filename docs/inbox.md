Ideas, links, and resources captured for triage. Newest first.
Triaged via `/triage-inbox` skill. Processed items are deleted — the inbox is a queue, not an archive.

## Untriaged

- We're missing our XAI key on prod: https://cineforge.copper-dog.com/brick-steel-full-retired/scenes/scene_001?tab=previz = CINE_FORGE_XAI_API_KEY (or legacy XAI_API_KEY) is not set

- Bad Char Resolution: In this tiny script it failed to combine Brick and Brick Braddock into the same char, leaving them as separate chars: https://cineforge.copper-dog.com/brick-steel-full-retired/characters
  - Can the in-app AI actually modify artifacts? I tried to get it to do it and it seemed like it was trying but it didn't actually deprecate the duplicate characters in the end: https://cineforge.copper-dog.com/brick-steel-full-retired/characters

- Finished Script Breakdown and screen went black again (https://cineforge.copper-dog.com/brick-steel-full-retired). This keeps happening. We need to fix this. It did it again after the Deep Breakdown, Shot Planning, Generate Storyboards, Render... Every long-running operation, actually. I can always refresh and it's fine but we can't have these black screen issues.

- When I tried to generate an image of Brick Steel it created an image of him with words and another image below (all in one image) of Brick and Dick with more words: https://cineforge.copper-dog.com/brick-steel-full-retired/characters/brick_braddock
  - When I tried again (generating 4 images) half of the images were of a police officer. Clearly a bad take on "retired detective". We need to do more work on the image generation. We should also check xAI for this: https://cineforge.copper-dog.com/brick-steel-full-retired/characters/brick_braddock
  - When I tried to generate with GPT-image it just spun on Generating and never returned: https://cineforge.copper-dog.com/brick-steel-full-retired/characters/brick_braddock ... Ah not entirely true. When I refreshed the page they were there. Maybe there's something wrong with the code that detects when the generations are complete for GPT-image?
  - I generated images for Dick Steel (twice) and got this error which is odd seeing as there isn't anything contraversial in the prompt as far as I can tell (although it doesn't show the prompt): Generation failed: OpenAI Images API returned HTTP 400: { "error": { "message": "Your request was rejected by the safety system. If you believe this is an error, contact us at help.openai.com and include the request ID req_c523ce0837bf40ae858a813cdbdce185.", "type": "image_generation_user_error", "param": null, "code": "moderation_blocked" } }

- the UI discusses keyframes but there seems to be no way/nowhere to generate them

- Bad final render: https://cineforge.copper-dog.com/brick-steel-full-retired/scenes/scene_001?tab=render
  - Interestingly in my first run through I did the bare minimum to get to the final render and it wasn't bad. Not great, they didn't pause and be depressed for a bit before saying "screw retirement" but it was ok. I had skipped all of the Direction tabs entirely. The SECOND run through I decided to improve it by doing every single Direction tab, and the render was terrible. The two characters looked identical and one came out and they both said screw retirement and cheersed and that was it.
  - I tried to render it again and Google gave a bizarre error seeing as we have no famous people in this: Google video operation missing output URI: {'name': 'models/veo-3.1-generate-preview/operations/hv2x64iecmmr', 'done': True, 'response': {'@type': 'type.googleapis.com/google.ai.generativelanguage.v1beta.PredictLongRunningResponse', 'generateVideoResponse': {'raiMediaFilteredCount': 1, 'raiMediaFilteredReasons': ["Sorry, we can't create videos with real people's names or likenesses. Please remove the celebrity reference and try again."]}}}
  - I did anohter one later after getting the char reference images in place: https://cineforge.copper-dog.com/brick-steel-full-retired/scenes/scene_001?tab=render
    - a) Not sure it used the references images
    - b) The prompt did NOT include exact script lines! For instance it said "Steel delivers the bear joke". What?? We need the EXACT lines;) This is an isolated video gen prompt. You can't hand-wave toward soething it doesn't know about in the actual script (which we didn't give it)



- Test out the new GPT Image 2 that just came out today (20260421)

- Do we have an eval for things like Script Breakdown, Deep Breakdown, Look & Feel, etc (including the component parts)? That would be a perfect thing to climb on. We can always be trying to improve the overall speed and quality of those pipelines.
  - We need a deep scan of all code to figure out where we're missing evals and integraton tests of this nature. We hit constant issues where all tests pass yet the app is quite broken.