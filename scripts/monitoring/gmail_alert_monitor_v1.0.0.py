#!/home/dave/skippy/mcp-servers/general-server/.venv/bin/python
"""
Gmail Alert Monitor v1.0.0
Checks eboncorp@gmail.com for unread alerts and system notifications.

Purpose: Monitor inbox for critical alerts that need attention
Usage: gmail_alert_monitor_v1.0.0.py [--verbose] [--notify]
Dependencies: google-auth, google-auth-oauthlib, google-api-python-client

Created: 2026-01-13
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Google API imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
CREDENTIALS_DIR = Path.home() / ".config/skippy/credentials"
AUTH_FILE = CREDENTIALS_DIR / "google_auth_eboncorp.json"
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "client_secret.json"
LOG_DIR = Path("/home/dave/skippy/logs/monitoring")
LOG_FILE = LOG_DIR / "gmail_monitor.log"

# Alert keywords to watch for
ALERT_KEYWORDS = [
    "system alert",
    "ebon",
    "failed",
    "error",
    "warning",
    "critical",
    "backup",
    "disk",
    "memory",
    "docker",
    "service",
]

# Senders to prioritize
PRIORITY_SENDERS = [
    "ebon",
    "skippy",
    "cron",
    "root@",
    "noreply",
]


def log_message(message: str, level: str = "INFO"):
    """Log a message to file and optionally stdout."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"

    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

    if os.environ.get("VERBOSE") or level in ("WARNING", "ERROR"):
        print(log_entry)


def send_notification(title: str, message: str):
    """Send desktop notification if available."""
    try:
        import subprocess
        subprocess.run(
            ["notify-send", "-u", "normal", title, message],
            capture_output=True,
            timeout=5
        )
    except Exception:
        pass  # Notification not critical


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    if not AUTH_FILE.exists():
        log_message(f"Token file not found: {AUTH_FILE}", "ERROR")
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(AUTH_FILE))

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed token
            with open(AUTH_FILE, "w") as f:
                f.write(creds.to_json())
            log_message("Token refreshed successfully")
        except Exception as e:
            log_message(f"Failed to refresh token: {e}", "ERROR")
            sys.exit(1)

    return build("gmail", "v1", credentials=creds)


def get_unread_messages(service, max_results: int = 50):
    """Get unread messages from inbox."""
    try:
        results = service.users().messages().list(
            userId="me",
            q="is:unread",
            maxResults=max_results
        ).execute()

        messages = results.get("messages", [])
        return messages
    except Exception as e:
        log_message(f"Failed to fetch messages: {e}", "ERROR")
        return []


def get_message_details(service, msg_id: str):
    """Get message details including subject and sender."""
    try:
        msg = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()

        headers = msg.get("payload", {}).get("headers", [])
        details = {"id": msg_id}

        for header in headers:
            name = header.get("name", "").lower()
            if name == "subject":
                details["subject"] = header.get("value", "(no subject)")
            elif name == "from":
                details["from"] = header.get("value", "unknown")
            elif name == "date":
                details["date"] = header.get("value", "")

        return details
    except Exception as e:
        log_message(f"Failed to get message {msg_id}: {e}", "ERROR")
        return None


def is_alert_message(details: dict) -> bool:
    """Check if message appears to be a system alert."""
    subject = details.get("subject", "").lower()
    sender = details.get("from", "").lower()

    # Check for alert keywords in subject
    for keyword in ALERT_KEYWORDS:
        if keyword in subject:
            return True

    # Check for priority senders
    for priority in PRIORITY_SENDERS:
        if priority in sender:
            return True

    return False


def check_inbox(verbose: bool = False, notify: bool = False):
    """Main function to check inbox for alerts."""
    log_message("Starting Gmail alert check")

    service = get_gmail_service()
    messages = get_unread_messages(service)

    total_unread = len(messages)
    alerts = []

    if total_unread == 0:
        log_message("No unread messages")
        return

    log_message(f"Found {total_unread} unread messages")

    # Analyze each message
    for msg in messages:
        details = get_message_details(service, msg["id"])
        if details and is_alert_message(details):
            alerts.append(details)

    alert_count = len(alerts)

    # Report findings
    if alert_count > 0:
        log_message(f"Found {alert_count} alert messages requiring attention", "WARNING")

        # Log alert details
        for alert in alerts[:10]:  # Limit to first 10
            log_message(f"  - From: {alert.get('from', 'unknown')[:50]}")
            log_message(f"    Subject: {alert.get('subject', '(none)')[:60]}")

        if alert_count > 10:
            log_message(f"  ... and {alert_count - 10} more alerts")

        # Send notification if requested
        if notify:
            send_notification(
                "Gmail Alerts",
                f"{alert_count} alert(s) in eboncorp@gmail.com\n"
                f"Latest: {alerts[0].get('subject', '')[:40]}"
            )

        # Write summary to status file
        status_file = LOG_DIR / "gmail_status.json"
        status = {
            "last_check": datetime.now().isoformat(),
            "total_unread": total_unread,
            "alert_count": alert_count,
            "alerts": alerts[:10],
        }
        with open(status_file, "w") as f:
            json.dump(status, f, indent=2)
    else:
        log_message(f"No alert messages found ({total_unread} regular unread)")

    log_message("Gmail check complete")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor eboncorp@gmail.com for system alerts"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print all log messages to stdout"
    )
    parser.add_argument(
        "--notify", "-n",
        action="store_true",
        help="Send desktop notification if alerts found"
    )

    args = parser.parse_args()

    if args.verbose:
        os.environ["VERBOSE"] = "1"

    try:
        check_inbox(verbose=args.verbose, notify=args.notify)
    except Exception as e:
        log_message(f"Monitor failed: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
