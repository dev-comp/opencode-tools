#!/home/ikka/git/ai-test/qwen36b/opencode-tools/.venv/bin/python3
"""Google MCP Server for OpenCode.

Provides Google Drive, Gmail, and Calendar tools via the Model Context Protocol (MCP).
Run as a local MCP server in OpenCode.

Environment variables:
  GOOGLE_CREDENTIALS         - Path to Google service account JSON or OAuth2 credentials JSON
  GOOGLE_SERVICE_ACCOUNT     - Service account email (for service account auth)
  GOOGLE_DOMAIN              - Google Workspace domain (for domain-wide delegation)

For service account auth:
  1. Create a service account at https://console.cloud.google.com/iam-admin/serviceaccounts
  2. Create a JSON key and save as GOOGLE_CREDENTIALS path
  3. Enable Drive, Gmail, Calendar APIs for your project
  4. If using Workspace, delegate domain-wide authority

For OAuth2 user auth:
  1. Create OAuth2 credentials at https://console.cloud.google.com/apis/credentials
  2. Save client_secret.json and use GOOGLE_CREDENTIALS to point to it
  3. First run triggers a browser OAuth flow to produce credentials.json
"""

import json
import os
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Google", json_response=True)

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _get_google_config():
    """Return credentials path or None if not configured."""
    cred_path = os.environ.get("GOOGLE_CREDENTIALS", "").strip()
    if not cred_path:
        return None
    if not os.path.exists(cred_path):
        return None
    return cred_path


def _load_credentials(cred_path):
    """Load Google credentials from JSON file."""
    try:
        from google.oauth2.service_account import Credentials as ServiceAccountCredentials
        with open(cred_path) as f:
            data = json.load(f)

        service_account = os.environ.get("GOOGLE_SERVICE_ACCOUNT", "")
        domain = os.environ.get("GOOGLE_DOMAIN", "")

        scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar",
        ]

        creds = ServiceAccountCredentials.from_service_account_file(
            cred_path, scopes=scopes
        )
        if service_account and domain:
            creds = creds.with_subject(service_account)
        return {"type": "service_account", "creds": creds}
    except ImportError:
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import Flow
            # Try user OAuth2 flow
            flow = Flow.from_client_secrets_file(cred_path, scopes=scopes)
            flow.redirect_uri = "http://localhost:8080"
            return {"type": "oauth2", "flow": flow, "creds": None}
        except Exception:
            return None
    except Exception as e:
        return None

# ---------------------------------------------------------------------------
# Google Drive tools
# ---------------------------------------------------------------------------

