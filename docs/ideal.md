# CineForge — The Ideal

> **This is the most important document in the project.** It defines what CineForge
> should be with zero limitations. Every architectural decision should move toward
> this Ideal. Every compromise in `docs/spec.md` carries a detection mechanism for
> when it's no longer needed. The Ideal is the Requirements. The Spec is the
> Compromises. The Spec shrinks over time. This document rarely changes.

## 1. The Ideal

You have a story — a screenplay, a short story, a voice memo, a sketch on a napkin. You give it to CineForge. CineForge *understands* it: who these people are, what they want, why this scene exists, how the light should fall, where the silence belongs.

Now the creative work begins — and it's *fun*. You explore your story through conversation. Talk to the Director about the opening scene. Ask Billy why he lied to Jane — and hear him explain in his own voice, drawing on a psychology you hadn't fully articulated, bringing you to tears with insight into your own character. Debate the ending with the Sound Designer, who argues that silence serves the final moment better than score. Every creative discipline lives inside CineForge, and talking to them feels like collaborating with talented, passionate people who care about your story — not operating software.

The magic is in iteration. You may not know exactly what you want until you see it. CineForge generates — visuals, sound, video, storyboards — and you react. "No, darker." "Better — but John's wardrobe is wrong. Classy but shabby, with a green fedora." "Drop the fedora, make it slicked back hair." "Nice. Now make John speak two beats earlier." "John, can you say that line with more menace?" *"Actually, I think I'd be less menacing here and more vulnerable — because of my childhood. You want menacing or vulnerable?"* "Good point! Let's try vulnerable." Each iteration gets closer to the vision in your head — or helps you *discover* what that vision is. Some users know exactly what they want. Others find it through the act of reacting to what the AI produces. Both are first-class workflows. The AI anticipates too, generating options you didn't think to ask for — a variant framing, an alternate reading, a color grade that shifts the mood.

CineForge's job is to extract your vision — whatever it is, however vague — in the easiest, most enjoyable way possible. The difficulty of turning intent into outcome is the core problem. A user who says "make this screenplay into a movie" will likely not get exactly what they had in mind on the first try. If they had no particular vision and just wanted to see what the AI would do — great, success out of the box. But if they have a vision, CineForge's job is to pull it out of them through iterative exploration, not forms and pipeline stages.

When you're ready — whenever that is — take what you've made. A film with consistent characters, intentional editing, sound that serves the narrative. Or stop earlier: analysis for refining your screenplay, direction notes for a real-world shoot, storyboards for a pitch. Export to your editor of choice with CineForge's narrative intelligence embedded as markers and notes. CineForge makes films. NLEs edit them.

Bring a friend. Real filmmaking is collaborative, and so is CineForge. Work on a project together — argue about the ending, split creative responsibilities, build something with another person. One of the most fun parts of making something is making it with someone else.

At every point, you can see what CineForge decided and why. Change anything. Go back. Revisit a version you skipped three iterations ago. No decision is final, and nothing is ever lost. The comfort of knowing you can always undo makes experimentation fearless.

CineForge doesn't care if you're a first-time filmmaker or a veteran director. It meets you where you are. When you see "storyboard" and wonder what that means, you can just ask — the AI explains, naturally, as part of the conversation. When you know exactly what you want, CineForge keeps up. A 30-second commercial. A feature film. An episode of a series. A music video. All of them.

### Vision-Level Preferences

Qualities that persist regardless of implementation — these are part of the Ideal, not tied to any compromise:

