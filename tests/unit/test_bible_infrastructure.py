from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas import ArtifactMetadata


@pytest.mark.unit
def test_artifact_store_save_load_bible_entry(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    metadata = ArtifactMetadata(
        intent="test",
        rationale="test",
        confidence=1.0,
        source="human",
    )
    
    files = [
        {
            "filename": "master_v1.json",
            "purpose": "master_definition",
            "version": 1,
            "provenance": "system",
        }
    ]
    data_files = {"master_v1.json": '{"name": "ARIA"}'}
    
    ref = store.save_bible_entry(
        entity_type="character",
        entity_id="aria",
        display_name="Aria",
        files=files,
        data_files=data_files,
        metadata=metadata,
    )
    
    assert ref.artifact_type == "bible_manifest"
    assert ref.entity_id == "character_aria"
    assert ref.version == 1
    assert (tmp_path / ref.path).exists()
    
    # Load
    manifest, loaded_metadata = store.load_bible_entry(ref)
    assert manifest.entity_type == "character"
    assert manifest.entity_id == "aria"
    assert manifest.display_name == "Aria"
    assert len(manifest.files) == 1
    assert manifest.files[0].filename == "master_v1.json"
    
    # Check data file
    data_file_path = tmp_path / "artifacts" / "bibles" / "character_aria" / "master_v1.json"
    assert data_file_path.exists()
    assert data_file_path.read_text() == '{"name": "ARIA"}'


@pytest.mark.unit
def test_artifact_store_list_bible_entries(tmp_path: Path) -> None:
    store = ArtifactStore(project_dir=tmp_path)
    metadata = ArtifactMetadata(
        intent="test",
        rationale="test",
        confidence=1.0,
        source="human",
    )
    
    store.save_bible_entry("character", "aria", "Aria", [], {}, metadata)
    store.save_bible_entry("character", "noah", "Noah", [], {}, metadata)
    store.save_bible_entry("location", "studio", "Studio", [], {}, metadata)
    
    chars = store.list_bible_entries("character")
    assert sorted(chars) == ["aria", "noah"]
    
    locs = store.list_bible_entries("location")
    assert locs == ["studio"]
