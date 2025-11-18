# Intelligent File Processor - Quick Start

## ✅ System is Ready!

Everything is built, tested, and committed to GitHub:
- https://github.com/eboncorp/skippy-system-manager

## 🚀 How to Run

### Option 1: Easy Start (Recommended)
```bash
cd /home/dave/skippy/intelligent_file_processor
./START.sh
```

### Option 2: Manual Start
```bash
cd /home/dave/skippy/intelligent_file_processor
python3 file_processor_daemon.py
```

### Option 3: With Options
```bash
./file_processor_daemon.py --verbose    # Show debug output
./file_processor_daemon.py --config /path/to/custom_config.yaml
```

## 📝 Test It

**While the daemon is running**, open a new terminal and try:

```bash
# Test 1: Invoice
echo "INVOICE
Amazon.com
Date: November 18, 2025
Total: $45.99" > ~/skippy/Downloads/test_invoice.txt

# Test 2: Policy
echo "Policy Proposal: Public Safety
Dave Biggers for Louisville Metro Council
Budget: $10 million" > ~/skippy/Downloads/test_policy.txt

# Test 3: Technical
echo '#!/bin/bash
echo "Hello World"' > ~/skippy/Downloads/test_script.sh
```

Watch the daemon log output! Files should be:
1. Detected instantly
2. Analyzed (5 seconds stabilization)
3. Classified
4. Renamed intelligently
5. Moved to correct folder (after 30 second grace period)

## 📂 Where Files Go

### Campaign (RunDaveRun)
`/home/dave/skippy/rundaverun/documents/`
- Contains "Dave Biggers", "policy", "campaign"

### Business
`/home/dave/skippy/documents/business/`
- invoices/ - Contains "invoice", "bill", amounts
- receipts/ - Contains "receipt", vendor names
- contracts/ - Contains "contract", "agreement"

### Personal
`/home/dave/skippy/documents/personal/`
- medical/ - Healthcare documents
- financial/ - Bank statements, taxes
- legal/ - Legal documents

### Technical
`/home/dave/skippy/development/misc/`
- scripts/ - .sh, .py, .js files
- documentation/ - .md files

### Quarantine
`/home/dave/skippy/documents/quarantine/`
- Low confidence files (< 75%)

### Backups
`/home/dave/skippy/backups/file_processor/YYYY/MM/`
- All originals kept for 90 days

## ⚙️ Configuration

Edit settings:
```bash
nano config/default_config.yaml
```

Key settings:
- `watch_folders` - Which folders to monitor
- `processing.min_confidence` - Classification threshold (default: 75%)
- `processing.quarantine_period` - Grace period before final move (default: 30s)
- `destinations` - Where to organize files

## 🛑 Stop the Daemon

Press `Ctrl+C` in the terminal where daemon is running

## 🐛 Troubleshooting

### No files being processed?
```bash
# Check daemon is running
ps aux | grep file_processor

# Check watched folders exist
ls -la ~/skippy/Downloads/
```

### Files going to quarantine?
- Confidence < 75%
- Check: `/home/dave/skippy/documents/quarantine/`
- Lower `min_confidence` in config if too aggressive

### Want to see what's happening?
```bash
# Run with verbose logging
./file_processor_daemon.py --verbose
```

## 📊 What's Working Now (MVP)

✅ Automatic file watching (4 folders)
✅ Content analysis (PDF, images, text)
✅ Intelligent classification (50+ rules)
✅ Smart renaming (YYYY-MM-DD_vendor_type.ext)
✅ Safe organization (backups, grace period)
✅ Desktop notifications
✅ Quarantine for uncertain files

## 🔮 Coming Next (Phase 2-5)

- OCR for scanned documents
- AI classification via Claude
- Web dashboard
- CLI tool (`skippy-files` command)
- Learning from corrections
- Duplicate detection

## 📚 Full Documentation

See:
- `README.md` - Complete user guide
- `/home/dave/skippy/documentation/intelligent_file_processor/` - Full design docs

## 💡 Tips

1. **Start small** - Test with a few files first
2. **Watch the logs** - Run with --verbose to see what's happening
3. **30-second grace** - You have time to cancel if something looks wrong
4. **Quarantine is your friend** - Check it regularly for mis-classified files
5. **Backups are automatic** - Originals saved for 90 days

## ⏱️ Time Savings

**Expected:**
- 93% reduction in file organization time
- 75 min/day → 5 min/day
- 425 hours/year saved!

---

**Ready to automate your life? Run `./START.sh` and let it work!** 🎉
