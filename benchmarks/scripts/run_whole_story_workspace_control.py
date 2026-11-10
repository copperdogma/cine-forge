#!/usr/bin/env python3
"""Fresh maintained whole pipeline, untouched models/prompts/retries/allowances."""
# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'benchmarks/scripts')]
from full_script_throughput_eval import _run_case  # noqa: E402
from full_script_throughput_support import ThroughputEvalManifest  # noqa: E402
from whole_story_workspace_control_meter import PhysicalMeter  # noqa: E402

from cine_forge.api.service import OperatorConsoleService  # noqa: E402

E = ROOT / 'docs/evals/evidence/story-237-whole-task20261109'
CASES = ('open_frequency', 'last_ferry', 'matinee_echo')


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=CASES, required=True)
    args = parser.parse_args()
    case = args.case
    admission = json.loads((E / f'admit-{case}.json').read_text())
    assert admission.get('control') is True
    assert not (E / f'{case}-control-result.json').exists(), 'Do not silently repeat control'
    original = json.loads((ROOT / 'benchmarks/fixtures/full_script_throughput_cases.json').read_text())
    original['cases'] = [{'case_id': case, 'label': f'Whole workspace {case}',
                          'input_fixture': f'benchmarks/fixtures/whole_story_workspace_v1/{case}.fountain'}]
    manifest = ThroughputEvalManifest.model_validate(original)
    dump(E / f'{case}-control-manifest.json', original)
    with PhysicalMeter(E / 'physical-calls') as meter:
        meter.group = f'control-{case}'
        result = _run_case(case=manifest.cases[0], manifest=manifest, keep_projects=True)
    record = result.model_dump(mode='json')
    record['physical_admission_halted'] = meter.exhausted
    record['physical_calls'] = [x for x in meter.rows if x['group'] == f'control-{case}']
    dump(E / f'{case}-control-result.json', record)
    project = ROOT / result.project_dir
    service = OperatorConsoleService(workspace_root=ROOT)
    pid = service.open_project(str(project))
    groups = service.list_artifact_groups(pid)
    artifacts = []
    for group in groups:
        detail = service.read_artifact(pid, group['artifact_type'],
                                       group['entity_id'], group['latest_version'])
        artifacts.append({'artifact_type': group['artifact_type'],
                          'entity_id': group['entity_id'],
                          'payload': detail['payload']['data'],
                          'bible_files': detail.get('bible_files', {}),
                          'health': detail['health']})
    dump(E / f'{case}-control-consumer.json', {
        'project_id': pid, 'pipeline_complete': result.success and not meter.exhausted,
        'summary': service.project_summary(pid), 'artifacts': artifacts,
        'graph': service.get_pipeline_graph(pid),
    })
    print(json.dumps({'case': case, 'complete': result.success and not meter.exhausted,
                      'project': result.project_dir, 'physical_calls': len(record['physical_calls']),
                      'accounted_usd': str(meter.accounted())}, indent=2))


if __name__ == '__main__':
    main()
