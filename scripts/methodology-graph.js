#!/usr/bin/env node

const { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } = require("node:fs");
const { basename, join, relative } = require("node:path");

const ROOT = process.cwd();
const STATE_PATH = join(ROOT, "docs/methodology/state.yaml");
const GRAPH_PATH = join(ROOT, "docs/methodology/graph.json");
const STORIES_INDEX_PATH = join(ROOT, "docs/stories.md");
const BUILD_MAP_PATH = join(ROOT, "docs/build-map.md");
const IDEAL_PATH = join(ROOT, "docs/ideal.md");
const SPEC_PATH = join(ROOT, "docs/spec.md");
const EVALS_PATH = join(ROOT, "docs/evals/registry.yaml");
const UI_SCOUT_INDEX_PATH = join(ROOT, "docs/ui-scout.md");
const UI_SCOUT_DIR = join(ROOT, "docs/ui-scout");
const UI_SCOUT_TEMPLATE_PATH = join(ROOT, "docs/ui-scout/_template.md");
const UI_SCOUT_RUNBOOK_PATH = join(ROOT, "docs/runbooks/full-pipeline-ui-manual-walkthrough.md");
const README_PATH = join(ROOT, "README.md");
const STORIES_DIR = join(ROOT, "docs/stories");
const ADRS_DIR = join(ROOT, "docs/decisions");

const STORY_ID_RE = "[0-9]{3}[a-z]?";
const STORY_FILE_RE = new RegExp(`^story-(${STORY_ID_RE})-.+\\.md$`, "i");
const STORY_HEADING_RE = new RegExp(`^#\\s+Story\\s+(${STORY_ID_RE})\\s*(?:[:\\u2014-])\\s+(.+)$`, "i");
const WORK_LOG_ENTRY_RE = /^(?<stamp>\d{8}-\d{4})\s+—\s+(?<summary>.+)$/;
const VALID_STORY_STATUSES = new Set(["Draft", "Pending", "In Progress", "Done", "Deferred", "Blocked", "Cancelled"]);
const TERMINAL_STORY_STATUSES = new Set(["Done", "Deferred", "Cancelled"]);
const REQUIRED_STORY_FRONTMATTER_KEYS = [
  "id",
  "title",
  "status",
  "priority",
  "ideal_refs",
  "spec_refs",
  "adr_refs",
  "depends_on",
  "category_refs",
  "compromise_refs",
  "input_coverage_refs",
  "architecture_domains",
  "roadmap_tags",
  "legacy_system",
];
const REQUIRED_ADR_FRONTMATTER_KEYS = [
  "status",
  "spec_refs",
  "ideal_refs",
  "story_refs",
  "compromise_refs",
  "related_adrs",
  "supersedes",
  "superseded_by",
];
const REQUIRED_EVAL_LINEAGE_KEYS = [
  "spec_refs",
  "story_refs",
  "category_refs",
  "compromise_refs",
];
const STATIC_ACTIVE_SURFACE_PATHS = [
  join(ROOT, "AGENTS.md"),
  README_PATH,
  IDEAL_PATH,
  SPEC_PATH,
  join(ROOT, "docs/scout.md"),
  UI_SCOUT_INDEX_PATH,
  UI_SCOUT_TEMPLATE_PATH,
  join(ROOT, "docs/inbox.md"),
  join(ROOT, "docs/evals/README.md"),
  join(ROOT, "docs/evals/attempt-template.md"),
  join(ROOT, "docs/methodology-artifact-audit-and-migration.md"),
  join(ROOT, "docs/methodology-ideal-spec-compromise.md"),
  join(ROOT, "docs/setup-checklist.md"),
  join(ROOT, "docs/runbooks/setup-methodology.md"),
  join(ROOT, "docs/runbooks/triage.md"),
  UI_SCOUT_RUNBOOK_PATH,
  join(ROOT, "docs/runbooks/migrate-problem-first-triage-and-story-workflow.md"),
  join(ROOT, "docs/runbooks/triage-evals.md"),
  join(ROOT, "docs/runbooks/align.md"),
  join(ROOT, "docs/runbooks/create-eval.md"),
  join(ROOT, "docs/runbooks/finish-and-push.md"),
  join(ROOT, "docs/runbooks/triage-architecture.md"),
  join(ROOT, ".agents/skills/setup-methodology/SKILL.md"),
  join(ROOT, ".agents/skills/triage/SKILL.md"),
  join(ROOT, ".agents/skills/triage-stories/SKILL.md"),
  join(ROOT, ".agents/skills/triage-evals/SKILL.md"),
  join(ROOT, ".agents/skills/triage-inbox/SKILL.md"),
  join(ROOT, ".agents/skills/align/SKILL.md"),
  join(ROOT, ".agents/skills/create-eval/SKILL.md"),
  join(ROOT, ".agents/skills/improve-eval/SKILL.md"),
  join(ROOT, ".agents/skills/build-story/SKILL.md"),
  join(ROOT, ".agents/skills/validate/SKILL.md"),
  join(ROOT, ".agents/skills/mark-story-done/SKILL.md"),
  join(ROOT, ".agents/skills/create-story/SKILL.md"),
  join(ROOT, ".agents/skills/create-story/templates/story.md"),
  join(ROOT, ".agents/skills/setup-methodology/templates/setup-checklist.md"),
  join(ROOT, ".agents/skills/init-project/SKILL.md"),
  join(ROOT, ".agents/skills/finish-and-push/SKILL.md"),
  join(ROOT, ".agents/skills/create-cross-cli-skill/SKILL.md"),
  join(ROOT, ".agents/skills/decompose-spec/SKILL.md"),
  join(ROOT, ".agents/skills/create-adr/SKILL.md"),
  join(ROOT, ".agents/skills/create-adr/templates/adr.md"),
  join(ROOT, ".agents/skills/retrofit-ideal/SKILL.md"),
  join(ROOT, ".agents/skills/triage-architecture/SKILL.md"),
];
const ACTIVE_SURFACE_PATHS = collectActiveSurfacePaths();
const MANUAL_STORIES_RE =
  /update.*docs\/stories\.md|append.*docs\/stories\.md|edit.*docs\/stories\.md|hand-authored story index|manual story index/i;
const STORY_INDEX_FRAMING_RE = /\bstory index\b/i;
const BUILD_MAP_AUTHORITY_RE =
  /central planning\s*\/\s*triage dashboard|build-map-first|build map first|hand-authored build-map|build-map-centered|docs\/build-map\.md.*central|update build map|append.*docs\/build-map\.md|edit.*docs\/build-map\.md/i;
const RETIRED_SETUP_PATH_RE = /(?:^|[^a-z0-9_./-])(?:docs\/)?setup\.md\b/i;
const ALLOWED_LEGACY_CONTEXT_RE =
  /generated|state\.yaml|graph\.json|legacy|migration|historical|archive|archived|not authoritative|generated dashboard/i;
const ALLOWED_STORIES_INDEX_CONTEXT_RE =
  /generated story index|generated planning surfaces|generated dashboard|generated view|compiler|do not modify the generated story index/i;
const VALID_STATE_TOP_LEVEL_KEYS = new Set([
  "version",
  "format",
  "seeded_at",
  "seeded_from",
  "categories",
  "compromises",
  "stories_index",
  "roadmap",
  "ui_scout",
  "architecture_audits",
]);
const VALID_STATE_CATEGORY_KEYS = new Set([
  "substrate",
  "phase",
  "story_coverage",
  "product_need",
  "tech_need",
  "absorbs",
  "notes",
  "last_reviewed",
]);
const VALID_STATE_COMPROMISE_KEYS = new Set([
  "phase",
  "current",
  "converge_signal",
  "evidence",
  "last_reviewed",
]);
const VALID_STATE_STORIES_INDEX_KEYS = new Set([
  "current_execution_map",
  "sections",
]);
const VALID_STATE_SECTION_KEYS = new Set([
  "id",
  "title",
  "lines",
  "markdown",
]);
const VALID_STATE_CURRENT_EXECUTION_MAP_KEYS = new Set([
  "summary",
  "lanes",
]);
const VALID_STATE_EXECUTION_LANE_KEYS = new Set([
  "id",
  "title",
  "statuses",
  "empty_message",
  "story_notes",
  "health_flag",
]);
const VALID_STATE_ROADMAP_KEYS = new Set([
  "active_focus",
  "sequencing_bias",
  "campaigns",
]);
const VALID_STATE_SEQUENCING_BIAS_KEYS = new Set([
  "target",
  "reason",
  "story_refs",
]);
const VALID_STATE_CAMPAIGN_KEYS = new Set([
  "id",
  "status",
  "notes",
  "story_refs",
]);
const VALID_STATE_ARCHITECTURE_AUDIT_KEYS = new Set([
  "cadence",
  "domains",
]);
const VALID_STATE_UI_SCOUT_KEYS = new Set([
  "cadence",
  "last_run_at",
  "last_run_story_id",
  "scenarios",
]);
const VALID_STATE_UI_SCOUT_CADENCE_KEYS = new Set([
  "max_days_without_run",
]);
const VALID_STATE_UI_SCOUT_SCENARIO_KEYS = new Set([
  "label",
  "last_checked",
  "latest_report",
  "status",
  "follow_up_story_refs",
]);
const VALID_UI_SCOUT_SCENARIO_STATUSES = new Set([
  "pass",
  "issues_found",
  "recheck_due",
  "never",
]);
const VALID_STATE_AUDIT_CADENCE_KEYS = new Set([
  "target_story_interval",
]);
const VALID_STATE_AUDIT_DOMAIN_KEYS = new Set([
  "last_audited_at",
  "recent_story_refs",
  "stories_since_audit",
  "open_findings",
  "manual_priority",
  "last_summary",
  "last_result",
]);

function readUtf8(path) {
  return readFileSync(path, "utf8");
}

function toRelative(path) {
  return relative(ROOT, path).replaceAll("\\", "/");
}

