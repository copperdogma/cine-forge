from typing import Any

from fpdf import FPDF


class PDFExporter(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("helvetica", "I", 8)
            self.cell(
                0, 10, "CineForge Project Report", 
                align="R", new_x="LMARGIN", new_y="NEXT"
            )

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
        replacements = {
            "\u2018": "'", "\u2019": "'",  # Smart quotes
            "\u201c": '"', "\u201d": '"',  # Smart double quotes
            "\u2013": "-", "\u2014": "-",  # Dashes
            "\u2026": "...",               # Ellipsis
        }
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s.encode("latin-1", "replace").decode("latin-1")

    def generate_project_pdf(
        self,
        project_name: str,
        project_id: str,
        scenes: list[dict[str, Any]],
        characters: dict[str, dict[str, Any]],
        locations: dict[str, dict[str, Any]],
        props: dict[str, dict[str, Any]],
        output_path: str
    ):
        pdf = PDFExporter()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # --- Title Page ---
        pdf.ln(60)
        # Use multi_cell for title to allow wrapping if it's very long
        pdf.set_font("helvetica", "B", 28)
        pdf.multi_cell(
            0, 15, self.sanitize(project_name), 
            align="C", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.ln(5)
        pdf.set_font("helvetica", "", 16)
        pdf.cell(
            0, 10, "Project Analysis Report", 
            align="C", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.ln(5)
        pdf.set_font("helvetica", "I", 12)
        pdf.cell(
            0, 10, f"Project ID: {project_id}", 
            align="C", new_x="LMARGIN", new_y="NEXT"
        )
        
        pdf.add_page()

        # --- Scenes Summary ---
        pdf.set_font("helvetica", "B", 20)
        pdf.cell(0, 15, "Scenes Overview", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 10)
        
        scene_rows = [["#", "Heading", "Time", "Summary"]]
        for i, scene in enumerate(scenes):
            idx = str(scene.get("scene_number") or (i + 1))
            heading = scene.get("heading") or "Unknown"
            time = scene.get("time_of_day") or ""
            summary = (scene.get("summary") or "")[:80] + "..."
            scene_rows.append([
                self.sanitize(idx), 
                self.sanitize(heading), 
                self.sanitize(time), 
                self.sanitize(summary)
            ])

        with pdf.table(col_widths=(10, 60, 30, 90)) as table:
            for row in scene_rows:
                row_cells = table.row()
                for item in row:
                    row_cells.cell(item)
        
        # --- Characters Detail ---
        if characters:
            pdf.add_page()
            pdf.set_font("helvetica", "B", 20)
            pdf.cell(0, 15, "Characters", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)

            for char_id, char_data in characters.items():
                name = char_data.get("name") or self.format_entity_name(char_id)
                pdf.set_font("helvetica", "B", 14)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(0, 10, self.sanitize(name), fill=True, new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(30, 7, "Role:")
                pdf.set_font("helvetica", "", 10)
                pdf.cell(
                    0, 7, 
                    self.sanitize(char_data.get("narrative_role") or "Unknown"), 
                    new_x="LMARGIN", new_y="NEXT"
                )
                
                if aliases := char_data.get("aliases"):
                    pdf.set_font("helvetica", "B", 10)
                    pdf.cell(30, 7, "Aliases:")
                    pdf.set_font("helvetica", "", 10)
                    pdf.cell(
                        0, 7, self.sanitize(", ".join(aliases)), 
                        new_x="LMARGIN", new_y="NEXT"
                    )

                pdf.ln(2)
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 7, "Description:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 10)
                desc = char_data.get("description") or "No description available."
                pdf.multi_cell(
                    0, 5, self.sanitize(desc), 
                    new_x="LMARGIN", new_y="NEXT"
                )
                
                # Traits
                if traits := char_data.get("inferred_traits"):
                    pdf.ln(2)
                    pdf.set_font("helvetica", "B", 10)
                    pdf.cell(0, 7, "Inferred Traits:", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 9)
                    for t in traits:
                        if isinstance(t, dict):
                            txt = f"- {t.get('trait')}: {t.get('value')} ({t.get('rationale')})"
                            pdf.multi_cell(0, 4, self.sanitize(txt), new_x="LMARGIN", new_y="NEXT")
                
                pdf.ln(5)

        # --- Locations Detail ---
        if locations:
            pdf.add_page()
            pdf.set_font("helvetica", "B", 20)
            pdf.cell(0, 15, "Locations", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)

            for loc_id, loc_data in locations.items():
                name = loc_data.get("name") or self.format_entity_name(loc_id)
                pdf.set_font("helvetica", "B", 14)
                pdf.set_fill_color(240, 240, 240)
                pdf.cell(0, 10, self.sanitize(name), fill=True, new_x="LMARGIN", new_y="NEXT")
                
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 7, "Significance:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 10)
                sig = loc_data.get("narrative_significance") or "No detail available."
                pdf.multi_cell(
                    0, 5, self.sanitize(sig), 
                    new_x="LMARGIN", new_y="NEXT"
                )
                
                if physical := loc_data.get("physical_traits"):
                    pdf.ln(2)
                    pdf.set_font("helvetica", "B", 10)
                    pdf.cell(0, 7, "Physical Detail:", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 9)
                    for p in physical:
                        pdf.multi_cell(0, 4, self.sanitize(f"- {p}"), new_x="LMARGIN", new_y="NEXT")
                
                pdf.ln(5)

        pdf.output(output_path)

    def generate_call_sheet(
        self,
        project_name: str,
        scenes: list[dict[str, Any]],
        output_path: str
    ):
        pdf = PDFExporter()
        pdf.add_page()
        
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 15, "CALL SHEET", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(30, 8, "Production:")
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 8, self.sanitize(project_name), new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)

        rows = [["Scene", "Set", "Desc", "Cast", "Pages"]]
        for i, scene in enumerate(scenes):
            idx = str(scene.get("scene_number") or (i + 1))
            heading = scene.get("heading") or "Unknown"
            summary = (scene.get("summary") or "")[:50]
            cast = ", ".join(scene.get("characters_present") or [])[:30]
            pages = "1/8"
            rows.append([
                self.sanitize(idx), 
                self.sanitize(heading), 
                self.sanitize(summary), 
                self.sanitize(cast), 
                pages
            ])

        with pdf.table(col_widths=(15, 60, 60, 40, 15)) as table:
            for row in rows:
                row_cells = table.row()
                for item in row:
                    row_cells.cell(item)

        pdf.output(output_path)
