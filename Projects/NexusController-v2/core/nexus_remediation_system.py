#!/usr/bin/env python3
"""
NexusController v2.0 Automated Remediation System
Intelligent automated remediation workflows for infrastructure issues
"""

import os
import sys
import json
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod
import uuid
from pathlib import Path

# Import core systems
from nexus_event_system import Event, EventType, EventBus
from nexus_monitoring_system import Alert, AlertSeverity

class RemediationTrigger(Enum):
    """Remediation trigger types"""
    ALERT = "alert"                    # Triggered by alert
    DRIFT = "drift"                    # Triggered by state drift
    SCHEDULE = "schedule"              # Scheduled remediation
    MANUAL = "manual"                  # Manually triggered
    THRESHOLD = "threshold"            # Threshold-based
    FAILURE = "failure"                # Failure recovery

class RemediationStatus(Enum):
    """Remediation execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK = "rollback"

class RemediationPriority(Enum):
    """Remediation priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(Enum):
    """Types of remediation actions"""
    # System actions
    RESTART_SERVICE = "restart_service"
    STOP_SERVICE = "stop_service"
    START_SERVICE = "start_service"
    KILL_PROCESS = "kill_process"
    CLEANUP_DISK = "cleanup_disk"
    CLEAR_CACHE = "clear_cache"
    
    # Network actions
    RESTART_NETWORK = "restart_network"
    RESET_CONNECTION = "reset_connection"
    UPDATE_FIREWALL = "update_firewall"
    FLUSH_DNS = "flush_dns"
    
    # Infrastructure actions
    SCALE_RESOURCE = "scale_resource"
    RESTART_INSTANCE = "restart_instance"
    FAILOVER = "failover"
    BACKUP_DATA = "backup_data"
    
    # Application actions
    RESTART_APPLICATION = "restart_application"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    CLEAR_LOGS = "clear_logs"
    UPDATE_CONFIG = "update_config"
    
    # Custom actions
    RUN_SCRIPT = "run_script"
    EXECUTE_COMMAND = "execute_command"
    SEND_NOTIFICATION = "send_notification"
    CUSTOM = "custom"

@dataclass
class RemediationAction:
    """Single remediation action definition"""
    
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.CUSTOM
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    retry_count: int = 3
    rollback_action: Optional['RemediationAction'] = None
    prerequisites: List[str] = field(default_factory=list)  # Action IDs that must complete first
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['action_type'] = self.action_type.value
        result['timeout'] = self.timeout.total_seconds()
        if self.rollback_action:
            result['rollback_action'] = self.rollback_action.to_dict()
        return result

@dataclass 
class RemediationWorkflow:
    """Complete remediation workflow definition"""
    
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    trigger_type: RemediationTrigger = RemediationTrigger.MANUAL
    priority: RemediationPriority = RemediationPriority.MEDIUM
    actions: List[RemediationAction] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)  # Conditions for execution
    cooldown: timedelta = field(default_factory=lambda: timedelta(minutes=30))
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    
    def can_execute(self) -> bool:
        """Check if workflow can be executed"""
        if not self.enabled:
            return False
        
        # Check cooldown
        if self.last_executed and self.cooldown:
            if datetime.now() - self.last_executed < self.cooldown:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['trigger_type'] = self.trigger_type.value
        result['priority'] = self.priority.value
        result['actions'] = [action.to_dict() for action in self.actions]
        result['cooldown'] = self.cooldown.total_seconds()
        result['created_at'] = self.created_at.isoformat()
        if self.last_executed:
            result['last_executed'] = self.last_executed.isoformat()
        return result

