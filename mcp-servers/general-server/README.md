# General Purpose MCP Server v2.3.2

FastMCP-based Model Context Protocol server with 75 tools for file operations, system utilities, Google Drive, stock photos, and Google Photos.

## Overview

This MCP server provides comprehensive tooling for:
- File system operations (read, write, search, archive)
- System utilities (process management, network, monitoring)
- **Google Drive management (13 tools)** - Organization, uploads, sharing, metadata
- **Pexels stock photos (4 tools)** ✅ - Free high-quality photography for campaigns
- **Google Photos (6 tools)** ⚠️ - Personal photo library access (OAuth pending)

## Version 2.3.2 Highlights

**New in v2.3.2 (2025-11-12):**
- ✅ 4 Pexels stock photo tools (search, download, curated)
- ⚠️ 6 Google Photos tools (OAuth issue being resolved)
- Campaign-ready stock photography integration
- 3M+ free photos available for website and social media
- Complete documentation for both integrations

**Previous (v2.3.0):**
- 5 new Google Drive tools for uploads, sharing, and metadata
- Complete file upload functionality with MIME type detection
- Public and user-specific file sharing
- Comprehensive metadata retrieval
- File copying and batch upload capabilities

**Previous (v2.2.0):**
- 8 Google Drive organization tools
- Pattern-based file organization
- Batch file operations
- Folder management

## Quick Start

```bash
# Activate virtual environment
cd /home/dave/skippy/mcp-servers/general-server
source .venv/bin/activate

# Run the server
python server.py
```

## Google Drive Tools (13 Total)

### Organization & Management (v2.2.0)
1. **gdrive_create_folder** - Create folders
2. **gdrive_move_file** - Move files/folders
3. **gdrive_list_folder_contents** - Browse contents
4. **gdrive_trash_file** - Move to trash
5. **gdrive_rename_file** - Rename files/folders
6. **gdrive_batch_move_files** - Bulk moves
7. **gdrive_get_folder_id_by_name** - Find folders
8. **gdrive_organize_by_pattern** - Pattern-based organization

### Upload & Sharing (v2.3.0)
9. **gdrive_upload_file** - Upload single files
10. **gdrive_share_file** - Share with link generation
11. **gdrive_get_file_metadata** - Get detailed metadata
12. **gdrive_copy_file** - Copy files
13. **gdrive_batch_upload** - Batch upload from directory

## Example Usage

### Upload and Share a File

```python
from server import gdrive_upload_file, gdrive_share_file
import json

# Upload file
upload_result = gdrive_upload_file(
    local_file_path="/path/to/document.pdf",
    destination_folder_id="1abc123xyz"
)

file_data = json.loads(upload_result)
file_id = file_data['file_id']

# Share publicly
share_result = gdrive_share_file(
    file_id=file_id,
    permission_type="anyone",
    role="reader"
)

link = json.loads(share_result)['view_link']
print(f"Shareable link: {link}")
```

### Organize Files by Pattern

```python
from server import gdrive_organize_by_pattern

# Move all invoices to Invoices folder
result = gdrive_organize_by_pattern(
    search_pattern="name contains 'invoice'",
    destination_folder_id="1invoices123",
    max_files=100
)
```

### Batch Upload Directory

```python
from server import gdrive_batch_upload

# Upload all PDFs from directory
result = gdrive_batch_upload(
    local_directory="/home/user/reports",
    destination_folder_id="1reports456",
    file_pattern="*.pdf"
)
```

## Documentation

- **[GDRIVE_TOOLS_REFERENCE.md](GDRIVE_TOOLS_REFERENCE.md)** - Complete Google Drive tools documentation
- **[CHANGELOG_v2.3.0.md](CHANGELOG_v2.3.0.md)** - Version 2.3.0 release notes

## Features

### File Operations
- Read, write, edit files
- File search (glob patterns, regex)
- Archive operations (zip, tar)
- Directory management

### System Utilities
- Process management
- Network operations
- System monitoring
- Shell command execution

### Google Drive (13 tools)
- Complete folder hierarchy management
- Pattern-based file organization
- Single and batch file uploads
- Public and user-specific sharing
- Comprehensive metadata access
- File copying and renaming

## Technical Details

- **Framework:** FastMCP
- **Language:** Python 3.12
- **Google API:** Drive API v3
- **Authentication:** OAuth 2.0
- **Warning Suppression:** Configured for oauth2client compatibility

## Tool Count by Category

| Category | Tools | Version | Status |
|----------|-------|---------|--------|
| File Operations | 15 | v2.1.0 | ✅ |
| System Utilities | 12 | v2.1.0 | ✅ |
| Network Tools | 8 | v2.1.0 | ✅ |
| Archive Operations | 5 | v2.1.0 | ✅ |
| Process Management | 7 | v2.1.0 | ✅ |
| Google Drive Organization | 8 | v2.2.0 | ✅ |
| Google Drive Upload/Share | 5 | v2.3.0 | ✅ |
| **Pexels Stock Photos** | **4** | **v2.3.2** | **✅** |
| **Google Photos** | **6** | **v2.3.2** | **⚠️** |
| Other Tools | 5 | v2.1.0 | ✅ |
| **Total** | **75** | **v2.3.2** | - |

## Requirements

```
fastmcp
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```

## Configuration

Google Drive authentication:
- Credentials stored in `~/.credentials/`
- OAuth 2.0 with user consent
- Automatic token refresh

## Recent Accomplishments

### Google Drive Organization (November 2025)
- Organized 390+ files across Google Drive
- Created professional folder structure matching local conventions
- Organized categories: Documents, Downloads, Pictures, Technical, Financial, Business, Campaign, Taxes, etc.
- Pattern-based organization for backups, logs, archives

### MCP Server Evolution
- **v2.1.0** (Oct 2025): 52 general-purpose tools
- **v2.2.0** (Nov 2025): +8 Google Drive organization tools
- **v2.3.0** (Nov 2025): +5 upload/share/metadata tools
- **v2.3.2** (Nov 2025): +4 Pexels stock photos, +6 Google Photos tools

## Project Structure

```
/home/dave/skippy/mcp-servers/general-server/
├── server.py                    # Main MCP server (2687 lines)
├── .venv/                       # Python virtual environment
├── README.md                    # This file
├── GDRIVE_TOOLS_REFERENCE.md    # Complete Drive tools documentation
├── CHANGELOG_v2.3.0.md          # Version 2.3.0 release notes
└── credentials/                 # Google OAuth credentials
```

## Author

**Claude Code** - Anthropic AI Assistant
- MCP Server Development
- Google Drive Integration
- Documentation & Testing

## Version History

- **v2.3.2** (2025-11-12): Added Pexels (4 tools) & Google Photos (6 tools) - 75 total
- **v2.3.0** (2025-11-11): Added 5 Google Drive upload/share tools (65 total)
- **v2.2.0** (2025-11-10): Added 8 Google Drive organization tools (60 total)
- **v2.1.0** (2025-10-31): Initial release with 52 general-purpose tools

## Support

For issues or questions:
- Review documentation in `GDRIVE_TOOLS_REFERENCE.md`
- Check `CHANGELOG_v2.3.0.md` for recent changes
- Verify Google Drive authentication is configured

## License

Internal tool for personal use.

---

**Last Updated:** November 12, 2025
**Current Version:** v2.3.2
**Total Tools:** 75 (52 general + 13 Google Drive + 4 Pexels + 6 Google Photos)
