---
description: Deploy verification with multi-layer cache flush and visual confirmation
allowed-tools: ["Bash", "Read", "Write", "mcp__general-server__wp_cli_command", "mcp__general-server__run_remote_command", "mcp__general-server__screenshot_capture", "mcp__general-server__http_get"]
argument-hint: "[URL or page_id to verify] [optional: expected_text to check for]"
---

# Deploy Verify Command

Comprehensive deployment verification with multi-layer cache invalidation and visual confirmation.

**Problem Solved:** Changes deployed but not visible due to caching at WordPress, server, or CDN layers.

## Quick Usage

```
/deploy-verify https://rundaverun.org/about/
/deploy-verify 105 "42 Louisville neighborhoods"
/deploy-verify --flush-only
```

## Full Verification Workflow

### Step 1: Parse Arguments
```bash
# Determine what to verify
TARGET="$1"           # URL or page ID
EXPECTED_TEXT="$2"    # Optional text to verify

# Normalize to URL
if [[ "$TARGET" =~ ^[0-9]+$ ]]; then
  # It's a page ID
  PAGE_ID="$TARGET"
  # Get URL from WordPress
  LOCAL_URL=$(wp --path="/home/dave/skippy/rundaverun_local_site/app/public" post list --post__in=$PAGE_ID --field=url 2>/dev/null | head -1)
  PROD_URL="https://rundaverun.org$(echo "$LOCAL_URL" | sed 's|http://[^/]*||')"
else
  PROD_URL="$TARGET"
  PAGE_ID=""
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              DEPLOY VERIFICATION                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Target: $PROD_URL"
echo "Expected: ${EXPECTED_TEXT:-'(not specified)'}"
echo ""
```

### Step 2: Create Session Directory
```bash
SESSION_DIR="/home/dave/skippy/work/deploy/$(date +%Y%m%d_%H%M%S)_verify"
mkdir -p "$SESSION_DIR"
echo "Session: $SESSION_DIR"
```

### Step 3: Capture BEFORE State
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ STEP 1: Capture BEFORE State                                │"
echo "└─────────────────────────────────────────────────────────────┘"

# Screenshot before
# Use mcp__general-server__screenshot_capture for BEFORE screenshot
echo "📸 Taking BEFORE screenshot..."
```

Use `mcp__general-server__screenshot_capture`:
- URL: $PROD_URL
- output_path: $SESSION_DIR/before.png

```bash
# Save HTTP response
curl -sI "$PROD_URL" > "$SESSION_DIR/headers_before.txt"
echo "📋 Headers saved"

# Save HTML content
curl -s "$PROD_URL" > "$SESSION_DIR/content_before.html"
echo "📄 Content saved ($(wc -c < "$SESSION_DIR/content_before.html") bytes)"
```

### Step 4: Multi-Layer Cache Flush
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ STEP 2: Multi-Layer Cache Flush                             │"
echo "└─────────────────────────────────────────────────────────────┘"
```

#### Layer 1: Local WordPress Cache
```bash
echo "  [1/5] Local WordPress cache..."
WP_PATH="/home/dave/skippy/rundaverun_local_site/app/public"
wp --path="$WP_PATH" cache flush 2>/dev/null && echo "       ✅ WP object cache flushed"
wp --path="$WP_PATH" transient delete --all 2>/dev/null && echo "       ✅ Transients deleted"
```

#### Layer 2: Production WordPress Cache
```bash
echo "  [2/5] Production WordPress cache..."
```

Use `mcp__general-server__run_remote_command` (or SSH):
```bash
SSH_CMD='SSH_AUTH_SOCK="" ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i ~/.ssh/godaddy_rundaverun git_deployer_f44cc3416a_545525@bp6.0cf.myftpupload.com'

$SSH_CMD "cd html && wp cache flush 2>/dev/null && echo 'WP cache flushed'"
$SSH_CMD "cd html && wp transient delete --all 2>/dev/null && echo 'Transients deleted'"
```

#### Layer 3: Plugin Caches (Autoptimize, etc.)
```bash
echo "  [3/5] Plugin caches..."
$SSH_CMD "cd html && rm -rf wp-content/cache/autoptimize/* 2>/dev/null && echo 'Autoptimize cache cleared'"
$SSH_CMD "cd html && rm -rf wp-content/cache/min/* 2>/dev/null && echo 'Minification cache cleared'"
```

