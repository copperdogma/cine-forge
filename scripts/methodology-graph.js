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
const STORIES_DIR = join(ROOT, "docs/stories");
const ADRS_DIR = join(ROOT, "docs/decisions");

const STORY_ID_RE = "[0-9]{3}[a-z]?";
const STORY_FILE_RE = new RegExp(`^story-(${STORY_ID_RE})-.+\\.md$`, "i");
const STORY_HEADING_RE = new RegExp(`^#\\s+Story\\s+(${STORY_ID_RE})\\s*(?:[:\\u2014-])\\s+(.+)$`, "i");
const STORY_ID_INLINE_RE = new RegExp(`\\b(?:Story\\s+|story[- ]?)(${STORY_ID_RE})\\b`, "gi");
const SPEC_REF_RE = /\bspec:\d+(?:\.\d+)*\b/g;
const ADR_ID_RE = /\bADR-\d{3}\b/g;
const COMPROMISE_ID_RE = /\b(?:C|B)\d+\b/g;
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
const ACTIVE_SURFACE_PATHS = [
  join(ROOT, "AGENTS.md"),
  join(ROOT, "docs/methodology-ideal-spec-compromise.md"),
  join(ROOT, "docs/setup-checklist.md"),
  join(ROOT, "docs/runbooks/setup-methodology.md"),
  join(ROOT, "docs/runbooks/triage.md"),
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
  join(ROOT, ".agents/skills/triage-architecture/SKILL.md"),
];
const MANUAL_STORIES_RE =
  /update.*docs\/stories\.md|append.*docs\/stories\.md|edit.*docs\/stories\.md|hand-authored story index|manual story index/i;
const BUILD_MAP_AUTHORITY_RE =
  /central planning\s*\/\s*triage dashboard|build-map-first|build map first|hand-authored build-map|build-map-centered|docs\/build-map\.md.*central/i;
const ALLOWED_LEGACY_CONTEXT_RE =
  /generated|state\.yaml|graph\.json|legacy|migration|historical|archive|archived|not authoritative|generated dashboard/i;

function readUtf8(path) {
  return readFileSync(path, "utf8");
}

