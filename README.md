# OpenCode Tools

MCP servers for OpenCode (formerly opencode-dev/opencode) that provide access to **GitHub** and **Atlassian** (Confluence + Jira).

## Features

- **20 tools** across 2 MCP servers (13 Atlassian, 7 GitHub)
- **Private by design** — secrets stored in a local env file, never committed
- **Global installation** — one config entry, available across all projects
- **Zero external dependencies** — uses only Python stdlib + `mcp` + `requests`

## Quick Start

1. Clone this repo
2. Run `bash setup.sh`
3. Fill in your credentials in `.env`
4. Add servers to `~/.config/opencode/config.json`
5. Restart OpenCode

See the full guide: https://pshapoval.atlassian.net/wiki/spaces/KB/pages/241926146/Connect+OpenCode+to+Atlassian+Cloud

## Available Tools

### Atlassian MCP (13 tools)

**Confluence** (7 tools):
- `confluence_search_pages` — search pages by query, space, or label
- `confluence_get_page` — read page content by ID
- `confluence_get_page_children` — list child pages
- `confluence_create_page` — create a new page
- `confluence_update_page` — update an existing page
- `confluence_list_spaces` — list all spaces
- `confluence_get_space` — get space details

**Jira** (6 tools):
- `jira_search_issues` — search issues via JQL
- `jira_get_issue` — get issue details by key
- `jira_create_issue` — create a new issue
- `jira_update_issue` — update an existing issue
- `jira_list_projects` — list projects
- `jira_list_statuses` — list statuses

### GitHub MCP (7 tools)

- `list_repos` — list org or user repositories
- `get_repo` — get repository details
- `search_repos` — search repositories
- `list_files` — list files in a directory
- `read_file` — read file content by path
- `create_file` — create a new file with commit
- `update_file` — update existing file (requires SHA)
- `delete_file` — delete a file (requires SHA)

## Project Structure

```
opencode-tools/
  atlassian_mcp_server.py  # Confluence + Jira tools
  github_mcp_server.py     # GitHub tools
  .opencode/skills/        # Agent skill docs
  setup.sh                 # One-shot install
  .env.example             # Credential template
```

## License

MIT