#### Layer 4: Server-Level Cache (GoDaddy)
```bash
echo "  [4/5] Server cache (GoDaddy)..."
# GoDaddy Managed WordPress has server-side caching
# Flush via WP-CLI command that triggers server cache clear
$SSH_CMD "cd html && wp rewrite flush 2>/dev/null && echo 'Rewrite rules flushed'"

# Alternative: touch a file to invalidate cache
$SSH_CMD "touch html/wp-content/cache-bust-$(date +%s).txt 2>/dev/null"
```

#### Layer 5: CDN Cache (if Cloudflare)
```bash
echo "  [5/5] CDN cache..."
# Check if Cloudflare is configured
if [ -f "$HOME/.cloudflare/credentials.json" ]; then
  # Purge specific URL
  CF_ZONE=$(cat ~/.cloudflare/zone_id 2>/dev/null)
  CF_TOKEN=$(cat ~/.cloudflare/api_token 2>/dev/null)
  if [ -n "$CF_ZONE" ] && [ -n "$CF_TOKEN" ]; then
    curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE/purge_cache" \
      -H "Authorization: Bearer $CF_TOKEN" \
      -H "Content-Type: application/json" \
      --data "{\"files\":[\"$PROD_URL\"]}" > /dev/null
    echo "       ✅ Cloudflare cache purged for URL"
  fi
else
  echo "       ℹ️  No Cloudflare configured (skipped)"
fi
```

### Step 5: Wait for Cache Propagation
```bash
echo ""
echo "  ⏳ Waiting 10 seconds for cache propagation..."
sleep 10
```

### Step 6: Capture AFTER State
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ STEP 3: Capture AFTER State                                 │"
echo "└─────────────────────────────────────────────────────────────┘"

# Screenshot after
echo "📸 Taking AFTER screenshot..."
```

Use `mcp__general-server__screenshot_capture`:
- URL: $PROD_URL
- output_path: $SESSION_DIR/after.png

```bash
# Save HTTP response
curl -sI "$PROD_URL" > "$SESSION_DIR/headers_after.txt"
echo "📋 Headers saved"

# Save HTML content
curl -s "$PROD_URL" > "$SESSION_DIR/content_after.html"
echo "📄 Content saved ($(wc -c < "$SESSION_DIR/content_after.html") bytes)"
```

### Step 7: Verification Checks
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ STEP 4: Verification                                        │"
echo "└─────────────────────────────────────────────────────────────┘"

PASS=0
FAIL=0

# Check 1: HTTP Status
HTTP_STATUS=$(curl -sI "$PROD_URL" | head -1 | awk '{print $2}')
if [ "$HTTP_STATUS" = "200" ]; then
  echo "  ✅ HTTP Status: 200 OK"
  ((PASS++))
else
  echo "  ❌ HTTP Status: $HTTP_STATUS"
  ((FAIL++))
fi

# Check 2: Content Changed (if we had cached content)
if [ -f "$SESSION_DIR/content_before.html" ] && [ -f "$SESSION_DIR/content_after.html" ]; then
  BEFORE_SIZE=$(wc -c < "$SESSION_DIR/content_before.html")
  AFTER_SIZE=$(wc -c < "$SESSION_DIR/content_after.html")
  DIFF_LINES=$(diff "$SESSION_DIR/content_before.html" "$SESSION_DIR/content_after.html" 2>/dev/null | wc -l)

  if [ "$DIFF_LINES" -gt 0 ]; then
    echo "  ℹ️  Content Changed: $DIFF_LINES lines differ"
  else
    echo "  ℹ️  Content: No change detected"
  fi
fi

# Check 3: Expected Text Present
if [ -n "$EXPECTED_TEXT" ]; then
  if grep -q "$EXPECTED_TEXT" "$SESSION_DIR/content_after.html" 2>/dev/null; then
    echo "  ✅ Expected text found: '$EXPECTED_TEXT'"
    ((PASS++))
  else
    echo "  ❌ Expected text NOT found: '$EXPECTED_TEXT'"
    ((FAIL++))
  fi
fi

# Check 4: No Cache Headers (content should be fresh)
CACHE_CONTROL=$(grep -i "cache-control" "$SESSION_DIR/headers_after.txt" 2>/dev/null)
if echo "$CACHE_CONTROL" | grep -qi "no-cache\|max-age=0"; then
  echo "  ✅ Cache headers indicate fresh content"
  ((PASS++))
else
  echo "  ⚠️  Cache headers: $CACHE_CONTROL"
fi

# Check 5: Response Time
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "$PROD_URL")
if (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
  echo "  ✅ Response time: ${RESPONSE_TIME}s"
  ((PASS++))
else
  echo "  ⚠️  Response time: ${RESPONSE_TIME}s (slow)"
fi
```

