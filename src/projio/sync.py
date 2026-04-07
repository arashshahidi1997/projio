"""projio sync — auto-discover code libraries, sync filters, generate pandoc defaults."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


def _discover_code_libs(root: Path) -> list[dict[str, Any]]:
    """Scan code/lib/*/ for Python packages.

    Returns a list of dicts with keys: name, path, has_init.
    """
    lib_dir = root / "code" / "lib"
    if not lib_dir.is_dir():
        return []
    libs = []
    for child in sorted(lib_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        has_init = (child / "__init__.py").exists() or (child / "src").is_dir()
        libs.append({
            "name": child.name,
            "path": str(child.relative_to(root)),
            "has_init": has_init,
        })
    return libs


def _detect_project_utils(root: Path) -> str | None:
    """Check if code/utils/ exists and contains Python code."""
    utils_dir = root / "code" / "utils"
    if utils_dir.is_dir():
        return str(utils_dir.relative_to(root))
    return None


def _sync_codio_libraries(
    root: Path, libs: list[dict[str, Any]], *, dry_run: bool = False,
) -> list[dict[str, str]]:
    """Register discovered libraries in the codio catalog.

    Returns a list of actions taken (added, skipped, updated).
    """
    try:
        from codio import load_config, Registry
        from codio.models import LibraryCatalogEntry, ProjectProfileEntry
        from codio.skills.update import add_library
    except ImportError:
        return [{"action": "error", "name": "", "reason": "codio package not installed"}]

    try:
        config = load_config(root)
        registry = Registry(config=config)
    except Exception as exc:
        return [{"action": "error", "name": "", "reason": str(exc)}]

    actions = []
    existing = {lib.name for lib in registry.list()}

    for lib_info in libs:
        name = lib_info["name"]
        rel_path = lib_info["path"]

        if name in existing:
            # Check if role is already set; update if blank
            record = registry.get(name)
            if record is not None and not getattr(record, "role", ""):
                if dry_run:
                    actions.append({"action": "would_update", "name": name, "field": "role=core"})
                else:
                    cat = registry.catalog.get(name)
                    if cat is not None:
                        cat_dict = cat.model_dump()
                        cat_dict["role"] = "core"
                        updated = LibraryCatalogEntry(**cat_dict)
                        add_library(registry, updated)
                        actions.append({"action": "updated", "name": name, "field": "role=core"})
            else:
                actions.append({"action": "skipped", "name": name, "reason": "already registered"})
            continue

        if dry_run:
            actions.append({"action": "would_add", "name": name, "path": rel_path})
            continue

        catalog_entry = LibraryCatalogEntry(
            name=name,
            kind="internal",
            role="core",
            path=rel_path,
            language="python",
            summary=f"Project core library: {name}",
        )
        profile_entry = ProjectProfileEntry(
            name=name,
            priority="tier1",
            runtime_import="internal",
            status="active",
        )
        add_library(registry, catalog_entry, profile_entry)
        actions.append({"action": "added", "name": name, "path": rel_path})

    return actions


def _sync_project_utils_config(
    root: Path, utils_path: str | None, *, dry_run: bool = False,
) -> dict[str, Any]:
    """Ensure code.project_utils is set in .projio/config.yml if utils exist."""
    import yaml

    from projio.config import get_project_config_path

    config_path = get_project_config_path(root)
    if not config_path.exists():
        return {"action": "skipped", "reason": "no .projio/config.yml"}

    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    code_section = cfg.get("code", {}) or {}
    current = code_section.get("project_utils", "")

    if utils_path and not current:
        if dry_run:
            return {"action": "would_set", "field": "code.project_utils", "value": utils_path}
        cfg.setdefault("code", {})["project_utils"] = utils_path
        config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return {"action": "set", "field": "code.project_utils", "value": utils_path}

    if current:
        return {"action": "skipped", "field": "code.project_utils", "reason": f"already set to {current}"}

    return {"action": "skipped", "field": "code.project_utils", "reason": "no code/utils/ found"}


def _get_bundled_filter() -> bytes:
    """Read the bundled include.lua from package data."""
    import importlib.resources

    ref = importlib.resources.files("projio") / "data" / "filters" / "include.lua"
    return ref.read_bytes()


def _sync_lua_filter(root: Path, *, dry_run: bool = False) -> dict[str, str]:
    """Copy include.lua to .projio/filters/ if missing or outdated.

    Compares content hashes to detect changes.
    """
    target = root / ".projio" / "filters" / "include.lua"
    try:
        bundled = _get_bundled_filter()
    except Exception as exc:
        return {"action": "error", "reason": f"cannot read bundled filter: {exc}"}

    bundled_hash = hashlib.sha256(bundled).hexdigest()

    if target.is_file():
        existing_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        if existing_hash == bundled_hash:
            return {"action": "skipped", "reason": "up to date"}
        if dry_run:
            return {"action": "would_update", "reason": "content changed"}
        target.write_bytes(bundled)
        return {"action": "updated", "path": str(target.relative_to(root))}

    if dry_run:
        return {"action": "would_copy", "path": ".projio/filters/include.lua"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(bundled)
    return {"action": "copied", "path": str(target.relative_to(root))}


def _get_bundled_csl_files() -> dict[str, bytes]:
    """Read all bundled CSL files from package data."""
    import importlib.resources

    csl_dir = importlib.resources.files("projio") / "data" / "csl"
    result: dict[str, bytes] = {}
    for item in csl_dir.iterdir():
        if hasattr(item, "name") and item.name.endswith(".csl"):
            result[item.name] = item.read_bytes()
    return result


def _sync_csl_files(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Copy bundled CSL files to .projio/render/csl/ if missing or outdated."""
    target_dir = root / ".projio" / "render" / "csl"
    try:
        bundled = _get_bundled_csl_files()
    except Exception as exc:
        return {"action": "error", "reason": f"cannot read bundled CSL files: {exc}"}

    if not bundled:
        return {"action": "skipped", "reason": "no bundled CSL files found"}

    copied = []
    updated = []
    skipped = []

    for name, content in sorted(bundled.items()):
        target = target_dir / name
        bundled_hash = hashlib.sha256(content).hexdigest()

        if target.is_file():
            existing_hash = hashlib.sha256(target.read_bytes()).hexdigest()
            if existing_hash == bundled_hash:
                skipped.append(name)
                continue
            if not dry_run:
                target.write_bytes(content)
            updated.append(name)
        else:
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            copied.append(name)

    return {
        "action": "synced" if not dry_run else "would_sync",
        "copied": copied,
        "updated": updated,
        "skipped": skipped,
    }


def _sync_render_config(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """If .projio/render.yml exists, generate pandoc-defaults.yaml."""
    render_yml = root / ".projio" / "render.yml"
    if not render_yml.is_file():
        return {"action": "skipped", "reason": "no .projio/render.yml"}

    from projio.render import load_render_config, write_pandoc_defaults

    config = load_render_config(root)
    output = root / ".projio" / "render" / "pandoc-defaults.yaml"
    if dry_run:
        return {"action": "would_generate", "output": str(output.relative_to(root))}
    out_path = write_pandoc_defaults(config, root, output=output)
    return {"action": "generated", "output": str(out_path.relative_to(root))}


def _validate_code_envs(root: Path) -> dict[str, Any]:
    """Check that conda envs declared in code.envs actually exist.

    Returns a dict with ``valid``, ``missing``, and ``warnings`` keys.
    """
    from projio.config import load_effective_config

    try:
        cfg = load_effective_config(root)
    except FileNotFoundError:
        return {"valid": [], "missing": [], "warnings": ["no .projio/config.yml"]}

    code = cfg.get("code", {}) or {}
    conda_prefix = code.get("conda_prefix")
    envs = code.get("envs", {}) or {}

    if not envs:
        return {"valid": [], "missing": [], "warnings": []}
    if not conda_prefix:
        return {
            "valid": [],
            "missing": [],
            "warnings": ["code.envs configured but code.conda_prefix is missing"],
        }

    prefix = Path(conda_prefix)
    valid: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []

    if not prefix.is_dir():
        warnings.append(f"conda_prefix does not exist: {prefix}")

    seen_envs: set[str] = set()
    for purpose, env_name in sorted(envs.items()):
        if env_name in seen_envs:
            continue
        seen_envs.add(env_name)
        env_dir = prefix / "envs" / env_name
        if env_dir.is_dir():
            valid.append(env_name)
        else:
            missing.append(env_name)

    return {"valid": valid, "missing": missing, "warnings": warnings}


def _sync_projio_mk(root: Path, *, dry_run: bool = False) -> dict[str, str]:
    """Regenerate projio.mk to pick up new manuscripts/masters."""
    from projio.init import _projio_mk

    mk_path = root / ".projio" / "projio.mk"
    new_content = _projio_mk(root)

    if mk_path.is_file():
        existing = mk_path.read_text(encoding="utf-8")
        if existing == new_content:
            return {"action": "skipped", "reason": "up to date"}

    if dry_run:
        return {"action": "would_update"}

    mk_path.parent.mkdir(parents=True, exist_ok=True)
    mk_path.write_text(new_content, encoding="utf-8")
    return {"action": "updated"}


def _sync_mkdocs_monorepo(root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Ensure mkdocs.yml has monorepo plugin and pipeio !include if pipeio is present.

    Only acts when:
    - mkdocs.yml exists in the project
    - pipeio is available (registry exists)

    Uses text-level insertion to avoid YAML parsing issues with
    ``!!python/name:`` tags used by mkdocs-material.
    """
    mkdocs_path = root / "mkdocs.yml"
    if not mkdocs_path.exists():
        mkdocs_path = root / "mkdocs.yaml"
    if not mkdocs_path.exists():
        return {"action": "skipped", "reason": "no mkdocs.yml"}

    has_pipeio = (
        (root / ".projio" / "pipeio" / "registry.yml").exists()
        or (root / ".pipeio" / "registry.yml").exists()
    )
    if not has_pipeio:
        return {"action": "skipped", "reason": "no pipeio registry"}

    text = mkdocs_path.read_text(encoding="utf-8")
    changed = False
    include_line = "  - Pipelines: '!include ./docs/pipelines/mkdocs.yml'"

    # --- Ensure monorepo in plugins ---
    if "- monorepo" not in text:
        # Find plugins: section or insert one
        if re.search(r"^plugins:", text, re.MULTILINE):
            # Append monorepo after last plugin entry
            text = re.sub(
                r"(^plugins:\n(?:  - .+\n)*)",
                r"\g<1>  - monorepo\n",
                text,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            # Insert plugins section before markdown_extensions (common anchor)
            anchor = re.search(r"^markdown_extensions:", text, re.MULTILINE)
            if anchor:
                text = text[:anchor.start()] + "plugins:\n  - search\n  - monorepo\n\n" + text[anchor.start():]
            else:
                text += "\nplugins:\n  - search\n  - monorepo\n"
        changed = True

    # --- Ensure Pipelines !include in nav ---
    if "!include ./docs/pipelines/mkdocs.yml" not in text:
        # Find the nav: section
        nav_match = re.search(r"^nav:", text, re.MULTILINE)
        if nav_match:
            # Find insertion point: before "- Log:" if present, else end of nav
            log_match = re.search(r"^  - Log:", text, re.MULTILINE)
            if log_match:
                text = text[:log_match.start()] + include_line + "\n" + text[log_match.start():]
            else:
                # Append at end of nav (find last nav entry)
                text = text.rstrip("\n") + "\n" + include_line + "\n"
            changed = True

    if not changed:
        return {"action": "skipped", "reason": "already configured"}

    if dry_run:
        return {"action": "would_update"}

    mkdocs_path.write_text(text, encoding="utf-8")
    return {"action": "updated", "path": str(mkdocs_path.relative_to(root))}


_PROJIO_VSCODE_BEGIN = "// >>> projio >>>"
_PROJIO_VSCODE_END = "// <<< projio <<<"


_PROJIO_WATCHER_EXCLUDES = [
    "**/site/**",
    "**/_site/**",
    "**/_build/**",
    "**/build/**",
    "**/.projio/indexio/index/**",
    "**/.snakemake/**",
    "**/__pycache__/**",
    "**/.git/**",
]


def _find_json_block(text: str, key: str) -> tuple[int, int] | None:
    """Find the span of a JSON key + brace-delimited value in JSONC text.

    Returns (start, end) covering from the key to the closing brace,
    including any trailing comma.  Uses brace counting to handle nested values.
    """
    key_pattern = rf'"{re.escape(key)}"\s*:\s*\{{'
    m = re.search(key_pattern, text)
    if not m:
        return None
    # Walk forward counting braces from the opening {
    brace_start = text.index("{", m.start() + len(key))
    depth = 0
    for i in range(brace_start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                # Consume trailing comma and whitespace
                rest = text[end:]
                trail = re.match(r'\s*,?', rest)
                if trail:
                    end += trail.end()
                # Include leading whitespace/newline before the key
                start = m.start()
                while start > 0 and text[start - 1] in " \t":
                    start -= 1
                if start > 0 and text[start - 1] == "\n":
                    start -= 1
                return (start, end)
    return None


def _collect_existing_excludes(text: str, key: str) -> list[str]:
    """Extract existing exclude patterns from a JSONC settings key."""
    span = _find_json_block(text, key)
    if not span:
        return []
    block = text[span[0]:span[1]]
    return re.findall(r'"([^"]+)"\s*:\s*true', block)


def _remove_unmanaged_excludes(text: str, key: str) -> str:
    """Remove the user-section exclude block so it doesn't conflict with the managed one."""
    managed_pattern = rf"{re.escape(_PROJIO_VSCODE_BEGIN)}.*?{re.escape(_PROJIO_VSCODE_END)}"
    managed_match = re.search(managed_pattern, text, flags=re.DOTALL)

    span = _find_json_block(text, key)
    if not span:
        return text
    # Skip if inside managed block
    if managed_match and managed_match.start() <= span[0] <= managed_match.end():
        return text
    return text[:span[0]] + text[span[1]:]


def _sync_vscode_settings(root: Path, render_cfg: Any, *, dry_run: bool = False) -> dict[str, str]:
    """Sync projio-managed VS Code settings: PandocCiter + watcher excludes.

    Uses a managed block (like gitignore) to avoid destroying JSONC comments
    or user settings.  The block is inserted/replaced between markers.

    For files.watcherExclude: merges projio's standard patterns with any
    existing user patterns, then writes the combined set into the managed
    block.  The unmanaged copy (if any) is removed to avoid conflicts.
    """
    settings_path = root / ".vscode" / "settings.json"
    if not settings_path.parent.is_dir():
        return {"action": "skipped", "reason": "no .vscode/"}
    if not settings_path.exists():
        return {"action": "skipped", "reason": "no .vscode/settings.json"}

    bib = render_cfg.bibliography or ""
    csl = render_cfg.csl or ""

    text = settings_path.read_text(encoding="utf-8")

    # Collect existing watcher excludes from BOTH user section and managed block
    existing_excludes = _collect_existing_excludes(text, "files.watcherExclude")
    # Merge: projio standard + existing user patterns (deduplicated, sorted)
    merged_excludes = sorted(set(_PROJIO_WATCHER_EXCLUDES + existing_excludes))

    # Remove unmanaged files.watcherExclude so it doesn't conflict
    text = _remove_unmanaged_excludes(text, "files.watcherExclude")

    # Build the managed block
    lines = [f"  {_PROJIO_VSCODE_BEGIN}"]
    if bib:
        lines.append(f'  "PandocCiter.DefaultBibs": ["{bib}"],')
        lines.append(f'  "PandocCiter.UseDefaultBib": true,')
    if csl:
        lines.append(f'  "pandocCiter.csl": "{csl}",')
    lines.append(f'  "files.watcherExclude": {{')
    for pattern in merged_excludes:
        lines.append(f'    "{pattern}": true,')
    lines.append(f'  }},')
    lines.append(f"  {_PROJIO_VSCODE_END}")
    block = "\n".join(lines)

    original = settings_path.read_text(encoding="utf-8")

    # Replace existing managed block, or insert before closing brace
    managed_re = rf"[ \t]*{re.escape(_PROJIO_VSCODE_BEGIN)}\n.*?{re.escape(_PROJIO_VSCODE_END)}"
    if re.search(managed_re, text, flags=re.DOTALL):
        text = re.sub(managed_re, block, text, flags=re.DOTALL)
    else:
        last_brace = text.rfind("}")
        if last_brace >= 0:
            text = text[:last_brace] + "\n" + block + "\n" + text[last_brace:]

    if text == original:
        return {"action": "skipped", "reason": "already up to date"}

    if dry_run:
        return {"action": "would_update"}

    settings_path.write_text(text, encoding="utf-8")
    return {"action": "updated"}


def sync_workspace(root: str | Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Run all sync operations on a projio workspace.

    1. Discover code/lib/*/ → register in codio with role=core
    2. Detect code/utils/ → set code.project_utils in config
    3. Copy include.lua to .projio/filters/
    4. Copy CSL files to .projio/render/csl/
    5. Generate .projio/render/pandoc-defaults.yaml from .projio/render.yml
    6. Validate code.envs conda configuration
    7. Regenerate projio.mk
    8. Ensure mkdocs.yml has monorepo plugin + pipeio !include
    9. Sync VS Code settings (PandocCiter + watcher excludes) via managed block

    Args:
        root: Project root directory.
        dry_run: If True, show what would change without writing.

    Returns:
        Summary of actions taken.
    """
    root_path = Path(root).expanduser().resolve()
    projio_dir = root_path / ".projio"
    if not projio_dir.is_dir():
        print(f"[ERROR] No .projio/ directory in {root_path}. Run: projio init")
        return {"error": "not initialized"}

    prefix = "[DRY RUN] " if dry_run else ""

    # 1. Discover code libraries
    libs = _discover_code_libs(root_path)
    if libs:
        print(f"{prefix}Found {len(libs)} library(ies) in code/lib/: {', '.join(l['name'] for l in libs)}")
        lib_actions = _sync_codio_libraries(root_path, libs, dry_run=dry_run)
        for action in lib_actions:
            if action["action"] in ("added", "would_add"):
                print(f"  {prefix}[+] {action['name']} → codio (role=core, kind=internal)")
            elif action["action"] in ("updated", "would_update"):
                print(f"  {prefix}[~] {action['name']} → {action.get('field', '')}")
            elif action["action"] == "skipped":
                print(f"  [=] {action['name']} ({action.get('reason', '')})")
            elif action["action"] == "error":
                print(f"  [!] {action.get('reason', 'unknown error')}")
    else:
        lib_actions = []
        print(f"{prefix}No libraries found in code/lib/")

    # 2. Detect project utils
    utils_path = _detect_project_utils(root_path)
    utils_action = _sync_project_utils_config(root_path, utils_path, dry_run=dry_run)
    if utils_action["action"] in ("set", "would_set"):
        print(f"{prefix}[+] {utils_action['field']} = {utils_action['value']}")
    elif utils_action["action"] == "skipped":
        reason = utils_action.get("reason", "")
        if "already set" in reason:
            print(f"[=] code.project_utils ({reason})")
        elif "not found" not in reason:
            print(f"[=] code.project_utils ({reason})")

    # 3. Sync Lua filter
    filter_action = _sync_lua_filter(root_path, dry_run=dry_run)
    if filter_action["action"] in ("copied", "would_copy"):
        print(f"{prefix}[+] include.lua → .projio/filters/")
    elif filter_action["action"] in ("updated", "would_update"):
        print(f"{prefix}[~] include.lua updated in .projio/filters/")
    elif filter_action["action"] == "skipped":
        print(f"[=] include.lua ({filter_action.get('reason', '')})")
    elif filter_action["action"] == "error":
        print(f"[!] Lua filter: {filter_action.get('reason', '')}")

    # 4. Sync CSL files
    csl_action = _sync_csl_files(root_path, dry_run=dry_run)
    if csl_action.get("copied"):
        print(f"{prefix}[+] CSL files → .projio/render/csl/: {', '.join(csl_action['copied'])}")
    if csl_action.get("updated"):
        print(f"{prefix}[~] CSL files updated: {', '.join(csl_action['updated'])}")
    if csl_action.get("action") == "error":
        print(f"[!] CSL sync: {csl_action.get('reason', '')}")

    # 5. Generate pandoc defaults from render.yml
    from projio.render import RenderConfig, load_render_config
    try:
        render_cfg = load_render_config(root_path)
    except Exception:
        render_cfg = RenderConfig()
    render_action = _sync_render_config(root_path, dry_run=dry_run)
    if render_action["action"] in ("generated", "would_generate"):
        print(f"{prefix}[+] pandoc-defaults.yaml → {render_action.get('output', '')}")
    elif render_action["action"] == "skipped":
        pass  # silent if no render.yml

    # 6. Validate code.envs configuration
    env_validation = _validate_code_envs(root_path)
    for w in env_validation.get("warnings", []):
        print(f"[!] code.envs: {w}")
    for m in env_validation.get("missing", []):
        print(f"[!] code.envs: conda env not found: {m}")
    if env_validation.get("valid"):
        print(f"[=] code.envs: validated {', '.join(env_validation['valid'])}")

    # 7. Regenerate projio.mk to pick up new manuscripts/masters
    mk_action = _sync_projio_mk(root_path, dry_run=dry_run)
    if mk_action["action"] in ("updated", "would_update"):
        print(f"{prefix}[~] projio.mk regenerated")

    # 8. Ensure mkdocs monorepo plugin + pipeio !include
    mkdocs_action = _sync_mkdocs_monorepo(root_path, dry_run=dry_run)
    if mkdocs_action["action"] in ("updated", "would_update"):
        print(f"{prefix}[+] mkdocs.yml: monorepo plugin + Pipelines !include")
    elif mkdocs_action["action"] == "skipped":
        reason = mkdocs_action.get("reason", "")
        if reason not in ("no mkdocs.yml", "no pipeio registry"):
            print(f"[=] mkdocs.yml ({reason})")

    # 9. Sync VS Code settings (PandocCiter + watcher excludes)
    vscode_action = _sync_vscode_settings(root_path, render_cfg, dry_run=dry_run)
    if vscode_action["action"] in ("updated", "would_update"):
        print(f"{prefix}[+] .vscode/settings.json: projio managed block updated")
    elif vscode_action["action"] == "skipped":
        reason = vscode_action.get("reason", "")
        if "no .vscode" in reason:
            print(f"[!] {reason} — PandocCiter autocompletion won't work without it")

    return {
        "libraries": lib_actions,
        "project_utils": utils_action,
        "lua_filter": filter_action,
        "csl_files": csl_action,
        "render": render_action,
        "code_envs": env_validation,
        "projio_mk": mk_action,
        "mkdocs": mkdocs_action,
        "vscode": vscode_action,
    }
