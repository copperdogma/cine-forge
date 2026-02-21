from typing import Any, Dict, List, Optional
from fpdf import FPDF

class PDFExporter(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 10)
        # self.cell(0, 10, "CineForge Export", align="R", new_x="LMARGIN", new_y="NEXT")

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

class PDFGenerator:
    def format_entity_name(self, entity_id: str) -> str:
        if not entity_id:
            return "Unknown"
        return entity_id.replace("_", " ").title()

    def sanitize(self, text: str | Any) -> str:
        if text is None:
            return ""
        s = str(text)
        # Replace common Windows-1252 / Unicode chars with Latin-1 equivalents
        replacements = {
            "\u2018": "'", "\u2019": "'",  # Smart quotes
            "\u201c": '"', "\u201d": '"',  # Smart double quotes
            "\u2013": "-", "\u2014": "-",  # Dashes
            "\u2026": "...",               # Ellipsis
        }
        for k, v in replacements.items():
            s = s.replace(k, v)
        # Strip anything else that isn't latin-1 compatible to prevent crash
        return s.encode("latin-1", "replace").decode("latin-1")

    def generate_project_pdf(
        self,
        project_name: str,
        project_id: str,
        scenes: List[Dict[str, Any]],
        characters: Dict[str, Dict[str, Any]],
        locations: Dict[str, Dict[str, Any]],
        props: Dict[str, Dict[str, Any]],
        output_path: str
    ):
        pdf = PDFExporter()
        pdf.add_page()
        
        # Title Page
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 20, self.sanitize(project_name), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 14)
        pdf.cell(0, 10, self.sanitize(f"Project ID: {project_id}"), align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(20)

        # Scenes Table
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "Scenes", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 10)
        
        scene_rows = []
        scene_rows.append(["#", "Slugline", "Time", "Summary"])
        for i, scene in enumerate(scenes):
            idx = str(scene.get("scene_number") or (i + 1))
            heading = scene.get("heading") or "Unknown"
            location = scene.get("location") or ""
            int_ext = scene.get("int_ext") or ""
            slug = f"{int_ext} {location}"
            time = scene.get("time_of_day") or ""
            summary = (scene.get("summary") or "")[:100] # Truncate for table
            
            scene_rows.append([
                self.sanitize(idx),
                self.sanitize(slug),
                self.sanitize(time),
                self.sanitize(summary)
            ])

        with pdf.table() as table:
            for row in scene_rows:
                row_cells = table.row()
                for item in row:
                    row_cells.cell(item)
        
        pdf.add_page()

        # Characters
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "Characters", new_x="LMARGIN", new_y="NEXT")
        
        char_rows = [["Name", "Scenes", "Description"]]
        for char_id, char_data in characters.items():
            name = self.format_entity_name(char_id)
            count = str(len(char_data.get("scene_presence") or []))
            desc = (char_data.get("description") or "")[:100]
            char_rows.append([
                self.sanitize(name),
                self.sanitize(count),
                self.sanitize(desc)
            ])

        with pdf.table() as table:
            for row in char_rows:
                row_cells = table.row()
                for item in row:
                    row_cells.cell(item)

        pdf.add_page()

        # Locations
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "Locations", new_x="LMARGIN", new_y="NEXT")
        
        loc_rows = [["Name", "Scenes", "Description"]]
        for loc_id, loc_data in locations.items():
            name = self.format_entity_name(loc_id)
            count = str(len(loc_data.get("scene_presence") or []))
            desc = (loc_data.get("description") or "")[:100]
            loc_rows.append([
                self.sanitize(name),
                self.sanitize(count),
                self.sanitize(desc)
            ])

        with pdf.table() as table:
            for row in loc_rows:
                row_cells = table.row()
                for item in row:
                    row_cells.cell(item)

        pdf.output(output_path)

    def generate_call_sheet(
        self,
        project_name: str,
        scenes: List[Dict[str, Any]],
        output_path: str
    ):
        pdf = PDFExporter()
        pdf.add_page()
        
        pdf.set_font("helvetica", "B", 22)
        pdf.cell(0, 15, "CALL SHEET", align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(30, 8, "Production:", align="L")
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 8, self.sanitize(project_name), align="L", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)

        # Table
        rows = [["Scene", "Set", "Desc", "Cast", "Pages"]]
        for i, scene in enumerate(scenes):
            idx = str(scene.get("scene_number") or (i + 1))
            location = scene.get("location") or ""
            int_ext = scene.get("int_ext") or ""
            slug = f"{int_ext} {location}"
            summary = (scene.get("summary") or "")[:50]
            cast = "TBD" # Needs more complex logic to list cast names
            pages = "1/8"
            rows.append([
                self.sanitize(idx),
                self.sanitize(slug),
                self.sanitize(summary),
                cast,
                pages
            ])

        with pdf.table() as table:
            for row in rows:
                row_cells = table.row()
                for item in row:
                    row_cells.cell(item)

        pdf.output(output_path)
