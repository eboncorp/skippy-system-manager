#\!/usr/bin/env python3
"""
Enhanced NexusController for Media Server
Real-time service monitoring and management
"""
import asyncio
import subprocess
import json
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn

app = FastAPI(
    title="NexusController Media Server",
    description="Infrastructure management for media services",
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

class ServiceActionResponse(BaseModel):
    service: str
    action: str
    status: str
    message: str

async def get_docker_services() -> List[ServiceStatus]:
    """Get status of Docker services"""
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
                
                services.append(ServiceStatus(
                    name=name,
                    status="running" if "Up " in status else "stopped",
                    container_id=container_id,
                    uptime=uptime,
                    ports=port_list,
                    health=health
                ))
        
        return services
    except subprocess.CalledProcessError as e:
        print(f"Error getting docker services: {e}")
        return []

async def get_service_logs(service_name: str, lines: int = 50) -> str:
    """Get logs for a specific service"""
    try:
        result = subprocess.run([
            "docker", "logs", "--tail", str(lines), service_name
        ], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting logs: {e}"

async def manage_service(service_name: str, action: str) -> ServiceActionResponse:
    """Manage service (start, stop, restart)"""
    try:
        if action == "restart":
            result = subprocess.run([
                "docker", "restart", service_name
            ], capture_output=True, text=True, check=True)
            return ServiceActionResponse(
                service=service_name,
                action=action,
                status="success",
                message=f"Service {service_name} restarted successfully"
            )
        elif action == "stop":
            result = subprocess.run([
                "docker", "stop", service_name
            ], capture_output=True, text=True, check=True)
            return ServiceActionResponse(
                service=service_name,
                action=action,
                status="success",
                message=f"Service {service_name} stopped successfully"
            )
        elif action == "start":
            result = subprocess.run([
                "docker", "start", service_name
            ], capture_output=True, text=True, check=True)
            return ServiceActionResponse(
                service=service_name,
                action=action,
                status="success",
                message=f"Service {service_name} started successfully"
            )
        else:
            return ServiceActionResponse(
                service=service_name,
                action=action,
                status="error",
                message=f"Unknown action: {action}"
            )
    except subprocess.CalledProcessError as e:
        return ServiceActionResponse(
            service=service_name,
            action=action,
            status="error",
            message=f"Failed to {action} service: {e}"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check with real service status"""
    services = await get_docker_services()
    service_status = {}
    
    for service in services:
        service_status[service.name] = service.status
    
    overall_status = "healthy" if all(s == "running" for s in service_status.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        services=service_status
    )

@app.get("/api/v1/status")
async def get_status():
    """Get detailed system status"""
    services = await get_docker_services()
    
    return {
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "media_server": "10.0.0.29",
        "services": [s.name for s in services],
        "services_running": len([s for s in services if s.status == "running"]),
        "services_total": len(services)
    }

@app.get("/api/v1/services", response_model=List[ServiceStatus])
async def list_services():
    """List all managed services with detailed status"""
    return await get_docker_services()

@app.get("/api/v1/services/{service_name}")
async def get_service_detail(service_name: str):
    """Get detailed information about a specific service"""
    services = await get_docker_services()
    service = next((s for s in services if s.name == service_name), None)
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return service

@app.get("/api/v1/services/{service_name}/logs")
async def get_service_logs_endpoint(service_name: str, lines: int = 50):
    """Get logs for a specific service"""
    services = await get_docker_services()
    if not any(s.name == service_name for s in services):
        raise HTTPException(status_code=404, detail="Service not found")
    
    logs = await get_service_logs(service_name, lines)
    return {
        "service": service_name,
        "lines": lines,
        "logs": logs,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/services/{service_name}/{action}", response_model=ServiceActionResponse)
async def manage_service_endpoint(service_name: str, action: str):
    """Manage a service (start, stop, restart)"""
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid action. Use start, stop, or restart")
    
    services = await get_docker_services()
    if not any(s.name == service_name for s in services):
        raise HTTPException(status_code=404, detail="Service not found")
    
    return await manage_service(service_name, action)

@app.get("/api/v1/system/info")
async def get_system_info():
    """Get system information"""
    try:
        # Get system info
        uptime_result = subprocess.run(["uptime"], capture_output=True, text=True)
        df_result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        
        return {
            "hostname": "media-server",
            "uptime": uptime_result.stdout.strip() if uptime_result.returncode == 0 else "unknown",
            "disk_usage": df_result.stdout.strip() if df_result.returncode == 0 else "unknown",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    config = {
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": "info",
        "reload": False
    }
    
    print(f"Starting Enhanced NexusController Media Server on {config['host']}:{config['port']}")
    uvicorn.run(app, **config)
