#!/usr/bin/env python3
"""
Cloud Service Integrations for NexusController Secure
AWS, Azure, GCP, DigitalOcean, and other cloud provider management
"""

import boto3
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class AWSManager:
    """AWS service management and monitoring"""
    
    def __init__(self, logger):
        self.logger = logger
        self.session = None
        self.credentials_configured = self.check_credentials()
    
    def check_credentials(self) -> bool:
        """Check if AWS credentials are configured"""
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            return credentials is not None
        except Exception:
            return False
    
    def configure_credentials(self, access_key: str, secret_key: str, region: str = 'us-east-1'):
        """Configure AWS credentials"""
        try:
            aws_dir = Path.home() / '.aws'
            aws_dir.mkdir(mode=0o700, exist_ok=True)
            
            # Write credentials
            credentials_file = aws_dir / 'credentials'
            with open(credentials_file, 'w') as f:
                f.write(f"[default]\n")
                f.write(f"aws_access_key_id = {access_key}\n")
                f.write(f"aws_secret_access_key = {secret_key}\n")
            
            os.chmod(credentials_file, 0o600)
            
            # Write config
            config_file = aws_dir / 'config'
            with open(config_file, 'w') as f:
                f.write(f"[default]\n")
                f.write(f"region = {region}\n")
                f.write(f"output = json\n")
            
            self.credentials_configured = True
            print("✅ AWS credentials configured")
            return True
            
        except Exception as e:
            print(f"❌ Error configuring AWS credentials: {e}")
            return False
    
    def list_ec2_instances(self) -> List[Dict]:
        """List EC2 instances"""
        if not self.credentials_configured:
            return []
        
        try:
            ec2 = boto3.client('ec2')
            response = ec2.describe_instances()
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'id': instance['InstanceId'],
                        'type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'public_ip': instance.get('PublicIpAddress', 'N/A'),
                        'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                        'name': next((tag['Value'] for tag in instance.get('Tags', []) 
                                    if tag['Key'] == 'Name'), 'Unnamed')
                    })
            
            return instances
            
        except Exception as e:
            print(f"❌ Error listing EC2 instances: {e}")
            return []
    
    def get_cost_and_usage(self, days: int = 30) -> Dict:
        """Get AWS cost and usage data"""
        if not self.credentials_configured:
            return {}
        
        try:
            from datetime import timedelta
            
            ce = boto3.client('ce')
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            response = ce.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            return response
            
        except Exception as e:
            print(f"❌ Error getting cost data: {e}")
            return {}

