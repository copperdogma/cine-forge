"""Service layer for Operator Console Lite backend."""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.engine import DriverEngine


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
    def project_id_for_path(path: Path) -> str:
        normalized = str(path.resolve(strict=False))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def create_project(self, project_path: str) -> str:
        path = self.normalize_project_path(project_path)
        path.mkdir(parents=True, exist_ok=True)
        (path / "artifacts").mkdir(parents=True, exist_ok=True)
        (path / "graph").mkdir(parents=True, exist_ok=True)
        project_id = self.project_id_for_path(path)
        self._project_registry[project_id] = path
        return project_id

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
        project_id = self.project_id_for_path(path)
        self._project_registry[project_id] = path
        return project_id

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
        return {
            "project_id": project_id,
            "display_name": path.name,
            "artifact_groups": artifact_groups,
            "run_count": run_count,
        }

    def list_recent_projects(self) -> list[dict[str, Any]]:
        candidates: dict[str, Path] = {}
        for project_id, project_path in self._project_registry.items():
            if self._is_valid_project_dir(project_path):
                candidates[project_id] = project_path

        runs_dir = self.workspace_root / "output" / "runs"
        if runs_dir.exists():
            for run_dir in runs_dir.iterdir():
                if not run_dir.is_dir():
                    continue
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
                project_id = self.project_id_for_path(project_path)
                candidates[project_id] = project_path
                self._project_registry[project_id] = project_path

        output_root = self.workspace_root / "output"
        if output_root.exists():
            for child in output_root.iterdir():
                if not child.is_dir() or child.name == "runs":
                    continue
                if not self._is_valid_project_dir(child):
                    continue
                project_id = self.project_id_for_path(child)
                candidates[project_id] = child
                self._project_registry[project_id] = child

        projects: list[dict[str, Any]] = []
        for project_id, project_path in candidates.items():
            with self._run_lock:
                self._project_registry[project_id] = project_path
            summary = self.project_summary(project_id)
            summary["project_path"] = str(project_path)
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
            "accept_config": bool(request.get("accept_config", False)),
        }
        # Map tiered models to ensure all possible recipe placeholders are satisfied
        work = request.get("work_model") or request["default_model"]
        verify = request.get("verify_model") or request.get("qa_model") or work
        escalate = request.get("escalate_model") or work

        runtime_params.update({
            "work_model": work,
            "utility_model": work,  # Aliased for recipes using utility naming
            "verify_model": verify,
            "qa_model": verify,
            "escalate_model": escalate,
            "sota_model": escalate, # Aliased for recipes using sota naming
            "skip_qa": bool(request.get("skip_qa", False))
        })

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
        meta_path = run_dir / "operator_console_run_meta.json"
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
