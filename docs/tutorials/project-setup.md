# Project Setup Workflow

This tutorial shows the intended `projio` workflow for bootstrapping a research project that publishes through DataLad.

The key design rule is:

- DataLad owns credentials, hosting-site defaults, and sibling configuration.
- `projio` owns project-local conventions, preview UX, and cross-tool bootstrap steps.

## Prerequisites

Before using the helper commands, set up stable infrastructure in DataLad and Git:

```bash
# Example global defaults
git config --global datalad.github.access-protocol ssh
git config --global datalad.gitlab-default-site lrz
git config --global datalad.gitlab-lrz-layout flat
git config --global datalad.gitlab-lrz-access ssh
git config --global datalad.gitlab-lrz-url https://gitlab.lrz.de
```

Store credentials with DataLad or your system credential helper, instead of putting tokens into `projio` config.

A practical local fallback is to export a token from a file in your shell startup, for example:

```bash
export DATALAD_GITHUB_TOKEN="$(cat ~/.config/tokens/github)"
```

That is still better than storing the token in `.projio/config.yml`, because the secret remains outside project config and can be reused by native DataLad commands.

## 1. Initialize the project workspace

Inside a project repository:

```bash
projio init .
```

Or choose a thin project kind:

```bash
projio init . --kind tool
projio init . --kind study
```

This creates:

- `.projio/config.yml`
- `.projio/projio.mk`
- `Makefile`
- `.gitignore` with a managed `projio` section
- `docs/index.md`

If the repository does not already look like a Sphinx or Vite/React frontend project, `projio` also writes `mkdocs.yml` and sets `site.framework: mkdocs`.

`tool` adds a light Python package scaffold:

- `pyproject.toml`
- `src/<repo_slug>/__init__.py`
- `tests/`

`study` stays close to the generic scaffold and only adds a minimal study-oriented starter doc.

The scaffolded `helpers:` section should stay project-local. Use it for naming conventions and templates, not secrets.

If you use VS Code and expect large static outputs, initialize with:

```bash
projio init . --vscode
```

This writes `.vscode/settings.json` excludes for `site/`.

If the repo will publish through GitHub Pages, also scaffold the workflow:

```bash
projio init . --github-pages
```

This writes `.github/workflows/docs.yml` with framework-specific build and artifact settings.

If you want cross-project defaults for your account, scaffold a user config once:

```bash
projio config init-user
```

This writes `~/.config/projio/config.yml`. You can then keep lab or personal defaults there and only put project-specific overrides into `.projio/config.yml`.

The generated `Makefile` gives you short aliases for common project plumbing, for example:

```bash
make projio-status
make projio-auth
make projio-gh
make projio-gl
make projio-ria
```

Example:

```yaml
helpers:
  sibling:
    github:
      sibling: github
      credential: github
      project_template: "{project_name}"
    gitlab:
      sibling: gitlab
      credential: gitlab-lrz
      project_template: "sirotalab/{project_name}"
    ria:
      sibling: origin
      alias_strategy: basename
      storage_url: ria+file:///storage/share/git/ria-store
      shared: group
```

## 2. Check infrastructure state

Run:

```bash
projio auth -C . doctor
```

This reports the DataLad/Git state that the helpers will use:

- GitHub access protocol from Git config
- GitLab default site and site-specific config
- configured git remotes
- `remote.<name>.datalad-publish-depends`
- RIA storage URL from project or user `projio` config

If this output is incomplete, fix DataLad or Git config first. Do not work around missing host configuration by expanding `projio` into a parallel credential store.

To inspect the merged result of user defaults plus project overrides, run:

```bash
projio config -C . show
```

## 3. Preview sibling creation

`projio` is preview-first. Start by checking the command it plans to run:

```bash
projio sibling -C . github
projio sibling -C . gitlab
projio sibling -C . ria
```

The helpers derive dataset-specific values from the current repository and `.projio/config.yml`, while stable host settings come from DataLad config. Credential names such as `github` or `gitlab-lrz` can safely live in `.projio/config.yml`; the actual secret should still live in DataLad's credential store or in a local environment-variable workflow such as `DATALAD_GITHUB_TOKEN` exported from a file.

Typical overrides:

```bash
projio sibling -C . github --project my-explicit-repo
projio sibling -C . gitlab --project sirotalab/my-explicit-repo
projio sibling -C . ria --alias mydataset
```

## 4. Execute when the preview looks right

When the planned command is correct, rerun it with `--yes`:

```bash
projio sibling -C . github --yes
projio sibling -C . gitlab --yes
projio sibling -C . ria --yes
```

This keeps `projio` as a thin orchestration layer over native DataLad commands.

## 5. Set up docs

To scaffold docs files without touching sibling configuration:

```bash
projio docs -C . mkdocs-init
```

Then build or serve the site:

```bash
projio site build -C .
projio site serve -C .
```

`projio site` explicitly handles three site cases: MkDocs, Sphinx, and Vite-based React frontends.

If the project uses `indexio` chat and MkDocs, enable this in `.projio/config.yml`:

```yaml
site:
  chatbot:
    enabled: true
```

For `projio site serve`, this is enough for a local preview: `projio` will auto-start the `indexio` chat backend and inject the widget into the served site.

For `projio site build`, also set:

```yaml
site:
  chatbot:
    backend_url: "https://your-chat-host.example"
```

so the built static site knows where the deployed chatbot server lives.

## 6. Recommended mental model

Use this split consistently:

- Put secrets, GitLab site definitions, transport defaults, and publish dependencies in DataLad, Git config, or local shell environment setup.
- Put project naming templates, preferred sibling names, credential names, and RIA alias conventions in `.projio/config.yml`.
- Use `projio` to preview, validate, and compose commands across Datalad and docs setup.

If a new feature starts duplicating DataLad config semantics, it likely belongs in DataLad config instead of `projio`.
