#!/usr/bin/env python3
"""
Yahoo Mail Utility v2.0.0
Access davidbiggers@yahoo.com via IMAP/SMTP

Usage:
    python3 yahoo_mail_v1.0.0.py status        # Show inbox status
    python3 yahoo_mail_v1.0.0.py recent [N]    # Show N recent emails (default 5)
    python3 yahoo_mail_v1.0.0.py sent [N]      # Show N recent sent emails (default 5)
    python3 yahoo_mail_v1.0.0.py send TO SUBJ  # Send email (reads body from stdin)
    python3 yahoo_mail_v1.0.0.py send TO SUBJ --attach FILE  # Send with attachment
    python3 yahoo_mail_v1.0.0.py send TO SUBJ --attach FILE1 --attach FILE2  # Multiple
    python3 yahoo_mail_v1.0.0.py send TO SUBJ --yes  # Skip confirmation prompt

Flags:
    --yes           Skip confirmation prompt (auto-confirm)
    --force-empty   Allow empty body with attachments
    --attach FILE   Add attachment (can use multiple times)

SAFETY FEATURES (v2.0.0):
    1. Empty body check - blocks attachments without message body
    2. Send confirmation - shows preview, requires Y to send
    3. External recipient warning - confirms non-yahoo addresses
    4. Sensitive data scan - detects SSN, credit cards, passwords
    5. Subject line check - warns on empty/generic subjects
    6. Large attachment warning - warns if >10MB total
    7. Duplicate detection - warns if same email sent in last 24hrs

Created: 2026-01-18
Updated: 2026-01-24 - v2.0.0 with comprehensive safety checks
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
import re
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
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

# Safety config
SENT_LOG_FILE = Path.home() / ".cache" / "yahoo_mail_sent.json"
TRUSTED_DOMAINS = ["yahoo.com", "gmail.com", "outlook.com", "hotmail.com"]
GENERIC_SUBJECTS = ["test", "hi", "hello", "hey", ".", "...", "fwd", "re"]
MAX_ATTACHMENT_SIZE_MB = 10


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
    st, data = mail.search(None, "ALL")
    total = len(data[0].split()) if data[0] else 0

    # Unread messages
    st, data = mail.search(None, "UNSEEN")
    unread = len(data[0].split()) if data[0] else 0

    mail.logout()

    print(f"📧 Yahoo Mail: {EMAIL}")
    print(f"📬 Inbox: {total:,} messages")
    print(f"📩 Unread: {unread:,} messages")


def recent(count=5):
    """Show recent emails."""
    mail = get_imap_connection()
    mail.select("Inbox")

    st, data = mail.search(None, "ALL")
    msg_ids = data[0].split()

    if not msg_ids:
        print("No messages in inbox.")
        return

    recent_ids = msg_ids[-count:][::-1]
    print(f"📧 Recent {len(recent_ids)} emails:\n")

    for msg_id in recent_ids:
        st, msg_data = mail.fetch(msg_id, "(RFC822.HEADER)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject = decode_subject(msg.get("Subject"))
        sender = msg.get("From", "Unknown")
        date = msg.get("Date", "Unknown")

        if len(subject) > 60:
            subject = subject[:57] + "..."
        if len(sender) > 40:
            sender = sender[:37] + "..."

        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print(f"Date: {date}")
        print("-" * 50)

    mail.logout()


def sent(count=5):
    """Show recent sent emails."""
    mail = get_imap_connection()
    mail.select('"Sent"')

    st, data = mail.search(None, "ALL")
    msg_ids = data[0].split()

    if not msg_ids:
        print("No messages in sent folder.")
        return

    recent_ids = msg_ids[-count:][::-1]
    print(f"📤 Recent {len(recent_ids)} sent emails:\n")

    for msg_id in recent_ids:
        st, msg_data = mail.fetch(msg_id, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        subject = decode_subject(msg.get("Subject"))
        recipient = msg.get("To", "Unknown")
        date = msg.get("Date", "Unknown")

        # Get body length
        body_len = 0
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_len = len(payload.decode('utf-8', errors='replace').strip())
                    break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body_len = len(payload.decode('utf-8', errors='replace').strip())

        if len(subject) > 50:
            subject = subject[:47] + "..."
        if len(recipient) > 35:
            recipient = recipient[:32] + "..."

        body_status = f"✅ {body_len} chars" if body_len > 0 else "⚠️ EMPTY"

        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Body: {body_status}")
        print(f"Date: {date}")
        print("-" * 50)

    mail.logout()


# ============== SAFETY CHECKS ==============

def check_sensitive_data(text):
    """Scan for sensitive data patterns. Returns list of warnings."""
    warnings = []

    # SSN pattern (XXX-XX-XXXX)
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
        warnings.append("⚠️  SENSITIVE: Possible SSN detected")

    # Credit card patterns (16 digits, with or without spaces/dashes)
    if re.search(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', text):
        warnings.append("⚠️  SENSITIVE: Possible credit card number detected")

    # Password patterns
    if re.search(r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+', text):
        warnings.append("⚠️  SENSITIVE: Possible password detected")

    # API key patterns
    if re.search(r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*\S+', text):
        warnings.append("⚠️  SENSITIVE: Possible API key/token detected")

    return warnings


def check_subject(subject):
    """Check subject line quality. Returns list of warnings."""
    warnings = []

    if not subject or not subject.strip():
        warnings.append("⚠️  SUBJECT: Empty subject line")
    elif subject.lower().strip() in GENERIC_SUBJECTS:
        warnings.append(f"⚠️  SUBJECT: Generic subject '{subject}' - consider being more specific")
    elif len(subject) < 5:
        warnings.append("⚠️  SUBJECT: Very short subject line")

    return warnings


def check_recipient(to_addr):
    """Check recipient address. Returns list of warnings."""
    warnings = []

    # Extract domain
    match = re.search(r'@([\w.-]+)', to_addr)
    if match:
        domain = match.group(1).lower()
        if domain not in TRUSTED_DOMAINS:
            warnings.append(f"⚠️  EXTERNAL: Sending to external domain @{domain}")

    # Basic email format check
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', to_addr):
        warnings.append("❌ INVALID: Email address format looks incorrect")

    return warnings


def check_attachments(attachment_paths):
    """Check attachments. Returns (total_size_mb, warnings)."""
    warnings = []
    total_size = 0

    for path in attachment_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size

            # Check for sensitive filenames
            fname = os.path.basename(path).lower()
            if any(s in fname for s in ['password', 'credential', 'secret', '.env', 'private']):
                warnings.append(f"⚠️  SENSITIVE FILE: {fname}")

    total_mb = total_size / (1024 * 1024)
    if total_mb > MAX_ATTACHMENT_SIZE_MB:
        warnings.append(f"⚠️  LARGE: Total attachments {total_mb:.1f}MB (>{MAX_ATTACHMENT_SIZE_MB}MB)")

    return total_mb, warnings


def check_duplicate(to_addr, subject):
    """Check if similar email was sent recently. Returns warning or None."""
    SENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create hash of recipient + subject
    email_hash = hashlib.md5(f"{to_addr}:{subject}".lower().encode()).hexdigest()

    # Load sent log
    sent_log = {}
    if SENT_LOG_FILE.exists():
        try:
            sent_log = json.loads(SENT_LOG_FILE.read_text())
        except:
            sent_log = {}

    # Check for recent duplicate
    if email_hash in sent_log:
        last_sent = datetime.fromisoformat(sent_log[email_hash])
        if datetime.now() - last_sent < timedelta(hours=24):
            hours_ago = (datetime.now() - last_sent).total_seconds() / 3600
            return f"⚠️  DUPLICATE: Similar email sent {hours_ago:.1f} hours ago"

    return None


def log_sent_email(to_addr, subject):
    """Log sent email for duplicate detection."""
    SENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    email_hash = hashlib.md5(f"{to_addr}:{subject}".lower().encode()).hexdigest()

    sent_log = {}
    if SENT_LOG_FILE.exists():
        try:
            sent_log = json.loads(SENT_LOG_FILE.read_text())
        except:
            sent_log = {}

    sent_log[email_hash] = datetime.now().isoformat()

    # Keep only last 100 entries
    if len(sent_log) > 100:
        sorted_items = sorted(sent_log.items(), key=lambda x: x[1], reverse=True)
        sent_log = dict(sorted_items[:100])

    SENT_LOG_FILE.write_text(json.dumps(sent_log, indent=2))


def show_send_preview(to, subject, body, attachments, warnings):
    """Show email preview with all warnings."""
    print("\n" + "=" * 60)
    print("📧 EMAIL PREVIEW")
    print("=" * 60)
    print(f"From: {EMAIL}")
    print(f"To:   {to}")
    print(f"Subj: {subject}")
    print("-" * 60)

    if attachments:
        print(f"Attachments ({len(attachments)}):")
        for a in attachments:
            size = os.path.getsize(a) / 1024 if os.path.exists(a) else 0
            print(f"  📎 {os.path.basename(a)} ({size:.1f} KB)")
        print("-" * 60)

    body_preview = body.strip()[:500] if body else "(empty)"
    if len(body.strip()) > 500:
        body_preview += "..."
    print(f"Body ({len(body.strip())} chars):")
    print(body_preview)
    print("-" * 60)

    if warnings:
        print("\n⚠️  WARNINGS:")
        for w in warnings:
            print(f"  {w}")
        print()

    print("=" * 60)


def send_email(to, subject, body, attachments=None, force_empty=False, auto_confirm=False):
    """Send an email with comprehensive safety checks."""

    # Normalize attachments
    if attachments is None:
        attachments = []
    elif isinstance(attachments, str):
        attachments = [attachments]

    body_stripped = body.strip() if body else ""
    has_attachments = len(attachments) > 0

    # Collect all warnings
    all_warnings = []

    # 1. Empty body check
    if not body_stripped and has_attachments and not force_empty:
        print("❌ BLOCKED: Cannot send attachments with empty message body!")
        print("   To override, use --force-empty flag")
        return False

    if not body_stripped and not has_attachments:
        print("❌ BLOCKED: Cannot send email with empty body and no attachments!")
        return False

    # 2. Subject check
    all_warnings.extend(check_subject(subject))

    # 3. Recipient check
    all_warnings.extend(check_recipient(to))

    # 4. Sensitive data scan (body)
    all_warnings.extend(check_sensitive_data(body))

    # 5. Attachment checks (size + sensitive filenames)
    if attachments:
        total_mb, attach_warnings = check_attachments(attachments)
        all_warnings.extend(attach_warnings)

        # Also scan text-based attachments for sensitive data
        for path in attachments:
            if os.path.exists(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.txt', '.md', '.csv', '.json', '.xml', '.html']:
                    try:
                        content = Path(path).read_text(errors='replace')[:10000]
                        file_warnings = check_sensitive_data(content)
                        for w in file_warnings:
                            all_warnings.append(f"{w} (in {os.path.basename(path)})")
                    except:
                        pass

    # 6. Duplicate check
    dup_warning = check_duplicate(to, subject)
    if dup_warning:
        all_warnings.append(dup_warning)

    # Show preview
    show_send_preview(to, subject, body, attachments, all_warnings)

    # 7. Confirmation prompt
    if not auto_confirm:
        has_critical = any("❌" in w or "SENSITIVE" in w for w in all_warnings)
        prompt = "Send this email? [y/N]: " if has_critical else "Send this email? [Y/n]: "
        default = "n" if has_critical else "y"

        try:
            response = input(prompt).strip().lower() or default
        except EOFError:
            response = default

        if response != 'y':
            print("❌ Email cancelled.")
            return False

    # Build and send email
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    for attachment_path in attachments:
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

    server = smtplib.SMTP(SMTP_SERVER, 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

    # Log for duplicate detection
    log_sent_email(to, subject)

    print(f"\n✅ Email sent to {to}")
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
    elif cmd == "sent":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        sent(count)
    elif cmd == "send":
        if len(sys.argv) < 4:
            print("Usage: yahoo_mail.py send TO SUBJECT [--attach FILE] [--yes] [--force-empty]")
            print("Body is read from stdin")
            return

        to = sys.argv[2]
        subject = sys.argv[3]

        attachments = []
        force_empty = False
        auto_confirm = False
        args = sys.argv[4:]
        i = 0
        while i < len(args):
            if args[i] == "--attach" and i + 1 < len(args):
                attachments.append(args[i + 1])
                i += 2
            elif args[i] == "--force-empty":
                force_empty = True
                i += 1
            elif args[i] == "--yes" or args[i] == "-y":
                auto_confirm = True
                i += 1
            else:
                i += 1

        print("Enter message body (Ctrl+D when done):")
        body = sys.stdin.read()
        send_email(to, subject, body, attachments if attachments else None,
                   force_empty=force_empty, auto_confirm=auto_confirm)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
