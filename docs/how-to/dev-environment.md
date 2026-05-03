# Set up a projio dev environment

Goal: from a fresh clone, get to a working `projio --help`, a queryable
MCP server, and live-rendered Excalidraw diagrams — without polluting
your home directory.

The recipe assumes Linux. macOS works for the `default`/`dev` envs but
the `full` env (datalad + git-annex) is linux-only on conda-forge.

## Pixi for project work

[pixi](https://pixi.sh) handles the project-level workspace: editable
installs of projio + every subpackage, dev tools (pytest, build),
pandoc, and the Snakemake/marimo runners that pipeio shells out to.

```bash
git clone --recurse-submodules https://github.com/arashshahidi1997/projio.git
cd projio
pixi install -e dev            # install projio + 6 subpackages + dev tools
pixi run -e dev test           # ~5 min full test suite
pixi run docs                  # mkdocs build --strict
```

After this, the dev env lives at `.pixi/envs/dev/` inside the repo.
`pixi run` activates it transparently for any task; you don't need to
`pixi shell` unless you want a fully-activated subshell.

### Off-home pixi global tools

For tools you want **everywhere** (datalad, mkdocs, pandoc, quarto),
not just inside one project, use **pixi global** with
`PIXI_HOME=/storage2/<you>/.pixi` (or any non-home path) so the env
trees stay off NFS:

```bash
echo 'export PIXI_HOME=/storage2/<you>/.pixi' >> ~/.bashrc
pixi global install datalad
pixi global install quarto      # pulls pandoc as a dep
```

The `find_pandoc()` helper in `notio.present` falls back to
`~/.pixi/bin/pandoc` when `shutil.which` fails, so MCP servers and
hooks resolve pandoc correctly even when their parent shell didn't
source `.bashrc`.

## uv tool for editable global CLIs

The `projio` CLI itself needs to be on `PATH` from any directory, but
**editable** so source edits take effect immediately. Pixi global doesn't
support editable PyPI installs in 0.67; uv tool does.

```bash
export UV_TOOL_DIR=/storage2/<you>/.uv-tools           # off-home
uv tool install --editable /path/to/projio \
  --with-editable /path/to/projio/packages/indexio \
  --with-editable /path/to/projio/packages/biblio \
  --with-editable /path/to/projio/packages/notio \
  --with-editable /path/to/projio/packages/codio \
  --with-editable /path/to/projio/packages/figio \
  --with-editable /path/to/projio/packages/pipeio \
  --with mkdocs --with mkdocs-material --with mkdocs-monorepo-plugin \
  --with mkdocs-ezlinks-plugin --with mkdocs-bibtex \
  --with-executables-from "notio,biblio-tools,codio-tools,figio-tools,indexio,pipeio"
```

Result: `projio`, `notio`, `biblio`, `codio`, `figio`, `indexio`,
`pipeio` (and their helper subcommands) all on `PATH`, all editable
against the local checkout. Run from `cd /tmp` and `projio status -C
/path/to/your-project` works.

To refresh after a `pyproject.toml` change, re-run with `--force`. Source
edits don't need a refresh — they're live.

## Self-hosted Excalidraw for diagrams

Projio's docs and decks embed hand-drawn diagrams via SVGs in
`docs/assets/excalidraw/`. To author or refine them locally:

1. Build Excalidraw once on a machine with Node ≥ 18:

   ```bash
   cd /storage2/<you>/infra/third_party
   git clone --depth 1 https://github.com/excalidraw/excalidraw.git
   cd excalidraw
   corepack enable --install-directory ~/.local/bin
   ~/.local/bin/yarn install
   ~/.local/bin/yarn build
   ```

2. Serve in a `screen` (or `tmux`) session for persistence:

   ```bash
   screen -dmS excalidraw bash -c \
     "cd /storage2/<you>/infra/third_party/excalidraw/excalidraw-app/build && \
      npx -y serve -l 5000 . 2>&1 | tee /tmp/excalidraw.log"
   ```

3. Browse to `http://<host>:5000` from any lab machine. Same UI as
   excalidraw.com, fully local.

For batch SVG export from `.excalidraw` JSON sources, use
`@swiftlysingh/excalidraw-cli`:

```bash
cd docs/assets/excalidraw
for f in *.excalidraw; do
  npx -y @swiftlysingh/excalidraw-cli convert "$f" --format svg -o "${f}.svg"
done
```

The `<!-- svg-source:excalidraw -->` watermark in each output confirms
the official Excalidraw rendering pipeline produced the SVG.

See [docs/assets/excalidraw/README.md](https://github.com/arashshahidi1997/projio/blob/master/docs/assets/excalidraw/README.md)
for the pair-file convention (`.excalidraw` JSON source +
`.excalidraw.svg` rendered output) and embedding examples.

## Verify

```bash
projio --help                  # CLI on PATH
projio status -C /path/to/some-project   # query a project
~/.pixi/bin/pixi --version     # pixi global tools available
which pandoc                   # via pixi global quarto env or symlink
```

## Where things live

| Artifact | Path |
|---|---|
| Pixi project envs | `<repo>/.pixi/envs/{default,dev,full}/` (gitignored) |
| Pixi global envs | `$PIXI_HOME/envs/<env>/` |
| Uv tool envs | `$UV_TOOL_DIR/<tool>/` (binaries symlinked into `~/.local/bin/`) |
| Excalidraw build | `<infra>/third_party/excalidraw/excalidraw-app/build/` |
| MCP server | started by Claude Code from `.mcp.json` (one per project) |
