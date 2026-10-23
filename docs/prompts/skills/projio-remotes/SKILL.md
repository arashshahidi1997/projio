---
name: projio-remotes
description: >
  Set up and use a project's remotes: check the workspace and credentials,
  create DataLad siblings (RIA store for annexed data, GitHub or GitLab for
  the git history) with the preview-first `projio sibling` commands, wire
  publish dependencies so annexed files land in the store, then save and
  push routinely. Use when asked to "set up remotes", "put this on GitHub",
  "add a RIA sibling", "why did push not upload the PDFs", or before the
  first push of a new project.
metadata:
  short-description: Check auth -> RIA + GitHub/GitLab siblings (preview, then --yes) -> publish-depends -> save/push
  tags: [datalad, remotes, siblings, setup, workspace]
  tooling:
    cli: [projio auth doctor, projio sibling ria, projio sibling github, projio sibling gitlab, projio status, datalad siblings, datalad save, datalad push]
    mcp:
      - server: projio
        tools: [datalad_status, datalad_siblings, datalad_save, datalad_push]
---

# Project remotes

A projio project is a DataLad dataset: git history plus annexed files (PDFs,
data, figures). Git hosts (GitHub, GitLab) take the history only; annexed
content needs a store that holds it, the lab's RIA store. The usual setup is
one RIA sibling (`origin`) and one git host, with the git host depending on
the store so one push sends both.

## When to use

- A new project before its first push, or one that lacks a remote.
- A push that "worked" but collaborators cannot `datalad get` files (no
  publish dependency, or no store).
- Routine save and push at the end of a session.

Not for creating the workspace itself (`projio init`, see `projio-orient`).

## Workflow

1. **Look first.** `projio status -C .` and `projio auth -C . doctor`
   (GitHub protocol, GitLab site, remotes with their publish-depends, the RIA
   storage URL), then `datalad siblings` (or `datalad_siblings()`). Report
   what exists before proposing anything.

2. **Decide with the user** which remotes this project needs:
   - the RIA store (`helpers.sibling.ria.storage_url` in `.projio/config.yml`)
     for any project with annexed content: lab work, papers, data;
   - GitHub for code or public projects; GitLab (`helpers.sibling.gitlab`,
     e.g. LRZ) for lab-internal ones.
   Names come from `helpers.sibling.*` (default `origin` for RIA, `github`,
   `gitlab`).

3. **Preview, then create.** Every sibling command shows the `datalad`
   command it would run and does nothing without `--yes`:

   ```bash
   projio sibling -C . ria                 # preview: store, alias, shared mode
   projio sibling -C . github              # preview: repo name, protocol, credential
   ```

   Show the previews to the user. Creating a GitHub or GitLab repository is
   outward-facing: run the `--yes` form only after the user agrees, RIA
   first, then the git host. An alias that already exists in the RIA store
   stops the command; never pass `--force-alias` without the user.

4. **Wire the publish dependency** so pushing to the git host also sends
   annexed files to the store:

   ```bash
   datalad siblings configure -s github --publish-depends origin
   ```

   Check it with `projio auth -C . doctor` (`publish-depends=origin`).

5. **First push.** `datalad push --to github` (or `datalad_push(sibling=
   "github")`). Report what went where: git to the host, annexed files to
   the store.

6. **Routine.** `datalad save -m "<what changed>"` (or `datalad_save`), then
   `datalad push --to <host>`. Subdatasets (`packages/*`) are saved first,
   with `datalad save -r` from the superdataset when they changed.

## Hard rules

- Never put a token or password in `.projio/config.yml` or any tracked file;
  credentials live in DataLad's credential store or the environment
  (`projio auth doctor` shows where each one resolves from).
- No `--yes` on a command that creates a remote repository without the
  user's go-ahead; no force pushes.
- DataLad runs as the bare `datalad` on PATH (pixi global or uv tool
  install), not through a conda env.
- Do not delete or rename siblings to "fix" a push; report and ask.
