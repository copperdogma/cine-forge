#!/usr/bin/env python3
"""FINAL one-slot exact MAX replay after premature provider EOF.

Only max_tokens changes from the actual prior streamed request. No continuation,
semantic repair, prompt/schema/effort change, model fallback or client retry.
"""
# ruff: noqa: E501
from __future__ import annotations

import hashlib
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'benchmarks/scripts')]
from recover_whole_story_workspace_stream import read_sse  # noqa: E402
from whole_story_workspace_contract import (  # noqa: E402
    consumer_smoke,
    decode_native_envelope,
    materialize_workspace,
)
from whole_story_workspace_meter import PhysicalMeter  # noqa: E402

from cine_forge.env import load_cine_forge_dotenv, require_env  # noqa: E402

E = ROOT / 'docs/evals/evidence/story-237-whole-task20261109'
SOURCE = ROOT / 'benchmarks/fixtures/whole_story_workspace_v1/open_frequency.fountain'


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    if sys.flags.optimize:
        raise RuntimeError('Optimized Python would disable integrity assertions')
    # Verify original semantic/source epoch; only meter acquired post-run guards.
    frozen = json.loads((E / 'freeze.json').read_text())
    for item in frozen['files']:
        raw = (ROOT / item['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            assert item['path'] == 'benchmarks/scripts/whole_story_workspace_meter.py'
            matches = [x for x in json.loads((E / 'producer-archive-index.json').read_text())
                       if x['original_path'] == item['path'] and x['sha256'] == item['sha256']]
            assert matches
            raw = (ROOT / matches[0]['archive_path']).read_bytes()
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
    load_cine_forge_dotenv(ROOT)
    prior = json.loads((E / 'physical-calls/ledger.json').read_text())
    assert len(prior) == 48, 'Final replay is exactly one physical slot'
    prior_wire = E / 'physical-calls' / prior[2]['name'] / 'request.json'
    wire = prior_wire.read_bytes()
    assert hashlib.sha256(wire).hexdigest() == prior[2]['request_sha256']
    authorization = json.loads((E / 'FINAL_REPLAY_AUTHORIZED.json').read_text())
    assert authorization['only_request_sha256'] == prior[2]['request_sha256']
    body = json.loads(wire)
    assert body['max_tokens'] == 128000 and body['output_config']['effort'] == 'xhigh'
    assert body['stream'] is True and body['service_tier'] == 'standard_only'
    assert not (E / 'open_frequency-xhigh128000-final-replay-receipt.json').exists()
    original_urlopen = urllib.request.urlopen
    meter = PhysicalMeter(E / 'physical-calls')
    meter.group = 'subject-open_frequency-xhigh128000-FINAL-verbatim-replay'
    # Exact same wire: reuse frozen free count12481 +2048 margin, with actual prior input12597.
    meter.count_native = lambda repeated_body, request: 12481
    start = time.perf_counter()

    def streaming_transport(request, *args, **kwargs):
        if request.full_url.endswith('/count_tokens'):
            return original_urlopen(request, *args, **kwargs)
        assert json.loads(request.data) == body
        folder = meter.root / meter.rows[-1]['name']
        with original_urlopen(request, timeout=1800) as response:
            dump(folder / 'http-receipt.json', {'status': response.status,
                 'content_type': response.headers.get('content-type'),
                 'request_id': response.headers.get('request-id')})
            assert response.status == 200
            assert 'text/event-stream' in response.headers.get('content-type', '')
            derived = read_sse(response, folder / 'response.sse')
        raw = (folder / 'response.sse').read_bytes()
        meter.rows[-1].update(response_origin='DERIVED native Message from complete raw SSE',
                             raw_sse_sha256=hashlib.sha256(raw).hexdigest(),
                             raw_sse_bytes=len(raw))
        meter.save()
        return io.BytesIO(json.dumps(derived).encode())

    meter.original = streaming_transport
    dump(E / 'open_frequency-xhigh128000-final-replay-request.json', body)
    freeze = {'reason': 'One FINAL root-authorized exact archived MAX request replay after premature provider EOF, not known max_tokens or semantic failure. No valid answer selection.',
              'body_delta_from_actual_prior_stream': {}, 'wire_sha256': hashlib.sha256(wire).hexdigest(),
              'supported_native_max_tokens': 128000, 'timeout_seconds': 1800,
              'reservation_usd': '5.352464', 'prior_conservative_accounted_usd': '11.203642',
              'hard_cap_usd': '20', 'no_further_max_cap_rescue': True, 'files': []}
    for p in [Path(__file__), ROOT / 'benchmarks/scripts/recover_whole_story_workspace_stream.py',
              ROOT / 'benchmarks/scripts/whole_story_workspace_meter.py',
              ROOT / 'benchmarks/scripts/whole_story_workspace_contract.py',
              E / 'open_frequency-xhigh128000-final-replay-request.json', E / 'native-fable-model-capabilities.json']:
        raw = p.read_bytes()
        freeze['files'].append({'path': str(p.relative_to(ROOT)), 'bytes': len(raw),
                                'sha256': hashlib.sha256(raw).hexdigest()})
    path = E / 'open_frequency-xhigh128000-final-replay-freeze.json'
    assert not path.exists()
    dump(path, freeze)
    request = urllib.request.Request('https://api.anthropic.com/v1/messages', method='POST',
        data=wire, headers={'x-api-key': require_env('ANTHROPIC_API_KEY'),
             'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with meter:
        with urllib.request.urlopen(request, timeout=1800) as response:
            derived = json.load(response)
    dump(E / 'open_frequency-xhigh128000-final-replay-derived-message.json', derived)
    receipt = {'origin': 'DERIVED from complete raw SSE',
               'configuration': 'FINAL exact same xhigh /128000 streamed request, provider EOF recovery',
               'elapsed_ms': round((time.perf_counter() - start) * 1000),
               'model': derived.get('model'), 'stop_reason': derived.get('stop_reason'),
               'usage': derived.get('usage'), 'meter_entry': meter.rows[-1]}
    dump(E / 'open_frequency-xhigh128000-final-replay-receipt.json', receipt)
    assert derived['stop_reason'] == 'end_turn'
    assert str(derived.get('id', '')).startswith('msg_')
    assert derived.get('type') == 'message' and derived.get('role') == 'assistant'
    assert derived['usage']['service_tier'] == 'standard' and derived['usage']['speed'] == 'standard'
    texts = [b['text'] for b in derived['content'] if b['type'] == 'text']
    assert len(texts) == 1
    envelope = json.loads(texts[0])
    full = decode_native_envelope(envelope, source_bytes=SOURCE.read_bytes(),
                                  source_filename=SOURCE.name).model_dump(mode='json')
    dump(E / 'open_frequency-subject-bundle.json', full)
    project = ROOT / 'output/story-237-fable-open_frequency'
    materialize_workspace(full, source_bytes=SOURCE.read_bytes(), project_dir=project,
        run_context={'producer': 'one xhigh128000 Fable semantic inference on FINAL verbatim provider-EOF replay',
                     'receipt': receipt})
    smoke = consumer_smoke(repo_root=ROOT, project_dir=project, payload=full,
                           source_bytes=SOURCE.read_bytes())
    dump(E / 'open_frequency-subject-consumer.json', smoke)
    print(json.dumps({'receipt': receipt, 'consumer': smoke}, indent=2))


if __name__ == '__main__':
    main()
