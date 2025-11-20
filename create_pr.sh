#!/bin/bash
# Create Pull Request for Claude Code Robustness System
# Run this script to create the PR automatically

set -euo pipefail

echo "Creating Pull Request..."
echo ""

gh pr create \
  --title "feat: Complete Claude Code Robustness System (All 12 Issues) - v2.0.0" \
  --body-file PULL_REQUEST_SUMMARY.md \
  --base main \
  --head claude/debug-issues-01CvoVuPY8Z5EPpc2od4kbFk

echo ""
echo "✅ Pull Request created successfully!"
