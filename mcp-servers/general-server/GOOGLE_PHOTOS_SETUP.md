# Google Photos API Setup Guide
**For MCP General Server v2.3.1**
**Created:** November 12, 2025

---

## Quick Links

- **Google Cloud Console:** https://console.cloud.google.com/
- **Enable API:** https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com
- **Credentials:** https://console.cloud.google.com/apis/credentials
- **Official Docs:** https://developers.google.com/photos/library/guides/get-started

---

## Prerequisites

You should already have:
- ✅ Google Cloud project created
- ✅ OAuth consent screen configured
- ✅ OAuth credentials downloaded at `/home/dave/skippy/.credentials/credentials.json`

If not, follow the Google Drive setup first: `GOOGLE_DRIVE_SETUP.md`

---

## Step 1: Enable Google Photos Library API (1 minute)

1. Go to: https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com
2. Make sure your project is selected (top bar)
3. Click "Enable" button
4. Wait for confirmation (~10 seconds)

---

## Step 2: Update OAuth Scopes (2 minutes)

You need to add Photos scopes to your OAuth consent screen:

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Click "Edit App"
3. Scroll to "Scopes" section, click "Add or Remove Scopes"
4. Search for "photoslibrary"
5. Select these scopes:
   - ✅ `.../auth/photoslibrary.readonly` - Read access to photos
   - ✅ `.../auth/photoslibrary.readonly.appcreateddata` - Read app-created data
6. Click "Update"
7. Click "Save and Continue"
8. Click "Back to Dashboard"

---

## Step 3: Install Python Dependencies (1 minute)

The MCP server needs the Google Photos Library client:

```bash
cd /home/dave/skippy/mcp-servers/general-server
source .venv/bin/activate
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**Note:** These should already be installed from Google Drive setup.

---

## Step 4: Update Environment Configuration

The `.env` file needs to include Photos scopes:

```bash
# Edit the .env file to add Photos scope
nano /home/dave/skippy/mcp-servers/general-server/.env
```

Update the `GOOGLE_SCOPES` line to include Photos:

```bash
# Old (Drive only):
GOOGLE_DRIVE_SCOPES=https://www.googleapis.com/auth/drive.readonly

# New (Drive + Photos):
GOOGLE_SCOPES=https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/photoslibrary.readonly

# Token paths (already configured)
GOOGLE_CREDENTIALS_PATH=/home/dave/skippy/.credentials/credentials.json
GOOGLE_TOKEN_PATH=/home/dave/skippy/.credentials/google_token.json
```

---

## Step 5: Re-authorize with New Scopes (2 minutes)

Since you're adding a new scope (Photos), you need to re-authorize:

```bash
# Delete existing token
rm /home/dave/skippy/.credentials/google_drive_token.json

# Restart MCP server
# The next time you use a Google tool, browser will open for re-authorization
```

When the browser opens:
1. Select your Google account
2. Review permissions (now includes Photos)
3. Click "Continue" on security warning
4. Click "Allow" to grant access
5. Close browser when complete

New token will be saved with both Drive and Photos access.

---

## Step 6: Verify Setup

Test your Google Photos access:

```python
# Test from Python (after implementation)
from server import gphotos_list_albums

result = gphotos_list_albums(10)
print(result)
```

Expected output:
```json
{
  "success": true,
  "count": X,
  "albums": [
    {
      "id": "...",
      "title": "Album Name",
      "mediaItemsCount": "42",
      "coverPhotoUrl": "..."
    }
  ]
}
```

---

## Available Tools (To Be Implemented)

### 1. List Albums
```python
gphotos_list_albums(max_results=20)
# Returns: List of your photo albums
```

### 2. Search Media Items
```python
gphotos_search_media(
    album_id=None,
    start_date="2025-01-01",
    end_date="2025-12-31",
    max_results=50
)
# Returns: Photos/videos matching criteria
```

### 3. Get Album Contents
```python
gphotos_get_album_contents(album_id, max_results=100)
# Returns: All media items in an album
```

### 4. Download Media Item
```python
gphotos_download_media(media_id, output_path)
# Downloads a photo/video to local file
```

### 5. Get Media Metadata
```python
gphotos_get_media_metadata(media_id)
# Returns: Full metadata (location, camera info, etc.)
```

### 6. Search by Location
```python
gphotos_search_by_location(
    location_name="San Francisco",
    max_results=50
)
# Returns: Photos taken at location
```

---

## API Scopes Explained

| Scope | Access Level | Usage |
|-------|-------------|-------|
| `photoslibrary.readonly` | Read-only access | Browse albums, download photos |
| `photoslibrary.readonly.appcreateddata` | Read app-created data | Access media items added by your app |
| `photoslibrary` | Full access | Upload, modify, delete photos |
| `photoslibrary.appendonly` | Add-only | Upload new photos only |

**Current Setup:** `photoslibrary.readonly` (safe, read-only)

---

## Troubleshooting

### Error: "API has not been enabled"
**Solution:**
```bash
# Enable Photos API:
# 1. Go to: https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com
# 2. Click "Enable"
```

### Error: "insufficient_scope"
**Solution:**
```bash
# Delete token and re-authorize with new scopes:
rm /home/dave/skippy/.credentials/google_token.json
# Restart MCP server or run tool again
```

### Error: "The OAuth client was deleted"
**Solution:**
- Your OAuth credentials may have been deleted
- Re-download credentials.json from Google Cloud Console
- Place in `/home/dave/skippy/.credentials/credentials.json`

### Photos not showing up
**Possible causes:**
1. Authorization incomplete - check token file exists
2. Wrong Google account - verify you authorized correct account
3. No photos in library - test with account that has photos
4. Date filters too restrictive - try broader date range

---

## Security & Privacy

### What Access is Granted?
- ✅ **Read-only** access to your Google Photos
- ✅ Can list albums and browse photos
- ✅ Can download photos you own
- ❌ **Cannot** upload photos
- ❌ **Cannot** modify or delete photos
- ❌ **Cannot** share photos

### Revoking Access
To revoke at any time:
1. Go to: https://myaccount.google.com/permissions
2. Find "MCP General Server"
3. Click "Remove Access"

### Data Storage
- Token stored locally: `/home/dave/skippy/.credentials/google_token.json`
- No photos stored by MCP server (only downloads when requested)
- Metadata cached temporarily during operations

---

## Rate Limits & Quotas

**Free Tier:**
- 10,000 requests per day per project
- 10 requests per second per project
- 1,000 requests per 100 seconds per user

**Sufficient for:**
- ✅ Personal browsing and downloading
- ✅ Small automation scripts
- ✅ Organizing albums
- ❌ Mass downloads (respect quotas)

---

## Usage Examples

### List your photo albums
```python
# Get first 20 albums
result = gphotos_list_albums(20)
for album in result['albums']:
    print(f"{album['title']}: {album['mediaItemsCount']} items")
