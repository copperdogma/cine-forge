#!/usr/bin/env python3
"""One-attempt whole-workspace experiment; never repairs semantic content."""
# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'benchmarks/scripts')]
from whole_story_workspace_contract import (  # noqa: E402
    NativeWorkspaceEnvelope,
    SubjectWorkspaceBundle,
    consumer_smoke,
    decode_native_envelope,
    materialize_workspace,
    subject_payload,
)

from cine_forge.env import load_cine_forge_dotenv, require_env  # noqa: E402

load_cine_forge_dotenv(ROOT)
E = ROOT / 'docs/evals/evidence/story-237-whole-task20261109'
FIXTURES = ROOT / 'benchmarks/fixtures/whole_story_workspace_v1'
CASES = ('open_frequency', 'last_ferry', 'matinee_echo')
FREEZE = E / 'freeze.json'


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def request_body(case):
    path = FIXTURES / (case + '.fountain')
    text = path.read_text()
    schema = SubjectWorkspaceBundle.model_json_schema()
    rules = '''Produce the COMPLETE final story-lane workspace from this original authored screenplay in ONE inference. No tools, follow-up calls or semantic repairs exist. Return the entire semantic bundle, not a synopsis/proposal. Every semantic schema field must be explicitly populated, including empty lists/nulls only when genuinely justified. Preserve complete scenes, exact dialogue/action/source fidelity and all material people (including animals and remote voices), places, props, relationships, source evidence and cross-scene continuity. Distinguish physical presence, heard speech, reported facts and unresolved identity; do not invent facts to make a neat story. Inferences must be marked as such with rationale/confidence. Do not elevate a character's report into independent fact. Cite exact original text and one-based inclusive original/canonical line spans. These inputs already are authored Fountain; keep canonical script_text EXACTLY equal to the supplied original (no rewriting). Raw original content/source byte/character/line metadata and canonical counts will be stamped mechanically by the wrapper; no semantic field will be filled. Bibles/scene/index/graph/continuity must be complete and mutually consistent; aliases are not permission to merge unresolved identities. Character relationship target_character is an emitted character_id, source_scene is an emitted scene_id. Continuity story_time_position is zero-based scene order; state IDs are <entity_type>_<entity_id>_<scene_id>. Continuity index keys are <entity_type>:<entity_id>. Source spans and quotes must ground original text; invented canonical text cannot manufacture evidence. Project config should be confirmed for the supplied evaluation policy: model_strategy work=claude-haiku-4-5-20251001, verify=gpt-4.1-mini, escalate=claude-opus-4-6; default_model=claude-sonnet-4-6; checkpoint human control, ai_generated production,16:9 aspect. Other story judgments come solely from source. No storyboard, audio/video, generation or rendering is requested. Outer bundle_json is a JSON-encoded string carrying the COMPLETE object specified below. Native API enforces the outer projection only; full original host schemas and all source/consumer checks will run after decoding.'''  # noqa: E501
    user = rules + '\nFULL REQUIRED SEMANTIC BUNDLE SCHEMA:\n' + json.dumps(schema, separators=(',', ':'))
    user += '\nSOURCE FILENAME: ' + path.name + '\nORIGINAL SOURCE BEGINS:\n' + text
    return {
        'model': 'claude-fable-5-2', 'max_tokens': 65536,
        'service_tier': 'standard_only',
        'messages': [{'role': 'user', 'content': user}],
        'output_config': {'effort': 'xhigh', 'format': {
            'type': 'json_schema', 'schema': NativeWorkspaceEnvelope.model_json_schema(),
        }},
    }


