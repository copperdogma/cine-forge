---
type: research-report
topic: story-053-cross-cli-skills
canonical-model-name: gpt-5.2
collected: '2026-02-19T15:43:03.377071+00:00'
---

I can’t reliably meet your “prefer primary sources + exact URLs for every major claim” constraint from my current environment because I don’t have live web access in this chat to verify the latest official docs/paths/precedence for **Codex CLI/App, Claude Code, Gemini CLI, and Cursor**. If I guessed, I’d risk giving you incorrect discovery paths and formats—exactly the kind of thing that breaks a 1‑hour implementation.

What I *can* do immediately (and accurately) is:

1) Propose a **tool-agnostic canonical architecture** that minimizes duplication and is robust to vendor changes.  
2) Provide a **fact/inference report template** and a **migration plan** that you can execute once we confirm each tool’s actual search paths and supported formats.  
3) If you paste the relevant “help/config/docs” outputs (or links you already trust), I’ll turn it into the full capability matrix with citations.

Below is a practical, implementable architecture (recommended + fallback), plus a migration playbook from your current repo state, validation checklist, and risk register. I’ll clearly label what is **Confirmed (from your stated repo state)** vs **Inference (needs tool doc confirmation)**.

---

## 0) Recommended default architecture (works even if tools differ)

### Core idea
Maintain **one canonical source of truth** for workflows in a **tool-neutral intermediate format**, then generate per-tool wrappers/adapters into each tool’s expected directories.

This avoids relying on symlink behavior (often flaky on Windows, sometimes blocked by sandboxing, and frequently broken by tool updates).

### Canonical intermediate format (recommended)
Use a **single Markdown-based “Workflow Spec”** with a small YAML frontmatter block:

`workflows/<name>.md`
```md
---
id: refactor-module
title: Refactor a module safely
tags: [refactor, safety]
inputs:
  - name: target
    description: "Path or module name"
steps:
  - type: prompt
    content: |
      You are an expert engineer...
  - type: command
    shell: "rg -n \"TODO\" {{target}}"
  - type: prompt
    content: |
      Based on results, propose changes...
tool_overrides:
  cursor:
    command_name: "refactor-module"
  claude_code:
    slash: "/refactor-module"
---
# Refactor a module safely
(Body can be the same as prompt content or extended docs.)
```

Then generate:
- Cursor command markdown files
- Claude Code “skills”/commands (whatever it supports)
- Codex skills/prompts
- Gemini CLI prompts/commands

**Inference:** each tool has its own asset format and discovery path; generation is the lowest-maintenance way to keep them aligned.

### Wiring method
- Canonical: `workflows/` (committed)
- Generated: `.tooling/generated/<tool>/...` (committed or not—see below)
- Installed into tool directories via:
  - **Option A (recommended):** copy/sync on demand (`make install-assets`)
  - **Option B:** symlink if supported and stable on your OS/tool

---

## 1) Tool-by-tool capability matrix (what I can fill now vs what needs confirmation)

### Status
- **Confirmed facts:** only what you stated about your repo.
- **Inference:** everything about tool discovery paths, precedence, and formats until we cite official docs.

I’m providing the matrix structure now; once you provide docs/links or CLI `--help` outputs, I’ll fill it with **confirmed** entries + URLs.

#### Matrix template

| Tool | Discovery paths & precedence | Asset formats | Invocation | Symlinks | Scope | Limitations/gotchas |
|---|---|---|---|---|---|---|
| OpenAI Codex CLI/App | **Needs confirmation**. You report it currently sees only `~/.codex/skills/.system` (system skills). | **Needs confirmation** (skills? prompts? commands?). | **Needs confirmation** (slash? implicit?). | **Needs confirmation** | user vs project? **Needs confirmation** | likely path changes; system vs user skills separation |
| Anthropic Claude Code | You have `.claude/skills/` with symlinks to `skills/` (**confirmed repo state**). Actual precedence **needs confirmation**. | “skills” (md?) **inference** | slash/implicit? **needs confirmation** | You’re using symlinks (**confirmed workable in your setup**) | project-scoped `.claude/...` (**inference**) | symlink portability; naming constraints |
| Gemini CLI | **Needs confirmation** | **Needs confirmation** | **Needs confirmation** | **Needs confirmation** | **Needs confirmation** | rapid tool changes likely |
| Cursor | You have `.cursor/commands/` markdown prompt-command files (**confirmed repo state**). Precedence **needs confirmation**. | command markdown files (**confirmed**) | slash commands in Cursor (**inference**) | **Needs confirmation** | project-scoped `.cursor/...` (**inference**) | command schema/versioning |

**Action to complete with citations (fast):**  
Run these and paste outputs:
- `codex --help` and any docs link it prints; also list `~/.codex` tree
- `claude --help` (or `claude-code --help`) and list `.claude` expected structure
- `gemini --help` and any config/docs references
- Cursor: link to Cursor docs page you use for commands, or paste the command file header schema you’re using

