---
type: synthesis-report
topic: story-053-cross-cli-skills
synthesis-model: claude-opus-4-6
source-reports:
- claude-opus-4-6-report.md
- gpt-5-2-report.md
synthesized: '2026-02-19T15:45:57.428690+00:00'
---



---
canonical-model-name: "claude"
report-date: "2025-07-10"
research-topic: "story-053-cross-cli-skills"
report-type: "synthesis"
---

# Synthesis Report: Unified Agent Workflow Architecture Across Four AI Coding CLIs

## 1. Executive Summary

- **All four tools (Claude Code, Codex CLI, Gemini CLI, Cursor) consume Markdown-based instruction/workflow files**, but each has distinct discovery paths, naming conventions, and metadata requirements.
- **A canonical-source-with-generated-adapters architecture** is the only approach that reliably serves all four tools while maintaining a single source of truth.
- **Symlinks work reliably for Claude Code and Gemini CLI**, are acceptable for Codex CLI (standard filesystem I/O), but are **unreliable for Cursor** due to file-watcher issues — Cursor requires generated/copied `.mdc` files.
- **Codex CLI has no native skills directory or slash command system** — the `~/.codex/skills/.system` path referenced in the current repo state is not a documented Codex feature and needs investigation. Codex workflows are invoked conversationally via references in `codex.md` or `AGENTS.md`.
- **Cursor's `.mdc` format** (Markdown + YAML frontmatter with `description`, `globs`, `alwaysApply`) is the only tool-specific format that cannot be a plain symlink to a canonical `.md` file.
- **Template variable syntax differs**: `$ARGUMENTS` (Claude Code, possibly Gemini), `{{input}}`/`{{selection}}` (Cursor), none (Codex) — requiring transformation in the generation step.
- **The recommended repo layout** uses `skills/` as the canonical directory, symlinks for Claude and Gemini, generated `.mdc` for Cursor, and a generated skills index in `codex.md`.
- **A single `sync-skills.sh` script** (~100 lines of bash) handles all generation and wiring — no heavy toolchain required.
- **Generated files should be committed** so that `git clone` yields a working setup without running a build step.
- **The current repo state has a misconfigured Claude Code path** (`.claude/skills/` instead of `.claude/commands/`) that needs immediate correction.
- **Risk is dominated by vendor churn** — all four tools are actively evolving, with Gemini CLI being the newest and most volatile.
- **The fallback architecture** (symlinks for Claude/Gemini, manual `.mdc` copies for Cursor, hand-maintained `codex.md`) works for ≤10 skills without any tooling dependency.

## 2. Source Quality Review

| Dimension | Report 1 (Claude Opus 4) | Report 2 (GPT-5) |
|---|---|---|
| **Evidence Density** | 4/5 | 2/5 |
| **Practical Applicability** | 5/5 | 3/5 |
| **Specificity** | 5/5 | 3/5 |
| **Internal Consistency** | 4/5 | 4/5 |
| **Overall** | **4.5/5** | **3.0/5** |

**Report 1 Critique:** Exceptionally detailed and implementation-ready. Provides exact file paths, a complete sync script, a Python conversion utility, concrete `.gitignore`/`.gitattributes` guidance, and a step-by-step migration with actual shell commands. It includes specific URLs for major claims (Anthropic docs, OpenAI Codex repo, Gemini CLI repo, Cursor docs). The main weakness is that some claims about symlink behavior and Gemini CLI command format are marked as community-confirmed or inference rather than vendor-documented. The Cursor rules vs. commands distinction is well-handled. Minor issue: the report's migration playbook appears truncated at the end.

**Report 2 Critique:** Intellectually honest about its limitations — explicitly states it cannot verify tool-specific paths and repeatedly marks claims as "needs confirmation." This epistemic humility is valuable but results in a report that is structurally complete yet substantively hollow for the most critical sections (capability matrix, exact discovery paths). The architecture proposal is sound in principle but generic: it could apply to any set of CLI tools. The Jinja2 template approach is over-engineered for this use case. The suggestion to rename `skills/` to `workflows/` introduces unnecessary migration churn. The report is useful as a cross-check on architectural reasoning but provides almost no tool-specific facts to implement against.

