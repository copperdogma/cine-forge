import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath("src"))

from cine_forge.ai.fdx import export_screenplay_text


def test_afterwriting_pdf():
    text = """
Title: THE MARINER
Author: CAM
    
ACT ONE

EXT. THE MARINER'S HUT - DAY

THE MARINER (80s, grizzled) sits by the fire. He drinks some soup.

MARINER
It's going to be a long day.

FADE OUT:
"""
    result = export_screenplay_text(text, "pdf")
    if result.success:
        print(f"PDF Generated successfully via {result.backend}")
        output_file = Path("tmp/research/api-test.pdf")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_bytes(result.content)
        print(f"Wrote to {output_file}")
    else:
        print(f"FAIL: {result.issues}")

if __name__ == "__main__":
    test_afterwriting_pdf()
