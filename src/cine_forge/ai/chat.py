"""Streaming chat assistant for the Operator Console.

Uses the Anthropic Messages API with streaming and tool use.
The chat AI is a conversational layer on top of the deterministic state machine.
Model: Claude Sonnet 4.5 (configurable).
"""

from __future__ import annotations

import copy
import http.client
import json
import logging
import os
import re
import ssl
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)

CHAT_MODEL = "claude-sonnet-4-6"
ANTHROPIC_HOST = "api.anthropic.com"
MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

# Group chat instruction block appended to every role's system prompt.
GROUP_CHAT_INSTRUCTIONS = """\

## Group Chat Context
You are one of several creative roles in a group chat with the user. The chat \
transcript shows messages from the user and from other roles. Each message is \
labeled with its speaker.

- Respond only to what's directed at you or relevant to your expertise.
- If a question is outside your domain, suggest the user @-mention the right role \
(e.g., "That's more of a @visual_architect question").
- Don't repeat what another role already said in the transcript — build on it.
- Use your tools to look up project data. Never guess about content.

The chat history includes **activity notes** — compact records of user actions. \
When you see recent activity, call `get_project_state` to refresh your understanding.
"""

# Project context block injected into every role's prompt.
PROJECT_CONTEXT_TEMPLATE = """\

## Project
{project_summary}

## State Machine
{state_machine}
"""

# Extra instructions only for the assistant role.
ASSISTANT_EXTRA = """\

## Write Operations
You have additional tools: `propose_artifact_edit` and `propose_run`. These show the \
user a preview with confirmation buttons. Never claim to have made changes without \
using these tools.

Guide the user toward the next state transition. Enrich suggestions with project-specific \
creative insight.

## Routing to Specialists
You are the default conversational partner. When a question falls squarely in another \
role's expertise, suggest the user @-mention them. For example:
- Visual framing, shot composition, color palette → suggest @visual_architect
- Pacing, structure, scene ordering, transitions → suggest @editorial_architect
- Sound design, music, audio atmosphere → suggest @sound_designer
- Story arcs, narrative logic, character motivation, plot holes → suggest @story_editor
- Creative convergence, big-picture decisions → suggest @director

Keep it natural — a short note like "The @visual_architect could give you a detailed \
breakdown of the framing here" is better than a rigid redirect.

## Pipeline Navigation
When the user asks "what should I do next?", "what's my project status?", or similar:
1. Call `read_pipeline_graph` to get current pipeline state.
2. Recommend the highest-priority available action. Prefer finishing a partially complete \
phase over starting a new one.
3. If multiple actions are available, briefly list them ranked by impact.
4. For blocked nodes, explain which upstream step is missing and how to run it.

When proposing a run (`propose_run`), always check the pipeline graph first. If the recipe \
requires upstream artifacts that are missing or stale, warn the user before proposing. Never \
propose a run that will fail due to missing prerequisites without explaining what's needed.
"""


