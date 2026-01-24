# Changelog - General Purpose MCP Server

## [2.3.2] - 2025-11-12

### 🚀 Stock Photos & Google Photos Integration - 10 New Tools!

**Total Tools**: 75 (increased from 65)

### Added - Two New Integrations

#### Pexels Stock Photos Integration (4 tools) ✅ FULLY OPERATIONAL
- `pexels_search_photos` - Search 3M+ free stock photos
- `pexels_get_photo` - Get specific photo details
- `pexels_download_photo` - Download photos locally
- `pexels_curated_photos` - Browse curated collections

**Status**: ✅ Fully tested and operational
**API Key**: Configured and working (200 requests/hour free tier)
**Use Case**: Campaign website stock photography, social media, newsletters

#### Google Photos Integration (6 tools) ⚠️ PENDING OAUTH FIX
- `gphotos_list_albums` - List photo albums
- `gphotos_search_media` - Search photos by date/location
- `gphotos_get_album_contents` - Browse album contents
- `gphotos_download_media` - Download photos/videos
- `gphotos_get_media_metadata` - Get EXIF data
- `_get_google_photos_service` - OAuth helper

**Status**: ⚠️ Code complete, OAuth 403 error (scope propagation issue)
**Known Issue**: Google OAuth consent screen needs time to propagate
**Documentation**: Complete setup guide available

### Documentation Added
- `CHANGELOG_v2.3.2.md` - Complete version documentation
- `PEXELS_SETUP.md` - Pexels integration guide
- `GOOGLE_PHOTOS_SETUP.md` - Google Photos setup (313 lines)
- `GOOGLE_PHOTOS_QUICKSTART.md` - Quick reference
- `GOOGLE_APIS_README.md` - Consolidated Google integrations

### Configuration
```bash
# .env additions
PEXELS_API_KEY=<configured>
GOOGLE_PHOTOS_CREDENTIALS_PATH=~/.config/skippy/credentials/google_drive_credentials.json
GOOGLE_PHOTOS_TOKEN_PATH=~/.config/skippy/credentials/google_photos_token.json
```

---

## [2.1.0] - 2025-11-10

### 🚀 Major Integration Update - 9 New Tools Added!

**Total Tools**: 52 (increased from 43)

### Added - Four Major Integrations

#### GitHub Integration (3 tools) - HIGH PRIORITY
- `github_create_pr` - Create pull requests automatically
- `github_create_issue` - Create issues with labels and assignees
- `github_list_prs` - List and filter pull requests

**Setup Required**: GitHub Personal Access Token (scopes: repo, workflow, read:org)

**Use Cases**:
- Automated PR creation after repository updates
- Issue tracking for bugs and features
- CI/CD workflow monitoring
- Repository insights and statistics

#### Slack Integration (2 tools) - HIGH PRIORITY
- `slack_send_message` - Send messages to channels with threading
- `slack_upload_file` - Upload files with comments

**Setup Required**: Slack Bot Token (scopes: chat:write, files:write, channels:read)

**Use Cases**:
- Deployment notifications
- Error alerts from NexusController
- Campaign update announcements
- Team collaboration

#### Browser Automation (2 tools) - MEDIUM PRIORITY
- `browser_screenshot` - Capture webpage screenshots (full page or viewport)
- `browser_test_form` - Automated form submission testing

**Setup Required**: None (uses Pyppeteer)

**Use Cases**:
- Visual regression testing for rundaverun.org
- Form submission testing (contact, volunteer, email signup)
- Mobile responsiveness checking
- Documentation screenshots

#### Google Drive Integration (3 tools) - MEDIUM PRIORITY
- `gdrive_search_files` - Search files with Drive query syntax
- `gdrive_download_file` - Download files by ID
- `gdrive_read_document` - Read Google Docs as text

**Setup Required**: OAuth 2.0 credentials from Google Cloud Console

**Use Cases**:
- Campaign document access
- Policy document retrieval
- Backup verification
- Document version tracking

### Dependencies Added
```python
PyGithub==2.8.1              # GitHub API
slack-sdk==3.37.0            # Slack API
pyppeteer==2.0.0             # Browser automation
google-api-python-client==2.187.0  # Google Drive
google-auth-httplib2==0.2.1
google-auth-oauthlib==1.2.3
```