- **Easy, fun, and engaging** — This is the primary test for every design decision. If using CineForge feels like work, something is wrong. The experience should be enjoyable, the kind of thing you lose an afternoon to because you're having a great time exploring your story
- **Iterative by nature** — The core creative loop is generate → react → refine → generate. Every feature should support this loop. Users don't configure then execute; they explore and converge
- **Creative partnership** — The interaction feels like collaborating with brilliant, passionate creative people — not operating a tool. Talking to your characters can bring you to tears. Debating with the Director can change how you see your own story. The emotional engagement is the product
- **Radical transparency** — Every AI decision is visible, explainable, and overridable. The user always knows what's certain (from their script) vs. what's improvised (AI filling gaps)
- **Nothing is ever lost** — Every version, decision, conversation, and alternative is permanent and navigable. No decision eliminates options. Experimentation is fearless because undo is always available
- **Any depth of engagement** — From "just make a film" to frame-by-frame, beat-by-beat creative control. The user chooses their level of involvement per feature, per scene, at any time
- **Teaching in context** — Filmmaking concepts are explained naturally when users encounter them: subtle help affordances, AI that answers "what's a storyboard?" mid-conversation, links to learn more. Never a tutorial wall; always available when curiosity strikes
- **Export-first, not edit** — CineForge produces and exports. Professional NLEs handle editing. Don't build what DaVinci Resolve already does for free
- **Taste belongs to the user** — The system amplifies creative vision, never overrides it. Style is a human choice expressed through conversation, references, and example
- **Accessible by default** — Works regardless of film knowledge, budget, or technical sophistication. A teenager with a story and a veteran director both find what they need
- **Voice-first as the ultimate expression** — The final form of CineForge is a voice conversation. Watch your film take shape, pause, speak, adjust, watch the change. "Make John speak earlier." "Darker lighting." "John, try that with more vulnerability." This is the north star for the interaction model — every intermediate interface is a step toward this

---

## 2. Requirements and Quality Bar

Requirements are capabilities the system must have regardless of implementation. Each is universal to the Ideal. Quality bar entries define "correct" with concrete examples — these become golden reference seeds.

### Story Understanding

**R1. The system must accept any story input and understand it completely.**
- Screenplay (FDX, Fountain, PDF), prose fiction, treatments, outlines, notes
- Non-screenplay inputs are understood as stories and intelligently structured — not mechanically "converted"
- Any length: 30-second commercial scripts to feature-length screenplays
- Quality bar: Given *The Mariner* (FDX, ~12,000 words), correctly identify all 18 speaking characters, 15 locations, key props (oar, purse, flare gun), and 45 scenes with accurate headings, character presence, and narrative beats.

**R2. The system must understand characters as complete psychological entities, not name tags.**
- Motivation, arc, relationships, internal contradictions, subtext
- Not just "who appears in which scene" but "what do they want and why are they here"
- Deep enough for a user to have a meaningful, emotionally resonant conversation with any character
- Quality bar: For Billy in *The Mariner* — identify: ex-sailor pride as defining trait, the oar as symbol of the sea he can't return to, adversarial relationship with his father rooted in abandonment, emotional arc from defiance through reluctant reconciliation. Miss none of these. Get the subtext right.