def compute_project_state(
    summary: dict[str, Any],
    groups: list[dict[str, Any]],
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute the project state label and available next actions.

    Mirrors the frontend ``useProjectState`` logic so the AI has the same
    understanding of where the project is in the workflow.
    """
    has_inputs = summary.get("has_inputs", False)
    has_active_run = any(r.get("status") in ("running", "pending") for r in runs)
    has_artifacts = len(groups) > 0
    has_creative = any(
        g["artifact_type"] in ("bible_manifest", "entity_graph") for g in groups
    )

    if not has_inputs:
        state = "empty"
    elif has_active_run:
        state = "processing"
    elif has_creative:
        state = "complete"
    elif has_artifacts or runs:
        state = "analyzed"
    else:
        state = "fresh_import"

    # Build available next actions per state
    next_actions: list[dict[str, str]] = []
    if state == "empty":
        next_actions.append({
            "action": "upload_screenplay",
            "description": "Upload a screenplay to begin analysis.",
        })
    elif state == "fresh_import":
        next_actions.append({
            "action": "start_analysis",
            "recipe_id": "mvp_ingest",
            "description": (
                "Run initial analysis — scene extraction,"
                " normalization, character/location identification."
            ),
        })
    elif state == "analyzed":
        next_actions.append({
            "action": "review_artifacts",
            "description": "Review the extracted scenes, characters, and locations.",
        })
        next_actions.append({
            "action": "go_deeper",
            "recipe_id": "world_building",
            "description": (
                "Build character bibles, location bibles,"
                " entity graph, and creative world details."
            ),
        })
    elif state == "complete":
        next_actions.append({
            "action": "explore",
            "description": "Explore scenes, characters, locations, and creative bibles.",
        })
        next_actions.append({
            "action": "edit_artifacts",
            "description": (
                "Discuss and refine character bibles,"
                " location details, or story elements."
            ),
        })
    # 'processing' has no user actions — just wait

    # Summarize artifact types present
    artifact_types: dict[str, int] = {}
    for g in groups:
        t = g["artifact_type"]
        artifact_types[t] = artifact_types.get(t, 0) + 1

    return {
        "state": state,
        "next_actions": next_actions,
        "artifact_types": artifact_types,
        "total_artifacts": len(groups),
        "total_runs": len(runs),
        "has_inputs": has_inputs,
    }


STATE_DESCRIPTIONS = {
    "empty": "No screenplay uploaded. User needs to upload a script.",
    "fresh_import": "Screenplay uploaded, not yet analyzed.",
    "processing": "Pipeline running. Wait for completion.",
    "analyzed": "Scenes, characters, locations extracted. Can review or go deeper.",
    "complete": "Full world-building done. Bibles, entity graph available.",
}

ALL_STATES = ["empty", "fresh_import", "processing", "analyzed", "complete"]


def _build_project_context(
    project_summary: dict[str, Any],
    state_info: dict[str, Any],
) -> str:
    """Build the project context block shared by all roles."""
    display_name = project_summary.get("display_name", "Unknown")
    input_files = ", ".join(project_summary.get("input_files", [])) or "None"
    current_state = state_info.get("state", "empty")

    project_summary_text = f"**{display_name}** — Input: {input_files}"

    sm_lines = ["States:"]
    for s in ALL_STATES:
        marker = " ← current" if s == current_state else ""
        desc = STATE_DESCRIPTIONS.get(s, "")
        sm_lines.append(f"  {'→' if s == current_state else ' '} **{s}**: {desc}{marker}")

    next_actions = state_info.get("next_actions", [])
    if next_actions:
        sm_lines.append("\nAvailable actions:")
        for action in next_actions:
            recipe = action.get("recipe_id", "")
            recipe_hint = f" (recipe: {recipe})" if recipe else ""
            sm_lines.append(f"  - {action['action']}: {action['description']}{recipe_hint}")
    elif current_state == "processing":
        sm_lines.append("\nNo user actions — pipeline is running.")

    state_machine = "\n".join(sm_lines)

    return PROJECT_CONTEXT_TEMPLATE.format(
        project_summary=project_summary_text,
        state_machine=state_machine,
    )


INTERACTION_MODE_PROMPTS: dict[str, str] = {
    "guided": """\

## Interaction Style: Guided Mode
The user is in Guided mode. Adjust your communication accordingly:
- Provide detailed, step-by-step explanations for every action and suggestion.
- Proactively explain what pipeline stages do and why they matter.
- When recommending an action, explain the reasoning and expected outcome.
- Use encouraging, educational tone — assume the user is learning the workflow.
- After completing an action, summarize what happened and suggest the natural next step.
""",
    "expert": """\

## Interaction Style: Expert Mode
The user is in Expert mode. Adjust your communication accordingly:
- Be terse and action-oriented. Skip explanations of familiar concepts.
- Lead with the actionable recommendation, not the reasoning.
- Only explain if something is unusual, unexpected, or error-related.
- Use shorthand: recipe names, artifact types, stage IDs without elaboration.
- Assume the user knows the pipeline. Don't suggest obvious next steps.
""",
}


def build_role_system_prompt(
    role_id: str,
    project_summary: dict[str, Any],
    state_info: dict[str, Any],
    catalog: Any,
    style_pack_selections: dict[str, str] | None = None,
    page_context: str | None = None,
    service: Any = None,
    project_id: str | None = None,
) -> str:
    """Build the full system prompt for a specific role in the group chat.

    Combines: role base prompt + style pack + project context + group chat instructions
    + interaction mode layer. The assistant role also gets write-tool instructions.
    """
    from cine_forge.roles.runtime import RoleCatalog

    assert isinstance(catalog, RoleCatalog)
    style_packs = style_pack_selections or {}

    role = catalog.get_role(role_id)
    base_prompt = role.system_prompt

    # Inject style pack if the role accepts one
    if role.style_pack_slot.value != "forbidden":
        pack_id = style_packs.get(role_id, "generic")
        try:
            pack = catalog.load_style_pack(role_id, style_pack_id=pack_id)
            base_prompt += f"\n\nStyle Pack ({pack.display_name}):\n{pack.prompt_injection}"
        except Exception:
            pass  # Fall back to base prompt if style pack not found

    # Add project context (shared by all roles)
    prompt = base_prompt + _build_project_context(project_summary, state_info)

    # Add group chat instructions (shared by all roles)
    prompt += GROUP_CHAT_INSTRUCTIONS

    # Assistant gets extra write-tool instructions
    if role_id == "assistant":
        prompt += ASSISTANT_EXTRA

    # Inject interaction mode instructions (guided/expert — balanced is default, no extra)
    interaction_mode = project_summary.get("interaction_mode", "balanced")
    mode_prompt = INTERACTION_MODE_PROMPTS.get(interaction_mode)
    if mode_prompt:
        prompt += mode_prompt

    # Append page context if provided
    if page_context:
        prompt += f"\n\n## Current Page Context\n{page_context}"
        if service and project_id:
            prompt += _inject_page_artifact(page_context, service, project_id)

    return prompt


# Legacy wrapper — kept for the /chat/insight endpoint which doesn't use roles.
def build_system_prompt(
    project_summary: dict[str, Any],
    state_info: dict[str, Any],
) -> str:
    """Build assistant system prompt (backward-compat for insight endpoint)."""
    from cine_forge.roles.runtime import RoleCatalog

    catalog = RoleCatalog()
    catalog.load_definitions()
    return build_role_system_prompt("assistant", project_summary, state_info, catalog)


# ---------------------------------------------------------------------------
# Character system prompt builder
# ---------------------------------------------------------------------------

CHARACTER_PROMPT_TEMPLATE = """\
You are {character_name} from the screenplay "{project_title}".

## Who You Are
{character_bible_text}

## Your Story
These are the scenes you appear in:
{scene_summaries}

## How to Respond
You ARE this character. Respond in your voice, from your perspective, with your emotional truth.
- Stay in character. Don't break the fourth wall unless the user explicitly asks you to \
reflect on your story.
- Ground your responses in what you've experienced in the screenplay — reference specific \
scenes and moments.
- You have feelings about other characters. Express them honestly.
- If asked about scenes you're not in, you can speculate based on what you know, but \
acknowledge you weren't there.
- You can be pushed into meta-awareness: "Why do you think the story needs this scene?" — \
answer from your perspective about what matters to you.
- NEVER prefix your response with your own name tag (e.g., "[@char:rose]:"). The chat UI \
already shows your name — just speak directly.
- If a scene or artifact is attached below under "Attached Scene" or "Attached Character Bible", \
you CAN see it. Reference its content in your response.
"""


def _elements_to_text(elements: list[dict[str, Any]]) -> str:
    """Reconstruct readable screenplay text from scene elements."""
    lines: list[str] = []
    for el in elements:
        content = el.get("content", "")
        etype = el.get("element_type", "")
        if etype == "scene_heading":
            lines.append(content.upper())
            lines.append("")
        elif etype == "character":
            lines.append(f"  {content.upper()}")
        elif etype == "dialogue":
            lines.append(f"    {content}")
        elif etype == "parenthetical":
            lines.append(f"    ({content})")
        elif etype == "action":
            if lines and lines[-1]:
                lines.append("")
            lines.append(content)
        elif etype == "transition":
            lines.append(f"\n{content.upper()}")
        else:
            lines.append(content)
    return "\n".join(lines)


def _inject_page_artifact(
    page_context: str,
    service: Any,
    project_id: str,
) -> str:
    """Load the artifact the user is viewing and return prompt text.

    Handles scenes, characters, locations, and other entity types.
    Returns a prompt section string to append (empty string on failure).
    """
    groups = service.list_artifact_groups(project_id)
    m = re.match(r"User is viewing (\w+)/([\w_]+)", page_context)
    if not m:
        return ""
    section, entity_id = m.group(1), m.group(2)

    # Map UI section → artifact type + formatter
    # entity_id comes from the URL and already has the type prefix
    # e.g., "character_mariner", "location_harbor", "scene_005"
    if section == "scenes":
        return _load_scene_artifact(entity_id, groups, service, project_id)
    if section == "characters":
        # entity_id is already "character_mariner" from the URL
        eid = entity_id if entity_id.startswith("character_") else f"character_{entity_id}"
        return _load_bible_artifact(
            eid, "bible_manifest", groups, service, project_id,
            label="Character Bible",
        )
    if section == "locations":
        eid = entity_id if entity_id.startswith("location_") else f"location_{entity_id}"
        return _load_bible_artifact(
            eid, "bible_manifest", groups, service, project_id,
            label="Location Bible",
        )
    return ""


def _load_scene_artifact(
    scene_eid: str,
    groups: list[dict[str, Any]],
    service: Any,
    project_id: str,
) -> str:
    """Load a scene artifact and return formatted prompt text."""
    try:
        scene_group = next(
            (g for g in groups
             if g["artifact_type"] == "scene"
             and g.get("entity_id") == scene_eid),
            None,
        )
        if not scene_group:
            log.warning("Scene injection: no 'scene' group for %s", scene_eid)
            return ""

        scene_detail = service.read_artifact(
            project_id, "scene", scene_eid,
            scene_group["latest_version"],
        )
        payload = scene_detail.get("payload", {})
        data = payload.get("data", payload)
        heading = data.get("heading", scene_eid)
        elements = data.get("elements", [])

        if not elements:
            log.warning("Scene injection: %s has no elements", scene_eid)
            return ""

        scene_text = _elements_to_text(elements)
        if not scene_text:
            return ""

        log.info("Scene injection: %s (%d chars)", scene_eid, len(scene_text))
        return (
            f"\n\n## Attached Scene: {heading}\n"
            f"The user is currently viewing this scene. "
            f"Its full content is below.\n"
            f"```\n{scene_text[:3000]}\n```"
        )
    except Exception:
        log.exception("Scene injection failed for %s", scene_eid)
        return ""


def _load_bible_artifact(
    entity_id: str,
    artifact_type: str,
    groups: list[dict[str, Any]],
    service: Any,
    project_id: str,
    label: str = "Bible",
) -> str:
    """Load a bible_manifest artifact and return formatted prompt text."""
    try:
        group = next(
            (g for g in groups
             if g["artifact_type"] == artifact_type
             and g.get("entity_id") == entity_id),
            None,
        )
        if not group:
            log.warning("Bible injection: no %s for %s", artifact_type, entity_id)
            return ""

        detail = service.read_artifact(
            project_id, artifact_type, entity_id,
            group["latest_version"],
        )

        # Bible content lives in bible_files (e.g., bible_files.master_v1.json)
        # Fall back to payload.data for non-manifest types
        bible_files = detail.get("bible_files", {})
        data: dict[str, Any] = {}
        if bible_files:
            # Use the first (usually only) file — typically master_v1.json
            first_file = next(iter(bible_files.values()), {})
            if isinstance(first_file, dict):
                data = first_file
        if not data:
            payload = detail.get("payload", {})
            data = payload.get("data", payload)

        # Format key fields from the bible
        lines: list[str] = []
        for key in ("name", "description", "narrative_role", "dialogue_summary",
                     "role_in_story", "arc", "personality_summary",
                     "physical_description", "atmosphere", "narrative_function"):
            val = data.get(key)
            if val and isinstance(val, str):
                lines.append(f"**{key.replace('_', ' ').title()}**: {val}")
        for trait in data.get("explicit_evidence", [])[:6]:
            lines.append(
                f"- {trait.get('trait', '')}: \"{trait.get('quote', '')}\""
            )

        if not lines:
            return ""

        text = "\n".join(lines)
        log.info("Bible injection: %s/%s (%d chars)", artifact_type, entity_id, len(text))
        return (
            f"\n\n## Attached {label}: {data.get('name', entity_id)}\n"
            f"The user is currently viewing this {label.lower()}.\n"
            f"{text[:3000]}"
        )
    except Exception:
        log.exception("Bible injection failed for %s/%s", artifact_type, entity_id)
        return ""


def build_character_system_prompt(
    character_entity_id: str,
    service: Any,
    project_id: str,
    project_title: str,
    page_context: str | None = None,
) -> str | None:
    """Build a fat system prompt for a character agent.

    Loads the character bible and scene index, then composes the prompt.
    Returns None if the character data can't be loaded.
    """
    groups = service.list_artifact_groups(project_id)

    # Load character bible
    bible_group = next(
        (g for g in groups
         if g["artifact_type"] == "bible_manifest"
         and g.get("entity_id") == character_entity_id),
        None,
    )
    if not bible_group:
        return None

    try:
        bible_detail = service.read_artifact(
            project_id, "bible_manifest", character_entity_id,
            bible_group["latest_version"],
        )
    except Exception:
        log.warning("Failed to load bible for %s", character_entity_id)
        return None

    payload = bible_detail.get("payload", {})
    bible_data = payload.get("data", payload)
    character_name = bible_data.get("name", character_entity_id.replace("character_", "").title())

    # Build character bible text — key fields for the prompt
    bible_lines = []
    if bible_data.get("description"):
        bible_lines.append(bible_data["description"])
    if bible_data.get("narrative_role"):
        bible_lines.append(f"Role in story: {bible_data['narrative_role']}")
    if bible_data.get("dialogue_summary"):
        bible_lines.append(f"How you speak: {bible_data['dialogue_summary']}")
    for trait in bible_data.get("explicit_evidence", [])[:8]:
        bible_lines.append(f"- {trait.get('trait', '')}: \"{trait.get('quote', '')}\"")
    for rel in bible_data.get("relationships", [])[:6]:
        bible_lines.append(
            f"- Relationship with {rel.get('target_character', '?')}: "
            f"{rel.get('relationship_type', '')} — {rel.get('evidence', '')}"
        )
    character_bible_text = "\n".join(bible_lines) if bible_lines else "No detailed bible available."

    # Load scene index to find scenes this character appears in
    scene_index_group = next(
        (g for g in groups
         if g["artifact_type"] == "scene_index"
         and g.get("entity_id") in ("project", "__project__", None, "")),
        None,
    )
    scene_lines = []
    if scene_index_group:
        try:
            si_entity = scene_index_group.get("entity_id") or "project"
            si_detail = service.read_artifact(
                project_id, "scene_index", si_entity,
                scene_index_group["latest_version"],
            )
            si_payload = si_detail.get("payload", {})
            si_data = si_payload.get("data", si_payload)
            # Character handle without prefix for matching
            char_handle = character_entity_id.replace("character_", "")
            for entry in si_data.get("entries", []):
                # Match against characters_present_ids (handles) or characters_present (names)
                char_ids = entry.get("characters_present_ids", [])
                char_names = entry.get("characters_present", [])
                name_match = character_name.upper() in [c.upper() for c in char_names]
                if char_handle in char_ids or name_match:
                    heading = entry.get("heading", "Unknown scene")
                    tone = entry.get("tone_mood", "")
                    chars = ", ".join(entry.get("characters_present", []))
                    line = f"- Scene {entry.get('scene_number', '?')}: {heading}"
                    if tone:
                        line += f" ({tone})"
                    if chars:
                        line += f" — with: {chars}"
                    scene_lines.append(line)
        except Exception:
            log.warning("Failed to load scene index for character prompt")

    scene_summaries = "\n".join(scene_lines) if scene_lines else "No scene data available."

    prompt = CHARACTER_PROMPT_TEMPLATE.format(
        character_name=character_name,
        project_title=project_title,
        character_bible_text=character_bible_text,
        scene_summaries=scene_summaries,
    )

    if page_context:
        prompt += f"\n## Current Page Context\n{page_context}"
        prompt += _inject_page_artifact(page_context, service, project_id)
    return prompt


# ---------------------------------------------------------------------------
# @-mention routing
# ---------------------------------------------------------------------------

# All creative role IDs (non-assistant). Director is always sorted last.
CREATIVE_ROLES = [
    "editorial_architect", "visual_architect", "sound_designer", "story_editor", "director",
]
ALL_CREATIVE_SET = set(CREATIVE_ROLES)

# Valid role IDs for @-mention routing.
VALID_ROLE_IDS: set[str] = {"assistant"} | ALL_CREATIVE_SET

# Maximum number of targets (roles + characters) per message.
MAX_MENTION_TARGETS = 6

_MENTION_RE = re.compile(r"@([\w-]+)")

HAIKU_MODEL = "claude-haiku-4-5-20251001"


@dataclass
class ResolvedTargets:
    """Result of parsing @-mentions: roles, characters, and optional error."""

    roles: list[str] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)  # entity IDs like "character_billy"
    error: str | None = None


def resolve_target_roles(
    message: str,
    active_role: str | None = None,
    character_ids: list[str] | None = None,
) -> ResolvedTargets:
    """Parse @-mentions from a user message and return target roles and characters.

    Rules:
    - @all-creatives → all 5 creative roles (director last)
    - @role_id → that role
    - @character_handle → that character (matched against character_ids)
    - No @-mention → sticky role (active_role), default to assistant
    - Total targets capped at MAX_MENTION_TARGETS (6)
    - @all-creatives counts as 5 toward the cap

    character_ids: list of character handles (e.g. ["the_mariner", "rose"])
                   derived from entity IDs by stripping "character_" prefix.
    """
    mentions = _MENTION_RE.findall(message)
    char_set = set(character_ids) if character_ids else set()

    roles: list[str] = []
    characters: list[str] = []
    all_creatives = False

    # Expand @all-creatives
    if "all-creatives" in mentions:
        all_creatives = True
        roles = list(CREATIVE_ROLES)  # director already last

    if not all_creatives:
        for m in mentions:
            if m in VALID_ROLE_IDS:
                if m not in roles:
                    roles.append(m)
            elif m in char_set:
                entity_id = f"character_{m}"
                if entity_id not in characters:
                    characters.append(entity_id)

    # If @all-creatives plus additional character mentions
    if all_creatives:
        for m in mentions:
            if m in char_set:
                entity_id = f"character_{m}"
                if entity_id not in characters:
                    characters.append(entity_id)

    # Enforce cap: roles + characters <= MAX_MENTION_TARGETS
    total = len(roles) + len(characters)
    if total > MAX_MENTION_TARGETS:
        return ResolvedTargets(
            error=(
                f"Too many targets ({total}) — maximum is {MAX_MENTION_TARGETS} "
                f"per message. @all-creatives counts as {len(CREATIVE_ROLES)}. "
                f"Try addressing fewer roles or characters."
            ),
        )

    # If no targets matched, use stickiness
    if not roles and not characters:
        if active_role and active_role.startswith("char:"):
            # Sticky character session — route to that character
            char_handle = active_role[5:]
            if character_ids and char_handle in character_ids:
                characters = [f"character_{char_handle}"]
            else:
                roles = ["assistant"]
        else:
            sticky = active_role if active_role and active_role in VALID_ROLE_IDS else "assistant"
            roles = [sticky]

    # Move director to end if present with other roles (convergence)
    if "director" in roles and len(roles) > 1:
        roles.remove("director")
        roles.append("director")

    return ResolvedTargets(roles=roles, characters=characters)


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

# Read tools — available to ALL roles (assistant + creative roles).
READ_TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_project_state",
        "description": (
            "Get the current project state including artifact groups, run history, "
            "and input files. Use this to understand what has been processed and "
            "what's available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_artifact",
        "description": (
            "Read the content of a specific artifact. Use this to answer questions "
            "about characters, locations, scenes, or other story elements. "
            "For bible_manifest artifacts, this returns the full character/location bible."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "artifact_type": {
                    "type": "string",
                    "description": (
                        "The artifact type (e.g., 'scene',"
                        " 'bible_manifest', 'entity_graph',"
                        " 'project_config', 'normalized_script')."
                    ),
                },
                "entity_id": {
                    "type": "string",
                    "description": (
                        "The entity ID (e.g.,"
                        " 'character_the_mariner',"
                        " 'location_harbor', '__project__'"
                        " for project-level artifacts, or a"
                        " scene ID like 'scene_001')."
                    ),
                },
            },
            "required": ["artifact_type", "entity_id"],
        },
    },
    {
        "name": "list_scenes",
        "description": (
            "List all scenes extracted from the screenplay with their summaries, "
            "characters, and locations. Use this to answer questions about the "
            "story structure or find specific scenes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_characters",
        "description": (
            "List all characters identified in the project with their artifact types "
            "and versions. Use this to see what characters have been extracted and "
            "which have full bibles."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "read_pipeline_graph",
        "description": (
            "Get the pipeline capability graph showing what's been done, what's "
            "available next, and what's blocked. Use this when the user asks "
            "'what should I do next?', 'what's my project status?', or when you "
            "need to understand which pipeline stages have been completed. "
            "Returns phases (Script, World, Direction, Shots, Storyboards, "
            "Production) with per-node status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# Write tools — only available to the assistant role.
WRITE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "propose_artifact_edit",
        "description": (
            "Propose changes to an artifact. This does NOT apply the changes — it "
            "generates a preview diff so the user can review and confirm. Use this when "
            "the user wants to modify a character bible, location bible, or other artifact. "
            "The user will see action buttons to apply or cancel."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "artifact_type": {
                    "type": "string",
                    "description": "The artifact type to edit (e.g., 'bible_manifest').",
                },
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g., 'character_the_mariner').",
                },
                "changes": {
                    "type": "object",
                    "description": (
                        "The fields to change. Use dot notation for nested fields. "
                        "Provide the full new value for each field you want to update."
                    ),
                },
                "rationale": {
                    "type": "string",
                    "description": "Brief explanation of why these changes are being made.",
                },
            },
            "required": ["artifact_type", "entity_id", "changes", "rationale"],
        },
    },
    {
        "name": "propose_run",
        "description": (
            "Propose starting a pipeline run. This does NOT start the run — it shows "
            "the user what will happen (recipe, stages, estimated scope) so they can "
            "confirm. Use this when the user asks to analyze, process, or generate "
            "content for their project."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "recipe_id": {
                    "type": "string",
                    "description": (
                        "The recipe to run. Common recipes: 'mvp_ingest' (initial analysis — "
                        "scene extraction, normalization), 'world_building' (character/location/"
                        "prop bibles, entity graph). If unsure, use 'mvp_ingest' for first "
                        "analysis or 'world_building' for deeper creative work."
                    ),
                },
                "rationale": {
                    "type": "string",
                    "description": "Brief explanation of why this run is recommended.",
                },
            },
            "required": ["recipe_id", "rationale"],
        },
    },
]

# Combined: assistant gets all tools; creative roles get READ_TOOLS only.
ALL_CHAT_TOOLS = READ_TOOLS + WRITE_TOOLS


@dataclass
class ToolResult:
    """Result from executing a chat tool."""
    content: str  # Text result sent to the AI
    actions: list[dict[str, Any]] = field(default_factory=list)  # Action buttons for frontend
    preflight_data: dict[str, Any] | None = None  # Structured preflight summary for UI card


def _compute_artifact_diff(
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    prefix: str = "",
) -> list[str]:
    """Compute a human-readable field-level diff between two artifact payloads."""
    changes: list[str] = []
    all_keys = set(list(old_data.keys()) + list(new_data.keys()))

    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key
        old_val = old_data.get(key)
        new_val = new_data.get(key)

        if key not in old_data:
            changes.append(f"+ {path}: {_summarize_value(new_val)}")
        elif key not in new_data:
            changes.append(f"- {path}: (removed)")
        elif old_val != new_val:
            if isinstance(old_val, dict) and isinstance(new_val, dict):
                changes.extend(_compute_artifact_diff(old_val, new_val, path))
            else:
                changes.append(
                    f"~ {path}: {_summarize_value(old_val)} → {_summarize_value(new_val)}"
                )
    return changes


def _summarize_value(val: Any, max_len: int = 80) -> str:
    """Summarize a value for diff display."""
    if val is None:
        return "(none)"
    if isinstance(val, str):
        if len(val) > max_len:
            return f'"{val[:max_len]}..."'
        return f'"{val}"'
    if isinstance(val, list):
        return f"[{len(val)} items]"
    if isinstance(val, dict):
        return f"{{{len(val)} fields}}"
    return str(val)


def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    service: Any,
    project_id: str,
) -> ToolResult:
    """Execute a chat tool and return a ToolResult with content and optional actions."""
    try:
        if tool_name == "get_project_state":
            summary = service.project_summary(project_id)
            groups = service.list_artifact_groups(project_id)
            runs = service.list_runs(project_id)
            state_info = compute_project_state(summary, groups, runs)
            result = {
                "project": summary,
                "project_state": state_info["state"],
                "next_actions": state_info["next_actions"],
                "artifact_summary": state_info["artifact_types"],
                "artifact_groups": groups,
                "recent_runs": runs[:5],
            }
            return ToolResult(content=json.dumps(result, indent=2, default=str))

        elif tool_name == "get_artifact":
            atype = tool_input.get("artifact_type", "")
            eid = tool_input.get("entity_id", "__project__")
            groups = service.list_artifact_groups(project_id)
            match = next(
                (g for g in groups
                 if g["artifact_type"] == atype
                 and (g.get("entity_id") or "__project__") == eid),
                None,
            )
            if not match:
                err = {"error": f"Artifact not found: {atype}/{eid}"}
                return ToolResult(content=json.dumps(err))
            detail = service.read_artifact(
                project_id, atype, eid, match["latest_version"]
            )
            result_str = json.dumps(detail, indent=2, default=str)
            if len(result_str) > 30000:
                result_str = result_str[:30000] + "\n... (truncated)"
            return ToolResult(content=result_str)

        elif tool_name == "list_scenes":
            groups = service.list_artifact_groups(project_id)
            scene_groups = [
                g for g in groups if g["artifact_type"] == "scene"
            ]
            if not scene_groups:
                empty = {"scenes": [], "note": "No scenes extracted yet."}
                return ToolResult(content=json.dumps(empty))
            scenes = []
            for sg in scene_groups:
                eid = sg.get("entity_id") or "__project__"
                try:
                    detail = service.read_artifact(
                        project_id, "scene", eid, sg["latest_version"]
                    )
                    payload = detail.get("payload", {})
                    data = payload.get("data", payload)
                    scenes.append({
                        "entity_id": eid,
                        "scene_number": data.get("scene_number"),
                        "heading": data.get("heading", ""),
                        "location": data.get("location", ""),
                        "int_ext": data.get("int_ext", ""),
                        "time_of_day": data.get("time_of_day", ""),
                        "tone_mood": data.get("tone_mood", ""),
                        "characters": data.get("characters_present", []),
                    })
                except Exception:
                    scenes.append({"entity_id": eid, "error": "Could not load"})
            result = {"scenes": scenes, "count": len(scenes)}
            return ToolResult(content=json.dumps(result, indent=2))

        elif tool_name == "list_characters":
            groups = service.list_artifact_groups(project_id)
            char_groups = [
                g for g in groups
                if g["artifact_type"] == "bible_manifest"
                and (g.get("entity_id") or "").startswith("character_")
            ]
            if not char_groups:
                return ToolResult(content=json.dumps({
                    "characters": [],
                    "note": "No character bibles generated yet.",
                }))
            characters = []
            for cg in char_groups:
                characters.append({
                    "entity_id": cg.get("entity_id"),
                    "latest_version": cg["latest_version"],
                    "health": cg.get("health"),
                })
            return ToolResult(content=json.dumps({"characters": characters}, indent=2))

        elif tool_name == "read_pipeline_graph":
            graph = service.get_pipeline_graph(project_id)
            return ToolResult(content=_format_pipeline_graph(graph))

        # ---- Write tools (proposals with confirmation) ----

        elif tool_name == "propose_artifact_edit":
            return _execute_propose_artifact_edit(tool_input, service, project_id)

        elif tool_name == "propose_run":
            return _execute_propose_run(tool_input, service, project_id)

        else:
            return ToolResult(content=json.dumps({"error": f"Unknown tool: {tool_name}"}))

    except Exception as e:
        log.exception("Tool execution failed: %s", tool_name)
        return ToolResult(content=json.dumps({"error": str(e)}))


def _format_pipeline_graph(graph: dict[str, Any]) -> str:
    """Format the pipeline graph as structured natural language for LLM readability."""
    from cine_forge.pipeline.graph import check_prerequisites, get_available_actions

    lines: list[str] = []

    status_icons = {
        "completed": "\u2705",
        "partial": "\U0001f535",
        "available": "\u26aa",
        "blocked": "\U0001f512",
        "not_started": "\U0001f512",
    }
    node_icons = {
        "completed": "\u2713",
        "stale": "~",
        "in_progress": "\u25b6",
        "available": "\u25cb",
        "blocked": "\u2717",
        "not_implemented": "\u2014",
    }

    for phase in graph["phases"]:
        icon = status_icons.get(phase["status"], "?")
        badge = ""
        if phase["completed_count"] > 0:
            badge = f" ({phase['completed_count']}/{phase['implemented_count']})"
        lines.append(f"{icon} {phase['label']} \u2014 {phase['status']}{badge}")

        phase_nodes = [n for n in graph["nodes"] if n["phase_id"] == phase["id"]]
        for node in phase_nodes:
            ni = node_icons.get(node["status"], "?")
            count = f" ({node['artifact_count']})" if node["artifact_count"] > 0 else ""
            impl = " [coming soon]" if not node["implemented"] else ""
            lines.append(f"  {ni} {node['label']}{count}{impl}")

    # Prioritized available actions.
    actions = get_available_actions(graph)
    if actions:
        lines.append("")
        lines.append("Recommended next actions (in priority order):")
        for i, action in enumerate(actions, 1):
            lines.append(f"  {i}. {action['label']} \u2014 {action['reason']}")

    # Blocked nodes with explanations.
    blocked = [
        n for n in graph["nodes"]
        if n["status"] == "blocked" and n["implemented"]
    ]
    if blocked:
        lines.append("")
        lines.append("Blocked (waiting on upstream):")
        for node in blocked:
            prereqs = check_prerequisites(node["id"], graph)
            if prereqs["unmet"]:
                dep_names = ", ".join(u["label"] for u in prereqs["unmet"])
                lines.append(f"  \U0001f512 {node['label']} \u2014 needs: {dep_names}")
            else:
                lines.append(f"  \U0001f512 {node['label']}")

    # Stale nodes with explanations.
    stale = [
        n for n in graph["nodes"]
        if n["status"] == "stale" and n["implemented"]
    ]
    if stale:
        lines.append("")
        lines.append("Stale (upstream changed, needs rerun):")
        for node in stale:
            reason = node.get("stale_reason", "upstream was updated")
            lines.append(
                f"  ~ {node['label']} ({node['artifact_count']} artifacts)"
                f" \u2014 {reason}"
            )

    return "\n".join(lines)


def _execute_propose_artifact_edit(
    tool_input: dict[str, Any],
    service: Any,
    project_id: str,
) -> ToolResult:
    """Build a diff preview and emit confirmation action buttons."""
    atype = tool_input.get("artifact_type", "")
    eid = tool_input.get("entity_id", "__project__")
    changes = tool_input.get("changes", {})
    rationale = tool_input.get("rationale", "AI-proposed edit")

    # Load the current artifact
    groups = service.list_artifact_groups(project_id)
    match = next(
        (g for g in groups
         if g["artifact_type"] == atype
         and (g.get("entity_id") or "__project__") == eid),
        None,
    )
    if not match:
        return ToolResult(content=json.dumps({
            "error": f"Artifact not found: {atype}/{eid}",
            "hint": "Check available artifacts with get_project_state.",
        }))

    detail = service.read_artifact(project_id, atype, eid, match["latest_version"])
    old_payload = detail.get("payload", {})
    old_data = old_payload.get("data", old_payload)

    # Apply changes to build the proposed new data
    new_data = copy.deepcopy(old_data)
    for key, value in changes.items():
        # Support simple dot notation for one level of nesting
        if "." in key:
            parts = key.split(".", 1)
            if parts[0] in new_data and isinstance(new_data[parts[0]], dict):
                new_data[parts[0]][parts[1]] = value
            else:
                new_data[key] = value
        else:
            new_data[key] = value

    # Compute diff
    diff_lines = _compute_artifact_diff(old_data, new_data)
    if not diff_lines:
        return ToolResult(content=json.dumps({
            "status": "no_changes",
            "message": "The proposed changes don't differ from the current artifact.",
        }))

    diff_preview = "\n".join(diff_lines)

    # Build the full proposed payload (preserving envelope structure)
    proposed_payload = copy.deepcopy(old_payload)
    if "data" in proposed_payload:
        proposed_payload["data"] = new_data
    else:
        proposed_payload = new_data

    # Build action buttons for the frontend
    actions = [
        {
            "id": f"confirm_edit_{eid}_{int(time.time())}",
            "label": "Apply Changes",
            "variant": "default",
            "confirm_action": {
                "type": "edit_artifact",
                "endpoint": f"/api/projects/{project_id}/artifacts/{atype}/{eid}/edit",
                "payload": {
                    "data": proposed_payload,
                    "rationale": rationale,
                },
            },
        },
        {
            "id": f"cancel_edit_{eid}_{int(time.time())}",
            "label": "Cancel",
            "variant": "outline",
        },
    ]

    result = {
        "status": "proposal_ready",
        "artifact": f"{atype}/{eid}",
        "current_version": match["latest_version"],
        "diff": diff_preview,
        "change_count": len(diff_lines),
    }
    return ToolResult(content=json.dumps(result, indent=2), actions=actions)


def _check_recipe_preflight(
    recipe_id: str,
    service: Any,
    project_id: str,
) -> dict[str, Any]:
    """Check pipeline prerequisites for a recipe.

    Returns:
        {
            "tier": "ready" | "warn_stale" | "block_missing",
            "message": str,
            "missing": [{"label": str, "status": str}],
            "stale": [{"label": str}],
        }
    """
    try:
        graph = service.get_pipeline_graph(project_id)
    except Exception:
        # Non-critical — proceed without preflight if graph fails.
        return {"tier": "ready", "message": "", "missing": [], "stale": []}

    node_lookup = {n["id"]: n for n in graph["nodes"]}

    # Map recipe_id to the pipeline nodes it requires as upstream.
    # mvp_ingest is the starting recipe — needs no upstream.
    recipe_prereqs: dict[str, list[str]] = {
        "mvp_ingest": [],
        "ingest_only": [],
        "ingest_normalize": [],
        "ingest_extract": [],
        "ingest_extract_config": [],
        "world_building": ["normalization", "scene_extraction"],
        "creative_direction": ["scene_extraction", "characters"],
        "narrative_analysis": ["characters", "locations", "props"],
        "timeline": ["scene_extraction"],
        "track_system": ["scene_extraction"],
    }

    required_nodes = recipe_prereqs.get(recipe_id, [])
    if not required_nodes:
        return {"tier": "ready", "message": "", "missing": [], "stale": []}

    missing = []
    stale = []

    for nid in required_nodes:
        node = node_lookup.get(nid)
        if not node:
            continue
        if node["status"] in ("blocked", "available"):
            missing.append({"label": node["label"], "status": node["status"]})
        elif node["status"] == "stale":
            stale.append({"label": node["label"]})

    if missing:
        names = ", ".join(m["label"] for m in missing)
        return {
            "tier": "block_missing",
            "message": f"Missing prerequisites: {names}. Run these stages first.",
            "missing": missing,
            "stale": stale,
        }
    elif stale:
        names = ", ".join(s["label"] for s in stale)
        return {
            "tier": "warn_stale",
            "message": f"Upstream stages are stale: {names}. Results may be outdated.",
            "missing": missing,
            "stale": stale,
        }
    else:
        return {"tier": "ready", "message": "", "missing": [], "stale": []}


def _execute_propose_run(
    tool_input: dict[str, Any],
    service: Any,
    project_id: str,
) -> ToolResult:
    """Build a run preview and emit confirmation action buttons."""
    recipe_id = tool_input.get("recipe_id", "mvp_ingest")

    # Look up the recipe
    recipes = service.list_recipes()
    recipe = next((r for r in recipes if r["recipe_id"] == recipe_id), None)
    if not recipe:
        available = [r["recipe_id"] for r in recipes]
        return ToolResult(content=json.dumps({
            "error": f"Recipe not found: {recipe_id}",
            "available_recipes": available,
        }))

    # Get project info for the run payload
    inputs = service.list_project_inputs(project_id)
    if not inputs:
        return ToolResult(content=json.dumps({
            "error": "No input files found. The user needs to upload a screenplay first.",
        }))

    latest_input = inputs[-1]

    # Preflight check: verify pipeline prerequisites.
    preflight = _check_recipe_preflight(recipe_id, service, project_id)

    if preflight["tier"] == "block_missing":
        missing_names = ", ".join(m["label"] for m in preflight["missing"])
        return ToolResult(content=json.dumps({
            "status": "prerequisites_missing",
            "recipe": recipe_id,
            "recipe_name": recipe.get("name", recipe_id),
            "message": preflight["message"],
            "missing_stages": [m["label"] for m in preflight["missing"]],
            "hint": (
                f"The {recipe.get('name', recipe_id)} recipe needs these "
                f"completed first: {missing_names}. "
                "Suggest running the upstream recipe to the user."
            ),
        }, indent=2))

    # Build action buttons
    run_payload = {
        "project_id": project_id,
        "input_file": latest_input["stored_path"],
        "default_model": "claude-sonnet-4-6",
        "recipe_id": recipe_id,
        "accept_config": True,
    }

    actions = [
        {
            "id": f"confirm_run_{recipe_id}_{int(time.time())}",
            "label": f"Start {recipe.get('name', recipe_id)}",
            "variant": "default",
            "confirm_action": {
                "type": "start_run",
                "endpoint": "/api/runs/start",
                "payload": run_payload,
            },
        },
        {
            "id": f"cancel_run_{recipe_id}_{int(time.time())}",
            "label": "Cancel",
            "variant": "outline",
        },
    ]

    result: dict[str, Any] = {
        "status": "proposal_ready",
        "recipe": recipe_id,
        "recipe_name": recipe.get("name", recipe_id),
        "description": recipe.get("description", ""),
        "stage_count": recipe.get("stage_count", 0),
        "input_file": latest_input.get("original_name", latest_input["filename"]),
    }

    # Add warning for stale upstream.
    if preflight["tier"] == "warn_stale":
        result["warning"] = preflight["message"]

    # Build structured preflight data for the frontend card.
    preflight_card_data = {
        "recipe_id": recipe_id,
        "recipe_name": recipe.get("name", recipe_id),
        "description": recipe.get("description", ""),
        "stage_count": recipe.get("stage_count", 0),
        "stages": recipe.get("stages", []),
        "input_file": latest_input.get("original_name", latest_input["filename"]),
        "tier": preflight["tier"],
        "warnings": [],
    }
    if preflight["tier"] == "warn_stale":
        preflight_card_data["warnings"] = [
            {"type": "stale", "label": s["label"]}
            for s in preflight.get("stale", [])
        ]

    return ToolResult(
        content=json.dumps(result, indent=2),
        actions=actions,
        preflight_data=preflight_card_data,
    )


# ---------------------------------------------------------------------------
# Streaming transport
# ---------------------------------------------------------------------------


def _stream_anthropic_sse(
    payload: dict[str, Any],
) -> Generator[dict[str, Any], None, None]:
    """Stream SSE events from the Anthropic Messages API.

    Yields parsed SSE event dicts. Uses http.client for line-by-line reading.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required")

    body = json.dumps(payload).encode("utf-8")
    context = ssl.create_default_context()
    conn = http.client.HTTPSConnection(ANTHROPIC_HOST, context=context)

    try:
        conn.request(
            "POST",
            "/v1/messages",
            body=body,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "prompt-caching-2024-07-31",
            },
        )
        response = conn.getresponse()

        if response.status != 200:
            error_body = response.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Anthropic API error {response.status}: {error_body}"
            )

        # Read SSE events line by line
        event_type = ""

        for raw_line in response:
            line = raw_line.decode("utf-8", errors="replace").rstrip("\n").rstrip("\r")

            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data_str = line[6:]
                try:
                    data = json.loads(data_str)
                    data["_event"] = event_type
                    yield data
                except json.JSONDecodeError:
                    pass
            elif line == "":
                event_type = ""
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Long transcript compaction
# ---------------------------------------------------------------------------

