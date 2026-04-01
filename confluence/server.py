"""
Confluence MCP Server
Read-only access to Confluence pages and spaces over stdio transport for use with Claude Code.
"""

import os
import json
import re
import logging
import httpx
from mcp.server.fastmcp import FastMCP

# --- Configuration via environment variables ---
CONFLUENCE_BASE_URL = os.environ.get("CONFLUENCE_BASE_URL", "")  # e.g. https://confluence.yourcompany.com
CONFLUENCE_USERNAME = os.environ.get("CONFLUENCE_USERNAME", "")
CONFLUENCE_PASSWORD = os.environ.get("CONFLUENCE_PASSWORD", "")  # password or API token (Cloud)
CONFLUENCE_PAT = os.environ.get("CONFLUENCE_PAT", "")            # alternative: bearer token (Data Center)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("confluence-mcp")

mcp = FastMCP("confluence-server")


def _auth_headers() -> dict[str, str]:
    if CONFLUENCE_PAT:
        return {"Authorization": f"Bearer {CONFLUENCE_PAT}"}
    return {}


def _auth_kwarg() -> dict:
    if CONFLUENCE_PAT:
        return {}
    if CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD:
        return {"auth": (CONFLUENCE_USERNAME, CONFLUENCE_PASSWORD)}
    return {}


def _strip_tags(text: str) -> str:
    """Remove XML/HTML tags and collapse whitespace for readable plain text."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _api(path: str) -> str:
    return f"{CONFLUENCE_BASE_URL.rstrip('/')}/rest/api{path}"


async def _get(path: str, params: dict | None = None) -> dict | str:
    """Make a GET request to the Confluence REST API. Returns parsed JSON or an error dict."""
    try:
        async with httpx.AsyncClient(timeout=30, verify=True) as client:
            resp = await client.get(
                _api(path),
                params=params or {},
                headers={"Accept": "application/json", **_auth_headers()},
                **_auth_kwarg(),
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"Confluence returned HTTP {e.response.status_code}", "detail": e.response.text[:500]}
    except httpx.RequestError as e:
        return {"error": f"Request failed: {str(e)}"}


@mcp.tool()
async def search_pages(
    cql: str,
    max_results: int = 25,
    include_body: bool = False,
) -> str:
    """
    Search Confluence content using a CQL (Confluence Query Language) query.

    Args:
        cql: A CQL query string, e.g. 'space = "MYSPACE" AND title ~ "deploy"'
             or 'text ~ "kubernetes" AND type = page ORDER BY lastModified DESC'
        max_results: Maximum number of results to return (default 25, max 200)
        include_body: If True, include a plain-text excerpt of the page body in results.

    Returns:
        JSON string with matching pages (id, title, space, url, last modified).
    """
    if not CONFLUENCE_BASE_URL:
        return json.dumps({"error": "CONFLUENCE_BASE_URL environment variable is not set."})

    max_results = min(max(1, max_results), 200)
    expand = "space,version,ancestors"
    if include_body:
        expand += ",body.export_view"

    data = await _get("/content/search", {
        "cql": cql,
        "limit": max_results,
        "expand": expand,
    })

    if "error" in data:
        return json.dumps(data)

    results = []
    for item in data.get("results", []):
        entry = {
            "id": item.get("id"),
            "type": item.get("type"),
            "title": item.get("title"),
            "space": (item.get("space") or {}).get("key"),
            "space_name": (item.get("space") or {}).get("name"),
            "url": CONFLUENCE_BASE_URL.rstrip("/") + (item.get("_links") or {}).get("webui", ""),
            "version": (item.get("version") or {}).get("number"),
            "last_modified": (item.get("version") or {}).get("when"),
            "last_modified_by": ((item.get("version") or {}).get("by") or {}).get("displayName"),
            "ancestors": [a.get("title") for a in item.get("ancestors", [])],
        }
        if include_body:
            raw = ((item.get("body") or {}).get("export_view") or {}).get("value", "")
            entry["body_excerpt"] = _strip_tags(raw)[:2000]
        results.append(entry)

    return json.dumps({
        "total": data.get("totalSize", len(results)),
        "count": len(results),
        "results": results,
    }, indent=2)


@mcp.tool()
async def get_page(page_id: str) -> str:
    """
    Get the full content of a Confluence page by its ID.

    Args:
        page_id: The numeric page ID (visible in the page URL or from search results).

    Returns:
        JSON string with the page title, metadata, and plain-text body content.
    """
    if not CONFLUENCE_BASE_URL:
        return json.dumps({"error": "CONFLUENCE_BASE_URL environment variable is not set."})

    data = await _get(f"/content/{page_id}", {
        "expand": "body.export_view,space,version,ancestors,children.page",
    })

    if "error" in data:
        return json.dumps(data)

    raw_body = ((data.get("body") or {}).get("export_view") or {}).get("value", "")
    children = [
        {"id": c.get("id"), "title": c.get("title")}
        for c in ((data.get("children") or {}).get("page") or {}).get("results", [])
    ]

    result = {
        "id": data.get("id"),
        "type": data.get("type"),
        "title": data.get("title"),
        "space": (data.get("space") or {}).get("key"),
        "space_name": (data.get("space") or {}).get("name"),
        "url": CONFLUENCE_BASE_URL.rstrip("/") + (data.get("_links") or {}).get("webui", ""),
        "version": (data.get("version") or {}).get("number"),
        "last_modified": (data.get("version") or {}).get("when"),
        "last_modified_by": ((data.get("version") or {}).get("by") or {}).get("displayName"),
        "ancestors": [a.get("title") for a in data.get("ancestors", [])],
        "child_pages": children,
        "body": _strip_tags(raw_body),
    }

    return json.dumps(result, indent=2)


@mcp.tool()
async def list_spaces(
    max_results: int = 50,
    space_type: str = "global",
) -> str:
    """
    List available Confluence spaces.

    Args:
        max_results: Maximum number of spaces to return (default 50).
        space_type: Filter by space type: 'global' (default), 'personal', or '' for all.

    Returns:
        JSON string with space keys, names, and URLs.
    """
    if not CONFLUENCE_BASE_URL:
        return json.dumps({"error": "CONFLUENCE_BASE_URL environment variable is not set."})

    params: dict = {"limit": min(max(1, max_results), 500), "expand": "description.plain"}
    if space_type:
        params["type"] = space_type

    data = await _get("/space", params)

    if "error" in data:
        return json.dumps(data)

    spaces = []
    for s in data.get("results", []):
        spaces.append({
            "key": s.get("key"),
            "name": s.get("name"),
            "type": s.get("type"),
            "description": ((s.get("description") or {}).get("plain") or {}).get("value", ""),
            "url": CONFLUENCE_BASE_URL.rstrip("/") + (s.get("_links") or {}).get("webui", ""),
        })

    return json.dumps({
        "total": data.get("limit", len(spaces)),
        "count": len(spaces),
        "spaces": spaces,
    }, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
