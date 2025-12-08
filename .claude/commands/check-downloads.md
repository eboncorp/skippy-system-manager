Check downloads and show where the intelligent file processor sorted them.

## Steps:

1. **Check pending downloads** in /home/dave/skippy/operations/downloads/
   - List any files waiting to be processed

2. **Show recently sorted files** from the processor log:
   - Parse /home/dave/skippy/system/logs_main/file_processor.log
   - Find lines containing "Moved:" to show original filename and destination
   - Show the last 10 sorted files (or number specified by user)

3. **For each sorted file show:**
   - Date/time processed
   - Original filename
   - Destination path (shortened, relative to /home/dave/skippy/)
   - Category it was classified as (if visible in log)

4. **Summary:**
   - Number of files pending in downloads
   - Number of files sorted today
   - Most recent sort destination

Example output format:
```
=== Pending Downloads ===
(none)

=== Recently Sorted (last 10) ===
[2025-12-07 17:34:13]
  File: button_color_red_black.png
  To:   business/campaign/documents/correspondence/

[2025-12-07 10:03:58]
  File: EVERYTHING_COMPLETE.zip
  To:   development/misc/misc/
```
