# API Key Lifecycle Protocol

**Version**: 1.0.0
**Last Updated**: 2025-11-16
**Owner**: Security Administration

---

## Context

This protocol manages the complete lifecycle of API keys, tokens, and credentials used across all systems. Proper key management prevents security breaches, service interruptions, and unauthorized access.

## Purpose

- Track all API keys and their expiration dates
- Enforce regular key rotation
- Prevent unauthorized key usage
- Maintain audit trail of key access
- Enable rapid response to compromised keys

---

## Key Inventory

### Current API Keys (Store securely, update regularly)

```
Location: /home/dave/skippy/.credentials/
Backup: Encrypted in password manager

1. Google Photos OAuth Token
   - File: google_photos_token.json
   - Scope: photospicker.mediaitems.readonly
   - Expires: Check token file
   - Rotation: 90 days

2. GitHub Personal Access Token
   - Variable: GITHUB_TOKEN
   - Scopes: repo, workflow
   - Expires: Set in GitHub settings
   - Rotation: 90 days

3. Pexels API Key
   - File: .env (PEXELS_API_KEY)
   - Type: Permanent (no expiration)
   - Rotation: On compromise only

4. WordPress Application Passwords
   - Location: WordPress user settings
   - Users: admin, api-user
   - Rotation: 180 days

5. Google Drive OAuth Token
   - File: google_drive_token.json
   - Scope: drive.readonly
   - Expires: Check token file
   - Rotation: 90 days
```

---

## Key Lifecycle Phases

### 1. Generation
- Use cryptographically secure random generation
- Minimum 32 characters for API keys
- Include uppercase, lowercase, numbers
- Never include special characters that need escaping

### 2. Distribution
- Never commit to git
- Store in .env files with 600 permissions
- Use environment variables in code
- Encrypt at rest where possible

### 3. Rotation Schedule

| Key Type | Rotation Period | Alert Days Before |
|----------|-----------------|-------------------|
| OAuth Tokens | 90 days | 14, 7, 1 |
| API Keys | 180 days | 30, 14, 7 |
| Database Passwords | 365 days | 60, 30, 14 |
| WordPress Salts | 365 days | 60 |
| SSH Keys | 365 days | 60 |

### 4. Revocation
- Immediate on compromise
- Remove from all locations
- Audit recent usage
- Generate replacement immediately
- Update all dependent services

### 5. Archival
- Document retired keys (hash only)
- Record rotation date and reason
- Maintain audit log for 2 years

---

## Key Rotation Procedure

### Step 1: Pre-Rotation Preparation
```bash
# 1. Identify services using the key
grep -r "API_KEY_NAME" /home/dave/skippy/

# 2. Create backup of current configuration
cp /home/dave/skippy/.credentials/.env \
   /home/dave/skippy/.credentials/.env.backup.$(date +%Y%m%d)

# 3. Document current key (hash only, never full key)
echo "OLD_KEY_HASH=$(echo -n "$OLD_KEY" | sha256sum | cut -d' ' -f1)" >> rotation_log.txt
```

### Step 2: Generate New Key
```bash
# For random API keys
NEW_KEY=$(openssl rand -base64 32 | tr -d '=/+' | cut -c1-40)

# For GitHub tokens
# Go to: https://github.com/settings/tokens/new

# For Google OAuth
# Re-run OAuth flow to get new refresh token
```

### Step 3: Update Configuration
```bash
# Update .env file
sed -i "s/OLD_KEY/NEW_KEY/g" /home/dave/skippy/.credentials/.env

# Update environment
source /home/dave/skippy/.credentials/.env

# Verify new key works
# Run test specific to the service
```

### Step 4: Verify Functionality
```bash
# Test API connection with new key
curl -H "Authorization: Bearer $NEW_KEY" https://api.service.com/test

# Check all dependent services
bash /home/dave/skippy/scripts/system/test_all_integrations.sh
```

### Step 5: Revoke Old Key
```bash
# After confirming new key works (24-48 hour grace period)
# Revoke old key in service provider dashboard

# Document revocation
echo "$(date): Revoked old key for SERVICE_NAME" >> /home/dave/skippy/logs/key_rotation.log
```

---

## Automated Key Expiration Monitoring

