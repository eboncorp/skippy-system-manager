# Intelligent File Processing System - Design Document

**Date:** 2025-11-18
**Version:** 1.0.0
**Status:** Design Phase

---

## 🎯 Goals

Create a fully automated, intelligent file processing system that:
1. **Watches** all input folders (downloads, uploads, scans)
2. **Reads** file content using OCR, metadata extraction, and AI
3. **Classifies** files intelligently (personal, business, campaign, etc.)
4. **Renames** files with descriptive, searchable names
5. **Organizes** files into logical folder structures
6. **Learns** from user corrections to improve over time
7. **Notifies** user of actions taken
8. **Backs up** everything before moving

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT FOLDERS (Watched)                       │
├─────────────────────────────────────────────────────────────────┤
│  • /home/dave/skippy/Downloads/                                 │
│  • /home/dave/skippy/claude/downloads/                          │
│  • /home/dave/skippy/claude/uploads/                            │
│  • /home/dave/Scans/Incoming/                                   │
│  • /home/dave/Documents/ (Simple Scan default)                  │
│  • /home/dave/Pictures/Screenshots/                             │
│  • /home/dave/Desktop/ (optional)                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              INTELLIGENT FILE PROCESSOR DAEMON                   │
├─────────────────────────────────────────────────────────────────┤
│  1. File Detection (inotify)                                    │
│  2. Quarantine/Staging (safety period)                          │
│  3. Content Analysis                                             │
│  4. Classification                                               │
│  5. Smart Rename                                                 │
│  6. Organization                                                 │
│  7. Logging & Notification                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT DESTINATIONS                           │
├─────────────────────────────────────────────────────────────────┤
│  CAMPAIGN (RunDaveRun)                                          │
│  ├── policies/                                                  │
│  ├── press_releases/                                            │
│  ├── media_assets/                                              │
│  ├── financial_reports/                                         │
│  └── correspondence/                                            │
│                                                                  │
│  BUSINESS (EbonCorp)                                            │
│  ├── contracts/                                                 │
│  ├── invoices/                                                  │
│  ├── receipts/                                                  │
│  ├── financial/                                                 │
│  ├── legal/                                                     │
│  └── correspondence/                                            │
│                                                                  │
│  PERSONAL                                                        │
│  ├── medical/                                                   │
│  ├── financial/                                                 │
│  ├── insurance/                                                 │
│  ├── legal/                                                     │
│  ├── taxes/                                                     │
│  ├── receipts/                                                  │
│  └── misc/                                                      │
│                                                                  │
│  TECHNICAL                                                       │
│  ├── scripts/                                                   │
│  ├── documentation/                                             │
│  ├── code_snippets/                                             │
│  └── system_configs/                                            │
│                                                                  │
│  MEDIA                                                           │
│  ├── photos/YYYY/MM/                                            │
│  ├── videos/YYYY/MM/                                            │
│  ├── music/Artist/Album/                                        │
│  └── screenshots/YYYY/MM/                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Intelligence Layers

### Layer 1: File Type Detection
```python
- Extension analysis (.pdf, .jpg, .docx, etc.)
- MIME type detection
- File signature verification (magic bytes)
- Binary vs text detection
```

### Layer 2: Content Analysis
```python
- PDF text extraction (PyPDF2, pdfplumber)
- Image OCR (Tesseract)
- Metadata extraction (exiftool, PIL)
- Document properties (author, title, keywords)
- Email parsing (.eml, .msg files)
```

### Layer 3: Semantic Understanding
```python
- Keyword matching (bill, invoice, receipt, contract, policy)
- Named entity recognition (names, dates, amounts, addresses)
- Pattern matching (SSN, EIN, phone numbers, emails)
- Date extraction
- Amount/currency detection
```

### Layer 4: AI Classification (Optional - MCP Integration)
```python
- Send file content to Claude via MCP
- Get classification suggestion
- Get rename suggestion
- Get summary for logging
- Learn from user feedback
```

---

## 📝 Smart Rename System

### Format Templates

**Invoices/Receipts:**
```
{YYYY-MM-DD}_{vendor}_{type}_{amount}.{ext}
Example: 2025-11-18_amazon_receipt_45.99.pdf
```

**Medical Documents:**
```
{YYYY-MM-DD}_{provider}_{type}_{patient}.{ext}
Example: 2025-11-18_baptist_health_lab_results_dave.pdf
```

