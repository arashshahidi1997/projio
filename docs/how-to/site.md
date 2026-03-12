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
