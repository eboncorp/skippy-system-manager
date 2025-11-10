#!/bin/bash
###############################################################################
# WordPress Color Contrast Checker - Enhanced
# Version: 1.2.0
# Created: 2025-11-08
# Updated: 2025-11-08 (Added dark background detection)
#
# Description:
#   Scans WordPress pages and CSS files for WCAG 2.1 AA color contrast
#   violations and detects:
#   - White-on-white text from CSS inheritance
#   - Dark-on-dark text from CSS inheritance (NEW in v1.2.0)
#
# Usage:
#   bash wordpress_color_contrast_checker_v1.2.0.sh [page_ids...]
#
# Examples:
#   bash wordpress_color_contrast_checker_v1.2.0.sh 105
#   bash wordpress_color_contrast_checker_v1.2.0.sh 105 107 337
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

echo -e "${BLUE}=== WordPress Color Contrast Checker v1.2.0 ===${NC}"
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
" 2>/dev/null || echo "0.00"
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
" 2>/dev/null || echo "FAIL"
}

###############################################################################
# CHECK 1: CSS Inheritance Issues (White-on-White Detection)
###############################################################################
echo -e "${BLUE}CHECK 1: White Background Inheritance Issues${NC}"
echo "Scanning for white-on-white text from parent color inheritance..."
echo ""

# Find all CSS files in the plugin
CSS_FILES=$(find wp-content/plugins/dave-biggers-policy-manager/assets/css wp-content/themes -name "*.css" -type f 2>/dev/null)

for css_file in $CSS_FILES; do
    # Look for classes with white backgrounds but no explicit text color
    WHITE_BG_LINES=$(grep -n "background.*white\|background.*#fff\|background.*#ffffff" "$css_file" 2>/dev/null | cut -d: -f1)

    if [ -n "$WHITE_BG_LINES" ]; then
        for line_num in $WHITE_BG_LINES; do
            # Get the class name (look backwards from the background line)
            CLASS_NAME=$(sed -n "1,${line_num}p" "$css_file" 2>/dev/null | tac | grep -m 1 "^\s*\." 2>/dev/null | sed 's/\s*{.*//' | sed 's/^\s*\.//' | sed 's/\s.*//' || echo "")

            if [ -n "$CLASS_NAME" ]; then
                # Check if this class or its immediate block has an explicit color property
                BLOCK_START=$(grep -n "^\.$CLASS_NAME\|^\s*\.$CLASS_NAME" "$css_file" 2>/dev/null | head -1 | cut -d: -f1)

                if [ -n "$BLOCK_START" ]; then
                    # Extract the block (from class name to closing brace)
                    BLOCK=$(sed -n "${BLOCK_START},/^}/p" "$css_file" 2>/dev/null | head -20)

                    # Check if block has explicit color (not just background)
                    if echo "$BLOCK" | grep -q "^\s*color:"; then
                        # Has explicit color - good!
                        :
                    else
                        echo -e "  ${YELLOW}⚠${NC} .$CLASS_NAME has white background but NO explicit text color"
                        echo -e "    ${YELLOW}File:${NC} $css_file:$line_num"
                        echo -e "    ${YELLOW}Risk:${NC} Will inherit color from parent - could cause white-on-white text"
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
# CHECK 2: Dark Background Inheritance Issues (NEW in v1.2.0)
###############################################################################
echo -e "${BLUE}CHECK 2: Dark Background Inheritance Issues${NC}"
echo "Scanning for dark-on-dark text from parent color inheritance..."
echo ""