**Contracts/Legal:**
```
{YYYY-MM-DD}_{party}_{document_type}_{brief_desc}.{ext}
Example: 2025-11-18_acme_corp_contract_consulting_services.pdf
```

**Campaign Materials:**
```
{YYYY-MM-DD}_{category}_{title}.{ext}
Example: 2025-11-18_policy_public_safety_budget_proposal.pdf
```

**Screenshots:**
```
{YYYY-MM-DD}_{HH-MM-SS}_{app}_{description}.{ext}
Example: 2025-11-18_01-39-02_firefox_rundaverun_homepage.png
```

**Generic:**
```
{YYYY-MM-DD}_{original_name_cleaned}.{ext}
Example: 2025-11-18_important_document.pdf
```

### Name Cleaning Rules
- Convert to lowercase
- Replace spaces with underscores
- Remove special characters (keep: - _ .)
- Truncate to 200 chars max
- Remove duplicate underscores
- Strip leading/trailing underscores

---

## 🔍 Classification Rules

### Priority Order (First Match Wins)

1. **Campaign Files** (RunDaveRun)
   - Keywords: "Dave Biggers", "rundaverun", "campaign", "policy", "Louisville Metro Council"
   - Email domains: @rundaverun.org
   - Folders: Anything in /rundaverun/

2. **Business Files** (EbonCorp)
   - Keywords: "EbonCorp", "invoice", "contract", "LLC"
   - EIN: XX-XXXXXXX pattern
   - Email domains: @eboncorp.com
   - Vendor names: (configurable list)

3. **Personal - Financial**
   - Keywords: "bank statement", "credit card", "investment", "tax"
   - Bank names: Chase, Fifth Third, etc.

4. **Personal - Medical**
   - Keywords: "patient", "doctor", "lab results", "prescription", "insurance"
   - Provider names: Baptist Health, Norton, etc.

5. **Personal - Legal**
   - Keywords: "contract", "lease", "title", "deed", "will"

6. **Technical**
   - Extensions: .sh, .py, .js, .md, .json, .yaml, .conf
   - Keywords: "script", "code", "config"

7. **Media**
   - Extensions: .jpg, .png, .mp4, .mp3, .wav
   - Based on EXIF data

8. **Unknown** → Quarantine for manual review

---

## ⚙️ Daemon Configuration

### File: `/etc/skippy/file_processor_config.yaml`

```yaml
# Intelligent File Processor Configuration
version: 1.0.0

# Input folders to watch
watch_folders:
  - path: /home/dave/skippy/Downloads
    enabled: true
    recursive: false

  - path: /home/dave/skippy/claude/downloads
    enabled: true
    recursive: false

  - path: /home/dave/skippy/claude/uploads
    enabled: true
    recursive: false

  - path: /home/dave/Scans/Incoming
    enabled: true
    recursive: false

  - path: /home/dave/Documents
    enabled: true
    recursive: false
    # Only watch for scanner output
    extensions: [.pdf, .png, .jpg, .jpeg, .tiff]

  - path: /home/dave/Pictures/Screenshots
    enabled: true
    recursive: false

  - path: /home/dave/Desktop
    enabled: false  # Optional - enable if desired
    recursive: false

# Processing behavior
processing:
  # Wait time before processing (allow file to fully download/save)
  stabilization_delay: 5  # seconds

  # Quarantine period (allow user to cancel if needed)
  quarantine_period: 30  # seconds

  # Enable AI classification via MCP
  use_ai_classification: true

  # Confidence threshold (0-100)
  min_confidence: 75

  # Unknown files go to quarantine
  quarantine_unknown: true

  # Backup before moving
  create_backup: true
  backup_retention_days: 90

# Output destinations
destinations:
  campaign: /home/dave/skippy/rundaverun/documents
  business: /home/dave/skippy/documents/business
  personal: /home/dave/skippy/documents/personal
  technical: /home/dave/skippy/development/misc
  media_photos: /home/dave/skippy/Pictures
  media_videos: /home/dave/skippy/videos
  media_screenshots: /home/dave/skippy/Pictures/Screenshots
  quarantine: /home/dave/skippy/documents/quarantine

# Notification settings
notifications:
  enabled: true
  method: desktop  # desktop, email, slack, log
  notify_on_success: true
  notify_on_error: true
  notify_on_quarantine: true

  # Desktop notification
  desktop:
    duration: 5000  # milliseconds
    urgency: normal  # low, normal, critical

  # Email notification (optional)
  email:
    enabled: false
    to: dave@eboncorp.com
    from: skippy@localhost

  # Slack notification (optional)
  slack:
    enabled: false
    webhook_url: ""

# Logging
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: /home/dave/skippy/logs/file_processor.log
  max_size_mb: 50
  backup_count: 5

  # Log every action to database for learning
  database: /home/dave/skippy/logs/file_processor.db

# Learning system
learning:
  enabled: true
  # Track user manual corrections
  track_corrections: true
  # Adjust classification weights based on history
  adaptive_classification: true

# Ignore patterns (never process these)
ignore_patterns:
  - "*.tmp"
  - "*.crdownload"
  - "*.part"
  - "*.download"
  - "*.swp"
  - "*.~lock*"
  - ".DS_Store"
  - "Thumbs.db"
  - "desktop.ini"

# File age limits
age_limits:
  # Don't process files older than X days (already organized)
  max_age_days: 7
  # Don't process files in the future (bad timestamps)
  allow_future_dates: false

# Performance
performance:
  # Max file size to OCR (in MB)
  max_ocr_size_mb: 50
  # Max concurrent processing
  max_workers: 4
  # Batch processing interval
  batch_interval_seconds: 10
```

