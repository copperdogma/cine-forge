"""Integrity checks for repository-retained visual eval evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from cine_forge.evals.result_json import load_result_json

STORYBOARD_RETAINED_SCHEMA_VERSION = "storyboard-generation-quality-v3"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for one retained file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_file_inventory(
    root: Path,
    *,
    manifest_name: str = "manifest.json",
) -> list[dict[str, Any]]:
    """Hash every retained dataset file except the self-describing manifest."""
    if root.is_symlink():
        raise ValueError("retained media root cannot be a symlink")
    resolved_root = root.resolve()
    inventory: list[dict[str, Any]] = []
    for path in sorted(resolved_root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"retained media cannot contain a symlink: {path}")
        if not path.is_file() or path.name == manifest_name:
            continue
        try:
            path.resolve(strict=True).relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"retained media file escapes its root: {path}") from exc
        inventory.append(
            {
                "path": path.relative_to(resolved_root).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return inventory


def validate_retained_media_manifest(
    manifest_path: Path,
    *,
    expected_schema_version: str = STORYBOARD_RETAINED_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Fail when a retained dataset is missing, changed, or has unlisted files."""
    if manifest_path.is_symlink():
        raise ValueError("retained media manifest cannot be a symlink")
    resolved_manifest = manifest_path.resolve(strict=True)
    dataset_root = resolved_manifest.parent
    payload = load_result_json(resolved_manifest)
    if not isinstance(payload, dict):
        raise ValueError("retained media manifest must contain one object")
    schema_version = payload.get("schema_version")
    if schema_version != expected_schema_version:
        raise ValueError(
            "retained media manifest schema mismatch: "
            f"expected {expected_schema_version!r}, got {schema_version!r}"
        )

    raw_inventory = payload.get("file_inventory")
    if not isinstance(raw_inventory, list) or not raw_inventory:
        raise ValueError("retained media manifest requires a non-empty file_inventory")
    declared: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(raw_inventory):
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "bytes"}:
            raise ValueError(
                f"retained media file_inventory[{index}] must contain path, sha256, bytes"
            )
        relative = _validated_relative_path(row["path"], location=f"file_inventory[{index}]")
        if relative.name == resolved_manifest.name:
            raise ValueError("retained media manifest cannot inventory itself")
        key = relative.as_posix()
        if key in declared:
            raise ValueError(f"retained media file_inventory duplicates {key}")
        digest = row["sha256"]
        size = row["bytes"]
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"retained media file {key} has invalid sha256")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError(f"retained media file {key} has invalid byte count")
        declared[key] = row

    actual = {row["path"]: row for row in build_file_inventory(dataset_root)}
    missing = sorted(set(declared) - set(actual))
    extra = sorted(set(actual) - set(declared))
    if missing or extra:
        raise ValueError(
            f"retained media inventory mismatch; missing={missing}; extra={extra}"
        )
    for key, expected in declared.items():
        observed = actual[key]
        if observed["bytes"] != expected["bytes"]:
            raise ValueError(f"retained media byte count mismatch for {key}")
        if observed["sha256"] != expected["sha256"]:
            raise ValueError(f"retained media sha256 mismatch for {key}")
    return payload


def validate_retained_media_provenance(
    manifest_path: Path,
    *,
    repo_root: Path,
    expected_schema_version: str = STORYBOARD_RETAINED_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Validate dataset bytes plus every repository source named by its manifest."""
    payload = validate_retained_media_manifest(
        manifest_path,
        expected_schema_version=expected_schema_version,
    )
    root = repo_root.resolve()
    _validate_repo_hash_pair(
        payload,
        path_key="runtime_result",
        hash_key="runtime_result_sha256",
        repo_root=root,
    )
    _validate_repo_hash_pair(
        payload,
        path_key="fixture_manifest",
        hash_key="fixture_manifest_sha256",
        repo_root=root,
    )
    contracts = payload.get("contract_sha256")
    if not isinstance(contracts, dict) or not contracts:
        raise ValueError("retained media manifest requires contract_sha256")
    for raw_path, digest in contracts.items():
        path = _resolve_repo_path(raw_path, repo_root=root, location="contract_sha256")
        _require_digest(path, digest, location=f"contract_sha256[{raw_path!r}]")
    return payload


def _validate_repo_hash_pair(
    payload: dict[str, Any],
    *,
    path_key: str,
    hash_key: str,
    repo_root: Path,
) -> None:
    path = _resolve_repo_path(payload.get(path_key), repo_root=repo_root, location=path_key)
    _require_digest(path, payload.get(hash_key), location=hash_key)


def _resolve_repo_path(value: object, *, repo_root: Path, location: str) -> Path:
    relative = _validated_relative_path(value, location=location)
    unresolved = repo_root / relative
    _reject_symlink_chain(unresolved, root=repo_root, location=location)
    path = unresolved.resolve(strict=True)
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"{location} must resolve inside the repository") from exc
    if not path.is_file():
        raise ValueError(f"{location} must resolve to a file")
    return path


def _reject_symlink_chain(path: Path, *, root: Path, location: str) -> None:
    root = root.resolve()
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError(f"{location} cannot resolve through a symlink")
        if root not in current.parents:
            raise ValueError(f"{location} must resolve inside the repository")
        current = current.parent


def _validated_relative_path(value: object, *, location: str) -> PurePosixPath:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be a non-empty repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() in {"", "."}:
        raise ValueError(f"{location} must be a safe repository-relative path")
    return path


def _require_digest(path: Path, expected: object, *, location: str) -> None:
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(f"{location} must be a SHA-256 digest")
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(
            f"{location} does not match {path}: expected {expected}, got {observed}"
        )
