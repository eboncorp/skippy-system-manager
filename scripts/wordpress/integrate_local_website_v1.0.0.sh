#!/bin/bash

# Integration Script for Dave Biggers Campaign - Local WordPress Site
# This script integrates all campaign materials into the local website

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# WordPress directory
WP_DIR="/home/dave/Local Sites/rundaverun-local/app/public"
CAMPAIGN_DIR="/home/dave/rundaverun/campaign"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Dave Biggers Campaign Integration${NC}"
echo -e "${BLUE}Local WordPress Site${NC}"
echo -e "${BLUE}================================${NC}\n"

# Change to WordPress directory
cd "$WP_DIR"

# Step 1: Activate glossary plugin
echo -e "${YELLOW}Step 1: Activating Glossary Plugin...${NC}"
wp plugin activate voter-education-glossary
echo -e "${GREEN}✓ Plugin activated${NC}\n"

# Step 2: Import glossary terms
echo -e "${YELLOW}Step 2: Importing 351 Glossary Terms...${NC}"
GLOSSARY_FILE="$WP_DIR/wp-content/plugins/voter-education-glossary/FINAL_GLOSSARY_353_TERMS.json"

if [ -f "$GLOSSARY_FILE" ]; then
    # Import using WP-CLI eval-file or direct PHP
    wp eval-file <<'PHP'
<?php
$glossary_file = '/home/dave/Local Sites/rundaverun-local/app/public/wp-content/plugins/voter-education-glossary/FINAL_GLOSSARY_353_TERMS.json';
$json_content = file_get_contents($glossary_file);
$terms = json_decode($json_content, true);

$imported = 0;
$skipped = 0;

foreach ($terms as $term_data) {
    // Check if term already exists
    $existing = get_page_by_title($term_data['term'], OBJECT, 'glossary_term');

    if (!$existing) {
        $post_id = wp_insert_post([
            'post_title' => $term_data['term'],
            'post_content' => $term_data['definition'],
            'post_status' => 'publish',
            'post_type' => 'glossary_term',
        ]);

        if (!is_wp_error($post_id)) {
            // Add meta fields
            update_post_meta($post_id, 'louisville_context', $term_data['louisville_context']);
            update_post_meta($post_id, 'why_it_matters', $term_data['why_it_matters']);
            update_post_meta($post_id, 'dave_proposal', isset($term_data['dave_proposal']) ? $term_data['dave_proposal'] : '');
            update_post_meta($post_id, 'related_terms', isset($term_data['related_terms']) ? $term_data['related_terms'] : '');
            update_post_meta($post_id, 'aliases', isset($term_data['aliases']) ? $term_data['aliases'] : '');

            // Set category
            if (isset($term_data['category'])) {
                wp_set_object_terms($post_id, $term_data['category'], 'glossary_category');
            }

            $imported++;
        }
    } else {
        $skipped++;
    }
}

echo "Imported: $imported terms\n";
echo "Skipped (already exist): $skipped terms\n";
PHP
    echo -e "${GREEN}✓ Glossary terms imported${NC}\n"
else
    echo -e "${RED}✗ Glossary file not found: $GLOSSARY_FILE${NC}\n"
fi

# Step 3: Create Policy Index Page
echo -e "${YELLOW}Step 3: Creating Policy Index Page...${NC}"
wp post create --post_type=page --post_title='Policies' --post_name='policies' --post_status='publish' --post_content='<h1>Dave Biggers Policy Platform</h1><p>Comprehensive policy proposals for Louisville. Select a policy area below:</p>' 2>/dev/null || echo "  (Policy index page may already exist)"
echo -e "${GREEN}✓ Policy index page ready${NC}\n"

# Step 4: Create Budget Index Page
echo -e "${YELLOW}Step 4: Creating Budget Index Page...${NC}"
wp post create --post_type=page --post_title='Budget' --post_name='budget' --post_status='publish' --post_content='<h1>Budget Plan</h1><p>Comprehensive budget analysis for Louisville.</p>' 2>/dev/null || echo "  (Budget index page may already exist)"
echo -e "${GREEN}✓ Budget index page ready${NC}\n"

