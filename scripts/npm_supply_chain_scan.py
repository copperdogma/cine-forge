#!/usr/bin/env python3
"""Scan npm surfaces for known supply-chain incident indicators."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INCIDENTS = ROOT / "docs/security/npm-supply-chain-incidents.json"

PACKAGE_FILE_NAMES = {
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
}

SKIP_DIRS = {
    ".cache",
    ".git",
    ".next",
    ".nuxt",
    ".pnpm-store",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "venv",
}

WORKFLOW_FILE_RE = re.compile(r".+\.ya?ml$", re.IGNORECASE)
VERSION_PATTERN = r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?"
VERSION_RE = re.compile(rf"\b{VERSION_PATTERN}\b")


@dataclass
class Hit:
    kind: str
    path: str
    detail: str
    severity: str = "info"


@dataclass
class ProjectResult:
    key: str
    name: str
    path: str
    exists: bool
    scanned_package_files: int = 0
    scanned_workflows: int = 0
    affected_hits: list[Hit] = field(default_factory=list)
    dependency_leads: list[Hit] = field(default_factory=list)
    ioc_hits: list[Hit] = field(default_factory=list)
    related_clean_hits: list[Hit] = field(default_factory=list)
    workflow_flags: list[Hit] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_blocking_hit(self) -> bool:
        return bool(self.affected_hits or self.ioc_hits)

    @property
    def has_risky_workflow_combo(self) -> bool:
        return any(hit.severity in {"high", "medium"} for hit in self.workflow_flags)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan package manifests, lockfiles, and GitHub Actions workflows for known npm supply-chain incident indicators."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repo root to scan when --projects is not provided.",
    )
    parser.add_argument(
        "--projects",
        type=Path,
        default=None,
        help="Optional Conductor-style projects.yaml to scan multiple repos.",
    )
    parser.add_argument(
        "--include-root",
        action="store_true",
        help="Include --root as the first project when --projects is provided.",
    )
    parser.add_argument("--incidents", type=Path, default=DEFAULT_INCIDENTS)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if an affected package/version or IOC is found.",
    )
    parser.add_argument(
        "--project-key",
        default=None,
        help="Project key to use for a single-root scan. Defaults to the root directory name.",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        help="Project name to use for a single-root scan. Defaults to --project-key.",
    )
    parser.add_argument(
        "--no-conductor",
        action="store_true",
        help="Compatibility alias for omitting --include-root in Conductor scans.",
    )
    return parser.parse_args(argv)


def load_incidents(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_projects_yaml(path: Path) -> list[dict[str, str]]:
    projects: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#") or line.startswith("version:") or line.startswith("projects:"):
            continue
        if line.startswith("  - "):
            current = {}
            projects.append(current)
            if ":" in line[4:]:
                key, value = line[4:].split(":", 1)
                current[key.strip()] = strip_quotes(value.strip())
            continue
        if current is None:
            continue
        if line.startswith("    ") and not line.startswith("      - ") and ":" in line:
            key, value = line.strip().split(":", 1)
            key = key.strip()
            if key in {"key", "name", "path"}:
                current[key] = strip_quotes(value.strip())

    return projects


def load_projects(args: argparse.Namespace) -> list[dict[str, str]]:
    projects: list[dict[str, str]] = []
    root = args.root.expanduser().resolve()

    if args.projects is None:
        key = args.project_key or root.name
        projects.append({"key": key, "name": args.project_name or key, "path": str(root)})
        return projects

    if args.include_root and not args.no_conductor:
        key = args.project_key or root.name
        projects.append({"key": key, "name": args.project_name or key, "path": str(root)})

    for project in parse_projects_yaml(args.projects):
        key = str(project.get("key", "unknown"))
        projects.append(
            {
                "key": key,
                "name": str(project.get("name", key)),
                "path": str(project.get("path", "")),
            }
        )
    return projects


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def read_text_lossy(path: Path, max_bytes: int = 12_000_000) -> str:
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="ignore")


def iter_package_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        current = Path(dirpath)
        for filename in filenames:
            if filename in PACKAGE_FILE_NAMES:
                files.append(current / filename)
    return sorted(files)


def iter_workflow_files(root: Path) -> list[Path]:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return []
    return sorted(path for path in workflows.iterdir() if path.is_file() and WORKFLOW_FILE_RE.match(path.name))


def iter_all_file_names(root: Path) -> list[Path]:
    matches: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
        current = Path(dirpath)
        for filename in filenames:
            matches.append(current / filename)
    return matches


def window_has_version(text: str, package: str, version: str) -> bool:
    for match in re.finditer(re.escape(package), text):
        start = max(0, match.start() - 350)
        end = min(len(text), match.end() + 900)
        if version in text[start:end]:
            return True
    tarball = f"{package.rsplit('/', 1)[-1]}-{version}.tgz"
    return tarball in text and package in text


def dependency_maps(package_json: dict[str, Any]) -> list[dict[str, str]]:
    maps: list[dict[str, str]] = []
    for key in (
        "dependencies",
        "devDependencies",
        "optionalDependencies",
        "peerDependencies",
        "resolutions",
        "overrides",
    ):
        value = package_json.get(key)
        if isinstance(value, dict):
            maps.append({str(name): str(spec) for name, spec in value.items()})
    return maps


def json_manifest_hit(text: str, package: str, bad_versions: list[str]) -> str | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    for mapping in dependency_maps(data):
        spec = mapping.get(package)
        if not spec:
            continue
        for version in bad_versions:
            if spec == version or spec == f"npm:{package}@{version}":
                return f"{package}@{version} pinned in package.json"
        return f"{package} declared as {spec!r}; lockfile decides exact install"
    return None


def package_json_clean_hits(text: str, clean_patterns: list[re.Pattern[str]]) -> list[str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []
    hits: list[str] = []
    for mapping in dependency_maps(data):
        for package, spec in mapping.items():
            if any(pattern.search(package) for pattern in clean_patterns):
                hits.append(f"{package} declared as {spec!r}")
    return hits


def lock_json_clean_hits(text: str, clean_patterns: list[re.Pattern[str]]) -> list[str]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, dict):
        return []

    hits: set[str] = set()
    packages = data.get("packages")
    if isinstance(packages, dict):
        for raw_name, package_data in packages.items():
            if not isinstance(raw_name, str) or not isinstance(package_data, dict):
                continue
            name = raw_name.removeprefix("node_modules/")
            version = package_data.get("version")
            if isinstance(version, str) and any(pattern.search(name) for pattern in clean_patterns):
                hits.add(f"{name}@{version}")

    dependencies = data.get("dependencies")
    if isinstance(dependencies, dict):
        for name, package_data in dependencies.items():
            if not isinstance(name, str) or not isinstance(package_data, dict):
                continue
            version = package_data.get("version")
            if isinstance(version, str) and any(pattern.search(name) for pattern in clean_patterns):
                hits.add(f"{name}@{version}")

    return sorted(hits)


def clean_text_hits(text: str, clean_patterns: list[re.Pattern[str]]) -> list[str]:
    hits: set[str] = set()
    for pattern in clean_patterns:
        direct_lock_re = re.compile(rf"(?P<package>{pattern.pattern})@(?P<version>{VERSION_PATTERN})")
        for match in direct_lock_re.finditer(text):
            hits.add(f"{match.group('package')}@{match.group('version')}")
    return sorted(hits)


def scan_package_file(
    project_root: Path,
    path: Path,
    incidents: list[dict[str, Any]],
    result: ProjectResult,
) -> None:
    text = read_text_lossy(path)
    relative = rel(path, project_root)

    for incident in incidents:
        for package in incident.get("affected_packages", []):
            name = str(package["name"])
            versions = [str(version) for version in package.get("versions", [])]

            if path.name == "package.json":
                manifest = json_manifest_hit(text, name, versions)
                if manifest:
                    severity = "high" if "pinned" in manifest else "info"
                    if severity == "high":
                        result.affected_hits.append(Hit("affected-manifest", relative, manifest, severity))
                    else:
                        result.dependency_leads.append(Hit("affected-name", relative, manifest, severity))

            for version in versions:
                if window_has_version(text, name, version):
                    result.affected_hits.append(
                        Hit(
                            "affected-version",
                            relative,
                            f"{name}@{version} from {incident['id']}",
                            "high",
                        )
                    )

        for ioc in incident.get("iocs", []):
            value = str(ioc["value"])
            if value in text:
                result.ioc_hits.append(
                    Hit(
                        f"ioc-{ioc.get('type', 'string')}",
                        relative,
                        f"{value}: {ioc.get('note', 'incident indicator')}",
                        "high",
                    )
                )

        clean_patterns = [
            re.compile(str(note["pattern"])) for note in incident.get("clean_package_notes", [])
        ]
        if path.name == "package.json":
            clean_hits = package_json_clean_hits(text, clean_patterns)
        elif path.name in {"package-lock.json", "npm-shrinkwrap.json"}:
            clean_hits = lock_json_clean_hits(text, clean_patterns)
        else:
            clean_hits = clean_text_hits(text, clean_patterns)
        for clean_hit in clean_hits:
            result.related_clean_hits.append(Hit("related-clean-package", relative, clean_hit, "info"))


def scan_ioc_file_names(project_root: Path, incidents: list[dict[str, Any]], result: ProjectResult) -> None:
    file_iocs = {
        str(ioc["value"]): str(ioc.get("note", "incident indicator"))
        for incident in incidents
        for ioc in incident.get("iocs", [])
        if ioc.get("type") == "file"
    }
    if not file_iocs:
        return
    for path in iter_all_file_names(project_root):
        note = file_iocs.get(path.name)
        if note:
            result.ioc_hits.append(Hit("ioc-file-name", rel(path, project_root), f"{path.name}: {note}", "high"))


def workflow_labels(text: str) -> set[str]:
    labels: set[str] = set()
    lower = text.lower()
    if "pull_request_target" in lower:
        labels.add("pull_request_target")
    if "actions/cache" in lower:
        labels.add("actions/cache")
    if re.search(r"id-token\s*:\s*write", lower):
        labels.add("id-token:write")
    if re.search(r"\b(npm|pnpm|yarn)\s+(ci|install|add|update|upgrade)\b", lower):
        labels.add("dependency-install")
    if re.search(r"\b(npm|pnpm)\s+publish\b|yarn\s+npm\s+publish", lower):
        labels.add("npm-publish")
    if "secrets." in lower or "${{ secrets" in lower:
        labels.add("secrets")
    if "ignore-scripts" in lower:
        labels.add("ignore-scripts")
    return labels


def scan_workflow(project_root: Path, path: Path, result: ProjectResult) -> None:
    text = read_text_lossy(path)
    labels = workflow_labels(text)
    if not labels:
        return

    relative = rel(path, project_root)
    detail = ", ".join(sorted(labels))
    severity = "info"
    if "pull_request_target" in labels and ("dependency-install" in labels or "actions/cache" in labels):
        severity = "high"
    elif "id-token:write" in labels and "dependency-install" in labels:
        severity = "medium"
    elif "secrets" in labels and "dependency-install" in labels:
        severity = "medium"
    elif "npm-publish" in labels and "dependency-install" in labels:
        severity = "medium"

    result.workflow_flags.append(Hit("workflow-supply-chain-surface", relative, detail, severity))


def dedupe_hits(hits: list[Hit]) -> list[Hit]:
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[Hit] = []
    for hit in hits:
        key = (hit.kind, hit.path, hit.detail, hit.severity)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
    return deduped


def scan_project(project: dict[str, str], incidents: list[dict[str, Any]]) -> ProjectResult:
    path = Path(project["path"]).expanduser()
    result = ProjectResult(
        key=project["key"],
        name=project["name"],
        path=str(path),
        exists=path.exists(),
    )
    if not path.exists():
        result.warnings.append("project path does not exist")
        return result

    package_files = iter_package_files(path)
    result.scanned_package_files = len(package_files)
    for package_file in package_files:
        scan_package_file(path, package_file, incidents, result)

    scan_ioc_file_names(path, incidents, result)

    workflows = iter_workflow_files(path)
    result.scanned_workflows = len(workflows)
    for workflow in workflows:
        scan_workflow(path, workflow, result)

    result.affected_hits = dedupe_hits(result.affected_hits)
    result.dependency_leads = dedupe_hits(result.dependency_leads)
    result.ioc_hits = dedupe_hits(result.ioc_hits)
    result.related_clean_hits = dedupe_hits(result.related_clean_hits)
    result.workflow_flags = dedupe_hits(result.workflow_flags)
    return result


def hit_to_json(hit: Hit) -> dict[str, str]:
    return {
        "kind": hit.kind,
        "path": hit.path,
        "detail": hit.detail,
        "severity": hit.severity,
    }


def result_to_json(result: ProjectResult) -> dict[str, Any]:
    return {
        "key": result.key,
        "name": result.name,
        "path": result.path,
        "exists": result.exists,
        "scanned_package_files": result.scanned_package_files,
        "scanned_workflows": result.scanned_workflows,
        "affected_hits": [hit_to_json(hit) for hit in result.affected_hits],
        "dependency_leads": [hit_to_json(hit) for hit in result.dependency_leads],
        "ioc_hits": [hit_to_json(hit) for hit in result.ioc_hits],
        "related_clean_hits": [hit_to_json(hit) for hit in result.related_clean_hits],
        "workflow_flags": [hit_to_json(hit) for hit in result.workflow_flags],
        "warnings": result.warnings,
    }


def print_text(results: list[ProjectResult], incidents: dict[str, Any]) -> None:
    incident_ids = ", ".join(str(incident["id"]) for incident in incidents.get("incidents", []))
    print("npm supply-chain scan")
    print(f"incidents: {incident_ids}")
    print(f"projects: {len(results)}")
    print()

    for result in results:
        status = "missing" if not result.exists else "checked"
        if result.has_blocking_hit:
            status = "attention"
        print(f"{result.key}: {status}")
        print(f"  path: {result.path}")
        print(f"  package files: {result.scanned_package_files}; workflows: {result.scanned_workflows}")

        for warning in result.warnings:
            print(f"  warning: {warning}")
        for hit in result.affected_hits:
            print(f"  affected [{hit.severity}] {hit.path}: {hit.detail}")
        for hit in result.dependency_leads:
            print(f"  dependency lead [{hit.severity}] {hit.path}: {hit.detail}")
        for hit in result.ioc_hits:
            print(f"  ioc [{hit.severity}] {hit.path}: {hit.detail}")
        for hit in result.related_clean_hits[:8]:
            print(f"  related clean package: {hit.path}: {hit.detail}")
        if len(result.related_clean_hits) > 8:
            print(f"  related clean package: ... {len(result.related_clean_hits) - 8} more")
        for hit in result.workflow_flags:
            print(f"  workflow [{hit.severity}] {hit.path}: {hit.detail}")
        if not (
            result.affected_hits
            or result.dependency_leads
            or result.ioc_hits
            or result.related_clean_hits
            or result.workflow_flags
            or result.warnings
        ):
            print("  no npm incident indicators or workflow flags")
        print()

    affected_count = sum(len(result.affected_hits) for result in results)
    dependency_leads = sum(len(result.dependency_leads) for result in results)
    ioc_count = sum(len(result.ioc_hits) for result in results)
    risky_workflows = sum(1 for result in results if result.has_risky_workflow_combo)
    print("summary:")
    print(f"  affected hits: {affected_count}")
    print(f"  dependency leads: {dependency_leads}")
    print(f"  ioc hits: {ioc_count}")
    print(f"  risky workflow combinations: {risky_workflows}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    incidents = load_incidents(args.incidents)
    projects = load_projects(args)
    results = [scan_project(project, incidents.get("incidents", [])) for project in projects]

    if args.json:
        print(
            json.dumps(
                {
                    "incidents": incidents.get("incidents", []),
                    "results": [result_to_json(result) for result in results],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text(results, incidents)

    if args.strict and any(result.has_blocking_hit for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