---

## 🗄️ Database Schema

### SQLite Database: `/home/dave/skippy/logs/file_processor.db`

```sql
-- Files processed
CREATE TABLE processed_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT NOT NULL,
    original_name TEXT NOT NULL,
    final_path TEXT NOT NULL,
    final_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,  -- SHA256 for deduplication
    file_size INTEGER,
    mime_type TEXT,
    classification TEXT,
    confidence REAL,
    method TEXT,  -- 'rule', 'ai', 'manual'
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_folder TEXT,
    destination_folder TEXT
);

-- User corrections (for learning)
CREATE TABLE corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES processed_files(id),
    old_classification TEXT,
    new_classification TEXT,
    old_path TEXT,
    new_path TEXT,
    corrected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Classification rules (learned patterns)
CREATE TABLE learned_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,
    classification TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    source TEXT,  -- 'user_correction', 'ai', 'system'
    times_applied INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Processing errors
CREATE TABLE errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    error_message TEXT,
    error_type TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE
);

-- Quarantine queue
CREATE TABLE quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    reason TEXT,
    suggested_classification TEXT,
    confidence REAL,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed BOOLEAN DEFAULT FALSE
);

-- Statistics
CREATE TABLE stats (
    date DATE PRIMARY KEY,
    files_processed INTEGER DEFAULT 0,
    files_quarantined INTEGER DEFAULT 0,
    files_errored INTEGER DEFAULT 0,
    avg_confidence REAL,
    processing_time_avg REAL
);
```

---

## 🚀 Implementation Components

### Component 1: File Watcher (`file_watcher_daemon.py`)
- Uses inotify to watch all configured folders
- Detects: CREATE, CLOSE_WRITE, MOVED_TO events
- Queues files for processing
- Handles multiple simultaneous events

### Component 2: Content Analyzer (`content_analyzer.py`)
- PDF text extraction
- Image OCR (Tesseract)
- Metadata extraction
- Email parsing
- Returns structured data for classification

### Component 3: Classifier (`intelligent_classifier.py`)
- Rule-based classification
- AI-enhanced classification (MCP)
- Confidence scoring
- Learning from corrections

### Component 4: Smart Renamer (`smart_renamer.py`)
- Template-based naming
- Date extraction and formatting
- Entity extraction (amounts, vendors, etc.)
- Name sanitization

### Component 5: File Organizer (`file_organizer.py`)
- Creates destination folders
- Moves files safely (atomic operations)
- Creates backups
- Handles naming conflicts (append _001, _002, etc.)

### Component 6: Notification Manager (`notification_manager.py`)
- Desktop notifications
- Email notifications (optional)
- Slack notifications (optional)
- Log notifications

### Component 7: Learning Engine (`learning_engine.py`)
- Tracks user corrections
- Adjusts classification weights
- Suggests new rules
- Improves over time

### Component 8: Web UI (Optional) (`web_dashboard.py`)
- View recent activity
- Review quarantined files
- Train the system (mark correct/incorrect)
- View statistics
- Search processed files

---

## 📊 User Interfaces