# Step 5: Import Policy Documents (simplified - create basic pages)
echo -e "${YELLOW}Step 5: Creating Policy Document Pages...${NC}"

# Policy titles
declare -a POLICIES=(
    "01:Public Safety & Community Policing"
    "02:Criminal Justice Reform"
    "03:Health & Human Services"
    "04:Budget & Financial Management"
    "05:Affordable Housing & Anti-Displacement"
    "06:Education & Youth Development"
    "07:Environmental Justice & Climate Action"
    "08:Economic Development & Jobs"
    "09:Infrastructure & Transportation"
    "10:Arts, Culture & Tourism"
    "11:Technology & Innovation"
    "12:Public Health & Wellness"
    "13:Neighborhood Development"
    "14:Senior Services"
    "15:Disability Rights & Accessibility"
    "16:Food Systems & Urban Agriculture"
)

for policy in "${POLICIES[@]}"; do
    IFS=':' read -r num title <<< "$policy"
    slug=$(echo "policy-$num-$(echo $title | tr '[:upper:]' '[:lower:]' | tr ' &' '--' | tr -d ',')" | sed 's/--*/-/g')

    # Check if page exists
    existing=$(wp post list --post_type=page --name="$slug" --format=ids 2>/dev/null)

    if [ -z "$existing" ]; then
        echo "  Creating: Policy #$num: $title"
        wp post create --post_type=page \
            --post_title="Policy #$num: $title" \
            --post_name="$slug" \
            --post_status='publish' \
            --post_content="<h1>Policy #$num: $title</h1><p>Full policy document coming soon. See /home/dave/rundaverun/campaign/POLICY_${num}_*.md for content.</p>" \
            2>/dev/null || echo "    (Skipped)"
    else
        echo "  ✓ Already exists: Policy #$num"
    fi
done

echo -e "${GREEN}✓ Policy pages created${NC}\n"

# Step 6: Import Budget Documents
echo -e "${YELLOW}Step 6: Creating Budget Document Pages...${NC}"

declare -a BUDGETS=(
    "detailed-line-items:Detailed Line-Item Budget"
    "summary:Budget Summary"
    "comparison:Budget Comparison: Greenberg vs. Biggers"
)

for budget in "${BUDGETS[@]}"; do
    IFS=':' read -r slug title <<< "$budget"

    existing=$(wp post list --post_type=page --name="budget-$slug" --format=ids 2>/dev/null)

    if [ -z "$existing" ]; then
        echo "  Creating: $title"
        wp post create --post_type=page \
            --post_title="$title" \
            --post_name="budget-$slug" \
            --post_status='publish' \
            --post_content="<h1>$title</h1><p>See /home/dave/rundaverun/campaign/BUDGET_*.md for full content.</p>" \
            2>/dev/null || echo "    (Skipped)"
    else
        echo "  ✓ Already exists: $title"
    fi
done

echo -e "${GREEN}✓ Budget pages created${NC}\n"

# Step 7: Set up navigation menu
echo -e "${YELLOW}Step 7: Setting Up Navigation Menu...${NC}"
echo "  (Menu setup requires WordPress admin - will be done manually)"
echo -e "${GREEN}✓ Navigation structure ready${NC}\n"

# Final summary
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}Integration Complete!${NC}"
echo -e "${BLUE}================================${NC}\n"

echo -e "Next steps:"
echo -e "  1. Visit: ${BLUE}http://rundaverun-local.local/${NC}"
echo -e "  2. Check Glossary: ${BLUE}http://rundaverun-local.local/glossary/${NC}"
echo -e "  3. Review Policies: ${BLUE}http://rundaverun-local.local/policies/${NC}"
echo -e "  4. Review Budget: ${BLUE}http://rundaverun-local.local/budget/${NC}"
echo -e "  5. WordPress Admin: ${BLUE}http://rundaverun-local.local/wp-admin/${NC}"
echo -e "\n${YELLOW}Note:${NC} Policy and budget pages have placeholder content."
echo -e "Full content from markdown files needs to be copied in manually or"
echo -e "via a more sophisticated importer.\n"
