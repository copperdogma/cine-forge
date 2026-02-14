# CineForge User Personas

CineForge is a personal project built primarily for one use case: **a person with scripts who wants to see them come to life, with no film industry experience.** The UI is designed for this user first.

Secondary personas exist as lenses to avoid over-fitting the UI to a single workflow. They are not market segments — they're useful perspectives for ensuring the tool remains flexible.

---

## Primary User

**The Storyteller** — Has written scripts or prose stories. Wants to see them realized as films. Has no film production background, no crew, no budget. Comes to CineForge because the alternative is "these stories stay in a drawer forever."

Key traits:
- Deeply invested in the *story*, not the filmmaking process.
- Willing to learn film concepts when they're explained in context, but not willing to study them upfront.
- Trusts AI to make good creative decisions by default. Wants to intervene only when something feels wrong.
- Success metric: "I saw my story as a film and it felt right."

---

## Interaction Modes

The primary user operates in four modes. These are not different people — they're the same person in different moments. The UI must support fluid transitions between them.

### Autopilot Mode
"Run it, show me what comes out."

- Drag in a script. Click OK. Watch progress. Browse results.
- Every decision is AI-made. The user's only action is approval.
- This is the default mode and the most common one.
- The UI should make this path feel effortless and fast.

### Learning Mode
"Why did it do that?"

- Same workflow as autopilot, but the user is curious about the process.
- They click into artifacts, read AI rationale, explore agent reasoning.
- They want to understand film concepts (coverage, blocking, continuity) through the AI's explanations, not through textbooks.
- The UI should make explanations discoverable without cluttering the autopilot path.

### Directing Mode
"I want to control this specific thing."

- The user disagrees with an AI decision or has a strong preference.
- They override one value (a character's tone, a scene's lighting, a project config field) and let AI handle everything else.
- This might be triggered by seeing something in the artifacts that doesn't match their vision.
- The UI should make overrides feel natural — edit inline, not through a separate "advanced settings" panel.

### Reviewing Mode
"Show me what was produced."

- The user steps back and evaluates the pipeline's output.
- They browse artifacts, compare versions, check health indicators.
- They approve or reject before the next stage (checkpoint mode per spec 2.5).
- The UI should present artifacts as a coherent story, not as a list of JSON files.

---

## Secondary Personas

These are brief notes for future-proofing. They are not design drivers today.

### The Student
Uses CineForge primarily to learn filmmaking. Inspects every decision, reads every rationale. Wants the tool to be a teacher. Overlaps heavily with Learning Mode of the primary user, but may want more structured educational content (tutorials, glossaries, "why did the AI choose this shot type?").

### The Creator
Content creator (YouTube, social media, music video). Has visual sense and audience awareness but isn't a filmmaker. Values speed and iteration over craft precision. Might run the pipeline 5 times with different style packs to find the right vibe. Wants quick exports and shareable previews.

### The Craftsperson
Deep expertise in one film domain (cinematography, sound design, editing). Wants fine control over their domain and AI handling everything else. The UI needs domain-specific artifact viewers that respect expert-level detail (e.g., a DP wants to see lighting setups, not just "NIGHT").

### The Planner
Uses CineForge for pre-production planning only — shot lists, breakdowns, schedules, budgets. May film IRL. Wants exportable production documents. Cares about cost tracking and logistics, not AI-generated video.
