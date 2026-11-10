"""Physical-budget and full-consumer checks without inference."""
import copy
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'benchmarks/scripts'))
from whole_story_workspace_contract import (  # noqa: E402
    consumer_payload,
    subject_payload,
    validate_bundle,
)
from whole_story_workspace_meter import AdmissionDenied, PhysicalMeter  # noqa: E402

pytestmark = pytest.mark.unit


def request():
    return urllib.request.Request('https://api.anthropic.com/v1/messages',
        data=json.dumps({'model': 'claude-fable-5-2', 'max_tokens': 65536,
                         'messages': [{'role': 'user', 'content': 'authored'}]}).encode(),
        headers={'x-api-key': 'offline-only'})


def test_budget_denial_sends_nothing_and_blocks_later_fallback(tmp_path):
    meter = PhysicalMeter(tmp_path, cap='1')
    meter.count_native = lambda *a: 1000
    meter.original = lambda *a, **kw: pytest.fail('Denied call reached network')
    with pytest.raises(AdmissionDenied, match='Hard USD20'):
        meter.urlopen(request())
    assert not meter.rows and meter.exhausted
    with pytest.raises(AdmissionDenied, match='already halted'):
        meter.urlopen(request())


def test_unknown_http_exposure_keeps_full_reservation_and_raw_error(tmp_path):
    meter = PhysicalMeter(tmp_path)
    meter.count_native = lambda *a: 1000
    def fail(*a, **kw):
        raise urllib.error.HTTPError('synthetic', 400, 'synthetic', {}, io.BytesIO(b'bad grammar'))
    meter.original = fail
    with pytest.raises(urllib.error.HTTPError):
        meter.urlopen(request())
    row = meter.rows[0]
    assert row['state'] == 'unknown-exposure-held'
    assert row['accounted_usd'] == row['reservation_usd']
    assert (tmp_path / row['name'] / 'error-body.txt').read_bytes() == b'bad grammar'


