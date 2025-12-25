# Scan Documents

Start scanning documents with the Epson V39 scanner.

## Instructions for Claude

When this command is invoked, help the user scan documents with these options:

### Quick Scan (Default)
```bash
# Launch GUI scanner for easy scanning
bash /home/dave/skippy/scripts/automation/epson_scan_gui_v1.0.0.sh
```

### Smart Scan (CLI with OCR)
```bash
# Launch smart scanner with auto-naming and categorization
bash /home/dave/skippy/scripts/automation/epson_v39_smart_scanner_v2.0.0.sh
```

### Check Scanner Status
```bash
# Verify scanner is connected
epsonscan2 --list 2>&1
```

## Scan Output Locations

| Type | Location |
|------|----------|
| Session Output | `/home/dave/ScannedDocuments/YYYY-MM-DD_HH-MM-SS/` |
| Incoming Queue | `/home/dave/skippy/operations/scans/incoming/` |
| Processed | `/home/dave/skippy/operations/scans/processed/` |

## Post-Scan Processing

After scanning, offer to:
1. Move scans to Skippy incoming queue for processing
2. Run document classification
3. Upload to Google Drive

### Move to Skippy Pipeline
```bash
# Move scanned PDFs to incoming queue
mv /home/dave/ScannedDocuments/*/processed/*.pdf /home/dave/skippy/operations/scans/incoming/
```

### Process with Document Intelligence
```bash
bash /home/dave/skippy/scripts/automation/smart_document_scanner_v1.0.0.sh
```

## Usage Examples

| Command | Description |
|---------|-------------|
| `/scan` | Show scan options |
| `/scan quick` | Launch GUI scanner |
| `/scan smart` | Launch CLI with OCR |
| `/scan status` | Check scanner connection |

## Troubleshooting

If scanner not detected:
1. Check USB connection
2. Run `lsusb | grep -i epson`
3. Ensure epsonscan2 is installed: `which epsonscan2`
