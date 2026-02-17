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
import ssl
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Generator

log = logging.getLogger(__name__)

CHAT_MODEL = "claude-sonnet-4-5-20250929"
ANTHROPIC_HOST = "api.anthropic.com"
MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are the CineForge Assistant — a knowledgeable creative collaborator for filmmakers \
using the CineForge story development platform.

## Who You Are
You're like a smart, enthusiastic assistant director who has read the screenplay, \
knows the characters intimately, understands film production concepts, and can discuss \
creative ideas with substance. You're not a chatbot or help desk — you engage in real \
creative discussion grounded in the user's actual project.

## What You Know
- **The user's project**: You have access to their project state, artifacts (character \
bibles, location bibles, scene breakdowns, entity graphs), and chat history. Use tools \
to look things up when needed.
- **Film production concepts**: Coverage, blocking, continuity, shot types, lighting, \
color grading, sound design, editorial structure. Explain these in context of the user's \
project, never abstractly.
- **CineForge workflow**: The platform processes screenplays through an analysis pipeline \
(scene extraction, character/location/prop identification) and then builds creative \
artifacts (character bibles, location bibles, entity relationship graphs). Users can \
review, discuss, and iterate on these artifacts.

## How You Behave
- **Be concise**: Short, focused responses. No walls of text. Quick answers for simple \
questions, more depth only when the topic warrants it.
- **Be grounded**: When discussing the user's project, reference specific characters, \
scenes, locations, and plot points. Use tools to look up details rather than guessing.
- **Be creative**: When discussing creative ideas, offer specific, actionable suggestions. \
"The Mariner's motivation in scene 7 seems unclear — his decision could be driven by grief \
rather than duty" is good. "Consider developing the character more" is bad.
- **Be honest**: If you don't know something or can't find it, say so. Don't make things up.
- **Suggest actions**: When an action is possible, offer it. "Want me to look at the \
character bible?" or "I can check what scenes mention that location."

## Project Context
{project_context}

## Current State
{state_context}

## State Machine Context
{state_machine_context}
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
            "description": "Run initial analysis — scene extraction, normalization, character/location identification.",
        })
    elif state == "analyzed":
        next_actions.append({
            "action": "review_artifacts",
            "description": "Review the extracted scenes, characters, and locations.",
        })
        next_actions.append({
            "action": "go_deeper",
            "recipe_id": "world_building",
            "description": "Build character bibles, location bibles, entity graph, and creative world details.",
        })
    elif state == "complete":
        next_actions.append({
            "action": "explore",
            "description": "Explore scenes, characters, locations, and creative bibles.",
        })
        next_actions.append({
            "action": "edit_artifacts",
            "description": "Discuss and refine character bibles, location details, or story elements.",
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


def build_system_prompt(
    project_summary: dict[str, Any],
    artifact_groups: list[dict[str, Any]],
    project_state: str,
    state_info: dict[str, Any] | None = None,
) -> str:
    """Assemble the system prompt with project-specific context."""
    project_context = (
        f"Project: {project_summary.get('display_name', 'Unknown')}\n"
        f"Input files: {', '.join(project_summary.get('input_files', [])) or 'None'}\n"
        f"Artifact groups: {len(artifact_groups)}\n"
        f"Runs completed: {project_summary.get('run_count', 0)}"
    )

    artifact_summary = ""
    if artifact_groups:
        artifact_lines = []
        for ag in artifact_groups:
            entity = ag.get("entity_id") or "project"
            artifact_lines.append(
                f"  - {ag['artifact_type']}/{entity} (v{ag['latest_version']}, "
                f"health: {ag.get('health', 'unknown')})"
            )
        artifact_summary = "\nAvailable artifacts:\n" + "\n".join(artifact_lines)

    state_context = f"Project state: {project_state}{artifact_summary}"

    # Build state machine context — tells the AI what the deterministic state
    # machine would suggest, so the AI can augment with creative insight.
    state_machine_lines = [f"The project is in the **{project_state}** state."]

    state_descriptions = {
        "empty": "No screenplay uploaded yet. The user needs to upload a script to begin.",
        "fresh_import": "A screenplay has been uploaded but not analyzed. The next step is running the initial analysis pipeline.",
        "processing": "A pipeline run is currently in progress. Wait for it to complete.",
        "analyzed": "Initial analysis is complete — scenes, characters, and locations have been extracted. The user can review these or run the world-building pipeline for deeper creative artifacts.",
        "complete": "Full analysis and world-building are done. Character bibles, location bibles, and the entity graph are available. The user can explore, discuss, and refine artifacts.",
    }
    state_machine_lines.append(state_descriptions.get(project_state, ""))

    if state_info and state_info.get("next_actions"):
        state_machine_lines.append("\nAvailable next steps:")
        for action in state_info["next_actions"]:
            recipe = action.get("recipe_id", "")
            recipe_hint = f" (recipe: {recipe})" if recipe else ""
            state_machine_lines.append(
                f"- **{action['action']}**: {action['description']}{recipe_hint}"
            )

    state_machine_lines.append(
        "\nYou should be aware of these state-driven suggestions and enrich them "
        "with project-specific creative insight. When suggesting a next step, reference "
        "specific characters, scenes, or story elements the user will encounter."
    )

    state_machine_context = "\n".join(state_machine_lines)

    return SYSTEM_PROMPT.format(
        project_context=project_context,
        state_context=state_context,
        state_machine_context=state_machine_context,
    )


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

CHAT_TOOLS = [
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
                    "description": "The artifact type (e.g., 'scene_extract', 'bible_manifest', 'entity_graph', 'project_config', 'normalized_script').",
                },
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID (e.g., 'character_the_mariner', 'location_harbor', '__project__' for project-level artifacts, or a scene ID like 'scene_001').",
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
                return ToolResult(content=json.dumps({"error": f"Artifact not found: {atype}/{eid}"}))
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
                return ToolResult(content=json.dumps({"scenes": [], "note": "No scenes extracted yet."}))
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
            return ToolResult(content=json.dumps({"scenes": scenes, "count": len(scenes)}, indent=2))

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
    rationale = tool_input.get("rationale", "AI-proposed run")

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
    summary = service.project_summary(project_id)
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
        "default_model": "claude-sonnet-4-5-20250929",
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
            },
        )
        response = conn.getresponse()

        if response.status != 200:
            error_body = response.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Anthropic API error {response.status}: {error_body}"
            )

        # Read SSE events line by line
        buffer = ""
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