function listFilesRecursively(rootDir, predicate) {
  if (!existsSync(rootDir)) return [];
  const output = [];
  for (const entry of readdirSync(rootDir, { withFileTypes: true })) {
    const fullPath = join(rootDir, entry.name);
    if (entry.isDirectory()) {
      output.push(...listFilesRecursively(fullPath, predicate));
      continue;
    }
    if (predicate(fullPath, entry.name)) output.push(fullPath);
  }
  return output;
}

function collectActiveSurfacePaths() {
  return uniqueSorted(
    [
      ...STATIC_ACTIVE_SURFACE_PATHS,
      ...listFilesRecursively(ADRS_DIR, (_path, name) => name === "adr.md"),
      ...listFilesRecursively(join(ROOT, ".gemini/commands"), (_path, name) => name.endsWith(".toml")),
    ].filter((path) => existsSync(path)),
  );
}

function stripQuotes(value) {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function uniqueSorted(values, compare) {
  const seen = new Set();
  const output = [];
  for (const value of values) {
    if (!value || seen.has(value)) continue;
    seen.add(value);
    output.push(value);
  }
  return output.sort(compare || ((a, b) => String(a).localeCompare(String(b))));
}

function leadingSpaces(line) {
  return line.length - line.trimStart().length;
}

function stripInlineComment(value) {
  const hash = value.indexOf("#");
  return (hash >= 0 ? value.slice(0, hash) : value).trim();
}

function storyIdParts(id) {
  const match = String(id).match(/^(\d+)([a-z]?)$/i);
  if (!match) return { number: Number.POSITIVE_INFINITY, suffix: String(id) };
  return { number: Number(match[1]), suffix: match[2].toLowerCase() };
}

function compareStoryIdStrings(a, b) {
  const left = storyIdParts(a);
  const right = storyIdParts(b);
  if (left.number !== right.number) return left.number - right.number;
  if (left.suffix === right.suffix) return 0;
  if (!left.suffix) return -1;
  if (!right.suffix) return 1;
  return left.suffix.localeCompare(right.suffix);
}

function compareStoryRecords(a, b) {
  return compareStoryIdStrings(a.id, b.id);
}

function compareSpecRefs(a, b) {
  const left = String(a).match(/^spec:(\d+)/);
  const right = String(b).match(/^spec:(\d+)/);
  const leftNum = left ? Number(left[1]) : Number.POSITIVE_INFINITY;
  const rightNum = right ? Number(right[1]) : Number.POSITIVE_INFINITY;
  if (leftNum !== rightNum) return leftNum - rightNum;
  return String(a).localeCompare(String(b));
}

function categoryForSpecRef(specRef) {
  const match = String(specRef).match(/^(spec:\d+)/);
  return match ? match[1] : null;
}

function parseJsonCompatibleYaml(path) {
  try {
    return JSON.parse(readUtf8(path));
  } catch (error) {
    throw new Error(`${toRelative(path)} must currently be JSON-compatible YAML: ${error.message}`);
  }
}

function parseDateOnlyUtc(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const [year, month, day] = value.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  if (
    Number.isNaN(date.getTime()) ||
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    return null;
  }
  return date;
}

function diffDateOnlyDays(start, end) {
  return Math.round((end.getTime() - start.getTime()) / 86_400_000);
}

function collectUiScoutReportIds() {
  return new Set(
    listFilesRecursively(UI_SCOUT_DIR, (_path, name) => name.endsWith(".md") && name !== "_template.md")
      .map((path) => basename(path, ".md")),
  );
}

function analyzeUiScoutFreshness(uiScout) {
  if (!uiScout || typeof uiScout !== "object" || Array.isArray(uiScout)) {
    return {
      needsAttention: true,
      summary: "attention needed — ui_scout state is missing",
    };
  }

  const attentionReasons = [];
  const cadence = uiScout.cadence && typeof uiScout.cadence === "object" && !Array.isArray(uiScout.cadence)
    ? uiScout.cadence
    : {};
  const maxDaysWithoutRun = Number.isFinite(cadence.max_days_without_run)
    ? Number(cadence.max_days_without_run)
    : null;
  const lastRunAt = typeof uiScout.last_run_at === "string" ? uiScout.last_run_at : null;
  const lastRunDate = parseDateOnlyUtc(lastRunAt);
  if (!lastRunAt) {
    attentionReasons.push("last run date is missing");
  } else if (!lastRunDate) {
    attentionReasons.push(`last run date ${lastRunAt} is invalid`);
  }
  if (maxDaysWithoutRun != null && lastRunDate) {
    const today = new Date();
    const todayUtc = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
    const daysSinceRun = diffDateOnlyDays(lastRunDate, todayUtc);
    if (daysSinceRun > maxDaysWithoutRun) {
      attentionReasons.push(`last run ${lastRunAt} is ${daysSinceRun} days old against a ${maxDaysWithoutRun}-day cadence`);
    }
  }

  const scenarios = uiScout.scenarios && typeof uiScout.scenarios === "object" && !Array.isArray(uiScout.scenarios)
    ? uiScout.scenarios
    : {};
  if (Object.keys(scenarios).length === 0) {
    attentionReasons.push("no UI scout scenarios are defined");
  }
  for (const [scenarioId, scenarioValue] of Object.entries(scenarios)) {
    const label = String(scenarioValue.label || scenarioId).trim() || scenarioId;
    const status = String(scenarioValue.status || "").trim();
    const followUpStoryRefs = Array.isArray(scenarioValue.follow_up_story_refs)
      ? scenarioValue.follow_up_story_refs.map(String).sort(compareStoryIdStrings)
      : [];
    const followUpSuffix = followUpStoryRefs.length > 0 ? ` (follow-up stories: ${followUpStoryRefs.join(", ")})` : "";
    if (status === "never") {
      attentionReasons.push(`${scenarioId} (${label}) has never been checked`);
    } else if (status === "issues_found") {
      attentionReasons.push(`${scenarioId} (${label}) still has unresolved issues${followUpSuffix}`);
    } else if (status === "recheck_due") {
      attentionReasons.push(`${scenarioId} (${label}) is awaiting recheck${followUpSuffix}`);
    }
  }

  if (attentionReasons.length > 0) {
    const firstReason = attentionReasons[0];
    const suffix = attentionReasons.length > 1 ? `; +${attentionReasons.length - 1} more` : "";
    return {
      needsAttention: true,
      summary: `attention needed — ${firstReason}${suffix}`,
    };
  }

  return {
    needsAttention: false,
    summary: `fresh — last run ${lastRunAt || "unknown"}`,
  };
}

function parseFrontmatterDocument(text, path) {
  if (!text.startsWith("---\n") && !text.startsWith("---\r\n")) {
    return { frontmatter: {}, body: text, hasFrontmatter: false };
  }

  const lines = text.split(/\r?\n/);
  let end = -1;
  for (let index = 1; index < lines.length; index += 1) {
    if (lines[index].trim() === "---") {
      end = index;
      break;
    }
  }
  if (end === -1) throw new Error(`Unterminated frontmatter in ${path}`);
  return {
    frontmatter: parseSimpleFrontmatter(lines.slice(1, end), path),
    body: lines.slice(end + 1).join("\n"),
    hasFrontmatter: true,
  };
}

function parseSimpleFrontmatter(lines, path) {
  const result = {};
  let currentListKey = null;

  for (const rawLine of lines) {
    const line = rawLine.replace(/\t/g, "  ");
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const listMatch = line.match(/^ {2}-\s+(.+)$/);
    if (listMatch) {
      if (!currentListKey || !Array.isArray(result[currentListKey])) {
        throw new Error(`Frontmatter list item without key in ${path}: ${rawLine}`);
      }
      result[currentListKey].push(stripQuotes(listMatch[1]));
      continue;
    }

    const keyMatch = line.match(/^([a-z0-9_]+):(?:\s+(.*))?$/i);
    if (!keyMatch) throw new Error(`Unsupported frontmatter line in ${path}: ${rawLine}`);

    currentListKey = null;
    const key = keyMatch[1];
    const rawValue = keyMatch[2] ? keyMatch[2].trim() : "";

    if (!rawValue) {
      result[key] = [];
      currentListKey = key;
      continue;
    }

    if (rawValue === "[]") {
      result[key] = [];
      continue;
    }

    result[key] = stripQuotes(rawValue);
  }

  return result;
}

function frontmatterString(frontmatter, key) {
  const value = frontmatter[key];
  return typeof value === "string" ? value : null;
}

function frontmatterStringArray(frontmatter, key) {
  const value = frontmatter[key];
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.filter((entry) => typeof entry === "string");
  return [];
}

function findFirstNonEmptyLine(lines) {
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].trim()) return { index, line: lines[index] };
  }
  return null;
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function extractMarkdownSection(body, heading) {
  const pattern = new RegExp(`(?:^|\\n)##\\s+${escapeRegExp(heading)}\\s*\\n([\\s\\S]*?)(?=\\n##\\s+|$)`);
  const match = body.match(pattern);
  return match ? match[1].trim() : null;
}

function normalizeOptionalSectionText(value) {
  if (typeof value !== "string") return null;
  const normalized = value.trim();
  if (!normalized) return null;
  if (/^(?:n\/a|none|not applicable|not blocked|tbd|—|-)$/i.test(normalized)) return null;
  return normalized;
}

function summarizeInlineText(value, maxLength = 96) {
  if (!value) return "—";
  const inline = value.replace(/\s+/g, " ").trim();
  if (inline.length <= maxLength) return inline;
  return `${inline.slice(0, maxLength - 1).trimEnd()}…`;
}