for css_file in $CSS_FILES; do
    # Look for classes with dark backgrounds (gradients with dark colors, or solid dark colors)
    # Patterns: #003f87, #002557, #003D7A, #002952, etc.
    DARK_BG_LINES=$(grep -n "background.*#00[0-9a-fA-F]\{4\}\|background.*linear-gradient.*#00[0-9a-fA-F]\{4\}" "$css_file" 2>/dev/null | cut -d: -f1)

    if [ -n "$DARK_BG_LINES" ]; then
        for line_num in $DARK_BG_LINES; do
            # Get the class name (look backwards from the background line)
            CLASS_NAME=$(sed -n "1,${line_num}p" "$css_file" 2>/dev/null | tac | grep -m 1 "^\s*\." 2>/dev/null | sed 's/\s*{.*//' | sed 's/^\s*\.//' | sed 's/\s.*//' || echo "")

            if [ -n "$CLASS_NAME" ]; then
                # Check if this class has an explicit color property
                BLOCK_START=$(grep -n "^\.$CLASS_NAME\|^\s*\.$CLASS_NAME" "$css_file" 2>/dev/null | head -1 | cut -d: -f1)

                if [ -n "$BLOCK_START" ]; then
                    # Extract the block (from class name to closing brace)
                    BLOCK=$(sed -n "${BLOCK_START},/^}/p" "$css_file" 2>/dev/null | head -20)

                    # Check if block has explicit color (not just background)
                    if echo "$BLOCK" | grep -q "^\s*color:"; then
                        # Has explicit color - check if it's appropriate for dark background
                        COLOR_VALUE=$(echo "$BLOCK" | grep "^\s*color:" | sed 's/.*color:\s*//' | sed 's/;.*//' | sed 's/\s*!important.*//' | tr -d ' ')

                        # If color is explicitly white, good!
                        if echo "$COLOR_VALUE" | grep -qiE "white|#fff|#ffffff|rgba?\(255,\s*255,\s*255"; then
                            : # Color is white - good for dark background
                        else
                            echo -e "  ${YELLOW}⚠${NC} .$CLASS_NAME has dark background but color may not be light enough"
                            echo -e "    ${YELLOW}File:${NC} $css_file:$line_num"
                            echo -e "    ${YELLOW}Color:${NC} $COLOR_VALUE"
                            echo -e "    ${YELLOW}Fix:${NC} Verify color is 'white' or '#fff' for dark backgrounds"
                        fi
                    else
                        echo -e "  ${RED}✗${NC} .$CLASS_NAME has dark background but NO explicit text color"
                        echo -e "    ${RED}File:${NC} $css_file:$line_num"
                        echo -e "    ${RED}Risk:${NC} Will inherit color from parent - likely causes dark-on-dark text"
                        echo -e "    ${RED}Fix:${NC} Add 'color: white !important;' to .$CLASS_NAME"
                        ISSUES_FOUND=$((ISSUES_FOUND + 1))
                    fi
                fi
            fi
        done
    fi
done

echo ""

###############################################################################
# CHECK 3: Explicit Color Contrast Violations
###############################################################################
echo -e "${BLUE}CHECK 3: Explicit Color Contrast Violations${NC}"
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

    # Check for yellow text on dark blue backgrounds
    if echo "$PAGE_CONTENT" | grep -q "background.*gradient.*#003D7A\|background.*gradient.*#002952"; then
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
# CHECK 4: JavaScript-Generated Content Analysis
###############################################################################
echo -e "${BLUE}CHECK 4: JavaScript-Generated Content${NC}"
echo "Analyzing dynamically generated content for contrast issues..."
echo ""

JS_FILES=$(find wp-content/plugins/dave-biggers-policy-manager/assets/js -name "*.js" -type f 2>/dev/null)

for js_file in $JS_FILES; do
    # Look for innerHTML or insertAdjacentHTML with list items or text
    if grep -q "innerHTML.*<li>\|innerHTML.*<p>" "$js_file" 2>/dev/null; then
        echo "Dynamic content generation in: $js_file"

        # Check if the corresponding CSS has proper color settings
        CSS_FILE="${js_file//.js/.css}"
        CSS_FILE="${CSS_FILE//js/css}"

        if [ -f "$CSS_FILE" ]; then
            echo -e "  ${GREEN}✓${NC} Corresponding CSS file exists: $CSS_FILE"
        else
            echo -e "  ${YELLOW}⚠${NC} No corresponding CSS file - ensure parent provides explicit color"
        fi
    fi
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
    echo "  2. Add explicit 'color: white !important;' to all classes with dark backgrounds"
    echo "  3. Test color combinations using: https://webaim.org/resources/contrastchecker/"
    echo "  4. WCAG AA requires:"
    echo "     - 4.5:1 contrast for normal text"
    echo "     - 3.0:1 contrast for large text (18pt+ or 14pt+ bold)"
    echo "  5. Always set text color explicitly - never rely on inheritance"
    echo ""
    exit 1
fi
