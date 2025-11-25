# WiFi SSL Certificate Troubleshooting Guide

## Problem Summary
- **Works on:** Phone hotspot (5G)
- **Fails on:** Home WiFi network
- **Error:** `NET::ERR_CERT_AUTHORITY_INVALID` when accessing https://claude.ai
- **Browser:** Shows "Your connection is not private"

## Current Status
✅ System CA certificates updated
✅ Diagnostic scripts created
✅ Baseline captured from working hotspot connection

## Scripts Created

### 1. Quick Network Test: `~/test_network_ssl.sh`
**Use this to quickly compare networks**

```bash
~/test_network_ssl.sh
```

Run this on BOTH networks:
- Once while on your phone hotspot (✓ already done)
- Once while on your home WiFi

**What to look for:**
- Certificate Issuer should be "Let's Encrypt"
- If it shows a different issuer on WiFi, your router is intercepting HTTPS

### 2. Full Diagnostics: `~/wifi_debug.sh`
**Comprehensive network and SSL diagnostics**

```bash
~/wifi_debug.sh
```

This creates a detailed report in `/tmp/wifi_diagnostics_*.txt`

### 3. Browser Certificate Fix: `~/fix_browser_certs.sh`
**Resets browser certificate databases**

```bash
~/fix_browser_certs.sh
```

**WARNING:** This will:
- Close all browsers
- Backup existing cert databases
- Reset certificate databases
- Browser will recreate them on restart

## Step-by-Step Troubleshooting

### STEP 1: Switch to WiFi and Test
1. Disconnect from phone hotspot
2. Connect to your home WiFi
3. Run: `~/test_network_ssl.sh`
4. Compare the output with the hotspot test

### STEP 2: Check the Certificate Issuer

**On Hotspot (working):**
```
Certificate Issuer: C = US, O = Let's Encrypt, CN = E8
✓ Certificate is from Let's Encrypt (EXPECTED - GOOD)
```

**On WiFi - Expected to see:**
- **If SAME (Let's Encrypt):** Browser certificate database issue → Run `fix_browser_certs.sh`
- **If DIFFERENT:** Router is doing SSL inspection → Check router settings

### STEP 3: If Router is Intercepting

Your router might have features called:
- "HTTPS Inspection"
- "SSL Inspection"
- "Deep Packet Inspection"
- "Parental Controls"
- "Web Security"
- "Advanced Threat Protection"

**Solution Options:**
1. **Disable the feature in router settings** (preferred)
2. **Install router's root certificate** in browser (less secure)
3. **Use alternative DNS** (may or may not help)

### STEP 4: Try Alternative DNS

If the router is the problem, try using different DNS:

```bash
# Use Google DNS
sudo resolvectl dns wlp44s0 8.8.8.8 8.8.4.4

# Or use Cloudflare DNS
sudo resolvectl dns wlp44s0 1.1.1.1 1.0.0.1

# Verify it changed
resolvectl status
```

Then restart browser and test.

### STEP 5: Reset Browser Certificates

If same certificate issuer on both networks but browser still fails:

```bash
~/fix_browser_certs.sh
```

This will reset the browser's certificate database.

## Common Causes Ranked by Likelihood

1. **Router SSL/HTTPS Inspection** (80% likely)
   - Router intercepts HTTPS and presents own certificate
   - Browser doesn't trust router's certificate
   - Command-line tools may still work

2. **Browser Certificate Database Corruption** (15% likely)
   - Browser's NSS/cert database is corrupted
   - Fixed by resetting cert database

3. **Captive Portal** (4% likely)
   - WiFi network requires login/authentication
   - Usually shows redirect instead

4. **DNS Hijacking** (1% likely)
   - DNS server redirects to wrong IP
   - Would affect all tools, not just browser

## Files Created

- `/home/dave/test_network_ssl.sh` - Quick SSL test
- `/home/dave/wifi_debug.sh` - Full diagnostics
- `/home/dave/fix_browser_certs.sh` - Reset browser certs
- `/tmp/network_diagnostics.txt` - Baseline from hotspot
- `/tmp/ssl_test_log.txt` - Test history log

## What I Found (While on Hotspot)

```
Network: Phone Hotspot (SM-G935PD3Bxzx)
IP: 10.196.42.92/24
Gateway: 10.196.42.104
DNS: 8.8.8.8 (Google DNS)
Certificate: Let's Encrypt E8 ✓
SSL Verification: PASSED ✓
```

## Next Steps

1. **Switch to your home WiFi**
2. **Run:** `~/test_network_ssl.sh`
3. **Compare** certificate issuers
4. **Based on results:**
   - Same issuer → Run `~/fix_browser_certs.sh`
   - Different issuer → Check router for SSL inspection
   - Need more info → Run `~/wifi_debug.sh`

## Quick Reference Commands

```bash
# Check current network
iwgetid -r

# Quick SSL test
~/test_network_ssl.sh

# Full diagnostics
~/wifi_debug.sh

# Fix browser certs
~/fix_browser_certs.sh

# Check what network you're on
ip addr show wlp44s0 | grep inet

# View test history
cat /tmp/ssl_test_log.txt
```

## Need More Help?

If none of these work, run the full diagnostic and review:
```bash
~/wifi_debug.sh
cat /tmp/wifi_diagnostics_*.txt | less
```

---
**Created:** 2025-10-25
**Scripts ready to use:** ✓
