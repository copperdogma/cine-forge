#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TODAY = date.fromisoformat(
    os.environ.get("TRIAGE_FACTS_TODAY", date.today().isoformat())
)

LANE_SKILLS = [
    "triage-stories",
    "triage-inbox",
    "triage-evals",
    "triage-architecture",
    "triage-health",
    "codebase-improvement-scout",
    "discover-models",
    "loop-verify",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize cheap CineForge triage facts."
    )
    parser.add_argument("--json", action="store_true", help="emit JSON facts")
    args = parser.parse_args()
    facts = collect_facts()
    if args.json:
        print(json.dumps(facts, indent=2, sort_keys=True))
    else:
        print_text(facts)
    return 0


def collect_facts() -> dict[str, Any]:
    graph = read_json("docs/methodology/graph.json", {})
    state = graph.get("state") if isinstance(graph.get("state"), dict) else {}
    return {
        "generated_for_date": TODAY.isoformat(),
        "repo": "cine-forge",
        "git": git_facts(),
        "lanes": lane_presence(),
        "methodology_tooling": methodology_tooling_facts(),
        "graph": graph_facts(graph),
        "state": state_facts(state),
        "inbox": inbox_facts(),
        "architecture": architecture_facts(state),
        "ui_scout": ui_scout_facts(state),
        "codebase_improvement": codebase_improvement_facts(),
        "recent_churn": recent_churn_facts(),
    }


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_json(relative_path: str, fallback: Any) -> Any:
    text = read_text(relative_path)
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def git(args: list[str], *, strip: bool = True) -> str:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            encoding="utf-8",
            env=env,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    output = completed.stdout
    return output.strip() if strip else re.sub(r"(?:\r?\n)+$", "", output)


def git_facts() -> dict[str, Any]:
    status = git(["status", "--short"], strip=False)
    return {
        "branch": git(["branch", "--show-current"]) or None,
        "head": git(["rev-parse", "--short", "HEAD"]) or None,
        "upstream": git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        or None,
        "dirty": bool(status),
        "status_short": [line for line in status.splitlines() if line][:30],
    }


def lane_presence() -> dict[str, str]:
    return {
        name: "present"
        if (ROOT / ".agents" / "skills" / name / "SKILL.md").exists()
        else "absent"
        for name in LANE_SKILLS
    }


def methodology_tooling_facts() -> dict[str, Any]:
    skill_root = ROOT / ".agents" / "skills"
    wrapper_root = ROOT / ".gemini" / "commands"
    invocable = []
    if skill_root.exists():
        for skill_file in sorted(skill_root.glob("*/SKILL.md")):
            skill_text = read_text(str(skill_file.relative_to(ROOT)))
            if re.search(r"^user-invocable:\s*true\s*$", skill_text, re.M):
                invocable.append(skill_file.parent.name)
    wrappers = (
        sorted(path.stem for path in wrapper_root.glob("*.toml"))
        if wrapper_root.exists()
        else []
    )
    return {
        "invocable_skill_count": len(invocable),
        "gemini_wrapper_count": len(wrappers),
        "missing_gemini_wrappers": sorted(set(invocable) - set(wrappers)),
        "extra_gemini_wrappers": sorted(set(wrappers) - set(invocable)),
    }


def graph_facts(graph: dict[str, Any]) -> dict[str, Any]:
    stories = graph.get("stories") or []
    evals = graph.get("evals") or []
    compromises = (graph.get("spec") or {}).get("compromises") or []
    return {
        "stories": {
            "total": len(stories),
            "by_status": count_by(
                stories, lambda item: item.get("status") or "Unknown"
            ),
            "recommended_now": [
                compact_actionability(item)
                for item in stories
                if (item.get("actionability") or {}).get("recommendedNow")
            ],
            "blocked": [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "path": item.get("path"),
                    "unblock_condition": item.get("unblockCondition") or "",
                }
                for item in stories
                if item.get("status") == "Blocked"
            ],
            "in_progress": [
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "path": item.get("path"),
                }
                for item in stories
                if item.get("status") == "In Progress"
            ],
        },
        "evals": {
            "total": len(evals),
            "by_type": count_by(evals, lambda item: item.get("type") or "unknown"),
            "recommended_now": [
                compact_actionability(item)
                for item in evals
                if (item.get("actionability") or {}).get("recommendedNow")
            ],
            "retry_ready": [
                {
                    "id": item.get("id"),
                    "ready_triggers": [
                        retry.get("condition")
                        for retry in item.get("retryState") or []
                        if retry.get("status") == "ready"
                    ],
                }
                for item in evals
                if any(
                    retry.get("status") == "ready"
                    for retry in item.get("retryState") or []
                )
            ],
            "stale_scores": [
                {
                    "id": item.get("id"),
                    "measured": (item.get("latestScore") or {}).get("measured"),
                    "days_since": days_since(
                        (item.get("latestScore") or {}).get("measured")
                    ),
                }
                for item in evals
                if not (item.get("latestScore") or {}).get("measured")
                or days_since((item.get("latestScore") or {}).get("measured")) > 30
            ][:20],
        },
        "compromises": {
            "total": len(compromises),
            "by_phase": count_by(
                compromises,
                lambda item: (item.get("state") or {}).get("phase") or "unknown",
            ),
            "recommended_now": [
                compact_actionability(item)
                for item in compromises
                if (item.get("actionability") or {}).get("recommendedNow")
            ],
        },
    }