function toRelative(path) {
  return relative(ROOT, path).replaceAll("\\", "/");
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

function extractMatches(text, pattern) {
  return uniqueSorted(text.match(pattern) || []);
}

function extractStoryIds(text) {
  const ids = [];
  for (const match of text.matchAll(STORY_ID_INLINE_RE)) {
    ids.push(match[1]);
  }
  return uniqueSorted(ids, compareStoryIdStrings);
}

function parseJsonCompatibleYaml(path) {
  try {
    return JSON.parse(readUtf8(path));
  } catch (error) {
    throw new Error(`${toRelative(path)} must currently be JSON-compatible YAML: ${error.message}`);
  }
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

function deriveEvalCompromiseIds(id, blockText) {
  const ids = new Set(extractMatches(blockText, COMPROMISE_ID_RE));
  const prefix = id.match(/^compromise-(c\d+|b\d+)/i);
  if (prefix) ids.add(prefix[1].toUpperCase());
  return Array.from(ids).sort();
}

function parseEvalRegistry() {
  const lines = readUtf8(EVALS_PATH).split(/\r?\n/);
  const records = [];
  let current = null;
  let block = [];

  const flush = () => {
    if (!current || !current.id) return;
    const blockText = block.join("\n");
    const specRefs = extractMatches(blockText, SPEC_REF_RE);
    records.push({
      id: current.id,
      name: current.name || current.id,
      type: current.type || "unknown",
      command: current.command || "",
      path: toRelative(EVALS_PATH),
      specRefs,
      storyIds: extractStoryIds(blockText),
      compromiseIds: deriveEvalCompromiseIds(current.id, blockText),
      categoryRefs: [],
    });
  };

  for (const line of lines) {
    const idMatch = line.match(/^ {2}- id:\s+(.+)$/);
    if (idMatch) {
      flush();
      current = { id: stripQuotes(idMatch[1]) };
      block = [line];
      continue;
    }
    if (current) {
      block.push(line);
      const fieldMatch = line.match(/^ {4}(name|type|command):\s+(.+)$/);
      if (fieldMatch) current[fieldMatch[1]] = stripQuotes(fieldMatch[2]);
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

function renderCurrentExecutionMap(currentExecutionMap, stories) {
  if (!currentExecutionMap || typeof currentExecutionMap !== "object") return null;

  const lines = [];
  const summary = typeof currentExecutionMap.summary === "string" ? currentExecutionMap.summary.trim() : "";
  const lanes = Array.isArray(currentExecutionMap.lanes) ? currentExecutionMap.lanes : [];
  const storyById = new Map(stories.map((story) => [story.id, story]));

  if (summary) lines.push(summary, "");

  for (const lane of lanes) {
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

  for (const section of customSections) {
    const markdown = markdownFromSection(section);
    const title = String(section.title || "").trim();
    if (!title || !markdown) continue;
    lines.push(`## ${title}`, "", markdown, "");
  }

  if (activeFocus.length > 0 || sequencingBias.length > 0 || campaigns.length > 0) {
    lines.push("## Active Focus", "");
    if (activeFocus.length > 0) lines.push(`- Active categories: ${activeFocus.map((entry) => `\`${entry}\``).join(", ")}`);
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

  for (const categoryId of Object.keys(state.categories || {})) {
    if (!categoryIds.has(categoryId)) errors.push(`state.categories.${categoryId} does not match any spec category`);
  }
  for (const compromiseId of Object.keys(state.compromises || {})) {
    if (!compromiseIds.has(compromiseId)) errors.push(`state.compromises.${compromiseId} does not match any spec compromise`);
  }

  const customSections = Array.isArray((state.stories_index || {}).sections) ? state.stories_index.sections : [];
  customSections.forEach((section, index) => {
    if (String(section.id || "") === "current-execution-map") {
      errors.push(`state.stories_index.sections[${index}] uses deprecated current-execution-map prose; use state.stories_index.current_execution_map instead`);
    }
  });

  const currentExecutionMap = (state.stories_index || {}).current_execution_map || {};
  const currentExecutionMapLanes = Array.isArray(currentExecutionMap.lanes) ? currentExecutionMap.lanes : [];
  currentExecutionMapLanes.forEach((lane, index) => {
    const laneLabel = String(lane.id || lane.title || index);
    const statuses = Array.isArray(lane.statuses) ? lane.statuses.map(String) : [];
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

  const sequencingBiasEntries = Array.isArray((state.roadmap || {}).sequencing_bias) ? (state.roadmap || {}).sequencing_bias : [];
  sequencingBiasEntries.forEach((entry, index) => {
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

  for (const [domainId, domainValue] of Object.entries(auditDomains)) {
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
      if (BUILD_MAP_AUTHORITY_RE.test(line) && !ALLOWED_LEGACY_CONTEXT_RE.test(line)) {
        errors.push(`${toRelative(activePath)}:${index + 1} still teaches authored build-map authority`);
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
    const categoryRefs = new Set();
    for (const specRef of evalRecord.specRefs) {
      const categoryId = categoryForSpecRef(specRef);
      if (categoryId) categoryRefs.add(categoryId);
    }
    for (const compromiseId of evalRecord.compromiseIds) {
      const compromise = compromiseById.get(compromiseId);
      if (compromise) categoryRefs.add(compromise.categoryId);
    }
    for (const storyId of evalRecord.storyIds) {
      const story = storyById.get(storyId);
      if (story) story.categoryRefs.forEach((categoryId) => categoryRefs.add(categoryId));
    }
    evalRecord.categoryRefs = uniqueSorted(categoryRefs, compareSpecRefs);
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
    evalIds: evals.filter((evalRecord) => evalRecord.compromiseIds.includes(entry.id)).map((evalRecord) => evalRecord.id).sort(),
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
