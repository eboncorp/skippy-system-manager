# Complete Home Cloud Setup Guide - Part 31

## Part 10.26: Alert Escalation System

### Escalation Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
from collections import defaultdict
from typing import Dict, List, Any, Optional
from enum import Enum
import yaml
import aiohttp
from dataclasses import dataclass

class EscalationLevel(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    MANAGER = "manager"
    EXECUTIVE = "executive"

class ResponseStatus(Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

@dataclass
class EscalationPolicy:
    id: str
    name: str
    levels: List[Dict]
    repeat_interval: int
    max_repeats: int
    sla_timeout: int

class EscalationManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=24)
        self.load_config()
        self.setup_escalation_tracking()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/escalation_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        """Load escalation configuration"""
        self.config = {
            'escalation': {
                'policies': {
                    'critical': {
                        'levels': [
                            {
                                'level': 'primary',
                                'delay': 0,
                                'notification_channels': ['email', 'slack', 'sms'],
                                'responders': ['oncall_primary'],
                                'timeout': 300  # 5 minutes
                            },
                            {
                                'level': 'secondary',
                                'delay': 600,  # 10 minutes
                                'notification_channels': ['email', 'slack', 'sms', 'phone'],
                                'responders': ['oncall_secondary'],
                                'timeout': 600  # 10 minutes
                            },
                            {
                                'level': 'manager',
                                'delay': 1800,  # 30 minutes
                                'notification_channels': ['email', 'slack', 'sms', 'phone'],
                                'responders': ['team_manager'],
                                'timeout': 1800  # 30 minutes
                            },
                            {
                                'level': 'executive',
                                'delay': 3600,  # 1 hour
                                'notification_channels': ['email', 'slack', 'sms', 'phone'],
                                'responders': ['director', 'vp'],
                                'timeout': 3600  # 1 hour
                            }
                        ],
                        'repeat_interval': 7200,  # 2 hours
                        'max_repeats': 3,
                        'sla_timeout': 3600  # 1 hour
                    },
                    'high': {
                        'levels': [
                            {
                                'level': 'primary',
                                'delay': 0,
                                'notification_channels': ['email', 'slack'],
                                'responders': ['oncall_primary'],
                                'timeout': 900  # 15 minutes
                            },
                            {
                                'level': 'secondary',
                                'delay': 1800,  # 30 minutes
                                'notification_channels': ['email', 'slack', 'sms'],
                                'responders': ['oncall_secondary'],
                                'timeout': 1800  # 30 minutes
                            },
                            {
                                'level': 'manager',
                                'delay': 3600,  # 1 hour
                                'notification_channels': ['email', 'slack', 'sms'],
                                'responders': ['team_manager'],
                                'timeout': 3600  # 1 hour
                            }
                        ],
                        'repeat_interval': 14400,  # 4 hours
                        'max_repeats': 2,
                        'sla_timeout': 7200  # 2 hours
                    },
                    'medium': {
                        'levels': [
                            {
                                'level': 'primary',
                                'delay': 0,
                                'notification_channels': ['email', 'slack'],
                                'responders': ['oncall_primary'],
                                'timeout': 3600  # 1 hour
                            },
                            {
                                'level': 'secondary',
                                'delay': 7200,  # 2 hours
                                'notification_channels': ['email', 'slack'],
                                'responders': ['oncall_secondary'],
                                'timeout': 7200  # 2 hours
                            }
                        ],
                        'repeat_interval': 28800,  # 8 hours
                        'max_repeats': 1,
                        'sla_timeout': 14400  # 4 hours
                    }
                }
            },
            'rotations': {
                'oncall_primary': {
                    'type': 'weekly',
                    'members': ['user1', 'user2', 'user3'],
                    'start_time': '09:00',
                    'handoff_day': 'monday'
                },
                'oncall_secondary': {
                    'type': 'weekly',
                    'members': ['user4', 'user5', 'user6'],
                    'start_time': '09:00',
                    'handoff_day': 'monday'
                }
            },
            'response_tracking': {
                'acknowledgment_timeout': 300,  # 5 minutes
                'resolution_reminders': {
                    'interval': 1800,  # 30 minutes
                    'max_reminders': 3
                },
                'sla_monitoring': {
                    'enabled': True,
                    'warning_threshold': 0.8,  # 80% of SLA
                    'notification_channels': ['email', 'slack']
                }
            },
            'reporting': {
                'metrics_interval': 3600,  # 1 hour
                'daily_summary': {
                    'enabled': True,
                    'time': '00:00',
                    'recipients': ['manager@example.com']
                },
                'weekly_report': {
                    'enabled': True,
                    'day': 'monday',
                    'time': '09:00',
                    'recipients': ['director@example.com']
                }
            }
        }
        
    def setup_escalation_tracking(self):
        """Initialize escalation tracking"""
        self.active_escalations = defaultdict(dict)
        self.escalation_history = defaultdict(list)
        self.response_tracking = defaultdict(dict)
        self.sla_tracking = defaultdict(dict)
    
    async def start_escalation(self, alert: Dict) -> bool:
        """Start escalation process for alert"""
        try:
            # Get escalation policy
            policy = self.get_escalation_policy(alert)
            if not policy:
                logging.error(f"No escalation policy found for alert {alert['id']}")
                return False
            
            # Initialize escalation
            escalation = {
                'alert_id': alert['id'],
                'policy_id': policy.id,
                'current_level': 0,
                'started_at': datetime.now().isoformat(),
                'current_level_started_at': datetime.now().isoformat(),
                'repeat_count': 0,
                'status': ResponseStatus.PENDING.value
            }
            
            # Store escalation
            await self.store_escalation(escalation)
            
            # Start first level
            await self.execute_escalation_level(escalation, policy.levels[0])
            
            return True
            
        except Exception as e:
            logging.error(f"Error starting escalation: {str(e)}")
            return False
    
    def get_escalation_policy(self, alert: Dict) -> Optional[EscalationPolicy]:
        """Get appropriate escalation policy for alert"""
        try:
            # Determine policy based on alert severity
            severity = alert.get('severity', 'medium').lower()
            if severity in self.config['escalation']['policies']:
                policy_config = self.config['escalation']['policies'][severity]
                return EscalationPolicy(
                    id=f"policy_{severity}",
                    name=f"{severity.capitalize()} Severity Policy",
                    levels=policy_config['levels'],
                    repeat_interval=policy_config['repeat_interval'],
                    max_repeats=policy_config['max_repeats'],
                    sla_timeout=policy_config['sla_timeout']
                )
            return None
            
        except Exception as e:
            logging.error(f"Error getting escalation policy: {str(e)}")
            return None
    
    async def store_escalation(self, escalation: Dict):
        """Store escalation details"""
        try:
            # Store in Redis
            self.redis.hset(
                f"escalation:{escalation['alert_id']}",
                mapping=escalation
            )
            
            # Update tracking
            self.active_escalations[escalation['alert_id']] = escalation
            
            # Add to history
            self.escalation_history[escalation['alert_id']].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'start_escalation',
                'details': escalation
            })
            
        except Exception as e:
            logging.error(f"Error storing escalation: {str(e)}")
    
    async def execute_escalation_level(self, escalation: Dict, level: Dict):
        """Execute escalation level actions"""
        try:
            # Get responders for level
            responders = await self.get_level_responders(level)
            
            # Send notifications
            for responder in responders:
                for channel in level['notification_channels']:
                    await self.send_escalation_notification(
                        escalation,
                        level,
                        responder,
                        channel
                    )
            
            # Update escalation status
            escalation['current_level_started_at'] = datetime.now().isoformat()
            await self.store_escalation(escalation)
            
            # Start timeout timer
            asyncio.create_task(
                self.monitor_level_timeout(
                    escalation['alert_id'],
                    level['timeout']
                )
            )
            
        except Exception as e:
            logging.error(f"Error executing escalation level: {str(e)}")
    
    async def get_level_responders(self, level: Dict) -> List[str]:
        """Get responders for escalation level"""
        try:
            responders = []
            for responder_group in level['responders']:
                if responder_group in self.config['rotations']:
                    # Handle rotation-based responders
                    rotation = self.config['rotations'][responder_group]
                    current_responder = await self.get_current_rotation_member(rotation)
                    if current_responder:
                        responders.append(current_responder)
                else:
                    # Static responder
                    responders.append(responder_group)
            
            return responders
            
        except Exception as e:
            logging.error(f"Error getting level responders: {str(e)}")
            return []
    
    async def get_current_rotation_member(self, rotation: Dict) -> Optional[str]:
        """Get current on-call member from rotation"""
        try:
            # Calculate current rotation position
            now = datetime.now()
            start_of_week = now - timedelta(days=now.weekday())
            weeks_elapsed = (now - start_of_week).days // 7
            
            # Get current member
            position = weeks_elapsed % len(rotation['members'])
            return rotation['members'][position]
            
        except Exception as e:
            logging.error(f"Error getting rotation member: {str(e)}")
            return None
    
    async def monitor_level_timeout(self, alert_id: str, timeout: int):
        """Monitor response timeout for escalation level"""
        try:
            await asyncio.sleep(timeout)
            
            # Check if still active
            escalation = self.active_escalations.get(alert_id)
            if not escalation:
                return
            
            if escalation['status'] == ResponseStatus.PENDING.value:
                # Timeout reached, escalate to next level
                await self.escalate_to_next_level(alert_id)
                
        except Exception as e:
            logging.error(f"Error monitoring level timeout: {str(e)}")
    
    async def escalate_to_next_level(self, alert_id: str):
        """Escalate to next level in policy"""
        try:
            escalation = self.active_escalations.get(alert_id)
            if not escalation:
                return
            
            policy = self.get_escalation_policy({'id': alert_id})
            if not policy:
                return
            
            # Check if there are more levels
            next_level = escalation['current_level'] + 1
            if next_level < len(policy.levels):
                # Move to next level
                escalation['current_level'] = next_level
                escalation['current_level_started_at'] = datetime.now().isoformat()
                await self.store_escalation(escalation)
                
                # Execute next level
                await self.execute_escalation_level(
                    escalation,
                    policy.levels[next_level]
                )
            else:
                # No more levels, check if should repeat
                if escalation['repeat_count'] < policy.max_repeats:
                    # Reset to first level and increment repeat count
                    escalation['current_level'] = 0
                    escalation['repeat_count'] += 1
                    await self.store_escalation(escalation)
                    
                    # Execute first level again
                    await self.execute_escalation_level(
                        escalation,
                        policy.levels[0]
                    )
                else:
                    # Max repeats reached, mark as failed
                    await self.handle_escalation_failure(alert_id)
                    
        except Exception as e:
            logging.error(f"Error escalating to next level: {str(e)}")

    async def start(self):
        """Start the escalation manager"""
        try:
            logging.info("Starting Escalation Manager")
            
            # Start background tasks
            asyncio.create_task(self.monitor_active_escalations())
            asyncio.create_task(self.monitor_sla_compliance())
            asyncio.create_task(self.generate_reports())
            
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Error in escalation manager: {str(e)}")
            raise

# Run the escalation manager
if __name__ == "__main__":
    manager = EscalationManager()
    asyncio.run(manager.start())
```

I'll continue with the Response Tracking and SLA Monitoring components next. Would you like me to proceed?