@mcp.tool()
def google_drive_list_files(
    folder_id: str | None = None,
    query: str | None = None,
    limit: int = 10,
) -> str:
    """List files in a Google Drive folder.

    Args:
        folder_id: Drive folder ID. If omitted, lists root folder.
        query: Optional search query (e.g. 'name contains "report"').
        limit: Maximum number of results (1-100, default 10).

    Returns:
        JSON list of files with id, name, type, and web_link.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured. Set GOOGLE_CREDENTIALS."})

    try:
        from googleapiclient.discovery import build
        drive = build("drive", "v3", credentials=config["creds"])
        params = {"pageSize": min(limit, 100)}
        if folder_id:
            params["q"] = f"'{folder_id}' in parents"
        if query:
            if folder_id:
                params["q"] += f" and {query}"
            else:
                params["q"] = query
        params["fields"] = "files(id, name, mimeType, modifiedTime, size, webViewLink, parents)"

        results = drive.files().list(**params).execute()
        files = results.get("files", [])
        output = []
        for f in files:
            output.append({
                "id": f.get("id"),
                "name": f.get("name"),
                "type": f.get("mimeType"),
                "modified": f.get("modifiedTime"),
                "web_link": f.get("webViewLink"),
            })
        return json.dumps(output, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def google_drive_read_file(
    file_id: str,
) -> str:
    """Read the content of a Google Drive file.

    Args:
        file_id: The Drive file ID.

    Returns:
        JSON with filename, type, and content (for text files).
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io
        drive = build("drive", "v3", credentials=config["creds"])
        file_meta = drive.files().get(fileId=file_id, fields="name, mimeType").execute()
        if file_meta.get("mimeType") != "text/plain":
            return json.dumps({
                "error": "Not a text file",
                "mimeType": file_meta.get("mimeType"),
                "name": file_meta.get("name"),
                "note": "Use download link for binary files",
                "webViewLink": file_meta.get("webViewLink"),
            })

        request = drive.files().export_media(fileId=file_id, mimeType="text/plain")
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        content = fh.getvalue().decode("utf-8", errors="replace")
        return json.dumps({
            "name": file_meta.get("name"),
            "content": content,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def google_drive_create_file(
    name: str,
    content: str,
    folder_id: str | None = None,
    mime_type: str = "text/plain",
) -> str:
    """Create a new file in Google Drive.

    Args:
        name: File name.
        content: File content.
        folder_id: Parent folder ID (optional).
        mime_type: MIME type (default: text/plain).

    Returns:
        JSON with file id, name, and web link.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaStringUpload
        drive = build("drive", "v3", credentials=config["creds"])
        file_metadata = {"name": name}
        if folder_id:
            file_metadata["parents"] = [folder_id]
        media = MediaStringUpload(content, mimetype=mime_type)
        file = drive.files().create(body=file_metadata, media_body=media, fields="id, name, webViewLink").execute()
        return json.dumps({
            "id": file.get("id"),
            "name": file.get("name"),
            "web_link": file.get("webViewLink"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Gmail tools
# ---------------------------------------------------------------------------

@mcp.tool()
def google_gmail_search(
    query: str,
    max_results: int = 10,
) -> str:
    """Search Gmail messages.

    Args:
        query: Gmail search query (supports Gmail operators).
        max_results: Maximum number of results (1-100, default 10).

    Returns:
        JSON list of messages with id, subject, sender, date, and snippet.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        from googleapiclient.discovery import build
        gmail = build("gmail", "v1", credentials=config["creds"])
        results = gmail.users().messages().list(
            userId="me", q=query, maxResults=min(max_results, 100)
        ).execute()
        messages = results.get("messages", [])
        output = []
        for msg in messages:
            msg_data = gmail.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataFields="snippet,from,subject,date"
            ).execute()
            payload = msg_data.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
            output.append({
                "id": msg_data.get("id"),
                "thread_id": msg_data.get("threadId"),
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
                "snippet": msg_data.get("snippet", ""),
            })
        return json.dumps(output, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def google_gmail_read(
    message_id: str,
) -> str:
    """Read a Gmail message.

    Args:
        message_id: Gmail message ID.

    Returns:
        JSON with subject, sender, date, and full body.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        from googleapiclient.discovery import build
        gmail = build("gmail", "v1", credentials=config["creds"])
        msg = gmail.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        body = ""
        if payload.get("parts"):
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    import base64
                    body = base64.b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    break
        elif payload.get("body", {}).get("data"):
            import base64
            body = base64.b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        return json.dumps({
            "id": msg.get("id"),
            "subject": headers.get("Subject", ""),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "date": headers.get("Date", ""),
            "body": body,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def google_gmail_send(
    to: str,
    subject: str,
    body: str,
    cc: str | None = None,
) -> str:
    """Send a Gmail message.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body (plain text or HTML).
        cc: CC recipient (optional).

    Returns:
        JSON with message id, thread id, and status.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        import base64
        from email.mime.text import MIMEText
        from googleapiclient.discovery import build
        gmail = build("gmail", "v1", credentials=config["creds"])
        msg = MIMEText(body, "html" if "<html" in body.lower() else "plain")
        msg["to"] = to
        msg["subject"] = subject
        if cc:
            msg["cc"] = cc
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        sent_msg = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
        return json.dumps({
            "id": sent_msg.get("id"),
            "thread_id": sent_msg.get("threadId"),
            "status": "sent",
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Google Calendar tools
# ---------------------------------------------------------------------------

@mcp.tool()
def google_calendar_list_events(
    calendar_id: str = "primary",
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 10,
) -> str:
    """List calendar events.

    Args:
        calendar_id: Calendar ID (default: 'primary').
        time_min: Start time in ISO 8601 format (e.g. '2026-01-01T00:00:00Z').
        time_max: End time in ISO 8601 format.
        max_results: Maximum results (1-250, default 10).

    Returns:
        JSON list of events with summary, start, end, and location.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        from googleapiclient.discovery import build
        from datetime import datetime, timezone
        cal = build("calendar", "v3", credentials=config["creds"])

        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
        if not time_max:
            time_max = (datetime.now(timezone.utc) + __import__("datetime").timedelta(days=7)).isoformat()

        events = cal.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=min(max_results, 250),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        items = events.get("items", [])
        output = []
        for evt in items:
            start = evt.get("start", {})
            end = evt.get("end", {})
            output.append({
                "id": evt.get("id"),
                "summary": evt.get("summary", "Untitled"),
                "start": start.get("dateTime") or start.get("date"),
                "end": end.get("dateTime") or end.get("date"),
                "location": evt.get("location", ""),
                "description": evt.get("description", ""),
                "html_link": evt.get("htmlLink"),
            })
        return json.dumps(output, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def google_calendar_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    attendees: list[str] | None = None,
) -> str:
    """Create a calendar event.

    Args:
        summary: Event title.
        start_time: Start time in ISO 8601 format.
        end_time: End time in ISO 8601 format.
        description: Event description.
        location: Event location.
        attendees: List of attendee email addresses.

    Returns:
        JSON with event id, summary, start/end times, and link.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        from googleapiclient.discovery import build
        cal = build("calendar", "v3", credentials=config["creds"])
        event = {
            "summary": summary,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if attendees:
            event["attendees"] = [{"email": a} for a in attendees]

        created = cal.events().insert(calendarId="primary", body=event).execute()
        return json.dumps({
            "id": created.get("id"),
            "summary": created.get("summary"),
            "start": created.get("start", {}).get("dateTime"),
            "end": created.get("end", {}).get("dateTime"),
            "html_link": created.get("htmlLink"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def google_calendar_update_event(
    event_id: str,
    summary: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    description: str | None = None,
    location: str | None = None,
) -> str:
    """Update a calendar event.

    Args:
        event_id: Calendar event ID.
        summary: New title (optional).
        start_time: New start time (optional).
        end_time: New end time (optional).
        description: New description (optional).
        location: New location (optional).

    Returns:
        JSON with updated event details.
    """
    config = _get_google_config()
    if config is None:
        return json.dumps({"error": "Google not configured."})

    try:
        from googleapiclient.discovery import build
        cal = build("calendar", "v3", credentials=config["creds"])
        event = cal.events().get(calendarId="primary", eventId=event_id).execute()
        if summary is not None:
            event["summary"] = summary
        if start_time is not None:
            event["start"] = {"dateTime": start_time}
        if end_time is not None:
            event["end"] = {"dateTime": end_time}
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location

        updated = cal.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        return json.dumps({
            "id": updated.get("id"),
            "summary": updated.get("summary"),
            "start": updated.get("start", {}).get("dateTime"),
            "end": updated.get("end", {}).get("dateTime"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if _get_google_config() is None:
        print("ERROR: Google not configured.", file=sys.stderr)
        print("Set GOOGLE_CREDENTIALS to path of a service account or OAuth2 JSON file.", file=sys.stderr)
        sys.exit(1)

    mcp.run(transport="stdio")