### Changed
- Version bumped from 2.0.0 to 2.1.0
- Tool count increased from 43 to 52
- Enhanced requirements.txt with 6 new dependencies
- Updated .env template with integration variables
- Improved import handling (graceful degradation if packages missing)

### Technical Details
- **Code**: 1,850+ lines (up from 1,328 lines)
- **New Dependencies**: 6 packages installed
- **Async Support**: Added for browser automation
- **OAuth Support**: Automatic token refresh for Google Drive
- **Error Handling**: Enhanced for external API failures
- **Security**: All tokens stored in .env file

### Configuration Required

Add to `.env` file:
```bash
# GitHub
GITHUB_TOKEN=your_github_personal_access_token

# Slack
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Google Drive
GOOGLE_DRIVE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_DRIVE_TOKEN_PATH=/path/to/token.json
```

### Upgrade Instructions

From v2.0.0 to v2.1.0:

1. **Install Dependencies**:
```bash
cd /home/dave/skippy/mcp-servers/general-server
source .venv/bin/activate
pip install PyGithub slack-sdk pyppeteer google-api-python-client google-auth-oauthlib
```

2. **Update Configuration**:
```bash
# Add new variables to .env file
nano .env
```

3. **Setup Integrations** (optional - only for features you need):
- GitHub: Create token at https://github.com/settings/tokens
- Slack: Create bot at https://api.slack.com/apps
- Google: Create credentials at https://console.cloud.google.com/

4. **Restart Server** (if running):
```bash
# Restart Claude for Desktop or restart MCP server
```

### Breaking Changes
**None** - All v2.0.0 tools remain unchanged and fully compatible.

### Feature Comparison Matrix

| Feature | v2.0.0 | v2.1.0 | New |
|---------|--------|--------|-----|
| File Operations | ✅ | ✅ | |
| System Monitoring | ✅ | ✅ | |
| WordPress | ✅ | ✅ | |
| Git | ✅ | ✅ | |
| GitHub | ❌ | ✅ | ⭐ |
| Slack | ❌ | ✅ | ⭐ |
| Browser Automation | ❌ | ✅ | ⭐ |
| Google Drive | ❌ | ✅ | ⭐ |
| Docker | ✅ | ✅ | |
| Database | ✅ | ✅ | |

---

## [2.0.0] - 2025-10-31 (Evening)

### 🚀 Major Update - 27 New Tools Added!

**Total Tools**: 43 (increased from 16)

### Added

#### WordPress Management (5 tools) - HIGH PRIORITY
- `wp_cli_command` - Run WP-CLI commands on local WordPress
- `wp_db_export` - Export WordPress database with timestamp
- `wp_search_replace` - Safe search-replace in database
- `wp_get_posts` - List WordPress posts/pages
- `wordpress_quick_backup` - Complete backup (files + database)

**Rationale**: WordPress is 40% of user's work, essential tools for daily operations.

#### Git Operations (4 tools) - HIGH PRIORITY
- `git_status` - Get repository status
- `git_diff` - Show staged/unstaged changes
- `run_credential_scan` - Run pre-commit security scan
- `git_log` - View recent commit history

**Rationale**: Security (Pre-Commit Sanitization Protocol) and Git Workflow Protocol compliance.

#### Skippy Script Management (3 tools) - HIGH PRIORITY
- `search_skippy_scripts` - Search 226+ existing scripts by keyword
- `list_script_categories` - List all script categories
- `get_script_info` - Get script details and documentation

**Rationale**: Script Creation Protocol requires checking existing scripts before creating new ones.

#### Protocol & Conversation Access (3 tools)
- `search_protocols` - Search 18 protocols + 4 quick references
- `get_protocol` - Read specific protocol file
- `search_conversations` - Search 70+ session transcripts

**Rationale**: Quick access to established procedures and past solutions.

#### Docker Container Management (3 tools)
- `docker_ps_remote` - List containers on ebon server
- `docker_logs_remote` - Get container logs
- `jellyfin_status` - Check Jellyfin health

**Rationale**: Ebon server runs Jellyfin and other Docker containers that need monitoring.

