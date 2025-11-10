#!/bin/bash
###############################################################################
# WordPress Color Contrast Checker
# Version: 1.0.0
# Created: 2025-11-08
#
# Description:
#   Scans WordPress pages for WCAG 2.1 AA color contrast violations
#   Detects text that blends into backgrounds (invisible text)
#
# Usage:
#   bash wordpress_color_contrast_checker_v1.0.0.sh [page_ids...]
#
# Examples:
#   bash wordpress_color_contrast_checker_v1.0.0.sh 105
#   bash wordpress_color_contrast_checker_v1.0.0.sh 105 107 337
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

echo -e "${BLUE}=== WordPress Color Contrast Checker ===${NC}"
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

# Function to calculate relative luminance
calculate_luminance() {
    local r=$1 g=$2 b=$3

    # Use Python for precise floating point math
    python3 -c "
r, g, b = $r / 255.0, $g / 255.0, $b / 255.0

def gamma(c):
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

r_lin = gamma(r)
g_lin = gamma(g)
b_lin = gamma(b)

luminance = 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin
print(f'{luminance:.6f}')
"
}

# Function to calculate contrast ratio
calculate_contrast() {
    local color1="$1"
    local color2="$2"

    read -r r1 g1 b1 <<< "$(hex_to_rgb "$color1")"
    read -r r2 g2 b2 <<< "$(hex_to_rgb "$color2")"

    local l1=$(calculate_luminance "$r1" "$g1" "$b1")
    local l2=$(calculate_luminance "$r2" "$g2" "$b2")

    python3 -c "
l1, l2 = $l1 + 0.05, $l2 + 0.05
ratio = max(l1, l2) / min(l1, l2)
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

# Main checking loop
for page_id in $PAGE_IDS; do
    if ! wp post get "$page_id" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC} Page $page_id not found, skipping"
        continue
    fi

    PAGE_TITLE=$(wp post get "$page_id" --field=post_title 2>/dev/null)
    echo -e "${BLUE}Checking Page $page_id: $PAGE_TITLE${NC}"

    # Get page content
    PAGE_CONTENT=$(wp post get "$page_id" --field=post_content 2>/dev/null)

    # Extract inline styles with color specifications
    # Look for patterns like: style="...color: #HEX...background: ...#HEX..."
    echo "$PAGE_CONTENT" | grep -oP 'style="[^"]*"' | while read -r style_block; do
        # Extract foreground color
        FG_COLOR=$(echo "$style_block" | grep -oP '(?<=color:\s)(#[0-9A-Fa-f]{3,6}|[^;]+)' | grep -oP '#[0-9A-Fa-f]{3,6}' | head -1)

        # Extract background color (including gradients)
        BG_COLOR=$(echo "$style_block" | grep -oP '(?<=background[^:]*:\s)[^;]+' | grep -oP '#[0-9A-Fa-f]{3,6}' | head -1)

        # If we have both colors, check contrast
        if [ -n "$FG_COLOR" ] && [ -n "$BG_COLOR" ]; then
            # Normalize colors (add # if missing)
            [[ "$FG_COLOR" != \#* ]] && FG_COLOR="#$FG_COLOR"
            [[ "$BG_COLOR" != \#* ]] && BG_COLOR="#$BG_COLOR"

            # Calculate contrast
            RATIO=$(calculate_contrast "$FG_COLOR" "$BG_COLOR")
            WCAG=$(check_wcag "$RATIO")

            # Report results
            if [ "$WCAG" = "FAIL" ]; then
                echo -e "  ${RED}✗ FAIL${NC} Text $FG_COLOR on background $BG_COLOR"
                echo -e "    Contrast ratio: ${RATIO}:1 (needs 4.5:1 for WCAG AA)"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            elif [ "$WCAG" = "WARN" ]; then
                echo -e "  ${YELLOW}⚠ WARN${NC} Text $FG_COLOR on background $BG_COLOR"
                echo -e "    Contrast ratio: ${RATIO}:1 (OK for large text only, needs 4.5:1 for normal)"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            fi

            # Check for invisible text (same colors)
            if [ "$FG_COLOR" = "$BG_COLOR" ]; then
                echo -e "  ${RED}✗ INVISIBLE TEXT${NC} Text and background are the same color: $FG_COLOR"
                ISSUES_FOUND=$((ISSUES_FOUND + 1))
            fi
        fi
    done

    # Check for specific known problematic combinations
    YELLOW_ON_BLUE=$(echo "$PAGE_CONTENT" | grep -c 'color:\s*#FFC72C.*background.*#003D7A\|color:\s*#FFC72C.*background.*#002952' || echo 0)
    if [ "$YELLOW_ON_BLUE" -gt 0 ]; then
        RATIO=$(calculate_contrast "#FFC72C" "#003D7A")
        echo -e "  ${RED}✗ FAIL${NC} Found campaign yellow (#FFC72C) on dark blue (#003D7A)"
        echo -e "    Contrast ratio: ${RATIO}:1 (needs 4.5:1 for WCAG AA)"
        echo -e "    Occurrences: $YELLOW_ON_BLUE"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    fi

    echo ""
done

# Summary
echo -e "${BLUE}=== Summary ===${NC}"
if [ "$ISSUES_FOUND" -eq 0 ]; then
    echo -e "${GREEN}✓ No color contrast issues found${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $ISSUES_FOUND color contrast issues${NC}"
    echo ""
    echo "Recommendations:"
    echo "  1. Use darker text colors or lighter backgrounds"
    echo "  2. Test with online tools: https://webaim.org/resources/contrastchecker/"
    echo "  3. WCAG AA requires 4.5:1 contrast for normal text, 3:1 for large text"
    exit 1
fi
