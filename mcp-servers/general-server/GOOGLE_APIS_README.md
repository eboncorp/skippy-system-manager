# Google APIs Integration Guide

**MCP General Server v2.3.1**
**Last Updated:** November 12, 2025

---

## Overview

The MCP General Server includes comprehensive Google API integration:

- ✅ **Google Drive** (16 tools) - v2.3.0
- ✅ **Google Photos** (6 tools) - v2.3.1

Both use the same OAuth credentials and follow identical setup patterns.

---

## Quick Links

| Resource | Link |
|----------|------|
| **Enable Drive API** | https://console.cloud.google.com/apis/library/drive.googleapis.com |
| **Enable Photos API** | https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com |
| **OAuth Credentials** | https://console.cloud.google.com/apis/credentials |
| **Consent Screen** | https://console.cloud.google.com/apis/credentials/consent |
| **Manage Permissions** | https://myaccount.google.com/permissions |

---

## Setup Guides

### Google Drive
- **Quick Start:** `GOOGLE_DRIVE_SETUP.md`
- **Status:** ✅ Already configured
- **Token:** `~/.config/skippy/credentials/google_drive_token.json`

### Google Photos
- **Quick Start:** `GOOGLE_PHOTOS_QUICKSTART.md` ⭐ START HERE
- **Complete Guide:** `GOOGLE_PHOTOS_SETUP.md`
- **Status:** ⏳ Needs authorization (4 minutes)
- **Token:** `~/.config/skippy/credentials/google_photos_token.json` (created on first use)

---

## Available Tools

### Google Drive (16 tools)

| Category | Tools |
|----------|-------|
| **Search & Browse** | `gdrive_search_files`, `gdrive_list_folder_contents`, `gdrive_get_folder_id_by_name` |
| **Read** | `gdrive_download_file`, `gdrive_read_document`, `gdrive_get_file_metadata` |
| **Organize** | `gdrive_create_folder`, `gdrive_move_file`, `gdrive_batch_move_files`, `gdrive_organize_by_pattern` |
| **Manage** | `gdrive_rename_file`, `gdrive_trash_file`, `gdrive_copy_file` |
| **Upload** | `gdrive_upload_file`, `gdrive_batch_upload` |
| **Share** | `gdrive_share_file` |

### Google Photos (6 tools)

| Category | Tools |
|----------|-------|
| **Browse** | `gphotos_list_albums`, `gphotos_get_album_contents` |
| **Search** | `gphotos_search_media` (by date, album) |
| **Download** | `gphotos_download_media` |
| **Metadata** | `gphotos_get_media_metadata` |

---

## Configuration

### Environment Variables (.env)

```bash
# Google Drive
GOOGLE_DRIVE_CREDENTIALS_PATH=~/.config/skippy/credentials/google_drive_credentials.json
GOOGLE_DRIVE_TOKEN_PATH=~/.config/skippy/credentials/google_drive_token.json
GOOGLE_DRIVE_SCOPES=https://www.googleapis.com/auth/drive

# Google Photos
GOOGLE_PHOTOS_CREDENTIALS_PATH=~/.config/skippy/credentials/google_drive_credentials.json
GOOGLE_PHOTOS_TOKEN_PATH=~/.config/skippy/credentials/google_photos_token.json
GOOGLE_PHOTOS_SCOPES=https://www.googleapis.com/auth/photoslibrary.readonly
```

### Credentials Structure

```
~/.config/skippy/credentials/
├── credentials.json                    # OAuth client secret
├── google_drive_credentials.json       # Symlink to credentials.json
├── google_drive_token.json             # Drive access token ✅
└── google_photos_token.json            # Photos access token (created on first use)
```

---

## Setup Status

| Component | Status | Action Needed |
|-----------|--------|---------------|
| Google Cloud Project | ✅ Complete | None |
| OAuth Credentials | ✅ Complete | None |
| Drive API | ✅ Complete | None |
| Drive Token | ✅ Active | None |
| **Photos API** | ⏳ **Pending** | **Enable in Console** |
| **Photos Scope** | ⏳ **Pending** | **Add to OAuth** |
| **Photos Token** | ⏳ **Pending** | **Authorize** |

---

## Next Steps for Photos

### 1. Enable Photos API (1 min)
```
https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com
→ Click "Enable"
```

### 2. Add Photos Scope (2 min)
```
https://console.cloud.google.com/apis/credentials/consent
→ Edit App
→ Add or Remove Scopes
→ Select: .../auth/photoslibrary.readonly
→ Save
```

### 3. Authorize (1 min)
```python
# In Claude Code, use any Photos tool
gphotos_list_albums(10)
# Browser opens → Authorize → Done!
```

**Total Time:** ~4 minutes

---

## Common Tasks

### Campaign Photo Management

