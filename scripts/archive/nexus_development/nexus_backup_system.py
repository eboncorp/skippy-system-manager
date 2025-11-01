#\!/usr/bin/env python3
"""
NexusController Backup System
Automated backup and disaster recovery for media server
"""
import os
import subprocess
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/home/ebon/nexus_backup.log"),
        logging.StreamHandler()
    ]
)

class NexusBackupSystem:
    def __init__(self):
        self.backup_base = Path("/home/ebon/backups")
        self.backup_base.mkdir(exist_ok=True)
        
        # Backup configuration
        self.backup_targets = {
            "docker_volumes": {
                "jellyfin_config": "/var/lib/docker/volumes/jellyfin_config/_data",
                "jellyfin_cache": "/var/lib/docker/volumes/jellyfin_cache/_data", 
                "homeassistant_config": "/var/lib/docker/volumes/homeassistant_config/_data",
                "nodered_data": "/var/lib/docker/volumes/nodered_data/_data",
                "mosquitto_config": "/var/lib/docker/volumes/mosquitto_config/_data",
                "mosquitto_data": "/var/lib/docker/volumes/mosquitto_data/_data"
            },
            "system_configs": {
                "nexus_controller": "/home/ebon",
                "docker_compose": "/home/ebon"
            }
        }
        
        # Retention policy
        self.retention_days = 30
        self.max_backups = 10

    def create_backup(self, backup_type="full"):
        """Create a new backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        logging.info(f"Starting {backup_type} backup to {backup_dir}")
        
        backup_manifest = {
            "timestamp": timestamp,
            "type": backup_type,
            "created": datetime.now().isoformat(),
            "status": "in_progress",
            "files": {}
        }
        
        try:
            # Backup Docker volumes
            docker_backup_dir = backup_dir / "docker_volumes"
            docker_backup_dir.mkdir(exist_ok=True)
            
            for volume_name, source_path in self.backup_targets["docker_volumes"].items():
                if os.path.exists(source_path):
                    dest_path = docker_backup_dir / volume_name
                    logging.info(f"Backing up {volume_name} from {source_path}")
                    
                    # Use tar for efficient backup
                    tar_file = dest_path.with_suffix(".tar.gz")
                    result = subprocess.run([
                        "sudo", "tar", "-czf", str(tar_file), "-C", str(Path(source_path).parent), 
                        Path(source_path).name
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        backup_manifest["files"][volume_name] = {
                            "source": source_path,
                            "backup": str(tar_file),
                            "size": os.path.getsize(tar_file),
                            "status": "success"
                        }
                    else:
                        logging.error(f"Failed to backup {volume_name}: {result.stderr}")
                        backup_manifest["files"][volume_name] = {
                            "source": source_path,
                            "status": "failed",
                            "error": result.stderr
                        }
                else:
                    logging.warning(f"Source path not found: {source_path}")
            
            # Backup system configurations
            config_backup_dir = backup_dir / "configs"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Backup NexusController files
            nexus_files = [
                "nexus_media_server.py", "enhanced_simple_server.py", "simple_nexus_server.py",
                "media_service_monitor.py", "nexus_backup_system.py", "config-media.yaml",
                "docker-compose.media.yml", "Dockerfile", "requirements.txt"
            ]
            
            for file_name in nexus_files:
                source_file = Path("/home/ebon") / file_name
                if source_file.exists():
                    dest_file = config_backup_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    backup_manifest["files"][file_name] = {
                        "source": str(source_file),
                        "backup": str(dest_file),
                        "size": os.path.getsize(dest_file),
                        "status": "success"
                    }
            
            # Create backup manifest
            backup_manifest["status"] = "completed"
            backup_manifest["completed"] = datetime.now().isoformat()
            backup_manifest["total_files"] = len(backup_manifest["files"])
            backup_manifest["successful_files"] = len([f for f in backup_manifest["files"].values() if f.get("status") == "success"])
            
            with open(backup_dir / "manifest.json", "w") as f:
                json.dump(backup_manifest, f, indent=2)
            
            logging.info(f"Backup completed successfully: {backup_manifest[successful_files]}/{backup_manifest[total_files]} files")
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            return True, backup_dir
            
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            backup_manifest["status"] = "failed"
            backup_manifest["error"] = str(e)
            
            with open(backup_dir / "manifest.json", "w") as f:
                json.dump(backup_manifest, f, indent=2)
            
            return False, str(e)

    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        backup_dirs = []
        
        for item in self.backup_base.iterdir():
            if item.is_dir() and item.name.startswith("backup_"):
                backup_dirs.append(item)
        
        # Sort by modification time (newest first)
        backup_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove excess backups
        if len(backup_dirs) > self.max_backups:
            for old_backup in backup_dirs[self.max_backups:]:
                logging.info(f"Removing old backup: {old_backup}")
                shutil.rmtree(old_backup)
        
        # Remove backups older than retention period
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        for backup_dir in backup_dirs:
            if datetime.fromtimestamp(backup_dir.stat().st_mtime) < cutoff_date:
                logging.info(f"Removing expired backup: {backup_dir}")
                shutil.rmtree(backup_dir)

    def list_backups(self):
        """List available backups"""
        backups = []
        
        for item in self.backup_base.iterdir():
            if item.is_dir() and item.name.startswith("backup_"):
                manifest_file = item / "manifest.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                    backups.append({
                        "path": str(item),
                        "name": item.name,
                        "timestamp": manifest.get("created", "unknown"),
                        "status": manifest.get("status", "unknown"),
                        "files": manifest.get("total_files", 0),
                        "successful": manifest.get("successful_files", 0)
                    })
        
        return sorted(backups, key=lambda x: x["timestamp"], reverse=True)

    def get_backup_status(self):
        """Get current backup system status"""
        backups = self.list_backups()
        
        return {
            "backup_location": str(self.backup_base),
            "total_backups": len(backups),
            "latest_backup": backups[0] if backups else None,
            "retention_days": self.retention_days,
            "max_backups": self.max_backups,
            "disk_usage": self.get_disk_usage()
        }

    def get_disk_usage(self):
        """Get disk usage for backup directory"""
        if self.backup_base.exists():
            total_size = sum(f.stat().st_size for f in self.backup_base.rglob("*") if f.is_file())
            return {
                "bytes": total_size,
                "human": self.format_bytes(total_size)
            }
        return {"bytes": 0, "human": "0 B"}

    def format_bytes(self, bytes):
        """Format bytes to human readable format"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} PB"

def main():
    backup_system = NexusBackupSystem()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            status = backup_system.get_backup_status()
            print(json.dumps(status, indent=2))
        elif sys.argv[1] == "list":
            backups = backup_system.list_backups()
            for backup in backups:
                print(f"{backup[name]}: {backup[status]} - {backup[successful]}/{backup[files]} files - {backup[timestamp]}")
        elif sys.argv[1] == "backup":
            success, result = backup_system.create_backup()
            if success:
                print(f"Backup created successfully: {result}")
            else:
                print(f"Backup failed: {result}")
        else:
            print("Usage: nexus_backup_system.py [status|list|backup]")
    else:
        # Default: create backup
        success, result = backup_system.create_backup()
        if success:
            print(f"Backup created successfully: {result}")
        else:
            print(f"Backup failed: {result}")

if __name__ == "__main__":
    main()
