#!/usr/bin/env python3
"""
NexusController v2.0 REST API Server
Modern web API for enterprise integration and remote management
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

# Web framework imports
try:
    from fastapi import FastAPI, HTTPException, Depends, Security, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("ERROR: FastAPI not installed. Run: pip3 install fastapi uvicorn")
    sys.exit(1)

# Core NexusController imports
from nexus_controller_v2 import (
    NexusConfig, SecurityManager, SSHManager, NetworkDiscovery,
    CloudIntegration, SystemMonitor, BackupManager
)

# Pydantic models for API
class NetworkScanRequest(BaseModel):
    network_range: str = Field(..., description="Network range in CIDR notation")
    timeout: Optional[int] = Field(120, description="Scan timeout in seconds")

class NetworkScanResponse(BaseModel):
    scan_id: str
    network_range: str
    devices_found: int
    scan_duration: float
    timestamp: str
    devices: List[Dict[str, Any]]

class SSHConnectionRequest(BaseModel):
    hostname: str = Field(..., description="Target hostname or IP")
    username: str = Field(..., description="SSH username")
    port: int = Field(22, description="SSH port")
    auth_method: str = Field("key", description="Authentication method: key or password")
    auth_value: Optional[str] = Field(None, description="Password or key file path")

class SSHConnectionResponse(BaseModel):
    connection_id: str
    hostname: str
    username: str
    connected: bool
    timestamp: str
    message: str

class SystemMetricsResponse(BaseModel):
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    processes: Dict[str, int]
    alerts: List[Dict[str, Any]]

class BackupRequest(BaseModel):
    backup_type: str = Field("full", description="Backup type: full, config, keys")
    description: Optional[str] = Field(None, description="Backup description")

class BackupResponse(BaseModel):
    backup_id: str
    backup_type: str
    size: int
    timestamp: str
    status: str
    message: str

class APIKeyManager:
    """Manage API keys for authentication"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.api_keys = {}
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from encrypted storage"""
        keys_file = self.security.config.config_dir / "api_keys.json"
        
        if keys_file.exists():
            try:
                with open(keys_file, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted = self.security.decrypt_data(encrypted_data)
                    self.api_keys = json.loads(decrypted)
            except Exception as e:
                logging.error(f"Failed to load API keys: {e}")
                self.api_keys = {}
        else:
            # Create default admin key
            admin_key = self.security.generate_api_key()
            self.api_keys = {
                admin_key: {
                    "name": "admin",
                    "permissions": ["*"],
                    "created": datetime.now().isoformat(),
                    "last_used": None
                }
            }
            self.save_api_keys()
            logging.info(f"Created admin API key: {admin_key}")
    
    def save_api_keys(self):
        """Save API keys to encrypted storage"""
        keys_file = self.security.config.config_dir / "api_keys.json"
        
        try:
            data = json.dumps(self.api_keys, indent=2)
            encrypted = self.security.encrypt_data(data)
            
            with open(keys_file, 'wb') as f:
                f.write(encrypted)
            
            os.chmod(keys_file, 0o600)
            
        except Exception as e:
            logging.error(f"Failed to save API keys: {e}")
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return key info"""
        if api_key in self.api_keys:
            key_info = self.api_keys[api_key]
            # Update last used timestamp
            key_info["last_used"] = datetime.now().isoformat()
            self.save_api_keys()
            return key_info
        return None
    
    def create_api_key(self, name: str, permissions: List[str]) -> str:
        """Create new API key"""
        api_key = self.security.generate_api_key()
        self.api_keys[api_key] = {
            "name": name,
            "permissions": permissions,
            "created": datetime.now().isoformat(),
            "last_used": None
        }
        self.save_api_keys()
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key"""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            self.save_api_keys()
            return True
        return False

class NexusAPIServer:
    """FastAPI server for NexusController"""
    
    def __init__(self):
        # Initialize core components
        self.config = NexusConfig()
        self.security_manager = SecurityManager(self.config)
        self.ssh_manager = SSHManager(self.security_manager, self.config)
        self.network_discovery = NetworkDiscovery(self.config)
        self.system_monitor = SystemMonitor(self.config)
        self.backup_manager = BackupManager(self.config, self.security_manager)
        self.cloud_integration = CloudIntegration(self.config, self.security_manager)
        
        # Initialize API key manager
        self.api_key_manager = APIKeyManager(self.security_manager)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="NexusController API",
            description="Enterprise Infrastructure Management REST API",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup authentication
        self.security = HTTPBearer()
        
        # Setup routes
        self.setup_routes()
        
        # Setup logging
        self.setup_logging()
        
        logging.info("NexusController API Server initialized")
    
    def setup_logging(self):
        """Configure API server logging"""
        log_file = self.config.logs_dir / f"api_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        """Dependency to validate API key"""
        api_key = credentials.credentials
        key_info = self.api_key_manager.validate_api_key(api_key)
        
        if not key_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return key_info
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "security": "ok",
                    "network": "ok",
                    "monitoring": "ok",
                    "backup": "ok"
                }
            }
        
        @self.app.get("/api/v1/system/info")
        async def get_system_info(user: dict = Depends(self.get_current_user)):
            """Get system information"""
            try:
                import platform
                import psutil
                
                return {
                    "hostname": platform.node(),
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "cpu_count": psutil.cpu_count(),
                    "memory_total": psutil.virtual_memory().total,
                    "uptime": datetime.now().isoformat(),
                    "nexus_version": "2.0.0"
                }
            except Exception as e:
                logging.error(f"Failed to get system info: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/system/metrics", response_model=SystemMetricsResponse)
        async def get_system_metrics(user: dict = Depends(self.get_current_user)):
            """Get current system metrics"""
            try:
                metrics = await asyncio.get_event_loop().run_in_executor(
                    None, self.system_monitor.collect_metrics
                )
                
                if not metrics:
                    raise HTTPException(status_code=500, detail="Failed to collect metrics")
                
                return SystemMetricsResponse(
                    timestamp=metrics['timestamp'],
                    cpu_percent=metrics['cpu']['percent'],
                    memory_percent=metrics['memory']['percent'],
                    disk_usage={mount: usage['percent'] for mount, usage in metrics.get('disk', {}).items()},
                    network_io=metrics.get('network', {}),
                    processes=metrics.get('processes', {}),
                    alerts=self.system_monitor.alerts[-10:]  # Last 10 alerts
                )
            except Exception as e:
                logging.error(f"Failed to get system metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/network/scan", response_model=NetworkScanResponse)
        async def scan_network(request: NetworkScanRequest, user: dict = Depends(self.get_current_user)):
            """Scan network for devices"""
            try:
                scan_start = datetime.now()
                
                # Run network scan in executor to avoid blocking
                devices = await asyncio.get_event_loop().run_in_executor(
                    None, self.network_discovery.scan_network, request.network_range
                )
                
                scan_end = datetime.now()
                scan_duration = (scan_end - scan_start).total_seconds()
                
                # Convert devices to list format
                device_list = []
                for ip, device_info in devices.items():
                    device_list.append({
                        "ip": ip,
                        "hostname": device_info.get('hostname'),
                        "mac": device_info.get('mac'),
                        "vendor": device_info.get('vendor'),
                        "status": device_info.get('status'),
                        "discovered_at": device_info.get('discovered_at')
                    })
                
                return NetworkScanResponse(
                    scan_id=f"scan_{int(scan_start.timestamp())}",
                    network_range=request.network_range,
                    devices_found=len(devices),
                    scan_duration=scan_duration,
                    timestamp=scan_start.isoformat(),
                    devices=device_list
                )
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logging.error(f"Network scan failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/network/devices")
        async def get_discovered_devices(user: dict = Depends(self.get_current_user)):
            """Get all discovered network devices"""
            try:
                devices = []
                for ip, device_info in self.network_discovery.discovered_devices.items():
                    devices.append({
                        "ip": ip,
                        "hostname": device_info.get('hostname'),
                        "mac": device_info.get('mac'),
                        "vendor": device_info.get('vendor'),
                        "status": device_info.get('status'),
                        "discovered_at": device_info.get('discovered_at')
                    })
                
                return {
                    "devices": devices,
                    "total": len(devices),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logging.error(f"Failed to get devices: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/ssh/connect", response_model=SSHConnectionResponse)
        async def connect_ssh(request: SSHConnectionRequest, user: dict = Depends(self.get_current_user)):
            """Establish SSH connection"""
            try:
                connect_start = datetime.now()
                
                # Prepare connection parameters
                kwargs = {
                    "hostname": request.hostname,
                    "username": request.username,
                    "port": request.port
                }
                
                if request.auth_method == "password":
                    kwargs["password"] = request.auth_value
                elif request.auth_method == "key":
                    kwargs["key_path"] = request.auth_value
                
                # Run SSH connection in executor
                client = await asyncio.get_event_loop().run_in_executor(
                    None, self.ssh_manager.connect, **kwargs
                )
                
                connection_id = f"{request.username}@{request.hostname}:{request.port}"
                
                return SSHConnectionResponse(
                    connection_id=connection_id,
                    hostname=request.hostname,
                    username=request.username,
                    connected=True,
                    timestamp=connect_start.isoformat(),
                    message="SSH connection established successfully"
                )
                
            except Exception as e:
                logging.error(f"SSH connection failed: {e}")
                return SSHConnectionResponse(
                    connection_id="",
                    hostname=request.hostname,
                    username=request.username,
                    connected=False,
                    timestamp=datetime.now().isoformat(),
                    message=str(e)
                )
        
        @self.app.get("/api/v1/ssh/connections")
        async def get_ssh_connections(user: dict = Depends(self.get_current_user)):
            """Get active SSH connections"""
            try:
                connections = []
                for conn_id, conn_info in self.ssh_manager.connections.items():
                    connections.append({
                        "connection_id": conn_id,
                        "connected_at": conn_info["connected_at"].isoformat(),
                        "last_used": conn_info["last_used"].isoformat(),
                        "active": True
                    })
                
                return {
                    "connections": connections,
                    "total": len(connections),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logging.error(f"Failed to get SSH connections: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/backup/create", response_model=BackupResponse)
        async def create_backup(request: BackupRequest, user: dict = Depends(self.get_current_user)):
            """Create system backup"""
            try:
                backup_start = datetime.now()
                
                # Run backup in executor
                success = await asyncio.get_event_loop().run_in_executor(
                    None, self.backup_manager.create_backup, request.backup_type
                )
                
                if success:
                    # Get the latest backup info
                    latest_backup = self.backup_manager.manifest['backups'][-1]
                    
                    return BackupResponse(
                        backup_id=latest_backup['name'],
                        backup_type=latest_backup['type'],
                        size=latest_backup['size'],
                        timestamp=latest_backup['timestamp'],
                        status="completed",
                        message="Backup created successfully"
                    )
                else:
                    return BackupResponse(
                        backup_id="",
                        backup_type=request.backup_type,
                        size=0,
                        timestamp=backup_start.isoformat(),
                        status="failed",
                        message="Backup creation failed"
                    )
                
            except Exception as e:
                logging.error(f"Backup creation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/backup/list")
        async def list_backups(user: dict = Depends(self.get_current_user)):
            """List all backups"""
            try:
                return {
                    "backups": self.backup_manager.manifest['backups'],
                    "last_backup": self.backup_manager.manifest['last_backup'],
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logging.error(f"Failed to list backups: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/admin/api-keys")
        async def create_api_key(
            name: str,
            permissions: List[str],
            user: dict = Depends(self.get_current_user)
        ):
            """Create new API key (admin only)"""
            # Check if user has admin permissions
            if "*" not in user.get("permissions", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin permissions required"
                )
            
            try:
                api_key = self.api_key_manager.create_api_key(name, permissions)
                return {
                    "api_key": api_key,
                    "name": name,
                    "permissions": permissions,
                    "created": datetime.now().isoformat()
                }
            except Exception as e:
                logging.error(f"Failed to create API key: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/api/v1/admin/api-keys/{api_key}")
        async def revoke_api_key(api_key: str, user: dict = Depends(self.get_current_user)):
            """Revoke API key (admin only)"""
            # Check if user has admin permissions
            if "*" not in user.get("permissions", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin permissions required"
                )
            
            try:
                success = self.api_key_manager.revoke_api_key(api_key)
                if success:
                    return {"message": "API key revoked successfully"}
                else:
                    raise HTTPException(status_code=404, detail="API key not found")
            except Exception as e:
                logging.error(f"Failed to revoke API key: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def run(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """Run the API server"""
        logging.info(f"Starting NexusController API Server on {host}:{port}")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            access_log=True,
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    },
                },
                "handlers": {
                    "default": {
                        "formatter": "default",
                        "class": "logging.StreamHandler",
                        "stream": "ext://sys.stdout",
                    },
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["default"],
                },
            }
        )

def main():
    """Main entry point for API server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NexusController API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    try:
        server = NexusAPIServer()
        server.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logging.info("API server shutdown by user")
    except Exception as e:
        logging.error(f"API server failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())