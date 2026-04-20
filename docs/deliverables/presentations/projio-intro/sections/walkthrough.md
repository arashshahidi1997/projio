---
title: "Walkthrough"
order: 50
deck: projio-intro
status: draft
tags: [presentation, section]
---

# Walkthrough

From plain repo to MCP-queryable project in three commands.

---

## 1. Scaffold

```bash
cd ~/projects/pixecog
projio init --kind study
```

Writes `.projio/`, `.claude/settings.json`, `.mcp.json`. Picks one of three kinds: `generic`, `tool`, `study`.

## 2. Sync

```bash
projio sync
```

- Auto-discovers `code/lib/*` → registers with codio
- Detects `code/utils/` → updates config
- Syncs bundled Lua filter + CSL files into `.projio/`
- Generates `pandoc-defaults.yaml` from `.projio/render.yml`
- Incrementally rebuilds stale indexio sources

## 3. Query

Open the repo in Claude Code. The MCP server is already permissioned.

```
> rag_query("how does bad-channel detection decide exclude vs interpolate?")
> paper_context("mofrad2024hippocampus")
> pipeio_flow_status("preprocess_ieeg")
> questio_status()
```

<aside class="notes">
Pixecog lives at /storage2/arash/projects/pixecog. Running `projio sync` there picks up the preprocess_ieeg flow, the spindle/SWR detectors, and the BIDS derivatives structure. The RAG query example is a real thing the team asks — before projio it meant reading three scripts and a config.
</aside>
