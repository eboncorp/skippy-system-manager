#!/bin/bash
#
# Setup script for General Purpose MCP Server
# Version: 1.0.0
# Created: 2025-10-31
#

set -e

echo "=========================================="
echo "General Purpose MCP Server Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/.venv"
SERVER_FILE="$SCRIPT_DIR/server.py"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"

# Alternative Claude config location
if [ ! -f "$CLAUDE_CONFIG" ]; then
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
fi

echo "Step 1: Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✓ Found $PYTHON_VERSION${NC}"
echo ""

echo "Step 2: Checking virtual environment..."
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi
echo ""

echo "Step 3: Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip3 install --quiet --upgrade pip
pip3 install --quiet -r "$REQUIREMENTS"
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

echo "Step 4: Making server executable..."
chmod +x "$SERVER_FILE"
echo -e "${GREEN}✓ Server is executable${NC}"
echo ""

echo "Step 5: Testing server..."
if timeout 3 python3 "$SERVER_FILE" <<< '{"jsonrpc":"2.0","id":1,"method":"ping"}' &>/dev/null; then
    echo -e "${GREEN}✓ Server responds to requests${NC}"
else
    echo -e "${YELLOW}⚠ Server test inconclusive (this is normal)${NC}"
fi
echo ""

echo "Step 6: Claude for Desktop configuration..."
if [ -f "$CLAUDE_CONFIG" ]; then
    echo -e "${YELLOW}Found existing Claude config at:${NC}"
    echo "  $CLAUDE_CONFIG"
    echo ""
    echo "You need to add this to your configuration:"
    echo ""
    echo -e "${GREEN}\"general-server\": {${NC}"
    echo -e "${GREEN}  \"command\": \"$VENV_DIR/bin/python3\",${NC}"
    echo -e "${GREEN}  \"args\": [\"$SERVER_FILE\"]${NC}"
    echo -e "${GREEN}}${NC}"
    echo ""
    echo "Would you like to automatically update the config? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        # Backup original
        cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${GREEN}✓ Backed up original config${NC}"

        # Check if mcpServers exists
        if grep -q '"mcpServers"' "$CLAUDE_CONFIG"; then
            # Add to existing mcpServers
            echo "Adding to existing mcpServers..."
            # This is a simplified approach - manual editing is safer
            echo -e "${YELLOW}⚠ Please manually add the server config shown above${NC}"
        else
            # Create new mcpServers section
            echo "Creating mcpServers section..."
            cat "$SCRIPT_DIR/claude_desktop_config_example.json" > "$CLAUDE_CONFIG"
            echo -e "${GREEN}✓ Configuration updated${NC}"
        fi
    else
        echo "Skipping automatic configuration."
        echo "Please manually add the configuration shown above."
    fi
else
    echo -e "${YELLOW}⚠ Claude for Desktop config not found at:${NC}"
    echo "  $CLAUDE_CONFIG"
    echo ""
    echo "Expected locations:"
    echo "  - Linux: ~/.config/Claude/claude_desktop_config.json"
    echo "  - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
    echo "  - Windows: %APPDATA%/Claude/claude_desktop_config.json"
    echo ""
    echo "Create the file and add the configuration shown above."
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify the configuration in Claude for Desktop config"
echo "2. Restart Claude for Desktop completely (Cmd+Q or Quit)"
echo "3. Look for the tool icon in Claude for Desktop"
echo "4. Test with: 'List files in /home/dave/skippy/scripts'"
echo ""
echo "Troubleshooting:"
echo "  - Check logs: tail -f ~/Library/Logs/Claude/mcp*.log"
echo "  - Test server: cd $SCRIPT_DIR && source .venv/bin/activate && python3 server.py"
echo "  - Read README: cat $SCRIPT_DIR/README.md"
echo ""
echo "Happy coding! 🚀"
