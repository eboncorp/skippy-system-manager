Run the screenshot cleanup utility to organize screenshots folder.

Execute: `/home/dave/skippy/scripts/monitoring/screenshot_cleanup_v1.0.0.py --dry-run` first to preview changes, then run with `--now` to apply cleanup.

The cleanup will:
- Consolidate Screenshots and screenshots folders
- Keep 20 most recent screenshots
- Archive screenshots older than 30 days to monthly folders
- Delete archived screenshots older than 180 days
