# Confluence MCP Server

Read-only MCP server for Confluence (Data Center or Cloud). Exposes three tools:

| Tool | Description |
|------|-------------|
| `search_pages` | CQL search across all content |
| `get_page` | Fetch full page content by ID |
| `list_spaces` | List available spaces |

## Setup

```bash
cd confluence
uv sync
```

## Configuration

All config is via environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `CONFLUENCE_BASE_URL` | Yes | Base URL, e.g. `https://confluence.yourcompany.com` (Data Center) or `https://yourcompany.atlassian.net/wiki` (Cloud) |
| `CONFLUENCE_PAT` | One of these | Personal Access Token (Data Center) — uses Bearer auth |
| `CONFLUENCE_USERNAME` + `CONFLUENCE_PASSWORD` | One of these | Basic auth credentials (Cloud: use API token as password) |

## Running

```bash
CONFLUENCE_BASE_URL=https://confluence.example.com \
CONFLUENCE_PAT=your_token \
uv run python server.py
```

## Claude Code integration

Add to `.claude/settings.json` (or global settings):

```json
{
  "mcpServers": {
    "confluence": {
      "command": "uv",
      "args": ["run", "python", "/path/to/confluence/server.py"],
      "env": {
        "CONFLUENCE_BASE_URL": "https://confluence.yourcompany.com",
        "CONFLUENCE_PAT": "your_token"
      }
    }
  }
}
```

## CQL examples

```
# Pages in a specific space modified recently
space = "ENG" AND type = page ORDER BY lastModified DESC

# Full-text search
text ~ "deployment runbook" AND type = page

# Pages under a parent
ancestor = 12345

# By label
label = "architecture" AND space = "ARCH"
```
