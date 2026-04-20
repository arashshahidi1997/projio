"""MCP tools: Quarto-powered executable reports.

**Phase 1** — scaffolding + render:

- :func:`report_init` — scaffold ``docs/deliverables/reports/<name>/report.qmd``
  with frontmatter preamble filled from ``questio_status``, recent ``result``
  notes, and ``pipeio_flow_status``.
- :func:`report_build` — preflight-validate the report, resolve the project's
  ``quarto`` binary per :mod:`projio.mcp.pipeio`'s runner chain, invoke
  ``quarto render`` inside the compute env, and return the build path + log.

Design spec: ``docs/specs/quarto-reports.md``.

Phase 2 (deferred): ``report_list``, ``report_status``, ``report_validate``,
``report_refresh_import``, ``report_freeze_import``.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .common import JsonDict, get_project_root, json_dict


# --- Templates -------------------------------------------------------------

TEMPLATES = ("progress", "update", "milestone")

# In-process cache for `quarto --version` probe (Section 12a).
_VERSION_CACHE: dict[tuple[str, ...], tuple[str, str | None]] = {}


# --- Parsing helpers -------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_CITE_RE = re.compile(r"@[A-Za-z0-9_:.\-]+")
_EMBED_RE = re.compile(
    r"\{\{<\s*embed\s+([^\s#]+)#([A-Za-z0-9_\-:.]+)(?:\s+[^>]*)?\s*>\}\}"
)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_LABEL_IN_SOURCE_RE = re.compile(r"^\s*#\|\s*label:\s*([A-Za-z0-9_\-:.]+)\s*$", re.MULTILINE)


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter_dict, body) from a .qmd/.md string.

    Missing frontmatter yields ``({}, text)``.  Malformed frontmatter yields
    ``({}, text)`` rather than raising — validation layers report on the
    structural problem.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        data = yaml.safe_load(match.group(1)) or {}
        if not isinstance(data, dict):
            return {}, text
    except yaml.YAMLError:
        return {}, text
    return data, text[match.end():]


def _find_report(root: Path, name: str) -> tuple[Path, Path] | None:
    """Locate a report's directory and .qmd source.

    Preferred layout: ``docs/deliverables/reports/<name>/report.qmd`` (the
    subdirectory gives ``_freeze/`` and ``_files/`` a home).  Flat single-file
    reports (``docs/deliverables/reports/<name>.qmd``) are also honored per
    §3 of the spec but remain discouraged — no ``build/`` subdirectory is
    created for them.
    """
    base = root / "docs" / "deliverables" / "reports"
    subdir = base / name / "report.qmd"
    if subdir.is_file():
        return subdir.parent, subdir
    flat = base / f"{name}.qmd"
    if flat.is_file():
        return base, flat
    return None


# --- Quarto runner resolution (Section 8) ----------------------------------


def _resolve_quarto_cmd(env_override: str = "") -> list[str]:
    """Resolve the ``quarto`` command per §8 of the spec.

    Chain:
    1. ``env_override`` or ``code.envs.report`` → ``<runner> run [-e <env>] quarto``
    2. ``code.envs.default`` → same
    3. ``quarto`` on PATH → bare invocation
    4. Empty list → "not found" (caller surfaces the install hint).
    """
    from .pipeio import _resolve_runner, _run_cmd

    runner = _resolve_runner()

    # Env-wrapped paths.
    env_name = env_override or _resolve_report_env_name()
    if not env_name:
        env_name = _resolve_default_env_from_config()

    if env_name:
        return _run_cmd(env_name, "quarto")

    # On PATH.
    import shutil
    binary = shutil.which("quarto")
    if binary:
        return [binary]

    # Not found. Let the caller surface the error.
    _ = runner  # silence unused
    return []


def _resolve_report_env_name() -> str | None:
    """Return ``code.envs.report`` from project config, or None."""
    try:
        from projio.config import load_effective_config
        root = get_project_root()
        cfg = load_effective_config(root)
        envs = (cfg.get("code", {}) or {}).get("envs", {}) or {}
        return envs.get("report") or None
    except Exception:
        return None


def _resolve_default_env_from_config() -> str | None:
    """Return ``code.envs.default`` from project config, or None."""
    try:
        from projio.config import load_effective_config
        root = get_project_root()
        cfg = load_effective_config(root)
        envs = (cfg.get("code", {}) or {}).get("envs", {}) or {}
        return envs.get("default") or None
    except Exception:
        return None


# --- Quarto config (.projio/render/quarto.yml) -----------------------------


DEFAULT_MIN_VERSION = "1.5"


def _load_quarto_config(root: Path) -> dict[str, Any]:
    """Load ``.projio/render/quarto.yml`` with defaults."""
    path = root / ".projio" / "render" / "quarto.yml"
    data: dict[str, Any] = {}
    if path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                data = loaded
        except yaml.YAMLError:
            data = {}
    return {
        "min_version": str(data.get("min_version") or DEFAULT_MIN_VERSION),
    }


# --- Version probe (Section 12a) -------------------------------------------


_VERSION_SPLIT_RE = re.compile(r"[.\-+]")


def _parse_version(raw: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of ints for comparison.

    Handles the common ``1.5.55`` style.  Non-numeric trailing chunks are
    ignored; a parse failure returns ``(0,)``.
    """
    raw = raw.strip().split()[0] if raw else ""
    parts: list[int] = []
    for piece in _VERSION_SPLIT_RE.split(raw):
        if not piece:
            break
        try:
            parts.append(int(piece))
        except ValueError:
            break
    return tuple(parts) if parts else (0,)


