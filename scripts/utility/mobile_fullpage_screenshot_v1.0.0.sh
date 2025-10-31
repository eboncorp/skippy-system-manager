#!/bin/bash

# Full-page Mobile Screenshot Script for rundaverun.org

URL="https://rundaverun.org"
OUTPUT_DIR="./mobile_screenshots"

mkdir -p "$OUTPUT_DIR"

echo "Capturing full-page mobile screenshots of $URL..."

# iPhone 12/13/14 (390 width) - Full page
echo "Capturing iPhone 12 full page view (390px wide)..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/iphone-12-390-fullpage.png" --window-size=390,3000 --virtual-time-budget=5000 "$URL"

# Samsung Galaxy (360 width) - Full page
echo "Capturing Samsung Galaxy full page view (360px wide)..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/samsung-360-fullpage.png" --window-size=360,3000 --virtual-time-budget=5000 "$URL"

# About page
echo "Capturing About page full view (390px wide)..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/about-page-390-fullpage.png" --window-size=390,3000 --virtual-time-budget=5000 "$URL/about-dave/"

echo ""
echo "Full-page screenshots saved!"
ls -lh "$OUTPUT_DIR/*fullpage*"