**Weighting Decision:** Report 1 is weighted heavily (approximately 85%) for all tool-specific facts and implementation details. Report 2 contributes useful framing on the copy-vs-symlink tradeoff, the risk register structure, and the principle of generated-then-committed outputs.

## 3. Consolidated Findings by Topic

### 3.1 Tool-by-Tool Capability Matrix

| Feature | Claude Code | Codex CLI | Gemini CLI | Cursor |
|---|---|---|---|---|
| **Instruction file** | `CLAUDE.md` (project root, parents, `~/.claude/`) | `codex.md` / `CODEX.md` (root), `AGENTS.md` (recursive), `~/.codex/instructions.md` | `GEMINI.md` (root, parents, `~/.gemini/`) | `.cursor/rules/*.mdc` (project), `~/.cursor/rules/*.mdc` (user) |
| **Slash commands** | `.claude/commands/*.md` (project), `~/.claude/commands/*.md` (user) | ❌ None | `.gemini/commands/*.md` (project), `~/.gemini/commands/*.md` (user) | `.cursor/commands/*.md` (project) |
| **Skills/workflows** | Via `@file` or slash commands pointing to skill files | Via conversational reference ("follow the workflow in skills/X.md") | Via `@file` or slash commands | Via rules with auto-matching (globs/description) or `@ruleName` |
| **Auto-discovery** | `CLAUDE.md` auto-loaded; commands discovered by directory | `codex.md`/`AGENTS.md` auto-loaded | `GEMINI.md` auto-loaded; commands discovered by directory | Rules auto-attached via `globs` or `description` matching |
| **Symlinks reliable** | ✅ Yes (confirmed by community practice) | ✅ Yes (standard file I/O) | ✅ Likely (standard file I/O, not explicitly documented) | ⚠️ Unreliable (file watcher issues reported) |
| **User scope path** | `~/.claude/` | `~/.codex/` | `~/.gemini/` | `~/.cursor/` |
| **Project scope path** | `.claude/` + `CLAUDE.md` | `codex.md` / `AGENTS.md` at root | `.gemini/` + `GEMINI.md` | `.cursor/` |
| **Template variables** | `$ARGUMENTS` | ❌ None | `$ARGUMENTS` (inferred from Claude Code parity) | `{{selection}}`, `{{file}}`, `{{input}}` |
| **Asset format** | Plain Markdown | Plain Markdown | Plain Markdown | Markdown + YAML frontmatter, `.mdc` extension |
| **Namespacing** | Subdirs → colon-separated (e.g., `deploy/staging.md` → `/deploy:staging`) | N/A | Unknown | Flat namespace in commands/ |

**Confidence levels:**
- Claude Code: High (official docs at docs.anthropic.com/en/docs/claude-code/memory and /slash-commands)
- Codex CLI: High for documented features; **high confidence that no native skills/slash system exists** (github.com/openai/codex)
- Gemini CLI: Medium (github.com/google-gemini/gemini-cli; tool is very new, conventions evolving)
- Cursor: High (docs.cursor.com/context/rules)

### 3.2 Compatibility Strategy

**Fully shareable across all four tools:**
- Workflow body content (Markdown prose: steps, checklists, code patterns, conventions)
- File path references relative to project root
- Shell scripts invoked by workflows
- A canonical skill ID derived from kebab-case filename

**Must be adapted per tool:**

| Adaptation | Details |
|---|---|
| File location | Each tool scans its own directory tree |
| File extension | Cursor requires `.mdc`; all others use `.md` |
| Frontmatter | Cursor requires `description`/`globs`/`alwaysApply`; others tolerate or ignore frontmatter |
| Template variables | `$ARGUMENTS` → `{{input}}` transformation needed for Cursor |
| Invocation | Slash commands (Claude, Gemini, Cursor) vs. conversational (Codex) |
| Instruction file name | `CLAUDE.md` / `codex.md` / `GEMINI.md` / rules — all different |

**Recommended canonical intermediate format:**

Standard Markdown with an extended YAML frontmatter block:

