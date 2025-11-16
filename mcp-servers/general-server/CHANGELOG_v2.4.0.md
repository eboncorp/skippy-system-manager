# MCP General Server v2.4.0 Changelog

**Release Date:** November 16, 2025
**Major Update:** Google Photos Picker API Migration

---

## Summary

Replaced deprecated Google Photos Library API (removed March 31, 2025) with the new Google Photos Picker API. This is a breaking change that replaces 5 old tools with 5 new tools using a different workflow.

---

## Breaking Changes

### Removed Tools (Deprecated Library API)
- ❌ `gphotos_list_albums()` - No longer supported
- ❌ `gphotos_search_media()` - No longer supported
- ❌ `gphotos_get_album_contents()` - No longer supported
- ❌ `gphotos_download_media()` - No longer supported
- ❌ `gphotos_get_media_metadata()` - No longer supported

### New Tools (Picker API)
- ✅ `gphotos_create_picker_session()` - Create photo selection session
- ✅ `gphotos_check_session()` - Poll session status
- ✅ `gphotos_get_selected_media()` - Retrieve selected photos
- ✅ `gphotos_download_selected()` - Download photos by baseUrl
- ✅ `gphotos_delete_session()` - Clean up sessions

---

## Why This Change?

Google deprecated the following scopes on March 31, 2025:
- `photoslibrary.readonly`
- `photoslibrary.sharing`
- `photoslibrary`

After this date, these scopes return **403 PERMISSION_DENIED** errors. Google recommends migrating to the Picker API for photo selection use cases.

---

## New Workflow

The Picker API uses a session-based workflow instead of direct library access:

```python
# 1. Create a picker session
session = gphotos_create_picker_session()
# Returns: session_id, picker_uri

# 2. Open picker_uri in browser
# User selects photos in Google Photos interface

# 3. Poll for completion
status = gphotos_check_session(session_id)
# Wait until media_items_set = True

# 4. Get selected photos
photos = gphotos_get_selected_media(session_id)
# Returns: list of photos with baseUrl

# 5. Download photos
gphotos_download_selected(base_url, output_path, mime_type)

# 6. Optionally delete session
gphotos_delete_session(session_id)
```

---

## OAuth Scope Changes

**Old Scope (DEPRECATED):**
```
https://www.googleapis.com/auth/photoslibrary.readonly
```

**New Scope:**
```
https://www.googleapis.com/auth/photospicker.mediaitems.readonly
```

---

## Configuration Updates

`.env` file updated:
```bash
# Old
GOOGLE_PHOTOS_SCOPES=https://www.googleapis.com/auth/photoslibrary.readonly

# New
GOOGLE_PHOTOS_SCOPES=https://www.googleapis.com/auth/photospicker.mediaitems.readonly
```

---

## Key Differences

| Feature | Old Library API | New Picker API |
|---------|----------------|----------------|
| **Access Model** | Direct library access | Session-based selection |
| **User Experience** | Programmatic queries | Interactive picker UI |
| **Album Browsing** | Yes | No (user selects directly) |
| **Search by Date** | Yes | No (user searches in UI) |
| **Privacy** | Full library access | Only selected photos |
| **User Control** | Limited | Full control over sharing |

---

## Limitations

1. **No programmatic search** - Cannot query albums or filter by date programmatically
2. **Session-based** - Requires user interaction via picker UI
3. **60-minute expiry** - baseUrls expire after 60 minutes
4. **User-driven** - User must manually select photos in Google Photos

---

## Benefits

1. **Privacy-focused** - Users explicitly choose what to share
2. **Future-proof** - Uses current Google-recommended API
3. **Secure** - No broad library access
4. **Compliant** - Follows Google's new data access policies

---

## Tool Count Update

**v2.3.2:** 79 tools (5 deprecated Google Photos Library tools)
**v2.4.0:** 79 tools (5 new Google Photos Picker tools)

Total tool count remains the same.

---

## Files Changed

1. `server.py` - Replaced Google Photos Library API tools with Picker API tools
2. `.env` - Updated GOOGLE_PHOTOS_SCOPES to use picker scope
3. `CHANGELOG_v2.4.0.md` - This file

---

## Migration Steps

1. Enable Google Photos Picker API in Google Cloud Console
2. Add `photospicker.mediaitems.readonly` scope to OAuth consent screen
3. Delete old token: `rm ~/.credentials/google_photos_token.json`
4. Re-authorize with new scope (browser will open)
5. Update any code using old gphotos_* functions to new workflow

---

## Testing Verified

- ✅ Session creation successful
- ✅ Session ID returned
- ✅ Picker URI generated
- ✅ Token saved with correct scope
- ✅ Pexels integration still functional (unchanged)

---

## Recommendation

For most stock photography needs, continue using Pexels (3M+ free photos). Use Google Photos Picker API when you need to:
- Import specific personal photos
- Let users select campaign photos from their library
- Maintain user privacy and control

---

**Previous Version:** v2.3.2 (November 12, 2025)
**This Version:** v2.4.0 (November 16, 2025)
