# MCP Server Campaign-Relevant Tools Audit

**Date:** 2025-11-19
**MCP Server Version:** 2.3.2
**Total Tools Available:** 52 tools
**Campaign-Critical Tools:** 28 tools (54%)

---

## Executive Summary

The general-purpose MCP server provides 52 tools across 6 categories. Of these, **28 tools (54%)** are directly relevant to campaign operations, particularly for:

1. **Content Management** - Google Drive uploads, WordPress management
2. **Visual Content** - Pexels stock photography for website/social media
3. **Infrastructure** - Server monitoring, backups, remote management
4. **Development** - Git operations, WordPress database operations
5. **Documentation** - File operations for protocols and session notes

---

## Campaign-Critical Tools by Priority

### 🔴 **HIGH PRIORITY (Daily Use)**

#### Google Drive Management (13 tools)
**Use Cases:** Campaign document management, file sharing, team collaboration

**Organization Tools:**
- `gdrive_create_folder` - Organize campaign materials by category
- `gdrive_move_file` - Reorganize as campaign evolves
- `gdrive_list_folder_contents` - Browse campaign files
- `gdrive_rename_file` - Update file naming conventions
- `gdrive_batch_move_files` - Bulk reorganization
- `gdrive_organize_by_pattern` - Auto-organize by file type/pattern

**Upload & Sharing Tools:**
- `gdrive_upload_file` - Upload policy docs, reports, presentations
- `gdrive_batch_upload` - Batch upload photos from events
- `gdrive_share_file` - Share with volunteers, donors, press
- `gdrive_get_file_metadata` - Verify upload details
- `gdrive_copy_file` - Duplicate templates

**Search & Navigation:**
- `gdrive_get_folder_id_by_name` - Find specific folders
- `gdrive_trash_file` - Archive outdated materials

**Campaign Workflows:**
1. **Event Photos:** Batch upload event photos → Organize into dated folders → Share with press
2. **Policy Documents:** Upload new policy → Move to "Published Policies" → Share publicly
3. **Donor Reports:** Upload report → Share with specific donors → Track metadata
4. **Team Collaboration:** Create shared folders → Upload materials → Set permissions

---

#### Pexels Stock Photos (4 tools)
**Use Cases:** Website imagery, social media posts, campaign materials

**Available Tools:**
- `pexels_search_photos` - Search 3M+ free images
- `pexels_download_photo` - Download high-quality images
- `pexels_curated_photos` - Browse curated collections
- `pexels_get_photo_details` - Get photo metadata

**Campaign Keywords to Use:**
- "Louisville neighborhood" - Local imagery
- "community meeting" - Event visuals
- "people voting" - Democracy themes
- "diverse community" - Inclusion messaging
- "public safety officers" - Safety platform
- "Kentucky landmarks" - Local identity
- "town hall meeting" - Engagement visuals
- "volunteers helping" - Community service

**Advantages:**
- ✅ Free for commercial use (no attribution required)
- ✅ High-quality professional photography
- ✅ Instant downloads
- ✅ Perfect for social media dimensions
- ✅ 3M+ images available

**Typical Workflow:**
1. Search by campaign theme ("community meeting")
2. Review results, select best image
3. Download to campaign assets folder
4. Use for website, social media, or print materials

---

#### WordPress Management (5 tools)
**Use Cases:** Campaign website updates, content management, database operations

**Available Tools:**
- `wp_cli_command` - Run any WP-CLI command
- `wp_get_posts` - List posts/pages
- `wp_db_export` - Backup WordPress database
- `wp_search_replace` - Database search/replace (careful!)
- `wordpress_quick_backup` - Full site backup

**Campaign Use Cases:**
1. **Content Audits:** `wp_get_posts` to list all published policies
2. **Database Backups:** Before major updates, export database
3. **Full Backups:** Before design changes or plugin updates
4. **Bulk Updates:** Search/replace old campaign URLs (dry-run first!)
5. **Post Management:** Check post status, update metadata

**Safety Note:** Always use `dry_run=True` for `wp_search_replace` first!

---

### 🟡 **MEDIUM PRIORITY (Weekly Use)**

#### Remote Server Management - Ebon (3 tools)
**Use Cases:** WordPress hosting server health, uptime monitoring

**Available Tools:**
- `run_remote_command` - Execute commands on ebon
- `check_ebon_status` - Quick health check
- `ebon_full_status` - Comprehensive status

