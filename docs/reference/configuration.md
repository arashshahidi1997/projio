# Configuration

## Config files

| File | Purpose |
|------|---------|
| `.projio/config.yml` | Project-level configuration (required) |
| `~/.config/projio/config.yml` | User-level defaults (optional) |

User config is merged with project config using deep merge. Project values take precedence.

The user config path respects `XDG_CONFIG_HOME`.

## Config schema

```yaml
project_name: my-project
project_kind: generic     # generic | tool | study
description: ""

indexio:
  config: .indexio/config.yaml
  persist_dir: .projio/index

biblio:
  enabled: true
  config: bib/config/biblio.yml

notio:
  enabled: true
  notes_dir: notes/

codio:
  enabled: true
  catalog_path: .codio/catalog.yml
  profiles_path: .codio/profiles.yml
  notes_dir: docs/reference/codelib/libraries/

site:
  base_port: 8000
  host: "127.0.0.1"
  chatbot:
    enabled: false
    backend_url: null
    host: "127.0.0.1"
    port: 9100
    title: "Docs Assistant"
    storage_key: "my-project_chat_v1"

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
      storage_url: ria+file:///path/to/ria-store
      shared: group
  docs:
    mkdocs:
      enabled: false
```

## Ecosystem sections

Each ecosystem package has a top-level section (`indexio`, `biblio`, `notio`, `codio`) with an `enabled` flag. Setting `enabled: false` prevents that subsystem's MCP tools from being registered.

## Helper config

The `helpers.sibling` section provides defaults for `projio sibling` commands. Values here are used when CLI flags are not provided.

Credential names (e.g., `github`, `gitlab-lrz`) can safely live in `.projio/config.yml`. Actual secrets should remain in DataLad's credential store or environment variables.

## Site chatbot config

`site.chatbot` controls whether `projio site build` / `projio site serve` inject the `indexio` chatbot widget into supported site frameworks.

- `enabled: true` turns the integration on
- for `projio site serve`, MkDocs sites can auto-start an `indexio` backend locally if `backend_url` is unset
- for `projio site build`, set `backend_url` to the deployed chatbot server URL if you want the static site to include the widget
- MkDocs is supported in this first pass; Sphinx and Vite are not yet wired
