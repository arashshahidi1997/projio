"""projio CLI — init / status / site / helpers / mcp."""
from __future__ import annotations

import argparse
from typing import Iterable


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="projio",
        description="Project knowledge orchestrator for research repositories.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Scaffold .projio/ workspace files.")
    p_init.add_argument("root", nargs="?", default=".", help="Project root (default: .).")
    p_init.add_argument(
        "--kind",
        choices=("generic", "tool", "study"),
        default="generic",
        help="Project scaffold kind (default: generic).",
    )
    p_init.add_argument(
        "-c", "--profile",
        choices=("research", "full"),
        default=None,
        help="Activate a preset bundle of components (research: notio+biblio+indexio, full: all).",
    )
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files.")
    p_init.add_argument(
        "--vscode",
        action="store_true",
        help="Create .vscode/settings.json with projio site excludes.",
    )
    p_init.add_argument(
        "--github-pages",
        action="store_true",
        help="Create a GitHub Pages workflow at .github/workflows/docs.yml.",
    )
    p_init.add_argument(
        "--gitlab-pages",
        action="store_true",
        help="Create a GitLab Pages CI config at .gitlab-ci.yml.",
    )

    p_add = sub.add_parser("add", help="Activate a package component in the workspace.")
    p_add.add_argument("package", help="Package to activate (biblio, notio, codio, indexio, claude).")
    p_add.add_argument("-C", "--root", default=".", help="Project root (default: .).")

    p_remove = sub.add_parser("remove", help="Deactivate a package component.")
    p_remove.add_argument("package", help="Package to deactivate.")
    p_remove.add_argument("-C", "--root", default=".", help="Project root (default: .).")

    p_list = sub.add_parser("list", help="List workspace components and their status.")
    p_list.add_argument("-C", "--root", default=".", help="Project root (default: .).")

    p_status = sub.add_parser("status", help="Show project, index, and git status.")
    p_status.add_argument("-C", "--root", default=".", help="Project root (default: .).")

    p_url = sub.add_parser("url", help="Print remote repository and Pages URLs.")
    p_url.add_argument("-C", "--root", default=".", help="Project root (default: .).")

    p_config = sub.add_parser("config", help="Manage projio config files.")
    p_config.add_argument("-C", "--root", default=".", help="Project root (default: .).")
    config_sub = p_config.add_subparsers(dest="config_command", required=True)
    p_config_init_user = config_sub.add_parser("init-user", help="Scaffold ~/.config/projio/config.yml.")
    p_config_init_user.add_argument("--force", action="store_true", help="Overwrite existing user config.")
    config_sub.add_parser("show", help="Print merged user + project config.")

    p_site = sub.add_parser("site", help="Doc-site operations (MkDocs, Sphinx, React frontend via Vite).")
    site_sub = p_site.add_subparsers(dest="site_command", required=True)

    _fw_choices = ("mkdocs", "sphinx", "vite")

    p_site_build = site_sub.add_parser("build", help="Build the doc site.")
    p_site_build.add_argument("-C", "--root", default=".", help="Project root.")
    p_site_build.add_argument("--strict", action="store_true", help="Fail on warnings.")
    p_site_build.add_argument("--framework", choices=_fw_choices, default=None,
                              help="Override framework detection.")

    p_site_serve = site_sub.add_parser("serve", help="Serve the doc site locally.")
    p_site_serve.add_argument("-C", "--root", default=".", help="Project root.")
    p_site_serve.add_argument("--port", type=int, default=None, help="Port (default: auto-find from base_port).")
    p_site_serve.add_argument("--framework", choices=_fw_choices, default=None,
                              help="Override framework detection.")
    p_site_serve.add_argument("--background", action="store_true", help="Run server in background.")

    p_site_publish = site_sub.add_parser("publish", help="Publish site to GitHub Pages.")
    p_site_publish.add_argument("-C", "--root", default=".", help="Project root.")

    p_site_stop = site_sub.add_parser("stop", help="Stop a running doc server.")
    p_site_stop.add_argument("-C", "--root", default=".", help="Project root.")
    p_site_stop.add_argument("--port", type=int, default=None, help="Stop server on this port.")
    p_site_stop.add_argument("--pid", type=int, default=None, help="Stop server with this PID.")
    p_site_stop.add_argument("--all", action="store_true", dest="stop_all", help="Stop all servers.")

    p_site_list = site_sub.add_parser("list", help="List running doc servers.")
    p_site_list.add_argument("-C", "--root", default=".", help="Project root.")

    p_site_detect = site_sub.add_parser("detect", help="Detect doc-site framework.")
    p_site_detect.add_argument("-C", "--root", default=".", help="Project root.")

    p_sibling = sub.add_parser("sibling", help="Manage Datalad siblings.")
    p_sibling.add_argument("-C", "--root", default=".", help="Project root (default: .).")
    sibling_sub = p_sibling.add_subparsers(dest="sibling_command", required=True)

    p_sibling_github = sibling_sub.add_parser("github", help="Create a GitHub sibling.")
    p_sibling_github.add_argument("--project", help="Target GitHub repo name.")
    p_sibling_github.add_argument("--sibling", help="Sibling name.")
    p_sibling_github.add_argument("--credential", help="Datalad credential name.")
    p_sibling_github.add_argument("--access-protocol", help="GitHub access protocol.")
    p_sibling_github.add_argument("--yes", action="store_true", help="Execute instead of preview.")

    p_sibling_gitlab = sibling_sub.add_parser("gitlab", help="Create a GitLab sibling.")
    p_sibling_gitlab.add_argument("--project", help="Target GitLab project path.")
    p_sibling_gitlab.add_argument("--sibling", help="Sibling name.")
    p_sibling_gitlab.add_argument("--site", help="GitLab site profile.")
    p_sibling_gitlab.add_argument("--layout", help="GitLab layout.")
    p_sibling_gitlab.add_argument("--access", help="GitLab access mode.")
    p_sibling_gitlab.add_argument("--credential", help="Datalad credential name.")
    p_sibling_gitlab.add_argument("--yes", action="store_true", help="Execute instead of preview.")

    p_sibling_ria = sibling_sub.add_parser("ria", help="Create a RIA sibling.")
    p_sibling_ria.add_argument("--sibling", help="Sibling name.")
    p_sibling_ria.add_argument("--alias", help="RIA alias.")
    p_sibling_ria.add_argument("--storage-url", help="RIA storage URL.")
    p_sibling_ria.add_argument("--shared", help="RIA shared mode.")
    p_sibling_ria.add_argument("--yes", action="store_true", help="Execute instead of preview.")

    p_docs = sub.add_parser("docs", help="Project docs helpers.")
    p_docs.add_argument("-C", "--root", default=".", help="Project root (default: .).")
    docs_sub = p_docs.add_subparsers(dest="docs_command", required=True)
    p_docs_mkdocs = docs_sub.add_parser("mkdocs-init", help="Scaffold MkDocs files.")
    p_docs_mkdocs.add_argument("--force", action="store_true", help="Overwrite existing files.")

    p_auth = sub.add_parser("auth", help="Authentication diagnostics.")
    p_auth.add_argument("-C", "--root", default=".", help="Project root (default: .).")
    auth_sub = p_auth.add_subparsers(dest="auth_command", required=True)
    auth_sub.add_parser("doctor", help="Show helper credential resolution status.")

    p_mcp = sub.add_parser("mcp", help="Start the FastMCP server (stdio).")
    p_mcp.add_argument("-C", "--root", default=".", help="Project root (default: .).")

    p_mcp_config = sub.add_parser("mcp-config", help="Generate .mcp.json for Claude Code.")
    p_mcp_config.add_argument("-C", "--root", default=".", help="Project root (default: .).")
    p_mcp_config.add_argument("--output", default=None, help="Output path (default: .mcp.json in project root).")
    p_mcp_config.add_argument("--yes", action="store_true", help="Write the file (default: preview only).")

    return parser


