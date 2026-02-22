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
        if self.page_no() > 1:
            self.set_y(0.5)
            self.set_x(-1.5)
            self.set_font("Courier", "", 12)
            self.cell(0, 0, f"{self.page_no()}.", align="R")
            self.set_y(1.0)

    def footer(self):
        pass

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

    def render_pdf(self, scenes: List[Dict[str, Any]], output_path: str, pre_scene_text: str = ""):
        pdf = ScreenplayPDF()
        pdf.add_page()
        
        # Render pre-scene content (Title, Teaser, etc.)
        if pre_scene_text:
            pdf.set_font("Courier", "", 12)
            lines = pre_scene_text.splitlines()
            for line in lines:
                if not line.strip():
                    pdf.ln(pdf.line_height)
                    continue
                # Simple heuristic: if uppercase and short, maybe it's a sub-header or title
                # For now, just render as action text (full width)
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

    def render_docx(self, scenes: List[Dict[str, Any]], output_path: str, pre_scene_text: str = ""):
        doc = Document()
        section = doc.sections[0]
        section.left_margin = Inches(1.5)
        section.right_margin = Inches(1.0)
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)

        style = doc.styles['Normal']
        font = style.font
        font.name = 'Courier'
        font.size = Pt(12)

        # Render pre-scene content
        if pre_scene_text:
            lines = pre_scene_text.splitlines()
            for line in lines:
                p = doc.add_paragraph()
                if line.strip():
                    p.add_run(self.sanitize(line))
                p.paragraph_format.space_after = Pt(0)
            doc.add_paragraph() # Extra space after pre-scene content

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
