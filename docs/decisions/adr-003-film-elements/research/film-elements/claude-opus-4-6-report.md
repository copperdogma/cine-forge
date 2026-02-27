---
type: research-report
topic: film-elements
canonical-model-name: claude-opus-4-6
research-mode: standard
collected: '2026-02-27T06:28:48.460727+00:00'
---

# The creative gap between screenplay and finished film

**A screenplay specifies roughly 15–20% of the creative decisions in a finished film.** The remaining 80%+ — encompassing over 100 distinct creative elements spanning visual design, sound, performance, pacing, and continuity — must be invented, negotiated, and executed by a production team. For an AI filmmaking tool like CineForge, the central design challenge is not generating video but organizing the creative control surface so that both beginners and filmmakers can express intent across these 100+ elements without being overwhelmed. This report maps every element, analyzes how current tools and professionals organize them, studies how non-filmmakers naturally describe creative intent, charts the dependencies between elements, and evaluates four candidate groupings against the evidence. **Option D (By Creative Concern) emerges as the strongest foundation**, but the research suggests a hybrid that layers emotional intent on top of creative concern groups and scope levels underneath.

---

## 1. Every creative decision between script and screen

The complete inventory below catalogs **107 distinct creative elements** organized into five domains. For each element, three dimensions are noted: the scope at which it operates, how likely a non-filmmaker is to consciously care about it, and what happens when AI handles it without human guidance.

### Pre-production decisions (project-wide)

These choices establish the visual and sonic DNA of the entire film. They are set early and cascade through every downstream decision.

