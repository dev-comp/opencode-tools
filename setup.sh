#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== OpenCode Tools Setup ==="
echo "Installs MCP servers for GitHub and Atlassian (Confluence + Jira)"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

# Create venv if not exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

echo "Installing dependencies..."
"$SCRIPT_DIR/.venv/bin/pip" install -q mcp requests

# Check if .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "WARNING: .env not found. Copy .env.example and fill in your credentials:"
    echo "  cp .env.example .env"
fi

# Test both servers
echo ""
echo "Testing Atlassian MCP server..."
(
    export CONFLUENCE_BASE_URL="https://test.atlassian.net/wiki"
    export CONFLUENCE_API_TOKEN="test"
    export JIRA_BASE_URL="https://test.atlassian.net"
    export JIRA_API_TOKEN="test"
    timeout 3 "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/atlassian_mcp_server.py" 2>&1 || true
)

echo ""
echo "Testing GitHub MCP server..."
(
    export GITHUB_TOKEN="test"
    export GITHUB_ORG="test"
    timeout 3 "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/github_mcp_server.py" 2>&1 || true
)

echo ""
echo "=== Servers Ready ==="
echo ""
echo "Atlassian tools (13):"
echo "  confluence_search_pages, confluence_get_page, confluence_get_page_children"
echo "  confluence_create_page, confluence_update_page, confluence_list_spaces"
echo "  confluence_get_space, jira_search_issues, jira_get_issue"
echo "  jira_create_issue, jira_update_issue, jira_list_projects"
echo "  jira_list_statuses"
echo ""
echo "GitHub tools (21):"
echo "  list_repos, get_repo, search_repos"
echo "  list_files, read_file, create_file, update_file, delete_file"
echo "  list_branches, create_branch"
echo "  list_issues, get_issue, create_issue, update_issue"
echo "  list_issue_comments, add_comment"
echo "  list_pull_requests, get_pull_request, merge_pull_request"
echo "  list_pr_comments, create_pull_request"
echo ""
echo "Add to your OpenCode config (~/.config/opencode/config.json):"
echo ""
echo '  "mcp": {'
echo '    "atlassian": {'
echo '      "type": "local",'
echo "      \"command\": [\"python3\", \"$SCRIPT_DIR/.venv/bin/python3\", \"$SCRIPT_DIR/atlassian_mcp_server.py\"]"
echo '    },'
echo '    "github": {'
echo '      "type": "local",'
echo "      \"command\": [\"python3\", \"$SCRIPT_DIR/.venv/bin/python3\", \"$SCRIPT_DIR/github_mcp_server.py\"]"
echo '    }'
echo '  }'
