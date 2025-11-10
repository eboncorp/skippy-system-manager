# Deployment Checklist - Quick Reference

**Protocol:** [Deployment Checklist Protocol](../../conversations/deployment_checklist_protocol.md)
**Priority:** HIGH
**Use:** Every production deployment

---

## 🚦 Pre-Flight Checklist

### Phase 1: Pre-Deployment (DO FIRST!)

- [ ] **Backup created**
  ```bash
  wp db export backup_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] **Changes tested locally**
  - Test on `rundaverun-local` first
  - Verify all functionality
  - Check mobile responsiveness

- [ ] **Fact-checked all data**
  - Verify against QUICK_FACTS_SHEET.md
  - No outdated statistics
  - All numbers current

- [ ] **Authorization obtained** (if needed)
  - Destructive operations require approval
  - Run `/authorize-claude` if applicable

- [ ] **Session directory created**
  ```bash
  SESSION="/home/dave/skippy/work/wordpress/rundaverun/$(date +%Y%m%d_%H%M%S)_deployment"
  mkdir -p "$SESSION"
  ```

---

## 🚀 Deployment Steps

### Step 1: Final Verification
```bash
# Check current state
wp option get siteurl
wp option get home
wp plugin list --status=active
wp theme list --status=active
```

### Step 2: Apply Changes
```bash
# Use WordPress Content Update Protocol
# Save before/after files in session directory
```

### Step 3: Immediate Verification
```bash
# Check site loads
curl -I https://davebiggers.com | head -1

# Check specific changes applied
wp post get [ID] --field=post_content | grep "new content"
```

### Step 4: Functional Testing
- [ ] Homepage loads
- [ ] Navigation works
- [ ] Forms submit
- [ ] Links work
- [ ] Mobile menu functions
- [ ] Search works

### Step 5: Performance Check
```bash
# Page load time
curl -o /dev/null -s -w "%{time_total}\n" https://davebiggers.com
```

---

## ✅ Post-Deployment Verification

### Immediate Checks (5 minutes)
- [ ] Site accessible
- [ ] No fatal errors
- [ ] Changes visible
- [ ] Core functionality works
- [ ] No console errors (F12)

### Detailed Checks (15 minutes)
- [ ] All pages load
- [ ] Forms work
- [ ] Images display
- [ ] Links work
- [ ] Mobile responsive
- [ ] Search functions
- [ ] Contact form delivers

### Browser Testing
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Mobile browser

---

## 📱 Mobile Testing

### Device Testing
- [ ] iPhone/iOS
- [ ] Android phone
- [ ] Tablet (if applicable)

### Functionality
- [ ] Menu opens/closes
- [ ] Forms work
- [ ] Touch targets adequate
- [ ] Text readable
- [ ] Images scale properly

---

## 🆘 Rollback Plan

### If Deployment Fails:

**Option 1: Revert Changes**
```bash
cd $SESSION
wp post update [ID] --post_content="$(cat page_[ID]_before.html)"
```

**Option 2: Restore Database**
```bash
wp db import backup_YYYYMMDD_HHMMSS.sql
```

**Option 3: Restore Files** (if files changed)
```bash
# Restore from backup location
cp -r backup_YYYYMMDD/* .
```

### Rollback Verification:
```bash
# Verify site works
curl -I https://davebiggers.com

# Check specific content reverted
wp post get [ID] --field=post_content | grep "original content"
```

---

## 📊 Deployment Report

Create in session directory:
```bash
cat > $SESSION/DEPLOYMENT_REPORT.md <<EOF
# Deployment Report - $(date +%Y-%m-%d)

## Changes Deployed
- [List changes]

## Verification Status
- [ ] Site accessible
- [ ] Changes applied
- [ ] Functionality verified
- [ ] Mobile tested
- [ ] Performance acceptable

## Issues Found
- [List any issues]

## Rollback Plan
- Backup location: [path]
- Rollback tested: [yes/no]

## Sign-off
- Deployed by: [name]
- Date: $(date)
- Status: [Success/Partial/Failed]
EOF
```

---

## 🚨 Emergency Procedures

### Site Down
1. Check error logs: `wp log list`
2. Check recent changes: `git log -5`
3. Rollback if needed
4. Contact support if persists

### Database Issues
1. Check DB connection: `wp db check`
2. Repair if needed: `wp db repair`
3. Restore from backup if corrupted

### Plugin Conflicts
1. Deactivate recent plugins
2. Test site
3. Reactivate one by one
4. Identify problematic plugin

---

## 📋 Common Deployment Types

### Content Update
- Use WordPress Content Update Protocol
- Verify with fact-checking
- Test on local first

### Plugin Update
- Backup first
- Test on local
- Update one at a time
- Verify functionality

### Theme Changes
- Child theme preferred
- Test thoroughly
- Have rollback ready

### Configuration Changes
- Document before state
- Make changes
- Verify immediately
- Document after state

---

## 📝 Deployment Types & Risk Levels

| Type | Risk | Backup Required | Testing Required |
|------|------|-----------------|------------------|
| Content Edit | Low | Optional | Local testing |
| Plugin Update | Medium | YES | Local + staging |
| Theme Change | High | YES | Extensive testing |
| Database Change | High | YES | Backup + testing |
| Config Change | Medium | YES | Immediate verify |

---

## 🔐 Security Considerations

Before deployment:
- [ ] No credentials in code
- [ ] No debug mode enabled
- [ ] Security plugins active
- [ ] SSL certificate valid
- [ ] File permissions correct

---

**Full Protocol:** conversations/deployment_checklist_protocol.md
**Related:** wordpress_content_update_protocol.md, emergency_rollback_protocol.md
