#!/bin/bash
# Quick Fix Script for WordPress Shell Command Exposure Issue
# Date: November 4, 2025
# Restores 14 posts with shell command syntax back to proper HTML

set -e  # Exit on error

echo "=============================================="
echo "WordPress Shell Command Fix Script"
echo "Restoring 14 affected posts..."
echo "=============================================="
echo ""

cd "/home/dave/Local Sites/rundaverun-local/app/public"

# Define post IDs and their corresponding backup files
declare -A posts=(
  [106]="/tmp/post106_styles_fixed.html"
  [107]="/tmp/post107_fixed.html"
  [109]="/tmp/post109_fixed.html"
  [151]="/tmp/post151_fixed.html"
  [245]="/tmp/post245_fixed.html"
  [249]="/tmp/post249_fixed.html"
  [328]="/tmp/post328_fixed.html"
  [699]="/tmp/post699_fixed.html"
  [700]="/tmp/post700_fixed.html"
  [716]="/tmp/post716_fixed.html"
  [717]="/tmp/post717_fixed.html"
  [934]="/tmp/post934_fixed.html"
  [941]="/tmp/post941_fixed.html"
  [942]="/tmp/post942_fixed.html"
)

declare -A titles=(
  [106]="About Dave"
  [107]="Our Plan"
  [109]="Contact"
  [151]="7. Research Bibliography & Citations"
  [245]="15. ABOUT DAVE BIGGERS"
  [249]="18. OUR PLAN FOR LOUISVILLE"
  [328]="Complete Voter Education Glossary"
  [699]="19. Public Safety & Community Policing"
  [700]="20. Criminal Justice Reform"
  [716]="21. Health & Human Services"
  [717]="34. Economic Development & Jobs"
  [934]="Volunteer Dashboard"
  [941]="Phone Banking Script"
  [942]="Canvassing Talking Points"
)

success_count=0
fail_count=0

# Restore each post
for post_id in "${!posts[@]}"; do
  file="${posts[$post_id]}"
  title="${titles[$post_id]}"

  echo "Processing Post $post_id: $title"

  # Check if backup file exists
  if [ ! -f "$file" ]; then
    echo "  ✗ ERROR: Backup file not found: $file"
    ((fail_count++))
    continue
  fi

  # Get file size for confirmation
  size=$(stat -c%s "$file")
  echo "  - Backup file: $file ($size bytes)"

  # Restore the post
  if wp post update "$post_id" --post_content="$(cat "$file")" --allow-root > /dev/null 2>&1; then
    echo "  ✓ Successfully restored"
    ((success_count++))
  else
    echo "  ✗ FAILED to restore"
    ((fail_count++))
  fi

  echo ""
done

echo "=============================================="
echo "Restoration Complete"
echo "=============================================="
echo "Successfully restored: $success_count posts"
echo "Failed: $fail_count posts"
echo ""

# Verify no shell commands remain
echo "Verifying fix..."
remaining=$(wp db query "SELECT COUNT(*) as count FROM wp_7e1ce15f22_posts WHERE post_status='publish' AND post_content LIKE '%\$(cat%'" --allow-root | tail -n 1)

if [ "$remaining" = "0" ]; then
  echo "✓ VERIFICATION PASSED: No shell commands found in published content"
else
  echo "⚠ WARNING: $remaining posts still contain shell commands"
fi

echo ""
echo "Check these pages on your website:"
echo "- http://rundaverun-local.local/about-dave"
echo "- http://rundaverun-local.local/our-plan"
echo "- http://rundaverun-local.local/contact"
echo ""
echo "Script completed at $(date)"
