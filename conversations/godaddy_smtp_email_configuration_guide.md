# GoDaddy SMTP Configuration for rundaverun.org

## Manual Configuration Steps (Production)

After deploying to GoDaddy, configure WP Mail SMTP:

### 1. Access WP Mail SMTP Settings
- Log into WordPress admin
- Go to: **WP Mail SMTP → Settings**

### 2. Select Mailer
- Choose: **Other SMTP**

### 3. SMTP Configuration

**From Email:** dave@rundaverun.org
**From Name:** Dave Biggers for Mayor
**Force From Email:** Yes (checked)
**Force From Name:** Yes (checked)

**SMTP Host:** smtp.secureserver.net
**SMTP Port:** 465
**Encryption:** SSL

**Authentication:** ON (enabled)
**SMTP Username:** dave@rundaverun.org
**SMTP Password:** [Your GoDaddy email password]

### 4. Alternative Configuration (if Office 365)

If your GoDaddy email is through Office 365:

**SMTP Host:** smtp.office365.com
**SMTP Port:** 587
**Encryption:** TLS

**SMTP Username:** dave@rundaverun.org
**SMTP Password:** [Your Office 365 password]

### 5. Test Email

After configuration:
1. Go to: **WP Mail SMTP → Email Test**
2. Send test email to: davidbiggers@yahoo.com
3. Verify receipt

### 6. Update Admin Email (if needed)

Go to: **Settings → General**
- Admin Email Address: dave@rundaverun.org (or keep davidbiggers@yahoo.com)

---

## Benefits of This Configuration

✅ **Reliable Delivery:** SMTP authentication ensures emails reach inbox
✅ **SPF/DKIM:** GoDaddy handles email authentication automatically
✅ **No Spam Flags:** Emails sent from authorized server
✅ **Error Logging:** WP Mail SMTP logs all email attempts
✅ **Delivery Reports:** Track which emails were sent successfully

---

## Affected Systems

This configuration will handle email for:
- Contact Form 7 submissions
- Newsletter signups (double opt-in confirmation)
- Volunteer registration confirmations
- Newsletter sends (via custom plugin)
- WordPress admin notifications

---

## Security Notes

- NEVER commit SMTP password to version control
- Use SSL/TLS encryption for all SMTP connections
- Consider separate email for admin notifications vs. public-facing emails
- Enable 2FA on your GoDaddy email account

---

## Troubleshooting

**If emails still don't send:**
1. Verify SMTP credentials in GoDaddy cPanel
2. Check WP Mail SMTP → Email Log for errors
3. Confirm port 465 (SSL) or 587 (TLS) not blocked by host
4. Try alternative port (465 ↔ 587)
5. Confirm email account has sending permissions

**Common Issues:**
- Wrong port/encryption combination
- Password typo or special characters
- Account not activated in GoDaddy
- Firewall blocking SMTP ports
- Daily sending limits exceeded

---

## Current Local Configuration

On local development, WP Mail SMTP is installed but NOT configured.
This is intentional - email won't work locally but will work on production after configuration.

---

**Created:** November 3, 2025
**For:** rundaverun.org production deployment
