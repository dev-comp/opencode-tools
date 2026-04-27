#!/home/ikka/git/ai-test/qwen36b/opencode-tools/.venv/bin/python3
"""GitHub MCP Server for OpenCode.

Provides GitHub repository, file, issue, and PR tools via the Model Context Protocol (MCP).
Run as a local MCP server in OpenCode.

Environment variables:
  GITHUB_TOKEN           - GitHub Personal Access Token (required)
  GITHUB_ORG             - Optional org name for org-scoped operations
  GITHUB_USER            - Fallback user for org-less operations

If GITHUB_TOKEN is omitted, all tools are disabled.
"""

import json
import os
import sys
import base64

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GitHub", json_response=True)

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _get_github_config():
    """Return (username_or_org, token) or None if not configured."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return None
    org = os.environ.get("GITHUB_ORG", "")
    user = os.environ.get("GITHUB_USER", "")
    owner = org or user
    if not owner:
        return None
    return owner, token


def _auth_header(token: str) -> dict:
    """Build bearer-auth header for GitHub API."""
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}


def _api_get(owner: str, repo: str | None, path: str, params: dict | None = None) -> dict:
    """GET request to GitHub API."""
    import requests
    base = f"https://api.github.com/repos/{owner}" if repo else "https://api.github.com"
    url = f"{base}/{path.lstrip('/')}"
    resp = requests.get(url, headers=_auth_header(os.environ["GITHUB_TOKEN"]), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _api_post(owner: str, repo: str | None, path: str, json_body: dict) -> dict:
    """POST request to GitHub API."""
    import requests
    base = f"https://api.github.com/repos/{owner}" if repo else "https://api.github.com"
    url = f"{base}/{path.lstrip('/')}"
    resp = requests.post(url, headers=_auth_header(os.environ["GITHUB_TOKEN"]), json=json_body, timeout=30)
    resp.raise_for_status()
    if resp.status_code == 204:
        return {}
    return resp.json()


def _api_put(owner: str, repo: str | None, path: str, json_body: dict) -> dict:
    """PUT request to GitHub API."""
    import requests
    base = f"https://api.github.com/repos/{owner}" if repo else "https://api.github.com"
    url = f"{base}/{path.lstrip('/')}"
    resp = requests.put(url, headers=_auth_header(os.environ["GITHUB_TOKEN"]), json=json_body, timeout=30)
    resp.raise_for_status()
    if resp.status_code == 204:
        return {}
    return resp.json()


def _api_delete(owner: str, repo: str | None, path: str) -> dict:
    """DELETE request to GitHub API."""
    import requests
    base = f"https://api.github.com/repos/{owner}" if repo else "https://api.github.com"
    url = f"{base}/{path.lstrip('/')}"
    resp = requests.delete(url, headers=_auth_header(os.environ["GITHUB_TOKEN"]), timeout=30)
    resp.raise_for_status()
    if resp.status_code == 204:
        return {}
    return resp.json()


def _decode_b64(text: str | None) -> str | None:
    """Decode base64-encoded content, return None if input is None."""
    if text is None:
        return None
    try:
        return base64.b64decode(text).decode("utf-8", errors="replace")
    except Exception:
        return text

# ---------------------------------------------------------------------------
# Repository tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_repos(
    org: str | None = None,
    type: str = "all",
    sort: str = "updated",
    direction: str = "desc",
    limit: int = 10,
) -> str:
    """List repositories.

    Args:
        org: Organization name. If omitted, lists the authenticated user's repos.
        type: Filter type - 'all', 'owner', 'public', 'private', 'member'. Default 'all'.
        sort: Sort field - 'updated', 'created', 'pushed', 'full_name'.
        direction: Sort direction - 'asc' or 'desc'.
        limit: Maximum number of results (1-100, default 10).

    Returns:
        JSON list of repos with id, name, full_name, description, url, and stargazers_count.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured. Set GITHUB_TOKEN."})

    owner = org or config[0]
    is_org = bool(org)

    path = f"/orgs/{owner}/repos" if is_org else "/user/repos"
    params = {"type": type, "sort": sort, "direction": direction, "per_page": min(limit, 100)}

    try:
        data = _api_get(owner, None, path, params=params)
        results = []
        for repo in data:
            results.append({
                "id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "stargazers_count": repo.get("stargazers_count"),
                "fork": repo.get("fork"),
                "default_branch": repo.get("default_branch"),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_repo(
    repo: str,
) -> str:
    """Get details of a specific repository.

    Args:
        repo: Full repo name in 'owner/name' format (e.g. 'pshapoval/connect-to-github').

    Returns:
        JSON with full repository details.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        data = _api_get(owner, repo, f"/repos/{repo}")
        return json.dumps({
            "id": data.get("id"),
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "html_url": data.get("html_url"),
            "default_branch": data.get("default_branch"),
            "stargazers_count": data.get("stargazers_count"),
            "forks_count": data.get("forks_count"),
            "open_issues_count": data.get("open_issues_count"),
            "language": data.get("language"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "owner": data.get("owner", {}).get("login"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def search_repos(
    query: str,
    sort: str = "stars",
    order: str = "desc",
    limit: int = 10,
) -> str:
    """Search GitHub repositories.

    Args:
        query: Search query (e.g. 'machine learning language:python').
        sort: Sort field - 'stars', 'forks', 'help-wanted-issues', 'updated'.
        order: Sort order - 'asc' or 'desc'.
        limit: Maximum number of results (1-100, default 10).

    Returns:
        JSON list of matching repos with id, name, description, url, and star count.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    try:
        data = _api_get("", None, f"/search/repositories", params={
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(limit, 100),
        })
        results = []
        for repo in data.get("items", []):
            results.append({
                "id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "html_url": repo.get("html_url"),
                "stargazers_count": repo.get("stargazers_count"),
                "language": repo.get("language"),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# File tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_files(
    repo: str,
    path: str = "",
    branch: str | None = None,
) -> str:
    """List files in a repository directory.

    Args:
        repo: Full repo name in 'owner/name' format.
        path: Directory path within the repo (default: root).
        branch: Branch name (default: repo default branch).

    Returns:
        JSON list of files with name, path, type (file/dir), and size.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    try:
        params = {}
        if branch:
            params["ref"] = branch
        data = _api_get(*repo.split("/", 1), repo, f"/contents/{path.lstrip('/')}", params=params)
        results = []
        for item in data:
            results.append({
                "name": item.get("name"),
                "path": item.get("path"),
                "type": item.get("type"),
                "size": item.get("size"),
                "download_url": item.get("download_url"),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def read_file(
    repo: str,
    path: str,
    branch: str | None = None,
) -> str:
    """Read file content from a repository.

    Args:
        repo: Full repo name in 'owner/name' format.
        path: Path to the file within the repo.
        branch: Branch name (default: repo default branch).

    Returns:
        JSON with content (decoded from base64), filename, and size.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    try:
        params = {}
        if branch:
            params["ref"] = branch
        data = _api_get(*repo.split("/", 1), repo, f"/contents/{path.lstrip('/')}", params=params)
        content = _decode_b64(data.get("content"))
        return json.dumps({
            "path": data.get("path"),
            "name": data.get("name"),
            "size": data.get("size"),
            "content": content,
            "sha": data.get("sha"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_file(
    repo: str,
    path: str,
    content: str,
    message: str,
    branch: str | None = None,
    encoding: str = "utf-8",
) -> str:
    """Create a new file in a repository.

    Args:
        repo: Full repo name in 'owner/name' format.
        path: Path where the file should be created.
        content: File content (plain text).
        message: Commit message.
        branch: Target branch (default: repo default branch).
        encoding: Content encoding - 'utf-8' or 'base64'.

    Returns:
        JSON with commit info, file path, and SHA.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        if encoding == "base64":
            encoded = base64.b64encode(content.encode()).decode()
        else:
            encoded = base64.b64encode(content.encode("utf-8")).decode()

        json_body = {
            "message": message,
            "content": encoded,
        }
        if branch:
            json_body["branch"] = branch

        data = _api_post(owner, repo, f"/repos/{repo}/contents/{path.lstrip('/')}", json_body=json_body)
        return json.dumps({
            "commit": {
                "sha": data.get("commit", {}).get("sha"),
                "url": data.get("commit", {}).get("url"),
            },
            "content": {
                "path": data.get("content", {}).get("path"),
                "sha": data.get("content", {}).get("sha"),
            },
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def update_file(
    repo: str,
    path: str,
    content: str,
    message: str,
    sha: str,
    branch: str | None = None,
    encoding: str = "utf-8",
) -> str:
    """Update an existing file in a repository.

    Args:
        repo: Full repo name in 'owner/name' format.
        path: Path to the existing file.
        content: New file content (plain text).
        message: Commit message.
        sha: Current file SHA (required for update).
        branch: Target branch (default: repo default branch).
        encoding: Content encoding - 'utf-8' or 'base64'.

    Returns:
        JSON with commit info, file path, and new SHA.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        if encoding == "base64":
            encoded = base64.b64encode(content.encode()).decode()
        else:
            encoded = base64.b64encode(content.encode("utf-8")).decode()

        json_body = {
            "message": message,
            "content": encoded,
            "sha": sha,
        }
        if branch:
            json_body["branch"] = branch

        data = _api_put(owner, repo, f"/repos/{repo}/contents/{path.lstrip('/')}", json_body=json_body)
        return json.dumps({
            "commit": {
                "sha": data.get("commit", {}).get("sha"),
                "url": data.get("commit", {}).get("url"),
            },
            "content": {
                "path": data.get("content", {}).get("path"),
                "sha": data.get("content", {}).get("sha"),
            },
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def delete_file(
    repo: str,
    path: str,
    message: str,
    sha: str,
    branch: str | None = None,
) -> str:
    """Delete a file from a repository.

    Args:
        repo: Full repo name in 'owner/name' format.
        path: Path to the file to delete.
        message: Commit message.
        sha: Current file SHA (required).
        branch: Target branch (default: repo default branch).

    Returns:
        JSON with commit info and deleted file path.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        json_body = {
            "message": message,
            "sha": sha,
        }
        if branch:
            json_body["branch"] = branch

        data = _api_delete(owner, repo, f"/repos/{repo}/contents/{path.lstrip('/')}",)
        return json.dumps({
            "commit": {
                "sha": data.get("commit", {}).get("sha"),
                "url": data.get("commit", {}).get("url"),
            },
            "content": {
                "path": data.get("content", {}).get("path"),
            },
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------------------------------------------------------------------------
# Branch tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_branches(
    repo: str,
    pattern: str | None = None,
) -> str:
    """List branches in a repository.

    Args:
        repo: Full repo name in 'owner/name' format.
        pattern: Optional branch name filter (glob-like, e.g. 'feature/*').

    Returns:
        JSON list of branches with name, protected, and commit info.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        params = {}
        if pattern:
            params["pattern"] = pattern
        data = _api_get(owner, repo, f"/repos/{repo}/branches", params=params)
        results = []
        for branch in data:
            results.append({
                "name": branch.get("name"),
                "protected": branch.get("protected"),
                "commit": {
                    "sha": branch.get("commit", {}).get("sha"),
                    "url": branch.get("commit", {}).get("url"),
                },
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_branch(
    repo: str,
    branch: str,
    from_branch: str | None = None,
) -> str:
    """Create a new branch from an existing one.

    Args:
        repo: Full repo name in 'owner/name' format.
        branch: Name of the new branch to create.
        from_branch: Source branch to create from (default: repo default branch).

    Returns:
        JSON with branch name and commit SHA.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        # Get the default branch SHA
        default_branch = from_branch or _api_get(owner, repo, f"/repos/{repo}").get("default_branch")
        ref_data = _api_get(owner, repo, f"/repos/{repo}/git/refs/heads/{default_branch}")
        sha = ref_data.get("object", {}).get("sha")

        if not sha:
            return json.dumps({"error": f"Could not resolve SHA for branch '{default_branch}'."})

        json_body = {
            "ref": f"refs/heads/{branch}",
            "sha": sha,
        }
        data = _api_post(owner, repo, f"/repos/{repo}/git/refs", json_body=json_body)
        return json.dumps({
            "ref": data.get("ref"),
            "sha": data.get("object", {}).get("sha"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------------------------------------------------------------------------
# Issue tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_issues(
    repo: str,
    state: str = "open",
    labels: list[str] | None = None,
    sort: str = "created",
    direction: str = "desc",
    limit: int = 10,
) -> str:
    """List issues in a repository.

    Args:
        repo: Full repo name in 'owner/name' format.
        state: Issue state - 'open', 'closed', or 'all'.
        labels: Optional list of label names to filter by.
        sort: Sort field - 'created', 'updated', 'comments'.
        direction: Sort direction - 'asc' or 'desc'.
        limit: Maximum number of results (1-100, default 10).

    Returns:
        JSON list of issues with number, title, state, and URL.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        params = {"state": state, "sort": sort, "direction": direction, "per_page": min(limit, 100)}
        if labels:
            params["labels"] = ",".join(labels)

        data = _api_get(owner, repo, f"/repos/{repo}/issues", params=params)
        results = []
        for issue in data:
            results.append({
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "labels": [lb.get("name") for lb in issue.get("labels", [])],
                "html_url": issue.get("html_url"),
                "created_at": issue.get("created_at"),
                "assignee": issue.get("assignee", {}).get("login") if issue.get("assignee") else None,
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_issue(
    repo: str,
    number: int,
) -> str:
    """Get details of a specific issue.

    Args:
        repo: Full repo name in 'owner/name' format.
        number: Issue number.

    Returns:
        JSON with full issue details.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        data = _api_get(owner, repo, f"/repos/{repo}/issues/{number}")
        return json.dumps({
            "number": data.get("number"),
            "title": data.get("title"),
            "state": data.get("state"),
            "body": data.get("body"),
            "labels": [lb.get("name") for lb in data.get("labels", [])],
            "html_url": data.get("html_url"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "assignee": data.get("assignee", {}).get("login") if data.get("assignee") else None,
            "user": data.get("user", {}).get("login"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_issue(
    repo: str,
    title: str,
    body: str | None = None,
    labels: list[str] | None = None,
    assignee: str | None = None,
) -> str:
    """Create a new issue.

    Args:
        repo: Full repo name in 'owner/name' format.
        title: Issue title.
        body: Issue body (supports Markdown).
        labels: List of label names.
        assignee: Username to assign.

    Returns:
        JSON with issue number, title, state, and URL.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        json_body = {"title": title}
        if body:
            json_body["body"] = body
        if labels:
            json_body["labels"] = labels
        if assignee:
            json_body["assignee"] = assignee

        data = _api_post(owner, repo, f"/repos/{repo}/issues", json_body=json_body)
        return json.dumps({
            "number": data.get("number"),
            "title": data.get("title"),
            "state": data.get("state"),
            "html_url": data.get("html_url"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def update_issue(
    repo: str,
    number: int,
    title: str | None = None,
    body: str | None = None,
    state: str | None = None,
    labels: list[str] | None = None,
    assignee: str | None = None,
) -> str:
    """Update an existing issue.

    Args:
        repo: Full repo name in 'owner/name' format.
        number: Issue number.
        title: New title (optional).
        body: New body (optional).
        state: New state - 'open' or 'closed' (optional).
        labels: New label list, replaces existing (optional).
        assignee: New assignee username (optional).

    Returns:
        JSON with updated issue details.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        json_body: dict = {}
        if title is not None:
            json_body["title"] = title
        if body is not None:
            json_body["body"] = body
        if state is not None:
            json_body["state"] = state
        if labels is not None:
            json_body["labels"] = labels
        if assignee is not None:
            json_body["assignee"] = assignee

        data = _api_put(owner, repo, f"/repos/{repo}/issues/{number}", json_body=json_body)
        return json.dumps({
            "number": data.get("number"),
            "title": data.get("title"),
            "state": data.get("state"),
            "html_url": data.get("html_url"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_issue_comments(
    repo: str,
    number: int,
    sort: str = "created",
    direction: str = "desc",
    limit: int = 10,
) -> str:
    """List comments on an issue.

    Args:
        repo: Full repo name in 'owner/name' format.
        number: Issue number.
        sort: Sort field - 'created' or 'updated'.
        direction: Sort direction - 'asc' or 'desc'.
        limit: Maximum number of results (1-100, default 10).

    Returns:
        JSON list of comments with body, author, and created_at.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        data = _api_get(owner, repo, f"/repos/{repo}/issues/{number}/comments", params={
            "sort": sort, "direction": direction, "per_page": min(limit, 100),
        })
        results = []
        for comment in data:
            results.append({
                "id": comment.get("id"),
                "body": comment.get("body"),
                "user": comment.get("user", {}).get("login"),
                "created_at": comment.get("created_at"),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def add_comment(
    repo: str,
    number: int,
    body: str,
) -> str:
    """Add a comment to an issue or PR.

    Args:
        repo: Full repo name in 'owner/name' format.
        number: Issue or PR number.
        body: Comment body (supports Markdown).

    Returns:
        JSON with comment id, body, and URL.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        data = _api_post(owner, repo, f"/repos/{repo}/issues/{number}/comments", json_body={"body": body})
        return json.dumps({
            "id": data.get("id"),
            "body": data.get("body"),
            "html_url": data.get("html_url"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------------------------------------------------------------------------
# Pull request tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_pull_requests(
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    limit: int = 10,
) -> str:
    """List pull requests in a repository.

    Args:
        repo: Full repo name in 'owner/name' format.
        state: PR state - 'open', 'closed', or 'all'.
        sort: Sort field - 'created', 'updated', 'popularity', 'long-running'.
        direction: Sort direction - 'asc' or 'desc'.
        limit: Maximum number of results (1-100, default 10).

    Returns:
        JSON list of PRs with number, title, state, and URL.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        data = _api_get(owner, repo, f"/repos/{repo}/pulls", params={
            "state": state, "sort": sort, "direction": direction, "per_page": min(limit, 100),
        })
        results = []
        for pr in data:
            results.append({
                "number": pr.get("number"),
                "title": pr.get("title"),
                "state": pr.get("state"),
                "html_url": pr.get("html_url"),
                "created_at": pr.get("created_at"),
                "merged": pr.get("merged"),
                "draft": pr.get("draft"),
                "user": pr.get("user", {}).get("login"),
                "head_ref": pr.get("head", {}).get("ref"),
                "base_ref": pr.get("base", {}).get("ref"),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_pull_request(
    repo: str,
    number: int,
) -> str:
    """Get details of a specific pull request.

    Args:
        repo: Full repo name in 'owner/name' format.
        number: PR number.

    Returns:
        JSON with full PR details.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        data = _api_get(owner, repo, f"/repos/{repo}/pulls/{number}")
        return json.dumps({
            "number": data.get("number"),
            "title": data.get("title"),
            "body": data.get("body"),
            "state": data.get("state"),
            "html_url": data.get("html_url"),
            "created_at": data.get("created_at"),
            "merged": data.get("merged"),
            "draft": data.get("draft"),
            "merged_by": data.get("merged_by", {}).get("login") if data.get("merged_by") else None,
            "user": data.get("user", {}).get("login"),
            "head_ref": data.get("head", {}).get("ref"),
            "base_ref": data.get("base", {}).get("ref"),
            "mergeable": data.get("mergeable"),
            "mergeable_state": data.get("mergeable_state"),
            "review_comments": data.get("review_comments"),
            "commits": data.get("commits"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def merge_pull_request(
    repo: str,
    number: int,
    commit_title: str | None = None,
    commit_message: str | None = None,
    merge_method: str = "merge",
) -> str:
    """Merge a pull request.

    Args:
        repo: Full repo name in 'owner/name' format.
        number: PR number.
        commit_title: Commit title (optional).
        commit_message: Commit message (optional).
        merge_method: Merge method - 'merge', 'squash', or 'rebase'.

    Returns:
        JSON with merge success status and commit info.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        json_body = {"merge_method": merge_method}
        if commit_title:
            json_body["commit_title"] = commit_title
        if commit_message:
            json_body["commit_message"] = commit_message

        data = _api_put(owner, repo, f"/repos/{repo}/pulls/{number}/merge", json_body=json_body)
        return json.dumps({
            "merged": data.get("merged"),
            "sha": data.get("sha"),
            "message": data.get("message"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def list_pr_comments(
    repo: str,
    number: int,
) -> str:
    """List review comments on a pull request.

    Args:
        repo: Full repo name in 'owner/name' format.
        number: PR number.

    Returns:
        JSON list of review comments with path, line, and body.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        data = _api_get(owner, repo, f"/repos/{repo}/pulls/{number}/comments")
        results = []
        for comment in data:
            results.append({
                "id": comment.get("id"),
                "path": comment.get("path"),
                "line": comment.get("line"),
                "body": comment.get("body"),
                "user": comment.get("user", {}).get("login"),
            })
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def create_pull_request(
    repo: str,
    title: str,
    body: str | None = None,
    head: str | None = None,
    base: str | None = None,
    draft: bool = False,
) -> str:
    """Create a new pull request.

    Args:
        repo: Full repo name in 'owner/name' format.
        title: PR title.
        body: PR body (supports Markdown).
        head: Source branch name.
        base: Target branch name (default: repo default branch).
        draft: Whether to create as draft PR.

    Returns:
        JSON with PR number, title, state, and URL.
    """
    config = _get_github_config()
    if config is None:
        return json.dumps({"error": "GitHub not configured."})

    owner, name = repo.split("/", 1)
    try:
        # Get default branch if base not specified
        if not base:
            repo_info = _api_get(owner, repo, f"/repos/{repo}")
            base = repo_info.get("default_branch", "main")

        json_body = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            json_body["body"] = body

        data = _api_post(owner, repo, f"/repos/{repo}/pulls", json_body=json_body)
        return json.dumps({
            "number": data.get("number"),
            "title": data.get("title"),
            "state": data.get("state"),
            "html_url": data.get("html_url"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if _get_github_config() is None:
        print("ERROR: GitHub not configured.", file=sys.stderr)
        print("Set GITHUB_TOKEN and GITHUB_ORG or GITHUB_USER", file=sys.stderr)
        sys.exit(1)

    mcp.run(transport="stdio")
