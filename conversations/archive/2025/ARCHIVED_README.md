# Archived Protocols

**Date Archived:** 2025-11-05
**Reason:** Low usage, consolidation, or superseded by newer protocols

---

## Archived Protocols in This Directory

### file_download_management_protocol.md
**Archived:** 2025-11-05
**Reason:** Rarely referenced (< 5 times), limited utility
**Status:** Can be restored if needed
**Replacement:** General file organization covered in documentation_standards_protocol

### package_creation_protocol.md
**Archived:** 2025-11-05
**Reason:** Used < 5 times, highly specialized use case
**Status:** Can be restored if needed
**Replacement:** Script management protocol covers most script packaging needs

---

## How to Restore an Archived Protocol

If you need to restore an archived protocol:

```bash
# Move it back to active protocols
mv /home/dave/skippy/conversations/archive/2025/[protocol_name].md /home/dave/skippy/conversations/

# Update the protocol version and status
# Add note: "Restored from archive YYYY-MM-DD"

# Commit the restoration
git add conversations/[protocol_name].md conversations/archive/2025/ARCHIVED_README.md
git commit -m "Restore: [protocol_name] - [reason for restoration]"
```

---

## Archive Policy

**Protocols are archived when:**
- Used less than 5 times in 6 months
- Superseded by consolidated protocols
- No longer relevant to current operations
- Functionality covered by other protocols

**Archived protocols are:**
- Kept for reference (not deleted)
- Organized by year
- Can be restored if needed
- Reviewed annually for permanent deletion

**Permanent deletion after:**
- 2 years in archive with no restoration requests
- Confirmed no historical value
- Approved by protocol review

---

**Last Updated:** 2025-11-05
