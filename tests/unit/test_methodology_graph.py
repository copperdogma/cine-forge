from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "methodology-graph.js"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def _seed_methodology_repo(
    tmp_path: Path,
    story_status: str,
    blocker_summary: str,
    blocker_evidence: str,
    unblock_condition: str,
) -> Path:
    _write(
        tmp_path / "docs" / "ideal.md",
        """
        # Ideal

        ## Requirements and Quality Bar

        **R14. Nothing is ever lost**
        """,
    )
    _write(
        tmp_path / "docs" / "spec.md",
        """
        # Spec

        ## spec:11 — Execution Tooling

        ### spec:11.1 — Story Lifecycle and Handoff Chain
        """,
    )
    _write(
        tmp_path / "docs" / "methodology" / "state.yaml",
        """
        {
          "categories": {
            "spec:11": {
              "product_need": "Execution clarity",
              "tech_need": "Methodology substrate",
              "substrate": "exists",
              "phase": "hold",
              "story_coverage": "partial",
              "notes": []
            }
          },
          "compromises": {},
          "stories_index": {
            "sections": []
          },
          "roadmap": {
            "active_focus": [],
            "sequencing_bias": [],
            "campaigns": []
          },
          "architecture_audits": {
            "cadence": {
              "target_story_interval": 5
            },
            "domains": {}
          },
          "ui_scout": {
            "cadence": {
              "max_days_without_run": 7
            },
            "last_run_at": "2026-04-04",
            "last_run_story_id": "001",
            "scenarios": {
              "FP1": {
                "label": "Canonical fixture",
                "last_checked": "2026-04-04",
                "latest_report": "report-001",
                "status": "pass",
                "follow_up_story_refs": []
              }
            }
          }
        }
        """,
    )
    _write(
        tmp_path / "docs" / "ui-scout" / "report-001.md",
        """
        # UI Scout Report 001

        Fixture report for methodology graph tests.
        """,
    )
    _write(tmp_path / "docs" / "evals" / "registry.yaml", "")
    (tmp_path / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
    _write(
        tmp_path / "docs" / "stories" / "story-001-honest-blocked-story.md",
        f"""
        ---
        id: "001"
        title: "Honest blocked story"
        status: "{story_status}"
        priority: "High"
        ideal_refs:
          - "R14"
        spec_refs:
          - "spec:11"
          - "spec:11.1"
        adr_refs: []
        depends_on: []
        category_refs:
          - "spec:11"
        compromise_refs: []
        input_coverage_refs: []
        architecture_domains: []
        roadmap_tags: []
        legacy_system: ""
        ---

        # Story 001 — Honest blocked story

        **Priority**: High
        **Status**: {story_status}
        **Ideal Refs**: R14
        **Spec Refs**: spec:11; spec:11.1
        **ADR Refs**: None found after search
        **Depends On**: None

        ## Goal

        Keep blocked-story truth inspectable.

        ## Acceptance Criteria

        - [ ] Blocked stories must record their blocker truth honestly.

        ## Out of Scope

        - [ ] None

        ## Workflow Gates

        - [ ] Build complete: implementation finished, required checks run, and human summary shared
        - [ ] Validation complete or explicitly skipped by user
        - [ ] Story marked done via `/mark-story-done`

        ## Blocker Summary

        {blocker_summary}

        ## Blocker Evidence

        {blocker_evidence}

        ## Unblock Condition

        {unblock_condition}

        ## Work Log

        20260404-0000 — fixture: seeded methodology graph test fixture.
        Evidence=test-only temp repo. Next=run compiler
        """,
    )
    return tmp_path


def _run_methodology_graph(tmp_path: Path, command: str) -> subprocess.CompletedProcess[str]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is required for methodology graph tests")
    return subprocess.run(
        [node, str(SCRIPT_PATH), command],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_methodology_graph_exports_blocker_metadata_for_blocked_story(tmp_path: Path) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Blocked",
        blocker_summary="Waiting on upstream substrate decision.",
        blocker_evidence="Current compiler contract still disagrees with the skill surface.",
        unblock_condition="Land the compiler and skill alignment patch.",
    )

    result = _run_methodology_graph(tmp_path, "build")

    assert result.returncode == 0, result.stderr
    graph = json.loads(
        (tmp_path / "docs" / "methodology" / "graph.json").read_text(
            encoding="utf-8"
        )
    )
    story = graph["stories"][0]
    assert story["status"] == "Blocked"
    assert story["blockerSummary"] == "Waiting on upstream substrate decision."
    assert (
        story["blockerEvidence"]
        == "Current compiler contract still disagrees with the skill surface."
    )
    assert story["unblockCondition"] == "Land the compiler and skill alignment patch."
    assert story["lastWorkLogEntry"]["date"] == "2026-04-04"
    assert story["actionability"]["posture"] == "blocked"

    stories_index = (tmp_path / "docs" / "stories.md").read_text(encoding="utf-8")
    assert (
        "Concrete enough to preserve, but blocked by a named evidence-backed blocker"
        in stories_index
    )
    assert (
        "| 001 | Honest blocked story | High | Blocked | "
        "Waiting on upstream substrate decision. |" in stories_index
    )


def test_methodology_graph_rejects_blocked_story_with_placeholder_blocker_fields(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Blocked",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )

    result = _run_methodology_graph(tmp_path, "print")

    assert result.returncode == 1
    assert "story 001 is Blocked but missing Blocker Summary" in result.stderr
    assert "story 001 is Blocked but missing Blocker Evidence" in result.stderr
    assert "story 001 is Blocked but missing Unblock Condition" in result.stderr


def test_methodology_graph_exports_eval_actionability(tmp_path: Path) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Pending",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "evals" / "registry.yaml",
        """
        evals:
          - id: sample-detector
            name: Sample Detector
            type: quality
            spec_refs:
              - spec:11
            story_refs:
              - "001"
            category_refs:
              - spec:11
            compromise_refs: []
            scores:
              - model: "Gemini 2.5 Flash"
                measured: 2026-04-04
                note: "Current detector is still below the target."
            attempts:
              - id: "001"
                date: 2026-04-04
                status: partial
                approach: "Ran the bounded detector once."
                note: "Same harness still misses the edge case."
                retry_status: exhausted-until-new-trigger
                retry_when:
                  - condition: new-approach
                    note: "Only retry after a materially new substrate appears."
        """,
    )

    result = _run_methodology_graph(tmp_path, "build")

    assert result.returncode == 0, result.stderr
    graph = json.loads(
        (tmp_path / "docs" / "methodology" / "graph.json").read_text(
            encoding="utf-8"
        )
    )
    eval_record = graph["evals"][0]
    assert eval_record["actionability"]["retryTriggerStatus"] == "exhausted"
    assert eval_record["actionability"]["retryWhen"] == ["new-approach"]
    assert eval_record["actionability"]["lastRelevantAction"]["date"] == "2026-04-04"


def test_methodology_graph_preserves_eval_description_and_top_level_retry_when(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Pending",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "evals" / "registry.yaml",
        """
        evals:
          - id: sample-eval
            name: Sample Eval
            type: quality
            description: >
              Sample eval description that should survive graph compilation.
            spec_refs:
              - spec:11
            story_refs:
              - "001"
            category_refs:
              - spec:11
            compromise_refs: []
            retry_when:
              - golden-fix
        """,
    )

    result = _run_methodology_graph(tmp_path, "build")

    assert result.returncode == 0, result.stderr
    graph = json.loads(
        (tmp_path / "docs" / "methodology" / "graph.json").read_text(
            encoding="utf-8"
        )
    )
    eval_record = graph["evals"][0]
    assert (
        eval_record["description"]
        == "Sample eval description that should survive graph compilation."
    )
    assert eval_record["actionability"]["retryWhen"] == ["golden-fix"]
    assert eval_record["actionability"]["retryTriggerStatus"] == "waiting"


def test_methodology_graph_renders_structured_current_execution_map(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="In Progress",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "methodology" / "state.yaml",
        """
        {
          "categories": {
            "spec:11": {
              "product_need": "Execution clarity",
              "tech_need": "Methodology substrate",
              "substrate": "exists",
              "phase": "hold",
              "story_coverage": "partial",
              "notes": []
            }
          },
          "compromises": {},
          "stories_index": {
            "current_execution_map": {
              "summary": "Compiler-driven execution map summary.",
              "lanes": [
                {
                  "id": "in-progress",
                  "title": "In Progress",
                  "statuses": ["In Progress"],
                  "empty_message": "No stories currently in progress.",
                  "story_notes": {
                    "001": "Active methodology follow-on."
                  }
                },
                {
                  "id": "blocked",
                  "title": "Blocked",
                  "statuses": ["Blocked"],
                  "health_flag": true,
                  "empty_message": "No stories currently blocked.",
                  "story_notes": {}
                }
              ]
            },
            "sections": []
          },
          "roadmap": {
            "active_focus": ["spec:11"],
            "sequencing_bias": [
              {
                "target": "spec:11",
                "reason": "Keep the methodology lane honest.",
                "story_refs": ["001"]
              }
            ],
            "campaigns": [
              {
                "id": "workflow-repair",
                "status": "active",
                "story_refs": ["001"],
                "notes": "Still in flight."
              }
            ]
          },
          "architecture_audits": {
            "cadence": {
              "target_story_interval": 5
            },
            "domains": {}
          },
          "ui_scout": {
            "cadence": {
              "max_days_without_run": 7
            },
            "last_run_at": "2026-04-04",
            "last_run_story_id": "001",
            "scenarios": {
              "FP1": {
                "label": "Canonical fixture",
                "last_checked": "2026-04-04",
                "latest_report": "report-001",
                "status": "pass",
                "follow_up_story_refs": []
              }
            }
          }
        }
        """,
    )

    result = _run_methodology_graph(tmp_path, "build")

    assert result.returncode == 0, result.stderr
    stories_index = (tmp_path / "docs" / "stories.md").read_text(encoding="utf-8")
    assert "## Current Execution Map" in stories_index
    assert "Compiler-driven execution map summary." in stories_index
    assert "| **001** Honest blocked story | Active methodology follow-on. |" in stories_index
    assert "## Health Flags" in stories_index
    assert "No stories currently blocked." in stories_index
    assert (
        "- Sequencing bias: `spec:11` (stories: 001) — Keep the methodology lane honest."
        in stories_index
    )


def test_methodology_graph_renders_blocked_line_as_health_flag_not_execution_lane(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Blocked",
        blocker_summary="Waiting on upstream substrate decision.",
        blocker_evidence="Current compiler contract still disagrees with the skill surface.",
        unblock_condition="Land the compiler and skill alignment patch.",
    )
    _write(
        tmp_path / "docs" / "methodology" / "state.yaml",
        """
        {
          "categories": {
            "spec:11": {
              "product_need": "Execution clarity",
              "tech_need": "Methodology substrate",
              "substrate": "exists",
              "phase": "hold",
              "story_coverage": "partial",
              "notes": []
            }
          },
          "compromises": {},
          "stories_index": {
            "current_execution_map": {
              "summary": "Compiler-driven execution map summary.",
              "lanes": [
                {
                  "id": "in-progress",
                  "title": "In Progress",
                  "statuses": ["In Progress"],
                  "empty_message": "No stories currently in progress.",
                  "story_notes": {}
                },
                {
                  "id": "blocked",
                  "title": "Blocked — Dependency Chain Not Ready Yet",
                  "statuses": ["Blocked"],
                  "health_flag": true,
                  "empty_message": "No blocked lines currently need attention.",
                  "story_notes": {
                    "001": "Blocked until unblocked; keep visible, do not reopen."
                  }
                }
              ]
            },
            "sections": []
          },
          "roadmap": {
            "active_focus": [],
            "sequencing_bias": [],
            "campaigns": []
          },
          "architecture_audits": {
            "cadence": {
              "target_story_interval": 5
            },
            "domains": {}
          },
          "ui_scout": {
            "cadence": {
              "max_days_without_run": 7
            },
            "last_run_at": "2026-04-04",
            "last_run_story_id": "001",
            "scenarios": {
              "FP1": {
                "label": "Canonical fixture",
                "last_checked": "2026-04-04",
                "latest_report": "report-001",
                "status": "pass",
                "follow_up_story_refs": []
              }
            }
          }
        }
        """,
    )

    result = _run_methodology_graph(tmp_path, "build")

    assert result.returncode == 0, result.stderr
    stories_index = (tmp_path / "docs" / "stories.md").read_text(encoding="utf-8")
    assert "## Current Execution Map" in stories_index
    assert "### In Progress" in stories_index
    assert "No stories currently in progress." in stories_index
    assert "## Health Flags" in stories_index
    assert "### Blocked — Dependency Chain Not Ready Yet" in stories_index
    assert (
        "| **001** Honest blocked story | "
        "Blocked until unblocked; keep visible, do not reopen. |"
        in stories_index
    )


def test_methodology_graph_rejects_stale_execution_map_and_campaign_refs(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Done",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "methodology" / "state.yaml",
        """
        {
          "categories": {
            "spec:11": {
              "product_need": "Execution clarity",
              "tech_need": "Methodology substrate",
              "substrate": "exists",
              "phase": "hold",
              "story_coverage": "partial",
              "notes": []
            }
          },
          "compromises": {},
          "stories_index": {
            "current_execution_map": {
              "summary": "Compiler-driven execution map summary.",
              "lanes": [
                {
                  "id": "in-progress",
                  "title": "In Progress",
                  "statuses": ["In Progress"],
                  "empty_message": "No stories currently in progress.",
                  "story_notes": {
                    "001": "Active methodology follow-on."
                  }
                }
              ]
            },
            "sections": []
          },
          "roadmap": {
            "active_focus": ["spec:11"],
            "sequencing_bias": [
              {
                "target": "spec:11",
                "reason": "Keep the methodology lane honest.",
                "story_refs": ["001"]
              }
            ],
            "campaigns": [
              {
                "id": "workflow-repair",
                "status": "active",
                "story_refs": ["001"],
                "notes": "Still in flight."
              }
            ]
          },
          "architecture_audits": {
            "cadence": {
              "target_story_interval": 5
            },
            "domains": {}
          },
          "ui_scout": {
            "cadence": {
              "max_days_without_run": 7
            },
            "last_run_at": "2026-04-04",
            "last_run_story_id": "001",
            "scenarios": {
              "FP1": {
                "label": "Canonical fixture",
                "last_checked": "2026-04-04",
                "latest_report": "report-001",
                "status": "pass",
                "follow_up_story_refs": []
              }
            }
          }
        }
        """,
    )

    result = _run_methodology_graph(tmp_path, "print")

    assert result.returncode == 1
    assert (
        "state.stories_index.current_execution_map.lanes[0] (in-progress) references story 001 "
        "with status Done, expected In Progress" in result.stderr
    )
    assert (
        "state.roadmap.sequencing_bias[0] points only at terminal stories: 001"
        in result.stderr
    )
    assert (
        "state.roadmap.campaigns[0] (workflow-repair) is active but only references "
        "terminal stories: 001" in result.stderr
    )


def test_methodology_graph_rejects_eval_missing_explicit_lineage_fields(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Done",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "evals" / "registry.yaml",
        """
        evals:
          - id: sample-eval
            name: Sample Eval
            type: quality
            description: >
              Minimal eval fixture without explicit lineage metadata.
            runner: promptfoo
            command: "echo sample"
        """,
    )

    result = _run_methodology_graph(tmp_path, "print")

    assert result.returncode == 1
    assert (
        "eval sample-eval is missing explicit lineage fields: spec_refs, "
        "story_refs, category_refs, compromise_refs" in result.stderr
    )
    assert (
        "eval sample-eval has no category_refs; explicit eval category ownership "
        "is required" in result.stderr
    )


def test_methodology_graph_exports_explicit_eval_lineage(tmp_path: Path) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Done",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "evals" / "registry.yaml",
        """
        evals:
          - id: sample-eval
            name: Sample Eval
            type: quality
            spec_refs:
              - spec:11
            story_refs:
              - "001"
            category_refs:
              - spec:11
            compromise_refs: []
            description: >
              Minimal eval fixture with explicit lineage metadata.
            runner: promptfoo
            command: "echo sample"
        """,
    )

    result = _run_methodology_graph(tmp_path, "build")

    assert result.returncode == 0, result.stderr
    graph = json.loads(
        (tmp_path / "docs" / "methodology" / "graph.json").read_text(
            encoding="utf-8"
        )
    )
    eval_record = graph["evals"][0]
    assert eval_record["id"] == "sample-eval"
    assert eval_record["specRefs"] == ["spec:11"]
    assert eval_record["storyIds"] == ["001"]
    assert eval_record["categoryRefs"] == ["spec:11"]
    assert eval_record["declaredCategoryRefs"] == ["spec:11"]
    assert eval_record["derivedCategoryRefs"] == ["spec:11"]


