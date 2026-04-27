# GitHub

Use these Confluence and Jira tools to read and write Atlassian workspace content.
Use when asked to search, read, create, or update Confluence pages or Jira issues.

Additionally, this MCP server provides GitHub tools for repository, file, issue, and PR operations.
Use when asked to search repos, read/write files, manage issues, or handle pull requests on GitHub.

## GitHub Tools

### Repository

| Tool | Description |
|------|-------------|
| atlassian.github_list_repos | List org or user repositories |
| atlassian.github_get_repo | Get repository details |
| atlassian.github_search_repos | Search repositories |

### Files

| Tool | Description |
|------|-------------|
| atlassian.github_list_files | List files in a directory |
| atlassian.github_read_file | Read file content by path |
| atlassian.github_create_file | Create a new file with commit |
| atlassian.github_update_file | Update existing file (requires SHA) |
| atlassian.github_delete_file | Delete a file (requires SHA) |

### Branches

| Tool | Description |
|------|-------------|
| atlassian.github_list_branches | List repository branches |
| atlassian.github_create_branch | Create a new branch |

### Issues

| Tool | Description |
|------|-------------|
| atlassian.github_list_issues | List repo issues with filters |
| atlassian.github_get_issue | Get issue details by number |
| atlassian.github_create_issue | Create a new issue |
| atlassian.github_update_issue | Update issue fields |
| atlassian.github_list_issue_comments | List comments on an issue |
| atlassian.github_add_comment | Add a comment to issue or PR |

### Pull Requests

| Tool | Description |
|------|-------------|
| atlassian.github_list_pull_requests | List PRs with filters |
| atlassian.github_get_pull_request | Get PR details |
| atlassian.github_merge_pull_request | Merge a PR |
| atlassian.github_list_pr_comments | List review comments on PR |
| atlassian.github_create_pull_request | Create a new PR |

## Usage Notes

- File operations require the file SHA for updates and deletes - read first to get it
- Branch operations reference the target branch name
- Issues and PRs use numeric numbers, not keys
- Use `GITHUB_ORG` env var for org-scoped repos or `GITHUB_USER` for personal repos
- All tools return JSON - parse results before taking next action
- For file creation/update, content is UTF-8 encoded as base64 per GitHub API spec
