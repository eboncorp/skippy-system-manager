# Complete Home Cloud Setup Guide - Part 7

## Part 9: Intrusion Detection System

### 9.1 Real-time Network Monitoring

#### Network IDS Implementation
```python
#!/usr/bin/env python3
import asyncio
import pyshark
import json
import redis
import logging
from datetime import datetime
from collections import defaultdict
import aiohttp
import yaml

class NetworkIDS:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.redis = redis.Redis(host='localhost', port=6379, db=1)
        self.threat_patterns = self.load_threat_patterns()
        self.connection_tracker = defaultdict(lambda: {
            'count': 0,
            'first_seen': None,
            'last_seen': None,
            'bytes_in': 0,
            'bytes_out': 0,
            'ports': set(),
            'protocols': set()
        })
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/network_ids.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        with open('/opt/security/ids_config.yml', 'r') as f:
            self.config = yaml.safe_load(f)
            
    def load_threat_patterns(self):
        """Load known threat patterns"""
        with open('/opt/security/threat_patterns.yml', 'r') as f:
            return yaml.safe_load(f)
    
    async def capture_traffic(self):
        """Capture and analyze network traffic"""
        capture = pyshark.LiveCapture(
            interface=self.config['monitor_interface'],
            bpf_filter='not port 22'  # Exclude SSH traffic
        )
        
        for packet in capture.sniff_continuously():
            await self.analyze_packet(packet)
    
    async def analyze_packet(self, packet):
        """Analyze individual packets"""
        try:
            if hasattr(packet, 'ip'):
                # Extract packet information
                src_ip = packet.ip.src
                dst_ip = packet.ip.dst
                protocol = packet.transport_layer if hasattr(packet, 'transport_layer') else 'OTHER'
                
                # Update connection tracker
                for ip in [src_ip, dst_ip]:
                    if self.connection_tracker[ip]['first_seen'] is None:
                        self.connection_tracker[ip]['first_seen'] = datetime.now()
                    
                    self.connection_tracker[ip]['last_seen'] = datetime.now()
                    self.connection_tracker[ip]['count'] += 1
                    self.connection_tracker[ip]['protocols'].add(protocol)
                    
                    if hasattr(packet, 'length'):
                        if ip == src_ip:
                            self.connection_tracker[ip]['bytes_out'] += int(packet.length)
                        else:
                            self.connection_tracker[ip]['bytes_in'] += int(packet.length)
                    
                    if hasattr(packet, packet.transport_layer.lower()):
                        transport = getattr(packet, packet.transport_layer.lower())
                        if hasattr(transport, 'dstport'):
                            self.connection_tracker[ip]['ports'].add(int(transport.dstport))
                
                # Check for suspicious patterns
                await self.check_patterns(packet)
                
                # Perform behavioral analysis
                await self.analyze_behavior(src_ip)
                await self.analyze_behavior(dst_ip)
                
            # Clean up old entries
            await self.cleanup_old_entries()
            
        except Exception as e:
            logging.error(f"Error analyzing packet: {str(e)}")
    
    async def check_patterns(self, packet):
        """Check packet against known threat patterns"""
        for pattern in self.threat_patterns:
            match = True
            for field, value in pattern['signature'].items():
                if not hasattr(packet, field) or not getattr(packet, field) == value:
                    match = False
                    break
            
            if match:
                await self.handle_threat(
                    threat_type=pattern['type'],
                    severity=pattern['severity'],
                    packet=packet
                )
    
    async def analyze_behavior(self, ip):
        """Analyze IP behavior for anomalies"""
        conn = self.connection_tracker[ip]
        
        # Check for port scanning
        if len(conn['ports']) > self.config['max_ports']:
            await self.handle_threat(
                threat_type='port_scan',
                severity='high',
                ip=ip,
                details=f"Accessed {len(conn['ports'])} different ports"
            )
        
        # Check for bandwidth abuse
        total_bytes = conn['bytes_in'] + conn['bytes_out']
        if total_bytes > self.config['max_bytes']:
            await self.handle_threat(
                threat_type='bandwidth_abuse',
                severity='medium',
                ip=ip,
                details=f"Transferred {total_bytes} bytes"
            )
        
        # Check for rapid connection attempts
        if conn['count'] > self.config['max_connections']:
            await self.handle_threat(
                threat_type='connection_flood',
                severity='high',
                ip=ip,
                details=f"Made {conn['count']} connections"
            )
    
    async def handle_threat(self, threat_type, severity, **kwargs):
        """Handle detected threats"""
        threat_id = f"threat:{datetime.now().isoformat()}:{threat_type}"
        
        # Create threat record
        threat = {
            'type': threat_type,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'details': kwargs
        }
        
        # Store in Redis
        self.redis.setex(
            threat_id,
            self.config['threat_ttl'],
            json.dumps(threat)
        )
        
        # Log threat
        logging.warning(f"Threat detected: {json.dumps(threat)}")
        
        # Take action based on severity
        if severity == 'high':
            await self.immediate_response(threat)
        
        # Send notification
        await self.send_notification(threat)
    
    async def immediate_response(self, threat):
        """Implement immediate response to high-severity threats"""
        try:
            if 'ip' in threat['details']:
                ip = threat['details']['ip']
                
                # Block IP using firewall
                firewall = DynamicFirewall()
                firewall.add_rule(
                    ip=ip,
                    action='DROP',
                    duration=self.config['block_duration']
                )
                
                # Record action
                logging.info(f"Blocked IP {ip} due to {threat['type']}")
        
        except Exception as e:
            logging.error(f"Error in immediate response: {str(e)}")
    
    async def send_notification(self, threat):
        """Send threat notification"""
        webhook_url = self.config['webhook_url']
        
        message = {
            'text': f"Security Alert!\n"
                   f"Type: {threat['type']}\n"
                   f"Severity: {threat['severity']}\n"
                   f"Time: {threat['timestamp']}\n"
                   f"Details: {json.dumps(threat['details'])}"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(webhook_url, json=message) as response:
                    if response.status != 200:
                        logging.error(f"Failed to send notification: {response.status}")
            except Exception as e:
                logging.error(f"Error sending notification: {str(e)}")
    
    async def cleanup_old_entries(self):
        """Clean up old tracking entries"""
        current_time = datetime.now()
        for ip in list(self.connection_tracker.keys()):
            if (current_time - self.connection_tracker[ip]['last_seen']).total_seconds() > self.config['entry_ttl']:
                del self.connection_tracker[ip]

    async def run(self):
        """Main IDS loop"""
        try:
            logging.info("Starting Network IDS...")
            await self.capture_traffic()
        except Exception as e:
            logging.error(f"Critical error in IDS: {str(e)}")
            raise

# Configuration example (ids_config.yml)
"""
monitor_interface: eth0
max_ports: 20
max_bytes: 1000000000  # 1GB
max_connections: 1000
threat_ttl: 86400  # 24 hours
entry_ttl: 3600   # 1 hour
block_duration: 3600  # 1 hour
webhook_url: "https://hooks.slack.com/services/your/webhook/url"
"""

# Threat patterns example (threat_patterns.yml)
"""
- type: sql_injection
  severity: high
  signature:
    tcp.dstport: 3306
    payload: "UNION SELECT"

- type: xss_attempt
  severity: high
  signature:
    http.request.method: "POST"
    http.request.uri: "script"

- type: directory_traversal
  severity: high
  signature:
    http.request.uri: "../"
"""

# Run the IDS
if __name__ == "__main__":
    ids = NetworkIDS()
    asyncio.run(ids.run())
```

Would you like me to continue with the Mobile Device Configuration and Performance Monitoring sections next?