#### Log File Analysis (3 tools)
- `tail_log` - Get last N lines of any log file
- `search_log` - Search logs with context
- `check_claude_logs` - Check Claude for Desktop MCP logs

**Rationale**: Troubleshooting and debugging support.

#### Database Tools (1 tool)
- `mysql_query_safe` - Execute safe SELECT-only queries

**Rationale**: WordPress database inspection without modification risk.

#### Enhanced Monitoring (1 tool)
- `ebon_full_status` - Comprehensive ebon status (system + Docker + Jellyfin)

**Rationale**: Better than basic check_ebon_status, shows complete picture.

#### Duplicate Management (1 tool)
- `find_duplicates` - Find duplicate files using existing script

**Rationale**: Integration with user's existing duplicate finder tool.

### Changed
- Updated server version from 1.0.0 to 2.0.0
- Added path constants for WordPress, Skippy, conversations, scripts
- Improved error messages with context
- Better datetime formatting in file info outputs

### Technical Details
- Code: 1,312 lines (up from 488 lines)
- Dependencies: No new dependencies required (all use existing libraries)
- Performance: All tools have timeouts for safety
- Security: Database tool blocks destructive queries, credential scan integrated

---

## [1.0.0] - 2025-10-31 (Initial Release)

### Added

#### File Operations (5 tools)
- `read_file` - Read file contents with line range
- `write_file` - Write/append to files
- `list_directory` - List directory contents with glob
- `search_files` - Search text within files
- `get_file_info` - Get file/directory metadata

#### System Monitoring (5 tools)
- `get_disk_usage` - Check disk space
- `get_memory_info` - RAM and swap stats
- `get_cpu_info` - CPU usage per core
- `list_processes` - Running processes
- `check_service_status` - Systemd service status

#### Remote Server Management (2 tools)
- `run_remote_command` - Execute commands on ebon via SSH
- `check_ebon_status` - Quick ebon health check

#### Web Requests (2 tools)
- `http_get` - HTTP GET with custom headers
- `http_post` - HTTP POST with JSON data

#### Utilities (2 tools)
- `run_shell_command` - Execute local shell commands
- `get_file_info` - Detailed file information

### Infrastructure
- FastMCP server setup with STDIO transport
- Virtual environment with dependencies
- Comprehensive README and setup automation
- Claude for Desktop integration configured

---

## Upgrade Notes

### From v1.0.0 to v2.0.0

**No breaking changes** - All existing tools work the same way.

**What to do:**
1. The server file has been updated automatically
2. Restart Claude for Desktop to load new tools
3. You'll now see 43 tools instead of 16
4. All new tools are immediately available

**New Features You'll Notice:**
- WordPress commands available through natural language
- Script search before creating new scripts (follows protocol)
- Access to protocols and past conversations
- Git operations with credential scanning
- Docker container management on ebon
- Database query capability (read-only for safety)

**Configuration:**
- No config changes needed
- Same claude_desktop_config.json works
- Same virtual environment works
- No new dependencies to install

---

## Statistics

### v2.0.0
- **Total Tools**: 43
- **Lines of Code**: 1,312
- **Tool Categories**: 13
- **Development Time**: ~2 hours total
- **Priority Tools Added**: 12 (WordPress, Git, Skippy)

### v1.0.0
- **Total Tools**: 16
- **Lines of Code**: 488
- **Tool Categories**: 6
- **Development Time**: ~45 minutes

---

## Future Roadmap

### Planned Enhancements
- Configuration file support (externalize paths)
- Tool response caching for frequently accessed data
- Batch operations for common workflows
- More WordPress automation (theme management, user management)
- Advanced git operations (branch management, stashing)
- Real-time log tailing for monitoring

### Under Consideration
- FTP/SFTP file transfer tools
- Email sending capability
- Cron job management
- System package management
- Network diagnostics
- SSL certificate checking

---

## Credits

**Author**: Claude Code
**Created for**: Dave's Skippy System & RunDaveRun Campaign
**Based on**: User's established protocols and workflows
**License**: Personal use

---

**Last Updated**: 2025-10-31
**Current Version**: 2.0.0
**Status**: ✅ Ready for production use