function compactDateToIso(value) {
  return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`;
}

function summarizeText(value, maxLength = 220) {
  if (!value) return "";
  const inline = String(value).replace(/\s+/g, " ").trim();
  if (!inline) return "";
  if (inline.length <= maxLength) return inline;
  return `${inline.slice(0, maxLength - 1).trimEnd()}…`;
}

function extractLastWorkLogEntry(workLog) {
  if (!workLog) return null;
  const matches = workLog
    .split(/\r?\n/)
    .map((line) => line.trim().match(WORK_LOG_ENTRY_RE))
    .filter(Boolean);
  if (matches.length === 0) return null;
  const last = matches[matches.length - 1];
  const timestamp = last.groups?.stamp || last[1];
  return {
    timestamp,
    date: compactDateToIso(timestamp.slice(0, 8)),
    summary: summarizeText(last.groups?.summary || last[2]),
  };
}

function collectSectionLines(blockLines, key, indent) {
  const marker = `${" ".repeat(indent)}${key}:`;
  const start = blockLines.findIndex((line) => line.startsWith(marker));
  if (start === -1) return [];
  const collected = [];
  for (let index = start + 1; index < blockLines.length; index += 1) {
    const line = blockLines[index];
    if (line.trim() && leadingSpaces(line) <= indent) break;
    collected.push(line);
  }
  return collected;
}

function parseMappingListSection(sectionLines, itemIndent, fieldIndent, listFieldNames = new Set()) {
  const items = [];
  let current = null;
  let currentField = null;
  let currentListField = null;

  for (const line of sectionLines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const indent = leadingSpaces(line);

    if (indent === itemIndent && trimmed.startsWith("- ")) {
      if (current) items.push(current);
      current = {};
      currentField = null;
      currentListField = null;
      const rest = trimmed.slice(2);
      const match = rest.match(/^([a-z_]+):(?:\s*(.*))?$/);
      if (match) {
        const key = match[1];
        const rawValue = match[2] ?? "";
        if (listFieldNames.has(key) && !rawValue) {
          current[key] = [];
          currentListField = key;
        } else {
          current[key] = stripQuotes(stripInlineComment(rawValue));
          currentField = key;
        }
      }
      continue;
    }

    if (!current) continue;

    if (currentListField && indent === fieldIndent + 2 && trimmed.startsWith("- ")) {
      const rest = trimmed.slice(2);
      const conditionMatch = rest.match(/^condition:\s*(.+)$/);
      const value = stripQuotes(stripInlineComment(conditionMatch ? conditionMatch[1] : rest));
      current[currentListField].push(value);
      continue;
    }

    if (indent === fieldIndent) {
      const match = trimmed.match(/^([a-z_]+):(?:\s*(.*))?$/);
      if (match) {
        const key = match[1];
        const rawValue = match[2] ?? "";
        currentListField = null;
        if (listFieldNames.has(key) && !rawValue) {
          current[key] = [];
          currentListField = key;
          currentField = null;
        } else {
          current[key] = stripQuotes(stripInlineComment(rawValue === ">" ? "" : rawValue));
          currentField = key;
        }
        continue;
      }
    }

    if (indent > fieldIndent && currentField && !currentListField) {
      const existing = typeof current[currentField] === "string" ? current[currentField] : "";
      current[currentField] = `${existing} ${trimmed}`.trim();
    }
  }

  if (current) items.push(current);
  return items;
}

function parseRetryWhenSection(sectionLines) {
  return uniqueSorted(
    sectionLines
      .map((line) => {
        const trimmed = line.trim();
        if (leadingSpaces(line) !== 6 || !trimmed.startsWith("- ")) return "";
        const rest = trimmed.slice(2);
        const match = rest.match(/^condition:\s*(.+)$/);
        return stripQuotes(stripInlineComment(match ? match[1] : rest));
      })
      .filter(Boolean),
  );
}

function parseAttemptSection(sectionLines) {
  return parseMappingListSection(sectionLines, 6, 8, new Set(["retry_when"]))
    .map((item) => ({
      id: String(item.id || "").trim(),
      date: String(item.date || "").trim(),
      approach: summarizeText(String(item.approach || "").trim(), 400),
      note: summarizeText(String(item.note || "").trim(), 400),
      retryStatus: String(item.retry_status || "").trim(),
      retryWhen: uniqueSorted(Array.isArray(item.retry_when) ? item.retry_when.map(String).filter(Boolean) : []),
    }))
    .filter((item) => item.id);
}

function parseScoreSection(sectionLines) {
  return parseMappingListSection(sectionLines, 6, 8)
    .map((item) => ({
      model: String(item.model || "").trim(),
      measured: String(item.measured || "").trim(),
      note: summarizeText(String(item.note || "").trim(), 400),
    }))
    .filter((item) => item.model || item.measured || item.note);
}

function latestItem(items, dateKey, fallbackKey) {
  if (!items.length) return null;
  return items
    .slice()
    .sort(
      (a, b) =>
        String(a[dateKey] || "").localeCompare(String(b[dateKey] || "")) ||
        String(a[fallbackKey] || "").localeCompare(String(b[fallbackKey] || "")),
    )
    .at(-1);
}

function summarizeStoryActionability(story) {
  const postureMap = {
    "In Progress": "in-progress",
    Pending: "ready-now",
    Blocked: "blocked",
    Draft: "draft",
    Done: "completed",
    Deferred: "completed",
    Cancelled: "completed",
  };
  const posture = postureMap[story.status] || "unknown";
  return {
    sourceKind: "story",
    sourceId: story.id,
    sourcePath: story.path,
    recommendedNow: posture === "in-progress" || posture === "ready-now",
    posture,
    whyNow: summarizeText(story.lastWorkLogEntry?.summary),
    lastRelevantAction: {
      date: story.lastWorkLogEntry?.date || null,
      sourceType: story.lastWorkLogEntry ? "story-work-log" : "story-status",
      source: story.path,
      summary: story.lastWorkLogEntry?.summary || "",
    },
  };
}

function summarizeEvalActionability(evalRecord) {
  const latestAttempt = latestItem(evalRecord.attempts, "date", "id");
  const latestScore = evalRecord.latestScore;
  const retryWhen = latestAttempt?.retryWhen?.length ? latestAttempt.retryWhen.slice() : evalRecord.retryWhen.slice();
  const retryTriggerStatus =
    latestAttempt?.retryStatus === "exhausted-until-new-trigger"
      ? "exhausted"
      : retryWhen.length > 0
        ? "waiting"
        : "none";
  const postureMap = {
    waiting: "wait-for-trigger",
    exhausted: "trigger-exhausted",
    none: "no-trigger-recorded",
  };
  return {
    sourceKind: "eval",
    sourceId: evalRecord.id,
    sourcePath: evalRecord.path,
    recommendedNow: false,
    posture: postureMap[retryTriggerStatus],
    whyNow: latestAttempt?.note || latestScore?.note || "",
    retryTriggerStatus,
    retryWhen,
    lastRelevantAction: latestAttempt
      ? {
          date: latestAttempt.date || null,
          sourceType: "eval-attempt",
          source: evalRecord.path,
          sourceId: latestAttempt.id,
          summary: latestAttempt.note || latestAttempt.approach,
        }
      : {
          date: latestScore?.measured || null,
          sourceType: "eval-score",
          source: evalRecord.path,
          summary: latestScore?.note || "",
        },
  };
}

function selectStoryByPosture(stories, postureRank) {
  return stories
    .slice()
    .sort((a, b) => {
      const aRank = postureRank[a.actionability?.posture || "unknown"] ?? 99;
      const bRank = postureRank[b.actionability?.posture || "unknown"] ?? 99;
      const rankDelta = aRank - bRank;
      if (rankDelta !== 0) return rankDelta;
      const aDate = a.actionability?.lastRelevantAction.date || "";
      const bDate = b.actionability?.lastRelevantAction.date || "";
      return bDate.localeCompare(aDate) || compareStoryIdStrings(a.id, b.id);
    })[0];
}

function selectCompromiseActionability(stories, evals) {
  const actionableStories = stories.filter((story) => story.actionability?.recommendedNow);
  let selected = null;
  if (actionableStories.length > 0) {
    selected = { ...selectStoryByPosture(actionableStories, { "in-progress": 0, "ready-now": 1 }).actionability };
  } else if (evals.length > 0) {
    selected = {
      ...evals
        .slice()
        .sort((a, b) => {
          const aExhausted = a.actionability?.retryTriggerStatus === "exhausted" ? 1 : 0;
          const bExhausted = b.actionability?.retryTriggerStatus === "exhausted" ? 1 : 0;
          const exhaustedDelta = aExhausted - bExhausted;
          if (exhaustedDelta !== 0) return exhaustedDelta;
          const aDate = a.actionability?.lastRelevantAction.date || "";
          const bDate = b.actionability?.lastRelevantAction.date || "";
          return bDate.localeCompare(aDate) || a.id.localeCompare(b.id);
        })[0].actionability,
    };
  } else if (stories.length > 0) {
    selected = { ...selectStoryByPosture(stories, { blocked: 0, draft: 1, completed: 2, unknown: 3 }).actionability };
  }
  if (!selected) return null;
  selected.storyIds = stories.map((story) => story.id);
  selected.evalIds = evals.map((entry) => entry.id);
  return selected;
}

function parseIdeal() {
  const lines = readUtf8(IDEAL_PATH).split(/\r?\n/);
  const requirements = [];
  let section = null;

  for (const line of lines) {
    if (line.startsWith("## ")) {
      section = line.slice(3).trim();
      continue;
    }

    if (section === "3. Requirements and Quality Bar" || section === "Requirements and Quality Bar") {
      const match = line.match(/^\*\*(R\d+)\.\s+(.+?)\*\*/);
      if (match) requirements.push({ id: match[1], label: match[2].trim() });
    }
  }

  return {
    path: toRelative(IDEAL_PATH),
    title: lines[0].replace(/^#\s*/, "").trim(),
    requirements,
  };
}

function parseSpec() {
  const lines = readUtf8(SPEC_PATH).split(/\r?\n/);
  const categories = [];
  const compromises = new Map();
  let currentCategory = null;

  for (const line of lines) {
    const categoryMatch = line.match(/^##\s+(spec:\d+)\s+—\s+(.+)$/);
    if (categoryMatch) {
      currentCategory = categoryMatch[1];
      categories.push({ id: currentCategory, title: categoryMatch[2].trim(), sections: [] });
      continue;
    }

    const sectionMatch = line.match(/^###\s+(spec:\d+(?:\.\d+)*)\s+—\s+(.+)$/);
    if (sectionMatch && currentCategory) {
      const category = categories.find((entry) => entry.id === currentCategory);
      category.sections.push({ id: sectionMatch[1], title: sectionMatch[2].trim() });
      continue;
    }

    const boldCompromiseMatch = line.match(/^\s*(?:-\s+)?\*\*(C\d+|B\d+):\s+([^*]+)\*\*/);
    if (boldCompromiseMatch && currentCategory && !compromises.has(boldCompromiseMatch[1])) {
      compromises.set(boldCompromiseMatch[1], {
        id: boldCompromiseMatch[1],
        title: boldCompromiseMatch[2].trim(),
        categoryId: currentCategory,
      });
      continue;
    }

    const tableCompromiseMatch = line.match(/^\|\s*(B\d+)\s*\|\s*([^|]+?)\s*\|/);
    if (tableCompromiseMatch && currentCategory && !compromises.has(tableCompromiseMatch[1])) {
      compromises.set(tableCompromiseMatch[1], {
        id: tableCompromiseMatch[1],
        title: tableCompromiseMatch[2].trim(),
        categoryId: currentCategory,
      });
    }
  }

  return {
    path: toRelative(SPEC_PATH),
    categories,
    compromises: Array.from(compromises.values()).sort((a, b) => a.id.localeCompare(b.id)),
  };
}

function parseStory(path) {
  const source = readUtf8(path);
  const parsed = parseFrontmatterDocument(source, toRelative(path));
  const lines = parsed.body.split(/\r?\n/);
  const headingLine = findFirstNonEmptyLine(lines);

  const fileId = basename(path).match(STORY_FILE_RE)?.[1];
  if (!fileId) throw new Error(`Unable to derive story id from ${toRelative(path)}`);

  const headingMatch = headingLine ? headingLine.line.match(STORY_HEADING_RE) : null;
  const title =
    frontmatterString(parsed.frontmatter, "title") ||
    (headingMatch ? headingMatch[2].trim() : basename(path));
  const explicitIdealRefs = frontmatterStringArray(parsed.frontmatter, "ideal_refs");
  const explicitSpecRefs = frontmatterStringArray(parsed.frontmatter, "spec_refs");
  const explicitAdrRefs = frontmatterStringArray(parsed.frontmatter, "adr_refs");
  const explicitDependsOn = frontmatterStringArray(parsed.frontmatter, "depends_on");
  const explicitCategoryRefs = frontmatterStringArray(parsed.frontmatter, "category_refs");
  const explicitCompromiseRefs = frontmatterStringArray(parsed.frontmatter, "compromise_refs");
  const explicitInputCoverageRefs = frontmatterStringArray(parsed.frontmatter, "input_coverage_refs");
  const blockerSummary = normalizeOptionalSectionText(extractMarkdownSection(parsed.body, "Blocker Summary"));
  const blockerEvidence = normalizeOptionalSectionText(extractMarkdownSection(parsed.body, "Blocker Evidence"));
  const unblockCondition = normalizeOptionalSectionText(extractMarkdownSection(parsed.body, "Unblock Condition"));
  const lastWorkLogEntry = extractLastWorkLogEntry(extractMarkdownSection(parsed.body, "Work Log"));
  const missingFrontmatterKeys = parsed.hasFrontmatter
    ? REQUIRED_STORY_FRONTMATTER_KEYS.filter((key) => !(key in parsed.frontmatter))
    : REQUIRED_STORY_FRONTMATTER_KEYS.slice();

  return {
    id: frontmatterString(parsed.frontmatter, "id") || fileId,
    title,
    path: toRelative(path),
    status: frontmatterString(parsed.frontmatter, "status") || "Unknown",
    priority: frontmatterString(parsed.frontmatter, "priority") || "Unknown",
    idealRefs: uniqueSorted(explicitIdealRefs),
    specRefs: uniqueSorted(explicitSpecRefs),
    adrIds: uniqueSorted(explicitAdrRefs),
    compromiseIds: uniqueSorted(explicitCompromiseRefs),
    dependsOn: uniqueSorted(explicitDependsOn, compareStoryIdStrings),
    categoryRefs: uniqueSorted(explicitCategoryRefs, compareSpecRefs),
    inputCoverageRefs: uniqueSorted(explicitInputCoverageRefs),
    architectureDomains: uniqueSorted(frontmatterStringArray(parsed.frontmatter, "architecture_domains")),
    roadmapTags: uniqueSorted(frontmatterStringArray(parsed.frontmatter, "roadmap_tags")),
    legacySystem: frontmatterString(parsed.frontmatter, "legacy_system") || "",
    blockerSummary,
    blockerEvidence,
    unblockCondition,
    lastWorkLogEntry,
    metadataSource: parsed.hasFrontmatter ? "frontmatter" : "legacy",
    missingFrontmatterKeys,
  };
}

function parseStories() {
  return readdirSync(STORIES_DIR)
    .filter((file) => STORY_FILE_RE.test(file))
    .sort()
    .map((file) => parseStory(join(STORIES_DIR, file)));
}

function parseAdr(path) {
  const source = readUtf8(path);
  const parsed = parseFrontmatterDocument(source, toRelative(path));
  const lines = parsed.body.split(/\r?\n/);
  const headingLine = findFirstNonEmptyLine(lines);
  const heading = headingLine ? headingLine.line.match(/^#\s+(ADR-\d{3}):\s+(.+)$/) : null;
  if (!heading) throw new Error(`Unable to parse ADR heading in ${toRelative(path)}`);
  const explicitSpecRefs = frontmatterStringArray(parsed.frontmatter, "spec_refs");
  const explicitStoryRefs = frontmatterStringArray(parsed.frontmatter, "story_refs");
  const explicitCompromiseRefs = frontmatterStringArray(parsed.frontmatter, "compromise_refs");
  const explicitIdealRefs = frontmatterStringArray(parsed.frontmatter, "ideal_refs");
  const explicitRelatedAdrs = frontmatterStringArray(parsed.frontmatter, "related_adrs");
  const explicitSupersedes = frontmatterStringArray(parsed.frontmatter, "supersedes");
  const explicitSupersededBy = frontmatterStringArray(parsed.frontmatter, "superseded_by");
  const missingFrontmatterKeys = parsed.hasFrontmatter
    ? REQUIRED_ADR_FRONTMATTER_KEYS.filter((key) => !(key in parsed.frontmatter))
    : REQUIRED_ADR_FRONTMATTER_KEYS.slice();

  return {
    id: heading[1],
    title: heading[2].trim(),
    path: toRelative(path),
    status: frontmatterString(parsed.frontmatter, "status") || "UNKNOWN",
    specRefs: uniqueSorted(explicitSpecRefs),
    storyIds: uniqueSorted(explicitStoryRefs, compareStoryIdStrings),
    compromiseIds: uniqueSorted(explicitCompromiseRefs),
    idealRefs: uniqueSorted(explicitIdealRefs),
    relatedAdrIds: uniqueSorted(explicitRelatedAdrs),
    supersedes: uniqueSorted(explicitSupersedes),
    supersededBy: uniqueSorted(explicitSupersededBy),
    metadataSource: parsed.hasFrontmatter ? "frontmatter" : "legacy",
    missingFrontmatterKeys,
  };
}

function parseAdrs() {
  const records = [];
  for (const entry of readdirSync(ADRS_DIR).sort()) {
    const path = join(ADRS_DIR, entry, "adr.md");
    if (existsSync(path)) records.push(parseAdr(path));
  }
  return records;
}

function parseEvalRegistry() {
  const lines = readUtf8(EVALS_PATH).split(/\r?\n/);
  const records = [];
  let current = null;
  let currentListField = null;
  let currentTextField = null;
  let block = [];

  const flush = () => {
    if (!current || !current.id) return;
    const topLevelRetryWhen = parseRetryWhenSection(collectSectionLines(block, "retry_when", 4));
    const attempts = parseAttemptSection(collectSectionLines(block, "attempts", 4));
    const latestScore = latestItem(parseScoreSection(collectSectionLines(block, "scores", 4)), "measured", "model") || null;
    const specRefs = uniqueSorted(current.spec_refs || [], compareSpecRefs);
    const storyIds = uniqueSorted(current.story_refs || [], compareStoryIdStrings);
    const categoryRefs = uniqueSorted(current.category_refs || [], compareSpecRefs);
    const compromiseIds = uniqueSorted(current.compromise_refs || []);
    records.push({
      id: current.id,
      name: current.name || current.id,
      type: current.type || "unknown",
      command: current.command || "",
      description: summarizeText(current.description || "", 500),
      path: toRelative(EVALS_PATH),
      specRefs,
      storyIds,
      categoryRefs,
      compromiseIds,
      retryWhen: topLevelRetryWhen,
      attempts,
      latestScore,
      declaredSpecRefs: specRefs,
      declaredStoryIds: storyIds,
      declaredCategoryRefs: categoryRefs,
      declaredCompromiseIds: compromiseIds,
      missingLineageKeys: REQUIRED_EVAL_LINEAGE_KEYS.filter((key) => !current.seenLineageKeys.has(key)),
    });
  };

  for (const line of lines) {
    const idMatch = line.match(/^ {2}- id:\s+(.+)$/);
    if (idMatch) {
      flush();
      current = {
        id: stripQuotes(idMatch[1]),
        spec_refs: [],
        story_refs: [],
        category_refs: [],
        compromise_refs: [],
        seenLineageKeys: new Set(),
      };
      block = [line];
      currentListField = null;
      currentTextField = null;
      continue;
    }
    if (!current) continue;
    block.push(line);

    const lineageMatch = line.match(/^ {4}(spec_refs|story_refs|category_refs|compromise_refs):(?:\s+(.*))?$/);
    if (lineageMatch) {
      const key = lineageMatch[1];
      const rawValue = lineageMatch[2] ? lineageMatch[2].trim() : "";
      current.seenLineageKeys.add(key);
      currentListField = null;
      currentTextField = null;
      if (!rawValue) {
        current[key] = [];
        currentListField = key;
        continue;
      }
      if (rawValue === "[]") {
        current[key] = [];
        continue;
      }
      current[key] = [stripQuotes(rawValue)];
      continue;
    }

    const listItemMatch = line.match(/^ {6}-\s+(.+)$/);
    if (listItemMatch && currentListField) {
      current[currentListField].push(stripQuotes(listItemMatch[1]));
      continue;
    }

    if (/^ {4}[a-z0-9_]+:/i.test(line)) {
      currentListField = null;
      currentTextField = null;
    }

    const fieldMatch = line.match(/^ {4}(name|type|command|description):(?:\s+(.*))?$/);
    if (fieldMatch) {
      const key = fieldMatch[1];
      const rawValue = fieldMatch[2] ? fieldMatch[2].trim() : "";
      current[key] = stripQuotes(rawValue === ">" ? "" : rawValue);
      currentTextField = key;
      continue;
    }

    if (leadingSpaces(line) > 4 && currentTextField && !currentListField) {
      const existing = typeof current[currentTextField] === "string" ? current[currentTextField] : "";
      current[currentTextField] = summarizeText(`${existing} ${line.trim()}`.trim(), 500);
    }
  }

  flush();
  return records;
}

function markdownFromSection(section) {
  if (typeof section.markdown === "string") return section.markdown.trim();
  if (Array.isArray(section.lines)) return section.lines.join("\n").trim();
  return "";
}

function formatExampleList(values, limit = 3) {
  if (values.length <= limit) return values.join(", ");
  return `${values.slice(0, limit).join(", ")} +${values.length - limit} more`;
}

function pushUnexpectedKeys(errors, value, allowedKeys, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return;
  for (const key of Object.keys(value)) {
    if (!allowedKeys.has(key)) errors.push(`${label}.${key} is not a recognized structured state key`);
  }
}

function renderCurrentExecutionMap(currentExecutionMap, stories, { healthFlag = false } = {}) {
  if (!currentExecutionMap || typeof currentExecutionMap !== "object") return null;

  const lines = [];
  const summary = typeof currentExecutionMap.summary === "string" ? currentExecutionMap.summary.trim() : "";
  const lanes = Array.isArray(currentExecutionMap.lanes) ? currentExecutionMap.lanes : [];
  const storyById = new Map(stories.map((story) => [story.id, story]));

  if (!healthFlag && summary) lines.push(summary, "");

  for (const lane of lanes) {
    if (Boolean(lane.health_flag) !== healthFlag) continue;

    const title = String(lane.title || "").trim();
    if (!title) continue;

    const statuses = new Set(Array.isArray(lane.statuses) ? lane.statuses.map(String) : []);
    const emptyMessage = String(lane.empty_message || "No stories currently fit this lane.").trim();
    const storyNotes =
      lane.story_notes && typeof lane.story_notes === "object" && !Array.isArray(lane.story_notes)
        ? lane.story_notes
        : {};
    const laneRows = Object.keys(storyNotes)
      .sort(compareStoryIdStrings)
      .map((storyId) => ({ storyId, story: storyById.get(storyId), reason: String(storyNotes[storyId] || "").trim() }))
      .filter(({ story, reason }) => story && reason && (statuses.size === 0 || statuses.has(story.status)));

    lines.push(`### ${title}`, "");
    if (laneRows.length === 0) {
      lines.push(emptyMessage, "");
      continue;
    }

    lines.push("| Story | Why |");
    lines.push("|---|---|");
    for (const { story, reason } of laneRows) {
      lines.push(`| **${story.id}** ${story.title.replaceAll("|", "\\|")} | ${reason.replaceAll("|", "\\|")} |`);
    }
    lines.push("");
  }

  return lines.join("\n").trim();
}

