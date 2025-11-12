# Conversation Index
**Last Updated:** 2025-11-12
**Total Conversations:** 125+ files
**Index Version:** 1.1

---

## Recent Activity (Last 30 Days)

### November 2025

- **github_integration_complete_2025-11-12.md** [Nov 12]
  - Tags: `github`, `security`, `integration`, `rundaverun`, `features`
  - Summary: Reviewed all 8 GitHub branches, fixed critical security vulnerability (removed SQL files), documented 2 existing features (donation tracker, Spanish support)
  - Key Achievements: Security fix pushed to GitHub, 27 security issues identified, features ready to use

- **security_audit_rundaverun_2025-11-12.md** [Nov 12]
  - Tags: `security`, `audit`, `vulnerabilities`, `rundaverun`
  - Summary: Comprehensive 37KB security audit with 27 issues (5 critical, 8 high, 9 medium, 5 low). Risk score 6.2/10.
  - Critical Issues: Database credentials in repo (FIXED), unsanitized input, wp-config exposure, low test coverage

- **pexels_setup_complete_2025-11-12.md** [Nov 12]
  - Tags: `mcp-server`, `pexels`, `stock-photos`, `integration`, `v2.3.2`
  - Summary: Successfully integrated Pexels stock photos API with 4 tools. Fully tested and operational. 3M+ free photos available.
  - Tools: search_photos, get_photo, download_photo, curated_photos

- **google_photos_final_troubleshooting.md** [Nov 12]
  - Tags: `mcp-server`, `google-photos`, `oauth`, `troubleshooting`, `pending`
  - Summary: Google Photos integration (6 tools) complete but blocked by OAuth 403 error. To be revisited when OAuth propagates.
  - Status: Code complete, documentation complete, OAuth issue pending

- **site_quality_assurance_complete_session_2025-11-03.md** [Nov 3]
  - Tags: `wordpress`, `qa`, `bugfixes`, `production-ready`, `rundaverun`
  - Summary: Fixed 22 critical issues including factual errors, broken links, and budget inconsistencies. Site now production-ready for deployment.
  - Key Files: `proofreading_report`, `FACT_SHEET`, `functional_testing_report`

- **deployment_infrastructure_review_2025-11-03.md** [Nov 3]
  - Tags: `deployment`, `rest-api`, `github`, `filezilla`, `infrastructure`
  - Summary: Reviewed existing deployment methods: REST API for data sync, FileZilla for file transfer, GitHub Actions for code deployment.

- **budget_audit_correction_deployment_session_2025-11-02.md** [Nov 2]
  - Tags: `budget`, `corrections`, `deployment`, `rundaverun`
  - Summary: Standardized budget figures across all policy documents ($77.4M substations, $34.2M wellness, $1.80 ROI)

- **DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md** [Nov 1]
  - Tags: `reference`, `authoritative`, `campaign-data`, `rundaverun`
  - Summary: THE authoritative source for all campaign facts, figures, and biographical information
  - **CRITICAL**: Always reference this file for campaign facts

### October 2025
- **github_cicd_rest_api_setup_session_2025-10-21.md** [Oct 21]
  - Tags: `deployment`, `github-actions`, `rest-api`, `automation`
  - Summary: Completed GitHub Actions CI/CD setup with REST API authentication for automated deployments

- **protocol_system_implementation_session_2025-10-28.md** [Oct 28]
  - Tags: `protocols`, `documentation`, `skippy`, `standards`
  - Summary: Implemented protocol system for standardized workflows and documentation

---

## Active Projects

### MCP Server Development
**Status:** 🟢 Active Development
**Current Version:** v2.3.2 (75 tools)
**Last Update:** November 12, 2025
**Session Count:** 8+ files

**Key Files:**
- `/home/dave/skippy/mcp-servers/general-server/server.py` - Main server (v2.3.2)
- `CHANGELOG_v2.3.2.md` - Latest version documentation
- `PEXELS_SETUP.md` - Stock photos integration guide
- `GOOGLE_PHOTOS_SETUP.md` - Google Photos setup (pending OAuth)

**Current State:**
- ✅ 4 Pexels stock photo tools (fully operational)
- ⚠️ 6 Google Photos tools (OAuth 403 issue pending)
- ✅ 13 Google Drive tools (fully operational)
- ✅ 52 general-purpose tools
- 📚 Comprehensive documentation

**Integrations:**
1. **Pexels Stock Photos** (v2.3.2) ✅ - Free campaign photography
2. **Google Photos** (v2.3.2) ⚠️ - Personal photo library (OAuth pending)
3. **Google Drive** (v2.2.0-v2.3.0) ✅ - File management
4. **GitHub** (v2.1.0) ✅ - Repository operations
5. **Slack** (v2.1.0) ✅ - Team notifications

---

