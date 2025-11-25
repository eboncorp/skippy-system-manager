# Intelligent File Processor - MVP v1.0.0

**Status:** ✅ Ready to Run
**Created:** 2025-11-18
**Phase:** MVP (Minimum Viable Product)

---

## What It Does

Automatically watches configured folders and:
1. ✅ **Detects** new files instantly
2. ✅ **Analyzes** content (PDF text, image metadata)
3. ✅ **Classifies** intelligently (Campaign, Business, Personal, Technical, Media)
4. ✅ **Renames** with smart, searchable names (YYYY-MM-DD_description.ext)
5. ✅ **Organizes** into logical folders automatically
6. ✅ **Notifies** you with desktop notifications
7. ✅ **Backs up** originals for safety
8. ✅ **Quarantines** uncertain files for review

---

## Quick Start

### 1. Review Configuration

Edit the configuration file:
```bash
nano config/default_config.yaml
```

Key settings:
- `watch_folders` - Which folders to monitor
- `destinations` - Where to organize files
- `processing.min_confidence` - Classification threshold (default: 75%)
- `processing.quarantine_period` - Seconds before final move (default: 30s)

### 2. Run the Daemon

```bash
cd /home/dave/skippy/intelligent_file_processor
./file_processor_daemon.py
```

Or with options:
```bash
./file_processor_daemon.py --verbose    # Show debug logging
./file_processor_daemon.py --config /path/to/config.yaml  # Custom config
```

### 3. Test It!

Open a new terminal and drop a test file:
```bash
# Download a sample PDF
wget -O /home/dave/skippy/Downloads/test_invoice.pdf https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf

# Or create a text file
echo "This is an invoice from Amazon for $45.99" > /home/dave/skippy/Downloads/test_invoice.txt
```

Watch the daemon process it!

### 4. Stop the Daemon

Press `Ctrl+C` to stop gracefully.

---

## Watched Folders (Default)

The daemon monitors these folders:
- `/home/dave/skippy/Downloads/`
- `/home/dave/skippy/claude/downloads/`
- `/home/dave/skippy/claude/uploads/`
- `/home/dave/Scans/Incoming/`

(More can be enabled in config)

---

## Output Destinations

Files are organized to:

### Campaign (RunDaveRun)
`/home/dave/skippy/rundaverun/documents/`
- policies/
- press_releases/
- media_assets/
- financial_reports/
- correspondence/

### Business (EbonCorp)
`/home/dave/skippy/documents/business/`
- contracts/
- invoices/
- receipts/
- financial/
- legal/
- correspondence/

### Personal
`/home/dave/skippy/documents/personal/`
- medical/
- financial/
- insurance/
- legal/
- taxes/
- receipts/
- misc/

### Technical
`/home/dave/skippy/development/misc/`
- scripts/
- documentation/
- configs/
- misc/

### Media
- Photos: `/home/dave/skippy/Pictures/YYYY/MM/`
- Videos: `/home/dave/skippy/videos/YYYY/MM/`
- Screenshots: `/home/dave/skippy/Pictures/Screenshots/YYYY/MM/`

### Quarantine
`/home/dave/skippy/documents/quarantine/`
- Low confidence files for manual review

### Backups
`/home/dave/skippy/backups/file_processor/YYYY/MM/`
- Originals kept for 90 days

---

## Smart Naming Examples

**Before:**
- `invoice.pdf`
- `IMG_2847.jpg`
- `Screenshot from 2025-11-18.png`
- `important_document.pdf`

**After:**
- `2025-11-18_amazon_receipt_45_99.pdf`
- `2025-11-18_campaign_event_volunteer_group.jpg`
- `2025-11-18_01-39-firefox_rundaverun_homepage.png`
- `2025-11-18_contract_consulting_services.pdf`

---

## Classification Rules

The system uses 50+ rules to classify files:

### Campaign (RunDaveRun)
- Keywords: "Dave Biggers", "rundaverun", "Louisville Metro Council", "policy"
- Emails: @rundaverun.org

### Business (EbonCorp)
- Keywords: "EbonCorp", "invoice", "contract", "LLC"
- Vendor names: Amazon, Walmart, AT&T, etc.

### Personal - Medical
- Keywords: "patient", "doctor", "lab results", "prescription"
- Providers: Baptist Health, Norton, Anthem, etc.

