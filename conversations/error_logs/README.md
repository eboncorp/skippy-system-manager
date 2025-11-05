# Error Logs Directory

**Purpose:** Centralized storage for error logs across all protocols and systems
**Protocol:** Documented in error_logging_protocol.md

---

## Directory Structure

```
error_logs/
├── recurring/        # Errors that happen repeatedly (need fixing)
├── resolved/         # Errors that have been fixed (historical reference)  
└── YYYY-MM/         # Monthly error logs (active tracking)
```

---

## Log File Naming Convention

```
YYYYMMDD_HHMMSS_{system}_{error_type}.log
```

**Examples:**
- `20251104_112500_wordpress_database_error.log`
- `20251104_150300_script_syntax_error.log`
- `20251104_203000_deployment_failed.log`

---

**Created:** November 4, 2025
**Status:** Active