function renderStoriesIndex(graph) {
  const lines = [];
  const categoryOrder = new Map(graph.spec.categories.map((category, index) => [category.id, index]));
  const state = graph.state;
  const roadmap = state.roadmap || {};
  const activeFocus = Array.isArray(roadmap.active_focus) ? roadmap.active_focus.map(String) : [];
  const sequencingBias = Array.isArray(roadmap.sequencing_bias) ? roadmap.sequencing_bias : [];
  const campaigns = Array.isArray(roadmap.campaigns) ? roadmap.campaigns.filter((entry) => entry.status === "active") : [];
  const currentExecutionMap = (state.stories_index || {}).current_execution_map || null;
  const customSections = Array.isArray((state.stories_index || {}).sections) ? state.stories_index.sections : [];
  const uiScoutFreshness = analyzeUiScoutFreshness(state.ui_scout);
  const statusRank = new Map([
    ["In Progress", 0],
    ["Pending", 1],
    ["Blocked", 2],
    ["Draft", 3],
    ["Deferred", 4],
    ["Done", 5],
    ["Cancelled", 6],
  ]);
  const priorityRank = new Map([
    ["High", 0],
    ["Medium", 1],
    ["Low", 2],
  ]);

  const primaryCategoryId = (story) => {
    if (story.categoryRefs.length === 0) return null;
    return story.categoryRefs
      .slice()
      .sort((a, b) => (categoryOrder.get(a) || 999) - (categoryOrder.get(b) || 999) || compareSpecRefs(a, b))[0];
  };

  const storySort = (a, b) => {
    const statusDelta = (statusRank.get(a.status) ?? 99) - (statusRank.get(b.status) ?? 99);
    if (statusDelta !== 0) return statusDelta;
    const priorityDelta = (priorityRank.get(a.priority) ?? 99) - (priorityRank.get(b.priority) ?? 99);
    if (priorityDelta !== 0) return priorityDelta;
    return compareStoryRecords(a, b);
  };

  const storiesByPrimaryCategory = new Map();
  const uncategorized = [];
  for (const story of graph.stories) {
    const categoryId = primaryCategoryId(story);
    if (!categoryId) {
      uncategorized.push(story);
      continue;
    }
    if (!storiesByPrimaryCategory.has(categoryId)) storiesByPrimaryCategory.set(categoryId, []);
    storiesByPrimaryCategory.get(categoryId).push(story);
  }
  for (const stories of storiesByPrimaryCategory.values()) stories.sort(storySort);
  uncategorized.sort(storySort);

  lines.push("# Project Stories — cine-forge", "");
  lines.push("> Generated from story metadata + `docs/methodology/state.yaml`. Do not edit manually.", "");
  lines.push("## Status Key", "");
  lines.push("- **Draft** — Worth preserving, but still incomplete or substrate-unverified");
  lines.push("- **Pending** — Fully detailed and honestly buildable now");
  lines.push("- **In Progress** — Active work");
  lines.push("- **Blocked** — Concrete enough to preserve, but blocked by a named evidence-backed blocker");
  lines.push("- **Deferred** — Intentionally parked");
  lines.push("- **Cancelled** — Explicitly abandoned");
  lines.push("- **Done** — Complete and validated");
  lines.push("");
  lines.push("## Numbering Convention", "");
  lines.push("Story IDs are identifiers, not sequencing proof. Legacy suffix IDs such as `003b` and `011f` remain valid historical identifiers. New stories should continue using the next available plain numeric ID.");
  lines.push("");

  const currentExecutionMapMarkdown = renderCurrentExecutionMap(currentExecutionMap, graph.stories);
  if (currentExecutionMapMarkdown) {
    lines.push("## Current Execution Map", "", currentExecutionMapMarkdown, "");
  }
  const healthFlagsMarkdown = renderCurrentExecutionMap(currentExecutionMap, graph.stories, { healthFlag: true });
  if (healthFlagsMarkdown) {
    lines.push("## Health Flags", "", healthFlagsMarkdown, "");
  }

  for (const section of customSections) {
    const markdown = markdownFromSection(section);
    const title = String(section.title || "").trim();
    if (!title || !markdown) continue;
    lines.push(`## ${title}`, "", markdown, "");
  }

  if (activeFocus.length > 0 || sequencingBias.length > 0 || campaigns.length > 0 || uiScoutFreshness) {
    lines.push("## Active Focus", "");
    if (activeFocus.length > 0) lines.push(`- Active categories: ${activeFocus.map((entry) => `\`${entry}\``).join(", ")}`);
    if (uiScoutFreshness) lines.push(`- UI scout freshness: ${uiScoutFreshness.summary}`);
    for (const bias of sequencingBias) {
      const storyRefs = Array.isArray(bias.story_refs) ? bias.story_refs.map(String).sort(compareStoryIdStrings) : [];
      const suffix = storyRefs.length > 0 ? ` (stories: ${storyRefs.join(", ")})` : "";
      lines.push(`- Sequencing bias: \`${String(bias.target || "")}\`${suffix} — ${String(bias.reason || "")}`);
    }
    for (const campaign of campaigns) {
      const storyRefs = Array.isArray(campaign.story_refs) ? campaign.story_refs.map(String).sort(compareStoryIdStrings) : [];
      const suffix = storyRefs.length > 0 ? ` (stories: ${storyRefs.join(", ")})` : "";
      lines.push(`- Active campaign \`${String(campaign.id || "")}\`${suffix}: ${String(campaign.notes || "")}`);
    }
    lines.push("");
  }

  lines.push("## Story Index", "");
  lines.push("Grouped by primary `spec:N` category. Stories keep all category refs visible in the table.");
  lines.push("");

  const pushStoryTable = (stories) => {
    lines.push("| ID | Title | Priority | Status | Blocker | Categories | Depends On | Link |");
    lines.push("|---|---|---|---|---|---|---|---|");
    for (const story of stories) {
      const blocker = story.status === "Blocked" ? summarizeInlineText(story.blockerSummary) : "—";
      lines.push(
        `| ${story.id} | ${story.title.replaceAll("|", "\\|")} | ${story.priority} | ${story.status} | ${blocker.replaceAll("|", "\\|")} | ${story.categoryRefs.join(", ") || "—"} | ${story.dependsOn.join(", ") || "—"} | [story-${story.id}](${story.path.replace(/^docs\//, "")}) |`,
      );
    }
    lines.push("");
  };

  for (const category of graph.spec.categories) {
    const stories = storiesByPrimaryCategory.get(category.id) || [];
    if (stories.length === 0) continue;
    lines.push(`### ${category.id} — ${category.title}`, "");
    pushStoryTable(stories);
  }
  if (uncategorized.length > 0) {
    lines.push("### Uncategorized", "");
    pushStoryTable(uncategorized);
  }

  return `${lines.join("\n").trimEnd()}\n`;
}

