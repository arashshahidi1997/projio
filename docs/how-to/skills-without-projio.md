# Use projio's skills without projio

A few of projio's skills work in any git project. They are shared as a Claude Code
plugin, so friends, colleagues and students can use them without installing projio,
its MCP server or its packages. They need git and Python 3.9 or later.

| Plugin | Skills | What they do |
|---|---|---|
| `projio-workflow` | `project-manager`, `manager-setup`, `session-wrap`, `always-complete` | A standing manager session that tracks incoming notes, running sessions, handoffs and what to start next; its setup in a new project; a session wrap that commits by path and writes a handoff; and the "always complete, never finished" check |

## Install

In Claude Code, add projio's marketplace once, then install the plugin:

```text
/plugin marketplace add arashshahidi1997/projio
/plugin install projio-workflow@projio
```

On Claude Code 2.1.275 or later one line does both:
`/plugin install projio-workflow --marketplace arashshahidi1997/projio`.

Then, in a project, ask for "set up a manager" (`manager-setup`), "wrap up"
(`session-wrap`) or type `/always-complete`. Without projio the skills use plain
files: the manager config is `.claude/manager.yml` and handoffs are Markdown files
in the handoff folder. Each skill has a "projio or not" table that maps every
projio step to its plain equivalent.

## Updates

The plugin is versioned with projio, and Claude Code installs a plugin version
once and keeps it. A new projio release bumps the version; to get it, refresh the
marketplace and update the plugin:

```text
/plugin marketplace update projio
```

then update `projio-workflow` from the `/plugin` menu (Installed tab). To get
updates at startup, turn on auto-update for the `projio` marketplace in the
`/plugin` menu (Marketplaces tab); it is off by default for marketplaces other
than Anthropic's.

## For maintainers

`.claude-plugin/marketplace.json` at the repository root lists the plugin. It is
a non-strict plugin with `source: "./"`, so the skills are served from
`src/projio/data/skills/` with no copies, and `mcpServers: {}` keeps the
repository's own `.mcp.json` out of the plugin. A skill is shared when it carries
`metadata.portable: true` in its frontmatter; `tests/test_marketplace.py` checks
that the marketplace lists exactly those skills, that the version matches
`pyproject.toml`, and that a portable skill requires no projio MCP tool (its
`tooling.mcp` entries are `optional: true`), runs no `projio` command in a code
block and has helpers that import only the standard library. Check the manifest
with `claude plugin validate .`.
