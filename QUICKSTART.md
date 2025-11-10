# 🚀 Skippy System Manager - Quick Start Guide

**Welcome!** This guide will get you oriented in 5 minutes.

---

## 📍 You Are Here

**Repository:** `skippy-system-manager`
**Purpose:** Protocol-driven system management and automation
**Primary Focus:** WordPress campaign site management, security, operations

---

## 🎯 First Steps (2 minutes)

### 1. Understand the Structure

```
skippy-system-manager/
├── documentation/
│   ├── protocols/           ← 27 active protocols (PRIMARY)
│   ├── quick-references/    ← One-page cheat sheets
│   └── PROTOCOL_GOVERNANCE.md
├── conversations/
│   ├── *protocol*.md        ← 25 legacy protocols (still valid)
│   ├── sessions/            ← Historical work sessions
│   └── reports/             ← Audit reports
├── scripts/
│   ├── utility/             ← Protocol validation, search tools
│   └── ...                  ← 226+ utility scripts
└── claude/uploads/          ← Protocol packages for Claude.ai
```

### 2. Know the Key Files

**Start with these:**
- **This file** - You're reading it now!
- `conversations/PROTOCOL_INDEX.md` - Master catalog (52 protocols)
- `documentation/protocols/README.md` - Protocol guide
- `PROTOCOL_IMPROVEMENTS_COMPLETE_2025-11-10.md` - Recent improvements

---

## 📚 Essential Protocols (Know These First)

### 🔥 CRITICAL (Must follow always)

1. **[WordPress Content Update](documentation/protocols/wordpress_content_update_protocol.md)**
   - 7-step mandatory process
   - Never use /tmp/
   - Always verify changes
   - Quick ref: `documentation/quick-references/wordpress_content_update_quick_ref.md`

2. **[Fact-Checking](documentation/protocols/fact_checking_protocol.md)**
   - Verify all numbers before publishing
   - Master source: `QUICK_FACTS_SHEET.md`
   - Quick ref: `documentation/quick-references/fact_checking_quick_ref.md`

3. **[Git Workflow](documentation/protocols/git_workflow_protocol.md)**
   - Safety rules (never force push to main!)
   - Commit message standards
   - Quick ref: `documentation/quick-references/git_workflow_quick_ref.md`

### ⭐ HIGH (Use frequently)

4. **[Deployment Checklist](conversations/deployment_checklist_protocol.md)**
   - Pre-flight checks
   - Post-deployment verification
   - Quick ref: `documentation/quick-references/deployment_checklist_quick_ref.md`

5. **[Emergency Rollback](documentation/protocols/emergency_rollback_protocol.md)**
   - When deployment goes wrong
   - Site down procedures
   - Quick ref: `documentation/quick-references/emergency_rollback_quick_ref.md`

---

## 🔧 Essential Tools (Use These)

### Protocol Search Tool
```bash
# Find protocols quickly
bash scripts/utility/search_protocols_v2.0.0.sh wordpress
bash scripts/utility/search_protocols_v2.0.0.sh --category security
bash scripts/utility/search_protocols_v2.0.0.sh --help
```

### Protocol Validation
```bash
# Check protocol system health
bash scripts/utility/validate_protocols_v2.0.0.sh
```

### Quick References
```bash
# One-page cheat sheets
ls documentation/quick-references/
cat documentation/quick-references/wordpress_content_update_quick_ref.md
```

---

## 📋 Common Tasks

### WordPress Update
```bash
# 1. Create session directory
SESSION="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_description"
mkdir -p "$SESSION"

# 2. Follow 7-step process (see quick ref)
cat documentation/quick-references/wordpress_content_update_quick_ref.md
```

### Find a Protocol
```bash
# Option 1: Search
bash scripts/utility/search_protocols_v2.0.0.sh backup

# Option 2: Browse index
cat conversations/PROTOCOL_INDEX.md

# Option 3: List by location
ls documentation/protocols/        # Primary (27)
ls conversations/*protocol*.md     # Legacy (25)
```

### Validate System
```bash
# Check health
bash scripts/utility/validate_protocols_v2.0.0.sh

# Expected output:
# - Documentation: ✅ 27/27 (100%)
# - Conversations: ⚠️ 5/25 (20%)
# - Overall: 62% header compliance
```

