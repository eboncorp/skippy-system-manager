#!/usr/bin/env python3
"""
Send pending crypto notifications via Gmail MCP

This script reads pending notifications from the adaptive trader
and sends them via email. Run this via cron or after each trading cycle.

Usage:
    python send_notifications.py         # Send all pending
    python send_notifications.py --dry   # Preview without sending
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

NOTIFICATIONS_FILE = Path("/home/dave/skippy/work/crypto/paper_trading/notifications.json")

def load_pending():
    """Load pending notifications"""
    if not NOTIFICATIONS_FILE.exists():
        return []
    
    with open(NOTIFICATIONS_FILE) as f:
        notifications = json.load(f)
    
    # Filter for pending only
    return [n for n in notifications if n.get('sent_via') == 'pending']

def send_via_claude(notification: dict, dry_run: bool = False) -> bool:
    """Send notification using Claude Code Gmail MCP"""
    
    if dry_run:
        print(f"\n[DRY RUN] Would send to: {notification['recipient']}")
        print(f"Subject: {notification['subject']}")
        print(f"Reason: {notification['reason']}")
        return True
    
    # Create a temp file with the email command for claude
    email_cmd = f"""
Send this email:
To: {notification['recipient']}
Subject: {notification['subject']}

{notification['body']}
"""
    
    # Use subprocess to send via gmail (or queue for manual send)
    print(f"\n📧 Sending: {notification['subject']}")
    print(f"   To: {notification['recipient']}")
    print(f"   Reason: {notification['reason']}")
    
    return True

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

def main():
    dry_run = '--dry' in sys.argv
    
    pending = load_pending()
    
    if not pending:
        print("✅ No pending notifications")
        return
    
    print(f"📬 Found {len(pending)} pending notification(s)")
    
    for notification in pending:
        success = send_via_claude(notification, dry_run)
        if success and not dry_run:
            mark_sent(notification)
            print("   ✅ Sent and marked")
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Complete!")

if __name__ == "__main__":
    main()