class ContainerManager:
    """Docker and Kubernetes management"""
    
    def __init__(self, logger):
        self.logger = logger
        self.docker_available = self.check_docker()
        self.kubectl_available = self.check_kubectl()
    
    def check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_kubectl(self) -> bool:
        """Check if kubectl is available"""
        try:
            result = subprocess.run(['kubectl', 'version', '--client'], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def list_docker_containers(self) -> List[Dict]:
        """List Docker containers"""
        if not self.docker_available:
            return []
        
        try:
            result = subprocess.run([
                'docker', 'ps', '--format', 
                'table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                containers = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            containers.append({
                                'id': parts[0],
                                'image': parts[1],
                                'status': parts[2],
                                'ports': parts[3],
                                'name': parts[4]
                            })
                
                return containers
            
            return []
            
        except Exception as e:
            print(f"❌ Error listing Docker containers: {e}")
            return []
    
    def get_k8s_pods(self) -> List[Dict]:
        """Get Kubernetes pods"""
        if not self.kubectl_available:
            return []
        
        try:
            result = subprocess.run([
                'kubectl', 'get', 'pods', '-o', 'json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                pods = []
                
                for pod in data.get('items', []):
                    pods.append({
                        'name': pod['metadata']['name'],
                        'namespace': pod['metadata']['namespace'],
                        'status': pod['status']['phase'],
                        'ready': self.count_ready_containers(pod),
                        'restarts': self.count_restarts(pod),
                        'age': self.calculate_age(pod['metadata']['creationTimestamp'])
                    })
                
                return pods
            
            return []
            
        except Exception as e:
            print(f"❌ Error getting Kubernetes pods: {e}")
            return []
    
    def count_ready_containers(self, pod: Dict) -> str:
        """Count ready containers in pod"""
        containers = pod['status'].get('containerStatuses', [])
        ready = sum(1 for c in containers if c.get('ready', False))
        total = len(containers)
        return f"{ready}/{total}"
    
    def count_restarts(self, pod: Dict) -> int:
        """Count total restarts for pod"""
        containers = pod['status'].get('containerStatuses', [])
        return sum(c.get('restartCount', 0) for c in containers)
    
    def calculate_age(self, creation_timestamp: str) -> str:
        """Calculate pod age"""
        try:
            from dateutil import parser
            created = parser.parse(creation_timestamp)
            now = datetime.now(created.tzinfo)
            delta = now - created
            
            if delta.days > 0:
                return f"{delta.days}d"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600}h"
            else:
                return f"{delta.seconds // 60}m"
        except:
            return "unknown"

class DatabaseManager:
    """Database connection and management"""
    
    def __init__(self, logger):
        self.logger = logger
        self.connections = {}
    
    def add_database(self, name: str, db_type: str, host: str, port: int, 
                    username: str, password: str, database: str = None):
        """Add database connection"""
        self.connections[name] = {
            'type': db_type,
            'host': host,
            'port': port,
            'username': username,
            'password': password,  # In production, encrypt this
            'database': database,
            'added_at': datetime.now().isoformat()
        }
    
    def test_connection(self, name: str) -> bool:
        """Test database connection"""
        if name not in self.connections:
            return False
        
        conn_info = self.connections[name]
        db_type = conn_info['type'].lower()
        
        try:
            if db_type == 'postgresql':
                import psycopg2
                conn = psycopg2.connect(
                    host=conn_info['host'],
                    port=conn_info['port'],
                    user=conn_info['username'],
                    password=conn_info['password'],
                    database=conn_info.get('database', 'postgres')
                )
                conn.close()
                return True
                
            elif db_type == 'mysql':
                import mysql.connector
                conn = mysql.connector.connect(
                    host=conn_info['host'],
                    port=conn_info['port'],
                    user=conn_info['username'],
                    password=conn_info['password'],
                    database=conn_info.get('database')
                )
                conn.close()
                return True
                
            elif db_type == 'redis':
                import redis
                r = redis.Redis(
                    host=conn_info['host'],
                    port=conn_info['port'],
                    password=conn_info['password']
                )
                r.ping()
                return True
                
            else:
                print(f"❌ Unsupported database type: {db_type}")
                return False
                
        except ImportError as e:
            print(f"❌ Database driver not installed: {e}")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

class MonitoringManager:
    """System monitoring and alerting"""
    
    def __init__(self, logger):
        self.logger = logger
        self.alerts = []
        self.thresholds = {
            'cpu': 80,
            'memory': 85,
            'disk': 90,
            'network': 1000  # MB/s
        }
    
    def check_system_health(self) -> Dict:
        """Comprehensive system health check"""
        try:
            import psutil
            
            health = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                },
                'memory': psutil.virtual_memory()._asdict(),
                'disk': {},
                'network': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                'processes': len(psutil.pids()),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
            # Disk usage for all mounted drives
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    health['disk'][partition.device] = usage._asdict()
                except PermissionError:
                    continue
            
            # Check for alerts
            self.check_alerts(health)
            
            return health
            
        except Exception as e:
            self.logger.log_event("health_check_error", {"error": str(e)})
            return {}
    
    def check_alerts(self, health: Dict):
        """Check for alert conditions"""
        alerts = []
        
        # CPU alert
        if health['cpu']['percent'] > self.thresholds['cpu']:
            alerts.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f"CPU usage high: {health['cpu']['percent']:.1f}%",
                'threshold': self.thresholds['cpu'],
                'current': health['cpu']['percent']
            })
        
        # Memory alert
        memory_percent = health['memory']['percent']
        if memory_percent > self.thresholds['memory']:
            alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f"Memory usage high: {memory_percent:.1f}%",
                'threshold': self.thresholds['memory'],
                'current': memory_percent
            })
        
        # Disk alerts
        for device, usage in health['disk'].items():
            disk_percent = (usage['used'] / usage['total']) * 100
            if disk_percent > self.thresholds['disk']:
                alerts.append({
                    'type': 'disk',
                    'level': 'critical' if disk_percent > 95 else 'warning',
                    'message': f"Disk {device} full: {disk_percent:.1f}%",
                    'threshold': self.thresholds['disk'],
                    'current': disk_percent
                })
        
        if alerts:
            self.alerts.extend(alerts)
            for alert in alerts:
                self.logger.log_event("system_alert", alert)
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        # In a real implementation, this would query stored alerts
        return self.alerts

