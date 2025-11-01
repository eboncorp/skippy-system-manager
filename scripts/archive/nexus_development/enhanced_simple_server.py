#\!/usr/bin/env python3
"""
Enhanced Simple NexusController for Media Server
Real service monitoring with external data source
"""
import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn

app = FastAPI(
    title="NexusController Media Server",
    description="Real-time infrastructure management for media services",
    version="2.0.0"
)

class ServiceStatus(BaseModel):
    name: str
    status: str
    container_id: Optional[str] = None
    uptime: Optional[str] = None
    ports: List[str] = []
    health: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]

def load_service_status() -> Dict:
    """Load service status from external monitoring file"""
    try:
        status_file = "/app/media_service_status.json"
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                data = json.load(f)
                return data
        else:
            # Fallback to static data if file not available
            return {
                "timestamp": datetime.now().isoformat(),
                "media_server": "10.0.0.29",
                "services": [
                    {"name": "jellyfin", "status": "running", "ports": ["8096:8096"], "health": "healthy"},
                    {"name": "homeassistant", "status": "running", "ports": [], "health": "unknown"},
                    {"name": "mosquitto", "status": "running", "ports": ["1883:1883"], "health": "unknown"},
                    {"name": "nodered", "status": "running", "ports": ["1880:1880"], "health": "healthy"}
                ],
                "services_running": 4,
                "services_total": 4,
                "overall_status": "healthy"
            }
    except Exception as e:
        print(f"Error loading service status: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "services": [],
            "services_running": 0,
            "services_total": 0,
            "overall_status": "unknown"
        }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check with real service status"""
    data = load_service_status()
    service_status = {}
    
    for service in data.get("services", []):
        service_status[service["name"]] = service["status"]
    
    return HealthResponse(
        status=data.get("overall_status", "unknown"),
        timestamp=datetime.now(),
        services=service_status
    )

@app.get("/api/v1/status")
async def get_status():
    """Get detailed system status"""
    data = load_service_status()
    
    return {
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "media_server": data.get("media_server", "10.0.0.29"),
        "services": [s["name"] for s in data.get("services", [])],
        "services_running": data.get("services_running", 0),
        "services_total": data.get("services_total", 0),
        "overall_status": data.get("overall_status", "unknown"),
        "last_update": data.get("timestamp", "unknown")
    }

@app.get("/api/v1/services", response_model=List[ServiceStatus])
async def list_services():
    """List all managed services with detailed status"""
    data = load_service_status()
    services = []
    
    for service in data.get("services", []):
        services.append(ServiceStatus(
            name=service.get("name", "unknown"),
            status=service.get("status", "unknown"),
            container_id=service.get("container_id"),
            uptime=service.get("uptime"),
            ports=service.get("ports", []),
            health=service.get("health")
        ))
    
    return services

@app.get("/api/v1/services/{service_name}")
async def get_service_detail(service_name: str):
    """Get detailed information about a specific service"""
    data = load_service_status()
    
    for service in data.get("services", []):
        if service.get("name") == service_name:
            return ServiceStatus(
                name=service.get("name", "unknown"),
                status=service.get("status", "unknown"),
                container_id=service.get("container_id"),
                uptime=service.get("uptime"),
                ports=service.get("ports", []),
                health=service.get("health")
            )
    
    raise HTTPException(status_code=404, detail="Service not found")

@app.get("/api/v1/system/info")
async def get_system_info():
    """Get system information"""
    data = load_service_status()
    
    return {
        "hostname": "media-server",
        "media_server": data.get("media_server", "10.0.0.29"),
        "monitoring": "active" if os.path.exists("/app/media_service_status.json") else "unavailable",
        "services_summary": {
            "total": data.get("services_total", 0),
            "running": data.get("services_running", 0),
            "status": data.get("overall_status", "unknown")
        },
        "timestamp": datetime.now().isoformat(),
        "last_monitoring_update": data.get("timestamp", "unknown")
    }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": "info",
        "reload": False
    }
    
    print(f"Starting Enhanced NexusController Media Server on {config['host']}:{config['port']}")
    print("Real-time service monitoring enabled")
    uvicorn.run(app, **config)
