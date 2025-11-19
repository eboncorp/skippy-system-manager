---
name: gdrive-upload
description: Quick Google Drive file upload helper
---

# Google Drive Upload

Upload file(s) to Google Drive using MCP server.

**Usage:** `/gdrive-upload [file_path] [folder_name]`

## Instructions for Claude

1. Use MCP `gdrive_upload_file` tool to upload the specified file
2. If folder_name provided, use `gdrive_get_folder_id_by_name` to find folder ID first
3. Generate shareable link with `gdrive_share_file` if requested
4. Report the upload status and any shareable links

## Common Use Cases

- Upload campaign documents to Google Drive
- Share files with team members
- Archive important files to cloud storage
- Batch upload images or documents

**Example:** "Upload the policy document to Campaign Materials folder"
