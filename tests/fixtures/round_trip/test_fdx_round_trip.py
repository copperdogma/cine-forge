import os
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# Add src to path
sys.path.append(os.path.abspath("src"))

from cine_forge.ai.fdx import detect_and_convert_fdx, export_screenplay_text


def test_fdx_round_trip(fdx_path):
    print(f"Testing FDX Round Trip: {fdx_path}")
    content = fdx_path.read_text(encoding="utf-8")
    
    # FDX -> Fountain
    result = detect_and_convert_fdx(content)
    if not result.is_fdx:
        print(f"  Error: {fdx_path} is not recognized as FDX")
        return False
    
    fountain_text = result.fountain_text
    
    # Fountain -> FDX
    export_result = export_screenplay_text(fountain_text, "fdx")
    if not export_result.success:
        print(f"  Error: Fountain -> FDX export failed: {export_result.issues}")
        return False
    
    new_fdx_content = export_result.content.decode("utf-8")
    
    # Structural Compare (Scene Headings, Characters)
    def extract_structure(fdx_xml):
        root = ET.fromstring(fdx_xml)
        paras = []
        for p in root.iter():
            if p.tag.endswith("Paragraph"):
                ptype = p.attrib.get("Type", "Action")
                text = "".join(p.itertext()).strip().upper()
                if text:
                    paras.append((ptype, text))
        return paras

    old_struct = extract_structure(content)
    new_struct = extract_structure(new_fdx_content)
    
    # For now, let's just count Scene Headings and Characters
    old_headings = [p[1] for p in old_struct if p[0] == "Scene Heading"]
    new_headings = [p[1] for p in new_struct if p[0] == "Scene Heading"]
    
    def normalize_char(name):
        # Remove (CONT'D), (O.S.), (V.O.) and whitespace
        n = name.split("(")[0].strip().upper()
        return " ".join(n.split())

    old_chars = set(normalize_char(p[1]) for p in old_struct if p[0] == "Character")
    new_chars = set(normalize_char(p[1]) for p in new_struct if p[0] == "Character")
    
    print(f"  Headings: {len(old_headings)} (old) vs {len(new_headings)} (new)")
    print(f"  Characters: {len(old_chars)} (old) vs {len(new_chars)} (new)")
    
    if len(old_headings) != len(new_headings):
        print("  FAIL: Heading count mismatch")
        return False
    
    if old_chars != new_chars:
        print("  FAIL: Character set mismatch")
        print(f"  Missing in new: {old_chars - new_chars}")
        print(f"  Extra in new: {new_chars - old_chars}")
        return False
        
    print("  SUCCESS: FDX Round Trip matches core structure.")
    return True

if __name__ == "__main__":
    success = True
    for folder in Path("tests/fixtures/round_trip").iterdir():
        if not folder.is_dir():
            continue
        fdx_file = next(folder.glob("*.fdx"), None)
        if fdx_file:
            if not test_fdx_round_trip(fdx_file):
                success = False
    
    if not success:
        sys.exit(1)
