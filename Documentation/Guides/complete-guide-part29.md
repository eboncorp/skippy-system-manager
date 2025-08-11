# Complete Home Cloud Setup Guide - Part 29

## Part 10.24: Alert Management System

### Alert Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
from collections import defaultdict
import aiohttp
from typing import Dict, List, Any, Optional
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AlertState(Enum):
    NEW = "new"
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"

class AlertPriority(Enum):
    P1 = 1  # Critical - Immediate response required
    P2 = 2  # High - Response required within 30 minutes
    P3 = 3  # Medium - Response required within 2 hours
    P4 = 4  # Low - Response required within 8 hours
    P5 = 5  # Info - No immediate response required

class AlertManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=22)
        self.load_config()
        self.setup_alert_tracking()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/alert_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        """Load alert management configuration"""
        self.config = {
            'alerts': {
                'retention': {
                    'active': 86400,     # 1 day
                    'resolved': 604800,   # 1 week
                    'acknowledged': 259200  # 3 days
                },
                'deduplication': {
                    'enabled': True,
                    'window': 300,  # 5 minutes
                    'attributes': ['source', 'type', 'severity']
                },
                'grouping': {
                    'enabled': True,
                    'window': 300,  # 5 minutes
                    'max_group_size': 10,
                    'attributes': ['source', 'type']
                },
                'escalation': {
                    'policies': {
                        'p1': [
                            {
                                'delay': 0,
                                'channels': ['email', 'slack', 'sms'],
                                'groups': ['oncall']
                            },
                            {
                                'delay': 900,  # 15 minutes
                                'channels': ['email', 'slack', 'sms', 'phone'],
                                'groups': ['oncall', 'manager']
                            },
                            {
                                'delay': 1800,  # 30 minutes
                                'channels': ['email', 'slack', 'sms', 'phone'],
                                'groups': ['manager', 'director']
                            }
                        ],
                        'p2': [
                            {
                                'delay': 0,
                                'channels': ['email', 'slack'],
                                'groups': ['oncall']
                            },
                            {
                                'delay': 1800,  # 30 minutes
                                'channels': ['email', 'slack', 'sms'],
                                'groups': ['oncall', 'manager']
                            }
                        ],
                        'p3': [
                            {
                                'delay': 0,
                                'channels': ['email', 'slack'],
                                'groups': ['oncall']
                            }
                        ],
                        'default': [
                            {
                                'delay': 0,
                                'channels': ['email'],
                                'groups': ['oncall']
                            }
                        ]
                    }
                }
            },
            'channels': {
                'email': {
                    'enabled': True,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'username': 'alerts@example.com',
                    'password': 'your_password',
                    'from_address': 'alerts@example.com',
                    'template_dir': '/opt/templates/email'
                },
                'slack': {
                    'enabled': True,
                    'webhook_url': 'https://hooks.slack.com/services/xxx',
                    'channels': {
                        'critical': '#alerts-critical',
                        'high': '#alerts-high',
                        'default': '#alerts'
                    },
                    'mention_users': {
                        'p1': ['@oncall'],
                        'p2': ['@oncall']
                    }
                },
                'sms': {
                    'enabled': True,
                    'provider': 'twilio',
                    'account_sid': 'your_sid',
                    'auth_token': 'your_token',
                    'from_number': '+1234567890'
                },
                'phone': {
                    'enabled': True,
                    'provider': 'twilio',
                    'account_sid': 'your_sid',
                    'auth_token': 'your_token',
                    'from_number': '+1234567890',
                    'voice_language': 'en-US'
                }
            },
            'recipients': {
                'groups': {
                    'oncall': {
                        'email': ['oncall@example.com'],
                        'slack': ['@oncall'],
                        'sms': ['+1234567890'],
                        'phone': ['+1234567890']
                    },
                    'manager': {
                        'email': ['manager@example.com'],
                        'slack': ['@manager'],
                        'sms': ['+1234567891'],
                        'phone': ['+1234567891']
                    },
                    'director': {
                        'email': ['director@example.com'],
                        'slack': ['@director'],
                        'sms': ['+1234567892'],
                        'phone': ['+1234567892']
                    }
                }
            },
            'templates': {
                'base_dir': '/opt/templates',
                'default_template': 'default.j2',
                'custom_templates': {
                    'disk_space': 'disk_space.j2',
                    'service_down': 'service_down.j2',
                    'high_cpu': 'high_cpu.j2'
                }
            }
        }
        
    def setup_alert_tracking(self):
        """Initialize alert tracking structures"""
        self.active_alerts = defaultdict(dict)
        self.alert_groups = defaultdict(list)
        self.escalation_timers = defaultdict(dict)
        self.alert_history = defaultdict(list)
        
    async def process_alert(self, alert: Dict):
        """Process new alert"""
        try:
            # Generate alert ID
            alert_id = self.generate_alert_id(alert)
            alert['id'] = alert_id
            alert['created_at'] = datetime.now().isoformat()
            alert['state'] = AlertState.NEW.value
            
            # Check for deduplication
            if await self.should_deduplicate(alert):
                logging.info(f"Alert {alert_id} deduplicated")
                return
            
            # Set priority if not provided
            if 'priority' not in alert:
                alert['priority'] = await self.determine_priority(alert)
            
            # Group alert if needed
            group_id = await self.group_alert(alert)
            if group_id:
                alert['group_id'] = group_id
            
            # Store alert
            await self.store_alert(alert)
            
            # Process alert based on priority
            await self.process_alert_by_priority(alert)
            
        except Exception as e:
            logging.error(f"Error processing alert: {str(e)}")
    
    def generate_alert_id(self, alert: Dict) -> str:
        """Generate unique alert ID"""
        try:
            # Combine relevant fields for ID generation
            id_components = [
                str(alert.get('source', '')),
                str(alert.get('type', '')),
                datetime.now().strftime('%Y%m%d%H%M%S'),
                str(len(self.active_alerts))
            ]
            
            return '_'.join(id_components)
            
        except Exception as e:
            logging.error(f"Error generating alert ID: {str(e)}")
            return f"alert_{datetime.now().timestamp()}"
    
    async def should_deduplicate(self, alert: Dict) -> bool:
        """Check if alert should be deduplicated"""
        try:
            if not self.config['alerts']['deduplication']['enabled']:
                return False
            
            # Get deduplication key
            dedup_key = self.get_deduplication_key(alert)
            
            # Check recent alerts
            recent_alert = self.redis.get(f"dedup:{dedup_key}")
            if recent_alert:
                # Update count for existing alert
                existing_alert = json.loads(recent_alert)
                existing_alert['count'] = existing_alert.get('count', 1) + 1
                self.redis.set(
                    f"dedup:{dedup_key}",
                    json.dumps(existing_alert),
                    ex=self.config['alerts']['deduplication']['window']
                )
                return True
            
            # Store new alert for deduplication
            self.redis.set(
                f"dedup:{dedup_key}",
                json.dumps(alert),
                ex=self.config['alerts']['deduplication']['window']
            )
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking deduplication: {str(e)}")
            return False
    
    def get_deduplication_key(self, alert: Dict) -> str:
        """Generate deduplication key for alert"""
        try:
            # Combine configured attributes
            key_components = [
                str(alert.get(attr, ''))
                for attr in self.config['alerts']['deduplication']['attributes']
            ]
            
            return '_'.join(key_components)
            
        except Exception as e:
            logging.error(f"Error generating deduplication key: {str(e)}")
            return str(datetime.now().timestamp())
    
    async def determine_priority(self, alert: Dict) -> str:
        """Determine alert priority"""
        try:
            # Check severity mapping
            severity = alert.get('severity', '').lower()
            if severity == 'critical':
                return AlertPriority.P1.name
            elif severity == 'high':
                return AlertPriority.P2.name
            elif severity == 'medium':
                return AlertPriority.P3.name
            elif severity == 'low':
                return AlertPriority.P4.name
            else:
                return AlertPriority.P5.name
                
        except Exception as e:
            logging.error(f"Error determining priority: {str(e)}")
            return AlertPriority.P3.name
    
    async def group_alert(self, alert: Dict) -> Optional[str]:
        """Group similar alerts"""
        try:
            if not self.config['alerts']['grouping']['enabled']:
                return None
            
            # Get grouping key
            group_key = self.get_grouping_key(alert)
            
            # Check existing groups
            for group_id, group in self.alert_groups.items():
                if len(group) < self.config['alerts']['grouping']['max_group_size']:
                    if self.should_add_to_group(alert, group):
                        group.append(alert)
                        return group_id
            
            # Create new group
            group_id = f"group_{datetime.now().timestamp()}"
            self.alert_groups[group_id] = [alert]
            return group_id
            
        except Exception as e:
            logging.error(f"Error grouping alert: {str(e)}")
            return None
    
    def get_grouping_key(self, alert: Dict) -> str:
        """Generate grouping key for alert"""
        try:
            # Combine configured attributes
            key_components = [
                str(alert.get(attr, ''))
                for attr in self.config['alerts']['grouping']['attributes']
            ]
            
            return '_'.join(key_components)
            
        except Exception as e:
            logging.error(f"Error generating grouping key: {str(e)}")
            return str(datetime.now().timestamp())
    
    async def store_alert(self, alert: Dict):
        """Store alert in database"""
        try:
            # Store in Redis
            self.redis.hset(
                f"alert:{alert['id']}",
                mapping=alert
            )
            
            # Set expiration based on state
            expiration = self.config['alerts']['retention'][alert['state']]
            self.redis.expire(f"alert:{alert['id']}", expiration)
            
            # Update active alerts
            self.active_alerts[alert['id']] = alert
            
            # Update history
            self.alert_history[alert['source']].append({
                'id': alert['id'],
                'timestamp': alert['created_at'],
                'type': alert['type'],
                'priority': alert['priority']
            })
            
        except Exception as e:
            logging.error(f"Error storing alert: {str(e)}")

    async def start(self):
        """Start the alert manager"""
        try:
            logging.info("Starting Alert Manager")
            
            # Start background tasks
            asyncio.create_task(self.process_escalations())
            asyncio.create_task(self.cleanup_old_alerts())
            
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Error in alert manager: {str(e)}")
            raise

# Run the alert manager
if __name__ == "__main__":
    manager = AlertManager()
    asyncio.run(manager.start())
```

I'll continue with the Alert Notification and Escalation System implementation next. Would you like me to proceed?