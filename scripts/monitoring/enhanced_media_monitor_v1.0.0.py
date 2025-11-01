#!/usr/bin/env python3
"""
Enhanced Media Service Monitor
Monitors Docker services and music library organization progress
"""
import subprocess
import json
import time
import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

def get_docker_services() -> List[Dict]:
    """Get status of Docker services on the host"""
    try:
        result = subprocess.run([
            "docker", "ps", "--format", 
            "{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.ID}}"
        ], capture_output=True, text=True, check=True)
        
        services = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 4:
                name, status, ports, container_id = parts[:4]
                
                # Skip nexuscontroller itself
                if name == "nexuscontroller-media":
                    continue
                
                # Parse status for health info
                health = "healthy" if "healthy" in status else "unknown"
                uptime_match = re.search(r"Up (.+?)(?:\s\(|$)", status)
                uptime = uptime_match.group(1) if uptime_match else "unknown"
                
                # Parse ports
                port_list = []
                if ports and ports != "":
                    port_matches = re.findall(r"(\d+)->(\d+)", ports)
                    port_list = [f"{match[0]}:{match[1]}" for match in port_matches]
                
                services.append({
                    "name": name,
                    "status": "running" if "Up " in status else "stopped",
                    "container_id": container_id,
                    "uptime": uptime,
                    "ports": port_list,
                    "health": health
                })
        
        return services
    except subprocess.CalledProcessError as e:
        print(f"Error getting docker services: {e}")
        return []

def get_music_organization_status() -> Dict:
    """Get status of music library organization"""
    status = {
        "active": False,
        "process_id": None,
        "files_organized": 0,
        "total_files": 0,
        "percent_complete": 0,
        "current_file": None,
        "estimated_time_remaining": None
    }
    
    # Check if organization script is running
    try:
        result = subprocess.run([
            "ps", "aux"
        ], capture_output=True, text=True, check=True)
        
        for line in result.stdout.split("\n"):
            if "organize_music.py" in line and "grep" not in line:
                parts = line.split()
                if len(parts) > 1:
                    status["active"] = True
                    status["process_id"] = parts[1]
                break
    except:
        pass
    
    # Count files in organized directory
    organized_dir = Path("/mnt/media/music_organized")
    source_dir = Path("/mnt/media/music")
    
    if organized_dir.exists():
        try:
            # Count organized files
            organized_count = sum(1 for _ in organized_dir.rglob("*") if _.is_file())
            status["files_organized"] = organized_count
            
            # Count total music files
            music_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg'}
            total_count = sum(1 for f in source_dir.iterdir() 
                            if f.is_file() and f.suffix.lower() in music_extensions)
            status["total_files"] = total_count
            
            # Calculate percentage
            if total_count > 0:
                status["percent_complete"] = round((organized_count / total_count) * 100, 2)
            
            # Check progress log for current file
            log_file = Path("/tmp/organize_progress.log")
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            # Get last line that shows processing
                            for line in reversed(lines[-10:]):
                                if "Processing:" in line:
                                    status["current_file"] = line.split("Processing:")[-1].strip()
                                    break
                except:
                    pass
            
            # Estimate time remaining (rough estimate)
            if status["active"] and organized_count > 0 and total_count > organized_count:
                # Assume 1-2 files per second processing rate
                remaining_files = total_count - organized_count
                est_seconds = remaining_files / 1.5  # Average rate
                hours = int(est_seconds // 3600)
                minutes = int((est_seconds % 3600) // 60)
                if hours > 0:
                    status["estimated_time_remaining"] = f"{hours}h {minutes}m"
                else:
                    status["estimated_time_remaining"] = f"{minutes}m"
        except Exception as e:
            print(f"Error counting files: {e}")
    
    return status

def get_jellyfin_status() -> Dict:
    """Get Jellyfin service status"""
    status = {
        "running": False,
        "library_scan_active": False,
        "version": "unknown",
        "web_ui_accessible": False
    }
    
    # Check if Jellyfin container is running
    try:
        result = subprocess.run([
            "docker", "ps", "--filter", "name=jellyfin", "--format", "{{.Status}}"
        ], capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            status["running"] = "Up" in result.stdout
            
            # Check if web UI is accessible
            try:
                import requests
                response = requests.get("http://localhost:8096/health", timeout=2)
                status["web_ui_accessible"] = response.status_code == 200
            except:
                # If requests not available, try curl
                try:
                    result = subprocess.run([
                        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
                        "http://localhost:8096/health"
                    ], capture_output=True, text=True, timeout=2)
                    status["web_ui_accessible"] = result.stdout.strip() == "200"
                except:
                    pass
    except:
        pass
    
    return status

def generate_status_report():
    """Generate a comprehensive status report"""
    services = get_docker_services()
    music_status = get_music_organization_status()
    jellyfin_status = get_jellyfin_status()
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "media_server": "10.0.0.29",
        "services": services,
        "services_running": len([s for s in services if s["status"] == "running"]),
        "services_total": len(services),
        "overall_status": "healthy" if all(s["status"] == "running" for s in services) else "degraded",
        "music_organization": music_status,
        "jellyfin": jellyfin_status
    }
    
    return report

def save_status_to_file():
    """Save current status to a file"""
    report = generate_status_report()
    
    # Save to a location accessible by the container
    with open("/home/ebon/media_service_status.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"[{datetime.now():%H:%M:%S}] Status updated:")
    print(f"  Services: {report['services_running']}/{report['services_total']} running")
    
    if report['music_organization']['active']:
        print(f"  Music Org: {report['music_organization']['percent_complete']}% complete " +
              f"({report['music_organization']['files_organized']}/{report['music_organization']['total_files']} files)")
        if report['music_organization']['estimated_time_remaining']:
            print(f"  Est. Time: {report['music_organization']['estimated_time_remaining']}")
    
    if report['jellyfin']['running']:
        print(f"  Jellyfin: Running (Web UI: {'✓' if report['jellyfin']['web_ui_accessible'] else '✗'})")

def monitor_and_restart_organization():
    """Check if organization script needs to be restarted"""
    music_status = get_music_organization_status()
    
    # If organization is not complete but script is not running, restart it
    if (music_status['total_files'] > 0 and 
        music_status['percent_complete'] < 100 and 
        not music_status['active']):
        
        print(f"Music organization incomplete ({music_status['percent_complete']}%), restarting...")
        try:
            subprocess.run([
                "nohup", "python3", "/tmp/organize_music.py", 
                "/mnt/media/music", "/mnt/media/music_organized"
            ], 
            stdout=open("/tmp/organize_progress.log", "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True)
            print("Music organization script restarted")
        except Exception as e:
            print(f"Failed to restart organization: {e}")

if __name__ == "__main__":
    print("Enhanced Media Service Monitor started...")
    print("Monitoring: Docker services, Music organization, Jellyfin status")
    
    # Run once immediately
    save_status_to_file()
    
    # Main monitoring loop
    counter = 0
    while True:
        time.sleep(30)  # Check every 30 seconds
        save_status_to_file()
        
        # Every 5 minutes, check if organization needs restart
        counter += 1
        if counter >= 10:  # 10 * 30 seconds = 5 minutes
            monitor_and_restart_organization()
            counter = 0