**Campaign Monitoring:**
- **Website Uptime:** Check if WordPress is running
- **Disk Space:** Ensure server has space for uploads
- **Service Status:** Verify nginx, MySQL, PHP-FPM running
- **Performance:** Check load average, memory usage

**Common Commands:**
- "Is the WordPress site up on ebon?"
- "Check disk space on ebon server"
- "Get full status of ebon including Docker"

---

#### File Operations (5 tools)
**Use Cases:** Session documentation, protocol management, file operations

**Available Tools:**
- `read_file` - Read files with line ranges
- `write_file` - Write/append content
- `list_directory` - List with glob patterns
- `search_files` - Text search within files
- `get_file_info` - File metadata

**Campaign Use Cases:**
1. **Session Notes:** Write session summaries to `/home/dave/skippy/documentation/conversations/`
2. **Protocol Updates:** Read, modify, update protocols
3. **File Search:** Find specific campaign documents
4. **Fact Checking:** Read `QUICK_FACTS_SHEET.md` for data verification

---

### 🟢 **LOW PRIORITY (Occasional Use)**

#### Git Operations (4 tools)
**Use Cases:** Version control for campaign materials

**Available Tools:**
- `git_status` - Check repo status
- `git_diff` - View changes
- `git_recent_commits` - View commit history
- `git_commit` - Create commits

**Campaign Use Cases:**
- Track changes to policy documents
- Version control for WordPress plugin development
- Commit session documentation
- Review recent changes to campaign materials

---

#### System Monitoring (5 tools)
**Use Cases:** Infrastructure health, resource management

**Available Tools:**
- `get_disk_usage` - Check disk space
- `get_memory_info` - RAM usage
- `get_cpu_info` - CPU usage
- `list_processes` - Running processes
- `check_service_status` - Service status

**When to Use:**
- Before major uploads (check disk space)
- When site feels slow (check resources)
- Troubleshooting server issues
- Routine health checks

---

#### Web Requests (2 tools)
**Use Cases:** API integration, external data fetching

**Available Tools:**
- `http_get` - GET requests
- `http_post` - POST requests

**Campaign Use Cases:**
- Check campaign website accessibility
- Test API endpoints
- Fetch data from external services
- Integration testing

---

## Campaign Workflow Examples

### Workflow 1: Event Photo Publishing
**Scenario:** Upload and publish photos from town hall meeting

**Steps:**
1. Use `pexels_search_photos` to find supplemental "town hall meeting" stock photos
2. Use `gdrive_create_folder` to create "2025-11-19_Town_Hall" folder
3. Use `gdrive_batch_upload` to upload event photos from local directory
4. Use `gdrive_organize_by_pattern` to sort by file type (JPG, PNG)
5. Use `gdrive_share_file` to create public link for press
6. Download 2-3 Pexels images for social media posts

**Tools Used:** 6 tools, ~5 minutes

---

### Workflow 2: Policy Document Publishing
**Scenario:** Create and publish new climate policy

**Steps:**
1. Use `read_file` to read policy template
2. Use `write_file` to create new policy document
3. Use `wp_cli_command` to create WordPress draft post
4. Use `gdrive_upload_file` to upload PDF version to "Published Policies"
5. Use `gdrive_share_file` to generate public link
6. Use `wp_db_export` to backup database before publishing

**Tools Used:** 6 tools, ~10 minutes

---

### Workflow 3: Weekly Infrastructure Health Check
**Scenario:** Monday morning server health check

**Steps:**
1. Use `check_ebon_status` to get quick server overview
2. Use `get_disk_usage` to check available space
3. Use `wp_cli_command "plugin list"` to verify plugins up to date
4. Use `wordpress_quick_backup` to create weekly backup
5. Use `gdrive_upload_file` to upload backup to Google Drive

**Tools Used:** 5 tools, ~15 minutes

---

### Workflow 4: Social Media Content Creation
**Scenario:** Create visual content for Facebook post

**Steps:**
1. Use `pexels_search_photos "diverse community Louisville"` to find images
2. Review results and select 2-3 images
3. Use `pexels_download_photo` for each selected image
4. Use `gdrive_upload_file` to upload to "Social Media Assets"
5. Use `gdrive_share_file` to get links for design team

**Tools Used:** 3-5 tools, ~5 minutes

---

## Quick Reference by Campaign Task

