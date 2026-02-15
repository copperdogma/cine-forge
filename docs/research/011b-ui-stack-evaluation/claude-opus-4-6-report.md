---
type: research-report
topic: 011b-ui-stack-evaluation
canonical-model-name: claude-opus-4-6
collected: '2026-02-15T01:24:49.908592+00:00'
---



# CineForge Operator Console: Technology Stack Research

## 1. Component Library Selection

### Evaluation Framework

I'm evaluating each library against the specific constraint that **AI agents write 100% of the code**. This changes the calculus dramatically. What matters is: how much of the library's API surface is well-represented in training data, how deterministic is the output, and how high is the visual ceiling when the AI is "driving."

---

### shadcn/ui

**What it is (Feb 2026 state):** A collection of copy-paste component source files built on Radix UI primitives, styled with Tailwind CSS, using `class-variance-authority` for variants. Not an npm package — you own the source. By early 2026, shadcn/ui has added chart components (Recharts-based), a CLI (`npx shadcn@latest add`), and broad adoption across AI-generated codebases.

**AI Code Quality: 9/10**
This is the single most well-represented component library in AI training data as of 2025-2026. Claude, GPT-4, and Codex have seen enormous volumes of shadcn/ui code. The output is consistently correct because:
- Components follow predictable patterns (`cn()` utility, `cva` variants, Radix composition)
- Tailwind classes are atomic and well-understood by all major models
- The "copy-paste ownership" model means AI can modify component internals without fighting an abstraction boundary

AI agents generate shadcn code with fewer hallucinated props, fewer incorrect compositions, and more consistent patterns than any other library.

**Visual Ceiling: 6.5/10 (default) → 8.5/10 (with effort)**
This is the critical weakness. Default shadcn/ui produces what I call the "shadcn look": clean, competent, immediately recognizable as a shadcn site. Every Y Combinator startup dashboard in 2024-2025 looks like this. For CineForge — a creative production tool — this is insufficient.

However, the ceiling is higher than the default. Because you own the source:
- You can replace the default `slate` color palette with a custom dark-mode palette
- You can swap the default `inter` typography for something with more character
- You can modify the component source to add motion (Framer Motion), custom focus rings, etc.
- The Radix primitives underneath are fully unstyled — the visual layer is entirely Tailwind, which is infinitely customizable

The gap between "shadcn default" and "shadcn customized" is large, and AI agents can navigate this gap *if given a clear design token system to follow*.

**Composability: 9.5/10**
Excellent. Components are just files in your project. AI can modify them, extend them, combine them. No `styled()` wrappers, no theme provider chains, no slot APIs to learn.

**Accessibility: 9/10**
Inherits Radix UI's accessibility — keyboard navigation, ARIA attributes, focus management, screen reader announcements. This is genuinely production-grade a11y with zero additional work.

**Bundle Size: 9/10**
You only include what you use. Each component is a separate file. Tree-shaking is trivial. Radix primitives are small. Tailwind is purged at build time.

**Dark Mode / Theming: 8/10**
Built-in CSS variable system. `dark:` variant in Tailwind. Easy to customize, but the theming system is basic compared to design-token-native libraries. You manage your own tokens.

---

### Radix UI (Direct, unstyled)

**What it is:** The primitive layer underneath shadcn/ui. Unstyled, accessible components: Dialog, Popover, Select, Tabs, etc. You provide 100% of the styling.

**AI Code Quality: 7/10**
AI agents know Radix well, but generating correct *styling* from scratch for every component is where quality drops. The AI must make aesthetic decisions for every element — border radius, spacing, color, hover state, focus ring. Without a reference design system, the output is inconsistent. One component gets `rounded-lg`, another gets `rounded-md`. Padding varies. Colors drift.

**Visual Ceiling: 10/10 (theoretical) / varies wildly (practical)**
Unlimited ceiling because there are no default styles to overcome. But in practice, AI-generated styling from scratch is inconsistent. You'd need to establish a very tight design token system and reference components for the AI to match.

**Composability: 10/10** — It's just primitives.

**Accessibility: 9.5/10** — This is the gold standard for React accessibility primitives.

**Bundle Size: 9.5/10** — Minimal. Each primitive is a small package.

**Dark Mode: N/A** — You build this yourself.

**Verdict:** Radix direct is the right choice if you have a human designer producing detailed specs. For AI-only generation, the lack of visual defaults creates too much variance. shadcn/ui exists precisely to solve this problem.

---

### Mantine (v7+)

**What it is:** A full-featured React component library with 100+ components, built-in hooks, form management, and a custom CSS-in-JS solution (moved to CSS modules in v7). Highly opinionated with good defaults.

**AI Code Quality: 7.5/10**
Mantine is well-represented in training data, but its large API surface creates issues. Mantine components have many props, and AI agents sometimes:
- Hallucinate props that don't exist or confuse v6 and v7 APIs (major breaking changes)
- Mix Mantine's styling approach with Tailwind (Mantine uses its own `classNames` API and CSS modules)
- Get confused by Mantine's form library vs. react-hook-form patterns

The v6 → v7 migration is a particular problem. Training data contains significant v6 code, and the APIs changed substantially.

**Visual Ceiling: 7.5/10**
Mantine's defaults are attractive — slightly more opinionated and polished than shadcn's defaults. But it has its own recognizable "Mantine look." Customization is possible through the theming system but fights the library's opinions more than shadcn.

**Composability: 6/10**
This is Mantine's weakness for AI generation. Components are relatively monolithic. Customizing internal structure (e.g., changing how a Select renders its dropdown items) requires understanding the `classNames` prop API, `styles` prop, or component slots. AI agents frequently get this wrong.

**Accessibility: 8/10**
Good but not Radix-level. Mantine handles basic ARIA and keyboard nav, but some edge cases require manual intervention.

