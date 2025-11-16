# MCP General Server v2.3.1 Changelog

**Release Date:** November 12, 2025
**Author:** Claude Code

---

## 🎉 New Features: Google Photos Integration

Added 6 new tools for managing Google Photos:

### Authentication
- **`_get_google_photos_service()`** - OAuth authentication helper for Photos Library API
- Uses same credentials as Google Drive (unified Google account)
- Separate token file for Photos access
- Read-only scope by default for security

### Tools Added

1. **`gphotos_list_albums(max_results)`**
   - List all photo albums from Google Photos
   - Returns album ID, title, media count, cover photo URL
   - Pagination support for large collections

2. **`gphotos_search_media(album_id, start_date, end_date, max_results)`**
   - Search photos and videos with flexible filters
   - Filter by album, date range, or both
   - Returns media ID, filename, MIME type, dimensions, creation time
   - Base URLs for temporary downloads (60-minute validity)

3. **`gphotos_get_album_contents(album_id, max_results)`**
   - Get all media items from a specific album
   - Includes album metadata (title, total item count)
   - Pagination for albums with many photos

4. **`gphotos_download_media(media_id, output_path)`**
   - Download original quality photos or videos
   - Automatic format detection (photo vs video)
   - Returns file size, dimensions, MIME type

5. **`gphotos_get_media_metadata(media_id)`**
   - Get detailed EXIF and metadata
   - Photo info: camera make/model, focal length, aperture, ISO, exposure
   - Video info: FPS, codec, processing status
   - Creation time, dimensions, product URL

6. **Helper function for Photos API integration**
   - Full OAuth flow with automatic browser launch
   - Token refresh on expiration
   - Credential caching for future sessions

---

## 📝 Configuration Changes

### New Environment Variables (.env)

```bash
# Google Photos Integration (OAuth)
GOOGLE_PHOTOS_CREDENTIALS_PATH=/home/dave/skippy/.credentials/google_drive_credentials.json
GOOGLE_PHOTOS_TOKEN_PATH=/home/dave/skippy/.credentials/google_photos_token.json
GOOGLE_PHOTOS_SCOPES=https://www.googleapis.com/auth/photoslibrary.readonly
```

**Note:** Uses same credentials file as Google Drive for convenience.

---

## 📚 Documentation Added

1. **`GOOGLE_PHOTOS_SETUP.md`** - Complete setup guide
   - Step-by-step API enablement
   - OAuth consent screen configuration
   - Scope selection and security considerations
   - Troubleshooting common issues
   - Usage examples and best practices
   - Rate limits and quotas

---

## 🔧 Technical Details

### Dependencies
No new dependencies required - uses existing `google-api-python-client` package installed for Google Drive integration.

### API Information
- **API:** Google Photos Library API v1
- **Scope:** `photoslibrary.readonly` (read-only, safe)
- **Rate Limits:** 10,000 requests/day (free tier)
- **Authentication:** OAuth 2.0 with local server flow

### File Structure
```
mcp-servers/general-server/
├── server.py (updated to v2.3.1)
├── .env (updated with Photos config)
├── GOOGLE_PHOTOS_SETUP.md (new)
├── CHANGELOG_v2.3.1.md (this file)
└── .credentials/
    ├── google_drive_credentials.json (shared)
    ├── google_drive_token.json (Drive)
    └── google_photos_token.json (Photos - new)
```

---

## 🎯 Use Cases

### Campaign Photography Management
```python
# Find photos from recent campaign event
photos = gphotos_search_media(
    start_date="2025-11-01",
    end_date="2025-11-12",
    max_results=50
)

# Download high-res images for website
for photo in photos['mediaItems']:
    gphotos_download_media(
        photo['id'],
        f"/home/dave/campaign_photos/{photo['filename']}"
    )
```

### Album Organization
```python
# List all albums
albums = gphotos_list_albums(100)

# Find campaign events album
campaign_album = [a for a in albums if 'Campaign' in a['title']][0]

# Get all photos from album
contents = gphotos_get_album_contents(campaign_album['id'])
```

### Metadata Extraction
```python
# Get detailed photo info
metadata = gphotos_get_media_metadata(photo_id)
# Returns camera settings, GPS location, dimensions, etc.
```

---

## 🔒 Security Notes

**Read-Only Access:**
- Cannot upload photos
- Cannot modify or delete photos
- Cannot create albums
- Can only browse and download own photos

**Token Storage:**
- Tokens stored locally in `.credentials/`
- Not committed to git (in `.gitignore`)
- Automatic refresh on expiration
- Can be revoked at: https://myaccount.google.com/permissions

---

## 🧪 Testing Checklist

Before using Photos tools:

- [ ] Enable Google Photos Library API in Cloud Console
- [ ] Update OAuth consent screen with Photos scope
- [ ] Verify credentials.json exists
- [ ] Run first tool to trigger OAuth flow
- [ ] Confirm browser opens for authorization
- [ ] Check token saved at `.credentials/google_photos_token.json`
- [ ] Test `gphotos_list_albums()`
- [ ] Test `gphotos_search_media()` with date filter
- [ ] Test `gphotos_download_media()` with sample photo

---

## 📊 Statistics

**Code Changes:**
- Lines added: ~400
- New tools: 6
- New helper functions: 1
- Documentation pages: 1
- Configuration variables: 3

**Tool Count:**
- Total MCP tools: 70+ (was 64)
- Google integration tools: 22 (16 Drive + 6 Photos)

---

## 🔄 Upgrade Path

### From v2.3.0 to v2.3.1

1. **Pull latest code:**
   ```bash
   cd /home/dave/skippy/mcp-servers/general-server
   git pull
   ```

2. **Update .env file:**
   ```bash
   # Add Photos configuration (see section above)
   nano .env
   ```

3. **Enable Photos API:**
   - Visit: https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com
   - Click "Enable"

4. **Update OAuth scopes:**
   - Go to OAuth consent screen
   - Add `photoslibrary.readonly` scope

5. **First run authorization:**
   ```python
   # Use any Photos tool - browser will open
   gphotos_list_albums(5)
   ```

6. **Verify token created:**
   ```bash
   ls -la /home/dave/skippy/.credentials/google_photos_token.json
   ```

---

## 🐛 Known Issues

None at this time.

---

## 🚀 Future Enhancements

Potential additions for v2.4.0:

- [ ] Upload photos to Google Photos
- [ ] Create and manage albums
- [ ] Add photos to existing albums
- [ ] Batch download entire albums
- [ ] Location-based search
- [ ] Face detection search
- [ ] Shared album management
- [ ] Photo metadata editing

---

## 📞 Support

**Documentation:**
- Setup Guide: `GOOGLE_PHOTOS_SETUP.md`
- Drive Setup: `GOOGLE_DRIVE_SETUP.md`
- API Docs: https://developers.google.com/photos/library/guides/overview

**Issues:**
- Report bugs or request features
- Check troubleshooting section in setup guide

---

## 🙏 Acknowledgments

- Google Photos Library API documentation
- Google Cloud Platform OAuth implementation
- MCP FastMCP framework

---

**Version:** 2.3.1
**Previous Version:** 2.3.0
**Next Version:** TBD