---

## 🎓 Learning Path (15 minutes)

### Day 1: WordPress Work (5 min)
1. Read: `documentation/quick-references/wordpress_content_update_quick_ref.md`
2. Read: `documentation/quick-references/fact_checking_quick_ref.md`
3. Bookmark: Master index at `conversations/PROTOCOL_INDEX.md`

### Week 1: Core Operations (10 min)
1. Read: `documentation/quick-references/git_workflow_quick_ref.md`
2. Read: `documentation/quick-references/deployment_checklist_quick_ref.md`
3. Scan: `documentation/protocols/README.md` for full protocol list

### Month 1: Deep Dive (Optional)
1. Review: `documentation/PROTOCOL_GOVERNANCE.md` - How protocols work
2. Explore: `conversations/PROTOCOL_INDEX.md` - All 52 protocols categorized
3. Read: Protocols relevant to your work

---

## 🗺️ Protocol Categories

**52 protocols organized into 8 categories:**

1. **🔒 Security & Access** (10) - authorization, secrets, access control
2. **🚀 Operations** (10) - monitoring, incidents, health checks
3. **💻 Development** (7) - git, debugging, scripts, testing
4. **🚢 Deployment** (5) - publishing, WordPress, configuration
5. **📊 Data & Content** (6) - backups, migrations, retention
6. **📝 Documentation** (7) - standards, reports, knowledge transfer
7. **⚙️ System** (4) - automation, diagnostics, tooling
8. **🆕 Workflow** (3) - sessions, verification, processes

**Full list:** `conversations/PROTOCOL_INDEX.md`

---

## 🚨 Emergency Procedures

### Site Down?
```bash
# Quick reference card has full procedure
cat documentation/quick-references/emergency_rollback_quick_ref.md

# Key steps:
# 1. Check if WP-CLI accessible
# 2. Deactivate recent changes
# 3. Restore from backup if needed
# 4. Verify site is back
```

### Need to Rollback?
```bash
# Find your session directory
ls -lt /home/dave/skippy/work/wordpress/rundaverun/ | head -5

# Revert content
cd [session-dir]
wp post update [ID] --post_content="$(cat page_[ID]_before.html)"
```

### Can't Find Something?
```bash
# Search tool is your friend
bash scripts/utility/search_protocols_v2.0.0.sh [keyword]

# Or check the index
grep -i "[keyword]" conversations/PROTOCOL_INDEX.md
```

---

## 💡 Pro Tips

### 1. Keep Quick Refs Open
```bash
# Keep these open in editor tabs for daily use:
code documentation/quick-references/wordpress_content_update_quick_ref.md
code documentation/quick-references/fact_checking_quick_ref.md
code documentation/quick-references/git_workflow_quick_ref.md
```

### 2. Use Session Directories
```bash
# NEVER use /tmp/ - always create session directories
SESSION="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_task"
mkdir -p "$SESSION"
cd "$SESSION"
```

### 3. Verify Everything
```bash
# After WordPress update, ALWAYS:
wp post get [ID] --field=post_content > page_[ID]_after.html
diff page_[ID]_final.html page_[ID]_after.html
```

### 4. Search Before Creating
```bash
# Before creating new protocol, search if it exists
bash scripts/utility/search_protocols_v2.0.0.sh [topic]
```

---

## 📊 System Health Dashboard

**Current Status:** A- (90%)
- ✅ 52 active protocols
- ✅ 0 duplicates
- ✅ Clear organization
- ✅ Comprehensive tooling
- ⚠️ 62% header compliance (target: 100%)

**Check health anytime:**
```bash
bash scripts/utility/validate_protocols_v2.0.0.sh
```

---

## 🔗 Important Locations

### Documentation
- **Protocols:** `documentation/protocols/` (27 - PRIMARY)
- **Quick Refs:** `documentation/quick-references/` (5 cards)
- **Governance:** `documentation/PROTOCOL_GOVERNANCE.md`

### Conversations
- **Legacy Protocols:** `conversations/*protocol*.md` (25 - still valid)
- **Master Index:** `conversations/PROTOCOL_INDEX.md` ⭐
- **Sessions:** `conversations/sessions/2025/`
- **Reports:** `conversations/reports/`