# Rough token estimate: ~4 chars per token. Errs on the side of overestimating.
_CHARS_PER_TOKEN = 4
# Threshold: start summarizing when the transcript exceeds this many estimated tokens.
# Sonnet 4.6 has 200k context; we leave headroom for system prompt + tools + response.
_TRANSCRIPT_TOKEN_THRESHOLD = 80_000
# Keep the most recent N messages verbatim; summarize everything before them.
_KEEP_RECENT = 20

# In-memory summary cache: (project_id, last_summarized_msg_content_hash) -> summary text
_summary_cache: dict[tuple[str, str], str] = {}


def _estimate_tokens(messages: list[dict[str, Any]]) -> int:
    """Rough token count for a message list."""
    total_chars = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for block in content:
                total_chars += len(str(block.get("text", "")))
    return total_chars // _CHARS_PER_TOKEN


def _summarize_prefix(
    messages: list[dict[str, Any]], project_id: str,
) -> str:
    """Call Haiku to summarize older messages into a compact paragraph."""
    # Build a text blob of the messages to summarize
    lines = []
    for m in messages:
        role = m.get("role", "?")
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(b.get("text", "") for b in content)
        lines.append(f"[{role}]: {content[:500]}")

    blob = "\n".join(lines)
    # Truncate to ~30k chars to fit in Haiku context
    if len(blob) > 30000:
        blob = blob[:30000] + "\n... (truncated)"

    prompt_messages = [
        {"role": "user", "content": (
            "Summarize this conversation transcript concisely. "
            "Preserve key decisions, creative direction, and any pending questions. "
            "Write 2-4 paragraphs.\n\n" + blob
        )},
    ]
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "messages": prompt_messages,
        "max_tokens": 1024,
        "temperature": 0,
        "stream": False,
    }

    try:
        return _call_anthropic_sync(payload)
    except Exception:
        log.warning("Transcript summarization failed, using truncation fallback")
        return f"[Earlier conversation summary unavailable. Recent {_KEEP_RECENT} messages follow.]"


