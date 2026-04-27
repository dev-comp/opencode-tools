# OpenCode Tools

MCP servers for OpenCode (formerly opencode-dev/opencode) that provide access to **GitHub**, **Atlassian** (Confluence + Jira), and **Google** (Drive + Gmail + Calendar).

## Features

- **32 tools** across 3 MCP servers (13 Atlassian, 10 GitHub, 9 Google)
- **Private by design** -- secrets stored in a local env file, never committed
- **Global installation** -- one config entry, available across all projects
- **Zero external dependencies** -- uses only Python stdlib + `mcp` + `requests`

## Quick Start

1. Clone this repo
2. Run `bash setup.sh`
3. Fill in your credentials in `.env`
4. Add servers to `~/.config/opencode/config.json`
5. Restart OpenCode

See the full how-to guide: https://pshapoval.atlassian.net/wiki/spaces/KB/pages/241926146/Connect+OpenCode+to+GitHub+and+Atlassian

## Available Tools

### Atlassian MCP (13 tools)

**Confluence** (7 tools):
- `confluence_search_pages` -- search pages by query, space, or label
- `confluence_get_page` -- read page content by ID
- `confluence_get_page_children` -- list child pages
- `confluence_create_page` -- create a new page
- `confluence_update_page` -- update an existing page
- `confluence_list_spaces` -- list all spaces
- `confluence_get_space` -- get space details

**Jira** (6 tools):
- `jira_search_issues` -- search issues via JQL
- `jira_get_issue` -- get issue details by key
- `jira_create_issue` -- create a new issue
- `jira_update_issue` -- update an existing issue
- `jira_list_projects` -- list projects
- `jira_list_statuses` -- list statuses

### GitHub MCP (10 tools)

- `list_repos` -- list org or user repositories
- `get_repo` -- get repository details
- `search_repos` -- search repositories
- `list_files` -- list files in a directory
- `read_file` -- read file content by path
- `create_file` -- create a new file with commit
- `update_file` -- update existing file (requires SHA)
- `delete_file` -- delete a file (requires SHA)
- `list_branches` -- list repository branches
- `create_branch` -- create a new branch

### Google MCP (9 tools)

**Drive** (3 tools):
- `google_drive_list_files` -- list files in a Drive folder
- `google_drive_read_file` -- read text file content
- `google_drive_create_file` -- create a new file

**Gmail** (3 tools):
- `google_gmail_search` -- search messages by query
- `google_gmail_read` -- read a message by ID
- `google_gmail_send` -- send an email

**Calendar** (3 tools):
- `google_calendar_list_events` -- list calendar events
- `google_calendar_create_event` -- create a new event
- `google_calendar_update_event` -- update an existing event

## Project Structure

```
opencode-tools/
  atlassian_mcp_server.py  # Confluence + Jira tools
  github_mcp_server.py     # GitHub tools
  google_mcp_server.py     # Google Drive + Gmail + Calendar tools
  .opencode/skills/        # Agent skill docs
  setup.sh                 # One-shot install
  .env.example             # Credential template
```

## Security Notes

- Never commit `.env` files or any files containing secrets
- Use fine-grained GitHub tokens with minimal scopes
- Use Atlassian Legacy tokens (not scoped tokens) for Basic Auth
- Set file permissions on `.env` to `600` (owner read/write only)

## License

MIT
