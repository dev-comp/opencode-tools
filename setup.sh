#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== OpenCode Tools Setup ==="
echo "Installs MCP servers for GitHub, Atlassian (Confluence + Jira), and Google"
echo ""

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
fi

echo "Installing dependencies..."
"$SCRIPT_DIR/.venv/bin/pip" install -q mcp requests google-api-python-client google-auth-httplib2 google-auth-oauthlib

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "WARNING: .env not found. Copy .env.example and fill in your credentials:"
    echo "  cp .env.example .env"
fi

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
echo "Testing Google MCP server..."
(
    export GOOGLE_CREDENTIALS="/tmp/nonexistent.json"
    timeout 3 "$SCRIPT_DIR/.venv/bin/python3" "$SCRIPT_DIR/google_mcp_server.py" 2>&1 || true
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
echo "GitHub tools (10):"
echo "  list_repos, get_repo, search_repos"
echo "  list_files, read_file, create_file, update_file, delete_file"
echo "  list_branches, create_branch"
echo ""
echo "Google tools (9):"
echo "  google_drive_list_files, google_drive_read_file, google_drive_create_file"
echo "  google_gmail_search, google_gmail_read, google_gmail_send"
echo "  google_calendar_list_events, google_calendar_create_event"
echo "  google_calendar_update_event"
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
echo '    },'
echo '    "google": {'
echo '      "type": "local",'
echo "      \"command\": [\"python3\", \"$SCRIPT_DIR/.venv/bin/python3\", \"$SCRIPT_DIR/google_mcp_server.py\"]"
echo '    }'
echo '  }'
