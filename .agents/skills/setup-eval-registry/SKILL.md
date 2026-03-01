---
name: setup-eval-registry
description: Bootstrap the eval registry system for tracking and improving AI evals
user-invocable: true
---

# /setup-eval-registry

Bootstrap the eval registry system in the current project. Creates the `docs/evals/`
directory structure, empty registry, templates, and `scripts/discover-models.py`.
Safe to run on an existing project — does not overwrite existing files.

## What This Skill Produces

- `docs/evals/registry.yaml` — Empty eval registry (schema documented, no entries)
- `docs/evals/attempt-template.md` — Template for improvement attempt write-ups
- `docs/evals/attempts/` — Directory for individual attempt files
- `docs/evals/README.md` — Protocol documentation for the system
- `scripts/discover-models.py` — Provider-agnostic model discovery script

## When to Run This

Run this once when starting a new project that will have AI-powered capabilities,
or when adding the eval registry to an existing project that doesn't have one yet.

After bootstrapping, add your project-specific eval entries to `docs/evals/registry.yaml`
following the schema documented in the file header.

## Steps

### 1. Execute the bootstrap script

Run the inline script below. It is idempotent — skip if file already exists.

```bash
#!/usr/bin/env bash
# setup-eval-registry bootstrap
# Run from the project root. Skips files that already exist.

set -e

SKIP=0
CREATE=0

skip_if_exists() {
  local path="$1"
  if [ -e "$path" ]; then
    echo "  [skip] $path (already exists)"
    SKIP=$((SKIP + 1))
    return 1
  fi
  return 0
}

create_file() {
  local path="$1"
  local content="$2"
  mkdir -p "$(dirname "$path")"
  printf '%s' "$content" > "$path"
  echo "  [create] $path"
  CREATE=$((CREATE + 1))
}

echo "Setting up eval registry..."

# ── docs/evals/registry.yaml ───────────────────────────────────────────────
if skip_if_exists "docs/evals/registry.yaml"; then :; else
  :
fi

if [ ! -e "docs/evals/registry.yaml" ]; then
  mkdir -p docs/evals
  cat > "docs/evals/registry.yaml" << 'REGISTRY_EOF'
# Eval Registry
# Central source of truth for all evals, their scores, and improvement attempts.
# Updated by AI agents whenever evals are run. See README.md for the protocol.
#
# Types:
#   quality     — "How good is our output?" Continuous improvement target.
#   compromise  — "Can we eliminate this compromise?" Binary pass/fail gate.
#
# retry_when conditions:
#   new-worker-model     — A smarter orchestrating AI might succeed where the previous one couldn't
#   new-subject-model    — A better pipeline model might pass without code changes
#   cheaper-subject-model — Works on expensive model, need cost parity at lower tier
#   new-approach         — Current approaches exhausted, needs fresh thinking
#   golden-fix           — Golden reference may be wrong or incomplete
#   architecture-change  — Upstream pipeline needs to change first
#   dependency-available — Waiting on a library/tool/API that doesn't exist yet

evals:

  # ── Quality Evals ─────────────────────────────────────────────────────────
  # Add entries here as you build AI-powered capabilities.
  # Each eval corresponds to one AI task in your pipeline.
  #
  # Example entry:
  #
  # - id: my-capability
  #   name: My Capability
  #   type: quality
  #   description: >
  #     What this eval tests — be specific about the input, output,
  #     and what "good" looks like.
  #   pipeline_stage: extract  # or: normalize, enrich, qa, generate, etc.
  #   runner: promptfoo
  #   command: "cd benchmarks && promptfoo eval -c tasks/my-capability.yaml --no-cache -j 3"
  #   config: benchmarks/tasks/my-capability.yaml
  #   scorer: benchmarks/scorers/my_capability_scorer.py
  #   golden: benchmarks/golden/my-capability-golden.json
  #   test_cases: 3  # number of test cases
  #
  #   target:
  #     metric: overall
  #     value: 0.95
  #     constraints:
  #       cost_usd_max: null
  #       duration_seconds_max: null
  #
  #   scores:
  #     - model: "Sonnet 4.6"
  #       metrics:
  #         overall: 0.942
  #       measured: 2026-01-01
  #       git_sha: "abc1234"
  #       result_file: benchmarks/results/my-capability-sonnet46.json
  #
  #   attempts: []

  # ── Compromise Evals ──────────────────────────────────────────────────────
  # Add entries here for each compromise in docs/spec.md that has a detection
  # mechanism. Each tests whether a spec compromise can be eliminated.
  #
  # Example entry:
  #
  # - id: compromise-C1-example
  #   name: "Compromise C1: Example Compromise"
  #   type: compromise
  #   compromise_id: "C1"
  #   description: >
  #     What capability gate would allow eliminating this compromise?
  #   detection_mechanism: >
  #     Concrete, measurable condition. E.g.: SOTA model achieves X on Y task
  #     with Z constraints.
  #   ideal_link: "docs/ideal.md"
  #   spec_link: "docs/spec.md#section"
  #   runner: promptfoo  # or: custom, registry-scan, capability-check
  #   command: null  # fill in when eval is implemented
  #   scores: []
  #   attempts: []
REGISTRY_EOF
  echo "  [create] docs/evals/registry.yaml"
  CREATE=$((CREATE + 1))
fi

# ── docs/evals/attempts/ ───────────────────────────────────────────────────
if [ ! -e "docs/evals/attempts/.gitkeep" ]; then
  mkdir -p docs/evals/attempts
  touch docs/evals/attempts/.gitkeep
  echo "  [create] docs/evals/attempts/.gitkeep"
  CREATE=$((CREATE + 1))
fi

# ── docs/evals/attempt-template.md ────────────────────────────────────────
if [ ! -e "docs/evals/attempt-template.md" ]; then
  cat > "docs/evals/attempt-template.md" << 'TEMPLATE_EOF'
# Eval Attempt {ID} — {Eval Name}: {Short Title}

**Status:** In Progress | Succeeded | Failed | Inconclusive
**Eval:** {eval-id from registry.yaml}
**Date:** {YYYY-MM-DD}
**Worker Model:** {AI doing the improvement work, e.g. "Opus 4.6"}
**Subject Model(s):** {Model(s) being evaluated/used in pipeline, e.g. "Sonnet 4.6, Haiku 4.5"}

## Mission

{One paragraph: what are we trying to improve, from what score to what target, and why this eval was chosen.}

## Prior Attempts

{Summary of past attempts on this eval — what was tried, what failed, what's off-limits.
Read ALL previous attempt files for this eval before writing this section.
If this is the first attempt, write "First attempt on this eval."}

## Plan

{Numbered steps for the improvement approach. Be specific.}

## Work Log

{Chronological log of what was tried and what happened. Include scores.}

- {timestamp or step}: {action taken} — {result, with score if applicable}

## Conclusion

**Result:** {succeeded | failed | inconclusive}
**Score before:** {0.XXX}
**Score after:** {0.XXX}

**What worked:** {For successes — what specifically made the difference.}

**What failed:** {For failures — what approaches didn't work and why.}

**What NOT to retry:** {Approaches that made things worse or are definitively dead ends.}

**Retry when:**
{Structured conditions under which this should be retried. Use registry condition codes:
new-worker-model, new-subject-model, cheaper-subject-model, new-approach,
golden-fix, architecture-change, dependency-available}

---

## Definition of Done Checklist

- [ ] Read all previous attempts for this eval before starting
- [ ] Ran the eval with `--no-cache` to get clean measurements
- [ ] Recorded score_before and score_after in this file
- [ ] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [ ] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [ ] If approach succeeded: verified improvement holds across multiple runs
- [ ] If approach failed: classified the failure and set retry_when conditions
- [ ] Did NOT silently accept score regressions
TEMPLATE_EOF
  echo "  [create] docs/evals/attempt-template.md"
  CREATE=$((CREATE + 1))
fi

# ── docs/evals/README.md ───────────────────────────────────────────────────
if [ ! -e "docs/evals/README.md" ]; then
  cat > "docs/evals/README.md" << 'README_EOF'
# Eval Registry System

Central tracking for all evaluation metrics, improvement attempts, and compromise gates.

## Structure

```
docs/evals/
├── registry.yaml          # Source of truth — all evals, scores, attempt summaries
├── attempt-template.md    # Template for new improvement attempt stories
├── attempts/              # One markdown file per improvement attempt
│   ├── 001-{eval}-{title}.md
│   └── ...
└── README.md              # This file
```

## Registry Protocol

### When to update `registry.yaml`

**Always** update the registry when you run an eval. This is part of the Definition of Done.

| Situation | Action |
|---|---|
| Ran an eval (any reason) | Update the `scores` section with new measurements + git_sha + date |
| Completed an improvement attempt | Add entry to `attempts` list + update scores |
| New eval created | Add full eval entry to registry |
| New compromise identified | Add compromise eval entry |
| Score is stale (code changed since git_sha) | Re-run and update |

### Staleness

A score is **stale** if the codebase has changed significantly since `git_sha`. The `/improve-eval` skill checks this automatically. When in doubt, re-measure.

## Improvement Attempts

### Creating an attempt

1. Copy `attempt-template.md` to `attempts/{NNN}-{eval-id}-{short-title}.md`
2. Number sequentially across ALL evals (not per-eval)
3. Read ALL previous attempts for the target eval before starting
4. Follow the Definition of Done checklist at the bottom of the template

### Attempt summary in registry

After completing an attempt (success or failure), add a compact summary to the eval's `attempts` list:

```yaml
attempts:
  - id: "001"
    story: attempts/001-my-capability-prompt-tuning.md
    date: 2026-03-01
    status: failed  # succeeded | failed | inconclusive
    approach: "Multi-layer analysis prompt with structured output example"
    worker_model: "Opus 4.6"
    worker_model_date: 2025-12-01
    subject_model: "Sonnet 4.6"
    score_before: 0.880
    score_after: 0.865
    retry_when:
      - condition: new-worker-model
        note: "Approach is valid but needs smarter orchestrator"