```markdown
---
skill: deploy-staging
description: "Deploy current branch to staging environment"
tags: [deploy, staging, ci]
arguments:
  - name: branch
    description: "Branch to deploy"
    default: "current"
globs: ["deploy/**", "Dockerfile"]
---

# Deploy to Staging

## Steps
1. Verify no uncommitted changes
2. Run test suite: `npm test`
3. Build Docker image: `docker build -t app:staging .`
4. Deploy: `./scripts/deploy.sh staging $ARGUMENTS`
5. Verify: `curl -f https://staging.example.com/health`

## Rollback
If deployment fails:
1. Run `./scripts/rollback.sh staging`
2. Notify #deployments channel
```

This format is consumed directly by Claude Code and Gemini CLI (they ignore/tolerate the frontmatter), and is transformed for Cursor and Codex by the sync script.

**Strategy verdict: Hybrid (canonical + generated wrappers)** — single source of truth with thin generation. This outperforms all alternatives:
- "All-symlinks" breaks for Cursor
- "All-generated" loses editability and adds unnecessary complexity for Claude/Gemini
- "Manual copies" guarantees drift

### 3.3 Recommended Repo Layout

```
project-root/
├── skills/                          # CANONICAL SOURCE OF TRUTH
│   ├── deploy-staging.md
│   ├── code-review.md
│   ├── test-coverage.md
│   └── ...
│
├── scripts/
│   └── sync-skills.sh               # Generation/sync script (~100 LOC bash)
│
├── CLAUDE.md                         # Hand-maintained + auto-appended skills ref
├── codex.md                          # Auto-generated skills index section
├── GEMINI.md                         # Hand-maintained + auto-appended skills ref
│
├── .claude/
│   └── commands/                     # SYMLINKS → ../../skills/*.md
│       ├── deploy-staging.md → ../../skills/deploy-staging.md
│       └── ...
│
├── .gemini/
│   └── commands/                     # SYMLINKS → ../../skills/*.md
│       ├── deploy-staging.md → ../../skills/deploy-staging.md
│       └── ...
│
├── .cursor/
│   └── rules/                        # GENERATED .mdc files (not symlinks)
│       ├── skill-deploy-staging.mdc
│       └── ...
│
├── .gitignore
└── .gitattributes
```

**Naming conventions:**
- Canonical files: `kebab-case.md` in `skills/`
- Cursor generated rules: `skill-<name>.mdc` (prefixed to distinguish from hand-written rules)
- Command/skill names derived from filename (e.g., `deploy-staging.md` → `/deploy-staging`)

**Version control:**
- **Commit:** `skills/`, `scripts/sync-skills.sh`, `.claude/commands/` (symlinks), `.gemini/commands/` (symlinks), `.cursor/rules/skill-*.mdc` (generated), `codex.md`, `CLAUDE.md`, `GEMINI.md`
- **Do not commit:** user-scoped configs (`~/.claude/`, `~/.codex/`, etc.)
- **`.gitattributes`:** Mark generated files with `linguist-generated=true`

**Rationale for committing generated files:** Any contributor who clones the repo gets working tool integration immediately. The sync script is for updating after skill changes, not for bootstrapping.

### 3.4 Wiring Details

**Claude Code:** Symlinks from `.claude/commands/*.md` → `../../skills/*.md`. Claude Code resolves symlinks via standard filesystem I/O. The `$ARGUMENTS` placeholder in canonical files works natively.

**Gemini CLI:** Same symlink approach as Claude Code. `.gemini/commands/*.md` → `../../skills/*.md`.

**Cursor:** Generated `.mdc` files in `.cursor/rules/`. The sync script extracts frontmatter from canonical `.md`, maps it to Cursor's required frontmatter (`description`, `globs`, `alwaysApply`), transforms `$ARGUMENTS` → `{{input}}`, and writes `.mdc` files with the correct extension.

**Codex CLI:** No slash commands or skills directory. Instead, `codex.md` contains a generated skills index block (delimited by HTML comments) that lists all available workflows with descriptions and file paths, instructing the agent to read the referenced file when asked to perform that task.

### 3.5 Fallback Architecture (No Generation)

For teams that want zero tooling overhead and have ≤10 skills:

- `skills/` remains canonical
- `.claude/commands/` and `.gemini/commands/` use symlinks (same as primary)
- `.cursor/rules/` contains **manually maintained** `.mdc` copies
- `codex.md` is hand-written with a skills reference section
- **Accepted tradeoffs:** Cursor `.mdc` files will drift from canonical; manual maintenance of `codex.md` skill index; breaks down beyond ~10 skills

## 4. Conflict Resolution Ledger

| Claim | Report 1 Position | Report 2 Position | Adjudication | Confidence |
|---|---|---|---|---|
| **Codex CLI has a native skills directory** | Explicitly denies it — no `skills/` convention found in Codex repo | Notes `~/.codex/skills/.system` is user-reported, marks as "needs confirmation" | **Report 1 correct.** The Codex CLI GitHub repo (github.com/openai/codex) shows no skills directory convention. The `~/.codex/skills/.system` in the current state is likely a custom/local setup or confusion with another tool. | High |
| **Should canonical dir be `skills/` or `workflows/`?** | Uses `skills/` (matches current state) | Proposes renaming to `workflows/` | **Keep `skills/`.** Renaming introduces unnecessary git history churn and breaking changes for no functional benefit. The name is already established in the repo. | High |
| **Symlinks vs. copy/sync as default wiring** | Symlinks for Claude/Gemini, generated for Cursor | Prefers copy/sync for all (cites Windows/sandboxing concerns) | **Hybrid: symlinks for Claude/Gemini, generated copies for Cursor.** Symlinks are simpler and confirmed working for Claude Code. The Windows concern is valid but secondary if the team is on macOS/Linux. Add a note for Windows users to use the copy approach. | High |
| **Should generated files be committed?** | Yes — ensures clone-and-go | Offers both options, leans toward committing | **Agree: commit generated files.** The operational benefit of immediate usability on clone outweighs the minor noise in diffs. `.gitattributes` with `linguist-generated=true` mitigates review noise. | High |
| **Generator technology** | Bash script (~100 LOC) with optional Python helper | Python with Jinja2 templates | **Bash is sufficient and preferable.** The transformations are simple (extract frontmatter, rewrite variables, emit `.mdc`). Adding Python/Jinja2 introduces a dependency for negligible benefit. A Python helper is acceptable as an optional enhancement for complex frontmatter parsing. | Medium-High |
| **Cursor: rules/ vs commands/ as target** | Recommends `.cursor/rules/` (auto-matching via globs/description is more powerful) | Uses `.cursor/commands/` (matches current state) | **Report 1 correct.** Cursor's rules system with `.mdc` frontmatter enables auto-attachment based on file context, which is significantly more powerful than slash commands for workflow automation. Migrate from commands/ to rules/. | High |
| **Gemini CLI command format** | States `.gemini/commands/*.md` with `$ARGUMENTS` | Marks as "needs confirmation" | **Report 1 is more specific but confidence is medium.** Gemini CLI is very new (mid-2025). The command format is plausible based on the pattern established by Claude Code, but should be verified. | Medium |

## 5. Decision Matrix

| Architecture Option | Simplicity (×2) | Reliability (×3) | Maintainability (×2) | Cross-tool Coverage (×3) | Total (/50) |
|---|---|---|---|---|---|
| **A: Canonical + Generated Wrappers (hybrid)** | 3 (×2=6) | 4 (×3=12) | 5 (×2=10) | 5 (×3=15) | **43** |
| B: All Symlinks | 5 (×2=10) | 2 (×3=6) | 4 (×2=8) | 3 (×3=9) | 33 |
| C: All Generated | 2 (×2=4) | 4 (×3=12) | 3 (×2=6) | 5 (×3=15) | 37 |
| D: Manual Copies | 5 (×2=10) | 3 (×3=9) | 1 (×2=2) | 4 (×3=12) | 33 |

**Winner: Option A — Canonical + Generated Wrappers (hybrid)**

Scoring rationale:
- Reliability weighted highest because broken tool integration wastes developer time
- Cross-tool coverage weighted equally because the whole point is unified support
- Simplicity weighted lower because a one-time setup cost is acceptable
- Option A scores highest on maintainability because edits happen in one place

## 6. Final Recommendation

### Implement the Canonical-Source-with-Adapters Architecture

**One sentence:** Keep all workflow content in `skills/*.md` with extended frontmatter, symlink into `.claude/commands/` and `.gemini/commands/`, generate `.mdc` files into `.cursor/rules/`, and generate a skills index into `codex.md` — all via a single `sync-skills.sh` script that is run after any skill change.

**Key design decisions:**
1. **`skills/` is the single source of truth.** Do not rename it.
2. **Symlinks for Claude Code and Gemini CLI.** They handle symlinks correctly and consume the canonical format directly.
3. **Generated `.mdc` for Cursor.** Cursor's file watcher is unreliable with symlinks, and the `.mdc` format requires tool-specific frontmatter.
4. **Generated skills index block in `codex.md`.** Codex CLI has no slash commands; it needs explicit references to skill files.
5. **Commit all generated artifacts.** Clone-and-go is more valuable than a clean git history.
6. **Bash sync script, no heavy dependencies.** Python helper is optional for robust YAML parsing but not required.
7. **Prefix Cursor-generated rules with `skill-`** to distinguish them from hand-written rules.

## 7. Implementation Plan / Next Steps

### Migration from Current State (Estimated: 45–60 minutes)

**Prerequisites:** Ensure you're on a clean branch.

---

**Step 1: Audit current state (5 min)**

```bash
echo "=== Canonical Skills ==="
ls -la skills/*.md 2>/dev/null

echo "=== Claude (current) ==="
ls -la .claude/skills/ 2>/dev/null
ls -la .claude/commands/ 2>/dev/null

echo "=== Cursor (current) ==="
ls -la .cursor/commands/ 2>/dev/null
ls -la .cursor/rules/ 2>/dev/null

echo "=== Instruction Files ==="
for f in CLAUDE.md codex.md CODEX.md GEMINI.md .cursorrules; do
    [ -f "$f" ] && echo "EXISTS: $f" || echo "MISSING: $f"
done

echo "=== Codex user dir ==="
ls -la ~/.codex/ 2>/dev/null
```

**Step 2: Add frontmatter to canonical skills (10 min)**

For each `skills/*.md` that lacks frontmatter:

```bash
for skill in skills/*.md; do
    if ! head -1 "$skill" | grep -q '^---$'; then
        name=$(basename "$skill" .md)
        desc=$(grep '^# ' "$skill" | head -1 | sed 's/^# //')
        tmpfile=$(mktemp)
        cat > "$tmpfile" <<EOF
---
skill: $name
description: "${desc:-$name workflow}"
tags: []
globs: []
---

EOF
        cat "$skill" >> "$tmpfile"
        mv "$tmpfile" "$skill"
        echo "✓ Added frontmatter to $skill"
    fi
done
```

**Step 3: Fix Claude Code wiring (3 min)**

Claude Code uses `.claude/commands/`, not `.claude/skills/`:

```bash
rm -rf .claude/skills/
mkdir -p .claude/commands
for skill in skills/*.md; do
    name=$(basename "$skill")
    ln -sf "../../skills/$name" ".claude/commands/$name"
done
echo "✓ Claude Code wired via .claude/commands/"
```

**Step 4: Set up Gemini CLI (2 min)**

```bash
mkdir -p .gemini/commands
for skill in skills/*.md; do
    name=$(basename "$skill")
    ln -sf "../../skills/$name" ".gemini/commands/$name"
done
echo "✓ Gemini CLI wired via .gemini/commands/"
```

**Step 5: Migrate Cursor to rules/ with generated .mdc (10 min)**

```bash
# Backup existing Cursor commands
[ -d .cursor/commands ] && cp -r .cursor/commands .cursor/commands.bak

# Generate .mdc rules
mkdir -p .cursor/rules
for skill in skills/*.md; do
    name=$(basename "$skill" .md)
    target=".cursor/rules/skill-${name}.mdc"

    # Extract frontmatter values
    desc=$(sed -n '/^---$/,/^---$/{ /^description:/{ s/description: *"\{0,1\}\(.*\)"\{0,1\}$/\1/; p; } }' "$skill")
    globs=$(sed -n '/^---$/,/^---$/{ /^globs:/{ s/globs: *//; p; } }' "$skill")

    # Extract body (after second ---)
    body=$(awk 'BEGIN{c=0} /^---$/{c++; if(c==2){found=1; next}} found{print}' "$skill")

    # Transform template variables
    body=$(echo "$body" | sed 's/\$ARGUMENTS/{{input}}/g; s/\${\([[:alnum:]_]*\)}/{{input}}/g')

    cat > "$target" <<CURSOR_EOF
