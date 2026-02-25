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
- Character voice, motivation, performance → suggest @actor_agent
- Creative convergence, big-picture decisions → suggest @director

Keep it natural — a short note like "The @visual_architect could give you a detailed \
breakdown of the framing here" is better than a rigid redirect.
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


def build_role_system_prompt(
    role_id: str,
    project_summary: dict[str, Any],
    state_info: dict[str, Any],
    catalog: Any,
    style_pack_selections: dict[str, str] | None = None,
    page_context: str | None = None,
) -> str:
    """Build the full system prompt for a specific role in the group chat.

    Combines: role base prompt + style pack + project context + group chat instructions.
    The assistant role also gets write-tool instructions.
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

    # Append page context if provided
    if page_context:
        prompt += f"\n\n## Current Page Context\n{page_context}"

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
# @-mention routing
# ---------------------------------------------------------------------------

# All creative role IDs (non-assistant). Director is always sorted last.
CREATIVE_ROLES = [
    "editorial_architect", "visual_architect", "sound_designer", "actor_agent", "director",
]
ALL_CREATIVE_SET = set(CREATIVE_ROLES)

# Valid role IDs for @-mention routing.
VALID_ROLE_IDS: set[str] = {"assistant"} | ALL_CREATIVE_SET

_MENTION_RE = re.compile(r"@([\w-]+)")


def resolve_target_roles(
    message: str,
    active_role: str | None = None,
) -> list[str]:
    """Parse @-mentions from a user message and return target role IDs.

    Rules:
    - @all-creatives → all 5 creative roles (director last)
    - Explicit @-mentions → those roles (director sorted last if present)
    - No @-mention → sticky role (active_role), default to assistant
    """
    mentions = _MENTION_RE.findall(message)

    # Expand @all-creatives
    if "all-creatives" in mentions:
        return list(CREATIVE_ROLES)  # director is already last

    # Filter to valid role IDs
    targets = [m for m in mentions if m in VALID_ROLE_IDS]

    if not targets:
        # Stickiness: route to last-addressed role
        return [active_role if active_role and active_role in VALID_ROLE_IDS else "assistant"]

    # Deduplicate while preserving order, sort director last
    seen: set[str] = set()
    deduped: list[str] = []
    for t in targets:
        if t not in seen:
            seen.add(t)
            deduped.append(t)

    # Move director to end if present (convergence: sees all other responses first)
    if "director" in deduped and len(deduped) > 1:
        deduped.remove("director")
        deduped.append("director")

    return deduped


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
                        "The artifact type (e.g., 'scene_extract',"
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
                g for g in groups if g["artifact_type"] == "scene_extract"
            ]
            if not scene_groups:
                empty = {"scenes": [], "note": "No scenes extracted yet."}
                return ToolResult(content=json.dumps(empty))
            scenes = []
            for sg in scene_groups:
                eid = sg.get("entity_id") or "__project__"
                try:
                    detail = service.read_artifact(
                        project_id, "scene_extract", eid, sg["latest_version"]
                    )
                    payload = detail.get("payload", {})
                    data = payload.get("data", payload)
                    scenes.append({
                        "entity_id": eid,
                        "heading": data.get("heading", ""),
                        "summary": data.get("summary", ""),
                        "characters": data.get("characters", []),
                        "location": data.get("location", ""),
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

    result = {
        "status": "proposal_ready",
        "recipe": recipe_id,
        "recipe_name": recipe.get("name", recipe_id),
        "description": recipe.get("description", ""),
        "stage_count": recipe.get("stage_count", 0),
        "input_file": latest_input.get("original_name", latest_input["filename"]),
    }
    return ToolResult(content=json.dumps(result, indent=2), actions=actions)


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

    for _ in range(max_tool_rounds):
        payload = {
            "model": model,
            "system": system_blocks,
            "messages": current_messages,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7,
            "stream": True,
            "tools": tools,
        }

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
            current_messages.append({"role": "user", "content": tool_results})

            text_buffer = ""
            tool_use_blocks = []
            has_tool_use = False
            continue

        # No tool calls — this role is done
        if pending_actions:
            yield {"type": "actions", "actions": pending_actions, "speaker": speaker}
        return

    # Exhausted tool rounds
    if pending_actions:
        yield {"type": "actions", "actions": pending_actions, "speaker": speaker}


def stream_group_chat(
    messages: list[dict[str, Any]],
    target_roles: list[str],
    project_summary: dict[str, Any],
    state_info: dict[str, Any],
    service: Any,
    project_id: str,
    catalog: Any,
    style_pack_selections: dict[str, str] | None = None,
    page_context: str | None = None,
    model: str = CHAT_MODEL,
) -> Generator[dict[str, Any], None, None]:
    """Stream group chat responses from one or more roles.

    For single role: stream directly.
    For multi-role: stream non-Director roles sequentially (threads are complex
    with generators), appending each response to the transcript, then Director last.

    Yields the same chunk shapes as _stream_single_role, plus:
      {"type": "role_start", "speaker": "...", "display_name": "..."}
      {"type": "role_done", "speaker": "..."}
      {"type": "done"} — all roles finished
    """
    from cine_forge.roles.runtime import RoleCatalog

    assert isinstance(catalog, RoleCatalog)

    def _tools_for_role(role_id: str) -> list[dict[str, Any]]:
        """Assistant gets all tools; creative roles get read tools only."""
        if role_id == "assistant":
            return ALL_CHAT_TOOLS
        return READ_TOOLS

    def _stream_one(
        role_id: str, msgs: list[dict[str, Any]],
    ) -> Generator[dict[str, Any], None, None]:
        """Stream a single role with role_start/role_done envelope."""
        role = catalog.get_role(role_id)
        yield {
            "type": "role_start",
            "speaker": role_id,
            "display_name": role.display_name,
        }
        system_prompt = build_role_system_prompt(
            role_id, project_summary, state_info, catalog,
            style_pack_selections, page_context,
        )
        tools = _tools_for_role(role_id)
        yield from _stream_single_role(
            msgs, system_prompt, tools, service, project_id, role_id, model,
        )
        yield {"type": "role_done", "speaker": role_id}

    if len(target_roles) == 1:
        # Single role — direct streaming, no multi-role overhead
        yield from _stream_one(target_roles[0], messages)
        yield {"type": "done"}
        return

    # Multi-role: stream each sequentially. For each role after the first,
    # the transcript includes the previous roles' full responses so they
    # can build on each other. Director always goes last.
    #
    # We collect each role's full text to append to the transcript before
    # the next role sees it.
    current_messages = list(messages)

    for role_id in target_roles:
        role_text = ""
        for chunk in _stream_one(role_id, current_messages):
            yield chunk
            if chunk.get("type") == "text":
                role_text += chunk.get("content", "")

        # Append this role's response to the transcript so the next role sees it.
        # Anthropic requires alternating user/assistant messages, so we also
        # insert a synthetic user turn to bridge to the next role.
        if role_text:
            current_messages.append({
                "role": "assistant",
                "content": role_text,
            })
            current_messages.append({
                "role": "user",
                "content": "[Group chat continues — next role responding]",
            })

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
        "Give a brief (2-4 sentence) creative observation about the project "
        "based on what you find — mention specific characters, themes, or story "
        "elements. Then suggest what the user should look at first or do next. "
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
