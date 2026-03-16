# Projio VS Code Extension

A thin VS Code client for projio workspaces. This extension provides IDE integration over the core projio system — it does not replicate projio logic in TypeScript.

## Local Development

```bash
cd editors/vscode
npm install
npm run compile
```

Then open `editors/vscode/` in VS Code and press **F5** to launch the Extension Development Host.

## Commands

| Command | Palette title | Description |
|---------|--------------|-------------|
| `projio.hello` | Projio: Hello | Greeting / smoke test |
| `projio.detectWorkspace` | Projio: Detect Workspace | Check if the open folder is a projio project |
| `projio.showStatus` | Projio: Show Status | Show workspace info in a document |

## Architecture

Core projio logic stays in the Python package (`src/projio/`). This extension is a UI shell that detects workspace state and will eventually connect to the projio MCP server for richer interactions.