function renderBuildMap(graph) {
  const lines = [];
  lines.push("# Build Map", "");
  lines.push("> Generated from `docs/methodology/state.yaml` + `docs/methodology/graph.json`. Do not edit manually.");
  lines.push("> Canonical planning state lives in `docs/methodology/state.yaml`; this file is a human-readable dashboard view.", "");
  lines.push("## How to Read This Map", "");
  lines.push("- **Product need**: what the category must deliver to the user or the execution experience.");
  lines.push("- **Tech need**: what architectural or workflow substrate must exist.");
  lines.push("- **Substrate** and **Phase** come from structured operational state.");
  lines.push("- **Stories / ADR Refs / Evals** are compiled from canonical sources.");
  lines.push("");

  for (const category of graph.spec.categories) {
    const categoryState = category.state || {};
    const storyCoverage = categoryState.story_coverage || (category.storyIds.length > 0 ? "partial" : "none");
    const absorbs = Array.isArray(categoryState.absorbs) ? categoryState.absorbs : [];
    const notes = Array.isArray(categoryState.notes) ? categoryState.notes : [];
    const adrs = category.adrIds.length > 0 ? category.adrIds.join(", ") : "None found after search";
    lines.push(`## ${category.id} — ${category.title}`, "");
    lines.push(`**Product need:** ${String(categoryState.product_need || "TBD")}`);
    lines.push(`**Tech need:** ${String(categoryState.tech_need || "TBD")}`);
    lines.push(`**Substrate:** ${String(categoryState.substrate || "unknown")}`);
    lines.push(`**Phase:** ${String(categoryState.phase || "unknown")}`);
    lines.push("");
    lines.push(`**Story coverage:** ${storyCoverage}`);
    lines.push(`**Stories:** ${category.storyIds.length > 0 ? category.storyIds.sort(compareStoryIdStrings).join(", ") : "None yet"}`);
    lines.push(`**ADR Refs:** ${adrs}`);
    lines.push(`**Spec:** ${category.id}${category.sections.length > 0 ? ` (${category.sections.map((section) => section.id).join(", ")})` : ""}`);
    lines.push(`**Absorbs:** ${absorbs.length > 0 ? absorbs.join("; ") : "None"}`);
    lines.push("");
    if (notes.length > 0) {
      lines.push("### Phase Notes", "");
      for (const note of notes) lines.push(`- ${note}`);
      lines.push("");
    }
    const categoryCompromises = graph.spec.compromises.filter((entry) => entry.categoryId === category.id);
    if (categoryCompromises.length > 0) {
      lines.push("### Compromise Progress", "");
      for (const compromise of categoryCompromises) {
        const state = compromise.state || {};
        lines.push(`- **${compromise.id}: ${compromise.title}** — **${String(state.phase || "unknown")}**`);
        if (state.current) lines.push(`  - Current: ${String(state.current)}`);
        if (state.converge_signal) lines.push(`  - Converge signal: ${String(state.converge_signal)}`);
        if (state.evidence) lines.push(`  - Evidence: ${String(state.evidence)}`);
      }
      lines.push("");
    }
  }

  lines.push("---", "");
  lines.push(`*Last generated: ${new Date().toISOString().slice(0, 10)}*`);
  return `${lines.join("\n").trimEnd()}\n`;
}