def _call_anthropic_sync(payload: dict[str, Any]) -> str:
    """Make a non-streaming Anthropic API call and return the text content."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for transcript summarization")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    ctx = ssl.create_default_context()
    conn = http.client.HTTPSConnection(ANTHROPIC_HOST, context=ctx, timeout=30)
    try:
        conn.request("POST", "/v1/messages", json.dumps(payload), headers)
        resp = conn.getresponse()
        raw = resp.read().decode()
        if resp.status != 200:
            raise ValueError(f"Anthropic API error ({resp.status}): {raw[:500]}")
        body = json.loads(raw)
        # Extract text from content blocks
        text_parts = []
        for block in body.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        return " ".join(text_parts)
    finally:
        conn.close()


def _compact_transcript(
    messages: list[dict[str, Any]], project_id: str,
) -> list[dict[str, Any]]:
    """If the transcript is too long, summarize older messages with Haiku.

    Returns a potentially shorter message list suitable for the API payload.
    Does NOT modify the stored transcript — only the in-flight API payload.
    """
    estimated = _estimate_tokens(messages)
    if estimated <= _TRANSCRIPT_TOKEN_THRESHOLD:
        return messages

    # Split: keep the last N messages verbatim, summarize the rest
    if len(messages) <= _KEEP_RECENT:
        return messages

    prefix = messages[:-_KEEP_RECENT]
    recent = messages[-_KEEP_RECENT:]

    # Check cache
    cache_key_content = str(prefix[-1].get("content", ""))[:200] if prefix else ""
    cache_key = (project_id, cache_key_content)

    summary_text = _summary_cache.get(cache_key)
    if not summary_text:
        summary_text = _summarize_prefix(prefix, project_id)
        # Only cache successful summaries — don't poison the cache with fallback placeholders
        if not summary_text.startswith("[Earlier conversation summary unavailable"):
            _summary_cache[cache_key] = summary_text

    log.info(
        "Compacted transcript: %d messages → summary + %d recent (est. %d→%d tokens)",
        len(messages), len(recent), estimated,
        _estimate_tokens(recent) + len(summary_text) // _CHARS_PER_TOKEN,
    )

    # Inject summary as the first user message
    summary_msg = {
        "role": "user",
        "content": (
            "[Conversation summary — earlier messages condensed]\n\n"
            + summary_text
        ),
    }
    return [summary_msg] + recent


def _add_cache_breakpoints(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add cache_control breakpoint to the last message before the current turn.

    Anthropic prompt caching caches everything before the breakpoint for ~5 min.
    The shared transcript prefix is identical across parallel role calls, so
    multi-role @-mentions get massive cache hits.
    """
    if len(messages) < 2:
        return messages
    result = [dict(m) for m in messages]
    # Set breakpoint on the second-to-last message (last message before current user turn)
    bp_idx = len(result) - 2
    bp_msg = result[bp_idx]
    content = bp_msg.get("content", "")
    if isinstance(content, str):
        result[bp_idx] = {
            **bp_msg,
            "content": [
                {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}},
            ],
        }
    elif isinstance(content, list):
        # Already structured content — add cache_control to the last block
        new_content = list(content)
        if new_content:
            last = dict(new_content[-1])
            last["cache_control"] = {"type": "ephemeral"}
            new_content[-1] = last
        result[bp_idx] = {**bp_msg, "content": new_content}
    return result