def main(argv: Iterable[str] | None = None) -> None:
    args = _build_parser().parse_args(list(argv) if argv is not None else None)

    if args.command == "init":
        from .init import scaffold
        scaffold(
            args.root,
            kind=args.kind,
            profile=args.profile,
            force=args.force,
            vscode=args.vscode,
            github_pages=args.github_pages,
            gitlab_pages=args.gitlab_pages,
        )
        return

    if args.command == "add":
        from .init import add_package
        add_package(args.root, args.package)
        return

    if args.command == "remove":
        from .init import remove_package
        remove_package(args.root, args.package)
        return

    if args.command == "list":
        from .init import print_packages
        print_packages(args.root)
        return

    if args.command == "status":
        from .status import print_report
        print_report(args.root)
        return

    if args.command == "url":
        from .url import print_urls
        print_urls(args.root)
        return

    if args.command == "config":
        from . import config as config_mod
        if args.config_command == "init-user":
            config_mod.scaffold_user_config(force=args.force)
        elif args.config_command == "show":
            config_mod.print_effective_config(args.root)
        return

    if args.command == "site":
        from . import site as site_mod
        if args.site_command == "build":
            site_mod.build(args.root, strict=args.strict, framework=args.framework)
        elif args.site_command == "serve":
            result = site_mod.serve(
                args.root, port=args.port, framework=args.framework,
                background=args.background,
            )
            if args.background:
                print(f"Server started: {result['url']} (PID {result['pid']})")
        elif args.site_command == "publish":
            site_mod.publish(args.root)
        elif args.site_command == "stop":
            if args.stop_all:
                info = site_mod.stop_all(args.root)
                print(f"Stopped {info['stopped']} server(s)")
            else:
                info = site_mod.stop(args.root, port=args.port, pid=args.pid)
                if info["stopped"]:
                    print(f"Stopped server PID {info['pid']} on port {info['port']}")
                else:
                    print(f"Error: {info.get('error', 'unknown')}")
        elif args.site_command == "list":
            servers = site_mod.list_servers(args.root)
            if not servers:
                print("No running servers.")
            for s in servers:
                print(f"  {s['framework']}  port={s['port']}  pid={s['pid']}  since {s['started_at']}")
        elif args.site_command == "detect":
            from pathlib import Path
            fw = site_mod.detect_framework(Path(args.root).expanduser().resolve())
            print(f"Detected framework: {fw}")
        return

    if args.command == "sibling":
        from .helpers import siblings
        if args.sibling_command == "github":
            siblings.sibling_github(
                root=args.root,
                sibling=args.sibling,
                project=args.project,
                credential=args.credential,
                access_protocol=args.access_protocol,
                yes=args.yes,
            )
        elif args.sibling_command == "gitlab":
            siblings.sibling_gitlab(
                root=args.root,
                sibling=args.sibling,
                project=args.project,
                site=args.site,
                layout=args.layout,
                access=args.access,
                credential=args.credential,
                yes=args.yes,
            )
        elif args.sibling_command == "ria":
            siblings.sibling_ria(
                root=args.root,
                sibling=args.sibling,
                alias=args.alias,
                storage_url=args.storage_url,
                shared=args.shared,
                yes=args.yes,
            )
        return

    if args.command == "docs":
        from .helpers.docs import mkdocs_init
        if args.docs_command == "mkdocs-init":
            mkdocs_init(args.root, force=args.force)
        return

    if args.command == "auth":
        from .helpers.auth import auth_doctor
        if args.auth_command == "doctor":
            auth_doctor(args.root)
        return

    if args.command == "mcp":
        import os
        os.environ.setdefault("PROJIO_ROOT", str(args.root))
        from .mcp.server import main as mcp_main
        mcp_main()
        return

    if args.command == "mcp-config":
        from pathlib import Path
        from .config import load_effective_config, get_nested
        from .mcp.config_gen import write_mcp_config

        root = Path(args.root).expanduser().resolve()
        cfg = load_effective_config(root)
        python_bin = get_nested(cfg, "runtime", "python_bin", default=None)
        output = Path(args.output) if args.output else None
        write_mcp_config(root, python_bin=python_bin, output=output, yes=args.yes)
        return

    raise SystemExit(2)