```bash
#!/bin/bash
# key_expiration_monitor.sh

CREDENTIALS_DIR="/home/dave/skippy/.credentials"
ALERT_FILE="/home/dave/skippy/conversations/key_expiration_alert.md"

echo "# API Key Expiration Report" > "$ALERT_FILE"
echo "**Generated:** $(date)" >> "$ALERT_FILE"
echo "" >> "$ALERT_FILE"

# Check Google Photos token
if [ -f "$CREDENTIALS_DIR/google_photos_token.json" ]; then
    EXPIRY=$(python3 -c "
import json
with open('$CREDENTIALS_DIR/google_photos_token.json') as f:
    data = json.load(f)
    print(data.get('expiry', 'No expiry found'))
" 2>/dev/null)
    echo "- Google Photos Token: $EXPIRY" >> "$ALERT_FILE"
fi

# Check GitHub token (from environment or file)
if [ -n "$GITHUB_TOKEN" ]; then
    # Test if token is still valid
    if curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -q "login"; then
        echo "- GitHub Token: Valid (check rotation date manually)" >> "$ALERT_FILE"
    else
        echo "- **WARNING**: GitHub Token: INVALID or EXPIRED" >> "$ALERT_FILE"
    fi
fi

# List .env file modification date
ENV_AGE=$(stat -c %Y "$CREDENTIALS_DIR/.env" 2>/dev/null)
ENV_DAYS=$(( ($(date +%s) - ENV_AGE) / 86400 ))
if [ "$ENV_DAYS" -gt 90 ]; then
    echo "- **WARNING**: .env file is $ENV_DAYS days old (consider rotation)" >> "$ALERT_FILE"
else
    echo "- .env file age: $ENV_DAYS days" >> "$ALERT_FILE"
fi

echo "" >> "$ALERT_FILE"
echo "## Recommended Actions" >> "$ALERT_FILE"
if grep -q "WARNING" "$ALERT_FILE"; then
    echo "- Review and rotate keys marked as WARNING" >> "$ALERT_FILE"
    echo "- Update key_rotation.log after rotation" >> "$ALERT_FILE"
fi

echo "Report saved: $ALERT_FILE"
```

---

## Emergency Key Compromise Response

### Immediate Actions (Within 15 minutes)
1. **Revoke compromised key** in service provider dashboard
2. **Generate new key** using secure method
3. **Update all configurations** with new key
4. **Audit access logs** for unauthorized usage
5. **Notify affected parties** if user data accessed

### Investigation (Within 24 hours)
1. Determine how key was compromised
2. Check git history for accidental commits
3. Review access logs for anomalies
4. Scan for key exposure in public sources

### Prevention
1. Add pre-commit hook to detect key patterns
2. Enable secret scanning on GitHub
3. Review .gitignore comprehensiveness
4. Rotate all potentially exposed keys

---

## Secure Storage Best Practices

### DO:
```bash
# Store in .env with restricted permissions
chmod 600 /home/dave/skippy/.credentials/.env
chmod 700 /home/dave/skippy/.credentials/

# Use environment variables
export API_KEY=$(grep API_KEY .env | cut -d'=' -f2)

# Reference variables in code
PEXELS_KEY = os.getenv("PEXELS_API_KEY")

# Keep .credentials in .gitignore
echo "/.credentials/" >> .gitignore
```

### DON'T:
```bash
# Never hardcode keys
API_KEY = "sk_live_abc123..."  # BAD!

# Never commit to git
git add .env  # BAD!

# Never log keys
print(f"Using key: {API_KEY}")  # BAD!

# Never share via unencrypted channels
```

---

## Key Access Audit

### Weekly Review
- Check who/what accessed keys
- Review failed authentication attempts
- Monitor key usage patterns
- Verify key scopes are minimal

### Audit Log Format
```
/home/dave/skippy/logs/key_access.log

Format: [TIMESTAMP] [KEY_NAME] [ACTION] [SERVICE] [RESULT]
Example: 2025-11-16T03:15:42Z GITHUB_TOKEN API_CALL gh_repo_list SUCCESS
```

---

## Integration with Other Protocols

- **Secret Rotation Protocol**: Extends with lifecycle management
- **Incident Response Protocol**: Key compromise is security incident
- **Health Check Protocol**: Include key validity in health checks
- **Git Workflow Protocol**: Pre-commit hooks for key detection

---

## Quick Reference

```bash
# Check key expiration
python3 -c "import json; print(json.load(open('.credentials/token.json'))['expiry'])"

# Generate secure key
openssl rand -base64 32

# List credential files
ls -la ~/.credentials/

# Test GitHub token
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | jq .login

# Test Pexels key
curl -s -H "Authorization: $PEXELS_API_KEY" "https://api.pexels.com/v1/curated" | jq .total_results

# Rotate reminder
echo "REMINDER: Check key rotation schedule monthly"
```

---

**Generated**: 2025-11-16
**Status**: Active
**Next Review**: 2025-12-16
