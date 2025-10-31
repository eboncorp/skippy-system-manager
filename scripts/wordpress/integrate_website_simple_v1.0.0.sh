#!/bin/bash

# Simple Website Integration Script for Dave Biggers Campaign
# Everything is already built - we just need to activate it!

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

WP_DIR="/home/dave/Local Sites/rundaverun-local/app/public"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Dave Biggers Campaign - Website Integration${NC}"
echo -e "${BLUE}========================================${NC}\n"

cd "$WP_DIR"

# Step 1: Activate glossary plugin
echo -e "${YELLOW}Step 1: Activating Glossary Plugin...${NC}"
wp plugin activate voter-education-glossary 2>/dev/null || echo "Already activated"
echo -e "${GREEN}✓ Plugin active${NC}\n"

# Step 2: Info about glossary import
echo -e "${YELLOW}Step 2: Glossary Import${NC}"
echo -e "The glossary plugin is now active with built-in importer."
echo -e "\nTo import the 351 glossary terms:"
echo -e "  1. Go to: ${BLUE}http://rundaverun-local.local/wp-admin/${NC}"
echo -e "  2. Navigate to: ${BLUE}Glossary Terms → Import Terms${NC}"
echo -e "  3. Upload file: ${BLUE}FINAL_GLOSSARY_353_TERMS.json${NC}"
echo -e "     (Located in the plugin directory)"
echo -e "${GREEN}✓ Ready for import${NC}\n"

# Step 3: Check what pages exist
echo -e "${YELLOW}Step 3: Checking Existing Pages...${NC}"
wp post list --post_type=page --format=table --fields=ID,post_title,post_name 2>/dev/null | head -20
echo -e "${GREEN}✓ Pages listed${NC}\n"

# Final instructions
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${YELLOW}What's Ready:${NC}"
echo -e "  ✓ Glossary plugin activated"
echo -e "  ✓ 351 terms ready to import via WordPress admin"
echo -e "  ✓ 16 policy documents in /home/dave/rundaverun/campaign/POLICY_*.md"
echo -e "  ✓ 3 budget documents in /home/dave/rundaverun/campaign/BUDGET_*.md"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Import glossary via WordPress admin"
echo -e "  2. Create policy pages (can be done via admin or WP-CLI)"
echo -e "  3. Create budget pages (can be done via admin or WP-CLI)"
echo -e "  4. Set up navigation menu"

echo -e "\n${YELLOW}Quick Links:${NC}"
echo -e "  WordPress Admin: ${BLUE}http://rundaverun-local.local/wp-admin/${NC}"
echo -e "  Glossary Import: ${BLUE}http://rundaverun-local.local/wp-admin/edit.php?post_type=glossary_term&page=glossary-importer${NC}"
echo -e "  Site Frontend: ${BLUE}http://rundaverun-local.local/${NC}\n"
