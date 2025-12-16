Check downloads and show where the intelligent file processor sorted them.

## Steps:

1. **Check pending downloads** in /home/dave/skippy/operations/downloads/
   - List any files waiting to be processed

2. **Check quarantine** (low-confidence files needing review):
   - List files in /home/dave/skippy/operations/quarantine/
   - Show the most recent 5 quarantined files

3. **Show recently processed files** from the processor log:
   - Parse /home/dave/skippy/system/logs_main/file_processor.log
   - Find lines containing "Moved:" OR "Quarantined:"
   - Show the last 10 processed files (or number specified by user)

4. **For each file show:**
   - Date/time processed
   - Original filename
   - Destination path OR "QUARANTINE" if quarantined
   - Reason (if quarantined)

5. **Summary:**
   - Number of files pending in downloads
   - Number of files in quarantine
   - Most recent processed file

Example output format:
```
=== Pending Downloads ===
(none)

=== Quarantine (needs review) ===
[2025-12-15 22:46:07] files (1)_001.zip (Low confidence 35%)

=== Recently Processed (last 10) ===
[2025-12-15 22:46:07]
  File: files (1).zip
  To:   QUARANTINE (Low confidence 35%)

[2025-12-07 17:34:13]
  File: button_color_red_black.png
  To:   business/campaign/documents/
```

## Also check:
- ~/Downloads (browser default) - remind user to download to /home/dave/skippy/operations/downloads/ instead