### 1. Desktop Notifications
```
┌─────────────────────────────────────────┐
│ 📄 File Processed                       │
├─────────────────────────────────────────┤
│ important_document.pdf                  │
│ → 2025-11-18_contract_consulting.pdf   │
│                                         │
│ Classified: Business > Contracts        │
│ Confidence: 92%                         │
│                                         │
│ [View] [Undo] [Dismiss]                │
└─────────────────────────────────────────┘
```

### 2. Command Line Tool
```bash
# View recent activity
skippy-files status

# Review quarantine
skippy-files quarantine list

# Process quarantined file
skippy-files quarantine process 123 --category=business

# Search processed files
skippy-files search "invoice 2025-11"

# Train on correction
skippy-files learn --file-id=456 --correct-category=campaign

# View statistics
skippy-files stats --period=week
```

### 3. Web Dashboard (http://localhost:8765)
- Recent activity timeline
- Quarantine review interface
- Statistics dashboard
- Search interface
- Training interface
- Configuration editor

---

## 🔐 Security & Safety

### Safety Features
1. **Quarantine Period** - 30 second delay before final move (allow undo)
2. **Backups** - Original files backed up for 90 days
3. **Atomic Operations** - No partial moves/renames
4. **Checksum Verification** - Verify file integrity after move
5. **Permission Checking** - Verify write access before moving
6. **Conflict Resolution** - Never overwrite existing files

### Security Features
1. **Path Traversal Prevention** - Validate all paths
2. **Symlink Protection** - Don't follow symlinks
3. **Size Limits** - Don't process files > 1GB
4. **Malware Scanning** (Optional) - ClamAV integration
5. **Credential Protection** - Never log file contents with passwords
6. **Encrypted Logging** (Optional) - Encrypt sensitive logs

---

## 📈 Performance Optimization

### Strategies
1. **Parallel Processing** - Process multiple files concurrently
2. **Smart Caching** - Cache OCR results, metadata
3. **Batch Processing** - Group small files
4. **Priority Queue** - Process important files first
5. **Resource Limits** - Throttle when system busy
6. **Incremental OCR** - Only OCR first N pages

### Expected Performance
- **Small files (<1MB)**: 1-2 seconds
- **Medium files (1-10MB)**: 3-5 seconds
- **Large PDFs (10-50MB)**: 10-30 seconds
- **Very large files (>50MB)**: Quarantine for manual review

---

## 🎨 Advanced Features

### 1. Duplicate Detection
- SHA256 checksums
- Fuzzy matching for near-duplicates
- Suggest deletion or consolidation

### 2. Format Conversion
- Auto-convert HEIC → JPG
- Auto-convert DOCX → PDF
- Optimize PDFs (compression)

### 3. Email Integration
- Watch email attachments
- Parse email context for better classification
- Extract sender/subject for naming

### 4. Cloud Sync
- Auto-upload to Google Drive
- Backup to S3/Backblaze
- Sync across devices

### 5. Version Control
- Track document versions
- Compare changes
- Restore previous versions

### 6. Smart Tags
- Auto-tag files (searchable)
- Extract hashtags from filenames
- Category tags

### 7. Scheduled Tasks
- Monthly "organize Desktop" cleanup
- Weekly duplicate scan
- Daily statistics report

---

## 🧪 Testing Strategy

### Unit Tests
- Each component independently
- Mock file operations
- Test classification rules
- Test rename templates

### Integration Tests
- End-to-end file processing
- Multi-file scenarios
- Error handling
- Notification delivery

### Performance Tests
- Process 1000 files
- Concurrent processing
- Memory usage
- CPU usage

### User Acceptance Tests
- Real-world file samples
- Classification accuracy
- Rename quality
- User satisfaction

---

## 📋 Implementation Phases

### Phase 1: Core System (Week 1)
- ✅ File watcher daemon
- ✅ Basic content analyzer
- ✅ Rule-based classifier
- ✅ Smart renamer
- ✅ File organizer
- ✅ Desktop notifications
- ✅ Basic logging

### Phase 2: Intelligence (Week 2)
- ✅ OCR integration
- ✅ Metadata extraction
- ✅ AI classification (MCP)
- ✅ Database logging
- ✅ Learning engine

### Phase 3: User Experience (Week 3)
- ✅ CLI tool
- ✅ Quarantine review system
- ✅ Undo functionality
- ✅ Search capability
- ✅ Statistics dashboard

### Phase 4: Advanced Features (Week 4)
- ✅ Web UI
- ✅ Duplicate detection
- ✅ Format conversion
- ✅ Cloud sync
- ✅ Email integration

