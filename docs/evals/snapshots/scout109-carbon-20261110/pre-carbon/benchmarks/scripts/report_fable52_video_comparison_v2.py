#!/usr/bin/env python3
"""Offline assembly/verification; never calls a provider."""
# ruff: noqa: E501
import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'benchmarks/scorers'))
from video_understanding_scorer import get_assert  # noqa: E402

E = ROOT / 'docs/evals/evidence/story-236-fable5220261109'
F = ROOT / 'docs/evals/story-236-fable5220261109-fable52-freeze.json'
R = ROOT / 'benchmarks/results/video-understanding-fable52-vs-sol-luna-v4-20261109-v2.json'
M = ROOT / 'docs/evals/story-236-fable5220261109-evidence-v2.json'
ARMS = ('fable52', 'sol', 'luna')


def read(p):
    return json.loads(p.read_text())


def dump(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n')


def inventory(p):
    raw = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def assemble():
    rows = []
    source = read(E / 'source-review.json')
    for case in range(1, 7):
        cid = f'vfp_active_{case:03d}'
        for arm in ARMS:
            receipt = read(E / f'native-{arm}-{cid}.json')
            judge = read(E / f'judge-opus-{arm}-{cid}.json')
            response = receipt['response']
            score = get_assert(response['output'], {'vars': receipt['vars']})
            combined = (score['score'] + judge['score']) / 2
            source_row = source['cases'][cid]['arms'][arm]
            dual = bool(score['pass'] and judge['score'] >= .8 and combined >= .8)
            rows.append({'arm': arm, 'case': cid, 'clip': receipt['vars']['clip_id'],
                         'structural': score, 'rubric': judge['score'], 'combined': combined,
                         'dual_quality_pass': dual,
                         'zero_definite_source_inventions': not source_row['definite_source_errors'],
                         'full_quality_pass': dual and not source_row['definite_source_errors'] and not source_row['source_contract_grounding_misses'],
                         'source_adjudication': source_row,
                         'latency_ms': response['latencyMs'], 'cost_usd': response['cost'],
                         'production_latency_pass': response['latencyMs'] <= 15000,
                         'production_cost_pass': response['cost'] <= .02,
                         'model': response['raw']['model'], 'usage': response['raw']['usage']})
    ledger = read(E / 'ledger-v2.json')
    assert len(ledger) == 37
    assert all(x['state'] in {'settled', 'rejected-reservation-retained'} for x in ledger)
    accounted = sum(Decimal(x['accounted_usd']) for x in ledger)
    total = sum(Decimal(x['accounted_usd']) for x in ledger if x['state'] == 'settled')
    unknown = accounted - total
    assert accounted <= 20
    aggregate = {}
    for arm in ARMS:
        group = [r for r in rows if r['arm'] == arm]
        aggregate[arm] = {
            'cases': len(group), 'structural_mean': sum(x['structural']['score'] for x in group) / 6,
            'rubric_mean': sum(x['rubric'] for x in group) / 6,
            'combined_mean': sum(x['combined'] for x in group) / 6,
            'dual_passes': sum(x['dual_quality_pass'] for x in group),
            'full_quality_passes': sum(x['full_quality_pass'] for x in group),
            'mean_latency_ms': sum(x['latency_ms'] for x in group) / 6,
            'subject_cost_usd': str(sum(Decimal(str(x['cost_usd'])) for x in group)),
            'mean_subject_cost_usd': str(sum(Decimal(str(x['cost_usd'])) for x in group) / 6),
        }
    return {'date': '2026-11-09', 'base_git_sha': '0693227394bd9a63b1df1300070421000e0dd7b6',
            'candidate': 'claude-fable-5-2', 'route': 'Direct Anthropic Messages standard; authorized recovery after OpenRouter402',
            'requested_effort': 'xhigh', 'output_allowance': 32768,
            'thinking_usage': 'Adaptive always-on; requested xhigh on wire. Actual total billed output and output_tokens_details.thinking_tokens retained per native response; no effort sweep.',
            'schema': 'API-enforced exact13-key projected structural subset; full original Pydantic constraints validated locally',
            'rows': rows, 'aggregate': aggregate, 'ledger': ledger, 'total_spend_usd': str(total),
            'unknown_exposure_usd': str(unknown), 'conservative_accounted_usd': str(accounted), 'cap_usd': '20',
            'freshness': '18 uncached subjects,18 blind source-complete native Opus4.6 reviews; offline native-envelope replay parity; no duplicate inference',
            'openrouter': 'access rejected before provider assignment/inference usage; no explicit billing reconciliation, retain full USD2.15872 unknown reservation; not qualified',
            'limits': 'Six exposed authored synthetic cases, no population/p95 claim, no held-out promotion. Anthropic same-provider judge bias disclosed; source-first independent agent corroboration for concrete facts. Other efforts, audio/video, screenplay/runtime integration unmeasured.'}


def verify():
    assert read(R) == assemble()
    for item in read(M)['files']:
        assert inventory(ROOT / item['path']) == item, item['path']
    for item in read(F)['files']:
        assert inventory(ROOT / item['path']) == item, item['path']
    for row in read(R)['rows']:
        arm, cid = row['arm'], row['case']
        parity = read(E / f'native-{arm}-{cid}-parity.json')
        assert parity['same_wire_body'] and parity['same_output']
        body = read(E / f'native-{arm}-{cid}-request.json')['payload']
        if arm == 'fable52':
            assert body['model'] == 'claude-fable-5-2'
            assert body['output_config']['effort'] == 'xhigh' and body['max_tokens'] == 32768
            assert len(body['output_config']['format']['schema']['required']) == 13
            assert len([p for p in body['messages'][0]['content'] if p['type'] == 'image']) == 5
            assert not {'temperature', 'speed', 'service_tier'} & set(body)
            assert row['usage']['speed'] == 'standard'
            assert row['usage']['service_tier'] == 'standard'
    print('Verified18 subject/parity pairs,18 full-source reviews,37 reconciled ledger entries, all producing/source/evidence hashes; no inference.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify()
        return
    assert not R.exists(), 'Immutable result already exists'
    dump(R, assemble())
    paths = [p for p in E.rglob('*') if p.is_file()]
    paths += [F, F.with_name(F.stem + '-openrouter.json'), R, Path(__file__),
              ROOT / 'benchmarks/scripts/report_fable52_video_comparison.py',
              ROOT / 'benchmarks/results/video-understanding-fable52-vs-sol-luna-v4-20261109.json',
              ROOT / 'docs/evals/story-236-fable5220261109-evidence.json']
    for folder in ROOT.glob('docs/evals/snapshots/story-236-fable5220261109-*'):
        paths += [p for p in folder.rglob('*') if p.is_file()]
    dump(M, {'files': [inventory(p) for p in sorted(set(paths))],
             'regenerate': 'Original selected campaign: owner wrapper around run_fable52_video_comparison.py preflight, then case --case vfp_active_001..006. Closed result forbids further inference; new authorized identity required.',
             'offline_verify': 'PYTHONPATH=src <cineforge-python> benchmarks/scripts/report_fable52_video_comparison_v2.py --verify'})
    verify()


if __name__ == '__main__':
    main()