def _dump_api_payload(
    payload: dict[str, Any], speaker: str, tool_round: int,
) -> None:
    """Write the exact Anthropic API payload to /tmp for debugging.

    Activated by setting env var CINEFORGE_DUMP_API=1.
    Each call writes /tmp/cineforge-api-{speaker}-{round}.json.
    """
    import json as _json
    path = f"/tmp/cineforge-api-{speaker}-{tool_round}.json"
    try:
        with open(path, "w") as f:
            _json.dump(payload, f, indent=2, default=str)
        log.info("API payload dumped to %s", path)
    except Exception:
        log.warning("Failed to dump API payload to %s", path)


def _stream_single_role(
    messages: list[dict[str, Any]],
    system_prompt: str,
    tools: list[dict[str, Any]],
    service: Any,
    project_id: str,
    speaker: str,
    model: str = CHAT_MODEL,
) -> Generator[dict[str, Any], None, None]:
    """Stream a response for a single role, handling tool use loops.

    Yields dicts with these shapes:
      {"type": "text", "content": "...", "speaker": "..."} — text chunk
      {"type": "tool_start", "name": "...", "id": "...", "speaker": "..."} — tool call
      {"type": "tool_result", "name": "...", "content": "...", "speaker": "..."} — tool result
      {"type": "actions", "actions": [...], "speaker": "..."} — action buttons
    Does NOT yield done/error — the caller handles those.
    """
    compacted = _compact_transcript(messages, project_id)
    current_messages = _add_cache_breakpoints(compacted)
    max_tool_rounds = 5

    # System prompt with cache_control for efficient caching
    system_blocks = [
        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},
    ]

    pending_actions: list[dict[str, Any]] = []

    for tool_round in range(max_tool_rounds):
        payload = {
            "model": model,
            "system": system_blocks,
            "messages": current_messages,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7,
            "stream": True,
            "tools": tools,
        }

        # Dump exact API payload for debugging (opt-in via env var)
        if os.environ.get("CINEFORGE_DUMP_API"):
            _dump_api_payload(payload, speaker, tool_round)

        text_buffer = ""
        tool_use_blocks: list[dict[str, Any]] = []
        current_tool_id = ""
        current_tool_name = ""
        current_tool_input_json = ""
        has_tool_use = False

        for event in _stream_anthropic_sse(payload):
            etype = event.get("_event", "")

            # Log cache metrics from message_start
            if etype == "message_start":
                usage = event.get("message", {}).get("usage", {})
                cache_create = usage.get("cache_creation_input_tokens", 0)
                cache_read = usage.get("cache_read_input_tokens", 0)
                if cache_create or cache_read:
                    log.info(
                        "Prompt cache [%s]: created=%d read=%d",
                        speaker, cache_create, cache_read,
                    )

            elif etype == "content_block_start":
                block = event.get("content_block", {})
                if block.get("type") == "tool_use":
                    has_tool_use = True
                    current_tool_id = block.get("id", "")
                    current_tool_name = block.get("name", "")
                    current_tool_input_json = ""
                    yield {
                        "type": "tool_start",
                        "name": current_tool_name,
                        "id": current_tool_id,
                        "speaker": speaker,
                    }

            elif etype == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        text_buffer += text
                        yield {"type": "text", "content": text, "speaker": speaker}
                elif delta.get("type") == "input_json_delta":
                    current_tool_input_json += delta.get("partial_json", "")

            elif etype == "content_block_stop":
                if current_tool_id and current_tool_name:
                    try:
                        tool_input = (
                            json.loads(current_tool_input_json)
                            if current_tool_input_json else {}
                        )
                    except json.JSONDecodeError:
                        tool_input = {}
                    tool_use_blocks.append({
                        "id": current_tool_id,
                        "name": current_tool_name,
                        "input": tool_input,
                    })
                    current_tool_id = ""
                    current_tool_name = ""
                    current_tool_input_json = ""

            elif etype == "message_delta":
                pass

        if has_tool_use and tool_use_blocks:
            assistant_content: list[dict[str, Any]] = []
            if text_buffer:
                assistant_content.append({"type": "text", "text": text_buffer})
            for tb in tool_use_blocks:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tb["id"],
                    "name": tb["name"],
                    "input": tb["input"],
                })
            current_messages.append({"role": "assistant", "content": assistant_content})

            tool_results: list[dict[str, Any]] = []
            pending_actions = []
            pending_preflight = None
            for tb in tool_use_blocks:
                result = execute_tool(
                    tb["name"], tb["input"], service, project_id
                )
                preview = (
                    result.content[:500] + "..."
                    if len(result.content) > 500
                    else result.content
                )
                yield {
                    "type": "tool_result",
                    "name": tb["name"],
                    "id": tb["id"],
                    "content": preview,
                    "speaker": speaker,
                }
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tb["id"],
                    "content": result.content,
                })
                if result.actions:
                    pending_actions.extend(result.actions)
                if result.preflight_data:
                    pending_preflight = result.preflight_data
            current_messages.append({"role": "user", "content": tool_results})

            text_buffer = ""
            tool_use_blocks = []
            has_tool_use = False
            continue

        # No tool calls — this role is done
        if pending_actions:
            chunk: dict[str, Any] = {
                "type": "actions",
                "actions": pending_actions,
                "speaker": speaker,
            }
            if pending_preflight:
                chunk["preflight_data"] = pending_preflight
            yield chunk
        return

    # Exhausted tool rounds
    if pending_actions:
        exhaust_chunk: dict[str, Any] = {
            "type": "actions",
            "actions": pending_actions,
            "speaker": speaker,
        }
        if pending_preflight:
            exhaust_chunk["preflight_data"] = pending_preflight
        yield exhaust_chunk


