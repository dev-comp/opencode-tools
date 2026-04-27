---
name: atlassian
description: Use Confluence and Jira tools to read and write Atlassian workspace content. Use when asked to search, read, create, or update Confluence pages or Jira issues.
license: MIT
---

## What I do

This skill teaches you to use the Atlassian MCP server tools for Confluence and Jira operations.

### Confluence Tools

| Tool | Purpose |
|------|---------|
| `confluence_search_pages` | Search pages by query, space key, or label |
| `confluence_get_page` | Read a page by its numeric ID |
| `confluence_get_page_children` | List child pages of a given page |
| `confluence_create_page` | Create a new page in a space |
| `confluence_update_page` | Update an existing page |
| `confluence_list_spaces` | List available spaces |
| `confluence_get_space` | Get details about a space |

### Jira Tools

| Tool | Purpose |
|------|---------|
| `jira_search_issues` | Search issues via JQL |
| `jira_get_issue` | Get issue details by key (e.g. DEV-123) |
| `jira_create_issue` | Create a new issue |
| `jira_update_issue` | Update an existing issue |
| `jira_list_projects` | List projects |
| `jira_list_statuses` | List available statuses |

## When to use me

- User asks to search, read, create, or update Confluence pages
- User asks about Jira issues, projects, or statuses
- User mentions Confluence spaces, pages, or wiki content
- User mentions Jira tickets, boards, or sprint work

## Common patterns

### Searching Confluence pages
1. Use `confluence_search_pages` with a query or space key
2. From results, extract the `id` needed for read/write operations
3. Use `confluence_get_page` with the page ID

### Creating a Confluence page
1. Optionally use `confluence_list_spaces` to confirm the space key
2. Use `confluence_create_page` with space_key, title, and body
3. Body supports Confluence Storage Format (wiki markup) or plain text

### Working with Jira
1. Use `jira_list_projects` to find project keys
2. Use `jira_search_issues` with JQL for targeted searches
3. Use `jira_get_issue` with the issue key for full details
4. Use `jira_create_issue` to create new issues

## Tips

- Page IDs in Confluence are numeric, not the human-readable URL slug
- JQL syntax: `project = "KEY" AND status = "Open" AND assignee = currentUser()`
- Use `body_format="plain"` for simple text, `body_format="storage"` for wiki markup
- If a space or project key is unknown, list them first with the respective list tool
- Error messages from the MCP tools contain helpful diagnostic information
