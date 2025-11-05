# File Download Management Protocol

**Date Created**: 2025-10-28
**Purpose**: Automatic detection and processing of downloaded files
**Applies To**: All files downloaded to `/home/dave/skippy/claude/downloads/`
**Priority**: MEDIUM (convenience and efficiency)

## Overview

This protocol establishes automated workflows for handling files downloaded to the Claude downloads folder. When Claude Code is running and a new file appears in the downloads folder, Claude should automatically detect, read, and process it according to file type.

---

## Downloads Directory

**Primary Location**: `/home/dave/skippy/claude/downloads/`

**Purpose**: Staging area for files downloaded from web browsers, email, or other sources that need Claude's analysis or processing.

---

## Automatic Detection

### When User Mentions Downloads

When the user says phrases like:
- "I just downloaded a file"
- "Check the downloads folder"
- "I have a new file"
- "Look at what I downloaded"

**Claude should automatically**:
1. Check `/home/dave/skippy/claude/downloads/` for most recent file
2. Identify the newest file by modification time
3. Read and analyze the file
4. Provide appropriate response based on file type

### Proactive Checking

If user says "watch downloads" or "monitor downloads":
- Periodically check for new files (every 30-60 seconds)
- Alert when new file detected
- Automatically process new files

---

## File Type Handling

### Text Files (.txt, .md, .log)

**Action**:
1. Read the file contents
2. Provide summary of what's in the file
3. Ask what user wants to do with it
   - Move to organized location?
   - Extract information?
   - Process/transform?

**Example**:
```
Found: protocol_notes.txt (5KB, just now)
Contents: Notes about WordPress deployment procedures

Suggested actions:
- Add to existing protocol?
- Create new protocol?
- File in conversations/?
```

---

### ZIP/Archive Files (.zip, .tar.gz, .7z)

**Action**:
1. List archive contents
2. Show file count and total size
3. Ask if user wants to extract
4. Suggest extraction location based on content

**Example**:
```
Found: project_files.zip (2.5MB, just now)
Contents: 15 files
- 8 PHP files
- 4 CSS files
- 3 JS files

Extract to:
- /home/dave/rundaverun/campaign/ (WordPress files detected)
- /home/dave/skippy/claude/downloads/extracted/ (general)
- Other location?
```

---

### Images (.png, .jpg, .jpeg, .gif, .webp)

**Action**:
1. Read and display the image
2. Describe what's in the image
3. Suggest actions based on content
   - Screenshot → extract text/analyze
   - Diagram → explain and document
   - Photo → organize/rename

**Example**:
```
Found: Screenshot from 2025-10-28 03-15-42.png (125KB, just now)

Image shows: Terminal window with error message about WordPress database connection

Suggested actions:
- Log this error?
- Troubleshoot the issue?
- Add to common errors guide?
```

---

### PDF Files (.pdf)

**Action**:
1. Read the PDF
2. Summarize contents
3. Extract key information
4. Suggest organization location

**Example**:
```
Found: invoice_october_2025.pdf (85KB, just now)

Document type: Invoice
Key info:
- Date: October 2025
- Amount: $247.50
- Vendor: DigitalOcean

Suggested actions:
- File in /home/dave/Documents/Financial/Invoices/?
- Extract data to spreadsheet?
- Just review and delete?
```

---

### Code Files (.js, .py, .php, .sh, .css, etc.)

**Action**:
1. Read the code
2. Analyze what it does
3. Check for security issues
4. Suggest where to save it

**Example**:
```
Found: wordpress_backup_script.sh (3KB, just now)

Script type: Bash shell script
Purpose: WordPress database backup automation
Functions: Database export, compression, upload to S3

Security check: ✅ No hardcoded credentials
Quality: Good - uses best practices

Suggested actions:
- Save to /home/dave/skippy/scripts/wordpress/?
- Review and test before using?
- Add to WordPress maintenance protocol?
```

---

### JSON/CSV/Data Files (.json, .csv, .xml)

**Action**:
1. Parse the file
2. Show structure and sample data
3. Suggest processing options

**Example**:
```
Found: voter_data_export.csv (450KB, just now)

Format: CSV with 1,245 rows
Columns: name, address, district, status, notes

Suggested actions:
- Import to database?
- Analyze/summarize data?
- Convert to different format?
- Clean and organize?
```

---

### Unknown/Binary Files

