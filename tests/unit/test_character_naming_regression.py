
import pytest
from cine_forge.modules.world_building.character_bible_v1.main import _normalize_character_name, _is_plausible_character_name

@pytest.mark.parametrize("input_name, expected", [
    ("THE MARINER", "MARINER"),
    ("THE MARINER (V.O.)", "MARINER"),
    ("ROSE", "ROSE"),
    ("THE SHADOW", "SHADOW"),
    ("THEA", "THEA"), # Should NOT strip because it's part of the name
    ("DAD", "DAD"),
    ("MR. SALVATORI", "MR SALVATORI"),
])
def test_normalize_character_name(input_name, expected):
    assert _normalize_character_name(input_name) == expected

@pytest.mark.parametrize("name, expected", [
    ("MARINER", True),
    ("ROSE", True),
    ("THE MARINER", False), # If normalization fails to strip THE
    ("THE", False),
    ("DAD", True),
    ("MR SALVATORI", True),
    ("THUG", False), # In stopword list
])
def test_is_plausible_character_name(name, expected):
    assert _is_plausible_character_name(name) == expected
