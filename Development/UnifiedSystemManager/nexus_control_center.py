#!/usr/bin/env python3
"""
NexusController - EbonCorp Control Center
Centralized management for ebon@ebon home server and future ebon-* servers
"""

import sys
import os
import json
import subprocess
import socket
import time
import requests
import paramiko
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import ipaddress

# Import custom modules
from github_integration import GitHubManager, GitHubBackup, GitHubCLI
from cloud_integrations import ContainerManager, MonitoringManager, NetworkScanner

class EbonServerManager:
    """Centralized management for Ebon servers"""
    
    def __init__(self, logger):
        self.logger = logger
        self.servers = {
            'ebon': {
                'host': '10.0.0.29',
                'port': 22,
                'username': 'ebon',
                'name': 'Ebon Home Server',
                'type': 'home_server',
                'description': 'Main home server with web services',
                'services': ['ssh', 'http', 'https'],
                'auto_discovered': False
            }
        }
        
        # Network ranges to scan for ebon-* servers
        self.scan_networks = [
            '10.0.0.0/24',
            '192.168.1.0/24',
            '192.168.0.0/24'
        ]
        
        self.server_status = {}
        self.last_scan = None
    
    def discover_ebon_servers(self) -> List[Dict]:
        """Discover ebon-prefixed servers on the network"""
        discovered = []
        
        print("🔍 Scanning for ebon-* servers...")
        
        for network in self.scan_networks:
            try:
                network_obj = ipaddress.IPv4Network(network, strict=False)
                
                for ip in network_obj.hosts():
                    ip_str = str(ip)
                    
                    # Quick port 22 check
                    if self._check_port(ip_str, 22, timeout=1):
                        # Try to get hostname
                        hostname = self._get_hostname(ip_str)
                        
                        if hostname and (hostname.startswith('ebon-') or hostname == 'ebon'):
                            server_info = {
                                'host': ip_str,
                                'hostname': hostname,
                                'port': 22,
                                'username': 'ebon',  # Assume ebon user
                                'name': hostname.replace('-', ' ').title(),
                                'type': self._determine_server_type(hostname),
                                'description': f'Auto-discovered {hostname}',
                                'services': ['ssh'],
                                'auto_discovered': True
                            }
                            
                            # Check for additional services
                            if self._check_port(ip_str, 80):
                                server_info['services'].append('http')
                            if self._check_port(ip_str, 443):
                                server_info['services'].append('https')
                            
                            discovered.append(server_info)
                            print(f"  ✅ Found: {hostname} at {ip_str}")
            
            except Exception as e:
                print(f"  ⚠️  Error scanning {network}: {e}")
        
        # Update servers dictionary
        for server in discovered:
            server_id = server['hostname']
            if server_id not in self.servers:
                self.servers[server_id] = server
                print(f"  📝 Added {server_id} to server list")
        
        self.last_scan = datetime.now()
        self.logger.log_event("server_discovery", {
            "discovered_count": len(discovered),
            "total_servers": len(self.servers)
        })
        
        return discovered
    
    def _check_port(self, host: str, port: int, timeout: float = 2.0) -> bool:
        """Check if port is open on host"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _get_hostname(self, ip: str) -> Optional[str]:
        """Get hostname for IP address"""
        try:
            # Try reverse DNS first
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname.split('.')[0]  # Get just the hostname part
        except:
            # Try SSH banner if available
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((ip, 22))
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                sock.close()
                
                # Look for hostname in SSH banner
                if 'ebon' in banner.lower():
                    parts = banner.split()
                    for part in parts:
                        if 'ebon' in part.lower():
                            return part.strip()
            except:
                pass
            
            return None
    
    def _determine_server_type(self, hostname: str) -> str:
        """Determine server type from hostname"""
        if hostname == 'ebon':
            return 'home_server'
        elif 'eth' in hostname:
            return 'blockchain'
        elif 'db' in hostname:
            return 'database'
        elif 'web' in hostname:
            return 'web_server'
        elif 'api' in hostname:
            return 'api_server'
        else:
            return 'general'
    
    def check_server_status(self, server_id: str) -> Dict:
        """Check comprehensive status of a server"""
        if server_id not in self.servers:
            return {'status': 'unknown', 'error': 'Server not found'}
        
        server = self.servers[server_id]
        status = {
            'server_id': server_id,
            'name': server['name'],
            'timestamp': datetime.now().isoformat(),
            'connectivity': {},
            'services': {},
            'system': {},
            'error': None
        }
        
        try:
            # Basic connectivity
            ssh_available = self._check_port(server['host'], server['port'], timeout=5)
            status['connectivity']['ssh'] = ssh_available
            
            if ssh_available:
                # Check other services
                for service in server.get('services', []):
                    if service == 'http':
                        status['services']['http'] = self._check_port(server['host'], 80)
                    elif service == 'https':
                        status['services']['https'] = self._check_port(server['host'], 443)
                
                # Try to get system info via SSH (if keys are set up)
                try:
                    system_info = self._get_remote_system_info(server)
                    if system_info:
                        status['system'] = system_info
                except Exception as e:
                    status['system']['error'] = str(e)
            
            # Overall status
            if ssh_available:
                status['status'] = 'online'
            else:
                status['status'] = 'offline'
        
        except Exception as e:
            status['status'] = 'error'
            status['error'] = str(e)
        
        self.server_status[server_id] = status
        return status
    
    def _get_remote_system_info(self, server: Dict) -> Dict:
        """Get system information from remote server via SSH"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Try key-based authentication first
            ssh.connect(
                hostname=server['host'],
                port=server['port'],
                username=server['username'],
                timeout=10,
                look_for_keys=True
            )
            
            commands = {
                'uptime': 'uptime',
                'load': 'cat /proc/loadavg',
                'memory': 'free -m',
                'disk': 'df -h /',
                'os': 'cat /etc/os-release | grep PRETTY_NAME',
                'kernel': 'uname -r',
                'processes': 'ps aux | wc -l'
            }
            
            system_info = {}
            
            for key, cmd in commands.items():
                try:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    output = stdout.read().decode('utf-8').strip()
                    if output:
                        system_info[key] = output
                except:
                    system_info[key] = 'unavailable'
            
            ssh.close()
            return system_info
            
        except paramiko.AuthenticationException:
            return {'auth_error': 'SSH key authentication failed'}
        except Exception as e:
            return {'connection_error': str(e)}
    
    def execute_command(self, server_id: str, command: str) -> Dict:
        """Execute command on remote server"""
        if server_id not in self.servers:
            return {'success': False, 'error': 'Server not found'}
        
        server = self.servers[server_id]
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=server['host'],
                port=server['port'],
                username=server['username'],
                timeout=10,
                look_for_keys=True
            )
            
            stdin, stdout, stderr = ssh.exec_command(command)
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            ssh.close()
            
            result = {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'output': output,
                'error': error,
                'command': command,
                'server': server_id,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.log_event("remote_command", {
                "server": server_id,
                "command": command[:50],  # Log first 50 chars
                "success": result['success']
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command,
                'server': server_id
            }
    
    def get_server_logs(self, server_id: str, log_file: str = '/var/log/syslog', lines: int = 50) -> List[str]:
        """Get logs from remote server"""
        command = f"tail -n {lines} {log_file}"
        result = self.execute_command(server_id, command)
        
        if result['success']:
            return result['output'].strip().split('\n')
        else:
            return [f"Error retrieving logs: {result.get('error', 'Unknown error')}"]

class VPNProviderManager:
    """Multi-VPN provider management"""
    
    def __init__(self, logger):
        self.logger = logger
        self.providers = {}
        self.active_provider = None
        self.connection_status = {'connected': False, 'provider': None}
        
        # Detect available VPN providers
        self._detect_vpn_providers()
    
    def _detect_vpn_providers(self):
        """Detect available VPN providers"""
        # NordVPN
        try:
            result = subprocess.run(['nordvpn', '--version'], capture_output=True)
            if result.returncode == 0:
                self.providers['nordvpn'] = {
                    'name': 'NordVPN',
                    'command': 'nordvpn',
                    'available': True,
                    'type': 'commercial'
                }
        except FileNotFoundError:
            self.providers['nordvpn'] = {
                'name': 'NordVPN',
                'command': 'nordvpn',
                'available': False,
                'type': 'commercial'
            }
        
        # ExpressVPN
        try:
            result = subprocess.run(['expressvpn', '--version'], capture_output=True)
            if result.returncode == 0:
                self.providers['expressvpn'] = {
                    'name': 'ExpressVPN',
                    'command': 'expressvpn',
                    'available': True,
                    'type': 'commercial'
                }
        except FileNotFoundError:
            self.providers['expressvpn'] = {
                'name': 'ExpressVPN',
                'command': 'expressvpn',
                'available': False,
                'type': 'commercial'
            }
        
        # WireGuard
        try:
            result = subprocess.run(['wg', '--version'], capture_output=True)
            if result.returncode == 0:
                self.providers['wireguard'] = {
                    'name': 'WireGuard',
                    'command': 'wg',
                    'available': True,
                    'type': 'protocol'
                }
        except FileNotFoundError:
            self.providers['wireguard'] = {
                'name': 'WireGuard',
                'command': 'wg',
                'available': False,
                'type': 'protocol'
            }
        
        # OpenVPN
        try:
            result = subprocess.run(['openvpn', '--version'], capture_output=True)
            if result.returncode == 0:
                self.providers['openvpn'] = {
                    'name': 'OpenVPN',
                    'command': 'openvpn',
                    'available': True,
                    'type': 'protocol'
                }
        except FileNotFoundError:
            self.providers['openvpn'] = {
                'name': 'OpenVPN',
                'command': 'openvpn',
                'available': False,
                'type': 'protocol'
            }
    
    def get_available_providers(self) -> List[Dict]:
        """Get list of available VPN providers"""
        return [
            {
                'id': provider_id,
                'name': provider['name'],
                'available': provider['available'],
                'type': provider['type']
            }
            for provider_id, provider in self.providers.items()
        ]
    
    def recommend_best_vpn(self) -> str:
        """Recommend best available VPN provider"""
        # Priority order based on features and performance
        priority = ['wireguard', 'nordvpn', 'expressvpn', 'openvpn']
        
        for provider_id in priority:
            if provider_id in self.providers and self.providers[provider_id]['available']:
                return provider_id
        
        return None
    
    def get_provider_status(self, provider_id: str) -> Dict:
        """Get status of specific VPN provider"""
        if provider_id not in self.providers:
            return {'status': 'unknown', 'error': 'Provider not found'}
        
        provider = self.providers[provider_id]
        
        if not provider['available']:
            return {'status': 'unavailable', 'message': 'Provider not installed'}
        
        try:
            if provider_id == 'nordvpn':
                result = subprocess.run(['nordvpn', 'status'], capture_output=True, text=True)
                if result.returncode == 0:
                    output = result.stdout
                    return {
                        'status': 'available',
                        'connected': 'Connected' in output,
                        'details': output.strip()
                    }
            
            elif provider_id == 'wireguard':
                result = subprocess.run(['wg', 'show'], capture_output=True, text=True)
                if result.returncode == 0:
                    connected = len(result.stdout.strip()) > 0
                    return {
                        'status': 'available',
                        'connected': connected,
                        'details': result.stdout.strip() if connected else 'No active connections'
                    }
            
            # Add other providers as needed
            
            return {'status': 'available', 'connected': False}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def connect_vpn(self, provider_id: str, location: str = None) -> bool:
        """Connect to VPN using specified provider"""
        if provider_id not in self.providers:
            print(f"❌ Unknown VPN provider: {provider_id}")
            return False
        
        provider = self.providers[provider_id]
        
        if not provider['available']:
            print(f"❌ {provider['name']} not available")
            return False
        
        try:
            if provider_id == 'nordvpn':
                cmd = ['nordvpn', 'connect']
                if location:
                    cmd.append(location)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0
                
                if success:
                    print(f"✅ Connected to {provider['name']}")
                    self.connection_status = {'connected': True, 'provider': provider_id}
                    self.active_provider = provider_id
                else:
                    print(f"❌ {provider['name']} connection failed: {result.stderr}")
                
                return success
            
            elif provider_id == 'wireguard':
                # Assume config name if location provided, otherwise use default
                config_name = location if location else 'wg0'
                
                result = subprocess.run(['sudo', 'wg-quick', 'up', config_name], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
                
                if success:
                    print(f"✅ Connected to {provider['name']}")
                    self.connection_status = {'connected': True, 'provider': provider_id}
                    self.active_provider = provider_id
                else:
                    print(f"❌ {provider['name']} connection failed: {result.stderr}")
                
                return success
            
            # Add other providers
            
        except Exception as e:
            print(f"❌ VPN connection error: {e}")
            return False
        
        return False
    
    def disconnect_vpn(self, provider_id: str = None) -> bool:
        """Disconnect from VPN"""
        if not provider_id:
            provider_id = self.active_provider
        
        if not provider_id:
            print("❌ No active VPN connection")
            return False
        
        try:
            if provider_id == 'nordvpn':
                result = subprocess.run(['nordvpn', 'disconnect'], capture_output=True, text=True)
                success = result.returncode == 0
            
            elif provider_id == 'wireguard':
                # Try common config names
                configs = ['wg0', 'nexus', 'client']
                success = False
                
                for config in configs:
                    result = subprocess.run(['sudo', 'wg-quick', 'down', config], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        success = True
                        break
            
            else:
                success = False
            
            if success:
                print(f"✅ Disconnected from VPN")
                self.connection_status = {'connected': False, 'provider': None}
                self.active_provider = None
            else:
                print(f"❌ Disconnect failed")
            
            return success
            
        except Exception as e:
            print(f"❌ VPN disconnect error: {e}")
            return False

class GitHubProgramManager:
    """Enhanced GitHub management for all programs"""
    
    def __init__(self, github_manager, logger):
        self.github = github_manager
        self.logger = logger
        self.local_projects_dir = Path.home() / 'projects'
        self.local_projects_dir.mkdir(exist_ok=True)
    
    def scan_local_projects(self) -> List[Dict]:
        """Scan for local Git repositories"""
        projects = []
        
        # Common project directories
        search_dirs = [
            Path.home() / 'projects',
            Path.home() / 'code',
            Path.home() / 'dev',
            Path.home() / 'src',
            Path.home() / 'workspace',
            Path.home() / 'Documents'
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                for item in search_dir.iterdir():
                    if item.is_dir() and (item / '.git').exists():
                        try:
                            # Get Git info
                            os.chdir(item)
                            
                            # Get remote URL
                            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                                  capture_output=True, text=True)
                            remote_url = result.stdout.strip() if result.returncode == 0 else None
                            
                            # Get current branch
                            result = subprocess.run(['git', 'branch', '--show-current'], 
                                                  capture_output=True, text=True)
                            current_branch = result.stdout.strip() if result.returncode == 0 else 'unknown'
                            
                            # Get last commit
                            result = subprocess.run(['git', 'log', '-1', '--format=%H:%s'], 
                                                  capture_output=True, text=True)
                            last_commit = result.stdout.strip() if result.returncode == 0 else None
                            
                            # Check for uncommitted changes
                            result = subprocess.run(['git', 'status', '--porcelain'], 
                                                  capture_output=True, text=True)
                            has_changes = len(result.stdout.strip()) > 0
                            
                            projects.append({
                                'name': item.name,
                                'path': str(item),
                                'remote_url': remote_url,
                                'current_branch': current_branch,
                                'last_commit': last_commit,
                                'has_uncommitted_changes': has_changes,
                                'is_github': 'github.com' in (remote_url or '')
                            })
                            
                        except Exception as e:
                            print(f"⚠️  Error scanning {item}: {e}")
        
        return projects
    
    def sync_all_repos(self) -> Dict:
        """Sync all local GitHub repositories"""
        projects = self.scan_local_projects()
        github_projects = [p for p in projects if p['is_github']]
        
        results = {
            'total': len(github_projects),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for project in github_projects:
            try:
                os.chdir(project['path'])
                
                # Pull latest changes
                result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
                
                if result.returncode == 0:
                    results['success'] += 1
                    results['details'].append({
                        'name': project['name'],
                        'status': 'success',
                        'message': 'Updated successfully'
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'name': project['name'],
                        'status': 'failed',
                        'message': result.stderr.strip()
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'name': project['name'],
                    'status': 'error',
                    'message': str(e)
                })
        
        return results
    
    def clone_all_repos(self) -> Dict:
        """Clone all repositories from GitHub account"""
        if not self.github.current_account:
            return {'error': 'No active GitHub account'}
        
        repos = self.github.list_repositories('all')
        
        results = {
            'total': len(repos),
            'cloned': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }
        
        for repo in repos:
            repo_name = repo['name']
            clone_path = self.local_projects_dir / repo_name
            
            if clone_path.exists():
                results['skipped'] += 1
                results['details'].append({
                    'name': repo_name,
                    'status': 'skipped',
                    'message': 'Already exists locally'
                })
                continue
            
            try:
                # Clone with SSH
                ssh_url = repo['ssh_url']
                result = subprocess.run([
                    'git', 'clone', ssh_url, str(clone_path)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    results['cloned'] += 1
                    results['details'].append({
                        'name': repo_name,
                        'status': 'cloned',
                        'message': f'Cloned to {clone_path}'
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'name': repo_name,
                        'status': 'failed',
                        'message': result.stderr.strip()
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'name': repo_name,
                    'status': 'error',
                    'message': str(e)
                })
        
        return results

class NexusControlCenter:
    """Main NexusController - EbonCorp Control Center"""
    
    def __init__(self):
        print("🏢 Initializing NexusController - EbonCorp Control Center...")
        
        # Import base components
        sys.path.append(str(Path(__file__).parent))
        
        # Initialize logger
        from nexus_secure import SecureLogger
        self.logger = SecureLogger()
        
        # Initialize managers
        self.ebon_manager = EbonServerManager(self.logger)
        self.vpn_manager = VPNProviderManager(self.logger)
        self.container_manager = ContainerManager(self.logger)
        self.monitoring_manager = MonitoringManager(self.logger)
        self.network_scanner = NetworkScanner(self.logger)
        
        # GitHub integration
        self.github_manager = GitHubManager(self.logger)
        self.github_backup = GitHubBackup(self.github_manager, self.logger)
        self.github_cli = GitHubCLI(self.logger)
        self.github_programs = GitHubProgramManager(self.github_manager, self.logger)
        
        # Auto-discover servers on startup
        self.auto_discover_servers()
        
        print("✅ EbonCorp Control Center initialized")
    
    def auto_discover_servers(self):
        """Auto-discover ebon servers on startup"""
        try:
            discovered = self.ebon_manager.discover_ebon_servers()
            if discovered:
                print(f"🔍 Auto-discovered {len(discovered)} ebon servers")
            else:
                print("🔍 No additional ebon servers found on network")
        except Exception as e:
            print(f"⚠️  Auto-discovery failed: {e}")
    
    def show_main_dashboard(self):
        """Display comprehensive control center dashboard"""
        print("\n" + "="*90)
        print("🏢 EBONCORP NEXUS CONTROL CENTER - INFRASTRUCTURE DASHBOARD")
        print("="*90)
        
        # Server Status Overview
        print("\n🖥️  EBON SERVER INFRASTRUCTURE")
        print("-" * 35)
        
        for server_id, server in self.ebon_manager.servers.items():
            status = self.ebon_manager.check_server_status(server_id)
            
            if status['status'] == 'online':
                status_emoji = "🟢"
                status_text = "ONLINE"
            elif status['status'] == 'offline':
                status_emoji = "🔴"
                status_text = "OFFLINE"
            else:
                status_emoji = "🟡"
                status_text = "UNKNOWN"
            
            print(f"{status_emoji} {server['name']} ({server['host']})")
            print(f"   Status: {status_text} | Type: {server['type']} | Services: {', '.join(server.get('services', []))}")
            
            if 'system' in status and status['system']:
                system = status['system']
                if 'uptime' in system:
                    print(f"   Uptime: {system['uptime']}")
                if 'load' in system:
                    print(f"   Load: {system['load']}")
        
        # VPN Status
        print("\n🌐 VPN PROVIDERS")
        print("-" * 15)
        
        providers = self.vpn_manager.get_available_providers()
        active_vpn = None
        
        for provider in providers:
            if provider['available']:
                status = self.vpn_manager.get_provider_status(provider['id'])
                if status.get('connected'):
                    print(f"🟢 {provider['name']}: CONNECTED")
                    active_vpn = provider['name']
                else:
                    print(f"⚪ {provider['name']}: Available")
            else:
                print(f"🔴 {provider['name']}: Not installed")
        
        if not active_vpn:
            recommended = self.vpn_manager.recommend_best_vpn()
            if recommended:
                rec_name = self.vpn_manager.providers[recommended]['name']
                print(f"💡 Recommended: {rec_name}")
        
        # GitHub Projects
        print("\n🐙 GITHUB PROJECTS")
        print("-" * 17)
        
        if self.github_manager.current_account:
            print(f"👤 Account: {self.github_manager.current_account}")
            
            # Show local projects
            local_projects = self.github_programs.scan_local_projects()
            github_projects = [p for p in local_projects if p['is_github']]
            
            if github_projects:
                print(f"📁 Local repos: {len(github_projects)}")
                for project in github_projects[:5]:  # Show first 5
                    changes_indicator = "📝" if project['has_uncommitted_changes'] else "✅"
                    print(f"   {changes_indicator} {project['name']} ({project['current_branch']})")
            else:
                print("📁 No local GitHub repositories found")
        else:
            print("⚠️  No GitHub account configured")
        
        # Docker Containers
        print("\n🐳 CONTAINER SERVICES")
        print("-" * 20)
        
        if self.container_manager.docker_available:
            containers = self.container_manager.list_docker_containers()
            if containers:
                print(f"📦 Active: {len(containers)}")
                for container in containers[:3]:
                    print(f"   🐳 {container['name']} - {container['status']}")
            else:
                print("📦 No containers running")
        else:
            print("⚠️  Docker not available")
        
        # System Health
        print("\n📊 CONTROL CENTER HEALTH")
        print("-" * 25)
        
        health = self.monitoring_manager.check_system_health()
        if health:
            cpu_emoji = "🟢" if health['cpu']['percent'] < 70 else "🟡" if health['cpu']['percent'] < 90 else "🔴"
            mem_emoji = "🟢" if health['memory']['percent'] < 70 else "🟡" if health['memory']['percent'] < 90 else "🔴"
            
            print(f"{cpu_emoji} CPU: {health['cpu']['percent']:.1f}%")
            print(f"{mem_emoji} Memory: {health['memory']['percent']:.1f}%")
            print(f"🔢 Processes: {health['processes']}")
    
    def server_management_menu(self):
        """Ebon server management menu"""
        while True:
            print("\n🖥️  Ebon Server Management")
            print("=" * 30)
            
            # List all servers
            print("📋 Configured Servers:")
            for server_id, server in self.ebon_manager.servers.items():
                auto_tag = " [AUTO]" if server.get('auto_discovered') else ""
                print(f"  🖥️  {server_id}: {server['name']} ({server['host']}){auto_tag}")
            
            print("\n1. 📊 Server Status Dashboard")
            print("2. 🔍 Discover New Servers")
            print("3. 🔗 Connect to Server")
            print("4. 💻 Execute Remote Command")
            print("5. 📋 View Server Logs")
            print("6. ⚙️  Server Configuration")
            print("7. ➕ Add Manual Server")
            print("8. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-8): ").strip()
            
            if choice == '1':
                self.show_detailed_server_status()
            elif choice == '2':
                self.discover_servers()
            elif choice == '3':
                self.connect_to_server()
            elif choice == '4':
                self.execute_remote_command()
            elif choice == '5':
                self.view_server_logs()
            elif choice == '6':
                self.server_configuration()
            elif choice == '7':
                self.add_manual_server()
            elif choice == '8':
                break
            else:
                print("❌ Invalid choice")
    
    def show_detailed_server_status(self):
        """Show detailed status for all servers"""
        print("\n📊 Detailed Server Status")
        print("-" * 30)
        
        for server_id in self.ebon_manager.servers:
            print(f"\n🖥️  {server_id.upper()}:")
            status = self.ebon_manager.check_server_status(server_id)
            
            # Basic status
            print(f"   Status: {status['status']}")
            print(f"   Connectivity: SSH={status['connectivity'].get('ssh', False)}")
            
            # Services
            if status['services']:
                services_str = ", ".join([f"{k}={v}" for k, v in status['services'].items()])
                print(f"   Services: {services_str}")
            
            # System info
            if status['system'] and 'error' not in status['system']:
                system = status['system']
                if 'uptime' in system:
                    print(f"   Uptime: {system['uptime']}")
                if 'load' in system:
                    print(f"   Load: {system['load']}")
                if 'memory' in system:
                    print(f"   Memory: {system['memory'].split()[1]}")  # Used memory
            elif 'system' in status and 'error' in status['system']:
                print(f"   System: {status['system']['error']}")
    
    def discover_servers(self):
        """Manual server discovery"""
        print("\n🔍 Discovering Ebon Servers...")
        discovered = self.ebon_manager.discover_ebon_servers()
        
        if discovered:
            print(f"\n✅ Discovered {len(discovered)} new servers:")
            for server in discovered:
                print(f"   🖥️  {server['hostname']} at {server['host']}")
        else:
            print("\n📝 No new servers discovered")
    
    def connect_to_server(self):
        """Connect to selected server"""
        servers = list(self.ebon_manager.servers.keys())
        
        if not servers:
            print("❌ No servers configured")
            return
        
        print("\n🔗 Select server to connect:")
        for i, server_id in enumerate(servers, 1):
            server = self.ebon_manager.servers[server_id]
            print(f"  {i}. {server['name']} ({server['host']})")
        
        try:
            choice = int(input("\n🎯 Select server: ")) - 1
            if 0 <= choice < len(servers):
                server_id = servers[choice]
                server = self.ebon_manager.servers[server_id]
                
                print(f"🚀 Connecting to {server['name']}...")
                
                # Launch SSH connection
                ssh_cmd = [
                    'ssh',
                    f"{server['username']}@{server['host']}",
                    '-p', str(server['port'])
                ]
                
                subprocess.run(ssh_cmd)
                
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def execute_remote_command(self):
        """Execute command on remote server"""
        servers = list(self.ebon_manager.servers.keys())
        
        if not servers:
            print("❌ No servers configured")
            return
        
        print("\n💻 Select server for command execution:")
        for i, server_id in enumerate(servers, 1):
            server = self.ebon_manager.servers[server_id]
            print(f"  {i}. {server['name']}")
        
        try:
            choice = int(input("\n🎯 Select server: ")) - 1
            if 0 <= choice < len(servers):
                server_id = servers[choice]
                
                command = input("💻 Enter command: ").strip()
                if command:
                    print(f"🔄 Executing on {server_id}...")
                    
                    result = self.ebon_manager.execute_command(server_id, command)
                    
                    print(f"\n📋 Result:")
                    print(f"   Success: {result['success']}")
                    if result.get('output'):
                        print(f"   Output:\n{result['output']}")
                    if result.get('error'):
                        print(f"   Error:\n{result['error']}")
                else:
                    print("❌ No command specified")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def view_server_logs(self):
        """View logs from selected server"""
        servers = list(self.ebon_manager.servers.keys())
        
        if not servers:
            print("❌ No servers configured")
            return
        
        print("\n📋 Select server for log viewing:")
        for i, server_id in enumerate(servers, 1):
            server = self.ebon_manager.servers[server_id]
            print(f"  {i}. {server['name']}")
        
        try:
            choice = int(input("\n🎯 Select server: ")) - 1
            if 0 <= choice < len(servers):
                server_id = servers[choice]
                
                log_file = input("📄 Log file [/var/log/syslog]: ").strip()
                if not log_file:
                    log_file = "/var/log/syslog"
                
                lines = input("📝 Number of lines [50]: ").strip()
                try:
                    lines = int(lines) if lines else 50
                except ValueError:
                    lines = 50
                
                print(f"📋 Retrieving logs from {server_id}...")
                logs = self.ebon_manager.get_server_logs(server_id, log_file, lines)
                
                print(f"\n📋 Last {lines} lines from {log_file}:")
                print("-" * 60)
                for line in logs:
                    print(line)
                
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def server_configuration(self):
        """Server configuration management"""
        print("\n⚙️  Server Configuration")
        print("-" * 25)
        print("1. 📝 Edit Server Details")
        print("2. 🔑 SSH Key Management") 
        print("3. 🔧 Service Configuration")
        print("4. 🗑️  Remove Server")
        print("5. 🔙 Back")
        
        choice = input("\n🎯 Select option (1-5): ").strip()
        
        if choice == '1':
            print("📝 Server editing not implemented in demo")
        elif choice == '2':
            print("🔑 SSH key management not implemented in demo")
        elif choice == '3':
            print("🔧 Service configuration not implemented in demo")
        elif choice == '4':
            print("🗑️  Server removal not implemented in demo")
        elif choice == '5':
            return
    
    def add_manual_server(self):
        """Add server manually"""
        print("\n➕ Add Manual Server")
        print("-" * 20)
        
        hostname = input("🖥️  Hostname (e.g., ebon-db): ").strip()
        if not hostname:
            return
        
        host = input("🌐 IP Address: ").strip()
        if not host:
            return
        
        port = input("🔌 SSH Port [22]: ").strip()
        try:
            port = int(port) if port else 22
        except ValueError:
            port = 22
        
        username = input("👤 Username [ebon]: ").strip()
        if not username:
            username = "ebon"
        
        description = input("📝 Description: ").strip()
        
        # Add to servers
        self.ebon_manager.servers[hostname] = {
            'host': host,
            'port': port,
            'username': username,
            'name': hostname.replace('-', ' ').title(),
            'type': self.ebon_manager._determine_server_type(hostname),
            'description': description or f'Manually added {hostname}',
            'services': ['ssh'],
            'auto_discovered': False
        }
        
        print(f"✅ Added {hostname} to server list")
    
    def vpn_management_menu(self):
        """VPN provider management menu"""
        while True:
            print("\n🌐 VPN Provider Management")
            print("=" * 30)
            
            # Show available providers
            providers = self.vpn_manager.get_available_providers()
            
            print("📋 Available VPN Providers:")
            for provider in providers:
                status_emoji = "🟢" if provider['available'] else "🔴"
                type_tag = f"[{provider['type']}]"
                print(f"  {status_emoji} {provider['name']} {type_tag}")
                
                if provider['available']:
                    status = self.vpn_manager.get_provider_status(provider['id'])
                    if status.get('connected'):
                        print(f"     🔗 CONNECTED")
            
            # Show recommendation
            recommended = self.vpn_manager.recommend_best_vpn()
            if recommended:
                rec_name = self.vpn_manager.providers[recommended]['name']
                print(f"\n💡 Recommended: {rec_name}")
            
            print("\n1. 🔗 Connect to VPN")
            print("2. 🔌 Disconnect VPN")
            print("3. 📊 Provider Status")
            print("4. 📦 Install VPN Client")
            print("5. ⚙️  VPN Configuration")
            print("6. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-6): ").strip()
            
            if choice == '1':
                self.connect_vpn()
            elif choice == '2':
                self.disconnect_vpn()
            elif choice == '3':
                self.show_vpn_status()
            elif choice == '4':
                self.install_vpn_client()
            elif choice == '5':
                print("⚙️  VPN configuration not implemented in demo")
            elif choice == '6':
                break
            else:
                print("❌ Invalid choice")
    
    def connect_vpn(self):
        """Connect to selected VPN provider"""
        available_providers = [p for p in self.vpn_manager.get_available_providers() if p['available']]
        
        if not available_providers:
            print("❌ No VPN providers available")
            return
        
        print("\n🔗 Select VPN Provider:")
        for i, provider in enumerate(available_providers, 1):
            print(f"  {i}. {provider['name']}")
        
        try:
            choice = int(input("\n🎯 Select provider: ")) - 1
            if 0 <= choice < len(available_providers):
                provider_id = available_providers[choice]['id']
                
                location = input("🌍 Location (optional): ").strip()
                location = location if location else None
                
                if self.vpn_manager.connect_vpn(provider_id, location):
                    print("✅ VPN connection successful")
                else:
                    print("❌ VPN connection failed")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def disconnect_vpn(self):
        """Disconnect from VPN"""
        if self.vpn_manager.connection_status['connected']:
            provider = self.vpn_manager.connection_status['provider']
            if self.vpn_manager.disconnect_vpn(provider):
                print("✅ VPN disconnected")
            else:
                print("❌ Disconnect failed")
        else:
            print("ℹ️  No active VPN connection")
    
    def show_vpn_status(self):
        """Show detailed VPN status"""
        print("\n📊 VPN Provider Status")
        print("-" * 25)
        
        for provider_id, provider in self.vpn_manager.providers.items():
            print(f"\n🔹 {provider['name']}:")
            status = self.vpn_manager.get_provider_status(provider_id)
            
            for key, value in status.items():
                print(f"   {key}: {value}")
    
    def install_vpn_client(self):
        """Install VPN client"""
        print("\n📦 Install VPN Client")
        print("-" * 20)
        
        unavailable_providers = [p for p in self.vpn_manager.get_available_providers() if not p['available']]
        
        if not unavailable_providers:
            print("✅ All supported VPN clients are already installed")
            return
        
        print("Available for installation:")
        for i, provider in enumerate(unavailable_providers, 1):
            print(f"  {i}. {provider['name']}")
        
        try:
            choice = int(input("\n🎯 Select provider to install: ")) - 1
            if 0 <= choice < len(unavailable_providers):
                provider_name = unavailable_providers[choice]['name']
                print(f"📦 Installation of {provider_name} not implemented in demo")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def github_programs_menu(self):
        """GitHub programs management menu"""
        while True:
            print("\n🐙 GitHub Programs Management")
            print("=" * 35)
            
            if self.github_manager.current_account:
                print(f"👤 Active Account: {self.github_manager.current_account}")
                
                # Show local project summary
                local_projects = self.github_programs.scan_local_projects()
                github_projects = [p for p in local_projects if p['is_github']]
                projects_with_changes = [p for p in github_projects if p['has_uncommitted_changes']]
                
                print(f"📁 Local GitHub repos: {len(github_projects)}")
                if projects_with_changes:
                    print(f"📝 With uncommitted changes: {len(projects_with_changes)}")
            else:
                print("⚠️  No GitHub account configured")
            
            print("\n1. 📋 View Local Projects")
            print("2. 🔄 Sync All Repositories")
            print("3. 📥 Clone All GitHub Repos")
            print("4. 🚀 Push All Changes")
            print("5. 🐙 GitHub Account Management")
            print("6. 📦 Repository Operations")
            print("7. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-7): ").strip()
            
            if choice == '1':
                self.show_local_projects()
            elif choice == '2':
                self.sync_all_repositories()
            elif choice == '3':
                self.clone_all_repositories()
            elif choice == '4':
                self.push_all_changes()
            elif choice == '5':
                self.github_account_management()
            elif choice == '6':
                self.repository_operations()
            elif choice == '7':
                break
            else:
                print("❌ Invalid choice")
    
    def show_local_projects(self):
        """Show detailed local project information"""
        print("\n📋 Local GitHub Projects")
        print("-" * 25)
        
        projects = self.github_programs.scan_local_projects()
        github_projects = [p for p in projects if p['is_github']]
        
        if github_projects:
            for project in github_projects:
                changes_indicator = "📝" if project['has_uncommitted_changes'] else "✅"
                print(f"\n{changes_indicator} {project['name']}")
                print(f"   Path: {project['path']}")
                print(f"   Branch: {project['current_branch']}")
                print(f"   Remote: {project['remote_url']}")
                if project['last_commit']:
                    commit_hash, commit_msg = project['last_commit'].split(':', 1)
                    print(f"   Last commit: {commit_hash[:8]} - {commit_msg}")
        else:
            print("📁 No local GitHub repositories found")
            print("💡 Use option 3 to clone all your GitHub repositories")
    
    def sync_all_repositories(self):
        """Sync all local repositories"""
        print("\n🔄 Syncing All Repositories...")
        
        results = self.github_programs.sync_all_repos()
        
        print(f"\n📊 Sync Results:")
        print(f"   Total: {results['total']}")
        print(f"   ✅ Success: {results['success']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        if results['details']:
            print(f"\n📋 Details:")
            for detail in results['details']:
                status_emoji = "✅" if detail['status'] == 'success' else "❌"
                print(f"   {status_emoji} {detail['name']}: {detail['message']}")
    
    def clone_all_repositories(self):
        """Clone all repositories from GitHub"""
        if not self.github_manager.current_account:
            print("❌ No GitHub account configured")
            return
        
        confirm = input("📥 Clone all repositories from GitHub? (y/N): ").lower() == 'y'
        if not confirm:
            return
        
        print("\n📥 Cloning All GitHub Repositories...")
        
        results = self.github_programs.clone_all_repos()
        
        if 'error' in results:
            print(f"❌ Error: {results['error']}")
            return
        
        print(f"\n📊 Clone Results:")
        print(f"   Total: {results['total']}")
        print(f"   📥 Cloned: {results['cloned']}")
        print(f"   ⏭️  Skipped: {results['skipped']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        if results['details']:
            print(f"\n📋 Details:")
            for detail in results['details'][:10]:  # Show first 10
                if detail['status'] == 'cloned':
                    status_emoji = "📥"
                elif detail['status'] == 'skipped':
                    status_emoji = "⏭️"
                else:
                    status_emoji = "❌"
                print(f"   {status_emoji} {detail['name']}: {detail['message']}")
    
    def push_all_changes(self):
        """Push changes in all repositories"""
        print("\n🚀 Push All Changes")
        print("-" * 18)
        
        projects = self.github_programs.scan_local_projects()
        github_projects = [p for p in projects if p['is_github']]
        projects_with_changes = [p for p in github_projects if p['has_uncommitted_changes']]
        
        if not projects_with_changes:
            print("✅ No uncommitted changes found")
            return
        
        print(f"📝 Found {len(projects_with_changes)} projects with changes:")
        for project in projects_with_changes:
            print(f"   📝 {project['name']}")
        
        confirm = input("\n🚀 Commit and push all changes? (y/N): ").lower() == 'y'
        if not confirm:
            return
        
        commit_message = input("💬 Commit message [Auto-commit via NexusController]: ").strip()
        if not commit_message:
            commit_message = "Auto-commit via NexusController"
        
        for project in projects_with_changes:
            try:
                os.chdir(project['path'])
                
                # Add all changes
                subprocess.run(['git', 'add', '.'], capture_output=True)
                
                # Commit
                result = subprocess.run(['git', 'commit', '-m', commit_message], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Push
                    push_result = subprocess.run(['git', 'push'], capture_output=True, text=True)
                    
                    if push_result.returncode == 0:
                        print(f"   ✅ {project['name']}: Committed and pushed")
                    else:
                        print(f"   ⚠️  {project['name']}: Committed but push failed")
                else:
                    print(f"   ❌ {project['name']}: Commit failed")
                    
            except Exception as e:
                print(f"   ❌ {project['name']}: Error - {e}")
    
    def github_account_management(self):
        """GitHub account management"""
        from github_integration import account_management_menu
        account_management_menu(self.github_manager)
    
    def repository_operations(self):
        """Repository operations"""
        from github_integration import repository_menu
        repository_menu(self.github_manager)
    
    def main_menu(self):
        """Main control center menu"""
        while True:
            self.show_main_dashboard()
            
            print("\n🏢 NEXUS CONTROL CENTER")
            print("=" * 30)
            print("1. 🖥️  Ebon Server Management")
            print("2. 🌐 VPN Provider Management")
            print("3. 🐙 GitHub Programs Management")
            print("4. 🐳 Container Management")
            print("5. 📊 System Monitoring")
            print("6. 🔍 Network Operations")
            print("7. ⚙️  Configuration")
            print("8. 🚪 Exit")
            
            choice = input("\n🎯 Select option (1-8): ").strip()
            
            if choice == '1':
                self.server_management_menu()
            elif choice == '2':
                self.vpn_management_menu()
            elif choice == '3':
                self.github_programs_menu()
            elif choice == '4':
                self.container_management_menu()
            elif choice == '5':
                self.monitoring_menu()
            elif choice == '6':
                self.network_operations_menu()
            elif choice == '7':
                self.configuration_menu()
            elif choice == '8':
                print("👋 EbonCorp Control Center shutting down...")
                break
            else:
                print("❌ Invalid choice")
    
    def container_management_menu(self):
        """Container management operations"""
        print("\n🐳 Container Management")
        print("=" * 25)
        
        if not self.container_manager.docker_available:
            print("⚠️  Docker not available")
            return
        
        containers = self.container_manager.list_docker_containers()
        
        if containers:
            print(f"📦 Active containers ({len(containers)}):")
            for container in containers:
                print(f"   🐳 {container['name']} - {container['status']}")
                print(f"      Image: {container['image']} | Ports: {container['ports']}")
        else:
            print("📦 No containers running")
        
        input("\n📋 Press Enter to continue...")
    
    def monitoring_menu(self):
        """System monitoring menu"""
        health = self.monitoring_manager.check_system_health()
        
        if health:
            print(f"\n📊 System Health Report")
            print("=" * 25)
            print(f"🔥 CPU: {health['cpu']['percent']:.1f}%")
            print(f"💾 Memory: {health['memory']['percent']:.1f}%")
            print(f"🔢 Processes: {health['processes']}")
            
            # Disk usage
            for device, usage in health.get('disk', {}).items():
                disk_percent = (usage['used'] / usage['total']) * 100
                print(f"💿 {device}: {disk_percent:.1f}%")
        
        input("\n📋 Press Enter to continue...")
    
    def network_operations_menu(self):
        """Network operations menu"""
        print("\n🔍 Network Operations")
        print("=" * 20)
        
        print("1. 🌐 Network Discovery")
        print("2. 🔍 Port Scanning")
        print("3. 📊 Network Status")
        print("4. 🔙 Back")
        
        choice = input("\n🎯 Select option (1-4): ").strip()
        
        if choice == '1':
            print("🔍 Scanning local network...")
            hosts = self.network_scanner.scan_network()
            if hosts:
                print(f"\n🌐 Discovered {len(hosts)} hosts:")
                for host in hosts[:10]:  # Show first 10
                    print(f"   🖥️  {host['ip']} - {host['hostname']}")
            else:
                print("📝 No hosts discovered")
        
        elif choice == '2':
            target = input("🎯 Target IP to scan: ").strip()
            if target:
                print(f"🔍 Scanning {target}...")
                results = self.network_scanner.port_scan(target)
                if 'error' not in results:
                    print(f"\n🔍 Port scan results:")
                    for port, info in results['ports'].items():
                        status = "🟢 Open" if info['open'] else "🔴 Closed"
                        print(f"   {port}: {status} ({info['service']})")
        
        elif choice == '3':
            print("📊 Network status monitoring not implemented in demo")
        
        elif choice == '4':
            return
        
        input("\n📋 Press Enter to continue...")
    
    def configuration_menu(self):
        """Configuration management menu"""
        print("\n⚙️  Configuration Management")
        print("=" * 30)
        
        print("1. 🐙 GitHub Configuration")
        print("2. 🖥️  Server Configuration")
        print("3. 🌐 VPN Configuration")
        print("4. 📊 Monitoring Settings")
        print("5. 🔒 Security Settings")
        print("6. 🔙 Back")
        
        choice = input("\n🎯 Select option (1-6): ").strip()
        
        if choice == '1':
            print("🐙 Use GitHub Programs Management menu for GitHub configuration")
        elif choice == '2':
            print("🖥️  Use Server Management menu for server configuration")
        elif choice == '3':
            print("🌐 Use VPN Management menu for VPN configuration")
        elif choice == '4':
            print("📊 Monitoring settings not implemented in demo")
        elif choice == '5':
            print("🔒 Security settings not implemented in demo")
        elif choice == '6':
            return
    
    def run(self):
        """Run the control center"""
        try:
            print("\n🚀 EbonCorp Control Center starting...")
            self.main_menu()
        except KeyboardInterrupt:
            print("\n\n👋 Control Center shutdown")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.logger.log_event("application_error", {"error": str(e)})

def main():
    """Application entry point"""
    print("🏢 NexusController - EbonCorp Control Center")
    print("Centralized Infrastructure Management Platform")
    print("=" * 55)
    
    app = NexusControlCenter()
    app.run()

if __name__ == '__main__':
    main()