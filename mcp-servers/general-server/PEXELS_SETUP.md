# Pexels Stock Photos Integration

**MCP General Server v2.3.2**
**Created:** November 12, 2025

---

## Overview

Pexels integration provides access to millions of free stock photos for your campaign website and marketing materials.

**Features:**
- ✅ Search millions of high-quality stock photos
- ✅ Download in multiple sizes (original, large, medium, small)
- ✅ Filter by orientation, size, and color
- ✅ Get curated/trending photos
- ✅ 100% free - unlimited requests
- ✅ No attribution required (but appreciated)

---

## Setup (Already Complete!)

✅ API Key configured in `.env`
✅ 4 Pexels tools added to MCP server
✅ Tested and working

---

## Available Tools

### 1. pexels_search_photos()

Search for stock photos by keyword.

**Parameters:**
- `query` (required): Search term (e.g., "campaign event", "community", "voting")
- `per_page`: Results per page (max 80, default 15)
- `page`: Page number (default 1)
- `orientation`: "landscape", "portrait", or "square"
- `size`: "large", "medium", or "small"
- `color`: "red", "orange", "yellow", "green", "turquoise", "blue", "violet", "pink", "brown", "black", "gray", "white"

**Returns:**
- Photo ID
- Photographer name and URL
- Photo dimensions
- Download URLs (original, large, medium, small)
- Average color
- Alt text

**Example:**
```python
# Search for campaign photos
result = pexels_search_photos(
    query="political campaign",
    per_page=20,
    orientation="landscape"
)
```

### 2. pexels_get_photo()

Get details of a specific photo by ID.

**Parameters:**
- `photo_id` (required): The Pexels photo ID

**Returns:**
- Full photo details
- All available download URLs
- Photographer information

**Example:**
```python
# Get photo details
result = pexels_get_photo(1464210)
```

### 3. pexels_download_photo()

Download a photo to local filesystem.

**Parameters:**
- `photo_id` (required): The Pexels photo ID
- `output_path` (required): Where to save the file
- `size`: "original", "large", "medium", "small" (default: "large")

**Returns:**
- Success confirmation
- File path
- File size
- Photographer name
- Dimensions

**Example:**
```python
# Download a photo
result = pexels_download_photo(
    photo_id=1464210,
    output_path="/home/dave/campaign_photos/hero_image.jpg",
    size="original"
)
```

### 4. pexels_curated_photos()

Get trending/curated photos (Pexels staff picks).

**Parameters:**
- `per_page`: Results per page (max 80, default 15)
- `page`: Page number (default 1)

**Returns:**
- List of curated photos
- Same format as search results

**Example:**
```python
# Get trending photos
result = pexels_curated_photos(per_page=20)
```

---

## Use Cases for RunDaveRun Campaign

### 1. Hero Images for Website

```python
# Search for professional political imagery
photos = pexels_search_photos(
    query="leadership professional",
    orientation="landscape",
    per_page=20
)

# Download high-res for homepage
pexels_download_photo(
    photo_id=selected_id,
    output_path="/home/dave/rundaverun/media/hero.jpg",
    size="original"
)
```

### 2. Event Backgrounds

```python
# Find community/event photos
community_photos = pexels_search_photos(
    query="community gathering",
    orientation="landscape",
    color="blue"  # Match campaign colors
)
```

### 3. Policy Page Headers

```python
# Different topics for policy pages
topics = [
    "education classroom",
    "healthcare hospital",
    "infrastructure construction",
    "public safety",
    "environment nature"
]

for topic in topics:
    photos = pexels_search_photos(query=topic, per_page=5)
    # Download best match for each policy page
```

### 4. Social Media Content

```python
# Get portrait orientation for social media
social_photos = pexels_search_photos(
    query="voting democracy",
    orientation="portrait",
    per_page=10
)

# Download medium size for social posts
pexels_download_photo(
    photo_id=photo_id,
    output_path="/home/dave/social_media/post_image.jpg",
    size="medium"
)
```

---

## Best Practices

### Attribution

While Pexels doesn't require attribution, it's good practice:

```html
<!-- Example attribution -->
<p class="photo-credit">
  Photo by <a href="photographer_url">Photographer Name</a>
  on <a href="https://www.pexels.com">Pexels</a>
</p>
```