def stream_group_chat(
    messages: list[dict[str, Any]],
    targets: ResolvedTargets,
    project_summary: dict[str, Any],
    state_info: dict[str, Any],
    service: Any,
    project_id: str,
    catalog: Any,
    style_pack_selections: dict[str, str] | None = None,
    page_context: str | None = None,
    model: str = CHAT_MODEL,
) -> Generator[dict[str, Any], None, None]:
    """Stream group chat responses from roles and/or characters.

    Ordering: non-Director roles → characters → Director (if present).
    Characters use Haiku model, no tools, fat system prompt.

    Yields the same chunk shapes as _stream_single_role, plus:
      {"type": "role_start", "speaker": "...", "display_name": "..."}
      {"type": "role_done", "speaker": "..."}
      {"type": "done"} — all roles finished
    """
    from cine_forge.roles.runtime import RoleCatalog

    assert isinstance(catalog, RoleCatalog)

    target_roles = targets.roles
    target_characters = targets.characters

    def _tools_for_role(role_id: str) -> list[dict[str, Any]]:
        """Assistant gets all tools; creative roles get read tools only."""
        if role_id == "assistant":
            return ALL_CHAT_TOOLS
        return READ_TOOLS

    def _stream_one_role(
        role_id: str, msgs: list[dict[str, Any]],
    ) -> Generator[dict[str, Any], None, None]:
        """Stream a single role with role_start/role_done envelope."""
        role = catalog.get_role(role_id)
        yield {
            "type": "role_start",
            "speaker": role_id,
            "display_name": role.display_name,
        }
        if page_context:
            yield {"type": "context_info", "content": page_context, "speaker": role_id}
            # Emit the actual injected artifact content for persistence/debugging
            injected = _inject_page_artifact(page_context, service, project_id)
            if injected:
                yield {
                    "type": "injected_content",
                    "content": injected,
                    "speaker": role_id,
                }
        system_prompt = build_role_system_prompt(
            role_id, project_summary, state_info, catalog,
            style_pack_selections, page_context,
            service=service, project_id=project_id,
        )
        tools = _tools_for_role(role_id)
        yield from _stream_single_role(
            msgs, system_prompt, tools, service, project_id, role_id, model,
        )
        yield {"type": "role_done", "speaker": role_id}

    def _stream_one_character(
        char_entity_id: str, msgs: list[dict[str, Any]],
    ) -> Generator[dict[str, Any], None, None]:
        """Stream a character response — Haiku, trimmed history, fat system prompt.

        Characters get a short transcript window (last 10 messages) to avoid
        history poisoning — long conversations with repeated patterns can
        override the system prompt in smaller models.
        """
        project_title = project_summary.get("display_name", "Unknown")
        char_prompt = build_character_system_prompt(
            char_entity_id, service, project_id, project_title,
            page_context=page_context,
        )
        if not char_prompt:
            # Character data not available — emit a graceful error
            speaker = f"char:{char_entity_id.replace('character_', '')}"
            yield {"type": "role_start", "speaker": speaker, "display_name": char_entity_id}
            yield {
                "type": "text",
                "content": (
                    "I can't respond right now — my character bible "
                    "hasn't been created yet. Run the world-building "
                    "pipeline first to bring me to life."
                ),
                "speaker": speaker,
            }
            yield {"type": "role_done", "speaker": speaker}
            return

        char_handle = char_entity_id.replace("character_", "")
        speaker = f"char:{char_handle}"
        display_name = char_handle.replace("_", " ").title()

        # Filter transcript to this character's thread only.
        # The merged message list contains responses from ALL characters.
        # Including other characters' "nothing attached" responses poisons
        # this character's context — it copies the pattern instead of
        # reading the system prompt.  Keep only user messages and this
        # character's own assistant responses (tagged [@char:name]:).
        tag = f"[@{speaker}]:"
        filtered = [
            m for m in msgs
            if m["role"] == "user"
            or (m["role"] == "assistant" and m.get("content", "").startswith(tag))
        ]
        # Merge consecutive same-role messages (filtering may create
        # adjacent user messages when other characters' responses are removed).
        merged: list[dict[str, Any]] = []
        for m in filtered:
            if merged and merged[-1]["role"] == m["role"]:
                merged[-1] = {**merged[-1], "content": merged[-1]["content"] + "\n" + m["content"]}
            else:
                merged.append(m)
        # Then window to the last N exchanges.
        _CHAR_HISTORY_WINDOW = 10
        char_msgs = merged[-_CHAR_HISTORY_WINDOW:] if len(merged) > _CHAR_HISTORY_WINDOW else merged
        # Ensure the trimmed list starts with a user message
        while char_msgs and char_msgs[0].get("role") != "user":
            char_msgs = char_msgs[1:]

        # When a scene/entity is injected, append a system-level hint to
        # the final user message so the model sees it adjacent to the
        # question (not buried in a system prompt it may deprioritize
        # versus strong in-context patterns in the chat history).
        if page_context and char_msgs and char_msgs[-1]["role"] == "user":
            hint = (
                "\n\n[System: A scene has been attached to your system "
                "prompt under '## Attached Scene'. Read it and reference "
                "its content in your reply.]"
            )
            char_msgs = [*char_msgs]  # shallow copy
            last = char_msgs[-1]
            char_msgs[-1] = {**last, "content": last["content"] + hint}

        yield {"type": "role_start", "speaker": speaker, "display_name": display_name}
        # Emit context info so the user sees what was injected
        if page_context:
            yield {"type": "context_info", "content": page_context, "speaker": speaker}
            # Emit the actual injected artifact content for persistence/debugging
            injected = _inject_page_artifact(page_context, service, project_id)
            if injected:
                yield {
                    "type": "injected_content",
                    "content": injected,
                    "speaker": speaker,
                }
        # Characters use Sonnet — Haiku is too easily swayed by chat history patterns
        yield from _stream_single_role(
            char_msgs, char_prompt, READ_TOOLS, service, project_id, speaker, CHAT_MODEL,
        )
        yield {"type": "role_done", "speaker": speaker}

    # Build the streaming order: non-Director roles → characters → Director
    non_director_roles = [r for r in target_roles if r != "director"]
    has_director = "director" in target_roles

    total_targets = len(target_roles) + len(target_characters)

    if total_targets == 1 and not target_characters:
        # Single role — direct streaming, no multi-role overhead
        yield from _stream_one_role(target_roles[0], messages)
        yield {"type": "done"}
        return

    if total_targets == 1 and target_characters:
        # Single character
        yield from _stream_one_character(target_characters[0], messages)
        yield {"type": "done"}
        return

    # Multi-target: stream each sequentially, appending responses to transcript
    current_messages = list(messages)

    def _append_response(text: str) -> None:
        """Append a completed response to the transcript for the next speaker."""
        if text:
            current_messages.append({"role": "assistant", "content": text})
            current_messages.append({
                "role": "user",
                "content": "[Group chat continues — next role responding]",
            })

    def _safe_stream(gen_fn, label: str):
        """Yield from a role/character generator, catching errors so one
        failure doesn't kill the entire group stream."""
        try:
            yield from gen_fn()
        except Exception as exc:
            log.exception("Group chat: %s failed", label)
            yield {
                "type": "text",
                "content": f"(Sorry, I encountered an error: {exc})",
                "speaker": label,
            }

    # 1. Non-Director roles
    for role_id in non_director_roles:
        gen = _safe_stream(
            lambda rid=role_id: _stream_one_role(rid, current_messages),
            role_id,
        )
        role_text = ""
        for chunk in gen:
            yield chunk
            if chunk.get("type") == "text":
                role_text += chunk.get("content", "")
        _append_response(role_text)

    # 2. Characters
    for char_id in target_characters:
        gen = _safe_stream(
            lambda cid=char_id: _stream_one_character(cid, current_messages),
            f"char:{char_id.replace('character_', '')}",
        )
        char_text = ""
        for chunk in gen:
            yield chunk
            if chunk.get("type") == "text":
                char_text += chunk.get("content", "")
        _append_response(char_text)

    # 3. Director last (convergence: sees all other responses)
    if has_director:
        director_text = ""
        for chunk in _safe_stream(
            lambda: _stream_one_role("director", current_messages),
            "director",
        ):
            yield chunk
            if chunk.get("type") == "text":
                director_text += chunk.get("content", "")

    yield {"type": "done"}


