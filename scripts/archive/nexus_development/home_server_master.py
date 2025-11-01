#!/usr/bin/env python3
"""
HP Z4 G4 Home Server Master
A simple web-based server management interface
"""
import os
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
import http.server
import socketserver
import subprocess
import json

class HomeServerMaster:
    def __init__(self):
        self.version = "1.0.0"
        self.start_time = datetime.now()
        self.hostname = os.uname().nodename
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("HomeServerMaster")
        
    def get_system_info(self):
        """Get basic system information"""
        try:
            # Get system stats
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().split()[:3]
            
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                
            # Parse memory info
            mem_total = None
            mem_available = None
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) // 1024  # Convert to MB
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) // 1024  # Convert to MB
                    
            # Get disk usage
            disk_info = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            disk_usage = disk_info.stdout.split('\n')[1].split()
            
            return {
                'hostname': self.hostname,
                'uptime': str(datetime.now() - self.start_time),
                'load_avg': load_avg,
                'memory': {
                    'total': f"{mem_total}MB" if mem_total else "Unknown",
                    'available': f"{mem_available}MB" if mem_available else "Unknown"
                },
                'disk': {
                    'size': disk_usage[1] if len(disk_usage) > 1 else "Unknown",
                    'used': disk_usage[2] if len(disk_usage) > 2 else "Unknown",
                    'free': disk_usage[3] if len(disk_usage) > 3 else "Unknown"
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {'error': str(e)}

    def generate_html(self):
        """Generate the main dashboard HTML"""
        sys_info = self.get_system_info()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HP Z4 G4 Home Server</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .stat-card h3 {{
            margin: 0 0 15px 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #FFD700;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }}
        .services {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }}
        .refresh-btn {{
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
            transition: transform 0.2s;
        }}
        .refresh-btn:hover {{
            transform: scale(1.05);
        }}
        .status-online {{
            color: #4ECDC4;
            font-weight: bold;
        }}
    </style>
    <script>
        function refreshPage() {{
            location.reload();
        }}
        
        // Auto-refresh every 30 seconds
        setInterval(refreshPage, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ HP Z4 G4 Home Server</h1>
            <p>High-Performance Workstation Server</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>🏠 Hostname</h3>
                <div class="stat-value">{sys_info.get('hostname', 'Unknown')}</div>
            </div>
            
            <div class="stat-card">
                <h3>⏱️ Uptime</h3>
                <div class="stat-value">{sys_info.get('uptime', 'Unknown')}</div>
            </div>
            
            <div class="stat-card">
                <h3>💾 Memory</h3>
                <div class="stat-value">{sys_info.get('memory', {}).get('available', 'Unknown')} free</div>
                <small>of {sys_info.get('memory', {}).get('total', 'Unknown')} total</small>
            </div>
            
            <div class="stat-card">
                <h3>💽 Disk Space</h3>
                <div class="stat-value">{sys_info.get('disk', {}).get('free', 'Unknown')} free</div>
                <small>of {sys_info.get('disk', {}).get('size', 'Unknown')} total</small>
            </div>
        </div>
        
        <div class="services">
            <h2>📋 Server Status</h2>
            <p><span class="status-online">● ONLINE</span> - Home Server Master v{self.version}</p>
            <p><strong>Started:</strong> {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Access URL:</strong> http://10.0.0.29:8080</p>
            <p><strong>Local Access:</strong> http://{self.hostname}.local:8080</p>
            
            <h3>📊 Load Average</h3>
            <p>1min: {sys_info.get('load_avg', ['?'])[0]} | 5min: {sys_info.get('load_avg', ['?', '?'])[1] if len(sys_info.get('load_avg', [])) > 1 else '?'} | 15min: {sys_info.get('load_avg', ['?', '?', '?'])[2] if len(sys_info.get('load_avg', [])) > 2 else '?'}</p>
            
            <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh Stats</button>
        </div>
        
        <div class="services">
            <h2>🛠️ Quick Actions</h2>
            <p>• SSH Access: <code>ssh ebon@10.0.0.29</code></p>
            <p>• System Info: <code>htop</code> or <code>systemctl status</code></p>
            <p>• View Logs: <code>journalctl -f</code></p>
        </div>
    </div>
</body>
</html>"""
        return html

    def start_web_server(self):
        """Start the web server"""
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, server_instance=None, **kwargs):
                self.server_instance = server_instance
                super().__init__(*args, **kwargs)
                
            def do_GET(self):
                if self.path == '/' or self.path == '/index.html':
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    html = self.server_instance.generate_html()
                    self.wfile.write(html.encode())
                elif self.path == '/api/status':
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    status = {
                        'status': 'online',
                        'version': self.server_instance.version,
                        'uptime': str(datetime.now() - self.server_instance.start_time),
                        'system': self.server_instance.get_system_info()
                    }
                    self.wfile.write(json.dumps(status, indent=2).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"404 Not Found")
                    
            def log_message(self, format, *args):
                # Custom logging to reduce noise
                if '200' in str(args[1]):
                    return  # Don't log successful requests
                super().log_message(format, *args)

        try:
            handler = lambda *args, **kwargs: Handler(*args, server_instance=self, **kwargs)
            with socketserver.TCPServer(("", 8080), handler) as httpd:
                self.logger.info(f"🚀 HP Z4 G4 Home Server started!")
                self.logger.info(f"📍 Web interface: http://10.0.0.29:8080")
                self.logger.info(f"🏠 Local access: http://{self.hostname}.local:8080")
                self.logger.info(f"⚡ Server version: {self.version}")
                httpd.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")

    def start(self):
        """Start the Home Server Master"""
        self.logger.info("Starting HP Z4 G4 Home Server Master...")
        self.start_web_server()

if __name__ == "__main__":
    server = HomeServerMaster()
    server.start()
