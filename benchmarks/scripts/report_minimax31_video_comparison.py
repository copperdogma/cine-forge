#!/usr/bin/env python3
"""Replay the Scout099 first-case diagnostic from retained receipts, without APIs."""
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

EVIDENCE = ROOT / 'docs/evals/evidence/story-226-minimax3120261020'
RESULT = ROOT / 'benchmarks/results/video-understanding-minimax31-first-v4-20261020.json'
MANIFEST = ROOT / 'docs/evals/story-226-minimax3120261020-evidence.json'


def assemble():
    rows = []
    for arm in ('minimax31', 'sol', 'luna'):
        prefix = 'diagnostic' if arm == 'minimax31' else 'subject'
        receipt = json.loads((EVIDENCE / f'{prefix}-{arm}-vfp_active_001.json').read_text())
        judge = json.loads((EVIDENCE / f'judge-opus-{arm}-vfp_active_001.json').read_text())
        assertion = get_assert(receipt['response']['output'], {'vars': receipt['vars']})
        rows.append({
            'arm': arm, 'n': 1, 'deterministic': assertion,
            'rubric': judge['score'], 'combined': (assertion['score'] + judge['score']) / 2,
            'dual_pass': assertion['pass'] and judge['score'] >= .8,
            'latency_ms': receipt['response']['latencyMs'],
            'cost_usd': receipt['response']['cost'],
            'qualified_strict_transport': arm != 'minimax31',
            'comparison_boundary': 'same-input first-case diagnostic; candidate schema unenforced',
        })
    ledger = json.loads((EVIDENCE / 'ledger.json').read_text())
    assert all(x['state'] == 'settled' for x in ledger)
    total = sum(Decimal(str(x['accounted_usd'])) for x in ledger)
    assert total <= 4
    return {
        'date': '2026-10-20',
        'base_git_sha': '01527226f8047f2af4db231091f690e314e11950',
        'candidate': 'minimax/minimax-m3.1-flash:free', 'provider': 'Minimax',
        'requested_effort': 'high', 'max_tokens': 32768,
        'candidate_reasoning_tokens': 1083,
        'rows': rows, 'ledger': ledger, 'spend_usd_mixed_reported_estimated': str(total),
        'unknown_exposure_usd': '0', 'cap_usd': '4',
        'candidate_remaining_cases': 'prop/motion not measured',
        'controls_remaining_cases': 'prop/motion not run after strict transport stop',
        'verdict': 'Defer candidate adoption: required strict contract unavailable. No qualified winner. Retain maintained Sol quality/Luna economy references.',
        'limits': 'One exposed synthetic case, no p95/generalization or six-case promotion. Candidate correctly observes growth, but unsupported slow_push_in is not evidence of mechanism. Tone, emotion, color and keyword grades retain source/scorer ambiguity. Candidate exceeds15s. Router price0 is not direct API economics. Other effort levels unmeasured; no within-task calibration.',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    result = assemble()
    if args.verify:
        assert json.loads(RESULT.read_text()) == result
        manifest = json.loads(MANIFEST.read_text())
        for item in manifest['files']:
            data = (ROOT / item['path']).read_bytes()
            assert len(data) == item['bytes']
            assert hashlib.sha256(data).hexdigest() == item['sha256'], item['path']
        print('Verified retained receipts, ledger, scores and all manifest hashes')
    else:
        assert not RESULT.exists(), 'Immutable result already exists'
        RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'rows': result['rows'], 'spend': result['spend_usd_mixed_reported_estimated']}, indent=2))


if __name__ == '__main__':
    main()
