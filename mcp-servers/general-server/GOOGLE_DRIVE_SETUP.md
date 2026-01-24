# Google Drive API Setup Guide
**For MCP General Server v2.1.0**
**Updated:** November 10, 2025

---

## Quick Links

- **Google Cloud Console:** https://console.cloud.google.com/
- **Enable API:** https://console.cloud.google.com/apis/library/drive.googleapis.com
- **Credentials:** https://console.cloud.google.com/apis/credentials
- **Official Docs:** https://developers.google.com/drive/api/quickstart/python

---

## Step 1: Create/Select Project (2 minutes)

1. Go to: https://console.cloud.google.com/
2. Click project dropdown (top left)
3. Click "New Project"
   - Name: "MCP General Server" (or any name)
   - Click "Create"
4. Wait for project creation (~10 seconds)

---

## Step 2: Enable Google Drive API (1 minute)

1. Go to: https://console.cloud.google.com/apis/library/drive.googleapis.com
2. Make sure your project is selected (top bar)
3. Click "Enable" button
4. Wait for confirmation

---

## Step 3: Configure OAuth Consent Screen (2 minutes)

1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Select "External" user type
3. Click "Create"
4. Fill in required fields:
   - **App name:** MCP General Server
   - **User support email:** your-email@gmail.com
   - **Developer contact:** your-email@gmail.com
5. Click "Save and Continue"
6. On "Scopes" page:
   - Click "Add or Remove Scopes"
   - Search for "drive.readonly"
   - Select: `.../auth/drive.readonly`
   - Click "Update"
   - Click "Save and Continue"
7. On "Test users" page:
   - Click "Add Users"
   - Add your email address
   - Click "Save and Continue"
8. Click "Back to Dashboard"

---

## Step 4: Create OAuth Credentials (2 minutes)

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure consent screen (follow Step 3)
4. Select application type:
   - **Application type:** Desktop app
   - **Name:** MCP General Server Desktop
5. Click "Create"
6. A dialog appears with Client ID and Secret
7. Click "Download JSON"
8. Save the file

---

## Step 5: Install Credentials (1 minute)

1. **Rename downloaded file:**
   ```bash
   mv ~/Downloads/client_secret_*.json ~/Downloads/credentials.json
   ```

2. **Create credentials directory:**
   ```bash
   mkdir -p ~/.config/skippy/credentials
   chmod 700 ~/.config/skippy/credentials
   ```

3. **Move credentials file:**
   ```bash
   mv ~/Downloads/credentials.json ~/.config/skippy/credentials/
   chmod 600 ~/.config/skippy/credentials/credentials.json
   ```

4. **Verify:**
   ```bash
   ls -la ~/.config/skippy/credentials/credentials.json
   ```
   Should show: `-rw------- 1 dave dave`

---

## Step 6: First Run - OAuth Authorization (2 minutes)

When you first use Google Drive tools, a browser will open:

1. **The server will open a browser automatically**
2. **Select your Google account**
3. **Click "Continue" on the security warning**
   - (App is unverified - this is normal for personal projects)
4. **Click "Allow" to grant access**
5. **Browser will show "The authentication flow has completed"**
6. **Close the browser**

The token will be saved at:
```
~/.config/skippy/credentials/google_drive_token.json
```

You won't need to authorize again unless you delete the token file.

---

## Verification

Test your setup:

```python
# In MCP server or Python:
from server import gdrive_search_files

# Search your Drive
result = gdrive_search_files("name contains 'test'", 5)
print(result)
```

Expected output:
```json
{
  "success": true,
  "count": X,
  "files": [...]
}
```

---

## Troubleshooting

### Error: "credentials.json not found"
**Solution:**
```bash
# Check file exists:
ls ~/.config/skippy/credentials/credentials.json

# If not, re-download from:
https://console.cloud.google.com/apis/credentials
```

### Error: "The OAuth client was not found"
**Solution:**
- Make sure you selected "Desktop app" not "Web application"
- Re-create the OAuth client ID

### Error: "Access denied" or "invalid_grant"
**Solution:**
```bash
# Delete token and re-authorize:
rm ~/.config/skippy/credentials/google_drive_token.json
# Run tool again - browser will open for new authorization
```

### Error: "API has not been enabled"
**Solution:**
- Go to: https://console.cloud.google.com/apis/library/drive.googleapis.com
- Make sure correct project is selected
- Click "Enable"

### Browser doesn't open during authorization
**Solution:**
```bash
# Manual authorization:
# 1. Note the URL printed in console
# 2. Open it manually in browser
# 3. Complete authorization
# 4. Copy the code from browser
# 5. Paste into console
```

---

## Security Notes

### What Access is Granted?
- **Read-only access** to your Google Drive
- Cannot modify, delete, or create files
- Can list files and download them

### Revoking Access
To revoke access later:
1. Go to: https://myaccount.google.com/permissions
2. Find "MCP General Server"
3. Click "Remove Access"

### Sharing Credentials
**Never share:**
- `credentials.json` - Contains client secret
- `google_drive_token.json` - Contains access token

Both files are in `.gitignore` and won't be committed to git.

---

## Environment Variables

Already configured in `.env`:
```bash
GOOGLE_DRIVE_CREDENTIALS_PATH=~/.config/skippy/credentials/credentials.json
GOOGLE_DRIVE_TOKEN_PATH=~/.config/skippy/credentials/google_drive_token.json
GOOGLE_DRIVE_SCOPES=https://www.googleapis.com/auth/drive.readonly
```

To change scopes (for read-write access):
```bash
# Edit .env:
GOOGLE_DRIVE_SCOPES=https://www.googleapis.com/auth/drive
```

Then delete token and re-authorize.

---

## Available Scopes

| Scope | Access Level |
|-------|-------------|
| `drive.readonly` | Read-only (recommended) |
| `drive` | Full read/write access |
| `drive.file` | Only files created by app |
| `drive.metadata.readonly` | Metadata only |

**Current:** `drive.readonly` (safe default)

---

## Usage Examples

### Search for files
```python
gdrive_search_files("name contains 'policy'", 10)
gdrive_search_files("mimeType='application/pdf'", 20)
gdrive_search_files("modifiedTime > '2025-01-01'", 5)
```

### Download a file
```python
gdrive_download_file("1ABC...XYZ", "/tmp/downloaded_file.pdf")
```

### Read a Google Doc
```python
content = gdrive_read_document("1ABC...XYZ")
print(content)
```

---

## Cost

**Free Tier:**
- Google Drive API is completely free
- No credit card required
- Rate limits: 20,000 queries per 100 seconds per user

**Limits:**
- 1,000 queries per 100 seconds per project
- 12,000 queries per minute per user

These limits are very generous for personal use.

---

## Quick Setup Checklist

- [ ] Create Google Cloud project
- [ ] Enable Google Drive API
- [ ] Configure OAuth consent screen
- [ ] Create OAuth client ID (Desktop app)
- [ ] Download credentials.json
- [ ] Move to `~/.config/skippy/credentials/`
- [ ] First run - complete OAuth authorization
- [ ] Verify token saved in `.credentials/`
- [ ] Test with `gdrive_search_files()`

**Total Time:** ~10 minutes

---

## Support

**Official Documentation:**
- https://developers.google.com/drive/api/quickstart/python
- https://developers.google.com/drive/api/guides/search-files

**Common Issues:**
- https://stackoverflow.com/questions/tagged/google-drive-api

**Google Cloud Support:**
- https://console.cloud.google.com/support

---

**Last Updated:** November 10, 2025
**MCP Server Version:** 2.1.0
