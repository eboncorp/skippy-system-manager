#!/usr/bin/env python3
"""
Ebonhawk Agent Auto-Updater
Checks for updates and automatically updates the maintenance agent
"""

import os
import sys
import json
import hashlib
import subprocess
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict

class EbonhawkAgentUpdater:
    """Auto-updater for Ebonhawk Maintenance Agent"""
    
    def __init__(self):
        self.agent_path = Path.home() / "Scripts" / "ebonhawk_maintenance_agent.py"
        self.config_path = Path.home() / ".ebonhawk-maintenance" / "updater_config.json"
        self.github_repo = "eboncorp/ebonhawk-agent"  # Update with actual repo
        self.update_check_interval = 86400  # 24 hours
        
        # Create config directory
        self.config_path.parent.mkdir(exist_ok=True)
        
        # Load or create config
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load updater configuration"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        else:
            config = {
                "last_check": None,
                "current_version": self.get_file_hash(),
                "auto_update": True,
                "update_channel": "stable",  # stable, beta, dev
                "github_token": None,
                "update_sources": [
                    f"https://raw.githubusercontent.com/{self.github_repo}/main/ebonhawk_maintenance_agent.py",
                    "https://backup-server.local/agents/ebonhawk_maintenance_agent.py"
                ]
            }
            self.save_config(config)
            return config
    
    def save_config(self, config: Dict = None):
        """Save updater configuration"""
        if config:
            self.config = config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)
    
    def get_file_hash(self, file_path: Path = None) -> str:
        """Get SHA256 hash of a file"""
        if file_path is None:
            file_path = self.agent_path
        
        if not file_path.exists():
            return ""
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def should_check_update(self) -> bool:
        """Check if it's time to check for updates"""
        if not self.config.get("auto_update"):
            return False
        
        last_check = self.config.get("last_check")
        if not last_check:
            return True
        
        last_check_time = datetime.fromisoformat(last_check)
        if datetime.now() - last_check_time > timedelta(seconds=self.update_check_interval):
            return True
        
        return False
    
    def fetch_remote_version(self) -> Optional[str]:
        """Fetch the remote version of the agent"""
        for source in self.config.get("update_sources", []):
            try:
                headers = {}
                if self.config.get("github_token") and "github" in source:
                    headers["Authorization"] = f"token {self.config['github_token']}"
                
                response = requests.get(source, headers=headers, timeout=10)
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                print(f"Failed to fetch from {source}: {e}")
                continue
        
        return None
    
    def check_for_updates(self) -> bool:
        """Check if updates are available"""
        print("Checking for updates...")
        
        remote_content = self.fetch_remote_version()
        if not remote_content:
            print("Could not fetch remote version")
            return False
        
        # Calculate hash of remote content
        remote_hash = hashlib.sha256(remote_content.encode()).hexdigest()
        current_hash = self.get_file_hash()
        
        # Update last check time
        self.config["last_check"] = datetime.now().isoformat()
        self.save_config()
        
        if remote_hash != current_hash:
            print(f"Update available!")
            print(f"  Current version: {current_hash[:8]}...")
            print(f"  Remote version:  {remote_hash[:8]}...")
            return True
        else:
            print("Agent is up to date")
            return False
    
    def backup_current_version(self):
        """Backup current agent before updating"""
        if not self.agent_path.exists():
            return
        
        backup_dir = Path.home() / ".ebonhawk-maintenance" / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"ebonhawk_maintenance_agent_{timestamp}.py"
        
        subprocess.run(["cp", str(self.agent_path), str(backup_path)], check=True)
        print(f"Backed up current version to: {backup_path}")
        
        # Keep only last 5 backups
        backups = sorted(backup_dir.glob("ebonhawk_maintenance_agent_*.py"))
        if len(backups) > 5:
            for old_backup in backups[:-5]:
                old_backup.unlink()
    
    def update_agent(self) -> bool:
        """Update the agent to the latest version"""
        remote_content = self.fetch_remote_version()
        if not remote_content:
            print("Failed to fetch update")
            return False
        
        try:
            # Backup current version
            self.backup_current_version()
            
            # Write new version
            with open(self.agent_path, 'w') as f:
                f.write(remote_content)
            
            # Make executable
            os.chmod(self.agent_path, 0o755)
            
            # Update config with new version hash
            self.config["current_version"] = self.get_file_hash()
            self.config["last_update"] = datetime.now().isoformat()
            self.save_config()
            
            print("Successfully updated agent!")
            
            # Restart service if running
            self.restart_service()
            
            return True
            
        except Exception as e:
            print(f"Update failed: {e}")
            return False
    
    def restart_service(self):
        """Restart the maintenance agent service"""
        try:
            # Check if service is running
            result = subprocess.run(
                ["systemctl", "is-active", "ebonhawk-maintenance"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("Restarting ebonhawk-maintenance service...")
                subprocess.run(["sudo", "systemctl", "restart", "ebonhawk-maintenance"], check=True)
                print("Service restarted")
        except:
            pass  # Service might not be installed
    
    def run(self, force: bool = False):
        """Run the updater"""
        if force or self.should_check_update():
            if self.check_for_updates():
                if self.config.get("auto_update") or force:
                    self.update_agent()
                else:
                    print("Auto-update disabled. Run with --force to update")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ebonhawk Agent Auto-Updater')
    parser.add_argument('--check', action='store_true', help='Check for updates')
    parser.add_argument('--force', action='store_true', help='Force update')
    parser.add_argument('--disable', action='store_true', help='Disable auto-updates')
    parser.add_argument('--enable', action='store_true', help='Enable auto-updates')
    parser.add_argument('--status', action='store_true', help='Show update status')
    
    args = parser.parse_args()
    
    updater = EbonhawkAgentUpdater()
    
    if args.disable:
        updater.config["auto_update"] = False
        updater.save_config()
        print("Auto-updates disabled")
    
    elif args.enable:
        updater.config["auto_update"] = True
        updater.save_config()
        print("Auto-updates enabled")
    
    elif args.status:
        print("Ebonhawk Agent Updater Status:")
        print(f"  Auto-update: {'Enabled' if updater.config.get('auto_update') else 'Disabled'}")
        print(f"  Last check: {updater.config.get('last_check', 'Never')}")
        print(f"  Last update: {updater.config.get('last_update', 'Never')}")
        print(f"  Current version: {updater.config.get('current_version', 'Unknown')[:8]}...")
    
    elif args.check:
        updater.check_for_updates()
    
    elif args.force:
        updater.run(force=True)
    
    else:
        updater.run()

if __name__ == "__main__":
    main()