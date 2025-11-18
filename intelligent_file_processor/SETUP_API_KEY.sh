#!/bin/bash
# Setup Anthropic API Key for AI Classification

echo "======================================================================"
echo " Anthropic API Key Setup"
echo "======================================================================"
echo ""
echo "To enable AI classification, you need an Anthropic API key."
echo "Get one from: https://console.anthropic.com/settings/keys"
echo ""
echo "Current status:"

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  ✅ API key is set in environment"
else
    echo "  ⚠️  API key is NOT set"
fi

echo ""
echo "To set your API key permanently, add this to ~/.bashrc:"
echo ""
echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
echo ""
echo "Then run: source ~/.bashrc"
echo ""
echo "To set temporarily for this session:"
echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
echo ""
echo "======================================================================"