def stream_chat_response(
    messages: list[dict[str, Any]],
    system_prompt: str,
    service: Any,
    project_id: str,
    model: str = CHAT_MODEL,
) -> Generator[dict[str, Any], None, None]:
    """Stream a chat response, handling tool use loops.

    Yields dicts with these shapes:
      {"type": "text", "content": "..."} — text chunk
      {"type": "tool_start", "name": "...", "id": "..."} — tool call starting
      {"type": "tool_result", "name": "...", "content": "..."} — tool result
      {"type": "done"} — stream complete
      {"type": "error", "content": "..."} — error
    """
    current_messages = list(messages)
    max_tool_rounds = 5  # Prevent infinite tool loops
    pending_actions: list[dict[str, Any]] = []

    for _ in range(max_tool_rounds):
        payload = {
            "model": model,
            "system": system_prompt,
            "messages": current_messages,
            "max_tokens": MAX_TOKENS,
            "temperature": 0.7,
            "stream": True,
            "tools": CHAT_TOOLS,
        }

        text_buffer = ""
        tool_use_blocks: list[dict[str, Any]] = []
        current_tool_id = ""
        current_tool_name = ""
        current_tool_input_json = ""
        has_tool_use = False
        stop_reason = ""

        for event in _stream_anthropic_sse(payload):
            etype = event.get("_event", "")

            if etype == "content_block_start":
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
                    }

            elif etype == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    text = delta.get("text", "")
                    if text:
                        text_buffer += text
                        yield {"type": "text", "content": text}
                elif delta.get("type") == "input_json_delta":
                    current_tool_input_json += delta.get("partial_json", "")

            elif etype == "content_block_stop":
                if current_tool_id and current_tool_name:
                    try:
                        tool_input = json.loads(current_tool_input_json) if current_tool_input_json else {}
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
                delta = event.get("delta", {})
                stop_reason = delta.get("stop_reason", "")

        # If there were tool calls, execute them and continue the loop
        if has_tool_use and tool_use_blocks:
            # Build the assistant message with content blocks
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

            # Execute tools and build tool_result message
            tool_results: list[dict[str, Any]] = []
            pending_actions: list[dict[str, Any]] = []
            for tb in tool_use_blocks:
                result = execute_tool(
                    tb["name"], tb["input"], service, project_id
                )
                preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
                yield {
                    "type": "tool_result",
                    "name": tb["name"],
                    "content": preview,
                }
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tb["id"],
                    "content": result.content,
                })
                if result.actions:
                    pending_actions.extend(result.actions)
            current_messages.append({"role": "user", "content": tool_results})

            # Reset for next round
            text_buffer = ""
            tool_use_blocks = []
            has_tool_use = False
            continue

        # No tool calls — we're done
        # Emit any pending actions from the last tool round
        if pending_actions:
            yield {"type": "actions", "actions": pending_actions}
        yield {"type": "done"}
        return

    # Exhausted tool rounds
    if pending_actions:
        yield {"type": "actions", "actions": pending_actions}
    yield {"type": "done"}


# ---------------------------------------------------------------------------
# Auto-insight generation
# ---------------------------------------------------------------------------

INSIGHT_PROMPTS: dict[str, str] = {
    "run_completed": (
        "A pipeline run just completed ({recipe_id} recipe). "
        "It produced: {artifact_summary}. "
        "Use your tools to look at what was produced. "
        "Give a brief (2-4 sentence) creative observation about the project "
        "based on what you find — mention specific characters, themes, or story "
        "elements. Then suggest what the user should look at first or do next. "
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
        return template.format_map({**context, **{k: f"({k})" for k in ["recipe_id", "artifact_summary"]}})