**R3. The system must maintain perfect continuity across the entire narrative.**
- Track character state (costume, injuries, emotional state, location, possessions) through story time
- Track location state (damage, time of day, weather, who's present)
- Detect and flag continuity errors: character in two places simultaneously, disappearing props, timeline impossibilities
- Propagate changes intelligently: upstream revision flags affected downstream with specific reasons
- Quality bar: If Billy gets punched in Scene 12, every subsequent scene should note the injury until healing is established or time passes. If Scene 15 describes him as uninjured with no explanation, flag the discontinuity with evidence from both scenes.

### Creative Collaboration

**R4. The system must support natural, emotionally engaging conversation with AI creative roles and characters.**
- Users address specific roles (@director, @visual_architect, @sound_designer) or characters (@billy)
- Each role speaks in its own voice with genuine creative expertise
- Characters respond in-character, grounded in their full narrative context — deep enough to surprise the user with insight into their own story
- Multiple roles join when their domain is touched; roles stay silent when they have nothing to add
- Scope wanders naturally — a conversation about acting shifts to lighting shifts to pacing, and the right roles enter and leave
- Quality bar: Asking @billy "Why did you lie to Jane?" produces a response that draws from Billy's established psychology, references the specific scene, reveals subtext the user might not have considered — in Billy's voice, not a summary about Billy. The response should feel like talking to a person who deeply understands this character.

**R5. The system must support the full spectrum of human involvement.**
- **Autonomous**: "Make a film from this script with Tarantino directing and Deakins shooting"
- **Collaborative**: conversation-driven direction with AI as creative partner
- **Advisory**: AI analyzes and suggests, human makes all decisions
- **Direct edit**: human changes any artifact, system adapts immediately — no AI approval gate
- Any combination, at any time, with per-feature granularity (autonomous for sound design, collaborative for visual direction, manual for dialogue)

**R6. The system must apply creative style and taste.**
- Style packs shape how each creative role thinks and creates
- Packs are created from anything: a filmmaker's name, a film title, a mood board, a written description, a combination
- User-provided references (images, frame grabs, audio clips) influence output
- Multiple styles can coexist: one director style, a different visual style, a different sound style
- Quality bar: With a "Roger Deakins" visual style pack, visual direction should favor natural lighting, muted palettes, long takes, motivated camera movement, and deep staging — identifiably informed by Deakins' body of work.

### Iterative Refinement

**R7. The system must support rapid iterative generation — the core creative loop.**
- Generate → user reacts → refine → generate again. This is the primary workflow, not a secondary mode
- The AI generates variants proactively: alternate framings, readings, color grades, compositions — options the user didn't ask for that expand the creative space
- Users who can't articulate what they want can discover it by reacting to what's generated. "Not that. More like that. Yes, but darker."
- Iteration is fast enough to maintain creative flow. Waiting breaks the spell
- Every generated variant is kept — the user can revisit any previous iteration and branch from it
- Quality bar: A user working on Scene 7's visual direction sees 3 lighting variants generated. They pick one, adjust ("warmer, more golden hour"), get 2 new variants, pick one, adjust John's wardrobe, see the scene re-rendered. Total time from first generation to "that's what I wanted": under 5 minutes. Every intermediate variant is still accessible.

### Production Output

**R8. The system must produce professional-grade production artifacts.**
- Script analysis: scene breakdowns, character/location/prop bibles, entity relationship graph
- Production documents: shot lists, call sheets, breakdown sheets
- Visual assets: storyboards (sketch, clean line, animation-style), reference image packs (multi-angle character/location/prop), keyframes
- Motion assets: animatics with accurate timing and camera motion, previz video
- Generated media: video with consistent characters, coherent visual language, and intentional editing
- Generated audio: character-specific dialogue voices (tone, accent, age, personality), music/soundtrack, sound design, ambient atmosphere
- Quality bar: A generated sequence of 3 scenes should maintain Billy's appearance (face, build, costume, injury state), visual style (lighting, color grade), and sound atmosphere — with editorial cuts motivated by the story beats identified in the editorial direction.

**R9. The system must export to professional formats with embedded narrative intelligence.**
- Timeline interchange: OpenTimelineIO, Final Cut XML, AAF, EDL
- Production documents: formatted shot lists, call sheets, breakdown sheets
- Storyboard packages: PDF, image sequences
- Narrative metadata embedded in exports: scene boundaries as markers, beat changes, character entrances/exits, emotional tone shifts as color-coded regions, clip notes with context
- Quality bar: An OpenTimelineIO export imports into DaVinci Resolve with scene markers at every boundary, color-coded regions for act structure, clip notes containing character presence and emotional beats — metadata that makes the editor's job dramatically easier because the export understands story structure.

### Audience & Presentation

**R10. The system must show a playable assembly at every stage.**
- From the moment scenes exist, the user can "watch" their film
- Best available representation per scene: text summary → storyboard → animatic → final render — mixed freely
- Simple reordering and trim before export (drag scenes, cut at boundaries) — NOT a full NLE
- Quality bar: After scene extraction + storyboards for Act 1, the user presses play and sees a timed sequence of storyboard frames with scene headings, temp dialogue, and sound atmosphere — enough to evaluate pacing and flow before committing to full generation.

**R11. The system must show production readiness per scene.**
- For every production element in every scene: what's been specified by the user, what AI has inferred, and what's completely missing
- Red / yellow / green readiness per element (characters, location, visual direction, sound, shots, voice)
- One-click path to fill any gap, with honest quality estimate ("generating now will use AI defaults for lighting — specify visual direction first for better results")
- Quality bar: Scene 7's workspace shows: characters (green — full bibles + reference images), location (yellow — bible exists, no reference images, AI will improvise appearance), sound (red — not started, AI fills with generic ambient). The user sees exactly what will be solid vs. improvised if they generate now.

### Transparency & Control

**R12. Every AI decision must be explainable and overridable.**
- Show: what was decided, why, alternatives considered, confidence level, which role made it
- Human overrides take effect instantly — no AI approval, no "are you sure"
- When roles disagree, both positions are permanently preserved with full rationale
- For generated media: show the prompt that produced it, let users edit and re-submit directly
- Quality bar: When editorial direction recommends a jump cut, the user sees: the recommendation, the reasoning ("to emphasize the jarring time shift"), alternatives considered ("dissolve — too gentle; match cut — no visual match available"), confidence (0.85), and a link to the scene analysis that informed it.

**R13. The system must learn from user choices.**
- Every suggestion accepted, rejected, or modified is recorded as a preference signal
- Future suggestions improve based on accumulated choices — across the project, not just the current scene
- Preference learning is transparent: users can see what the system has learned about their taste
- Quality bar: If the user consistently picks intimate close-ups over wide establishing shots, future shot plans should bias toward close framing for emotional beats — without explicit configuration. If asked, the system can explain: "I noticed you prefer close framing for dialogue — should I keep doing that?"

### Persistence & Provenance

**R14. Nothing is ever lost. No decision is final.**
- Every artifact version is a complete, independently loadable snapshot — no reconstruction from diffs
- Every conversation transcript is retained permanently (creative-archaeological value)
- Every decision records: what was decided, by whom, why, and what alternatives were considered
- Full version history is navigable — "time walk" through any artifact's evolution
- Branching: copy the project and continue from any point
- The user never has to worry about losing work or closing off options — experimentation is psychologically safe
- Quality bar: Six months after completing a project, the user can open it, navigate to Scene 12's visual direction v3, see exactly what changed from v2, read the conversation that led to the change, and understand the Director's reasoning — all without any context loading or "summarize what happened."

**R15. Changes propagate intelligently through the dependency graph.**
- When an upstream artifact changes, all downstream artifacts that depend on it are evaluated
- Assessment distinguishes cosmetic changes (still valid) from fundamental changes (needs revision) with specific reasons
- Quality bar: Changing Billy's name spelling → only name references need updating, everything else confirmed still valid. Changing Billy's core motivation → all performance direction, dialogue alternatives, and relationship dynamics for his scenes are flagged for revision, each with a specific reason ("Billy's motivation in Scene 14 was 'prove himself to father' — this no longer applies given the new backstory").

### Together

**R16. The system must support multi-human collaboration.**
- Multiple people work on the same project simultaneously — different creative roles, shared vision
- Real-time or asynchronous: both work
- Shared conversation history, shared artifacts, shared version timeline
- Roles can be divided: one person handles visual direction, another handles sound, both see each other's work
- Quality bar: Two friends working on a short film — one focuses on the script and characters, the other on visual style and music. Both see the same project state, both can talk to the AI roles, both contribute artifacts that the other can see and react to. Disagreements are resolved through conversation (with each other and with the AI), not merge conflicts.
