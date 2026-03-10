from __future__ import annotations

from projio.cli import _build_parser


def test_cli_parses_init_positional_root() -> None:
    parser = _build_parser()
    args = parser.parse_args(["init", ".", "--force"])
    assert args.command == "init"
    assert args.root == "."
    assert args.kind == "generic"
    assert args.force is True


def test_cli_parses_init_kind_variants() -> None:
    parser = _build_parser()
    tool_args = parser.parse_args(["init", ".", "--kind", "tool"])
    study_args = parser.parse_args(["init", ".", "--kind", "study"])
    assert tool_args.kind == "tool"
    assert study_args.kind == "study"


def test_cli_parses_github_sibling_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["sibling", "-C", "/tmp/repo", "github", "--project", "demo", "--yes"])
    assert args.command == "sibling"
    assert args.root == "/tmp/repo"
    assert args.sibling_command == "github"
    assert args.project == "demo"
    assert args.yes is True


def test_cli_parses_gitlab_sibling_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["sibling", "gitlab", "--site", "lrz", "--layout", "flat"])
    assert args.command == "sibling"
    assert args.sibling_command == "gitlab"
    assert args.site == "lrz"
    assert args.layout == "flat"


def test_cli_parses_ria_sibling_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["sibling", "ria", "--storage-url", "ria+file:///tmp/store"])
    assert args.command == "sibling"
    assert args.sibling_command == "ria"
    assert args.storage_url == "ria+file:///tmp/store"


def test_cli_parses_docs_and_auth_commands() -> None:
    parser = _build_parser()
    docs_args = parser.parse_args(["docs", "mkdocs-init", "--force"])
    auth_args = parser.parse_args(["auth", "doctor"])
    assert docs_args.command == "docs"
    assert docs_args.docs_command == "mkdocs-init"
    assert docs_args.force is True
    assert auth_args.command == "auth"
    assert auth_args.auth_command == "doctor"


def test_cli_parses_config_commands() -> None:
    parser = _build_parser()
    init_args = parser.parse_args(["config", "init-user", "--force"])
    show_args = parser.parse_args(["config", "-C", "/tmp/repo", "show"])
    assert init_args.command == "config"
    assert init_args.config_command == "init-user"
    assert init_args.force is True
    assert show_args.command == "config"
    assert show_args.config_command == "show"
    assert show_args.root == "/tmp/repo"


def test_cli_parses_site_and_auth_with_c_alias() -> None:
    parser = _build_parser()
    site_args = parser.parse_args(["site", "build", "-C", "/tmp/repo"])
    auth_args = parser.parse_args(["auth", "-C", "/tmp/repo", "doctor"])
    assert site_args.root == "/tmp/repo"
    assert auth_args.root == "/tmp/repo"
