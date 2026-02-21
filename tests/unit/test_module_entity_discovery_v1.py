import pytest
from cine_forge.modules.world_building.entity_discovery_v1.main import run_module

def test_entity_discovery_refine_mode_bootstraps():
    """Verify that discovery bootstraps from existing bibles."""
    inputs = {
        "canonical_script": {
            "script_text": "INT. OFFICE - DAY\n\nAbe enters. He carries a RARE COIN.",
            "title": "Test"
        },
        "character_bible": [
            {"name": "ABE"}
        ],
        "prop_bible": [
            {"canonical_name": "GOLD COIN"}
        ]
    }
    
    params = {
        "discovery_model": "mock",
        "enable_locations": False
    }
    
    import cine_forge.modules.world_building.entity_discovery_v1.main as discovery_main
    from unittest.mock import MagicMock
    
    original_call = discovery_main.call_llm
    mock_call = MagicMock()
    
    mock_call.side_effect = [
        (MagicMock(items=["ABE"]), {"estimated_cost_usd": 0.01}), 
        (MagicMock(items=["GOLD COIN"]), {"estimated_cost_usd": 0.01}),
    ]
    
    discovery_main.call_llm = mock_call
    
    try:
        result = run_module(inputs, params, {})
        
        discovery_data = result["artifacts"][0]["data"]
        assert "ABE" in discovery_data["characters"]
        assert "GOLD COIN" in discovery_data["props"]
        
        char_prompt = mock_call.call_args_list[0][1]["prompt"]
        assert "ABE" in char_prompt
        
        prop_prompt = mock_call.call_args_list[1][1]["prompt"]
        assert "GOLD COIN" in prop_prompt
        
    finally:
        discovery_main.call_llm = original_call