**Action**:
1. Show file info (name, size, type)
2. Use `file` command to identify
3. Ask user what it is
4. Suggest next steps

**Example**:
```
Found: data_export.bin (12MB, just now)

File type: Unknown binary data
MIME type: application/octet-stream

What is this file?
- Database dump?
- Compressed archive?
- Backup file?
```

---

## Workflow After Detection

### Step 1: Identify File
```bash
ls -lt /home/dave/skippy/claude/downloads/ | head -5
```

### Step 2: Read/Analyze
Based on file type, use appropriate tool:
- Read tool for text/code
- Read tool for images/PDFs (visual analysis)
- Bash with unzip -l for archives
- File command for unknown types

### Step 3: Present Options

Always provide 3-4 actionable options:
1. **Organize**: Where to move/rename the file
2. **Process**: What to do with the contents
3. **Keep**: Leave in downloads for now
4. **Delete**: If not needed

### Step 4: Execute User Choice

After user decides, execute the action:
- Move files with proper naming
- Extract archives to appropriate locations
- Process data as requested
- Clean up downloads folder

---

## Naming Convention for Downloaded Files

### When Moving from Downloads

Apply standard naming convention:
- **Before**: `Screenshot from 2025-10-28 03-15-42.png`
- **After**: `screenshot_2025-10-28_031542_wordpress_error.png`

**Rules**:
- Lowercase with underscores
- Keep date if useful (YYYY-MM-DD format)
- Add descriptive suffix
- Remove spaces and special characters

---

## Organization Locations

### Common Destinations

**Scripts**:
→ `/home/dave/skippy/scripts/[category]/`

**Documentation**:
→ `/home/dave/skippy/conversations/`

**WordPress Files**:
→ `/home/dave/rundaverun/campaign/`

**Screenshots**:
→ `/home/dave/Pictures/Screenshots/` (if important)
→ Delete if temporary

**Data Files**:
→ `/home/dave/skippy/data/` or relevant project folder

**Temporary/Review**:
→ Keep in downloads temporarily
→ Delete after processing

---

## Cleanup Policy

### When to Delete from Downloads

**Immediately after**:
- ✅ File moved to permanent location
- ✅ Contents extracted and archived
- ✅ Information captured elsewhere

**Keep temporarily if**:
- ⚠️ Need to review further
- ⚠️ Waiting for user decision
- ⚠️ Part of multi-file download

**Delete weekly**:
- 🗑️ Files older than 7 days
- 🗑️ Duplicate downloads
- 🗑️ Temporary test files

---

## User Interaction Patterns

### Pattern 1: Silent Download
User downloads file without mentioning it.

**Claude should**:
- NOT automatically detect (no interruption)
- Wait for user to mention it
- Respond when user says "check downloads"

### Pattern 2: Announced Download
User says "I just downloaded X"

**Claude should**:
- Immediately check downloads folder
- Find newest file
- Read and analyze
- Present options

### Pattern 3: Monitoring Request
User says "watch for downloads"

**Claude should**:
- Acknowledge monitoring
- Check every 30-60 seconds
- Alert on new files
- Auto-process per this protocol

### Pattern 4: Batch Downloads
User downloads multiple files

**Claude should**:
- List all recent files (last 5-10 minutes)
- Offer to process each
- Ask if batch operation preferred
- Process efficiently

---

## Examples

### Example 1: Protocol Document

**User**: "I just downloaded a protocol document"

**Claude**:
```bash
ls -lt /home/dave/skippy/claude/downloads/ | head -3
```

**Output**:
```
-rw-rw-r-- 1 dave dave 15234 Oct 28 03:20 deployment_checklist_v2.md
```

**Claude Response**:
```
Found: deployment_checklist_v2.md (15KB, just downloaded)

Reading contents... This appears to be an updated deployment checklist
protocol with enhanced pre-deployment checks and GoDaddy-specific steps.

Suggested actions:
1. Update existing protocol: /home/dave/skippy/conversations/deployment_checklist_protocol.md
2. Save as new version: deployment_checklist_v2.0.md
3. Review differences first

Which would you like?
```

---

### Example 2: Screenshot

**User**: "Check downloads"

**Claude**:
```bash
ls -lt /home/dave/skippy/claude/downloads/ | head -3
```

**Output**:
```
-rw-rw-r-- 1 dave dave 234567 Oct 28 03:25 error_screenshot.png
```

