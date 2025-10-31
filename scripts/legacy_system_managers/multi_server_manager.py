#!/usr/bin/env python3
"""
Multi-Server Manager - Component for managing multiple remote servers
Extends Web System Manager with real SSH-based remote management
"""

import os
import sys
import json
import sqlite3
import subprocess
import threading
import time
import logging
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import concurrent.futures
import queue

# SSH and networking imports with fallbacks
try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

try:
    import fabric
    FABRIC_AVAILABLE = True
except ImportError:
    FABRIC_AVAILABLE = False

@dataclass
class ServerConnection:
    """Server connection configuration"""
    hostname: str
    ip_address: str
    port: int
    username: str
    password: Optional[str] = None
    key_file: Optional[str] = None
    timeout: int = 30

@dataclass
class ServerTask:
    """Task to be executed on a server"""
    task_id: str
    server_id: int
    command: str
    priority: int = 5
    timeout: int = 300
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class MultiServerManager:
    """Manages multiple remote servers with SSH connections"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path.home() / ".unified-system-manager" / "multi-server.db"
        self.base_path = self.db_path.parent
        self.base_path.mkdir(exist_ok=True)
        
        # Initialize logging
        self.setup_logging()
        
        # Initialize database
        self.init_database()
        
        # Connection pool and task queue
        self.connection_pool = {}
        self.task_queue = queue.PriorityQueue()
        self.worker_threads = []
        self.max_workers = 10
        self.running = False
        
        # Server discovery and monitoring
        self.discovery_enabled = False
        self.monitoring_interval = 60
        
        self.logger.info("Multi-Server Manager initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_path = self.base_path / "logs"
        log_path.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path / "multi-server.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"{__name__}.MultiServerManager")
    
    def init_database(self):
        """Initialize database for multi-server management"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Enhanced servers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT UNIQUE NOT NULL,
                    ip_address TEXT NOT NULL,
                    port INTEGER DEFAULT 22,
                    username TEXT NOT NULL,
                    auth_method TEXT DEFAULT 'password',
                    key_file TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_seen TIMESTAMP,
                    last_check TIMESTAMP,
                    system_info TEXT,
                    capabilities TEXT,
                    tags TEXT,
                    group_name TEXT DEFAULT 'default',
                    priority INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Server groups for organization
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Task execution history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    server_id INTEGER,
                    command TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    return_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            """)
            
            # Server metrics for monitoring
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    unit TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            """)
            
            # Network topology discovery
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_topology (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_server_id INTEGER,
                    target_server_id INTEGER,
                    connection_type TEXT,
                    latency REAL,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_server_id) REFERENCES servers (id),
                    FOREIGN KEY (target_server_id) REFERENCES servers (id)
                )
            """)
            
            # Configuration templates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    template_content TEXT NOT NULL,
                    template_type TEXT DEFAULT 'shell',
                    variables TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_server(self, connection: ServerConnection, group: str = "default", tags: List[str] = None) -> int:
        """Add a new server to management"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert server
                cursor.execute("""
                    INSERT INTO servers (
                        hostname, ip_address, port, username, 
                        auth_method, key_file, group_name, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    connection.hostname,
                    connection.ip_address, 
                    connection.port,
                    connection.username,
                    'key' if connection.key_file else 'password',
                    connection.key_file,
                    group,
                    json.dumps(tags or [])
                ))
                
                server_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Added server: {connection.hostname} (ID: {server_id})")
                
                # Test connection
                if self.test_connection(server_id):
                    self.update_server_status(server_id, "online")
                else:
                    self.update_server_status(server_id, "offline")
                
                return server_id
                
        except sqlite3.IntegrityError:
            self.logger.warning(f"Server {connection.hostname} already exists")
            return -1
        except Exception as e:
            self.logger.error(f"Failed to add server: {e}")
            return -1
    
    def get_ssh_connection(self, server_id: int) -> Optional[paramiko.SSHClient]:
        """Get or create SSH connection to server"""
        if not PARAMIKO_AVAILABLE:
            self.logger.error("Paramiko not available for SSH connections")
            return None
        
        # Check if connection exists and is alive
        if server_id in self.connection_pool:
            client = self.connection_pool[server_id]
            try:
                # Test if connection is still alive
                client.exec_command('echo test', timeout=5)
                return client
            except:
                # Connection is dead, remove from pool
                del self.connection_pool[server_id]
        
        # Create new connection
        server_info = self.get_server_info(server_id)
        if not server_info:
            return None
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using key or password
            if server_info['key_file'] and os.path.exists(server_info['key_file']):
                client.connect(
                    hostname=server_info['ip_address'],
                    port=server_info['port'],
                    username=server_info['username'],
                    key_filename=server_info['key_file'],
                    timeout=30
                )
            else:
                # For demo purposes, we'll skip password auth
                # In production, you'd handle password authentication securely
                self.logger.warning(f"No key file found for server {server_id}")
                return None
            
            self.connection_pool[server_id] = client
            self.logger.info(f"Established SSH connection to {server_info['hostname']}")
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to connect to server {server_id}: {e}")
            return None
    
    def execute_remote_command(self, server_id: int, command: str, timeout: int = 300) -> Dict[str, Any]:
        """Execute command on remote server"""
        start_time = time.time()
        task_id = f"task_{int(time.time())}_{server_id}"
        
        # Record task start
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_history (task_id, server_id, command, status, started_at)
                VALUES (?, ?, ?, 'running', ?)
            """, (task_id, server_id, command, datetime.now()))
            conn.commit()
        
        try:
            client = self.get_ssh_connection(server_id)
            if not client:
                raise Exception("Failed to establish SSH connection")
            
            # Execute command
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            
            # Get results
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8')
            stderr_text = stderr.read().decode('utf-8')
            
            execution_time = time.time() - start_time
            
            result = {
                'task_id': task_id,
                'server_id': server_id,
                'command': command,
                'return_code': exit_code,
                'stdout': stdout_text,
                'stderr': stderr_text,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update task history
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE task_history 
                    SET status = 'completed', return_code = ?, stdout = ?, stderr = ?, 
                        execution_time = ?, completed_at = ?
                    WHERE task_id = ?
                """, (exit_code, stdout_text, stderr_text, execution_time, datetime.now(), task_id))
                conn.commit()
            
            self.logger.info(f"Executed command on server {server_id}: {command}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                'task_id': task_id,
                'server_id': server_id,
                'command': command,
                'error': str(e),
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # Update task history with error
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE task_history 
                    SET status = 'failed', stderr = ?, execution_time = ?, completed_at = ?
                    WHERE task_id = ?
                """, (str(e), execution_time, datetime.now(), task_id))
                conn.commit()
            
            self.logger.error(f"Command execution failed on server {server_id}: {e}")
            return error_result
    
    def execute_parallel_command(self, server_ids: List[int], command: str, max_workers: int = 5) -> List[Dict[str, Any]]:
        """Execute command on multiple servers in parallel"""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks
            future_to_server = {
                executor.submit(self.execute_remote_command, server_id, command): server_id 
                for server_id in server_ids
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_server):
                server_id = future_to_server[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Parallel execution failed for server {server_id}: {e}")
                    results.append({
                        'server_id': server_id,
                        'command': command,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
        
        return results
    
    def test_connection(self, server_id: int) -> bool:
        """Test connection to a server"""
        try:
            result = self.execute_remote_command(server_id, "echo 'connection_test'", timeout=10)
            return result.get('return_code') == 0
        except:
            return False
    
    def get_server_info(self, server_id: int) -> Optional[Dict[str, Any]]:
        """Get server information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hostname, ip_address, port, username, auth_method, 
                       key_file, status, group_name, tags, system_info
                FROM servers WHERE id = ?
            """, (server_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': server_id,
                    'hostname': row[0],
                    'ip_address': row[1],
                    'port': row[2],
                    'username': row[3],
                    'auth_method': row[4],
                    'key_file': row[5],
                    'status': row[6],
                    'group_name': row[7],
                    'tags': json.loads(row[8]) if row[8] else [],
                    'system_info': json.loads(row[9]) if row[9] else {}
                }
            return None
    
    def get_all_servers(self, group: str = None) -> List[Dict[str, Any]]:
        """Get all servers, optionally filtered by group"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if group:
                cursor.execute("""
                    SELECT id, hostname, ip_address, port, username, status, 
                           group_name, tags, last_seen
                    FROM servers WHERE group_name = ? ORDER BY hostname
                """, (group,))
            else:
                cursor.execute("""
                    SELECT id, hostname, ip_address, port, username, status, 
                           group_name, tags, last_seen
                    FROM servers ORDER BY hostname
                """)
            
            servers = []
            for row in cursor.fetchall():
                servers.append({
                    'id': row[0],
                    'hostname': row[1],
                    'ip_address': row[2],
                    'port': row[3],
                    'username': row[4],
                    'status': row[5],
                    'group_name': row[6],
                    'tags': json.loads(row[7]) if row[7] else [],
                    'last_seen': row[8]
                })
            
            return servers
    
    def update_server_status(self, server_id: int, status: str):
        """Update server status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE servers 
                SET status = ?, last_check = ?, updated_at = ?
                WHERE id = ?
            """, (status, datetime.now(), datetime.now(), server_id))
            conn.commit()
    
    def collect_system_info(self, server_id: int) -> Dict[str, Any]:
        """Collect comprehensive system information from a server"""
        commands = {
            'hostname': 'hostname',
            'uptime': 'uptime',
            'kernel': 'uname -r',
            'os_release': 'cat /etc/os-release 2>/dev/null || echo "Unknown"',
            'cpu_info': 'nproc && cat /proc/cpuinfo | grep "model name" | head -1',
            'memory': 'free -h',
            'disk_usage': 'df -h',
            'network_interfaces': 'ip addr show',
            'running_services': 'systemctl list-units --type=service --state=running | head -20',
            'load_average': 'cat /proc/loadavg',
            'last_login': 'last -n 5'
        }
        
        system_info = {}
        
        for key, command in commands.items():
            try:
                result = self.execute_remote_command(server_id, command, timeout=30)
                if result.get('return_code') == 0:
                    system_info[key] = result['stdout'].strip()
                else:
                    system_info[key] = f"Error: {result.get('stderr', 'Unknown error')}"
            except Exception as e:
                system_info[key] = f"Error: {str(e)}"
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE servers 
                SET system_info = ?, last_seen = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(system_info), datetime.now(), datetime.now(), server_id))
            conn.commit()
        
        return system_info
    
    def discover_network_services(self, server_id: int) -> Dict[str, Any]:
        """Discover network services on a server"""
        discovery_commands = {
            'listening_ports': 'netstat -tuln 2>/dev/null || ss -tuln',
            'network_connections': 'netstat -an | grep ESTABLISHED | head -10',
            'docker_containers': 'docker ps 2>/dev/null || echo "Docker not available"',
            'systemd_services': 'systemctl list-units --type=service --state=active --no-pager | head -20'
        }
        
        services = {}
        for key, command in discovery_commands.items():
            try:
                result = self.execute_remote_command(server_id, command, timeout=30)
                if result.get('return_code') == 0:
                    services[key] = result['stdout'].strip()
            except Exception as e:
                services[key] = f"Error: {str(e)}"
        
        return services
    
    def create_server_group(self, name: str, description: str = "") -> bool:
        """Create a new server group"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO server_groups (name, description)
                    VALUES (?, ?)
                """, (name, description))
                conn.commit()
                self.logger.info(f"Created server group: {name}")
                return True
        except sqlite3.IntegrityError:
            self.logger.warning(f"Server group {name} already exists")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create server group: {e}")
            return False
    
    def get_server_groups(self) -> List[Dict[str, Any]]:
        """Get all server groups"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sg.name, sg.description, sg.created_at,
                       COUNT(s.id) as server_count
                FROM server_groups sg
                LEFT JOIN servers s ON sg.name = s.group_name
                GROUP BY sg.name, sg.description, sg.created_at
                ORDER BY sg.name
            """)
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    'name': row[0],
                    'description': row[1],
                    'created_at': row[2],
                    'server_count': row[3]
                })
            
            return groups
    
    def get_task_history(self, server_id: int = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task execution history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if server_id:
                cursor.execute("""
                    SELECT th.task_id, th.server_id, s.hostname, th.command, 
                           th.status, th.return_code, th.execution_time,
                           th.created_at, th.completed_at
                    FROM task_history th
                    JOIN servers s ON th.server_id = s.id
                    WHERE th.server_id = ?
                    ORDER BY th.created_at DESC
                    LIMIT ?
                """, (server_id, limit))
            else:
                cursor.execute("""
                    SELECT th.task_id, th.server_id, s.hostname, th.command, 
                           th.status, th.return_code, th.execution_time,
                           th.created_at, th.completed_at
                    FROM task_history th
                    JOIN servers s ON th.server_id = s.id
                    ORDER BY th.created_at DESC
                    LIMIT ?
                """, (limit,))
            
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    'task_id': row[0],
                    'server_id': row[1],
                    'hostname': row[2],
                    'command': row[3],
                    'status': row[4],
                    'return_code': row[5],
                    'execution_time': row[6],
                    'created_at': row[7],
                    'completed_at': row[8]
                })
            
            return tasks
    
    def start_monitoring(self):
        """Start background monitoring of all servers"""
        if self.running:
            return
        
        self.running = True
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_thread, 
                daemon=True,
                name=f"MultiServerWorker-{i}"
            )
            worker.start()
            self.worker_threads.append(worker)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="MultiServerMonitor"
        )
        monitor_thread.start()
        
        self.logger.info("Started multi-server monitoring")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        
        # Close all SSH connections
        for client in self.connection_pool.values():
            try:
                client.close()
            except:
                pass
        self.connection_pool.clear()
        
        self.logger.info("Stopped multi-server monitoring")
    
    def _worker_thread(self):
        """Worker thread for processing tasks"""
        while self.running:
            try:
                # Get task from queue (with timeout)
                task = self.task_queue.get(timeout=1)
                
                # Process task
                self.execute_remote_command(
                    task.server_id, 
                    task.command, 
                    task.timeout
                )
                
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker thread error: {e}")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                servers = self.get_all_servers()
                
                for server in servers:
                    if not self.running:
                        break
                    
                    server_id = server['id']
                    
                    # Test connectivity
                    if self.test_connection(server_id):
                        self.update_server_status(server_id, "online")
                        
                        # Collect system info periodically
                        last_seen = server.get('last_seen')
                        if not last_seen or \
                           (datetime.now() - datetime.fromisoformat(last_seen)).seconds > 3600:
                            self.collect_system_info(server_id)
                    else:
                        self.update_server_status(server_id, "offline")
                
                # Wait before next monitoring cycle
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(10)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Server statistics
            cursor.execute("SELECT COUNT(*) FROM servers")
            total_servers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM servers WHERE status = 'online'")
            online_servers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM servers WHERE status = 'offline'")
            offline_servers = cursor.fetchone()[0]
            
            # Task statistics
            cursor.execute("SELECT COUNT(*) FROM task_history")
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM task_history WHERE status = 'completed'")
            completed_tasks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM task_history WHERE status = 'failed'")
            failed_tasks = cursor.fetchone()[0]
            
            # Group statistics
            cursor.execute("SELECT COUNT(*) FROM server_groups")
            total_groups = cursor.fetchone()[0]
            
            return {
                'servers': {
                    'total': total_servers,
                    'online': online_servers,
                    'offline': offline_servers,
                    'unknown': total_servers - online_servers - offline_servers
                },
                'tasks': {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'failed': failed_tasks,
                    'success_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                },
                'groups': {
                    'total': total_groups
                },
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Main function for testing"""
    print("🌐 Multi-Server Manager - Testing Mode")
    
    manager = MultiServerManager()
    
    # Create a test group
    manager.create_server_group("test_servers", "Test server group")
    
    # Add localhost for testing
    connection = ServerConnection(
        hostname="localhost",
        ip_address="127.0.0.1",
        port=22,
        username=os.getenv('USER', 'testuser')
    )
    
    server_id = manager.add_server(connection, group="test_servers", tags=["local", "test"])
    
    if server_id > 0:
        print(f"✅ Added server with ID: {server_id}")
        
        # Test command execution
        result = manager.execute_remote_command(server_id, "echo 'Hello from Multi-Server Manager'")
        print(f"📋 Command result: {result}")
        
        # Collect system info
        info = manager.collect_system_info(server_id)
        print(f"🖥️ System info collected: {len(info)} items")
        
        # Get statistics
        stats = manager.get_statistics()
        print(f"📊 Statistics: {json.dumps(stats, indent=2)}")
    
    manager.stop_monitoring()

if __name__ == "__main__":
    main()