function validateGraph(state, spec, stories, adrs, evals) {
  const errors = [];
  const warnings = [];
  const categoryIds = new Set(spec.categories.map((entry) => entry.id));
  const specSectionIds = new Set(spec.categories.flatMap((entry) => entry.sections.map((section) => section.id)));
  const validSpecRefs = new Set([...categoryIds, ...specSectionIds]);
  const compromiseIds = new Set(spec.compromises.map((entry) => entry.id));
  const storyIds = new Set(stories.map((entry) => entry.id));
  const storyById = new Map(stories.map((entry) => [entry.id, entry]));
  const adrIds = new Set(adrs.map((entry) => entry.id));
  const campaignIds = new Set(((state.roadmap || {}).campaigns || []).map((campaign) => String(campaign.id || "")));
  const auditDomains = (((state.architecture_audits || {}).domains || {}));
  const auditDomainIds = new Set(Object.keys(auditDomains));
  const uiScoutReportIds = collectUiScoutReportIds();
  const uiScout = state.ui_scout || {};

  pushUnexpectedKeys(errors, state, VALID_STATE_TOP_LEVEL_KEYS, "state");
  for (const categoryId of Object.keys(state.categories || {})) {
    if (!categoryIds.has(categoryId)) errors.push(`state.categories.${categoryId} does not match any spec category`);
    pushUnexpectedKeys(errors, (state.categories || {})[categoryId], VALID_STATE_CATEGORY_KEYS, `state.categories.${categoryId}`);
  }
  for (const compromiseId of Object.keys(state.compromises || {})) {
    if (!compromiseIds.has(compromiseId)) errors.push(`state.compromises.${compromiseId} does not match any spec compromise`);
    pushUnexpectedKeys(errors, (state.compromises || {})[compromiseId], VALID_STATE_COMPROMISE_KEYS, `state.compromises.${compromiseId}`);
  }

  pushUnexpectedKeys(errors, state.stories_index || {}, VALID_STATE_STORIES_INDEX_KEYS, "state.stories_index");
  const customSections = Array.isArray((state.stories_index || {}).sections) ? state.stories_index.sections : [];
  customSections.forEach((section, index) => {
    pushUnexpectedKeys(errors, section, VALID_STATE_SECTION_KEYS, `state.stories_index.sections[${index}]`);
    if (String(section.id || "") === "current-execution-map") {
      errors.push(`state.stories_index.sections[${index}] uses deprecated current-execution-map prose; use state.stories_index.current_execution_map instead`);
    }
  });

  const currentExecutionMap = (state.stories_index || {}).current_execution_map || {};
  pushUnexpectedKeys(errors, currentExecutionMap, VALID_STATE_CURRENT_EXECUTION_MAP_KEYS, "state.stories_index.current_execution_map");
  const currentExecutionMapLanes = Array.isArray(currentExecutionMap.lanes) ? currentExecutionMap.lanes : [];
  currentExecutionMapLanes.forEach((lane, index) => {
    pushUnexpectedKeys(errors, lane, VALID_STATE_EXECUTION_LANE_KEYS, `state.stories_index.current_execution_map.lanes[${index}]`);
    const laneLabel = String(lane.id || lane.title || index);
    const statuses = Array.isArray(lane.statuses) ? lane.statuses.map(String) : [];
    if (typeof lane.health_flag !== "undefined" && typeof lane.health_flag !== "boolean") {
      errors.push(`state.stories_index.current_execution_map.lanes[${index}] (${laneLabel}) uses invalid health_flag value`);
    }
    const storyNotes =
      lane.story_notes && typeof lane.story_notes === "object" && !Array.isArray(lane.story_notes)
        ? lane.story_notes
        : {};
    statuses.forEach((status) => {
      if (!VALID_STORY_STATUSES.has(status)) {
        errors.push(`state.stories_index.current_execution_map.lanes[${index}] (${laneLabel}) uses invalid status ${status}`);
      }
    });
    Object.keys(storyNotes).forEach((storyRef) => {
      if (!storyIds.has(storyRef)) {
        errors.push(`state.stories_index.current_execution_map.lanes[${index}] (${laneLabel}) references missing story ${storyRef}`);
        return;
      }
      const story = storyById.get(storyRef);
      if (statuses.length > 0 && !statuses.includes(story.status)) {
        errors.push(
          `state.stories_index.current_execution_map.lanes[${index}] (${laneLabel}) references story ${storyRef} with status ${story.status}, expected ${statuses.join(" / ")}`,
        );
      }
    });
  });

  pushUnexpectedKeys(errors, state.roadmap || {}, VALID_STATE_ROADMAP_KEYS, "state.roadmap");
  const sequencingBiasEntries = Array.isArray((state.roadmap || {}).sequencing_bias) ? (state.roadmap || {}).sequencing_bias : [];
  sequencingBiasEntries.forEach((entry, index) => {
    pushUnexpectedKeys(errors, entry, VALID_STATE_SEQUENCING_BIAS_KEYS, `state.roadmap.sequencing_bias[${index}]`);
    const storyRefs = Array.isArray(entry.story_refs) ? entry.story_refs.map(String) : [];
    storyRefs.forEach((storyRef) => {
      if (!storyIds.has(storyRef)) {
        errors.push(`state.roadmap.sequencing_bias[${index}] references missing story ${storyRef}`);
      }
    });
    if (
      storyRefs.length > 0 &&
      storyRefs.every((storyRef) => {
        const story = storyById.get(storyRef);
        return story && TERMINAL_STORY_STATUSES.has(story.status);
      })
    ) {
      errors.push(`state.roadmap.sequencing_bias[${index}] points only at terminal stories: ${storyRefs.join(", ")}`);
    }
  });

  const campaigns = Array.isArray((state.roadmap || {}).campaigns) ? (state.roadmap || {}).campaigns : [];
  campaigns.forEach((campaign, index) => {
    pushUnexpectedKeys(errors, campaign, VALID_STATE_CAMPAIGN_KEYS, `state.roadmap.campaigns[${index}]`);
    const storyRefs = Array.isArray(campaign.story_refs) ? campaign.story_refs.map(String) : [];
    storyRefs.forEach((storyRef) => {
      if (!storyIds.has(storyRef)) {
        errors.push(`state.roadmap.campaigns[${index}] (${String(campaign.id || index)}) references missing story ${storyRef}`);
      }
    });
    if (
      String(campaign.status || "") === "active" &&
      storyRefs.length > 0 &&
      storyRefs.every((storyRef) => {
        const story = storyById.get(storyRef);
        return story && TERMINAL_STORY_STATUSES.has(story.status);
      })
    ) {
      errors.push(`state.roadmap.campaigns[${index}] (${String(campaign.id || index)}) is active but only references terminal stories: ${storyRefs.join(", ")}`);
    }
  });

  if (typeof state.ui_scout === "undefined") {
    errors.push("state.ui_scout is required for the canonical UI product-truth lane");
  } else if (!state.ui_scout || typeof state.ui_scout !== "object" || Array.isArray(state.ui_scout)) {
    errors.push("state.ui_scout must be an object");
  }
  pushUnexpectedKeys(errors, uiScout, VALID_STATE_UI_SCOUT_KEYS, "state.ui_scout");
  pushUnexpectedKeys(errors, (uiScout || {}).cadence || {}, VALID_STATE_UI_SCOUT_CADENCE_KEYS, "state.ui_scout.cadence");
  if (typeof uiScout.last_run_at !== "undefined" && !parseDateOnlyUtc(uiScout.last_run_at)) {
    errors.push("state.ui_scout.last_run_at must use YYYY-MM-DD");
  }
  if (typeof uiScout.last_run_story_id !== "undefined" && !storyIds.has(String(uiScout.last_run_story_id))) {
    errors.push(`state.ui_scout.last_run_story_id references missing story ${String(uiScout.last_run_story_id)}`);
  }
  if (
    typeof ((uiScout || {}).cadence || {}).max_days_without_run !== "undefined" &&
    (!Number.isInteger(uiScout.cadence.max_days_without_run) || uiScout.cadence.max_days_without_run < 1)
  ) {
    errors.push("state.ui_scout.cadence.max_days_without_run must be a positive integer");
  }
  const uiScoutScenarios =
    uiScout.scenarios && typeof uiScout.scenarios === "object" && !Array.isArray(uiScout.scenarios)
      ? uiScout.scenarios
      : {};
  if (typeof uiScout.scenarios !== "undefined" && (!uiScout.scenarios || typeof uiScout.scenarios !== "object" || Array.isArray(uiScout.scenarios))) {
    errors.push("state.ui_scout.scenarios must be an object keyed by scenario id");
  }
  for (const [scenarioId, scenarioValue] of Object.entries(uiScoutScenarios)) {
    pushUnexpectedKeys(errors, scenarioValue, VALID_STATE_UI_SCOUT_SCENARIO_KEYS, `state.ui_scout.scenarios.${scenarioId}`);
    const status = String(scenarioValue.status || "");
    if (status && !VALID_UI_SCOUT_SCENARIO_STATUSES.has(status)) {
      errors.push(`state.ui_scout.scenarios.${scenarioId}.status uses invalid value ${status}`);
    }
    if (typeof scenarioValue.last_checked !== "undefined" && !parseDateOnlyUtc(scenarioValue.last_checked)) {
      errors.push(`state.ui_scout.scenarios.${scenarioId}.last_checked must use YYYY-MM-DD`);
    }
    if (
      typeof scenarioValue.latest_report !== "undefined" &&
      !uiScoutReportIds.has(String(scenarioValue.latest_report))
    ) {
      errors.push(`state.ui_scout.scenarios.${scenarioId}.latest_report references missing docs/ui-scout report ${String(scenarioValue.latest_report)}`);
    }
    const followUpStoryRefs = Array.isArray(scenarioValue.follow_up_story_refs)
      ? scenarioValue.follow_up_story_refs.map(String)
      : [];
    for (const storyRef of followUpStoryRefs) {
      if (!storyIds.has(storyRef)) {
        errors.push(`state.ui_scout.scenarios.${scenarioId}.follow_up_story_refs includes missing story ${storyRef}`);
      }
    }
  }

  for (const story of stories) {
    if (story.metadataSource !== "frontmatter") {
      errors.push(`story ${story.id} is missing frontmatter; legacy story metadata parsing has been retired`);
    }
    if (story.metadataSource === "frontmatter" && story.missingFrontmatterKeys.length > 0) {
      errors.push(`story ${story.id} frontmatter missing keys: ${story.missingFrontmatterKeys.join(", ")}`);
    }
    if (story.categoryRefs.length === 0) {
      errors.push(`story ${story.id} has no category_refs; explicit story category ownership is required`);
    }
    if (!VALID_STORY_STATUSES.has(story.status)) warnings.push(`story ${story.id} has non-standard status ${story.status}`);
    if (story.status === "Blocked") {
      if (!story.blockerSummary) errors.push(`story ${story.id} is Blocked but missing Blocker Summary`);
      if (!story.blockerEvidence) errors.push(`story ${story.id} is Blocked but missing Blocker Evidence`);
      if (!story.unblockCondition) errors.push(`story ${story.id} is Blocked but missing Unblock Condition`);
    } else if (story.blockerSummary || story.blockerEvidence || story.unblockCondition) {
      warnings.push(`story ${story.id} is ${story.status} but still carries blocker details; clear them or restore N/A when unblocked`);
    }
    for (const dependency of story.dependsOn) {
      if (!storyIds.has(dependency)) errors.push(`story ${story.id} depends_on missing story ${dependency}`);
      if (dependency === story.id) errors.push(`story ${story.id} cannot depend on itself`);
    }
    for (const adrId of story.adrIds) {
      if (!adrIds.has(adrId)) warnings.push(`story ${story.id} references ADR with no local adr.md: ${adrId}`);
    }
    for (const compromiseId of story.compromiseIds) {
      if (!compromiseIds.has(compromiseId)) errors.push(`story ${story.id} references missing compromise ${compromiseId}`);
    }
    for (const categoryId of story.categoryRefs) {
      if (!categoryIds.has(categoryId)) errors.push(`story ${story.id} references missing category ${categoryId}`);
    }
    for (const specRef of story.specRefs.filter((entry) => entry.startsWith("spec:"))) {
      if (!validSpecRefs.has(specRef)) errors.push(`story ${story.id} references missing spec ref ${specRef}`);
    }
    for (const domainId of story.architectureDomains) {
      if (!auditDomainIds.has(domainId)) errors.push(`story ${story.id} references missing architecture domain ${domainId}`);
    }
    for (const tag of story.roadmapTags) {
      if (tag.startsWith("campaign:") && !campaignIds.has(tag.replace(/^campaign:/, ""))) {
        errors.push(`story ${story.id} references missing roadmap campaign ${tag}`);
      }
    }
  }

  for (const adr of adrs) {
    if (adr.metadataSource !== "frontmatter") {
      errors.push(`ADR ${adr.id} is missing frontmatter; legacy ADR metadata parsing has been retired`);
    }
    if (adr.metadataSource === "frontmatter" && adr.missingFrontmatterKeys.length > 0) {
      errors.push(`ADR ${adr.id} frontmatter missing keys: ${adr.missingFrontmatterKeys.join(", ")}`);
    }
    for (const storyId of adr.storyIds) {
      if (!storyIds.has(storyId)) errors.push(`ADR ${adr.id} references missing story ${storyId}`);
    }
    for (const compromiseId of adr.compromiseIds) {
      if (!compromiseIds.has(compromiseId)) errors.push(`ADR ${adr.id} references missing compromise ${compromiseId}`);
    }
    for (const specRef of adr.specRefs.filter((entry) => entry.startsWith("spec:"))) {
      if (!validSpecRefs.has(specRef)) errors.push(`ADR ${adr.id} references missing spec ref ${specRef}`);
    }
  }

  for (const evalRecord of evals) {
    if (evalRecord.missingLineageKeys.length > 0) {
      errors.push(`eval ${evalRecord.id} is missing explicit lineage fields: ${evalRecord.missingLineageKeys.join(", ")}`);
    }
    if (evalRecord.declaredCategoryRefs.length === 0) {
      errors.push(`eval ${evalRecord.id} has no category_refs; explicit eval category ownership is required`);
    } else if (
      (evalRecord.derivedCategoryRefs || []).join(", ") !== evalRecord.declaredCategoryRefs.join(", ")
    ) {
      errors.push(
        `eval ${evalRecord.id} category_refs mismatch derived lineage: declared ${evalRecord.declaredCategoryRefs.join(", ") || "—"} vs derived ${(evalRecord.derivedCategoryRefs || []).join(", ") || "—"}`,
      );
    }
    for (const categoryId of evalRecord.categoryRefs) {
      if (!categoryIds.has(categoryId)) errors.push(`eval ${evalRecord.id} references missing category ${categoryId}`);
    }
    for (const storyId of evalRecord.storyIds) {
      if (!storyIds.has(storyId)) errors.push(`eval ${evalRecord.id} references missing story ${storyId}`);
    }
    for (const compromiseId of evalRecord.compromiseIds) {
      if (!compromiseIds.has(compromiseId)) errors.push(`eval ${evalRecord.id} references missing compromise ${compromiseId}`);
    }
    for (const specRef of evalRecord.specRefs.filter((entry) => entry.startsWith("spec:"))) {
      if (!validSpecRefs.has(specRef)) errors.push(`eval ${evalRecord.id} references missing spec ref ${specRef}`);
    }
  }

  pushUnexpectedKeys(errors, state.architecture_audits || {}, VALID_STATE_ARCHITECTURE_AUDIT_KEYS, "state.architecture_audits");
  pushUnexpectedKeys(errors, (state.architecture_audits || {}).cadence || {}, VALID_STATE_AUDIT_CADENCE_KEYS, "state.architecture_audits.cadence");
  for (const [domainId, domainValue] of Object.entries(auditDomains)) {
    pushUnexpectedKeys(errors, domainValue, VALID_STATE_AUDIT_DOMAIN_KEYS, `state.architecture_audits.domains.${domainId}`);
    const storyRefs = Array.isArray(domainValue.recent_story_refs) ? domainValue.recent_story_refs.map(String) : [];
    for (const storyRef of storyRefs) {
      if (!storyIds.has(storyRef)) errors.push(`state.architecture_audits.domains.${domainId}.recent_story_refs includes missing story ${storyRef}`);
    }
  }

  for (const activePath of ACTIVE_SURFACE_PATHS) {
    if (!existsSync(activePath)) continue;
    const lines = readUtf8(activePath).split(/\r?\n/);
    lines.forEach((line, index) => {
      if (MANUAL_STORIES_RE.test(line) && !ALLOWED_LEGACY_CONTEXT_RE.test(line)) {
        errors.push(`${toRelative(activePath)}:${index + 1} still teaches manual docs/stories.md edits`);
      }
      if (
        STORY_INDEX_FRAMING_RE.test(line) &&
        !ALLOWED_STORIES_INDEX_CONTEXT_RE.test(line) &&
        !ALLOWED_LEGACY_CONTEXT_RE.test(line)
      ) {
        errors.push(`${toRelative(activePath)}:${index + 1} still uses unqualified story-index wording`);
      }
      if (BUILD_MAP_AUTHORITY_RE.test(line) && !ALLOWED_LEGACY_CONTEXT_RE.test(line)) {
        errors.push(`${toRelative(activePath)}:${index + 1} still teaches authored build-map authority`);
      }
      if (RETIRED_SETUP_PATH_RE.test(line) && !ALLOWED_LEGACY_CONTEXT_RE.test(line)) {
        errors.push(`${toRelative(activePath)}:${index + 1} still references retired setup.md guidance`);
      }
    });
  }

  const overdueDomains = [];
  const cadence = (((state.architecture_audits || {}).cadence || {}));
  const targetInterval = Number.isFinite(cadence.target_story_interval) ? Number(cadence.target_story_interval) : null;
  for (const [domainId, domainValue] of Object.entries(auditDomains)) {
    const storiesSinceAudit = Number.isFinite(domainValue.stories_since_audit) ? Number(domainValue.stories_since_audit) : null;
    const openFindings = Array.isArray(domainValue.open_findings) ? domainValue.open_findings : [];
    const manualPriority = String(domainValue.manual_priority || "");
    if (
      manualPriority === "high" ||
      openFindings.length > 0 ||
      (targetInterval != null && storiesSinceAudit != null && storiesSinceAudit >= targetInterval)
    ) {
      overdueDomains.push(domainId);
    }
  }
  if (overdueDomains.length > 0) {
    warnings.push(`Architecture audit domains due or carrying open findings: ${formatExampleList(overdueDomains)}`);
  }

  const uiScoutFreshness = analyzeUiScoutFreshness(uiScout);
  if (uiScoutFreshness && uiScoutFreshness.needsAttention) {
    warnings.push(`UI scout freshness due: ${uiScoutFreshness.summary}`);
  }

  return { errors, warnings };
}

