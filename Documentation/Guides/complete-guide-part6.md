# Complete Home Cloud Setup Guide - Part 6

## Part 8: Remote Access Security

### 8.1 Advanced Firewall Configuration

#### Dynamic Firewall Manager
```python
#!/usr/bin/env python3
import subprocess
import json
import time
import redis
import ipaddress
from datetime import datetime, timedelta

class DynamicFirewall:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.config = self.load_config()
        self.whitelist = self.load_whitelist()
        
    def load_config(self):
        with open('/opt/security/firewall_config.json', 'r') as f:
            return json.load(f)
    
    def load_whitelist(self):
        with open('/opt/security/ip_whitelist.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def is_whitelisted(self, ip):
        """Check if IP is whitelisted"""
        return any(ipaddress.ip_address(ip) in ipaddress.ip_network(net)
                  for net in self.whitelist)
    
    def add_rule(self, ip, port, action='DROP', duration=3600):
        """Add firewall rule"""
        if self.is_whitelisted(ip):
            return False
        
        rule = {
            'ip': ip,
            'port': port,
            'action': action,
            'expires': int(time.time()) + duration
        }
        
        # Store rule in Redis
        self.redis_client.setex(
            f"firewall:rule:{ip}:{port}",
            duration,
            json.dumps(rule)
        )
        
        # Apply iptables rule
        cmd = [
            'iptables',
            '-A', 'INPUT',
            '-s', ip,
            '-p', 'tcp',
            '--dport', str(port),
            '-j', action
        ]
        subprocess.run(cmd)
        return True
    
    def remove_rule(self, ip, port):
        """Remove firewall rule"""
        cmd = [
            'iptables',
            '-D', 'INPUT',
            '-s', ip,
            '-p', 'tcp',
            '--dport', str(port),
            '-j', 'DROP'
        ]
        subprocess.run(cmd)
        
        # Remove from Redis
        self.redis_client.delete(f"firewall:rule:{ip}:{port}")
    
    def get_active_rules(self):
        """Get all active firewall rules"""
        rules = []
        for key in self.redis_client.scan_iter("firewall:rule:*"):
            rule_data = self.redis_client.get(key)
            if rule_data:
                rules.append(json.loads(rule_data))
        return rules
    
    def cleanup_expired_rules(self):
        """Remove expired rules"""
        current_time = int(time.time())
        for rule in self.get_active_rules():
            if rule['expires'] <= current_time:
                self.remove_rule(rule['ip'], rule['port'])
    
    def analyze_traffic(self, log_file):
        """Analyze traffic patterns and apply rules"""
        # Parse log file (example for nginx access log)
        suspicious = {}
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    ip = line.split()[0]
                    if self.is_whitelisted(ip):
                        continue
                    
                    # Count requests per IP
                    if ip not in suspicious:
                        suspicious[ip] = {
                            'count': 0,
                            'errors': 0,
                            'last_seen': None
                        }
                    
                    suspicious[ip]['count'] += 1
                    suspicious[ip]['last_seen'] = datetime.now()
                    
                    # Check for error responses
                    status_code = int(line.split()[8])
                    if status_code >= 400:
                        suspicious[ip]['errors'] += 1
                    
                except Exception as e:
                    continue
        
        # Apply rules based on analysis
        for ip, data in suspicious.items():
            if data['count'] > self.config['request_threshold']:
                self.add_rule(ip, 80, duration=3600)
            
            if data['errors'] > self.config['error_threshold']:
                self.add_rule(ip, 80, duration=7200)
    
    def run(self):
        """Main firewall management loop"""
        while True:
            try:
                # Cleanup expired rules
                self.cleanup_expired_rules()
                
                # Analyze traffic
                self.analyze_traffic('/var/log/nginx/access.log')
                
                # Sleep for interval
                time.sleep(self.config['check_interval'])
                
            except Exception as e:
                print(f"Error in firewall management: {str(e)}")
                time.sleep(60)

```

