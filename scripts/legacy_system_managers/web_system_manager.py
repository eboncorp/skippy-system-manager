#!/usr/bin/env python3
"""
Web-Based System Manager v4.0
A comprehensive web interface for remote system management
Extends the Advanced System Manager with web capabilities
"""

import os
import sys
import json
import sqlite3
import subprocess
import threading
import time
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import signal

# Web framework imports with fallbacks
try:
    from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# System monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Configuration management
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

@dataclass
class ServerInfo:
    """Information about a managed server"""
    hostname: str
    ip_address: str
    port: int
    status: str
    last_seen: datetime
    system_info: Dict[str, Any]
    
class WebSystemManager:
    """Web-based system manager with remote capabilities"""
    
    def __init__(self):
        self.version = "4.0"
        self.base_path = Path.home() / ".unified-system-manager"
        self.web_config_path = self.base_path / "web-config.json"
        self.db_path = self.base_path / "web-system.db"
        
        # Ensure directories exist
        self.base_path.mkdir(exist_ok=True)
        
        # Initialize logging
        self.setup_logging()
        
        # Initialize database
        self.init_database()
        
        # Load configuration
        self.config = self.load_web_config()
        
        # Initialize Flask app if available
        if FLASK_AVAILABLE:
            self.app = Flask(__name__)
            self.app.secret_key = self.config.get('secret_key', secrets.token_hex(32))
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            self.setup_routes()
        else:
            self.app = None
            self.socketio = None
            self.logger.warning("Flask not available - web interface disabled")
        
        # Server management
        self.managed_servers = {}
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Authentication
        self.users = self.load_users()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_path = self.base_path / "logs"
        log_path.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path / "web-manager.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def init_database(self):
        """Initialize SQLite database for web management"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Servers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT UNIQUE NOT NULL,
                    ip_address TEXT NOT NULL,
                    port INTEGER DEFAULT 22,
                    status TEXT DEFAULT 'offline',
                    last_seen TIMESTAMP,
                    system_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Web sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS web_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Remote commands table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS remote_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    command TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_at TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            """)
            
            # Monitoring alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            """)
            
            conn.commit()
    
    def load_web_config(self) -> Dict[str, Any]:
        """Load web configuration"""
        default_config = {
            'host': '0.0.0.0',
            'port': 8080,
            'debug': False,
            'secret_key': secrets.token_hex(32),
            'auth_required': True,
            'session_timeout': 3600,  # 1 hour
            'monitoring_interval': 60,  # 1 minute
            'max_servers': 50,
            'ssl_enabled': False,
            'ssl_cert': '',
            'ssl_key': ''
        }
        
        if self.web_config_path.exists():
            try:
                with open(self.web_config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
            except Exception as e:
                self.logger.warning(f"Failed to load web config: {e}")
        
        # Save current config
        self.save_web_config(default_config)
        return default_config
    
    def save_web_config(self, config: Dict[str, Any]):
        """Save web configuration"""
        try:
            with open(self.web_config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save web config: {e}")
    
    def load_users(self) -> Dict[str, str]:
        """Load user credentials (hashed passwords)"""
        users_path = self.base_path / "users.json"
        default_users = {
            'admin': self.hash_password('admin123')  # Default admin user
        }
        
        if users_path.exists():
            try:
                with open(users_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load users: {e}")
        
        # Save default users
        try:
            with open(users_path, 'w') as f:
                json.dump(default_users, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save users: {e}")
            
        return default_users
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verify user password"""
        if username not in self.users:
            return False
        return self.users[username] == self.hash_password(password)
    
    def setup_routes(self):
        """Setup Flask routes"""
        if not self.app:
            return
            
        @self.app.route('/')
        def index():
            if self.config['auth_required'] and 'username' not in session:
                return redirect(url_for('login'))
            return render_template_string(self.get_dashboard_template())
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                
                if self.verify_password(username, password):
                    session['username'] = username
                    session['login_time'] = time.time()
                    self.logger.info(f"User {username} logged in from {request.remote_addr}")
                    return redirect(url_for('index'))
                else:
                    self.logger.warning(f"Failed login attempt for {username} from {request.remote_addr}")
                    return render_template_string(self.get_login_template(), error="Invalid credentials")
            
            return render_template_string(self.get_login_template())
        
        @self.app.route('/logout')
        def logout():
            username = session.get('username', 'Unknown')
            session.clear()
            self.logger.info(f"User {username} logged out")
            return redirect(url_for('login'))
        
        @self.app.route('/api/servers')
        def api_servers():
            if not self.check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            return jsonify(self.get_servers())
        
        @self.app.route('/api/servers/<int:server_id>/command', methods=['POST'])
        def api_execute_command(server_id):
            if not self.check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            
            command = request.json.get('command')
            if not command:
                return jsonify({'error': 'Command required'}), 400
            
            result = self.execute_remote_command(server_id, command)
            return jsonify(result)
        
        @self.app.route('/api/system/info')
        def api_system_info():
            if not self.check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            return jsonify(self.get_system_info())
        
        @self.app.route('/api/monitoring/start', methods=['POST'])
        def api_start_monitoring():
            if not self.check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            
            self.start_monitoring()
            return jsonify({'status': 'Monitoring started'})
        
        @self.app.route('/api/monitoring/stop', methods=['POST'])
        def api_stop_monitoring():
            if not self.check_auth():
                return jsonify({'error': 'Unauthorized'}), 401
            
            self.stop_monitoring()
            return jsonify({'status': 'Monitoring stopped'})
        
        # SocketIO events
        if self.socketio:
            @self.socketio.on('connect')
            def handle_connect():
                if self.config['auth_required'] and 'username' not in session:
                    return False
                emit('status', {'message': 'Connected to Web System Manager'})
            
            @self.socketio.on('get_real_time_data')
            def handle_real_time_data():
                if not self.check_auth():
                    return
                emit('real_time_data', self.get_real_time_data())
    
    def check_auth(self) -> bool:
        """Check if user is authenticated"""
        if not self.config['auth_required']:
            return True
        
        if 'username' not in session:
            return False
        
        # Check session timeout
        login_time = session.get('login_time', 0)
        if time.time() - login_time > self.config['session_timeout']:
            session.clear()
            return False
        
        return True
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """Get list of managed servers"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, hostname, ip_address, port, status, last_seen, system_info
                FROM servers ORDER BY hostname
            """)
            
            servers = []
            for row in cursor.fetchall():
                server = {
                    'id': row[0],
                    'hostname': row[1],
                    'ip_address': row[2],
                    'port': row[3],
                    'status': row[4],
                    'last_seen': row[5],
                    'system_info': json.loads(row[6]) if row[6] else {}
                }
                servers.append(server)
            
            return servers
    
    def add_server(self, hostname: str, ip_address: str, port: int = 22) -> bool:
        """Add a new server to management"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO servers (hostname, ip_address, port)
                    VALUES (?, ?, ?)
                """, (hostname, ip_address, port))
                conn.commit()
                
                self.logger.info(f"Added server: {hostname} ({ip_address}:{port})")
                return True
        except sqlite3.IntegrityError:
            self.logger.warning(f"Server {hostname} already exists")
            return False
        except Exception as e:
            self.logger.error(f"Failed to add server: {e}")
            return False
    
    def execute_remote_command(self, server_id: int, command: str) -> Dict[str, Any]:
        """Execute command on remote server"""
        # For now, execute locally as proof of concept
        # In production, this would use SSH or other remote execution methods
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            command_result = {
                'command': command,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO remote_commands (server_id, command, status, result, executed_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (server_id, command, 'completed', json.dumps(command_result), datetime.now()))
                conn.commit()
            
            return command_result
            
        except subprocess.TimeoutExpired:
            error_result = {
                'command': command,
                'error': 'Command timed out',
                'timestamp': datetime.now().isoformat()
            }
            return error_result
        except Exception as e:
            error_result = {
                'command': command,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return error_result
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        info = {
            'hostname': os.uname().nodename,
            'platform': os.uname().sysname,
            'kernel': os.uname().release,
            'architecture': os.uname().machine,
            'timestamp': datetime.now().isoformat()
        }
        
        if PSUTIL_AVAILABLE:
            info.update({
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'available': psutil.virtual_memory().available,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'free': psutil.disk_usage('/').free,
                    'percent': psutil.disk_usage('/').percent
                },
                'uptime': time.time() - psutil.boot_time()
            })
        
        return info
    
    def get_real_time_data(self) -> Dict[str, Any]:
        """Get real-time system data for dashboard"""
        return {
            'system_info': self.get_system_info(),
            'servers': self.get_servers(),
            'timestamp': datetime.now().isoformat()
        }
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Started background monitoring")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("Stopped background monitoring")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Update system information
                self.update_server_status()
                
                # Check for alerts
                self.check_system_alerts()
                
                # Emit real-time data if websocket is available
                if self.socketio:
                    self.socketio.emit('real_time_update', self.get_real_time_data())
                
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(10)  # Wait before retrying
    
    def update_server_status(self):
        """Update status of all managed servers"""
        # For now, just update the local server
        # In production, this would ping all managed servers
        system_info = self.get_system_info()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Update or insert localhost entry
            cursor.execute("""
                INSERT OR REPLACE INTO servers (hostname, ip_address, port, status, last_seen, system_info)
                VALUES ('localhost', '127.0.0.1', 22, 'online', ?, ?)
            """, (datetime.now(), json.dumps(system_info)))
            conn.commit()
    
    def check_system_alerts(self):
        """Check for system alerts and warnings"""
        if not PSUTIL_AVAILABLE:
            return
        
        alerts = []
        
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 90:
            alerts.append({
                'type': 'disk_space',
                'severity': 'critical',
                'message': f"Disk usage critical: {disk_usage.percent:.1f}%"
            })
        elif disk_usage.percent > 80:
            alerts.append({
                'type': 'disk_space',
                'severity': 'warning',
                'message': f"Disk usage high: {disk_usage.percent:.1f}%"
            })
        
        # Check memory usage
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            alerts.append({
                'type': 'memory',
                'severity': 'critical',
                'message': f"Memory usage critical: {memory.percent:.1f}%"
            })
        elif memory.percent > 80:
            alerts.append({
                'type': 'memory',
                'severity': 'warning',
                'message': f"Memory usage high: {memory.percent:.1f}%"
            })
        
        # Store alerts in database
        if alerts:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for alert in alerts:
                    cursor.execute("""
                        INSERT INTO monitoring_alerts (server_id, alert_type, severity, message)
                        SELECT id, ?, ?, ? FROM servers WHERE hostname = 'localhost'
                    """, (alert['type'], alert['severity'], alert['message']))
                conn.commit()
    
    def get_dashboard_template(self) -> str:
        """Get HTML template for dashboard"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web System Manager v4.0</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 300;
            text-align: center;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .header p {
            text-align: center;
            opacity: 0.8;
            font-size: 1.1em;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3);
        }
        
        .card h3 {
            color: #4ecdc4;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-value {
            font-weight: bold;
            color: #ff6b6b;
        }
        
        .servers-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 30px;
        }
        
        .server-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .server-status {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .status-online {
            background: #4ecdc4;
            color: #1e3c72;
        }
        
        .status-offline {
            background: #ff6b6b;
            color: white;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: linear-gradient(45deg, #ff6b6b, #ff8e53);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }
        
        .btn-secondary {
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
        }
        
        .btn-secondary:hover {
            box-shadow: 0 5px 15px rgba(78, 205, 196, 0.4);
        }
        
        .command-section {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .command-input {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 1em;
            margin-bottom: 15px;
        }
        
        .command-input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        
        .output-area {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 15px;
        }
        
        .chart-container {
            height: 200px;
            margin-top: 20px;
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .controls {
                flex-direction: column;
            }
            
            .server-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Web System Manager v4.0</h1>
            <p>Remote System Management & Monitoring Dashboard</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="startMonitoring()">▶️ Start Monitoring</button>
            <button class="btn btn-secondary" onclick="stopMonitoring()">⏹️ Stop Monitoring</button>
            <button class="btn" onclick="refreshData()">🔄 Refresh</button>
            <a href="/logout" class="btn btn-secondary">🚪 Logout</a>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>🖥️ System Information</h3>
                <div id="system-info">
                    <div class="metric">
                        <span>Loading...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 Resource Usage</h3>
                <div class="chart-container">
                    <canvas id="resourceChart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h3>⚡ Performance Metrics</h3>
                <div id="performance-metrics">
                    <div class="metric">
                        <span>Loading...</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="servers-section">
            <h3>🖥️ Managed Servers</h3>
            <div id="servers-list">
                <div class="server-item">
                    <span>Loading servers...</span>
                </div>
            </div>
        </div>
        
        <div class="command-section">
            <h3>💻 Remote Command Execution</h3>
            <input type="text" class="command-input" id="command-input" placeholder="Enter command to execute...">
            <button class="btn" onclick="executeCommand()">🚀 Execute Command</button>
            <div class="output-area" id="command-output">Command output will appear here...</div>
        </div>
    </div>
    
    <script>
        // Initialize Socket.IO
        const socket = io();
        let resourceChart;
        
        // Initialize resource chart
        function initResourceChart() {
            const ctx = document.getElementById('resourceChart').getContext('2d');
            resourceChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['CPU', 'Memory', 'Disk'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#ff6b6b', '#4ecdc4', '#45b7d1'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: 'white'
                            }
                        }
                    }
                }
            });
        }
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to server');
            refreshData();
        });
        
        socket.on('real_time_update', function(data) {
            updateDashboard(data);
        });
        
        // Update dashboard with real-time data
        function updateDashboard(data) {
            updateSystemInfo(data.system_info);
            updateServers(data.servers);
            updateResourceChart(data.system_info);
        }
        
        function updateSystemInfo(info) {
            const container = document.getElementById('system-info');
            container.innerHTML = `
                <div class="metric">
                    <span>Hostname:</span>
                    <span class="metric-value">${info.hostname || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span>Platform:</span>
                    <span class="metric-value">${info.platform || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span>Architecture:</span>
                    <span class="metric-value">${info.architecture || 'N/A'}</span>
                </div>
                <div class="metric">
                    <span>Kernel:</span>
                    <span class="metric-value">${info.kernel || 'N/A'}</span>
                </div>
            `;
            
            // Update performance metrics
            const perfContainer = document.getElementById('performance-metrics');
            if (info.cpu_percent !== undefined) {
                perfContainer.innerHTML = `
                    <div class="metric">
                        <span>CPU Usage:</span>
                        <span class="metric-value">${info.cpu_percent.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span>Memory:</span>
                        <span class="metric-value">${info.memory ? info.memory.percent.toFixed(1) : 'N/A'}%</span>
                    </div>
                    <div class="metric">
                        <span>Disk:</span>
                        <span class="metric-value">${info.disk ? info.disk.percent.toFixed(1) : 'N/A'}%</span>
                    </div>
                    <div class="metric">
                        <span>Uptime:</span>
                        <span class="metric-value">${formatUptime(info.uptime)}</span>
                    </div>
                `;
            }
        }
        
        function updateServers(servers) {
            const container = document.getElementById('servers-list');
            if (servers.length === 0) {
                container.innerHTML = '<div class="server-item">No servers registered</div>';
                return;
            }
            
            container.innerHTML = servers.map(server => `
                <div class="server-item">
                    <div>
                        <strong>${server.hostname}</strong><br>
                        <small>${server.ip_address}:${server.port}</small>
                    </div>
                    <span class="server-status status-${server.status}">
                        ${server.status.toUpperCase()}
                    </span>
                </div>
            `).join('');
        }
        
        function updateResourceChart(info) {
            if (resourceChart && info.cpu_percent !== undefined) {
                resourceChart.data.datasets[0].data = [
                    info.cpu_percent,
                    info.memory ? info.memory.percent : 0,
                    info.disk ? info.disk.percent : 0
                ];
                resourceChart.update();
            }
        }
        
        function formatUptime(seconds) {
            if (!seconds) return 'N/A';
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${days}d ${hours}h ${minutes}m`;
        }
        
        // Control functions
        function startMonitoring() {
            fetch('/api/monitoring/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('Monitoring started:', data));
        }
        
        function stopMonitoring() {
            fetch('/api/monitoring/stop', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('Monitoring stopped:', data));
        }
        
        function refreshData() {
            socket.emit('get_real_time_data');
        }
        
        function executeCommand() {
            const command = document.getElementById('command-input').value.trim();
            if (!command) return;
            
            const output = document.getElementById('command-output');
            output.textContent = 'Executing command...';
            
            fetch('/api/servers/1/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                output.textContent = `Command: ${data.command}\\n\\nOutput:\\n${data.stdout || ''}\\n\\nErrors:\\n${data.stderr || ''}\\n\\nReturn Code: ${data.returncode}`;
                document.getElementById('command-input').value = '';
            })
            .catch(error => {
                output.textContent = `Error: ${error.message}`;
            });
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            initResourceChart();
            refreshData();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
            
            // Handle Enter key in command input
            document.getElementById('command-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    executeCommand();
                }
            });
        });
    </script>
</body>
</html>
        """
    
    def get_login_template(self) -> str:
        """Get HTML template for login page"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Web System Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            width: 100%;
            max-width: 400px;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .login-header h1 {
            font-size: 2.5em;
            font-weight: 300;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #4ecdc4;
            font-weight: bold;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 1em;
        }
        
        .form-group input::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #4ecdc4;
            box-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
        }
        
        .btn {
            width: 100%;
            background: linear-gradient(45deg, #ff6b6b, #ff8e53);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.3s ease;
            margin-top: 20px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }
        
        .error {
            background: rgba(255, 107, 107, 0.2);
            border: 1px solid #ff6b6b;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .info {
            text-align: center;
            margin-top: 20px;
            opacity: 0.8;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🔐 Login</h1>
            <p>Web System Manager v4.0</p>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" placeholder="Enter username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" placeholder="Enter password" required>
            </div>
            
            <button type="submit" class="btn">🚀 Login</button>
        </form>
        
        <div class="info">
            Default credentials: admin / admin123
        </div>
    </div>
</body>
</html>
        """
    
    def run(self):
        """Run the web application"""
        if not FLASK_AVAILABLE:
            print("❌ Flask is not available. Please install Flask and Flask-SocketIO:")
            print("   pip3 install flask flask-socketio")
            return False
        
        print(f"🌐 Starting Web System Manager v{self.version}")
        print(f"📍 Server will be available at: http://{self.config['host']}:{self.config['port']}")
        print(f"🔐 Authentication: {'Enabled' if self.config['auth_required'] else 'Disabled'}")
        
        if self.config['auth_required']:
            print("📝 Default login: admin / admin123")
        
        # Start monitoring
        self.start_monitoring()
        
        try:
            # Run the Flask application
            self.socketio.run(
                self.app,
                host=self.config['host'],
                port=self.config['port'],
                debug=self.config['debug'],
                allow_unsafe_werkzeug=True
            )
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Web System Manager...")
            self.stop_monitoring()
        except Exception as e:
            print(f"❌ Failed to start web server: {e}")
            return False
        
        return True

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Received shutdown signal...")
    sys.exit(0)

def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Initializing Web System Manager v4.0...")
    
    # Create and run the web system manager
    manager = WebSystemManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "--help":
            print("""
Web System Manager v4.0 - Remote System Management

Usage: python3 web-system-manager.py [OPTIONS]

Options:
  --help          Show this help message
  --version       Show version information
  --config        Show current configuration
  --add-server    Add a new server to management
  --list-servers  List all managed servers

Features:
  🌐 Web-based remote management interface
  📊 Real-time system monitoring dashboard
  🖥️ Multi-server management capabilities
  💻 Remote command execution
  🔐 Authentication and session management
  📈 Performance metrics and alerts
  🔄 Background monitoring and automation

Default web interface: http://localhost:8080
Default credentials: admin / admin123
            """)
            return
        elif command == "--version":
            print(f"Web System Manager v{manager.version}")
            return
        elif command == "--config":
            print(json.dumps(manager.config, indent=2))
            return
        elif command == "--list-servers":
            servers = manager.get_servers()
            if servers:
                print(f"📋 Managed servers ({len(servers)}):")
                for server in servers:
                    print(f"  • {server['hostname']} ({server['ip_address']}:{server['port']}) - {server['status']}")
            else:
                print("📋 No servers registered")
            return
    
    # Run the web interface
    success = manager.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()