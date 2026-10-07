from pathlib import Path

import pytest

from cine_forge.modules.visualization.storyboard_v1.generation import (
    _resolve_storyboard_image_request,
)
from cine_forge.modules.visualization.storyboard_v1.reference_limits import (
    NANO_BANANA_MODEL,
    reference_limit_note,
)


@pytest.mark.unit
@pytest.mark.parametrize("uses_template,expected_count", [(False, 14), (True, 13)])
def test_storyboard_caps_direct_references_and_provenance(
    tmp_path: Path, uses_template: bool, expected_count: int
) -> None:
    refs = [f"reference_{index}.jpg" for index in range(20)]
    template = tmp_path / "grid_template.jpg" if uses_template else None
    model, paths, direct = _resolve_storyboard_image_request(
        project_dir=tmp_path,
        image_model=NANO_BANANA_MODEL,
        reference_images=refs,
        template_path=template,
    )
    assert model == NANO_BANANA_MODEL
    assert len(paths) == 14
    assert direct == refs[:expected_count]
    if template:
        assert paths[0] == str(template)
    assert paths[int(uses_template):] == [str(tmp_path / ref) for ref in direct]
    notes = reference_limit_note(model, refs, direct, "Scene action")
    assert notes is not None
    assert notes.startswith("Scene action\nReference image limit:")
    assert refs[expected_count] in notes
    assert refs[expected_count - 1] not in notes


@pytest.mark.unit
def test_explicit_openai_storyboard_reference_selection_is_preserved(tmp_path: Path) -> None:
    refs = [f"reference_{index}.jpg" for index in range(15)]
    model, paths, direct = _resolve_storyboard_image_request(
        project_dir=tmp_path, image_model="gpt-image-2", reference_images=refs
    )
    assert model == "gpt-image-2"
    assert len(paths) == 15
    assert direct == refs
    assert reference_limit_note(model, refs, direct, "Action") == "Action"
