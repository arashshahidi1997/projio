"""Configuration loading for project and user-level projio settings."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_USER_CONFIG = """\
# projio user defaults
helpers:
  sibling:
    github:
      sibling: github
      credential: github
      project_template: "{project_name}"
    gitlab:
      sibling: gitlab
      credential: gitlab
      project_template: "{project_name}"
    ria:
      sibling: origin
      alias_strategy: basename
      storage_url: ria+file:///storage/share/git/ria-store
      shared: group

# claude code permissions (synced to .claude/settings.json)
# claude:
#   extra_permissions:
#     - "Read(/storage/share/codelib/**)"
#   extra_mcp_wildcards:
#     - "mcp__sirocampus__*"
"""


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise TypeError(f"Expected mapping in {path}")
    return payload


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_user_config_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home.expanduser() / "projio" / "config.yml"


def get_project_config_path(root: str | Path) -> Path:
    return Path(root).expanduser().resolve() / ".projio" / "config.yml"


def load_user_config() -> dict[str, Any]:
    return _read_yaml_mapping(get_user_config_path())


def load_project_config(root: str | Path) -> dict[str, Any]:
    path = get_project_config_path(root)
    if not path.exists():
        raise FileNotFoundError(f"No .projio/config.yml found in {Path(root).expanduser().resolve()}. Run: projio init")
    return _read_yaml_mapping(path)


def load_effective_config(root: str | Path) -> dict[str, Any]:
    user_cfg = load_user_config()
    project_cfg = load_project_config(root)
    return _deep_merge(user_cfg, project_cfg)


def get_nested(mapping: dict[str, Any], *parts: str, default: Any = None) -> Any:
    current: Any = mapping
    for part in parts:
        if not isinstance(current, dict):
            return default
        current = current.get(part, default)
        if current is default:
            return default
    return current


def resolve_env_python(
    root: str | Path,
    purpose: str,
    *,
    binary: str = "python",
) -> str | None:
    """Resolve a binary path for *purpose* from ``code.envs`` config.

    Looks up ``code.envs.<purpose>`` for the conda env name and combines it
    with ``code.conda_prefix`` to produce an absolute path.  Returns ``None``
    when the config keys are absent.

    Args:
        root: Project root directory.
        purpose: Environment purpose key (``default``, ``docs``, ``rag``,
            ``datalad``).
        binary: Binary name to resolve inside the env (default ``python``).
    """
    try:
        cfg = load_effective_config(root)
    except FileNotFoundError:
        return None
    code = cfg.get("code", {}) or {}
    conda_prefix = code.get("conda_prefix")
    envs = code.get("envs", {}) or {}

    env_name = envs.get(purpose)
    if not env_name or not conda_prefix:
        return None

    path = Path(conda_prefix) / "envs" / env_name / "bin" / binary
    return str(path)


def resolve_env_all(root: str | Path) -> dict[str, str | None]:
    """Resolve all standard env binaries from ``code.envs`` config.

    Returns a dict with keys: ``python``, ``projio``, ``docs``, ``datalad``,
    ``pandoc``.  Values are absolute paths or ``None`` if not configured.
    """
    return {
        "python": resolve_env_python(root, "default"),
        "projio": resolve_env_python(root, "rag"),
        "docs": resolve_env_python(root, "docs"),
        "datalad": resolve_env_python(root, "datalad", binary="datalad"),
        "pandoc": resolve_env_python(root, "datalad", binary="pandoc"),
        "matlab": resolve_env_python(root, "matlab", binary="matlab"),
    }


def scaffold_user_config(*, force: bool = False) -> Path:
    path = get_user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        print(f"[SKIP] {path} already exists (--force to overwrite)")
        return path
    path.write_text(DEFAULT_USER_CONFIG, encoding="utf-8")
    print(f"[OK] wrote {path}")
    return path


def print_effective_config(root: str | Path) -> None:
    payload = load_effective_config(root)
    print(yaml.safe_dump(payload, sort_keys=False))


def _resolve_conda_python(env_name: str) -> str:
    """Resolve a conda env name to its python binary path."""
    import shutil
    import subprocess

    conda = shutil.which("conda")
    if not conda:
        raise FileNotFoundError("conda not found on PATH")

    result = subprocess.run(
        [conda, "run", "-n", env_name, "python", "-c", "import sys; print(sys.executable)"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"conda env {env_name!r} not found or broken: {result.stderr.strip()}")
    return result.stdout.strip()


def set_python(root: str | Path, *, python_path: str | None = None, conda_env: str | None = None) -> None:
    """Set runtime.python_bin in project config, then regenerate projio.mk."""
    import sys

    root_path = Path(root).expanduser().resolve()
    config_path = get_project_config_path(root_path)
    if not config_path.exists():
        raise FileNotFoundError(f"No .projio/config.yml in {root_path}. Run: projio init")

    # Resolve the python path
    if conda_env:
        resolved = _resolve_conda_python(conda_env)
    elif python_path:
        resolved = str(Path(python_path).expanduser().resolve())
    else:
        resolved = sys.executable

    # Verify it exists
    if not Path(resolved).exists():
        raise FileNotFoundError(f"Python not found: {resolved}")

    # Update config
    cfg = _read_yaml_mapping(config_path)
    cfg.setdefault("runtime", {})["python_bin"] = resolved
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    print(f"[OK] runtime.python_bin = {resolved}")

    # Regenerate projio.mk to pick up the new python
    from projio.init import _projio_mk, _write_if_needed
    mk_path = root_path / ".projio" / "projio.mk"
    _write_if_needed(mk_path, _projio_mk(root_path), root_path, force=True)