| Campaign Task | Recommended MCP Tools |
|---------------|----------------------|
| **Upload event photos** | `gdrive_batch_upload`, `gdrive_create_folder` |
| **Find stock imagery** | `pexels_search_photos`, `pexels_download_photo` |
| **Publish policy doc** | `gdrive_upload_file`, `gdrive_share_file` |
| **Backup WordPress** | `wordpress_quick_backup`, `wp_db_export` |
| **Check website health** | `check_ebon_status`, `wp_cli_command` |
| **Organize files** | `gdrive_organize_by_pattern`, `gdrive_batch_move_files` |
| **Share with team** | `gdrive_share_file`, `gdrive_get_folder_id_by_name` |
| **Create social media** | `pexels_search_photos`, `pexels_download_photo` |

---

## Integration with Existing Skills

**MCP tools complement these existing skills:**

1. **wordpress-deployment** → Use MCP `wp_cli_command` for deployment
2. **content-approval** → Use MCP `gdrive_share_file` for review links
3. **google-drive-sync** → Use MCP tools for manual Drive operations
4. **social-media-management** → Use MCP Pexels tools for imagery
5. **backup-infrastructure** → Use MCP `wordpress_quick_backup`

---

## Recommendations

### Immediate Action Items

1. **Start Using Google Drive Tools**
   - Set up folder structure for campaign materials
   - Practice batch upload workflow
   - Create sharing templates for different audiences

2. **Integrate Pexels Into Content Workflow**
   - Create saved search keywords for campaign themes
   - Build visual asset library in Google Drive
   - Use for weekly social media content creation

3. **Schedule Weekly Server Checks**
   - Use `/ebon-status` every Monday morning
   - Run `wordpress_quick_backup` weekly
   - Upload backups to Google Drive automatically

4. **Create MCP-Based Slash Commands** (Already done ✅)
   - `/gdrive-upload` for quick uploads
   - `/stock-photo` for image searches
   - `/mcp-status` for server health
   - `/ebon-status` for ebon checks

### Long-term Opportunities

1. **Automate Common Workflows**
   - Create scripts that use MCP tools for repetitive tasks
   - Build templates for event photo processing
   - Automate weekly backup + upload to Drive

2. **Expand MCP Server**
   - Add social media API tools (Facebook, Twitter)
   - Add email tools (campaign newsletters)
   - Add FEC reporting tools (if available)

3. **Team Training**
   - Document MCP workflows for volunteers
   - Create video tutorials for common tasks
   - Build MCP command cheat sheet

---

## Tool Usage Tracking (Recommended)

**High-value metrics to track:**
- Google Drive uploads per week
- Pexels images downloaded per month
- WordPress backups created
- Server health checks performed
- Time saved vs manual operations

**Estimated Time Savings:**
- Google Drive batch operations: 50% time savings
- Stock photo sourcing: 75% time savings vs manual search
- WordPress backups: 80% time savings vs manual FTP
- Server monitoring: 60% time savings vs SSH login

**Monthly time savings estimate:** 10-15 hours

---

## Security & Best Practices

### Google Drive
- ✅ OAuth authentication (already configured)
- ✅ Review sharing permissions regularly
- ✅ Use specific permissions (reader/commenter/editor)
- ⚠️ Avoid public sharing of sensitive campaign data

### WordPress
- ✅ Always backup before database operations
- ✅ Use dry-run mode for search/replace
- ✅ Test WP-CLI commands on staging first
- ⚠️ Verify backups actually work (test restore)

### Pexels
- ✅ Free for commercial use (already compliant)
- ✅ Optional attribution (recommended for goodwill)
- ✅ Track image sources for licensing records

### Server Access
- ✅ SSH credentials secured in MCP config
- ✅ Commands run with user permissions (not root)
- ⚠️ Audit server access logs regularly

---

## Conclusion

The MCP server provides **28 campaign-critical tools** that directly support:
- ✅ Content management (Google Drive)
- ✅ Visual content creation (Pexels)
- ✅ Website operations (WordPress)
- ✅ Infrastructure monitoring (ebon)
- ✅ Development workflows (Git, files)

**Key Advantages:**
1. **Time Savings:** 10-15 hours/month estimated
2. **Cost Savings:** Free stock photos (normally $100-300/month)
3. **Efficiency:** Automated workflows replace manual operations
4. **Quality:** Professional tools for campaign operations

**Next Steps:**
1. Start using Google Drive tools for document management
2. Integrate Pexels into social media workflow
3. Schedule weekly server health checks
4. Track usage and time savings for reporting

---

**Status:** ✅ MCP server fully integrated and operational
**Last Updated:** 2025-11-19
**Next Review:** 2025-12-19 (monthly)
