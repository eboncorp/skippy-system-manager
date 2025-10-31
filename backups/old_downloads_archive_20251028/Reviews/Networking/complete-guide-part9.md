# Complete Home Cloud Setup Guide - Part 9

## Part 10.3: Push Notification System

### Push Notification Server Implementation
```python
#!/usr/bin/env python3
import asyncio
import aiohttp
from aiohttp import web
import json
import redis
import logging
from datetime import datetime
import jwt
from pywebpush import webpush, WebPushException
import yaml

class PushNotificationServer:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.redis = redis.Redis(host='localhost', port=6379, db=2)
        self.setup_routes()
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/push_server.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load server configuration"""
        with open('/opt/mobile/push_config.yml', 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Load VAPID keys
        with open('/opt/mobile/vapid_private.key', 'r') as f:
            self.private_key = f.read().strip()
        with open('/opt/mobile/vapid_public.key', 'r') as f:
            self.public_key = f.read().strip()
    
    def setup_routes(self):
        """Setup API routes"""
        self.app = web.Application()
        self.app.router.add_post('/register', self.register_device)
        self.app.router.add_post('/subscribe', self.subscribe_topic)
        self.app.router.add_post('/unsubscribe', self.unsubscribe_topic)
        self.app.router.add_post('/push', self.push_notification)
    
    async def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config['jwt_secret'],
                algorithms=['HS256']
            )
            return payload
        except jwt.InvalidTokenError:
            return None
    
    async def register_device(self, request):
        """Register a new device for push notifications"""
        try:
            data = await request.json()
            device_id = data['device_id']
            subscription_info = data['subscription']
            
            # Store device information
            device_key = f"device:{device_id}"
            self.redis.hmset(device_key, {
                'subscription': json.dumps(subscription_info),
                'registered_at': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat()
            })
            
            # Set default topics
            default_topics = ['system', 'security']
            for topic in default_topics:
                self.redis.sadd(f"topic:{topic}", device_id)
            
            return web.Response(
                text=json.dumps({'status': 'success', 'device_id': device_id}),
                content_type='application/json'
            )
            
        except Exception as e:
            logging.error(f"Error registering device: {str(e)}")
            return web.Response(
                status=400,
                text=json.dumps({'error': str(e)}),
                content_type='application/json'
            )
    
    async def subscribe_topic(self, request):
        """Subscribe device to a topic"""
        try:
            data = await request.json()
            device_id = data['device_id']
            topic = data['topic']
            
            # Verify device exists
            if not self.redis.exists(f"device:{device_id}"):
                raise ValueError("Device not registered")
            
            # Add to topic
            self.redis.sadd(f"topic:{topic}", device_id)
            
            return web.Response(
                text=json.dumps({'status': 'success'}),
                content_type='application/json'
            )
            
        except Exception as e:
            logging.error(f"Error subscribing to topic: {str(e)}")
            return web.Response(
                status=400,
                text=json.dumps({'error': str(e)}),
                content_type='application/json'
            )
    
    async def unsubscribe_topic(self, request):
        """Unsubscribe device from a topic"""
        try:
            data = await request.json()
            device_id = data['device_id']
            topic = data['topic']
            
            self.redis.srem(f"topic:{topic}", device_id)
            
            return web.Response(
                text=json.dumps({'status': 'success'}),
                content_type='application/json'
            )
            
        except Exception as e:
            logging.error(f"Error unsubscribing from topic: {str(e)}")
            return web.Response(status=400)
    
    async def push_notification(self, request):
        """Send push notification"""
        try:
            data = await request.json()
            topic = data.get('topic')
            message = data['message']
            
            # Get devices for topic
            if topic:
                devices = self.redis.smembers(f"topic:{topic}")
            else:
                devices = [data['device_id']]
            
            # Send to each device
            results = []
            for device_id in devices:
                try:
                    device_info = self.redis.hgetall(f"device:{device_id}")
                    if not device_info:
                        continue
                    
                    subscription = json.loads(device_info[b'subscription'].decode())
                    
                    # Send push notification
                    result = await self.send_push(subscription, message)
                    results.append({
                        'device_id': device_id,
                        'status': 'success' if result else 'failed'
                    })
                    
                except Exception as e:
                    logging.error(f"Error sending to device {device_id}: {str(e)}")
                    results.append({
                        'device_id': device_id,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            return web.Response(
                text=json.dumps({
                    'status': 'success',
                    'results': results
                }),
                content_type='application/json'
            )
            
        except Exception as e:
            logging.error(f"Error processing push request: {str(e)}")
            return web.Response(
                status=400,
                text=json.dumps({'error': str(e)}),
                content_type='application/json'
            )
    
    async def send_push(self, subscription_info, message):
        """Send push notification to a specific subscription"""
        try:
            data = json.dumps(message)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: webpush(
                    subscription_info=subscription_info,
                    data=data,
                    vapid_private_key=self.private_key,
                    vapid_claims={
                        "sub": f"mailto:{self.config['contact_email']}"
                    }
                )
            )
            
            return True
            
        except WebPushException as e:
            logging.error(f"WebPush error: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Push error: {str(e)}")
            return False
    
    async def cleanup_old_devices(self):
        """Cleanup inactive devices"""
        while True:
            try:
                current_time = datetime.now()
                all_devices = self.redis.keys("device:*")
                
                for device_key in all_devices:
                    device_info = self.redis.hgetall(device_key)
                    last_seen = datetime.fromisoformat(
                        device_info[b'last_seen'].decode()
                    )
                    
                    # Remove devices inactive for more than 30 days
                    if (current_time - last_seen).days > 30:
                        device_id = device_key.decode().split(':')[1]
                        
                        # Remove from all topics
                        all_topics = self.redis.keys("topic:*")
                        for topic in all_topics:
                            self.redis.srem(topic, device_id)
                        
                        # Remove device info
                        self.redis.delete(device_key)
                
                await asyncio.sleep(86400)  # Run daily
                
            except Exception as e:
                logging.error(f"Error in cleanup: {str(e)}")
                await asyncio.sleep(3600)  # Retry in an hour
    
    async def start(self):
        """Start the push notification server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            self.config['host'],
            self.config['port']
        )
        
        # Start cleanup task
        asyncio.create_task(self.cleanup_old_devices())
        
        await site.start()
        logging.info(f"Server started at {self.config['host']}:{self.config['port']}")

# Example configuration (push_config.yml)
"""
host: "0.0.0.0"
port: 8080
contact_email: "admin@yourdomain.com"
jwt_secret: "your-secret-key"
cleanup_interval: 86400
"""

# Run the server
if __name__ == "__main__":
    server = PushNotificationServer()
    asyncio.run(server.start())
```

### 10.4 Mobile Battery Optimization

I'll continue with the Battery Optimization and Bandwidth Management systems next. Would you like me to proceed?