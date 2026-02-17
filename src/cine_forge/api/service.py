"""Service layer for CineForge API backend."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.engine import DriverEngine

log = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-level error with API-ready details."""

    def __init__(self, code: str, message: str, hint: str | None = None, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.status_code = status_code


class OperatorConsoleService:
    """Coordinates project registration, run execution, and artifact browsing."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self._project_registry: dict[str, Path] = {}
        self._run_errors: dict[str, str] = {}
        self._run_threads: dict[str, threading.Thread] = {}
        self._run_lock = threading.Lock()

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

    def generate_slug(
        self, content_snippet: str, original_filename: str,
    ) -> dict[str, Any]:
        """Use a fast LLM to extract a title and slug from screenplay content."""
        prompt = (
            "You are a screenplay title extractor. Given the first part of a "
            "screenplay or script document, extract:\n"
            "1. The most likely title of the work\n"
            "2. One alternative title/name (if available)\n\n"
            "Respond with JSON only:\n"
            '{"title": "The Main Title", "alt_title": "Alternative Name or null"}\n\n'
            f"Original filename: {original_filename}\n\n"
            f"--- Document content (first ~2000 chars) ---\n{content_snippet[:2000]}"
        )
        try:
            from cine_forge.ai.llm import call_llm
            result, _meta = call_llm(
                prompt=prompt,
                model="claude-haiku-4-5-20251001",
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
        project_path: Path, slug: str, display_name: str,
    ) -> None:
        meta = {"slug": slug, "display_name": display_name}
        (project_path / "project.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8",
        )

    @staticmethod
    def _read_project_json(project_path: Path) -> dict[str, str] | None:
        pj = project_path / "project.json"
        if not pj.exists():
            return None
        try:
            return json.loads(pj.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def update_project_settings(
        self, project_id: str, display_name: str | None = None,
    ) -> dict[str, Any]:
        """Update mutable project settings (display_name, etc.)."""
        path = self.require_project_path(project_id)
        pj = self._read_project_json(path) or {"slug": project_id}
        if display_name is not None:
            pj["display_name"] = display_name
        self._write_project_json(path, pj.get("slug", project_id), pj["display_name"])
        return self.project_summary(project_id)

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

    def require_project_path(self, project_id: str) -> Path:
        path = self._project_registry.get(project_id)
        if path is None:
            raise ServiceError(
                code="project_not_opened",
                message="Unknown project_id for this backend session.",
                hint="Call /api/projects/open or /api/projects/new before project-scoped APIs.",
                status_code=404,
            )
        return path

    def project_summary(self, project_id: str) -> dict[str, Any]:
        path = self.require_project_path(project_id)
        artifact_groups = len(self.list_artifact_groups(project_id))
        run_count = len(self.list_runs(project_id))
        inputs = self.list_project_inputs(project_id)
        input_files = [inp["original_name"] for inp in inputs]
        # Prefer display_name from project.json, fall back to heuristic
        pj = self._read_project_json(path)
        display_name = (pj or {}).get("display_name") or self._clean_display_name(path, input_files)
        return {
            "project_id": project_id,
            "display_name": display_name,
            "artifact_groups": artifact_groups,
            "run_count": run_count,
            "has_inputs": len(inputs) > 0,
            "input_files": input_files,
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

    def list_recent_projects(self) -> list[dict[str, Any]]:
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

        projects: list[dict[str, Any]] = []
        for slug, project_path in candidates.items():
            with self._run_lock:
                self._project_registry[slug] = project_path
            summary = self.project_summary(slug)
            summary["project_path"] = str(project_path)
            try:
                summary["last_modified"] = project_path.stat().st_mtime
            except OSError:
                summary["last_modified"] = None
            projects.append(summary)

        def _mtime(item: dict[str, Any]) -> float:
            try:
                return Path(item["project_path"]).stat().st_mtime
            except FileNotFoundError:
                return 0.0

        projects.sort(key=_mtime, reverse=True)
        return projects

    def list_runs(self, project_id: str) -> list[dict[str, Any]]:
        project_path = self.require_project_path(project_id)
        runs_dir = self.workspace_root / "output" / "runs"
        if not runs_dir.exists():
            return []
        runs: list[dict[str, Any]] = []
        for run_dir in sorted(
            [path for path in runs_dir.iterdir() if path.is_dir()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        ):
            state_path = run_dir / "run_state.json"
            if not state_path.exists():
                continue
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if not self._run_belongs_to_project(
                run_dir=run_dir,
                project_path=project_path,
                run_state=state,
            ):
                continue
            statuses = {stage["status"] for stage in state.get("stages", {}).values()}
            if "failed" in statuses:
                status = "failed"
            elif "running" in statuses:
                status = "running"
            elif "paused" in statuses:
                status = "paused"
            elif statuses and statuses <= {"done", "skipped_reused"}:
                status = "done"
            else:
                status = "pending"
            runs.append(
                {
                    "run_id": state.get("run_id", run_dir.name),
                    "status": status,
                    "started_at": state.get("started_at"),
                    "finished_at": state.get("finished_at"),
                }
            )
        return runs

    def list_artifact_groups(self, project_id: str) -> list[dict[str, Any]]:
        project_path = self.require_project_path(project_id)
        artifacts_root = project_path / "artifacts"
        if not artifacts_root.exists():
            return []
        store = ArtifactStore(project_dir=project_path)
        groups: list[dict[str, Any]] = []
        for artifact_type_dir in sorted(path for path in artifacts_root.iterdir() if path.is_dir()):
            artifact_type = artifact_type_dir.name
            if artifact_type == "bibles":
                # Special handling for folder-based bibles
                bibles_iter = (path for path in artifact_type_dir.iterdir() if path.is_dir())
                for entity_type_dir in sorted(bibles_iter):
                    # entity_type_dir name is like "character_aria"
                    entity_id = entity_type_dir.name
                    # For folder-based bibles, the manifest is the versioned artifact
                    refs = store.list_versions(artifact_type="bible_manifest", entity_id=entity_id)
                    if not refs:
                        continue
                    latest = refs[-1]
                    health = store.graph.get_health(latest)
                    groups.append(
                        {
                            "artifact_type": "bible_manifest",
                            "entity_id": entity_id,
                            "latest_version": latest.version,
                            "health": health.value if health else None,
                        }
                    )
                continue

            for entity_dir in sorted(path for path in artifact_type_dir.iterdir() if path.is_dir()):
                entity_id = None if entity_dir.name == "__project__" else entity_dir.name
                refs = store.list_versions(artifact_type=artifact_type, entity_id=entity_id)
                if not refs:
                    continue
                latest = refs[-1]
                health = store.graph.get_health(latest)
                groups.append(
                    {
                        "artifact_type": artifact_type,
                        "entity_id": entity_id,
                        "latest_version": latest.version,
                        "health": health.value if health else None,
                    }
                )
        return groups

    def list_artifact_versions(
        self, project_id: str, artifact_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        project_path = self.require_project_path(project_id)
        normalized_entity = None if entity_id == "__project__" else entity_id
        store = ArtifactStore(project_dir=project_path)
        refs = store.list_versions(artifact_type=artifact_type, entity_id=normalized_entity)
        versions: list[dict[str, Any]] = []
        for ref in refs:
            artifact = store.load_artifact(ref)
            health = store.graph.get_health(ref)
            versions.append(
                {
                    "artifact_type": artifact_type,
                    "entity_id": normalized_entity,
                    "version": ref.version,
                    "health": health.value if health else None,
                    "path": ref.path,
                    "created_at": artifact.metadata.created_at.isoformat(),
                    "intent": artifact.metadata.intent,
                    "producing_module": artifact.metadata.producing_module,
                }
            )
        return versions

    def read_artifact(
        self, project_id: str, artifact_type: str, entity_id: str, version: int
    ) -> dict[str, Any]:
        project_path = self.require_project_path(project_id)
        normalized_entity = None if entity_id == "__project__" else entity_id
        store = ArtifactStore(project_dir=project_path)

        # Load all versions to find the one with the matching version number
        # This ensures we get the correct relative path from the store
        refs = store.list_versions(artifact_type=artifact_type, entity_id=normalized_entity)
        ref = next((r for r in refs if r.version == version), None)

        if not ref:
            raise ServiceError(
                code="artifact_not_found",
                message=(
                    "Artifact version not found for "
                    f"{artifact_type}/{entity_id}/v{version}."
                ),
                hint="Check available versions via the artifact versions endpoint.",
                status_code=404,
            )

        artifact = store.load_artifact(ref)
        response = {
            "artifact_type": artifact_type,
            "entity_id": normalized_entity,
            "version": version,
            "payload": artifact.model_dump(mode="json"),
        }

        # If it's a bible manifest, load the contents of the files it references
        if artifact_type == "bible_manifest":
            bible_files = {}
            # Ref path is artifacts/bibles/{entity_id}/manifest_vN.json
            # project_path is already absolute.
            bible_dir = (project_path / ref.path).parent

            # Manifest data is in artifact.data
            manifest_data = artifact.data

            # Ensure we have a dict to work with
            if not isinstance(manifest_data, dict):
                try:
                    manifest_data = manifest_data.model_dump()
                except AttributeError:
                    manifest_data = {}

            files_list = manifest_data.get("files") or []
            for file_entry in files_list:
                filename = file_entry.get("filename")
                if filename:
                    file_path = bible_dir / filename
                    if file_path.exists():
                        # Try to load as JSON first for rich UI display
                        try:
                            bible_files[filename] = json.loads(
                                file_path.read_text(encoding="utf-8")
                            )
                        except json.JSONDecodeError:
                            bible_files[filename] = file_path.read_text(encoding="utf-8")
            response["bible_files"] = bible_files

        return response

    def edit_artifact(
        self,
        project_id: str,
        artifact_type: str,
        entity_id: str,
        data: dict[str, Any],
        rationale: str,
    ) -> dict[str, Any]:
        """Create a new version of an artifact with human-edited data."""
        from cine_forge.schemas import ArtifactMetadata

        project_path = self.require_project_path(project_id)
        normalized_entity = None if entity_id == "__project__" else entity_id
        store = ArtifactStore(project_dir=project_path)

        # Verify the artifact group exists
        refs = store.list_versions(artifact_type=artifact_type, entity_id=normalized_entity)
        if not refs:
            raise ServiceError(
                code="artifact_not_found",
                message=f"No existing artifact found for {artifact_type}/{entity_id}.",
                hint="You can only edit existing artifacts.",
                status_code=404,
            )

        # Get the latest version to use as lineage
        latest_ref = refs[-1]

        # Create metadata for the new version
        metadata = ArtifactMetadata(
            lineage=[latest_ref],
            intent="override",
            rationale=rationale,
            confidence=1.0,
            source="human",
            producing_module="operator_console.manual_edit",
        )

        # Save the new artifact version
        new_ref = store.save_artifact(
            artifact_type=artifact_type,
            entity_id=normalized_entity,
            data=data,
            metadata=metadata,
        )

        return {
            "artifact_type": artifact_type,
            "entity_id": normalized_entity,
            "version": new_ref.version,
            "path": new_ref.path,
        }

    # --- Chat persistence (JSONL) ---

    def _chat_path(self, project_id: str) -> Path:
        project_path = self.require_project_path(project_id)
        return project_path / "chat.jsonl"

    def list_chat_messages(self, project_id: str) -> list[dict[str, Any]]:
        """Read all chat messages from the project's chat.jsonl file."""
        path = self._chat_path(project_id)
        if not path.exists():
            return []
        messages: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("Skipping malformed chat line in %s", path)
        return messages

    def append_chat_message(self, project_id: str, message: dict[str, Any]) -> dict[str, Any]:
        """Append a chat message to the project's chat.jsonl (idempotent by message ID)."""
        path = self._chat_path(project_id)
        msg_id = message.get("id", "")

        # Idempotency check — scan for existing ID
        if path.exists() and msg_id:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    existing = json.loads(line)
                    if existing.get("id") == msg_id:
                        return existing  # Already persisted
                except json.JSONDecodeError:
                    continue

        # Append
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(message, separators=(",", ":")) + "\n")
        return message

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

        # Search scene_index artifact for scene headings/locations
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
                    if q in heading.lower() or q in loc.lower() or q in tod.lower():
                        first_word = heading.split(" ")[0].rstrip(".") if heading else ""
                        int_ext = first_word if first_word in ("INT", "EXT", "INT/EXT") else ""
                        scenes.append({
                            "scene_id": entry.get("scene_id", ""),
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
                    if any(q in s for s in searchable):
                        entry = {
                            "entity_id": manifest_entity_id,
                            "display_name": display_name,
                            "entity_type": entity_type,
                            "artifact_type": artifact_type,
                        }
                        if entity_type == "character":
                            characters.append(entry)
                        elif entity_type == "location":
                            locations.append(entry)
                        elif entity_type == "prop":
                            props.append(entry)
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
        project_path = self.require_project_path(project_id)
        run_id = request.get("run_id") or f"run-{uuid.uuid4().hex[:8]}"
        
        recipe_id = request.get("recipe_id") or "mvp_ingest"
        recipe_filename = f"recipe-{recipe_id.replace('_', '-')}.yaml"
        recipe_path = self.workspace_root / "configs" / "recipes" / recipe_filename
        
        if not recipe_path.exists():
            raise ServiceError(
                code="recipe_not_found",
                message=f"Recipe file not found: {recipe_path}",
                hint=f"Ensure configs/recipes/{recipe_filename} exists in workspace.",
                status_code=500,
            )

        runtime_params: dict[str, Any] = {
            "input_file": request["input_file"],
            "default_model": request["default_model"],
            "model": request["default_model"],
            # Backward-compat aliases for custom recipes using ${utility_model}/${sota_model}
            "utility_model": request.get("work_model") or request["default_model"],
            "sota_model": request.get("escalate_model") or request["default_model"],
            "accept_config": bool(request.get("accept_config", False)),
            "skip_qa": bool(request.get("skip_qa", False)),
        }
        # Only override tier-specific module params if explicitly provided.
        # Otherwise, modules use their built-in defaults (e.g., Haiku for QA).
        if request.get("work_model"):
            runtime_params["work_model"] = request["work_model"]
        if request.get("verify_model") or request.get("qa_model"):
            v = request.get("verify_model") or request["qa_model"]
            runtime_params["verify_model"] = v
            runtime_params["qa_model"] = v
        if request.get("escalate_model"):
            runtime_params["escalate_model"] = request["escalate_model"]

        run_dir = self.workspace_root / "output" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        self._write_run_meta(
            run_dir=run_dir,
            project_id=project_id,
            project_path=project_path,
        )

        config_file = request.get("config_file")
        if request.get("config_overrides"):
            config_file = str(run_dir / "config_overrides.yaml")
            config_path = Path(config_file)
            config_path.write_text(
                json.dumps(request["config_overrides"], indent=2, sort_keys=True),
                encoding="utf-8",
            )

        if config_file:
            runtime_params["config_file"] = str(config_file)

        worker = threading.Thread(
            target=self._run_pipeline,
            kwargs={
                "project_path": project_path,
                "recipe_path": recipe_path,
                "run_id": run_id,
                "force": bool(request.get("force", False)),
                "runtime_params": runtime_params,
                "start_from": request.get("start_from"),
            },
            daemon=True,
        )
        with self._run_lock:
            self._run_threads[run_id] = worker
        worker.start()
        return run_id

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

    def _run_pipeline(
        self,
        project_path: Path,
        recipe_path: Path,
        run_id: str,
        force: bool,
        runtime_params: dict[str, Any],
        start_from: str | None = None,
    ) -> None:
        try:
            engine = DriverEngine(
                workspace_root=self.workspace_root,
                project_dir=project_path,
            )
            engine.run(
                recipe_path=recipe_path,
                run_id=run_id,
                force=force,
                runtime_params=runtime_params,
                start_from=start_from,
            )
            with self._run_lock:
                self._run_errors.pop(run_id, None)
        except Exception as exc:  # noqa: BLE001
            with self._run_lock:
                self._run_errors[run_id] = str(exc)
            # Persist error to disk
            error_path = self.workspace_root / "output" / "runs" / run_id / "background_error.log"
            try:
                error_path.write_text(str(exc), encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass
        finally:
            with self._run_lock:
                self._run_threads.pop(run_id, None)

    def read_run_state(self, run_id: str) -> dict[str, Any]:
        state_path = self.workspace_root / "output" / "runs" / run_id / "run_state.json"
        if not state_path.exists():
            # Check if it failed during early initialization before it could write the file
            with self._run_lock:
                background_error = self._run_errors.get(run_id)
            if background_error:
                return {
                    "run_id": run_id,
                    "state": {
                        "run_id": run_id,
                        "recipe_id": "failed_init",
                        "dry_run": False,
                        "started_at": time.time(),
                        "stages": {},
                        "total_cost_usd": 0.0,
                        "instrumented": False,
                    },
                    "background_error": background_error,
                }

            raise ServiceError(
                code="run_state_not_found",
                message=f"Run state not found for run_id='{run_id}'.",
                hint="Start a run first or verify run_id.",
                status_code=404,
            )
        state = json.loads(state_path.read_text(encoding="utf-8"))

        # Compute live elapsed duration for running stages
        now = time.time()
        for stage_state in state.get("stages", {}).values():
            if stage_state.get("status") == "running" and "started_at" in stage_state:
                stage_state["duration_seconds"] = round(now - stage_state["started_at"], 4)

        with self._run_lock:
            background_error = self._run_errors.get(run_id)
            is_active = run_id in self._run_threads

        if not background_error:
            # Check disk for persisted error
            error_path = self.workspace_root / "output" / "runs" / run_id / "background_error.log"
            if error_path.exists():
                background_error = error_path.read_text(encoding="utf-8")

        # Detect orphaned runs (marked running/pending but no thread active)
        if not is_active and not state.get("finished_at"):
            # If the backend restarted, the thread map is empty.
            # We treat any non-finished run as failed/orphaned.
            any_stuck = False
            for stage in state.get("stages", {}).values():
                if stage.get("status") in ("running", "pending"):
                    stage["status"] = "failed"
                    any_stuck = True
            
            if any_stuck and not background_error:
                background_error = "Run orphaned (backend restart or crash)"

        return {"run_id": run_id, "state": state, "background_error": background_error}

    def read_run_events(self, run_id: str) -> dict[str, Any]:
        events_path = self.workspace_root / "output" / "runs" / run_id / "pipeline_events.jsonl"
        if not events_path.exists():
            raise ServiceError(
                code="run_events_not_found",
                message=f"Run events not found for run_id='{run_id}'.",
                hint="Start a run first or verify run_id.",
                status_code=404,
            )
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return {"run_id": run_id, "events": events}

    def _run_belongs_to_project(
        self,
        run_dir: Path,
        project_path: Path,
        run_state: dict[str, Any],
    ) -> bool:
        run_meta_path = run_dir / "run_meta.json"
        if not run_meta_path.exists():
            run_meta_path = run_dir / "operator_console_run_meta.json"
        if not run_meta_path.exists():
            return False
        run_meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
        return run_meta.get("project_path") == str(project_path)

    @staticmethod
    def _is_valid_project_dir(path: Path) -> bool:
        return (
            path.exists()
            and path.is_dir()
            and (path / "artifacts").exists()
            and (path / "graph").exists()
        )

    @staticmethod
    def _write_run_meta(run_dir: Path, project_id: str, project_path: Path) -> None:
        meta_path = run_dir / "run_meta.json"
        payload = {
            "project_id": project_id,
            "project_path": str(project_path),
        }
        meta_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )

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
