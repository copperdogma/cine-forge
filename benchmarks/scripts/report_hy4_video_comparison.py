#!/usr/bin/env python3
"""Offline reconstruction/verification of the retained Hy4 comparison."""
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

EVIDENCE = ROOT / 'docs/evals/evidence/story-235-hy420261105'
FREEZE = ROOT / 'docs/evals/story-235-hy420261105-hy4-freeze.json'
RESULT = ROOT / 'benchmarks/results/video-understanding-hy4-vs-sol-luna-v4-20261105.json'
MANIFEST = ROOT / 'docs/evals/story-235-hy420261105-evidence.json'
ARMS = ('hy4', 'sol', 'luna')
CASE = 'vfp_active_001'


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')


def inventory(path):
    raw = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def assemble():
    rows = []
    for arm in ARMS:
        r = read(EVIDENCE / f'subject-{arm}-{CASE}.json')
        j = read(EVIDENCE / f'judge-opus-{arm}-{CASE}.json')
        response = r['response']
        score = get_assert(response['output'], {'vars': r['vars']})
        combined = (score['score'] + j['score']) / 2
        rows.append({'arm': arm, 'case': CASE, 'deterministic': score,
                     'rubric': j['score'], 'combined': combined,
                     'quality_pass': bool(score['pass'] and j['score'] >= .8 and combined >= .8),
                     'latency_ms': response['latencyMs'], 'cost_usd': response['cost'],
                     'subject_model': response['raw']['model']})
    ledger = read(EVIDENCE / 'ledger.json')
    assert len(ledger) == 9 and all(x['state'] == 'settled' for x in ledger)
    total = sum(Decimal(x['accounted_usd']) for x in ledger)
    assert total <= 5
    categories = {prefix: str(sum(Decimal(x['accounted_usd']) for x in ledger
                                  if x['name'].startswith(prefix + '-')))
                  for prefix in ['native', 'subject', 'judge']}
    return {'date': '2026-11-05', 'base_git_sha': 'a66e6834ecb98f2a656e34aa37fde0015d11c3af',
            'candidate': 'tencent/hy4', 'canonical_slug': 'tencent/hy4-20261104',
            'route': 'OpenRouter Tencent FP4', 'effort': 'high', 'output_allowance': 32768,
            'rows': rows, 'ledger': ledger, 'total_spend_usd': str(total),
            'spend_categories_usd': categories, 'unknown_exposure_usd': '0', 'cap_usd': '5',
            'verdict': 'Retain Sol/Luna research references; reject tested Hy4 high32768 arm.',
            'source_failure': 'Frame3 evidence invents wider gaps between heads and torsos; original heads touch/overlap torsos. Enlargement only partially described.',
            'limits': 'One exposed synthetic case per arm; no model qualifies. Tone/color/lexical penalties ambiguous. No product analyzer/promotion. Native Hy4 242893ms includes operator storage pause and is excluded from latency comparison. Other efforts and remaining cases unmeasured.'}


def verify():
    assert read(RESULT) == assemble()
    manifest = read(MANIFEST)
    for item in manifest['files']:
        actual = inventory(ROOT / item['path'])
        assert actual == item, f"Evidence changed: {item['path']}"
    for item in read(FREEZE)['files']:
        actual = inventory(ROOT / item['path'])
        assert actual == item, f"Producing input changed: {item['path']}"
    for arm in ARMS:
        native = read(EVIDENCE / f'native-{arm}-{CASE}-request.json')
        subject = read(EVIDENCE / f'subject-{arm}-{CASE}-request.json')
        assert native == subject, arm
    candidate = read(EVIDENCE / f'subject-hy4-{CASE}-request.json')['payload']
    assert candidate['model'] == 'tencent/hy4'
    assert candidate['reasoning'] == {'effort': 'high'}
    assert candidate['provider']['order'] == ['Tencent']
    assert candidate['provider']['allow_fallbacks'] is False
    assert candidate['provider']['require_parameters'] is True
    assert candidate['response_format']['json_schema']['strict'] is True
    assert candidate['max_completion_tokens'] == 32768
    assert all(x['quality_pass'] is False for x in read(RESULT)['rows'])
    print('Verified9 settledcalls,3 exact native/parity pairs, strict high route, frozen sources/code and evidence hashes; no inference.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify()
        return
    assert not RESULT.exists(), 'Immutable result exists'
    dump(RESULT, assemble())
    files = [p for p in EVIDENCE.rglob('*') if p.is_file()]
    files += [FREEZE, RESULT, Path(__file__)]
    dump(MANIFEST, {'files': [inventory(p) for p in sorted(set(files))],
                    'regenerate': 'Owner provider wrapper around run_hy4_video_comparison.py preflight; qualify --first; judges --case vfp_active_001. Closed result prevents further paid execution; later authorized runs need new identities.',
                    'offline_verify': 'PYTHONPATH=src <cineforge-python> benchmarks/scripts/report_hy4_video_comparison.py --verify'})
    verify()


if __name__ == '__main__':
    main()