function buildGraph() {
  const ideal = parseIdeal();
  const spec = parseSpec();
  const state = parseJsonCompatibleYaml(STATE_PATH);
  const stories = parseStories();
  const adrs = parseAdrs();
  const evals = parseEvalRegistry();
  const compromiseById = new Map(spec.compromises.map((entry) => [entry.id, entry]));

  for (const story of stories) {
    story.categoryRefs = uniqueSorted(story.categoryRefs, compareSpecRefs);
    story.actionability = summarizeStoryActionability(story);
  }

  const storyById = new Map(stories.map((story) => [story.id, story]));

  for (const adr of adrs) {
    const categoryRefs = new Set();
    for (const specRef of adr.specRefs) {
      const categoryId = categoryForSpecRef(specRef);
      if (categoryId) categoryRefs.add(categoryId);
    }
    for (const compromiseId of adr.compromiseIds) {
      const compromise = compromiseById.get(compromiseId);
      if (compromise) categoryRefs.add(compromise.categoryId);
    }
    for (const storyId of adr.storyIds) {
      const story = storyById.get(storyId);
      if (story) story.categoryRefs.forEach((categoryId) => categoryRefs.add(categoryId));
    }
    adr.categoryRefs = uniqueSorted(categoryRefs, compareSpecRefs);
  }

  for (const evalRecord of evals) {
    const derivedCategoryRefs = new Set();
    for (const specRef of evalRecord.specRefs) {
      const categoryId = categoryForSpecRef(specRef);
      if (categoryId) derivedCategoryRefs.add(categoryId);
    }
    for (const compromiseId of evalRecord.compromiseIds) {
      const compromise = compromiseById.get(compromiseId);
      if (compromise) derivedCategoryRefs.add(compromise.categoryId);
    }
    for (const storyId of evalRecord.storyIds) {
      const story = storyById.get(storyId);
      if (story) story.categoryRefs.forEach((categoryId) => derivedCategoryRefs.add(categoryId));
    }
    evalRecord.derivedCategoryRefs = uniqueSorted(derivedCategoryRefs, compareSpecRefs);
    evalRecord.categoryRefs = uniqueSorted(
      evalRecord.declaredCategoryRefs.length > 0 ? evalRecord.declaredCategoryRefs : evalRecord.derivedCategoryRefs,
      compareSpecRefs,
    );
    evalRecord.actionability = summarizeEvalActionability(evalRecord);
  }

  const categories = spec.categories.map((category) => ({
    id: category.id,
    title: category.title,
    sections: category.sections,
    state: (state.categories || {})[category.id] || null,
    compromiseIds: spec.compromises.filter((entry) => entry.categoryId === category.id).map((entry) => entry.id),
    storyIds: stories.filter((story) => story.categoryRefs.includes(category.id)).map((story) => story.id).sort(compareStoryIdStrings),
    adrIds: adrs.filter((adr) => adr.categoryRefs.includes(category.id)).map((adr) => adr.id).sort(),
    evalIds: evals.filter((entry) => entry.categoryRefs.includes(category.id)).map((entry) => entry.id).sort(),
  }));

  const compromises = spec.compromises.map((entry) => ({
    ...entry,
    state: (state.compromises || {})[entry.id] || null,
    storyIds: stories.filter((story) => story.compromiseIds.includes(entry.id)).map((story) => story.id).sort(compareStoryIdStrings),
    evalIds: evals.filter((evalRecord) => evalRecord.compromiseIds.includes(entry.id)).map((evalRecord) => evalRecord.id).sort(),
    actionability: selectCompromiseActionability(
      stories.filter((story) => story.compromiseIds.includes(entry.id)),
      evals.filter((evalRecord) => evalRecord.compromiseIds.includes(entry.id)),
    ),
  }));

  const validation = validateGraph(state, spec, stories, adrs, evals);

  return {
    version: 1,
    paths: {
      ideal: toRelative(IDEAL_PATH),
      spec: toRelative(SPEC_PATH),
      state: toRelative(STATE_PATH),
      graph: toRelative(GRAPH_PATH),
      stories_index: toRelative(STORIES_INDEX_PATH),
      build_map: toRelative(BUILD_MAP_PATH),
      ui_scout_index: toRelative(UI_SCOUT_INDEX_PATH),
      ui_scout_dir: toRelative(UI_SCOUT_DIR),
      stories_dir: toRelative(STORIES_DIR),
      adrs_dir: toRelative(ADRS_DIR),
      evals: toRelative(EVALS_PATH),
    },
    ideal,
    spec: {
      path: spec.path,
      categories,
      compromises,
    },
    stories: stories.sort(compareStoryRecords),
    adrs: adrs.sort((a, b) => a.id.localeCompare(b.id)),
    evals: evals.sort((a, b) => a.id.localeCompare(b.id)),
    state,
    validation,
  };
}

