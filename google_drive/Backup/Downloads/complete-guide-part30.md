# Complete Home Cloud Setup Guide - Part 30

## Part 10.25: Alert Notification and Escalation System

### Alert Notifier
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
import jinja2
from twilio.rest import Client
import aiofiles
import os
import yaml

class NotificationChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    PHONE = "phone"
    WEBHOOK = "webhook"

class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"
    READ = "read"

class AlertNotifier:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=23)
        self.load_config()
        self.setup_templates()
        self.setup_notification_tracking()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/alert_notifier.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        """Load notification configuration"""
        self.config = {
            'notifications': {
                'retries': {
                    'max_attempts': 3,
                    'delay': 300,  # 5 minutes
                    'backoff_factor': 2
                },
                'batch': {
                    'enabled': True,
                    'interval': 60,  # 1 minute
                    'max_size': 10
                },
                'tracking': {
                    'enabled': True,
                    'store_duration': 604800  # 7 days
                }
            },
            'templates': {
                'base_dir': '/opt/templates',
                'default': {
                    'email': 'email/default.j2',
                    'slack': 'slack/default.j2',
                    'sms': 'sms/default.j2'
                },
                'custom': {
                    'disk_space': {
                        'email': 'email/disk_space.j2',
                        'slack': 'slack/disk_space.j2',
                        'sms': 'sms/disk_space.j2'
                    },
                    'service_down': {
                        'email': 'email/service_down.j2',
                        'slack': 'slack/service_down.j2',
                        'sms': 'sms/service_down.j2'
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
                    'use_ssl': True,
                    'timeout': 30
                },
                'slack': {
                    'enabled': True,
                    'webhook_url': 'https://hooks.slack.com/services/xxx',
                    'bot_token': 'xoxb-xxx',
                    'default_channel': '#alerts',
                    'username': 'Alert Bot',
                    'icon_emoji': ':warning:'
                },
                'sms': {
                    'enabled': True,
                    'provider': 'twilio',
                    'account_sid': 'your_sid',
                    'auth_token': 'your_token',
                    'from_number': '+1234567890',
                    'max_length': 160,
                    'split_long': True
                },
                'phone': {
                    'enabled': True,
                    'provider': 'twilio',
                    'account_sid': 'your_sid',
                    'auth_token': 'your_token',
                    'from_number': '+1234567890',
                    'voice_language': 'en-US',
                    'retry_attempts': 2
                },
                'webhook': {
                    'enabled': True,
                    'endpoints': {
                        'primary': 'http://primary/webhook',
                        'backup': 'http://backup/webhook'
                    },
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-API-Key': 'your_api_key'
                    },
                    'timeout': 10
                }
            }
        }
        
    def setup_templates(self):
        """Initialize Jinja2 templates"""
        try:
            self.template_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(self.config['templates']['base_dir']),
                autoescape=True
            )
            
            # Load and compile templates
            self.templates = {}
            for channel in NotificationChannel:
                self.templates[channel.value] = {
                    'default': self.template_env.get_template(
                        self.config['templates']['default'][channel.value]
                    )
                }
                
                # Load custom templates
                for alert_type, templates in self.config['templates']['custom'].items():
                    if channel.value in templates:
                        self.templates[channel.value][alert_type] = \
                            self.template_env.get_template(templates[channel.value])
                            
        except Exception as e:
            logging.error(f"Error setting up templates: {str(e)}")
    
    def setup_notification_tracking(self):
        """Initialize notification tracking"""
        self.notification_queue = defaultdict(list)
        self.notification_history = defaultdict(list)
        self.delivery_status = defaultdict(dict)
        self.retry_queue = defaultdict(list)
    
    async def send_notification(self, alert: Dict, channel: NotificationChannel) -> bool:
        """Send notification through specified channel"""
        try:
            # Check channel configuration
            if not self.config['channels'][channel.value]['enabled']:
                logging.warning(f"Channel {channel.value} is disabled")
                return False
            
            # Generate notification content
            content = await self.generate_content(alert, channel)
            
            # Send based on channel
            if channel == NotificationChannel.EMAIL:
                success = await self.send_email(alert, content)
            elif channel == NotificationChannel.SLACK:
                success = await self.send_slack(alert, content)
            elif channel == NotificationChannel.SMS:
                success = await self.send_sms(alert, content)
            elif channel == NotificationChannel.PHONE:
                success = await self.send_phone(alert, content)
            elif channel == NotificationChannel.WEBHOOK:
                success = await self.send_webhook(alert, content)
            else:
                logging.error(f"Unknown notification channel: {channel}")
                return False
            
            # Track notification
            await self.track_notification(alert, channel, success)
            
            return success
            
        except Exception as e:
            logging.error(f"Error sending notification: {str(e)}")
            await self.handle_notification_failure(alert, channel, str(e))
            return False
    
    async def generate_content(self, alert: Dict, 
                             channel: NotificationChannel) -> Dict:
        """Generate notification content using templates"""
        try:
            # Get appropriate template
            template = self.get_template(alert, channel)
            
            # Prepare template context
            context = {
                'alert': alert,
                'timestamp': datetime.now().isoformat(),
                'channel': channel.value,
                'config': self.config['channels'][channel.value]
            }
            
            # Render template
            content = template.render(**context)
            
            # Format based on channel
            if channel == NotificationChannel.EMAIL:
                return self.format_email_content(content, alert)
            elif channel == NotificationChannel.SLACK:
                return self.format_slack_content(content, alert)
            elif channel == NotificationChannel.SMS:
                return self.format_sms_content(content, alert)
            elif channel == NotificationChannel.PHONE:
                return self.format_phone_content(content, alert)
            elif channel == NotificationChannel.WEBHOOK:
                return self.format_webhook_content(content, alert)
            
        except Exception as e:
            logging.error(f"Error generating content: {str(e)}")
            return self.generate_fallback_content(alert, channel)
    
    def get_template(self, alert: Dict, channel: NotificationChannel):
        """Get appropriate template for alert"""
        try:
            alert_type = alert.get('type', 'default')
            
            # Check for custom template
            if (alert_type in self.templates[channel.value] and
                self.templates[channel.value][alert_type]):
                return self.templates[channel.value][alert_type]
            
            # Fall back to default template
            return self.templates[channel.value]['default']
            
        except Exception as e:
            logging.error(f"Error getting template: {str(e)}")
            return self.templates[channel.value]['default']
    
    async def send_email(self, alert: Dict, content: Dict) -> bool:
        """Send email notification"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = content['subject']
            msg['From'] = self.config['channels']['email']['from_address']
            msg['To'] = content['to']
            
            # Add HTML and text parts
            text_part = MIMEText(content['text'], 'plain')
            html_part = MIMEText(content['html'], 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(
                self.config['channels']['email']['smtp_server'],
                self.config['channels']['email']['smtp_port']
            ) as server:
                server.starttls()
                server.login(
                    self.config['channels']['email']['username'],
                    self.config['channels']['email']['password']
                )
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            return False
    
    async def send_slack(self, alert: Dict, content: Dict) -> bool:
        """Send Slack notification"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config['channels']['slack']['webhook_url'],
                    json=content,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logging.error(f"Error sending Slack notification: {str(e)}")
            return False
    
    async def send_sms(self, alert: Dict, content: Dict) -> bool:
        """Send SMS notification"""
        try:
            client = Client(
                self.config['channels']['sms']['account_sid'],
                self.config['channels']['sms']['auth_token']
            )
            
            message = client.messages.create(
                body=content['text'],
                from_=self.config['channels']['sms']['from_number'],
                to=content['to']
            )
            
            return message.status != 'failed'
            
        except Exception as e:
            logging.error(f"Error sending SMS: {str(e)}")
            return False
    
    async def track_notification(self, alert: Dict, channel: NotificationChannel,
                               success: bool):
        """Track notification status"""
        try:
            notification_record = {
                'alert_id': alert['id'],
                'channel': channel.value,
                'timestamp': datetime.now().isoformat(),
                'status': NotificationStatus.SENT.value if success else NotificationStatus.FAILED.value,
                'attempts': 1
            }
            
            # Store in Redis
            self.redis.hset(
                f"notification:{alert['id']}:{channel.value}",
                mapping=notification_record
            )
            
            # Set expiration
            self.redis.expire(
                f"notification:{alert['id']}:{channel.value}",
                self.config['notifications']['tracking']['store_duration']
            )
            
            # Update history
            self.notification_history[alert['id']].append(notification_record)
            
        except Exception as e:
            logging.error(f"Error tracking notification: {str(e)}")

    async def start(self):
        """Start the notification manager"""
        try:
            logging.info("Starting Alert Notifier")
            
            # Start background tasks
            asyncio.create_task(self.process_notification_queue())
            asyncio.create_task(self.process_retry_queue())
            asyncio.create_task(self.cleanup_old_notifications())
            
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Error in alert notifier: {str(e)}")
            raise

# Run the alert notifier
if __name__ == "__main__":
    notifier = AlertNotifier()
    asyncio.run(notifier.start())
```

I'll continue with the Alert Escalation System implementation next. Would you like me to proceed?