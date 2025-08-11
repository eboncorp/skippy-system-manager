#!/usr/bin/env python3
"""
NexusController v2.0 WebSocket Server
Real-time updates and bidirectional communication
"""

import os
import sys
import json
import asyncio
import logging
import weakref
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.websockets import WebSocketState
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Import core systems
from nexus_event_system import Event, EventType, EventBus, EventHandler

class MessageType(Enum):
    """WebSocket message types"""
    # System messages
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILED = "auth_failed"
    ERROR = "error"
    
    # Subscription messages
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIPTION_SUCCESS = "subscription_success"
    SUBSCRIPTION_FAILED = "subscription_failed"
    
    # Data messages
    EVENT = "event"
    SYSTEM_STATUS = "system_status"
    NETWORK_UPDATE = "network_update"
    SSH_STATUS = "ssh_status"
    METRICS_UPDATE = "metrics_update"
    ALERT = "alert"
    
    # Command messages
    COMMAND = "command"
    COMMAND_RESULT = "command_result"
    
    # Custom messages
    CUSTOM = "custom"

@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.CUSTOM
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    channel: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'correlation_id': self.correlation_id,
            'channel': self.channel
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        """Create from dictionary"""
        return cls(
            message_id=data.get('message_id', str(uuid.uuid4())),
            message_type=MessageType(data.get('message_type', 'custom')),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            data=data.get('data', {}),
            correlation_id=data.get('correlation_id'),
            channel=data.get('channel')
        )

@dataclass
class ClientConnection:
    """WebSocket client connection info"""
    
    connection_id: str
    websocket: Any  # WebSocket connection object
    authenticated: bool = False
    user_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class WebSocketEventHandler(EventHandler):
    """Event handler that broadcasts events via WebSocket"""
    
    def __init__(self, websocket_server):
        self.websocket_server = websocket_server
    
    async def handle(self, event: Event):
        """Handle event by broadcasting to WebSocket clients"""
        # Convert event to WebSocket message
        message = WebSocketMessage(
            message_type=MessageType.EVENT,
            data={
                'event_type': event.event_type.value,
                'source': event.source,
                'event_data': event.data,
                'severity': event.severity,
                'tags': event.tags
            },
            channel=f"events.{event.event_type.value}"
        )
        
        # Broadcast to subscribers
        await self.websocket_server.broadcast_to_channel(
            f"events.{event.event_type.value}", 
            message
        )
        
        # Also broadcast to general events channel
        await self.websocket_server.broadcast_to_channel("events.all", message)
    
    def can_handle(self, event: Event) -> bool:
        """Can handle all events"""
        return True

