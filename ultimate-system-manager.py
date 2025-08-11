#!/usr/bin/env python3
"""
Ultimate System Manager v5.0
The complete unified system management platform
Integrates all components: Local management, Web interface, Multi-server, AI maintenance, and Cloud monitoring
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import our components
try:
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    
    # Import all our components
    from advanced_system_manager import AdvancedSystemManager
    from web_system_manager import WebSystemManager
    from multi_server_manager import MultiServerManager
    from ai_maintenance_engine import AIMaintenanceEngine
    from cloud_monitoring_integration import CloudMonitoringIntegration
    
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Component import failed: {e}")
    COMPONENTS_AVAILABLE = False

class UltimateSystemManager:
    """The ultimate unified system management platform"""
    
    def __init__(self):
        self.version = "5.0"
        self.base_path = Path.home() / ".unified-system-manager"
        self.base_path.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Component instances
        self.local_manager = None
        self.web_manager = None
        self.multi_server_manager = None
        self.ai_engine = None
        self.cloud_integration = None
        
        # Runtime state
        self.running = False
        self.components_started = []
        
        self.logger.info(f"Ultimate System Manager v{self.version} initialized")
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_path = self.base_path / "logs"
        log_path.mkdir(exist_ok=True)
        
        # Create main log file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path / "ultimate-manager.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("UltimateSystemManager")
    
    def initialize_components(self) -> bool:
        """Initialize all system components"""
        if not COMPONENTS_AVAILABLE:
            self.logger.error("Required components not available")
            return False
        
        try:
            print("🔧 Initializing Ultimate System Manager components...")
            
            # Initialize Advanced System Manager (local)
            print("  📱 Initializing Advanced System Manager...")
            self.local_manager = AdvancedSystemManager()
            
            # Initialize Web System Manager
            print("  🌐 Initializing Web System Manager...")
            self.web_manager = WebSystemManager()
            
            # Initialize Multi-Server Manager
            print("  🖥️ Initializing Multi-Server Manager...")
            self.multi_server_manager = MultiServerManager()
            
            # Initialize AI Maintenance Engine
            print("  🤖 Initializing AI Maintenance Engine...")
            self.ai_engine = AIMaintenanceEngine()
            
            # Initialize Cloud Monitoring Integration
            print("  ☁️ Initializing Cloud Monitoring Integration...")
            self.cloud_integration = CloudMonitoringIntegration()
            
            print("✅ All components initialized successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            print(f"❌ Component initialization failed: {e}")
            return False
    
    def start_all_services(self):
        """Start all system services"""
        if not self.initialize_components():
            return False
        
        print("\n🚀 Starting Ultimate System Manager services...")
        
        try:
            # Start local manager services
            if self.local_manager:
                print("  🔄 Starting local system monitoring...")
                self.local_manager.start_monitoring()
                self.components_started.append("local_manager")
            
            # Start multi-server monitoring
            if self.multi_server_manager:
                print("  🖥️ Starting multi-server monitoring...")
                self.multi_server_manager.start_monitoring()
                self.components_started.append("multi_server")
            
            # Start AI analysis
            if self.ai_engine:
                print("  🤖 Starting AI predictive maintenance...")
                self.ai_engine.start_analysis()
                self.components_started.append("ai_engine")
            
            # Start cloud monitoring
            if self.cloud_integration:
                print("  ☁️ Starting cloud monitoring integration...")
                self.cloud_integration.start_monitoring()
                self.components_started.append("cloud_integration")
            
            # Start web interface (this will block)
            if self.web_manager:
                print("  🌐 Starting web interface...")
                print(f"     💻 Web dashboard: http://localhost:8080")
                print(f"     🔐 Default login: admin / admin123")
                print(f"     📊 Real-time monitoring enabled")
                print(f"     🤖 AI-powered insights active")
                print(f"     🖥️ Multi-server management ready")
                print(f"     ☁️ Cloud integration enabled")
                
                self.running = True
                self.components_started.append("web_manager")
                
                # This will block until web server stops
                return self.web_manager.run()
            
        except Exception as e:
            self.logger.error(f"Failed to start services: {e}")
            print(f"❌ Service startup failed: {e}")
            return False
    
    def stop_all_services(self):
        """Stop all system services gracefully"""
        print("\n🛑 Stopping Ultimate System Manager services...")
        
        self.running = False
        
        # Stop each component that was started
        if "web_manager" in self.components_started and self.web_manager:
            print("  🌐 Stopping web interface...")
            # Web manager stops when run() exits
        
        if "cloud_integration" in self.components_started and self.cloud_integration:
            print("  ☁️ Stopping cloud monitoring...")
            self.cloud_integration.stop_monitoring()
        
        if "ai_engine" in self.components_started and self.ai_engine:
            print("  🤖 Stopping AI analysis...")
            self.ai_engine.stop_analysis()
        
        if "multi_server" in self.components_started and self.multi_server_manager:
            print("  🖥️ Stopping multi-server monitoring...")
            self.multi_server_manager.stop_monitoring()
        
        if "local_manager" in self.components_started and self.local_manager:
            print("  📱 Stopping local system monitoring...")
            self.local_manager.stop_monitoring()
        
        print("✅ All services stopped successfully!")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'version': self.version,
            'running': self.running,
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Get status from each component
        if self.local_manager:
            try:
                local_stats = self.local_manager.get_comprehensive_status()
                status['components']['local_manager'] = {
                    'status': 'running' if 'local_manager' in self.components_started else 'stopped',
                    'stats': local_stats
                }
            except Exception as e:
                status['components']['local_manager'] = {'status': 'error', 'error': str(e)}
        
        if self.multi_server_manager:
            try:
                server_stats = self.multi_server_manager.get_statistics()
                status['components']['multi_server'] = {
                    'status': 'running' if 'multi_server' in self.components_started else 'stopped',
                    'stats': server_stats
                }
            except Exception as e:
                status['components']['multi_server'] = {'status': 'error', 'error': str(e)}
        
        if self.ai_engine:
            try:
                ai_stats = self.ai_engine.get_analysis_summary()
                status['components']['ai_engine'] = {
                    'status': 'running' if 'ai_engine' in self.components_started else 'stopped',
                    'stats': ai_stats
                }
            except Exception as e:
                status['components']['ai_engine'] = {'status': 'error', 'error': str(e)}
        
        if self.cloud_integration:
            try:
                cloud_stats = self.cloud_integration.get_monitoring_summary()
                status['components']['cloud_integration'] = {
                    'status': 'running' if 'cloud_integration' in self.components_started else 'stopped',
                    'stats': cloud_stats
                }
            except Exception as e:
                status['components']['cloud_integration'] = {'status': 'error', 'error': str(e)}
        
        return status
    
    def run_cli_mode(self):
        """Run in CLI mode with interactive menu"""
        while True:
            self.show_main_menu()
            choice = input("\nSelect option: ").strip()
            
            if choice == '1':
                self.start_all_services()
                break
            elif choice == '2':
                self.show_system_status()
            elif choice == '3':
                self.run_component_test()
            elif choice == '4':
                self.show_configuration()
            elif choice == '5':
                self.show_help()
            elif choice == '0':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please try again.")
    
    def show_main_menu(self):
        """Show the main CLI menu"""
        print("\n" + "="*60)
        print(f"🚀 Ultimate System Manager v{self.version}")
        print("   The Complete Unified System Management Platform")
        print("="*60)
        print("\nMain Menu:")
        print("  1. 🌐 Start All Services (Web + Monitoring + AI + Cloud)")
        print("  2. 📊 Show System Status")
        print("  3. 🧪 Run Component Tests")
        print("  4. ⚙️ Show Configuration")
        print("  5. ❓ Help & Documentation")
        print("  0. 🚪 Exit")
        print("\nComponents:")
        print("  📱 Advanced System Manager (Local monitoring & cleanup)")
        print("  🌐 Web System Manager (Remote web interface)")
        print("  🖥️ Multi-Server Manager (SSH-based server management)")
        print("  🤖 AI Maintenance Engine (Predictive maintenance)")
        print("  ☁️ Cloud Monitoring Integration (AWS/GCP/Azure)")
    
    def show_system_status(self):
        """Show detailed system status"""
        print("\n📊 System Status Report")
        print("-" * 40)
        
        status = self.get_system_status()
        
        print(f"Version: {status['version']}")
        print(f"Running: {'Yes' if status['running'] else 'No'}")
        print(f"Timestamp: {status['timestamp']}")
        
        print("\nComponent Status:")
        for component, info in status['components'].items():
            status_icon = "✅" if info['status'] == 'running' else "❌" if info['status'] == 'error' else "⏸️"
            print(f"  {status_icon} {component}: {info['status']}")
            
            if 'stats' in info and info['stats']:
                # Show key statistics
                stats = info['stats']
                if 'plugins' in stats:
                    print(f"     Plugins: {stats['plugins']['loaded']}")
                if 'servers' in stats:
                    print(f"     Servers: {stats['servers']['total']} ({stats['servers']['online']} online)")
                if 'alerts' in stats:
                    print(f"     Alerts: {stats['alerts']['total_active']} active")
        
        input("\nPress Enter to continue...")
    
    def run_component_test(self):
        """Run tests for all components"""
        print("\n🧪 Running Component Tests")
        print("-" * 30)
        
        if not self.initialize_components():
            return
        
        tests = [
            ("📱 Local Manager", self.test_local_manager),
            ("🖥️ Multi-Server Manager", self.test_multi_server),
            ("🤖 AI Engine", self.test_ai_engine),
            ("☁️ Cloud Integration", self.test_cloud_integration)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                result = test_func()
                print(f"  ✅ {result}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
        
        input("\nPress Enter to continue...")
    
    def test_local_manager(self) -> str:
        """Test local manager component"""
        if not self.local_manager:
            return "Component not initialized"
        
        # Test plugin loading
        plugins = self.local_manager.plugin_manager.get_loaded_plugins()
        return f"Local manager working - {len(plugins)} plugins loaded"
    
    def test_multi_server(self) -> str:
        """Test multi-server manager component"""
        if not self.multi_server_manager:
            return "Component not initialized"
        
        # Test server listing
        servers = self.multi_server_manager.get_all_servers()
        return f"Multi-server manager working - {len(servers)} servers configured"
    
    def test_ai_engine(self) -> str:
        """Test AI engine component"""
        if not self.ai_engine:
            return "Component not initialized"
        
        # Test metric collection
        metrics = self.ai_engine.collect_system_metrics(1)
        return f"AI engine working - collected {len(metrics)} metrics"
    
    def test_cloud_integration(self) -> str:
        """Test cloud integration component"""
        if not self.cloud_integration:
            return "Component not initialized"
        
        # Test configuration
        config = self.cloud_integration.config
        enabled_providers = [p for p, c in config.items() if isinstance(c, dict) and c.get('enabled')]
        return f"Cloud integration working - {len(enabled_providers)} providers configured"
    
    def show_configuration(self):
        """Show system configuration"""
        print("\n⚙️ System Configuration")
        print("-" * 25)
        
        config_files = [
            self.base_path / "config.yaml",
            self.base_path / "web-config.json",
            self.base_path / "cloud-config.json"
        ]
        
        for config_file in config_files:
            print(f"\n📄 {config_file.name}:")
            if config_file.exists():
                print(f"  📍 Location: {config_file}")
                print(f"  📏 Size: {config_file.stat().st_size} bytes")
                print(f"  📅 Modified: {datetime.fromtimestamp(config_file.stat().st_mtime)}")
            else:
                print(f"  ❌ Not found at {config_file}")
        
        print(f"\n📂 Base directory: {self.base_path}")
        print(f"💾 Database files: {len(list(self.base_path.glob('*.db')))}")
        print(f"📋 Log files: {len(list((self.base_path / 'logs').glob('*.log'))) if (self.base_path / 'logs').exists() else 0}")
        
        input("\nPress Enter to continue...")
    
    def show_help(self):
        """Show help and documentation"""
        print("\n❓ Ultimate System Manager Help")
        print("=" * 35)
        
        print("""
