Start the downloads folder watcher daemon.

Run the downloads watcher in the background to automatically detect new files in `/home/dave/skippy/claude/downloads/`.

When a new file is detected, the watcher creates a notification file at `/tmp/claude_downloads_notification.json` that Claude can check and process according to the File Download Management Protocol.

Execute:
```bash
/home/dave/skippy/scripts/monitoring/downloads_watcher_v1.0.0.py --daemon
```

Then check for notifications periodically or when user mentions downloads.
