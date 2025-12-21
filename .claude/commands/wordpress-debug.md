---
description: Automated WordPress diagnostic - runs 20-layer analysis and identifies issues
argument-hint: "[environment: local|production] [options: --quick|--layer N]"
allowed-tools: ["Bash", "Read", "Grep", "WebFetch", "mcp__general-server__wp_cli_command", "mcp__general-server__screenshot_capture"]
---

# WordPress Debug Command

Comprehensive 20-layer diagnostic for WordPress issues. Reduces 2-3 hour debug sessions to 15-30 minutes.

## Quick Start

**Run this command to execute the unified diagnostic:**

```bash
# Set environment
ENVIRONMENT="${1:-local}"
OPTIONS="${2:-}"

# Create session directory
SESSION_DIR="/home/dave/skippy/work/wordpress/$(date +%Y%m%d_%H%M%S)_debug_${ENVIRONMENT}"
mkdir -p "$SESSION_DIR"

# Run unified 20-layer diagnostic
bash /home/dave/skippy/scripts/wordpress/wp_unified_diagnostic_v3.0.0.sh "$ENVIRONMENT" $OPTIONS 2>&1 | tee "$SESSION_DIR/diagnostic_output.log"

echo ""
echo "Session directory: $SESSION_DIR"
echo "Full report: $SESSION_DIR/diagnostic_report.md"
```

## Environment Configuration

| Environment | Site URL | WP Path |
|-------------|----------|---------|
| `local` | http://rundaverun-local-complete-022655.local | /home/dave/skippy/websites/rundaverun/local_site/rundaverun_local_site/app/public |
| `production` | https://rundaverun.org | Via SSH to GoDaddy |

## Command Options

| Option | Description |
|--------|-------------|
| `--quick` | Run only layers 1-10 (fast mode, ~2 min) |
| `--full` | Run all 20 layers (default, ~5 min) |
| `--layer N` | Run only layer N |
| `--skip N` | Skip layer N |

## 20-Layer Diagnostic Framework

### Core Layers (1-10) - Always Run

| Layer | Check | Quick Fix |
|-------|-------|-----------|
| 1 | System Environment | PHP version, disk space, memory |
| 2 | WordPress Core | `wp core verify-checksums` |
| 3 | Database Integrity | `wp db check` |
| 4 | Plugin Health | `wp plugin list --status=active` |
| 5 | Theme Integrity | `wp theme list` |
| 6 | Content Structure | Page/post counts, empty pages |
| 7 | Shortcodes/Hooks | Registered shortcodes, cron |
| 8 | Performance | Autoload size, transients |
| 9 | Security | File permissions, users |
| 10 | Error Logs | debug.log analysis |

### Extended Layers (11-15) - Quality

| Layer | Check | Quick Fix |
|-------|-------|-----------|
| 11 | Link Integrity | Broken internal links |
| 12 | SEO Metadata | Title, description, OG tags |
| 13 | Accessibility | WCAG 2.1 AA compliance |
| 14 | Image Optimization | Large images, WebP usage |
| 15 | JavaScript | Syntax errors, eval usage |

### Infrastructure Layers (16-20) - Production

| Layer | Check | Quick Fix |
|-------|-------|-----------|
| 16 | REST API | Endpoint health |
| 17 | SSL/DNS/CDN | Certificate, DNS, headers |
| 18 | Form Testing | CF7 forms, newsletter |
| 19 | Email Config | SMTP setup |
| 20 | Production Remote | SSH diagnostics |

## Issue-Specific Quick Fixes

### 404 Not Found
```bash
WP_PATH="/home/dave/skippy/websites/rundaverun/local_site/rundaverun_local_site/app/public"
wp --path="$WP_PATH" --allow-root rewrite flush
wp --path="$WP_PATH" --allow-root option get permalink_structure
```

### 500 Internal Server Error
```bash
# Check recent errors
tail -50 "$WP_PATH/wp-content/debug.log" | grep -E "Fatal|Error"

# Isolate plugin issue
wp --path="$WP_PATH" --allow-root plugin deactivate --all
wp --path="$WP_PATH" --allow-root plugin activate dave-biggers-policy-manager
```

### White Screen of Death
```bash
# Enable debug
wp --path="$WP_PATH" --allow-root config set WP_DEBUG true --raw
wp --path="$WP_PATH" --allow-root config set WP_DEBUG_LOG true --raw

# Check for fatal
tail -20 "$WP_PATH/wp-content/debug.log"
```

### CSS/JS Not Loading
```bash
# Check asset paths
curl -sI "$SITE_URL/wp-content/themes/astra-child/style.css" | head -5

# Flush caches
wp --path="$WP_PATH" --allow-root cache flush
wp --path="$WP_PATH" --allow-root transient delete --all
```

### REST API Issues
```bash
# Test REST API
curl -s "$SITE_URL/wp-json/" | jq '.name, .url'
curl -s "$SITE_URL/wp-json/wp/v2/pages?per_page=1" | jq 'length'
```

## Production Diagnostics

For production site (rundaverun.org) via SSH:

```bash
# SSH command template
SSH_CMD='SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i ~/.ssh/godaddy_rundaverun git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com'

# Check WordPress version
$SSH_CMD "cd html && wp core version --allow-root"

# Check plugins
$SSH_CMD "cd html && wp plugin list --status=active --allow-root"

# Check recent errors
$SSH_CMD "cd html && tail -50 wp-content/debug.log 2>/dev/null | grep -E 'Fatal|Error'"

# Flush caches
$SSH_CMD "cd html && wp cache flush --allow-root && wp transient delete --all --allow-root && wp rewrite flush --allow-root"
```

## Cache Flush Checklist

After any fix, flush all caches:

```bash
# WordPress caches
wp --path="$WP_PATH" --allow-root cache flush
wp --path="$WP_PATH" --allow-root transient delete --all
wp --path="$WP_PATH" --allow-root rewrite flush

# If using Autoptimize
wp --path="$WP_PATH" --allow-root option delete autoptimize_cache

# Browser: Hard refresh (Ctrl+Shift+R)
# CDN: May need manual purge from GoDaddy panel
```

## Output Format

After running diagnostics, provide:

1. **Summary** - Pass/Fail counts, health score
2. **Critical Issues** - Must fix before deployment
3. **Warnings** - Should fix when possible
4. **Recommendations** - Best practices
5. **Session Directory** - Location of full report

## Related Scripts

| Script | Purpose |
|--------|---------|
| `wp_unified_diagnostic_v3.0.0.sh` | Main 20-layer diagnostic |
| `pre_deployment_validator_v1.0.0.sh` | Pre-deploy checks |
| `deployment_verification_v1.0.0.sh` | Post-deploy verification |
| `wordpress_color_contrast_checker_v1.2.0.sh` | WCAG contrast |
| `wp_mobile_responsive_checker_v1.0.0.sh` | Mobile testing |

## Session Directory Pattern

All debug sessions create a work directory:

```
/home/dave/skippy/work/wordpress/YYYYMMDD_HHMMSS_debug_{environment}/
├── diagnostic_output.log    # Console output
├── diagnostic_report.md     # Full markdown report
└── screenshots/             # If visual testing enabled
```

**NEVER use /tmp/** - files are lost on reboot.
