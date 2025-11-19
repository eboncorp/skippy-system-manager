#!/bin/bash
# Quick Start Script for Intelligent File Processor
# Run this to start the daemon

# Export API key for daemon process
if [ -z "$ANTHROPIC_API_KEY" ]; then
    # Try to load from ~/.bashrc
    if grep -q "ANTHROPIC_API_KEY" ~/.bashrc; then
        source ~/.bashrc
    fi
fi

echo "========================================"
echo " Intelligent File Processor v1.0.0 MVP"
echo "========================================"
echo ""

# Check if in correct directory
if [ ! -f "file_processor_daemon.py" ]; then
    echo "❌ Error: Must run from intelligent_file_processor directory"
    echo "   cd /home/dave/skippy/intelligent_file_processor"
    exit 1
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import watchdog; import yaml; import PyPDF2; import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip3 install -r requirements.txt
fi
echo "✅ Dependencies OK"
echo ""

# Show configuration
echo "Configuration:"
echo "  - Watching: operations/downloads, operations/claude/*, operations/scans/incoming, Scans/Incoming"
echo "  - Min confidence: 75%"
echo "  - Quarantine period: 30 seconds (grace period)"
echo "  - Backups: Enabled (90 days retention)"
echo "  - AI Classification: Enabled (Claude API)"
echo ""

# Check watched folders exist
echo "Creating watched folders if needed..."
mkdir -p /home/dave/skippy/operations/downloads
mkdir -p /home/dave/skippy/operations/claude/{downloads,uploads}
mkdir -p /home/dave/skippy/operations/scans/incoming
mkdir -p /home/dave/Scans/Incoming
echo "✅ Folders ready"
echo ""

# Create destination folders
echo "Creating destination folders..."
mkdir -p /home/dave/skippy/business/campaign/documents
mkdir -p /home/dave/skippy/business/eboncorp
mkdir -p /home/dave/skippy/personal
mkdir -p /home/dave/skippy/operations/quarantine
mkdir -p /home/dave/skippy/development/misc
mkdir -p /home/dave/skippy/system/backups/file_processor
mkdir -p /home/dave/skippy/media/photos
mkdir -p /home/dave/skippy/media/videos
echo "✅ Destinations ready"
echo ""

echo "========================================"
echo " Starting Daemon..."
echo "========================================"
echo ""
echo "📁 Drop files in watched folders and they'll be auto-organized!"
echo "⏸️  Press Ctrl+C to stop"
echo ""

# Run daemon
python3 file_processor_daemon.py "$@"
