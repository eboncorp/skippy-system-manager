# Complete Home Cloud Setup Guide - Part 11

## Part 10.6: Bandwidth Management System

### Adaptive Bandwidth Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
import redis
import aiohttp
from datetime import datetime, timedelta
import psutil
import speedtest
from collections import defaultdict
import numpy as np

class BandwidthManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=4)
        self.network_stats = defaultdict(lambda: {
            'download_speed': [],
            'upload_speed': [],
            'latency': [],
            'connection_type': None,
            'quality_profile': 'auto'
        })
        self.load_config()
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/bandwidth_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load bandwidth management configuration"""
        self.config = {
            'speed_test_interval': 3600,  # 1 hour
            'stats_retention': 86400,     # 24 hours
            'quality_profiles': {
                'ultra': {
                    'video_quality': '4K',
                    'bitrate': 25000000,  # 25 Mbps
                    'min_download': 30000000,  # 30 Mbps required
                    'buffer_size': 30,    # 30 seconds
                    'chunk_size': 10485760  # 10 MB
                },
                'high': {
                    'video_quality': '1080p',
                    'bitrate': 8000000,   # 8 Mbps
                    'min_download': 10000000,  # 10 Mbps required
                    'buffer_size': 20,
                    'chunk_size': 5242880  # 5 MB
                },
                'medium': {
                    'video_quality': '720p',
                    'bitrate': 3000000,   # 3 Mbps
                    'min_download': 5000000,  # 5 Mbps required
                    'buffer_size': 15,
                    'chunk_size': 2097152  # 2 MB
                },
                'low': {
                    'video_quality': '480p',
                    'bitrate': 1500000,   # 1.5 Mbps
                    'min_download': 2000000,  # 2 Mbps required
                    'buffer_size': 10,
                    'chunk_size': 1048576  # 1 MB
                }
            }
        }
    
    async def measure_network_speed(self, device_id):
        """Measure current network conditions"""
        try:
            # Initialize speedtest
            st = speedtest.Speedtest()
            
            # Get best server
            st.get_best_server()
            
            # Measure download speed
            download_speed = st.download()
            
            # Measure upload speed
            upload_speed = st.upload()
            
            # Measure latency
            latency = st.results.ping
            
            # Store results
            measurement = {
                'timestamp': datetime.now().isoformat(),
                'download_speed': download_speed,
                'upload_speed': upload_speed,
                'latency': latency
            }
            
            # Update device stats
            self.network_stats[device_id]['download_speed'].append(download_speed)
            self.network_stats[device_id]['upload_speed'].append(upload_speed)
            self.network_stats[device_id]['latency'].append(latency)
            
            # Trim old measurements
            self.trim_measurements(device_id)
            
            # Store in Redis
            self.redis.hset(
                f"network_stats:{device_id}",
                mapping={
                    'current_measurement': json.dumps(measurement),
                    'last_update': datetime.now().isoformat()
                }
            )
            
            return measurement
            
        except Exception as e:
            logging.error(f"Error measuring network speed: {str(e)}")
            return None
    
    def trim_measurements(self, device_id):
        """Keep only recent measurements"""
        cutoff_time = datetime.now() - timedelta(seconds=self.config['stats_retention'])
        
        for metric in ['download_speed', 'upload_speed', 'latency']:
            self.network_stats[device_id][metric] = [
                m for m in self.network_stats[device_id][metric]
                if m['timestamp'] > cutoff_time.isoformat()
            ]
    
    def determine_quality_profile(self, network_stats):
        """Determine optimal quality profile based on network conditions"""
        try:
            # Calculate average speeds and variance
            download_speeds = [m['download_speed'] for m in network_stats['download_speed']]
            avg_download = np.mean(download_speeds) if download_speeds else 0
            speed_variance = np.var(download_speeds) if download_speeds else 0
            
            # Calculate average latency
            latencies = [m['latency'] for m in network_stats['latency']]
            avg_latency = np.mean(latencies) if latencies else 0
            
            # Determine base profile based on download speed
            profile = 'low'
            for level in ['ultra', 'high', 'medium']:
                if (avg_download >= self.config['quality_profiles'][level]['min_download'] and
                    speed_variance < avg_download * 0.2):  # Less than 20% variance
                    profile = level
                    break
            
            # Adjust based on latency
            if avg_latency > 100:  # High latency
                profile = self.downgrade_profile(profile)
            
            return profile
            
        except Exception as e:
            logging.error(f"Error determining quality profile: {str(e)}")
            return 'low'  # Default to low quality on error
    
    def downgrade_profile(self, current_profile):
        """Downgrade quality profile by one level"""
        profiles = ['ultra', 'high', 'medium', 'low']
        current_index = profiles.index(current_profile)
        if current_index < len(profiles) - 1:
            return profiles[current_index + 1]
        return current_profile
    
    async def update_streaming_settings(self, device_id, profile):
        """Update streaming settings for device"""
        try:
            settings = self.config['quality_profiles'][profile]
            
            # Store settings in Redis
            self.redis.hset(
                f"streaming_settings:{device_id}",
                mapping={
                    'profile': profile,
                    'settings': json.dumps(settings),
                    'updated_at': datetime.now().isoformat()
                }
            )
            
            # Send settings to device
            await self.send_device_settings(device_id, settings)
            
        except Exception as e:
            logging.error(f"Error updating streaming settings: {str(e)}")
    
    async def send_device_settings(self, device_id, settings):
        """Send updated settings to device"""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    'http://localhost:8080/push',
                    json={
                        'device_id': device_id,
                        'message': {
                            'type': 'streaming_settings',
                            'data': settings
                        }
                    }
                )
        except Exception as e:
            logging.error(f"Error sending device settings: {str(e)}")
    
    async def monitor_network_usage(self):
        """Monitor network usage across all connections"""
        while True:
            try:
                # Get current network stats
                net_io = psutil.net_io_counters()
                
                # Store in Redis for monitoring
                self.redis.hset(
                    'system_network_stats',
                    mapping={
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'packets_sent': net_io.packets_sent,
                        'packets_recv': net_io.packets_recv,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logging.error(f"Error monitoring network usage: {str(e)}")
                await asyncio.sleep(5)
    
    async def manage_bandwidth(self):
        """Main bandwidth management loop"""
        while True:
            try:
                # Check all registered devices
                device_keys = self.redis.keys("network_stats:*")
                
                for device_key in device_keys:
                    device_id = device_key.decode().split(':')[1]
                    
                    # Measure network conditions
                    measurement = await self.measure_network_speed(device_id)
                    
                    if measurement:
                        # Determine optimal quality profile
                        profile = self.determine_quality_profile(
                            self.network_stats[device_id]
                        )
                        
                        # Update device settings if needed
                        current_profile = self.network_stats[device_id]['quality_profile']
                        if profile != current_profile:
                            await self.update_streaming_settings(device_id, profile)
                            self.network_stats[device_id]['quality_profile'] = profile
                
                await asyncio.sleep(self.config['speed_test_interval'])
                
            except Exception as e:
                logging.error(f"Error in bandwidth management: {str(e)}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start bandwidth management system"""
        logging.info("Starting Bandwidth Management System")
        
        # Start network usage monitoring
        asyncio.create_task(self.monitor_network_usage())
        
        # Start main bandwidth management loop
        await self.manage_bandwidth()

# Run the bandwidth manager
if __name__ == "__main__":
    manager = BandwidthManager()
    asyncio.run(manager.start())
```

I'll continue with the Mobile Cache Management and Network Performance Optimization systems. Would you like me to proceed?