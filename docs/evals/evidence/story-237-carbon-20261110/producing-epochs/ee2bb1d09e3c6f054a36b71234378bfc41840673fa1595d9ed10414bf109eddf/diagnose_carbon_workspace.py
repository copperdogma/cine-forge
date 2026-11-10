"""Identify every reachable host check on saved original output; never score a repair."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from unittest.mock import patch

import whole_story_workspace_contract as contract
from preflight_carbon_workspace import CASES, E, FIXTURES, ROOT, dump, sha


def diagnose(case):
    path=E/(case+"-visible.txt")
    source=FIXTURES/(case+".fountain")
    raw=json.loads(json.loads(path.read_text())["bundle_json"])
    contract.SubjectWorkspaceBundle.model_validate(raw)
    failures=[]
    def observe(condition, message):
        if not condition:
            failures.append(message)
    interrupted=None
    with patch.object(contract,"_require",side_effect=observe):
        try:
            contract.consumer_payload(raw,source_bytes=source.read_bytes(),source_filename=source.name)
        except (KeyError,IndexError) as exc:
            interrupted=f"{type(exc).__name__}: {exc}"
    original=source.read_text()
    generated=raw["canonical_script"]["script_text"]
    report={"method":"Read-only all-errors traversal on original output. No workspace was written and no gate relaxed for scoring.",
            "visible_sha256":sha(path),"source_sha256":sha(source),
            "schema_valid":True,"host_failures":dict(Counter(failures)),"interrupted":interrupted,
            "source_chars":len(original),"canonical_chars":len(generated),
            "sole_canonical_difference_is_trailing_lf":generated+"\n"==original}
    if report["sole_canonical_difference_is_trailing_lf"]:
        changed=json.loads(json.dumps(raw))
        changed["canonical_script"]["script_text"]+="\n"
        try:
            bundle=contract.consumer_payload(changed,source_bytes=source.read_bytes(),source_filename=source.name)
            report["lf_only_diagnostic"]="all strict upstream host checks pass on separated copy"
            project=ROOT/"output"/("carbon-diagnostic-appended-lf-"+case)
            if not project.exists():
                contract.materialize_workspace(bundle,source_bytes=source.read_bytes(),project_dir=project,
                             run_context={"classification":"One-byte LF-restored derivative; diagnostic only"})
            receipt=contract.consumer_smoke(repo_root=ROOT,project_dir=project,payload=bundle,
                                           source_bytes=source.read_bytes())
            receipt["classification"]="One trailing LF appended only to derivative canonical text. Actual unmodified candidate failed and was never materialized."
            dump(E/("diagnostic-only-lf-restored-consumer.json" if case==CASES[0] else case+"-diagnostic-lf-restored-consumer.json"),receipt)
        except ValueError as exc:
            report["lf_only_diagnostic"]="strict separated copy also fails: "+str(exc)[:700]
    dump(E/(case+"-host-diagnostic.json"),report)
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("case",choices=CASES)
    diagnose(parser.parse_args().case)