**Claude**:
```
Found: error_screenshot.png (235KB, 2 minutes ago)

[Displays image]

Image shows: WordPress admin panel with "Error establishing database
connection" message. Database credentials visible in wp-config.php.

This is a critical error. Suggested actions:
1. Log this error: Add to error_logging_protocol.md
2. Troubleshoot: Check database credentials and connection
3. Document solution: Update common_errors_solutions_guide.md
4. Delete screenshot: Contains sensitive credential information

Recommend: Log error, troubleshoot issue, then delete screenshot.
Proceed?
```

---

### Example 3: Code File

**User**: "I downloaded a backup script"

**Claude**:
```bash
ls -lt /home/dave/skippy/claude/downloads/ | head -3
```

**Output**:
```
-rw-rw-r-- 1 dave dave 5432 Oct 28 03:30 wp_backup.sh
```

**Claude**:
```
Found: wp_backup.sh (5KB, just now)

Reading script...

Script analysis:
- Purpose: WordPress database backup
- Creates: Timestamped SQL dumps
- Compression: gzip
- Retention: 7 days
- Security: ✅ No hardcoded credentials
- Quality: Good practices used

Suggested action:
Save to: /home/dave/skippy/scripts/wordpress/wordpress_backup_v1.0.0.sh

Changes needed:
1. Add version number (per script_saving_protocol.md)
2. Add documentation header
3. Set executable permissions

Create enhanced version with proper formatting?
```

---

## Integration with Other Protocols

### Script Saving Protocol
Reference: `/home/dave/skippy/conversations/script_saving_protocol.md`

When script downloaded → apply script saving standards:
- Versioning required
- Documentation header required
- Save to proper category
- Set permissions

### Error Logging Protocol
Reference: `/home/dave/skippy/conversations/error_logging_protocol.md`

When error screenshot downloaded → offer to log error:
- Extract error message
- Capture context
- Document solution
- Add to error log

### Git Workflow Protocol
Reference: `/home/dave/skippy/conversations/git_workflow_protocol.md`

When code files downloaded → suggest git workflow:
- Review code
- Test locally
- Commit with proper message
- Push if appropriate

### WordPress Maintenance Protocol
Reference: `/home/dave/skippy/conversations/wordpress_maintenance_protocol.md`

When WordPress files downloaded → apply WP workflows:
- Test in Local first
- Backup before applying
- Use WP-CLI when possible
- Deploy with checklist

---

## Automation Opportunities

### Future Enhancements

**inotify-based watcher** (advanced):
```bash
inotifywait -m /home/dave/skippy/claude/downloads/ -e create -e moved_to
```

**Cron-based checker** (simple):
```bash
*/5 * * * * /home/dave/skippy/scripts/utility/check_downloads.sh
```

**Claude integration**:
- Auto-detect when Claude Code starts
- Check for new files since last session
- Process any pending downloads

---

## Best Practices

### Do's ✅

- ✅ Always read and analyze files before suggesting actions
- ✅ Apply security checks to code files
- ✅ Use proper naming conventions when organizing
- ✅ Offer 3-4 clear action options
- ✅ Clean up downloads folder regularly
- ✅ Apply relevant protocol standards

### Don'ts ❌

- ❌ Don't automatically move files without user approval
- ❌ Don't delete files without confirmation
- ❌ Don't execute code from downloads without review
- ❌ Don't ignore security concerns
- ❌ Don't leave downloads folder cluttered

---

## Quick Reference

### Check Downloads Command
```bash
ls -lt /home/dave/skippy/claude/downloads/ | head -10
```

### Read Most Recent File
```bash
# Get most recent filename
LATEST=$(ls -t /home/dave/skippy/claude/downloads/ | head -1)
# Read it
cat "/home/dave/skippy/claude/downloads/$LATEST"
```

### Common File Type Checks
```bash
file "/home/dave/skippy/claude/downloads/filename"
```

### Archive Contents
```bash
unzip -l "/home/dave/skippy/claude/downloads/file.zip"
```

---

**This protocol is part of the persistent memory system.**
**Reference when handling downloaded files.**

**Auto-triggers when**:
- User mentions downloading files
- User says "check downloads"
- User requests monitoring

**Integration**:
- Works with all existing protocols
- Enforces naming conventions
- Maintains organization standards
- Ensures security practices
