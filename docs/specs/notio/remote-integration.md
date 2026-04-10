# Remote Platform Integration Spec

**Status:** Draft
**Date:** 2026-04-09
**Package:** `notio`

## Motivation

Notio notes live in the repo — structured, agent-queryable, integrated with
the project knowledge graph (pipeio mods, biblio citekeys, series
cross-references). GitHub/GitLab Issues live on the platform — collaborative,
visible to non-cloners, with comments, labels, assignees, milestones, and
notifications.

These are complementary surfaces of the same work items. Notio should not
replicate platform features (labels, assignment, comment threads, notifications).
Instead it should bridge the two so that:

- Agents see platform feedback without needing API access
- Collaborators and supervisors use their familiar platform UI
- The repo remains the structured, queryable record

This follows the same design philosophy as biblio ↔ Zotero: biblio is
project-centric and agent-first; Zotero is person-centric and GUI-first.
Here, notio is project-centric and agent-first; GitHub/GitLab is
platform-centric and human-first.

## Design Principles

- **Two views, one work item.** A note and a platform issue are linked, not
  synced. Each is authoritative for its own domain: the note owns structured
  context (frontmatter, refs, series); the issue owns the conversation.
- **Explicit actions, not magic sync.** Promote, capture, and pull are
  user-triggered commands. No webhooks, no always-on infrastructure.
- **Platform-agnostic.** The core model works for GitHub, GitLab, or any
  platform with an issue API. Platform-specific logic is isolated in
  adapters.
- **Agent reads, human writes.** Remote thread content flows into the note
  for agent consumption. Agents never post to the platform directly.
- **Append-only mirror.** Pulled thread content is overwritten on each pull
  (full mirror). The platform is authoritative for the conversation.

## Data Model

### The `remote` frontmatter field

A note links to a platform issue via a `remote` field:

```yaml
---
title: "pipeio docs_collect missing overview"
status: open
remote: github#42
refs: [pipeio/ecephys]
tags: [pipeio, docs]
---
```

Format: `{platform}#{number}` where platform is `github` or `gitlab`.

The platform and repo are resolved from the project's git remote origin,
not stored in the note. This keeps notes portable — if the repo moves, the
link still resolves.

### Remote thread section

When pulled, platform comments are written into a fenced section at the end
of the note:

```markdown
## Remote Thread

<!-- notio:remote-thread github#42 -->

> **@supervisor** (2026-04-09 14:30):
> The coupling metric looks off — try normalizing by session length first.

> **@collaborator** (2026-04-09 15:12):
> I ran into the same thing with the theta band. See issue #38.

<!-- /notio:remote-thread -->
```

Design choices:

- **Full mirror, not incremental.** The entire thread between the markers is
  replaced on each pull. This is idempotent and avoids merge conflicts.
- **Blockquote format.** Each comment is a blockquote with author and
  timestamp. Agents can parse this; MkDocs renders it cleanly.
- **HTML markers.** The `<!-- notio:remote-thread -->` markers delimit the
  managed section. Content outside the markers is never touched.
- **No local annotations inside the thread.** If you want to annotate a
  comment, do it outside the markers (e.g. in a Notes section above).

## Operations

### `notio promote`

Promotes a local note to a platform issue.

```bash
notio promote docs/log/issue/issue-arash-20260409-034440.md
```

Behavior:

1. Reads the note title, body, and tags
2. Creates a platform issue via API (`gh issue create` / `glab issue create`)
3. Writes the `remote: github#42` field back into the note frontmatter
4. Adds a backlink in the issue body: `_Tracked in repo: docs/log/issue/issue-arash-20260409-034440.md_`

Options:

| Flag | Effect |
|------|--------|
| `--labels` | Override label mapping (default: note tags → issue labels) |
| `--assignee` | Set assignee on the platform issue |
| `--milestone` | Set milestone on the platform issue |
| `--dry-run` | Print what would be created without calling the API |

Only notes without an existing `remote` field can be promoted. Attempting to
promote a linked note is an error.

### `notio capture`

Creates a local note from a platform issue.

```bash
notio capture github#42
notio capture gitlab#15 --type issue
```

Behavior:

1. Fetches the issue via API
2. Creates a note of the specified type (default: `issue`)
3. Maps issue labels → note tags, issue body → note body
4. Sets `remote: github#42` in frontmatter
5. Pulls the comment thread into the Remote Thread section
6. Rebuilds the type index