def test_usage_settlement_persists_complete_envelope_before_return(tmp_path):
    meter = PhysicalMeter(tmp_path)
    meter.count_native = lambda *a: 1000
    body = {'model': 'claude-fable-5-2', 'id': 'offline',
            'usage': {'input_tokens': 1000, 'output_tokens': 500,
                      'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}}
    meter.original = lambda *a, **kw: io.BytesIO(json.dumps(body).encode())
    response = meter.urlopen(request())
    row = meter.rows[0]
    assert row['state'] == 'settled-usage-estimate'
    assert float(row['accounted_usd']) == pytest.approx(.028)
    assert json.loads((tmp_path / row['name'] / 'response.json').read_text()) == body
    assert json.load(response) == body


def test_complete_exemplar_semantic_projection_roundtrip():
    root = ROOT / 'benchmarks/fixtures/whole_story_workspace_v1'
    payload = json.loads((root / 'open_frequency-consumer-example.json').read_text())
    source = (root / 'open_frequency.fountain').read_bytes()
    assert consumer_payload(subject_payload(payload), source_bytes=source,
                            source_filename='open_frequency.fountain') == payload
    bad = copy.deepcopy(payload)
    bad['canonical_script']['script_text'] += '\nInvented source.'
    bad['canonical_script']['line_count'] = len(bad['canonical_script']['script_text'].splitlines())
    with pytest.raises(ValueError, match='preserve exact original'):
        validate_bundle(bad, source_bytes=source)
    bad = copy.deepcopy(payload)
    del bad['characters'][0]['relationships']
    with pytest.raises(ValueError):
        validate_bundle(bad, source_bytes=source)


@pytest.mark.parametrize('fault', ['negative', 'boolean', 'wrong_model', 'premium', 'too_many'])
def test_bad_usage_identity_or_tier_retains_full_unknown_reservation(tmp_path, fault):
    meter = PhysicalMeter(tmp_path)
    meter.count_native = lambda *a: 1000
    raw = {'model': 'claude-fable-5-2', 'id': 'offline',
           'usage': {'input_tokens': 1000, 'output_tokens': 500}}
    if fault == 'negative':
        raw['usage']['cache_read_input_tokens'] = -1
    elif fault == 'boolean':
        raw['usage']['output_tokens'] = True
    elif fault == 'wrong_model':
        raw['model'] = 'claude-other'
    elif fault == 'premium':
        raw['usage']['speed'] = 'fast'
    else:
        raw['usage']['output_tokens'] = 65537
    meter.original = lambda *a, **kw: io.BytesIO(json.dumps(raw).encode())
    req = request()
    with pytest.raises(AdmissionDenied):
        meter.urlopen(req)
    row = meter.rows[0]
    assert row['state'] == 'unknown-exposure-held'
    assert row['accounted_usd'] == row['reservation_usd']
    assert (tmp_path / row['name'] / 'request.json').read_bytes() == req.data
    assert json.loads((tmp_path / row['name'] / 'response.json').read_text()) == raw


def test_stream_documented_events_accumulate_text_thinking_and_cumulative_usage(tmp_path):
    from recover_whole_story_workspace_stream import read_sse
    events = [
        {'type': 'message_start', 'message': {'model': 'claude-fable-5-2', 'content': [],
            'usage': {'input_tokens': 100, 'output_tokens': 1}, 'stop_reason': None}},
        {'type': 'ping'},
        {'type': 'content_block_start', 'index': 0,
         'content_block': {'type': 'thinking', 'thinking': '', 'signature': ''}},
        {'type': 'content_block_delta', 'index': 0,
         'delta': {'type': 'thinking_delta', 'thinking': ''}},
        {'type': 'content_block_delta', 'index': 0,
         'delta': {'type': 'signature_delta', 'signature': 'synthetic'}},
        {'type': 'content_block_stop', 'index': 0},
        {'type': 'content_block_start', 'index': 1,
         'content_block': {'type': 'text', 'text': ''}},
        {'type': 'content_block_delta', 'index': 1,
         'delta': {'type': 'text_delta', 'text': '{"bundle_json":'}},
        {'type': 'content_block_delta', 'index': 1,
         'delta': {'type': 'text_delta', 'text': '"{}"}'}},
        {'type': 'content_block_stop', 'index': 1},
        {'type': 'message_delta', 'delta': {'stop_reason': 'end_turn'},
         'usage': {'output_tokens': 12}},
        {'type': 'message_stop'},
    ]
    raw = b''.join(f'event: {e["type"]}\ndata: {json.dumps(e)}\n\n'.encode() for e in events)
    path = tmp_path / 'response.sse'
    result = read_sse(io.BytesIO(raw), path)
    assert path.read_bytes() == raw
    assert result['usage'] == {'input_tokens': 100, 'output_tokens': 12}
    assert result['content'][0]['signature'] == 'synthetic'
    assert json.loads(result['content'][1]['text']) == {'bundle_json': '{}'}
    with pytest.raises(AssertionError, match='terminal'):
        read_sse(io.BytesIO(raw.rsplit(b'event: message_stop', 1)[0]), tmp_path / 'partial.sse')
    bad = b'event: error\ndata: {"type":"error","error":{"type":"overloaded_error"}}\n\n'
    with pytest.raises(RuntimeError, match='SSE error'):
        read_sse(io.BytesIO(bad), tmp_path / 'error.sse')
    assert (tmp_path / 'error.sse').read_bytes() == bad


def test_pinned_control_discovery_runtime_haiku_overrides_recipe_gemini(monkeypatch):
    import importlib

    from full_script_throughput_eval import _build_runtime_params
    module = importlib.import_module('cine_forge.modules.world_building.entity_discovery_v1.main')
    models = []
    def fake(**kwargs):
        models.append(kwargs['model'])
        return module._IncrementalDiscovery(items=[]), {'input_tokens': 0, 'output_tokens': 0,
                                                        'estimated_cost_usd': 0}
    monkeypatch.setattr(module, 'call_llm', fake)
    module.run_module(
        inputs={'normalize': {'script_text': 'Authored source', 'title': 'Authored'},
                'breakdown_scenes': {'unique_characters': ['ARIA'], 'entries': []}},
        params={'discovery_model': 'gemini-2.5-flash-lite'},
        context={'runtime_params': _build_runtime_params(input_file=Path('authored.fountain'))},
    )
    assert models and set(models) == {'claude-haiku-4-5-20251001'}


def test_unplanned_url_never_logs_query_credentials_or_userinfo(tmp_path):
    from whole_story_workspace_control_meter import PhysicalMeter, safe_url
    fake_secret = 'SYNTHETIC_PRIVATE_KEY'
    url = ('https://fakeuser:fakepassword@generativelanguage.googleapis.com/v1beta/'
           f'models/gemini-2.5-flash-lite:generateContent?key={fake_secret}#private')
    meter = PhysicalMeter(tmp_path)
    meter.original = lambda *a, **kw: pytest.fail('Unplanned Google request dispatched')
    with pytest.raises(AdmissionDenied) as caught:
        meter.urlopen(urllib.request.Request(url, data=b'{}'))
    text = str(caught.value)
    assert fake_secret not in text and 'fakepassword' not in text and '?' not in text
    assert safe_url(url).endswith('gemini-2.5-flash-lite:generateContent')
    assert not meter.rows and meter.exhausted
    assert all(fake_secret not in p.read_text() for p in tmp_path.rglob('*') if p.is_file())


def test_closed_experiment_never_replays_a_failed_qualification(tmp_path):
    root = tmp_path / 'physical-calls'
    (tmp_path / 'CLOSED.json').write_text('{}')
    meter = PhysicalMeter(root)
    meter.count_native = lambda *a: pytest.fail('Closed run reached count/dispatch')
    meter.original = lambda *a, **kw: pytest.fail('Closed run reached network')
    with pytest.raises(AdmissionDenied, match='Closed experiment'):
        meter.urlopen(request())
    assert not meter.rows and meter.exhausted