```

### Retry conditions

| Condition | Meaning | Recheck trigger |
|---|---|---|
| `new-worker-model` | Smarter AI might execute same approach better | New model release |
| `new-subject-model` | Better pipeline model might pass without code changes | New model release |
| `cheaper-subject-model` | Works on expensive model, need cost parity | Pricing changes |
| `new-approach` | Current approaches exhausted | Fresh thinking / new technique |
| `golden-fix` | Golden reference may be wrong/incomplete | Manual review |
| `architecture-change` | Upstream pipeline needs to change first | Pipeline refactor |
| `dependency-available` | Waiting on a library/tool/API | Ecosystem changes |

## Compromise Evals

Compromise evals test whether a spec compromise can be eliminated. They link to `docs/spec.md` compromise entries and `docs/ideal.md`.

When a compromise eval passes its gate consistently, the compromise can be deleted from `docs/spec.md` and the system moves closer to the Ideal.

Failed attempts on compromise evals are especially valuable to log — they record "the frontier isn't here yet" with evidence, and become easy wins when the frontier advances.

## Scoring

Evals can report any metrics they want. The registry stores whatever the eval produces:

```yaml
scores:
  - model: "Sonnet 4.6"
    metrics:
      overall: 0.942        # headline score
      major_items: 0.98     # sub-scores if available
      minor_items: 0.91
    cost_usd: 0.12           # optional: per-run cost
    duration_seconds: 45     # optional: wall-clock time
