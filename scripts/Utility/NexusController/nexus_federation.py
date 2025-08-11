#!/usr/bin/env python3
"""
NexusController v2.0 Federation System
Multi-node scaling and distributed infrastructure management
"""

import os
import sys
import json
import asyncio
import logging
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import weakref
from pathlib import Path

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Import core systems
from nexus_event_system import Event, EventType, EventBus
from nexus_state_manager import Resource, ResourceType, StateManager

class NodeRole(Enum):
    """Node roles in the federation"""
    LEADER = "leader"          # Primary coordinator node
    FOLLOWER = "follower"      # Regular federation member
    OBSERVER = "observer"      # Read-only node
    CANDIDATE = "candidate"    # Node trying to become leader

class NodeStatus(Enum):
    """Node status in federation"""
    UNKNOWN = "unknown"
    CONNECTING = "connecting"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    MAINTENANCE = "maintenance"

class FederationMessageType(Enum):
    """Federation message types"""
    # Discovery and joining
    DISCOVERY = "discovery"
    JOIN_REQUEST = "join_request"
    JOIN_ACCEPT = "join_accept"
    JOIN_REJECT = "join_reject"
    LEAVE = "leave"
    
    # Leadership election
    LEADER_ELECTION = "leader_election"
    LEADER_ANNOUNCE = "leader_announce"
    HEARTBEAT = "heartbeat"
    
    # State synchronization
    STATE_SYNC = "state_sync"
    STATE_REQUEST = "state_request"
    STATE_RESPONSE = "state_response"
    
    # Task distribution
    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    TASK_STATUS = "task_status"
    
    # Event replication
    EVENT_REPLICATE = "event_replicate"
    
    # Health checking
    HEALTH_CHECK = "health_check"
    HEALTH_RESPONSE = "health_response"

@dataclass
class FederationNode:
    """Federation node information"""
    
    node_id: str
    name: str
    host: str
    port: int
    role: NodeRole = NodeRole.FOLLOWER
    status: NodeStatus = NodeStatus.UNKNOWN
    version: str = "2.0.0"
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    joined_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    load_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def endpoint(self) -> str:
        """Get node API endpoint"""
        return f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['role'] = self.role.value
        result['status'] = self.status.value
        result['joined_at'] = self.joined_at.isoformat()
        result['last_seen'] = self.last_seen.isoformat()
        result['last_heartbeat'] = self.last_heartbeat.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FederationNode':
        """Create from dictionary"""
        data = data.copy()
        data['role'] = NodeRole(data['role'])
        data['status'] = NodeStatus(data['status'])
        data['joined_at'] = datetime.fromisoformat(data['joined_at'])
        data['last_seen'] = datetime.fromisoformat(data['last_seen'])
        data['last_heartbeat'] = datetime.fromisoformat(data['last_heartbeat'])
        return cls(**data)

