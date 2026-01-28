#!/usr/bin/env python3
"""
Send crypto notifications via Gmail SMTP

Usage:
    python send_notifications.py                    # Send pending notifications
    python send_notifications.py --daily "content"  # Send daily report
    python send_notifications.py --dry              # Preview without sending
"""

import json
import smtplib
import ssl
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "eboncorp@gmail.com"
RECIPIENT_EMAIL = "eboncorp@gmail.com"

# App password should be in environment or .env file
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

NOTIFICATIONS_FILE = Path("/home/dave/skippy/work/crypto/paper_trading/notifications.json")


def send_email(subject: str, body: str, dry_run: bool = False) -> bool:
    """Send email via Gmail SMTP"""

    if dry_run:
        print(f"\n[DRY RUN] Would send email:")
        print(f"  To: {RECIPIENT_EMAIL}")
        print(f"  Subject: {subject}")
        print(f"  Body preview: {body[:200]}...")
        return True

    if not GMAIL_APP_PASSWORD:
        print("❌ GMAIL_APP_PASSWORD not set")
        print("   Set it in environment or /home/dave/skippy/scripts/crypto/.env")
        # Still save the content for manual review
        return False

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SENDER_EMAIL
        message["To"] = RECIPIENT_EMAIL

        # Plain text body
        part = MIMEText(body, "plain")
        message.attach(part)

        # Send
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string())

        print(f"✅ Email sent: {subject}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def send_daily_report(content: str, dry_run: bool = False) -> bool:
    """Send daily automation report"""

    date_str = datetime.now().strftime("%Y-%m-%d")
    subject = f"📊 Crypto Daily Report - {date_str}"

    body = f"""DAILY CRYPTO AUTOMATION REPORT
================================
Date: {date_str}
Time: {datetime.now().strftime("%H:%M:%S")}

{content}

---
This is automated paper trading. No real trades executed.
Logs: /home/dave/skippy/work/crypto/daily_runs/
Trades: /home/dave/skippy/work/crypto/integrated/
"""

    return send_email(subject, body, dry_run)


def load_pending():
    """Load pending notifications"""
    if not NOTIFICATIONS_FILE.exists():
        return []

    with open(NOTIFICATIONS_FILE) as f:
        notifications = json.load(f)

    return [n for n in notifications if n.get('sent_via') == 'pending']


def mark_sent(notification: dict):
    """Mark notification as sent"""
    with open(NOTIFICATIONS_FILE) as f:
        all_notifications = json.load(f)

    for n in all_notifications:
        if n['timestamp'] == notification['timestamp']:
            n['sent_via'] = 'sent'
            n['sent_at'] = datetime.now().isoformat()

    with open(NOTIFICATIONS_FILE, 'w') as f:
        json.dump(all_notifications, f, indent=2)


def process_pending(dry_run: bool = False):
    """Process and send pending notifications"""
    pending = load_pending()

    if not pending:
        print("✅ No pending notifications")
        return

    print(f"📬 Found {len(pending)} pending notification(s)")

    for notification in pending:
        success = send_email(
            notification['subject'],
            notification['body'],
            dry_run
        )
        if success and not dry_run:
            mark_sent(notification)
            print("   ✅ Sent and marked")


def main():
    dry_run = '--dry' in sys.argv

    # Check for daily report mode
    if '--daily' in sys.argv:
        idx = sys.argv.index('--daily')
        if idx + 1 < len(sys.argv):
            content = sys.argv[idx + 1]
        else:
            # Read from stdin
            content = sys.stdin.read()

        send_daily_report(content, dry_run)
        return

    # Default: process pending notifications
    process_pending(dry_run)


if __name__ == "__main__":
    main()
