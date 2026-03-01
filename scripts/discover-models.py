#!/usr/bin/env python3
"""Discover available AI models across providers.

Checks environment for API keys, queries each provider's model endpoint,
and outputs a structured report of available models for eval work.

Usage:
    python scripts/discover-models.py              # Full report to stdout
    python scripts/discover-models.py --yaml        # YAML output (machine-readable)
    python scripts/discover-models.py --cache       # Write to docs/evals/models-available.yaml
    python scripts/discover-models.py --check-new   # Compare against registry, flag untested models
    python scripts/discover-models.py --summary     # Quick-glance tier summary for /improve-eval
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


# ── Tier Classification ──────────────────────────────────────────────────────
#
# Each entry is (pattern, tier). Patterns are matched in order — first match wins.
# Patterns are checked against the lowercase model ID.
#
# Tiers:
#   sota      — Frontier/flagship models. Use when quality is paramount.
#   mid       — Strong mid-tier. Good quality/cost tradeoff.
#   cheap     — Budget models. Fast and inexpensive, lower quality ceiling.
#   reasoning — Chain-of-thought / reasoning specialists (o-series, etc.).
#   legacy    — Older generation. Avoid for new evals.

TIER_PATTERNS: list[tuple[str, str]] = [
    # ── Reasoning models (check before generic GPT/Claude matches) ───────────
    (r"^o1\b",                  "reasoning"),
    (r"^o1-",                   "reasoning"),
    (r"^o3\b",                  "reasoning"),
    (r"^o3-",                   "reasoning"),
    (r"^o4\b",                  "reasoning"),
    (r"^o4-",                   "reasoning"),

    # ── Budget qualifiers — checked FIRST so "gpt-4.1-mini" hits cheap,
    #    not the mid-tier gpt-4.1 pattern below it. Same for flash-lite.
    # Use word-boundary-aware patterns: "mini" must be preceded by "-" or start,
    # not embedded inside a word like "gemini".
    (r"[-_]mini\b",             "cheap"),
    (r"[-_]nano\b",             "cheap"),
    (r"flash-lite",             "cheap"),
    (r"flash-8b",               "cheap"),
    (r"claude-haiku",           "cheap"),

    # ── OpenAI flagship ──────────────────────────────────────────────────────
    (r"^gpt-5\.2",              "sota"),
    (r"^gpt-5-2",               "sota"),   # dated snapshots e.g. gpt-5-2-2025-12-11
    (r"^gpt-5\b",               "sota"),
    (r"^gpt-5-",                "sota"),

    # ── OpenAI mid-tier ──────────────────────────────────────────────────────
    (r"^gpt-4\.1\b",            "mid"),
    (r"^gpt-4\.1-",             "mid"),
    (r"^gpt-4-1\b",             "mid"),
    (r"^gpt-4-1-",              "mid"),

    # ── OpenAI legacy ────────────────────────────────────────────────────────
    (r"^gpt-4o",                "legacy"),
    (r"^gpt-4\b",               "legacy"),
    (r"^gpt-4-",                "legacy"),
    (r"^chatgpt-4o",            "legacy"),

    # ── Anthropic flagship ───────────────────────────────────────────────────
    (r"claude-opus",            "sota"),

    # ── Anthropic mid-tier ───────────────────────────────────────────────────
    (r"claude-sonnet",          "mid"),

    # ── Anthropic legacy ─────────────────────────────────────────────────────
    (r"claude-3\b",             "legacy"),
    (r"claude-3-",              "legacy"),
    (r"claude-2",               "legacy"),

    # ── Google flagship ──────────────────────────────────────────────────────
    (r"gemini-3-pro",           "sota"),
    (r"gemini-3\.1-pro",        "sota"),
    (r"gemini-2\.5-pro",        "sota"),
    (r"gemini-2-5-pro",         "sota"),

    # ── Google mid-tier ──────────────────────────────────────────────────────
    # These are checked AFTER flash-lite/flash-8b so bare flash = mid is safe.
    (r"gemini-3-flash\b",       "mid"),
    (r"gemini-3\.1-flash\b",    "mid"),
    (r"gemini-2\.5-flash\b",    "mid"),
    (r"gemini-2-5-flash\b",     "mid"),
    (r"gemini-flash",           "mid"),   # catch-all for remaining flash variants

    # ── Google legacy ────────────────────────────────────────────────────────
    (r"gemini-2\.0",            "legacy"),
    (r"gemini-2-0",             "legacy"),
    (r"gemini-1\.",             "legacy"),
    (r"gemini-1-",              "legacy"),
]

TIER_LABELS = {
    "sota":      "SOTA      (flagship/frontier)",
    "mid":       "MID       (strong mid-tier)",
    "cheap":     "CHEAP     (budget/fast)",
    "reasoning": "REASONING (chain-of-thought)",
    "legacy":    "LEGACY    (older generation)",
}

# Display order for tiers in reports
TIER_ORDER = ["sota", "mid", "cheap", "reasoning", "legacy"]


def classify_tier(model_id: str) -> str:
    """Return the tier for a model ID. Falls back to 'mid' if no pattern matches."""
    lower = model_id.lower()
    for pattern, tier in TIER_PATTERNS:
        if re.search(pattern, lower):
            return tier
    return "mid"  # conservative default — treat unknown as mid, not sota or cheap


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
            "tier": classify_tier(model_id),
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
                "tier": classify_tier(model_id),
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
    known = [
        {"id": "claude-opus-4-6", "provider": "anthropic", "display_name": "Claude Opus 4.6", "created": "2025-12-01"},
        {"id": "claude-sonnet-4-6", "provider": "anthropic", "display_name": "Claude Sonnet 4.6", "created": "2025-12-01"},
        {"id": "claude-sonnet-4-5-20241022", "provider": "anthropic", "display_name": "Claude Sonnet 4.5", "created": "2025-10-01"},
        {"id": "claude-haiku-4-5-20251001", "provider": "anthropic", "display_name": "Claude Haiku 4.5", "created": "2025-10-01"},
    ]
    for m in known:
        m["tier"] = classify_tier(m["id"])
    return known


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
            "tier": classify_tier(model_id),
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


# ── Tier Grouping Helpers ────────────────────────────────────────────────────


def group_by_tier(all_models: list[dict]) -> dict[str, list[dict]]:
    """Group a flat list of model dicts by their tier field."""
    groups: dict[str, list[dict]] = {t: [] for t in TIER_ORDER}
    for m in all_models:
        tier = m.get("tier", "mid")
        if tier not in groups:
            tier = "mid"
        groups[tier].append(m)
    return groups


def collect_all_models(results: dict) -> list[dict]:
    """Flatten all provider results into a single list (skip errors/None)."""
    all_models = []
    for prov_id in PROVIDERS:
        models = results.get(prov_id)
        if models and not isinstance(models, str):
            all_models.extend(models)
    return all_models


def newest_model_in_tier(models: list[dict]) -> str | None:
    """Return the ID of the model with the most recent 'created' date."""
    dated = [m for m in models if m.get("created") and m["created"] != "unknown"]
    if not dated:
        return models[0]["id"] if models else None
    return max(dated, key=lambda m: m["created"])["id"]


# ── Output Formatting ───────────────────────────────────────────────────────


def format_text_report(results: dict, registry_models: set[str] | None = None) -> str:
    """Human-readable text report, models grouped by tier within each provider section."""
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

    # Models per provider, grouped by tier
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

        # Group by tier
        tier_groups: dict[str, list[dict]] = {t: [] for t in TIER_ORDER}
        for m in models:
            t = m.get("tier", "mid")
            tier_groups.setdefault(t, []).append(m)

        for tier in TIER_ORDER:
            tier_models = tier_groups.get(tier, [])
            if not tier_models:
                continue
            lines.append(f"  [{tier.upper()}]")
            for m in tier_models:
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

                lines.append(f"    {model_id}{extra}{in_registry}")

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


def format_summary_report(results: dict, registry_models: set[str] | None = None) -> str:
    """Quick-glance tier summary for /improve-eval.

    Shows: count per tier, which tiers have untested models, newest model per tier.
    """
    all_models = collect_all_models(results)
    if not all_models:
        return "No models discovered (check API keys)."

    groups = group_by_tier(all_models)

    lines = []
    lines.append("=" * 60)
    lines.append("  Model Tier Summary")
    lines.append(f"  {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"  {len(all_models)} total models across {sum(1 for v in results.values() if v and not isinstance(v, str))} providers")
    lines.append("=" * 60)
    lines.append("")

    for tier in TIER_ORDER:
        tier_models = groups.get(tier, [])
        if not tier_models:
            continue

        label = TIER_LABELS[tier]
        newest = newest_model_in_tier(tier_models)

        # Find untested models in this tier
        untested: list[str] = []
        if registry_models is not None:
            for m in tier_models:
                if not _matches_registry(m["id"], m.get("display_name", ""), registry_models):
                    untested.append(m["id"])

        lines.append(f"  {label}")
        lines.append(f"    Count   : {len(tier_models)}")
        if newest:
            lines.append(f"    Newest  : {newest}")
        if registry_models is not None:
            if untested:
                lines.append(f"    Untested: {len(untested)} model(s) — {', '.join(untested)}")
            else:
                lines.append(f"    Untested: none")
        lines.append("")

    # Untested alert block (only if registry loaded)
    if registry_models is not None:
        all_untested = [
            m for m in all_models
            if not _matches_registry(m["id"], m.get("display_name", ""), registry_models)
        ]
        if all_untested:
            lines.append(f"  ** {len(all_untested)} untested model(s) found — consider running /improve-eval **")
        else:
            lines.append("  All discovered models are covered by existing evals.")

    return "\n".join(lines)


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
    parser.add_argument("--summary", action="store_true", help="Quick-glance tier summary (for /improve-eval)")
    args = parser.parse_args()

    results = discover_models()

    # Load registry for comparison if requested
    registry_models = None
    if args.check_new or args.summary:
        registry_path = Path(__file__).parent.parent / "docs" / "evals" / "registry.yaml"
        registry_models = load_registry_models(registry_path)
        if registry_models:
            print(f"\nRegistry contains {len(registry_models)} tested models: {', '.join(sorted(registry_models))}", file=sys.stderr)

    if args.summary:
        output = format_summary_report(results, registry_models)
    elif args.yaml or args.cache:
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