### Personal - Financial
- Keywords: "bank statement", "credit card", "investment", "tax"
- Banks: Chase, Fifth Third, etc.

### Technical
- Extensions: .sh, .py, .js, .md, .json, .yaml
- Keywords: "script", "code", "config"

---

## Components

### Core Modules

1. **config_loader.py** - Configuration management
2. **file_watcher.py** - File system monitoring (watchdog-based)
3. **content_analyzer.py** - Content extraction (PDF, images, text)
4. **intelligent_classifier.py** - Rule-based classification
5. **smart_renamer.py** - Intelligent filename generation
6. **file_organizer.py** - Safe file moving with backups

### Main Daemon

**file_processor_daemon.py** - Ties everything together

---

## Testing Individual Components

Test each component independently:

### Test Content Analyzer
```bash
cd /home/dave/skippy/intelligent_file_processor/core
./content_analyzer.py /path/to/test/file.pdf
```

### Test Classifier
```bash
./intelligent_classifier.py /path/to/test/file.pdf
```

### Test Smart Renamer
```bash
./smart_renamer.py /path/to/test/file.pdf
```

---

## Configuration Options

### Key Settings

```yaml
# Processing behavior
processing:
  stabilization_delay: 5        # Wait for file to finish downloading
  quarantine_period: 30         # Grace period before final move
  min_confidence: 75            # Classification threshold (0-100)
  quarantine_unknown: true      # Quarantine low-confidence files
  create_backup: true           # Backup originals
  backup_retention_days: 90     # How long to keep backups

# Notifications
notifications:
  enabled: true
  notify_on_success: true       # Show notification for every file
  notify_on_error: true
  notify_on_quarantine: true
```

---

## Troubleshooting

### No files being processed?

1. Check daemon is running:
   ```bash
   ps aux | grep file_processor_daemon
   ```

2. Check watched folders exist:
   ```bash
   ls -la /home/dave/skippy/Downloads/
   ```

3. Check logs (if file logging enabled)

### Files going to quarantine?

- Files with confidence < 75% are quarantined
- Review quarantine folder: `/home/dave/skippy/documents/quarantine/`
- Lower `min_confidence` in config if too aggressive

### Wrong classification?

- Check the classification rules in `intelligent_classifier.py`
- Add custom keywords/patterns
- Consider enabling AI classification (Phase 2)

### Desktop notifications not showing?

- Check `notify-send` is installed:
  ```bash
  which notify-send
  ```
- Install if needed:
  ```bash
  sudo apt install libnotify-bin
  ```

---

## Safety Features

✅ **30-second grace period** - Cancel before final move
✅ **Automatic backups** - Originals kept for 90 days
✅ **Conflict resolution** - Never overwrites existing files
✅ **Quarantine system** - Low-confidence files reviewed manually
✅ **Atomic operations** - No partial moves or corruption

---

## Current Limitations (MVP)

This is the MVP (Phase 1). The following are planned but not yet implemented:

❌ OCR for scanned documents (Phase 2)
❌ AI classification via Claude (Phase 2)
❌ Web dashboard (Phase 4)
❌ CLI tool for review/search (Phase 3)
❌ Learning from corrections (Phase 4)
❌ Duplicate detection (Phase 4)
❌ Format conversion (Phase 4)

---

## Next Steps

### Phase 2: Intelligence (2 weeks)
- Add OCR (Tesseract)
- AI classification via MCP
- Database logging
- Learning engine

### Phase 3: User Experience (1 week)
- CLI tool (`skippy-files` command)
- Quarantine review interface
- Search capability
- Undo functionality

### Phase 4: Advanced Features (1-2 weeks)
- Web dashboard
- Duplicate detection
- Format conversion
- Email integration

---

## Documentation

Full design documentation:
- `/home/dave/skippy/documentation/intelligent_file_processor/QUICK_SUMMARY.md`
- `/home/dave/skippy/documentation/intelligent_file_processor/system_design.md`
- `/home/dave/skippy/documentation/intelligent_file_processor/implementation_roadmap.md`

---

## Support

**Issues?** Check troubleshooting section above
**Questions?** Review the full design documentation
**Feedback?** Let me know what works and what doesn't!

---

**Version:** 1.0.0 MVP
**Last Updated:** 2025-11-18
**Status:** ✅ Ready to Run
