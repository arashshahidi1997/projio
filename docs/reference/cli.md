# CLI

## Command groups

| Group | Purpose |
|-------|---------|
| `projio init` | Scaffold `.projio/` workspace files |
| `projio add` | Activate a package component in the workspace |
| `projio remove` | Deactivate a package component |
| `projio list` | List workspace components and their status |
| `projio status` | Show project, index, and git status |
| `projio url` | Print clickable remote and Pages URLs |
| `projio config` | Manage projio config files |
| `projio site` | MkDocs, Sphinx, and Vite/React frontend site workflows |
| `projio sibling` | Manage DataLad siblings |
| `projio docs` | Project docs helpers |
| `projio git` | Git helpers for projio-managed projects |
| `projio auth` | Authentication diagnostics |
| `projio claude` | Claude Code project settings |
| `projio skill` | Manage project skills |
| `projio mcp` | Start the FastMCP server (stdio) |
| `projio mcp-config` | Generate `.mcp.json` for Claude Code |

## Key commands

```bash
# workspace
projio init .
projio init . --kind tool
projio init . --kind study
projio init . --profile research
projio init . --profile full
projio init . --vscode
projio init . --github-pages
projio init . --force

# components
projio add biblio
projio add notio
projio add codio
projio add indexio
projio remove biblio
projio list

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

# git
projio git -C . untrack
projio git -C . untrack --dry-run

# auth
projio auth -C . doctor

# claude
projio claude -C . update-permissions
projio claude -C . update-permissions --dry-run

# skill
projio skill -C . list
projio skill -C . new my-analysis

# mcp
projio mcp -C .

# mcp-config (generate .mcp.json for Claude Code)
projio mcp-config -C .                    # preview
projio mcp-config -C . --yes              # write
projio mcp-config -C . --output path.json # custom output
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

## Component management

### `projio init`

Creates the base workspace. Does **not** activate any package components by default.

**Filesystem effects:**

```
.projio/
├── projio.yml
├── packages.yml       # empty registry
├── config.yml
└── projio.mk
```

**Options:**

| Flag | Description |
|------|-------------|
| `--kind` | Workspace kind: `generic` (default), `tool`, `study` |
| `--profile` | Activate a preset bundle of components (see below) |
| `--vscode` | Write `.vscode/settings.json` with excludes |
| `--github-pages` | Write GitHub Pages deploy workflow |
| `--gitlab-pages` | Write GitLab Pages CI config at `.gitlab-ci.yml` |
| `--force` | Overwrite existing config files |

**Profiles:**

| Profile | Components |
|---------|------------|
| `research` | notio, biblio, indexio |
| `full` | notio, biblio, codio, indexio |

`projio init --profile research` is equivalent to `projio init` followed by `projio add notio`, `projio add biblio`, `projio add indexio`.

### `projio add <package>`

Activates a package component in the current workspace.

**Preconditions:**

- `.projio/` workspace must exist (run `projio init` first)
- The package must be importable (installed in the current environment)

**Filesystem effects:**

1. Creates `.projio/<package>/` directory
2. Updates `packages.yml` to set `enabled: true` and `path: .projio/<package>`
3. If the package provides an init hook, runs it to populate the component directory

**Migration behavior:**

If a standalone directory exists (e.g., `.codio/` when adding codio), the command offers to migrate its contents to `.projio/codio/`.

### `projio remove <package>`

Deactivates a package component.

**Filesystem effects:**

1. Updates `packages.yml` to set `enabled: false` and remove `path`
2. Does **not** delete the component directory — data is preserved

To fully remove component data, delete the directory manually after `projio remove`.

### `projio config set-python`

Sets `runtime.python_bin` in the project `.projio/config.yml`.

```bash
projio config -C . set-python                      # use current interpreter
projio config -C . set-python /path/to/python      # explicit path
projio config -C . set-python --env rag            # resolve conda env name
```

This is used by `projio mcp-config` to generate the correct `.mcp.json`.

### `projio git untrack`

Untracks files in the projio gitignore block that are still tracked by git. Useful after adding `.mcp.json` or `.claude/settings.json` to `.gitignore` retroactively.

**Options:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be untracked without modifying git |

### `projio claude update-permissions`

Scopes `Edit` and `Write` tool permissions to the project root in `.claude/settings.json`. This prevents Claude Code from accidentally editing files outside the project directory.

**Options:**

| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would change without writing |

### `projio skill`

Manages project skills in `.projio/skills/`.

```bash
projio skill -C . list               # list available skills
projio skill -C . new my-analysis    # scaffold a new skill
```

Skills are markdown prompts that agents can load via `skill_read()`. The `new` subcommand creates `.projio/skills/<name>/SKILL.md` with a template.

### `projio list`

Shows the status of all known components.

**Output example:**

```
Package    Enabled   Installed   Path
biblio     yes       yes         .projio/biblio
notio      yes       yes         .projio/notio
codio      no        yes         -
indexio    yes       no          .projio/indexio
```

The `Installed` column reflects whether the package is importable in the current Python environment. A component can be enabled but not installed (projio will skip its MCP tools).
