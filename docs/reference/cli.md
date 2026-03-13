# CLI

## Command groups

| Group | Purpose |
|-------|---------|
| `projio init` | Scaffold `.projio/` workspace files |
| `projio status` | Show project, index, and git status |
| `projio url` | Print clickable remote and Pages URLs |
| `projio config` | Manage projio config files |
| `projio site` | MkDocs, Sphinx, and Vite/React frontend site workflows |
| `projio sibling` | Manage DataLad siblings |
| `projio docs` | Project docs helpers |
| `projio auth` | Authentication diagnostics |
| `projio mcp` | Start the FastMCP server (stdio) |

## Key commands

```bash
# workspace
projio init .
projio init . --kind tool
projio init . --kind study
projio init . --vscode
projio init . --github-pages
projio init . --force

# config
projio config init-user
projio config init-user --force
projio config -C . show

# status
projio status -C .

# urls
projio url -C .

# site
projio site build -C .
projio site build -C . --strict
projio site serve -C .
projio site build -C . --framework sphinx
projio site serve -C . --framework vite
projio site publish -C .

# docs
projio docs -C . mkdocs-init
projio docs -C . mkdocs-init --force

# siblings (preview-first, add --yes to execute)
projio sibling -C . github
projio sibling -C . github --project my-repo --yes
projio sibling -C . gitlab
projio sibling -C . gitlab --project sirotalab/my-repo --yes
projio sibling -C . ria
projio sibling -C . ria --alias mydataset --yes

# auth
projio auth -C . doctor

# mcp
projio mcp -C .
```

`projio init --vscode` writes `.vscode/settings.json` with excludes for `site/` so search and watchers stay usable after a build.

`projio init --github-pages` writes `.github/workflows/docs.yml` so GitHub Pages deployment works with the detected MkDocs, Sphinx, or Vite site layout.

For MkDocs projects with `site.chatbot.enabled: true`, `projio site serve` also starts a local `indexio` chat backend and injects the widget into the served site.

## Global options

Most subcommands accept `-C` / `--root` to specify the project root directory (default: `.`).

## Sibling options

### `projio sibling github`

| Flag | Description |
|------|-------------|
| `--project` | Target GitHub repo name |
| `--sibling` | Sibling name |
| `--credential` | DataLad credential name |
| `--access-protocol` | GitHub access protocol |
| `--yes` | Execute instead of preview |

### `projio sibling gitlab`

| Flag | Description |
|------|-------------|
| `--project` | Target GitLab project path |
| `--sibling` | Sibling name |
| `--site` | GitLab site profile |
| `--layout` | GitLab layout |
| `--access` | GitLab access mode |
| `--credential` | DataLad credential name |
| `--yes` | Execute instead of preview |

### `projio sibling ria`

| Flag | Description |
|------|-------------|
| `--sibling` | Sibling name |
| `--alias` | RIA alias |
| `--storage-url` | RIA storage URL |
| `--shared` | RIA shared mode |
| `--yes` | Execute instead of preview |