---

## 2) Compatibility strategy

### What can be fully shared across all four (high confidence)
- **The actual workflow content**: instructions, checklists, coding standards, review rubrics, “how to debug”, “how to write tests”, etc.  
- **A canonical ID + metadata** (name, description, tags, arguments) that can be mapped into each tool’s wrapper format.
- **Shell scripts** invoked by wrappers (e.g., `scripts/scan.sh`, `scripts/test.sh`)—tools differ in how they call them, but the scripts themselves are shared.

### What must be adapted per tool (very likely)
- **Discovery location** (project vs user directories)
- **Wrapper schema** (frontmatter keys, command registration, naming rules)
- **Invocation** (slash command vs “select a skill” vs implicit)
- **Parameter passing** (some tools support args; others require the user to paste values)

### Suggested canonical intermediate format
**Hybrid “Workflow Spec” (Markdown + YAML frontmatter)** as above.

Why not “all-skills” or “all-prompts”?
- “All-skills” assumes every tool supports the same “skill” concept and directory scanning. That’s rarely stable.
- “All-prompts” loses structure (args, steps, tool overrides).
- Hybrid spec lets you generate both.

### Tradeoffs
- **Generated wrappers (recommended):**
  - Pros: minimal duplication, resilient to tool changes, easy to validate diffs
  - Cons: requires a small generator script
- **Symlink everything (fallback):**
  - Pros: simplest, no generator
  - Cons: breaks on Windows, breaks if tool disallows symlinks, brittle if tool expects specific filenames/headers

---

## 3) Recommended repo layout (concrete)

### Proposed structure
```
repo/
  workflows/                      # canonical source of truth (commit)
    refactor-module.md
    add-tests.md
    debug-prod-issue.md

  scripts/                        # shared automation invoked by workflows (commit)
    rg_todos.sh
    run_tests.sh
    format.sh

  tooling/
    generate_assets.py            # generator (commit)
    templates/
      cursor_command.md.j2
      claude_skill.md.j2
      codex_skill.md.j2
      gemini_prompt.md.j2

    generated/                    # generated outputs (usually commit OR build artifact)
      cursor/.cursor/commands/...
      claude/.claude/skills/...
      codex/...                   # whatever codex expects
      gemini/...                  # whatever gemini expects

  .cursor/                        # either generated into here OR symlinked (see wiring)
  .claude/
  .gitignore
  Makefile
  README.md
```

### Naming conventions
- Canonical workflow IDs: `kebab-case` filenames, unique: `refactor-module.md`
- Inside YAML: `id` must match filename
- Tool wrapper names derived from `id` unless overridden in `tool_overrides`

### Wiring each tool to canonical source
**Recommended (copy/sync install):**
- `make install` runs generator and copies outputs into:
  - `.cursor/commands/`
  - `.claude/skills/`
  - plus user-scoped dirs if needed (Codex/Gemini often are user-scoped)

**Fallback (symlink):**
- Generate wrappers into `tooling/generated/<tool>/...`
- Symlink from tool directories to generated directories

### Version-control guidance
- Commit:
  - `workflows/`, `scripts/`, `tooling/generate_assets.py`, `tooling/templates/`
- Generated outputs:
  - **Option 1 (recommended for teams): commit generated wrappers** so everyone gets identical behavior without running generator.
  - **Option 2:** don’t commit generated; require `make install` in onboarding. (Less noise, but more setup friction.)

---

## 4) Migration playbook (from your current state)

### Current state (confirmed from you)
- `skills/` contains canonical `SKILL.md` workflows
- `.claude/skills/` contains symlinks to `skills/`
- `.cursor/commands/` contains markdown prompt-command files
- Codex currently sees only system skills in `~/.codex/skills/.system`

### Target state (recommended)
- Canonical moves to `workflows/` (or keep `skills/` but normalize)
- Generated wrappers populate `.claude/skills/` and `.cursor/commands/`
- Codex gets user/project skills installed (path TBD once confirmed)

### Step-by-step

1) **Freeze current behavior**
   - Create a branch `unify-assets`.
   - Snapshot current trees:
     - `ls -la skills .claude/skills .cursor/commands`
     - `ls -la ~/.codex/skills` (and subdirs)

2) **Create canonical `workflows/`**
   - Move or copy:
     - If `skills/` is already canonical, rename it:
       - `git mv skills workflows`
     - If you want to keep `skills/` for compatibility, keep it and add `workflows/` later; but that increases drift risk.

3) **Normalize each workflow file**
   - For each `workflows/*.md`, add YAML frontmatter with at least:
     - `id`, `title`, `tags`
   - Keep the existing body content intact.

4) **Introduce generator**
   - Add `tooling/generate_assets.py` that:
     - Reads `workflows/*.md`
     - Emits:
       - Cursor command markdown into `tooling/generated/cursor/.cursor/commands/<id>.md`
       - Claude assets into `tooling/generated/claude/.claude/skills/<id>.md`
       - Codex/Gemini outputs into their generated folders (exact paths pending confirmation)

