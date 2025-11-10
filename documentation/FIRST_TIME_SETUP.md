# First Time Setup Guide

**Purpose:** Setup and verify protocol system infrastructure
**Run this:** When using protocols in a new environment or after fresh install

---

## Quick Setup Checklist

- [ ] Verify directory structure
- [ ] Test wp-cli works
- [ ] Verify QUICK_FACTS_SHEET.md location
- [ ] Install cleanup cron job
- [ ] Test protocol violation checker
- [ ] Review CLAUDE.md
- [ ] Test session directory creation

---

## 1. Verify Directory Structure

```bash
# Check all required directories exist
for dir in \
  "/home/dave/skippy/work" \
  "/home/dave/skippy/work/wordpress/rundaverun" \
  "/home/dave/skippy/work/wordpress/rundaverun-local" \
  "/home/dave/skippy/work/scripts" \
  "/home/dave/skippy/conversations" \
  "/home/dave/skippy/claude/uploads" \
  "/home/dave/skippy/documentation/protocols" \
  "/home/dave/skippy/scripts"; do
  if [ -d "$dir" ]; then
    echo "✅ $dir"
  else
    echo "❌ $dir (creating...)"
    mkdir -p "$dir"
  fi
done
```

---

## 2. Test wp-cli

```bash
# Verify wp-cli installed
wp --version

# Test on local site
cd "/home/dave/Local Sites/rundaverun-local/app/public"
wp option get siteurl

# Should show: http://rundaverun-local.local
```

---

## 3. Verify QUICK_FACTS_SHEET.md

```bash
# Check fact sheet exists
FACT_SHEET="/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md"

if [ -f "$FACT_SHEET" ]; then
  echo "✅ Fact sheet found"
  head -10 "$FACT_SHEET"
else
  echo "❌ Fact sheet not found at expected location"
  echo "Search for it:"
  find /home/dave/rundaverun -name "QUICK_FACTS_SHEET.md"
fi
```

---

## 4. Install Cleanup Cron Job

```bash
# Check if cleanup script exists
if [ -f "/home/dave/skippy/scripts/cleanup_work_files.sh" ]; then
  echo "✅ Cleanup script found"

  # Add to crontab (runs daily at 3 AM)
  (crontab -l 2>/dev/null; echo "0 3 * * * /home/dave/skippy/scripts/cleanup_work_files.sh") | crontab -

  echo "✅ Cron job installed"
else
  echo "⚠️  Cleanup script not found"
  echo "Create it following Work Files Preservation Protocol"
fi
```

---

## 5. Test Protocol Violation Checker

```bash
# Run violation checker
bash /home/dave/skippy/scripts/monitoring/protocol_violation_checker_v1.0.0.sh 7

# Should generate report in conversations/
ls -la /home/dave/skippy/conversations/protocol_violations_*.md
```

---

## 6. Review Key Files

```bash
# CLAUDE.md
cat /home/dave/.claude/CLAUDE.md | head -50

# Protocol Quick Reference
cat /home/dave/skippy/documentation/PROTOCOL_QUICK_REFERENCE.md

# Protocols README
cat /home/dave/skippy/documentation/protocols/README.md | head -100
```

---

## 7. Test Session Directory Creation

```bash
# Test creating a session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/rundaverun-local/$(date +%Y%m%d_%H%M%S)_test_setup"
mkdir -p "$SESSION_DIR"

if [ -d "$SESSION_DIR" ]; then
  echo "✅ Session directory created: $SESSION_DIR"

  # Create test README
  cat > "$SESSION_DIR/README.md" <<EOF
# Test Setup Session
Created during first-time setup
Date: $(date)
Status: ✅ Test successful
EOF

  echo "✅ Test README created"
  cat "$SESSION_DIR/README.md"
else
  echo "❌ Failed to create session directory"
fi
```

---

## 8. Verify Git Hook Installed

```bash
# Check pre-commit hook
if [ -f "/home/dave/skippy/.git/hooks/pre-commit" ]; then
  echo "✅ Pre-commit hook installed"
else
  echo "⚠️  Pre-commit hook not found"
  echo "Install from protocol documentation"
fi
```

---

## Setup Complete Checklist

After running all steps:
- [ ] All directories exist
- [ ] wp-cli works on local site
- [ ] QUICK_FACTS_SHEET.md found and accessible
- [ ] Cleanup cron job installed
- [ ] Protocol violation checker runs successfully
- [ ] Test session directory created
- [ ] Git pre-commit hook installed
- [ ] All key protocol files reviewed

---

## Next Steps

1. **Read these protocols first:**
   - CLAUDE.md
   - Protocol Quick Reference
   - WordPress Content Update Protocol
   - Fact-Checking Protocol

2. **Test on a simple task:**
   - Make a minor update to rundaverun-local
   - Follow all 7 steps
   - Verify protocol compliance

3. **Run weekly protocol checker:**
   ```bash
   bash /home/dave/skippy/scripts/monitoring/protocol_violation_checker_v1.0.0.sh 7
   ```

---

**Setup Date:** $(date)
**Environment:** Ready for Protocol-Compliant Work