function serializeGraph(graph) {
  return `${JSON.stringify(graph, null, 2)}\n`;
}

function printWarnings(warnings) {
  if (warnings.length === 0) return;
  console.warn("Methodology warnings:");
  warnings.forEach((warning) => console.warn(`- ${warning}`));
}

function main() {
  const command = process.argv[2] || "build";
  if (!["build", "check", "print"].includes(command)) {
    console.error("Usage: node scripts/methodology-graph.js [build|check|print]");
    process.exit(1);
  }

  const graph = buildGraph();
  const serialized = serializeGraph(graph);
  const storiesIndex = renderStoriesIndex(graph);
  const buildMap = renderBuildMap(graph);

  if (graph.validation.errors.length > 0) {
    console.error("Methodology graph validation failed:");
    graph.validation.errors.forEach((error) => console.error(`- ${error}`));
    process.exit(1);
  }

  if (command === "print") {
    process.stdout.write(serialized);
    return;
  }

  if (command === "check") {
    const checks = [
      [GRAPH_PATH, serialized, "graph"],
      [STORIES_INDEX_PATH, storiesIndex, "stories index"],
      [BUILD_MAP_PATH, buildMap, "build map"],
    ];
    for (const [path, expected, label] of checks) {
      if (!existsSync(path)) {
        console.error(`${toRelative(path)} does not exist. Run pnpm methodology:compile first.`);
        process.exit(1);
      }
      if (readUtf8(path) !== expected) {
        console.error(`${toRelative(path)} is out of date. Run pnpm methodology:compile. (${label})`);
        process.exit(1);
      }
    }
    printWarnings(graph.validation.warnings);
    console.log(`Methodology outputs are current: ${toRelative(GRAPH_PATH)}`);
    return;
  }

  mkdirSync(join(ROOT, "docs/methodology"), { recursive: true });
  writeFileSync(GRAPH_PATH, serialized);
  writeFileSync(STORIES_INDEX_PATH, storiesIndex);
  writeFileSync(BUILD_MAP_PATH, buildMap);
  console.log(`Wrote ${toRelative(GRAPH_PATH)}`);
  console.log(`Wrote ${toRelative(STORIES_INDEX_PATH)}`);
  console.log(`Wrote ${toRelative(BUILD_MAP_PATH)}`);
  printWarnings(graph.validation.warnings);
}

main();