class WebSocketServer:
    """WebSocket server for real-time communication"""
    
    def __init__(self, host: str = "localhost", port: int = 8765, event_bus: EventBus = None):
        self.host = host
        self.port = port
        self.event_bus = event_bus
        
        # Client management
        self.clients: Dict[str, ClientConnection] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel -> set of connection_ids
        
        # Authentication
        self.auth_required = True
        self.api_keys = set()  # Valid API keys
        
        # Server state
        self.server = None
        self.running = False
        
        # Background tasks
        self._ping_task = None
        self._cleanup_task = None
        
        # Statistics
        self.stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0
        }
        
        # Setup event handler
        if self.event_bus:
            self.event_handler = WebSocketEventHandler(self)
            self.event_bus.subscribe(
                [event_type for event_type in EventType],
                self.event_handler
            )
        
        logging.info(f"WebSocketServer initialized on {host}:{port}")
    
    async def start(self):
        """Start WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets library not available")
        
        self.running = True
        
        # Start WebSocket server
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        # Start background tasks
        self._ping_task = asyncio.create_task(self._ping_clients_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logging.info(f"WebSocket server started on ws://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop WebSocket server"""
        self.running = False
        
        # Cancel background tasks
        if self._ping_task:
            self._ping_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all client connections
        for client in list(self.clients.values()):
            try:
                await client.websocket.close()
            except Exception:
                pass
        
        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logging.info("WebSocket server stopped")
    
    async def handle_client(self, websocket, path):
        """Handle new client connection"""
        connection_id = str(uuid.uuid4())
        
        client = ClientConnection(
            connection_id=connection_id,
            websocket=websocket
        )
        
        self.clients[connection_id] = client
        self.stats['total_connections'] += 1
        self.stats['active_connections'] += 1
        
        logging.info(f"New WebSocket client connected: {connection_id}")
        
        try:
            # Send welcome message
            welcome_msg = WebSocketMessage(
                message_type=MessageType.AUTH,
                data={
                    'connection_id': connection_id,
                    'server_time': datetime.now().isoformat(),
                    'auth_required': self.auth_required
                }
            )
            await self.send_message(connection_id, welcome_msg)
            
            # Handle messages
            async for raw_message in websocket:
                try:
                    await self._handle_message(connection_id, raw_message)
                    self.stats['messages_received'] += 1
                except Exception as e:
                    logging.error(f"Error handling message from {connection_id}: {e}")
                    self.stats['errors'] += 1
                    
                    error_msg = WebSocketMessage(
                        message_type=MessageType.ERROR,
                        data={'error': str(e)}
                    )
                    await self.send_message(connection_id, error_msg)
        
        except websockets.exceptions.ConnectionClosed:
            logging.info(f"Client disconnected: {connection_id}")
        except Exception as e:
            logging.error(f"Client connection error: {e}")
        finally:
            await self._cleanup_client(connection_id)
    
    async def _handle_message(self, connection_id: str, raw_message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(raw_message)
            message = WebSocketMessage.from_dict(data)
            
            client = self.clients.get(connection_id)
            if not client:
                return
            
            # Handle different message types
            if message.message_type == MessageType.PING:
                await self._handle_ping(connection_id, message)
            
            elif message.message_type == MessageType.AUTH:
                await self._handle_auth(connection_id, message)
            
            elif message.message_type == MessageType.SUBSCRIBE:
                await self._handle_subscribe(connection_id, message)
            
            elif message.message_type == MessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe(connection_id, message)
            
            elif message.message_type == MessageType.COMMAND:
                await self._handle_command(connection_id, message)
            
            else:
                logging.warning(f"Unknown message type: {message.message_type}")
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Message handling error: {e}")
    
    async def _handle_ping(self, connection_id: str, message: WebSocketMessage):
        """Handle ping message"""
        client = self.clients.get(connection_id)
        if client:
            client.last_ping = datetime.now()
            
            pong_msg = WebSocketMessage(
                message_type=MessageType.PONG,
                correlation_id=message.message_id,
                data={'server_time': datetime.now().isoformat()}
            )
            await self.send_message(connection_id, pong_msg)
    
    async def _handle_auth(self, connection_id: str, message: WebSocketMessage):
        """Handle authentication"""
        client = self.clients.get(connection_id)
        if not client:
            return
        
        if not self.auth_required:
            client.authenticated = True
            client.user_id = "anonymous"
            
            auth_msg = WebSocketMessage(
                message_type=MessageType.AUTH_SUCCESS,
                correlation_id=message.message_id,
                data={'user_id': client.user_id}
            )
            await self.send_message(connection_id, auth_msg)
            return
        
        # Check API key
        api_key = message.data.get('api_key')
        if not api_key or api_key not in self.api_keys:
            auth_msg = WebSocketMessage(
                message_type=MessageType.AUTH_FAILED,
                correlation_id=message.message_id,
                data={'error': 'Invalid API key'}
            )
            await self.send_message(connection_id, auth_msg)
            return
        
        # Authentication successful
        client.authenticated = True
        client.user_id = message.data.get('user_id', 'authenticated_user')
        
        auth_msg = WebSocketMessage(
            message_type=MessageType.AUTH_SUCCESS,
            correlation_id=message.message_id,
            data={'user_id': client.user_id}
        )
        await self.send_message(connection_id, auth_msg)
    
    async def _handle_subscribe(self, connection_id: str, message: WebSocketMessage):
        """Handle subscription request"""
        client = self.clients.get(connection_id)
        if not client:
            return
        
        if self.auth_required and not client.authenticated:
            error_msg = WebSocketMessage(
                message_type=MessageType.SUBSCRIPTION_FAILED,
                correlation_id=message.message_id,
                data={'error': 'Authentication required'}
            )
            await self.send_message(connection_id, error_msg)
            return
        
        channel = message.data.get('channel')
        if not channel:
            error_msg = WebSocketMessage(
                message_type=MessageType.SUBSCRIPTION_FAILED,
                correlation_id=message.message_id,
                data={'error': 'Channel required'}
            )
            await self.send_message(connection_id, error_msg)
            return
        
        # Add to channel
        if channel not in self.channels:
            self.channels[channel] = set()
        
        self.channels[channel].add(connection_id)
        client.subscriptions.add(channel)
        
        success_msg = WebSocketMessage(
            message_type=MessageType.SUBSCRIPTION_SUCCESS,
            correlation_id=message.message_id,
            data={'channel': channel}
        )
        await self.send_message(connection_id, success_msg)
        
        logging.info(f"Client {connection_id} subscribed to channel: {channel}")
    
    async def _handle_unsubscribe(self, connection_id: str, message: WebSocketMessage):
        """Handle unsubscription request"""
        client = self.clients.get(connection_id)
        if not client:
            return
        
        channel = message.data.get('channel')
        if not channel:
            return
        
        # Remove from channel
        if channel in self.channels:
            self.channels[channel].discard(connection_id)
            if not self.channels[channel]:
                del self.channels[channel]
        
        client.subscriptions.discard(channel)
        
        logging.info(f"Client {connection_id} unsubscribed from channel: {channel}")
    
    async def _handle_command(self, connection_id: str, message: WebSocketMessage):
        """Handle command execution request"""
        client = self.clients.get(connection_id)
        if not client or not client.authenticated:
            error_msg = WebSocketMessage(
                message_type=MessageType.COMMAND_RESULT,
                correlation_id=message.message_id,
                data={'error': 'Authentication required'}
            )
            await self.send_message(connection_id, error_msg)
            return
        
        command = message.data.get('command')
        params = message.data.get('params', {})
        
        try:
            # Execute command (this would integrate with core systems)
            result = await self._execute_command(command, params)
            
            result_msg = WebSocketMessage(
                message_type=MessageType.COMMAND_RESULT,
                correlation_id=message.message_id,
                data={'result': result}
            )
            await self.send_message(connection_id, result_msg)
            
        except Exception as e:
            error_msg = WebSocketMessage(
                message_type=MessageType.COMMAND_RESULT,
                correlation_id=message.message_id,
                data={'error': str(e)}
            )
            await self.send_message(connection_id, error_msg)
    
    async def _execute_command(self, command: str, params: Dict[str, Any]) -> Any:
        """Execute command (integration point)"""
        # This would integrate with the main NexusController systems
        
        if command == "get_system_status":
            return {
                'status': 'running',
                'uptime': '1h 30m',
                'connected_clients': len(self.clients)
            }
        elif command == "list_network_devices":
            return []  # Would integrate with NetworkDiscovery
        elif command == "get_ssh_connections":
            return []  # Would integrate with SSHManager
        else:
            raise ValueError(f"Unknown command: {command}")
    
    async def send_message(self, connection_id: str, message: WebSocketMessage):
        """Send message to specific client"""
        client = self.clients.get(connection_id)
        if not client:
            return
        
        try:
            data = json.dumps(message.to_dict())
            await client.websocket.send(data)
            self.stats['messages_sent'] += 1
        except Exception as e:
            logging.error(f"Failed to send message to {connection_id}: {e}")
            await self._cleanup_client(connection_id)
    
    async def broadcast_to_channel(self, channel: str, message: WebSocketMessage):
        """Broadcast message to all clients in channel"""
        if channel not in self.channels:
            return
        
        # Get list of connection IDs (copy to avoid modification during iteration)
        connection_ids = list(self.channels[channel])
        
        for connection_id in connection_ids:
            await self.send_message(connection_id, message)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connected clients"""
        connection_ids = list(self.clients.keys())
        
        for connection_id in connection_ids:
            await self.send_message(connection_id, message)
    
    async def _cleanup_client(self, connection_id: str):
        """Clean up client connection"""
        if connection_id not in self.clients:
            return
        
        client = self.clients[connection_id]
        
        # Remove from all channels
        for channel in list(client.subscriptions):
            if channel in self.channels:
                self.channels[channel].discard(connection_id)
                if not self.channels[channel]:
                    del self.channels[channel]
        
        # Remove client
        del self.clients[connection_id]
        self.stats['active_connections'] -= 1
        
        logging.info(f"Client {connection_id} cleaned up")
    
    async def _ping_clients_loop(self):
        """Background task to ping clients"""
        while self.running:
            try:
                now = datetime.now()
                stale_clients = []
                
                for connection_id, client in self.clients.items():
                    # Check if client hasn't responded to ping in 60 seconds
                    if (now - client.last_ping).total_seconds() > 60:
                        stale_clients.append(connection_id)
                    else:
                        # Send ping
                        ping_msg = WebSocketMessage(
                            message_type=MessageType.PING,
                            data={'server_time': now.isoformat()}
                        )
                        await self.send_message(connection_id, ping_msg)
                
                # Clean up stale clients
                for connection_id in stale_clients:
                    await self._cleanup_client(connection_id)
                
                await asyncio.sleep(30)  # Ping every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Ping loop error: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_loop(self):
        """Background cleanup task"""
        while self.running:
            try:
                # Clean up empty channels
                empty_channels = [
                    channel for channel, clients in self.channels.items()
                    if not clients
                ]
                
                for channel in empty_channels:
                    del self.channels[channel]
                
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)
    
    def add_api_key(self, api_key: str):
        """Add valid API key for authentication"""
        self.api_keys.add(api_key)
    
    def remove_api_key(self, api_key: str):
        """Remove API key"""
        self.api_keys.discard(api_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            **self.stats,
            'channels': len(self.channels),
            'uptime': (datetime.now() - datetime.now()).total_seconds() if self.running else 0
        }
    
    def get_client_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get client connection info"""
        client = self.clients.get(connection_id)
        if not client:
            return None
        
        return {
            'connection_id': client.connection_id,
            'authenticated': client.authenticated,
            'user_id': client.user_id,
            'subscriptions': list(client.subscriptions),
            'connected_at': client.connected_at.isoformat(),
            'last_ping': client.last_ping.isoformat(),
            'metadata': client.metadata
        }

class FastAPIWebSocketServer:
    """FastAPI-based WebSocket server for integration with REST API"""
    
    def __init__(self, app: FastAPI, event_bus: EventBus = None):
        self.app = app
        self.event_bus = event_bus
        self.websocket_server = WebSocketServer(event_bus=event_bus)
        self.setup_routes()
    
    def setup_routes(self):
        """Setup WebSocket routes"""
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            
            connection_id = str(uuid.uuid4())
            
            # Create client connection
            client = ClientConnection(
                connection_id=connection_id,
                websocket=websocket
            )
            
            self.websocket_server.clients[connection_id] = client
            
            try:
                while True:
                    data = await websocket.receive_text()
                    await self.websocket_server._handle_message(connection_id, data)
            
            except WebSocketDisconnect:
                await self.websocket_server._cleanup_client(connection_id)
        
        @self.app.get("/ws/stats")
        async def get_websocket_stats():
            """Get WebSocket server statistics"""
            return self.websocket_server.get_stats()
        
        @self.app.get("/ws/clients")
        async def list_websocket_clients():
            """List connected WebSocket clients"""
            clients = []
            for connection_id in self.websocket_server.clients:
                client_info = self.websocket_server.get_client_info(connection_id)
                if client_info:
                    clients.append(client_info)
            return clients

def main():
    """Demo WebSocket server"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        if not WEBSOCKETS_AVAILABLE:
            print("websockets library not available")
            return
        
        # Create WebSocket server
        server = WebSocketServer(host="localhost", port=8765)
        server.auth_required = False  # Disable auth for demo
        
        await server.start()
        
        print("WebSocket server running on ws://localhost:8765")
        print("You can test with a WebSocket client")
        
        try:
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
                # Send periodic status updates
                status_msg = WebSocketMessage(
                    message_type=MessageType.SYSTEM_STATUS,
                    data={
                        'timestamp': datetime.now().isoformat(),
                        'clients': len(server.clients),
                        'uptime': '5m'
                    },
                    channel="system.status"
                )
                
                await server.broadcast_to_channel("system.status", status_msg)
                
                await asyncio.sleep(10)  # Every 10 seconds
        
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await server.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()