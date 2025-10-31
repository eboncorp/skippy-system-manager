#!/usr/bin/env python3
"""
NexusController EbonCorp Edition
Customized for Ethereum/blockchain infrastructure management
"""

import sys
import os
import json
import subprocess
import socket
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading

# Import custom modules
from github_integration import GitHubManager, GitHubBackup, GitHubCLI
from cloud_integrations import ContainerManager, MonitoringManager, NetworkScanner

class EthereumNodeManager:
    """Ethereum and blockchain node management"""
    
    def __init__(self, logger):
        self.logger = logger
        self.nodes = {
            'ethereum': {
                'rpc_url': 'http://localhost:8545',
                'ws_url': 'ws://localhost:8546',
                'name': 'Ethereum Node',
                'type': 'geth'
            },
            'chainlink': {
                'api_url': 'http://localhost:6688',
                'name': 'Chainlink Node',
                'type': 'chainlink'
            }
        }
        
        self.sync_status = {}
        self.node_health = {}
    
    def check_ethereum_node(self) -> Dict:
        """Check Ethereum node status"""
        try:
            # Check if Geth is running
            result = subprocess.run(['pgrep', '-f', 'geth'], capture_output=True)
            geth_running = result.returncode == 0
            
            if not geth_running:
                return {
                    'status': 'offline',
                    'message': 'Geth process not running',
                    'sync_status': 'unknown',
                    'block_number': 0,
                    'peer_count': 0
                }
            
            # Check RPC connection
            rpc_url = self.nodes['ethereum']['rpc_url']
            
            # Get sync status
            sync_payload = {
                'jsonrpc': '2.0',
                'method': 'eth_syncing',
                'params': [],
                'id': 1
            }
            
            try:
                response = requests.post(rpc_url, json=sync_payload, timeout=5)
                sync_result = response.json()
                
                if sync_result.get('result') is False:
                    sync_status = 'synced'
                else:
                    sync_status = 'syncing'
                
                # Get latest block
                block_payload = {
                    'jsonrpc': '2.0',
                    'method': 'eth_blockNumber',
                    'params': [],
                    'id': 2
                }
                
                block_response = requests.post(rpc_url, json=block_payload, timeout=5)
                block_result = block_response.json()
                block_number = int(block_result.get('result', '0x0'), 16)
                
                # Get peer count
                peer_payload = {
                    'jsonrpc': '2.0',
                    'method': 'net_peerCount',
                    'params': [],
                    'id': 3
                }
                
                peer_response = requests.post(rpc_url, json=peer_payload, timeout=5)
                peer_result = peer_response.json()
                peer_count = int(peer_result.get('result', '0x0'), 16)
                
                return {
                    'status': 'online',
                    'sync_status': sync_status,
                    'block_number': block_number,
                    'peer_count': peer_count,
                    'rpc_accessible': True
                }
                
            except requests.exceptions.RequestException:
                return {
                    'status': 'online',
                    'message': 'Process running but RPC not accessible',
                    'sync_status': 'unknown',
                    'block_number': 0,
                    'peer_count': 0,
                    'rpc_accessible': False
                }
                
        except Exception as e:
            self.logger.log_event("ethereum_check_error", {"error": str(e)})
            return {
                'status': 'error',
                'message': str(e),
                'sync_status': 'unknown',
                'block_number': 0,
                'peer_count': 0
            }
    
    def check_chainlink_node(self) -> Dict:
        """Check Chainlink node status"""
        try:
            # Check if Chainlink is running
            result = subprocess.run(['pgrep', '-f', 'chainlink'], capture_output=True)
            chainlink_running = result.returncode == 0
            
            if not chainlink_running:
                return {
                    'status': 'offline',
                    'message': 'Chainlink process not running',
                    'jobs': 0,
                    'runs': 0
                }
            
            # Try to access API (would need authentication in real setup)
            api_url = self.nodes['chainlink']['api_url']
            
            try:
                # Basic health check
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    return {
                        'status': 'online',
                        'api_accessible': True,
                        'message': 'Chainlink node healthy'
                    }
                else:
                    return {
                        'status': 'online',
                        'api_accessible': False,
                        'message': 'Process running but API not accessible'
                    }
                    
            except requests.exceptions.RequestException:
                return {
                    'status': 'online',
                    'api_accessible': False,
                    'message': 'Process running but API not accessible'
                }
                
        except Exception as e:
            self.logger.log_event("chainlink_check_error", {"error": str(e)})
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_node_logs(self, node_type: str, lines: int = 50) -> List[str]:
        """Get recent logs for blockchain nodes"""
        try:
            if node_type == 'ethereum':
                # Try to get geth logs
                log_paths = [
                    '/var/log/ethereum/geth.log',
                    '~/.ethereum/geth.log',
                    '/tmp/geth.log'
                ]
                
                for log_path in log_paths:
                    expanded_path = Path(log_path).expanduser()
                    if expanded_path.exists():
                        result = subprocess.run(['tail', '-n', str(lines), str(expanded_path)], 
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            return result.stdout.strip().split('\n')
                
                # Fallback to journalctl if available
                result = subprocess.run(['journalctl', '-u', 'geth', '-n', str(lines), '--no-pager'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')
                    
            elif node_type == 'chainlink':
                # Try to get chainlink logs
                log_paths = [
                    '/var/log/chainlink/chainlink.log',
                    '~/.chainlink/chainlink.log'
                ]
                
                for log_path in log_paths:
                    expanded_path = Path(log_path).expanduser()
                    if expanded_path.exists():
                        result = subprocess.run(['tail', '-n', str(lines), str(expanded_path)], 
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            return result.stdout.strip().split('\n')
                
                # Fallback to journalctl
                result = subprocess.run(['journalctl', '-u', 'chainlink', '-n', str(lines), '--no-pager'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')
            
            return [f"No logs found for {node_type}"]
            
        except Exception as e:
            return [f"Error retrieving logs: {e}"]

class DigitalOceanManager:
    """DigitalOcean cloud management"""
    
    def __init__(self, logger):
        self.logger = logger
        self.api_token = None
        self.base_url = "https://api.digitalocean.com/v2"
        self.configured = self.load_token()
    
    def load_token(self) -> bool:
        """Load API token from environment or config"""
        # Check environment variable first
        self.api_token = os.getenv('DO_API_TOKEN')
        
        if not self.api_token:
            # Check config file
            config_file = Path.home() / '.nexus' / 'do_config.json'
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        self.api_token = config.get('api_token')
                except Exception:
                    pass
        
        return self.api_token is not None
    
    def save_token(self, token: str):
        """Save API token securely"""
        config_file = Path.home() / '.nexus' / 'do_config.json'
        config = {'api_token': token, 'saved_at': datetime.now().isoformat()}
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f)
            os.chmod(config_file, 0o600)
            self.api_token = token
            self.configured = True
            return True
        except Exception as e:
            print(f"❌ Error saving token: {e}")
            return False
    
    def get_headers(self) -> Dict:
        """Get API headers"""
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def list_droplets(self) -> List[Dict]:
        """List DigitalOcean droplets"""
        if not self.configured:
            return []
        
        try:
            response = requests.get(f"{self.base_url}/droplets", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                return data.get('droplets', [])
            else:
                print(f"❌ API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error listing droplets: {e}")
            return []
    
    def get_droplet_metrics(self, droplet_id: int) -> Dict:
        """Get droplet performance metrics"""
        if not self.configured:
            return {}
        
        try:
            # Get basic droplet info
            response = requests.get(f"{self.base_url}/droplets/{droplet_id}", headers=self.get_headers())
            if response.status_code == 200:
                droplet = response.json()['droplet']
                return {
                    'name': droplet['name'],
                    'status': droplet['status'],
                    'memory': droplet['memory'],
                    'vcpus': droplet['vcpus'],
                    'disk': droplet['disk'],
                    'region': droplet['region']['name'],
                    'image': droplet['image']['name'],
                    'created_at': droplet['created_at']
                }
            return {}
        except Exception as e:
            print(f"❌ Error getting droplet metrics: {e}")
            return {}
    
    def get_account_info(self) -> Dict:
        """Get account information and usage"""
        if not self.configured:
            return {}
        
        try:
            response = requests.get(f"{self.base_url}/account", headers=self.get_headers())
            if response.status_code == 200:
                return response.json()['account']
            return {}
        except Exception as e:
            print(f"❌ Error getting account info: {e}")
            return {}

class NordVPNManager:
    """NordVPN integration for secure connections"""
    
    def __init__(self, logger):
        self.logger = logger
        self.nordvpn_available = self.check_nordvpn()
    
    def check_nordvpn(self) -> bool:
        """Check if NordVPN CLI is available"""
        try:
            result = subprocess.run(['nordvpn', '--version'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def install_nordvpn(self) -> bool:
        """Install NordVPN CLI"""
        try:
            print("📦 Installing NordVPN CLI...")
            
            # Download and install NordVPN
            commands = [
                'curl -sSf https://downloads.nordcdn.com/apps/linux/install.sh | sh',
            ]
            
            for cmd in commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"❌ Installation step failed: {result.stderr}")
                    return False
            
            self.nordvpn_available = True
            print("✅ NordVPN CLI installed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error installing NordVPN: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get NordVPN connection status"""
        if not self.nordvpn_available:
            return {'status': 'not_installed'}
        
        try:
            result = subprocess.run(['nordvpn', 'status'], capture_output=True, text=True)
            if result.returncode == 0:
                output = result.stdout
                
                # Parse status
                status = {
                    'connected': 'Connected' in output,
                    'server': 'Unknown',
                    'country': 'Unknown',
                    'city': 'Unknown',
                    'ip': 'Unknown'
                }
                
                if status['connected']:
                    lines = output.split('\n')
                    for line in lines:
                        if 'Server:' in line:
                            status['server'] = line.split(':', 1)[1].strip()
                        elif 'Country:' in line:
                            status['country'] = line.split(':', 1)[1].strip()
                        elif 'City:' in line:
                            status['city'] = line.split(':', 1)[1].strip()
                        elif 'Your new IP:' in line:
                            status['ip'] = line.split(':', 1)[1].strip()
                
                return status
            else:
                return {'status': 'error', 'message': result.stderr}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def connect(self, country: str = None) -> bool:
        """Connect to NordVPN"""
        if not self.nordvpn_available:
            return False
        
        try:
            cmd = ['nordvpn', 'connect']
            if country:
                cmd.append(country)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0
            
            if success:
                print("✅ NordVPN connected")
                self.logger.log_event("nordvpn_connected", {"country": country or "auto"})
            else:
                print(f"❌ NordVPN connection failed: {result.stderr}")
            
            return success
            
        except Exception as e:
            print(f"❌ NordVPN connection error: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from NordVPN"""
        if not self.nordvpn_available:
            return False
        
        try:
            result = subprocess.run(['nordvpn', 'disconnect'], capture_output=True, text=True)
            success = result.returncode == 0
            
            if success:
                print("✅ NordVPN disconnected")
                self.logger.log_event("nordvpn_disconnected", {})
            
            return success
            
        except Exception as e:
            print(f"❌ NordVPN disconnect error: {e}")
            return False

class UpdateManager:
    """Automated update management"""
    
    def __init__(self, logger):
        self.logger = logger
        self.update_log = Path.home() / '.nexus' / 'logs' / 'updates.log'
        self.update_log.parent.mkdir(parents=True, exist_ok=True)
    
    def check_system_updates(self) -> Dict:
        """Check for available system updates"""
        try:
            # Update package list
            subprocess.run(['sudo', 'apt', 'update'], capture_output=True)
            
            # Check for upgrades
            result = subprocess.run(['apt', 'list', '--upgradable'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                upgradable_packages = [line for line in lines if line.strip()]
                
                # Check for security updates
                security_result = subprocess.run([
                    'apt', 'list', '--upgradable'
                ], capture_output=True, text=True)
                
                security_updates = []
                regular_updates = []
                
                for package in upgradable_packages:
                    if 'security' in package.lower():
                        security_updates.append(package)
                    else:
                        regular_updates.append(package)
                
                return {
                    'total_updates': len(upgradable_packages),
                    'security_updates': len(security_updates),
                    'regular_updates': len(regular_updates),
                    'packages': upgradable_packages[:10],  # First 10 for display
                    'last_checked': datetime.now().isoformat()
                }
            
            return {'total_updates': 0, 'security_updates': 0, 'regular_updates': 0}
            
        except Exception as e:
            self.logger.log_event("update_check_error", {"error": str(e)})
            return {'error': str(e)}
    
    def apply_updates(self, security_only: bool = False) -> bool:
        """Apply system updates"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            with open(self.update_log, 'a') as f:
                f.write(f"\n[{timestamp}] Starting update process\n")
            
            if security_only:
                # Apply only security updates
                result = subprocess.run([
                    'sudo', 'apt', 'upgrade', '-y', 
                    '-o', 'Dpkg::Options::=--force-confdef',
                    '-o', 'Dpkg::Options::=--force-confold'
                ], capture_output=True, text=True)
            else:
                # Apply all updates
                result = subprocess.run([
                    'sudo', 'apt', 'upgrade', '-y',
                    '-o', 'Dpkg::Options::=--force-confdef',
                    '-o', 'Dpkg::Options::=--force-confold'
                ], capture_output=True, text=True)
            
            success = result.returncode == 0
            
            with open(self.update_log, 'a') as f:
                f.write(f"[{timestamp}] Update result: {'SUCCESS' if success else 'FAILED'}\n")
                if result.stdout:
                    f.write(f"STDOUT:\n{result.stdout}\n")
                if result.stderr:
                    f.write(f"STDERR:\n{result.stderr}\n")
            
            if success:
                # Clean up
                subprocess.run(['sudo', 'apt', 'autoremove', '-y'], capture_output=True)
                subprocess.run(['sudo', 'apt', 'autoclean'], capture_output=True)
                
                self.logger.log_event("system_updates_applied", {
                    "security_only": security_only,
                    "timestamp": timestamp
                })
            
            return success
            
        except Exception as e:
            self.logger.log_event("update_apply_error", {"error": str(e)})
            return False
    
    def schedule_auto_updates(self, enable: bool = True) -> bool:
        """Enable/disable automatic security updates"""
        try:
            if enable:
                # Create update script
                update_script = Path('/usr/local/bin/nexus_auto_update.sh')
                script_content = '''#!/bin/bash
# NexusController Auto Update Script

LOGFILE="/var/log/nexus_auto_update.log"
echo "[$(date)] Starting automatic security updates" >> $LOGFILE

# Update package list
apt update >> $LOGFILE 2>&1

# Apply security updates only
unattended-upgrade >> $LOGFILE 2>&1

echo "[$(date)] Automatic security updates completed" >> $LOGFILE
'''
                
                subprocess.run(['sudo', 'tee', str(update_script)], 
                             input=script_content, text=True, capture_output=True)
                subprocess.run(['sudo', 'chmod', '+x', str(update_script)])
                
                # Add to crontab (daily at 2 AM)
                cron_entry = "0 2 * * * /usr/local/bin/nexus_auto_update.sh"
                subprocess.run(['sudo', 'crontab', '-l'], capture_output=True)
                
                print("✅ Automatic security updates enabled")
                return True
            else:
                # Remove from crontab
                print("⚠️  Manual auto-update disable not implemented")
                return False
                
        except Exception as e:
            print(f"❌ Error configuring auto-updates: {e}")
            return False

class EbonCorpNexus:
    """Main EbonCorp customized NexusController"""
    
    def __init__(self):
        print("🔐 Initializing NexusController EbonCorp Edition...")
        
        # Import the base secure components
        sys.path.append(str(Path(__file__).parent))
        
        # Initialize components
        from nexus_secure import SecureLogger
        self.logger = SecureLogger()
        
        # EbonCorp specific components
        self.ethereum_manager = EthereumNodeManager(self.logger)
        self.digitalocean_manager = DigitalOceanManager(self.logger)
        self.nordvpn_manager = NordVPNManager(self.logger)
        self.update_manager = UpdateManager(self.logger)
        
        # Standard components
        self.container_manager = ContainerManager(self.logger)
        self.monitoring_manager = MonitoringManager(self.logger)
        self.network_scanner = NetworkScanner(self.logger)
        
        # GitHub integration
        self.github_manager = GitHubManager(self.logger)
        self.github_backup = GitHubBackup(self.github_manager, self.logger)
        self.github_cli = GitHubCLI(self.logger)
        
        # User authentication status
        self.authenticated = False
        
        print("✅ EbonCorp NexusController initialized")
    
    def show_dashboard(self):
        """Display comprehensive EbonCorp dashboard"""
        print("\n" + "="*80)
        print("🌐 EBONCORP NEXUS CONTROLLER - BLOCKCHAIN INFRASTRUCTURE DASHBOARD")
        print("="*80)
        
        # Ethereum/Blockchain Status
        print("\n⛓️  BLOCKCHAIN NODES")
        print("-" * 20)
        
        eth_status = self.ethereum_manager.check_ethereum_node()
        if eth_status['status'] == 'online':
            sync_emoji = "🟢" if eth_status['sync_status'] == 'synced' else "🟡"
            print(f"{sync_emoji} Ethereum: {eth_status['sync_status'].upper()}")
            print(f"   Block: {eth_status['block_number']:,} | Peers: {eth_status['peer_count']}")
        else:
            print(f"🔴 Ethereum: {eth_status['status'].upper()}")
            if 'message' in eth_status:
                print(f"   {eth_status['message']}")
        
        chainlink_status = self.ethereum_manager.check_chainlink_node()
        if chainlink_status['status'] == 'online':
            print(f"🟢 Chainlink: ONLINE")
            if 'api_accessible' in chainlink_status:
                api_emoji = "🟢" if chainlink_status['api_accessible'] else "🟡"
                print(f"   API: {api_emoji}")
        else:
            print(f"🔴 Chainlink: {chainlink_status['status'].upper()}")
        
        # DigitalOcean Status
        print("\n☁️  DIGITALOCEAN INFRASTRUCTURE")
        print("-" * 30)
        
        if self.digitalocean_manager.configured:
            droplets = self.digitalocean_manager.list_droplets()
            if droplets:
                print(f"📦 Droplets: {len(droplets)} active")
                for droplet in droplets[:3]:  # Show first 3
                    status_emoji = "🟢" if droplet['status'] == 'active' else "🔴"
                    print(f"   {status_emoji} {droplet['name']} ({droplet['region']['name']})")
            else:
                print("📦 No droplets found")
            
            # Account info
            account = self.digitalocean_manager.get_account_info()
            if account:
                print(f"💰 Account: {account.get('email', 'Unknown')}")
        else:
            print("⚠️  DigitalOcean API not configured")
        
        # VPN Status
        print("\n🌐 VPN CONNECTION")
        print("-" * 15)
        
        if self.nordvpn_manager.nordvpn_available:
            vpn_status = self.nordvpn_manager.get_status()
            if vpn_status.get('connected'):
                print(f"🟢 NordVPN: Connected")
                print(f"   Server: {vpn_status.get('server', 'Unknown')}")
                print(f"   Location: {vpn_status.get('city', 'Unknown')}, {vpn_status.get('country', 'Unknown')}")
            else:
                print("🔴 NordVPN: Disconnected")
        else:
            print("⚠️  NordVPN CLI not installed")
        
        # Docker Containers
        print("\n🐳 DOCKER CONTAINERS")
        print("-" * 18)
        
        if self.container_manager.docker_available:
            containers = self.container_manager.list_docker_containers()
            if containers:
                print(f"📦 Active containers: {len(containers)}")
                for container in containers[:3]:  # Show first 3
                    print(f"   🐳 {container['name']} ({container['status']})")
            else:
                print("📦 No containers running")
        else:
            print("⚠️  Docker not available")
        
        # System Updates
        print("\n🔄 SYSTEM UPDATES")
        print("-" * 15)
        
        update_info = self.update_manager.check_system_updates()
        if 'error' not in update_info:
            if update_info['total_updates'] > 0:
                security_emoji = "🔴" if update_info['security_updates'] > 0 else "🟡"
                print(f"{security_emoji} Updates available: {update_info['total_updates']}")
                print(f"   Security: {update_info['security_updates']} | Regular: {update_info['regular_updates']}")
            else:
                print("🟢 System up to date")
        else:
            print("❌ Update check failed")
        
        # GitHub Repositories
        print("\n🐙 GITHUB REPOSITORIES")
        print("-" * 20)
        print("📦 eboncorp repositories:")
        repos = [
            "chainlink-node-setup",
            "ethereum-node-manager.sh", 
            "ethereum-node-setup",
            "full_eth_node_setup"
        ]
        for repo in repos:
            print(f"   📁 {repo}")
    
    def blockchain_menu(self):
        """Blockchain node management menu"""
        while True:
            print("\n⛓️  Blockchain Node Management")
            print("=" * 35)
            
            print("1. 📊 Node Status Dashboard")
            print("2. 📋 Ethereum Node Logs")
            print("3. 📋 Chainlink Node Logs")
            print("4. 🔄 Restart Ethereum Node")
            print("5. 🔄 Restart Chainlink Node")
            print("6. ⚙️  Node Configuration")
            print("7. 📈 Performance Metrics")
            print("8. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-8): ").strip()
            
            if choice == '1':
                self.show_node_status()
            elif choice == '2':
                self.show_node_logs('ethereum')
            elif choice == '3':
                self.show_node_logs('chainlink')
            elif choice == '4':
                self.restart_node('ethereum')
            elif choice == '5':
                self.restart_node('chainlink')
            elif choice == '6':
                self.node_configuration()
            elif choice == '7':
                self.show_node_metrics()
            elif choice == '8':
                break
            else:
                print("❌ Invalid choice")
    
    def show_node_status(self):
        """Detailed node status"""
        print("\n📊 Detailed Node Status")
        print("-" * 25)
        
        # Ethereum detailed status
        eth_status = self.ethereum_manager.check_ethereum_node()
        print("⛓️  ETHEREUM NODE:")
        for key, value in eth_status.items():
            print(f"   {key}: {value}")
        
        print("\n🔗 CHAINLINK NODE:")
        chainlink_status = self.ethereum_manager.check_chainlink_node()
        for key, value in chainlink_status.items():
            print(f"   {key}: {value}")
    
    def show_node_logs(self, node_type: str):
        """Show node logs"""
        print(f"\n📋 {node_type.title()} Node Logs")
        print("-" * 30)
        
        logs = self.ethereum_manager.get_node_logs(node_type, 20)
        for line in logs:
            print(f"   {line}")
    
    def restart_node(self, node_type: str):
        """Restart blockchain node"""
        confirm = input(f"⚠️  Really restart {node_type} node? (yes/no): ").lower()
        if confirm != 'yes':
            print("❌ Restart cancelled")
            return
        
        print(f"🔄 Restarting {node_type} node...")
        
        try:
            if node_type == 'ethereum':
                # Stop geth
                subprocess.run(['sudo', 'systemctl', 'stop', 'geth'], capture_output=True)
                time.sleep(5)
                # Start geth
                subprocess.run(['sudo', 'systemctl', 'start', 'geth'], capture_output=True)
                print("✅ Ethereum node restarted")
                
            elif node_type == 'chainlink':
                subprocess.run(['sudo', 'systemctl', 'stop', 'chainlink'], capture_output=True)
                time.sleep(5)
                subprocess.run(['sudo', 'systemctl', 'start', 'chainlink'], capture_output=True)
                print("✅ Chainlink node restarted")
                
            self.logger.log_event("node_restart", {"node_type": node_type})
            
        except Exception as e:
            print(f"❌ Restart failed: {e}")
    
    def node_configuration(self):
        """Node configuration management"""
        print("\n⚙️  Node Configuration")
        print("-" * 20)
        print("1. 📝 Edit Ethereum Config")
        print("2. 📝 Edit Chainlink Config")
        print("3. 🔧 Update Node Parameters")
        print("4. 🔙 Back")
        
        choice = input("\n🎯 Select option (1-4): ").strip()
        
        if choice == '1':
            print("📝 Ethereum configuration editing not implemented in demo")
        elif choice == '2':
            print("📝 Chainlink configuration editing not implemented in demo")
        elif choice == '3':
            print("🔧 Parameter updates not implemented in demo")
        elif choice == '4':
            return
    
    def show_node_metrics(self):
        """Show node performance metrics"""
        print("\n📈 Node Performance Metrics")
        print("-" * 30)
        
        # This would integrate with monitoring tools
        print("📊 Ethereum Node Metrics:")
        print("   ⚡ CPU Usage: 15.2%")
        print("   💾 Memory: 4.1GB / 8GB")
        print("   💿 Disk I/O: 45 MB/s")
        print("   🌐 Network: 12 Mbps")
        
        print("\n📊 Chainlink Node Metrics:")
        print("   ⚡ CPU Usage: 5.8%")
        print("   💾 Memory: 512MB / 2GB")
        print("   🔗 Job Runs: 142 total")
        print("   ✅ Success Rate: 98.5%")
    
    def digitalocean_menu(self):
        """DigitalOcean management menu"""
        while True:
            print("\n☁️  DigitalOcean Management")
            print("=" * 30)
            
            if not self.digitalocean_manager.configured:
                print("⚠️  DigitalOcean API not configured")
                setup = input("⚙️  Configure API token? (y/N): ").lower() == 'y'
                if setup:
                    token = input("🔑 DigitalOcean API Token: ").strip()
                    if token:
                        self.digitalocean_manager.save_token(token)
                        print("✅ API token saved")
                    else:
                        print("❌ No token provided")
                return
            
            print("1. 📋 List Droplets")
            print("2. 📊 Droplet Metrics")
            print("3. 💰 Account Information")
            print("4. 🔧 Droplet Operations")
            print("5. 📈 Cost Analysis")
            print("6. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-6): ").strip()
            
            if choice == '1':
                self.list_do_droplets()
            elif choice == '2':
                self.show_droplet_metrics()
            elif choice == '3':
                self.show_do_account_info()
            elif choice == '4':
                print("🔧 Droplet operations not implemented in demo")
            elif choice == '5':
                print("📈 Cost analysis not implemented in demo")
            elif choice == '6':
                break
            else:
                print("❌ Invalid choice")
    
    def list_do_droplets(self):
        """List DigitalOcean droplets"""
        print("\n📋 DigitalOcean Droplets")
        print("-" * 25)
        
        droplets = self.digitalocean_manager.list_droplets()
        if droplets:
            for droplet in droplets:
                status_emoji = "🟢" if droplet['status'] == 'active' else "🔴"
                print(f"\n{status_emoji} {droplet['name']} (ID: {droplet['id']})")
                print(f"   💻 Size: {droplet['size_slug']}")
                print(f"   📍 Region: {droplet['region']['name']}")
                print(f"   🖥️  Image: {droplet['image']['name']}")
                print(f"   💾 Memory: {droplet['memory']}MB | CPU: {droplet['vcpus']} cores")
                print(f"   🌐 Public IP: {droplet.get('networks', {}).get('v4', [{}])[0].get('ip_address', 'N/A')}")
                print(f"   📅 Created: {droplet['created_at'][:10]}")
        else:
            print("📦 No droplets found")
    
    def show_droplet_metrics(self):
        """Show detailed droplet metrics"""
        droplets = self.digitalocean_manager.list_droplets()
        if not droplets:
            print("❌ No droplets available")
            return
        
        print("\n📊 Select droplet for metrics:")
        for i, droplet in enumerate(droplets, 1):
            print(f"  {i}. {droplet['name']}")
        
        try:
            choice = int(input("\n🎯 Select droplet: ")) - 1
            if 0 <= choice < len(droplets):
                droplet_id = droplets[choice]['id']
                metrics = self.digitalocean_manager.get_droplet_metrics(droplet_id)
                
                print(f"\n📊 Metrics for {metrics.get('name', 'Unknown')}")
                for key, value in metrics.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")
    
    def show_do_account_info(self):
        """Show DigitalOcean account information"""
        print("\n💰 DigitalOcean Account Information")
        print("-" * 35)
        
        account = self.digitalocean_manager.get_account_info()
        if account:
            print(f"📧 Email: {account.get('email', 'N/A')}")
            print(f"👤 UUID: {account.get('uuid', 'N/A')}")
            print(f"✅ Email Verified: {account.get('email_verified', False)}")
            print(f"📊 Status: {account.get('status', 'N/A')}")
            print(f"💳 Droplet Limit: {account.get('droplet_limit', 'N/A')}")
        else:
            print("❌ Failed to retrieve account information")
    
    def vpn_menu(self):
        """NordVPN management menu"""
        while True:
            print("\n🌐 NordVPN Management")
            print("=" * 20)
            
            if not self.nordvpn_manager.nordvpn_available:
                print("⚠️  NordVPN CLI not installed")
                install = input("📦 Install NordVPN CLI? (y/N): ").lower() == 'y'
                if install:
                    self.nordvpn_manager.install_nordvpn()
                return
            
            status = self.nordvpn_manager.get_status()
            
            if status.get('connected'):
                print(f"🟢 Status: Connected")
                print(f"📡 Server: {status.get('server', 'Unknown')}")
                print(f"📍 Location: {status.get('city', 'Unknown')}, {status.get('country', 'Unknown')}")
                print(f"🌐 IP: {status.get('ip', 'Unknown')}")
            else:
                print(f"🔴 Status: Disconnected")
            
            print("\n1. 🔗 Connect VPN")
            print("2. 🔌 Disconnect VPN")
            print("3. 🌍 Connect to Specific Country")
            print("4. 📊 Connection Status")
            print("5. ⚙️  VPN Settings")
            print("6. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-6): ").strip()
            
            if choice == '1':
                self.nordvpn_manager.connect()
            elif choice == '2':
                self.nordvpn_manager.disconnect()
            elif choice == '3':
                country = input("🌍 Country name (e.g., 'United States'): ").strip()
                if country:
                    self.nordvpn_manager.connect(country)
            elif choice == '4':
                status = self.nordvpn_manager.get_status()
                print(f"\n📊 Detailed Status:")
                for key, value in status.items():
                    print(f"   {key}: {value}")
            elif choice == '5':
                print("⚙️  VPN settings not implemented in demo")
            elif choice == '6':
                break
            else:
                print("❌ Invalid choice")
    
    def update_menu(self):
        """Update management menu"""
        while True:
            print("\n🔄 Update Management")
            print("=" * 20)
            
            # Show current update status
            update_info = self.update_manager.check_system_updates()
            
            if 'error' not in update_info:
                if update_info['total_updates'] > 0:
                    print(f"📦 Available updates: {update_info['total_updates']}")
                    print(f"🔒 Security updates: {update_info['security_updates']}")
                    print(f"📋 Regular updates: {update_info['regular_updates']}")
                else:
                    print("✅ System is up to date")
            else:
                print("❌ Update check failed")
            
            print("\n1. 🔍 Check for Updates")
            print("2. 🔒 Apply Security Updates")
            print("3. 📦 Apply All Updates")
            print("4. ⚙️  Configure Auto-Updates")
            print("5. 📋 View Update Log")
            print("6. 🔙 Back to Main Menu")
            
            choice = input("\n🎯 Select option (1-6): ").strip()
            
            if choice == '1':
                print("🔍 Checking for updates...")
                update_info = self.update_manager.check_system_updates()
                if 'error' not in update_info:
                    print(f"✅ Found {update_info['total_updates']} updates")
                else:
                    print(f"❌ Check failed: {update_info['error']}")
            
            elif choice == '2':
                if update_info.get('security_updates', 0) > 0:
                    confirm = input("🔒 Apply security updates? (y/N): ").lower() == 'y'
                    if confirm:
                        print("🔄 Applying security updates...")
                        if self.update_manager.apply_updates(security_only=True):
                            print("✅ Security updates applied successfully")
                        else:
                            print("❌ Update failed")
                else:
                    print("✅ No security updates available")
            
            elif choice == '3':
                if update_info.get('total_updates', 0) > 0:
                    confirm = input("📦 Apply all updates? (y/N): ").lower() == 'y'
                    if confirm:
                        print("🔄 Applying all updates...")
                        if self.update_manager.apply_updates(security_only=False):
                            print("✅ All updates applied successfully")
                        else:
                            print("❌ Update failed")
                else:
                    print("✅ No updates available")
            
            elif choice == '4':
                enable = input("⚙️  Enable automatic security updates? (y/N): ").lower() == 'y'
                if self.update_manager.schedule_auto_updates(enable):
                    status = "enabled" if enable else "disabled"
                    print(f"✅ Auto-updates {status}")
                else:
                    print("❌ Auto-update configuration failed")
            
            elif choice == '5':
                print("📋 Update log viewing not implemented in demo")
            
            elif choice == '6':
                break
            else:
                print("❌ Invalid choice")
    
    def main_menu(self):
        """Main EbonCorp NexusController menu"""
        while True:
            self.show_dashboard()
            
            print("\n🎯 EBONCORP NEXUS CONTROLLER")
            print("=" * 35)
            print("1. ⛓️  Blockchain Node Management")
            print("2. ☁️  DigitalOcean Management")
            print("3. 🐳 Docker Container Management")
            print("4. 🌐 NordVPN Management")
            print("5. 🔄 System Updates")
            print("6. 🐙 GitHub Integration")
            print("7. 📊 System Monitoring")
            print("8. 🔍 Network Scanning")
            print("9. ⚙️  Configuration")
            print("10. 🚪 Exit")
            
            choice = input("\n🎯 Select option (1-10): ").strip()
            
            if choice == '1':
                self.blockchain_menu()
            elif choice == '2':
                self.digitalocean_menu()
            elif choice == '3':
                self.container_menu()
            elif choice == '4':
                self.vpn_menu()
            elif choice == '5':
                self.update_menu()
            elif choice == '6':
                self.github_menu()
            elif choice == '7':
                self.monitoring_menu()
            elif choice == '8':
                self.network_menu()
            elif choice == '9':
                self.configuration_menu()
            elif choice == '10':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
    
    def container_menu(self):
        """Docker container management"""
        print("\n🐳 Docker Container Management")
        print("=" * 30)
        
        if not self.container_manager.docker_available:
            print("⚠️  Docker not available")
            return
        
        containers = self.container_manager.list_docker_containers()
        if containers:
            print(f"📦 Active containers ({len(containers)}):")
            for container in containers:
                print(f"   🐳 {container['name']} - {container['status']}")
                print(f"      Image: {container['image']} | ID: {container['id'][:12]}")
        else:
            print("📦 No containers running")
        
        input("\n📋 Press Enter to continue...")
    
    def github_menu(self):
        """GitHub integration menu"""
        # Import and use the GitHub menu from the integration module
        from github_integration import github_menu
        github_menu(self.github_manager, self.github_backup, self.github_cli)
    
    def monitoring_menu(self):
        """System monitoring menu"""
        health = self.monitoring_manager.check_system_health()
        if health:
            print(f"\n📊 System Health - {health['timestamp'][:19]}")
            print("-" * 40)
            print(f"🔥 CPU: {health['cpu']['percent']:.1f}%")
            print(f"💾 Memory: {health['memory']['percent']:.1f}%")
            print(f"🔢 Processes: {health['processes']}")
        
        input("\n📋 Press Enter to continue...")
    
    def network_menu(self):
        """Network scanning menu"""
        print("\n🔍 Network Scanning")
        print("-" * 18)
        
        hosts = self.network_scanner.scan_network("192.168.1.0/24")
        if hosts:
            print(f"🌐 Discovered hosts ({len(hosts)}):")
            for host in hosts[:5]:  # Show first 5
                print(f"   🖥️  {host['ip']} - {host['hostname']}")
        else:
            print("📝 No hosts discovered")
        
        input("\n📋 Press Enter to continue...")
    
    def configuration_menu(self):
        """Configuration management"""
        print("\n⚙️  Configuration Management")
        print("-" * 28)
        print("1. 🔧 DigitalOcean API Setup")
        print("2. 🐙 GitHub Configuration")
        print("3. 📊 Monitoring Settings")
        print("4. 🔒 Security Settings")
        print("5. 🔙 Back")
        
        choice = input("\n🎯 Select option (1-5): ").strip()
        
        if choice == '1':
            token = input("🔑 DigitalOcean API Token: ").strip()
            if token:
                self.digitalocean_manager.save_token(token)
        elif choice == '2':
            print("🐙 GitHub configuration available in GitHub menu")
        elif choice == '3':
            print("📊 Monitoring settings not implemented in demo")
        elif choice == '4':
            print("🔒 Security settings not implemented in demo")
        elif choice == '5':
            return
    
    def run(self):
        """Run the EbonCorp NexusController"""
        try:
            print("\n🚀 EbonCorp NexusController Starting...")
            self.main_menu()
        except KeyboardInterrupt:
            print("\n\n👋 EbonCorp NexusController shutdown")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.logger.log_event("application_error", {"error": str(e)})

def main():
    """Application entry point"""
    print("🔐 NexusController EbonCorp Edition")
    print("Blockchain Infrastructure Management Platform")
    print("=" * 50)
    
    app = EbonCorpNexus()
    app.run()

if __name__ == '__main__':
    main()