```python
# 1. Find campaign event photos
photos = gphotos_search_media(
    start_date="2025-11-01",
    end_date="2025-11-12",
    max_results=50
)

# 2. Download high-res images
for photo in photos['mediaItems']:
    if int(photo['width']) >= 1920:
        gphotos_download_media(
            photo['id'],
            f"/home/dave/campaign_photos/{photo['filename']}"
        )

# 3. Upload to Google Drive for backup
for file in os.listdir('/home/dave/campaign_photos'):
    gdrive_upload_file(
        f"/home/dave/campaign_photos/{file}",
        "DRIVE_FOLDER_ID"
    )
```

### Document + Photo Workflow

```python
# 1. Search Drive for campaign docs
docs = gdrive_search_files("name contains 'Campaign'", 20)

# 2. Search Photos for campaign images
photos = gphotos_search_media(start_date="2025-10-01")

# 3. Download both to workspace
for doc in docs:
    gdrive_download_file(doc['id'], f"/workspace/{doc['name']}")

for photo in photos:
    gphotos_download_media(photo['id'], f"/workspace/{photo['filename']}")
```

---

## API Quotas & Limits

### Google Drive
- **Queries per day:** 1,000,000,000 (1 billion)
- **Queries per 100 seconds:** 20,000
- **Cost:** Free forever

### Google Photos
- **Requests per day:** 10,000
- **Requests per second:** 10
- **Cost:** Free forever

Both are more than sufficient for personal/campaign use.

---

## Security & Privacy

### What Access is Granted?

| API | Read | Write | Delete |
|-----|------|-------|--------|
| Google Drive | ✅ | ✅ | ✅ (trash) |
| Google Photos | ✅ | ❌ | ❌ |

### Revoking Access

Anytime: https://myaccount.google.com/permissions
→ Find "MCP General Server"
→ Remove Access

### Token Security

- Stored locally only
- Not committed to git (in `.gitignore`)
- Encrypted at rest by OS
- Auto-refresh on expiration
- Can be manually deleted to force re-auth

---

## Troubleshooting

### "API not enabled"
**Solution:** Enable the API in Cloud Console (links at top)

### "insufficient_scope"
**Solution:** Delete token and re-authorize
```bash
rm ~/.config/skippy/credentials/google_photos_token.json
# Run tool again
```

### "Credentials not found"
**Solution:** Check symlink exists
```bash
ls -la ~/.config/skippy/credentials/google_drive_credentials.json
# Should point to credentials.json
```

### Browser doesn't open
**Solution:** Copy URL from console and open manually

### Wrong Google account
**Solution:** Use private/incognito window for authorization to select different account

---

## Documentation Files

| File | Purpose |
|------|---------|
| `GOOGLE_APIS_README.md` | This file - overview of both APIs |
| `GOOGLE_DRIVE_SETUP.md` | Drive setup guide (reference) |
| `GOOGLE_PHOTOS_SETUP.md` | Photos complete setup guide |
| `GOOGLE_PHOTOS_QUICKSTART.md` | Photos quick start (4 minutes) |
| `GDRIVE_TOOLS_REFERENCE.md` | Drive tools detailed reference |
| `CHANGELOG_v2.3.1.md` | Latest version changes |

---

## Support Resources

**Official Documentation:**
- Drive API: https://developers.google.com/drive/api/guides/about-sdk
- Photos API: https://developers.google.com/photos/library/guides/overview

**Community:**
- Stack Overflow: https://stackoverflow.com/questions/tagged/google-api
- GitHub Issues: https://github.com/googleapis/google-api-python-client

**Google Cloud:**
- Console: https://console.cloud.google.com/
- Support: https://cloud.google.com/support

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.3.1 | 2025-11-12 | Added Google Photos (6 tools) |
| 2.3.0 | 2025-11-11 | Added 5 Drive tools (upload, share, metadata) |
| 2.1.0 | 2025-11-10 | Initial Google Drive integration (11 tools) |

---

## Quick Reference Card

```bash
# GOOGLE DRIVE
gdrive_search_files("query", max)          # Search Drive
gdrive_download_file(id, path)             # Download file
gdrive_upload_file(path, folder_id)        # Upload file
gdrive_list_folder_contents(folder_id)     # List folder
gdrive_move_file(file_id, new_folder_id)   # Move file

# GOOGLE PHOTOS (after setup)
gphotos_list_albums(max)                   # List albums
gphotos_search_media(start, end, max)      # Search photos
gphotos_download_media(media_id, path)     # Download photo
gphotos_get_album_contents(album_id)       # Get album photos
gphotos_get_media_metadata(media_id)       # Get EXIF data
```

---

## Summary

**Total Google Tools:** 22
- Drive: 16 tools (full read/write)
- Photos: 6 tools (read-only)

**Setup Status:**
- Drive: ✅ Complete and working
- Photos: ⏳ 4 minutes of setup needed

**Next Action:** Follow `GOOGLE_PHOTOS_QUICKSTART.md` to enable Photos access

---

**Questions?** Check the troubleshooting section or relevant setup guide.

**Ready to start?** Open `GOOGLE_PHOTOS_QUICKSTART.md` and follow the 3 steps!