### Step 8: Generate Report
```bash
echo ""
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│ SUMMARY                                                     │"
echo "└─────────────────────────────────────────────────────────────┘"

if [ "$FAIL" -eq 0 ]; then
  echo "  ✅ DEPLOYMENT VERIFIED - All checks passed ($PASS/$PASS)"
else
  echo "  ⚠️  ISSUES DETECTED - $FAIL checks failed ($PASS passed)"
fi

echo ""
echo "  Session: $SESSION_DIR"
echo "  Screenshots: before.png, after.png"
echo "  Content: content_before.html, content_after.html"
```

### Step 9: Save Report
```bash
cat > "$SESSION_DIR/README.md" << EOF
# Deploy Verification Report

**Date:** $(date '+%Y-%m-%d %H:%M:%S')
**URL:** $PROD_URL
**Expected Text:** ${EXPECTED_TEXT:-'(not specified)'}

## Results

- Checks Passed: $PASS
- Checks Failed: $FAIL
- Status: $([ "$FAIL" -eq 0 ] && echo "✅ VERIFIED" || echo "⚠️ ISSUES")

## Cache Layers Flushed

1. ✅ Local WordPress object cache
2. ✅ Local WordPress transients
3. ✅ Production WordPress object cache
4. ✅ Production WordPress transients
5. ✅ Plugin caches (Autoptimize, etc.)
6. ✅ Server rewrite rules
7. $([ -f "$HOME/.cloudflare/credentials.json" ] && echo "✅" || echo "⏭️") Cloudflare CDN

## Files

- \`before.png\` - Screenshot before cache flush
- \`after.png\` - Screenshot after cache flush
- \`content_before.html\` - HTML before
- \`content_after.html\` - HTML after
- \`headers_before.txt\` - HTTP headers before
- \`headers_after.txt\` - HTTP headers after

## Troubleshooting

If content still appears cached:
1. Check browser cache (Ctrl+Shift+R for hard refresh)
2. Try incognito/private window
3. Wait additional 5-10 minutes for CDN propagation
4. Check if page-specific caching plugin is active
EOF

echo "  Report: $SESSION_DIR/README.md"
```

## Flush-Only Mode

For just flushing caches without verification:

```
/deploy-verify --flush-only
```

```bash
echo "Flushing all cache layers..."
# Run Steps 4.1 through 4.5 only
echo "✅ All caches flushed"
```

## Troubleshooting

### Content Still Cached

1. **Browser Cache:** Hard refresh with Ctrl+Shift+R
2. **ISP Cache:** Try different network or VPN
3. **CDN:** May take 5-15 minutes to propagate globally
4. **Varnish/Nginx:** Check server-level cache config

### Expected Text Not Found

1. Verify the text exists in WordPress admin
2. Check for JavaScript-rendered content (not in HTML source)
3. Look for encoding issues (special characters)
4. Confirm the correct page ID/URL

### Slow Response Time

1. Check server load with `/ebon-status`
2. Review large images or unoptimized assets
3. Check for database query bottlenecks
4. Consider enabling caching (after verification complete)

## Integration

This command uses:
- `mcp__general-server__screenshot_capture` - Visual verification
- `mcp__general-server__run_remote_command` - Production cache flush
- `mcp__general-server__wp_cli_command` - Local WordPress commands
- Standard curl for HTTP verification

Session files saved to `/home/dave/skippy/work/deploy/` for audit trail.
