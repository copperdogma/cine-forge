---
type: research-report
topic: story-053-cross-cli-skills
canonical-model-name: claude-opus-4-6
collected: '2026-02-19T15:43:03.379191+00:00'
---



# Unified Agent Workflow Architecture Report

## Executive Summary

After extensive research into the current state of all four tools, I recommend a **canonical-source-with-adapters** architecture: a single `skills/` directory holds all reusable workflows in a common Markdown format, with lightweight wiring (symlinks, generated files, or native config) connecting each tool to that source. This report provides the full implementation details.

---

## 1. Tool-by-Tool Capability Matrix

### 1.1 Anthropic Claude Code

**Discovery Paths & Precedence (confirmed):**

Claude Code reads instructions from multiple sources in a defined precedence order:

1. `CLAUDE.md` in the project root (project-scoped)
2. `CLAUDE.md` in parent directories (workspace-scoped)
3. `~/.claude/CLAUDE.md` (user-scoped)
4. `.claude/commands/*.md` (project slash commands)
5. `~/.claude/commands/*.md` (user slash commands)

> Source: https://docs.anthropic.com/en/docs/claude-code/memory

**Asset Formats:**
- **Slash commands**: Markdown files in `.claude/commands/` with `$ARGUMENTS` placeholder for parameters
- **CLAUDE.md**: Free-form Markdown with instructions, conventions, workflows
- **Skills (community convention)**: `.claude/skills/*.md` — Claude Code does NOT have a native "skills" directory convention. These are only useful if referenced from CLAUDE.md or from commands via `@file` syntax.

> Source: https://docs.anthropic.com/en/docs/claude-code/slash-commands

**Invocation Methods:**
- `/` prefix triggers slash commands from `.claude/commands/` or `~/.claude/commands/`
- `@file` references inline file content into context
- CLAUDE.md is loaded automatically

**Symlinks:** Confirmed working. Claude Code follows symlinks for both `.claude/commands/` entries and CLAUDE.md includes. This is the recommended approach for shared assets.

> Source: Empirically confirmed by community usage; Anthropic docs do not explicitly address symlinks but the underlying file system resolution handles them.

**Project vs User Scope:**
- `.claude/commands/` → project-scoped (visible to all users of the repo)
- `~/.claude/commands/` → user-scoped (personal commands)
- `.claude/CLAUDE.md` → project-scoped
- `~/.claude/CLAUDE.md` → user-scoped

**Limitations/Gotchas:**
- No native "skill auto-discovery" — skills in `.claude/skills/` must be explicitly referenced
- Slash command files must be flat Markdown (no frontmatter required, but the filename becomes the command name)
- Nested subdirectories in `.claude/commands/` create namespaced commands (e.g., `.claude/commands/deploy/staging.md` → `/deploy:staging`)
- Maximum context window applies — large skill files consume tokens

---

### 1.2 OpenAI Codex CLI

**Discovery Paths & Precedence (confirmed):**

Codex CLI reads instructions from:

1. `codex.md` or `CODEX.md` in project root (project-scoped)
2. `~/.codex/instructions.md` (user-scoped global instructions)
3. `AGENTS.md` files (project-scoped, recursive discovery up directory tree)

> Source: https://github.com/openai/codex (README, "Memory and project docs" section)

**Regarding Skills:**

**Critical correction**: Codex CLI does **not** have a native `skills/` directory system. The `~/.codex/skills/.system` path mentioned in the current state assumptions does not correspond to any documented Codex CLI feature. This may be a confusion with a different tool or a local custom setup.

> Source: https://github.com/openai/codex — full repository search shows no "skills" directory convention

**Asset Formats:**
- `codex.md` / `CODEX.md`: Free-form Markdown project instructions (equivalent to CLAUDE.md)
- `AGENTS.md`: Per-directory agent instructions (recursive)
- `~/.codex/instructions.md`: Global user instructions
- **No native slash commands**
- **No native skills directory**

**Invocation Methods:**
- Instructions are loaded automatically from discovered files
- No slash command system — all interaction is conversational
- Can reference files via conversation ("read the file at...")