Options:

| Flag | Effect |
|------|--------|
| `--type` | Note type to create (default: `issue`) |
| `--owner` | Override note owner (default: git user) |

Capturing an issue that already has a linked note is an error (prints the
existing note path).

### `notio pull`

Fetches remote thread updates for linked notes.

```bash
notio pull docs/log/issue/issue-arash-20260409-034440.md
notio pull --all
notio pull --type issue
```

Behavior:

1. Finds notes with a `remote` field (scoped by path, type, or `--all`)
2. For each, fetches the issue comment thread via API
3. Replaces the Remote Thread section (between markers) with the current
   thread
4. Reports: `Updated 3 notes (2 new comments)`

Options:

| Flag | Effect |
|------|--------|
| `--all` | Pull all linked notes across all types |
| `--type` | Pull all linked notes of a specific type |
| `--dry-run` | Show what would be updated without writing |

Pull is idempotent — running it twice with no new comments produces no diff.

### `notio remote-status`

Shows the link status of notes.

```bash
notio remote-status
```

Output:

```
issue   issue-arash-20260409-034440.md   github#42   3 comments (last: 2026-04-09)
issue   issue-arash-20260408-191633.md   (no remote)
task    task-arash-20260409-034513.md     github#55   1 comment  (last: 2026-04-08)
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `note_promote` | Promote a note to a platform issue |
| `note_capture` | Create a note from a platform issue |
| `note_pull` | Fetch remote thread updates |
| `note_remote_status` | List linked notes and thread freshness |

These tools allow agents to trigger pulls before processing feedback, or to
promote notes when a task needs human input. The agent never posts comments
itself — it reads the thread and acts on it.

## Authentication

Uses existing platform CLI tools — no separate token management:

| Platform | CLI | Auth |
|----------|-----|------|
| GitHub | `gh` | `gh auth login` (already configured for push) |
| GitLab | `glab` | `glab auth login` or `GITLAB_TOKEN` env var |

Platform is auto-detected from the git remote URL. If both remotes exist,
the `remote.platform` config key in `.projio/config.yml` disambiguates:

```yaml
remote:
  platform: github    # or gitlab
```

## Card Feed Integration

Linked notes render the remote reference as a chip in the card metadata:

```markdown
<small>**status:** open · **remote:** [github#42](https://github.com/user/repo/issues/42) · **tags:** pipeio, docs</small>
```

This makes the platform issue one click away from the MkDocs log page.

## What This Does NOT Do

- **No bidirectional status sync.** Closing a GitHub issue does not auto-close
  the note, and vice versa. Status is managed independently in each surface.
  If they drift, `notio pull` still works — the thread keeps flowing.
- **No comment posting.** Agents read platform feedback but never write to the
  platform. Human collaboration happens on the platform; agent work happens
  in the repo.
- **No webhook server.** All sync is pull-based and explicit. Can be run
  manually, in CI, or as a pre-session step.
- **No label/milestone sync.** Platform labels and note tags may diverge.
  This is acceptable — they serve different audiences.
- **No attachment sync.** Platform issue attachments (images, files) are not
  pulled. The thread section contains text only.

## Implementation Phases

### Phase 0: Frontmatter + card rendering

- Add `remote` to recognized frontmatter fields
- Render `remote` as a clickable chip in `_note_card()`
- No API calls, no CLI commands

### Phase 1: Promote + capture (CLI + MCP)

- `notio promote` and `notio capture` commands
- Platform adapter for GitHub (`gh` CLI)
- MCP tools: `note_promote`, `note_capture`

### Phase 2: Pull (CLI + MCP)

- `notio pull` command with thread mirroring
- `notio remote-status` command
- MCP tools: `note_pull`, `note_remote_status`

### Phase 3: GitLab adapter

- Platform adapter for GitLab (`glab` CLI)
- Auto-detection from git remote URL

## Workflow Example

```
Supervisor workflow:
1. Agent creates issue note during investigation
2. Agent promotes note → GitHub issue appears
3. Supervisor comments on GitHub issue from phone
4. Next session: agent runs notio pull → sees feedback in note
5. Agent acts on feedback, updates note status

Collaborator workflow:
1. Collaborator opens GitHub issue about a bug
2. Agent runs notio capture github#42 → local note created
3. Agent links note to pipeio mod via refs, investigates
4. Collaborator adds more context on GitHub
5. notio pull → agent sees update, continues work
```
