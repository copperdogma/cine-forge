import re
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns
from docx.shared import Inches, Pt


class ScreenplayRenderer:
    def sanitize(self, text: str | Any) -> str:
        if text is None:
            return ""
        s = str(text)
        replacements = {
            "\u2018": "'", "\u2019": "'",
            "\u201c": '"', "\u201d": '"',
            "\u2013": "-", "\u2014": "-",
            "\u2026": "...",
        }
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s.encode("latin-1", "replace").decode("latin-1")

    def _split_pre_scene(self, text: str) -> tuple[list[str], list[str]]:
        lines = text.splitlines()
        title_lines = []
        teaser_lines = []
        script_started = False
        markers = ["TEASER", "ACT ONE", "FADE IN", "EXT.", "INT."]
        
        for line in lines:
            if not script_started:
                upper_line = line.strip().upper()
                if any(m in upper_line for m in markers):
                    script_started = True
                    teaser_lines.append(line)
                else:
                    title_lines.append(line)
            else:
                teaser_lines.append(line)
        return title_lines, teaser_lines

    def render_pdf(
        self, scenes: list[dict[str, Any]], output_path: str, 
        pre_scene_text: str = "", project_title: str = "Untitled"
    ):
        """Render a screenplay PDF using 'afterwriting' by converting scenes to Fountain first."""
        fountain_text = self._scenes_to_fountain(scenes, pre_scene_text, project_title)
        self.render_script_pdf(fountain_text, output_path)

    def render_script_pdf(self, fountain_text: str, output_path: str):
        """Render raw Fountain text directly to PDF using 'afterwriting'."""
        from cine_forge.ai.fdx import export_screenplay_text
        from cine_forge.ai.fountain_validate import normalize_fountain_text
        
        # Ensure strict spacing and metadata cleaning before export
        cleaned_text = normalize_fountain_text(fountain_text)
        
        result = export_screenplay_text(cleaned_text, "pdf")
        if result.success and result.content:
            Path(output_path).write_bytes(result.content)
        else:
            raise RuntimeError(f"afterwriting PDF export failed: {result.issues}")

    def _scenes_to_fountain(
        self,
        scenes: list[dict[str, Any]],
        pre_scene_text: str = "",
        project_title: str = "Untitled",
    ) -> str:
        """Convert a list of scene objects and metadata to a Fountain-formatted string."""
        fountain_lines = []
        title_lines, teaser_lines = self._split_pre_scene(pre_scene_text)
        
        # afterwriting metadata headers
        if not title_lines:
            fountain_lines.append(f"Title: {project_title}")
        else:
            fountain_lines.extend(title_lines)
        
        fountain_lines.append("") # Blank line after metadata
        
        if teaser_lines:
            fountain_lines.extend(teaser_lines)
            fountain_lines.append("")

        for scene in scenes:
            for elem in scene.get("elements", []):
                etype = elem.get("element_type", "action")
                content = (elem.get("content") or "").strip()
                if not content:
                    continue
                    
                if etype == "scene_heading":
                    fountain_lines.append(f"\n{content.upper()}\n")
                elif etype == "character":
                    fountain_lines.append(f"\n{content.upper()}")
                elif etype == "parenthetical":
                    if content.startswith("(") and content.endswith(")"):
                        fountain_lines.append(content)
                    else:
                        fountain_lines.append(f"({content})")
                elif etype == "dialogue":
                    fountain_lines.append(content)
                elif etype == "transition":
                    fountain_lines.append(f"\n{content.upper()}\n")
                else: # action
                    fountain_lines.append(f"\n{content}\n")
        
        return "\n".join(fountain_lines)

    def _add_page_number(self, run):
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(ns.qn('w:fldCharType'), 'begin')
        run._r.append(fldChar1)

        instrText = OxmlElement('w:instrText')
        instrText.set(ns.qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        run._r.append(instrText)

        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(ns.qn('w:fldCharType'), 'end')
        run._r.append(fldChar2)

    def render_docx(
        self, scenes: list[dict[str, Any]], output_path: str, 
        pre_scene_text: str = "", project_title: str = "Untitled"
    ):
        from cine_forge.ai.fountain_validate import normalize_fountain_text
        
        doc = Document()
        
        # Set Global Style
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Courier'
        font.size = Pt(12)
        
        section = doc.sections[0]
        section.left_margin = Inches(1.5)
        section.right_margin = Inches(1.0)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.header_distance = Inches(0.5)

        # Enable different header for the first page (title page)
        section.different_first_page_header_footer = True
        
        # Add page numbers to header (except first page)
        header = section.header
        p_header = header.paragraphs[0]
        p_header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run_header = p_header.add_run()
        run_header.font.name = 'Courier'
        run_header.font.size = Pt(12)
        self._add_page_number(run_header)
        run_header.add_text(".")

        # Normalize pre_scene_text to ensure clean metadata blocks
        normalized_pre = normalize_fountain_text(pre_scene_text)
        title_lines, teaser_lines = self._split_pre_scene(normalized_pre)

        # 1. Title Page
        if not title_lines:
            title_lines = [f"Title: {project_title}"]

        # Push down approx 1/3
        for _ in range(15):
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)

        for i, line in enumerate(title_lines):
            stripped_line = line.strip()
            # Strip Fountain metadata tags: 'Key: Value' -> 'Value'
            pattern = (
                r"^(?:Title|Author|Authors|Source|Credit|Draft date|Contact|Notes|"
                r"Alternate Title|Episode):\s*(.*)"
            )
            match = re.match(pattern, stripped_line, re.IGNORECASE)
            display_text = match.group(1).strip() if match else stripped_line
            
            if not display_text:
                continue

            p = doc.add_paragraph()
            run = p.add_run(display_text.upper() if i == 0 else display_text)
            run.font.name = 'Courier'
            if i == 0:
                run.bold = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
        
        doc.add_page_break()

        # 2. Script Start
        if teaser_lines:
            for line in teaser_lines:
                p = doc.add_paragraph()
                if line.strip():
                    run = p.add_run(self.sanitize(line))
                    run.font.name = 'Courier'
                p.paragraph_format.space_after = Pt(0)
            doc.add_paragraph()

        for scene in scenes:
            for elem in scene.get("elements", []):
                etype = elem.get("element_type", "action")
                content = self.sanitize(elem.get("content", ""))
                p = doc.add_paragraph()
                if etype == "scene_heading":
                    run = p.add_run(content.upper())
                    run.bold = True
                    run.font.name = 'Courier'
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(12)
                elif etype == "character":
                    run = p.add_run(content.upper())
                    run.font.name = 'Courier'
                    p.paragraph_format.left_indent = Inches(2.0)
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(0)
                elif etype == "parenthetical":
                    run = p.add_run(f"({content})")
                    run.font.name = 'Courier'
                    p.paragraph_format.left_indent = Inches(1.5)
                    p.paragraph_format.space_after = Pt(0)
                elif etype == "dialogue":
                    run = p.add_run(content)
                    run.font.name = 'Courier'
                    p.paragraph_format.left_indent = Inches(1.0)
                    p.paragraph_format.right_indent = Inches(1.5)
                    p.paragraph_format.space_after = Pt(12)
                elif etype == "transition":
                    run = p.add_run(content.upper())
                    run.font.name = 'Courier'
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(12)
                else: # action
                    run = p.add_run(content)
                    run.font.name = 'Courier'
                    p.paragraph_format.space_after = Pt(12)
        doc.save(output_path)
