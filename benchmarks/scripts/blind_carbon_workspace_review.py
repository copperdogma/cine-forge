"""Build neutral source-review packets from each real console's payloads."""

from __future__ import annotations

import argparse
import json

from preflight_carbon_workspace import CASES, ROOT, E, dump

from cine_forge.api.service import OperatorConsoleService


def packet(case, arm):
    # Assign slots before either complete outcome, varying the order across cases.
    labels = {case_id: ("B", "A") if i % 2 == 0 else ("A", "B") for i, case_id in enumerate(CASES)}
    label = labels[case][int(arm == "control")]
    if arm == "control":
        result = json.loads((E / (case + "-control-result.json")).read_text())
        project = ROOT / result["project_dir"]
    else:
        project = ROOT / "output" / ("carbon-20261110-" + case)
    service = OperatorConsoleService(workspace_root=ROOT)
    pid = service.open_project(str(project))
    artifacts = []
    for group in service.list_artifact_groups(pid):
        detail = service.read_artifact(
            pid, group["artifact_type"], group["entity_id"], group["latest_version"]
        )
        data = detail["payload"]["data"]
        if group["artifact_type"] == "entity_discovery_results" and "processing_metadata" in data:
            # The step producer can be identified here. Keep every semantic field.
            data = dict(
                data,
                processing_metadata={
                    k: v for k, v in data["processing_metadata"].items() if k != "model"
                },
            )
        artifacts.append(
            {"artifact_type": group["artifact_type"], "entity_id": group["entity_id"], "data": data}
        )
    artifacts.sort(key=lambda g: (g["artifact_type"], g["entity_id"]))
    dest = E / "blind-v2" / (case + "-" + label + ".json")
    assert not dest.exists() and artifacts
    dump(dest, artifacts)
    print(dest, len(artifacts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES)
    parser.add_argument("arm", choices=["control", "candidate"])
    args = parser.parse_args()
    packet(args.case, args.arm)
