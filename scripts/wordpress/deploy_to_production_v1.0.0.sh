#!/bin/bash
# Automated Production Deployment Script

set -e

CAMPAIGN_DIR="/home/dave/Documents/Government/budgets/RunDaveRun/campaign"
SITE_URL="https://rundaverun.org"

cd "$CAMPAIGN_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 DEPLOYING TO PRODUCTION - rundaverun.org"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Check git status
echo "1️⃣ Checking git status..."
if [[ -n $(git status -s) ]]; then
    echo "   ⚠️  Uncommitted changes found:"
    git status -s
    read -p "   Commit changes first? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "   Commit message: " COMMIT_MSG
        git add -A
        git commit -m "$COMMIT_MSG"
        echo "   ✅ Changes committed"
    fi
else
    echo "   ✅ Working directory clean"
fi
echo ""

# Step 2: Push to GitHub
echo "2️⃣ Pushing to GitHub..."
if git push origin master; then
    echo "   ✅ Pushed to GitHub successfully"
else
    echo "   ❌ GitHub push failed"
    exit 1
fi
echo ""

# Step 3: Wait for GitHub Actions
echo "3️⃣ Waiting for GitHub Actions deployment..."
echo "   Check status: https://github.com/eboncorp/rundaverun-website/actions"
sleep 5

# Step 4: Deploy critical scripts directly
echo "4️⃣ Deploying critical scripts..."

# Deploy roles restoration script if needed
if [ -f "restore-wordpress-roles.php" ]; then
    echo "   Deploying restore-wordpress-roles.php..."
    # This would use scp or another method
    echo "   ⚠️  Manual deployment needed (SSH key required)"
fi

# Step 5: Clear caches
echo "5️⃣ Clearing caches..."
if curl -s "$SITE_URL/purge-all-caches.php" | grep -q "success"; then
    echo "   ✅ Caches cleared"
else
    echo "   ⚠️  Cache clear may have failed"
fi
echo ""

# Step 6: Health check
echo "6️⃣ Running health check..."
if [ -f "./wordpress-health-check.sh" ]; then
    ./wordpress-health-check.sh
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