🚀 OVERVIEW
The Ultimate System Manager is a comprehensive platform that combines:
- Local system monitoring and cleanup
- Web-based remote management interface  
- Multi-server management via SSH
- AI-powered predictive maintenance
- Cloud monitoring integration (AWS/GCP/Azure)

🌐 WEB INTERFACE
- Access: http://localhost:8080
- Default login: admin / admin123
- Features: Real-time dashboards, remote command execution, server management

🖥️ MULTI-SERVER MANAGEMENT
- SSH-based remote server control
- Parallel command execution
- Server grouping and tagging
- Automated health monitoring

🤖 AI MAINTENANCE
- Predictive system failure analysis
- Anomaly detection in metrics
- Automated maintenance recommendations
- Trend analysis and forecasting

☁️ CLOUD INTEGRATION
- AWS CloudWatch metrics
- Google Cloud Monitoring
- Azure Monitor integration
- Unified alerting across providers

📁 CONFIGURATION
- Base directory: ~/.unified-system-manager/
- Web config: web-config.json
- Cloud config: cloud-config.json
- Main config: config.yaml

🔧 DEPENDENCIES
- Required: Python 3.8+, sqlite3
- Web: Flask, Flask-SocketIO
- SSH: paramiko, fabric
- Cloud: boto3, google-cloud-monitoring, azure-monitor
- Optional: psutil, pyyaml, numpy, pandas

📞 SUPPORT
- Logs: ~/.unified-system-manager/logs/
- Database: ~/.unified-system-manager/*.db
- GitHub: Create issues for bug reports
        """)
        
        input("\nPress Enter to continue...")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n🛑 Received shutdown signal - stopping services...")
    if hasattr(signal_handler, 'manager'):
        signal_handler.manager.stop_all_services()
    sys.exit(0)

def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🌟 Starting Ultimate System Manager v5.0...")
    print("   The Complete Unified System Management Platform")
    
    # Create manager instance
    manager = UltimateSystemManager()
    signal_handler.manager = manager  # Store for signal handler
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['--help', '-h']:
            manager.show_help()
            return
        elif command in ['--version', '-v']:
            print(f"Ultimate System Manager v{manager.version}")
            return
        elif command in ['--start', '-s']:
            success = manager.start_all_services()
            sys.exit(0 if success else 1)
        elif command in ['--status']:
            status = manager.get_system_status()
            print(json.dumps(status, indent=2))
            return
        elif command in ['--test']:
            manager.run_component_test()
            return
    
    # Run in interactive CLI mode
    try:
        manager.run_cli_mode()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        manager.stop_all_services()

if __name__ == "__main__":
    main()