def compact_actionability(item: dict[str, Any]) -> dict[str, Any]:
    actionability = item.get("actionability") or {}
    return {
        "id": item.get("id"),
        "title": item.get("title") or item.get("name"),
        "posture": actionability.get("posture"),
        "why_now": actionability.get("whyNow") or "",
    }


def state_facts(state: dict[str, Any]) -> dict[str, Any]:
    categories = state.get("categories") or {}
    compromises = state.get("compromises") or {}
    return {
        "categories": {
            "total": len(categories),
            "by_phase": count_by(
                categories.values(), lambda item: item.get("phase") or "unknown"
            ),
            "by_substrate": count_by(
                categories.values(),
                lambda item: item.get("substrate") or "unknown",
            ),
            "partial_coverage": [
                key
                for key, item in categories.items()
                if item.get("story_coverage") in {"partial", "missing"}
            ],
        },
        "compromises": {
            "total": len(compromises),
            "by_phase": count_by(
                compromises.values(), lambda item: item.get("phase") or "unknown"
            ),
        },
    }


def inbox_facts() -> dict[str, Any]:
    text = read_text("docs/inbox.md")
    items = [
        line.strip()
        for line in text.splitlines()
        if line.lstrip().startswith(("- [ ]", "* [ ]", "- ", "* "))
        and "No live items" not in line
    ]
    return {"path": "docs/inbox.md", "untriaged_count": len(items), "sample": items[:10]}


def architecture_facts(state: dict[str, Any]) -> dict[str, Any]:
    audits = state.get("architecture_audits") or {}
    cadence = audits.get("cadence") or {}
    target = cadence.get("target_story_interval")
    domains = audits.get("domains") or {}
    due = []
    for domain, info in domains.items():
        stories_since = info.get("stories_since_audit")
        if info.get("open_findings") or info.get("manual_priority") == "high":
            due.append(domain)
        elif (
            isinstance(target, int)
            and isinstance(stories_since, int)
            and stories_since >= target
        ):
            due.append(domain)
    return {
        "status": "present" if domains else "absent",
        "target_story_interval": target,
        "domain_count": len(domains),
        "due_domains": sorted(set(due)),
    }


def ui_scout_facts(state: dict[str, Any]) -> dict[str, Any]:
    scout = state.get("ui_scout") or {}
    scenarios = scout.get("scenarios") or {}
    stale = []
    issue = []
    max_days = (scout.get("cadence") or {}).get("max_days_without_run")
    for key, item in scenarios.items():
        status = item.get("status") or "unknown"
        last_checked = item.get("last_checked")
        age = days_since(last_checked)
        if status in {"issues_found", "recheck_due", "never"}:
            issue.append(key)
        if isinstance(max_days, int) and age > max_days:
            stale.append(key)
    return {
        "status": "present" if scout else "absent",
        "last_run_at": scout.get("last_run_at"),
        "scenario_count": len(scenarios),
        "stale_scenarios": stale,
        "attention_scenarios": issue,
    }


def codebase_improvement_facts() -> dict[str, Any]:
    reports_dir = ROOT / "docs" / "reports" / "codebase-improvement"
    reports = sorted(reports_dir.glob("*.md")) if reports_dir.exists() else []
    latest = reports[-1] if reports else None
    return {
        "status": "present" if latest else "absent",
        "latest_report": str(latest.relative_to(ROOT)) if latest else None,
        "latest_age_days": days_since(extract_date(latest.name)) if latest else None,
    }


def recent_churn_facts() -> dict[str, Any]:
    output = git(["diff", "--name-only", "HEAD~20..HEAD"], strip=False)
    files = [line for line in output.splitlines() if line]
    top_dirs = Counter(path.split("/", 1)[0] for path in files).most_common(10)
    return {"changed_files_last_20_commits": len(files), "top_dirs": top_dirs}


def count_by(items: Any, key_fn) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in items:
        counter[str(key_fn(item))] += 1
    return dict(sorted(counter.items()))


def extract_date(name: str) -> str | None:
    match = re.search(r"(20\d{2})(\d{2})(\d{2})", name)
    if match:
        return "-".join(match.groups())
    match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", name)
    if match:
        return "-".join(match.groups())
    return None


def days_since(value: Any) -> int:
    if not value:
        return 10_000
    try:
        parsed = date.fromisoformat(str(value)[:10])
    except ValueError:
        return 10_000
    return (TODAY - parsed).days


def print_text(facts: dict[str, Any]) -> None:
    graph = facts["graph"]
    wrapper_drift = len(
        facts["methodology_tooling"]["missing_gemini_wrappers"]
    ) + len(facts["methodology_tooling"]["extra_gemini_wrappers"])
    print("Triage Facts")
    print(f"- branch: {facts['git']['branch']} @ {facts['git']['head']}")
    print(f"- dirty: {'yes' if facts['git']['dirty'] else 'no'}")
    print(f"- stories: {json.dumps(graph['stories']['by_status'], sort_keys=True)}")
    print(f"- recommended stories: {len(graph['stories']['recommended_now'])}")
    print(f"- recommended evals: {len(graph['evals']['recommended_now'])}")
    print(
        "- compromises by phase: "
        f"{json.dumps(graph['compromises']['by_phase'], sort_keys=True)}"
    )
    print(f"- inbox untriaged: {facts['inbox']['untriaged_count']}")
    print(f"- architecture due domains: {len(facts['architecture']['due_domains'])}")
    print(f"- ui scout attention: {len(facts['ui_scout']['attention_scenarios'])}")
    print(f"- codebase improvement: {facts['codebase_improvement']['status']}")
    print(f"- wrapper drift: {wrapper_drift}")


if __name__ == "__main__":
    raise SystemExit(main())
