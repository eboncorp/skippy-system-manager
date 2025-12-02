#!/bin/bash
###############################################################################
# WordPress Color Contrast Checker - Enhanced
# Version: 1.1.0
# Created: 2025-11-08
#
# Description:
#   Scans WordPress pages and CSS files for WCAG 2.1 AA color contrast
#   violations and detects white-on-white text from CSS inheritance
#
# Usage:
#   bash wordpress_color_contrast_checker_v1.1.0.sh [page_ids...]
#
# Examples:
#   bash wordpress_color_contrast_checker_v1.1.0.sh 105
#   bash wordpress_color_contrast_checker_v1.1.0.sh 105 107 337
#
# Exit Codes:
#   0 = All checks passed
#   1 = Contrast violations found
###############################################################################

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default page IDs if none provided
PAGE_IDS="${@:-105 107 337}"
ISSUES_FOUND=0

echo -e "${BLUE}=== WordPress Color Contrast Checker v1.1.0 ===${NC}"
echo "Checking pages: $PAGE_IDS"
echo ""

# Function to convert hex to RGB
hex_to_rgb() {
    local hex="$1"
    hex="${hex#\#}"

    # Handle 3-digit hex
    if [ ${#hex} -eq 3 ]; then
        hex="${hex:0:1}${hex:0:1}${hex:1:1}${hex:1:1}${hex:2:1}${hex:2:1}"
    fi

    local r=$((16#${hex:0:2}))
    local g=$((16#${hex:2:2}))
    local b=$((16#${hex:4:2}))

    echo "$r $g $b"
}

# Function to calculate contrast ratio using Python
calculate_contrast() {
    local color1="$1"
    local color2="$2"

    read -r r1 g1 b1 <<< "$(hex_to_rgb "$color1")"
    read -r r2 g2 b2 <<< "$(hex_to_rgb "$color2")"

    python3 -c "
r1, g1, b1 = $r1 / 255.0, $g1 / 255.0, $b1 / 255.0
r2, g2, b2 = $r2 / 255.0, $g2 / 255.0, $b2 / 255.0

def gamma(c):
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

l1 = 0.2126 * gamma(r1) + 0.7152 * gamma(g1) + 0.0722 * gamma(b1)
l2 = 0.2126 * gamma(r2) + 0.7152 * gamma(g2) + 0.0722 * gamma(b2)

ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
print(f'{ratio:.2f}')
"
}

# Function to check WCAG compliance
check_wcag() {
    local ratio=$1
    python3 -c "
ratio = $ratio
if ratio >= 4.5:
    print('PASS')
elif ratio >= 3.0:
    print('WARN')
else:
    print('FAIL')
"
}

###############################################################################
# CHECK 1: CSS Inheritance Issues (White-on-White Detection)
###############################################################################
echo -e "${BLUE}CHECK 1: CSS Inheritance Issues${NC}"
echo "Scanning for white-on-white text from parent color inheritance..."
echo ""

# Find all CSS files in the plugin
CSS_FILES=$(find wp-content/plugins/dave-biggers-policy-manager/assets/css -name "*.css" -type f 2>/dev/null)

for css_file in $CSS_FILES; do
    echo "Analyzing: $css_file"

    # Look for classes with white backgrounds but no explicit text color
    # These will inherit color from parent and could become white-on-white

    WHITE_BG_CLASSES=$(grep -n "background.*white\|background.*#fff\|background.*#ffffff" "$css_file" | cut -d: -f1)

    if [ -n "$WHITE_BG_CLASSES" ]; then
        for line_num in $WHITE_BG_CLASSES; do
            # Get the class name (look backwards from the background line)
            CLASS_NAME=$(sed -n "1,${line_num}p" "$css_file" | tac | grep -m 1 -oP '^\s*\.\K[a-zA-Z0-9_-]+' | head -1)

            if [ -n "$CLASS_NAME" ]; then
                # Check if this class or its immediate block has an explicit color property
                # Get the full CSS block for this class
                BLOCK_START=$(grep -n "^\.$CLASS_NAME\|^\s*\.$CLASS_NAME" "$css_file" | head -1 | cut -d: -f1)

                if [ -n "$BLOCK_START" ]; then
                    # Extract the block (from class name to closing brace)
                    BLOCK=$(sed -n "${BLOCK_START},/^}/p" "$css_file" | head -20)

                    # Check if block has explicit color (not just background)
                    if echo "$BLOCK" | grep -q "^\s*color:"; then
                        echo -e "  ${GREEN}✓${NC} .$CLASS_NAME has explicit text color"
                    else
                        echo -e "  ${YELLOW}⚠${NC} .$CLASS_NAME has white background but NO explicit text color"
                        echo -e "    ${YELLOW}WARNING:${NC} Will inherit color from parent - could cause white-on-white text"
                        echo -e "    ${YELLOW}Location:${NC} $css_file:$line_num"
                        echo -e "    ${YELLOW}Fix:${NC} Add 'color: #333;' to .$CLASS_NAME"
                        ISSUES_FOUND=$((ISSUES_FOUND + 1))
                    fi
                fi
            fi
        done
    fi
done

echo ""

###############################################################################
# CHECK 2: Explicit Color Contrast Violations
###############################################################################
echo -e "${BLUE}CHECK 2: Explicit Color Contrast Violations${NC}"
echo "Scanning page content for inline style contrast issues..."
echo ""

for page_id in $PAGE_IDS; do
    if ! wp post get "$page_id" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Page $page_id not found, skipping"
        continue
    fi

    PAGE_TITLE=$(wp post get "$page_id" --field=post_title 2>/dev/null)
    echo -e "${BLUE}Checking Page $page_id: $PAGE_TITLE${NC}"

    # Get page content
    PAGE_CONTENT=$(wp post get "$page_id" --field=post_content 2>/dev/null)

    # Look for inline styles with both color and background
    # Example: style="color: #FFC72C; background: linear-gradient(...#003D7A...)"

    # Extract sections with background gradients and look for text color
    if echo "$PAGE_CONTENT" | grep -q "background.*gradient.*#003D7A\|background.*gradient.*#002952"; then
        # Check if there's yellow text in these sections
        if echo "$PAGE_CONTENT" | grep -q "color:\s*#FFC72C"; then
            RATIO=$(calculate_contrast "#FFC72C" "#003D7A")
            STATUS=$(check_wcag "$RATIO")

            if [ "$STATUS" = "PASS" ]; then
                echo -e "  ${GREEN}✓${NC} Yellow (#FFC72C) on dark blue (#003D7A): ${RATIO}:1 PASS"
            elif [ "$STATUS" = "WARN" ]; then
                echo -e "  ${YELLOW}⚠${NC} Yellow (#FFC72C) on dark blue (#003D7A): ${RATIO}:1 (large text only)"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            else
                echo -e "  ${RED}✗${NC} Yellow (#FFC72C) on dark blue (#003D7A): ${RATIO}:1 FAIL"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            fi
        fi
    fi
done

echo ""

###############################################################################
# CHECK 3: JavaScript-Generated Content Analysis
###############################################################################
echo -e "${BLUE}CHECK 3: JavaScript-Generated Content${NC}"
echo "Analyzing dynamically generated content for contrast issues..."
echo ""

# Check JavaScript files for innerHTML insertions with potential color issues
JS_FILES=$(find wp-content/plugins/dave-biggers-policy-manager/assets/js -name "*.js" -type f 2>/dev/null)

for js_file in $JS_FILES; do
    # Look for innerHTML or insertAdjacentHTML with list items or text
    if grep -q "innerHTML.*<li>\|innerHTML.*<p>" "$js_file"; then
        echo "Found dynamic content generation in: $js_file"

        # Check if the corresponding CSS has proper color settings
        CSS_FILE="${js_file//.js/.css}"
        CSS_FILE="${CSS_FILE//js/css}"

        if [ -f "$CSS_FILE" ]; then
            echo -e "  ${GREEN}✓${NC} Corresponding CSS file exists: $CSS_FILE"
        else
            echo -e "  ${YELLOW}⚠${NC} No corresponding CSS file found"
        fi
    fi
done

echo ""

###############################################################################
# CHECK 4: Common Problematic Patterns
###############################################################################
echo -e "${BLUE}CHECK 4: Common Problematic Patterns${NC}"
echo "Checking for known problematic color combinations..."
echo ""

# Pattern 1: White text on white background
echo "Pattern: White-on-white detection"
for css_file in $CSS_FILES; do
    # Find selectors with both white background AND white color
    if grep -l "background.*white" "$css_file" | xargs grep -l "color.*white" >/dev/null 2>&1; then
        # This file has both - need to check if they're in same selector
        SELECTORS=$(grep -B 5 "color:\s*white" "$css_file" | grep "^\." | sed 's/\s*{.*//')

        for selector in $SELECTORS; do
            # Check if this selector also has white background
            if grep -A 10 "^$selector\|^\s*$selector" "$css_file" | grep -q "background.*white"; then
                echo -e "  ${RED}✗ CRITICAL:${NC} $selector has white text AND white background"
                echo -e "    File: $css_file"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            fi
        done
    fi
done

# Pattern 2: Parent with color:white, child with background:white but no color
echo ""
echo "Pattern: Inheritance-based white-on-white"
echo "Classes with white background that could inherit white text from parent:"

for css_file in $CSS_FILES; do
    # Find classes with white/light backgrounds
    grep -n "background:\s*white\|background:\s*#fff" "$css_file" | while read -r line; do
        line_num=$(echo "$line" | cut -d: -f1)

        # Get class name
        CLASS=$(sed -n "1,${line_num}p" "$css_file" | tac | grep -m 1 "^\." | sed 's/\s*{.*//' | sed 's/^\s*//')

        if [ -n "$CLASS" ]; then
            # Check if it has explicit color
            BLOCK=$(sed -n "/$CLASS/,/^}/p" "$css_file" | head -15)

            if ! echo "$BLOCK" | grep -q "^\s*color:"; then
                echo -e "  ${YELLOW}⚠${NC} $CLASS (in $css_file:$line_num)"
                echo -e "     ${YELLOW}Risk:${NC} Will inherit text color from parent element"
                echo -e "     ${YELLOW}Fix:${NC} Add explicit 'color: #333;' or similar"
            fi
        fi
    done
done

echo ""

###############################################################################
# Summary
###############################################################################
echo -e "${BLUE}=== Summary ===${NC}"
echo ""

if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo -e "${GREEN}✓ No color contrast issues found${NC}"
    echo ""
    echo "All text appears to have sufficient contrast and explicit color declarations."
    exit 0
else
    echo -e "${RED}✗ Found $ISSUES_FOUND color contrast issues or warnings${NC}"
    echo ""
    echo "Recommendations:"
    echo "  1. Add explicit 'color: #333;' to all classes with white backgrounds"
    echo "  2. Test color combinations using: https://webaim.org/resources/contrastchecker/"
    echo "  3. WCAG AA requires:"
    echo "     - 4.5:1 contrast for normal text"
    echo "     - 3.0:1 contrast for large text (18pt+ or 14pt+ bold)"
    echo "  4. Always set text color explicitly - never rely on inheritance in white boxes"
    echo ""
    exit 1
fi