def _probe_quarto_version(cmd: list[str]) -> tuple[str, str | None]:
    """Return (version_string, error) from ``<cmd> --version``.

    Cached in-process by the command tuple so repeated builds in one MCP
    session don't re-shell out.  A non-zero exit or missing binary yields an
    empty version string and a user-facing error message.
    """
    key = tuple(cmd)
    if key in _VERSION_CACHE:
        return _VERSION_CACHE[key]
    try:
        proc = subprocess.run(
            cmd + ["--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        result = ("", "quarto binary not found")
        _VERSION_CACHE[key] = result
        return result
    except subprocess.TimeoutExpired:
        result = ("", "quarto --version timed out after 10s")
        _VERSION_CACHE[key] = result
        return result
    if proc.returncode != 0:
        result = ("", f"quarto --version failed: {proc.stderr.strip() or proc.stdout.strip()}")
        _VERSION_CACHE[key] = result
        return result
    version = (proc.stdout or proc.stderr).strip().splitlines()[0] if proc.stdout or proc.stderr else ""
    _VERSION_CACHE[key] = (version, None)
    return version, None


def _check_min_version(cmd: list[str], min_version: str) -> str | None:
    """Return an actionable error string if quarto is missing or too old."""
    version, err = _probe_quarto_version(cmd)
    if err:
        return (
            f"{err}.  Install quarto ≥ {min_version}: "
            "https://quarto.org/docs/get-started/"
        )
    if _parse_version(version) < _parse_version(min_version):
        return (
            f"quarto ≥ {min_version} required; found {version}.\n"
            "Install: https://quarto.org/docs/get-started/"
        )
    return None


# --- Preflight validation (Section 5c) -------------------------------------


@dataclass
class _PreflightResult:
    embeds: list[dict[str, Any]]
    images: list[dict[str, Any]]
    bibliography: dict[str, Any] | None
    errors: list[str]


def _validate_notebook_embed(nb_path: Path, label: str) -> str | None:
    """Return an error string if the embed target is invalid, else None."""
    if not nb_path.is_file():
        return f"embed: notebook not found: {nb_path}"
    if nb_path.suffix != ".ipynb":
        return f"embed: {nb_path.name} is not a .ipynb (Quarto embed requires .ipynb)"
    try:
        raw = nb_path.read_text(encoding="utf-8")
        doc = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        return f"embed: cannot parse {nb_path.name}: {exc}"

    cells = doc.get("cells") or []
    executed = False
    label_matched = False
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source")
        if isinstance(source, list):
            src_text = "".join(source)
        else:
            src_text = source or ""
        # Execution check: at least one code cell has an execution_count
        if cell.get("execution_count") is not None:
            executed = True
        # Label check: `#| label: <label>` in source
        if any(m.group(1) == label for m in _LABEL_IN_SOURCE_RE.finditer(src_text)):
            label_matched = True
    if not executed:
        return (
            f"embed: {nb_path.name} has no executed cells — "
            "run pipeio_nb_exec first"
        )
    if not label_matched:
        return f"embed: label '{label}' not found in {nb_path.name}"
    return None


def _preflight_report(qmd_path: Path, frontmatter: dict[str, Any], body: str) -> _PreflightResult:
    """Parse embed shortcodes + image refs + bibliography; validate each."""
    errors: list[str] = []
    embeds: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []
    bib_info: dict[str, Any] | None = None

    # Embeds
    for match in _EMBED_RE.finditer(body):
        rel = match.group(1)
        label = match.group(2)
        target = (qmd_path.parent / rel).resolve()
        err = _validate_notebook_embed(target, label)
        entry = {
            "path": str(target),
            "label": label,
            "ok": err is None,
        }
        if err:
            entry["error"] = err
            errors.append(err)
        embeds.append(entry)

    # Image refs — restrict validation to local relative paths; skip URLs.
    for match in _IMAGE_RE.finditer(body):
        href = match.group(1).strip().split()[0]  # strip title="..."
        if not href or href.startswith(("http://", "https://", "data:")):
            continue
        if href.startswith("/"):
            # Absolute within project: resolve from project root if we can
            target = qmd_path.parent / href.lstrip("/")
        else:
            target = (qmd_path.parent / href).resolve()
        exists = target.is_file()
        entry = {"path": str(target), "ok": exists}
        if not exists:
            msg = f"image: file not found: {href}"
            entry["error"] = msg
            errors.append(msg)
        images.append(entry)

    # Bibliography — only required when the body contains at least one citation.
    # A report with no @citekey references builds fine without a bib file.
    bib = frontmatter.get("bibliography")
    if bib:
        target = (qmd_path.parent / str(bib)).resolve()
        exists = target.is_file()
        bib_info = {"path": str(target), "ok": exists}
        if not exists:
            if _CITE_RE.search(body):
                msg = f"bibliography: file not found: {bib}"
                bib_info["error"] = msg
                errors.append(msg)
            else:
                bib_info["ok"] = True
                bib_info["note"] = "no citations in body; bibliography not required"

    return _PreflightResult(embeds=embeds, images=images, bibliography=bib_info, errors=errors)


# --- Preamble collection for report_init -----------------------------------


def _collect_preamble(root: Path) -> dict[str, Any]:
    """Gather questio + result-notes + flow state for the init preamble.

    All calls are best-effort — missing subsystems yield empty lists rather
    than raising, because report_init should be usable in projects that
    haven't adopted questio/notio/pipeio yet.
    """
    questions: list[str] = []
    results: list[str] = []
    source_flows: list[str] = []

    # questio_status -> question IDs
    try:
        from .questio import questio_status
        status = questio_status()
        if isinstance(status, dict) and "questions" in status:
            raw = status.get("questions") or []
            if isinstance(raw, list):
                for q in raw:
                    qid = q.get("id") if isinstance(q, dict) else None
                    if qid:
                        questions.append(str(qid))
            elif isinstance(raw, dict):
                questions.extend(str(k) for k in raw.keys())
    except Exception:
        pass

    # result notes — scan filesystem directly so this works without notio installed
    result_dir = root / "docs" / "log" / "result"
    if result_dir.is_dir():
        for p in sorted(result_dir.glob("result-*.md"), reverse=True)[:5]:
            results.append(p.stem)

    # flows — scan .projio/pipeio/registry.yml / .pipeio/registry.yml
    for rel in (".projio/pipeio/registry.yml", ".pipeio/registry.yml"):
        reg_path = root / rel
        if reg_path.is_file():
            try:
                reg = yaml.safe_load(reg_path.read_text(encoding="utf-8")) or {}
                flows = reg.get("flows") or {}
                if isinstance(flows, dict):
                    source_flows.extend(sorted(flows.keys()))
            except yaml.YAMLError:
                pass
            break

    return {
        "questions": questions,
        "results": results,
        "source_flows": source_flows,
    }


# --- report.qmd scaffold ---------------------------------------------------


_BODY_BY_TEMPLATE: dict[str, str] = {
    "progress": (
        "# Overview\n\n"
        "Summarize the week's activity: what shipped, what's in flight, what's blocked.\n\n"
        "# Results\n\n"
        "<!-- Embed labeled notebook cells:\n"
        "{{< embed ../../../code/pipelines/<flow>/notebooks/<nb>.ipynb#fig-label >}}\n"
        "-->\n\n"
        "# Next steps\n\n"
        "- \n"
    ),
    "update": (
        "# Status update\n\n"
        "One-paragraph summary for supervisor / external audience.\n\n"
        "# Details\n\n"
        "<!-- Embed figures and discuss specific findings. -->\n"
    ),
    "milestone": (
        "# Milestone\n\n"
        "Name the milestone and the question(s) it advances.\n\n"
        "# Evidence\n\n"
        "<!-- Cite result notes with @result-<id> and embed key figures. -->\n\n"
        "# Decision / next milestone\n\n"
        "- \n"
    ),
}


def _default_title(name: str, template: str) -> str:
    pretty = name.replace("_", " ").replace("-", " ").strip().title() or "Report"
    if template == "progress":
        return f"Progress Report — {pretty}"
    if template == "milestone":
        return f"Milestone — {pretty}"
    return pretty


def _render_frontmatter(
    *,
    title: str,
    template: str,
    questions: list[str],
    results: list[str],
    source_flows: list[str],
    bibliography: str,
    csl: str,
) -> str:
    """Emit the .qmd frontmatter block."""
    fm: dict[str, Any] = {
        "title": title,
        "date": date.today().isoformat(),
        "format": {
            "html": {
                "toc": True,
                "code-fold": True,
                "theme": "cosmo",
            },
        },
        "bibliography": bibliography,
        "csl": csl,
        "type": "report",
        "template": template,
        "questions": questions,
        "results": results,
        "source_flows": source_flows,
    }
    body = yaml.dump(fm, sort_keys=False, default_flow_style=False)
    return f"---\n{body}---\n\n"


# --- MCP tools -------------------------------------------------------------


def report_init(name: str, template: str = "progress") -> JsonDict:
    """Scaffold a new report under ``docs/deliverables/reports/<name>/``.

    Args:
        name: Report name; becomes the subdirectory name.
        template: One of ``progress``, ``update``, ``milestone``.
    """
    if template not in TEMPLATES:
        return json_dict({
            "error": f"unknown template '{template}'; choose from {list(TEMPLATES)}",
        })

    root = get_project_root()
    base = root / "docs" / "deliverables" / "reports" / name
    report_path = base / "report.qmd"
    if report_path.is_file():
        return json_dict({
            "error": f"report already exists: {report_path.relative_to(root)}",
            "path": str(report_path.relative_to(root)),
        })

    preamble = _collect_preamble(root)
    title = _default_title(name, template)

    # Bibliography/CSL paths relative to docs/deliverables/reports/<name>/
    rel_prefix = "../../../../"
    bib_path = f"{rel_prefix}.projio/render/compiled.bib"
    csl_path = f"{rel_prefix}.projio/render/csl/apa.csl"

    content = _render_frontmatter(
        title=title,
        template=template,
        questions=preamble["questions"],
        results=preamble["results"],
        source_flows=preamble["source_flows"],
        bibliography=bib_path,
        csl=csl_path,
    ) + _BODY_BY_TEMPLATE[template]

    base.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")

    return json_dict({
        "name": name,
        "template": template,
        "path": str(report_path.relative_to(root)),
        "title": title,
        "questions": preamble["questions"],
        "results": preamble["results"],
        "source_flows": preamble["source_flows"],
    })


def report_build(name: str, format: str = "html") -> JsonDict:
    """Render ``docs/deliverables/reports/<name>/report.qmd`` via quarto.

    Execution chain:
    1. Locate the report and parse frontmatter
    2. Preflight: embed targets, image refs, bibliography
    3. Resolve quarto via ``code.envs.report`` / ``code.envs.default`` / PATH
    4. Verify the runtime quarto is ≥ ``min_version`` (from quarto.yml)
    5. ``quarto render report.qmd --to <format>`` inside the compute env
    """
    root = get_project_root()
    located = _find_report(root, name)
    if located is None:
        return json_dict({
            "error": (
                f"report not found: docs/deliverables/reports/{name}/report.qmd"
            ),
        })
    report_dir, qmd_path = located

    text = qmd_path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)

    preflight = _preflight_report(qmd_path, frontmatter, body)
    if preflight.errors:
        return json_dict({
            "error": "preflight validation failed",
            "report": str(qmd_path.relative_to(root)),
            "preflight_errors": preflight.errors,
            "embeds": preflight.embeds,
            "images": preflight.images,
            "bibliography": preflight.bibliography,
        })

    cmd = _resolve_quarto_cmd()
    if not cmd:
        return json_dict({
            "error": (
                "quarto not found — install with your package manager or download from "
                "https://quarto.org/docs/get-started/ , or add it to the project env "
                "and set code.envs.report"
            ),
        })

    quarto_cfg = _load_quarto_config(root)
    version_err = _check_min_version(cmd, quarto_cfg["min_version"])
    if version_err:
        return json_dict({"error": version_err})

    # Invoke quarto render
    render_cmd = cmd + ["render", str(qmd_path), "--to", format]
    try:
        proc = subprocess.run(
            render_cmd,
            capture_output=True,
            text=True,
            cwd=str(report_dir),
        )
    except FileNotFoundError as exc:
        return json_dict({"error": f"failed to launch quarto: {exc}"})

    output_path = qmd_path.with_suffix(_output_suffix(format))
    build: dict[str, Any] = {
        "command": render_cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    if proc.returncode != 0:
        build["error"] = (
            f"quarto render exited {proc.returncode} — see stderr for details"
        )
        return json_dict(build)

    if output_path.is_file():
        build["output"] = str(output_path.relative_to(root))
        build["output_abs"] = str(output_path)

    return json_dict(build)


def _output_suffix(format: str) -> str:
    """Map a Quarto ``--to`` target to the expected output extension."""
    mapping = {
        "html": ".html",
        "pdf": ".pdf",
        "docx": ".docx",
        "revealjs": ".html",
        "typst": ".pdf",
    }
    return mapping.get(format, f".{format}")
