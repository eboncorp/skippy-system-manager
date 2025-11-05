# Claude Upload Management Protocol

**Version:** 1.0
**Created:** November 1, 2025
**Purpose:** Standardize file management for Claude.ai uploads

---

## Standard Upload Directory

**Primary Location:** `/home/dave/skippy/claude/uploads/`

All files prepared for upload to Claude.ai MUST be saved to this directory.

---

## Naming Convention

Files should follow this format:

```
{project}_{description}_{YYYYMMDD}_{HHMMSS}.{ext}
```

**Examples:**
- `rundaverun_complete_local_site_20251101_230300.zip`
- `campaign_fact_sheet_20251101_230300.md`
- `wordpress_database_export_20251101_230300.sql`

---

## Required Metadata File

Each upload package MUST include a `START_HERE.md` or `README.md` file that contains:

1. **Package Contents** - List of files included
2. **Purpose** - What this upload is for
3. **Key Information** - Important facts, numbers, standards
4. **Import Instructions** - How to use the files
5. **Context** - Current state vs. desired state

---

## Automatic Protocol Steps

When creating files for Claude.ai upload:

### Step 1: Create Upload Package
```bash
# Create timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create package directory
mkdir -p /tmp/claude_upload_${TIMESTAMP}

# Add files to package
# ... copy relevant files ...

# Create START_HERE.md with package info
```

### Step 2: Create Archive
```bash
# Compress package
cd /tmp
zip -r "claude_upload_${PROJECT}_${TIMESTAMP}.zip" "claude_upload_${TIMESTAMP}/"
```

### Step 3: Save to Standard Location
```bash
# Move to upload directory
mv "claude_upload_${PROJECT}_${TIMESTAMP}.zip" /home/dave/skippy/claude/uploads/

# Verify
ls -lh /home/dave/skippy/claude/uploads/
```

### Step 4: Create Upload Log Entry
```bash
# Log the upload
echo "$(date): Created ${PROJECT} upload package (${SIZE})" >> /home/dave/skippy/claude/uploads/upload_log.txt
```

---

## File Retention Policy

- Keep upload packages for 30 days
- Archive to long-term storage after 30 days
- Clean up old packages monthly

---

## Upload Checklist

Before creating upload package, verify:

- [ ] All relevant files included
- [ ] START_HERE.md or README.md created with context
- [ ] Fact sheet included (if applicable)
- [ ] File sizes optimized (compress SQL files, etc.)
- [ ] Naming convention followed
- [ ] Saved to `/home/dave/skippy/claude/uploads/`
- [ ] File is accessible (check permissions)

---

## Quick Reference Commands

### Create Upload Package
```bash
# One-liner to create and save upload
TIMESTAMP=$(date +%Y%m%d_%H%M%S) && \
mkdir -p /tmp/claude_upload_${TIMESTAMP} && \
# ... add files ... && \
cd /tmp && \
zip -r "claude_upload_PROJECT_${TIMESTAMP}.zip" "claude_upload_${TIMESTAMP}/" && \
mv "claude_upload_PROJECT_${TIMESTAMP}.zip" /home/dave/skippy/claude/uploads/ && \
ls -lh /home/dave/skippy/claude/uploads/ | tail -1
```

### List Recent Uploads
```bash
ls -lht /home/dave/skippy/claude/uploads/ | head -10
```

### Find Upload by Date
```bash
find /home/dave/skippy/claude/uploads/ -name "*20251101*"
```

### Check Upload Size
```bash
du -sh /home/dave/skippy/claude/uploads/*
```

---

## Integration with Skippy

This protocol is part of the Skippy system and should be referenced in:
- `/home/dave/.claude/CLAUDE.md` (global instructions)
- Project-specific upload procedures
- Backup and archival scripts

---

## Example Upload Session

```bash
# 1. Create upload package
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT="rundaverun"
UPLOAD_DIR="/tmp/claude_upload_${TIMESTAMP}"

mkdir -p "$UPLOAD_DIR"

# 2. Add files
cp /path/to/fact_sheet.md "$UPLOAD_DIR/"
cp /path/to/database.sql "$UPLOAD_DIR/"
cp -r /path/to/plugin "$UPLOAD_DIR/"

# 3. Create README
cat > "$UPLOAD_DIR/START_HERE.md" <<EOF
# Project Upload - $(date)

## Contents
- fact_sheet.md
- database.sql
- plugin/

## Purpose
Upload package for project work in Claude.ai

## Key Information
...
EOF

# 4. Create archive
cd /tmp
zip -r "claude_upload_${PROJECT}_${TIMESTAMP}.zip" "claude_upload_${TIMESTAMP}/"

# 5. Save to standard location
mv "claude_upload_${PROJECT}_${TIMESTAMP}.zip" /home/dave/skippy/claude/uploads/

# 6. Log
echo "$(date): Created ${PROJECT} upload ($(du -h /home/dave/skippy/claude/uploads/claude_upload_${PROJECT}_${TIMESTAMP}.zip | cut -f1))" >> /home/dave/skippy/claude/uploads/upload_log.txt

# 7. Verify
ls -lh /home/dave/skippy/claude/uploads/ | tail -1
```

---

## Troubleshooting

**Can't find upload file:**
- Check `/home/dave/skippy/claude/uploads/`
- Search by date: `find /home/dave/skippy/claude/uploads/ -name "*YYYYMMDD*"`

**File too large for Claude.ai:**
- Compress SQL files: `gzip database.sql`
- Split large archives: `split -b 50M archive.zip archive.zip.part`
- Remove unnecessary files

**Permission denied:**
- Fix permissions: `chmod 644 /home/dave/skippy/claude/uploads/file.zip`
- Check ownership: `chown dave:dave /home/dave/skippy/claude/uploads/file.zip`

---

**Status:** Active Protocol
**Maintained By:** Dave
**Review Date:** Monthly