### Scripts
- **Validation:** `scripts/utility/validate_protocols_v2.0.0.sh`
- **Search:** `scripts/utility/search_protocols_v2.0.0.sh`
- **Full List:** `scripts/README.md` (see all 226+ scripts)

### Work Directories
- **WordPress Work:** `/home/dave/skippy/work/wordpress/`
- **Script Work:** `/home/dave/skippy/work/scripts/`
- **Archive:** `/home/dave/skippy/work/archive/` (auto-archived after 30 days)

---

## ❓ FAQ

### Q: Which protocol location should I use?
**A:** Prefer `documentation/protocols/` for new work. Legacy protocols in `conversations/` are still valid but being gradually migrated.

### Q: How do I know if a protocol is critical?
**A:** Check the Priority field in the protocol header, or look at the "Critical Protocols" section in `conversations/PROTOCOL_INDEX.md`.

### Q: What's the difference between protocols and quick references?
**A:** Protocols are comprehensive (full procedures, examples, context). Quick references are one-page cheat sheets for daily use.

### Q: Can I create new protocols?
**A:** Yes! Follow the process in `documentation/PROTOCOL_GOVERNANCE.md`. Use `documentation/protocols/PROTOCOL_TEMPLATE.md` as your starting point.

### Q: Where do I report protocol issues?
**A:** Contact the Protocol Owner (listed in protocol header), or open an issue in the tracker.

### Q: How often are protocols reviewed?
**A:** CRITICAL protocols monthly, HIGH quarterly, MEDIUM semi-annually, LOW annually. See `documentation/PROTOCOL_GOVERNANCE.md` for details.

---

## 🎯 Success Checklist

After reading this guide, you should be able to:

- [ ] Find protocols using search tool
- [ ] Locate quick reference cards
- [ ] Follow WordPress update process
- [ ] Verify fact-checking sources
- [ ] Use session directories (not /tmp/)
- [ ] Check system health with validation tool
- [ ] Know where to find emergency procedures
- [ ] Understand protocol categories

**If you can check all boxes, you're ready to go!** 🚀

---

## 📞 Getting Help

### Protocol Questions
1. Check relevant quick reference card
2. Read full protocol
3. Search for related protocols
4. Check master index for context

### Tool Usage
```bash
# All tools have --help
bash scripts/utility/search_protocols_v2.0.0.sh --help
bash scripts/utility/validate_protocols_v2.0.0.sh --help
```

### System Issues
1. Check `conversations/reports/` for recent audits
2. Run validation tool
3. Review emergency procedures
4. Contact Protocol Working Group (if established)

---

## 🚀 Next Steps

**Immediate (Today):**
1. ✅ Bookmark this file
2. ✅ Open quick reference cards for your work
3. ✅ Try the search tool

**This Week:**
1. Read protocols relevant to your work
2. Run validation tool to see system health
3. Create a session directory for your next task

**This Month:**
1. Review governance document
2. Explore all protocol categories
3. Consider joining Protocol Working Group (if formed)

---

## 📈 Recent Improvements (2025-11-10)

The system just received major upgrades:
- ✅ All duplicates resolved
- ✅ New validation & search tools (v2.0.0)
- ✅ 5 quick reference cards created
- ✅ Comprehensive governance document
- ✅ Master index with 52 protocols
- ✅ Grade improved from B+ (85%) to A- (90%)

**Full details:** `PROTOCOL_IMPROVEMENTS_COMPLETE_2025-11-10.md`

---

## 🎉 You're Ready!

**Time to get started:** ~5 minutes ✅
**Essential protocols known:** 5 ✅
**Tools available:** 2 search + validation ✅
**Quick references:** 5 one-page guides ✅

**Pick a task and start using the protocols!**

Need something? Search for it:
```bash
bash scripts/utility/search_protocols_v2.0.0.sh [your-topic]
```

---

**Last Updated:** 2025-11-10
**Version:** 1.0.0
**Questions?** Check `conversations/PROTOCOL_INDEX.md` or `documentation/PROTOCOL_GOVERNANCE.md`
