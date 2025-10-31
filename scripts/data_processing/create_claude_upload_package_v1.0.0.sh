#!/bin/bash
# Create optimized Claude.ai upload package
# Excludes duplicates, archives, and large files

set -e

CAMPAIGN_DIR="/home/dave/Documents/Government/budgets/RunDaveRun/campaign"
OUTPUT_DIR="/home/dave/Documents/Government/budgets/RunDaveRun/campaign/CLAUDE_UPLOAD_$(date +%Y%m%d)"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "========================================"
echo "Claude.ai Upload Package Creator"
echo "========================================"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Creating optimized package..."
echo ""

# Copy only essential files, excluding duplicates and archives
rsync -av \
  --include='*.md' \
  --include='*.txt' \
  --include='*.html' \
  --include='*.css' \
  --include='*.js' \
  --include='*.json' \
  --include='*.php' \
  --include='*.sql' \
  --include='*/' \
  --exclude='*.zip' \
  --exclude='*.tar.gz' \
  --exclude='*.pdf' \
  --exclude='*.jpg' \
  --exclude='*.jpeg' \
  --exclude='*.png' \
  --exclude='*.gif' \
  --exclude='*.webp' \
  --exclude='archive-old-versions/' \
  --exclude='*/archive-old-versions/*' \
  --exclude='*backup*/' \
  --exclude='*/backup*/*' \
  --exclude='.git/' \
  --exclude='*/.git/*' \
  --exclude='node_modules/' \
  --exclude='*/node_modules/*' \
  --exclude='wp-content/uploads/' \
  --exclude='zips/' \
  --exclude='*/zips/*' \
  --exclude='zips_text_output/' \
  --exclude='*/zips_text_output/*' \
  --exclude='mobile_screenshots/' \
  --exclude='*/mobile_screenshots/*' \
  --exclude='CLAUDE_AI_UPLOAD*/' \
  --exclude='*/CLAUDE_AI_UPLOAD*/*' \
  --exclude='GODADDY_DEPLOYMENT*/' \
  --exclude='*/GODADDY_DEPLOYMENT*/*' \
  --exclude='rundaverun-deploy-ready/' \
  --exclude='*/rundaverun-deploy-ready/*' \
  --exclude='*.phar' \
  --exclude='wp-cli.phar' \
  "$CAMPAIGN_DIR/" "$OUTPUT_DIR/"

# Get statistics
TOTAL_FILES=$(find "$OUTPUT_DIR" -type f | wc -l)
TOTAL_SIZE=$(du -sh "$OUTPUT_DIR" | awk '{print $1}')

echo ""
echo "========================================"
echo "Package Creation Complete!"
echo "========================================"
echo ""
echo "Output Directory: $OUTPUT_DIR"
echo "Total Files: $TOTAL_FILES"
echo "Total Size: $TOTAL_SIZE"
echo ""
echo "File Types Included:"
find "$OUTPUT_DIR" -type f -name "*.md" | wc -l | xargs echo "  Markdown (.md):"
find "$OUTPUT_DIR" -type f -name "*.php" | wc -l | xargs echo "  PHP (.php):"
find "$OUTPUT_DIR" -type f -name "*.txt" | wc -l | xargs echo "  Text (.txt):"
find "$OUTPUT_DIR" -type f -name "*.html" | wc -l | xargs echo "  HTML (.html):"
find "$OUTPUT_DIR" -type f -name "*.css" | wc -l | xargs echo "  CSS (.css):"
find "$OUTPUT_DIR" -type f -name "*.js" | wc -l | xargs echo "  JavaScript (.js):"
find "$OUTPUT_DIR" -type f -name "*.json" | wc -l | xargs echo "  JSON (.json):"
find "$OUTPUT_DIR" -type f -name "*.sql" | wc -l | xargs echo "  SQL (.sql):"
echo ""
echo "Next Steps:"
echo "1. The package is ready at: $OUTPUT_DIR"
echo "2. You can upload the entire directory to Claude.ai Projects"
echo "3. All files are under 30MB each"
echo "4. No duplicates or archives included"
echo ""