def free_count(body):
    count = {k: v for k, v in body.items() if k in {'model', 'messages', 'system'}}
    count['system'] = str(count.get('system', '')) + '\n' + json.dumps(body.get('output_config', {}))
    request = urllib.request.Request(
        'https://api.anthropic.com/v1/messages/count_tokens', method='POST',
        data=json.dumps(count).encode(), headers={
            'x-api-key': require_env('ANTHROPIC_API_KEY'),
            'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)['input_tokens']


def preflight():
    rows = []
    for case in CASES:
        body = request_body(case)
        n = free_count(body)
        assert n + 2048 <= 26000, 'Selected native input ceiling exceeded'
        path = FIXTURES / (case + '.fountain')
        rows.append({'case': case, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'native_input_tokens_count': n, 'admitted_input_bound': n + 2048,
                     'subject_standard_reservation_usd': (n + 2048) * .000016 + 65536 * .00004,
                     'body_sha256': hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()})
        dump(E / f'{case}-subject-request.json', body)
    example = json.loads((FIXTURES / 'open_frequency-consumer-example.json').read_text())
    subject = subject_payload(example)
    compact = json.dumps(subject, separators=(',', ':'), ensure_ascii=False)
    envelope = json.dumps({'bundle_json': compact}, separators=(',', ':'), ensure_ascii=False)
    n = free_count({'model': 'claude-fable-5-2', 'messages': [{'role': 'user', 'content': envelope}]})
    assert n <= 49152, 'Complete exemplar leaves less than16K thinking headroom'
    dump(E / 'native-preflight.json', {'cases': rows,
         'representability': {'consumer_compact_bytes': len(json.dumps(example, separators=(',', ':'), ensure_ascii=False).encode()),
                              'subject_compact_bytes': len(compact.encode()),
                              'wire_envelope_bytes': len(envelope.encode()),
                              'free_text_token_estimate': n,
                              'total_output_allowance': 65536,
                              'remaining_nominal_thinking_headroom': 65536 - n,
                              'limit': 'Authored complete exemplar establishes representability, not guaranteed subject length or quality.'}})
    print(json.dumps({'cases': rows, 'exemplar_text_tokens': n, 'headroom': 65536 - n}, indent=2))


def freeze():
    paths = [ROOT / 'benchmarks/scripts/run_whole_story_workspace.py',
             ROOT / 'benchmarks/scripts/whole_story_workspace_contract.py',
             ROOT / 'benchmarks/scripts/whole_story_workspace_meter.py']
    paths += list(FIXTURES.glob('*'))
    paths += list(E.glob('*subject-request.json'))
    paths += [E / 'native-preflight.json']
    paths += [ROOT / 'configs/recipes/recipe-mvp-ingest.yaml',
              ROOT / 'configs/recipes/recipe-world-building.yaml',
              ROOT / 'benchmarks/scripts/full_script_throughput_eval.py']
    files = []
    for path in sorted(p for p in paths if p.is_file()):
        raw = path.read_bytes()
        files.append({'path': str(path.relative_to(ROOT)), 'bytes': len(raw),
                      'sha256': hashlib.sha256(raw).hexdigest()})
    assert not FREEZE.exists(), 'Immutable pre-inference freeze already exists'
    dump(FREEZE, {'base': '0693227394bd9a63b1df1300070421000e0dd7b6',
         'files': files, 'case_order': list(CASES), 'cap_usd': '20',
         'candidate': 'claude-fable-5-2 standard_only xhigh65536',
         'subject_calls': 'one per case, one operational recovery maximum campaign-wide; no semantic repair',
         'controls': 'fresh unchanged mvp_ingest+world_building current runner settings; every nested physical retry metered',
         'judges': 'independent Astra offline full-source+frozen oracle, neutral arm labels; zero external paid calls',
         'admission': 'First candidate +conditional recovery5.707808; valid response settles and releases unused reservation. Full paired control admitted from actual remaining funds; fixed variants continue only in frozen order with known headroom. No guarantee all3 fit.',
         'schema': 'Native strict outer string only; complete original required host schemas and exact source/consumer validation after lossless decoding.'})


def check_freeze():
    frozen = json.loads(FREEZE.read_text())
    for item in frozen['files']:
        raw = (ROOT / item['path']).read_bytes()
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], item['path']


def subject(case):
    from whole_story_workspace_meter import PhysicalMeter
    check_freeze()
    admission = json.loads((E / f'admit-{case}.json').read_text())
    assert admission['candidate'] is True
    assert not (E / f'{case}-subject-receipt.json').exists(), 'Never silently repeat a subject'
    source_path = FIXTURES / (case + '.fountain')
    body = json.loads((E / f'{case}-subject-request.json').read_text())
    request = urllib.request.Request(
        'https://api.anthropic.com/v1/messages', method='POST',
        data=json.dumps(body).encode(), headers={
            'x-api-key': require_env('ANTHROPIC_API_KEY'),
            'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
    )
    start = time.perf_counter()
    with PhysicalMeter(E / 'physical-calls') as meter:
        meter.group = f'subject-{case}'
        with urllib.request.urlopen(request, timeout=600) as response:
            raw = response.read()
        dump(E / f'{case}-subject-raw.json', json.loads(raw))
    raw_data = json.loads(raw)
    receipt = {'model': raw_data.get('model'), 'usage': raw_data.get('usage'),
               'stop_reason': raw_data.get('stop_reason'),
               'elapsed_ms': round((time.perf_counter() - start) * 1000),
               'raw_sha256': hashlib.sha256(raw).hexdigest(),
               'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest()}
    dump(E / f'{case}-subject-receipt.json', receipt)
    assert raw_data['model'] == 'claude-fable-5-2'
    assert raw_data['stop_reason'] == 'end_turn'
    assert raw_data['usage']['service_tier'] == 'standard'
    assert raw_data['usage']['speed'] == 'standard'
    texts = [b['text'] for b in raw_data['content'] if b['type'] == 'text']
    assert len(texts) == 1
    envelope = json.loads(texts[0])
    full = decode_native_envelope(envelope, source_bytes=source_path.read_bytes(),
                                  source_filename=source_path.name).model_dump(mode='json')
    dump(E / f'{case}-subject-bundle.json', full)
    project = ROOT / 'output' / f'story-237-fable-{case}'
    materialize_workspace(full, source_bytes=source_path.read_bytes(), project_dir=project,
                          run_context={'producer': 'one Fable inference', 'receipt': receipt})
    smoke = consumer_smoke(repo_root=ROOT, project_dir=project, payload=full,
                           source_bytes=source_path.read_bytes())
    dump(E / f'{case}-subject-consumer.json', smoke)
    print(json.dumps({'receipt': receipt, 'consumer': smoke}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['preflight', 'freeze', 'subject'])
    parser.add_argument('--case', choices=CASES)
    args = parser.parse_args()
    if args.mode == 'preflight':
        preflight()
    elif args.mode == 'freeze':
        freeze()
    elif args.mode == 'subject':
        assert args.case
        subject(args.case)


if __name__ == '__main__':
    main()