@dataclass
class RemediationExecution:
    """Remediation execution instance"""
    
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    workflow_name: str = ""
    trigger_type: RemediationTrigger = RemediationTrigger.MANUAL
    status: RemediationStatus = RemediationStatus.PENDING
    priority: RemediationPriority = RemediationPriority.MEDIUM
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration: Optional[timedelta] = None
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
    rollback_executed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['trigger_type'] = self.trigger_type.value
        result['status'] = self.status.value
        result['priority'] = self.priority.value
        result['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            result['completed_at'] = self.completed_at.isoformat()
        if self.duration:
            result['duration'] = self.duration.total_seconds()
        return result

class RemediationActionExecutor(ABC):
    """Abstract base class for action executors"""
    
    @abstractmethod
    async def execute(self, action: RemediationAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute remediation action
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        pass
    
    @abstractmethod
    def can_handle(self, action_type: ActionType) -> bool:
        """Check if executor can handle action type"""
        pass

class SystemActionExecutor(RemediationActionExecutor):
    """Executor for system-level actions"""
    
    def __init__(self):
        self.supported_actions = {
            ActionType.RESTART_SERVICE,
            ActionType.STOP_SERVICE,
            ActionType.START_SERVICE,
            ActionType.KILL_PROCESS,
            ActionType.CLEANUP_DISK,
            ActionType.CLEAR_CACHE
        }
    
    async def execute(self, action: RemediationAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute system action"""
        try:
            if action.action_type == ActionType.RESTART_SERVICE:
                return await self._restart_service(action.parameters)
            elif action.action_type == ActionType.STOP_SERVICE:
                return await self._stop_service(action.parameters)
            elif action.action_type == ActionType.START_SERVICE:
                return await self._start_service(action.parameters)
            elif action.action_type == ActionType.KILL_PROCESS:
                return await self._kill_process(action.parameters)
            elif action.action_type == ActionType.CLEANUP_DISK:
                return await self._cleanup_disk(action.parameters)
            elif action.action_type == ActionType.CLEAR_CACHE:
                return await self._clear_cache(action.parameters)
            else:
                return False, f"Unsupported action type: {action.action_type}"
                
        except Exception as e:
            return False, f"System action failed: {str(e)}"
    
    def can_handle(self, action_type: ActionType) -> bool:
        """Check if can handle action type"""
        return action_type in self.supported_actions
    
    async def _restart_service(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Restart system service"""
        service_name = params.get('service_name')
        if not service_name:
            return False, "Service name not specified"
        
        # Mock implementation - would use systemctl or service command
        logging.info(f"Restarting service: {service_name}")
        await asyncio.sleep(2)  # Simulate service restart time
        
        return True, f"Service {service_name} restarted successfully"
    
    async def _stop_service(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Stop system service"""
        service_name = params.get('service_name')
        if not service_name:
            return False, "Service name not specified"
        
        logging.info(f"Stopping service: {service_name}")
        await asyncio.sleep(1)
        
        return True, f"Service {service_name} stopped successfully"
    
    async def _start_service(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Start system service"""
        service_name = params.get('service_name')
        if not service_name:
            return False, "Service name not specified"
        
        logging.info(f"Starting service: {service_name}")
        await asyncio.sleep(1)
        
        return True, f"Service {service_name} started successfully"
    
    async def _kill_process(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Kill process by PID or name"""
        pid = params.get('pid')
        process_name = params.get('process_name')
        
        if not pid and not process_name:
            return False, "PID or process name must be specified"
        
        target = pid if pid else process_name
        logging.info(f"Killing process: {target}")
        await asyncio.sleep(0.5)
        
        return True, f"Process {target} terminated successfully"
    
    async def _cleanup_disk(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Clean up disk space"""
        path = params.get('path', '/tmp')
        max_age_days = params.get('max_age_days', 7)
        
        logging.info(f"Cleaning up disk space in {path} (files older than {max_age_days} days)")
        await asyncio.sleep(3)  # Simulate cleanup time
        
        # Mock cleanup result
        cleaned_mb = 150
        return True, f"Cleaned up {cleaned_mb}MB of disk space in {path}"
    
    async def _clear_cache(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Clear system cache"""
        cache_type = params.get('cache_type', 'system')
        
        logging.info(f"Clearing {cache_type} cache")
        await asyncio.sleep(1)
        
        return True, f"{cache_type.title()} cache cleared successfully"

class NetworkActionExecutor(RemediationActionExecutor):
    """Executor for network-related actions"""
    
    def __init__(self):
        self.supported_actions = {
            ActionType.RESTART_NETWORK,
            ActionType.RESET_CONNECTION,
            ActionType.UPDATE_FIREWALL,
            ActionType.FLUSH_DNS
        }
    
    async def execute(self, action: RemediationAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute network action"""
        try:
            if action.action_type == ActionType.RESTART_NETWORK:
                return await self._restart_network(action.parameters)
            elif action.action_type == ActionType.RESET_CONNECTION:
                return await self._reset_connection(action.parameters)
            elif action.action_type == ActionType.UPDATE_FIREWALL:
                return await self._update_firewall(action.parameters)
            elif action.action_type == ActionType.FLUSH_DNS:
                return await self._flush_dns(action.parameters)
            else:
                return False, f"Unsupported action type: {action.action_type}"
                
        except Exception as e:
            return False, f"Network action failed: {str(e)}"
    
    def can_handle(self, action_type: ActionType) -> bool:
        """Check if can handle action type"""
        return action_type in self.supported_actions
    
    async def _restart_network(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Restart network interface"""
        interface = params.get('interface', 'eth0')
        
        logging.info(f"Restarting network interface: {interface}")
        await asyncio.sleep(5)  # Network restart takes time
        
        return True, f"Network interface {interface} restarted successfully"
    
    async def _reset_connection(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Reset network connection"""
        connection_id = params.get('connection_id')
        if not connection_id:
            return False, "Connection ID not specified"
        
        logging.info(f"Resetting connection: {connection_id}")
        await asyncio.sleep(2)
        
        return True, f"Connection {connection_id} reset successfully"
    
    async def _update_firewall(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Update firewall rules"""
        rule = params.get('rule')
        action = params.get('action', 'add')  # add, remove, update
        
        if not rule:
            return False, "Firewall rule not specified"
        
        logging.info(f"Updating firewall: {action} rule {rule}")
        await asyncio.sleep(1)
        
        return True, f"Firewall rule {action}ed successfully"
    
    async def _flush_dns(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Flush DNS cache"""
        logging.info("Flushing DNS cache")
        await asyncio.sleep(1)
        
        return True, "DNS cache flushed successfully"

class ApplicationActionExecutor(RemediationActionExecutor):
    """Executor for application-level actions"""
    
    def __init__(self):
        self.supported_actions = {
            ActionType.RESTART_APPLICATION,
            ActionType.ROLLBACK_DEPLOYMENT,
            ActionType.CLEAR_LOGS,
            ActionType.UPDATE_CONFIG
        }
    
    async def execute(self, action: RemediationAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute application action"""
        try:
            if action.action_type == ActionType.RESTART_APPLICATION:
                return await self._restart_application(action.parameters)
            elif action.action_type == ActionType.ROLLBACK_DEPLOYMENT:
                return await self._rollback_deployment(action.parameters)
            elif action.action_type == ActionType.CLEAR_LOGS:
                return await self._clear_logs(action.parameters)
            elif action.action_type == ActionType.UPDATE_CONFIG:
                return await self._update_config(action.parameters)
            else:
                return False, f"Unsupported action type: {action.action_type}"
                
        except Exception as e:
            return False, f"Application action failed: {str(e)}"
    
    def can_handle(self, action_type: ActionType) -> bool:
        """Check if can handle action type"""
        return action_type in self.supported_actions
    
    async def _restart_application(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Restart application"""
        app_name = params.get('application_name')
        if not app_name:
            return False, "Application name not specified"
        
        logging.info(f"Restarting application: {app_name}")
        await asyncio.sleep(3)
        
        return True, f"Application {app_name} restarted successfully"
    
    async def _rollback_deployment(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Rollback deployment"""
        app_name = params.get('application_name')
        version = params.get('version', 'previous')
        
        if not app_name:
            return False, "Application name not specified"
        
        logging.info(f"Rolling back {app_name} to {version}")
        await asyncio.sleep(5)
        
        return True, f"Application {app_name} rolled back to {version}"
    
    async def _clear_logs(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Clear application logs"""
        log_path = params.get('log_path')
        max_age_days = params.get('max_age_days', 30)
        
        if not log_path:
            return False, "Log path not specified"
        
        logging.info(f"Clearing logs in {log_path} older than {max_age_days} days")
        await asyncio.sleep(2)
        
        return True, f"Logs cleared from {log_path}"
    
    async def _update_config(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Update application configuration"""
        config_file = params.get('config_file')
        changes = params.get('changes', {})
        
        if not config_file:
            return False, "Config file not specified"
        
        logging.info(f"Updating configuration: {config_file}")
        await asyncio.sleep(1)
        
        return True, f"Configuration updated: {config_file}"

class CustomActionExecutor(RemediationActionExecutor):
    """Executor for custom actions"""
    
    def __init__(self):
        self.supported_actions = {
            ActionType.RUN_SCRIPT,
            ActionType.EXECUTE_COMMAND,
            ActionType.SEND_NOTIFICATION,
            ActionType.CUSTOM
        }
    
    async def execute(self, action: RemediationAction, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute custom action"""
        try:
            if action.action_type == ActionType.RUN_SCRIPT:
                return await self._run_script(action.parameters)
            elif action.action_type == ActionType.EXECUTE_COMMAND:
                return await self._execute_command(action.parameters)
            elif action.action_type == ActionType.SEND_NOTIFICATION:
                return await self._send_notification(action.parameters)
            elif action.action_type == ActionType.CUSTOM:
                return await self._execute_custom(action.parameters, context)
            else:
                return False, f"Unsupported action type: {action.action_type}"
                
        except Exception as e:
            return False, f"Custom action failed: {str(e)}"
    
    def can_handle(self, action_type: ActionType) -> bool:
        """Check if can handle action type"""
        return action_type in self.supported_actions
    
    async def _run_script(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Run script"""
        script_path = params.get('script_path')
        args = params.get('args', [])
        
        if not script_path:
            return False, "Script path not specified"
        
        logging.info(f"Running script: {script_path} {' '.join(args)}")
        await asyncio.sleep(2)
        
        # Mock execution result
        return True, f"Script {script_path} executed successfully"
    
    async def _execute_command(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute shell command"""
        command = params.get('command')
        
        if not command:
            return False, "Command not specified"
        
        logging.info(f"Executing command: {command}")
        await asyncio.sleep(1)
        
        # Mock execution result
        return True, f"Command executed successfully: {command}"
    
    async def _send_notification(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Send notification"""
        message = params.get('message', 'Remediation notification')
        recipient = params.get('recipient', 'admin')
        
        logging.info(f"Sending notification to {recipient}: {message}")
        await asyncio.sleep(0.5)
        
        return True, f"Notification sent to {recipient}"
    
    async def _execute_custom(self, params: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str]:
        """Execute custom logic"""
        custom_type = params.get('custom_type', 'unknown')
        
        logging.info(f"Executing custom action: {custom_type}")
        await asyncio.sleep(1)
        
        return True, f"Custom action {custom_type} completed"

class RemediationEngine:
    """Core remediation execution engine"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus
        self.workflows: Dict[str, RemediationWorkflow] = {}
        self.executions: Dict[str, RemediationExecution] = {}
        self.execution_history = []
        self.executors: List[RemediationActionExecutor] = []
        self._running = False
        self._execution_queue = asyncio.Queue()
        self._worker_tasks = []
        self._lock = threading.RLock()
        
        # Setup default executors
        self._setup_executors()
        
        # Configuration
        self.max_concurrent_executions = 5
        self.execution_timeout = timedelta(hours=1)
        
        logging.info("RemediationEngine initialized")
    
    def _setup_executors(self):
        """Setup default action executors"""
        self.executors = [
            SystemActionExecutor(),
            NetworkActionExecutor(),
            ApplicationActionExecutor(),
            CustomActionExecutor()
        ]
    
    async def start(self):
        """Start remediation engine"""
        self._running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent_executions):
            task = asyncio.create_task(self._execution_worker(f"worker_{i}"))
            self._worker_tasks.append(task)
        
        logging.info("RemediationEngine started")
    
    async def stop(self):
        """Stop remediation engine"""
        self._running = False
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        logging.info("RemediationEngine stopped")
    
    def add_workflow(self, workflow: RemediationWorkflow):
        """Add remediation workflow"""
        with self._lock:
            self.workflows[workflow.workflow_id] = workflow
        logging.info(f"Remediation workflow added: {workflow.name}")
    
    def remove_workflow(self, workflow_id: str):
        """Remove remediation workflow"""
        with self._lock:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
                logging.info(f"Remediation workflow removed: {workflow_id}")
    
    async def execute_workflow(self, workflow_id: str, trigger_type: RemediationTrigger,
                             trigger_data: Dict[str, Any] = None) -> Optional[str]:
        """Execute remediation workflow
        
        Returns execution ID if started, None if not executed
        """
        with self._lock:
            if workflow_id not in self.workflows:
                logging.error(f"Workflow not found: {workflow_id}")
                return None
            
            workflow = self.workflows[workflow_id]
            
            if not workflow.can_execute():
                logging.info(f"Workflow cannot execute: {workflow.name}")
                return None
            
            # Create execution
            execution = RemediationExecution(
                workflow_id=workflow_id,
                workflow_name=workflow.name,
                trigger_type=trigger_type,
                priority=workflow.priority,
                trigger_data=trigger_data or {}
            )
            
            self.executions[execution.execution_id] = execution
            workflow.last_executed = datetime.now()
            
            # Queue for execution
            await self._execution_queue.put(execution.execution_id)
            
            logging.info(f"Queued workflow execution: {workflow.name} ({execution.execution_id})")
            return execution.execution_id
    
    async def _execution_worker(self, worker_name: str):
        """Background worker for executing remediation workflows"""
        while self._running:
            try:
                # Get next execution
                execution_id = await asyncio.wait_for(
                    self._execution_queue.get(),
                    timeout=1.0
                )
                
                await self._execute_workflow_instance(execution_id)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Execution worker {worker_name} error: {e}")
    
    async def _execute_workflow_instance(self, execution_id: str):
        """Execute specific workflow instance"""
        try:
            with self._lock:
                if execution_id not in self.executions:
                    logging.error(f"Execution not found: {execution_id}")
                    return
                
                execution = self.executions[execution_id]
                workflow = self.workflows.get(execution.workflow_id)
                
                if not workflow:
                    execution.status = RemediationStatus.FAILED
                    execution.error_message = "Workflow not found"
                    return
            
            # Update execution status
            execution.status = RemediationStatus.RUNNING
            
            # Emit start event
            if self.event_bus:
                event = Event(
                    event_type=EventType.INFRA_REMEDIATION_STARTED,
                    source="nexus.remediation_engine",
                    data={
                        'execution_id': execution_id,
                        'workflow_name': workflow.name,
                        'trigger_type': execution.trigger_type.value,
                        'priority': execution.priority.value
                    }
                )
                await self.event_bus.publish(event)
            
            logging.info(f"Starting workflow execution: {workflow.name}")
            
            # Execute actions
            success = await self._execute_actions(workflow.actions, execution)
            
            # Update execution status
            execution.completed_at = datetime.now()
            execution.duration = execution.completed_at - execution.started_at
            
            if success:
                execution.status = RemediationStatus.COMPLETED
                workflow.success_count += 1
                logging.info(f"Workflow execution completed: {workflow.name}")
            else:
                execution.status = RemediationStatus.FAILED
                workflow.failure_count += 1
                
                # Attempt rollback if failed
                if not execution.rollback_executed:
                    await self._execute_rollback(workflow.actions, execution)
                
                logging.error(f"Workflow execution failed: {workflow.name}")
            
            # Move to history and cleanup
            self.execution_history.append(execution)
            with self._lock:
                if execution_id in self.executions:
                    del self.executions[execution_id]
            
            # Emit completion event
            if self.event_bus:
                event = Event(
                    event_type=EventType.INFRA_REMEDIATION_COMPLETED,
                    source="nexus.remediation_engine",
                    data={
                        'execution_id': execution_id,
                        'workflow_name': workflow.name,
                        'status': execution.status.value,
                        'duration_seconds': execution.duration.total_seconds() if execution.duration else 0,
                        'success': success
                    }
                )
                await self.event_bus.publish(event)
            
        except Exception as e:
            logging.error(f"Workflow execution error: {e}")
            
            # Update execution with error
            with self._lock:
                if execution_id in self.executions:
                    execution = self.executions[execution_id]
                    execution.status = RemediationStatus.FAILED
                    execution.error_message = str(e)
                    execution.completed_at = datetime.now()
    
    async def _execute_actions(self, actions: List[RemediationAction], 
                             execution: RemediationExecution) -> bool:
        """Execute list of actions"""
        try:
            context = {
                'execution_id': execution.execution_id,
                'workflow_id': execution.workflow_id,
                'trigger_data': execution.trigger_data
            }
            
            for action in actions:
                # Check prerequisites
                if not await self._check_prerequisites(action, execution):
                    execution.error_message = f"Prerequisites not met for action: {action.name}"
                    return False
                
                # Find executor
                executor = self._find_executor(action.action_type)
                if not executor:
                    execution.error_message = f"No executor found for action type: {action.action_type}"
                    return False
                
                # Execute action with retries
                success = False
                last_error = ""
                
                for attempt in range(action.retry_count + 1):
                    try:
                        # Execute with timeout
                        success, message = await asyncio.wait_for(
                            executor.execute(action, context),
                            timeout=action.timeout.total_seconds()
                        )
                        
                        # Record result
                        result = {
                            'action_id': action.action_id,
                            'action_name': action.name,
                            'action_type': action.action_type.value,
                            'attempt': attempt + 1,
                            'success': success,
                            'message': message,
                            'timestamp': datetime.now().isoformat()
                        }
                        execution.action_results.append(result)
                        
                        if success:
                            logging.info(f"Action completed: {action.name} - {message}")
                            break
                        else:
                            last_error = message
                            logging.warning(f"Action failed (attempt {attempt + 1}): {action.name} - {message}")
                            
                            if attempt < action.retry_count:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
                    except asyncio.TimeoutError:
                        last_error = f"Action timed out after {action.timeout.total_seconds()} seconds"
                        logging.error(f"Action timeout: {action.name}")
                    except Exception as e:
                        last_error = str(e)
                        logging.error(f"Action execution error: {action.name} - {e}")
                
                if not success:
                    execution.error_message = f"Action failed: {action.name} - {last_error}"
                    return False
            
            return True
            
        except Exception as e:
            execution.error_message = f"Action execution error: {str(e)}"
            return False
    
    async def _check_prerequisites(self, action: RemediationAction, 
                                 execution: RemediationExecution) -> bool:
        """Check if action prerequisites are met"""
        if not action.prerequisites:
            return True
        
        # Check if prerequisite actions completed successfully
        for prereq_id in action.prerequisites:
            found = False
            for result in execution.action_results:
                if result['action_id'] == prereq_id and result['success']:
                    found = True
                    break
            
            if not found:
                return False
        
        return True
    
    def _find_executor(self, action_type: ActionType) -> Optional[RemediationActionExecutor]:
        """Find executor for action type"""
        for executor in self.executors:
            if executor.can_handle(action_type):
                return executor
        return None
    
    async def _execute_rollback(self, actions: List[RemediationAction],
                              execution: RemediationExecution):
        """Execute rollback actions"""
        try:
            rollback_actions = []
            
            # Collect rollback actions in reverse order
            for action in reversed(actions):
                if action.rollback_action:
                    rollback_actions.append(action.rollback_action)
            
            if rollback_actions:
                logging.info(f"Executing rollback for {len(rollback_actions)} actions")
                execution.rollback_executed = True
                
                context = {
                    'execution_id': execution.execution_id,
                    'workflow_id': execution.workflow_id,
                    'rollback': True
                }
                
                for rollback_action in rollback_actions:
                    executor = self._find_executor(rollback_action.action_type)
                    if executor:
                        try:
                            success, message = await executor.execute(rollback_action, context)
                            
                            result = {
                                'action_id': rollback_action.action_id,
                                'action_name': f"Rollback: {rollback_action.name}",
                                'action_type': rollback_action.action_type.value,
                                'success': success,
                                'message': message,
                                'timestamp': datetime.now().isoformat(),
                                'rollback': True
                            }
                            execution.action_results.append(result)
                            
                            if success:
                                logging.info(f"Rollback completed: {rollback_action.name}")
                            else:
                                logging.error(f"Rollback failed: {rollback_action.name} - {message}")
                                
                        except Exception as e:
                            logging.error(f"Rollback error: {rollback_action.name} - {e}")
        
        except Exception as e:
            logging.error(f"Rollback execution error: {e}")
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow statistics"""
        with self._lock:
            stats = {
                'total_workflows': len(self.workflows),
                'enabled_workflows': sum(1 for w in self.workflows.values() if w.enabled),
                'active_executions': len(self.executions),
                'total_executions': len(self.execution_history),
                'workflow_stats': {}
            }
            
            for workflow in self.workflows.values():
                stats['workflow_stats'][workflow.name] = {
                    'success_count': workflow.success_count,
                    'failure_count': workflow.failure_count,
                    'last_executed': workflow.last_executed.isoformat() if workflow.last_executed else None,
                    'enabled': workflow.enabled
                }
            
            return stats
    
    def get_execution_history(self, limit: int = 50) -> List[RemediationExecution]:
        """Get execution history"""
        return self.execution_history[-limit:]

class RemediationSystem:
    """Complete automated remediation system"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus
        self.engine = RemediationEngine(event_bus)
        self._running = False
        
        # Setup default workflows
        self._setup_default_workflows()
        
        logging.info("RemediationSystem initialized")
    
    def _setup_default_workflows(self):
        """Setup default remediation workflows"""
        
        # High CPU remediation
        high_cpu_workflow = RemediationWorkflow(
            name="High CPU Remediation",
            description="Remediate high CPU usage",
            trigger_type=RemediationTrigger.ALERT,
            priority=RemediationPriority.HIGH,
            actions=[
                RemediationAction(
                    action_type=ActionType.CLEAR_CACHE,
                    name="Clear System Cache",
                    description="Clear system cache to free up CPU",
                    parameters={'cache_type': 'system'}
                ),
                RemediationAction(
                    action_type=ActionType.RESTART_SERVICE,
                    name="Restart High CPU Service",
                    description="Restart service consuming high CPU",
                    parameters={'service_name': 'high-cpu-service'}
                )
            ]
        )
        self.engine.add_workflow(high_cpu_workflow)
        
        # Disk space remediation
        disk_space_workflow = RemediationWorkflow(
            name="Disk Space Remediation",
            description="Free up disk space when usage is high",
            trigger_type=RemediationTrigger.ALERT,
            priority=RemediationPriority.MEDIUM,
            actions=[
                RemediationAction(
                    action_type=ActionType.CLEAR_LOGS,
                    name="Clear Old Logs",
                    description="Clear old log files",
                    parameters={'log_path': '/var/log', 'max_age_days': 30}
                ),
                RemediationAction(
                    action_type=ActionType.CLEANUP_DISK,
                    name="Clean Temporary Files",
                    description="Clean temporary files",
                    parameters={'path': '/tmp', 'max_age_days': 7}
                )
            ]
        )
        self.engine.add_workflow(disk_space_workflow)
        
        # Network connectivity remediation
        network_workflow = RemediationWorkflow(
            name="Network Connectivity Remediation",
            description="Restore network connectivity",
            trigger_type=RemediationTrigger.ALERT,
            priority=RemediationPriority.CRITICAL,
            actions=[
                RemediationAction(
                    action_type=ActionType.FLUSH_DNS,
                    name="Flush DNS Cache",
                    description="Clear DNS cache",
                    parameters={}
                ),
                RemediationAction(
                    action_type=ActionType.RESTART_NETWORK,
                    name="Restart Network Interface",
                    description="Restart primary network interface",
                    parameters={'interface': 'eth0'}
                )
            ]
        )
        self.engine.add_workflow(network_workflow)
    
    async def start(self):
        """Start remediation system"""
        self._running = True
        await self.engine.start()
        logging.info("RemediationSystem started")
    
    async def stop(self):
        """Stop remediation system"""
        self._running = False
        await self.engine.stop()
        logging.info("RemediationSystem stopped")
    
    async def handle_alert(self, alert: Alert):
        """Handle alert by triggering appropriate remediation"""
        try:
            # Map alert rules to workflows
            workflow_mapping = {
                'high_cpu': 'High CPU Remediation',
                'high_disk': 'Disk Space Remediation',
                'no_devices_online': 'Network Connectivity Remediation'
            }
            
            workflow_name = workflow_mapping.get(alert.rule_id)
            if not workflow_name:
                logging.info(f"No remediation workflow for alert: {alert.rule_name}")
                return
            
            # Find workflow by name
            workflow_id = None
            for wf_id, workflow in self.engine.workflows.items():
                if workflow.name == workflow_name:
                    workflow_id = wf_id
                    break
            
            if not workflow_id:
                logging.error(f"Remediation workflow not found: {workflow_name}")
                return
            
            # Execute workflow
            execution_id = await self.engine.execute_workflow(
                workflow_id,
                RemediationTrigger.ALERT,
                {
                    'alert_id': alert.alert_id,
                    'alert_rule': alert.rule_name,
                    'alert_severity': alert.severity.value,
                    'alert_value': alert.value
                }
            )
            
            if execution_id:
                logging.info(f"Triggered remediation for alert {alert.rule_name}: {execution_id}")
            else:
                logging.info(f"Remediation not triggered for alert {alert.rule_name} (cooldown or disabled)")
                
        except Exception as e:
            logging.error(f"Failed to handle alert remediation: {e}")
    
    def add_custom_workflow(self, workflow: RemediationWorkflow):
        """Add custom remediation workflow"""
        self.engine.add_workflow(workflow)
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get remediation system overview"""
        return {
            'engine_running': self._running,
            'workflow_stats': self.engine.get_workflow_stats(),
            'recent_executions': [
                execution.to_dict() 
                for execution in self.engine.get_execution_history(10)
            ]
        }

def main():
    """Demo of remediation system"""
    logging.basicConfig(level=logging.INFO)
    
    async def demo():
        # Create remediation system
        remediation_system = RemediationSystem()
        await remediation_system.start()
        
        print("Remediation system started")
        
        # Create a mock alert to trigger remediation
        from nexus_monitoring_system import Alert, AlertSeverity, AlertState
        
        mock_alert = Alert(
            rule_id="high_cpu",
            rule_name="High CPU Usage",
            metric_name="cpu_percent",
            severity=AlertSeverity.HIGH,
            state=AlertState.FIRING,
            message="CPU usage is above 80% (current: 95.2%)",
            value=95.2,
            threshold="> 80"
        )
        
        print(f"Triggering remediation for alert: {mock_alert.rule_name}")
        
        # Handle alert
        await remediation_system.handle_alert(mock_alert)
        
        # Wait for execution to complete
        await asyncio.sleep(10)
        
        # Get system overview
        overview = remediation_system.get_system_overview()
        print(f"\nRemediation System Overview:")
        print(f"  Engine running: {overview['engine_running']}")
        print(f"  Total workflows: {overview['workflow_stats']['total_workflows']}")
        print(f"  Active executions: {overview['workflow_stats']['active_executions']}")
        print(f"  Total executions: {overview['workflow_stats']['total_executions']}")
        
        # Show recent executions
        if overview['recent_executions']:
            print(f"\nRecent Executions:")
            for execution in overview['recent_executions']:
                print(f"  {execution['workflow_name']}: {execution['status']} ({execution.get('duration', 0):.1f}s)")
        
        await remediation_system.stop()
    
    asyncio.run(demo())

if __name__ == "__main__":
    main()