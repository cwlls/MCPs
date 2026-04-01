# Jira Data Center MCP Server

An MCP server that exposes Jira Data Center issue search (JQL) and issue detail retrieval as tools, over stdio transport. Built for use with Claude Code.

## Tools

| Tool | Description |
|------|-------------|
| `search_issues` | Search issues via JQL query. Returns key, summary, status, assignee, priority, type, created, updated. |
| `get_issue` | Get full details for a single issue by key (includes description, labels, components, fix versions). |

## Setup

### 1. Install dependencies

```bash
cd jira-mcp-server
pip install -e .
# or with uv:
uv pip install -e .
```

### 2. Set environment variables

**Option A — Basic auth (username + password):**
```bash
export JIRA_BASE_URL="https://jira.yourcompany.com"
export JIRA_USERNAME="your-username"
export JIRA_PASSWORD="your-password"
```

**Option B — Personal Access Token (recommended):**
```bash
export JIRA_BASE_URL="https://jira.yourcompany.com"
export JIRA_PAT="your-personal-access-token"
```

### 3. Register with Claude Code

Add this to your Claude Code MCP config (`.claude/mcp.json` in your project or `~/.claude/mcp.json` globally):

```json
{
  "mcpServers": {
    "jira": {
      "command": "python",
      "args": ["/absolute/path/to/jira-mcp-server/server.py"],
      "env": {
        "JIRA_BASE_URL": "https://jira.yourcompany.com",
        "JIRA_PAT": "your-personal-access-token"
      }
    }
  }
}
```

Or if using `uv`:

```json
{
  "mcpServers": {
    "jira": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/jira-mcp-server", "python", "server.py"],
      "env": {
        "JIRA_BASE_URL": "https://jira.yourcompany.com",
        "JIRA_PAT": "your-personal-access-token"
      }
    }
  }
}
```

## Example usage in Claude Code

Once registered, you can ask Claude things like:

- "Search Jira for all open bugs in project MYPROJ"
- "Find issues assigned to me that are in progress"
- "Get the details of PROJ-123"

Claude will call the appropriate MCP tool automatically.

## Self-signed certificates

If your Jira instance uses a self-signed cert, you can set `verify=False` in the httpx client calls in `server.py`, or set the `SSL_CERT_FILE` environment variable to your CA bundle.
