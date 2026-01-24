#!/usr/bin/env python3
"""
Universal Email Sender v1.0.0
Send emails via any configured SMTP account with comprehensive safety checks.

Usage:
    send_email.py --account yahoo TO SUBJECT    # Use Yahoo account
    send_email.py --account gmail TO SUBJECT    # Use Gmail account
    send_email.py TO SUBJECT                    # Use default account (yahoo)
    send_email.py --list                        # List configured accounts

Options:
    --account NAME   Use specific email account (yahoo, gmail, outlook)
    --attach FILE    Add attachment (can use multiple times)
    --yes            Skip confirmation prompt
    --force-empty    Allow empty body with attachments
    --list           List configured accounts

SAFETY FEATURES:
    1. Empty body check - blocks attachments without message body
    2. Send confirmation - shows preview, requires Y to send
    3. External recipient warning - confirms external domains
    4. Sensitive data scan - detects SSN, credit cards, passwords
    5. Subject line check - warns on empty/generic subjects
    6. Large attachment warning - warns if >10MB total
    7. Duplicate detection - warns if same email sent in last 24hrs

Configuration:
    Add accounts to /home/dave/skippy/.env:
        YAHOO_EMAIL=davidbiggers@yahoo.com
        YAHOO_APP_PASSWORD=xxxx
        GMAIL_EMAIL=eboncorp@gmail.com
        GMAIL_APP_PASSWORD=xxxx
        OUTLOOK_EMAIL=dave@outlook.com
        OUTLOOK_APP_PASSWORD=xxxx

Created: 2026-01-24
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
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


# Load credentials
_env = load_env("/home/dave/skippy/.env")

# Email account configurations
ACCOUNTS = {
    "yahoo": {
        "email": _env.get("YAHOO_EMAIL", ""),
        "password": _env.get("YAHOO_APP_PASSWORD", ""),
        "smtp_server": "smtp.mail.yahoo.com",
        "smtp_port": 587,
    },
    "gmail": {
        "email": _env.get("GMAIL_EMAIL", ""),
        "password": _env.get("GMAIL_APP_PASSWORD", ""),
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
    },
    "outlook": {
        "email": _env.get("OUTLOOK_EMAIL", ""),
        "password": _env.get("OUTLOOK_APP_PASSWORD", ""),
        "smtp_server": "smtp.office365.com",
        "smtp_port": 587,
    },
}

DEFAULT_ACCOUNT = "yahoo"

# Safety config
SENT_LOG_FILE = Path.home() / ".cache" / "email_sent_log.json"
TRUSTED_DOMAINS = ["yahoo.com", "gmail.com", "outlook.com", "hotmail.com", "bpa.tax"]
GENERIC_SUBJECTS = ["test", "hi", "hello", "hey", ".", "...", "fwd", "re"]
MAX_ATTACHMENT_SIZE_MB = 10


# ============== SAFETY CHECKS ==============

def check_sensitive_data(text):
    """Scan for sensitive data patterns."""
    warnings = []
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
        warnings.append("⚠️  SENSITIVE: Possible SSN detected")
    if re.search(r'\b(?:\d{4}[-\s]?){3}\d{4}\b', text):
        warnings.append("⚠️  SENSITIVE: Possible credit card number detected")
    if re.search(r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+', text):
        warnings.append("⚠️  SENSITIVE: Possible password detected")
    if re.search(r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*\S+', text):
        warnings.append("⚠️  SENSITIVE: Possible API key/token detected")
    return warnings


def check_subject(subject):
    """Check subject line quality."""
    warnings = []
    if not subject or not subject.strip():
        warnings.append("⚠️  SUBJECT: Empty subject line")
    elif subject.lower().strip() in GENERIC_SUBJECTS:
        warnings.append(f"⚠️  SUBJECT: Generic subject '{subject}'")
    elif len(subject) < 5:
        warnings.append("⚠️  SUBJECT: Very short subject line")
    return warnings


def check_recipient(to_addr):
    """Check recipient address."""
    warnings = []
    match = re.search(r'@([\w.-]+)', to_addr)
    if match:
        domain = match.group(1).lower()
        if domain not in TRUSTED_DOMAINS:
            warnings.append(f"⚠️  EXTERNAL: Sending to @{domain}")
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', to_addr):
        warnings.append("❌ INVALID: Email address format incorrect")
    return warnings


def check_attachments(attachment_paths):
    """Check attachments for size and sensitive filenames."""
    warnings = []
    total_size = 0
    for path in attachment_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            total_size += size
            fname = os.path.basename(path).lower()
            if any(s in fname for s in ['password', 'credential', 'secret', '.env', 'private']):
                warnings.append(f"⚠️  SENSITIVE FILE: {fname}")
    total_mb = total_size / (1024 * 1024)
    if total_mb > MAX_ATTACHMENT_SIZE_MB:
        warnings.append(f"⚠️  LARGE: Total {total_mb:.1f}MB (>{MAX_ATTACHMENT_SIZE_MB}MB)")
    return total_mb, warnings


def check_duplicate(to_addr, subject):
    """Check if similar email was sent recently."""
    SENT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    email_hash = hashlib.md5(f"{to_addr}:{subject}".lower().encode()).hexdigest()
    sent_log = {}
    if SENT_LOG_FILE.exists():
        try:
            sent_log = json.loads(SENT_LOG_FILE.read_text())
        except:
            pass
    if email_hash in sent_log:
        last_sent = datetime.fromisoformat(sent_log[email_hash])
        if datetime.now() - last_sent < timedelta(hours=24):
            hours_ago = (datetime.now() - last_sent).total_seconds() / 3600
            return f"⚠️  DUPLICATE: Similar email sent {hours_ago:.1f}h ago"
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
            pass
    sent_log[email_hash] = datetime.now().isoformat()
    if len(sent_log) > 100:
        sorted_items = sorted(sent_log.items(), key=lambda x: x[1], reverse=True)
        sent_log = dict(sorted_items[:100])
    SENT_LOG_FILE.write_text(json.dumps(sent_log, indent=2))


def show_preview(account_name, from_email, to, subject, body, attachments, warnings):
    """Show email preview."""
    print("\n" + "=" * 60)
    print(f"📧 EMAIL PREVIEW ({account_name.upper()})")
    print("=" * 60)
    print(f"From: {from_email}")
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
    print("=" * 60)


def send_email(account_name, to, subject, body, attachments=None, force_empty=False, auto_confirm=False):
    """Send email with safety checks."""

    # Get account config
    if account_name not in ACCOUNTS:
        print(f"❌ Unknown account: {account_name}")
        print(f"   Available: {', '.join(ACCOUNTS.keys())}")
        return False

    account = ACCOUNTS[account_name]
    if not account["email"] or not account["password"]:
        print(f"❌ Account '{account_name}' not configured in .env")
        return False

    # Normalize
    if attachments is None:
        attachments = []
    elif isinstance(attachments, str):
        attachments = [attachments]

    body_stripped = body.strip() if body else ""
    has_attachments = len(attachments) > 0

    # Collect warnings
    all_warnings = []

    # 1. Empty body check
    if not body_stripped and has_attachments and not force_empty:
        print("❌ BLOCKED: Cannot send attachments with empty body!")
        print("   Use --force-empty to override")
        return False

    if not body_stripped and not has_attachments:
        print("❌ BLOCKED: Cannot send empty email!")
        return False

    # 2-6. Run all checks
    all_warnings.extend(check_subject(subject))
    all_warnings.extend(check_recipient(to))
    all_warnings.extend(check_sensitive_data(body))

    if attachments:
        _, attach_warnings = check_attachments(attachments)
        all_warnings.extend(attach_warnings)
        for path in attachments:
            if os.path.exists(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.txt', '.md', '.csv', '.json', '.xml', '.html']:
                    try:
                        content = Path(path).read_text(errors='replace')[:10000]
                        for w in check_sensitive_data(content):
                            all_warnings.append(f"{w} (in {os.path.basename(path)})")
                    except:
                        pass

    dup = check_duplicate(to, subject)
    if dup:
        all_warnings.append(dup)

    # Show preview
    show_preview(account_name, account["email"], to, subject, body, attachments, all_warnings)

    # 7. Confirmation
    if not auto_confirm:
        has_critical = any("❌" in w or "SENSITIVE" in w for w in all_warnings)
        prompt = "Send? [y/N]: " if has_critical else "Send? [Y/n]: "
        default = "n" if has_critical else "y"
        try:
            response = input(prompt).strip().lower() or default
        except EOFError:
            response = default
        if response != 'y':
            print("❌ Cancelled.")
            return False

    # Build message
    msg = MIMEMultipart()
    msg['From'] = account["email"]
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    for path in attachments:
        if not os.path.exists(path):
            print(f"❌ Attachment not found: {path}")
            return False
        filename = os.path.basename(path)
        mime_type, _ = mimetypes.guess_type(path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        main_type, sub_type = mime_type.split('/', 1)
        with open(path, 'rb') as f:
            att = MIMEBase(main_type, sub_type)
            att.set_payload(f.read())
            encoders.encode_base64(att)
            att.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(att)

    # Send
    server = smtplib.SMTP(account["smtp_server"], account["smtp_port"])
    server.starttls()
    server.login(account["email"], account["password"])
    server.send_message(msg)
    server.quit()

    log_sent_email(to, subject)
    print(f"\n✅ Email sent via {account_name} to {to}")
    return True


def list_accounts():
    """List configured accounts."""
    print("\n📧 Configured Email Accounts:\n")
    for name, config in ACCOUNTS.items():
        email = config["email"]
        status = "✅ Configured" if email and config["password"] else "❌ Not configured"
        default = " (default)" if name == DEFAULT_ACCOUNT else ""
        print(f"  {name}{default}: {email or '(not set)'} - {status}")
    print()


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--help":
        print(__doc__)
        return

    if sys.argv[1] == "--list":
        list_accounts()
        return

    # Parse args
    account = DEFAULT_ACCOUNT
    attachments = []
    force_empty = False
    auto_confirm = False
    positional = []

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--account" and i + 1 < len(sys.argv):
            account = sys.argv[i + 1].lower()
            i += 2
        elif arg == "--attach" and i + 1 < len(sys.argv):
            attachments.append(sys.argv[i + 1])
            i += 2
        elif arg == "--yes" or arg == "-y":
            auto_confirm = True
            i += 1
        elif arg == "--force-empty":
            force_empty = True
            i += 1
        elif not arg.startswith("--"):
            positional.append(arg)
            i += 1
        else:
            i += 1

    if len(positional) < 2:
        print("Usage: send_email.py [--account NAME] TO SUBJECT [--attach FILE]")
        print("Body is read from stdin")
        return

    to = positional[0]
    subject = positional[1]

    print("Enter message body (Ctrl+D when done):")
    body = sys.stdin.read()

    send_email(account, to, subject, body, attachments, force_empty, auto_confirm)


if __name__ == "__main__":
    main()