### Phase 5: Polish & Optimization (Week 5)
- ✅ Performance tuning
- ✅ Comprehensive testing
- ✅ Documentation
- ✅ User training
- ✅ Monitoring & alerting

---

## 📦 Dependencies

### Python Packages
```bash
# Core
watchdog>=3.0.0          # File system watching
inotify>=0.2.10          # Linux inotify interface

# Content Analysis
PyPDF2>=3.0.0            # PDF text extraction
pdfplumber>=0.10.0       # Advanced PDF parsing
pytesseract>=0.3.10      # OCR
Pillow>=10.0.0           # Image processing
python-magic>=0.4.27     # File type detection

# AI/ML
anthropic>=0.7.0         # Claude API (for MCP)

# Database
sqlite3                  # Built-in

# Notifications
notify2>=0.3.1           # Desktop notifications
plyer>=2.1.0             # Cross-platform notifications

# Web UI (optional)
flask>=3.0.0             # Web framework
gunicorn>=21.0.0         # WSGI server

# Utilities
pyyaml>=6.0.0            # Config parsing
python-dateutil>=2.8.0   # Date parsing
chardet>=5.0.0           # Character encoding detection

# System
psutil>=5.9.0            # System monitoring
```

### System Packages
```bash
sudo apt install -y \
  tesseract-ocr \
  tesseract-ocr-eng \
  libnotify-bin \
  inotify-tools \
  clamav \
  clamav-daemon
```

---

## 🔧 Configuration Examples

### Example: Campaign-Focused Setup
```yaml
processing:
  use_ai_classification: true
  min_confidence: 85  # High confidence for campaign files

destinations:
  campaign: /home/dave/skippy/rundaverun/documents

learning:
  enabled: true
  adaptive_classification: true

# Prioritize campaign files
priority_keywords:
  - "Dave Biggers"
  - "rundaverun"
  - "Louisville Metro Council"
  - "policy"
```

### Example: Privacy-Focused Setup
```yaml
processing:
  use_ai_classification: false  # No external AI
  create_backup: true

logging:
  level: WARNING  # Minimal logging

notifications:
  desktop:
    enabled: true
  email:
    enabled: false
  slack:
    enabled: false
```

---

## 📖 User Documentation

### Quick Start Guide
1. Install system: `sudo ./install.sh`
2. Configure: Edit `/etc/skippy/file_processor_config.yaml`
3. Start daemon: `systemctl --user start skippy-file-processor`
4. Test: Drop a file in Downloads folder
5. Check: `skippy-files status`

### Troubleshooting
- **Files not processing?** Check `skippy-files status`
- **Wrong classification?** Use `skippy-files learn` to correct
- **Quarantine piling up?** Review with `skippy-files quarantine list`
- **Performance issues?** Check logs: `tail -f /home/dave/skippy/logs/file_processor.log`

---

## 🎯 Success Metrics

### System Performance
- **Processing Time**: < 5 seconds for 90% of files
- **Classification Accuracy**: > 90% after 1 week of learning
- **False Positives**: < 5% quarantine rate
- **System Load**: < 5% CPU, < 100MB RAM

### User Experience
- **Zero Manual Organization**: Files auto-organized 95%+ of time
- **Easy Corrections**: < 30 seconds to correct misclassification
- **Transparency**: Clear logs and notifications
- **Confidence**: Users trust the system

---

## 🚀 Future Enhancements

### Version 2.0 (Future)
- Mobile app for on-the-go review
- Voice commands ("Skippy, where did you put that invoice?")
- Integration with accounting software (QuickBooks, etc.)
- Blockchain-backed audit trail
- Multi-user support
- Cloud-native deployment

### AI Improvements
- Custom model training on user's files
- Contextual understanding (previous files, calendar events)
- Predictive organization (know what you'll need soon)
- Natural language queries

---

## 📝 Notes

This system represents a **significant upgrade** from the current manual approach:

**Current State:**
- No active watching
- Manual organization only
- No intelligent classification
- No learning capability

**Future State:**
- 24/7 automated processing
- Intelligent classification
- Smart renaming
- Continuous learning
- Near-zero manual work

**Expected Time Savings:**
- Current: ~2 hours/week on file organization
- Future: ~10 minutes/week reviewing edge cases
- **Savings: ~90% reduction in time spent**

---

**End of Design Document**
