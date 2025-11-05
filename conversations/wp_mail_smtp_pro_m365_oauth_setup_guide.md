# WP Mail SMTP Pro + Microsoft 365 OAuth Configuration Guide
**Campaign:** Dave Biggers for Mayor (rundaverun.org)  
**Created:** November 3, 2025  
**Email System:** Microsoft 365 (GoDaddy hosted) with Multi-Factor Authentication

---

## Why WP Mail SMTP Pro is Required

Your situation requires the Pro version because:

✅ **Microsoft 365 email with Multi-Factor Authentication (MFA) enabled**  
✅ **OAuth authentication required** (Basic Auth won't work with MFA)  
✅ **Future-proof** (Microsoft retiring Basic Auth March-April 2026)  
✅ **More secure** (no password stored in WordPress)  
✅ **Professional reliability** for campaign email delivery

**Cost:** $49-99/year (Essential or Plus plan recommended)

---

## Pre-Deployment Preparation (Do This First)

### Step 1: Purchase WP Mail SMTP Pro

1. Go to: https://wpmailsmtp.com/pricing/
2. Choose plan:
   - **Essential ($49/year):** Supports 1 site, includes Outlook mailer
   - **Plus ($99/year):** Supports 3 sites, includes priority support
3. Complete purchase
4. Download the Pro plugin ZIP file
5. Save your license key (you'll need this)

### Step 2: Create Microsoft Azure App Registration

**Important:** This MUST be done before configuring the plugin on production.

1. **Log into Microsoft Azure Portal:**
   - Go to: https://portal.azure.com/
   - Sign in with your GoDaddy/Microsoft 365 admin account

2. **Navigate to App Registrations:**
   - Search for "App registrations" in the top search bar
   - Click "App registrations"
   - Click "+ New registration"

3. **Register the Application:**
   - **Name:** `rundaverun.org WP Mail SMTP`
   - **Supported account types:** Select "Accounts in this organizational directory only"
   - **Redirect URI:** 
     - Type: Web
     - URI: `https://rundaverun.org/wp-admin/admin.php?page=wp-mail-smtp`
   - Click "Register"

4. **Copy Application (client) ID:**
   - After registration, you'll see the app overview page
   - Copy the "Application (client) ID" (looks like: `12345678-1234-1234-1234-123456789abc`)
   - Save this - you'll need it later

5. **Copy Directory (tenant) ID:**
   - On the same overview page
   - Copy the "Directory (tenant) ID"
   - Save this as well

6. **Create a Client Secret:**
   - In left sidebar, click "Certificates & secrets"
   - Click "+ New client secret"
   - Description: `WP Mail SMTP Secret`
   - Expires: Choose "24 months" (or custom)
   - Click "Add"
   - **IMMEDIATELY copy the "Value"** (it will only show once!)
   - Save this secret securely

7. **Set API Permissions:**
   - In left sidebar, click "API permissions"
   - Click "+ Add a permission"
   - Select "Microsoft Graph"
   - Select "Delegated permissions"
   - Search for and add:
     - `Mail.Send` (Send mail as a user)
     - `User.Read` (Sign in and read user profile)
   - Click "Add permissions"
   - Click "Grant admin consent for [your organization]"
   - Click "Yes" to confirm

**Save These Values:**
```
Application (client) ID: [your-client-id]
Directory (tenant) ID: [your-tenant-id]
Client Secret Value: [your-secret-value]
License Key: [your-wp-mail-smtp-pro-license]
```

---

## Production Deployment Steps

### Step 1: Install WP Mail SMTP Pro on Production

1. **Access Production WordPress Admin:**
   - Go to: https://rundaverun.org/wp-admin/
   - Log in with admin credentials

2. **Remove Free Version (if installed):**
   - Go to: Plugins → Installed Plugins
   - Find "WP Mail SMTP by WPForms"
   - Click "Deactivate" then "Delete"

3. **Upload Pro Version:**
   - Go to: Plugins → Add New
   - Click "Upload Plugin"
   - Choose the Pro ZIP file you downloaded
   - Click "Install Now"
   - Click "Activate Plugin"

4. **Enter License Key:**
   - You'll be prompted for your license key
   - Paste your license key
   - Click "Verify Key"

### Step 2: Configure Microsoft 365 OAuth Settings

1. **Access WP Mail SMTP Settings:**
   - Go to: WP Mail SMTP → Settings

2. **From Email Configuration:**
   - **From Email:** `dave@rundaverun.org`
   - **From Name:** `Dave Biggers for Mayor`
   - **Force From Email:** ✓ Checked
   - **Force From Name:** ✓ Checked

3. **Select Mailer:**
   - Choose: **Outlook** (NOT "Other SMTP"!)
   - This enables OAuth authentication

4. **Microsoft OAuth Configuration:**
   - **Application (client) ID:** [paste your client ID from Azure]
   - **Application Password:** [paste your client secret from Azure]
   - **Redirect URI:** Should auto-populate as:
     ```
     https://rundaverun.org/wp-admin/admin.php?page=wp-mail-smtp
     ```
   - Verify this matches the URI you registered in Azure

5. **Save Settings:**
   - Click "Save Settings" at the bottom

### Step 3: Authorize Microsoft 365 Connection

1. **Click "Allow plugin to send emails using your Microsoft account":**
   - This button appears after saving settings
   - You'll be redirected to Microsoft login

2. **Microsoft Login Flow:**
   - Enter your Microsoft 365 credentials (dave@rundaverun.org)
   - Complete MFA authentication (text code, app approval, etc.)
   - Review permissions requested:
     - Send mail as you
     - Maintain access to data you have given it access to
     - Sign in and read your profile
   - Click "Accept"

3. **Verify Connection:**
   - You'll be redirected back to WordPress
   - Should see: "Microsoft account has been successfully connected"
   - Green checkmark next to "Authentication Status"

### Step 4: Test Email Delivery

1. **Go to Email Test Tab:**
   - WP Mail SMTP → Tools → Email Test

2. **Send Test Email:**
   - **Send To:** `davidbiggers@yahoo.com`
   - **Subject:** Leave default or enter: "Test from rundaverun.org"
   - Click "Send Email"

3. **Verify Success:**
   - Should see: "Email was sent successfully!"
   - Check davidbiggers@yahoo.com inbox
   - Verify email arrived from dave@rundaverun.org
   - Check spam folder if not in inbox

4. **Check Email Log:**
   - Go to: WP Mail SMTP → Email Log
   - Verify test email appears with status "Sent"

---

## What This Configuration Handles

Once configured, OAuth authentication will handle email for:

✅ **Contact Form 7 submissions** → dave@rundaverun.org  
✅ **Newsletter signup confirmations** (double opt-in emails)  
✅ **Volunteer registration confirmations**  
✅ **Newsletter sends** (via custom plugin)  
✅ **WordPress admin notifications**  
✅ **Password reset emails**

---

## Troubleshooting

### Issue: "Could not authenticate your SMTP account"

**Possible Causes:**
1. Client ID or Secret incorrect/expired
2. Redirect URI mismatch between Azure and WordPress
3. API permissions not granted in Azure
4. MFA blocking programmatic access

**Solutions:**
1. Verify Client ID and Secret match Azure exactly
2. Regenerate Client Secret in Azure if needed
3. Verify Redirect URI matches exactly (including HTTPS)
4. Ensure admin consent was granted for API permissions
5. Check Azure app is not disabled

### Issue: "The redirect URI specified in the request does not match"

**Solution:**
1. Go to Azure Portal → App registrations → Your app
2. Click "Authentication" in left sidebar
3. Under "Redirect URIs," verify:
   ```
   https://rundaverun.org/wp-admin/admin.php?page=wp-mail-smtp
   ```
4. Must be exact match (HTTP vs HTTPS, trailing slashes, etc.)
5. Click "Save" if you made changes
6. Try authorizing again in WordPress

### Issue: "Authorization prompt never appears"

**Solution:**
1. Clear browser cache and cookies
2. Try different browser or incognito mode
3. Disable browser popup blockers
4. Check WordPress site is using HTTPS (not HTTP)

### Issue: Test email succeeds but form emails don't send

**Solution:**
1. Check WP Mail SMTP → Email Log for error messages
2. Verify Contact Form 7 is set to use WordPress mail (not own SMTP)
3. Clear all WordPress caches
4. Test individual form (not just email test page)

### Issue: Emails going to spam

**Solutions:**
1. **Verify SPF record** in GoDaddy DNS:
   - Should include Microsoft's servers
   - Example: `v=spf1 include:spf.protection.outlook.com ~all`

2. **Verify DKIM is enabled:**
   - GoDaddy handles this automatically for M365
   - Check: GoDaddy → Email → Email Settings → DKIM

3. **Check DMARC record:**
   - Add TXT record: `_dmarc.rundaverun.org`
   - Value: `v=DMARC1; p=quarantine; rua=mailto:dave@rundaverun.org`

4. **Warm up sending reputation:**
   - Start with low volume
   - Gradually increase over 2-3 weeks
   - Avoid sudden high-volume sends

---

## Security Best Practices

### Protect Your Credentials

1. **Never share Client Secret publicly**
   - Not in version control
   - Not in screenshots
   - Not in support tickets (unless encrypted)

2. **Rotate Client Secret annually:**
   - Azure Portal → Your app → Certificates & secrets
   - Create new secret
   - Update in WP Mail SMTP settings
   - Delete old secret after verification

3. **Enable Azure app activity monitoring:**
   - Review sign-in logs periodically
   - Set up alerts for suspicious activity

4. **Use strong WordPress admin passwords:**
   - Since OAuth credentials are stored in database
   - Enable WordPress 2FA if possible

### WordPress Security

1. **Keep WP Mail SMTP Pro updated:**
   - Updates often include security patches
   - Enable auto-updates if available

2. **Limit admin access:**
   - Only trusted users should access WP Mail SMTP settings
   - Use role-based access control

3. **Regular backups:**
   - Backup WordPress database (includes OAuth tokens)
   - Test restoration process

---

## Monitoring & Maintenance

### Regular Checks (Weekly)

1. **Email Log Review:**
   - WP Mail SMTP → Email Log
   - Check for failed sends
   - Monitor delivery rates

2. **Test Email Sends:**
   - Send test email weekly
   - Verify delivery to different providers (Gmail, Yahoo, Outlook)

3. **Form Functionality:**
   - Test contact form submissions
   - Verify confirmation emails arrive

### Monthly Checks

1. **Azure App Health:**
   - Log into Azure Portal
   - Review app sign-in logs
   - Check for errors or unauthorized access

2. **Client Secret Expiration:**
   - Note expiration date (set when created)
   - Set reminder 1 month before expiry
   - Rotate secret before expiration

3. **Email Deliverability:**
   - Check spam complaint rates
   - Monitor bounce rates
   - Review sender reputation (use tools like mail-tester.com)

### Quarterly Checks

1. **Review API Permissions:**
   - Ensure only necessary permissions are granted
   - Remove any unused permissions

2. **Update Documentation:**
   - Note any configuration changes
   - Document any issues and resolutions

3. **Test Failover:**
   - Verify backup email method if primary fails
   - Consider secondary SMTP provider for redundancy

---

## Email Volume Limits

### Microsoft 365 Sending Limits

**Per User (dave@rundaverun.org):**
- **10,000 recipients per day** (across all emails)
- **30 messages per minute**
- **500 recipients per message**

**Campaign Newsletter Considerations:**
- If subscriber list exceeds 10,000, consider:
  - Splitting sends across multiple days
  - Using dedicated email service (SendGrid, Mailchimp, etc.)
  - Requesting higher limits from Microsoft (business case required)

**Best Practices:**
- Keep transactional emails (confirmations, receipts) on WP Mail SMTP
- Use dedicated service for bulk newsletters (if >10k subscribers)

---

## Alternative: High-Volume Email Setup

If campaign grows beyond M365 limits, consider:

### Option 1: Azure Communication Services Email

**Benefits:**
- Higher volume limits
- Better for campaigns with large lists
- Native Microsoft integration
- More detailed analytics

**Setup:**
- Requires separate Azure setup
- More complex configuration
- Additional cost (~$0.25 per 1,000 emails)

### Option 2: Dedicated Email Service

**Services to Consider:**
- **SendGrid:** Good deliverability, generous free tier
- **Mailgun:** Developer-friendly, pay-as-you-go
- **Amazon SES:** Very low cost, requires technical setup

**Integration:**
- WP Mail SMTP Pro supports these providers
- Switch mailer in settings without code changes

---

## Cost Summary

### WP Mail SMTP Pro
- **Essential Plan:** $49/year (1 site)
- **Plus Plan:** $99/year (3 sites, priority support)
- **Recommended:** Essential (sufficient for campaign)

### Microsoft 365 (Existing)
- Already included in GoDaddy hosting package
- No additional cost for OAuth authentication

### Total Email Infrastructure Cost
- **Year 1:** $49-99 (WP Mail SMTP Pro license)
- **Ongoing:** $49-99/year (license renewal)

**Compare to alternatives:**
- Free plugins: Don't support OAuth, won't work with MFA
- Other premium plugins: $100-200/year, fewer features
- Dedicated email services: $10-50/month = $120-600/year

**Verdict:** WP Mail SMTP Pro is most cost-effective for your setup.

---

## Support Resources

### WP Mail SMTP Pro Support

**Documentation:** https://wpmailsmtp.com/docs/  
**Support Ticket:** https://wpmailsmtp.com/account/support/  
**Response Time:** 24-48 hours (faster with Plus plan)

### Microsoft Azure Support

**Azure Documentation:** https://docs.microsoft.com/azure/  
**App Registration Guide:** https://docs.microsoft.com/azure/active-directory/develop/quickstart-register-app  
**Graph API Permissions:** https://docs.microsoft.com/graph/permissions-reference

### GoDaddy Support

**Microsoft 365 Support:** 1-800-MY-GODADDY  
**Email Settings:** Email & Office → Manage (in GoDaddy account)

---

## Quick Reference Card

**For Production Setup:**

1. ✅ Purchase WP Mail SMTP Pro ($49-99)
2. ✅ Create Azure App Registration
   - Copy: Client ID, Tenant ID, Client Secret
3. ✅ Install Pro plugin on rundaverun.org
4. ✅ Enter license key
5. ✅ Configure Outlook mailer with OAuth credentials
6. ✅ Authorize Microsoft 365 connection (with MFA)
7. ✅ Send test email to verify
8. ✅ Check email log for success

**Credentials Needed:**
```
WP Mail SMTP Pro License: [from purchase]
Azure Client ID: [from app registration]
Azure Client Secret: [from app registration]
From Email: dave@rundaverun.org
From Name: Dave Biggers for Mayor
```

**Test Email To:** davidbiggers@yahoo.com

---

## Next Steps After Email Configuration

Once email is working:

1. ✅ Test all Contact Form 7 forms on production
2. ✅ Test newsletter signup (double opt-in flow)
3. ✅ Test volunteer registration confirmation
4. ✅ Send test newsletter to small group (5-10 people)
5. ✅ Monitor email log for 24 hours
6. ✅ Check spam reports and bounce rates
7. ✅ Document any issues and resolutions
8. ✅ Set up monitoring alerts (if available)

---

**Document Created:** November 3, 2025  
**For:** Dave Biggers for Mayor Campaign  
**Site:** rundaverun.org  
**Email:** dave@rundaverun.org (Microsoft 365 with MFA)

**Status:** Ready for production deployment ✅

---

*This guide provides complete step-by-step instructions for configuring professional email delivery for the campaign website using WP Mail SMTP Pro with Microsoft 365 OAuth authentication. Follow the steps in order for best results.*
