# Complete Home Cloud Setup Guide - Part 32

## Part 10.27: Response Tracking and SLA Monitoring System

### Response Manager
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
import aiohttp
from dataclasses import dataclass

class ResponseType(Enum):
    ACKNOWLEDGMENT = "acknowledgment"
    UPDATE = "update"
    RESOLUTION = "resolution"
    ESCALATION = "escalation"

class SLAStatus(Enum):
    COMPLIANT = "compliant"
    AT_RISK = "at_risk"
    BREACHED = "breached"

@dataclass
class SLADefinition:
    id: str
    name: str
    acknowledgment_time: int
    resolution_time: int
    priority: str
    business_hours: bool
    allowed_breaches: int

class ResponseManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=25)
        self.load_config()
        self.setup_tracking()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/response_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        """Load response tracking configuration"""
        self.config = {
            'response_tracking': {
                'timeouts': {
                    'acknowledgment': {
                        'critical': 300,    # 5 minutes
                        'high': 900,        # 15 minutes
                        'medium': 1800,     # 30 minutes
                        'low': 3600         # 1 hour
                    },
                    'updates': {
                        'critical': 900,    # 15 minutes
                        'high': 1800,       # 30 minutes
                        'medium': 3600,     # 1 hour
                        'low': 7200         # 2 hours
                    }
                },
                'reminders': {
                    'enabled': True,
                    'interval': {
                        'critical': 300,    # 5 minutes
                        'high': 600,        # 10 minutes
                        'medium': 1800,     # 30 minutes
                        'low': 3600         # 1 hour
                    },
                    'max_reminders': 3,
                    'channels': ['email', 'slack']
                }
            },
            'sla': {
                'definitions': {
                    'critical': {
                        'acknowledgment_time': 300,     # 5 minutes
                        'resolution_time': 3600,        # 1 hour
                        'business_hours': False,
                        'allowed_breaches': 0
                    },
                    'high': {
                        'acknowledgment_time': 1800,    # 30 minutes
                        'resolution_time': 14400,       # 4 hours
                        'business_hours': True,
                        'allowed_breaches': 1
                    },
                    'medium': {
                        'acknowledgment_time': 3600,    # 1 hour
                        'resolution_time': 28800,       # 8 hours
                        'business_hours': True,
                        'allowed_breaches': 2
                    },
                    'low': {
                        'acknowledgment_time': 7200,    # 2 hours
                        'resolution_time': 86400,       # 24 hours
                        'business_hours': True,
                        'allowed_breaches': 3
                    }
                },
                'business_hours': {
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'timezone': 'UTC',
                    'weekdays': [0, 1, 2, 3, 4]  # Monday to Friday
                },
                'monitoring': {
                    'check_interval': 60,  # 1 minute
                    'warning_threshold': 0.8,  # 80% of SLA
                    'notification_channels': ['email', 'slack']
                },
                'reporting': {
                    'enabled': True,
                    'interval': 'daily',
                    'recipients': ['manager@example.com'],
                    'include_details': True
                }
            }
        }
        
    def setup_tracking(self):
        """Initialize tracking structures"""
        self.active_responses = defaultdict(dict)
        self.response_history = defaultdict(list)
        self.sla_tracking = defaultdict(dict)
        self.reminder_tracking = defaultdict(list)
    
    async def track_response(self, alert_id: str, response: Dict) -> bool:
        """Track response to alert"""
        try:
            # Add response metadata
            response['timestamp'] = datetime.now().isoformat()
            response['tracking_id'] = f"{alert_id}_{len(self.response_history[alert_id])}"
            
            # Store response
            await self.store_response(alert_id, response)
            
            # Update SLA tracking
            await self.update_sla_tracking(alert_id, response)
            
            # Check if reminders should be cleared
            if response['type'] == ResponseType.ACKNOWLEDGMENT.value:
                await self.clear_acknowledgment_reminders(alert_id)
            
            return True
            
        except Exception as e:
            logging.error(f"Error tracking response: {str(e)}")
            return False
    
    async def store_response(self, alert_id: str, response: Dict):
        """Store response details"""
        try:
            # Store in Redis
            self.redis.hset(
                f"response:{alert_id}:{response['tracking_id']}",
                mapping=response
            )
            
            # Update tracking
            self.active_responses[alert_id] = response
            self.response_history[alert_id].append(response)
            
        except Exception as e:
            logging.error(f"Error storing response: {str(e)}")
    
    async def update_sla_tracking(self, alert_id: str, response: Dict):
        """Update SLA tracking based on response"""
        try:
            sla_tracking = self.sla_tracking[alert_id]
            
            if response['type'] == ResponseType.ACKNOWLEDGMENT.value:
                if 'acknowledgment_time' not in sla_tracking:
                    sla_tracking['acknowledgment_time'] = response['timestamp']
                    
            elif response['type'] == ResponseType.RESOLUTION.value:
                if 'resolution_time' not in sla_tracking:
                    sla_tracking['resolution_time'] = response['timestamp']
                    
            # Store updated tracking
            self.redis.hset(
                f"sla_tracking:{alert_id}",
                mapping=sla_tracking
            )
            
        except Exception as e:
            logging.error(f"Error updating SLA tracking: {str(e)}")
    
    async def check_sla_compliance(self, alert_id: str) -> Dict:
        """Check SLA compliance status"""
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                return {'status': SLAStatus.BREACHED.value}
            
            sla_def = self.get_sla_definition(alert)
            if not sla_def:
                return {'status': SLAStatus.BREACHED.value}
            
            tracking = self.sla_tracking[alert_id]
            current_time = datetime.now()
            
            # Check acknowledgment SLA
            if 'acknowledgment_time' not in tracking:
                ack_deadline = self.calculate_deadline(
                    alert['created_at'],
                    sla_def.acknowledgment_time,
                    sla_def.business_hours
                )
                if current_time > ack_deadline:
                    return {
                        'status': SLAStatus.BREACHED.value,
                        'breach_type': 'acknowledgment',
                        'breach_time': current_time.isoformat()
                    }
            
            # Check resolution SLA
            if 'resolution_time' not in tracking:
                res_deadline = self.calculate_deadline(
                    alert['created_at'],
                    sla_def.resolution_time,
                    sla_def.business_hours
                )
                if current_time > res_deadline:
                    return {
                        'status': SLAStatus.BREACHED.value,
                        'breach_type': 'resolution',
                        'breach_time': current_time.isoformat()
                    }
                
                # Check if at risk
                warning_time = res_deadline - timedelta(
                    seconds=int(sla_def.resolution_time * 
                              self.config['sla']['monitoring']['warning_threshold'])
                )
                if current_time > warning_time:
                    return {
                        'status': SLAStatus.AT_RISK.value,
                        'deadline': res_deadline.isoformat()
                    }
            
            return {'status': SLAStatus.COMPLIANT.value}
            
        except Exception as e:
            logging.error(f"Error checking SLA compliance: {str(e)}")
            return {'status': SLAStatus.BREACHED.value}
    
    def calculate_deadline(self, start_time: str, duration: int, 
                         business_hours: bool) -> datetime:
        """Calculate deadline considering business hours if needed"""
        try:
            start = datetime.fromisoformat(start_time)
            if not business_hours:
                return start + timedelta(seconds=duration)
            
            # Calculate deadline considering business hours
            remaining_seconds = duration
            current = start
            
            while remaining_seconds > 0:
                if self.is_business_hours(current):
                    remaining_seconds -= 1
                current += timedelta(seconds=1)
            
            return current
            
        except Exception as e:
            logging.error(f"Error calculating deadline: {str(e)}")
            return datetime.now() + timedelta(seconds=duration)
    
    def is_business_hours(self, time: datetime) -> bool:
        """Check if given time is within business hours"""
        try:
            # Check weekday
            if time.weekday() not in self.config['sla']['business_hours']['weekdays']:
                return False
            
            # Parse business hours
            start_time = datetime.strptime(
                self.config['sla']['business_hours']['start_time'],
                '%H:%M'
            ).time()
            end_time = datetime.strptime(
                self.config['sla']['business_hours']['end_time'],
                '%H:%M'
            ).time()
            
            return start_time <= time.time() <= end_time
            
        except Exception as e:
            logging.error(f"Error checking business hours: {str(e)}")
            return True
    
    def get_sla_definition(self, alert: Dict) -> Optional[SLADefinition]:
        """Get SLA definition for alert"""
        try:
            priority = alert.get('priority', 'medium').lower()
            if priority in self.config['sla']['definitions']:
                sla_config = self.config['sla']['definitions'][priority]
                return SLADefinition(
                    id=f"sla_{priority}",
                    name=f"{priority.capitalize()} Priority SLA",
                    acknowledgment_time=sla_config['acknowledgment_time'],
                    resolution_time=sla_config['resolution_time'],
                    priority=priority,
                    business_hours=sla_config['business_hours'],
                    allowed_breaches=sla_config['allowed_breaches']
                )
            return None
            
        except Exception as e:
            logging.error(f"Error getting SLA definition: {str(e)}")
            return None

    async def start(self):
        """Start the response manager"""
        try:
            logging.info("Starting Response Manager")
            
            # Start background tasks
            asyncio.create_task(self.monitor_sla_compliance())
            asyncio.create_task(self.process_reminders())
            asyncio.create_task(self.generate_sla_reports())
            
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Error in response manager: {str(e)}")
            raise

# Run the response manager
if __name__ == "__main__":
    manager = ResponseManager()
    asyncio.run(manager.start())
```

I'll continue with the SLA Reporting and Analytics System next. Would you like me to proceed?