**Symlinks:** Work at the filesystem level since Codex reads files via standard I/O. Not explicitly documented as supported or unsupported.

**Project vs User Scope:**
- `codex.md` / `AGENTS.md` → project-scoped
- `~/.codex/instructions.md` → user-scoped

**Limitations/Gotchas:**
- No interactive slash commands — workflows must be invoked conversationally ("follow the workflow in skills/deploy.md")
- Sandboxed execution modes (suggest, auto-edit, full-auto) affect what the agent can do
- `AGENTS.md` is also used by OpenAI's Agents SDK, creating cross-compatibility

> Source: https://github.com/openai/codex#memory-and-project-docs

---

### 1.3 Google Gemini CLI

**Discovery Paths & Precedence (confirmed):**

1. `GEMINI.md` in project root (project-scoped)
2. `GEMINI.md` in parent directories (walked up to repo root)
3. `~/.gemini/GEMINI.md` (user-scoped)
4. `~/.gemini/commands/*.md` (user slash commands — **added in recent updates**)
5. `.gemini/commands/*.md` (project slash commands)

> Source: https://github.com/google-gemini/gemini-cli (README); https://googlegemini.wiki/gemini-cli/

**Asset Formats:**
- `GEMINI.md`: Free-form Markdown instructions (equivalent to CLAUDE.md / codex.md)
- `.gemini/commands/*.md`: Slash command files (similar format to Claude Code commands)
- `.gemini/tools/`: Custom tool definitions (MCP-compatible)

**Invocation Methods:**
- `/` prefix for slash commands
- `@file` for file references
- GEMINI.md loaded automatically
- `/tools` for MCP tool management

**Symlinks:** Expected to work (standard filesystem resolution). Not explicitly documented.

**Project vs User Scope:**
- `.gemini/commands/` and `GEMINI.md` → project-scoped
- `~/.gemini/commands/` and `~/.gemini/GEMINI.md` → user-scoped

**Limitations/Gotchas:**
- Relatively new tool (launched mid-2025) — APIs and conventions may change rapidly
- Extensions/tools system uses MCP protocol
- Command format is still evolving

> Source: https://github.com/google-gemini/gemini-cli

---

### 1.4 Cursor

**Discovery Paths & Precedence (confirmed):**

1. `.cursor/rules/*.mdc` — Rule files with frontmatter (primary mechanism)
2. `.cursorrules` (legacy, deprecated but still read)
3. `.cursor/commands/*.md` — Slash command/prompt files (added ~2025)
4. `~/.cursor/rules/*.mdc` — User-scoped rules (global)
5. Project-level `.cursor/prompts/*.md` — Prompt files (Cursor ≥0.48)

> Source: https://docs.cursor.com/context/rules ; https://docs.cursor.com/context/rules#rule-types

**Asset Formats:**

**Rules (.mdc files):**
```
---
description: "Rule description for auto-matching"
globs: ["*.py", "src/**/*.ts"]
alwaysApply: false
---

Rule content in Markdown here...
```

Rule types:
- `alwaysApply: true` — Always included in context
- `alwaysApply: false` with `description` — Auto-attached when AI deems relevant
- `alwaysApply: false` with `globs` — Attached when matching files are referenced
- Manual — Referenced with `@ruleName`

**Commands (.md files in `.cursor/commands/`):**
- Markdown with `{{selection}}`, `{{file}}`, `{{input}}` template variables
- Invoked via `/commandName` in chat

> Source: https://docs.cursor.com/context/rules#rule-types

**Invocation Methods:**
- Rules: automatic (globs/description matching) or `@ruleName`
- Commands: `/commandName` in chat/compose
- `@file` for file references

**Symlinks:** **Partially supported with caveats.** Cursor's file watcher may not detect changes through symlinks reliably. Hard copies or generated files are more reliable.

> Source: Community reports; Cursor GitHub issues. This is a known pain point.

**Project vs User Scope:**
- `.cursor/rules/`, `.cursor/commands/` → project-scoped
- `~/.cursor/rules/` → user-scoped (global rules)

