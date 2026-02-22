from typing import Any


def generate_header(title: str, level: int = 1) -> str:
    return f"{'#' * level} {title}\n\n"

def generate_metadata(label: str, value: Any) -> str:
    if value is None:
        return ""
    return f"**{label}:** {value}\n\n"

def generate_list(label: str, items: list[str] | None) -> str:
    if not items:
        return ""
    md = f"**{label}:**\n"
    for item in items:
        md += f"- {item}\n"
    md += "\n"
    return md

class MarkdownExporter:
    def format_entity_name(self, entity_id: str) -> str:
        if not entity_id:
            return "Unknown"
        # Simple title case conversion: "the_mariner" -> "The Mariner"
        return entity_id.replace("_", " ").title()

    def generate_scene_markdown(self, scene_data: dict[str, Any], index: int) -> str:
        heading = (
            scene_data.get("heading") or 
            scene_data.get("scene_heading") or 
            f"Scene {index}"
        )
        location = scene_data.get("location") or scene_data.get("scene_location")
        int_ext = scene_data.get("int_ext") or scene_data.get("interior_exterior")
        time_of_day = scene_data.get("time_of_day") or scene_data.get("time")
        summary = scene_data.get("summary") or scene_data.get("description")

        md = generate_header(heading, 2)
        md += generate_metadata("Location", location)
        md += generate_metadata("Int/Ext", int_ext)
        md += generate_metadata("Time", time_of_day)
        md += generate_metadata("Scene Number", index)
        md += generate_metadata("Summary", summary)

        if characters := scene_data.get("characters_present"):
            md += generate_list("Characters Present", characters)
        
        # Props might be in 'props_present' or inferred elsewhere, check standard keys
        if props := scene_data.get("props_present"):
            md += generate_list("Props Present", props)

        # Tone & Mood
        if tone := scene_data.get("tone_mood") or scene_data.get("atmosphere"):
            md += generate_metadata("Tone & Mood", tone)
        
        # Tone Shifts
        if tone_shifts := scene_data.get("tone_shifts"):
            md += generate_list("Tone Shifts", tone_shifts)

        # Narrative Beats
        # Prefer 'narrative_beats' (list of dicts), fallback to 'plot_point' (string)
        if beats := scene_data.get("narrative_beats"):
            md += "**Narrative Beats:**\n"
            for beat in beats:
                if isinstance(beat, dict):
                    btype = beat.get("beat_type", "Beat").replace("_", " ").title()
                    desc = beat.get("description", "")
                    md += f"- **{btype}:** {desc}\n"
                else:
                    md += f"- {beat}\n"
            md += "\n"
        elif plot := scene_data.get("plot_point"):
            md += generate_metadata("Plot Point", plot)

        # Visual/Audio Details
        if visual_details := scene_data.get("visual_details"):
            md += generate_list("Visual Details", visual_details)
        if audio_details := scene_data.get("audio_details"):
            md += generate_list("Audio Details", audio_details)

        # Script Elements (The actual script content)
        if elements := scene_data.get("elements"):
            md += "**Script Content:**\n\n"
            for elem in elements:
                etype = elem.get("element_type", "action")
                content = elem.get("content", "")
                
                if etype == "scene_heading":
                    md += f"**{content.upper()}**\n\n"
                elif etype == "character":
                    md += f"**{content.upper()}**\n" # No center in MD, just bold
                elif etype == "dialogue":
                    md += f"> {content}\n\n" # Blockquote for dialogue
                elif etype == "parenthetical":
                    md += f"> *{content}*\n" # Italic blockquote
                elif etype == "transition":
                    md += f"*{content.upper()}*\n\n"
                else: # action, general
                    md += f"{content}\n\n"
            md += "---\n\n"

        return md

    def generate_entity_markdown(
        self, entity_data: dict[str, Any], entity_id: str, type_label: str
    ) -> str:
        name = entity_data.get("name") or self.format_entity_name(entity_id)
        md = generate_header(name, 2)

        # Aliases
        if aliases := entity_data.get("aliases"):
            md += f"**Aliases:** {', '.join(aliases)}\n\n"

        # Confidence
        if confidence := entity_data.get("overall_confidence"):
            md += f"**Confidence:** {int(confidence * 100)}%\n\n"

        # Description
        if description := entity_data.get("description"):
            md += generate_metadata("Description", description)

        # Narrative Role / Significance
        # Characters have 'narrative_role', Locations/Props have 'narrative_significance'
        if role := entity_data.get("narrative_role"):
            md += generate_metadata("Narrative Role", role)
        
        if significance := entity_data.get("narrative_significance"):
            md += generate_metadata("Narrative Significance", significance)

        # Dialogue Summary (Characters)
        if dialogue := entity_data.get("dialogue_summary"):
            md += generate_metadata("Dialogue Summary", dialogue)
        
        # Inferred Traits (Characters) - formatted nicely
        if traits := entity_data.get("inferred_traits"):
            md += "**Inferred Traits:**\n"
            for t in traits:
                if isinstance(t, dict):
                    trait_name = t.get("trait", "Unknown")
                    value = t.get("value", "")
                    rationale = t.get("rationale", "")
                    md += f"- **{trait_name}:** {value}\n"
                    if rationale:
                        md += f"  > {rationale}\n"
                else:
                    md += f"- {t}\n"
            md += "\n"

        # Physical Traits (Locations)
        if physical := entity_data.get("physical_traits"):
            md += generate_list("Physical Traits", physical)

        # Explicit Evidence (Characters)
        if evidence := entity_data.get("explicit_evidence"):
            md += "**Evidence:**\n"
            for ev in evidence:
                if isinstance(ev, dict):
                    trait = ev.get("trait")
                    quote = ev.get("quote")
                    source = ev.get("source_scene")
                    if trait:
                        md += f"- *{trait}*\n"
                    if quote:
                        md += f"  > \"{quote}\"\n"
                    if source:
                        md += f"  (Source: {source})\n"
                else:
                    md += f"- {ev}\n"
            md += "\n"

        # General Evidence (Locations/Props)
        if simple_evidence := entity_data.get("evidence"):
             if isinstance(simple_evidence, list):
                md += generate_list("Evidence", simple_evidence)
             else:
                md += generate_metadata("Evidence", simple_evidence)

        # Relationships
        if relationships := entity_data.get("relationships"):
            md += "**Relationships:**\n"
            for rel in relationships:
                if isinstance(rel, dict):
                    target = rel.get("target_character")
                    rtype = rel.get("relationship_type")
                    ev = rel.get("evidence")
                    md += f"- **{target}** ({rtype})\n"
                    if ev:
                        md += f"  > {ev}\n"
                else:
                    md += f"- {rel}\n"
            md += "\n"

        # Scene stats usually come from index, not just entity payload, but if available:
        if scene_presence := entity_data.get("scene_presence"):
            md += generate_metadata("Scene Count", len(scene_presence))
            md += generate_list("Scene Appearances", scene_presence)

        return md

    def generate_project_markdown(
        self,
        project_name: str,
        project_id: str,
        scenes: list[dict[str, Any]],
        characters: dict[str, dict[str, Any]],
        locations: dict[str, dict[str, Any]],
        props: dict[str, dict[str, Any]],
        script_content: str = "",
        include: list[str] | None = None
    ) -> str:
        if include is None:
            include = ["scenes", "characters", "locations", "props"]

        md = generate_header(project_name, 1)
        md += generate_metadata("Project ID", project_id)
        
        # Summary counts
        if "scenes" in include:
            md += generate_metadata("Total Scenes", len(scenes))
        if "characters" in include:
            md += generate_metadata("Characters", len(characters))
        if "locations" in include:
            md += generate_metadata("Locations", len(locations))
        if "props" in include:
            md += generate_metadata("Props", len(props))
        md += "---\n\n"

        # Script
        if "script" in include and script_content:
            md += generate_header("Screenplay", 1)
            md += f"```fountain\n{script_content}\n```\n\n"
            md += "---\n\n"

        # Scenes
        if "scenes" in include:
            md += generate_header("Scenes", 1)
            for i, scene in enumerate(scenes):
                idx = scene.get("scene_number") or (i + 1)
                md += self.generate_scene_markdown(scene, idx) + "---\n\n"

        # Characters
        if "characters" in include:
            md += generate_header("Characters", 1)
            for char_id, char_data in characters.items():
                md += self.generate_entity_markdown(char_data, char_id, "Character") + "---\n\n"

        # Locations
        if "locations" in include:
            md += generate_header("Locations", 1)
            for loc_id, loc_data in locations.items():
                md += self.generate_entity_markdown(loc_data, loc_id, "Location") + "---\n\n"

        # Props
        if "props" in include:
            md += generate_header("Props", 1)
            for prop_id, prop_data in props.items():
                md += self.generate_entity_markdown(prop_data, prop_id, "Prop") + "---\n\n"

        return md
