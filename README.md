# MCPs

Personal collection of MCP servers for use with Claude Code.

## Servers

| Server | Directory | Tools |
|--------|-----------|-------|
| **Jira** | [`jira/`](jira/README.md) | `search_issues`, `get_issue` |
| **Confluence** | [`confluence/`](confluence/README.md) | `search_pages`, `get_page`, `list_spaces` |

## Conventions

- **Runtime**: Python 3.10+, managed with `uv`
- **Framework**: `FastMCP` from `mcp.server.fastmcp`
- **Transport**: stdio
- **Auth/config**: environment variables only
- **HTTP client**: `httpx` (async)

## Claude Code integration

Add servers to your settings (global `~/.claude/settings.json` or project `.claude/settings.json`):

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["run", "python", "/path/to/MCPs/jira/server.py"],
      "env": {
        "JIRA_BASE_URL": "https://jira.yourcompany.com",
        "JIRA_PAT": "your-token"
      }
    },
    "confluence": {
      "command": "uv",
      "args": ["run", "python", "/path/to/MCPs/confluence/server.py"],
      "env": {
        "CONFLUENCE_BASE_URL": "https://confluence.yourcompany.com",
        "CONFLUENCE_PAT": "your-token"
      }
    }
  }
}
```

## Adding a new server

1. Create a subdirectory: `<name>/`
2. Add `server.py`, `pyproject.toml`, and `README.md`
3. Use `@mcp.tool()` to expose tools; accept all config via env vars
4. Run `uv lock` to generate the lockfile
5. Update this README and `CLAUDE.md`
