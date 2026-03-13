# Build the Documentation Site

`projio site` handles three explicit site cases:

- `mkdocs`
- `sphinx`
- `vite` for a React frontend

## Build

```bash
projio site build -C .
```

Build with strict mode (fail on warnings):

```bash
projio site build -C . --strict
```

Override framework detection when needed:

```bash
projio site build -C . --framework mkdocs
projio site build -C . --framework sphinx
projio site build -C . --framework vite
```

## Serve locally

```bash
projio site serve -C .
```

For MkDocs projects, `projio` can also inject the `indexio` chatbot widget and auto-start a local chatbot backend when `.projio/config.yml` contains:

```yaml
site:
  chatbot:
    enabled: true
```

For static site builds, also set `site.chatbot.backend_url` to the deployed chatbot server URL if you want the built site to include the widget.

For Vite projects, `projio` builds into `site/` by default so the generated static output lines up with the managed `.gitignore` and VS Code excludes.

If you also want GitHub Actions deployment, scaffold the Pages workflow once:

```bash
projio init . --github-pages
```

## Publish to GitHub Pages

```bash
projio site publish -C .
```

This runs `mkdocs gh-deploy` to push the built site to the `gh-pages` branch.

## Scaffold MkDocs files

If your project does not yet have MkDocs config:

```bash
projio docs -C . mkdocs-init
```
