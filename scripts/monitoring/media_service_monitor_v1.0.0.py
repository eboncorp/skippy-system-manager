#\!/usr/bin/env python3
"""
Media Service Monitor
External monitoring script that provides real service status
"""
import subprocess
import json
import time
import re
from datetime import datetime
from typing import List, Dict

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

def generate_status_report():
    """Generate a status report for all media services"""
    services = get_docker_services()
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "media_server": "10.0.0.29",
        "services": services,
        "services_running": len([s for s in services if s["status"] == "running"]),
        "services_total": len(services),
        "overall_status": "healthy" if all(s["status"] == "running" for s in services) else "degraded"
    }
    
    return report

def save_status_to_file():
    """Save current status to a file that NexusController can read"""
    report = generate_status_report()
    
    # Save to a location accessible by the container
    with open("/home/ebon/media_service_status.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Status updated: {len(report['services'])} services, {report['services_running']} running")

if __name__ == "__main__":
    print("Media Service Monitor started...")
    
    # Run once immediately
    save_status_to_file()
    
    # Then run every 30 seconds
    while True:
        time.sleep(30)
        save_status_to_file()