@dataclass
class FederationMessage:
    """Federation communication message"""
    
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: FederationMessageType = FederationMessageType.HEARTBEAT
    source_node: str = ""
    target_node: Optional[str] = None  # None for broadcast
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'source_node': self.source_node,
            'target_node': self.target_node,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'correlation_id': self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FederationMessage':
        """Create from dictionary"""
        return cls(
            message_id=data['message_id'],
            message_type=FederationMessageType(data['message_type']),
            source_node=data['source_node'],
            target_node=data.get('target_node'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            data=data['data'],
            correlation_id=data.get('correlation_id')
        )

class LeaderElection:
    """Raft-inspired leader election algorithm"""
    
    def __init__(self, node_id: str, federation):
        self.node_id = node_id
        self.federation = federation
        self.current_term = 0
        self.voted_for = None
        self.election_timeout = 5.0  # seconds
        self.heartbeat_interval = 1.0  # seconds
        self.election_timer = None
        self._lock = threading.RLock()
    
    async def start_election(self):
        """Start leader election process"""
        with self._lock:
            self.current_term += 1
            self.voted_for = self.node_id
            
            # Become candidate
            self.federation.local_node.role = NodeRole.CANDIDATE
            
            logging.info(f"Starting leader election for term {self.current_term}")
            
            # Request votes from other nodes
            vote_requests = []
            for node in self.federation.get_active_nodes():
                if node.node_id != self.node_id:
                    vote_requests.append(self._request_vote(node))
            
            # Wait for responses
            if vote_requests:
                responses = await asyncio.gather(*vote_requests, return_exceptions=True)
                
                # Count votes
                votes_received = 1  # Vote for self
                for response in responses:
                    if isinstance(response, dict) and response.get('vote_granted'):
                        votes_received += 1
                
                # Check if majority
                total_nodes = len(self.federation.nodes) + 1  # Include self
                if votes_received > total_nodes // 2:
                    await self._become_leader()
                else:
                    # Election failed, become follower
                    self.federation.local_node.role = NodeRole.FOLLOWER
                    logging.info(f"Election failed, received {votes_received}/{total_nodes} votes")
            else:
                # No other nodes, become leader
                await self._become_leader()
    
    async def _request_vote(self, node: FederationNode) -> Dict[str, Any]:
        """Request vote from a node"""
        try:
            message = FederationMessage(
                message_type=FederationMessageType.LEADER_ELECTION,
                source_node=self.node_id,
                target_node=node.node_id,
                data={
                    'term': self.current_term,
                    'candidate_id': self.node_id,
                    'last_log_index': 0,  # Simplified for now
                    'last_log_term': 0
                }
            )
            
            response = await self.federation._send_message(node, message)
            return response
            
        except Exception as e:
            logging.error(f"Failed to request vote from {node.node_id}: {e}")
            return {'vote_granted': False}
    
    async def _become_leader(self):
        """Become federation leader"""
        self.federation.local_node.role = NodeRole.LEADER
        self.federation.current_leader = self.node_id
        
        # Announce leadership
        announce_msg = FederationMessage(
            message_type=FederationMessageType.LEADER_ANNOUNCE,
            source_node=self.node_id,
            data={
                'term': self.current_term,
                'leader_id': self.node_id
            }
        )
        
        await self.federation.broadcast_message(announce_msg)
        
        logging.info(f"Became federation leader for term {self.current_term}")
        
        # Start sending heartbeats
        asyncio.create_task(self._heartbeat_loop())
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats as leader"""
        while (self.federation.local_node.role == NodeRole.LEADER and 
               self.federation.running):
            
            try:
                heartbeat_msg = FederationMessage(
                    message_type=FederationMessageType.HEARTBEAT,
                    source_node=self.node_id,
                    data={
                        'term': self.current_term,
                        'leader_id': self.node_id
                    }
                )
                
                await self.federation.broadcast_message(heartbeat_msg)
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.heartbeat_interval)

class TaskDistributor:
    """Distribute tasks across federation nodes"""
    
    def __init__(self, federation):
        self.federation = federation
        self.pending_tasks = {}
        self.task_assignments = {}  # task_id -> node_id
        self._lock = threading.RLock()
    
    async def distribute_task(self, task_type: str, task_data: Dict[str, Any], 
                            preferred_node: str = None) -> str:
        """Distribute task to appropriate node"""
        task_id = str(uuid.uuid4())
        
        # Select target node
        target_node = await self._select_node(task_type, preferred_node)
        
        if not target_node:
            raise RuntimeError("No suitable node available for task")
        
        # Create task assignment
        task_assignment = {
            'task_id': task_id,
            'task_type': task_type,
            'task_data': task_data,
            'created_at': datetime.now().isoformat(),
            'timeout': 300  # 5 minutes
        }
        
        with self._lock:
            self.pending_tasks[task_id] = task_assignment
            self.task_assignments[task_id] = target_node.node_id
        
        # Send task to node
        task_msg = FederationMessage(
            message_type=FederationMessageType.TASK_ASSIGN,
            source_node=self.federation.local_node.node_id,
            target_node=target_node.node_id,
            data=task_assignment
        )
        
        await self.federation._send_message(target_node, task_msg)
        
        logging.info(f"Task {task_id} assigned to node {target_node.node_id}")
        return task_id
    
    async def _select_node(self, task_type: str, preferred_node: str = None) -> Optional[FederationNode]:
        """Select best node for task execution"""
        active_nodes = self.federation.get_active_nodes()
        
        if preferred_node:
            # Try preferred node first
            for node in active_nodes:
                if node.node_id == preferred_node:
                    return node
        
        if not active_nodes:
            return None
        
        # Simple load balancing - select node with lowest load
        best_node = None
        lowest_load = float('inf')
        
        for node in active_nodes:
            cpu_load = node.load_metrics.get('cpu_percent', 0)
            memory_load = node.load_metrics.get('memory_percent', 0)
            combined_load = (cpu_load + memory_load) / 2
            
            if combined_load < lowest_load:
                lowest_load = combined_load
                best_node = node
        
        return best_node
    
    async def handle_task_result(self, task_id: str, result: Dict[str, Any]):
        """Handle task completion result"""
        with self._lock:
            if task_id in self.pending_tasks:
                task = self.pending_tasks.pop(task_id)
                self.task_assignments.pop(task_id, None)
                
                logging.info(f"Task {task_id} completed: {result.get('status', 'unknown')}")
                
                # Could emit event or store result
                return True
        
        return False

class FederationManager:
    """Main federation management system"""
    
    def __init__(self, node_id: str, name: str, host: str, port: int, 
                 event_bus: EventBus = None, state_manager: StateManager = None):
        
        # Local node info
        self.local_node = FederationNode(
            node_id=node_id,
            name=name,
            host=host,
            port=port,
            capabilities=['network_discovery', 'ssh_management', 'monitoring']
        )
        
        # Federation state
        self.nodes: Dict[str, FederationNode] = {}
        self.current_leader = None
        self.running = False
        
        # Core integrations
        self.event_bus = event_bus
        self.state_manager = state_manager
        
        # Sub-systems
        self.leader_election = LeaderElection(node_id, self)
        self.task_distributor = TaskDistributor(self)
        
        # Communication
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp required for federation")
        
        self.session = None
        
        # Background tasks
        self._discovery_task = None
        self._health_check_task = None
        self._state_sync_task = None
        
        # Configuration
        self.discovery_interval = 30  # seconds
        self.health_check_interval = 10  # seconds
        self.state_sync_interval = 60  # seconds
        self.node_timeout = 90  # seconds
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        logging.info(f"FederationManager initialized for node {node_id}")
    
    async def start(self, bootstrap_nodes: List[str] = None):
        """Start federation services"""
        self.running = True
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        
        # Set initial status
        self.local_node.status = NodeStatus.ACTIVE
        
        # Start background tasks
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._state_sync_task = asyncio.create_task(self._state_sync_loop())
        
        # Bootstrap federation
        if bootstrap_nodes:
            await self._bootstrap_from_nodes(bootstrap_nodes)
        else:
            # No bootstrap nodes, start election to become leader
            await self.leader_election.start_election()
        
        logging.info("Federation services started")
    
    async def stop(self):
        """Stop federation services"""
        self.running = False
        
        # Send leave message
        if self.nodes:
            leave_msg = FederationMessage(
                message_type=FederationMessageType.LEAVE,
                source_node=self.local_node.node_id,
                data={'reason': 'shutdown'}
            )
            await self.broadcast_message(leave_msg)
        
        # Cancel background tasks
        tasks = [self._discovery_task, self._health_check_task, self._state_sync_task]
        for task in tasks:
            if task:
                task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        logging.info("Federation services stopped")
    
    async def _bootstrap_from_nodes(self, bootstrap_nodes: List[str]):
        """Bootstrap federation by connecting to existing nodes"""
        for bootstrap_node in bootstrap_nodes:
            try:
                # Parse bootstrap node address
                if '://' not in bootstrap_node:
                    bootstrap_node = f"http://{bootstrap_node}"
                
                # Send discovery message
                discovery_msg = FederationMessage(
                    message_type=FederationMessageType.DISCOVERY,
                    source_node=self.local_node.node_id,
                    data=self.local_node.to_dict()
                )
                
                async with self.session.post(
                    f"{bootstrap_node}/api/v1/federation/message",
                    json=discovery_msg.to_dict()
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Process federation info
                        if 'nodes' in result:
                            for node_data in result['nodes']:
                                node = FederationNode.from_dict(node_data)
                                if node.node_id != self.local_node.node_id:
                                    self.nodes[node.node_id] = node
                        
                        # Update leader info
                        if 'leader' in result:
                            self.current_leader = result['leader']
                        
                        logging.info(f"Bootstrapped from {bootstrap_node}")
                        return  # Successfully bootstrapped
            
            except Exception as e:
                logging.warning(f"Failed to bootstrap from {bootstrap_node}: {e}")
        
        # If bootstrap failed, start election
        if not self.nodes:
            await self.leader_election.start_election()
    
    async def join_federation(self, target_node: str) -> bool:
        """Join an existing federation"""
        try:
            join_msg = FederationMessage(
                message_type=FederationMessageType.JOIN_REQUEST,
                source_node=self.local_node.node_id,
                data=self.local_node.to_dict()
            )
            
            async with self.session.post(
                f"{target_node}/api/v1/federation/message",
                json=join_msg.to_dict()
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get('accepted'):
                        # Update federation state
                        if 'nodes' in result:
                            for node_data in result['nodes']:
                                node = FederationNode.from_dict(node_data)
                                if node.node_id != self.local_node.node_id:
                                    self.nodes[node.node_id] = node
                        
                        if 'leader' in result:
                            self.current_leader = result['leader']
                        
                        logging.info(f"Successfully joined federation via {target_node}")
                        return True
                    else:
                        logging.warning(f"Join request rejected: {result.get('reason', 'unknown')}")
                
        except Exception as e:
            logging.error(f"Failed to join federation via {target_node}: {e}")
        
        return False
    
    async def handle_federation_message(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle incoming federation message"""
        try:
            if message.message_type == FederationMessageType.DISCOVERY:
                return await self._handle_discovery(message)
            
            elif message.message_type == FederationMessageType.JOIN_REQUEST:
                return await self._handle_join_request(message)
            
            elif message.message_type == FederationMessageType.HEARTBEAT:
                return await self._handle_heartbeat(message)
            
            elif message.message_type == FederationMessageType.LEADER_ELECTION:
                return await self._handle_leader_election(message)
            
            elif message.message_type == FederationMessageType.TASK_ASSIGN:
                return await self._handle_task_assignment(message)
            
            elif message.message_type == FederationMessageType.TASK_RESULT:
                return await self._handle_task_result(message)
            
            elif message.message_type == FederationMessageType.STATE_SYNC:
                return await self._handle_state_sync(message)
            
            else:
                logging.warning(f"Unknown federation message type: {message.message_type}")
                return {'error': 'Unknown message type'}
        
        except Exception as e:
            logging.error(f"Error handling federation message: {e}")
            return {'error': str(e)}
    
    async def _handle_discovery(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle discovery message"""
        source_node_data = message.data
        
        # Create or update node
        node = FederationNode.from_dict(source_node_data)
        node.last_seen = datetime.now()
        
        with self._lock:
            self.nodes[node.node_id] = node
        
        # Return federation info
        return {
            'nodes': [node.to_dict() for node in self.get_all_nodes()],
            'leader': self.current_leader
        }
    
    async def _handle_join_request(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle join request"""
        # Only leader can accept join requests
        if self.local_node.role != NodeRole.LEADER:
            return {
                'accepted': False,
                'reason': 'Not the leader',
                'leader': self.current_leader
            }
        
        source_node_data = message.data
        node = FederationNode.from_dict(source_node_data)
        node.last_seen = datetime.now()
        
        # Accept the node
        with self._lock:
            self.nodes[node.node_id] = node
        
        logging.info(f"Node {node.node_id} joined the federation")
        
        return {
            'accepted': True,
            'nodes': [node.to_dict() for node in self.get_all_nodes()],
            'leader': self.current_leader
        }
    
    async def _handle_heartbeat(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle heartbeat message"""
        source_node_id = message.source_node
        
        # Update node last seen
        with self._lock:
            if source_node_id in self.nodes:
                self.nodes[source_node_id].last_heartbeat = datetime.now()
                self.nodes[source_node_id].last_seen = datetime.now()
        
        # If this is from the leader, reset election timer
        if message.data.get('leader_id') == source_node_id:
            self.current_leader = source_node_id
        
        return {'status': 'ok'}
    
    async def _handle_leader_election(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle leader election message"""
        # Simplified vote granting logic
        term = message.data.get('term', 0)
        candidate_id = message.data.get('candidate_id')
        
        # Grant vote if we haven't voted in this term
        if (self.leader_election.current_term < term and 
            candidate_id and candidate_id != self.local_node.node_id):
            
            self.leader_election.current_term = term
            self.leader_election.voted_for = candidate_id
            
            return {'vote_granted': True, 'term': term}
        
        return {'vote_granted': False, 'term': self.leader_election.current_term}
    
    async def _handle_task_assignment(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle task assignment"""
        task_data = message.data
        task_id = task_data.get('task_id')
        task_type = task_data.get('task_type')
        
        try:
            # Execute task (this would integrate with actual task execution)
            result = await self._execute_local_task(task_type, task_data.get('task_data', {}))
            
            # Send result back
            result_msg = FederationMessage(
                message_type=FederationMessageType.TASK_RESULT,
                source_node=self.local_node.node_id,
                target_node=message.source_node,
                data={
                    'task_id': task_id,
                    'status': 'completed',
                    'result': result
                }
            )
            
            # Send result to source node
            source_node = self.nodes.get(message.source_node)
            if source_node:
                await self._send_message(source_node, result_msg)
            
            return {'status': 'accepted'}
        
        except Exception as e:
            logging.error(f"Task execution failed: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    async def _handle_task_result(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle task result"""
        task_id = message.data.get('task_id')
        result = message.data.get('result')
        
        await self.task_distributor.handle_task_result(task_id, message.data)
        
        return {'status': 'received'}
    
    async def _handle_state_sync(self, message: FederationMessage) -> Dict[str, Any]:
        """Handle state synchronization"""
        # This would integrate with StateManager for state sync
        return {'status': 'synced'}
    
    async def _execute_local_task(self, task_type: str, task_data: Dict[str, Any]) -> Any:
        """Execute task locally"""
        # This would integrate with actual task execution systems
        
        if task_type == "network_scan":
            # Would integrate with NetworkDiscovery
            return {'devices_found': 0, 'scan_completed': True}
        
        elif task_type == "health_check":
            # Would integrate with SystemMonitor
            return {'healthy': True, 'metrics': {}}
        
        elif task_type == "backup_create":
            # Would integrate with BackupManager
            return {'backup_id': str(uuid.uuid4()), 'size': 1024}
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def broadcast_message(self, message: FederationMessage):
        """Broadcast message to all nodes"""
        tasks = []
        
        for node in self.get_active_nodes():
            tasks.append(self._send_message(node, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_message(self, node: FederationNode, message: FederationMessage) -> Dict[str, Any]:
        """Send message to specific node"""
        try:
            async with self.session.post(
                f"{node.endpoint}/api/v1/federation/message",
                json=message.to_dict()
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    raise aiohttp.ClientError(f"HTTP {response.status}")
        
        except Exception as e:
            logging.error(f"Failed to send message to {node.node_id}: {e}")
            # Mark node as potentially failed
            node.status = NodeStatus.FAILED
            raise
    
    def get_active_nodes(self) -> List[FederationNode]:
        """Get list of active federation nodes"""
        with self._lock:
            return [node for node in self.nodes.values() 
                   if node.status == NodeStatus.ACTIVE]
    
    def get_all_nodes(self) -> List[FederationNode]:
        """Get all nodes including local node"""
        with self._lock:
            all_nodes = [self.local_node]
            all_nodes.extend(self.nodes.values())
            return all_nodes
    
    def is_leader(self) -> bool:
        """Check if this node is the leader"""
        return self.local_node.role == NodeRole.LEADER
    
    def get_federation_info(self) -> Dict[str, Any]:
        """Get federation status information"""
        with self._lock:
            return {
                'local_node': self.local_node.to_dict(),
                'nodes': [node.to_dict() for node in self.nodes.values()],
                'leader': self.current_leader,
                'total_nodes': len(self.nodes) + 1,
                'active_nodes': len(self.get_active_nodes()) + 1
            }
    
    async def _discovery_loop(self):
        """Background node discovery loop"""
        while self.running:
            try:
                # Clean up failed/timeout nodes
                now = datetime.now()
                timeout_threshold = now - timedelta(seconds=self.node_timeout)
                
                with self._lock:
                    failed_nodes = []
                    for node_id, node in self.nodes.items():
                        if node.last_seen < timeout_threshold:
                            failed_nodes.append(node_id)
                    
                    for node_id in failed_nodes:
                        logging.warning(f"Node {node_id} timed out, removing from federation")
                        del self.nodes[node_id]
                
                await asyncio.sleep(self.discovery_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Discovery loop error: {e}")
                await asyncio.sleep(self.discovery_interval)
    
    async def _health_check_loop(self):
        """Background health checking loop"""
        while self.running:
            try:
                # Update local node metrics
                # This would integrate with SystemMonitor
                self.local_node.load_metrics = {
                    'cpu_percent': 25.0,  # Would get from SystemMonitor
                    'memory_percent': 45.0,
                    'disk_percent': 30.0
                }
                
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _state_sync_loop(self):
        """Background state synchronization loop"""
        while self.running:
            try:
                # Sync state with other nodes (leader responsibility)
                if self.is_leader() and self.state_manager:
                    # This would sync state across federation
                    pass
                
                await asyncio.sleep(self.state_sync_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"State sync loop error: {e}")
                await asyncio.sleep(self.state_sync_interval)

def main():
    """Demo federation system"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        if not AIOHTTP_AVAILABLE:
            print("aiohttp library not available")
            return
        
        # Create federation manager
        federation = FederationManager(
            node_id="node_001",
            name="Demo Node 1",
            host="localhost",
            port=8080
        )
        
        await federation.start()
        
        print(f"Federation node started: {federation.local_node.node_id}")
        print(f"Role: {federation.local_node.role.value}")
        
        try:
            # Keep running
            while True:
                await asyncio.sleep(5)
                
                info = federation.get_federation_info()
                print(f"Federation info: {info['total_nodes']} nodes, leader: {info['leader']}")
        
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await federation.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()