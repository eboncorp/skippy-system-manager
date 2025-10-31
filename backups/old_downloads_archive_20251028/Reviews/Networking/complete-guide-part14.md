# Complete Home Cloud Setup Guide - Part 14

## Part 10.9: QoS Management System

### Quality of Service Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
import numpy as np
from collections import defaultdict
import subprocess
import psutil

class QoSManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=7)
        self.load_config()
        self.service_stats = defaultdict(lambda: {
            'bandwidth': [],
            'latency': [],
            'priority': 'normal',
            'current_allocation': None
        })
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/qos_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load QoS configuration"""
        self.config = {
            'priority_levels': {
                'critical': {
                    'weight': 1.0,
                    'min_bandwidth': 0.3,  # 30% of total
                    'max_latency': 50      # ms
                },
                'high': {
                    'weight': 0.7,
                    'min_bandwidth': 0.2,
                    'max_latency': 100
                },
                'normal': {
                    'weight': 0.5,
                    'min_bandwidth': 0.1,
                    'max_latency': 200
                },
                'low': {
                    'weight': 0.3,
                    'min_bandwidth': 0.05,
                    'max_latency': 500
                }
            },
            'service_priorities': {
                'voip': 'critical',
                'video': 'high',
                'sync': 'normal',
                'backup': 'low'
            },
            'monitoring': {
                'interval': 5,          # seconds
                'history_length': 720,   # 1 hour at 5-second intervals
                'alert_threshold': 0.8   # 80% of limit
            }
        }
    
    async def configure_tc_rules(self):
        """Configure traffic control rules"""
        try:
            # Clear existing rules
            subprocess.run(['tc', 'qdisc', 'del', 'dev', 'eth0', 'root'])
            
            # Create HTB qdisc
            subprocess.run([
                'tc', 'qdisc', 'add', 'dev', 'eth0', 'root', 'handle', '1:',
                'htb', 'default', '40'
            ])
            
            # Configure classes for each priority level
            class_id = 10
            for priority, settings in self.config['priority_levels'].items():
                subprocess.run([
                    'tc', 'class', 'add', 'dev', 'eth0', 'parent', '1:',
                    'classid', f'1:{class_id}', 'htb',
                    'rate', f"{int(settings['min_bandwidth'] * 1000000)}kbit",
                    'ceil', f"{int(settings['weight'] * 1000000)}kbit",
                    'prio', str(class_id // 10)
                ])
                class_id += 10
            
            logging.info("Traffic control rules configured successfully")
            
        except Exception as e:
            logging.error(f"Error configuring traffic control: {str(e)}")
    
    async def monitor_traffic(self):
        """Monitor network traffic and service performance"""
        while True:
            try:
                # Get current network stats
                stats = psutil.net_io_counters()
                current_time = datetime.now()
                
                # Monitor each service
                for service, priority in self.config['service_priorities'].items():
                    # Measure service metrics
                    metrics = await self.measure_service_metrics(service)
                    
                    # Update service stats
                    self.service_stats[service]['bandwidth'].append({
                        'timestamp': current_time.isoformat(),
                        'bytes': metrics['bytes'],
                        'latency': metrics['latency']
                    })
                    
                    # Trim old stats
                    self.service_stats[service]['bandwidth'] = [
                        stat for stat in self.service_stats[service]['bandwidth']
                        if datetime.fromisoformat(stat['timestamp']) > 
                        current_time - timedelta(hours=1)
                    ]
                    
                    # Check for QoS violations
                    await self.check_qos_violations(service, metrics)
                
                await asyncio.sleep(self.config['monitoring']['interval'])
                
            except Exception as e:
                logging.error(f"Error monitoring traffic: {str(e)}")
                await asyncio.sleep(10)
    
    async def measure_service_metrics(self, service):
        """Measure service-specific metrics"""
        try:
            # Example metrics collection (implement based on service type)
            if service == 'voip':
                return await self.measure_voip_metrics()
            elif service == 'video':
                return await self.measure_video_metrics()
            elif service == 'sync':
                return await self.measure_sync_metrics()
            else:
                return await self.measure_default_metrics()
                
        except Exception as e:
            logging.error(f"Error measuring metrics for {service}: {str(e)}")
            return {'bytes': 0, 'latency': 0}
    
    async def measure_voip_metrics(self):
        """Measure VoIP-specific metrics"""
        try:
            # Implement VoIP-specific measurements
            # Example: measure RTP packets, jitter, packet loss
            return {
                'bytes': 0,  # Implement actual measurement
                'latency': 0,  # Implement actual measurement
                'jitter': 0,
                'packet_loss': 0
            }
        except Exception as e:
            logging.error(f"Error measuring VoIP metrics: {str(e)}")
            return {'bytes': 0, 'latency': 0}
    
    async def measure_video_metrics(self):
        """Measure video streaming metrics"""
        try:
            # Implement video streaming measurements
            # Example: measure bitrate, buffer status, quality switches
            return {
                'bytes': 0,  # Implement actual measurement
                'latency': 0,  # Implement actual measurement
                'bitrate': 0,
                'buffer_level': 0
            }
        except Exception as e:
            logging.error(f"Error measuring video metrics: {str(e)}")
            return {'bytes': 0, 'latency': 0}
    
    async def check_qos_violations(self, service, metrics):
        """Check for QoS violations and adjust if needed"""
        try:
            priority = self.config['service_priorities'][service]
            limits = self.config['priority_levels'][priority]
            
            violations = []
            
            # Check latency violation
            if metrics['latency'] > limits['max_latency']:
                violations.append({
                    'type': 'latency',
                    'value': metrics['latency'],
                    'limit': limits['max_latency']
                })
            
            # Check bandwidth violation
            bandwidth_usage = self.calculate_bandwidth_usage(service)
            if bandwidth_usage < limits['min_bandwidth']:
                violations.append({
                    'type': 'bandwidth',
                    'value': bandwidth_usage,
                    'limit': limits['min_bandwidth']
                })
            
            if violations:
                await self.handle_qos_violations(service, violations)
            
        except Exception as e:
            logging.error(f"Error checking QoS violations: {str(e)}")
    
    def calculate_bandwidth_usage(self, service):
        """Calculate current bandwidth usage for service"""
        try:
            stats = self.service_stats[service]['bandwidth']
            if not stats:
                return 0
            
            recent_stats = [
                stat for stat in stats
                if datetime.fromisoformat(stat['timestamp']) >
                datetime.now() - timedelta(minutes=1)
            ]
            
            if not recent_stats:
                return 0
            
            total_bytes = sum(stat['bytes'] for stat in recent_stats)
            time_period = (
                datetime.fromisoformat(recent_stats[-1]['timestamp']) -
                datetime.fromisoformat(recent_stats[0]['timestamp'])
            ).total_seconds()
            
            return total_bytes / time_period if time_period > 0 else 0
            
        except Exception as e:
            logging.error(f"Error calculating bandwidth usage: {str(e)}")
            return 0
    
    async def handle_qos_violations(self, service, violations):
        """Handle QoS violations"""
        try:
            # Log violations
            logging.warning(f"QoS violations detected for {service}: {violations}")
            
            # Store violation record
            violation_record = {
                'timestamp': datetime.now().isoformat(),
                'service': service,
                'violations': violations
            }
            self.redis.lpush('qos_violations', json.dumps(violation_record))
            
            # Apply mitigation strategies
            for violation in violations:
                if violation['type'] == 'latency':
                    await self.mitigate_latency_violation(service, violation)
                elif violation['type'] == 'bandwidth':
                    await self.mitigate_bandwidth_violation(service, violation)
            
            # Send alert if needed
            await self.send_qos_alert(service, violations)
            
        except Exception as e:
            logging.error(f"Error handling QoS violations: {str(e)}")
    
    async def mitigate_latency_violation(self, service, violation):
        """Mitigate latency violation"""
        try:
            # Example mitigation strategies
            if service == 'voip':
                # Increase priority temporarily
                await self.adjust_service_priority(service, 'critical')
            elif service == 'video':
                # Reduce quality temporarily
                await self.adjust_video_quality(service, 'lower')
            
        except Exception as e:
            logging.error(f"Error mitigating latency violation: {str(e)}")
    
    async def mitigate_bandwidth_violation(self, service, violation):
        """Mitigate bandwidth violation"""
        try:
            # Example mitigation strategies
            if service == 'sync':
                # Reduce sync frequency
                await self.adjust_sync_frequency(service, 'reduce')
            elif service == 'backup':
                # Pause backup temporarily
                await self.pause_backup_service(service)
            
        except Exception as e:
            logging.error(f"Error mitigating bandwidth violation: {str(e)}")
    
    async def adjust_service_priority(self, service, new_priority):
        """Adjust service priority"""
        try:
            # Update TC rules for the service
            subprocess.run([
                'tc', 'filter', 'add', 'dev', 'eth0', 'parent', '1:0',
                'protocol', 'ip', 'prio', '1', 'u32',
                'match', 'ip', 'sport', str(self.get_service_port(service)),
                'flowid', f'1:{self.get_priority_class(new_priority)}'
            ])
            
            # Update service status
            self.service_stats[service]['priority'] = new_priority
            
            logging.info(f"Adjusted priority for {service} to {new_priority}")
            
        except Exception as e:
            logging.error(f"Error adjusting service priority: {str(e)}")
    
    def get_service_port(self, service):
        """Get port number for service"""
        # Implement service-to-port mapping
        service_ports = {
            'voip': 5060,
            'video': 1935,
            'sync': 8384,
            'backup': 8200
        }
        return service_ports.get(service, 0)
    
    def get_priority_class(self, priority):
        """Get TC class ID for priority level"""
        priority_classes = {
            'critical': 10,
            'high': 20,
            'normal': 30,
            'low': 40
        }
        return priority_classes.get(priority, 40)
    
    async def send_qos_alert(self, service, violations):
        """Send alert for QoS violations"""
        try:
            alert = {
                'service': service,
                'violations': violations,
                'timestamp': datetime.now().isoformat(),
                'recommendations': await self.generate_recommendations(
                    service,
                    violations
                )
            }
            
            # Store alert in Redis
            self.redis.lpush('qos_alerts', json.dumps(alert))
            
            # Send notification if configured
            # Implement notification logic (email, webhook, etc.)
            
        except Exception as e:
            logging.error(f"Error sending QoS alert: {str(e)}")
    
    async def generate_recommendations(self, service, violations):
        """Generate recommendations for QoS violations"""
        try:
            recommendations = []
            
            for violation in violations:
                if violation['type'] == 'latency':
                    recommendations.extend([
                        "Check network congestion",
                        "Verify service priority settings",
                        "Consider upgrading bandwidth"
                    ])
                elif violation['type'] == 'bandwidth':
                    recommendations.extend([
                        "Adjust service scheduling",
                        "Review bandwidth allocation",
                        "Consider service degradation"
                    ])
            
            return list(set(recommendations))  # Remove duplicates
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {str(e)}")
            return []

    async def start(self):
        """Start the QoS manager"""
        logging.info("Starting QoS Manager")
        
        # Configure initial TC rules
        await self.configure_tc_rules()
        
        # Start monitoring
        await self.monitor_traffic()

# Run the QoS manager
if __name__ == "__main__":
    manager = QoSManager()
    asyncio.run(manager.start())
```

I'll continue with the Application-Specific Optimizations system next. Would you like me to proceed?