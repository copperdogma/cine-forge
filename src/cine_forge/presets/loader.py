"""Load style presets from YAML files in configs/style_presets/."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from cine_forge.presets.models import StylePreset

logger = logging.getLogger(__name__)

_PRESETS_DIR = Path(__file__).resolve().parents[3] / "configs" / "style_presets"

# Module-level cache — populated on first call.
_cache: list[StylePreset] | None = None


def _load_all() -> list[StylePreset]:
    """Read every *.yaml in the presets directory, validate, return sorted."""
    presets: list[StylePreset] = []
    if not _PRESETS_DIR.is_dir():
        logger.warning("Style presets directory not found: %s", _PRESETS_DIR)
        return presets

    for path in sorted(_PRESETS_DIR.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text())
            presets.append(StylePreset.model_validate(raw))
        except Exception:
            logger.exception("Failed to load style preset: %s", path.name)
    return presets


def list_presets() -> list[StylePreset]:
    """Return all built-in style presets (cached after first call)."""
    global _cache
    if _cache is None:
        _cache = _load_all()
    return list(_cache)


def load_preset(preset_id: str) -> StylePreset | None:
    """Look up a single preset by ID. Returns None if not found."""
    for p in list_presets():
        if p.preset_id == preset_id:
            return p
    return None


def clear_cache() -> None:
    """Force reload on next access (useful in tests)."""
    global _cache
    _cache = None