class NetworkScanner:
    """Network scanning and discovery"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def scan_network(self, network: str = "192.168.1.0/24") -> List[Dict]:
        """Scan network for active hosts"""
        try:
            # Use nmap if available
            result = subprocess.run([
                'nmap', '-sn', network
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                hosts = []
                lines = result.stdout.split('\n')
                
                for i, line in enumerate(lines):
                    if 'Nmap scan report for' in line:
                        ip = line.split()[-1].strip('()')
                        
                        # Try to get hostname
                        hostname = 'Unknown'
                        if i + 1 < len(lines) and 'Host is up' in lines[i + 1]:
                            hostname_line = line.replace('Nmap scan report for ', '')
                            if '(' in hostname_line:
                                hostname = hostname_line.split(' (')[0]
                        
                        hosts.append({
                            'ip': ip,
                            'hostname': hostname,
                            'status': 'up'
                        })
                
                return hosts
            
            return []
            
        except FileNotFoundError:
            print("❌ nmap not installed. Install with: sudo apt install nmap")
            return []
        except Exception as e:
            print(f"❌ Network scan error: {e}")
            return []
    
    def port_scan(self, host: str, ports: List[int] = None) -> Dict:
        """Scan specific ports on host"""
        if ports is None:
            ports = [22, 80, 443, 3389, 5432, 3306]  # Common ports
        
        try:
            import socket
            
            results = {
                'host': host,
                'scanned_at': datetime.now().isoformat(),
                'ports': {}
            }
            
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                
                results['ports'][port] = {
                    'open': result == 0,
                    'service': self.identify_service(port)
                }
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def identify_service(self, port: int) -> str:
        """Identify common services by port"""
        services = {
            22: 'SSH',
            80: 'HTTP',
            443: 'HTTPS',
            3389: 'RDP',
            5432: 'PostgreSQL',
            3306: 'MySQL',
            6379: 'Redis',
            27017: 'MongoDB',
            8080: 'HTTP-Alt',
            8443: 'HTTPS-Alt'
        }
        return services.get(port, 'Unknown')

def cloud_menu(aws_manager, container_manager, database_manager, monitoring_manager, network_scanner):
    """Cloud services menu"""
    while True:
        print("\n☁️  Cloud & Infrastructure Management")
        print("=" * 40)
        
        print("1. 🌩️  AWS Management")
        print("2. 🐳 Container Management")
        print("3. 🗄️  Database Management")
        print("4. 📊 System Monitoring")
        print("5. 🔍 Network Scanning")
        print("6. 🔙 Back to Main Menu")
        
        choice = input("\n🎯 Select option (1-6): ").strip()
        
        if choice == '1':
            aws_menu(aws_manager)
        elif choice == '2':
            container_menu(container_manager)
        elif choice == '3':
            database_menu(database_manager)
        elif choice == '4':
            monitoring_menu(monitoring_manager)
        elif choice == '5':
            network_menu(network_scanner)
        elif choice == '6':
            break
        else:
            print("❌ Invalid choice")

def aws_menu(aws_manager):
    """AWS management submenu"""
    print("\n🌩️  AWS Management")
    print("-" * 20)
    
    if not aws_manager.credentials_configured:
        print("❌ AWS credentials not configured")
        setup = input("⚙️  Configure AWS credentials? (y/N): ").lower() == 'y'
        if setup:
            access_key = input("🔑 Access Key ID: ").strip()
            secret_key = input("🔐 Secret Access Key: ").strip()
            region = input("🌍 Region [us-east-1]: ").strip() or 'us-east-1'
            aws_manager.configure_credentials(access_key, secret_key, region)
        return
    
    print("1. 🖥️  List EC2 Instances")
    print("2. 💰 Cost and Usage")
    print("3. 🔧 Configure Credentials")
    print("4. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-4): ").strip()
    
    if choice == '1':
        instances = aws_manager.list_ec2_instances()
        if instances:
            print(f"\n🖥️  EC2 Instances ({len(instances)} total):")
            for instance in instances:
                status_emoji = "🟢" if instance['state'] == 'running' else "🔴"
                print(f"  {status_emoji} {instance['name']} ({instance['id']})")
                print(f"     Type: {instance['type']} | State: {instance['state']}")
                print(f"     Public IP: {instance['public_ip']} | Private IP: {instance['private_ip']}")
        else:
            print("📝 No EC2 instances found")
    
    elif choice == '2':
        cost_data = aws_manager.get_cost_and_usage()
        if cost_data:
            print("💰 Cost and usage data retrieved (processing not implemented in demo)")
        else:
            print("❌ Failed to retrieve cost data")
    
    elif choice == '3':
        access_key = input("🔑 New Access Key ID: ").strip()
        secret_key = input("🔐 New Secret Access Key: ").strip()
        region = input("🌍 Region [us-east-1]: ").strip() or 'us-east-1'
        aws_manager.configure_credentials(access_key, secret_key, region)
    
    elif choice == '4':
        return

def container_menu(container_manager):
    """Container management submenu"""
    print("\n🐳 Container Management")
    print("-" * 25)
    
    docker_status = "🟢" if container_manager.docker_available else "🔴"
    kubectl_status = "🟢" if container_manager.kubectl_available else "🔴"
    
    print(f"Docker: {docker_status} | Kubernetes: {kubectl_status}")
    
    print("\n1. 📋 List Docker Containers")
    print("2. 🎯 Kubernetes Pods")
    print("3. 🐳 Docker Operations")
    print("4. ☸️  Kubernetes Operations")
    print("5. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-5): ").strip()
    
    if choice == '1':
        containers = container_manager.list_docker_containers()
        if containers:
            print(f"\n🐳 Docker Containers ({len(containers)} total):")
            for container in containers:
                print(f"  📦 {container['name']} ({container['id'][:12]})")
                print(f"     Image: {container['image']} | Status: {container['status']}")
                print(f"     Ports: {container['ports']}")
        else:
            print("📝 No Docker containers found")
    
    elif choice == '2':
        pods = container_manager.get_k8s_pods()
        if pods:
            print(f"\n☸️  Kubernetes Pods ({len(pods)} total):")
            for pod in pods:
                status_emoji = "🟢" if pod['status'] == 'Running' else "🔴"
                print(f"  {status_emoji} {pod['name']} ({pod['namespace']})")
                print(f"     Status: {pod['status']} | Ready: {pod['ready']} | Restarts: {pod['restarts']} | Age: {pod['age']}")
        else:
            print("📝 No Kubernetes pods found")
    
    elif choice == '3':
        print("🐳 Docker operations not implemented in this demo")
    
    elif choice == '4':
        print("☸️  Kubernetes operations not implemented in this demo")
    
    elif choice == '5':
        return

def database_menu(database_manager):
    """Database management submenu"""
    print("\n🗄️  Database Management")
    print("-" * 25)
    
    if database_manager.connections:
        print("📋 Configured Databases:")
        for name, conn in database_manager.connections.items():
            print(f"  🗄️  {name} ({conn['type']}) - {conn['host']}:{conn['port']}")
    else:
        print("📋 No databases configured")
    
    print("\n1. ➕ Add Database")
    print("2. 🔍 Test Connections")
    print("3. 📊 Database Operations")
    print("4. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-4): ").strip()
    
    if choice == '1':
        add_database(database_manager)
    elif choice == '2':
        test_database_connections(database_manager)
    elif choice == '3':
        print("📊 Database operations not implemented in this demo")
    elif choice == '4':
        return

def add_database(database_manager):
    """Add new database connection"""
    print("\n➕ Add Database Connection")
    
    name = input("📝 Database name: ").strip()
    if not name:
        return
    
    db_types = ["postgresql", "mysql", "redis", "mongodb"]
    print("\n📋 Database types:")
    for i, db_type in enumerate(db_types, 1):
        print(f"  {i}. {db_type}")
    
    try:
        type_choice = int(input("🎯 Select type (1-4): ")) - 1
        if 0 <= type_choice < len(db_types):
            db_type = db_types[type_choice]
            
            host = input("🌐 Host: ").strip()
            port = int(input("🔌 Port: ").strip())
            username = input("👤 Username: ").strip()
            password = input("🔐 Password: ").strip()
            database = input("🗄️  Database name (optional): ").strip() or None
            
            database_manager.add_database(name, db_type, host, port, username, password, database)
            print(f"✅ Database '{name}' added successfully")
        else:
            print("❌ Invalid database type")
    except ValueError:
        print("❌ Invalid input")

def test_database_connections(database_manager):
    """Test all database connections"""
    if not database_manager.connections:
        print("❌ No databases configured")
        return
    
    print("\n🔍 Testing Database Connections:")
    for name in database_manager.connections:
        print(f"  Testing {name}...", end=" ")
        if database_manager.test_connection(name):
            print("✅")
        else:
            print("❌")

def monitoring_menu(monitoring_manager):
    """Monitoring management submenu"""
    print("\n📊 System Monitoring")
    print("-" * 20)
    
    print("1. 📊 System Health Check")
    print("2. 🚨 Recent Alerts")
    print("3. ⚙️  Alert Thresholds")
    print("4. 📈 Performance History")
    print("5. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-5): ").strip()
    
    if choice == '1':
        health = monitoring_manager.check_system_health()
        if health:
            display_system_health(health)
        else:
            print("❌ Failed to get system health data")
    
    elif choice == '2':
        alerts = monitoring_manager.get_recent_alerts()
        if alerts:
            print(f"\n🚨 Recent Alerts ({len(alerts)} total):")
            for alert in alerts[-10:]:  # Show last 10
                level_emoji = "🔴" if alert['level'] == 'critical' else "🟡"
                print(f"  {level_emoji} {alert['type'].upper()}: {alert['message']}")
        else:
            print("✅ No recent alerts")
    
    elif choice == '3':
        configure_thresholds(monitoring_manager)
    
    elif choice == '4':
        print("📈 Performance history not implemented in this demo")
    
    elif choice == '5':
        return

def display_system_health(health):
    """Display comprehensive system health"""
    print(f"\n📊 System Health Report - {health['timestamp'][:19]}")
    print("-" * 50)
    
    # CPU
    cpu = health['cpu']
    cpu_emoji = "🟢" if cpu['percent'] < 70 else "🟡" if cpu['percent'] < 85 else "🔴"
    print(f"{cpu_emoji} CPU: {cpu['percent']:.1f}% ({cpu['count']} cores)")
    
    # Memory
    memory = health['memory']
    mem_emoji = "🟢" if memory['percent'] < 70 else "🟡" if memory['percent'] < 85 else "🔴"
    print(f"{mem_emoji} Memory: {memory['percent']:.1f}% ({memory['used'] // (1024**3):.1f}GB / {memory['total'] // (1024**3):.1f}GB)")
    
    # Disk
    for device, usage in health['disk'].items():
        disk_percent = (usage['used'] / usage['total']) * 100
        disk_emoji = "🟢" if disk_percent < 70 else "🟡" if disk_percent < 85 else "🔴"
        print(f"{disk_emoji} Disk {device}: {disk_percent:.1f}% ({usage['used'] // (1024**3):.1f}GB / {usage['total'] // (1024**3):.1f}GB)")
    
    print(f"🔢 Processes: {health['processes']}")
    print(f"⏰ Uptime: {health['boot_time'][:19]}")

def configure_thresholds(monitoring_manager):
    """Configure alert thresholds"""
    print("\n⚙️  Alert Threshold Configuration")
    print("-" * 35)
    
    thresholds = monitoring_manager.thresholds
    
    print("Current thresholds:")
    for metric, threshold in thresholds.items():
        print(f"  {metric}: {threshold}%")
    
    print("\n1. 🔥 CPU threshold")
    print("2. 💾 Memory threshold")
    print("3. 💿 Disk threshold")
    print("4. 🔙 Back")
    
    choice = input("\n🎯 Select threshold to modify (1-4): ").strip()
    
    try:
        if choice == '1':
            new_value = int(input(f"🔥 New CPU threshold [current: {thresholds['cpu']}%]: "))
            thresholds['cpu'] = new_value
            print("✅ CPU threshold updated")
        elif choice == '2':
            new_value = int(input(f"💾 New Memory threshold [current: {thresholds['memory']}%]: "))
            thresholds['memory'] = new_value
            print("✅ Memory threshold updated")
        elif choice == '3':
            new_value = int(input(f"💿 New Disk threshold [current: {thresholds['disk']}%]: "))
            thresholds['disk'] = new_value
            print("✅ Disk threshold updated")
        elif choice == '4':
            return
    except ValueError:
        print("❌ Invalid threshold value")

def network_menu(network_scanner):
    """Network scanning submenu"""
    print("\n🔍 Network Scanning")
    print("-" * 20)
    
    print("1. 🌐 Network Discovery")
    print("2. 🔍 Port Scan")
    print("3. 📊 Network Analysis")
    print("4. 🔙 Back")
    
    choice = input("\n🎯 Select option (1-4): ").strip()
    
    if choice == '1':
        network = input("🌐 Network to scan [192.168.1.0/24]: ").strip() or "192.168.1.0/24"
        print(f"🔍 Scanning network {network}...")
        
        hosts = network_scanner.scan_network(network)
        if hosts:
            print(f"\n🌐 Discovered Hosts ({len(hosts)} total):")
            for host in hosts:
                print(f"  🖥️  {host['ip']} - {host['hostname']} ({host['status']})")
        else:
            print("📝 No hosts discovered")
    
    elif choice == '2':
        host = input("🎯 Host to scan: ").strip()
        if host:
            ports_input = input("🔌 Ports (comma-separated) [common ports]: ").strip()
            
            ports = None
            if ports_input:
                try:
                    ports = [int(p.strip()) for p in ports_input.split(',')]
                except ValueError:
                    print("❌ Invalid port format")
                    return
            
            print(f"🔍 Scanning {host}...")
            results = network_scanner.port_scan(host, ports)
            
            if 'error' in results:
                print(f"❌ Scan failed: {results['error']}")
            else:
                print(f"\n🔍 Port Scan Results for {results['host']}:")
                for port, info in results['ports'].items():
                    status = "🟢 Open" if info['open'] else "🔴 Closed"
                    print(f"  Port {port}: {status} ({info['service']})")
    
    elif choice == '3':
        print("📊 Network analysis not implemented in this demo")
    
    elif choice == '4':
        return

if __name__ == '__main__':
    print("☁️  Cloud Integrations Module")
    print("This module is designed to be integrated into NexusController Secure")