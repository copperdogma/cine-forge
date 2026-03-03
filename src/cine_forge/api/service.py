"""Service layer for CineForge API backend."""

from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

import yaml
from rapidfuzz import fuzz as _rfuzz

from cine_forge.api.artifact_manager import ArtifactManager
from cine_forge.api.chat_store import ChatStore
from cine_forge.api.exceptions import ServiceError
from cine_forge.api.run_orchestrator import RunOrchestrator
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.ingest.story_ingest_v1.main import (
    SUPPORTED_FILE_FORMATS,
    read_source_text_with_diagnostics,
)
from cine_forge.roles.runtime import RoleCatalog, RoleContext
from cine_forge.schemas import ArtifactMetadata, ArtifactRef

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Search helpers — fuzzy matching for search_entities
# ---------------------------------------------------------------------------

def _parse_scene_number(query: str) -> int | None:
    """Parse 'sc2', 'sc 2', 'sc-2', 'scene2', 'scene 2' → scene number or None."""
    m = re.match(r'^sc(?:ene)?\s*[-]?\s*(\d+)$', query.strip().lower())
    return int(m.group(1)) if m else None


def _is_scene_all(query: str) -> bool:
    """Return True if the query is a bare scene prefix ('sc' or 'scene') — return all scenes."""
    return query.strip().lower() in ("sc", "scene")


def _fuzzy_match(query: str, text: str) -> bool:
    """True if query matches text via exact substring, initials, or fuzzy ratio.

    Three strategies applied in order:
    - Exact substring: 'mariner' in 'The Mariner' (always checked, fast path)
    - Initials: 'ym' → 'Young Mariner' (2–5 all-alpha chars, first letter of each word)
    - Fuzzy ratio: 'marinner' → 'mariner' (queries ≥ 4 chars, threshold 75/100)
    """
    q = query.lower()
    t = text.lower()
    if q in t:
        return True
    if 2 <= len(q) <= 5 and q.isalpha():
        words = [w for w in t.split() if w]
        if q == "".join(w[0] for w in words):
            return True
    if len(q) >= 4:
        score = max(_rfuzz.ratio(q, t), _rfuzz.partial_ratio(q, t))
        if score >= 75:
            return True
    return False


