# Security Review

Use this skill when reviewing code changes, diffs, or push requests for security vulnerabilities.

## Available Tools

### Confluence

| Tool | Purpose |
|------|---------|
| atlassian.confluence_search_pages | Search pages by query, space key, or label |
| atlassian.confluence_get_page | Read a page by its numeric ID |
| atlassian.confluence_get_page_children | List child pages of a given page |
| atlassian.confluence_create_page | Create a new page in a space |
| atlassian.confluence_update_page | Update an existing page |
| atlassian.confluence_list_spaces | List available spaces |
| atlassian.confluence_get_space | Get details about a space |

### Jira

| Tool | Purpose |
|------|---------|
| atlassian.jira_search_issues | Search issues via JQL |
| atlassian.jira_get_issue | Get issue details by key (e.g. DEV-123) |
| atlassian.jira_create_issue | Create a new issue |
| atlassian.jira_update_issue | Update an existing issue |
| atlassian.jira_list_projects | List projects |
| atlassian.jira_list_statuses | List available statuses |

### GitHub

| Tool | Purpose |
|------|---------|
| atlassian.github_list_repos | List org or user repositories |
| atlassian.github_get_repo | Get repository details |
| atlassian.github_search_repos | Search repositories |
| atlassian.github_list_files | List files in a directory |
| atlassian.github_read_file | Read file content by path |
| atlassian.github_create_file | Create a new file with commit |
| atlassian.github_update_file | Update existing file (requires SHA) |
| atlassian.github_delete_file | Delete a file (requires SHA) |
| atlassian.github_list_branches | List repository branches |
| atlassian.github_create_branch | Create a new branch |
| atlassian.github_list_issues | List repo issues with filters |
| atlassian.github_get_issue | Get issue details by number |
| atlassian.github_create_issue | Create a new issue |
| atlassian.github_update_issue | Update issue fields |
| atlassian.github_list_issue_comments | List comments on an issue |
| atlassian.github_add_comment | Add a comment to issue or PR |
| atlassian.github_list_pull_requests | List PRs with filters |
| atlassian.github_get_pull_request | Get PR details |
| atlassian.github_merge_pull_request | Merge a PR |
| atlassian.github_list_pr_comments | List review comments on PR |
| atlassian.github_create_pull_request | Create a new PR |

## When to use me

- User asks to review a diff, commit, or pull request for security issues
- User mentions vulnerabilities, secrets, credentials, or code safety
- User asks to audit changes before merging

## Review checklist

### Secrets and credentials
- Look for hardcoded API keys, tokens, passwords in source code
- Check for credentials in config files, environment variables, or .env files
- Verify .gitignore includes sensitive files (.env, credentials, secrets/)
- Check for SSH keys or private keys committed to the repo

### Injection vulnerabilities
- SQL injection: unescaped user input in SQL queries
- Command injection: shell commands built from user input
- XSS: user content rendered without sanitization
- Path traversal: file paths constructed from user input

### Authentication and authorization
- Check for proper auth checks before sensitive operations
- Verify least-privilege access patterns
- Look for overly permissive CORS policies or public endpoints

### Dependencies and supply chain
- Check for outdated or known-vulnerable packages
- Review dependency updates in PRs
- Look for lock file changes that introduce new dependencies

### Data handling
- Verify proper logging (no sensitive data in logs)
- Check encryption of sensitive data at rest and in transit
- Look for proper data validation and sanitization

## Tips

- Start by reading the changed files, not just the diff
- Pay special attention to new files and new functions
- Check if secrets are being committed that should be in env vars
- When creating security findings, use `atlassian.jira_create_issue` to track them
