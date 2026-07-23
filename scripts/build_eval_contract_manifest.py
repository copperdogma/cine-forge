#!/usr/bin/env python3
"""Build or verify the immutable Story 208 eval-contract hash manifest."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = REPO_ROOT / "docs/evals/truth-audit-ledger.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "docs/evals/story-208-contract-manifest-v10.json"
REGISTRY_RELATIVE_PATH = "docs/evals/registry.yaml"
REGISTRY_HISTORY_KEYS = {"scores", "attempts"}

CONTRACT_KINDS = {
    "test_suite",
    "audit_harness",
    "promptfoo_task",
    "prompt",
    "llm_rubric",
    "python_scorer",
    "eval_transport",
    "custom_scorer_runner",
    "semantic_golden",
    "fixture_class",
    "registry_eval",
    "visual_lane",
    "runtime_root_lane",
}
ALLOWED_PREFIXES = (
    ".agents/skills/",
    "benchmarks/tasks/",
    "benchmarks/prompts/",
    "benchmarks/scorers/",
    "benchmarks/providers/",
    "benchmarks/golden/",
    "benchmarks/input/",
    "benchmarks/fixtures/",
    "benchmarks/video_understanding/",
    "benchmarks/previz_usefulness/",
    "benchmarks/final_render_provider_floor/",
    "benchmarks/scripts/",
    "tests/",
    "ui/tests/",
    "src/cine_forge/",
    "scripts/",
    "configs/recipes/",
    "docs/runbooks/",
)
ALLOWED_EXACT = {
    "AGENTS.md",
    "Makefile",
    "benchmarks/README.md",
    "docs/evals/README.md",
    "pyproject.toml",
    "ui/package.json",
    "docs/evals/registry.yaml",
    "docs/evals/truth-audit-ledger.yaml",
    "docs/methodology/state.yaml",
}
EXCLUDED_PREFIXES = (
    "benchmarks/results/",
    "output/",
    "docs/evals/attempts/",
    "docs/reports/",
    "docs/stories/",
)
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", "node_modules"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"unsupported registry contract value: {type(value).__name__}")


def _registry_contract_entry(path: Path) -> dict[str, Any]:
    """Hash eval definitions without mutable score and attempt history."""
    registry = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict) or not isinstance(registry.get("evals"), list):
        raise ValueError("eval registry must contain an evals list")
    contract_evals = []
    for index, row in enumerate(registry["evals"]):
        if not isinstance(row, dict):
            raise ValueError(f"eval registry row {index} must be a mapping")
        contract_evals.append(
            {key: value for key, value in row.items() if key not in REGISTRY_HISTORY_KEYS}
        )
    material = json.dumps(
        {"evals": contract_evals},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=_json_default,
    ).encode("utf-8")
    return {
        "path": f"{REGISTRY_RELATIVE_PATH}#contract-projection",
        "source_path": REGISTRY_RELATIVE_PATH,
        "projection": "all eval fields except mutable scores and attempts",
        "sha256": hashlib.sha256(material).hexdigest(),
        "bytes": len(material),
    }


def _is_contract_path(relative: str) -> bool:
    if relative in ALLOWED_EXACT:
        return True
    if relative.startswith(EXCLUDED_PREFIXES):
        return False
    return relative.startswith(ALLOWED_PREFIXES)


def _usable_file(path: Path, repo_root: Path, output_path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return False
    if path.resolve() == output_path.resolve() or not path.is_file():
        return False
    if any(part in EXCLUDED_PARTS for part in Path(relative).parts):
        return False
    if path.suffix in {".pyc", ".pyo"} or path.name == ".DS_Store":
        return False
    return _is_contract_path(relative)


def _expand_owned_path(repo_root: Path, owned_path: str, output_path: Path) -> set[Path]:
    matches = [Path(value) for value in glob.glob(str(repo_root / owned_path), recursive=True)]
    files: set[Path] = set()
    for match in matches:
        if match.is_dir():
            candidates = match.rglob("*")
        else:
            candidates = (match,)
        files.update(
            candidate.resolve()
            for candidate in candidates
            if _usable_file(candidate, repo_root, output_path)
        )
    return files


def collect_contract_files(
    repo_root: Path, ledger: dict[str, Any], output_path: Path
) -> list[Path]:
    """Resolve the audited maintained contracts, excluding historical result caches."""
    files: set[Path] = set()
    for surface in ledger.get("surfaces", []):
        if not isinstance(surface, dict) or surface.get("kind") not in CONTRACT_KINDS:
            continue
        for owned_path in surface.get("paths", []):
            if isinstance(owned_path, str):
                files.update(_expand_owned_path(repo_root, owned_path, output_path))

    for relative in ALLOWED_EXACT | {"scripts/build_eval_contract_manifest.py"}:
        path = repo_root / relative
        if _usable_file(path, repo_root, output_path):
            files.add(path.resolve())
    return sorted(files, key=lambda path: path.relative_to(repo_root).as_posix())


def build_manifest(repo_root: Path, ledger_path: Path, output_path: Path) -> dict[str, Any]:
    ledger = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(ledger, dict):
        raise ValueError("truth-audit ledger must be a mapping")
    entries = []
    for path in collect_contract_files(repo_root, ledger, output_path):
        relative = path.relative_to(repo_root).as_posix()
        if relative == REGISTRY_RELATIVE_PATH:
            entries.append(_registry_contract_entry(path))
        else:
            entries.append(
                {"path": relative, "sha256": _sha256(path), "bytes": path.stat().st_size}
            )
    entries.sort(key=lambda entry: entry["path"])
    bundle_material = "".join(
        f"{entry['path']}\0{entry['sha256']}\0{entry['bytes']}\n" for entry in entries
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "manifest_id": "story-208-eval-contracts-v10",
        "as_of": str(ledger.get("as_of", "")),
        "commit_identity_policy": (
            "the immutable Git commit containing this manifest identifies these "
            "exact contract bytes; a dirty working-tree copy is provisional"
        ),
        "source_ledger": ledger_path.relative_to(repo_root).as_posix(),
        "selection_policy": {
            "source": "terminal truth-audit ledger owned paths",
            "included_kinds": sorted(CONTRACT_KINDS),
            "excluded": [
                "historical benchmark result caches",
                "narrative attempt and story documents",
                "generated methodology views",
                "ignored runtime output directories",
                "mutable registry score and attempt history",
            ],
            "derived_contracts": [
                "docs/evals/registry.yaml eval definitions excluding scores and attempts"
            ],
        },
        "file_count": len(entries),
        "bundle_sha256": hashlib.sha256(bundle_material).hexdigest(),
        "files": entries,
    }


def validate_manifest(repo_root: Path, ledger_path: Path, output_path: Path) -> list[str]:
    if not output_path.exists():
        return [f"contract manifest does not exist: {output_path}"]
    try:
        recorded = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read contract manifest: {exc}"]
    expected = build_manifest(repo_root, ledger_path, output_path)
    if recorded == expected:
        return []
    errors = []
    if recorded.get("bundle_sha256") != expected["bundle_sha256"]:
        errors.append(
            "contract bundle drifted: "
            f"recorded={recorded.get('bundle_sha256')} current={expected['bundle_sha256']}"
        )
    if recorded.get("file_count") != expected["file_count"]:
        errors.append(
            f"contract file count drifted: recorded={recorded.get('file_count')} "
            f"current={expected['file_count']}"
        )
    return errors or ["contract manifest metadata drifted"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("choose exactly one of --write or --check")
    ledger_path = args.ledger.resolve()
    output_path = args.output.resolve()
    if args.write:
        payload = build_manifest(REPO_ROOT, ledger_path, output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(
            f"Eval contract manifest: WROTE {payload['file_count']} files "
            f"({payload['bundle_sha256']})"
        )
        return 0
    errors = validate_manifest(REPO_ROOT, ledger_path, output_path)
    if errors:
        print("Eval contract manifest: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Eval contract manifest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
