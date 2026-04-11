from __future__ import annotations

from projio.cli import _build_parser


def test_cli_parses_init_positional_root() -> None:
    parser = _build_parser()
    args = parser.parse_args(["init", ".", "--force", "--vscode", "--github-pages"])
    assert args.command == "init"
    assert args.root == "."
    assert args.kind == "generic"
    assert args.force is True
    assert args.vscode is True
    assert args.github_pages is True


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


def test_cli_parses_sync_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["sync", "-C", "/tmp/repo", "--dry-run"])
    assert args.command == "sync"
    assert args.root == "/tmp/repo"
    assert args.dry_run is True
    assert args.index is None  # neither --index nor --no-index


def test_cli_parses_sync_index_flag() -> None:
    parser = _build_parser()
    args = parser.parse_args(["sync", "--index"])
    assert args.index is True


def test_cli_parses_sync_no_index_flag() -> None:
    parser = _build_parser()
    args = parser.parse_args(["sync", "--no-index"])
    assert args.index is False


def test_cli_parses_sync_install_hooks() -> None:
    parser = _build_parser()
    args = parser.parse_args(["sync", "--install-hooks"])
    assert args.install_hooks is True


def test_cli_parses_render_sync_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["render", "sync"])
    assert args.command == "render"
    assert args.render_command == "sync"
    assert args.output is None


def test_cli_parses_render_sync_with_output() -> None:
    parser = _build_parser()
    args = parser.parse_args(["render", "sync", "--output", "/tmp/pandoc.yaml"])
    assert args.output == "/tmp/pandoc.yaml"


def test_cli_parses_render_show_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["render", "show"])
    assert args.command == "render"
    assert args.render_command == "show"


def test_cli_parses_skill_new_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["skill", "new", "my-analysis"])
    assert args.command == "skill"
    assert args.skill_command == "new"
    assert args.name == "my-analysis"


def test_cli_parses_skill_list_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["skill", "list"])
    assert args.command == "skill"
    assert args.skill_command == "list"


def test_cli_parses_git_untrack_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["git", "untrack", "--dry-run"])
    assert args.command == "git"
    assert args.git_command == "untrack"
    assert args.dry_run is True


def test_cli_parses_claude_update_permissions() -> None:
    parser = _build_parser()
    args = parser.parse_args(["claude", "update-permissions", "--dry-run"])
    assert args.command == "claude"
    assert args.claude_command == "update-permissions"
    assert args.dry_run is True


def test_cli_parses_claude_permissions_sync() -> None:
    parser = _build_parser()
    args = parser.parse_args(["claude", "permissions-sync"])
    assert args.command == "claude"
    assert args.claude_command == "permissions-sync"
    assert args.dry_run is False


def test_cli_parses_mcp_config_command() -> None:
    parser = _build_parser()
    args = parser.parse_args(["mcp-config", "-C", "/tmp/repo", "--yes"])
    assert args.command == "mcp-config"
    assert args.root == "/tmp/repo"
    assert args.yes is True


def test_cli_parses_config_set_python() -> None:
    parser = _build_parser()
    args = parser.parse_args(["config", "set-python", "/path/to/python"])
    assert args.command == "config"
    assert args.config_command == "set-python"
    assert args.python_path == "/path/to/python"
    assert args.conda_env is None


def test_cli_parses_config_set_python_env() -> None:
    parser = _build_parser()
    args = parser.parse_args(["config", "set-python", "--env", "cogpy"])
    assert args.conda_env == "cogpy"
    assert args.python_path is None


def test_cli_parses_site_serve_background() -> None:
    parser = _build_parser()
    args = parser.parse_args(["site", "serve", "--background", "--port", "9000"])
    assert args.command == "site"
    assert args.site_command == "serve"
    assert args.background is True
    assert args.port == 9000


def test_cli_parses_site_stop_all() -> None:
    parser = _build_parser()
    args = parser.parse_args(["site", "stop", "--all"])
    assert args.stop_all is True


def test_cli_parses_manuscript_init() -> None:
    parser = _build_parser()
    args = parser.parse_args(["manuscript", "init", "my-paper"])
    assert args.command == "manuscript"
    assert args.manuscript_command == "init"
    assert args.name == "my-paper"
    assert args.path is None


def test_cli_parses_master_init() -> None:
    parser = _build_parser()
    args = parser.parse_args(["master", "init", "my-plan", "--sections", "intro", "methods"])
    assert args.command == "master"
    assert args.master_command == "init"
    assert args.name == "my-plan"
    assert args.sections == ["intro", "methods"]
