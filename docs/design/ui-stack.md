# UI Stack Evaluation

**Status**: Not yet researched
**Method**: Deep research (`deep-research init ui-stack`)

---

## Purpose

Determine the best UI component library and tooling stack for CineForge, optimized for one key constraint: **AI agents (Cursor, Claude Code, Codex) write most of the UI code.** The stack must produce visually polished output when AI is the primary developer.

## Current Stack (Story 007b Stopgap)

- React 18 + TypeScript
- Vite
- Tailwind CSS (utility classes, no component library)
- No component library — all components are hand-written

This works but produces "developer tool" aesthetics, not "creative tool" aesthetics.

## Research Questions

### Component Library Selection
- Which component libraries produce the best visual quality when AI writes the code? (shadcn/ui, Radix, Mantine, Park UI, Ark UI, Chakra, others)
- Which have the highest "ceiling" — can they produce genuinely beautiful UIs, or do they plateau at "clean but generic"?
- Which are most composable — can AI mix and customize components without fighting the library's opinions?
- Which have the best accessibility defaults (WCAG 2.1 AA)?
- Bundle size and performance considerations for artifact-heavy UIs.

### AI Development Workflow
- What patterns produce the best AI-generated UI code? (Screenshot-driven iteration, component-first prompting, design-token systems?)
- Are there tools or approaches specifically designed for AI-assisted UI development? (v0, Bolt, Lovable, Antigravity — what's the state of the art in Feb 2026?)
- **Google Stitch** ([stitch.withgoogle.com](https://stitch.withgoogle.com/)): Gemini-powered text/image-to-UI tool from Google Labs. Generates complete UI designs from prompts or sketches, exports to Figma or HTML/CSS. Now supports Gemini 3 and interactive prototypes ("stitch together screens into flows"). Evaluate as a design/prototyping tool in the CineForge UI workflow — could it accelerate screen design before implementation?
- What anti-patterns lead to AI generating bad UI code? (Over-abstraction, unclear design systems, too many options?)

### Integration with Existing Stack
- Can the recommended library work with React 18 + Vite + Tailwind, or does the stack need to change?
- Are there React alternatives worth considering? (Solid, Svelte, etc. — only if they produce materially better AI-generated output.)
- Dark mode support and theming — does the library make this easy or painful?

### Type-Specific Viewers
- What libraries or patterns exist for:
  - Screenplay/script text rendering
  - Structured data / JSON browsing with collapsible sections
  - Graph / relationship visualization (for entity graph, dependency graph)
  - Timeline / track visualization (for future Phase 3 stories)
  - Diff / version comparison views
- Are these better served by the component library or by specialized packages?

## Expected Output

A decision document with:
- Recommended component library (with rationale and trade-offs)
- Recommended development workflow for AI-assisted UI coding
- Any stack changes from the current 007b baseline
- Specialized viewer library recommendations per artifact type
- A brief "what not to do" section based on research findings

## Deep Research Prompt Guidance

When running this research, the prompt should emphasize:
- AI code generation quality as the primary selection criterion, not developer ergonomics
- Visual polish ceiling — we want "looks like a real product" not "looks like a Tailwind template"
- Feb 2026 state of the art — this space moves fast, 2024/2025 advice may be outdated
- Practical evaluation: which libraries have the AI models seen the most training data for?