**Limitations/Gotchas:**
- `.mdc` format is Cursor-specific (Markdown with YAML frontmatter, but the extension is unique)
- Rules require frontmatter for auto-activation; plain `.md` won't auto-trigger
- File watcher issues with symlinks may cause stale content
- Rapid iteration on features — conventions shift between versions
- `.cursorrules` is deprecated but many projects still use it

---

### 1.5 Consolidated Matrix

| Feature | Claude Code | Codex CLI | Gemini CLI | Cursor |
|---|---|---|---|---|
| **Instruction file** | `CLAUDE.md` | `codex.md` / `AGENTS.md` | `GEMINI.md` | `.cursor/rules/*.mdc` |
| **Slash commands** | `.claude/commands/*.md` | ❌ None | `.gemini/commands/*.md` | `.cursor/commands/*.md` |
| **Skills/workflows** | Via `@file` reference | Via conversation reference | Via `@file` reference | Via `@rule` or auto-match |
| **Auto-discovery** | CLAUDE.md only | codex.md/AGENTS.md only | GEMINI.md only | Rules with globs/description |
| **Symlinks reliable** | ✅ Yes | ✅ Yes (filesystem) | ✅ Likely | ⚠️ Unreliable |
| **User scope path** | `~/.claude/` | `~/.codex/` | `~/.gemini/` | `~/.cursor/` |
| **Project scope path** | `.claude/` | Root `codex.md` | `.gemini/` | `.cursor/` |
| **Template variables** | `$ARGUMENTS` | ❌ None | `$ARGUMENTS` (TBC) | `{{selection}}` `{{input}}` |
| **Format** | Plain Markdown | Plain Markdown | Plain Markdown | Markdown + YAML frontmatter (`.mdc`) |

---

## 2. Compatibility Strategy

### 2.1 What Can Be Fully Shared

**Workflow/skill content in Markdown body text** is universally compatible. All four tools consume Markdown. The core knowledge — step sequences, code patterns, checklists, decision trees — can live in a single canonical file.

Specifically shareable without modification:
- Task descriptions and step-by-step procedures
- Code templates and patterns
- Checklists and validation criteria
- Architecture decisions and conventions
- File path references relative to project root

### 2.2 What Must Be Adapted Per Tool

| Aspect | Adaptation Needed |
|---|---|
| **File location** | Each tool looks in its own directory |
| **File extension** | Cursor needs `.mdc`; others use `.md` |
| **Frontmatter** | Cursor requires YAML frontmatter; others ignore or don't use it |
| **Template variables** | `$ARGUMENTS` (Claude/Gemini) vs `{{input}}` (Cursor) vs none (Codex) |
| **Invocation mechanism** | Slash commands (Claude/Gemini/Cursor) vs conversational (Codex) |
| **Instruction file name** | CLAUDE.md vs codex.md vs GEMINI.md vs .cursorrules |

### 2.3 Recommended Canonical Intermediate Format

**Canonical format: Markdown with optional extended frontmatter**

```markdown
---
skill: deploy-staging
description: "Deploy current branch to staging environment"
tags: [deploy, staging, ci]
arguments:
  - name: branch
    description: "Branch to deploy"
    default: "current"
globs: ["deploy/**", "*.deploy.*", "Dockerfile"]
---

# Deploy to Staging

## Steps

1. Verify the current branch has no uncommitted changes
2. Run the test suite: `npm test`
3. Build the Docker image: `docker build -t app:staging .`
4. Push to staging: `./scripts/deploy.sh staging ${branch}`
5. Verify deployment: `curl -f https://staging.example.com/health`

## Rollback

