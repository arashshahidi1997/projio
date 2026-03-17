# Site & Docs Workflow

This tutorial shows how to use projio's site tools to detect, serve, and manage documentation sites — including the indexio chatbot integration and GitHub Pages deployment.

## Prerequisites

- A projio workspace (`projio init .`)
- MkDocs installed (`pip install "projio[docs]"`)
- MCP server configured

## Step 1: Detect the documentation framework

Ask the agent what site framework is in use:

````
You: What documentation framework does this project use?
````

The agent calls `site_detect()`:

```json
{
  "framework": "mkdocs",
  "config_file": "mkdocs.yml",
  "site_name": "my-project",
  "build_dir": "site/"
}
```

projio detects three frameworks:

| Framework | Detected by |
|-----------|-------------|
| MkDocs | `mkdocs.yml` |
| Sphinx | `conf.py` |
| Vite/React | `vite.config.*` |

## Step 2: Serve documentation locally

````
You: Start the docs server.
````

The agent calls `site_serve()`:

```json
{
  "framework": "mkdocs",
  "url": "http://127.0.0.1:8000",
  "pid": 12345,
  "port": 8000
}
```

The server runs in the background. To use a specific port:

```json
site_serve(port=8080)
```

### With chatbot integration

If you have indexio configured and `site.chatbot.enabled: true` in `.projio/config.yml`:

```yaml
# .projio/config.yml
site:
  chatbot:
    enabled: true
```

`projio site serve` auto-starts an indexio chat backend and injects the widget into the served MkDocs site. This gives your documentation a searchable chatbot powered by your project's indexed corpus.

## Step 3: List running servers

````
You: What doc servers are running?
````

The agent calls `site_list()`:

```json
{
  "servers": [
    {"framework": "mkdocs", "port": 8000, "pid": 12345, "url": "http://127.0.0.1:8000"}
  ]
}
```

## Step 4: Stop a server

````
You: Stop the docs server on port 8000.
````

The agent calls `site_stop(port=8000)`:

```json
{
  "stopped": true,
  "port": 8000,
  "pid": 12345
}
```

## CLI equivalents

All site operations are also available from the command line:

```bash
projio site build -C .     # build static site
projio site serve -C .     # start dev server
```

And via Make targets:

```bash
make docs                  # mkdocs build --strict
make docs-serve            # mkdocs serve
```

## GitHub Pages deployment

### Scaffold the workflow

```bash
projio init . --github-pages
```

This writes `.github/workflows/docs.yml` with framework-specific build and deploy steps.

### Manual setup

For MkDocs projects, a typical GitHub Actions workflow:

```yaml
name: docs
on:
  push:
    branches: [master]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install "projio[docs]"
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/
      - uses: actions/deploy-pages@v4
```

### Chatbot in production

For deployed sites with chatbot, set the backend URL:

```yaml
# .projio/config.yml
site:
  chatbot:
    enabled: true
    backend_url: "https://your-chat-host.example"
```

The built static site will point to the deployed indexio chat backend instead of localhost.

## Worklog integration

In the worklog pipeline, site tools support:

- **Run reports** — agent results can be published to the project site
- **Documentation updates** — agents can trigger site rebuilds after creating or updating notes
- **Status dashboards** — serve documentation that includes generated task indexes and progress summaries

## Next steps

- [Ecosystem Overview](ecosystem-overview.md) — full setup walkthrough
- [Agent Orchestration](agent-orchestration.md) — multi-tool agent sessions
