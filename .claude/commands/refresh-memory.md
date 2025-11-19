Refresh context from conversation index.

**Quick Mode (Default):**
Reads the conversation index file for fast context refresh. Shows recent activity, key projects, and important reference files.

**Full Rebuild Mode:**
Use `--rebuild` flag to regenerate the index from all conversation files. This scans all conversations and updates summaries, tags, and metadata.

**Usage:**
- `/refresh-memory` - Quick scan (reads index only)
- `/refresh-memory --rebuild` - Full rebuild (regenerates index from all files)
- `/refresh-memory --recent` - Show only last 30 days
- `/refresh-memory --help` - Show all options

**Index Location:** `/home/dave/skippy/conversations/INDEX.md`

This index-based approach is fast and scalable, reading 1 file instead of 100+.