def test_methodology_graph_rejects_eval_category_refs_that_do_not_match_lineage(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Done",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "evals" / "registry.yaml",
        """
        evals:
          - id: sample-eval
            name: Sample Eval
            type: quality
            spec_refs:
              - spec:11
            story_refs: []
            category_refs:
              - spec:8
            compromise_refs: []
            description: >
              Minimal eval fixture with mismatched category metadata.
            runner: promptfoo
            command: "echo sample"
        """,
    )

    result = _run_methodology_graph(tmp_path, "print")

    assert result.returncode == 1
    assert (
        "eval sample-eval category_refs mismatch derived lineage: declared spec:8 "
        "vs derived spec:11" in result.stderr
    )
    assert "eval sample-eval references missing category spec:8" in result.stderr


def test_methodology_graph_rejects_unrecognized_structured_state_keys(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Done",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "methodology" / "state.yaml",
        """
        {
          "categories": {
            "spec:11": {
              "product_need": "Execution clarity",
              "tech_need": "Methodology substrate",
              "substrate": "exists",
              "phase": "hold",
              "story_coverage": "partial",
              "notes": [],
              "rogue_key": true
            }
          },
          "compromises": {},
          "stories_index": {
            "sections": []
          },
          "roadmap": {
            "active_focus": [],
            "sequencing_bias": [],
            "campaigns": []
          },
          "architecture_audits": {
            "cadence": {
              "target_story_interval": 5
            },
            "domains": {}
          },
          "ui_scout": {
            "cadence": {
              "max_days_without_run": 7
            },
            "last_run_at": "2026-04-04",
            "last_run_story_id": "001",
            "scenarios": {
              "FP1": {
                "label": "Canonical fixture",
                "last_checked": "2026-04-04",
                "latest_report": "report-001",
                "status": "pass",
                "follow_up_story_refs": []
              }
            }
          },
          "unexpected_top_level": true
        }
        """,
    )

    result = _run_methodology_graph(tmp_path, "print")

    assert result.returncode == 1
    assert "state.unexpected_top_level is not a recognized structured state key" in result.stderr
    assert (
        "state.categories.spec:11.rogue_key is not a recognized structured state key"
        in result.stderr
    )


def test_methodology_graph_lints_unqualified_story_index_wording_on_active_surfaces(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Done",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "README.md",
        """
        # Temp Repo

        Use the story index to find the next task.
        """,
    )

    result = _run_methodology_graph(tmp_path, "print")

    assert result.returncode == 1
    assert "README.md:3 still uses unqualified story-index wording" in result.stderr


def test_methodology_graph_does_not_flag_hyphenated_setup_filenames_as_retired_setup_guidance(
    tmp_path: Path,
) -> None:
    _seed_methodology_repo(
        tmp_path,
        story_status="Done",
        blocker_summary="N/A",
        blocker_evidence="N/A",
        unblock_condition="N/A",
    )
    _write(
        tmp_path / "docs" / "scout.md",
        """
        # Scout Index

        | ID | Scout |
        |---|---|
        | 016 | [Storybook Playwright setup](docs/scout/scout-016-storybook-playwright-setup.md) |
        """,
    )

    result = _run_methodology_graph(tmp_path, "build")

    assert result.returncode == 0, result.stderr
