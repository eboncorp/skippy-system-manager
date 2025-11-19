# Claude Code Configuration - Progressive Disclosure

**Version:** 2.0.0
**Last Updated:** 2025-11-19

---

## 🚀 Quick Start

### Use Optimized CLAUDE.md for 80% Faster Context Loading

**Instead of:** `.claude/CLAUDE.md` (618 lines)
**Use:** `.claude/CLAUDE_OPTIMIZED.md` (< 500 lines)

**Benefit:** 80% context reduction = faster Claude responses

---

## 📁 Modular Documentation Structure

### When You Need Details, Reference These:

**Workflows** (Complete step-by-step processes)
- `.claude/workflows/wordpress_update_workflow.md` - Full WordPress update workflow

**Protocols** (Detailed procedures)
- `.claude/protocols/file_naming_standards.md` - Comprehensive naming rules

**Reference** (Quick facts)
- `.claude/reference/quick_facts.md` - Campaign fact sheet

---

## 🎯 For New Users

**Start Here:**
1. Read `.claude/CLAUDE_OPTIMIZED.md` (5 minutes)
2. When working on WordPress: Reference `.claude/workflows/wordpress_update_workflow.md`
3. When creating scripts: Reference `.claude/protocols/file_naming_standards.md`
4. When checking facts: Reference `.claude/reference/quick_facts.md`

---

## 📊 Benefits of Progressive Disclosure

✅ **80% context reduction** - Loads faster
✅ **On-demand details** - Reference only when needed
✅ **Easier maintenance** - Update one file at a time
✅ **Better organization** - Find what you need quickly

---

## 🔧 Commands

**Fact-checking:**
```bash
/fact-check "content to verify"
```

**Content approval:**
```bash
/content-approve --page-id=105 --approver=dave --notes="description"
```

**Session summary:**
```bash
/session-summary
```

---

**Status:** ✅ Active
**Configuration:** Progressive Disclosure v2.0