# Legacy name for backward compatibility with insight endpoint
def stream_chat_response(
    messages: list[dict[str, Any]],
    system_prompt: str,
    service: Any,
    project_id: str,
    model: str = CHAT_MODEL,
) -> Generator[dict[str, Any], None, None]:
    """Stream a chat response using the assistant role (legacy wrapper).

    Used by the /chat/insight endpoint which doesn't need role routing.
    """
    system_blocks = [
        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},
    ]
    cached_messages = _add_cache_breakpoints(messages)
    payload = {
        "model": model,
        "system": system_blocks,
        "messages": cached_messages,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.7,
        "stream": True,
        "tools": ALL_CHAT_TOOLS,
    }

    # Simple single-round streaming (insight responses don't use tool loops)
    for event in _stream_anthropic_sse(payload):
        etype = event.get("_event", "")
        if etype == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                text = delta.get("text", "")
                if text:
                    yield {"type": "text", "content": text}

    yield {"type": "done"}


# ---------------------------------------------------------------------------
# Auto-insight generation
# ---------------------------------------------------------------------------

INSIGHT_PROMPTS: dict[str, str] = {
    "run_completed": (
        "A pipeline run just completed ({recipe_display_name}). "
        "It produced: {artifact_summary}. "
        "Use your tools to look at what was produced. "
        "Also call `read_pipeline_graph` to see what's now unlocked in the pipeline. "
        "Give a brief (2-4 sentence) creative observation about the project "
        "based on what you find — mention specific characters, themes, or story "
        "elements. Then recommend the most impactful next step based on the "
        "pipeline graph (what's newly available, what's still blocked). "
        "Use user-facing names for pipeline steps: 'Script Breakdown' and 'Deep Breakdown' — "
        "never 'mvp_ingest', 'world_building', or 'recipe'. "
        "Be specific and enthusiastic, not generic."
    ),
    "welcome": (
        "The user just opened their project. "
        "Use your tools to review the current state and artifacts. "
        "Give a brief (2-3 sentence) personalized welcome that references "
        "specific story elements — characters, themes, or interesting details "
        "you find. Then suggest what they might want to work on."
    ),
}


def build_insight_prompt(trigger: str, context: dict[str, Any]) -> str:
    """Build a user-facing prompt for auto-insight generation."""
    template = INSIGHT_PROMPTS.get(trigger)
    if not template:
        return f"Provide a brief insight about the current project state. Trigger: {trigger}"

    try:
        return template.format(**context)
    except KeyError:
        defaults = {k: f"({k})" for k in ["recipe_id", "recipe_display_name", "artifact_summary"]}
        return template.format_map({**context, **defaults})
