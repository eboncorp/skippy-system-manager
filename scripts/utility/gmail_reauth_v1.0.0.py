#!/home/dave/skippy/mcp-servers/general-server/.venv/bin/python
"""
Gmail Re-Authorization v1.0.0
Re-authorizes Gmail API access for eboncorp@gmail.com

Usage: gmail_reauth_v1.0.0.py
Dependencies: google-auth, google-auth-oauthlib, google-api-python-client

Created: 2026-01-25
"""

import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Configuration
CREDENTIALS_DIR = Path.home() / ".config/skippy/credentials"
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "credentials.json"
OUTPUT_TOKEN_FILE = CREDENTIALS_DIR / "google_auth_eboncorp.json"

# Scopes needed for Gmail access
SCOPES = [
    "https://mail.google.com/",  # Full Gmail access
    "https://www.googleapis.com/auth/gmail.readonly",
]


def main():
    print("=" * 60)
    print("Gmail Re-Authorization for eboncorp@gmail.com")
    print("=" * 60)
    print()

    if not CLIENT_SECRET_FILE.exists():
        print(f"ERROR: Client secret file not found: {CLIENT_SECRET_FILE}")
        return 1

    print(f"Using client credentials: {CLIENT_SECRET_FILE}")
    print(f"Output token file: {OUTPUT_TOKEN_FILE}")
    print()
    print("A browser window will open for authentication.")
    print("Please sign in with: eboncorp@gmail.com")
    print()
    input("Press Enter to continue...")

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES
    )

    # This will open a browser for authentication
    creds = flow.run_local_server(port=8080)

    # Save the credentials
    with open(OUTPUT_TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print()
    print("=" * 60)
    print("Authorization successful!")
    print(f"Token saved to: {OUTPUT_TOKEN_FILE}")
    print("=" * 60)

    # Test the connection
    print()
    print("Testing Gmail API connection...")
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    print(f"Connected as: {profile.get('emailAddress')}")
    print(f"Total messages: {profile.get('messagesTotal')}")

    return 0


if __name__ == "__main__":
    exit(main())
