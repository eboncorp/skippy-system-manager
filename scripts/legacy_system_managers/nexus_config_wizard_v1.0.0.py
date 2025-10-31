#!/usr/bin/env python3
"""
NexusController Secure - Interactive Configuration Wizard
Gathers user preferences for customization
"""

import json
import os
from pathlib import Path
from datetime import datetime

class ConfigurationWizard:
    def __init__(self):
        self.config = {
            'wizard_version': '1.0',
            'completed_at': None,
            'github': {},
            'cloud': {},
            'infrastructure': {},
            'security': {},
            'workflow': {},
            'features': {}
        }
        
        self.config_file = Path.home() / '.nexus' / 'user_preferences.json'
        Path.home().mkdir(exist_ok=True)
        (Path.home() / '.nexus').mkdir(mode=0o700, exist_ok=True)
    
    def display_banner(self):
        print("\n" + "="*60)
        print("🔐 NexusController Secure - Configuration Wizard")
        print("="*60)
        print("This wizard will gather your preferences to customize")
        print("NexusController Secure for your specific environment.")
        print("\n💡 You can skip any question by pressing Enter")
        print("💡 Your answers will be saved securely for customization")
        print("="*60)
    
    def ask_question(self, question, options=None, allow_multiple=False, default=None):
        """Ask a question with optional multiple choice"""
        print(f"\n📋 {question}")
        
        if options:
            for i, option in enumerate(options, 1):
                print(f"  {i}. {option}")
            
            if allow_multiple:
                print("  💡 Enter multiple numbers separated by commas (e.g., 1,3,5)")
            
            if default:
                print(f"  💡 Default: {default}")
        
        response = input("\n🎯 Your answer: ").strip()
        
        if not response and default:
            return default
        
        if options and response:
            try:
                if allow_multiple:
                    # Handle multiple selections
                    selections = [int(x.strip()) - 1 for x in response.split(',')]
                    return [options[i] for i in selections if 0 <= i < len(options)]
                else:
                    # Single selection
                    selection = int(response) - 1
                    if 0 <= selection < len(options):
                        return options[selection]
                    else:
                        print("❌ Invalid selection, skipping...")
                        return None
            except ValueError:
                if not allow_multiple:
                    # If not a number, treat as text answer
                    return response
                else:
                    print("❌ Invalid format, skipping...")
                    return None
        
        return response if response else None
    
    def github_section(self):
        print("\n🐙 GitHub Integration Configuration")
        print("-" * 40)
        
        self.config['github']['username'] = self.ask_question(
            "What's your primary GitHub username?",
            default="Skip if you don't use GitHub"
        )
        
        if self.config['github']['username'] and self.config['github']['username'] != "Skip if you don't use GitHub":
            self.config['github']['has_work_account'] = self.ask_question(
                "Do you have work/organization GitHub accounts?",
                ["Yes", "No"],
                default="No"
            ) == "Yes"
            
            if self.config['github']['has_work_account']:
                self.config['github']['work_accounts'] = self.ask_question(
                    "List your work/org GitHub usernames (comma-separated):"
                )
            
            self.config['github']['active_repos'] = self.ask_question(
                "What repositories do you work with most? (comma-separated)"
            )
            
            self.config['github']['backup_configs'] = self.ask_question(
                "Backup NexusController configs to private GitHub repo?",
                ["Yes", "No"],
                default="Yes"
            ) == "Yes"
            
            self.config['github']['auto_ssh_keys'] = self.ask_question(
                "Automatically upload SSH keys to GitHub?",
                ["Yes", "No"],
                default="Yes"
            ) == "Yes"
    
    def cloud_section(self):
        print("\n☁️  Cloud Services Configuration")
        print("-" * 35)
        
        cloud_providers = [
            "AWS (Amazon Web Services)",
            "Azure (Microsoft)",
            "GCP (Google Cloud Platform)",
            "DigitalOcean",
            "Linode",
            "Vultr",
            "Hetzner",
            "None"
        ]
        
        self.config['cloud']['providers'] = self.ask_question(
            "Which cloud providers do you use?",
            cloud_providers,
            allow_multiple=True
        )
        
        if self.config['cloud']['providers'] and "None" not in str(self.config['cloud']['providers']):
            self.config['cloud']['primary_provider'] = self.ask_question(
                "Which is your primary cloud provider?",
                self.config['cloud']['providers'] if isinstance(self.config['cloud']['providers'], list) else [self.config['cloud']['providers']]
            )
            
            self.config['cloud']['instance_count'] = self.ask_question(
                "Approximately how many cloud instances do you manage?",
                ["1-5", "6-20", "21-50", "50+"],
                default="1-5"
            )
            
            self.config['cloud']['cost_monitoring'] = self.ask_question(
                "Do you want cloud cost monitoring and alerts?",
                ["Yes", "No"],
                default="Yes"
            ) == "Yes"
        
        container_tech = [
            "Docker",
            "Kubernetes",
            "Docker Compose",
            "Podman",
            "LXC/LXD",
            "None"
        ]
        
        self.config['cloud']['containers'] = self.ask_question(
            "What container technologies do you use?",
            container_tech,
            allow_multiple=True
        )
        
        vpn_options = [
            "WireGuard",
            "OpenVPN",
            "Commercial VPN (ExpressVPN, NordVPN, etc.)",
            "Corporate VPN",
            "None"
        ]
        
        self.config['cloud']['vpn_preference'] = self.ask_question(
            "VPN preference for secure connections?",
            vpn_options
        )
    
    def infrastructure_section(self):
        print("\n🌐 Infrastructure Configuration")
        print("-" * 30)
        
        network_setup = [
            "Home lab (single location)",
            "Office network",
            "Multiple locations",
            "Mixed home/office",
            "Cloud-only"
        ]
        
        self.config['infrastructure']['network_type'] = self.ask_question(
            "Describe your network setup:",
            network_setup
        )
        
        self.config['infrastructure']['other_servers'] = self.ask_question(
            "List other servers/devices you manage (besides Ebon):"
        )
        
        database_types = [
            "PostgreSQL",
            "MySQL/MariaDB",
            "Redis",
            "MongoDB",
            "SQLite",
            "InfluxDB",
            "None"
        ]
        
        self.config['infrastructure']['databases'] = self.ask_question(
            "What databases do you use?",
            database_types,
            allow_multiple=True
        )
        
        dev_stack = [
            "Python",
            "JavaScript/Node.js",
            "Go",
            "Rust",
            "Java",
            "C/C++",
            "PHP",
            "Ruby",
            "Other"
        ]
        
        self.config['infrastructure']['development_stack'] = self.ask_question(
            "Primary development languages/frameworks?",
            dev_stack,
            allow_multiple=True
        )
        
        if self.config['infrastructure']['development_stack'] and "Other" in str(self.config['infrastructure']['development_stack']):
            self.config['infrastructure']['other_languages'] = self.ask_question(
                "Specify other languages/frameworks:"
            )
    
    def security_section(self):
        print("\n🔐 Security Configuration")
        print("-" * 25)
        
        security_level = [
            "Maximum Security (paranoid mode - all features enabled)",
            "High Security (balanced security with some convenience)",
            "Moderate Security (convenience prioritized)",
            "Custom (I'll choose specific features)"
        ]
        
        self.config['security']['level'] = self.ask_question(
            "Security preference level:",
            security_level,
            default="High Security (balanced security with some convenience)"
        )
        
        if "Custom" in str(self.config['security']['level']):
            security_features = [
                "YubiKey required for all operations",
                "VPN required for remote connections",
                "Port knocking for SSH",
                "Encrypted configuration backups",
                "Real-time intrusion detection",
                "Comprehensive audit logging",
                "Automatic security updates",
                "Network monitoring and scanning"
            ]
            
            self.config['security']['custom_features'] = self.ask_question(
                "Which security features do you want?",
                security_features,
                allow_multiple=True
            )
        
        backup_strategy = [
            "Cloud backup (GitHub/AWS S3/etc.)",
            "Local encrypted backup",
            "Both cloud and local",
            "Manual backup only"
        ]
        
        self.config['security']['backup_strategy'] = self.ask_question(
            "Backup strategy preference:",
            backup_strategy,
            default="Both cloud and local"
        )
        
        monitoring_level = [
            "Minimal (basic health checks)",
            "Standard (health + alerts)",
            "Comprehensive (full monitoring + dashboards)",
            "Enterprise (everything + custom metrics)"
        ]
        
        self.config['security']['monitoring_level'] = self.ask_question(
            "Monitoring and alerting level:",
            monitoring_level,
            default="Standard (health + alerts)"
        )
    
    def workflow_section(self):
        print("\n🛠️  Workflow Integration")
        print("-" * 25)
        
        editors = [
            "VS Code",
            "IntelliJ IDEA/PyCharm",
            "Vim/Neovim",
            "Emacs",
            "Sublime Text",
            "Atom",
            "Other"
        ]
        
        self.config['workflow']['ide'] = self.ask_question(
            "Primary IDE/Editor:",
            editors,
            allow_multiple=True
        )
        
        shells = [
            "Bash",
            "Zsh (with Oh My Zsh)",
            "Fish",
            "PowerShell",
            "Other"
        ]
        
        self.config['workflow']['shell'] = self.ask_question(
            "Terminal shell preference:",
            shells
        )
        
        operating_systems = [
            "Ubuntu/Debian",
            "CentOS/RHEL/Fedora",
            "Arch Linux",
            "macOS",
            "Windows (WSL)",
            "Multiple Linux distros",
            "Other"
        ]
        
        self.config['workflow']['operating_systems'] = self.ask_question(
            "Operating systems you work with:",
            operating_systems,
            allow_multiple=True
        )
        
        self.config['workflow']['automation_preferences'] = self.ask_question(
            "What automation would be most helpful? (describe in your own words)"
        )
        
        terminal_multiplexer = [
            "tmux",
            "screen",
            "Terminal tabs/windows only",
            "Don't use multiplexers"
        ]
        
        self.config['workflow']['terminal_multiplexer'] = self.ask_question(
            "Terminal multiplexer preference:",
            terminal_multiplexer
        )
    
    def features_section(self):
        print("\n💡 Additional Features")
        print("-" * 20)
        
        interface_preferences = [
            "CLI only (command line interface)",
            "CLI + Web dashboard",
            "CLI + Mobile notifications",
            "All interfaces (CLI + Web + Mobile + API)"
        ]
        
        self.config['features']['interface_preference'] = self.ask_question(
            "Interface preference:",
            interface_preferences,
            default="CLI + Web dashboard"
        )
        
        integration_services = [
            "Slack notifications",
            "Discord notifications",
            "Email alerts",
            "SMS alerts",
            "Webhook integrations",
            "REST API access",
            "None"
        ]
        
        self.config['features']['notification_integrations'] = self.ask_question(
            "Notification/integration services:",
            integration_services,
            allow_multiple=True
        )
        
        automation_features = [
            "Infrastructure as Code (Terraform/Ansible)",
            "CI/CD Pipeline automation",
            "Automated testing and deployment",
            "Log aggregation and analysis",
            "Performance monitoring and optimization",
            "Cost optimization recommendations",
            "Security vulnerability scanning",
            "Backup verification and testing"
        ]
        
        self.config['features']['desired_automation'] = self.ask_question(
            "Which automation features interest you most?",
            automation_features,
            allow_multiple=True
        )
        
        priority_features = [
            "Performance and speed",
            "Security and compliance",
            "Ease of use",
            "Comprehensive monitoring",
            "Integration capabilities",
            "Scalability",
            "Cost effectiveness"
        ]
        
        self.config['features']['priorities'] = self.ask_question(
            "Top 3 priorities for NexusController:",
            priority_features,
            allow_multiple=True
        )
        
        self.config['features']['additional_comments'] = self.ask_question(
            "Any additional features, concerns, or specific requirements?"
        )
    
    def summary_section(self):
        print("\n📋 Configuration Summary")
        print("=" * 30)
        
        # Display a summary of key choices
        if self.config['github'].get('username'):
            print(f"🐙 GitHub: {self.config['github']['username']}")
        
        if self.config['cloud'].get('providers'):
            providers = self.config['cloud']['providers']
            if isinstance(providers, list):
                print(f"☁️  Cloud: {', '.join(providers[:2])}{'...' if len(providers) > 2 else ''}")
            else:
                print(f"☁️  Cloud: {providers}")
        
        if self.config['security'].get('level'):
            print(f"🔐 Security: {self.config['security']['level']}")
        
        if self.config['workflow'].get('ide'):
            ide = self.config['workflow']['ide']
            if isinstance(ide, list):
                print(f"🛠️  IDE: {', '.join(ide[:2])}{'...' if len(ide) > 2 else ''}")
            else:
                print(f"🛠️  IDE: {ide}")
        
        print(f"\n💾 Configuration will be saved to:")
        print(f"   {self.config_file}")
        
        confirm = self.ask_question(
            "Save this configuration?",
            ["Yes", "No", "Restart wizard"],
            default="Yes"
        )
        
        return confirm
    
    def save_config(self):
        """Save configuration to file"""
        self.config['completed_at'] = datetime.now().isoformat()
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            os.chmod(self.config_file, 0o600)  # Secure permissions
            
            print(f"\n✅ Configuration saved successfully!")
            print(f"📁 Location: {self.config_file}")
            print(f"\n📧 Share this file path with Claude to customize NexusController:")
            print(f"   {self.config_file}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error saving configuration: {e}")
            return False
    
    def run_wizard(self):
        """Run the complete configuration wizard"""
        self.display_banner()
        
        while True:
            try:
                # Run each section
                self.github_section()
                self.cloud_section()
                self.infrastructure_section()
                self.security_section()
                self.workflow_section()
                self.features_section()
                
                # Show summary and confirm
                result = self.summary_section()
                
                if result == "Yes":
                    if self.save_config():
                        break
                    else:
                        print("\n🔄 Let's try saving again...")
                        continue
                elif result == "No":
                    print("\n👋 Configuration wizard cancelled.")
                    print("💡 Run the wizard again anytime: python3 nexus_config_wizard.py")
                    break
                elif result == "Restart wizard":
                    print("\n🔄 Restarting configuration wizard...\n")
                    self.config = {
                        'wizard_version': '1.0',
                        'completed_at': None,
                        'github': {},
                        'cloud': {},
                        'infrastructure': {},
                        'security': {},
                        'workflow': {},
                        'features': {}
                    }
                    continue
                else:
                    # Default to save
                    if self.save_config():
                        break
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️  Wizard interrupted.")
                save_partial = input("💾 Save partial configuration? (y/N): ").lower() == 'y'
                if save_partial:
                    self.save_config()
                else:
                    print("👋 Configuration not saved.")
                break
            
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("🔄 Restarting wizard...")
                continue
        
        print("\n🎉 Thank you for using the NexusController Configuration Wizard!")
        print("🔧 Your preferences will be used to customize the system.")

if __name__ == '__main__':
    wizard = ConfigurationWizard()
    wizard.run_wizard()