**Bundle Size: 6/10**
Larger than shadcn/Radix. Even with tree-shaking, Mantine's runtime (CSS module injection, theme context) adds overhead.

**Dark Mode: 8.5/10**
Mantine's `MantineProvider` with `colorScheme` is well-integrated. The dark theme looks good out of the box.

---

### Park UI

**What it is:** A component library built on Ark UI primitives (from the Chakra team), using Panda CSS for styling. Design-token-native. Available for React, Solid, and Vue.

**AI Code Quality: 4/10**
This is the critical failure. Park UI and Panda CSS have *vastly* less representation in AI training data compared to shadcn/Tailwind. In my assessment:
- Claude and GPT frequently hallucinate Panda CSS syntax
- Ark UI's component API is confused with Chakra v2 APIs
- The design token system (using Panda's `token()` function) is not well-learned

By Feb 2026, this may have improved somewhat, but the training data gap is 18-24 months behind shadcn/ui.

**Visual Ceiling: 8/10**
Park UI's defaults are quite polished. The design token system allows systematic theming. But you can't access this ceiling if the AI can't write correct code.

**Composability: 8/10** — Ark UI primitives are well-designed.

**Accessibility: 9/10** — Ark UI's accessibility model is strong (derived from Zag.js state machines).

**Bundle Size: 7/10** — Panda CSS is zero-runtime, but Ark UI has some overhead.

**Dark Mode: 9/10** — Design-token-native, semantic tokens handle dark mode elegantly.

**Verdict:** Excellent library, wrong timing. If AI training data catches up, revisit in late 2026 or 2027.

---

### Chakra UI v3

**What it is:** Major rewrite of Chakra UI on Ark UI primitives with Panda CSS. Released late 2024 / early 2025.

**AI Code Quality: 4.5/10**
Same fundamental problem as Park UI — Panda CSS and Ark UI are underrepresented in training data. Additionally, there's a severe *confusion* problem: AI agents have extensive training on Chakra v2 and frequently generate v2 code when asked for Chakra v3. The APIs are dramatically different. Props like `bg`, `p`, `mt` (Chakra v2's style props) don't work the same way in v3.

**Visual Ceiling: 8/10** — Good design system, but similar "Chakra look."

**Composability: 7/10** — Better than v2, but the migration confusion hurts.

**Accessibility: 9/10** — Ark UI foundation is strong.

**Verdict:** Don't use. The v2/v3 confusion in AI training data makes this actively dangerous for AI-generated code. Every other component will have subtle v2 contamination.

---

### Ant Design (antd v5+)

**What it is:** Enterprise-grade component library from Ant Financial. 60+ components. CSS-in-JS theming (switched to cssinjs in v5). Very complete — tables, forms, layouts, charts (via Ant Design Charts / G2).

**AI Code Quality: 7/10**
AI agents know Ant Design extremely well — it has massive training data representation, especially from Chinese tech codebases. The code is generally correct. However:
- Ant Design is extremely opinionated about layout and visual style
- Its CSS-in-JS runtime (`@ant-design/cssinjs`) can conflict with Tailwind
- AI-generated antd code tends to look like an enterprise admin panel, which is the opposite of CineForge's "creative tool" aesthetic
- The component APIs are large and AI sometimes generates deprecated v4 patterns

