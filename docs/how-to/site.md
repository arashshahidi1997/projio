# Build the Documentation Site

## Build

```bash
projio site build -C .
```

Build with strict mode (fail on warnings):

```bash
projio site build -C . --strict
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
