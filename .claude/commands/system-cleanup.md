Run the system cleanup utility to remove temporary files, caches, and old data.

Execute: `/home/dave/skippy/scripts/utility/system_cleanup_v1.0.0.sh`

This will:
- Remove Python cache files (__pycache__, *.pyc)
- Clean temporary files (*.tmp, *~, .~*)
- Remove logs older than 30 days
- Remove empty directories
- Clean old duplicate reports (>7 days)
