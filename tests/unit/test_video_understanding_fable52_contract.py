"""Offline qualification of the approved Fable wire controls, no inference."""
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'benchmarks/providers'))
provider = importlib.import_module('video_understanding_provider')
pytestmark = pytest.mark.unit


def test_exact_fable_xhigh_wire_and_fast_price_exclusion(monkeypatch, tmp_path):
    def capture(url, **kwargs):
        body = kwargs['body']
        assert body['model'] == 'anthropic/claude-fable-5.2'
        assert body['reasoning'] == {'effort': 'xhigh'}
        assert body['max_completion_tokens'] == 32768
        assert body['provider'] == {
            'order': ['Anthropic'], 'allow_fallbacks': False,
            'require_parameters': True, 'max_price': {'prompt': 8, 'completion': 40},
        }
        schema = body['response_format']['json_schema']
        assert schema['strict'] and len(schema['schema']['required']) == 13
        assert sum(x['type'] == 'image_url' for x in body['messages'][0]['content']) == 5
        raise RuntimeError('Captured without inference')
    monkeypatch.setattr(provider, '_request_json', capture)
    monkeypatch.setattr(provider, '_require_env', lambda _: 'offline-only')
    with pytest.raises(RuntimeError, match='Captured without inference'):
        provider._call_openrouter_strict(
            model='anthropic/claude-fable-5.2', user_text='Synthetic source',
            frames=[{'mime_type': 'image/jpeg', 'base64': 'offline'}] * 5,
            max_tokens=32768, upstream_provider='Anthropic', reasoning_effort='xhigh',
            raw_output_path=tmp_path / 'raw.json', timeout_seconds=360,
            max_price={'prompt': 8, 'completion': 40},
        )


def test_other_routes_do_not_implicitly_gain_xhigh(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail('Undeclared reasoning reached transport')
    monkeypatch.setattr(provider, '_request_json', forbidden)
    with pytest.raises(RuntimeError, match='Unsupported'):
        provider._call_openrouter_strict(
            model='tencent/hy4', user_text='Synthetic',
            frames=[{'mime_type': 'image/jpeg', 'base64': 'offline'}] * 5,
            max_tokens=32768, upstream_provider='Tencent', reasoning_effort='xhigh',
            raw_output_path=tmp_path / 'raw.json', timeout_seconds=360,
        )


def test_native_fable_uses_same_contract_and_bills_total_output(monkeypatch, tmp_path):
    import json
    saved = ROOT / 'docs/evals/evidence/story-235-hy420261105/subject-sol-vfp_active_001.json'
    output = json.loads(saved.read_text())['response']['output']
    captured = {}
    def transport(url, **kwargs):
        captured.update(url=url, **kwargs)
        return {'id': 'msg_offline', 'type': 'message', 'model': 'claude-fable-5-2',
                'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': output}],
                'usage': {'input_tokens': 2000, 'output_tokens': 1500,
                          'cache_read_input_tokens': 0, 'cache_creation_input_tokens': 0}}
    monkeypatch.setattr(provider, '_request_json', transport)
    monkeypatch.setattr(provider, '_require_env', lambda _: 'offline-only')
    monkeypatch.setattr(provider, 'REPO_ROOT', tmp_path)
    result = provider._call_anthropic(
        model='claude-fable-5-2', user_text='Synthetic source',
        frames=[{'mime_type': 'image/jpeg', 'base64': 'offline'}] * 5,
        max_tokens=32768, temperature=None, effort='xhigh',
        raw_output_path=tmp_path / 'raw.json',
    )
    body = captured['body']
    assert captured['timeout_seconds'] == 360
    assert body['output_config']['effort'] == 'xhigh'
    assert len(body['output_config']['format']['schema']['required']) == 13
    assert body['max_tokens'] == 32768 and 'temperature' not in body
    assert sum(p['type'] == 'image' for p in body['messages'][0]['content']) == 5
    assert result['reported_cost_usd'] == pytest.approx(.076)
    assert result['raw']['model'] == 'claude-fable-5-2'
    assert json.loads((tmp_path / 'raw.json').read_text())['stop_reason'] == 'end_turn'
