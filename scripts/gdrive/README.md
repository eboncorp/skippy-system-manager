# Google Drive Management Scripts

Collection of scripts for automated Google Drive organization and maintenance.

## Scripts

### 1. gdrive_auto_organize_v1.0.0.sh

Automatically organize Google Drive files using pattern-based rules.

**Usage:**
```bash
# Dry run (shows what would be organized without moving)
./gdrive_auto_organize_v1.0.0.sh --dry-run

# Actual run (moves files)
./gdrive_auto_organize_v1.0.0.sh
```

**Cron Schedule:**
```bash
# Daily at 3 AM
0 3 * * * /home/dave/skippy/scripts/gdrive/gdrive_auto_organize_v1.0.0.sh

# Weekly on Sunday at 3 AM
0 3 * * 0 /home/dave/skippy/scripts/gdrive/gdrive_auto_organize_v1.0.0.sh
```

**Organization Rules:**
- PDFs: Invoices, receipts, statements → Downloads/Financial
- Images: All image files → Pictures
- Documents: Word docs, text files → Documents
- Spreadsheets: Excel, CSV files → Financial
- Backups: Backup files → Technical
- Archives: ZIP, TAR, GZ files → Technical

**Features:**
- Pattern-based file matching
- Automatic folder creation/detection
- Comprehensive logging
- Dry-run mode for testing
- 30-day log rotation

**Logs:** `/home/dave/skippy/log/gdrive/auto_organize_*.log`

---

### 2. gdrive_folder_cleanup_v1.0.0.sh

Analyze and report duplicate/unclear folder names in Google Drive.

**Usage:**
```bash
# Analyze only (no changes)
./gdrive_folder_cleanup_v1.0.0.sh

# Fix mode (future feature)
./gdrive_folder_cleanup_v1.0.0.sh --fix
```

**Detects:**
- Duplicate folder names (case-insensitive)
- Unclear names (temp, untitled, misc, etc.)
- Number-only folder names
- Special characters or formatting issues

**Reports:**
- Folder contents samples
- Item counts per folder
- Naming recommendations
- Cleanup suggestions

**Logs:** `/home/dave/skippy/log/gdrive/folder_cleanup_*.log`

---

## Requirements

- MCP Server v2.3.0+ with Google Drive tools
- Python 3.12+ with virtual environment
- Google Drive API authentication configured
- Bash 4.0+

## Configuration

Both scripts use:
- **MCP Server:** `/home/dave/skippy/mcp-servers/general-server`
- **Log Directory:** `/home/dave/skippy/log/gdrive`
- **Folder Cache:** `/tmp/gdrive_organize_folders.json`

## Integration with MCP Server

These scripts leverage the MCP Server v2.3.0 Google Drive tools:
- `gdrive_organize_by_pattern` - Pattern-based file organization
- `gdrive_get_folder_id_by_name` - Folder lookup
- `gdrive_list_folder_contents` - Folder browsing
- `gdrive_rename_file` - Folder renaming (future)

## Best Practices

1. **Always test with --dry-run first**
2. **Review logs after each run**
3. **Backup important files before automation**
4. **Adjust patterns for your file structure**
5. **Run cleanup script monthly**

## Troubleshooting

**Folder cache not found:**
- Script will auto-create from common folders
- Verify folders exist in Google Drive

**Permission errors:**
- Check Google Drive API authentication
- Verify OAuth token is not expired

**Pattern not matching:**
- Test patterns individually with MCP tools
- Check Google Drive query syntax documentation

## Future Enhancements

- Auto-fix mode for folder cleanup
- Custom organization rules via config file
- Email notifications for organization summary
- Integration with backup systems
- Duplicate file detection

---

**Last Updated:** November 11, 2025  
**Version:** 1.0.0  
**Author:** Claude Code