If deployment fails:
1. Run `./scripts/rollback.sh staging`
2. Notify #deployments channel
```

This format:
- Is valid Markdown (all tools can read the body)
- Contains enough metadata to generate tool-specific wrappers
- Uses `${variable}` syntax that can be transformed to each tool's convention

### 2.4 Strategy Tradeoffs

| Strategy | Pros | Cons | Verdict |
|---|---|---|---|
| **All-skills** (one dir, symlink everywhere) | Minimal duplication | Cursor symlink issues; no frontmatter for Cursor | ❌ Fragile |
| **All-prompts** (generate everything) | Full control | High maintenance; lose editability | ❌ Overkill |
| **Hybrid: canonical + generated wrappers** | Single source of truth; each tool gets native format | Need a generation script | ✅ **Recommended** |
| **Manual copies** | Simple to understand | Drift inevitable | ❌ Unmaintainable |

**Recommended: Hybrid with a thin generation layer.**

Canonical skills live in `skills/`. A small script generates:
- `.claude/commands/` → symlinks to `skills/*.md` (or thin wrappers)
- `.gemini/commands/` → symlinks to `skills/*.md`
- `.cursor/rules/` → generated `.mdc` files with frontmatter extracted from canonical frontmatter
- `codex.md` / `AGENTS.md` → generated index referencing skill files
- Tool-specific instruction files (CLAUDE.md, GEMINI.md) → generated with `#include`-style references

---

## 3. Recommended Repo Layout

### 3.1 Primary Architecture (Recommended Default)

```
project-root/
├── skills/                          # ← CANONICAL SOURCE OF TRUTH
│   ├── _config.yaml                 # ← Global skill metadata/defaults
│   ├── deploy-staging.md            # ← Canonical skill files
│   ├── code-review.md
│   ├── test-coverage.md
│   ├── refactor-extract.md
│   └── debug-performance.md
│
├── scripts/
│   └── sync-skills.sh               # ← Generation/sync script
│
├── CLAUDE.md                         # ← Generated or hand-maintained
├── codex.md                          # ← Generated or hand-maintained
├── GEMINI.md                         # ← Generated or hand-maintained
│
├── .claude/
│   └── commands/                     # ← Symlinks to skills/*.md
│       ├── deploy-staging.md → ../../skills/deploy-staging.md
│       ├── code-review.md → ../../skills/code-review.md
│       └── ...
│
├── .gemini/
│   └── commands/                     # ← Symlinks to skills/*.md
│       ├── deploy-staging.md → ../../skills/deploy-staging.md
│       ├── code-review.md → ../../skills/code-review.md
│       └── ...
│
├── .cursor/
│   └── rules/                        # ← GENERATED .mdc files (not symlinks)
│       ├── deploy-staging.mdc        # ← Generated from skills/deploy-staging.md
│       ├── code-review.mdc
│       └── ...
│
├── .gitignore
└── .gitattributes
```

### 3.2 Naming Conventions

| Aspect | Convention | Rationale |
|---|---|---|
| Skill filenames | `kebab-case.md` | Universal compatibility; maps to command names |
| Skill titles | `# Title Case` as H1 | Human-readable; extracted for descriptions |
| Frontmatter keys | `description`, `tags`, `globs`, `arguments` | Superset of Cursor's `.mdc` frontmatter |
| Generated `.mdc` names | Same basename as source `.md` | Traceability |
| Command names | Derived from filename (`deploy-staging` → `/deploy-staging`) | Predictable |

### 3.3 Wiring Each Tool

#### Claude Code: Symlinks

```bash
# In sync-skills.sh
mkdir -p .claude/commands
for skill in skills/*.md; do
    name=$(basename "$skill")
    ln -sf "../../$skill" ".claude/commands/$name"
done
```

Claude Code handles symlinks correctly. The `$ARGUMENTS` placeholder in the canonical file works natively.

#### Gemini CLI: Symlinks

```bash
mkdir -p .gemini/commands
for skill in skills/*.md; do
    name=$(basename "$skill")
    ln -sf "../../$skill" ".gemini/commands/$name"
done
```

#### Cursor: Generated .mdc Files

```bash
mkdir -p .cursor/rules
for skill in skills/*.md; do
    name=$(basename "$skill" .md)
    # Extract frontmatter and transform
    python3 scripts/generate_mdc.py "$skill" ".cursor/rules/${name}.mdc"
done
```

Where `generate_mdc.py` (or equivalent in bash/node):

```python
#!/usr/bin/env python3
"""Convert canonical skill .md to Cursor .mdc format."""
import sys
import yaml
import re

def convert(src_path, dst_path):
    with open(src_path) as f:
        content = f.read()

    # Parse frontmatter
    fm_match = re.match(r'^---\n(.+?)\n---\n(.*)$', content, re.DOTALL)
    if fm_match:
        fm = yaml.safe_load(fm_match.group(1))
        body = fm_match.group(2)
    else:
        fm = {}
        body = content

    # Build Cursor frontmatter
    cursor_fm = {}
    if 'description' in fm:
        cursor_fm['description'] = fm['description']
    if 'globs' in fm:
        cursor_fm['globs'] = fm['globs']
    cursor_fm['alwaysApply'] = fm.get('alwaysApply', False)

    # Transform template variables: ${var} → {{input}}
    body = re.sub(r'\$\{(\w+)\}', r'{{\1}}', body)
    body = body.replace('$ARGUMENTS', '{{input}}')

    with open(dst_path, 'w') as f:
        f.write('---\n')
        f.write(yaml.dump(cursor_fm, default_flow_style=False))
        f.write('---\n')
        f.write(body)

if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
```

#### Codex CLI: Generated Index in codex.md

Since Codex has no slash commands, we generate references in `codex.md`:

```bash
cat > codex.md << 'HEADER'
# Project Instructions

## Available Workflows

The following skill workflows are available in the `skills/` directory.
When asked to perform one of these tasks, read the corresponding file and follow its steps.

HEADER

for skill in skills/*.md; do
    name=$(basename "$skill" .md)
    # Extract description from frontmatter
    desc=$(grep '^description:' "$skill" | sed 's/description: *"\(.*\)"/\1/')
    echo "- **${name}**: ${desc} → \`${skill}\`" >> codex.md
done
```

### 3.4 Version Control Guidance

**.gitignore:**
```gitignore
# Do NOT ignore these — they are generated but should be committed
# so the tools work immediately on clone without running sync
# .cursor/rules/
# .claude/commands/
# .gemini/commands/

# Ignore user-scoped configs
.claude/settings.local.json
```

**.gitattributes:**
```gitattributes
# Mark generated files so reviewers know not to edit directly
.cursor/rules/*.mdc    linguist-generated=true
codex.md               linguist-generated=true
```

**Recommendation:** Commit the generated files. This ensures any contributor who clones the repo gets working tool integration without running `sync-skills.sh`. The sync script is for maintaining/updating, not bootstrapping.

### 3.5 The Sync Script (Complete)

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$ROOT/skills"

echo "🔄 Syncing skills from $SKILLS_DIR..."

# ── Claude Code: symlinks ──
echo "  → Claude Code (.claude/commands/)"
mkdir -p "$ROOT/.claude/commands"
# Remove old skill symlinks
find "$ROOT/.claude/commands" -type l -delete 2>/dev/null || true
for skill in "$SKILLS_DIR"/*.md; do
    [ -f "$skill" ] || continue
    name=$(basename "$skill")
    ln -sf "../../skills/$name" "$ROOT/.claude/commands/$name"
    echo "    ✓ $name (symlink)"
done

# ── Gemini CLI: symlinks ──
echo "  → Gemini CLI (.gemini/commands/)"
mkdir -p "$ROOT/.gemini/commands"
find "$ROOT/.gemini/commands" -type l -delete 2>/dev/null || true
for skill in "$SKILLS_DIR"/*.md; do
    [ -f "$skill" ] || continue
    name=$(basename "$skill")
    ln -sf "../../skills/$name" "$ROOT/.gemini/commands/$name"
    echo "    ✓ $name (symlink)"
done

# ── Cursor: generated .mdc ──
echo "  → Cursor (.cursor/rules/)"
mkdir -p "$ROOT/.cursor/rules"
# Remove previously generated skill rules (tagged with comment)
find "$ROOT/.cursor/rules" -name "skill-*.mdc" -delete 2>/dev/null || true
for skill in "$SKILLS_DIR"/*.md; do
    [ -f "$skill" ] || continue
    name=$(basename "$skill" .md)
    target="$ROOT/.cursor/rules/skill-${name}.mdc"

    # Extract description from frontmatter (simple grep; use python for robustness)
    desc=$(sed -n '/^---$/,/^---$/{ /^description:/{ s/description: *"\{0,1\}\(.*\)"\{0,1\}/\1/; p; } }' "$skill")
    globs=$(sed -n '/^---$/,/^---$/{ /^globs:/{ s/globs: *//; p; } }' "$skill")

    # Get body (everything after second ---)
    body=$(awk 'BEGIN{c=0} /^---$/{c++; if(c==2){found=1; next}} found{print}' "$skill")

    # Transform template variables
    body=$(echo "$body" | sed 's/\$ARGUMENTS/{{input}}/g; s/\${[[:alnum:]_]*}/{{input}}/g')

    {
        echo "---"
        echo "description: \"${desc:-Skill: $name}\""
        if [ -n "$globs" ]; then
            echo "globs: $globs"
        fi
        echo "alwaysApply: false"
        echo "---"
        echo "$body"
    } > "$target"
    echo "    ✓ skill-${name}.mdc (generated)"