#### Real-time Traffic Analysis
```python
#!/usr/bin/env python3
import asyncio
import aiodns
import json
import aiohttp
import logging
from collections import defaultdict
from datetime import datetime, timedelta

class TrafficAnalyzer:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.traffic_stats = defaultdict(lambda: {
            'requests': 0,
            'bytes': 0,
            'errors': 0,
            'last_seen': None
        })
        self.dns_resolver = aiodns.DNSResolver()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/traffic_analyzer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        with open('/opt/security/analyzer_config.json', 'r') as f:
            self.config = json.load(f)
    
    async def resolve_ip(self, ip):
        """Reverse DNS lookup"""
        try:
            result = await self.dns_resolver.gethostbyaddr(ip)
            return result.name
        except:
            return None
    
    async def check_reputation(self, ip):
        """Check IP reputation using AbuseIPDB"""
        api_key = self.config['abuseipdb_key']
        url = f"https://api.abuseipdb.com/api/v2/check"
        
        headers = {
            'Key': api_key,
            'Accept': 'application/json'
        }
        
        params = {
            'ipAddress': ip,
            'maxAgeInDays': '30'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']['abuseConfidenceScore']
        return None
    
    async def analyze_request(self, ip, request_data):
        """Analyze a single request"""
        # Update basic stats
        self.traffic_stats[ip]['requests'] += 1
        self.traffic_stats[ip]['bytes'] += request_data['bytes']
        self.traffic_stats[ip]['last_seen'] = datetime.now()
        
        if request_data['status'] >= 400:
            self.traffic_stats[ip]['errors'] += 1
        
        # Perform additional checks if thresholds exceeded
        if self.traffic_stats[ip]['requests'] > self.config['request_threshold']:
            hostname = await self.resolve_ip(ip)
            reputation = await self.check_reputation(ip)
            
            if reputation and reputation > self.config['reputation_threshold']:
                await self.take_action(ip, 'high_reputation_score')
            
            if self.traffic_stats[ip]['errors'] > self.config['error_threshold']:
                await self.take_action(ip, 'high_error_rate')
    
    async def take_action(self, ip, reason):
        """Take action against suspicious IP"""
        actions = {
            'high_reputation_score': {
                'duration': 86400,  # 24 hours
                'action': 'DROP'
            },
            'high_error_rate': {
                'duration': 3600,  # 1 hour
                'action': 'DROP'
            }
        }
        
        action = actions.get(reason)
        if action:
            # Add firewall rule
            await self.add_firewall_rule(ip, action['action'], action['duration'])
            
            # Log action
            logging.warning(f"Action taken against {ip} for {reason}")
            
            # Send notification
            await self.send_notification({
                'ip': ip,
                'reason': reason,
                'action': action['action'],
                'duration': action['duration']
            })
    
    async def add_firewall_rule(self, ip, action, duration):
        """Add firewall rule using DynamicFirewall"""
        firewall = DynamicFirewall()
        firewall.add_rule(ip, '*', action=action, duration=duration)
    
    async def send_notification(self, data):
        """Send notification about action taken"""
        webhook_url = self.config['webhook_url']
        
        message = {
            'text': f"Security Alert: Action taken against {data['ip']}\n"
                   f"Reason: {data['reason']}\n"
                   f"Action: {data['action']}\n"
                   f"Duration: {data['duration']} seconds"
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=message)
    
    async def monitor_traffic(self):
        """Monitor traffic in real-time"""
        while True:
            try:
                # Read from log file
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://localhost:9200/logs/_search') as response:
                        if response.status == 200:
                            logs = await response.json()
                            for hit in logs['hits']['hits']:
                                log = hit['_source']
                                await self.analyze_request(log['remote_addr'], {
                                    'bytes': log['bytes_sent'],
                                    'status': log['status']
                                })
                
                # Cleanup old stats
                current_time = datetime.now()
                for ip in list(self.traffic_stats.keys()):
                    if (current_time - self.traffic_stats[ip]['last_seen'] >
                            timedelta(hours=1)):
                        del self.traffic_stats[ip]
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logging.error(f"Error in traffic monitoring: {str(e)}")
                await asyncio.sleep(5)

# Run the analyzer
if __name__ == "__main__":
    analyzer = TrafficAnalyzer()
    asyncio.run(analyzer.monitor_traffic())
```

I'll continue with the Intrusion Detection System and Mobile Device Configuration sections. Would you like me to proceed?