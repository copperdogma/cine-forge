Ideas, links, and resources captured for triage. Newest first.
Triaged via `/triage-inbox` skill. Processed items are deleted -- the inbox is a queue, not an archive.

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

- User Edits: We need a way for the user to edit things like Look & Feel or render prompts (with the ability to re-render after their edits). Sometimes the user just wants to tweak some stuff.

- Open/Jump: When building a scene, it has the Scene Tutorial that says "Open Storyboard". when you click it it does nothing you can see because the tab it just changed to is halfway down the page. All you see is it changing to "Jump to Storyboard". This should just be one click: Jump to storyboard which should open and jump to the storyboard. Same for all other tutorial flows like this.
  - FYI the Scene Tutorial should probably be named something else; it's not really a tutorial it's a hint/quick link to what needs to be done next)

- Black Sceen: The ongoing issue of the black screen at the end of certain runs seems to have been patched piecemeal. I no longer see it during Script Breakdown or Deep Breakdown but I get it on some things like rendering Storyboards. I can't tell if its intermittent or only fixed for some long runs. We need a much more in-depth investigation into why this is happening, what the root cause is, and how to fix it.

- Bad Previz: http://localhost:5174/brick-steel-full-retired/scenes/scene_001?tab=previz
  - It was TERRIBLE for this one! Previz is meant to focus on "camera placement, blocking, motion, pacing, and location" but I'm not sure it listened to much of the advice on that. We also need per SHOT previz, don't we? Plus it looks like a Family Guy cartoon which is distracting (exactly what previz should not be).
  - Check best practices for previz. How do they do it in hollywood? What does it look like? How DO they strip away detail so people don't focus on the wrong things? How do they render different people in them?

- do we have evals for all ai prompts? Did we try the different levels of 5.5?

- Table Reads: I'm not sure if any video gen AIs currently take voice references as inputs (like image or video references) but I'm sure they will, so we should develop a "table read" feature where we can supply a voice file that we can clone or we can "audition" some, likely generated by ElevenLabs, that we can hear read the lines so we can figure out which voice we'd want. I assume eventually video gen will take these as input but they'd be useful to IRL creators who are making radio plays, just trying to find the ideal voice to send to a casting director, etc.

- Update Ideal: I think we'd want a form of "casting" even with zero tech limits. A creator would have an image in their mind of what a character should look like so they can shape the character. The original one would be created based on any descirptions in the script, but then the creator could say "actually let's make them Asian. Heavier. With a moustache. And some tattoos. Okay nice now read your lines from scene one. [listen to virtual actor read lines] Maybe a deeper voice, more gravelly, like a smoker. And less of an accent." etc.

- Location References: It didn't do a great job generating location refereneces for a few reasons [http://localhost:5174/brick-steel-full-retired/locations/brick_s_patio]:
  - I think we only see his patio during the day but it generated it as night.
  - It's too close-cropped. It provides a narrow field of view which will make continuity difficult later if the camera strays from that narrow view. We need to see an image very representative of the WHOLE location.

- Multiple References: We may need a way, once we lock in the image, to create different views of a person/prop/location to use as genai video reference. For instance if we generate an image of a backyard and we only give one reference image, what happens when the camera turns around to pan the entire yard? Maybe locations can get top-down, elevation, various angles, etc, giving the gen ai (or IRL designers) all the detail they might need. Same for people and props.
  - But how to feed these in to gen AI? This might be a now-vs-future compromise, but we need to see what they can take. I doubt we can give 100 reference images per video generated, so we'd have to curate. Can we combine multiple views into a single reference images? Triage them according to what's most important for the final shot POVs?
