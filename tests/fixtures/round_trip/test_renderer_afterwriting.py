import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from cine_forge.export.screenplay import ScreenplayRenderer


def test_renderer_pdf():
    renderer = ScreenplayRenderer()
    scenes = [
        {
            "scene_number": 1,
            "heading": "EXT. BEACH - DAY",
            "elements": [
                {"element_type": "scene_heading", "content": "EXT. BEACH - DAY"},
                {"element_type": "character", "content": "THE MARINER"},
                {"element_type": "dialogue", "content": "The sea is angry today."}
            ]
        }
    ]
    output_path = "tmp/research/renderer-test.pdf"
    renderer.render_pdf(scenes, output_path, project_title="THE MARINER")
    if Path(output_path).exists():
        print(f"SUCCESS: Rendered PDF at {output_path}")
    else:
        print("FAIL: PDF not rendered")

if __name__ == "__main__":
    test_renderer_pdf()
