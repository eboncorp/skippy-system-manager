#!/usr/bin/env python3
"""
Yahoo Mail Utility v1.1.0
Access davidbiggers@yahoo.com via IMAP/SMTP

Usage:
    python3 yahoo_mail_v1.0.0.py status        # Show inbox status
    python3 yahoo_mail_v1.0.0.py recent [N]    # Show N recent emails (default 5)
    python3 yahoo_mail_v1.0.0.py send TO SUBJ  # Send email (reads body from stdin)
    python3 yahoo_mail_v1.0.0.py send TO SUBJ --attach FILE  # Send with attachment

Created: 2026-01-18
Updated: 2026-01-20 - Added attachment support
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import decode_header
import sys
import os
from datetime import datetime
import mimetypes


def load_env(path):
    """Load .env file manually."""
    env = {}
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    return env


# Load credentials from .env
_env = load_env("/home/dave/skippy/.env")

EMAIL = _env.get("YAHOO_EMAIL", "davidbiggers@yahoo.com")
PASSWORD = _env.get("YAHOO_APP_PASSWORD")
IMAP_SERVER = _env.get("YAHOO_IMAP_SERVER", "imap.mail.yahoo.com")
SMTP_SERVER = _env.get("YAHOO_SMTP_SERVER", "smtp.mail.yahoo.com")


def get_imap_connection():
    """Connect to Yahoo IMAP."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, 993)
    mail.login(EMAIL, PASSWORD)
    return mail


def decode_subject(subject):
    """Decode email subject."""
    if subject is None:
        return "(No Subject)"
    decoded = decode_header(subject)
    parts = []
    for content, encoding in decoded:
        if isinstance(content, bytes):
            parts.append(content.decode(encoding or 'utf-8', errors='replace'))
        else:
            parts.append(content)
    return ''.join(parts)


def status():
    """Show inbox status."""
    mail = get_imap_connection()
    mail.select("Inbox")

    # Total messages
    status, data = mail.search(None, "ALL")
    total = len(data[0].split()) if data[0] else 0

    # Unread messages
    status, data = mail.search(None, "UNSEEN")
    unread = len(data[0].split()) if data[0] else 0

    mail.logout()

    print(f"📧 Yahoo Mail: {EMAIL}")
    print(f"📬 Inbox: {total:,} messages")
    print(f"📩 Unread: {unread:,} messages")


def recent(count=5):
    """Show recent emails."""
    mail = get_imap_connection()
    mail.select("Inbox")

    status, data = mail.search(None, "ALL")
    msg_ids = data[0].split()

    if not msg_ids:
        print("No messages in inbox.")
        return

    # Get last N messages
    recent_ids = msg_ids[-count:][::-1]

    print(f"📧 Recent {len(recent_ids)} emails:\n")

    for msg_id in recent_ids:
        status, msg_data = mail.fetch(msg_id, "(RFC822.HEADER)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject = decode_subject(msg.get("Subject"))
        sender = msg.get("From", "Unknown")
        date = msg.get("Date", "Unknown")

        # Truncate long fields
        if len(subject) > 60:
            subject = subject[:57] + "..."
        if len(sender) > 40:
            sender = sender[:37] + "..."

        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Date: {date}")
        print("-" * 50)

    mail.logout()


def send_email(to, subject, body, attachment_path=None):
    """Send an email with optional attachment."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Add attachment if provided
    if attachment_path:
        if not os.path.exists(attachment_path):
            print(f"❌ Attachment not found: {attachment_path}")
            return False

        filename = os.path.basename(attachment_path)
        mime_type, _ = mimetypes.guess_type(attachment_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        main_type, sub_type = mime_type.split('/', 1)

        with open(attachment_path, 'rb') as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)

        print(f"📎 Attached: {filename}")

    server = smtplib.SMTP(SMTP_SERVER, 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

    print(f"✅ Email sent to {to}")
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        status()
    elif cmd == "recent":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        recent(count)
    elif cmd == "send":
        if len(sys.argv) < 4:
            print("Usage: yahoo_mail.py send TO SUBJECT [--attach FILE]")
            print("Body is read from stdin")
            return
        to = sys.argv[2]
        subject = sys.argv[3]

        # Check for --attach flag
        attachment = None
        if "--attach" in sys.argv:
            attach_idx = sys.argv.index("--attach")
            if attach_idx + 1 < len(sys.argv):
                attachment = sys.argv[attach_idx + 1]

        print("Enter message body (Ctrl+D to send):")
        body = sys.stdin.read()
        send_email(to, subject, body, attachment)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
