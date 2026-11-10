#!/usr/bin/env python3
"""Offline seal/replay of the closed whole-workspace capability experiment."""
# ruff: noqa: E501
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / 'docs/evals/evidence/story-237-whole-task20261109'
RESULT = ROOT / 'benchmarks/results/whole-story-workspace-fable52-20261109.json'
MANIFEST = ROOT / 'docs/evals/story-237-whole-task20261109-manifest.json'


def read(path):
    return json.loads(path.read_text())


def inventory(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def assemble():
    rows = read(E / 'physical-calls/ledger.json')
    assert len(rows) == 49
    assert all(r['state'] in {'settled-usage-estimate', 'unknown-exposure-held'} for r in rows)
    known = sum(Decimal(r['accounted_usd']) for r in rows if r['state'] == 'settled-usage-estimate')
    unknown = sum(Decimal(r['accounted_usd']) for r in rows if r['state'] == 'unknown-exposure-held')
    assert known + unknown <= 20
    control = [r for r in rows if r['group'] == 'control-open_frequency']
    assert len(control) == 45 and all(r['state'] == 'settled-usage-estimate' for r in control)
    c = read(E / 'open_frequency-control-result.json')
    consumer = read(E / 'open_frequency-control-consumer.json')
    native = read(E / 'open_frequency-stream-derived-message.json')
    assert native['stop_reason'] == 'max_tokens'
    assert native['usage']['output_tokens'] == 65536
    assert native['usage']['output_tokens_details']['thinking_tokens'] == 65536
    assert not any(b['type'] == 'text' for b in native['content'])
    partial = read(E / 'open_frequency-xhigh128000-partial-derived.json')
    assert partial['stopped'] is False
    visible = ''.join(b['text'] for b in partial['native_message_partial']['content'] if b['type'] == 'text')
    assert len(visible) == 15735
    try:
        json.loads(visible)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError('Previously incomplete visible JSON changed')
    final = read(E / 'final-replay-outcome.json')
    assert rows[-1]['request_sha256'] == rows[2]['request_sha256']
    assert (E / 'physical-calls' / rows[-1]['name'] / 'request.json').read_bytes() == (E / 'physical-calls' / rows[2]['name'] / 'request.json').read_bytes()
    return {
        'date': '2026-11-09', 'completed': '2026-11-10', 'story': '237', 'attempt': '058',
        'base_git_sha': '0693227394bd9a63b1df1300070421000e0dd7b6',
        'owner_boundary': 'story_lane_workspace_ready: mvp_ingest then world_building',
        'candidate': 'claude-fable-5-2 / native standard_only',
        'candidate_arms': [
            {'effort': 'xhigh', 'total_output': 65536, 'transport': 'nonstream',
             'outcome': '600040ms timeout before HTTP response; no output or usage', 'unknown_usd': '2.853904'},
            {'effort': 'xhigh', 'total_output': 65536, 'transport': 'streamed operational recovery',
             'outcome': 'Complete SSE message_stop but max_tokens; all65536tokens thinking, zero text/bundle',
             'latency_ms': 588353, 'usage_estimate_usd': '2.722216'},
            {'effort': 'xhigh', 'total_output': 128000, 'transport': 'streamed adequate-output arm',
             'outcome': 'Premature EOF:15735visible characters, incomplete outer JSON; no final usage/terminal. Cause unknown, not a known max_tokens stop.',
             'latency_ms': 1053981, 'unknown_usd': '5.352464'},
        ],
        'final_verbatim_replay': final,
        'candidate_whole_output_delivered': final['complete_whole_output'],
        'candidate_semantic_quality': final['source_quality'],
        'candidate_native_schema': 'API-enforced strict outer bundle_json string; complete original required host schema after decoding. No complete bundle reached host validation.',
        'incumbent': {
            'settings': 'Unchanged maintained throughput runner and two recipes; runtime Haiku work, Sonnet default/scene-analysis, GPT4.1Mini verify, Opus escalation retained.',
            'physical_calls': 45, 'models': dict(Counter(r['model'] for r in control)),
            'usage_estimate_usd': str(sum(Decimal(r['accounted_usd']) for r in control)),
            'legacy_helper_cost_usd': c['total_cost_usd'],
            'elapsed_ms': c['total_elapsed_ms'], 'recipe_completion': c['success'],
            'consumer_groups': len(consumer['artifacts']),
            'consumer_artifact_types': dict(Counter(a['artifact_type'] for a in consumer['artifacts'])),
            'all_consumer_health_labels_valid': all(a['health'] == 'valid' for a in consumer['artifacts']),
            'source_quality': 'FAIL independent whole-source review: invented facts, stale final-scene continuity, incomplete material entities/prop indexing, dangling graph endpoints and scene refs.',
            'review': 'docs/evals/evidence/story-237-whole-task20261109/source-review-control.md',
            'project': c['project_dir'],
            'durable_workspace': 'docs/evals/evidence/story-237-whole-task20261109/control-workspace',
        },
        'case_disposition': {
            'open_frequency': final['case_disposition'],
            'last_ferry': 'NOT MEASURED: shared qualification had not passed before extended provider recovery; final nativeMAX replay exhausted the prospective confirmation scope/budget. No invented failure; frozen source/oracle retained.',
            'matinee_echo': 'NOT MEASURED: shared qualification had not passed before extended provider recovery; final nativeMAX replay exhausted the prospective confirmation scope/budget. No invented failure; frozen source/oracle retained.',
        },
        'known_usage_estimate_usd': str(known), 'unknown_reservations_usd': str(unknown),
        'conservative_accounted_usd': str(known + unknown), 'hard_cap_usd': '20',
        'invoice_reconciliation': 'Not available; no unknown reservation released.',
        'decision': final['decision'],
        'limits': 'One authored source attempted; two fixed variants unmeasured after extended recovery. Other efforts unmeasured. No best-of-valid-answer selection, partial answer scoring, private source, runtime/default change, commit/push or deployment.',
        'worktree': {'path': '/Users/cam/.codex/worktrees/fable-whole-task-20261109/cine-forge', 'branch': 'codex/fable-whole-task-20261109-cine-forge',
                     'owner': 'Scout108 CineForge campaign', 'disposition': 'retained uncommitted for root review; no cleanup authorized'},
    }


def verify():
    assert read(RESULT) == assemble()
    for item in read(MANIFEST)['files']:
        if inventory(ROOT / item['path']) != item:
            # Landing changes shared records; preserve the producing epoch exactly.
            archive = ROOT / 'docs/evals/landing-fable-20261110/original-manifest-files.json'
            matches = [x for x in read(archive) if x['path'] == item['path'] and x['sha256'] == item['sha256']]
            assert len(matches) == 1, item['path']
            raw = (ROOT / matches[0]['archive_path']).read_bytes()
            assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], item['path']
    for name in ('freeze.json', 'open_frequency-stream-freeze.json', 'open_frequency-xhigh128000-freeze.json', 'control-producer-freeze-v2.json', 'open_frequency-xhigh128000-final-replay-freeze.json'):
        for item in read(E / name)['files']:
            raw = (ROOT / item['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != item['sha256']:
                matches = [x for x in read(E / 'producer-archive-index.json') if x['original_path'] == item['path'] and x['sha256'] == item['sha256']]
                assert matches, item['path']
                raw = (ROOT / matches[0]['archive_path']).read_bytes()
            assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'], item['path']
    for row in read(E / 'physical-calls/ledger.json'):
        folder = E / 'physical-calls' / row['name']
        request = (folder / 'request.json').read_bytes()
        assert hashlib.sha256(request).hexdigest() == row['request_sha256']
        assert '?' not in row['url'] and '@' not in row['url']
        if row.get('raw_sse_sha256'):
            assert hashlib.sha256((folder / 'response.sse').read_bytes()).hexdigest() == row['raw_sse_sha256']
    print('Verified49 physical calls, exact final verbatim request and all known/unknown holds; exact wire/source/producer/evidence hashes and complete control readback records. No inference.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify()
        return
    assert not RESULT.exists() and not MANIFEST.exists(), 'Closed immutable evidence already exists'
    dump(RESULT, assemble())
    paths = [p for p in E.rglob('*') if p.is_file()]
    for folder in ('story-236-whole-task20261109', 'story-236-whole-task-20261109'):
        paths += [p for p in (ROOT / 'docs/evals/evidence' / folder).rglob('*') if p.is_file()]
    paths += [p for p in (ROOT / 'benchmarks/fixtures/whole_story_workspace_v1').glob('*') if p.is_file()]
    paths += list((ROOT / 'benchmarks/scripts').glob('*whole_story_workspace*.py'))
    paths += [RESULT, ROOT / 'tests/unit/test_whole_story_workspace_experiment.py']
    dump(MANIFEST, {'files': [inventory(p) for p in sorted(set(paths))],
        'draft_prefix_accounting': 'Two story-236-whole-task evidence directories are pre-ID-allocation worker analysis for THIS Story237; unrelated to prior Scout107 Story236. All hashed and retained.',
        'producing_identity': 'Current remote base plus per-call frozen dirty code/source/request hashes. Runtime/recipes unchanged; no primary checkout edits.',
        'offline_verify': 'PYTHONPATH=src <cineforge-python> benchmarks/scripts/report_whole_story_workspace.py --verify',
        'reproduction': 'Closed selected run: no automatic paid replay. A new authorized identity is required; all original calls, failed/partial streams and unresolved charge exposure remain immutable.'})
    verify()


if __name__ == '__main__':
    main()
