# projio

Project knowledge orchestrator and MCP server for research repositories.

Scaffolds `.projio/` workspaces, builds project documentation sites, and exposes a FastMCP stdio server that gives Claude unified access to indexio (semantic search), biblio (bibliography), notio (notes), and codio (code intelligence) tools — all scoped to the current project root.

## Ecosystem

- `projio`: workspace scaffold, site orchestration, MCP entrypoint
- `indexio`: semantic search and chatbot backend
- `biblio`: bibliography workflows and bibliography-first publishing
- `notio`: notes, logs, and lightweight project memory
- `codio`: code discovery and reusable library intelligence

Placeholder GitHub Pages homes:

- [projio](https://arashshahidi1997.github.io/projio/)
- [indexio](https://arashshahidi1997.github.io/indexio/)
- [biblio](https://arashshahidi1997.github.io/biblio/)
- [notio](https://arashshahidi1997.github.io/notio/)
- [codio](https://arashshahidi1997.github.io/codio/)

The docs follow the Diataxis structure:

- Tutorials: end-to-end guided paths
- How-to guides: task-focused recipes
- Explanation: design choices and concepts
- Reference: command and file layout details

Start here:

- [Quickstart](tutorials/quickstart.md)
- [Project Setup Workflow](tutorials/project-setup.md)
- [Ecosystem overview](explanation/ecosystem.md)
- [CLI reference](reference/cli.md)
- [MCP tools reference](reference/mcp-tools.md)
