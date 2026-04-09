"""Project-local style-pack discovery, generation, and persistence."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Literal

import yaml

from cine_forge.roles.runtime import RoleCatalog, RoleRuntimeError
from cine_forge.schemas import StylePack, StylePackSlot

StylePackProvider = Literal["openai", "anthropic", "google"]

_RESEARCH_COMMAND = "/Users/cam/miniconda3/bin/deep-research"
_MANIFEST_MARKER = "<<<STYLE_PACK_MANIFEST_YAML"
_STYLE_MARKER = "<<<STYLE_PACK_STYLE_MD"
_SECTION_END = ">>>"
_REPORT_FILE_PATTERN = re.compile(r"(?:ai-.+-deep-research|.+-report|ai-agent-\d+)\.md$")
_PROVIDER_OPTIONS: tuple[dict[str, Any], ...] = (
    {"provider": "openai", "display_name": "OpenAI", "recommended": True},
    {"provider": "anthropic", "display_name": "Anthropic", "recommended": False},
    {"provider": "google", "display_name": "Google", "recommended": False},
)
_PROVIDER_DISPLAY_NAMES = {
    option["provider"]: option["display_name"] for option in _PROVIDER_OPTIONS
}


class StylePackServiceError(RuntimeError):
    """Structured failure from style-pack generation or persistence."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        hint: str | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.status_code = status_code


