import json
import re
from pathlib import Path


def extract_metadata(fountain_path):
    text = fountain_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    
    scene_headings = []
    characters = set()
    total_words = len(text.split())
    dialogue_words = 0
    
    current_element = None # Action, Character, Dialogue, etc.
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_element = None
            continue
            
        # Very simple heuristic for ground truth extraction
        if re.match(r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)", stripped.upper()):
            scene_headings.append(stripped.upper())
            current_element = "Heading"
        elif (
            stripped.upper() == stripped
            and any(c.isalpha() for c in stripped)
            and not stripped.endswith(":")
            and len(stripped) < 40
        ):
             # Likely character
             characters.add(stripped.split("(")[0].strip().upper())
             current_element = "Character"
        elif current_element == "Character" or current_element == "Dialogue":
             if not (stripped.startswith("(") and stripped.endswith(")")):
                 dialogue_words += len(stripped.split())
                 current_element = "Dialogue"
    
    return {
        "scene_count": len(scene_headings),
        "scene_headings": scene_headings,
        "characters": sorted(list(characters)),
        "total_word_count": total_words,
        "dialogue_word_count": dialogue_words
    }

if __name__ == "__main__":
    for folder in Path("tests/fixtures/round_trip").iterdir():
        if not folder.is_dir():
            continue
        fountain_file = next(folder.glob("*.fountain"), None)
        if fountain_file:
            print(f"Extracting {fountain_file}")
            meta = extract_metadata(fountain_file)
            output_file = folder / f"{fountain_file.stem}-golden.json"
            output_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
