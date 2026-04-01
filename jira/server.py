# Copyright 2026 Chris Wells <chris@rhza.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Jira Data Center MCP Server
Exposes JQL search as a tool over stdio transport for use with Claude Code.
"""

import os
import json
import logging
import httpx
from mcp.server.fastmcp import FastMCP

# --- Configuration via environment variables ---
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "")          # e.g. https://jira.yourcompany.com
JIRA_USERNAME = os.environ.get("JIRA_USERNAME", "")
JIRA_PASSWORD = os.environ.get("JIRA_PASSWORD", "")           # password or personal access token
JIRA_PAT = os.environ.get("JIRA_PAT", "")                     # alternative: bearer token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-mcp")

mcp = FastMCP("jira-server")


def _auth_headers() -> dict[str, str]:
    """Build auth headers. Supports basic auth or personal access token (bearer)."""
    if JIRA_PAT:
        return {"Authorization": f"Bearer {JIRA_PAT}"}
    return {}  # httpx basic auth is passed separately


def _auth_kwarg() -> dict:
    """Return httpx auth kwarg for basic auth, or empty dict for PAT."""
    if JIRA_PAT:
        return {}
    if JIRA_USERNAME and JIRA_PASSWORD:
        return {"auth": (JIRA_USERNAME, JIRA_PASSWORD)}
    return {}


@mcp.tool()
async def search_issues(
    jql: str,
    max_results: int = 50,
    fields: str = "summary,status,assignee,priority,issuetype,created,updated",
) -> str:
    """
    Search Jira issues using a JQL query.

    Args:
        jql: A JQL query string, e.g. 'project = MYPROJ AND status = "In Progress"'
        max_results: Maximum number of issues to return (default 50, max 1000)
        fields: Comma-separated list of fields to include in results.
                Defaults to: summary, status, assignee, priority, issuetype, created, updated

    Returns:
        JSON string with matching issues and their requested fields.
    """
    if not JIRA_BASE_URL:
        return json.dumps({"error": "JIRA_BASE_URL environment variable is not set."})

    max_results = min(max(1, max_results), 1000)
    url = f"{JIRA_BASE_URL.rstrip('/')}/rest/api/2/search"

    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": fields,
    }

    try:
        async with httpx.AsyncClient(timeout=30, verify=True) as client:
            resp = await client.get(
                url,
                params=params,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    **_auth_headers(),
                },
                **_auth_kwarg(),
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": f"Jira returned HTTP {e.response.status_code}",
            "detail": e.response.text[:500],
        })
    except httpx.RequestError as e:
        return json.dumps({"error": f"Request failed: {str(e)}"})

    # Flatten the response into a concise format
    issues = []
    for item in data.get("issues", []):
        f = item.get("fields", {})
        issue = {
            "key": item.get("key"),
            "summary": f.get("summary"),
            "status": (f.get("status") or {}).get("name"),
            "assignee": (f.get("assignee") or {}).get("displayName"),
            "priority": (f.get("priority") or {}).get("name"),
            "type": (f.get("issuetype") or {}).get("name"),
            "created": f.get("created"),
            "updated": f.get("updated"),
        }
        issues.append(issue)

    return json.dumps({
        "total": data.get("total", 0),
        "count": len(issues),
        "issues": issues,
    }, indent=2)


@mcp.tool()
async def get_issue(issue_key: str) -> str:
    """
    Get full details for a single Jira issue by key.

    Args:
        issue_key: The issue key, e.g. 'PROJ-123'

    Returns:
        JSON string with the issue's fields.
    """
    if not JIRA_BASE_URL:
        return json.dumps({"error": "JIRA_BASE_URL environment variable is not set."})

    url = f"{JIRA_BASE_URL.rstrip('/')}/rest/api/2/issue/{issue_key}"

    try:
        async with httpx.AsyncClient(timeout=30, verify=True) as client:
            resp = await client.get(
                url,
                headers={
                    "Accept": "application/json",
                    **_auth_headers(),
                },
                **_auth_kwarg(),
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": f"Jira returned HTTP {e.response.status_code}",
            "detail": e.response.text[:500],
        })
    except httpx.RequestError as e:
        return json.dumps({"error": f"Request failed: {str(e)}"})

    f = data.get("fields", {})
    result = {
        "key": data.get("key"),
        "summary": f.get("summary"),
        "description": f.get("description"),
        "status": (f.get("status") or {}).get("name"),
        "assignee": (f.get("assignee") or {}).get("displayName"),
        "reporter": (f.get("reporter") or {}).get("displayName"),
        "priority": (f.get("priority") or {}).get("name"),
        "type": (f.get("issuetype") or {}).get("name"),
        "labels": f.get("labels", []),
        "created": f.get("created"),
        "updated": f.get("updated"),
        "components": [c.get("name") for c in f.get("components", [])],
        "fix_versions": [v.get("name") for v in f.get("fixVersions", [])],
    }

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
