#!/usr/bin/env python3
"""Single operational SSE recovery; native Message derived from persisted SSE.

Protocol source: https://platform.claude.com/docs/en/build-with-claude/streaming
No SDK, hidden retry, continuation prompt, content repair or extra inference.
"""
# ruff: noqa: E501
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'benchmarks/scripts')]
from whole_story_workspace_contract import (  # noqa: E402
    consumer_smoke,
    decode_native_envelope,
    materialize_workspace,
)
from whole_story_workspace_meter import PhysicalMeter  # noqa: E402

from cine_forge.env import load_cine_forge_dotenv, require_env  # noqa: E402

E = ROOT / 'docs/evals/evidence/story-237-whole-task20261109'
CASES = ('open_frequency', 'last_ferry', 'matinee_echo')


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


class Accumulator:
    """Documented text/thinking-only Message event flow; no tools permitted."""
    def __init__(self):
        self.message = None
        self.open_blocks = set()
        self.closed_blocks = set()
        self.stopped = False

    def event(self, event):
        kind = event['type']
        if kind == 'ping':
            return
        if kind == 'error':
            raise RuntimeError('Native SSE error: ' + json.dumps(event['error']))
        if self.stopped:
            raise RuntimeError('SSE content after terminal message_stop')
        if kind == 'message_start':
            assert self.message is None
            self.message = copy.deepcopy(event['message'])
            assert self.message['model'] == 'claude-fable-5-2'
            assert self.message['content'] == []
        elif kind == 'content_block_start':
            assert self.message is not None
            index = event['index']
            assert index == len(self.message['content'])
            assert event['content_block']['type'] in {'thinking', 'text', 'redacted_thinking'}
            self.message['content'].append(copy.deepcopy(event['content_block']))
            self.open_blocks.add(index)
        elif kind == 'content_block_delta':
            index = event['index']
            assert index in self.open_blocks
            block, delta = self.message['content'][index], event['delta']
            key = {'text_delta': 'text', 'thinking_delta': 'thinking',
                   'signature_delta': 'signature'}.get(delta['type'])
            assert key is not None, 'Unplanned delta type'
            assert (key == 'text') == (block['type'] == 'text')
            block[key] = block.get(key, '') + delta[key]
        elif kind == 'content_block_stop':
            index = event['index']
            assert index in self.open_blocks
            self.open_blocks.remove(index)
            self.closed_blocks.add(index)
        elif kind == 'message_delta':
            assert self.message is not None
            for key, value in event.get('delta', {}).items():
                self.message[key] = value
            # Provider documents cumulative, not additive, usage deltas.
            self.message.setdefault('usage', {}).update(event.get('usage', {}))
        elif kind == 'message_stop':
            assert self.message is not None and not self.open_blocks
            assert self.closed_blocks == set(range(len(self.message['content'])))
            assert self.message.get('stop_reason') is not None
            self.stopped = True
        # Version policy permits unknown event types; retained raw, ignored.

    def final(self):
        assert self.stopped, 'Missing terminal message_stop; quarantine partial stream'
        assert self.message['model'] == 'claude-fable-5-2'
        return self.message


def read_sse(response, raw_path):
    acc = Accumulator()
    pending = []
    event_name = None
    with raw_path.open('wb') as raw:
        for line in response:
            raw.write(line)
            raw.flush()  # Bytes durable before interpreting even a single event.
            stripped = line.rstrip(b'\r\n')
            if stripped.startswith(b'event:'):
                event_name = stripped[6:].strip().decode()
            elif stripped.startswith(b'data:'):
                pending.append(stripped[5:].lstrip())
            elif not stripped and pending:
                event = json.loads(b'\n'.join(pending))
                assert event_name in (None, event['type']), 'SSE event name/body mismatch'
                acc.event(event)
                pending, event_name = [], None
                if acc.stopped:
                    break
    assert not pending
    return acc.final()


