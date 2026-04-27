# Google

Use these tools to interact with Google services (Drive, Gmail, Calendar).
Use when asked to read/write files in Google Drive, search/send emails, or manage calendar events.

## Prerequisites

Set up Google API access before using these tools:

1. Go to https://console.cloud.google.com/
2. Create a project (or select existing)
3. Enable APIs: Google Drive, Gmail, Google Calendar
4. Create credentials:
   - **Service account** (recommended) -- create JSON key, enable domain-wide delegation for Workspace
   - **OAuth2** -- create client ID, run the server once to authorize, then use the produced credentials.json
5. Set `GOOGLE_CREDENTIALS` environment variable to the path of the JSON file

## Available Tools

### Google Drive (3 tools)

| Tool | Description |
|------|-------------|
| google_drive_list_files | List files in a Drive folder |
| google_drive_read_file | Read text file content |
| google_drive_create_file | Create a new file |

### Gmail (3 tools)

| Tool | Description |
|------|-------------|
| google_gmail_search | Search messages by query |
| google_gmail_read | Read a message by ID |
| google_gmail_send | Send an email |

### Google Calendar (3 tools)

| Tool | Description |
|------|-------------|
| google_calendar_list_events | List calendar events |
| google_calendar_create_event | Create a new event |
| google_calendar_update_event | Update an existing event |

## Usage Notes

- File IDs in Drive are long alphanumeric strings, not URLs
- Gmail search supports Gmail operators (e.g. `from:john@example.com`)
- Calendar times should be ISO 8601 format (e.g. `2026-04-28T10:00:00Z`)
- Default calendar is "primary" -- use a specific ID for shared calendars
- All tools return JSON -- parse results before taking next action
