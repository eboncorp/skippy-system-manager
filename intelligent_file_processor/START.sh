#!/bin/bash
# Quick Start Script for Intelligent File Processor
# Run this to start the daemon

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
echo "  - Watching: Downloads, claude/downloads, claude/uploads, Scans/Incoming"
echo "  - Min confidence: 75%"
echo "  - Quarantine period: 30 seconds (grace period)"
echo "  - Backups: Enabled (90 days retention)"
echo ""

# Check watched folders exist
echo "Creating watched folders if needed..."
mkdir -p /home/dave/skippy/Downloads
mkdir -p /home/dave/skippy/claude/downloads
mkdir -p /home/dave/skippy/claude/uploads
mkdir -p /home/dave/Scans/Incoming
echo "✅ Folders ready"
echo ""

# Create destination folders
echo "Creating destination folders..."
mkdir -p /home/dave/skippy/rundaverun/documents
mkdir -p /home/dave/skippy/documents/{business,personal,quarantine}
mkdir -p /home/dave/skippy/development/misc
mkdir -p /home/dave/skippy/backups/file_processor
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
