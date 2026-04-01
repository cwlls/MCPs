# MCPs

Personal collection of MCP servers for use with Claude Code.

## Repository structure

Each MCP lives in its own subdirectory with a self-contained Python package (pyproject.toml, uv.lock, server.py).

```
<name>/
  server.py        # FastMCP server entry point
  pyproject.toml   # package metadata and deps
  uv.lock          # locked dependency tree
  README.md        # setup and usage docs
```

## Conventions

- **Runtime**: Python 3.10+, managed with `uv`
- **Framework**: `mcp[cli]` with `FastMCP` from `mcp.server.fastmcp`
- **Transport**: stdio (all servers run as `python server.py` or via `uv run`)
- **Auth/config**: environment variables only — no hardcoded secrets, no config files
- **HTTP client**: `httpx` (async)

## Adding a new MCP

1. Create a new subdirectory: `<name>/`
2. Add `pyproject.toml`, `server.py`, and a `README.md`
3. Use `FastMCP` and expose tools with `@mcp.tool()`
4. Accept all credentials/config via environment variables

## Current servers

| Directory | Description |
|-----------|-------------|
| `jira/`   | Jira Data Center — JQL search (`search_issues`) and issue detail retrieval (`get_issue`) via REST API v2. Auth: basic auth or PAT. |
| `confluence/` | Confluence (Data Center or Cloud) — CQL page search (`search_pages`), page content retrieval (`get_page`), and space listing (`list_spaces`). Auth: basic auth or PAT. |
