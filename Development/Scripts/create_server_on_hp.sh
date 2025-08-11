#!/bin/bash
# Script to create Home Server Master directly on HP Z4 G4
# Run this on the HP server: wget -O- https://pastebin.com/raw/XXXXX | bash

echo "🚀 Creating Home Server Master on HP Z4 G4"
echo "=========================================="

# First, create the main Home Server Master program
cat > /tmp/home_server_master.py << 'EOF'
#!/usr/bin/env python3
"""
Home Server Master Controller v1.0
Unified management system for HP Z4 G4 server
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading
import queue

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class ServerConfig:
    """Server configuration"""
    def __init__(self):
        self.server_name = "HP-Z4-G4-Server"
        self.server_port = 8080
        self.enable_web_ui = True
        self.enable_monitoring = True
        self.data_dir = Path.home() / ".home-server"
        self.log_dir = Path.home() / ".home-server" / "logs"
        self.config_dir = Path.home() / ".home-server" / "config"

class HomeServerMaster:
    """Main server controller for HP Z4 G4"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.start_time = datetime.now()
        self.config = ServerConfig()
        
        # Setup directories
        self.setup_directories()
        self.setup_logging()
        
        self.logger.info(f"Home Server Master v{self.version} starting on HP Z4 G4")
        
        # Runtime state
        self.running = False
        self.services = {}
        
    def setup_directories(self):
        """Create necessary directories"""
        for dir_path in [self.config.data_dir, self.config.log_dir, self.config.config_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def setup_logging(self):
        """Configure logging"""
        log_file = self.config.log_dir / f"server-{datetime.now():%Y%m%d}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("HomeServerMaster")
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        info = {
            'hostname': os.uname().nodename,
            'system': f"{os.uname().sysname} {os.uname().release}",
            'uptime': (datetime.now() - self.start_time).total_seconds()
        }
        
        if PSUTIL_AVAILABLE:
            info.update({
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'percent': psutil.virtual_memory().percent,
                    'available': psutil.virtual_memory().available,
                    'total': psutil.virtual_memory().total
                },
                'disk': {
                    'percent': psutil.disk_usage('/').percent,
                    'free': psutil.disk_usage('/').free,
                    'total': psutil.disk_usage('/').total
                }
            })
            
        return info
        
    def start_web_server(self):
        """Start simple web server"""
        try:
            import http.server
            import socketserver
            from threading import Thread
            
            class ServerHandler(http.server.SimpleHTTPRequestHandler):
                def do_GET(self):
                    if self.path == '/':
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>HP Z4 G4 Home Server</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                                .info {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
                                .metric {{ margin: 10px 0; }}
                            </style>
                        </head>
                        <body>
                            <div class="header">
                                <h1>🖥️ HP Z4 G4 Home Server</h1>
                                <p>Unified Management System v{self.version}</p>
                            </div>
                            
                            <div class="info">
                                <h2>📊 System Information</h2>
                                <div class="metric"><strong>Hostname:</strong> {os.uname().nodename}</div>
                                <div class="metric"><strong>System:</strong> {os.uname().sysname} {os.uname().release}</div>
                                <div class="metric"><strong>Uptime:</strong> {(datetime.now() - self.start_time).total_seconds():.0f} seconds</div>
                                <div class="metric"><strong>Server Started:</strong> {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                            </div>
                            
                            <div class="info">
                                <h2>🔧 Available Services</h2>
                                <div class="metric">• Web Management Interface (This page)</div>
                                <div class="metric">• SSH Access: ssh ebon@10.0.0.29</div>
                                <div class="metric">• System Monitoring</div>
                                <div class="metric">• Docker Container Management</div>
                            </div>
                            
                            <div class="info">
                                <h2>📈 Quick Stats</h2>
                                <div class="metric">Server ready for additional services</div>
                                <div class="metric">Perfect platform for Ethereum nodes, cloud sync, and more</div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        self.wfile.write(html.encode())
                    else:
                        super().do_GET()
            
            with socketserver.TCPServer(("", self.config.server_port), ServerHandler) as httpd:
                self.logger.info(f"Web server started on port {self.config.server_port}")
                httpd.serve_forever()
                
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            
    def start(self):
        """Start the server"""
        self.logger.info("Starting Home Server Master...")
        self.running = True
        
        # Start web server in background
        web_thread = threading.Thread(target=self.start_web_server, daemon=True)
        web_thread.start()
        
        self.logger.info("Home Server Master started successfully")
        self.logger.info(f"Web interface available at: http://10.0.0.29:{self.config.server_port}")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Stop the server"""
        self.logger.info("Stopping Home Server Master...")
        self.running = False
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='HP Z4 G4 Home Server Master')
    parser.add_argument('command', choices=['start', 'status'], help='Command to run')
    parser.add_argument('--port', type=int, default=8080, help='Web server port')
    
    args = parser.parse_args()
    
    server = HomeServerMaster()
    
    if args.command == 'start':
        signal.signal(signal.SIGINT, server.signal_handler)
        signal.signal(signal.SIGTERM, server.signal_handler)
        server.config.server_port = args.port
        server.start()
    elif args.command == 'status':
        info = server.get_system_info()
        print(json.dumps(info, indent=2, default=str))
EOF

# Create installer script
cat > /tmp/home_server_installer.sh << 'EOF'
#!/bin/bash
# Home Server Master Installer for HP Z4 G4

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="$HOME/.home-server"
BIN_DIR="$HOME/.local/bin"

echo -e "${BLUE}🏠 Installing Home Server Master on HP Z4 G4${NC}"
echo "=============================================="

# Create directories
mkdir -p "$INSTALL_DIR"/{logs,data,config} "$BIN_DIR"

# Copy main program
cp /tmp/home_server_master.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/home_server_master.py"

# Create wrapper script
cat > "$BIN_DIR/home-server" << 'WRAPPER_EOF'
#!/bin/bash
exec python3 "$HOME/.home-server/home_server_master.py" "$@"
WRAPPER_EOF
chmod +x "$BIN_DIR/home-server"

# Add to PATH
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.bashrc"
    echo -e "${YELLOW}Added $BIN_DIR to PATH. Run: source ~/.bashrc${NC}"
fi

# Create systemd service
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/home-server.service" << 'SERVICE_EOF'
[Unit]
Description=HP Z4 G4 Home Server Master
After=network-online.target

[Service]
Type=simple
ExecStart=/home/ebon/.local/bin/home-server start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
SERVICE_EOF

systemctl --user daemon-reload

echo -e "${GREEN}✅ Installation complete!${NC}"
echo
echo "🚀 To start the server:"
echo "  source ~/.bashrc"
echo "  home-server start"
echo
echo "🌐 Web interface will be available at:"
echo "  http://10.0.0.29:8080"
echo
echo "⚙️ To enable automatic startup:"
echo "  systemctl --user enable home-server.service"
echo "  systemctl --user start home-server.service"
EOF

chmod +x /tmp/home_server_installer.sh

echo "✅ Home Server Master files created!"
echo
echo "📋 Next steps on HP Z4 G4:"
echo "1. Run: /tmp/home_server_installer.sh"
echo "2. Run: source ~/.bashrc"
echo "3. Run: home-server start"
echo "4. Access: http://10.0.0.29:8080"