```

The `target` on the eval specifies what "good enough" means, including optional constraints:

```yaml
target:
  metric: overall
  value: 0.95
  constraints:
    cost_usd_max: 0.50       # improvement that costs $5/run isn't improvement
    duration_seconds_max: 120
```

The AI evaluating whether an attempt "succeeded" uses all of this context — score, cost, time, constraints — to make a holistic judgment.
README_EOF
  echo "  [create] docs/evals/README.md"
  CREATE=$((CREATE + 1))
fi

# ── scripts/discover-models.py ─────────────────────────────────────────────
# NOTE: This is a minimal version without tier classification or --summary.
# For the full version with tier classification (SOTA/mid/cheap/reasoning/legacy),
# copy from a project that has it, or run /improve-skill on this skill.
if [ ! -e "scripts/discover-models.py" ]; then
  mkdir -p scripts
  cat > "scripts/discover-models.py" << 'DISCOVER_EOF'
#!/usr/bin/env python3
"""Discover available AI models across providers.

Checks environment for API keys, queries each provider's model endpoint,
and outputs a structured report of available models for eval work.

Usage:
    python scripts/discover-models.py              # Full report to stdout
    python scripts/discover-models.py --yaml        # YAML output (machine-readable)
    python scripts/discover-models.py --cache       # Write to docs/evals/models-available.yaml
    python scripts/discover-models.py --check-new   # Compare against registry, flag untested models
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# httpx is a project dependency (pyproject.toml)
try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None


# ── Provider Definitions ────────────────────────────────────────────────────

PROVIDERS = {
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "display": "OpenAI",
        "setup_url": "https://platform.openai.com/api-keys",
        "setup_hint": "export OPENAI_API_KEY='sk-...'",
    },
    "anthropic": {
        "env_key": "ANTHROPIC_API_KEY",
        "display": "Anthropic",
        "setup_url": "https://console.anthropic.com/settings/keys",
        "setup_hint": "export ANTHROPIC_API_KEY='sk-ant-...'",
    },
    "google": {
        "env_key": "GEMINI_API_KEY",
        "display": "Google (Gemini)",
        "setup_url": "https://aistudio.google.com/app/apikey",
        "setup_hint": "export GEMINI_API_KEY='AI...'",
    },
}

# Chat-capable model patterns per provider (filters out embeddings, TTS, image, etc.)
OPENAI_CHAT_PATTERNS = [
    r"^gpt-",
    r"^o[134]-",
    r"^chatgpt-",
]

# Models to skip (old, deprecated, or irrelevant)
OPENAI_SKIP_PATTERNS = [
    r"-instruct",
    r"^gpt-3\.5",
    r"^gpt-4-\d{4}",  # dated snapshots like gpt-4-0613
    r"-realtime",
    r"-audio",
    r"-transcribe",
    r"-tts",
    r"-search-",
    r"-image",
    r"-codex",
    r"^chatgpt-image",
    r"-deep-research",
]

# Google models to skip (non-text, open-source, specialized)
GOOGLE_SKIP_PATTERNS = [
    r"^gemma-",         # open-source, not API-tier
    r"-tts",            # text-to-speech
    r"-image",          # image generation
    r"-robotics-",      # robotics
    r"^deep-research-", # deep research (not standard chat)
    r"-customtools",    # custom tools preview
    r"^nano-banana",    # internal codenames
    r"^gemini-2\.0-",   # older generation
    r"^gemini-1\.",     # very old
]


# ── Provider Query Functions ────────────────────────────────────────────────


def query_openai(api_key: str) -> list[dict]:
    """Query OpenAI /v1/models for chat-capable models."""
    resp = httpx.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    models = []
    for m in data.get("data", []):
        model_id = m["id"]
        # Filter to chat models
        if not any(re.match(p, model_id) for p in OPENAI_CHAT_PATTERNS):
            continue
        # Skip deprecated/irrelevant
        if any(re.search(p, model_id) for p in OPENAI_SKIP_PATTERNS):
            continue
        models.append({
            "id": model_id,
            "provider": "openai",
            "created": datetime.fromtimestamp(m.get("created", 0), tz=timezone.utc).strftime("%Y-%m-%d"),
        })

    # Sort by creation date descending (newest first)
    models.sort(key=lambda x: x["created"], reverse=True)
    return models


def query_anthropic(api_key: str) -> list[dict]:
    """Query Anthropic /v1/models for available models."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    try:
        resp = httpx.get(
            "https://api.anthropic.com/v1/models",
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        models = []
        for m in data.get("data", []):
            model_id = m["id"]
            # Parse created_at — may be ISO string or unix timestamp
            created_raw = m.get("created_at")
            if isinstance(created_raw, str):
                created = created_raw[:10]  # "2025-12-01T..." -> "2025-12-01"
            elif isinstance(created_raw, (int, float)) and created_raw > 0:
                created = datetime.fromtimestamp(created_raw, tz=timezone.utc).strftime("%Y-%m-%d")
            else:
                created = "unknown"
            models.append({
                "id": model_id,
                "provider": "anthropic",
                "display_name": m.get("display_name", model_id),
                "created": created,
            })

        models.sort(key=lambda x: x.get("created", ""), reverse=True)
        return models
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        # Anthropic models endpoint may not be available on all plans
        # Fall back to known models
        print(f"  Note: /v1/models returned {e}. Using known model list.", file=sys.stderr)
        return _anthropic_fallback()


def _anthropic_fallback() -> list[dict]:
    """Known Anthropic models when the API endpoint isn't available."""
    return [
        {"id": "claude-opus-4-6", "provider": "anthropic", "display_name": "Claude Opus 4.6", "created": "2025-12-01"},
        {"id": "claude-sonnet-4-6", "provider": "anthropic", "display_name": "Claude Sonnet 4.6", "created": "2025-12-01"},
        {"id": "claude-sonnet-4-5-20241022", "provider": "anthropic", "display_name": "Claude Sonnet 4.5", "created": "2025-10-01"},
        {"id": "claude-haiku-4-5-20251001", "provider": "anthropic", "display_name": "Claude Haiku 4.5", "created": "2025-10-01"},
    ]


def query_google(api_key: str) -> list[dict]:
    """Query Google Gemini /v1beta/models for generative models."""
    resp = httpx.get(
        f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    models = []
    for m in data.get("models", []):
        name = m.get("name", "")
        model_id = name.replace("models/", "")
        # Only include models that support generateContent
        methods = m.get("supportedGenerationMethods", [])
        if "generateContent" not in methods:
            continue
        # Skip embedding and old models
        if "embedding" in model_id or "aqa" in model_id:
            continue
        # Skip non-text, open-source, and specialized models
        if any(re.search(p, model_id) for p in GOOGLE_SKIP_PATTERNS):
            continue
        models.append({
            "id": model_id,
            "provider": "google",
            "display_name": m.get("displayName", model_id),
            "input_token_limit": m.get("inputTokenLimit"),
            "output_token_limit": m.get("outputTokenLimit"),
        })

    # Sort by name to group model families
    models.sort(key=lambda x: x["id"])
    return models


QUERY_FUNCS = {
    "openai": query_openai,
    "anthropic": query_anthropic,
    "google": query_google,
}


# ── Registry Comparison ────────────────────────────────────────────────────


def _normalize_model_name(name: str) -> str:
    """Normalize model name for fuzzy comparison."""
    return name.lower().replace(" ", "-").replace(".", "-").replace("_", "-")


def _matches_registry(model_id: str, display_name: str, registry_models: set[str]) -> bool:
    """Check if a discovered model matches any model in the registry.

    Registry uses human names like 'Sonnet 4.6', API returns IDs like 'claude-sonnet-4-6'.
    We need to match across these formats.
    """
    norm_id = _normalize_model_name(model_id)
    norm_display = _normalize_model_name(display_name) if display_name else ""

    for rm in registry_models:
        norm_rm = _normalize_model_name(rm)
        # Direct containment either direction
        if norm_rm in norm_id or norm_id in norm_rm:
            return True
        if norm_display and (norm_rm in norm_display or norm_display in norm_rm):
            return True
        # Handle "Sonnet 4.6" matching "claude-sonnet-4-6"
        # Strip provider prefix and compare
        stripped_id = re.sub(r"^(claude|gpt|gemini|o\d)-?", "", norm_id)
        stripped_rm = re.sub(r"^(claude|gpt|gemini|o\d)-?", "", norm_rm)
        if stripped_id and stripped_rm and (stripped_rm in stripped_id or stripped_id in stripped_rm):
            return True
        # Handle dated snapshots: "gpt-5-2-2025-12-11" should match "GPT-5.2"
        # Remove date suffixes for comparison
        id_no_date = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", norm_id)
        rm_no_date = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", norm_rm)
        if id_no_date and rm_no_date and (rm_no_date in id_no_date or id_no_date in rm_no_date):
            return True
    return False


def load_registry_models(registry_path: Path) -> set[str]:
    """Extract all model names mentioned in the eval registry."""
    if not registry_path.exists():
        return set()
    if yaml is None:
        # Fallback: grep for model names
        text = registry_path.read_text()
        models = set()
        for line in text.splitlines():
            if "model:" in line:
                m = line.split("model:")[-1].strip().strip('"').strip("'")
                if m:
                    models.add(m)
        return models

    data = yaml.safe_load(registry_path.read_text())
    models = set()
    for ev in data.get("evals", []):
        for score in ev.get("scores", []):
            m = score.get("model", "")
            if m:
                models.add(m)
    return models


# ── Output Formatting ───────────────────────────────────────────────────────


def format_text_report(results: dict, registry_models: set[str] | None = None) -> str:
    """Human-readable text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("  AI Model Discovery Report")
    lines.append(f"  {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("=" * 60)

    # Key status
    lines.append("\n## API Key Status\n")
    for prov_id, prov in PROVIDERS.items():
        key = os.environ.get(prov["env_key"], "")
        status = "SET" if key else "NOT SET"
        icon = "+" if key else "-"
        lines.append(f"  [{icon}] {prov['display']:20s} ({prov['env_key']}): {status}")
        if not key:
            lines.append(f"      Setup: {prov['setup_url']}")
            lines.append(f"      {prov['setup_hint']}")

    # Models per provider
    for prov_id in PROVIDERS:
        models = results.get(prov_id)
        if models is None:
            continue
        if isinstance(models, str):
            # Error message
            lines.append(f"\n## {PROVIDERS[prov_id]['display']}: ERROR\n")
            lines.append(f"  {models}")
            continue

        lines.append(f"\n## {PROVIDERS[prov_id]['display']} — {len(models)} chat models\n")
        for m in models:
            model_id = m["id"]
            extra = ""
            if "display_name" in m and m["display_name"] != model_id:
                extra = f" ({m['display_name']})"
            created = m.get("created", "")
            if created and created != "unknown":
                extra += f"  [created: {created}]"
            if "input_token_limit" in m and m["input_token_limit"]:
                extra += f"  [ctx: {m['input_token_limit']:,}]"

            # Flag if not in registry
            in_registry = ""
            if registry_models is not None:
                matched = _matches_registry(model_id, m.get("display_name", ""), registry_models)
                in_registry = "  [TESTED]" if matched else "  [NEW]"

            lines.append(f"  {model_id}{extra}{in_registry}")

    return "\n".join(lines)


def format_yaml_report(results: dict) -> str:
    """Machine-readable YAML report."""
    report = {
        "discovered": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "providers": {},
    }

    for prov_id in PROVIDERS:
        key_set = bool(os.environ.get(PROVIDERS[prov_id]["env_key"], ""))
        models = results.get(prov_id)

        entry = {
            "api_key_set": key_set,
            "env_key": PROVIDERS[prov_id]["env_key"],
        }

        if models is None:
            entry["status"] = "skipped"
            entry["models"] = []
        elif isinstance(models, str):
            entry["status"] = "error"
            entry["error"] = models
            entry["models"] = []
        else:
            entry["status"] = "ok"
            entry["model_count"] = len(models)
            entry["models"] = models

        report["providers"][prov_id] = entry

    if yaml:
        return yaml.dump(report, default_flow_style=False, sort_keys=False)
    else:
        return json.dumps(report, indent=2)


# ── Main ────────────────────────────────────────────────────────────────────


def discover_models() -> dict:
    """Query all providers and return results dict."""
    results = {}
    for prov_id, prov in PROVIDERS.items():
        api_key = os.environ.get(prov["env_key"], "")
        if not api_key:
            results[prov_id] = None
            continue

        print(f"Querying {prov['display']}...", file=sys.stderr)
        try:
            models = QUERY_FUNCS[prov_id](api_key)
            results[prov_id] = models
            print(f"  Found {len(models)} models", file=sys.stderr)
        except Exception as e:
            results[prov_id] = f"Error: {e}"
            print(f"  Error: {e}", file=sys.stderr)

    return results


def main():
    parser = argparse.ArgumentParser(description="Discover available AI models across providers")
    parser.add_argument("--yaml", action="store_true", help="Output as YAML (machine-readable)")
    parser.add_argument("--cache", action="store_true", help="Write to docs/evals/models-available.yaml")
    parser.add_argument("--check-new", action="store_true", help="Flag models not yet in eval registry")
    args = parser.parse_args()

    results = discover_models()

    # Load registry for comparison if requested
    registry_models = None
    if args.check_new:
        registry_path = Path(__file__).parent.parent / "docs" / "evals" / "registry.yaml"
        registry_models = load_registry_models(registry_path)
        if registry_models:
            print(f"\nRegistry contains {len(registry_models)} tested models: {', '.join(sorted(registry_models))}", file=sys.stderr)

    if args.yaml or args.cache:
        output = format_yaml_report(results)
    else:
        output = format_text_report(results, registry_models)

    if args.cache:
        cache_path = Path(__file__).parent.parent / "docs" / "evals" / "models-available.yaml"
        cache_path.write_text(output)
        print(f"\nWritten to {cache_path}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
DISCOVER_EOF
  chmod +x scripts/discover-models.py
  echo "  [create] scripts/discover-models.py"
  CREATE=$((CREATE + 1))
fi

echo ""
echo "Done. Created $CREATE file(s), skipped $SKIP."
echo ""
echo "Next steps:"
echo "  1. Add your first eval entry to docs/evals/registry.yaml"
echo "  2. Add 'eval registry updated' to your Definition of Done in AGENTS.md"
echo "  3. Run: python scripts/discover-models.py   # to see available models"
```

### 2. Update AGENTS.md Definition of Done

Check whether the AGENTS.md Definition of Done already mentions the eval registry. If it does not, add this bullet to the Definition of Done list:

```
  4. `docs/evals/registry.yaml` is updated — any eval run during this task has a new `scores` entry.
```

The check: grep AGENTS.md for "registry.yaml". If found, skip. If not found, add the bullet.

### 3. Verify

Confirm these files now exist:

```
docs/evals/registry.yaml
docs/evals/attempt-template.md
docs/evals/attempts/.gitkeep
docs/evals/README.md
scripts/discover-models.py
```

Report what was created vs skipped. If any file was skipped (already existed), note it for the user.

## Guardrails

- Never overwrite existing files. The bootstrap is additive only.
- Do not add project-specific eval entries to `registry.yaml` — that's the user's job.
- Do not modify `docs/spec.md` or `docs/ideal.md` — this skill only touches `docs/evals/` and `scripts/`.
- The `discover-models.py` script is copied verbatim — do not customize it per-project.
- If AGENTS.md does not exist yet, note that the Definition of Done update step should be done when AGENTS.md is created.
