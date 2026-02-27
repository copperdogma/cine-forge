---
type: research-prompt
topic: "film-elements"
created: "2026-02-26"
---

# Research Prompt: Film Elements — The Creative Gap Between Screenplay and Film

## Context

We're building CineForge, an AI film production tool that takes a screenplay and helps users create a complete film through iterative creative conversation. The AI generates video, sound, storyboards, and other production artifacts.

A screenplay provides: dialogue, action descriptions, scene headings (location + time of day), character names and presence, and some stage directions.

A finished film requires hundreds of additional creative decisions that the screenplay doesn't specify: lighting, camera work, color palette, costume, sound design, music, editing rhythm, performance nuance, blocking, set dressing, visual effects, and more.

Our core design principle: **the AI will make ALL of these decisions regardless** — it has to, in order to generate video. The question is whether the user has specified each element intentionally (high quality, matches their vision) or left it to AI improvisation (generic, may not match their vision). Our UI shows this as a per-element readiness indicator: red (AI guesses everything), yellow (some guidance exists), green (fully specified).

We currently organize these elements by **professional film role** (Editorial Architect, Visual Architect, Sound Designer, Actor Agents — each produces a "direction" artifact). But we suspect this is the wrong organizing principle for users. Most users don't think in terms of film crew departments. They think "I want this scene darker and more tense" — which is simultaneously visual, sonic, editorial, and performative.

We need to figure out:
1. The complete inventory of creative elements
2. The right way to group them for users
3. How users should interact with them

## What I Need

### 1. Complete Element Inventory

Enumerate every creative decision that must be made between a screenplay and a finished film. Be exhaustive. Include:

- **Pre-production decisions:** Character visual design, location design, costume, prop design, color palette, visual style, sound style
- **Per-scene creative interpretation:** Lighting, camera work, composition, pacing, transitions, ambient sound, music, blocking, performance direction, set dressing
- **Per-shot technical decisions:** Framing, camera angle, lens/focal length, camera movement, shot duration, depth of field
- **Post-production decisions:** Color grading, sound mixing, music scoring, edit pacing, transition effects, titles/credits, aspect ratio, VFX
- **Cross-cutting concerns:** Continuity (costume, injury, prop, location state across scenes), character consistency (visual and behavioral), visual motifs, sound motifs, narrative rhythm across acts

For each element, note:
- What scope does it operate at? (Project-wide, per-act, per-scene, per-shot, per-character)
- How likely is a non-filmmaker to care about or understand this element?
- What happens if this element is left entirely to AI? (Barely noticeable? Obviously generic? Actively bad?)

### 2. How Existing AI Film/Video Tools Organize These Elements

Research these specific tools and how they expose creative control to users:

- **LTX Studio** (Lightricks) — Script → storyboard → scene editor → timeline. What elements can users control? How are they organized?
- **Runway Gen-4** — Reference images for character consistency. What creative controls exist beyond prompting?
- **Kling 3.0** — Multi-shot generation (up to 6 cuts per generation). What scene-level controls does it offer?
- **Pika** — What creative parameters are exposed?
- **Sora** (OpenAI) — What creative controls exist?
- **Saga** — Script + storyboard + NLE. How does it structure creative decisions?
- **Veo 3** (Google) — What creative parameters are exposed?
- **Any other significant AI film/video tools released in 2025-2026**

For each tool:
- What elements can users control?
- How are elements grouped/organized in the UI?
- What do users praise about the creative control model?
- What do users complain about? (Too little control? Wrong abstractions? Missing elements?)

### 3. How Real Filmmakers Organize Creative Decisions

Research how professional film pre-production documents organize creative elements:

- **Breakdown sheets** — What categories do they use?
- **Lookbooks / mood boards** — How do directors communicate visual vision?
- **Shot lists** — What per-shot information is standard?
- **Sound design documents** — How do sound designers communicate intent?
- **Call sheets** — What per-scene information is included?
- **Director's notes / director's treatment** — How do directors describe their overall vision?

Key question: When a director communicates their vision to department heads, do they organize by department (visual, sound, performance) or by creative intent (mood, rhythm, character focus)? Is there an industry-standard grouping?

### 4. User Mental Models for Creative Description

Research how non-filmmakers naturally describe what they want in a scene:

- **UX research from video editing tools** (iMovie, CapCut, Canva Video, etc.) — How do casual users describe creative intent?
- **Film education** — How do introductory filmmaking courses organize creative concepts for beginners?
- **Consumer video tools** — How do tools like TikTok effects, Instagram filters, and YouTube Studio organize creative controls?
- **Creative brief formats** — How do advertising and marketing professionals describe video creative?

Key question: What vocabulary and groupings do people naturally use when they don't know filmmaking terminology? Do they think in sensory terms (what I see, what I hear)? Emotional terms (tense, warm, chaotic)? Reference terms (like Blade Runner, like a documentary)?

### 5. Element Interaction and Dependencies

Some elements constrain or influence each other. Map the key dependencies:

- How does lighting affect color palette choices?
- How does pacing affect shot duration and camera movement?
- How does blocking affect camera framing?
- How does ambient sound affect music choices?
- How does performance direction affect blocking and camera?

This matters because it determines whether elements should be specified independently or in groups. If lighting and color palette are almost always specified together, they should be in the same group.

### 6. Proposed Grouping Evaluation

Evaluate these four candidate groupings against the criteria: intuitive for non-filmmakers, useful for filmmakers, supports iterative refinement, maps well to AI generation parameters.

**Option A — By Professional Role:**
Editorial (pacing, transitions, coverage) | Visual (lighting, color, camera, costume, set) | Sound (ambient, music, effects, silence) | Performance (emotion, delivery, blocking)

**Option B — By Perception:**
What You See (lighting, color, camera, costume, set, blocking) | What You Hear (ambient, music, effects, dialogue delivery) | How It Flows (pacing, transitions, coverage) | What Characters Feel (emotion, motivation, subtext)

**Option C — By Scope:**
Project-Wide (visual style, sound style, character design) | Per-Scene (lighting, camera, pacing, ambient, blocking) | Per-Shot (framing, angle, lens, movement)

**Option D — By Creative Concern:**
Look & Feel (lighting, color, composition, camera, costume, set, motifs) | Sound & Music (ambient, effects, music, silence, sound transitions) | Rhythm & Flow (pacing, transitions, coverage, scene function) | Character & Performance (emotion, motivation, subtext, blocking, delivery, voice) | Story World (character design, location design, prop design, continuity)

For each option: How intuitive is it? Does it support "make this scene darker and tenser" spanning multiple groups? Does it work for both beginners and experts? Does it map well to how AI generation models accept parameters?

Also propose any grouping we haven't considered that the research suggests would be better.

## Output Format

For each section, provide:
1. **Key findings** — What did the research reveal?
2. **Recommended approach** with reasoning
3. **Runner-up** and when you'd pick it instead
4. **Avoid** — What looks tempting but has known issues
5. **Evidence** — Links, examples, user feedback, industry standards
