# MCP Server v2.3.0 - Google Drive Upload & Sharing Tools

**Release Date:** November 11, 2025  
**Author:** Claude Code  
**Previous Version:** v2.2.0 (60 tools)  
**Current Version:** v2.3.0 (65 tools)

## Overview

Version 2.3.0 adds comprehensive file upload, sharing, and metadata management capabilities to the MCP Server's Google Drive integration. This release complements the organization tools from v2.2.0 with essential file management features.

## New Tools Added (5)

### 1. `gdrive_upload_file`
**Purpose:** Upload files from local machine to Google Drive

**Parameters:**
- `local_file_path` (required): Path to local file
- `destination_folder_id` (optional): Target folder ID (uploads to root if not specified)
- `new_name` (optional): Rename file during upload

**Features:**
- Automatic MIME type detection
- Resumable uploads for large files
- Returns file ID, web link, size, and location

**Example:**
```python
result = gdrive_upload_file(
    local_file_path="/home/user/document.pdf",
    destination_folder_id="1abc123xyz",
    new_name="Monthly Report.pdf"
)
```

### 2. `gdrive_share_file`
**Purpose:** Share files/folders and generate shareable links

**Parameters:**
- `file_id` (required): ID of file/folder to share
- `permission_type` (optional): "anyone", "user", or "domain" (default: "anyone")
- `role` (optional): "reader", "writer", or "commenter" (default: "reader")
- `email_address` (optional): Required if permission_type is "user"

**Features:**
- Public link generation
- User-specific sharing
- Granular permission control
- Returns both view and download links

**Example:**
```python
result = gdrive_share_file(
    file_id="1abc123xyz",
    permission_type="anyone",
    role="reader"
)
```

### 3. `gdrive_get_file_metadata`
**Purpose:** Retrieve detailed file/folder metadata

**Parameters:**
- `file_id` (required): ID of file/folder
- `include_permissions` (optional): Include sharing details (default: False)

**Features:**
- Comprehensive metadata (name, size, dates, owner)
- Automatic size formatting (KB/MB/GB)
- Optional permission details
- Simplified owner/modifier information

**Example:**
```python
result = gdrive_get_file_metadata(
    file_id="1abc123xyz",
    include_permissions=True
)
```

### 4. `gdrive_copy_file`
**Purpose:** Create copies of files in Google Drive

**Parameters:**
- `file_id` (required): ID of file to copy
- `new_name` (optional): Name for copy (defaults to "Copy of [original]")
- `destination_folder_id` (optional): Target folder (defaults to same location)

**Features:**
- Quick file duplication
- Optional renaming during copy
- Cross-folder copying
- Returns IDs and links for both original and copy

**Example:**
```python
result = gdrive_copy_file(
    file_id="1abc123xyz",
    new_name="Backup Copy",
    destination_folder_id="1def456uvw"
)
```

### 5. `gdrive_batch_upload`
**Purpose:** Upload multiple files from a directory

**Parameters:**
- `local_directory` (required): Path to directory
- `destination_folder_id` (optional): Target folder ID
- `file_pattern` (optional): Glob pattern (default: "*" for all files)

**Features:**
- Glob pattern matching (*.pdf, *.jpg, etc.)
- Batch processing with individual results
- Success/failure tracking per file
- Automatic MIME type detection per file

**Example:**
```python
result = gdrive_batch_upload(
    local_directory="/home/user/documents",
    destination_folder_id="1abc123xyz",
    file_pattern="*.pdf"
)
```

## Technical Improvements

### Code Structure
- All tools follow consistent error handling patterns
- JSON response format for easy parsing
- HttpError and generic exception handling
- Proper use of Google Drive API fields parameter

### Dependencies
- Leverages existing `MediaFileUpload` import from googleapiclient
- Uses Python `mimetypes` module for type detection
- Compatible with existing OAuth2 authentication

### Testing
- Syntax validation confirmed
- Import testing successful for all 5 tools
- Live API testing with `gdrive_get_file_metadata` confirmed functional
- Integration with existing v2.2.0 tools verified

## Version History

### v2.3.0 (Current)
- **Total Tools:** 65
- **Added:** 5 upload/share/metadata tools
- **Status:** Active

### v2.2.0
- **Total Tools:** 60
- **Added:** 8 Google Drive organization tools
- **Focus:** Pattern-based file organization

### v2.1.0
- **Total Tools:** 52
- **Focus:** General-purpose MCP server foundation

## Google Drive Tools Complete Suite (13 tools)

### Organization Tools (v2.2.0)
1. `gdrive_create_folder` - Create new folders
2. `gdrive_move_file` - Move files between folders
3. `gdrive_list_folder_contents` - Browse folder contents
4. `gdrive_trash_file` - Move files to trash
5. `gdrive_rename_file` - Rename files/folders
6. `gdrive_batch_move_files` - Bulk file moves
7. `gdrive_get_folder_id_by_name` - Find folder IDs
8. `gdrive_organize_by_pattern` - Pattern-based organization

### Upload & Sharing Tools (v2.3.0)
9. `gdrive_upload_file` - Upload single files
10. `gdrive_share_file` - Share files/folders
11. `gdrive_get_file_metadata` - Get detailed metadata
12. `gdrive_copy_file` - Copy files
13. `gdrive_batch_upload` - Batch upload multiple files

## Use Cases

### Individual File Management
- Upload important documents to specific folders
- Share files with team members or publicly
- Create backups of critical files
- Review file metadata before operations

### Bulk Operations
- Upload entire directories of files
- Organize and share project folders
- Batch process file uploads with pattern matching

### Workflow Integration
- Automated backup uploads
- Document sharing workflows
- Metadata-based file management
- Cross-folder file organization

## Future Enhancements

Potential additions for v2.4.0:
- `gdrive_download_file` - Download files to local machine
- `gdrive_batch_download` - Bulk download operations
- `gdrive_search_files` - Advanced file search capabilities
- `gdrive_update_permissions` - Modify existing permissions
- `gdrive_empty_trash` - Permanent deletion capabilities

## Installation & Usage

No additional installation required. The tools are immediately available after updating to v2.3.0.

```python
# Import from MCP server
from server import (
    gdrive_upload_file,
    gdrive_share_file,
    gdrive_get_file_metadata,
    gdrive_copy_file,
    gdrive_batch_upload
)

# Use in your code
result = gdrive_upload_file("/path/to/file.pdf")
```

## Breaking Changes

**None.** Version 2.3.0 is fully backward compatible with v2.2.0 and v2.1.0.

## Credits

- **Development:** Claude Code
- **Framework:** FastMCP
- **API:** Google Drive API v3
- **OAuth:** Google Auth Libraries

---

**Server Location:** `/home/dave/skippy/mcp-servers/general-server/server.py`  
**Documentation:** `/home/dave/skippy/mcp-servers/general-server/CHANGELOG_v2.3.0.md`
