"""Module discovery for pipeline stages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ModuleManifest(BaseModel):
    """Normalized module manifest data."""

    module_id: str
    stage: str
    description: str
    input_schemas: list[str] = Field(default_factory=list)
    output_schemas: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    module_path: str
    entrypoint: str


def discover_modules(modules_root: Path) -> dict[str, ModuleManifest]:
    """Discover module manifests under stage/module_id folders."""
    registry: dict[str, ModuleManifest] = {}
    for manifest_path in modules_root.glob("*/*/module.yaml"):
        with manifest_path.open("r", encoding="utf-8") as file:
            payload = yaml.safe_load(file) or {}
        module_dir = manifest_path.parent
        manifest = ModuleManifest.model_validate(
            {
                **payload,
                "module_path": str(module_dir),
                "entrypoint": str(module_dir / "main.py"),
            }
        )
        registry[manifest.module_id] = manifest
    return registry
