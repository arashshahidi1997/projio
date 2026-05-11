# Siblings and RIA stores

**Status:** draft

!!! note "Sources & anchors"
    - **Stack component:** DataLad
    - **Canonical artifact:** survey component 2 §Convergent patterns RIA layout
    - **Workshop session:** Day-1 AM session 2 (DataLad)
    - **Outline:** [`_outline.md`](../_outline.md) §B

## Frame

A DataLad dataset can push to and pull from multiple named remotes — siblings
— each playing a different role: a RIA store for content, GitHub for metadata
and discoverability, a GitLab Pages target for publication. This chapter covers
how siblings work, how RIA stores are structured, and what projio's helper
layer adds.

## What a sibling is

A DataLad **sibling** extends the git concept of a remote to cover annex
content. Where a bare git remote stores commits and trees, a DataLad sibling
stores commits, trees, *and* annexed file content — or a subset of it. Every
subdataset can have multiple siblings with different purposes. Each sibling has
a name (`origin`, `ria-store`, `github`) and its own push/pull semantics.

Adding a sibling is one command:

```bash
datalad siblings add \
    -d . \
    --name ria-store \
    --url "ria+file:///storage2/ria-store" \
    --pushurl "ria+file:///storage2/ria-store"
```

The `--url` is used for fetching; `--pushurl` is used for writing. For a
local RIA store the two are identical. For a remote SSH sibling they may
differ — SSH for writes, HTTPS for reads.

## RIA stores: structure and access

RIA (Remote Indexed Archive) is DataLad's content-addressed object store. A
RIA store is a directory organized as a two-level hash tree
(`ab/cde.../objects/...`) where objects are stored by dataset ID and content
hash. The store supports two protocols:

- `ria+file:///path/to/store` — local filesystem access, no network overhead
- `ria+ssh://user@host/path/to/store` — SSH access to a remote host

Both protocols are transparent to DataLad. The `datalad push --to ria-store`
command is identical whether the store is local or remote.

A RIA store contains **aliases** — named pointers to datasets inside the store,
recorded in `store/alias/`. The `#~cogpy` fragment in a `datalad-url` resolves
through the alias table: `ria+file:///storage/share/git/ria-store#~cogpy` finds
the cogpy dataset regardless of where it lives inside the store's hash tree.
Aliases let multiple superdatasets share a stable reference to a library without
coupling to its internal storage layout.

The pattern across study projects: a **project-local** store at
`/storage2/ria-store/` holds all study-specific subdatasets for that project;
a **shared lab store** at `/storage/share/git/ria-store/` holds code libraries
that multiple projects consume. gecog's `.gitmodules` makes this split explicit —
each `datalad-url` field distinguishes project-local from lab-shared by the
store path.

## GitHub and GitLab siblings: metadata, not content

GitHub does not support the git-annex protocol and has a 100 MB file-size
limit. A GitHub sibling therefore holds metadata only: commit history, directory
layout, scripts, configs, YAML, notes. Adding one follows the standard DataLad
flow:

```bash
# Register the sibling
datalad siblings add --name github --url git@github.com:org/repo.git

# Push metadata only (no annex content)
datalad push --to github --data nothing
```

A collaborator who clones from GitHub gets the full git history and directory
structure but hollow symlinks for all annexed files. Running
`datalad get raw/sub-01/` against the RIA sibling fills the content. The two
siblings are complementary: GitHub for sharing and browsing; RIA store for
data.

GitLab siblings follow the same model. A GitLab Pages target can additionally
serve static site outputs from the `docs/` tree when triggered by CI.

## The push vs publish asymmetry

- **`datalad push --to <sibling>`** sends both git metadata and annex content.
  Use this for full data sync to a RIA store or any content-capable remote.

- **`datalad push --to <sibling> --data nothing`** sends only git metadata —
  commits, trees, notes, configs. Use this for GitHub/GitLab remotes that
  should be human-readable mirrors without becoming data stores.

In practice: push `--to ria-store` nightly or after each pipeline run; push
`--to github --data nothing` for discoverability and audit. Both are one-command
operations from the superdataset root. The asymmetry is invisible in day-to-day
use once siblings are configured, but understanding it matters when planning
backup and sharing strategy.

## Preview-first sibling helpers in projio

projio's `src/projio/helpers/` provides thin wrappers for provisioning GitHub,
GitLab, and RIA siblings. All helpers follow a **preview-first contract**: they
print the command they would run and require `--yes` to actually execute. This
prevents mistakes before they register a sibling at the wrong path or with
wrong permissions.

The MCP tool `datalad_siblings()` (exposed as `mcp__projio__datalad_siblings`)
returns the current sibling list for a dataset. Because DataLad commands must
run in the `labpy` conda environment (where git-annex lives), projio's tools
wrap the invocation rather than calling DataLad bare. The memory entry
`feedback_datalad_conda_wrap.md` captures this convention: bare `conda datalad`
without `conda run` fails silently.

## Permissions sync

`permissions_sync()` in projio reconciles `.claude/settings.json` tool
permissions for a project's known siblings and subdatasets. This is separate
from DataLad's own access control: DataLad controls who can push to a sibling;
projio controls which MCP tools and Bash patterns the agent is allowed to
execute. The overlap is in sibling management — adding a new sibling should
also update the agent's allow-list so `datalad push --to <new-sibling>` is
pre-approved in the project's `.claude/settings.json`. The honest state:
permissions sync is a helper tool, not a guarantee; the user must review and
commit the resulting settings changes.

## Further reading

- **[DataLad handbook](https://handbook.datalad.org/)** — covers `datalad push`, sibling setup, SSH and GitHub/GitLab configurations; RIA store creation and usage.
- **[git-annex special remotes](https://git-annex.branchable.com/special_remotes/)** — the protocol layer underlying DataLad siblings, including `ria+file://` and `ria+ssh://` transports.