**Visual Ceiling: 5/10 (for CineForge's use case)**
Ant Design looks like Ant Design. It's designed for data-heavy enterprise dashboards. Making it look like a creative production tool requires fighting the library at every turn. The theming system (ConfigProvider + design tokens in v5) is powerful but the fundamental visual language is "enterprise Chinese tech."

**Composability: 5/10**
Components are monolithic. Customizing internal rendering often requires undocumented CSS overrides. The `theme` prop system is complex.

**Accessibility: 6/10**
Historically weak on accessibility compared to Radix-based libraries. Has improved in v5 but still requires manual ARIA work in many components.

**Bundle Size: 4/10**
Large. Even with tree-shaking, antd pulls in significant runtime. Moment.js dependency was removed in v5, but the CSS-in-JS runtime is heavy.

**Dark Mode: 7/10**
v5 added algorithm-based theming (`theme.darkAlgorithm`). Works, but the dark theme has an "enterprise" feel.

**Verdict:** Wrong aesthetic for CineForge. Would be a strong pick for a data analytics dashboard.

---

### Material UI (MUI v5/v6)

**What it is:** React implementation of Google's Material Design. Largest ecosystem. Emotion-based styling (or Pigment CSS in newer versions).

**AI Code Quality: 8/10**
MUI has the deepest training data representation of any React component library. AI agents generate syntactically correct MUI code very reliably. However:
- `sx` prop, `styled()`, and theme overrides create multiple competing styling patterns; AI mixes them inconsistently
- MUI v5's Emotion dependency creates confusion when combined with Tailwind
- The `ThemeProvider` + `createTheme` API is verbose and AI sometimes generates incomplete theme configs

**Visual Ceiling: 5/10 (for CineForge)**
Material Design is a specific, recognizable design language. It screams "Google product." Making it not look like Material Design requires overriding nearly everything, at which point you're fighting the library.

**Composability: 6/10**
MUI components have extensive slot APIs (`slotProps`, `components` prop), but these are complex and AI agents frequently get them wrong.

**Accessibility: 8/10**
Good. Material Design specs include accessibility guidelines, and MUI follows them reasonably well.

**Bundle Size: 4/10**
Heavy. Emotion runtime, theme context, component runtime. MUI is one of the largest component libraries by bundle size.

**Dark Mode: 8/10**
Well-supported through `createTheme` with `palette.mode: 'dark'`. Material Design's dark theme spec is well-defined.

**Verdict:** Too heavy, too opinionated toward Material Design aesthetic. Wrong choice for a creative tool.

---

### Others Worth Considering

**Headless UI (Tailwind Labs):**
Smaller than Radix (fewer components) but very well-known to AI. Limited component set (Dialog, Menu, Listbox, Combobox, Switch, Tabs, Disclosure, Popover, Radio Group, Transition). Could supplement Radix/shadcn for specific components. AI generates very clean Headless UI code because the API surface is small.

**React Aria (Adobe):**
Adobe's accessibility-focused hooks library. Extremely thorough accessibility — arguably better than Radix. But it's hooks-only (no rendered components), which means AI must generate all markup and styling. Similar problem to raw Radix but worse — more boilerplate, less training data.

**Ariakit:**
Accessible unstyled components. Less training data than Radix, but solid accessibility. Not a strong pick for AI generation due to training data gaps.

**Kobalte (Solid.js):**
If you were on Solid, this is the Radix equivalent. Excellent, but Solid-specific.

**Bits UI / Melt UI (Svelte):**
Svelte equivalents. Mentioned for completeness.

**Next UI (now HeroUI):**
Built on React Aria + Tailwind + Framer Motion. Beautiful defaults, modern aesthetic. Training data is growing but still significantly behind shadcn. Worth monitoring. By Feb 2026, this could be a viable alternative. The visual ceiling is higher than shadcn defaults due to built-in animations.

---

### Component Library Summary Table

| Library | AI Code Quality | Visual Ceiling | Composability | A11y | Bundle Size | Dark Mode | **Overall (AI-first)** |
|---------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| shadcn/ui | 9 | 6.5→8.5 | 9.5 | 9 | 9 | 8 | **🥇 9.0** |
| Radix (direct) | 7 | 10 (theory) | 10 | 9.5 | 9.5 | N/A | 7.5 |
| Mantine v7 | 7.5 | 7.5 | 6 | 8 | 6 | 8.5 | 7.0 |
| Park UI | 4 | 8 | 8 | 9 | 7 | 9 | 5.5 |
| Chakra v3 | 4.5 | 8 | 7 | 9 | 7 | 8 | 5.5 |
| Ant Design v5 | 7 | 5 | 5 | 6 | 4 | 7 | 5.5 |
| MUI v5/v6 | 8 | 5 | 6 | 8 | 4 | 8 | 6.0 |
| HeroUI (NextUI) | 6.5 | 8.5 | 7 | 8.5 | 7 | 8.5 | 7.0 |

---

## 2. AI-Assisted UI Development Workflow

### State of the Art (Feb 2026)

AI-generated UI has matured significantly. The key developments:

1. **Screenshot-to-code is reliable** for static layouts. Given a screenshot or Figma frame, Claude/GPT-4o can reproduce it in React+Tailwind at ~85-90% fidelity.
2. **Interactive behavior generation** is the remaining frontier. AI can build a modal that opens/closes, but complex state interactions (drag-and-drop reordering, multi-panel resize, keyboard-driven workflows) still require careful prompting and iteration.
3. **Design system adherence** is the unlock. AI generates dramatically better code when given explicit design tokens, named patterns, and component APIs to follow — rather than freeform "make it look nice."

### Tool Evaluation

**v0 (Vercel)**
- **What it does:** Text/image-to-UI generation using shadcn/ui + Tailwind. Exports React components.
- **Quality:** The best "generate a component from a description" tool. Outputs are clean, use shadcn correctly, and are immediately usable.
- **CineForge applicability:** **High for prototyping, medium for production.** Use v0 to generate initial component designs, then integrate into the codebase. The components will need customization (CineForge design tokens, dark theme), but the structure and composition are solid starting points.
- **Limitation:** Generates individual components/pages, not full applications. No persistent state management, no routing, no backend integration.

**Bolt (StackBlitz)**
- **What it does:** Full-stack app generation in a browser-based IDE. Generates complete running apps.
- **Quality:** Impressive for demos, but the generated code has architectural problems at scale — monolithic files, inconsistent patterns, scattered state management.
- **CineForge applicability:** **Low.** CineForge already has backend architecture. Bolt's value proposition (full-stack from nothing) doesn't apply. The component-level code quality is lower than v0 or direct Claude Code generation.

**Lovable (formerly GPT Engineer)**
- **What it does:** AI app builder that generates full Supabase-backed apps. Focused on rapid prototyping.
- **Quality:** Good for MVPs. Uses shadcn/ui. But the code is optimized for "works quickly" not "production quality."
- **CineForge applicability:** **Low.** Same issue as Bolt — CineForge isn't a greenfield CRUD app.

**Google Stitch (stitch.withgoogle.com)**
- **What it does:** Gemini-powered design-to-code tool. Generates UI from text prompts or image inputs. Exports to Figma, HTML, React, Angular, Flutter.
- **Quality (as of early 2025, likely improved by Feb 2026):** Interesting for initial design exploration. The Figma export is useful for human designers. The React export quality is behind v0 — more generic, less idiomatic, sometimes uses inline styles instead of utility classes.
- **CineForge applicability:** **Low-Medium.** Could be useful as a "mood board" tool — generate visual concepts, then hand off to Claude Code for implementation. The direct code export is not production-quality.

**Antigravity**
- **What it does:** AI app builder focused on design quality. Claims to produce "designer-quality" output.
- **Quality:** Relatively new. Visual output is above average for AI builders. Less training data on the output quality.
- **CineForge applicability:** **Low.** Same category as Lovable/Bolt — app builder, not component tool.

**Claude Artifacts**
- **What it does:** Claude generates self-contained React components rendered in a sandbox. Single-file, inline Tailwind, Lucide icons.
- **Quality:** Surprisingly high for individual components. The constraint of a single file forces clean, self-contained code. Excellent for exploring UI concepts quickly.
- **CineForge applicability:** **Medium for design exploration.** Use Claude Artifacts to prototype individual views (script viewer, graph layout, timeline), screenshot them, then use those screenshots as reference for Claude Code to build production versions.

**Cursor Composer**
- **What it does:** Multi-file AI editing within the Cursor IDE. Understands project context, can modify multiple files simultaneously.
- **Quality:** The best tool for AI-assisted production code. Understands your existing codebase, respects your patterns, and generates code that fits architecturally.
- **CineForge applicability:** **High — core development workflow.** Cursor Composer (or Claude Code in similar agentic modes) is where production code gets written.

### Recommended Workflow for CineForge

```
┌─────────────────────────────────────────────────────────────┐
│                    DESIGN EXPLORATION                        │
│                                                             │
│  1. Claude Artifacts: Rapid concept prototyping             │
│     "Show me a dark-themed script viewer with fountain      │
│      formatting, sidebar, and version selector"             │
│                                                             │
│  2. v0 (Vercel): Component-level generation                 │
│     "Build a resizable panel layout with a left sidebar,    │
│      main content area, and right properties panel"         │
│                                                             │
│  3. Screenshot collection: Save best outputs as PNG         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    DESIGN SYSTEM DEFINITION                  │
│                                                             │
│  4. Define design tokens (colors, spacing, typography)      │
│     in a DESIGN_SYSTEM.md file at project root              │
│                                                             │
│  5. Create reference component implementations              │
│     (3-5 "golden" components that define the aesthetic)     │
│                                                             │
│  6. Write component specs in natural language before        │
│     asking AI to implement (COMPONENT_SPEC.md pattern)      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    PRODUCTION IMPLEMENTATION                 │
│                                                             │
│  7. Claude Code / Cursor Composer: Build components         │
│     referencing design tokens + screenshots + specs         │
│                                                             │
│  8. Component-per-file architecture                         │
│     (AI generates better code in <200-line files)           │
│                                                             │
│  9. Storybook or Ladle for visual regression                │
│     (AI can generate stories too)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Patterns That Cause AI to Generate BAD UI Code

1. **Monolithic files:** Your current 1800-line `App.tsx` is the worst case. AI agents lose context, generate inconsistent patterns within the same file, and can't reason about component boundaries. **Break into <200-line files.**

2. **Competing styling approaches:** Mixing Tailwind + CSS modules + inline styles + styled-components in the same project causes AI to randomly pick one per component. **Pick one approach (Tailwind) and enforce it.**

3. **No design token reference:** Without explicit color/spacing/typography tokens, AI invents values. One component uses `bg-gray-900`, another uses `bg-slate-950`, another uses `bg-zinc-900`. **Create a `tailwind.config` with semantic color names and a DESIGN_SYSTEM.md.**

4. **Vague prompts:** "Make it look better" produces random changes. "Match the visual density and color palette of DaVinci Resolve's edit page, using our defined --surface-primary and --surface-secondary tokens" produces consistent output.

5. **Over-abstraction too early:** Asking AI to "create a generic, reusable panel system that supports any content type with plugin architecture" produces overengineered abstractions. AI writes better code for concrete, specific components.

6. **No type constraints:** Without TypeScript interfaces for component props, AI generates components with inconsistent prop APIs. **Define interfaces first, then implement.**

---

## 3. Framework Evaluation

### React 18 vs. React 19

**React 19** (stable as of late 2024/early 2025):
- Server Components, `use()` hook, Actions, `useFormStatus`, `useOptimistic`
- `ref` as a regular prop (no more `forwardRef`)
- Improved context and suspense

**For CineForge:** React 19 is worth upgrading to, but the new features are mostly server-oriented. CineForge runs on localhost as a client-side app. The key benefit is:
- `ref` cleanup (no `forwardRef` boilerplate — AI generates cleaner code)
- Better Suspense boundaries (useful for lazy-loading heavy viewers)
- `useTransition` improvements for keeping the UI responsive during heavy updates

**AI impact:** React 19 code is well-represented in training data by Feb 2026. AI agents generate React 19 patterns correctly. The `forwardRef` removal alone reduces AI errors significantly.

**Recommendation: Upgrade to React 19.** Low risk, meaningful code quality improvements.

### Solid.js

**AI Code Quality: 6/10**
Solid has significantly less training data than React. AI agents frequently generate "React-like" code that doesn't work in Solid (using hooks patterns instead of signals, generating JSX that doesn't follow Solid's rules about destructuring props, using `.map()` instead of `<For>`).

**Solid-specific gotchas AI gets wrong:**
- Destructuring props (breaks reactivity)
- Conditional rendering (must use `<Show>` / `<Switch>`, not ternaries in all cases)
- Effect cleanup patterns
- Component lifecycle differences

**Visual ceiling impact:** No. The framework doesn't determine visual quality — the component library does. And Solid's component ecosystem is small.

**Verdict:** Solid is technically superior (fine-grained reactivity, smaller bundle, faster updates), but the AI code quality gap is disqualifying for CineForge's constraints.

### Svelte 5

**AI Code Quality: 6.5/10**
Svelte 5 (runes) has growing but still insufficient training data. AI agents:
- Confuse Svelte 4 (`$: reactive`, `export let`) with Svelte 5 (`$state`, `$derived`, `$effect`, `$props`)
- Generate incorrect rune syntax
- Can't reliably use Svelte 5's snippet/render features
- Component library ecosystem is smaller (no shadcn equivalent at Radix quality)

Svelte's advantage — less boilerplate — is real, but the AI training data gap and ecosystem limitations make it a poor choice for CineForge in Feb 2026.

**Verdict:** Don't switch. Revisit in 2027 if training data catches up.

### Vue 3

**AI Code Quality: 7.5/10**
Vue 3 Composition API is well-represented in training data. AI generates correct Vue code more reliably than Solid or Svelte 5. However:
- The component library ecosystem (Naive UI, PrimeVue, Vuetify 3) doesn't match React's depth
- Vue's template syntax is slightly less flexible than JSX for programmatic UI generation
- shadcn-vue exists but has less training data than the React original

**Verdict:** Viable but no advantage over React. The ecosystem delta matters — specialized viewer libraries (Fountain renderers, graph viz, timeline editors) are almost exclusively React-first.

### SSR/SSG Framework Consideration

**Should CineForge use Next.js/Remix/etc.?**

**No.** CineForge is a localhost development tool, not a deployed web application. Adding a meta-framework introduces:
- Server-side rendering complexity with no benefit (there's no SEO, no first-load optimization need for a local tool)
- File-based routing opinions that may not match CineForge's navigation model
- Build complexity (RSC hydration, server/client boundaries)
- Additional failure modes for AI-generated code (RSC "use client" directives, server actions, etc.)

**Stay with Vite + React (client-side SPA).** Vite's HMR and build speed are excellent. Add `react-router` v6/v7 if routing is needed.

### Framework Recommendation

**Stay on React. Upgrade to React 19. Keep Vite. Don't add a meta-framework.**

---

## 4. Specialized Viewer Libraries

### Screenplay/Script Text (Fountain Format)

**The Fountain Format:** A plain-text markup for screenplays (`.fountain` files). Defines Scene Headings, Action, Character, Dialogue, Parenthetical, Transition, etc.

**Available libraries:**

1. **fountain-js** (`npm: fountain-js`)
   - JavaScript Fountain parser. Parses `.fountain` text into a structured token array.
   - Outputs: Array of `{ type: 'scene_heading' | 'action' | 'dialogue' | ... , text: string }`
   - **Does NOT render** — it only parses. You must build the React rendering layer.
   - Active maintenance: Sporadic. But the Fountain spec is stable, so the parser works.
   - **Recommendation: Use this as the parser.**

2. **afterwriting-labs** (based on the After Writing screenplay editor)
   - More complete screenplay editor, but it's a full application, not an embeddable component.
   - Too heavy to integrate as a viewer.

3. **@fountain-js/parser** / community forks
   - Various forks of fountain-js with minor improvements. Check npm for latest activity.

**Recommended approach:**
```
fountain-js (parser) → Custom React renderer (AI-generated)
```

The rendering layer is straightforward for AI to generate. Screenplay formatting follows strict rules:
- Scene headings: ALL CAPS, left-aligned, bold
- Character names: ALL CAPS, centered above dialogue
- Dialogue: Centered, narrower margin
- Parentheticals: Centered, in parentheses, italic
- Action: Left-aligned, normal width
- Transitions: Right-aligned, ALL CAPS

This is a **perfect task for AI code generation** — well-defined rules, CSS-heavy, no complex state. Have Claude Code generate a `<FountainRenderer tokens={parsedTokens} />` component with proper typography.

**Typography matters:** Use a monospaced or semi-monospaced font. Traditional screenplay formatting uses Courier. For a modern tool, consider `Courier Prime` (Google Fonts, designed specifically for screenplays) or allow font selection.

---

### Structured Data Browser (JSON/YAML)

**Requirements:** Collapsible tree view, syntax highlighting, search, copy, large document support.

**Options:**

1. **react-json-view-lite** (`npm: react-json-view-lite`)
   - Lightweight, minimal dependencies
   - Supports collapse/expand, copy, basic theming
   - Missing: search, YAML support
   - 3KB gzipped

2. **@uiw/react-json-view** (`npm: @uiw/react-json-view`)
   - Feature-rich, customizable themes (including dark)
   - Collapse/expand with level control
   - Copy to clipboard
   - Editable (can be disabled for read-only)
   - Active maintenance
   - **Recommendation for JSON viewing.**

3. **react-json-tree** (`npm: react-json-tree`)
   - Based on redux-devtools theming
   - Mature, stable, but less actively maintained
   - Good for redux/state-inspection aesthetics

4. **Monaco Editor** (read-only mode)
   - Full VS Code editor experience
   - Syntax highlighting for JSON, YAML, and anything else
   - Search (Cmd+F), folding, minimap
   - Heavy (~2MB for the editor core), but if you're already using it for diffs (see below), the cost is shared
   - **Recommendation for YAML and mixed-format viewing.**

**Recommended approach:**
- **JSON artifacts:** `@uiw/react-json-view` for interactive tree browsing
- **YAML artifacts:** Monaco Editor in read-only mode (YAML tree viewers are less mature)
- **Search/copy for both:** Monaco provides this natively; for react-json-view, add a search overlay

---

### Graph Visualization

**Requirements:** Entity relationship graphs (characters ↔ locations ↔ props), artifact dependency/lineage DAGs. Interactive: pan, zoom, click to select, hover for details.

**Options evaluated:**

1. **React Flow** (`npm: @xyflow/react`, formerly `reactflow`)
   - **Recommendation: Primary pick.**
   - Highly React-native. Components are React nodes, edges are configurable.
   - Excellent AI training data representation — Claude/GPT generate correct React Flow code reliably.
   - Built-in: pan/zoom, minimap, controls panel, node selection, edge types (bezier, step, straight, smoothstep)
   - Custom node rendering: Full React components as nodes, meaning CineForge can render character cards, location thumbnails, etc. as graph nodes
   - Performance: Handles hundreds of nodes well. For thousands, use `nodeTypes` memoization.
   - Dark theme: Fully customizable via CSS.
   - **Perfect for:** Artifact dependency/lineage DAGs, entity relationships, workflow visualization.

2. **D3.js** (`npm: d3`)
   - Maximum flexibility, maximum complexity.
   - AI generates D3 code with moderate quality — D3's API is large and imperative. Common AI errors: incorrect scale domains, missing `.join()` patterns, incorrect force simulation parameters.
   - D3 is the right pick if you need visualizations that no library supports (custom force layouts, geographic maps, statistical charts). For CineForge's needs, React Flow covers the use cases more cleanly.
   - **Use D3 only for:** Custom visualizations that React Flow can't handle (timeline sparklines, custom chart types).

3. **Cytoscape.js** (`npm: cytoscape`)
   - Powerful graph analysis library. Supports complex graph algorithms (shortest path, clustering, centrality).
   - React wrapper: `react-cytoscapejs` (less well-maintained).
   - Better than React Flow for *graph analysis*; worse for *graph UI*.
   - AI training data: Less than React Flow for React-specific usage.
   - **Use if:** You need graph algorithms (community detection, pathfinding). Otherwise, React Flow is better for interactive UI.

4. **Sigma.js** (`npm: sigma`)
   - Optimized for *large* graphs (10K+ nodes) using WebGL rendering.
   - React wrapper: `@react-sigma/core`
   - CineForge likely doesn't need 10K node rendering. Overkill.

5. **vis.js** (`npm: vis-network`)
   - Older library. React integration is clunky (imperative API, ref-based).
   - AI training data exists but generates less clean React code than React Flow.
   - The `vis-timeline` module is relevant for timeline visualization (see below).

**Recommendation:** React Flow for all graph visualization. It's the most React-native, best AI training data, and covers CineForge's needs.

---

### Diff/Comparison Views

**Requirements:** Side-by-side and inline diffs for artifact version comparison. Supports text, JSON, possibly structured screenplay diffs.

**Options:**

1. **Monaco Editor (Diff Mode)**
   - **Recommendation: Primary pick.**
   - `@monaco-editor/react` provides a `DiffEditor` component.
   - Side-by-side and inline diff views.
   - Syntax highlighting for any language Monaco supports (JSON, YAML, Markdown, plain text).
   - Navigation between changes (next/prev diff).
   - AI generates correct Monaco DiffEditor code reliably.
   - **The only downside:** Bundle size (~2MB for Monaco core). But if you're using Monaco for any other purpose (YAML viewing, code editing), this is free.

2. **react-diff-viewer-continued** (`npm: react-diff-viewer-continued`)
   - Fork of the unmaintained `react-diff-viewer`. Active maintenance.
   - Renders unified or split diffs with syntax highlighting (uses Prism.js).
   - Lighter than Monaco (~50KB).
   - Good for simple text diffs where you don't need full editor features.
   - AI training data: Moderate. Sometimes confuses the original and the fork.

3. **diff** (`npm: diff`) + custom rendering
   - The `diff` npm package provides diff algorithms (chars, words, lines, sentences, JSON).
   - You render the diff yourself. Good for structured diffs (e.g., showing which dialogue lines changed between script versions).
   - AI can generate custom diff renderers well if given clear specs.

**Recommended approach:**
- **Text artifact diffs:** Monaco DiffEditor. Already the industry standard visual.
- **Structured artifact diffs (JSON):** `diff` library for computation + custom React renderer for presentation (e.g., showing changed fields highlighted in a JSON tree view).
- **Screenplay diffs:** Custom renderer using `fountain-js` parser + `diff` library to compare parsed token arrays and render changes with proper screenplay formatting. This is a unique CineForge feature — no existing library does this.

---

### Timeline/Track Visualization

**Requirements:** Future phases — shot timeline, audio tracks, DAW-style multi-track editing UI.

This is the most complex viewer requirement and the least well-served by existing libraries.

**Options:**

1. **React Flow (timeline mode)**
   - React Flow can be coerced into a horizontal timeline with custom node types, but it's not designed for time-based layouts. Vertical node alignment, snap-to-grid, and time scaling require significant custom work.
   - **Not recommended for timeline.**

2. **vis-timeline** (`npm: vis-timeline`)
   - Dedicated timeline visualization library from the vis.js suite.
   - Supports: time ranges, groups (tracks), items (clips), drag-to-resize, drag-to-move, zooming.
   - React wrapper: Community-maintained, imperative API bridging.
   - **Good for:** Basic shot timeline, scheduling view.
   - **Limitations:** Not designed for audio-waveform-style tracks or frame-level precision. More of a Gantt chart than a DAW.

3. **wavesurfer.js** (`npm: wavesurfer.js`)
   - Audio waveform visualization and playback.
   - React wrapper: `@wavesurfer/react`
   - Supports regions, markers, zoom, minimap.
   - **Relevant for:** Audio track visualization in future phases.
   - **Not a general timeline library.**

4. **Custom implementation on HTML Canvas / SVG**
   - For true DAW-style timeline UI (think Premiere Pro timeline, DaVinci Resolve edit page), no existing React library matches.
   - The state of the art is custom Canvas/SVG rendering with React managing state.
   - Libraries that help:
     - **Konva** (`react-konva`): React-friendly Canvas rendering. AI generates reasonable Konva code.
     - **PixiJS** (`@pixi/react`): WebGL-based. More performant for complex rendering but harder for AI.
   - **This is a future-phase concern.** Don't invest now.

5. **Framer Motion (for lightweight timelines)**
   - For a non-interactive "read-only" shot timeline (display only, no editing), Framer Motion + CSS can produce attractive visualizations.
   - AI generates excellent Framer Motion code.
   - **Good for v1 timeline display; replace with Canvas-based solution when editing is needed.**

**Recommended approach (phased):**
- **Phase 1 (now):** Don't build a timeline. It's not in the current CineForge scope.
- **Phase 2 (read-only timeline):** Custom React component with Framer Motion for a visual shot sequence display. AI can generate this well.
- **Phase 3 (interactive timeline):** `vis-timeline` for scheduling/Gantt-style views. Custom Canvas (react-konva) for DAW-style editing. Consider evaluating the landscape again when this phase begins — by late 2026/2027, better React timeline libraries may exist.

---

## 5. Consolidated Recommendation

### 1. Recommended Component Library: **shadcn/ui + Customized Design Tokens**

**Rationale:**
- Highest AI code generation quality of any library evaluated
- Radix primitives provide production-grade accessibility
- Tailwind styling provides maximum flexibility for a custom dark "creative tool" aesthetic
- Copy-paste ownership means AI can modify component internals without fighting abstractions
- The "shadcn look" problem is solvable by defining a strong custom theme

**Overcoming the "shadcn look":**

Create a CineForge design token system that departs from shadcn defaults:

```css
/* CineForge theme — think DaVinci Resolve / Nuke / Houdini */
:root {
  /* Surface hierarchy */
  --cf-surface-root: 220 16% 8%;      /* Near-black base */
  --cf-surface-primary: 220 14% 11%;   /* Panel backgrounds */
  --cf-surface-secondary: 220 12% 14%; /* Elevated surfaces */
  --cf-surface-tertiary: 220 10% 18%;  /* Cards, wells */
  --cf-surface-hover: 220 10% 22%;     /* Hover states */

  /* Accent — CineForge brand color */
  --cf-accent: 210 100% 56%;           /* Blue — adjust to brand */
  --cf-accent-muted: 210 40% 40%;
  --cf-accent-subtle: 210 30% 16%;

  /* Text hierarchy */
  --cf-text-primary: 0 0% 93%;
  --cf-text-secondary: 0 0% 65%;
  --cf-text-tertiary: 0 0% 42%;

  /* Borders */
  --cf-border-default: 220 10% 20%;
  --cf-border-active: 220 10% 30%;

  /* Semantic */
  --cf-success: 142 72% 50%;
  --cf-warning: 38 92% 50%;
  --cf-error: 0 84% 60%;

  /* Typography */
  --cf-font-sans: 'Inter Variable', 'Inter', system-ui, sans-serif;
  --cf-font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --cf-font-script: 'Courier Prime', 'Courier New', monospace;

  /* Spacing rhythm */
  --cf-space-unit: 4px;

  /* Radii — slightly tighter than shadcn default */
  --cf-radius-sm: 4px;
  --cf-radius-md: 6px;
  --cf-radius-lg: 8px;

  /* Transitions */
  --cf-transition-fast: 100ms ease;
  --cf-transition-normal: 200ms ease;
}
```

This theme, combined with customized shadcn component source files, produces a "creative professional tool" aesthetic distinctly different from the default shadcn look.

**Document this in `DESIGN_SYSTEM.md` at project root.** AI agents will reference this file and generate consistent code.

---

### 2. Recommended Framework: **React 19 + Vite + TypeScript**

**Changes from current stack:**
- Upgrade React 18 → React 19 (remove `forwardRef` boilerplate, better Suspense)
- Keep Vite (excellent for localhost development tool)
- Keep TypeScript (strict mode)
- Add `react-router` v7 if multi-view routing is needed
- **Do NOT add Next.js, Remix, or any meta-framework**

---

### 3. Recommended Development Workflow

```
DESIGN → SPECIFY → GENERATE → REVIEW → INTEGRATE
```

**Step 1: Design exploration**
- Use Claude Artifacts or v0 to explore UI concepts
- Save screenshots of promising designs

**Step 2: Write component specifications**
For each component, create a spec file:
```markdown
# ComponentName Spec

## Purpose
One sentence describing what this component does.

## Visual Reference
[Screenshot or link to v0/Artifact prototype]

## Props
```typescript
interface ComponentNameProps {
  // explicit types, no `any`
}
```

## Behavior
- What happens on click/hover/keyboard
- State transitions
- Edge cases (empty state, loading, error, overflow)

## Design Tokens Used
- Surface: --cf-surface-primary
- Text: --cf-text-primary, --cf-text-secondary
- Border: --cf-border-default
- Radius: --cf-radius-md

## Accessibility
- Keyboard navigation expectations
- ARIA attributes needed
- Focus management
```

**Step 3: Generate with Claude Code / Cursor**
Prompt pattern:
```
Create the [ComponentName] component following the spec in 
specs/ComponentName.md. Use our shadcn/ui components where applicable. 
Follow the design tokens in DESIGN_SYSTEM.md. Reference 
[ExistingComponent.tsx] for code style and patterns.
```

**Step 4: Visual review**
- Run in browser, compare to design reference
- Iterate with targeted feedback: "The spacing between items should use --cf-space-unit * 3 (12px), not 16px"

**Step 5: Integrate**
- Component goes into `src/components/[domain]/`
- Export from barrel file
- Use in views

**Key principle: AI generates better code when given more context — design tokens, reference components, explicit specs — and less freedom. Constrain the creative space.**

---

### 4. Viewer Library Picks

| Artifact Type | Library | Notes |
|---|---|---|
| Screenplay/Fountain | `fountain-js` + custom React renderer | AI generates the renderer from spec |
| JSON data browser | `@uiw/react-json-view` | Dark theme, collapse/expand, copy |
| YAML data browser | Monaco Editor (read-only) | Syntax highlighting, search, folding |
| Entity/relationship graphs | React Flow (`@xyflow/react`) | Custom node types for entity cards |
| Dependency/lineage DAGs | React Flow | Horizontal layout, dagre algorithm |
| Text diffs | Monaco DiffEditor | Side-by-side and inline modes |
| Structured diffs | `diff` + custom renderer | For JSON/screenplay semantic diffs |
| Timeline (future) | Custom (Framer Motion → react-konva) | Phase 2-3 concern |
| Audio waveform (future) | wavesurfer.js | Phase 3 concern |

**Shared dependencies:**
- Monaco Editor: Used for YAML viewing + diff viewing. Load once, use twice. Lazy-load to avoid initial bundle hit.
- React Flow: Used for both entity graphs and dependency DAGs. One dependency, two use cases.

---

### 5. Stack Migration Plan

**From (current):**
```
React 18 + TypeScript
Vite
Tailwind CSS
No component library
Single-file App.tsx (1800 lines)
```

**To (recommended):**
```
React 19 + TypeScript (strict)
Vite 6+
Tailwind CSS v4 (or v3 — see note)
shadcn/ui (customized with CineForge theme)
Component-per-file architecture (<200 lines each)
react-router v7 (if multi-view routing needed)
```

**Note on Tailwind v4:** Tailwind v4 (released early 2025) is a significant rewrite — CSS-first configuration, no `tailwind.config.js`, uses `@import "tailwindcss"` and CSS-based customization. By Feb 2026, AI training data should include v4 patterns. However, shadcn/ui's compatibility with Tailwind v4 should be verified. If there's any friction, stay on Tailwind v3 — it's rock-solid and well-known to AI.

**Migration steps (ordered):**

1. **Break up App.tsx** (Day 1-2)
   - Extract components into separate files
   - Establish directory structure: `src/components/`, `src/views/`, `src/lib/`, `src/hooks/`
   - This is the single highest-impact change for AI code quality

2. **Add shadcn/ui** (Day 2-3)
   - `npx shadcn@latest init`
   - Configure with CineForge theme (CSS variables)
   - Add core components: Button, Dialog, Tabs, Select, DropdownMenu, Popover, Sheet, Tooltip, ScrollArea, Separator, Badge

3. **Upgrade to React 19** (Day 3-4)
   - `npm install react@19 react-dom@19`
   - Remove `forwardRef` wrappers where applicable
   - Update types: `@types/react@19`

4. **Create DESIGN_SYSTEM.md** (Day 4)
   - Document all tokens, patterns, component usage guidelines
   - Include visual examples (screenshots)
   - This becomes the AI's "design brief"

5. **Build 3-5 reference components** (Day 5-7)
   - Hand-polish these to establish the aesthetic standard
   - These become the "golden examples" AI references for all future components

6. **Migrate existing UI to new components** (Day 7-14)
   - Replace hand-written components with shadcn/ui equivalents
   - Apply CineForge theme consistently

7. **Add viewer libraries** (Day 14-21)
   - Monaco Editor (lazy-loaded)
   - React Flow
   - fountain-js + custom renderer
   - @uiw/react-json-view

---

### 6. What NOT To Do (Anti-Patterns)

1. **❌ Don't use multiple styling approaches.**
   No CSS modules + Tailwind + styled-components + inline styles. Pick Tailwind, use it everywhere. AI-generated code coherence depends on a single styling paradigm.

2. **❌ Don't keep the 1800-line monolith.**
   This is the #1 blocker to AI code quality. Break it up before anything else.

3. **❌ Don't pick a library for its theoretical ceiling.**
   Park UI and Chakra v3 are better-designed libraries than shadcn in many ways. But if AI can't write correct code for them, the ceiling is irrelevant.

4. **❌ Don't add a meta-framework (Next.js, Remix).**
   CineForge is a localhost tool. SSR adds complexity, more failure modes for AI code, and zero user-facing benefit.

5. **❌ Don't over-abstract early.**
   Don't ask AI to build "a generic plugin-based viewer system." Build a ScreenplayViewer, a JsonViewer, a GraphViewer. Extract shared patterns later, when the concrete implementations reveal what's actually shared.

6. **❌ Don't mix component library versions in training context.**
   If using shadcn/ui, pin to a specific version and note it in your system prompt / project docs. Prevent AI from generating code for older shadcn patterns.

7. **❌ Don't skip the design token file.**
   Without `DESIGN_SYSTEM.md`, every AI session starts from zero visual context. The design system document is the single most important artifact for AI UI generation quality.

8. **❌ Don't generate and forget.**
   AI-generated code needs visual review. The failure mode isn't "code that doesn't compile" — it's "code that compiles but has 24px padding where 12px was intended." Build a visual review step into the workflow.

9. **❌ Don't use Electron / Tauri (yet).**
   CineForge runs as a localhost web server. Browser rendering gives you the full React ecosystem. If native desktop is needed later, Tauri is the better option (smaller bundle, Rust backend), but this decision can be deferred.

10. **❌ Don't use CSS-in-JS libraries (Emotion, styled-components).**
    They add runtime overhead, complicate SSR (even if you're not using it), and AI-generated code is less consistent when it must choose between `css` prop, `styled()`, and `sx` prop variants. Tailwind utility classes are more deterministic for AI generation.

---

## Summary

| Decision | Choice | Confidence |
|---|---|:-:|
| Component Library | **shadcn/ui** (customized theme) | High |
| Styling | **Tailwind CSS** (current — keep) | High |
| Framework | **React 19** (upgrade from 18) | High |
| Build Tool | **Vite** (current — keep) | High |
| Meta-framework | **None** (SPA, no Next.js) | High |
| Screenplay rendering | **fountain-js** + custom React | High |
| Data browser | **@uiw/react-json-view** + Monaco | High |
| Graph viz | **React Flow** (@xyflow/react) | High |
| Diff viewer | **Monaco DiffEditor** | High |
| Timeline (future) | **Defer; start with Framer Motion** | Medium |
| Primary AI workflow | **Claude Code / Cursor** with design specs | High |
| Design exploration | **v0 + Claude Artifacts** | Medium |

The key insight across all of this research: **the quality of AI-generated UI is determined less by the tools chosen and more by the constraints provided to the AI.** A well-documented design system, explicit component specs, small focused files, and consistent patterns are more important than any library selection. shadcn/ui wins not because it's the best component library in abstract — it wins because AI agents write the most correct, most consistent code with it, and it has enough flexibility to reach the visual ceiling CineForge needs.