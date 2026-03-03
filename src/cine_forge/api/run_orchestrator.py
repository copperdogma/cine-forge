"""Run lifecycle orchestration — thread management, state polling, retry.

Extracted from OperatorConsoleService (Story 118, Phase 5).
Owns all mutable run state (_run_threads, _run_errors, _run_lock).
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cine_forge.api.exceptions import ServiceError
from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas import ArtifactRef, RuntimeParams

if TYPE_CHECKING:
    from cine_forge.api.chat_store import ChatStore

log = logging.getLogger(__name__)


def _build_runtime_params_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Build a RuntimeParams-validated dict from a (possibly incomplete) persisted dict."""
    default_model = raw.get("default_model", raw.get("model", "unknown"))
    filled = {
        "model": default_model,
        "utility_model": default_model,
        "sota_model": default_model,
        **{k: v for k, v in raw.items() if k in RuntimeParams.model_fields},
    }
    return RuntimeParams(**filled).model_dump(by_alias=True, exclude_none=True)


class RunOrchestrator:
    """Manages pipeline run lifecycle: start, resume, retry, state polling."""

    def __init__(
        self,
        workspace_root: Path,
        chat_store: ChatStore,
        project_registry: dict[str, Path],
        project_path_resolver: Callable[[str], Path],
        project_json_reader: Callable[[Path], dict[str, Any] | None],
    ) -> None:
        self.workspace_root = workspace_root
        self._chat_store = chat_store
        self._project_registry = project_registry
        self._project_path_resolver = project_path_resolver
        self._project_json_reader = project_json_reader
        self._run_threads: dict[str, threading.Thread] = {}
        self._run_errors: dict[str, str] = {}
        self._run_lock = threading.Lock()

    @property
    def run_lock(self) -> threading.Lock:
        """Exposed for cross-cluster access (e.g., list_recent_projects)."""
        return self._run_lock

    # ------------------------------------------------------------------
    # Run listing
    # ------------------------------------------------------------------

    def list_runs(self, project_id: str) -> list[dict[str, Any]]:
        project_path = self._project_path_resolver(project_id)
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
                    "recipe_id": state.get("recipe_id", "mvp_ingest"),
                    "started_at": state.get("started_at"),
                    "finished_at": state.get("finished_at"),
                }
            )
        return runs

    # ------------------------------------------------------------------
    # Start / Resume / Retry
    # ------------------------------------------------------------------

    def start_run(
        self,
        project_id: str,
        request: dict[str, Any],
    ) -> str:

        project_path = self._project_path_resolver(project_id)
        run_id = request.get("run_id") or f"run-{uuid.uuid4().hex[:8]}"

        recipe_id = request.get("recipe_id") or "mvp_ingest"
        recipe_filename = f"recipe-{str(recipe_id).replace('_', '-')}.yaml"
        recipe_path = self.workspace_root / "configs" / "recipes" / recipe_filename
        if not recipe_path.exists():
            raise ServiceError(
                code="recipe_not_found",
                message=f"Recipe file not found: {recipe_path}",
                hint=f"Ensure configs/recipes/{recipe_filename} exists in workspace.",
                status_code=500,
            )

        verify_or_qa = request.get("verify_model") or request.get("qa_model")
        params = RuntimeParams(
            input_file=request["input_file"],
            default_model=request["default_model"],
            model=request["default_model"],
            utility_model=request.get("work_model") or request["default_model"],
            sota_model=request.get("escalate_model") or request["default_model"],
            human_control_mode=request.get("human_control_mode") or "autonomous",
            accept_config=bool(request.get("accept_config", False)),
            skip_qa=bool(request.get("skip_qa", False)),
            work_model=request.get("work_model"),
            verify_model=verify_or_qa,
            qa_model=verify_or_qa,
            escalate_model=request.get("escalate_model"),
        )
        runtime_params = params.model_dump(by_alias=True, exclude_none=True)

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
                "project_id": project_id,
                "project_path": project_path,
                "recipe_path": recipe_path,
                "run_id": run_id,
                "force": bool(request.get("force", False)),
                "runtime_params": runtime_params,
                "start_from": request.get("start_from"),
                "end_at": request.get("end_at"),
            },
            daemon=True,
        )
        with self._run_lock:
            self._run_threads[run_id] = worker
        worker.start()
        return run_id

    def resume_run(self, run_id: str) -> str:

        run_dir = self.workspace_root / "output" / "runs" / run_id
        state_path = run_dir / "run_state.json"
        if not state_path.exists():
            raise ServiceError(
                code="run_state_not_found",
                message=f"Run state not found: {run_id}",
                status_code=404,
            )

        state = json.loads(state_path.read_text(encoding="utf-8"))
        stages = state.get("stages", {})

        paused_stage_id = next(
            (sid for sid, s in stages.items() if s.get("status") == "paused"),
            None,
        )
        if not paused_stage_id:
            raise ServiceError(
                code="not_paused",
                message="Run is not paused.",
                status_code=400,
            )

        run_meta_path = run_dir / "run_meta.json"
        if not run_meta_path.exists():
            run_meta_path = run_dir / "operator_console_run_meta.json"
        run_meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
        project_id = str(run_meta.get("project_id", ""))
        project_path = Path(run_meta["project_path"])

        pj = self._project_json_reader(project_path) or {}
        mode = pj.get("human_control_mode", "autonomous")

        new_run_id = f"{run_id}-resume-{uuid.uuid4().hex[:4]}"
        resume_run_dir = self.workspace_root / "output" / "runs" / new_run_id
        resume_run_dir.mkdir(parents=True, exist_ok=True)
        self._write_run_meta(resume_run_dir, project_id, project_path)

        base_params = dict(state.get("runtime_params", {}))
        base_params["human_control_mode"] = mode
        base_params["user_approved"] = True
        base_params["resume_artifact_refs_by_stage"] = {
            sid: s.get("artifact_refs", [])
            for sid, s in stages.items() if isinstance(s, dict)
        }
        base_params.pop("__resume_artifact_refs_by_stage", None)
        runtime_params = _build_runtime_params_dict(base_params)

        recipe_id = state.get("recipe_id")
        recipe_filename = f"recipe-{str(recipe_id).replace('_', '-')}.yaml"
        recipe_path = self.workspace_root / "configs" / "recipes" / recipe_filename

        worker = threading.Thread(
            target=self._run_pipeline,
            kwargs={
                "project_id": project_id,
                "project_path": project_path,
                "recipe_path": recipe_path,
                "run_id": new_run_id,
                "force": False,
                "runtime_params": runtime_params,
                "start_from": paused_stage_id,
            },
            daemon=True,
        )
        with self._run_lock:
            self._run_threads[new_run_id] = worker
        worker.start()
        return new_run_id

    def retry_failed_stage(self, run_id: str) -> str:

        run_dir = self.workspace_root / "output" / "runs" / run_id
        state_path = run_dir / "run_state.json"
        if not state_path.exists():
            raise ServiceError(
                code="run_state_not_found",
                message=f"Run state not found for run_id='{run_id}'.",
                hint="Verify the run id before retrying a failed stage.",
                status_code=404,
            )

        state = json.loads(state_path.read_text(encoding="utf-8"))
        stages = state.get("stages", {})
        failed_stage_id = next(
            (stage_id for stage_id, stage in stages.items() if stage.get("status") == "failed"),
            None,
        )
        if not failed_stage_id:
            raise ServiceError(
                code="no_failed_stage",
                message=f"Run '{run_id}' has no failed stage to retry.",
                hint="Only failed runs can be resumed from a failed stage.",
                status_code=400,
            )

        recipe_id = state.get("recipe_id")
        if not recipe_id or recipe_id == "initializing":
            raise ServiceError(
                code="run_recipe_unknown",
                message=f"Run '{run_id}' does not have a resolvable recipe.",
                hint="Use a run with a completed run_state recipe_id.",
                status_code=400,
            )

        recipe_filename = f"recipe-{str(recipe_id).replace('_', '-')}.yaml"
        recipe_path = self.workspace_root / "configs" / "recipes" / recipe_filename
        if not recipe_path.exists():
            raise ServiceError(
                code="recipe_not_found",
                message=f"Recipe file not found for retry: {recipe_path}",
                hint="Ensure the original run recipe still exists.",
                status_code=500,
            )

        run_meta_path = run_dir / "run_meta.json"
        if not run_meta_path.exists():
            run_meta_path = run_dir / "operator_console_run_meta.json"
        if not run_meta_path.exists():
            raise ServiceError(
                code="run_meta_not_found",
                message=f"Run metadata not found for run_id='{run_id}'.",
                hint="Cannot determine project context for retry.",
                status_code=500,
            )
        run_meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
        project_id = str(run_meta.get("project_id") or "")
        project_path_raw = run_meta.get("project_path")
        if not project_id or not project_path_raw:
            raise ServiceError(
                code="run_meta_invalid",
                message=f"Run metadata is incomplete for run_id='{run_id}'.",
                hint="Expected project_id and project_path.",
                status_code=500,
            )

        project_path = Path(project_path_raw)
        self._project_registry[project_id] = project_path
        store = ArtifactStore(project_dir=project_path)

        effective_start_from = failed_stage_id
        ingest_stage = stages.get("ingest")
        if (
            isinstance(ingest_stage, dict)
            and ingest_stage.get("status") == "done"
            and failed_stage_id != "ingest"
            and not self._has_non_empty_raw_input(ingest_stage, store)
        ):
            effective_start_from = "ingest"

        new_run_id = f"{run_id}-retry-{uuid.uuid4().hex[:4]}"
        retry_run_dir = self.workspace_root / "output" / "runs" / new_run_id
        retry_run_dir.mkdir(parents=True, exist_ok=True)
        self._write_run_meta(
            run_dir=retry_run_dir,
            project_id=project_id,
            project_path=project_path,
        )

        retry_base = dict(state.get("runtime_params", {}))
        retry_base["resume_artifact_refs_by_stage"] = {
            stage_id: stage.get("artifact_refs", [])
            for stage_id, stage in stages.items()
            if isinstance(stage, dict)
        }
        retry_base.pop("__resume_artifact_refs_by_stage", None)
        retry_runtime = _build_runtime_params_dict(retry_base)

        worker = threading.Thread(
            target=self._run_pipeline,
            kwargs={
                "project_id": project_id,
                "project_path": project_path,
                "recipe_path": recipe_path,
                "run_id": new_run_id,
                "force": False,
                "runtime_params": retry_runtime,
                "start_from": effective_start_from,
            },
            daemon=True,
        )
        with self._run_lock:
            self._run_threads[new_run_id] = worker
        worker.start()
        return new_run_id

    # ------------------------------------------------------------------
    # State polling
    # ------------------------------------------------------------------

    def read_run_state(self, run_id: str) -> dict[str, Any]:

        state_path = self.workspace_root / "output" / "runs" / run_id / "run_state.json"
        if not state_path.exists():
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

        now = time.time()
        for stage_state in state.get("stages", {}).values():
            if stage_state.get("status") == "running" and "started_at" in stage_state:
                stage_state["duration_seconds"] = round(now - stage_state["started_at"], 4)

        with self._run_lock:
            background_error = self._run_errors.get(run_id)
            is_active = run_id in self._run_threads

        if not background_error:
            error_path = self.workspace_root / "output" / "runs" / run_id / "background_error.log"
            if error_path.exists():
                background_error = error_path.read_text(encoding="utf-8")

        # Detect orphaned runs (marked running/pending but no thread active)
        if not is_active and not state.get("finished_at"):
            any_stuck = False
            for stage in state.get("stages", {}).values():
                if stage.get("status") in ("running", "pending"):
                    stage["status"] = "failed"
                    any_stuck = True

            if any_stuck:
                state_path.write_text(
                    json.dumps(state, indent=2), encoding="utf-8"
                )
                if not background_error:
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

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_pipeline(
        self,
        project_id: str,
        project_path: Path,
        recipe_path: Path,
        run_id: str,
        force: bool,
        runtime_params: dict[str, Any],
        start_from: str | None = None,
        end_at: str | None = None,
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
                end_at=end_at,
            )
            with self._run_lock:
                self._run_errors.pop(run_id, None)
        except Exception as exc:  # noqa: BLE001
            with self._run_lock:
                self._run_errors[run_id] = str(exc)
            error_path = self.workspace_root / "output" / "runs" / run_id / "background_error.log"
            try:
                error_path.write_text(str(exc), encoding="utf-8")
            except Exception:  # noqa: BLE001
                pass

            self._handle_run_failure_chat_notification(project_id, project_path, run_id, exc)
        finally:
            with self._run_lock:
                self._run_threads.pop(run_id, None)

    def _handle_run_failure_chat_notification(
        self, project_id: str, project_path: Path, run_id: str, exc: Exception
    ) -> None:
        """Detect specific errors (like low credits) and notify user in chat."""
        msg = str(exc).lower()

        try:
            state_path = self.workspace_root / "output" / "runs" / run_id / "run_state.json"
            if state_path.exists():
                state_data = json.loads(state_path.read_text(encoding="utf-8"))
                for stage in state_data.get("stages", {}).values():
                    for attempt in stage.get("attempts", []):
                        if attempt.get("error"):
                            msg += " " + str(attempt["error"]).lower()
        except Exception:  # noqa: BLE001
            pass

        friendly_message = ""

        if any(
            token in msg
            for token in (
                "credit balance",
                "insufficient_quota",
                "insufficient quota",
                "exceeded your current quota",
                "billing",
                "credits",
                "top up",
                "balance is too low",
            )
        ):
            friendly_message = (
                "⚠️ **AI Credit Balance Empty**\n\n"
                "The pipeline run failed because your AI provider credit balance is too low. "
                "Please top up your credits at "
                "[Anthropic](https://console.anthropic.com/settings/billing) "
                "or [OpenAI](https://platform.openai.com/account/billing) to continue."
            )
        elif any(
            token in msg
            for token in ("rate limit", "429", "overloaded", "capacity", "too many requests")
        ):
            friendly_message = (
                "⚠️ **Rate Limit Exceeded**\n\n"
                "The AI provider is currently rate-limiting requests or is overloaded. "
                "Please wait a moment and try again."
            )

        if friendly_message:
            chat_msg = {
                "id": f"error_{run_id}_{uuid.uuid4().hex[:4]}",
                "type": "ai_response",
                "content": friendly_message,
                "timestamp": time.time(),
            }
            try:
                self._chat_store.append(project_path, chat_msg)
            except Exception:
                log.exception("Failed to append error message to chat")

    @staticmethod
    def _run_belongs_to_project(
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
    def _has_non_empty_raw_input(stage_state: dict[str, Any], store: ArtifactStore) -> bool:
        refs = stage_state.get("artifact_refs", [])
        if not isinstance(refs, list):
            return False
        for ref_payload in refs:
            if not isinstance(ref_payload, dict):
                continue
            if ref_payload.get("artifact_type") != "raw_input":
                continue
            try:
                ref = ArtifactRef.model_validate(ref_payload)
                artifact = store.load_artifact(ref)
            except Exception:  # noqa: BLE001
                continue
            raw = artifact.data
            data = raw if isinstance(raw, dict) else raw.model_dump()
            content = data.get("content")
            if isinstance(content, str) and content.strip():
                return True
        return False
