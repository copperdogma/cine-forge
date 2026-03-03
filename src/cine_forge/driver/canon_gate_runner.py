"""StageCanonGate — encapsulates the canon review phase of stage execution."""

from __future__ import annotations

import threading
import time
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.event_emitter import EventEmitter
from cine_forge.driver.retry_policy import REVIEWABLE_ARTIFACT_TYPES
from cine_forge.roles import CanonGate, RoleContext
from cine_forge.schemas import (
    EventType,
    ProgressEvent,
    ReviewReadiness,
)


class StageCanonGate:
    """Runs the canon review gate after artifact persistence.

    Returns whether the stage should pause for human approval.
    """

    def __init__(
        self,
        store: ArtifactStore,
        role_context: RoleContext,
        stage_id: str,
        stage_state: dict[str, Any],
        state_lock: threading.Lock,
        emitter: EventEmitter,
        write_run_state: Any,
        run_id: str,
        stage_started: float,
    ) -> None:
        self.store = store
        self.role_context = role_context
        self.stage_id = stage_id
        self.stage_state = stage_state
        self.state_lock = state_lock
        self.emitter = emitter
        self.write_run_state = write_run_state
        self.run_id = run_id
        self.stage_started = stage_started

    def evaluate(
        self,
        outputs: list[dict[str, Any]],
        persisted_outputs: list[dict[str, Any]],
        control_mode: str,
        resolved_runtime_params: dict[str, Any],
    ) -> bool:
        """Run the canon review gate.

        Returns True if the stage should pause for human approval, False otherwise.
        """
        review_required = any(
            a["artifact_type"] in REVIEWABLE_ARTIFACT_TYPES for a in outputs
        )

        # Skip review if in autonomous mode or advisory mode or if no reviewable artifacts
        if not review_required or control_mode in ("autonomous", "advisory"):
            return False

        # Find scenes to review
        scenes_to_review: set[str] = set()
        for art in outputs:
            if art["artifact_type"] == "scene":
                scenes_to_review.add(art.get("entity_id") or "project")

        if not scenes_to_review:
            scenes_to_review.add("project")

        gate = CanonGate(role_context=self.role_context, store=self.store)
        review_refs = []
        for scene_id in sorted(scenes_to_review):
            # Filter artifacts relevant to this scene (or all for 'project')
            relevant_refs = [
                item["ref"] for item in persisted_outputs
                if scene_id == "project" or item["ref"].entity_id == scene_id
            ]

            review_ref = gate.review_stage(
                stage_id=self.stage_id,
                scene_id=scene_id,
                artifact_refs=relevant_refs,
                control_mode=control_mode,
                user_approved=resolved_runtime_params.get("user_approved"),
            )
            review_refs.append(review_ref)
            with self.state_lock:
                self.stage_state["artifact_refs"].append(review_ref.model_dump())

        # Check if we should pause
        latest_reviews = [self.store.load_artifact(ref).data for ref in review_refs]
        if any(r.get("readiness") == ReviewReadiness.AWAITING_USER for r in latest_reviews):
            with self.state_lock:
                self.stage_state["status"] = "paused"
                self.stage_state["duration_seconds"] = round(
                    time.time() - self.stage_started, 4
                )
                self.emitter.emit(ProgressEvent(
                    event=EventType.stage_paused,
                    stage_id=self.stage_id,
                    reason="awaiting_human_approval",
                    artifacts=self.stage_state["artifact_refs"],
                ))
                self.write_run_state()
            print(
                f"[{self.run_id}] Stage '{self.stage_id}' paused for human approval."
            )
            return True

        return False
