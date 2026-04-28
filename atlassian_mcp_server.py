#!/home/ikka/git/ai-test/qwen36b/opencode-tools/.venv/bin/python3
"""Atlassian MCP Server for OpenCode.

Provides Confluence and Jira tools via the Model Context Protocol (MCP).
Run as a local MCP server in OpenCode.

Environment variables:
  CONFLUENCE_BASE_URL      - e.g. https://yourcompany.atlassian.net/wiki
  CONFLUENCE_API_TOKEN     - Confluence personal access token
  CONFLUENCE_USERNAME      - Confluence email/username (optional for Cloud)
  JIRA_BASE_URL            - e.g. https://yourcompany.atlassian.net
  JIRA_API_TOKEN           - Jira personal access token
  JIRA_USERNAME            - Jira email/username (optional for Cloud)

If CONFLUENCE_* vars are omitted, Confluence tools are disabled.
If JIRA_* vars are omitted, Jira tools are disabled.
"""

import json
import os
import sys
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv
load_dotenv("/home/ikka/.config/opencode/.env", override=True)

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Atlassian", json_response=True)

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------


def _get_confluence_config():
    """Return (base_url, email, token) or None if not configured."""
    base_url = os.environ.get("CONFLUENCE_BASE_URL", "").rstrip("/")
    token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    if not base_url or not token:
        return None
    return base_url, os.environ.get("CONFLUENCE_USERNAME", ""), token


def _get_jira_config():
    """Return (base_url, email, token) or None if not configured."""
    base_url = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
    token = os.environ.get("JIRA_API_TOKEN", "")
    if not base_url or not token:
        return None
    return base_url, os.environ.get("JIRA_USERNAME", ""), token


