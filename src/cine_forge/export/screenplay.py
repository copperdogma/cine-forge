from typing import Any, Dict, List, Optional
from fpdf import FPDF
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

class ScreenplayPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="in", format="Letter")
        self.set_margins(left=1.5, top=1.0, right=1.0)
        self.set_auto_page_break(auto=True, margin=1.0)
        self.set_font("Courier", size=12)
        self.line_height = 1/6

    def header(self):
        if self.page_no() > 2:
            self.set_y(0.5)
            self.set_x(-1.5)
            self.set_font("Courier", "", 12)
            self.cell(0, 0, f"{self.page_no() - 1}.", align="R")
            self.set_y(1.0)

    def footer(self):
        pass

    def render_title_page(self, title_lines: List[str]):
        """Render title page using only lines provided from the script."""
        if not title_lines:
            return
        self.add_page()
        self.set_font("Courier", "", 12)
        
        # Vertical start (industry standard is approx 1/3 down)
        self.set_y(3.5)
        
        for i, line in enumerate(title_lines):
            if not line.strip():
                self.ln(self.line_height)
                continue
                
            # Bold the first line (usually the title)
            if i == 0:
                self.set_font("Courier", "B", 12)
                self.multi_cell(0, self.line_height, line.strip().upper(), align="C", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Courier", "", 12)
            else:
                self.multi_cell(0, self.line_height, line.strip(), align="C", new_x="LMARGIN", new_y="NEXT")

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

    def _split_pre_scene(self, text: str) -> tuple[List[str], List[str]]:
        """Split pre-scene text into title-page material and teaser/start material."""
        lines = text.splitlines()
        title_lines = []
        teaser_lines = []
        
        script_started = False
        markers = ["TEASER", "ACT ONE", "FADE IN", "EXT.", "INT."]
        
        for line in lines:
            if not script_started:
                upper_line = line.strip().upper()
                # If we hit a script start marker, switch to teaser mode
                if any(m in upper_line for m in markers):
                    script_started = True
                    teaser_lines.append(line)
                else:
                    title_lines.append(line)
            else:
                teaser_lines.append(line)
                
        return title_lines, teaser_lines

    def render_pdf(self, scenes: List[Dict[str, Any]], output_path: str, pre_scene_text: str = "", project_title: str = "Untitled"):
        pdf = ScreenplayPDF()
        
        title_lines, teaser_lines = self._split_pre_scene(pre_scene_text)
        
        # 1. Title Page
        if title_lines:
            pdf.render_title_page(title_lines)
        else:
            # Fallback if no preamble but we have a title
            pdf.render_title_page([project_title])
        
        # 2. Script Start
        pdf.add_page()
        
        if teaser_lines:
            pdf.set_font("Courier", "", 12)
            for line in teaser_lines:
                if not line.strip():
                    pdf.ln(pdf.line_height)
                    continue
                pdf.multi_cell(0, pdf.line_height, self.sanitize(line), align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(pdf.line_height)

        for scene in scenes:
            elements = scene.get("elements", [])
            for elem in elements:
                etype = elem.get("element_type", "action")
                content = self.sanitize(elem.get("content", ""))
                
                if etype == "scene_heading":
                    pdf.ln(pdf.line_height)
                    pdf.set_font("Courier", "B", 12)
                    pdf.set_x(1.5)
                    pdf.multi_cell(0, pdf.line_height, content.upper(), align="L", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(pdf.line_height)
                elif etype == "character":
                    pdf.ln(pdf.line_height)
                    pdf.set_font("Courier", "", 12)
                    pdf.set_x(3.5)
                    pdf.multi_cell(2.0, pdf.line_height, content.upper(), align="L", new_x="LMARGIN", new_y="NEXT")
                elif etype == "parenthetical":
                    pdf.set_font("Courier", "", 12)
                    pdf.set_x(3.0)
                    pdf.multi_cell(2.0, pdf.line_height, f"({content})", align="L", new_x="LMARGIN", new_y="NEXT")
                elif etype == "dialogue":
                    pdf.set_font("Courier", "", 12)
                    pdf.set_x(2.5)
                    pdf.multi_cell(3.5, pdf.line_height, content, align="L", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(pdf.line_height)
                elif etype == "transition":
                    pdf.ln(pdf.line_height)
                    pdf.set_font("Courier", "", 12)
                    pdf.set_x(5.5)
                    pdf.multi_cell(2.0, pdf.line_height, content.upper(), align="L", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(pdf.line_height)
                else: # action, general
                    pdf.set_font("Courier", "", 12)
                    pdf.set_x(1.5)
                    pdf.multi_cell(6.0, pdf.line_height, content, align="L", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(pdf.line_height)
                    
        pdf.output(output_path)

    def render_docx(self, scenes: List[Dict[str, Any]], output_path: str, pre_scene_text: str = "", project_title: str = "Untitled"):
        doc = Document()
        section = doc.sections[0]
        section.left_margin = Inches(1.5)
        section.right_margin = Inches(1.0)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)

        title_lines, teaser_lines = self._split_pre_scene(pre_scene_text)

        # 1. Title Page
        if not title_lines:
            title_lines = [project_title]

        first_text_p = True
        for i, line in enumerate(title_lines):
            p = doc.add_paragraph()
            if first_text_p and line.strip():
                p.paragraph_format.space_before = Inches(2.5)
                first_text_p = False
            
            run = p.add_run(line.strip().upper() if i == 0 else line.strip())
            if i == 0:
                run.bold = True
            run.font.name = 'Courier'
            run.font.size = Pt(12)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
        
        doc.add_page_break()

        # 2. Script Start
        if teaser_lines:
            for line in teaser_lines:
                p = doc.add_paragraph()
                if line.strip():
                    p.add_run(self.sanitize(line))
                p.paragraph_format.space_after = Pt(0)
            doc.add_paragraph()

        for scene in scenes:
            elements = scene.get("elements", [])
            for elem in elements:
                etype = elem.get("element_type", "action")
                content = self.sanitize(elem.get("content", ""))
                
                p = doc.add_paragraph()
                
                if etype == "scene_heading":
                    p.add_run(content.upper()).bold = True
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(12)
                elif etype == "character":
                    p.add_run(content.upper())
                    p.paragraph_format.left_indent = Inches(2.0)
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(0)
                elif etype == "parenthetical":
                    p.add_run(f"({content})")
                    p.paragraph_format.left_indent = Inches(1.5)
                    p.paragraph_format.space_after = Pt(0)
                elif etype == "dialogue":
                    p.add_run(content)
                    p.paragraph_format.left_indent = Inches(1.0)
                    p.paragraph_format.right_indent = Inches(1.5)
                    p.paragraph_format.space_after = Pt(12)
                elif etype == "transition":
                    p.add_run(content.upper())
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    p.paragraph_format.space_before = Pt(12)
                    p.paragraph_format.space_after = Pt(12)
                else: # action
                    p.add_run(content)
                    p.paragraph_format.space_after = Pt(12)
                    
        doc.save(output_path)