```

### Search photos by date range
```python
# Get photos from January 2025
result = gphotos_search_media(
    start_date="2025-01-01",
    end_date="2025-01-31",
    max_results=100
)
```

### Download specific album
```python
# Get album contents
album_id = "ABC123..."
contents = gphotos_get_album_contents(album_id)

# Download each photo
for item in contents['mediaItems']:
    gphotos_download_media(
        item['id'],
        f"/home/dave/Downloads/{item['filename']}"
    )
```

### Search by creation date
```python
# Photos from vacation
result = gphotos_search_media(
    start_date="2024-07-01",
    end_date="2024-07-15"
)
```

---

## Integration with Existing Tools

Google Photos tools will work alongside Google Drive tools:

```python
# Use both APIs together:

# 1. Find photos
photos = gphotos_search_media(start_date="2025-01-01")

# 2. Download to temp directory
for photo in photos['mediaItems']:
    gphotos_download_media(photo['id'], f"/tmp/{photo['filename']}")

# 3. Upload to Google Drive
gdrive_upload_file(f"/tmp/{photo['filename']}", "folder_id_here")
```

---

## Quick Setup Checklist

- [ ] Enable Google Photos Library API
- [ ] Update OAuth consent screen with Photos scopes
- [ ] Verify Python dependencies installed
- [ ] Update `.env` with Photos scope
- [ ] Delete old token file
- [ ] Re-authorize with new scopes (browser will open)
- [ ] Verify token saved at `.credentials/google_token.json`
- [ ] Test with `gphotos_list_albums()`

**Total Time:** ~6 minutes (mostly waiting for API enablement)

---

## API Documentation

**Official Resources:**
- API Overview: https://developers.google.com/photos/library/guides/overview
- API Reference: https://developers.google.com/photos/library/reference/rest
- Python Client: https://developers.google.com/photos/library/guides/get-started-python
- Search Filters: https://developers.google.com/photos/library/guides/list#filter-media-items

**Community:**
- Stack Overflow: https://stackoverflow.com/questions/tagged/google-photos-api
- GitHub Issues: https://github.com/googleapis/google-api-python-client/issues

---

## Comparison: Google Photos vs Google Drive

| Feature | Google Photos | Google Drive |
|---------|--------------|--------------|
| **Purpose** | Photo/video library | File storage |
| **Organization** | Albums, dates, locations | Folders |
| **Metadata** | EXIF, GPS, faces | Basic file info |
| **Search** | By date, location, content | By name, type |
| **Best For** | Photo management | Document storage |

**Use together:** Photos for browsing images, Drive for backup/storage

---

## Next Steps After Setup

1. **Test basic listing:**
   ```python
   gphotos_list_albums(5)
   ```

2. **Browse recent photos:**
   ```python
   gphotos_search_media(start_date="2025-11-01", max_results=10)
   ```

3. **Download a photo:**
   ```python
   # Get photo ID from search result
   gphotos_download_media(photo_id, "/tmp/test_photo.jpg")
   ```

4. **Integrate with campaign:**
   - Search for campaign event photos
   - Download high-res images for website
   - Organize by event/date

---

## Cost

**Free Forever:**
- Google Photos Library API is 100% free
- No credit card required
- Generous rate limits for personal use

**Storage:**
- Photos stored in your Google account
- 15 GB free (shared with Drive/Gmail)
- Unlimited "High quality" (compressed) storage

---

**Last Updated:** November 12, 2025
**MCP Server Version:** 2.3.1 (pending)
**Status:** Documentation complete, implementation pending