def main():
    if sys.flags.optimize:
        raise RuntimeError('Optimized Python would disable required integrity assertions')
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=CASES, default='open_frequency')
    case = parser.parse_args().case
    source_path = ROOT / f'benchmarks/fixtures/whole_story_workspace_v1/{case}.fountain'
    from run_whole_story_workspace import check_freeze
    check_freeze()
    load_cine_forge_dotenv(ROOT)
    original = json.loads((E / f'{case}-subject-request.json').read_text())
    if case == 'open_frequency':
        prior_wire = E / 'physical-calls/0000-subject-open_frequency-claude-fable-5-2/request.json'
        assert json.loads(prior_wire.read_bytes()) == original, 'Recovery differs from actual original physical request'
    body = dict(original, stream=True)
    assert {k: v for k, v in body.items() if k != 'stream'} == original
    assert body['output_config']['effort'] == 'xhigh' and body['max_tokens'] == 65536
    assert body['service_tier'] == 'standard_only'
    assert not (E / f'{case}-stream-recovery-receipt.json').exists()
    original_urlopen = urllib.request.urlopen
    meter = PhysicalMeter(E / 'physical-calls')
    meter.group = f'subject-{case}-stream' + ('-operational-recovery' if case == 'open_frequency' else '')
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
        meter.rows[-1].update(response_origin='derived native Message from complete raw SSE',
                             raw_sse_sha256=hashlib.sha256(raw).hexdigest(),
                             raw_sse_bytes=len(raw))
        meter.save()
        return io.BytesIO(json.dumps(derived).encode())

    meter.original = streaming_transport
    dump(E / f'{case}-stream-request.json', body)
    snapshot_paths = [Path(__file__), ROOT / 'benchmarks/scripts/whole_story_workspace_meter.py',
                      ROOT / 'benchmarks/scripts/whole_story_workspace_contract.py',
                      E / f'{case}-stream-request.json']
    freeze = {'recovery_of': '600s nonstream timeout, original fullUSD2.853904 exposure held',
              'body_delta': {'stream': True}, 'timeout_seconds': 1800,
              'semantic_settings_unchanged': True, 'files': []}
    for p in snapshot_paths:
        data = p.read_bytes()
        freeze['files'].append({'path': str(p.relative_to(ROOT)), 'bytes': len(data),
                                'sha256': hashlib.sha256(data).hexdigest()})
    assert not (E / f'{case}-stream-freeze.json').exists()
    dump(E / f'{case}-stream-freeze.json', freeze)
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', method='POST',
        data=json.dumps(body).encode(), headers={'x-api-key': require_env('ANTHROPIC_API_KEY'),
             'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with meter:
        with urllib.request.urlopen(req, timeout=1800) as response:
            derived = json.load(response)
    dump(E / f'{case}-stream-derived-message.json', derived)
    receipt = {'origin': 'DERIVED from raw SSE, not a raw nonstream JSON envelope',
               'elapsed_ms': round((time.perf_counter() - start) * 1000),
               'stop_reason': derived.get('stop_reason'), 'usage': derived['usage'],
               'model': derived['model'], 'meter_entry': meter.rows[-1]}
    dump(E / f'{case}-stream-recovery-receipt.json', receipt)
    assert derived['stop_reason'] == 'end_turn'
    assert str(derived.get('id', '')).startswith('msg_')
    assert derived.get('type') == 'message' and derived.get('role') == 'assistant'
    assert derived['usage'].get('service_tier') == 'standard'
    assert derived['usage'].get('speed') == 'standard'
    texts = [x['text'] for x in derived['content'] if x['type'] == 'text']
    assert len(texts) == 1
    envelope = json.loads(texts[0])
    full = decode_native_envelope(envelope, source_bytes=source_path.read_bytes(),
                                  source_filename=source_path.name).model_dump(mode='json')
    dump(E / f'{case}-subject-bundle.json', full)
    project = ROOT / f'output/story-237-fable-{case}'
    materialize_workspace(full, source_bytes=source_path.read_bytes(), project_dir=project,
                          run_context={'producer': 'one streamed Fable inference, operational recovery',
                                       'receipt': receipt})
    smoke = consumer_smoke(repo_root=ROOT, project_dir=project, payload=full,
                           source_bytes=source_path.read_bytes())
    dump(E / f'{case}-subject-consumer.json', smoke)
    print(json.dumps({'receipt': receipt, 'consumer': smoke}, indent=2))


if __name__ == '__main__':
    main()
