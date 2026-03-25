"""Doc-site server management: detection, port iteration, process lifecycle."""
from __future__ import annotations

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# YAML round-trip helpers (preserve !!python/name: and similar tags)
# ---------------------------------------------------------------------------

class _TaggedScalar:
    """Wraps a YAML scalar whose tag is not handled by SafeLoader."""
    def __init__(self, tag: str, value: str) -> None:
        self.tag = tag
        self.value = value

class _PreservingLoader(yaml.SafeLoader):
    """SafeLoader that keeps unknown tags instead of raising."""

class _PreservingDumper(yaml.SafeDumper):
    """SafeDumper that emits preserved tags back."""

def _tagged_constructor(loader: yaml.SafeLoader, suffix: str, node: yaml.Node) -> _TaggedScalar:
    return _TaggedScalar("tag:yaml.org,2002:python/" + suffix, loader.construct_scalar(node))  # type: ignore[arg-type]

def _tagged_representer(dumper: yaml.SafeDumper, data: _TaggedScalar) -> yaml.ScalarNode:
    return dumper.represent_scalar(data.tag, data.value)

_PreservingLoader.add_multi_constructor("tag:yaml.org,2002:python/", _tagged_constructor)
_PreservingDumper.add_representer(_TaggedScalar, _tagged_representer)


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------

def detect_framework(root: Path) -> str:
    """Detect which doc-site framework a project uses.

    Returns ``"mkdocs"``, ``"sphinx"``, ``"vite"``, or ``"unknown"``.
    First match wins (priority order: mkdocs → sphinx → vite/React frontend).
    """
    # MkDocs
    if (root / "mkdocs.yml").exists() or (root / "mkdocs.yaml").exists():
        return "mkdocs"

    # Sphinx
    if (root / "docs" / "conf.py").exists():
        return "sphinx"
    makefile = root / "Makefile"
    if makefile.exists():
        try:
            text = makefile.read_text(encoding="utf-8", errors="replace")
            if "sphinx-build" in text or "sphinx_build" in text:
                return "sphinx"
        except OSError:
            pass

    # Vite / React frontend
    for pkg_dir in (root, root / "docs"):
        pkg_json = pkg_dir / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                all_deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
                if "vite" in all_deps or "react-scripts" in all_deps:
                    return "vite"
            except (OSError, json.JSONDecodeError):
                pass

    return "unknown"


# ---------------------------------------------------------------------------
# Port management
# ---------------------------------------------------------------------------

def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Return *True* if *host:port* is available for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 30) -> bool:
    """Block until *host:port* is accepting connections, or *timeout* expires."""
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect((host, port))
                return True
            except OSError:
                time.sleep(0.3)
    return False


def find_free_port(
    base: int = 8000,
    max_attempts: int = 50,
    host: str = "127.0.0.1",
) -> int:
    """Find a free port starting from *base*, incrementing up to *max_attempts*."""
    for offset in range(max_attempts):
        port = base + offset
        if _is_port_free(port, host):
            return port
    raise RuntimeError(
        f"No free port found in range {base}–{base + max_attempts - 1}"
    )


# ---------------------------------------------------------------------------
# Server state persistence (.projio/servers.json)
# ---------------------------------------------------------------------------

def _servers_path(root: Path) -> Path:
    return root / ".projio" / "servers.json"