---
description: "${desc:-Skill: $name}"
$([ -n "$globs" ] && echo "globs: $globs")
alwaysApply: false
---
$body
CURSOR_EOF
    echo "  ✓ skill-${name}.mdc"
done
echo "✓ Cursor wired via .cursor/rules/"
```

**Step 6: Generate Codex skills index (5 min)**

```bash
MARKER="<!-- BEGIN SKILLS INDEX -->"
END_MARKER="<!-- END SKILLS INDEX -->"

INDEX="$MARKER
## Available Skill Workflows

When asked to perform one of these tasks, read the corresponding file and follow its instructions:

$(for skill in skills/*.md; do
    name=$(basename "$skill" .md)
    desc=$(sed -n '/^---$/,/^---$/{ /^description:/{ s/description: *"\{0,1\}\(.*\)"\{0,1\}$/\1/; p; } }' "$skill")
    echo "- **${name}**: ${desc:-No description} → see \`skills/${name}.md\`"
done)

$END_MARKER"

if [ -f codex.md ]; then
    if grep -q "$MARKER" codex.md; then
        awk -v block="$INDEX" \
            "/$MARKER/{found=1; print block; next} /$END_MARKER/{found=0; next} !found{print}" \
            codex.md > codex.md.tmp && mv codex.md.tmp codex.md
    else
        echo "" >> codex.md
        echo "$INDEX" >> codex.md
    fi
else
    echo "# Project Instructions" > codex.md
    echo "" >> codex.md
    echo "$INDEX" >> codex.md
fi
echo "✓ codex.md updated with skills index"
```

**Step 7: Add skills references to CLAUDE.md and GEMINI.md (3 min)**

```bash
for tool_file in CLAUDE.md GEMINI.md; do
    REF_MARKER="<!-- BEGIN SKILLS REF -->"
    REF_END="<!-- END SKILLS REF -->"
    REF_BLOCK="$REF_MARKER
## Skills

Reusable workflows are available in \`skills/\`. Use them via slash commands (e.g., \`/deploy-staging\`) or by reading the file directly.
$REF_END"

    if [ -f "$tool_file" ]; then
        if ! grep -q "$REF_MARKER" "$tool_file"; then
            echo "" >> "$tool_file"
            echo "$REF_BLOCK" >> "$tool_file"
            echo "✓ $tool_file: appended skills reference"
        fi
    fi
done
```

**Step 8: Create the sync script (5 min)**

Save the complete sync script (combining Steps 3–7 logic) as `scripts/sync-skills.sh` and `chmod +x` it. This script becomes the single command to run whenever skills are added or modified.

**Step 9: Update .gitignore and .gitattributes (2 min)**

```bash
# .gitattributes
cat >> .gitattributes <<'EOF'
.cursor/rules/skill-*.mdc  linguist-generated=true
EOF

# Ensure generated directories are NOT in .gitignore
# (We want them committed)
```

**Step 10: Clean up deprecated paths (2 min)**

```bash
# Remove old .claude/skills/ if it still exists in git
git rm -rf .claude/skills/ 2>/dev/null || true

# Optionally remove .cursor/commands/ if fully migrated to rules/
# (Keep .cursor/commands.bak locally until validated)
```

**Step 11: Commit and validate (5 min)**

```bash
git add skills/ .claude/commands/ .gemini/commands/ .cursor/rules/ \
       codex.md CLAUDE.md GEMINI.md scripts/sync-skills.sh .gitattributes
git commit -m "unify: canonical skills/ with per-tool adapters

- skills/*.md is the single source of truth
- .claude/commands/ → symlinks to skills/
- .gemini/commands/ → symlinks to skills/
- .cursor/rules/skill-*.mdc → generated from skills/
- codex.md → auto-generated skills index
- scripts/sync-skills.sh → run after adding/changing skills"
```

## 8. Validation Checklist

### Fast Smoke Checks (5 minutes)

| Tool | Test | Expected Result |
|---|---|---|
| **Claude Code** | Run `claude` in repo, type `/deploy-staging` (or first skill name) | Command appears in autocomplete; content matches `skills/deploy-staging.md` body |
| **Claude Code** | `ls -la .claude/commands/deploy-staging.md` | Shows symlink → `../../skills/deploy-staging.md` |
| **Gemini CLI** | Run `gemini` in repo, type `/deploy-staging` | Command appears; content matches canonical source |
| **Gemini CLI** | `ls -la .gemini/commands/deploy-staging.md` | Shows symlink → `../../skills/deploy-staging.md` |
| **Cursor** | Open Cursor in repo, open a file matching a skill's glob pattern | Rule auto-attaches (check context panel); or type `@skill-deploy-staging` |
| **Cursor** | Open `.cursor/rules/skill-deploy-staging.mdc` | Has correct YAML frontmatter; body matches canonical minus `$ARGUMENTS` → `{{input}}` transform |
| **Codex CLI** | Run `codex` in repo, ask "what workflows are available?" | Agent reads `codex.md` and lists skills with correct descriptions |
| **Codex CLI** | Ask "deploy to staging" | Agent reads `skills/deploy-staging.md` and follows its steps |

### Deeper Checks (15 minutes)

| Check | Procedure | Pass Criteria |
|---|---|---|
| **Symlink integrity** | `find .claude/commands .gemini/commands -type l -exec test -e {} \; -print` | All symlinks resolve; no broken links |
| **Content parity** | `diff <(awk '/^---/{c++}c==2{exit}' skills/deploy-staging.md; cat) .cursor/rules/skill-deploy-staging.mdc` (compare bodies after frontmatter) | Bodies match except for template variable transformations |
| **Modification propagation** | Edit a line in `skills/deploy-staging.md`, then verify `.claude/commands/deploy-staging.md` reflects the change (symlink — instant), `.cursor/rules/skill-deploy-staging.mdc` reflects after `sync-skills.sh` | Symlinked tools update instantly; Cursor updates after sync |
| **New skill addition** | Add `skills/new-skill.md` with frontmatter, run `sync-skills.sh` | New skill appears in all four tool directories and in `codex.md` index |
| **Precedence test** | Create conflicting user-scoped and project-scoped assets for one tool; verify which wins | Document the result per tool for future reference |
| **Fresh clone test** | Clone the repo to a new directory, verify all tool assets are present without running any script | All symlinks intact; all `.mdc` files present; `codex.md` has skills index |

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation | Monitoring |
|---|---|---|---|---|
| **Vendor changes discovery paths or asset format** | High (especially Gemini CLI, Cursor) | High — tools silently stop finding assets | Keep wiring logic in one script; pin tool versions in docs; add smoke tests to CI | Quarterly: run smoke checks after tool updates |
| **Symlinks break on Windows or in CI** | Medium | Medium — affects subset of contributors | Document: Windows users run `sync-skills.sh --copy` mode (add flag to script); CI uses copy mode | Onboarding checklist; CI validation step |
| **Cursor file watcher serves stale `.mdc` content** | Medium | Medium — stale rules applied silently | Use generated copies, not symlinks; restart Cursor after sync; add version comment to `.mdc` files | Spot-check after sync |
| **Drift between canonical and generated files** | Medium | High — contradictory instructions to AI agents | Pre-commit hook: run `sync-skills.sh` and fail if `git diff --exit-code` shows changes | Git hook + CI check |
| **Codex CLI adds native skills/commands in future update** | Medium | Low-positive — enables better integration | Monitor Codex CLI releases; adapt sync script when native support appears | Watch github.com/openai/codex releases |
| **Frontmatter parsing breaks on edge cases** | Low | Medium — specific skills malformed for Cursor | Use consistent frontmatter structure; add linting for canonical `.md` files | Lint in CI (`grep -c '^---$' skills/*.md` should return 2 per file) |
| **`.mdc` format evolves (Cursor-specific)** | Medium | Medium | Cursor docs versioned; isolate `.mdc` generation in one function of sync script | Check Cursor changelog monthly |
| **Template variable mapping incomplete** | Low | Low — affects parameterized skills only | Test all parameterized skills after sync; keep variable mapping logic in one place | Part of deeper validation checklist |

## 10. Open Questions & Confidence Statement

### Open Questions

1. **Gemini CLI command file format:** Is `$ARGUMENTS` supported as a template