class OperatorConsoleService:
    """Coordinates project registration, run execution, and artifact browsing."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self._project_registry: dict[str, Path] = {}
        self._chat_store = ChatStore()
        self._orchestrator = RunOrchestrator(
            workspace_root=self.workspace_root,
            chat_store=self._chat_store,
            project_registry=self._project_registry,
            project_path_resolver=self.require_project_path,
            project_json_reader=self._read_project_json,
        )
        self.role_catalog = RoleCatalog()
        self.role_catalog.load_definitions()
        self._artifact_mgr = ArtifactManager(
            project_path_resolver=self.require_project_path,
            role_context_factory=self.get_role_context,
            role_catalog=self.role_catalog,
        )

    @staticmethod
    def normalize_project_path(project_path: str) -> Path:
        return Path(project_path).expanduser().resolve(strict=False)

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to a URL-friendly slug."""
        slug = text.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        return slug or "project"

    def ensure_unique_slug(self, slug: str) -> str:
        """Return *slug* if unused, otherwise append -2, -3, etc."""
        output_dir = self.workspace_root / "output"
        if not output_dir.exists():
            return slug
        existing = {p.name for p in output_dir.iterdir() if p.is_dir()}
        if slug not in existing:
            return slug
        for n in range(2, 1000):
            candidate = f"{slug}-{n}"
            if candidate not in existing:
                return candidate
        return f"{slug}-{uuid.uuid4().hex[:6]}"

    def quick_scan(self, filename: str, content: bytes) -> dict[str, Any]:
        """Extract a title and slug from a raw file content (even if binary)."""
        # 1. Use ingestion logic to extract text from the first part of the file
        # We save to a temporary file to use the existing diagnostic reader
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            # We only read the first part of the file if it's huge, but for quick-scan 
            # the content passed here should already be reasonably sized (e.g. 1MB).
            # read_source_text_with_diagnostics handles PDF/DOCX/Fountain
            text, _diag = read_source_text_with_diagnostics(tmp_path)
            
            # Use the first 8000 characters for the LLM
            snippet = text[:8000]
            return self.generate_slug(snippet, filename)
        except Exception as exc:
            log.warning("Quick scan failed: %s", exc)
            # Fallback to filename-based generation
            title = self._clean_display_name(Path("x"), [filename])
            slug = self.slugify(title)
            slug = self.ensure_unique_slug(slug)
            return {"slug": slug, "display_name": title, "alternatives": []}
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def generate_slug(
        self, content_snippet: str, original_filename: str,
    ) -> dict[str, Any]:
        """Use a fast LLM to extract a title and slug from screenplay content."""
        prompt = (
            "You are a screenplay title extractor. Given the first few pages of a "
            "screenplay or script document, identify the canonical title.\n\n"
            "Guidelines:\n"
            "- Look for a title page (usually centered, large text at the start)\n"
            "- Look for headers or 'PILOT' or 'EPISODE' tags\n"
            "- If an 'ALTERNATE TITLE' is provided, include it in the main title "
            "or as an alternative\n"
            "- Be precise. Do not guess if it's just random names.\n\n"
            "Respond with JSON only:\n"
            '{"title": "The Main Title", "alt_title": "Alternative Name or null"}\n\n'
            f"Original filename: {original_filename}\n\n"
            f"--- Document content (start of script) ---\n{content_snippet}"
        )
        try:
            from cine_forge.ai.llm import call_llm
            result, _meta = call_llm(
                prompt=prompt,
                model="claude-sonnet-4-6", # Upgraded to Sonnet for better precision on "good tests"
                max_retries=1,
                max_tokens=256,
                temperature=0.0,
            )
            text = result if isinstance(result, str) else str(result)
            # Strip markdown fences if present
            text = text.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
                text = text.strip()
            # Parse the JSON response
            parsed = json.loads(text)
            title = str(parsed.get("title", "")).strip()
            alt = str(parsed.get("alt_title") or "").strip()
        except Exception:
            log.warning("LLM slug generation failed, falling back to filename")
            title = ""
            alt = ""

        # Fall back to filename-derived name
        if not title:
            title = self._clean_display_name(Path("x"), [original_filename])

        slug = self.slugify(title)
        slug = self.ensure_unique_slug(slug)
        alternatives = [alt] if alt and alt.lower() != "null" else []

        return {"slug": slug, "display_name": title, "alternatives": alternatives}

    @staticmethod
    def _write_project_json(
        project_path: Path,
        slug: str,
        display_name: str,
        human_control_mode: str | None = None,
        interaction_mode: str | None = None,
        style_packs: dict[str, str] | None = None,
        ui_preferences: dict[str, Any] | None = None,
    ) -> None:
        """Write project.json with slug, display_name, and optional settings.

        Uses a read-modify-write approach to preserve existing data.
        """
        pj_path = project_path / "project.json"

        # Read existing data if present
        existing = {}
        if pj_path.exists():
            try:
                existing = json.loads(pj_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        # Update with new values
        existing["slug"] = slug
        existing["display_name"] = display_name
        if human_control_mode is not None:
            existing["human_control_mode"] = human_control_mode
        if interaction_mode is not None:
            existing["interaction_mode"] = interaction_mode
        if style_packs is not None:
            existing["style_packs"] = style_packs

        # Merge ui_preferences if provided (shallow merge)
        if ui_preferences is not None:
            existing_prefs = existing.get("ui_preferences", {})
            existing_prefs.update(ui_preferences)
            existing["ui_preferences"] = existing_prefs

        pj_path.write_text(
            json.dumps(existing, indent=2), encoding="utf-8",
        )

    @staticmethod
    def _read_project_json(project_path: Path) -> dict[str, Any] | None:
        pj = project_path / "project.json"
        if not pj.exists():
            return None
        try:
            return json.loads(pj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def update_project_settings(
        self,
        project_id: str,
        display_name: str | None = None,
        human_control_mode: str | None = None,
        interaction_mode: str | None = None,
        style_packs: dict[str, str] | None = None,
        ui_preferences: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update mutable project settings (display_name, human_control_mode, etc.)."""
        path = self.require_project_path(project_id)
        pj = self._read_project_json(path) or {"slug": project_id}

        # Update human_control_mode and sync to config if provided
        if human_control_mode is not None:
            self._sync_human_control_mode_to_config(project_id, human_control_mode)

        # Write back with all changes
        self._write_project_json(
            path,
            pj.get("slug", project_id),
            display_name if display_name is not None else pj.get("display_name", project_id),
            human_control_mode=(
                human_control_mode if human_control_mode is not None
                else pj.get("human_control_mode")
            ),
            interaction_mode=(
                interaction_mode if interaction_mode is not None
                else pj.get("interaction_mode")
            ),
            style_packs=style_packs if style_packs is not None else pj.get("style_packs"),
            ui_preferences=ui_preferences,
        )

        return self.project_summary(project_id)

    def _sync_human_control_mode_to_config(self, project_id: str, mode: str) -> None:
        """Update the canonical ProjectConfig artifact if it exists."""
        try:
            project_path = self.require_project_path(project_id)
            store = ArtifactStore(project_dir=project_path)
            versions = store.list_versions(artifact_type="project_config", entity_id="project")
            if not versions:
                log.info("No project_config found to sync human_control_mode")
                return

            latest_ref = versions[-1]
            artifact = store.load_artifact(latest_ref)
            data = artifact.data
            
            log.info("Syncing human_control_mode to project_config v%d", latest_ref.version)
            
            # Use model_dump if it's a Pydantic model, otherwise dict()
            if hasattr(data, "model_dump"):
                new_data = data.model_dump()
            elif isinstance(data, dict):
                new_data = dict(data)
            else:
                new_data = dict(data) # Fallback

            if new_data.get("human_control_mode") == mode:
                return

            new_data["human_control_mode"] = mode

            metadata = ArtifactMetadata(
                lineage=[latest_ref],
                intent="Update human control mode.",
                rationale=f"User changed mode to '{mode}' via settings.",
                confidence=1.0,
                source="human",
                producing_module="operator_console.settings",
            )
            store.save_artifact(
                artifact_type="project_config",
                entity_id="project",
                data=new_data,
                metadata=metadata,
            )
        except Exception:
            log.exception("Failed to sync human_control_mode to ProjectConfig")

    def create_project_from_slug(self, slug: str, display_name: str) -> str:
        """Create a new project under output/{slug}/ and return the slug as project_id."""
        slug = self.ensure_unique_slug(slug)
        project_path = self.workspace_root / "output" / slug
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "artifacts").mkdir(parents=True, exist_ok=True)
        (project_path / "graph").mkdir(parents=True, exist_ok=True)
        self._write_project_json(project_path, slug, display_name)
        self._project_registry[slug] = project_path
        return slug

    def create_project(self, project_path: str) -> str:
        """Legacy: create project from an explicit path (slug = folder name)."""
        path = self.normalize_project_path(project_path)
        path.mkdir(parents=True, exist_ok=True)
        (path / "artifacts").mkdir(parents=True, exist_ok=True)
        (path / "graph").mkdir(parents=True, exist_ok=True)
        slug = path.name
        self._write_project_json(path, slug, self._clean_display_name(path, []))
        self._project_registry[slug] = path
        return slug

    def open_project(self, project_path: str) -> str:
        path = self.normalize_project_path(project_path)
        if not path.exists() or not path.is_dir():
            raise ServiceError(
                code="project_not_found",
                message=f"Project directory not found: {path}",
                hint="Create the directory first or choose an existing project path.",
                status_code=404,
            )
        missing = [name for name in ("artifacts", "graph") if not (path / name).exists()]
        if missing:
            missing_csv = ", ".join(missing)
            raise ServiceError(
                code="invalid_project_structure",
                message=f"Project directory missing required paths: {missing_csv}",
                hint="Run 'New Project' to initialize project structure.",
                status_code=422,
            )
        slug = path.name
        # Backfill project.json for legacy folders
        if not (path / "project.json").exists():
            inputs = self._list_inputs_from_path(path)
            input_files = [inp["original_name"] for inp in inputs]
            display_name = self._clean_display_name(path, input_files)
            self._write_project_json(path, slug, display_name)
        self._project_registry[slug] = path
        return slug

    def get_role_context(self, project_id: str) -> RoleContext:
        """Get a RoleContext for the specified project."""
        project_path = self.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)
        
        # Load style pack selections from project.json
        pj = self._read_project_json(project_path) or {}
        style_packs = pj.get("style_packs", {})
        
        # Determine model resolver (could use project defaults)
        default_model = pj.get("default_model", "claude-sonnet-4-6")
        
        return RoleContext(
            catalog=self.role_catalog,
            project_dir=project_path,
            store=store,
            model_resolver=lambda _role_id: default_model,
            style_pack_selections=style_packs,
        )

    def require_project_path(self, project_id: str) -> Path:
        path = self._project_registry.get(project_id)
        if path is not None and self._is_valid_project_dir(path):
            return path

        # Survive backend restarts and deep links: resolve known slugs from disk.
        resolved = self._resolve_project_path(project_id)
        if resolved is not None:
            self._project_registry[project_id] = resolved
            return resolved

        raise ServiceError(
            code="project_not_opened",
            message="Unknown project_id for this backend session.",
            hint="Call /api/projects/open or /api/projects/new before project-scoped APIs.",
            status_code=404,
        )

    def get_artifact_store(self, project_id: str) -> ArtifactStore:
        """Return an ArtifactStore rooted at the resolved project path."""
        return ArtifactStore(project_dir=self.require_project_path(project_id))

    def _resolve_project_path(self, project_id: str) -> Path | None:
        candidate = self.workspace_root / "output" / project_id
        if self._is_valid_project_dir(candidate):
            return candidate

        runs_dir = self.workspace_root / "output" / "runs"
        if runs_dir.exists():
            for run_dir in runs_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                run_meta_path = run_dir / "run_meta.json"
                if not run_meta_path.exists():
                    run_meta_path = run_dir / "operator_console_run_meta.json"
                if not run_meta_path.exists():
                    continue
                try:
                    run_meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                if str(run_meta.get("project_id") or "") != project_id:
                    continue
                project_path_raw = run_meta.get("project_path")
                if not isinstance(project_path_raw, str):
                    continue
                project_path = self.normalize_project_path(project_path_raw)
                if self._is_valid_project_dir(project_path):
                    return project_path
        return None

    def project_summary(self, project_id: str) -> dict[str, Any]:
        path = self.require_project_path(project_id)
        artifact_groups = len(self.list_artifact_groups(project_id))
        run_count = len(self.list_runs(project_id))
        inputs = self.list_project_inputs(project_id)
        input_files = [inp["original_name"] for inp in inputs]
        # Prefer display_name from project.json, fall back to heuristic
        pj = self._read_project_json(path)
        display_name = (pj or {}).get("display_name") or self._clean_display_name(path, input_files)
        ui_preferences = (pj or {}).get("ui_preferences", {})
        human_control_mode = (pj or {}).get("human_control_mode", "autonomous")
        interaction_mode = (pj or {}).get("interaction_mode", "balanced")
        return {
            "project_id": project_id,
            "display_name": display_name,
            "artifact_groups": artifact_groups,
            "run_count": run_count,
            "has_inputs": len(inputs) > 0,
            "input_files": input_files,
            "ui_preferences": ui_preferences,
            "human_control_mode": human_control_mode,
            "interaction_mode": interaction_mode,
        }

    @staticmethod
    def _list_inputs_from_path(project_path: Path) -> list[dict[str, Any]]:
        """List input files from a project path (no project_id needed)."""
        inputs_dir = project_path / "inputs"
        if not inputs_dir.exists():
            return []
        inputs: list[dict[str, Any]] = []
        for entry in sorted(inputs_dir.iterdir()):
            if not entry.is_file():
                continue
            name = entry.name
            original_name = re.sub(r"^[0-9a-f]{8}_", "", name)
            inputs.append({
                "filename": name,
                "original_name": original_name,
                "size_bytes": entry.stat().st_size,
                "stored_path": str(entry),
            })
        return inputs

    def list_project_inputs(self, project_id: str) -> list[dict[str, Any]]:
        """List input files for a project."""
        project_path = self.require_project_path(project_id)
        inputs_dir = project_path / "inputs"
        if not inputs_dir.exists():
            return []
        inputs: list[dict[str, Any]] = []
        for entry in sorted(inputs_dir.iterdir()):
            if not entry.is_file():
                continue
            # Files stored as {uuid}_{original_name}
            name = entry.name
            # Strip the uuid prefix (8 hex chars + underscore)
            original_name = re.sub(r"^[0-9a-f]{8}_", "", name)
            inputs.append({
                "filename": name,
                "original_name": original_name,
                "size_bytes": entry.stat().st_size,
                "stored_path": str(entry),
            })
        return inputs

    def get_pipeline_graph(self, project_id: str) -> dict[str, Any]:
        """Return the pipeline capability graph with dynamic status."""
        from cine_forge.pipeline.graph import compute_pipeline_graph

        project_path = self.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)

        # Check for active runs to mark in-progress stages.
        active_stages: set[str] | None = None
        try:
            runs = self.list_runs(project_id)
            for run in runs:
                if run.get("state") == "running":
                    # Collect stage IDs that are currently running.
                    stages = run.get("stages", {})
                    active_stages = {
                        sid for sid, sdata in stages.items()
                        if isinstance(sdata, dict) and sdata.get("status") == "running"
                    }
                    break
        except Exception:
            pass  # Non-critical: proceed without active stage detection.

        return compute_pipeline_graph(store, active_run_stages=active_stages)

    def read_project_input(self, project_id: str, filename: str) -> str:
        """Read a project input file as text. Guards against path traversal."""
        project_path = self.require_project_path(project_id)
        inputs_dir = project_path / "inputs"
        # Prevent path traversal
        safe_name = Path(filename).name
        if safe_name != filename or ".." in filename:
            raise ServiceError(
                code="invalid_filename",
                message="Invalid filename.",
                hint="Use the exact filename from the inputs listing.",
                status_code=400,
            )
        target = inputs_dir / safe_name
        if not target.exists() or not target.is_file():
            raise ServiceError(
                code="input_not_found",
                message=f"Input file not found: {filename}",
                hint="List available inputs via GET /api/projects/{id}/inputs.",
                status_code=404,
            )

        file_format = target.suffix.lower().lstrip(".")
        if file_format in SUPPORTED_FILE_FORMATS:
            text, _diagnostics = read_source_text_with_diagnostics(target)
            if not text.strip():
                raise ServiceError(
                    code="input_extraction_failed",
                    message=(
                        f"Unable to extract readable text from '{filename}'. "
                        "The document appears image-only or extraction failed."
                    ),
                    hint=(
                        "Upload a text-selectable PDF/DOCX or enable OCR-capable extraction "
                        "in the runtime environment."
                    ),
                    status_code=422,
                )
            return text
        return target.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _clean_display_name(project_path: Path, input_files: list[str]) -> str:
        """Derive a human-readable display name from input files or project path."""
        # Prefer the input filename (cleaned up)
        raw = input_files[0] if input_files else project_path.name
        # Strip file extension
        name = re.sub(r"\.(pdf|fdx|fountain|txt|md|docx)$", "", raw, flags=re.IGNORECASE)
        # Strip leading timestamp patterns (e.g., 1771196674098_)
        name = re.sub(r"^\d{10,15}[_-]", "", name)
        # Replace underscores and hyphens with spaces
        name = name.replace("_", " ").replace("-", " ")
        # Remove common suffixes like "No ID"
        name = re.sub(r"\s+No\s+ID\s*$", "", name, flags=re.IGNORECASE)
        # Collapse multiple spaces
        name = re.sub(r"\s+", " ", name).strip()
        # Title case
        if name:
            name = name.title()
        return name or project_path.name

    def list_roles(self) -> list[dict[str, Any]]:
        """List all available roles from the catalog."""
        roles = self.role_catalog.list_roles()
        return [
            {
                "role_id": r.role_id,
                "display_name": r.display_name,
                "tier": r.tier.value,
                "description": r.description,
                "style_pack_slot": r.style_pack_slot.value,
            }
            for r in roles.values()
        ]

    def _discover_project_candidates(self) -> dict[str, Path]:
        """Discover all valid project directories (cheap — no project_summary calls)."""
        candidates: dict[str, Path] = {}

        # 1. Already-registered projects
        for slug, project_path in self._project_registry.items():
            if self._is_valid_project_dir(project_path):
                candidates[slug] = project_path

        # 2. Discover projects from run metadata
        runs_dir = self.workspace_root / "output" / "runs"
        if runs_dir.exists():
            for run_dir in runs_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                meta_path = run_dir / "run_meta.json"
                if not meta_path.exists():
                    meta_path = run_dir / "operator_console_run_meta.json"
                if not meta_path.exists():
                    continue
                try:
                    run_meta = json.loads(meta_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                project_path_raw = run_meta.get("project_path")
                if not isinstance(project_path_raw, str):
                    continue
                project_path = self.normalize_project_path(project_path_raw)
                if not self._is_valid_project_dir(project_path):
                    continue
                slug = project_path.name
                candidates[slug] = project_path
                self._project_registry[slug] = project_path

        # 3. Scan output/ for project folders
        output_root = self.workspace_root / "output"
        if output_root.exists():
            for child in output_root.iterdir():
                if not child.is_dir() or child.name == "runs":
                    continue
                if not self._is_valid_project_dir(child):
                    continue
                slug = child.name
                candidates[slug] = child
                self._project_registry[slug] = child

        return candidates

    def count_recent_projects(self) -> int:
        """Return the total number of discoverable projects without loading summaries."""
        return len(self._discover_project_candidates())

    def list_recent_projects(self, limit: int | None = None) -> list[dict[str, Any]]:
        candidates = self._discover_project_candidates()

        # Sort candidates by mtime cheaply before calling project_summary (which is expensive).
        def _candidate_mtime(entry: tuple[str, Path]) -> float:
            try:
                return entry[1].stat().st_mtime
            except OSError:
                return 0.0

        sorted_candidates = sorted(candidates.items(), key=_candidate_mtime, reverse=True)
        if limit is not None:
            sorted_candidates = sorted_candidates[:limit]

        projects: list[dict[str, Any]] = []
        for slug, project_path in sorted_candidates:
            with self._orchestrator.run_lock:
                self._project_registry[slug] = project_path
            summary = self.project_summary(slug)
            summary["project_path"] = str(project_path)
            try:
                summary["last_modified"] = project_path.stat().st_mtime
            except OSError:
                summary["last_modified"] = None
            projects.append(summary)

        projects.sort(key=lambda p: p.get("last_modified") or 0.0, reverse=True)
        return projects

    def list_runs(self, project_id: str) -> list[dict[str, Any]]:
        return self._orchestrator.list_runs(project_id)

    def list_artifact_groups(self, project_id: str) -> list[dict[str, Any]]:
        return self._artifact_mgr.list_artifact_groups(project_id)

    def list_artifact_versions(
        self, project_id: str, artifact_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        return self._artifact_mgr.list_artifact_versions(
            project_id, artifact_type, entity_id
        )

    def read_artifact(
        self, project_id: str, artifact_type: str, entity_id: str, version: int
    ) -> dict[str, Any]:
        return self._artifact_mgr.read_artifact(
            project_id, artifact_type, entity_id, version
        )

    def edit_artifact(
        self,
        project_id: str,
        artifact_type: str,
        entity_id: str,
        data: dict[str, Any],
        rationale: str,
    ) -> dict[str, Any]:
        """Create a new version of an artifact with human-edited data."""
        return self._artifact_mgr.edit_artifact(
            project_id, artifact_type, entity_id, data, rationale
        )

    # --- Chat persistence (delegates to ChatStore) ---

    def list_chat_messages(self, project_id: str) -> list[dict[str, Any]]:
        """Read all chat messages from the project's chat.jsonl file."""
        return self._chat_store.list_messages(self.require_project_path(project_id))

    def append_chat_message(self, project_id: str, message: dict[str, Any]) -> dict[str, Any]:
        """Append a chat message (idempotent, thread-safe upsert for activity messages)."""
        return self._chat_store.append(self.require_project_path(project_id), message)

    def respond_to_review(
        self,
        project_id: str,
        scene_id: str,
        stage_id: str,
        approved: bool,
        feedback: str | None = None,
    ) -> ArtifactRef:
        """Handle human approval/rejection of a stage review."""
        from cine_forge.roles.canon import CanonGate
        
        project_path = self.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)
        role_context = self.get_role_context(project_id)
        
        # Load the latest review to get context
        review_entity_id = f"{scene_id}_{stage_id}"
        refs = store.list_versions(artifact_type="stage_review", entity_id=review_entity_id)
        if not refs:
            raise ServiceError(
                code="review_not_found",
                message=f"No stage review found for {review_entity_id}.",
                status_code=404,
            )
        
        latest_review_ref = refs[-1]
        artifact = store.load_artifact(latest_review_ref)
        review_data = artifact.data
        
        # Re-run CanonGate with user response
        gate = CanonGate(role_context=role_context, store=store)
        
        # We need to reconstruct the artifact_refs from the review
        reviewed_artifact_refs = [
            ArtifactRef.model_validate(ref) 
            for ref in review_data.get("reviewed_artifacts", [])
        ]
        
        return gate.review_stage(
            stage_id=stage_id,
            scene_id=scene_id,
            artifact_refs=reviewed_artifact_refs,
            control_mode=review_data.get("control_mode", "checkpoint"),
            user_approved=approved,
            input_payload={"human_feedback": feedback} if feedback else None
        )

    def resume_run(self, run_id: str) -> str:
        """Resume a paused pipeline run (e.g. after human approval)."""
        return self._orchestrator.resume_run(run_id)

    def search_entities(self, project_id: str, query: str) -> dict[str, Any]:
        """Search across scenes, characters, locations, and props for a project."""
        project_path = self.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)
        q = query.lower().strip()
        if not q:
            return {"query": query, "scenes": [], "characters": [], "locations": [], "props": []}

        scenes: list[dict[str, Any]] = []
        characters: list[dict[str, Any]] = []
        locations: list[dict[str, Any]] = []
        props: list[dict[str, Any]] = []

        scene_num = _parse_scene_number(q)
        all_scenes = _is_scene_all(q)

        # Search scene_index artifact for scene headings/locations.
        # Production pipeline saves scene_index with entity_id="project"; tests may use None.
        scene_index_refs = store.list_versions(artifact_type="scene_index", entity_id="project")
        if not scene_index_refs:
            scene_index_refs = store.list_versions(artifact_type="scene_index", entity_id=None)
        if scene_index_refs:
            latest = scene_index_refs[-1]
            try:
                artifact = store.load_artifact(latest)
                raw = artifact.data
                data = raw if isinstance(raw, dict) else raw.model_dump()
                for entry in data.get("entries", []):
                    heading = entry.get("heading", "")
                    loc = entry.get("location", "")
                    tod = entry.get("time_of_day", "")
                    snum = entry.get("scene_number", 0)
                    matches = (
                        all_scenes
                        or (scene_num is not None and snum == scene_num)
                        or _fuzzy_match(q, heading)
                        or _fuzzy_match(q, loc)
                        or _fuzzy_match(q, tod)
                    )
                    if matches:
                        first_word = heading.split(" ")[0].rstrip(".") if heading else ""
                        int_ext = first_word if first_word in ("INT", "EXT", "INT/EXT") else ""
                        scenes.append({
                            "scene_id": entry.get("scene_id", ""),
                            "scene_number": snum,
                            "heading": heading,
                            "location": loc,
                            "time_of_day": tod,
                            "int_ext": int_ext,
                        })
            except Exception:
                log.warning("Failed to load scene_index for search", exc_info=True)

        # Search bible manifests for characters, locations, props
        artifacts_root = project_path / "artifacts"
        bibles_root = artifacts_root / "bibles"
        if bibles_root.exists():
            for entity_dir in sorted(p for p in bibles_root.iterdir() if p.is_dir()):
                entity_id = entity_dir.name
                refs = store.list_versions(artifact_type="bible_manifest", entity_id=entity_id)
                if not refs:
                    continue
                try:
                    artifact = store.load_artifact(refs[-1])
                    raw = artifact.data
                    data = raw if isinstance(raw, dict) else raw.model_dump()
                    # The manifest's own entity_id is unprefixed (e.g., "mariner")
                    # while the directory name is prefixed (e.g., "character_mariner").
                    # Use the manifest's entity_id for navigation.
                    manifest_entity_id = data.get("entity_id", entity_id)
                    display_name = data.get("display_name", manifest_entity_id)
                    entity_type = data.get("entity_type", "")
                    artifact_type = f"{entity_type}_bible" if entity_type else ""

                    searchable = (
                        display_name.lower(), manifest_entity_id.lower(), entity_id.lower(),
                    )
                    if any(_fuzzy_match(q, s) for s in searchable):
                        result_entry = {
                            "entity_id": manifest_entity_id,
                            "display_name": display_name,
                            "entity_type": entity_type,
                            "artifact_type": artifact_type,
                        }
                        if entity_type == "character":
                            characters.append(result_entry)
                        elif entity_type == "location":
                            locations.append(result_entry)
                        elif entity_type == "prop":
                            props.append(result_entry)
                except Exception:
                    log.warning(
                        "Failed to load bible manifest %s for search",
                        entity_id, exc_info=True,
                    )

        return {
            "query": query,
            "scenes": scenes,
            "characters": characters,
            "locations": locations,
            "props": props,
        }

    def list_recipes(self) -> list[dict[str, Any]]:
        """List available recipe files from configs/recipes/."""
        recipes_dir = self.workspace_root / "configs" / "recipes"
        if not recipes_dir.exists():
            return []

        recipes: list[dict[str, Any]] = []
        for recipe_file in sorted(recipes_dir.glob("recipe-*.yaml")):
            # Skip test fixtures
            if recipe_file.name == "recipe-test-echo.yaml":
                continue

            try:
                recipe_data = yaml.safe_load(recipe_file.read_text(encoding="utf-8"))
            except (yaml.YAMLError, OSError):
                continue

            if not isinstance(recipe_data, dict):
                continue

            # Convert filename to recipe_id: recipe-mvp-ingest.yaml -> mvp_ingest
            recipe_filename = recipe_file.stem  # e.g., "recipe-mvp-ingest"
            if recipe_filename.startswith("recipe-"):
                recipe_id = recipe_filename[7:].replace("-", "_")
            else:
                recipe_id = recipe_filename

            # Extract metadata from YAML
            name = recipe_data.get("name", recipe_id.replace("_", " ").title())
            description = recipe_data.get("description", "")
            stages = recipe_data.get("stages", [])
            stage_count = len(stages) if isinstance(stages, list) else 0

            recipes.append({
                "recipe_id": recipe_id,
                "name": name,
                "description": description,
                "stage_count": stage_count,
            })

        return recipes

    def start_run(self, project_id: str, request: dict[str, Any]) -> str:
        return self._orchestrator.start_run(project_id, request)

    def retry_failed_stage(self, run_id: str) -> str:
        return self._orchestrator.retry_failed_stage(run_id)

    def save_project_input(self, project_id: str, filename: str, content: bytes) -> dict[str, Any]:
        project_path = self.require_project_path(project_id)
        safe_filename = self._sanitize_filename(filename)
        inputs_dir = project_path / "inputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        target = inputs_dir / f"{uuid.uuid4().hex[:8]}_{safe_filename}"
        target.write_bytes(content)
        return {
            "original_name": filename,
            "stored_path": str(target),
            "size_bytes": len(content),
        }

    def read_run_state(self, run_id: str) -> dict[str, Any]:
        return self._orchestrator.read_run_state(run_id)

    def read_run_events(self, run_id: str) -> dict[str, Any]:
        return self._orchestrator.read_run_events(run_id)

    @staticmethod
    def _is_valid_project_dir(path: Path) -> bool:
        try:
            return (
                path.exists()
                and path.is_dir()
                and (path / "artifacts").exists()
                and (path / "graph").exists()
            )
        except OSError:
            return False

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        clean = Path(filename).name.strip()
        if not clean:
            return "uploaded_script.fountain"
        clean = re.sub(r"[^A-Za-z0-9._-]+", "_", clean)
        return clean[:120]


def _artifact_rel_path(artifact_type: str, entity_id: str | None, version: int) -> str:
    entity_key = entity_id or "__project__"
    return f"artifacts/{artifact_type}/{entity_key}/v{version}.json"