done

# ── Codex CLI: generate index in codex.md ──
echo "  → Codex CLI (codex.md)"
CODEX_MARKER="<!-- BEGIN SKILLS INDEX -->"
CODEX_END="<!-- END SKILLS INDEX -->"

# Generate skills index block
SKILLS_BLOCK="$CODEX_MARKER
## Available Skill Workflows

When asked to perform one of these tasks, read the corresponding file and follow its instructions:

$(for skill in "$SKILLS_DIR"/*.md; do
    [ -f "$skill" ] || continue
    name=$(basename "$skill" .md)
    desc=$(sed -n '/^---$/,/^---$/{ /^description:/{ s/description: *"\{0,1\}\(.*\)"\{0,1\}/\1/; p; } }' "$skill")
    echo "- **${name}**: ${desc:-No description} → see \`skills/${name}.md\`"
done)

$CODEX_END"

if [ -f "$ROOT/codex.md" ]; then
    # Replace existing block or append
    if grep -q "$CODEX_MARKER" "$ROOT/codex.md"; then
        # Use awk to replace between markers
        awk -v block="$SKILLS_BLOCK" \
            "/$CODEX_MARKER/{found=1; print block; next}
             /$CODEX_END/{found=0; next}
             !found{print}" "$ROOT/codex.md" > "$ROOT/codex.md.tmp"
        mv "$ROOT/codex.md.tmp" "$ROOT/codex.md"
    else
        echo "" >> "$ROOT/codex.md"
        echo "$SKILLS_BLOCK" >> "$ROOT/codex.md"
    fi
else
    echo "# Project Instructions" > "$ROOT/codex.md"
    echo "" >> "$ROOT/codex.md"
    echo "$SKILLS_BLOCK" >> "$ROOT/codex.md"
fi
echo "    ✓ codex.md (updated)"

# ── Instruction files: generate tool-specific refs ──
for tool_file in CLAUDE.md GEMINI.md; do
    MARKER="<!-- BEGIN SKILLS REF -->"
    END_MARKER="<!-- END SKILLS REF -->"
    REF_BLOCK="$MARKER
## Skills

Reusable workflows are in \`skills/\`. Use them via slash commands or by reading the file directly.
$END_MARKER"

    if [ -f "$ROOT/$tool_file" ]; then
        if ! grep -q "$MARKER" "$ROOT/$tool_file"; then
            echo "" >> "$ROOT/$tool_file"
            echo "$REF_BLOCK" >> "$ROOT/$tool_file"
            echo "  → $tool_file (appended skills reference)"
        fi
    fi
done

echo ""
echo "✅ Sync complete. $(ls "$SKILLS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') skills distributed to all tools."
```

Make executable: `chmod +x scripts/sync-skills.sh`

### 3.6 Fallback Architecture (Simpler, No Generation)

If you want zero tooling overhead and accept some duplication:

```
project-root/
├── skills/                          # Canonical source
│   ├── deploy-staging.md
│   └── ...
│
├── .claude/
│   └── commands/                    # Symlinks
│       └── deploy-staging.md → ../../skills/deploy-staging.md
│
├── .gemini/
│   └── commands/                    # Symlinks
│       └── deploy-staging.md → ../../skills/deploy-staging.md
│
├── .cursor/
│   └── rules/                       # MANUAL COPIES with .mdc extension + frontmatter
│       └── deploy-staging.mdc       # Manually maintained
│
├── CLAUDE.md                        # Hand-maintained, references skills/
├── codex.md                         # Hand-maintained, references skills/
├── GEMINI.md                        # Hand-maintained, references skills/
```

**Tradeoffs:**
- ✅ No build step
- ✅ No Python dependency
- ❌ Cursor `.mdc` files will drift from canonical source
- ❌ Manual maintenance of codex.md skill index
- ⚠️ Acceptable for ≤10 skills; breaks down beyond that

---

## 4. Migration Playbook

### Current State (as described):
```
project-root/
├── skills/                    # Canonical SKILL.md files
│   ├── deploy-staging.md
│   └── ...
├── .claude/
│   └── skills/                # Symlinks to skills/ (WRONG DIRECTORY — should be commands/)
│       └── deploy-staging.md → ../../skills/deploy-staging.md
├── .cursor/
│   └── commands/              # Markdown command files (standalone, possibly diverged)
│       └── deploy-staging.md
├── codex.md or similar        # May not exist
```

### Migration Steps

**Step 1: Audit current state (5 min)**

```bash
# Check what's in skills/
echo "=== Canonical Skills ==="
ls -la skills/*.md

# Check Claude setup
echo "=== Claude Skills (current) ==="
ls -la .claude/skills/ 2>/dev/null || echo "No .claude/skills/"
ls -la .claude/commands/ 2>/dev/null || echo "No .claude/commands/"

# Check Cursor setup
echo "=== Cursor Commands ==="
ls -la .cursor/commands/ 2>/dev/null || echo "No .cursor/commands/"
ls -la .cursor/rules/ 2>/dev/null || echo "No .cursor/rules/"

# Check for existing instruction files
echo "=== Instruction Files ==="
for f in CLAUDE.md codex.md GEMINI.md .cursorrules; do
    [ -f "$f" ] && echo "EXISTS: $f" || echo "MISSING: $f"
done
```

**Step 2: Ensure canonical skills have frontmatter (10 min)**

For each file in `skills/`, add frontmatter if missing:

```bash
for skill in skills/*.md; do
    if ! head -1 "$skill" | grep -q '^---$'; then
        name=$(basename "$skill" .md)
        # Extract first heading as description
        desc=$(grep '^# ' "$skill" | head -1 | sed 's/^# //')
        tmpfile=$(mktemp)
        {
            echo "---"
            echo "skill: $name"
            echo "description: \"${desc:-$name workflow}\""
            echo "tags: []"
            echo "globs: []"
            echo "---"
            echo ""
            cat "$skill"
        } > "$tmpfile"
        mv "$tmpfile" "$skill"
        echo "Added frontmatter to $skill"
    fi
done
```

**Step 3: Fix Claude Code wiring (2 min)**

Claude Code uses `.claude/commands/`, not `.claude/skills/`:

```bash
# Remove incorrect skills directory
rm -rf .claude/skills/

# Create correct commands directory with symlinks
mkdir -p .claude/commands
for skill in skills/*.md; do
    name=$(basename "$skill")
    ln -sf "../../skills/$name" ".claude/commands/$name"
done

echo "✓ Claude Code: .claude/commands/ now symlinked to skills/"
```

**Step 4: Set up Gemini CLI (2 min)**

```bash
mkdir -p .gemini/commands
for skill in skills/*.md; do
    name=$(basename "$skill")
    ln -sf "../../skills/$name" ".gemini/commands/$name"
done

echo "✓ Gemini CLI: .gemini/commands/ now symlinked to skills/"
```

**Step 5: Migrate Cursor from commands/ to rules/ (5 min)**

Cursor's command system exists but the rules system is more powerful (auto-matching via globs/description):

```bash
# Back up existing cursor commands
if [ -d .cursor/commands ]; then
    cp -r .cursor/commands .cursor/commands.bak
    echo "Backed up .cursor/commands to .cursor/commands.bak"
fi

# Generate .mdc rules from canonical skills
mkdir -p .cursor/rules
for skill in skills/*.md; do
    name=$(basename "$skill" .md)
    target=".cursor/rules/skill-${name}.mdc"

    desc=$(sed -n '/^---$/,/^---$/{ /^description