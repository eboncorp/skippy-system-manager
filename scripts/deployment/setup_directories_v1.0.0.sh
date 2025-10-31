#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Creating Ethereum Node Setup Directory Structure...${NC}"

# Create base directory
BASE_DIR="ethereum-node-setup"
mkdir -p "$BASE_DIR"
cd "$BASE_DIR"

# Create directory structure
directories=(
    "modules"
    "scripts"
    "docs"
    "configs"
    "configs/systemd"
    "configs/monitoring"
    "configs/security"
    "data"
    "logs"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo -e "${YELLOW}Created directory: $dir${NC}"
done

# Create module files (empty, for you to fill)
module_files=(
    "modules/utils.sh"
    "modules/monitoring_setup.sh"
    "modules/recovery_failover.sh"
    "modules/advanced_logging.sh"
    "modules/security_enhancements.sh"
    "modules/performance_tuning.sh"
    "modules/update_management.sh"
)

for file in "${module_files[@]}"; do
    touch "$file"
    chmod +x "$file"
    echo -e "${YELLOW}Created file: $file${NC}"
done

# Create main script files
main_files=(
    "install.sh"
    "start.sh"
    "stop.sh"
    "status.sh"
)

for file in "${main_files[@]}"; do
    touch "$file"
    chmod +x "$file"
    echo -e "${YELLOW}Created file: $file${NC}"
done

echo -e "${GREEN}Directory structure created successfully!${NC}"
echo
echo "Now you can copy the content from our previous artifacts into these files:"
echo "1. modules/utils.sh                   - Core utilities"
echo "2. modules/monitoring_setup.sh        - Monitoring module"
echo "3. modules/recovery_failover.sh       - Recovery and failover module"
echo "4. modules/advanced_logging.sh        - Advanced logging module"
echo "5. modules/security_enhancements.sh   - Security module"
echo "6. modules/performance_tuning.sh      - Performance tuning module"
echo "7. modules/update_management.sh       - Update management module"
echo "8. install.sh                         - Main installation script"
echo
echo "Directory structure is ready at: $BASE_DIR"