class StylePackService:
    """Owns project-local style-pack lifecycle helpers."""

    def __init__(
        self,
        *,
        base_catalog: RoleCatalog | None = None,
        deep_research_command: str = _RESEARCH_COMMAND,
    ) -> None:
        self.base_catalog = base_catalog or RoleCatalog()
        self.base_catalog.load_definitions()
        self.deep_research_command = deep_research_command

    def build_project_catalog(self, project_path: Path) -> RoleCatalog:
        catalog = RoleCatalog(
            root=self.base_catalog.root,
            style_pack_roots=[project_path / "style_packs"],
        )
        catalog.load_definitions()
        return catalog

    def list_library(
        self,
        *,
        project_path: Path,
        style_pack_selections: dict[str, str],
    ) -> dict[str, Any]:
        catalog = self.build_project_catalog(project_path)
        generation_role_ids = {role["role_id"] for role in self.list_generation_roles()}
        roles_payload: list[dict[str, Any]] = []

        roles = sorted(
            catalog.list_roles().values(),
            key=lambda item: item.display_name.lower(),
        )
        for role in roles:
            if role.style_pack_slot == StylePackSlot.FORBIDDEN:
                continue
            packs_payload: list[dict[str, Any]] = []
            for pack in catalog.list_style_packs(role.role_id):
                source = "built_in"
                if self.project_manifest_path(
                    project_path,
                    role.role_id,
                    pack.style_pack_id,
                ).exists():
                    source = "project"
                packs_payload.append(
                    {
                        "role_id": role.role_id,
                        "style_pack_id": pack.style_pack_id,
                        "display_name": pack.display_name,
                        "summary": pack.summary,
                        "source": source,
                    }
                )

            roles_payload.append(
                {
                    "role_id": role.role_id,
                    "display_name": role.display_name,
                    "can_generate": role.role_id in generation_role_ids,
                    "selected_style_pack_id": self._effective_selection(
                        catalog=catalog,
                        role_id=role.role_id,
                        selected_style_pack_id=style_pack_selections.get(role.role_id),
                    ),
                    "style_packs": packs_payload,
                }
            )

        return {
            "roles": roles_payload,
            "providers": list(_PROVIDER_OPTIONS),
        }

    def list_generation_roles(self) -> list[dict[str, str]]:
        roles = []
        for role in self.base_catalog.list_roles().values():
            if role.style_pack_slot != StylePackSlot.ACCEPTS:
                continue
            if not self.prompt_template_path(role.role_id).exists():
                continue
            roles.append({"role_id": role.role_id, "display_name": role.display_name})
        return sorted(roles, key=lambda item: item["display_name"].lower())

    def build_manual_prompt(
        self,
        *,
        role_id: str,
        subject: str,
    ) -> dict[str, str]:
        role = self._require_generation_role(role_id)
        return {
            "role_id": role_id,
            "role_display_name": role.display_name,
            "subject": subject,
            "prompt": self._build_research_prompt(role_id=role_id, subject=subject),
        }

    def generate_draft(
        self,
        *,
        project_path: Path,
        role_id: str,
        subject: str,
        provider: StylePackProvider,
    ) -> dict[str, Any]:
        role = self._require_generation_role(role_id)
        prompt = self._build_research_prompt(role_id=role_id, subject=subject)
        research_result = self._run_deep_research(
            prompt=prompt,
            role_id=role_id,
            provider=provider,
        )
        parsed = self._parse_report(
            report_text=research_result["report_text"],
            role_id=role_id,
            subject=subject,
        )
        return {
            "generation_mode": "deep_research",
            "role_id": role_id,
            "role_display_name": role.display_name,
            "provider": provider,
            "subject": subject,
            "research_cost": research_result["research_cost"],
            **parsed,
        }

    def import_draft(
        self,
        *,
        role_id: str,
        subject: str,
        raw_output: str,
    ) -> dict[str, Any]:
        role = self._require_generation_role(role_id)
        parsed = self._parse_report(report_text=raw_output, role_id=role_id, subject=subject)
        return {
            "generation_mode": "manual_import",
            "role_id": role_id,
            "role_display_name": role.display_name,
            "provider": None,
            "subject": subject,
            "research_cost": None,
            **parsed,
        }

    def save_draft(
        self,
        *,
        project_path: Path,
        role_id: str,
        style_pack_id: str,
        display_name: str,
        summary: str,
        prompt_injection: str,
        style_markdown: str,
        additional_files: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        role = self._require_style_pack_role(role_id)
        normalized_pack_id = self._slugify(style_pack_id)
        if not normalized_pack_id:
            raise StylePackServiceError(
                code="style_pack_invalid_id",
                message="Style pack id must contain at least one letter or number.",
                hint="Use a short kebab-case id like 'tarantino-dialogue'.",
                status_code=422,
            )

        pack_dir = project_path / "style_packs" / role_id / normalized_pack_id
        if pack_dir.exists():
            raise StylePackServiceError(
                code="style_pack_exists",
                message=(
                    f"Style pack '{normalized_pack_id}' already exists for "
                    f"{role.display_name}."
                ),
                hint="Choose a different style pack id or edit the existing pack manually.",
                status_code=409,
            )

        materialized_files = self._materialize_additional_files(additional_files or [])
        manifest_payload = {
            "style_pack_id": normalized_pack_id,
            "role_id": role_id,
            "display_name": display_name.strip(),
            "summary": summary.strip(),
            "prompt_injection": prompt_injection.strip(),
            "files": [
                {
                    "kind": "description",
                    "path": "style.md",
                    "caption": f"{role.display_name} style profile.",
                },
                *[
                    {
                        "kind": item["kind"],
                        "path": item["path"],
                        "caption": item["caption"],
                    }
                    for item in materialized_files
                ],
            ],
        }
        style_pack = StylePack.model_validate(manifest_payload)

        pack_dir.mkdir(parents=True, exist_ok=False)
        (pack_dir / "style.md").write_text(style_markdown.strip() + "\n", encoding="utf-8")
        for item in materialized_files:
            (pack_dir / item["path"]).write_text(item["content"].strip() + "\n", encoding="utf-8")
        (pack_dir / "manifest.yaml").write_text(
            yaml.safe_dump(style_pack.model_dump(mode="json"), sort_keys=False),
            encoding="utf-8",
        )
        return {
            "role_id": role_id,
            "style_pack_id": style_pack.style_pack_id,
            "display_name": style_pack.display_name,
            "summary": style_pack.summary,
            "source": "project",
        }

    def project_manifest_path(self, project_path: Path, role_id: str, style_pack_id: str) -> Path:
        return project_path / "style_packs" / role_id / style_pack_id / "manifest.yaml"

    def prompt_template_path(self, role_id: str) -> Path:
        return self.base_catalog.root / role_id / "style_pack_prompt.md"

    def _effective_selection(
        self,
        *,
        catalog: RoleCatalog,
        role_id: str,
        selected_style_pack_id: str | None,
    ) -> str | None:
        if selected_style_pack_id:
            try:
                catalog.load_style_pack(role_id, selected_style_pack_id)
                return selected_style_pack_id
            except RoleRuntimeError:
                pass

        packs = catalog.list_style_packs(role_id)
        if not packs:
            return None
        for pack in packs:
            if pack.style_pack_id == "generic":
                return "generic"
        return packs[0].style_pack_id

    def _require_style_pack_role(self, role_id: str):
        role = self.base_catalog.get_role(role_id)
        if role.style_pack_slot != StylePackSlot.ACCEPTS:
            raise StylePackServiceError(
                code="style_pack_role_forbidden",
                message=f"Role '{role.display_name}' does not accept style packs.",
                status_code=422,
            )
        return role

    def _require_generation_role(self, role_id: str):
        role = self._require_style_pack_role(role_id)
        if not self.prompt_template_path(role_id).exists():
            raise StylePackServiceError(
                code="style_pack_generation_unavailable",
                message=(
                    f"Role '{role.display_name}' does not have a style-pack creation "
                    "template."
                ),
                hint=(
                    "Choose one of the creative roles with an existing style-pack "
                    "prompt template."
                ),
                status_code=422,
            )
        return role

    def _build_research_prompt(self, *, role_id: str, subject: str) -> str:
        template_path = self.prompt_template_path(role_id)
        prompt_template = template_path.read_text(encoding="utf-8")
        rendered = prompt_template.replace("{{ user_input }}", subject.strip())
        rendered = rendered.replace("{{ style_pack_id }}", "choose-a-short-kebab-case-id")
        rendered = rendered.replace(
            "{{ display_name }}",
            "Choose a clear human-readable display name",
        )
        rendered = rendered.replace("{{ short_summary }}", "Write a one-sentence summary")
        return (
            f"{rendered}\n\n"
            "## Output Contract\n"
            "Return exactly two sections in this order.\n\n"
            f"{_MANIFEST_MARKER}\n"
            "style_pack_id: <short kebab-case id>\n"
            f"role_id: {role_id}\n"
            "display_name: <human-readable name>\n"
            "summary: <one-sentence summary>\n"
            "prompt_injection: |\n"
            "  <3-5 sentence creative directive>\n"
            "files:\n"
            "  - kind: description\n"
            "    path: style.md\n"
            "    caption: Core style profile.\n"
            "  # Optional when you want to preserve supporting notes or cited sources:\n"
            "  # - kind: notes\n"
            "  #   path: research-notes.md\n"
            "  #   caption: Preserved research notes and cited sources.\n"
            f"{_SECTION_END}\n\n"
            f"{_STYLE_MARKER}\n"
            "# Style Title\n"
            "<The full style.md content in markdown>\n"
            f"{_SECTION_END}\n\n"
            "Do not add any other code fences around these sections."
        )

    def _run_deep_research(
        self,
        *,
        prompt: str,
        role_id: str,
        provider: StylePackProvider,
    ) -> dict[str, Any]:
        command_path = Path(self.deep_research_command)
        if not command_path.exists():
            raise StylePackServiceError(
                code="deep_research_missing",
                message="The deep-research CLI is not installed in this environment.",
                hint=f"Expected executable at {self.deep_research_command}.",
                status_code=503,
            )

        topic = self._slugify(f"{role_id}-style-pack") or "style-pack"
        with tempfile.TemporaryDirectory(prefix="cineforge-style-pack-") as temp_dir:
            parent_dir = Path(temp_dir)
            project_dir = parent_dir / topic
            self._run_command(
                [
                    self.deep_research_command,
                    "init",
                    topic,
                    "--dir",
                    str(parent_dir),
                    "--agents",
                    "1",
                ],
                cwd=None,
            )
            research_prompt_path = project_dir / "research-prompt.md"
            self._write_research_prompt(research_prompt_path, prompt)
            run_result = self._run_command(
                [
                    self.deep_research_command,
                    "run",
                    "--provider",
                    provider,
                    "--mode",
                    "deep",
                    "--debug",
                ],
                cwd=project_dir,
            )
            report_path = self._resolve_report_path(project_dir=project_dir, provider=provider)
            report_text = report_path.read_text(encoding="utf-8")
            return {
                "report_text": report_text,
                "research_cost": self._extract_research_cost(
                    project_dir=project_dir,
                    provider=provider,
                    report_path=report_path,
                    run_stdout=run_result.stdout or "",
                ),
            }

    def _run_command(
        self,
        args: list[str],
        *,
        cwd: Path | None,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                args,
                cwd=str(cwd) if cwd is not None else None,
                capture_output=True,
                text=True,
                check=True,
                timeout=1800,
            )
        except FileNotFoundError as exc:
            raise StylePackServiceError(
                code="deep_research_missing",
                message="The deep-research CLI is not available.",
                hint=str(exc),
                status_code=503,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise StylePackServiceError(
                code="deep_research_timeout",
                message="Deep research took too long and was cancelled.",
                hint="Try again with a narrower subject or a different provider.",
                status_code=504,
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            stdout = (exc.stdout or "").strip()
            hint = stderr or stdout or None
            raise StylePackServiceError(
                code="deep_research_failed",
                message="Deep research generation failed.",
                hint=hint,
                status_code=502,
            ) from exc

    def _write_research_prompt(self, research_prompt_path: Path, prompt: str) -> None:
        template = research_prompt_path.read_text(encoding="utf-8")
        placeholder = "<!-- Paste your research prompt below this line -->"
        if placeholder in template:
            content = template.replace(placeholder, prompt)
        else:
            content = f"{template.rstrip()}\n\n{prompt}\n"
        research_prompt_path.write_text(content, encoding="utf-8")

    def _parse_report(self, *, report_text: str, role_id: str, subject: str) -> dict[str, Any]:
        manifest_text = self._extract_section(report_text, _MANIFEST_MARKER)
        style_markdown = self._extract_section(report_text, _STYLE_MARKER)

        if manifest_text is None:
            manifest_text = self._extract_yaml_code_block(report_text)
        if style_markdown is None:
            style_markdown = self._extract_markdown_code_block(report_text)

        if manifest_text is None or style_markdown is None:
            raise StylePackServiceError(
                code="style_pack_parse_failed",
                message="Could not parse the generated style-pack draft.",
                hint="The provider response did not include the required manifest/style sections.",
                status_code=502,
            )

        try:
            manifest_payload = yaml.safe_load(manifest_text)
        except yaml.YAMLError as exc:
            raise StylePackServiceError(
                code="style_pack_invalid_manifest",
                message="Generated manifest YAML could not be parsed.",
                hint=str(exc),
                status_code=502,
            ) from exc

        if not isinstance(manifest_payload, dict):
            raise StylePackServiceError(
                code="style_pack_invalid_manifest",
                message="Generated manifest was not a YAML mapping.",
                status_code=502,
            )

        manifest_role_id = str(manifest_payload.get("role_id") or role_id).strip()
        if manifest_role_id != role_id:
            raise StylePackServiceError(
                code="style_pack_role_mismatch",
                message=(
                    f"Generated manifest targeted role '{manifest_role_id}' instead of "
                    f"'{role_id}'."
                ),
                status_code=502,
            )

        display_name = str(manifest_payload.get("display_name") or subject).strip()
        summary = str(manifest_payload.get("summary") or "").strip()
        prompt_injection = str(manifest_payload.get("prompt_injection") or "").strip()
        style_pack_id = self._slugify(
            str(manifest_payload.get("style_pack_id") or display_name or subject)
        )

        if len(summary) < 8 or len(prompt_injection) < 8 or len(style_markdown.strip()) < 20:
            raise StylePackServiceError(
                code="style_pack_incomplete_draft",
                message="Generated style-pack draft was missing required creative content.",
                hint="Try again or edit the draft after generation.",
                status_code=502,
            )

        return {
            "style_pack_id": style_pack_id,
            "display_name": display_name,
            "summary": summary,
            "prompt_injection": prompt_injection,
            "style_markdown": style_markdown.strip(),
            "additional_files": self._build_additional_files(
                manifest_payload=manifest_payload,
                report_text=report_text,
            ),
        }

    def _materialize_additional_files(
        self,
        files: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        materialized: list[dict[str, Any]] = []
        seen_paths = {"style.md"}
        for file_payload in files:
            raw_content = str(file_payload.get("content") or "").strip()
            if not raw_content:
                continue
            path = self._normalize_support_file_path(str(file_payload.get("path") or ""))
            if path in seen_paths:
                raise StylePackServiceError(
                    code="style_pack_duplicate_file",
                    message=f"Style pack draft contains duplicate file path '{path}'.",
                    status_code=422,
                )
            seen_paths.add(path)
            materialized.append(
                {
                    "kind": str(file_payload.get("kind") or "notes"),
                    "path": path,
                    "caption": str(file_payload.get("caption") or "").strip() or None,
                    "content": raw_content,
                }
            )
        return materialized

    def _normalize_support_file_path(self, raw_path: str) -> str:
        candidate = Path(raw_path.strip())
        if raw_path.strip() == "" or candidate.is_absolute() or len(candidate.parts) != 1:
            raise StylePackServiceError(
                code="style_pack_invalid_file_path",
                message="Style pack support files must use a simple relative filename.",
                hint="Use names like 'research-notes.md' or 'sources.md'.",
                status_code=422,
            )
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "-", candidate.name).strip("-.").lower()
        if not safe_name:
            raise StylePackServiceError(
                code="style_pack_invalid_file_path",
                message="Style pack support file path is invalid.",
                hint="Use a filename with letters or numbers.",
                status_code=422,
            )
        return safe_name

    def _build_additional_files(
        self,
        *,
        manifest_payload: dict[str, Any],
        report_text: str,
    ) -> list[dict[str, str | None]]:
        files_payload = manifest_payload.get("files")
        notes_manifest_entry: dict[str, Any] | None = None
        if isinstance(files_payload, list):
            for item in files_payload:
                if (
                    isinstance(item, dict)
                    and str(item.get("kind") or "").strip() == "notes"
                ):
                    notes_manifest_entry = item
                    break

        research_notes = self._extract_research_notes(report_text)
        if not research_notes:
            return []

        return [
            {
                "kind": "notes",
                "path": self._normalize_support_file_path(
                    str(notes_manifest_entry.get("path") or "research-notes.md")
                    if notes_manifest_entry is not None
                    else "research-notes.md"
                ),
                "caption": (
                    str(notes_manifest_entry.get("caption") or "").strip()
                    if notes_manifest_entry is not None
                    else "Preserved research notes and cited sources."
                )
                or "Preserved research notes and cited sources.",
                "content": research_notes,
            }
        ]

    def _extract_research_notes(self, report_text: str) -> str:
        cleaned = self._strip_frontmatter(report_text)
        cleaned = re.sub(
            rf"{re.escape(_MANIFEST_MARKER)}\s*\n.*?(?:\n{re.escape(_SECTION_END)}|\Z)",
            "",
            cleaned,
            flags=re.DOTALL,
        )
        cleaned = re.sub(
            rf"{re.escape(_STYLE_MARKER)}\s*\n.*?(?:\n{re.escape(_SECTION_END)}|\Z)",
            "",
            cleaned,
            flags=re.DOTALL,
        )
        cleaned = re.sub(
            r"```(?:yaml|yml)\s*\n.*?```",
            "",
            cleaned,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cleaned = re.sub(
            r"```(?:markdown|md)\s*\n.*?```",
            "",
            cleaned,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return cleaned.strip()

    def _strip_frontmatter(self, text: str) -> str:
        return re.sub(r"\A---\s*\n.*?\n---\s*\n?", "", text, flags=re.DOTALL)

    def _resolve_report_path(self, *, project_dir: Path, provider: StylePackProvider) -> Path:
        filled_reports = self._list_filled_report_files(project_dir)
        preferred = project_dir / f"ai-{provider}-deep-research.md"
        if preferred in filled_reports:
            return preferred
        if len(filled_reports) == 1:
            return filled_reports[0]
        if filled_reports:
            return max(filled_reports, key=lambda path: path.stat().st_mtime)
        raise StylePackServiceError(
            code="deep_research_missing_output",
            message="Deep research completed without producing a report file.",
            hint="Check the deep-research CLI output and provider credentials.",
            status_code=502,
        )

    def _list_filled_report_files(self, project_dir: Path) -> list[Path]:
        reports: list[Path] = []
        for path in sorted(project_dir.iterdir()):
            if not path.is_file() or not _REPORT_FILE_PATTERN.fullmatch(path.name):
                continue
            if self._report_has_body(path):
                reports.append(path)
        return reports

    def _report_has_body(self, path: Path) -> bool:
        body = self._strip_frontmatter(path.read_text(encoding="utf-8")).strip()
        lines = [
            line for line in body.splitlines()
            if not line.strip().startswith("<!--") and line.strip() != "# Research Report"
        ]
        return any(line.strip() for line in lines)

    def _extract_research_cost(
        self,
        *,
        project_dir: Path,
        provider: StylePackProvider,
        report_path: Path,
        run_stdout: str,
    ) -> dict[str, Any] | None:
        report_text = report_path.read_text(encoding="utf-8")
        model = self._extract_frontmatter_value(report_text, "canonical-model-name") or provider
        request_id = self._extract_debug_request_id(project_dir=project_dir, provider=provider)

        debug_path = project_dir / "_debug-run.md"
        if debug_path.exists():
            debug_text = debug_path.read_text(encoding="utf-8")
            display_name = _PROVIDER_DISPLAY_NAMES[provider]
            pattern = re.compile(
                rf"## Response: {re.escape(display_name)} \((?P<model>[^)]+)\) \[[^\]]+\]\s+"
                rf"\*\*OK\*\* — .*?, (?P<tokens>[\d,]+) tokens, \$(?P<cost>[\d.]+), "
                rf"(?P<latency>[\d.]+)s",
                re.DOTALL,
            )
            match = pattern.search(debug_text)
            if match is not None:
                total_tokens = int(match.group("tokens").replace(",", ""))
                cost_value = float(match.group("cost"))
                return {
                    "model": match.group("model").strip(),
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": cost_value,
                    "latency_seconds": float(match.group("latency")),
                    "request_id": request_id,
                    "attribution": "deep_research_cli_estimate",
                    "note": (
                        "Cost is reported by the deep-research CLI. Deep-research mode uses "
                        "the upstream tool's estimate, not provider-billed exact pricing."
                    ),
                }

        stdout_pattern = re.compile(r"\$(?P<cost>[\d.]+)")
        cost_match = stdout_pattern.search(run_stdout)
        if cost_match is not None:
            return {
                "model": model,
                "total_tokens": 0,
                "estimated_cost_usd": float(cost_match.group("cost")),
                "latency_seconds": None,
                "request_id": request_id,
                "attribution": "deep_research_cli_estimate",
                "note": (
                    "Cost is reported by the deep-research CLI. Token counts were not "
                    "available from this run."
                ),
            }

        return {
            "model": model,
            "total_tokens": 0,
            "estimated_cost_usd": None,
            "latency_seconds": None,
            "request_id": request_id,
            "attribution": "provider_unavailable",
            "note": "This provider run did not expose cost metadata through the deep-research CLI.",
        }

    def _extract_frontmatter_value(self, text: str, key: str) -> str | None:
        match = re.match(r"\A---\s*\n(?P<frontmatter>.*?)\n---\s*\n?", text, flags=re.DOTALL)
        if match is None:
            return None
        payload = yaml.safe_load(match.group("frontmatter"))
        if not isinstance(payload, dict):
            return None
        value = payload.get(key)
        if value is None:
            return None
        return str(value).strip() or None

    def _extract_debug_request_id(
        self,
        *,
        project_dir: Path,
        provider: StylePackProvider,
    ) -> str | None:
        debug_json_path = project_dir / f"_debug-{provider}-dr.json"
        if not debug_json_path.exists():
            return None
        try:
            payload = json.loads(debug_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        request_id = payload.get("id")
        return str(request_id).strip() if request_id else None

    @staticmethod
    def _extract_section(text: str, marker: str) -> str | None:
        pattern = re.compile(
            rf"{re.escape(marker)}\s*\n(?P<body>.*?)(?:\n{re.escape(_SECTION_END)}|\Z)",
            re.DOTALL,
        )
        match = pattern.search(text)
        if match is None:
            return None
        return match.group("body").strip()

    @staticmethod
    def _extract_yaml_code_block(text: str) -> str | None:
        pattern = re.compile(r"```(?:yaml|yml)\s*\n(?P<body>.*?)```", re.DOTALL | re.IGNORECASE)
        for match in pattern.finditer(text):
            body = match.group("body").strip()
            if "style_pack_id:" in body and "role_id:" in body:
                return body
        return None

    @staticmethod
    def _extract_markdown_code_block(text: str) -> str | None:
        pattern = re.compile(r"```(?:markdown|md)\s*\n(?P<body>.*?)```", re.DOTALL | re.IGNORECASE)
        match = pattern.search(text)
        if match is None:
            return None
        return match.group("body").strip()

    @staticmethod
    def _slugify(value: str) -> str:
        slug = value.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")