**Visual style and world-building** includes overall visual approach (naturalistic vs. stylized vs. hyperreal), color palette with per-act arcs, aspect ratio, film stock or sensor emulation, lens philosophy (anamorphic vs. spherical, vintage vs. modern primes), world-building details (architecture, technology level, cultural signifiers), time-period authenticity, and visual motifs (recurring shapes, symbols, and colors carrying narrative meaning). Most of these operate at project-wide scope with per-act or per-scene variations. Non-filmmakers rarely name these elements explicitly but respond powerfully to them — **color palette** in particular triggers strong subconscious reactions (the teal-and-orange "cinematic" default is AI's most common visual cliché). When left to AI, the most dangerous defaults are world-building inconsistencies (anachronistic technology, generic "fantasy/sci-fi" aesthetics) and the absence of visual motifs, which strips the film of visual storytelling depth.

**Character design** covers casting appearance and voice, costume design (silhouette, fabric, color, evolution over story time), hair and makeup design, character-specific color palettes (e.g., Breaking Bad's Walter White shifting from khaki to black), hero prop design, and character physicality (gait, posture, gestural vocabulary). These operate per-character with project-wide consistency requirements. Non-filmmakers care deeply about how characters look — **character visual consistency is the single element audiences notice most** when it fails, and it remains AI's most persistent weakness. Current AI tools achieve 50–70% consistency across shots with reference-image conditioning (Runway Gen-4 leads at ~70%).

**Location and set design** encompasses location selection, set design and dressing (furniture, objects, wall colors, clutter level), architectural style, set color coordination with the film's palette, practical lighting sources built into sets, and set weathering/aging. These operate per-scene but must maintain project-wide coherence. AI's default produces sets that look "unlived-in" — a catalog-furniture aesthetic without the narrative specificity that environmental storytelling requires.

**Sound style** — the overarching sonic approach (naturalistic, heightened, surreal, minimal) — operates project-wide and is rarely articulated by non-filmmakers, yet its absence is felt immediately. AI defaults to "clean, full" sound without sonic character.

### Per-scene creative interpretation

Each scene requires a fresh set of creative decisions that serve the scene's emotional function while maintaining project-wide coherence.

**Lighting** involves key light placement, lighting ratio (high-key vs. low-key), color temperature, practical vs. motivated sources, shadow design, light source motivation, and lighting transitions within scenes. These decisions have **low conscious awareness among non-filmmakers** but profoundly shape mood. AI's most common failure is flat, even lighting — the absence of intentional shadow design removes dramatic tension. Lighting is the last element locked before shooting because it must respond to blocking, sets, and costumes — a dependency that AI tools currently ignore entirely.

**Camera work and composition** covers camera movement style (handheld, Steadicam, locked-off, crane, drone), composition approach (rule of thirds, symmetry, leading lines, depth layers), blocking (actor positions relative to each other and the camera), shot sizes, camera angles, and axis management (the 180-degree rule). **Blocking is the element where AI fails most consequentially** — it cannot encode power dynamics, spatial storytelling, or the subtext of physical proximity into character staging. Non-filmmakers feel these dynamics without naming them; a character framed alone in negative space reads as "isolated" regardless of whether the viewer knows the term.

**Pacing and transitions** — scene tempo, transition type (hard cut, dissolve, match cut), and scene duration — operate per-scene but form the macro rhythm across the entire film. Non-filmmakers are highly aware of pacing ("it dragged" or "it was relentless") even if they cannot diagnose why.

**Sound design per-scene** includes ambient sound/room tone, diegetic sound effects, music cue entry and exit points, sound perspective (matching shot size), and the deliberate use of silence. **Silence is the most commonly missed element in AI generation** — AI fills every moment with sound, losing one of cinema's most powerful tools.

**Performance direction** encompasses emotional intensity and subtext, micro-expressions, physical performance (body language, gestures, proximity), and vocal delivery (tone, pace, breath, hesitation). Non-filmmakers judge performance quality first and most harshly. AI-generated performances lack the internal contradiction and subtext that make human performances compelling — they are "on the nose," expressing exactly one emotion at a time.

**Atmosphere and environment** — weather, time of day, seasonal cues, and environmental storytelling details — complete the per-scene picture. AI defaults to clean, bright conditions unless explicitly instructed otherwise.

### Per-shot technical decisions

At the granular level, each shot requires decisions about framing (headroom, lead room, nose room), lens and focal length (14mm–300mm+), depth of field, focus pulls, camera movement within the shot, shot duration, camera height, lens characteristics (flare, distortion, bokeh shape), shot size classification, and compositional framing through architectural elements (doorways, windows, mirrors). Most of these have low conscious awareness among non-filmmakers, but wrong choices produce a visceral "something feels off" response. **AI's default is uniformity** — same focal length, same camera height, same depth of field — which produces technically acceptable but rhythmically dead visual language.

### Post-production decisions

Color correction (technical exposure/white balance matching), color grading (creative look development), edit pacing and rhythm, shot selection (choosing the best take), sound mixing (dialogue/music/effects balance), music scoring (original themes, orchestration, leitmotifs), Foley (footsteps, clothing, object interaction sounds), ADR, sound effects layering, VFX compositing, transition effects, title and credit design, final aspect ratio, and audio mastering. **Edit pacing and shot selection are the two post-production elements with the highest audience impact** and the hardest for AI to automate, because both require emotional judgment about what serves the story moment.

### Cross-cutting concerns

These are the elements that span the entire project and require memory across scenes: costume continuity, injury continuity, prop state continuity, location state continuity, character visual consistency, character behavioral consistency, visual motif tracking, sound motifs and leitmotifs, narrative rhythm across acts, color arc across the film, eyeline continuity, screen direction, and emotional continuity across cuts. **These are precisely the elements where AI fails most critically**, because current models generate each shot or scene independently without persistent state. The absence of unified intentionality — the sense that every creative decision serves the same narrative purpose — is what makes AI-generated film feel "soulless."

---

## 2. How current AI tools organize creative control

The 2025–2026 AI filmmaking tool landscape reveals five distinct organizational paradigms, each with characteristic strengths and failure modes.

### Pipeline-based organization: LTX Studio

LTX Studio follows a **linear production pipeline** — Script → Storyboard → Scene Editor → Timeline — that mirrors traditional filmmaking phases. Users control persistent character profiles (age, ethnicity, wardrobe, facial details), advanced camera keyframes (crane lifts, orbital movements, tracking shots), style references via image upload, lighting mood controls (golden hour, harsh noon, moody night), weather effects, and audio layers. The interface surfaces contextually relevant tools at each pipeline stage rather than showing everything simultaneously.

Users praise LTX Studio's all-in-one approach ("No other tool allows you to go from idea to video that fast, with that amount of control") and its camera control system, which reviewers describe as "more advanced than any competing AI video tool." Complaints center on character consistency breaking down in complex scenes, a steep learning curve for advanced features hidden in nested menus, and a computing-seconds pricing model that makes costs unpredictable. The pipeline approach works well for structured projects but struggles with iterative refinement — changing a project-wide visual decision requires propagating changes through multiple pipeline stages.

### Reference-image conditioning: Runway Gen-4 and Higgsfield

Runway Gen-4 organizes around three pillars: generation models (Gen-4, Gen-4 Turbo), performance tools (Act-One/Act-Two for webcam-to-character transfer), and editing tools (Aleph for in-video editing). Creative controls include Director Mode with precise camera paths, motion intensity adjustments, keyframing, and visual style categories (live-action, stop-motion, smooth animation). **Character consistency through reference-image conditioning** is Runway's signature strength, achieving ~70% consistency across shots in independent testing. Act-One and Act-Two solve the "dead face problem" by transferring real human micro-expressions onto AI characters.

Higgsfield Cinema Studio 2.0 pushes this paradigm further with **deterministic optical physics** — users select from 6 simulated camera bodies, 11 optical lenses with specific focal lengths, aperture controls with specific f-stops, and 15+ composable camera movements. Its "Hero Frame" workflow (generate and approve a static frame, then generate video that inherits its exact visual properties) gives filmmakers the most granular control available in any AI tool.

Users praise the director-level intentionality ("You aren't just rolling dice; you are crafting a scene") but complain about steep learning curves, credit burn rates (budget 3–5 tries per usable clip on Runway), **no native audio** on Runway (described as "deafening" silence), and maximum 16-second clip duration.

### Prompt-primary with social features: Sora 2

Sora 2 uses text prompts as the primary creative input, supplemented by a storyboard editor (frame-by-frame control by timestamp), character cameos (created from video recordings), and remix/blend/loop tools. It operates across a mobile app (social-first, TikTok-like feed) and web interface (more production-oriented with storyboard mode). **Native audio generation** (dialogue, sound effects, ambient sound, music) is a significant differentiator.

Sora's "world state" persistence — maintaining spatial relationships and environmental logic across shots — earns high marks for multi-shot narrative consistency. However, users criticize limited creative controls beyond prompting ("limited control compared to Runway"), the social-first design philosophy (criticized as "SlopTok"), strict content moderation blocking legitimate creative work, and geographic restrictions (available in only ~7 countries).

### Filmmaking workspace with modular ingredients: Google Flow/Veo 3

Google Flow organizes around a project workspace with distinct functional areas: prompt composer, ingredients panel (reusable characters, objects, styles), camera controls, scenebuilder (timeline-like editing), and a discovery feed (Flow TV). Veo 3 generates synchronized audio natively, and the "Ingredients to Video" feature lets users combine modular reference elements into scenes.

Veo 3 leads benchmarks on prompt adherence, physics simulation, and temporal consistency (scored 8.9/10). Users praise native audio as "the end of the silent era for AI video." Complaints focus on the **$250/month Ultra tier** required for Veo 3 access, 8-second clip limits, and the fact that Ingredients to Video auto-downgrades to Veo 2 despite UI selection — a UX trust issue.

### Multi-shot narrative generation: Kling 3.0

Kling 3.0's distinctive feature is **multi-shot generation** — up to 6 shots per generation, each with its own prompt and independently assigned duration (3–15 seconds). The model understands cinematic camera language (profile shots, tracking shots, shot-reverse-shot), supports native 5-language dialogue with emotion descriptors, and offers start-and-end-frame control. Character identity locks across shots within a generation.

Professional filmmakers note Kling 3.0 produces the closest thing to a "client-ready rough cut," and its multi-shot storyboarding is called a "game-changer." Complaints center on hand distortions, minor motion glitches, and degraded quality for complex simultaneous movements.

### Pipeline production tools: Saga and Pika

Saga uniquely combines AI scriptwriting, character development, beat sheet structuring, storyboard generation, pre-visualization, and a full NLE video editor in a single platform. It organizes controls by **production phase** (plot → character → acts → script → storyboard → previz → edit), not by technical parameter — the closest any AI tool comes to mirroring how filmmakers actually think about creative decisions. Built by professional Hollywood writers and film school professors, Saga emphasizes industry-authentic formatting and workflow.

Pika takes a different approach with "Scene Ingredients" — modular elements (falling snow, lens flare, film grain) with intensity sliders that can be layered and remixed. Pikaffects (inflate, melt, explode, cake-ify) target social media creators. Pika's UI is praised as the most accessible ("if you can type a sentence, you can make a video") but quality inconsistency is the dominant complaint: "results are a complete lottery."

### Cross-tool patterns and gaps

Across all tools, five consistent user complaints emerge: (1) credit/pricing confusion — every tool uses a different unit (computing seconds, credits, AI credits) making cost prediction impossible; (2) **short clip duration** (8–16 seconds per generation) as a universal constraint; (3) character consistency fragility; (4) a recognizable "AI aesthetic" that marks outputs as artificial; and (5) a gap between marketing claims ("create in seconds") and reality (**15–35 minutes per usable clip**). No current tool adequately addresses cross-cutting concerns — continuity, motif tracking, or narrative rhythm across a full project.

---

## 3. How professional filmmakers organize creative decisions

Professional film production operates with a **dual organizational system** that is directly relevant to CineForge's design challenge. Logistical documents organize by department; creative vision documents organize by intent.

### The departmental logistics layer

**Breakdown sheets** use 15–22 color-coded categories to tag every production element per scene: cast (red), extras (yellow), stunts (orange), special effects (green), sound effects (blue), props (purple/violet), vehicles and animals (pink), costumes (white), hair and makeup (asterisk), music (brown), set dressing (gray), and additional categories for greenery, special equipment, security, and VFX. Scene headers are color-coded by shooting condition (yellow = day exterior, white = day interior, green = night interior, blue = night exterior). Page counts are measured in eighths of a page. This system is purely logistical — it answers "what do we need to have on set?" not "what should this feel like?"

**Shot lists** document per-shot decisions as spreadsheet columns: scene number, shot number, setup number, shot description, shot size (WS/MS/CU/ECU/OTS), camera angle (eye-level/high/low/Dutch), camera movement (static/pan/tilt/dolly/tracking/crane/handheld/Steadicam), camera equipment, lens/focal length, subject, audio method, priority rating, and notes for lighting, blocking, and VFX. Advanced shot lists add reference images, frame rate, and best-take timecodes filled during production.

**Call sheets** organize by department (Camera, Electric, Grip, Art, Wardrobe, Hair/Makeup, Sound, Transportation) with per-person call times, scene-by-scene shooting schedules, location addresses, sunrise/sunset times, weather forecasts, and meal schedules governed by union rules.

### The creative vision layer

**Director's treatments** are 5–20 page visual pitch documents organized by creative intent, not department: personal connection to the material → logline → story synopsis → character descriptions → visual style with reference images → tone and mood → color palette → wardrobe → production design → editing and pacing → sound design and music → technical approach. The best treatments are "heavily visual" — interspersed with film stills, photography, and color swatches. They are organized as **story → look → feel → execution**, establishing the emotional and aesthetic target before specifying any technical means.

**Lookbooks and mood boards** serve as the cross-departmental bridge. When a costume designer and a lighting director reference the same mood board, they align tones and textures without needing to translate between departmental vocabularies. Mood boards are organized by creative intent (color palette, lighting mood, character quality, location atmosphere) rather than by department, though department-specific boards can be created as derivatives.

**Sound design documents** center on the spotting session — a collaborative viewing where the director and audio team mark every sonic moment. Spotting sheets track timecodes, sound element types (ambience, Foley, music, silence, effects, dialogue), character references, and critically, the director's emotional intent for each cue. The key discussion topics are overall sonic aesthetic, moments requiring designed sound, and "what feelings to convey to the audience."

### How directors actually communicate vision

The research reveals a consistent pattern: **directors organize by holistic creative concepts first, then translate to departments**. A director establishes a unified vision around tone, mood, theme, color, rhythm, and character focus. This vision is communicated to all department heads simultaneously in group pre-production meetings, using treatments and mood boards as shared reference documents. Department heads then translate the unified vision into their domain-specific execution. Individual meetings follow to refine details.

The critical insight is that **there is no single industry-standard grouping of creative elements that cuts across departments thematically.** The operational structure is firmly departmental. But the creative communication structure is organized by intent — mood, tone, character, visual world — and shared across all departments. The director's vision functions as the unifying force, and mood boards are the primary tool for achieving cross-departmental alignment.

---

## 4. How non-filmmakers naturally describe creative intent

Research across consumer video tools, film education, social media platforms, creative briefs, and academic studies reveals that non-filmmakers describe creative intent through **four overlapping modes** in a consistent priority order.

### Emotional and mood terms dominate

The primary mode is emotional: "I want it to feel tense / warm / chaotic / dreamy / epic / cozy / unsettling." Studies by Tarvainen et al. (2015, published in *Psychology of Aesthetics, Creativity, and the Arts*) found that audiences naturally speak of a film's "atmosphere," "tone," or "mood," and that low-level perceptual features like brightness alone strongly predicted mood valence ratings. Non-experts respond to and can rate aesthetic properties even when they cannot name the specific techniques producing them. The vocabulary is rich — moody, dramatic, heartwarming, eerie, uplifting, intimate, raw, powerful, "emotional rollercoaster," "gut punch." Every consumer tool and creative brief format places tone and mood at the center of creative specification.

### Reference and comparison terms are the most efficient

The secondary mode is comparative: "Like a Wes Anderson movie," "like Blade Runner," "like a nature documentary," "cottagecore aesthetic," "dark academia vibes." Film names, director names, aesthetic subculture names, and social media trend names function as **compressed creative intent packages** — encoding color, mood, composition, pacing, and sound in a single term. Gen-Z and social media culture have created a rich taxonomy of aesthetic subcultures (cottagecore, dark academia, clean girl, Y2K, cyberpunk) that serve as highly efficient creative shorthand. Creative briefs rely heavily on mood boards and example videos for the same reason: showing is faster than describing.

### Sensory and perceptual terms bridge emotion to technique

The tertiary mode is concrete and sensory: warm tones, muted colors, bright and saturated, dark, glowy, golden hour, grainy, crisp, slow motion, shaky camera, quiet, echo-y. These terms sit at the intersection of emotional intent and technical execution — a non-filmmaker can say "warm" and "glowy" without knowing to specify "increase color temperature to 5500K and add diffusion." Consumer tools consistently organize their options using this vocabulary: filter names like "Warm," "Cool," "Vintage," "Dramatic" bridge the gap between what users feel and what the software adjusts.

### Functional and outcome terms provide context

The quaternary mode is purpose-driven: "For Instagram Reels," "for a wedding," "needs to look professional," "something teens would share." This mode defines constraints and audience rather than aesthetic qualities.

### What consumer tools teach us

Consumer video tools use a three-tier vocabulary hierarchy: broad intuitive buckets (Filters, Effects, Music), mood/genre subcategories (Vintage, Dramatic, Fun), and individually named items (Golden Hour, Film Noir, Dreamy). **None of these tools ask users to specify ISO, f-stop, frame rate, or color temperature.** TikTok's effect taxonomy mixes subject context (Portrait, Food), social function (Trending, Interactive), and aesthetic quality (Vibe, Beauty) — reflecting how non-experts actually think, without separating technical function from social context from aesthetic outcome.

The dominant finding: **templates beat parameters.** Users strongly prefer choosing from curated starting points and adjusting, rather than building from blank canvases with sliders. AI prompting behavior confirms this — when forced to describe scenes in words, users naturally organize as WHO/WHAT (subject) → DOING WHAT (action) → WHERE (setting) → HOW IT FEELS (mood/aesthetic).

---

## 5. Element interactions demand grouped specification

The dependency map reveals that creative elements do not operate independently — they form tightly coupled clusters where misalignment between any two elements creates perceptible dissonance.

### The lighting-color-costume triangle

Lighting, color palette, and costume design form an inseparable triad. Production design introduces color into the physical space. Lighting determines how those colors are perceived — warm light shifts blues toward green, cool light shifts reds toward purple. Color grading refines the result in post. As cinematographer Vittorio Storaro demonstrated, these three form a chain: production design → lighting → color grading. When misaligned, carefully chosen warm costume tones can read as jaundiced under wrong-temperature lighting, and post-production grading cannot fully rescue fundamental clashes (e.g., a magenta costume under green light produces irrecoverable muddy color). **These elements must be specified as a group.**

### The pacing-camera-editing cluster

Pacing is constructed from shot duration + cut frequency + camera movement speed + content density + music tempo. These are functionally inseparable. Fast cuts with slow camera movement sends contradictory signals (tense editing, relaxed movement). Slow pacing with rapid movement induces nausea. Music tempo that fights edit rhythm feels "off" without audiences knowing why. An action scene cut slowly feels lethargic; a dramatic conversation cut quickly feels shallow. **Rhythm elements must be specified together.**

### The blocking-camera-performance triangle

Blocking, camera framing, and performance direction converge in a single creative act. A character's isolation in frame only works if they're blocked away from others. Power dynamics expressed through vertical positioning only read if the camera captures the height differential. Performance intensity determines appropriate shot size — a subtle micro-expression needs a close-up, while a grand gesture needs a wider shot. As Sony Cine's Bernstein warns: "Nothing about the position of the camera or the position of actors in a scene should be arbitrary." **These three must be choreographed simultaneously.**

### The ambient-music frequency allocation

Ambient sound and music occupy the same auditory space and must be frequency-allocated. If music has deep bass, ambient sounds should focus on mid/high frequencies. Removing ambient for music focus or removing music for ambient focus are both powerful creative choices that require coordination. Music and ambient sound competing for the same frequency range produces a muddy, fatiguing mix. **Sound elements must be balanced as a system.**

### Genre and mood as organizing principles

Genre shapes expectations for every other element — lighting conventions (horror = low-key; comedy = high-key), color palettes (horror = desaturated, cold; musical = saturated primaries), camera conventions (horror = tight POV; epic = sweeping crane), sound conventions (horror = silence and stingers; action = dense layers), and performance style (comedy = heightened; drama = naturalistic). Mood functions similarly but at a finer grain, operating per-scene rather than project-wide. **Genre and mood should be specified first because they constrain all downstream choices.**

The dependency hierarchy flows: Genre/Tone → Story → Visual Style + Color + Sound Style → Character Design ↔ Set Design → Blocking → Lighting → Camera → Performance Capture → Editing → Color Grading → Sound Mix → Finished Film. This cascade means that **elements should be specified top-down**, and changes at higher levels should automatically propagate constraints to lower levels.

---

## 6. Evaluating four grouping models against the evidence

Each candidate grouping is evaluated against four criteria derived from the research: intuitiveness for non-filmmakers, usefulness for filmmakers, support for iterative refinement (especially cross-cutting changes like "make this darker and tenser"), and mapping to AI generation parameters.

### Option A: by professional role

**Editorial** (pacing, transitions, coverage) | **Visual** (lighting, color, camera, costume, set) | **Sound** (ambient, music, effects, silence) | **Performance** (emotion, delivery, blocking)

This grouping mirrors the departmental structure of real film crews. It is immediately legible to professional filmmakers, maps cleanly to department-head conversations, and aligns with how operational production documents (breakdown sheets, call sheets) are organized.

However, the research shows directors communicate vision by *intent*, not by department. Non-filmmakers do not think in professional roles — they think in emotion and perception. "Make this scene darker and tenser" requires changes in Visual (lighting, color), Sound (ambient, music), Performance (intensity), and Editorial (pacing) — spanning all four groups with no clear entry point. The grouping also buries the critical blocking-camera-performance triangle across two groups (Visual and Performance), breaking the tight coupling the dependency analysis demands. **Intuitive for filmmakers; unintuitive for everyone else. Poor for cross-cutting intent.**

### Option B: by perception

**What You See** (lighting, color, camera, costume, set, blocking) | **What You Hear** (ambient, music, effects, dialogue delivery) | **How It Flows** (pacing, transitions, coverage) | **What Characters Feel** (emotion, motivation, subtext)

This grouping has strong sensory logic and maps to the tertiary mode of non-filmmaker description (sensory/perceptual terms). The see/hear split is immediately intuitive. Research on film education confirms that "what appears in the frame" (mise-en-scène) is the first concept taught to beginners.

The weaknesses are significant: "How It Flows" is abstract and hard for non-filmmakers to engage with independently. "What Characters Feel" mixes observable performance (body language, vocal delivery) with unobservable interiority (motivation, subtext) — a confusing blend. Blocking appears in "What You See" but is inseparable from performance direction in "What Characters Feel." "Make this darker and tenser" still spans three groups (See, Hear, Flows). The perception framing also **does not map well to AI generation parameters**, which are organized around technical controls (camera, lighting, style) rather than perceptual categories. **Intuitive entry point; breaks down at element level.**

### Option C: by scope

**Project-Wide** (visual style, sound style, character design) | **Per-Scene** (lighting, camera, pacing, ambient, blocking) | **Per-Shot** (framing, angle, lens, movement)

This grouping has elegant engineering logic. It mirrors the dependency cascade (higher-scope decisions constrain lower-scope ones), supports top-down iterative refinement naturally, and maps well to AI generation architecture (project-level embeddings, scene-level prompts, shot-level parameters). It is the implicit architecture of tools like LTX Studio (Script → Storyboard → Scene Editor → Timeline).

The fatal weakness: **non-filmmakers do not think in scope levels.** "Make this darker" requires changes at project level (palette), scene level (lighting), and shot level (exposure) — the user must distribute a single creative intent across three layers. Scope is an implementation concern, not a creative-thinking framework. Filmmakers think about scope implicitly but describe intent holistically. The research on director communication confirms that creative vision is articulated as unified concepts (mood, tone, character), not as scope-stratified parameters. **Excellent for implementation architecture; poor as a user-facing organizing principle.**

### Option D: by creative concern

**Look & Feel** (lighting, color, composition, camera, costume, set, motifs) | **Sound & Music** (ambient, effects, music, silence, sound transitions) | **Rhythm & Flow** (pacing, transitions, coverage, scene function) | **Character & Performance** (emotion, motivation, subtext, blocking, delivery, voice) | **Story World** (character design, location design, prop design, continuity)

This grouping most closely matches how directors actually communicate vision — organizing by creative intent rather than department or technical parameter. "Make this darker and tenser" primarily hits Look & Feel + Sound & Music (just two groups rather than three or four), with secondary implications for Rhythm & Flow. The blocking-camera-performance coupling is better preserved: blocking sits in Character & Performance alongside the performance elements it serves, while camera sits in Look & Feel alongside the visual elements it captures.

Story World as a separate group elegantly isolates the cross-cutting continuity concerns that are AI's biggest weakness, making them visible and manageable rather than scattered across other categories. Each group has a coherent creative identity that both beginners and experts can reason about.

Weaknesses: "Rhythm & Flow" remains abstract for beginners (the same problem as Option B's "How It Flows"). Some boundary ambiguity exists — camera movement could belong in Rhythm & Flow (it affects pacing) or Look & Feel (it affects visual composition). Blocking straddles Character & Performance and Look & Feel. But these overlaps reflect genuine creative reality rather than taxonomic failure. **Most aligned with how creative professionals think; reasonable for beginners; best isolation of AI's continuity problem.**

### The research suggests a fifth option

The evidence points toward a hybrid model not captured by any single option. The four modes of non-filmmaker description (emotion → reference → sensory → functional) suggest the primary interface should be **mood/intent-driven**, with creative concern groups as a secondary detail layer and scope as the implementation architecture underneath.

**Option E: Intent-first with creative concern detail**

The primary interaction layer would be emotional and referential: "How should this feel?" with mood descriptors (tense, warm, chaotic, dreamy), reference selections ("like Blade Runner," "documentary style"), and aesthetic presets ("golden hour," "noir," "cottagecore"). This maps to the dominant way non-filmmakers think and matches the "vibe" paradigm emerging in social media culture.

The secondary layer exposes Option D's creative concern groups for users who want fine-grained control: Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World. A filmmaker can drill into Look & Feel to specify anamorphic lenses and motivated lighting; a beginner can stay at the mood layer and let the system translate intent into technical decisions.

The implementation layer uses Option C's scope architecture: project-wide settings cascade into per-scene parameters into per-shot specifications. This is invisible to beginners, available to experts, and maps directly to how AI models accept parameters (style embeddings at project level, prompt conditioning at scene level, control signals at shot level).

This three-layer architecture — intent on top, creative concern in the middle, scope at the bottom — resolves the core tension: **beginners need emotion-first access, filmmakers need concern-based control, and AI models need scope-structured parameters.** A mood like "tense" can propagate through Look & Feel (high-contrast lighting, cool desaturated palette, tight framing), Sound & Music (sparse ambient, low-frequency score, silence before stingers), Rhythm & Flow (shorter shots accelerating, restricted coverage), and Character & Performance (restrained physicality, tight blocking), while each of these downstream implications remains individually adjustable.

---

## Recommended approach and alternatives

### Primary recommendation: Option D (By Creative Concern) with an intent layer and scope substrate

**Pick this when:** Building CineForge as a tool that must serve both non-filmmakers (the initial majority of users) and filmmakers (the aspirational user base that validates the tool's credibility). The intent layer provides the accessible entry point that consumer tool UX research demands. The creative concern groups provide the organizing principle that matches how directors actually think. The scope substrate provides the technical architecture that AI generation models require.

The five creative concern groups — **Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World** — should be the primary navigation structure, with each group containing both scope-specific controls (project-wide defaults, per-scene overrides, per-shot adjustments) and mood-to-parameter translation (selecting "tense" auto-adjusts relevant parameters within the group). Story World should prominently surface continuity management, making AI's biggest weakness visible and controllable.

### Runner-up: Option C (By Scope) as implementation-only architecture

**Pick this instead when:** The primary audience is technical users comfortable with hierarchical parameter systems, or when the tool's UX can layer creative concern groups on top of a scope-based data model without exposing scope as the primary navigation. Option C is the correct *engineering* architecture even if it is the wrong *user-facing* organization. Every AI filmmaking tool will need project/scene/shot scope internally; the question is whether to expose it.

### Avoid: Option A (By Professional Role) as user-facing organization

Option A is tempting because it mirrors real film industry structure, lending apparent legitimacy. But the research shows that even within the film industry, creative communication does not follow departmental lines — directors communicate by intent and use mood boards as cross-departmental bridges. For non-filmmakers, departmental thinking is completely alien. Pika's "Scene Ingredients" approach (modular, mixable, outcome-named) dramatically outperforms departmental organization for casual users, and Saga's phase-based organization outperforms it for structured projects. Building CineForge around professional roles would optimize for a mental model that neither beginners nor experienced directors actually use for creative thinking.

### Key design implications from the research

The dependency analysis demands that tightly coupled elements be presented together or have explicit linking. The lighting-color-costume triangle should be visually and functionally connected within Look & Feel. The pacing-camera-editing cluster should be connected within Rhythm & Flow. The blocking-camera-performance triangle requires a cross-group bridge between Character & Performance and Look & Feel — perhaps a "direct this moment" mode that surfaces relevant controls from both groups simultaneously.

The "make this darker and tenser" test is the acid test for any grouping. In the recommended architecture, this intent propagates through Look & Feel (lighting down, contrast up, palette cooled) and Sound & Music (ambience thinned, music tension increased) as primary targets, with secondary adjustments in Rhythm & Flow (shot duration shortened) and Character & Performance (blocking tightened). The intent layer handles this propagation automatically; the creative concern layer lets users adjust each propagated change independently.

Finally, the research on consumer tools delivers one finding that should shape CineForge's entire UX philosophy: **templates beat parameters, references beat descriptions, and "make it feel like this" beats "set this to that."** The most successful creative tools — from Instagram filters to TikTok effects to LTX Studio's style references — start with curated starting points and let users adjust, rather than presenting blank parameter spaces. CineForge should invest heavily in a library of mood presets, style references, and "vibe" packages that set coherent defaults across all five creative concern groups, giving users a starting point that already embodies unified creative intentionality — the very quality that AI struggles most to produce on its own.

---

## Conclusion

The 107+ creative elements between screenplay and finished film cluster into five natural creative concerns — Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, and Story World — that match how directors actually communicate vision. Non-filmmakers access these through emotional and referential vocabulary ("tense," "like Blade Runner"), not through technical parameters or departmental categories. Current AI tools are converging on structured scene-level direction but none adequately address the cross-cutting concerns (continuity, motifs, narrative rhythm) that make a film feel intentional rather than randomly generated. **The winning architecture layers mood-first intent on top of creative concern groups on top of scope-based parameters** — giving beginners emotional access, filmmakers granular control, and AI models structured inputs, all within a single coherent system. The most consequential design decision is not which grouping to choose but whether to make unified creative intentionality — the quality most absent from AI output — the central organizing principle of the tool.