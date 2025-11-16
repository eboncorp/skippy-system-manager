# Google Drive Tools Reference - MCP Server v2.3.0

Complete reference for all 13 Google Drive management tools in the MCP Server.

## Table of Contents

1. [Organization Tools (v2.2.0)](#organization-tools)
2. [Upload & Sharing Tools (v2.3.0)](#upload--sharing-tools)
3. [Quick Reference](#quick-reference)
4. [Common Workflows](#common-workflows)
5. [Error Handling](#error-handling)

---

## Organization Tools (v2.2.0)

### 1. gdrive_create_folder

Create a new folder in Google Drive.

**Parameters:**
- `folder_name` (required): Name for the new folder
- `parent_folder_id` (optional): Parent folder ID (creates in root if not specified)

**Returns:** JSON with folder ID, name, and web link

**Example:**
```python
result = gdrive_create_folder(
    folder_name="Project Documents",
    parent_folder_id="1abc123xyz"
)
```

**Response:**
```json
{
  "success": true,
  "folder_id": "1def456uvw",
  "folder_name": "Project Documents",
  "web_link": "https://drive.google.com/drive/folders/1def456uvw"
}
```

---

### 2. gdrive_move_file

Move a file or folder to a different location.

**Parameters:**
- `file_id` (required): ID of file/folder to move
- `new_parent_folder_id` (required): Destination folder ID

**Returns:** JSON with success status and file details

**Example:**
```python
result = gdrive_move_file(
    file_id="1abc123xyz",
    new_parent_folder_id="1def456uvw"
)
```

---

### 3. gdrive_list_folder_contents

List all files and folders in a specific folder.

**Parameters:**
- `folder_id` (required): ID of folder to list
- `max_results` (optional): Maximum number of items (default: 100)

**Returns:** JSON array with file/folder details

**Example:**
```python
result = gdrive_list_folder_contents(
    folder_id="1abc123xyz",
    max_results=50
)
```

**Response:**
```json
{
  "success": true,
  "folder_id": "1abc123xyz",
  "total_items": 42,
  "files": [
    {
      "id": "1file123",
      "name": "document.pdf",
      "mimeType": "application/pdf",
      "size": "1.5 MB",
      "modifiedTime": "2025-11-10T12:30:00Z"
    }
  ]
}
```

---

### 4. gdrive_trash_file

Move a file or folder to trash (soft delete).

**Parameters:**
- `file_id` (required): ID of file/folder to trash

**Returns:** JSON with success status

**Example:**
```python
result = gdrive_trash_file(file_id="1abc123xyz")
```

**Note:** Files can be restored from trash. Use with Google Drive web interface to permanently delete if needed.

---

### 5. gdrive_rename_file

Rename a file or folder.

**Parameters:**
- `file_id` (required): ID of file/folder to rename
- `new_name` (required): New name for the file/folder

**Returns:** JSON with updated file details

**Example:**
```python
result = gdrive_rename_file(
    file_id="1abc123xyz",
    new_name="Quarterly Report 2025.pdf"
)
```

---

### 6. gdrive_batch_move_files

Move multiple files to a destination folder in one operation.

**Parameters:**
- `file_ids` (required): List of file IDs to move
- `destination_folder_id` (required): Target folder ID

**Returns:** JSON with results for each file

**Example:**
```python
result = gdrive_batch_move_files(
    file_ids=["1abc123", "1def456", "1ghi789"],
    destination_folder_id="1target123"
)
```

**Response:**
```json
{
  "success": true,
  "total_files": 3,
  "successful_moves": 3,
  "failed_moves": 0,
  "results": [
    {
      "file_id": "1abc123",
      "file_name": "doc1.pdf",
      "success": true
    }
  ]
}
```

---

### 7. gdrive_get_folder_id_by_name

Search for folders by name and get their IDs.

**Parameters:**
- `folder_name` (required): Name to search for
- `exact_match` (optional): True for exact match, False for contains (default: False)
- `max_results` (optional): Maximum results to return (default: 10)

**Returns:** JSON array of matching folders

**Example:**
```python
result = gdrive_get_folder_id_by_name(
    folder_name="Documents",
    exact_match=True
)
```

**Response:**
```json
{
  "success": true,
  "search_name": "Documents",
  "exact_match": true,
  "found_count": 1,
  "folders": [
    {
      "id": "1abc123xyz",
      "name": "Documents",
      "parents": ["root"]
    }
  ]
}
```

---

### 8. gdrive_organize_by_pattern

Organize files matching a search pattern into a folder (batch move).

**Parameters:**
- `search_pattern` (required): Google Drive query (e.g., "name contains 'invoice'")
- `destination_folder_id` (required): Target folder ID
- `max_files` (optional): Maximum files to move (default: 50)

**Returns:** JSON with move results

**Example:**
```python
# Move all PDFs containing "invoice" to Invoices folder
result = gdrive_organize_by_pattern(
    search_pattern="mimeType='application/pdf' and name contains 'invoice'",
    destination_folder_id="1invoices123",
    max_files=100
)
```

**Common Search Patterns:**
```python
# By file type
"mimeType='application/pdf'"
"mimeType='image/jpeg'"
"mimeType='application/vnd.google-apps.folder'"

# By name
"name contains 'report'"
"name='exact_filename.pdf'"

# Combined patterns
"mimeType='application/pdf' and name contains '2025'"
"name contains 'invoice' and not name contains 'draft'"
```

**Response:**
```json
{
  "success": true,
  "pattern": "name contains 'invoice'",
  "total_found": 25,
  "successful_moves": 25,
  "failed_moves": 0,
  "results": [...]
}
```

---

## Upload & Sharing Tools (v2.3.0)

### 9. gdrive_upload_file

Upload a file from local machine to Google Drive.

**Parameters:**
- `local_file_path` (required): Path to local file
- `destination_folder_id` (optional): Target folder (uploads to root if omitted)
- `new_name` (optional): Rename during upload

**Returns:** JSON with file ID, size, and web link

**Example:**
```python
result = gdrive_upload_file(
    local_file_path="/home/user/documents/report.pdf",
    destination_folder_id="1abc123xyz",
    new_name="Monthly Report.pdf"
)
```

**Response:**
```json
{
  "success": true,
  "file_id": "1uploaded123",
  "file_name": "Monthly Report.pdf",
  "file_size_mb": 2.45,
  "mime_type": "application/pdf",
  "web_link": "https://drive.google.com/file/d/1uploaded123/view",
  "location": "Folder 1abc123xyz"
}
```

**Features:**
- Automatic MIME type detection
- Resumable uploads for large files
- Progress tracking
- Path expansion (~/ supported)

---

### 10. gdrive_share_file

Share a file or folder and generate shareable links.

**Parameters:**
- `file_id` (required): ID of file/folder to share
- `permission_type` (optional): "anyone", "user", or "domain" (default: "anyone")
- `role` (optional): "reader", "writer", or "commenter" (default: "reader")
- `email_address` (optional): Required if permission_type is "user"

**Returns:** JSON with shareable links and permission details

**Example 1: Public sharing**
```python
result = gdrive_share_file(
    file_id="1abc123xyz",
    permission_type="anyone",
    role="reader"
)
```

**Example 2: Share with specific user**
```python
result = gdrive_share_file(
    file_id="1abc123xyz",
    permission_type="user",
    role="writer",
    email_address="colleague@example.com"
)
```

**Response:**
```json
{
  "success": true,
  "file_name": "Project Plan.pdf",
  "file_type": "application/pdf",
  "permission_id": "permission123",
  "permission_type": "anyone",
  "role": "reader",
  "view_link": "https://drive.google.com/file/d/1abc123xyz/view",
  "download_link": "https://drive.google.com/uc?id=1abc123xyz&export=download",
  "shared_with": "Anyone with the link"
}
```

**Permission Types:**
- `anyone`: Anyone with the link can access
- `user`: Specific email address
- `domain`: Anyone in your Google Workspace domain

**Roles:**
- `reader`: Can view only
- `writer`: Can edit
- `commenter`: Can add comments (Google Docs, Sheets, etc.)

---

### 11. gdrive_get_file_metadata

Get detailed metadata for a file or folder.

**Parameters:**
- `file_id` (required): ID of file/folder
- `include_permissions` (optional): Include sharing details (default: False)

**Returns:** JSON with comprehensive metadata

**Example:**
```python
result = gdrive_get_file_metadata(
    file_id="1abc123xyz",
    include_permissions=True
)
```

**Response:**
```json
{
  "success": true,
  "metadata": {
    "id": "1abc123xyz",
    "name": "Project Plan.pdf",
    "mimeType": "application/pdf",
    "size": "2.45 MB",
    "size_formatted": "2.45 MB",
    "createdTime": "2025-01-15T08:30:00Z",
    "modifiedTime": "2025-11-10T14:22:00Z",
    "webViewLink": "https://drive.google.com/file/d/1abc123xyz/view",
    "parents": ["1parent123"],
    "starred": false,
    "trashed": false,
    "owner_email": "owner@example.com",
    "last_modified_by": "editor@example.com",
    "permissions": [...]
  }
}
```

**Use Cases:**
- Check file details before operations
- Verify ownership
- Review sharing permissions
- Get file sizes for quota management

---

### 12. gdrive_copy_file

Create a copy of a file in Google Drive.

**Parameters:**
- `file_id` (required): ID of file to copy
- `new_name` (optional): Name for copy (defaults to "Copy of [original]")
- `destination_folder_id` (optional): Target folder (defaults to same location)

**Returns:** JSON with details for both original and copy

**Example:**
```python
result = gdrive_copy_file(
    file_id="1abc123xyz",
    new_name="Backup - Project Plan.pdf",
    destination_folder_id="1backups456"
)
```

**Response:**
```json
{
  "success": true,
  "original_file_id": "1abc123xyz",
  "original_name": "Project Plan.pdf",
  "copied_file_id": "1copied789",
  "copied_file_name": "Backup - Project Plan.pdf",
  "web_link": "https://drive.google.com/file/d/1copied789/view"
}
```

**Note:** Only files can be copied, not folders. To copy folders, use batch operations with the files inside.

---

### 13. gdrive_batch_upload

Upload multiple files from a directory in one operation.

**Parameters:**
- `local_directory` (required): Path to directory with files
- `destination_folder_id` (optional): Target folder in Drive
- `file_pattern` (optional): Glob pattern (default: "*" for all files)

**Returns:** JSON with results for each file

**Example:**
```python
# Upload all PDFs from a directory
result = gdrive_batch_upload(
    local_directory="/home/user/invoices",
    destination_folder_id="1invoices123",
    file_pattern="*.pdf"
)
```

**Common Patterns:**
```python
"*.pdf"           # All PDFs
"*.{jpg,png}"     # Images
"report_*.xlsx"   # Excel files starting with "report_"
"*"               # All files (default)
```

**Response:**
```json
{
  "success": true,
  "total_files": 15,
  "successful_uploads": 14,
  "failed_uploads": 1,
  "results": [
    {
      "success": true,
      "file_name": "invoice_001.pdf",
      "file_id": "1file123",
      "size_mb": 0.85
    },
    {
      "success": false,
      "file_name": "corrupted.pdf",
      "error": "File read error"
    }
  ]
}
```

---

## Quick Reference

### By Use Case

**File Organization:**
- Create folders: `gdrive_create_folder`
- Move files: `gdrive_move_file`, `gdrive_batch_move_files`
- Organize by pattern: `gdrive_organize_by_pattern`
- Rename: `gdrive_rename_file`
- Delete: `gdrive_trash_file`

**File Uploads:**
- Single file: `gdrive_upload_file`
- Multiple files: `gdrive_batch_upload`

**File Sharing:**
- Share and get link: `gdrive_share_file`
- View permissions: `gdrive_get_file_metadata` with `include_permissions=True`

**File Discovery:**
- Browse folder: `gdrive_list_folder_contents`
- Find folders: `gdrive_get_folder_id_by_name`
- Search files: Use `gdrive_organize_by_pattern` with `max_files=0` to find without moving

**File Management:**
- Copy files: `gdrive_copy_file`
- Get details: `gdrive_get_file_metadata`

---

## Common Workflows

### Workflow 1: Upload and Share Documents

```python
# 1. Create a project folder
folder_result = gdrive_create_folder(
    folder_name="Q4 Reports",
    parent_folder_id="1projects123"
)
folder_id = json.loads(folder_result)['folder_id']

# 2. Upload multiple reports
upload_result = gdrive_batch_upload(
    local_directory="/home/user/reports/q4",
    destination_folder_id=folder_id,
    file_pattern="*.pdf"
)

# 3. Share the folder publicly
share_result = gdrive_share_file(
    file_id=folder_id,
    permission_type="anyone",
    role="reader"
)

# Get shareable link
link = json.loads(share_result)['view_link']
print(f"Reports available at: {link}")
```

### Workflow 2: Organize Messy Drive

```python
# 1. Find the Documents folder
find_result = gdrive_get_folder_id_by_name(
    folder_name="Documents",
    exact_match=True
)
docs_folder_id = json.loads(find_result)['folders'][0]['id']

# 2. Create category subfolders
invoices_folder = gdrive_create_folder(
    folder_name="Invoices",
    parent_folder_id=docs_folder_id
)
reports_folder = gdrive_create_folder(
    folder_name="Reports",
    parent_folder_id=docs_folder_id
)

# 3. Organize files by pattern
gdrive_organize_by_pattern(
    search_pattern="name contains 'invoice'",
    destination_folder_id=json.loads(invoices_folder)['folder_id'],
    max_files=100
)

gdrive_organize_by_pattern(
    search_pattern="name contains 'report'",
    destination_folder_id=json.loads(reports_folder)['folder_id'],
    max_files=100
)
```

### Workflow 3: Backup Important Files

```python
# 1. Create backup folder
backup_result = gdrive_create_folder(
    folder_name=f"Backup {datetime.now().strftime('%Y-%m-%d')}"
)
backup_id = json.loads(backup_result)['folder_id']

# 2. Find important files
important_folder_id = "1important123"
files_result = gdrive_list_folder_contents(
    folder_id=important_folder_id,
    max_results=100
)

# 3. Copy each file to backup folder
files = json.loads(files_result)['files']
for file in files:
    if file['mimeType'] != 'application/vnd.google-apps.folder':
        gdrive_copy_file(
            file_id=file['id'],
            new_name=f"BACKUP_{file['name']}",
            destination_folder_id=backup_id
        )
```

---

## Error Handling

All tools return JSON with `success` field. Check this before processing results:

```python
import json

result = gdrive_upload_file(
    local_file_path="/path/to/file.pdf",
    destination_folder_id="1abc123"
)

data = json.loads(result)

if data.get('success'):
    print(f"File uploaded: {data['file_id']}")
    print(f"Link: {data['web_link']}")
else:
    print(f"Error: {data.get('error', 'Unknown error')}")
```

**Common Error Responses:**

```json
{
  "success": false,
  "error": "File not found: /invalid/path.pdf"
}
```

```json
{
  "success": false,
  "error": "Google Drive API Error: 404 - File not found"
}
```

**Error Types:**
- File not found (local or Drive)
- Permission denied
- Quota exceeded
- API rate limits
- Network errors
- Invalid folder IDs

**Best Practices:**
1. Always check `success` field
2. Handle errors gracefully
3. Use `try/except` for JSON parsing
4. Verify folder IDs before batch operations
5. Test with small batches first

---

## Google Drive Query Syntax

For `gdrive_organize_by_pattern` and custom searches:

**Field Operators:**
```
name = 'exact name'
name contains 'partial'
mimeType = 'application/pdf'
mimeType contains 'image'
fullText contains 'search term'
```

**Logical Operators:**
```
and    # Both conditions must be true
or     # Either condition must be true
not    # Negate condition
```

**Common MIME Types:**
```
application/pdf                           # PDF files
application/vnd.google-apps.folder        # Folders
application/vnd.google-apps.document      # Google Docs
application/vnd.google-apps.spreadsheet   # Google Sheets
image/jpeg                                # JPEG images
image/png                                 # PNG images
text/plain                                # Text files
application/zip                           # ZIP archives
```

**Example Queries:**
```python
# PDFs created in 2025
"mimeType='application/pdf' and name contains '2025'"

# Images but not PNGs
"mimeType contains 'image' and not mimeType='image/png'"

# Files with "invoice" or "receipt" in name
"name contains 'invoice' or name contains 'receipt'"

# Folders only
"mimeType='application/vnd.google-apps.folder'"

# Non-folder files
"not mimeType='application/vnd.google-apps.folder'"
```

---

## Version History

- **v2.3.0** (2025-11-11): Added 5 upload/share/metadata tools
- **v2.2.0** (2025-11-10): Added 8 organization tools
- **v2.1.0** (2025-10-31): Initial MCP server with 52 general tools

---

**Server Location:** `/home/dave/skippy/mcp-servers/general-server/server.py`  
**Documentation:** `/home/dave/skippy/mcp-servers/general-server/GDRIVE_TOOLS_REFERENCE.md`  
**Changelog:** `/home/dave/skippy/mcp-servers/general-server/CHANGELOG_v2.3.0.md`