def _pid_alive(pid: int) -> bool:
    """Check whether a process is still running (Unix)."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _prune_dead(servers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [s for s in servers if _pid_alive(s["pid"])]


def _read_servers(root: Path) -> list[dict[str, Any]]:
    path = _servers_path(root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    live = _prune_dead(data if isinstance(data, list) else [])
    _write_servers(root, live)
    return live


def _write_servers(root: Path, servers: list[dict[str, Any]]) -> None:
    path = _servers_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(servers, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _load_site_config(root: Path) -> dict[str, Any]:
    """Load site-specific config (base_port, host) from projio config."""
    try:
        from .config import load_effective_config, get_nested
        cfg = load_effective_config(root)
        return {
            "framework": get_nested(cfg, "site", "framework", default=None),
            "output_dir": get_nested(cfg, "site", "output_dir", default="site"),
            "base_port": get_nested(cfg, "site", "base_port", default=8000),
            "host": get_nested(cfg, "site", "host", default="127.0.0.1"),
            "mkdocs": {
                "config_file": get_nested(cfg, "site", "mkdocs", "config_file", default="mkdocs.yml"),
                "site_dir": get_nested(cfg, "site", "mkdocs", "site_dir", default="site"),
            },
            "sphinx": {
                "source_dir": get_nested(cfg, "site", "sphinx", "source_dir", default="docs"),
                "build_dir": get_nested(cfg, "site", "sphinx", "build_dir", default="docs/_build/html"),
            },
            "vite": {
                "app_dir": get_nested(cfg, "site", "vite", "app_dir", default="."),
                "build_dir": get_nested(cfg, "site", "vite", "build_dir", default=get_nested(cfg, "site", "output_dir", default="site")),
            },
            "chatbot": {
                "enabled": get_nested(cfg, "site", "chatbot", "enabled", default=False),
                "backend_url": get_nested(cfg, "site", "chatbot", "backend_url", default=None),
                "host": get_nested(cfg, "site", "chatbot", "host", default="127.0.0.1"),
                "port": get_nested(cfg, "site", "chatbot", "port", default=9100),
                "title": get_nested(cfg, "site", "chatbot", "title", default="Docs Assistant"),
                "storage_key": get_nested(cfg, "site", "chatbot", "storage_key", default=f"{root.name}_chat_v1"),
                "indexio_config": get_nested(cfg, "indexio", "config", default=".projio/indexio/config.yaml"),
                "corpus": get_nested(cfg, "site", "chatbot", "corpus", default=None),
                "store": get_nested(cfg, "site", "chatbot", "store", default=None),
                "llm_backend": get_nested(cfg, "site", "chatbot", "llm_backend", default=None),
                "llm_model": get_nested(cfg, "site", "chatbot", "llm_model", default=None),
                "llm_base_url": get_nested(cfg, "site", "chatbot", "llm_base_url", default=None),
            },
        }
    except FileNotFoundError:
        return {
            "framework": None,
            "output_dir": "site",
            "base_port": 8000,
            "host": "127.0.0.1",
            "mkdocs": {
                "config_file": "mkdocs.yml",
                "site_dir": "site",
            },
            "sphinx": {
                "source_dir": "docs",
                "build_dir": "docs/_build/html",
            },
            "vite": {
                "app_dir": ".",
                "build_dir": "site",
            },
            "chatbot": {
                "enabled": False,
                "backend_url": None,
                "host": "127.0.0.1",
                "port": 9100,
                "title": "Docs Assistant",
                "storage_key": f"{root.name}_chat_v1",
                "indexio_config": ".projio/indexio/config.yaml",
                "corpus": None,
                "store": None,
                "llm_backend": None,
                "llm_model": None,
                "llm_base_url": None,
            },
        }


def _mkdocs_config_path(root: Path) -> Path:
    if (root / "mkdocs.yml").exists():
        return root / "mkdocs.yml"
    return root / "mkdocs.yaml"


def _resolve_framework(root: Path, *, framework: str | None, site_cfg: dict[str, Any]) -> str:
    if framework is not None:
        return framework
    configured = site_cfg.get("framework")
    if isinstance(configured, str) and configured in {"mkdocs", "sphinx", "vite"}:
        return configured
    return detect_framework(root)


def _vite_app_dir(root: Path, site_cfg: dict[str, Any]) -> Path:
    configured = Path(str(site_cfg.get("vite", {}).get("app_dir", ".")))
    candidate = (root / configured).resolve()
    if (candidate / "package.json").exists():
        return candidate
    if (root / "package.json").exists():
        return root
    docs_dir = root / "docs"
    if (docs_dir / "package.json").exists():
        return docs_dir
    return candidate


def _vite_build_dir(root: Path, site_cfg: dict[str, Any], app_dir: Path) -> str:
    configured = str(site_cfg.get("vite", {}).get("build_dir") or site_cfg.get("output_dir") or "site")
    target = (root / configured).resolve()
    return os.path.relpath(target, app_dir)


def _projio_site_dir(root: Path) -> Path:
    return root / ".projio" / "site"


def _mkdocs_chat_hook_path(root: Path) -> Path:
    return _projio_site_dir(root) / "indexio_chat_hook.py"


def _mkdocs_override_config_path(root: Path) -> Path:
    return root / ".projio.mkdocs.yml"


def _write_mkdocs_chat_hook(root: Path, *, backend_url: str, title: str, storage_key: str) -> Path:
    hook_path = _mkdocs_chat_hook_path(root)
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    base = backend_url.rstrip("/")
    api_url = f"{base}/chat/"
    stream_url = f"{base}/chat/stream"
    status_url = f"{base}/status"
    js_url = f"{base}/chatbot/chatbot.js"
    css_url = f"{base}/chatbot/chatbot.css"
    chat_cfg = {
        "apiUrl": api_url,
        "streamUrl": stream_url,
        "statusUrl": status_url,
        "title": title,
        "storageKey": storage_key,
    }
    snippet = (
        "<script>"
        f"window.INDEXIO_CHAT = {json.dumps(chat_cfg)};"
        "</script>"
        f'<script src="{js_url}"></script>'
        f'<link href="{css_url}" rel="stylesheet">'
    )
    hook_path.write_text(
        (
            '"""Generated by projio to inject the indexio chatbot widget into MkDocs pages."""\n'
            "from __future__ import annotations\n\n"
            f"SNIPPET = {snippet!r}\n\n"
            "def on_page_content(html, page, config, files):\n"
            "    if SNIPPET in html:\n"
            "        return html\n"
            "    if '</body>' in html:\n"
            "        return html.replace('</body>', SNIPPET + '</body>')\n"
            "    return html + SNIPPET\n"
        ),
        encoding="utf-8",
    )
    return hook_path


def _mkdocs_config_with_chatbot(
    root: Path, *, backend_url: str, title: str, storage_key: str
) -> Path:
    config_path = _mkdocs_config_path(root)
    payload = yaml.load(config_path.read_text(encoding="utf-8"), Loader=_PreservingLoader) or {}
    if not isinstance(payload, dict):
        raise TypeError(f"Expected mapping in {config_path}")
    hook_path = _write_mkdocs_chat_hook(
        root,
        backend_url=backend_url,
        title=title,
        storage_key=storage_key,
    )
    hooks = list(payload.get("hooks") or [])
    rel_hook = str(hook_path.relative_to(root))
    if rel_hook not in hooks:
        hooks.append(rel_hook)
    payload["hooks"] = hooks
    override_path = _mkdocs_override_config_path(root)
    override_path.write_text(yaml.dump(payload, Dumper=_PreservingDumper, sort_keys=False), encoding="utf-8")
    return override_path


def _indexio_serve_cmd(
    root: Path,
    chatbot_cfg: dict[str, Any],
    *,
    host: str,
    port: int,
    site_url: str | None = None,
) -> list[str]:
    if importlib.util.find_spec("indexio") is None:
        raise RuntimeError("site chatbot requires the indexio package to be installed")
    cmd = [
        sys.executable,
        "-m",
        "indexio",
        "serve",
        "--root",
        ".",
        "--config",
        str(chatbot_cfg["indexio_config"]),
        "--host",
        host,
        "--port",
        str(port),
        "--title",
        str(chatbot_cfg["title"]),
    ]
    if chatbot_cfg.get("corpus"):
        cmd.extend(["--corpus", str(chatbot_cfg["corpus"])])
    if chatbot_cfg.get("store"):
        cmd.extend(["--store", str(chatbot_cfg["store"])])
    if chatbot_cfg.get("llm_backend"):
        cmd.extend(["--llm-backend", str(chatbot_cfg["llm_backend"])])
    if chatbot_cfg.get("llm_model"):
        cmd.extend(["--llm-model", str(chatbot_cfg["llm_model"])])
    if chatbot_cfg.get("llm_base_url"):
        cmd.extend(["--llm-base-url", str(chatbot_cfg["llm_base_url"])])
    if site_url:
        cmd.extend(["--site-url", site_url])
    return cmd


def _prepare_site_chatbot(
    root: Path,
    *,
    framework: str,
    site_cfg: dict[str, Any],
    for_serve: bool,
    site_url: str | None = None,
) -> dict[str, Any]:
    chatbot_cfg = dict(site_cfg.get("chatbot") or {})
    if framework != "mkdocs" or not chatbot_cfg.get("enabled"):
        return {"config_path": None, "chat_cmd": None, "chat_proc": None, "backend_url": None}

    backend_url = chatbot_cfg.get("backend_url")
    chat_cmd = None
    if backend_url is None and for_serve:
        chat_host = str(chatbot_cfg.get("host") or site_cfg["host"])
        chat_port = find_free_port(base=int(chatbot_cfg.get("port", 9100)), host=chat_host)
        chat_cmd = _indexio_serve_cmd(root, chatbot_cfg, host=chat_host, port=chat_port, site_url=site_url)
        backend_url = f"http://{chat_host}:{chat_port}"
    elif backend_url is None:
        print("[projio-site] Chatbot enabled, but no site.chatbot.backend_url configured; skipping widget injection.")
        return {"config_path": None, "chat_cmd": None, "chat_proc": None, "backend_url": None}

    config_path = _mkdocs_config_with_chatbot(
        root,
        backend_url=str(backend_url),
        title=str(chatbot_cfg["title"]),
        storage_key=str(chatbot_cfg["storage_key"]),
    )
    return {"config_path": config_path, "chat_cmd": chat_cmd, "chat_proc": None, "backend_url": backend_url}


# ---------------------------------------------------------------------------
# Framework-specific commands
# ---------------------------------------------------------------------------

def _serve_cmd(
    framework: str, host: str, port: int, root: Path, site_cfg: dict[str, Any],
    *, config_path: Path | None = None, python_bin: str | None = None,
) -> tuple[list[str], Path]:
    """Build the subprocess command list for each framework."""
    py = python_bin or sys.executable
    if framework == "mkdocs":
        cmd = [py, "-m", "mkdocs", "serve", "--dev-addr", f"{host}:{port}"]
        if config_path is not None:
            cmd.extend(["-f", str(config_path)])
        return cmd, root
    if framework == "sphinx":
        sphinx_cfg = site_cfg["sphinx"]
        source_dir = str(sphinx_cfg["source_dir"])
        build_dir = str(sphinx_cfg["build_dir"])
        return [
            py, "-m", "sphinx_autobuild",
            source_dir, build_dir,
            "--host", host, "--port", str(port),
        ], root
    if framework == "vite":
        app_dir = _vite_app_dir(root, site_cfg)
        return ["npx", "vite", "--host", host, "--port", str(port)], app_dir
    raise ValueError(f"Cannot serve unknown framework: {framework}")


def _build_cmd(
    framework: str,
    root: Path,
    site_cfg: dict[str, Any],
    *,
    strict: bool = False,
    config_path: Path | None = None,
    python_bin: str | None = None,
) -> tuple[list[str], Path]:
    """Build the subprocess command list for building docs.

    *python_bin* overrides ``sys.executable`` for framework invocations that
    need a specific Python (e.g. one where mkdocs / sphinx is installed).
    """
    py = python_bin or sys.executable
    if framework == "mkdocs":
        cmd = [py, "-m", "mkdocs", "build"]
        if config_path is not None:
            cmd.extend(["-f", str(config_path)])
        if strict:
            cmd.append("--strict")
        return cmd, root
    if framework == "sphinx":
        sphinx_cfg = site_cfg["sphinx"]
        return [
            py,
            "-m",
            "sphinx",
            "-b",
            "html",
            str(sphinx_cfg["source_dir"]),
            str(sphinx_cfg["build_dir"]),
        ], root
    if framework == "vite":
        app_dir = _vite_app_dir(root, site_cfg)
        return ["npx", "vite", "build", "--outDir", _vite_build_dir(root, site_cfg, app_dir)], app_dir
    raise ValueError(f"Cannot build unknown framework: {framework}")


# ---------------------------------------------------------------------------
# Process lifecycle
# ---------------------------------------------------------------------------

def serve(
    root: str | Path,
    *,
    port: int | None = None,
    host: str | None = None,
    framework: str | None = None,
    background: bool = False,
) -> dict[str, Any]:
    """Start a doc server.

    Returns ``{"pid", "port", "framework", "url"}`` when *background* is True.
    Blocks (foreground) when *background* is False.
    """
    root = Path(root).expanduser().resolve()
    site_cfg = _load_site_config(root)

    if host is None:
        host = site_cfg["host"]
    framework = _resolve_framework(root, framework=framework, site_cfg=site_cfg)
    if framework == "unknown":
        raise RuntimeError(
            "Could not detect doc-site framework. "
            "Expected mkdocs.yml, docs/conf.py, or package.json for a Vite/React frontend."
        )
    if port is None:
        port = find_free_port(base=site_cfg["base_port"], host=host)
    # Build the local site URL, including any base path from mkdocs site_url.
    site_url = f"http://{host}:{port}"
    if framework == "mkdocs":
        try:
            from urllib.parse import urlparse

            mkdocs_raw = yaml.load(
                _mkdocs_config_path(root).read_text(encoding="utf-8"),
                Loader=_PreservingLoader,
            ) or {}
            mkdocs_site_url = mkdocs_raw.get("site_url", "")
            if mkdocs_site_url:
                base_path = urlparse(str(mkdocs_site_url)).path.rstrip("/")
                if base_path:
                    site_url = f"{site_url}{base_path}"
        except Exception:
            pass
    integration = _prepare_site_chatbot(root, framework=framework, site_cfg=site_cfg, for_serve=True, site_url=site_url)
    cmd, cmd_cwd = _serve_cmd(framework, host, port, root, site_cfg, config_path=integration["config_path"])

    # Start chatbot AFTER the site server binds its port so that VSCode
    # detects the user-facing site port first.
    def _start_chatbot() -> subprocess.Popen[bytes] | None:
        if integration["chat_cmd"] is None:
            return None
        _wait_for_port(port, host=host)
        return subprocess.Popen(
            integration["chat_cmd"], cwd=root,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

    if not background:
        if integration["backend_url"]:
            print(f"[projio-site] Chatbot backend: {integration['backend_url']}")
        site_proc = subprocess.Popen(cmd, cwd=cmd_cwd)
        chat_proc = _start_chatbot()
        try:
            rc = site_proc.wait()
            if rc != 0:
                sys.exit(rc)
            return {"pid": 0, "port": port, "framework": framework, "url": f"http://{host}:{port}"}
        finally:
            if chat_proc is not None:
                try:
                    chat_proc.terminate()
                except OSError:
                    pass

    proc = subprocess.Popen(cmd, cwd=cmd_cwd)
    chat_proc = _start_chatbot()
    record: dict[str, Any] = {
        "pid": proc.pid,
        "service": "site",
        "framework": framework,
        "port": port,
        "root": str(root),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": cmd,
    }
    servers = _read_servers(root)
    servers.append(record)
    if chat_proc is not None:
        servers.append(
            {
                "pid": chat_proc.pid,
                "service": "chatbot",
                "framework": "indexio-chat",
                "port": int(str(integration["backend_url"]).rsplit(":", 1)[1]),
                "root": str(root),
                "started_at": datetime.now(timezone.utc).isoformat(),
                "command": integration["chat_cmd"],
            }
        )
    _write_servers(root, servers)
    result = {
        "pid": proc.pid,
        "port": port,
        "framework": framework,
        "url": f"http://{host}:{port}",
    }
    if integration["backend_url"]:
        result["chatbot_url"] = integration["backend_url"]
    return result


def stop(
    root: str | Path,
    *,
    port: int | None = None,
    pid: int | None = None,
) -> dict[str, Any]:
    """Stop a running doc server by port or PID."""
    root = Path(root).expanduser().resolve()
    servers = _read_servers(root)
    target = None
    for s in servers:
        if (port is not None and s["port"] == port) or (pid is not None and s["pid"] == pid):
            target = s
            break
    if target is None:
        return {"stopped": False, "error": "No matching server found"}
    try:
        os.kill(target["pid"], signal.SIGTERM)
    except ProcessLookupError:
        pass
    servers = [s for s in servers if s is not target]
    _write_servers(root, servers)
    return {"stopped": True, "pid": target["pid"], "port": target["port"]}


def list_servers(root: str | Path) -> list[dict[str, Any]]:
    """Return live server records for the given project root."""
    root = Path(root).expanduser().resolve()
    return _read_servers(root)


def stop_all(root: str | Path) -> dict[str, Any]:
    """Stop all tracked servers for a project."""
    root = Path(root).expanduser().resolve()
    servers = _read_servers(root)
    count = 0
    for s in servers:
        try:
            os.kill(s["pid"], signal.SIGTERM)
            count += 1
        except ProcessLookupError:
            pass
    _write_servers(root, [])
    return {"stopped": count}


# ---------------------------------------------------------------------------
# Build & publish (enhanced with framework detection)
# ---------------------------------------------------------------------------

def build(
    root: str | Path,
    *,
    strict: bool = False,
    framework: str | None = None,
    python_bin: str | None = None,
) -> None:
    """Build docs. Auto-detects framework if not specified.

    *python_bin* overrides ``sys.executable`` for invoking the doc framework.
    """
    root = Path(root).expanduser().resolve()
    site_cfg = _load_site_config(root)
    framework = _resolve_framework(root, framework=framework, site_cfg=site_cfg)
    if framework == "unknown":
        raise RuntimeError("Could not detect doc-site framework.")
    integration = _prepare_site_chatbot(root, framework=framework, site_cfg=site_cfg, for_serve=False)
    cmd, cmd_cwd = _build_cmd(
        framework, root, site_cfg,
        strict=strict,
        config_path=integration["config_path"],
        python_bin=python_bin,
    )
    result = subprocess.run(cmd, cwd=cmd_cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def publish(
    root: str | Path,
    *,
    framework: str | None = None,
    python_bin: str | None = None,
) -> None:
    """Publish docs. Currently only mkdocs gh-deploy is supported."""
    root = Path(root).expanduser().resolve()
    site_cfg = _load_site_config(root)
    framework = _resolve_framework(root, framework=framework, site_cfg=site_cfg)
    if framework != "mkdocs":
        raise RuntimeError(
            f"Publish is currently only supported for mkdocs (detected: {framework}). "
            "Use your framework's deploy tooling directly."
        )
    py = python_bin or sys.executable
    cmd = [py, "-m", "mkdocs", "gh-deploy", "--force"]
    result = subprocess.run(cmd, cwd=root)
    if result.returncode != 0:
        sys.exit(result.returncode)