def _auth_header(email: str, token: str) -> dict[str, str]:
    """Build basic-auth header for Atlassian Cloud."""
    import base64
    credentials = f"{email}:{token}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def _make_request(base_url: str, email: str, token: str, method: str, path: str,
                  params: dict | None = None, json_body: dict | None = None) -> dict:
    """Helper to make an HTTP request to the Atlassian Cloud API."""
    import requests
    url = urljoin(base_url, path)
    headers = {"Accept": "application/json"}
    headers.update(_auth_header(email, token))
    resp = requests.request(method, url, params=params, json=json_body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Confluence tools
# ---------------------------------------------------------------------------

@mcp.tool()
def confluence_search_pages(
    query: str | None = None,
    space_key: str | None = None,
    label: str | None = None,
    limit: int = 10,
) -> str:
    """Search Confluence pages.

    Args:
        query: Free-text search query (body.content). Use None to skip.
        space_key: Filter by space key (e.g. 'DEV'). Use None to skip.
        label: Filter by label. Use None to skip.
        limit: Maximum number of results (1-50, default 10).

    Returns:
        JSON list of matching pages with id, title, space, and url.
    """
    config = _get_confluence_config()
    if config is None:
        return json.dumps({"error": "Confluence not configured. Set CONFLUENCE_BASE_URL and CONFLUENCE_API_TOKEN."})

    base_url, email, token = config
    path = "/wiki/rest/api/search"
    params: dict = {"limit": min(limit, 50)}
    if query:
        params["cql"] = f'text~"{query}"'
        if space_key:
            params["cql"] += f' AND space="{space_key}"'
        if label:
            params["cql"] += f' AND label="{label}"'
    elif space_key and label:
        params["cql"] = f'space="{space_key}" AND label="{label}"'
    elif space_key:
        params["cql"] = f'space="{space_key}"'
    elif label:
        params["cql"] = f'label="{label}"'

    try:
        data = _make_request(base_url, email, token, "GET", path, params=params)
        results = []
        for hit in data.get("results", []):
            page = hit.get("page", hit)
            results.append({
                "id": page.get("id"),
                "title": page.get("title", ""),
                "space": page.get("space", {}).get("key", ""),
                "url": page.get("_links", {}).get("webui", ""),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def confluence_get_page(
    page_id: str,
    body_format: str = "storage",
) -> str:
    """Get the content of a Confluence page.

    Args:
        page_id: The numeric page ID.
        body_format: Content format - 'storage' (default), 'view', 'atlas_doc_format', or 'plain'.

    Returns:
        Page content in the requested format plus metadata.
    """
    config = _get_confluence_config()
    if config is None:
        return json.dumps({"error": "Confluence not configured."})

    base_url, email, token = config
    path = f"/wiki/rest/api/content/{page_id}?body.output_format={body_format}"
    try:
        data = _make_request(base_url, email, token, "GET", path)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def confluence_get_page_children(
    page_id: str,
    limit: int = 10,
) -> str:
    """List child pages of a Confluence page.

    Args:
        page_id: The parent page ID.
        limit: Maximum results (1-50, default 10).

    Returns:
        JSON list of child pages with id, title, and url.
    """
    config = _get_confluence_config()
    if config is None:
        return json.dumps({"error": "Confluence not configured."})

    base_url, email, token = config
    path = f"/wiki/rest/api/content/{page_id}/child/page"
    params = {"limit": min(limit, 50)}
    try:
        data = _make_request(base_url, email, token, "GET", path, params=params)
        results = []
        for page in data.get("results", []):
            results.append({
                "id": page.get("id"),
                "title": page.get("title", ""),
                "url": page.get("_links", {}).get("webui", ""),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def confluence_create_page(
    space_key: str,
    title: str,
    body: str,
    parent_id: str | None = None,
    body_format: str = "storage",
) -> str:
    """Create a new Confluence page.

    Args:
        space_key: Target space key (e.g. 'DEV').
        title: Page title.
        body: Page body content.
        parent_id: Optional parent page ID for hierarchy.
        body_format: Content format - 'storage' (default), 'view', 'atlas_doc_format', or 'plain'.

    Returns:
        JSON with the new page id, title, and url.
    """
    config = _get_confluence_config()
    if config is None:
        return json.dumps({"error": "Confluence not configured."})

    base_url, email, token = config
    path = f"/wiki/rest/api/content"
    body_payload: dict = {"value": body, "representation": body_format}
    json_body: dict = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": body_payload,
    }
    if parent_id:
        json_body["ancestors"] = [{"id": parent_id}]

    try:
        data = _make_request(base_url, email, token, "POST", path, json_body=json_body)
        return json.dumps({
            "id": data.get("id"),
            "title": data.get("title"),
            "url": data.get("_links", {}).get("webui", ""),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def confluence_update_page(
    page_id: str,
    title: str | None = None,
    body: str | None = None,
    body_format: str = "storage",
) -> str:
    """Update an existing Confluence page.

    Args:
        page_id: The page ID to update.
        title: New title (optional; keep if omitted).
        body: New body content (optional; keep if omitted).
        body_format: Content format - 'storage' (default), 'view', 'atlas_doc_format', or 'plain'.

    Returns:
        JSON with the updated page id, title, version, and url.
    """
    config = _get_confluence_config()
    if config is None:
        return json.dumps({"error": "Confluence not configured."})

    base_url, email, token = config
    # First get existing version number
    path = f"/wiki/rest/api/content/{page_id}"
    try:
        existing = _make_request(base_url, email, token, "GET", path)
        version = existing.get("version", {}).get("number", 1)
    except Exception:
        version = 1

    json_body: dict = {"id": page_id, "version": {"number": version + 1}}
    if title is not None:
        json_body["title"] = title
    if body is not None:
        json_body["body"] = {"value": body, "representation": body_format}

    try:
        data = _make_request(base_url, email, token, "PUT", path, json_body=json_body)
        return json.dumps({
            "id": data.get("id"),
            "title": data.get("title"),
            "version": data.get("version", {}).get("number"),
            "url": data.get("_links", {}).get("webui", ""),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def confluence_list_spaces(
    limit: int = 20,
) -> str:
    """List Confluence spaces.

    Args:
        limit: Maximum number of spaces (1-100, default 20).

    Returns:
        JSON list of spaces with key, name, and url.
    """
    config = _get_confluence_config()
    if config is None:
        return json.dumps({"error": "Confluence not configured."})

    base_url, email, token = config
    path = "/wiki/rest/api/space"
    params = {"limit": min(limit, 100)}
    try:
        data = _make_request(base_url, email, token, "GET", path, params=params)
        results = []
        for space in data.get("results", []):
            results.append({
                "key": space.get("key"),
                "name": space.get("name", ""),
                "url": space.get("_links", {}).get("webui", ""),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def confluence_get_space(
    space_key: str,
) -> str:
    """Get details about a specific Confluence space.

    Args:
        space_key: The space key (e.g. 'DEV').

    Returns:
        JSON with space details including key, name, and description.
    """
    config = _get_confluence_config()
    if config is None:
        return json.dumps({"error": "Confluence not configured."})

    base_url, email, token = config
    path = f"/wiki/rest/api/space/{space_key}"
    try:
        data = _make_request(base_url, email, token, "GET", path)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Jira tools
# ---------------------------------------------------------------------------

@mcp.tool()
def jira_search_issues(
    jql: str,
    fields: str | None = None,
    limit: int = 10,
) -> str:
    """Search Jira issues using JQL (Jira Query Language).

    Args:
        jql: JQL query string (e.g. 'project = DEV AND status = "In Progress"').
        fields: Comma-separated list of fields to return (e.g. 'summary,status,assignee').
                 Use None to get all fields.
        limit: Maximum results (1-100, default 10).

    Returns:
        JSON list of matching issues with id, key, summary, and fields.
    """
    config = _get_jira_config()
    if config is None:
        return json.dumps({"error": "Jira not configured. Set JIRA_BASE_URL and JIRA_API_TOKEN."})

    base_url, email, token = config
    path = "/rest/api/2/search"
    params = {
        "jql": jql,
        "maxResults": min(limit, 100),
    }
    if fields:
        params["fields"] = fields

    try:
        data = _make_request(base_url, email, token, "GET", path, params=params)
        results = []
        for issue in data.get("issues", []):
            fields_data = issue.get("fields", {})
            results.append({
                "key": issue.get("key"),
                "id": issue.get("id"),
                "summary": fields_data.get("summary", ""),
                "status": fields_data.get("status", {}).get("name", ""),
                "assignee": fields_data.get("assignee", {}).get("displayName", "Unassigned") if fields_data.get("assignee") else "Unassigned",
                "priority": fields_data.get("priority", {}).get("name", "") if fields_data.get("priority") else "",
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        if "410" in str(e):
            return json.dumps({"error": "Search API unavailable on Jira Free plan. Create tasks and retrieve by key instead.", "workaround": "Create tasks via jira_create_issue, then retrieve via jira_get_issue"})
        return json.dumps({"error": str(e)})


@mcp.tool()
def jira_get_issue(
    issue_key: str,
    fields: str | None = None,
) -> str:
    """Get details of a specific Jira issue.

    Args:
        issue_key: The issue key (e.g. 'DEV-123').
        fields: Comma-separated list of fields to return. Use None for all fields.

    Returns:
        JSON with full issue details.
    """
    config = _get_jira_config()
    if config is None:
        return json.dumps({"error": "Jira not configured."})

    base_url, email, token = config
    path = f"/rest/api/2/issue/{issue_key}"
    params = {}
    if fields:
        params["fields"] = fields

    try:
        data = _make_request(base_url, email, token, "GET", path, params=params)
        return json.dumps(data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def jira_create_issue(
    project_key: str,
    summary: str,
    issue_type: str = "Task",
    description: str = "",
    assignee: str | None = None,
    labels: list[str] | None = None,
    parent_key: str | None = None,
) -> str:
    """Create a new Jira issue.

    Args:
        project_key: Target project key (e.g. 'DEV').
        summary: Issue summary / title.
        issue_type: Issue type - 'Task' (default), 'Bug', 'Story', 'Epic', 'Sub-task'.
        description: Issue description (optional).
        assignee: Username to assign to (optional).
        labels: List of labels to add (optional).
        parent_key: Parent issue key for sub-tasks (optional).

    Returns:
        JSON with the new issue key, id, and url.
    """
    config = _get_jira_config()
    if config is None:
        return json.dumps({"error": "Jira not configured."})

    base_url, email, token = config
    path = "/rest/api/2/issue"
    fields: dict = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }
    if description:
        fields["description"] = description
    if assignee:
        fields["assignee"] = {"name": assignee}
    if labels:
        fields["labels"] = labels
    if parent_key:
        fields["parent"] = {"key": parent_key}

    json_body = {"fields": fields}

    try:
        data = _make_request(base_url, email, token, "POST", path, json_body=json_body)
        return json.dumps({
            "key": data.get("key"),
            "id": data.get("id"),
            "self": data.get("self"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def jira_update_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    labels: list[str] | None = None,
) -> str:
    """Update an existing Jira issue.

    Args:
        issue_key: The issue key (e.g. 'DEV-123').
        summary: New summary (optional).
        description: New description (optional).
        status: New status name (optional).
        assignee: Username to assign to (optional).
        labels: New list of labels, replaces existing (optional).

    Returns:
        JSON with updated issue key and id.
    """
    config = _get_jira_config()
    if config is None:
        return json.dumps({"error": "Jira not configured."})

    base_url, email, token = config
    path = f"/rest/api/2/issue/{issue_key}"
    fields: dict = {}
    if summary is not None:
        fields["summary"] = summary
    if description is not None:
        fields["description"] = description
    if assignee is not None:
        fields["assignee"] = {"name": assignee}
    if labels is not None:
        fields["labels"] = labels

    json_body = {"fields": fields}

    try:
        data = _make_request(base_url, email, token, "PUT", path, json_body=json_body)
        return json.dumps({
            "key": data.get("key"),
            "id": data.get("id"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def jira_list_projects(
    limit: int = 20,
) -> str:
    """List Jira projects.

    Args:
        limit: Maximum results (1-100, default 20).

    Returns:
        JSON list of projects with key, name, and id.
    """
    config = _get_jira_config()
    if config is None:
        return json.dumps({"error": "Jira not configured."})

    base_url, email, token = config
    path = "/rest/api/2/project"
    params = {"maxResults": min(limit, 100)}
    try:
        data = _make_request(base_url, email, token, "GET", path, params=params)
        projects = data.get("values", []) if isinstance(data, dict) else data
        results = []
        for project in projects:
            results.append({
                "key": project.get("key"),
                "name": project.get("name", ""),
                "id": project.get("id"),
                "lead": project.get("lead", {}).get("displayName", "") if project.get("lead") else "",
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def jira_list_statuses() -> str:
    """List all available issue statuses in Jira.

    Returns:
        JSON list of statuses with id, name, and category.
    """
    config = _get_jira_config()
    if config is None:
        return json.dumps({"error": "Jira not configured."})

    base_url, email, token = config
    path = "/rest/api/2/status"
    try:
        data = _make_request(base_url, email, token, "GET", path)
        statuses = data.get("statuses", []) if isinstance(data, dict) else data
        results = []
        for status in statuses:
            results.append({
                "id": status.get("id"),
                "name": status.get("name", ""),
                "category": status.get("statusCategory", {}).get("key", ""),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Verify at least one service is configured
    conf = _get_confluence_config()
    jira = _get_jira_config()
    if conf is None and jira is None:
        print("ERROR: No Atlassian services configured.", file=sys.stderr)
        print("Set at least CONFLUENCE_BASE_URL + CONFLUENCE_API_TOKEN or JIRA_BASE_URL + JIRA_API_TOKEN", file=sys.stderr)
        sys.exit(1)

    # Run as stdio transport (default for local MCP servers in OpenCode)
    mcp.run(transport="stdio")
