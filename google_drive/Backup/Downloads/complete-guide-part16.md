# Complete Home Cloud Setup Guide - Part 16

## Part 10.11: Background Task and Power Management

### Background Task Scheduler
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
from collections import defaultdict
import psutil
import aiohttp
from typing import Dict, List, Any
import heapq

class BackgroundTaskManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=9)
        self.load_config()
        self.task_queue = []
        self.running_tasks = {}
        self.resource_monitor = ResourceMonitor()
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/task_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load task management configuration"""
        self.config = {
            'scheduling': {
                'max_concurrent_tasks': {
                    'critical': 3,
                    'high': 2,
                    'normal': 1,
                    'low': 1
                },
                'time_windows': {
                    'peak': {
                        'start': '08:00',
                        'end': '22:00',
                        'resource_limit': 0.5  # 50% of resources
                    },
                    'off_peak': {
                        'start': '22:00',
                        'end': '08:00',
                        'resource_limit': 0.8  # 80% of resources
                    }
                }
            },
            'resources': {
                'cpu_limit': 0.7,  # 70% max CPU usage
                'memory_limit': 0.8,  # 80% max memory usage
                'io_limit': 0.6,    # 60% max I/O usage
                'network_limit': 0.5  # 50% max network bandwidth
            },
            'power': {
                'battery_thresholds': {
                    'critical': 15,
                    'low': 30,
                    'normal': 50,
                    'high': 80
                },
                'power_profiles': {
                    'battery_critical': {
                        'cpu_limit': 0.3,
                        'task_concurrency': 1,
                        'network_limit': 0.2
                    },
                    'battery_low': {
                        'cpu_limit': 0.5,
                        'task_concurrency': 2,
                        'network_limit': 0.3
                    },
                    'battery_normal': {
                        'cpu_limit': 0.7,
                        'task_concurrency': 3,
                        'network_limit': 0.5
                    },
                    'charging': {
                        'cpu_limit': 0.9,
                        'task_concurrency': 4,
                        'network_limit': 0.8
                    }
                }
            },
            'task_priorities': {
                'backup': 'high',
                'sync': 'normal',
                'maintenance': 'low',
                'indexing': 'low'
            }
        }

    async def schedule_task(self, task: Dict):
        """Schedule a new background task"""
        try:
            # Assign priority and timestamp
            task['priority'] = self.get_task_priority(task['type'])
            task['scheduled_time'] = datetime.now().isoformat()
            task['status'] = 'pending'
            
            # Add to queue
            heapq.heappush(
                self.task_queue,
                (self.priority_value(task['priority']), task)
            )
            
            # Store task in Redis
            self.redis.hset(
                f"task:{task['id']}",
                mapping=task
            )
            
            # Trigger task processing
            await self.process_task_queue()
            
        except Exception as e:
            logging.error(f"Error scheduling task: {str(e)}")
    
    def get_task_priority(self, task_type: str) -> str:
        """Get priority for task type"""
        return self.config['task_priorities'].get(task_type, 'normal')
    
    def priority_value(self, priority: str) -> int:
        """Convert priority string to numeric value"""
        priority_map = {
            'critical': 0,
            'high': 1,
            'normal': 2,
            'low': 3
        }
        return priority_map.get(priority, 99)

    async def process_task_queue(self):
        """Process pending tasks in queue"""
        try:
            while self.task_queue:
                # Check resource availability
                if not await self.can_start_new_task():
                    break
                
                # Get highest priority task
                _, task = heapq.heappop(self.task_queue)
                
                # Start task execution
                asyncio.create_task(self.execute_task(task))
                
        except Exception as e:
            logging.error(f"Error processing task queue: {str(e)}")
    
    async def can_start_new_task(self) -> bool:
        """Check if new task can be started"""
        try:
            # Get current resource usage
            resources = await self.resource_monitor.get_resource_usage()
            
            # Get current time window
            window = self.get_current_time_window()
            
            # Get power profile
            power_profile = await self.get_power_profile()
            
            # Check resource limits
            if (resources['cpu'] > power_profile['cpu_limit'] or
                resources['memory'] > self.config['resources']['memory_limit'] or
                resources['io'] > self.config['resources']['io_limit']):
                return False
            
            # Check concurrent task limit
            current_tasks = len(self.running_tasks)
            if current_tasks >= power_profile['task_concurrency']:
                return False
            
            # Check time window restrictions
            if current_tasks >= window['resource_limit'] * power_profile['task_concurrency']:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking task start availability: {str(e)}")
            return False
    
    def get_current_time_window(self) -> Dict:
        """Get current time window configuration"""
        current_time = datetime.now().strftime('%H:%M')
        
        for window_name, window in self.config['scheduling']['time_windows'].items():
            if self.is_time_in_window(current_time, window['start'], window['end']):
                return window
        
        return self.config['scheduling']['time_windows']['off_peak']
    
    def is_time_in_window(self, current: str, start: str, end: str) -> bool:
        """Check if current time is within window"""
        if start <= end:
            return start <= current <= end
        else:  # Window crosses midnight
            return current >= start or current <= end
    
    async def get_power_profile(self) -> Dict:
        """Get current power profile based on battery status"""
        try:
            battery = await self.resource_monitor.get_battery_status()
            
            if battery['charging']:
                return self.config['power']['power_profiles']['charging']
            
            # Select profile based on battery level
            for threshold, profile_name in [
                ('critical', 'battery_critical'),
                ('low', 'battery_low'),
                ('normal', 'battery_normal')
            ]:
                if battery['level'] <= self.config['power']['battery_thresholds'][threshold]:
                    return self.config['power']['power_profiles'][profile_name]
            
            return self.config['power']['power_profiles']['battery_normal']
            
        except Exception as e:
            logging.error(f"Error getting power profile: {str(e)}")
            return self.config['power']['power_profiles']['battery_low']  # Conservative default

    async def execute_task(self, task: Dict):
        """Execute a background task"""
        try:
            # Update task status
            task['status'] = 'running'
            task['start_time'] = datetime.now().isoformat()
            self.running_tasks[task['id']] = task
            
            # Update Redis
            self.redis.hset(
                f"task:{task['id']}",
                mapping=task
            )
            
            # Execute task based on type
            result = await self.execute_task_by_type(task)
            
            # Update task completion
            task['status'] = 'completed' if result['success'] else 'failed'
            task['end_time'] = datetime.now().isoformat()
            task['result'] = result
            
            # Update Redis and remove from running tasks
            self.redis.hset(
                f"task:{task['id']}",
                mapping=task
            )
            del self.running_tasks[task['id']]
            
            # Process next task
            await self.process_task_queue()
            
        except Exception as e:
            logging.error(f"Error executing task: {str(e)}")
            task['status'] = 'failed'
            task['error'] = str(e)
            self.redis.hset(
                f"task:{task['id']}",
                mapping=task
            )
    
    async def execute_task_by_type(self, task: Dict) -> Dict:
        """Execute specific task type"""
        task_handlers = {
            'backup': self.execute_backup_task,
            'sync': self.execute_sync_task,
            'maintenance': self.execute_maintenance_task,
            'indexing': self.execute_indexing_task
        }
        
        handler = task_handlers.get(task['type'])
        if handler:
            return await handler(task)
        else:
            return {'success': False, 'error': 'Unknown task type'}
    
    async def execute_backup_task(self, task: Dict) -> Dict:
        """Execute backup task"""
        try:
            # Implement backup logic
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def execute_sync_task(self, task: Dict) -> Dict:
        """Execute sync task"""
        try:
            # Implement sync logic
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def execute_maintenance_task(self, task: Dict) -> Dict:
        """Execute maintenance task"""
        try:
            # Implement maintenance logic
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def execute_indexing_task(self, task: Dict) -> Dict:
        """Execute indexing task"""
        try:
            # Implement indexing logic
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class ResourceMonitor:
    """Monitor system resources"""
    
    async def get_resource_usage(self) -> Dict:
        """Get current resource usage"""
        try:
            return {
                'cpu': psutil.cpu_percent() / 100,
                'memory': psutil.virtual_memory().percent / 100,
                'io': self.get_io_usage(),
                'network': self.get_network_usage()
            }
        except Exception as e:
            logging.error(f"Error getting resource usage: {str(e)}")
            return {'cpu': 0, 'memory': 0, 'io': 0, 'network': 0}
    
    def get_io_usage(self) -> float:
        """Get I/O usage percentage"""
        try:
            io_counters = psutil.disk_io_counters()
            return min(io_counters.read_bytes + io_counters.write_bytes / 1e7, 1.0)
        except:
            return 0
    
    def get_network_usage(self) -> float:
        """Get network usage percentage"""
        try:
            net_counters = psutil.net_io_counters()
            return min(net_counters.bytes_sent + net_counters.bytes_recv / 1e7, 1.0)
        except:
            return 0
    
    async def get_battery_status(self) -> Dict:
        """Get battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    'level': battery.percent,
                    'charging': battery.power_plugged,
                    'time_left': battery.secsleft if battery.secsleft >= 0 else None
                }
            return {
                'level': 100,
                'charging': True,
                'time_left': None
            }
        except:
            return {
                'level': 100,
                'charging': True,
                'time_left': None
            }

# Run the task manager
if __name__ == "__main__":
    manager = BackgroundTaskManager()
    asyncio.run(manager.start())
```

I'll continue with the Power-Aware Scheduling system and Application-Specific Caching components. Would you like me to proceed?