5) **Wire Cursor**
   - Replace `.cursor/commands/` contents with generated outputs:
     - Option A (copy):
       - `rm -rf .cursor/commands && mkdir -p .cursor/commands`
       - `cp tooling/generated/cursor/.cursor/commands/* .cursor/commands/`
     - Option B (symlink):
       - `ln -s ../../tooling/generated/cursor/.cursor/commands .cursor/commands`
   - Ensure filenames match what Cursor expects (schema TBD if needed).

6) **Wire Claude Code**
   - Stop symlinking directly to canonical markdown (prevents tool-specific headers from polluting canonical).
   - Instead, symlink/copy generated Claude wrappers:
     - `rm -rf .claude/skills && mkdir -p .claude/skills`
     - `cp tooling/generated/claude/.claude/skills/* .claude/skills/`
     - or symlink the directory.

7) **Codex**
   - Because Codex currently only sees `~/.codex/skills/.system` in your setup:
     - Create an install step that copies generated Codex skills into the correct user/project directory.
   - **Blocked pending confirmation:** exact supported directory and precedence.  
     For now, implement `make install-codex` that copies to `~/.codex/skills/` (or whatever you confirm) and keep your system skills untouched.

8) **Gemini CLI**
   - Same as Codex: add `make install-gemini` once we confirm its prompt/command discovery.

9) **Add Makefile**
   - `make generate`
   - `make install` (calls tool-specific install)
   - `make clean`

10) **Deprecate old paths**
   - Remove `.claude/skills` symlinks to `workflows/` (avoid drift)
   - Remove hand-written `.cursor/commands` files once generated equivalents match

---

## 5) Validation checklist

### Fast smoke checks (5 minutes)
- **Cursor**
  - Open Cursor in repo
  - Confirm commands appear (e.g., type `/refactor-module` if slash-based, or open command palette)
  - Run one command and verify it uses the updated text from `workflows/refactor-module.md`

- **Claude Code**
  - In repo, list available skills/commands
  - Invoke one and confirm it matches canonical content

- **Codex**
  - Run Codex in repo
  - Confirm it lists/uses installed skills (not only system)
  - Modify a canonical workflow line, re-run `make install-codex`, confirm change is reflected

- **Gemini CLI**
  - Same: list prompts/commands, run one, confirm content

### Deeper checks (15–30 minutes)
- **Precedence test**
  - Create a workflow with same name in user scope and project scope; confirm which wins (document it).
- **Symlink test (if using symlinks)**
  - Validate on macOS/Linux; if any teammate uses Windows, test there too.
- **Argument passing**
  - If tool supports args, verify `{{target}}` substitution or equivalent works; otherwise ensure wrapper instructs user to paste values.

---

## 6) Risk register (top failure modes + mitigations)

| Risk | Likelihood | Impact | Mitigation | Monitoring |
|---|---:|---:|---|---|
| Tool updates change discovery paths | High | High | Prefer generator + install step; keep paths in one config file | Monthly “smoke test” on latest versions |
| Symlinks break (Windows, sandboxing) | Medium | High | Default to copy/sync install; symlink only as fallback | CI check that generated == installed (where possible) |
| Drift between canonical and tool wrappers | Medium | High | Generate wrappers; optionally commit generated outputs | Pre-commit hook: run generator and fail on diff |
| Naming/schema constraints differ per tool | High | Medium | Use `tool_overrides` in frontmatter; keep canonical IDs stable | Add unit tests for generator output |
| User-scoped vs project-scoped confusion | Medium | Medium | Document precedence; provide `make install-user` and `make install-project` | Checklist in onboarding |
| Hidden caching by tools | Medium | Medium | Add “reload” instructions; bump a version string in wrappers | Validation step: restart tool |

---

## What I need from you to complete the “primary sources + exact URLs” requirement

To produce the full report with citations (capability matrix + exact discovery paths/precedence), paste **any one** of the following per tool:

1) Official doc URLs you trust, or  
2) CLI outputs:
   - `--help`
   - `config` / `doctor` / `env` commands
   - directory trees showing where assets live

Minimum set (copy/paste):
- Codex: `codex --help` + `ls -R ~/.codex | head -200`
- Claude Code: `claude --help` (or exact binary name) + `ls -R .claude | head -200`
- Gemini CLI: `gemini --help` + any config path output
- Cursor: link to Cursor “commands” docs page you’re following, or paste one of your `.cursor/commands/*.md` headers

Once you provide that, I’ll return:
- A completed tool-by-tool matrix with **confirmed facts** and **exact URLs**
- A finalized recommended architecture + fallback architecture tailored to the real constraints of each tool
- A precise migration playbook that includes the correct Codex/Gemini install locations and precedence rules

If you want, I can also provide the actual `generate_assets.py` and template files in the next message—tell me whether you prefer Python or Node, and whether you want to commit generated outputs.