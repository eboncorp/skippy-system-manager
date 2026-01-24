# Google Photos Quick Start Guide

**Version:** 2.3.1
**Date:** November 12, 2025

---

## Prerequisites ✅

You already have:
- [x] Google Cloud project created
- [x] OAuth credentials at `~/.config/skippy/credentials/credentials.json`
- [x] Google Drive API enabled and working

---

## Setup (5 Minutes)

### Step 1: Enable Google Photos API

Open in browser:
```
https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com
```

1. Verify your project is selected (top bar)
2. Click **"Enable"** button
3. Wait ~10 seconds for confirmation

### Step 2: Add Photos Scope to OAuth

Open in browser:
```
https://console.cloud.google.com/apis/credentials/consent
```

1. Click **"Edit App"**
2. Scroll to **"Scopes"** section
3. Click **"Add or Remove Scopes"**
4. Search for: `photoslibrary`
5. Select: ☑️ `.../auth/photoslibrary.readonly`
6. Click **"Update"**
7. Click **"Save and Continue"**
8. Click **"Back to Dashboard"**

### Step 3: First Use (Triggers OAuth)

Open Claude Code and use any Photos tool:

```python
# This will open your browser for authorization
gphotos_list_albums(5)
```

**What happens:**
1. Browser opens automatically
2. Select your Google account
3. Click "Continue" on security warning
4. Click "Allow" to grant Photos access
5. Browser shows "Authentication complete"
6. Token saved to `.credentials/google_photos_token.json`

**Done!** You won't need to authorize again.

---

## Quick Test

Try these commands to verify setup:

### 1. List Albums
```python
# See all your photo albums
result = gphotos_list_albums(10)
print(result)
```

### 2. Search Recent Photos
```python
# Photos from last 30 days
result = gphotos_search_media(
    start_date="2025-10-12",
    end_date="2025-11-12",
    max_results=20
)
print(result)
```

### 3. Get Album Contents
```python
# Get photos from specific album
# (use album ID from list_albums result)
result = gphotos_get_album_contents("ALBUM_ID_HERE", 50)
print(result)
```

### 4. Download a Photo
```python
# Download photo to local file
# (use media ID from search result)
result = gphotos_download_media(
    "MEDIA_ID_HERE",
    "/home/dave/Downloads/test_photo.jpg"
)
print(result)
```

---

## Common Tasks

### Find Campaign Event Photos

```python
# Search by date range
photos = gphotos_search_media(
    start_date="2025-11-01",
    end_date="2025-11-05",
    max_results=50
)

# Results include photo IDs and filenames
for photo in photos['mediaItems']:
    print(f"{photo['filename']} - {photo['creationTime']}")
```

### Download Entire Album

```python
# 1. List albums to find ID
albums = gphotos_list_albums(20)

# 2. Find your album
for album in albums['albums']:
    if 'Campaign' in album['title']:
        print(f"Found: {album['title']} (ID: {album['id']})")
        album_id = album['id']

# 3. Get album contents
contents = gphotos_get_album_contents(album_id, 100)

# 4. Download each photo
for item in contents['mediaItems']:
    gphotos_download_media(
        item['id'],
        f"/home/dave/campaign_photos/{item['filename']}"
    )
```

### Get Photo Metadata (Camera Settings)

```python
# Get detailed EXIF data
metadata = gphotos_get_media_metadata(media_id)

# Shows:
# - Camera make/model
# - Focal length, aperture, ISO
# - Exposure time
# - GPS location (if available)
# - Original dimensions
```

---

## Available Tools

| Tool | Purpose | Returns |
|------|---------|---------|
| `gphotos_list_albums(max)` | List all albums | Album ID, title, count |
| `gphotos_search_media(...)` | Search photos by date/album | Media items with IDs |
| `gphotos_get_album_contents(id)` | Get photos from album | Media items in album |
| `gphotos_download_media(id, path)` | Download photo/video | File saved locally |
| `gphotos_get_media_metadata(id)` | Get EXIF & metadata | Camera settings, location |

---

## Troubleshooting

### "API not enabled"
**Solution:** Visit https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com and click Enable.

### "insufficient_scope"
**Solution:**
```bash
# Delete token and re-authorize
rm ~/.config/skippy/credentials/google_photos_token.json
# Run tool again - browser will open
```

### Browser doesn't open
**Solution:** Check the console output for the authorization URL and open it manually in your browser.

### "No albums found"
**Possible causes:**
- Wrong Google account (make sure you authorized the account with photos)
- No albums created in Google Photos
- Permission issue (re-authorize)

### Download fails
**Check:**
- Media ID is correct (from search result)
- Output path is writable
- Internet connection active (URLs expire after 60 minutes)

---

## Important Notes

**Read-Only Access:**
- ✅ Can browse all your photos
- ✅ Can download photos
- ✅ Can view metadata
- ❌ Cannot upload photos
- ❌ Cannot delete photos
- ❌ Cannot modify albums

**URLs Expire:**
- Download URLs (`baseUrl`) expire after 60 minutes
- Re-run search to get fresh URLs if needed

**Rate Limits:**
- 10,000 requests/day (free tier)
- Sufficient for personal use
- Be respectful of quotas

**Privacy:**
- Token stored locally only
- Not shared with anyone
- Can revoke at: https://myaccount.google.com/permissions

---

## File Locations

```
/home/dave/skippy/
├── .credentials/
│   ├── credentials.json (OAuth client)
│   ├── google_drive_credentials.json -> credentials.json
│   ├── google_drive_token.json (Drive access)
│   └── google_photos_token.json (Photos access - created on first use)
└── mcp-servers/general-server/
    ├── server.py (v2.3.1)
    ├── .env (configuration)
    ├── GOOGLE_PHOTOS_SETUP.md (detailed setup)
    └── GOOGLE_PHOTOS_QUICKSTART.md (this file)
```

---

## Next Steps

1. ✅ Complete setup (5 minutes)
2. ✅ Test with `gphotos_list_albums()`
3. ✅ Search for recent photos
4. ✅ Download a test photo
5. Use for campaign photo management!

---

## Support

**Documentation:**
- Full setup: `GOOGLE_PHOTOS_SETUP.md`
- API docs: https://developers.google.com/photos/library/guides/overview

**Help:**
- Check troubleshooting section above
- Verify credentials and API enablement
- Test with Google Drive tools first (same auth flow)

---

## Summary

**Setup Steps:**
1. Enable Photos API (1 click)
2. Add Photos scope to OAuth (5 clicks)
3. Run first tool (opens browser)
4. Authorize (2 clicks)
5. Done! ✅

**Time Required:** ~5 minutes

**Difficulty:** Easy (same as Google Drive)

**Benefit:** Access all your Google Photos from command line!

---

**Happy photo browsing! 📸**
