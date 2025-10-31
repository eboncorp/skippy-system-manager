#!/bin/bash

# Mobile Screenshot Script for rundaverun.org
# Captures screenshots at various mobile viewport sizes

URL="https://rundaverun.org"
OUTPUT_DIR="./mobile_screenshots"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Capturing mobile screenshots of $URL..."

# iPhone SE (375x667)
echo "Capturing iPhone SE view (375x667)..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/iphone-se-375.png" --window-size=375,667 --virtual-time-budget=5000 "$URL"

# iPhone 12/13/14 (390x844)
echo "Capturing iPhone 12/13/14 view (390x844)..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/iphone-12-390.png" --window-size=390,844 --virtual-time-budget=5000 "$URL"

# Samsung Galaxy S21 (360x800)
echo "Capturing Samsung Galaxy view (360x800)..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/samsung-360.png" --window-size=360,800 --virtual-time-budget=5000 "$URL"

# Small mobile (320x568)
echo "Capturing small mobile view (320x568)..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/small-mobile-320.png" --window-size=320,568 --virtual-time-budget=5000 "$URL"

# Also capture About page
echo "Capturing About page mobile view..."
google-chrome --headless --disable-gpu --screenshot="$OUTPUT_DIR/about-page-390.png" --window-size=390,844 --virtual-time-budget=5000 "$URL/about-dave/"

echo ""
echo "Screenshots saved to $OUTPUT_DIR/"
ls -lh "$OUTPUT_DIR/"