### RunDaveRun Campaign Website (rundaverun.org)
**Status:** ✅ Production Ready (awaiting deployment)
**Last Update:** November 12, 2025 (GitHub integration review)
**Session Count:** 51+ files

**Key Files:**
- `DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md` - Authoritative campaign data
- `DEPLOYMENT_GUIDE.md` - Deployment procedures
- `site_quality_assurance_complete_session_2025-11-03.md` - Latest QA session

**Current State:**
- ✅ 22 critical fixes completed
- ✅ All factual errors corrected
- ✅ Budget figures standardized
- ✅ Privacy Policy published
- ✅ Critical security fix (SQL files removed from GitHub)
- ✅ 2 features documented (donation tracker, Spanish support)
- 🟢 Ready for GoDaddy production deployment

**GitHub Repository Status:**
- Repository: `eboncorp/rundaverun-website`
- Security: 1 critical issue fixed, 4 remaining
- Features Available: Campaign donation tracker, Spanish/English switcher
- Branches: 8 branches reviewed and documented

**Deployment Infrastructure:**
1. **REST API**: WordPress API for content/database sync
2. **FileZilla/SFTP**: Manual file transfers (GoDaddy)
3. **GitHub Actions**: Automated code deployment via rsync

---

### Skippy Scripts & Protocols
**Status:** 🟢 Active Development
**Last Update:** October 31, 2025
**Session Count:** 23+ files

**Key Sessions:**
- `protocol_system_implementation_session_2025-10-28.md`
- `script_organization_and_protocol_creation_session_2025-10-31.md`
- `documentation_standards_protocol.md`

**Protocols Created:**
- Script creation protocol
- Package creation protocol
- Documentation standards
- Deployment checklist
- Auto-transcript protocol

---

## Important Reference Files

### Campaign Data
- **DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md** ⭐ AUTHORITATIVE SOURCE
  - Full name: Dave Biggers, Age 41
  - NOT married, NO children
  - Campaign budget: $1.2B (no new taxes)
  - 42 total policy documents (16 platform + 26 implementation)

### Deployment & Infrastructure
- **DEPLOYMENT_GUIDE.md** - WordPress deployment procedures
- **github_cicd_rest_api_setup_session_2025-10-21.md** - GitHub Actions setup
- **live_deployment_rest_api_session_2025-11-01.md** - REST API deployment process

### Quality Assurance Reports (Nov 3, 2025)
- **proofreading_report_20251103.md** - 24 content errors identified
- **punctuation_errors_report_20251103.md** - 20,060 formatting issues (3.6MB)
- **functional_testing_report_20251103.md** - 87 functional issues

---

## Tags & Topics

### Most Common Tags
- `wordpress` (47 files)
- `rundaverun` (47 files)
- `mcp-server` (8 files) ⭐ NEW
- `deployment` (15 files)
- `protocols` (12 files)
- `security` (10 files) ⭐ UPDATED
- `qa` (8 files)
- `bugfixes` (22 files)
- `integration` (8 files) ⭐ NEW
- `rest-api` (6 files)
- `github` (6 files) ⭐ UPDATED
- `github-actions` (5 files)

### Topics by Category

**Website Development:**
- WordPress customization
- Plugin development (dave-biggers-policy-manager)
- Theme customization (Astra child theme)
- Email system integration
- Volunteer management system

**Deployment & Infrastructure:**
- GitHub Actions CI/CD
- REST API integration
- SFTP/FileZilla transfers
- GoDaddy hosting configuration
- Database migrations

**Content & QA:**
- Proofreading & corrections
- Budget standardization
- Fact checking
- Link validation
- Accessibility improvements

**Tools & Automation:**
- Skippy script library (226+ scripts)
- Protocol system (18 protocols)
- Auto-transcription
- **MCP server development** ⭐ NEW
- **API integrations** (Pexels, Google Photos, Google Drive) ⭐ NEW
- **Security auditing** ⭐ NEW

**MCP Server & Integrations:** ⭐ NEW CATEGORY
- General-purpose MCP server (75 tools)
- Pexels stock photos integration
- Google Photos integration (pending OAuth)
- Google Drive management (13 tools)
- GitHub operations (3 tools)
- Slack notifications (2 tools)
- Browser automation (2 tools)

---

## Index Maintenance

**How to Update:**
- Run `/refresh-memory --rebuild` to regenerate from all conversation files
- Auto-updates when `/transcript` is executed (appends new entry)
- Manual edits can be made to this file as needed

**Index Statistics:**
- Files indexed: 116+
- Date range: August 2025 - November 2025
- Total size: ~100MB+ of conversations
- Projects tracked: 2 major, 5+ minor

---

## Notes

- This index uses an optimized quick-scan format
- For comprehensive analysis, use `/refresh-memory --rebuild`
- Keep this file updated as new conversations are created
- Tag taxonomy can be expanded as needed

**Next Index Rebuild:** When significant new sessions are added or on user request