### Search Tips

**Be specific:**
- ✅ "business meeting professional"
- ❌ "meeting"

**Use multiple searches:**
- Try variations: "vote", "voting", "ballot", "election"

**Filter strategically:**
- Use `orientation` for specific layouts
- Use `color` to match brand colors

### Download Strategy

**For web use:**
- Hero images: `original` or `large`
- Thumbnails: `medium` or `small`
- Social media: `medium`

**File naming:**
```python
# Use descriptive names
pexels_download_photo(
    photo_id=123456,
    output_path="/home/dave/rundaverun/media/homepage_hero_community.jpg"
)
```

---

## API Limits

**Free Tier:**
- ✅ Unlimited requests per month
- ✅ No rate limits
- ✅ Full resolution downloads
- ✅ Commercial use allowed

**Pexels License:**
- ✅ Free for personal and commercial use
- ✅ No attribution required
- ✅ Can modify photos
- ❌ Cannot sell unmodified photos
- ❌ Cannot create competing photo service

---

## Examples

### Find Campaign Event Photos

```python
# Search with multiple filters
photos = pexels_search_photos(
    query="political rally crowd",
    orientation="landscape",
    size="large",
    per_page=30
)

# Browse results
for photo in photos['photos']:
    print(f"ID: {photo['id']}")
    print(f"By: {photo['photographer']}")
    print(f"Size: {photo['width']}x{photo['height']}")
    print(f"URL: {photo['url']}")
    print()

# Download selected photo
pexels_download_photo(
    photo_id=selected_id,
    output_path="/home/dave/campaign_photos/rally.jpg",
    size="original"
)
```

### Batch Download for Policy Pages

```python
import json

# Define policy topics
policies = {
    "education": "classroom students learning",
    "healthcare": "doctor hospital medical",
    "economy": "business growth success",
    "environment": "nature green sustainability"
}

# Search and download for each
for policy, query in policies.items():
    # Search
    result = pexels_search_photos(query=query, per_page=5)
    photos = json.loads(result)['photos']

    # Download first result
    if photos:
        photo_id = photos[0]['id']
        pexels_download_photo(
            photo_id=photo_id,
            output_path=f"/home/dave/rundaverun/media/{policy}_header.jpg",
            size="large"
        )
```

### Get Curated Photos for Inspiration

```python
# Get trending photos
curated = pexels_curated_photos(per_page=20)

# Browse for inspiration
for photo in curated['photos']:
    print(f"Trending: {photo['photographer']}")
    print(f"View at: {photo['url']}")
```

---

## Integration with WordPress

After downloading photos, upload to WordPress:

```python
# 1. Download from Pexels
pexels_download_photo(
    photo_id=1464210,
    output_path="/tmp/campaign_hero.jpg",
    size="original"
)

# 2. Upload to WordPress media library
# (Use WordPress media upload tools)

# 3. Use in campaign pages
```

---

## Troubleshooting

### "API key not set" Error

Check `.env` file:
```bash
cat /home/dave/skippy/mcp-servers/general-server/.env | grep PEXELS
```

Should show:
```
PEXELS_API_KEY=2jPwvYEkwxNnWbqP4C0ixa0qq1A5R2EFh1wD2sJAvbZexzCSz0zAZamM
```

### No Results Found

Try:
- Simpler search terms
- Remove filters
- Check spelling
- Try synonyms

### Download Fails

Check:
- Output path is writable
- Sufficient disk space
- Internet connection

---

## Quick Reference

```python
# Search
pexels_search_photos("campaign", 20)

# Get photo details
pexels_get_photo(1464210)

# Download
pexels_download_photo(1464210, "/path/to/photo.jpg", "large")

# Curated
pexels_curated_photos(15)
```

---

## Resources

- **Pexels Website:** https://www.pexels.com
- **API Docs:** https://www.pexels.com/api/documentation/
- **License:** https://www.pexels.com/license/
- **Support:** https://help.pexels.com

---

## Summary

**Status:** ✅ Fully operational
**Tools:** 4 available
**API Key:** Configured
**Requests:** Unlimited
**Cost:** Free forever

Perfect for finding high-quality stock photos for your campaign website!

---

**Last Updated:** November 12, 2025
**Version:** 2.3.2
