# Complete Home Cloud Setup Guide - Part 17

## Part 10.12: Power-Aware Scheduling and Caching System

### Power-Aware Scheduler
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
from enum import Enum

class PowerState(Enum):
    CRITICAL = "critical"
    LOW = "low"
    NORMAL = "normal"
    OPTIMAL = "optimal"

class PowerAwareScheduler:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=10)
        self.load_config()
        self.power_state = PowerState.NORMAL
        self.device_profiles = {}
        self.task_history = defaultdict(list)
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/power_scheduler.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load power management configuration"""
        self.config = {
            'power_states': {
                'critical': {
                    'battery_threshold': 15,
                    'cpu_limit': 0.3,
                    'memory_limit': 0.5,
                    'network_limit': 0.2,
                    'task_concurrency': 1
                },
                'low': {
                    'battery_threshold': 30,
                    'cpu_limit': 0.5,
                    'memory_limit': 0.7,
                    'network_limit': 0.4,
                    'task_concurrency': 2
                },
                'normal': {
                    'battery_threshold': 50,
                    'cpu_limit': 0.7,
                    'memory_limit': 0.8,
                    'network_limit': 0.6,
                    'task_concurrency': 3
                },
                'optimal': {
                    'battery_threshold': 80,
                    'cpu_limit': 0.9,
                    'memory_limit': 0.9,
                    'network_limit': 0.8,
                    'task_concurrency': 4
                }
            },
            'task_profiles': {
                'backup': {
                    'min_battery': 30,
                    'cpu_weight': 0.5,
                    'memory_weight': 0.3,
                    'network_weight': 0.7,
                    'deferrable': True
                },
                'sync': {
                    'min_battery': 20,
                    'cpu_weight': 0.3,
                    'memory_weight': 0.2,
                    'network_weight': 0.8,
                    'deferrable': True
                },
                'streaming': {
                    'min_battery': 15,
                    'cpu_weight': 0.6,
                    'memory_weight': 0.4,
                    'network_weight': 0.9,
                    'deferrable': False
                },
                'indexing': {
                    'min_battery': 40,
                    'cpu_weight': 0.8,
                    'memory_weight': 0.6,
                    'network_weight': 0.2,
                    'deferrable': True
                }
            },
            'scheduling': {
                'prediction_window': 3600,  # 1 hour
                'min_battery_reserve': 10,
                'power_trend_samples': 12,
                'task_history_size': 100
            }
        }
    
    async def update_power_state(self, device_id: str):
        """Update power state based on current battery status"""
        try:
            battery_status = await self.get_battery_status(device_id)
            charging = battery_status['charging']
            level = battery_status['level']
            
            # Determine power state
            if charging:
                self.power_state = PowerState.OPTIMAL
            else:
                for state in PowerState:
                    if level <= self.config['power_states'][state.value]['battery_threshold']:
                        self.power_state = state
                        break
            
            # Update device profile
            await self.update_device_profile(device_id, battery_status)
            
            # Log state change
            logging.info(f"Power state updated for device {device_id}: {self.power_state}")
            
            return self.power_state
            
        except Exception as e:
            logging.error(f"Error updating power state: {str(e)}")
            return PowerState.NORMAL  # Default to normal state
    
    async def update_device_profile(self, device_id: str, battery_status: Dict):
        """Update device power profile"""
        try:
            # Get historical power data
            power_history = self.redis.lrange(f"power_history:{device_id}", 0, 
                                            self.config['scheduling']['power_trend_samples'])
            
            # Calculate power trend
            power_trend = self.calculate_power_trend(power_history)
            
            # Update profile
            profile = {
                'power_state': self.power_state.value,
                'battery_level': battery_status['level'],
                'charging': battery_status['charging'],
                'power_trend': power_trend,
                'last_update': datetime.now().isoformat()
            }
            
            # Store profile
            self.device_profiles[device_id] = profile
            self.redis.hset(f"device_profile:{device_id}", mapping=profile)
            
        except Exception as e:
            logging.error(f"Error updating device profile: {str(e)}")
    
    def calculate_power_trend(self, power_history: List) -> float:
        """Calculate power consumption trend"""
        try:
            if not power_history:
                return 0.0
            
            # Convert history to numeric values
            values = [float(entry) for entry in power_history]
            
            # Calculate trend using linear regression
            x = list(range(len(values)))
            x_mean = sum(x) / len(x)
            y_mean = sum(values) / len(values)
            
            numerator = sum((x[i] - x_mean) * (values[i] - y_mean) 
                          for i in range(len(values)))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(len(values)))
            
            return numerator / denominator if denominator != 0 else 0.0
            
        except Exception as e:
            logging.error(f"Error calculating power trend: {str(e)}")
            return 0.0
    
    async def can_schedule_task(self, task: Dict, device_id: str) -> bool:
        """Check if task can be scheduled based on power state"""
        try:
            profile = self.device_profiles.get(device_id)
            if not profile:
                return True  # Default to allowing if no profile exists
            
            task_profile = self.config['task_profiles'].get(task['type'])
            if not task_profile:
                return True  # Default to allowing if no task profile exists
            
            # Check battery level
            if (not profile['charging'] and 
                profile['battery_level'] < task_profile['min_battery']):
                return False
            
            # Check resource availability
            power_state_config = self.config['power_states'][profile['power_state']]
            resource_usage = await self.get_resource_usage(device_id)
            
            # Calculate weighted resource availability
            cpu_available = power_state_config['cpu_limit'] - resource_usage['cpu']
            memory_available = power_state_config['memory_limit'] - resource_usage['memory']
            network_available = power_state_config['network_limit'] - resource_usage['network']
            
            weighted_availability = (
                cpu_available * task_profile['cpu_weight'] +
                memory_available * task_profile['memory_weight'] +
                network_available * task_profile['network_weight']
            ) / (task_profile['cpu_weight'] + 
                 task_profile['memory_weight'] + 
                 task_profile['network_weight'])
            
            return weighted_availability > 0
            
        except Exception as e:
            logging.error(f"Error checking task scheduling: {str(e)}")
            return False
    
    async def predict_power_availability(self, device_id: str, 
                                       duration: int) -> Dict[str, float]:
        """Predict power availability for given duration"""
        try:
            profile = self.device_profiles.get(device_id)
            if not profile:
                return {'probability': 0.5, 'confidence': 0.0}
            
            # Calculate factors
            power_trend = profile['power_trend']
            battery_level = profile['battery_level']
            charging = profile['charging']
            
            if charging:
                return {'probability': 1.0, 'confidence': 0.9}
            
            # Predict battery level after duration
            predicted_level = battery_level + (power_trend * duration / 3600)
            
            # Calculate probability and confidence
            probability = max(0, min(1, predicted_level / 100))
            confidence = 1.0 - (duration / (24 * 3600))  # Decreases with duration
            
            return {
                'probability': probability,
                'confidence': confidence
            }
            
        except Exception as e:
            logging.error(f"Error predicting power availability: {str(e)}")
            return {'probability': 0.5, 'confidence': 0.0}
    
    async def optimize_task_scheduling(self, device_id: str, tasks: List[Dict]):
        """Optimize task scheduling based on power state"""
        try:
            optimized_schedule = []
            profile = self.device_profiles.get(device_id)
            
            if not profile:
                return tasks  # Return original schedule if no profile exists
            
            # Sort tasks by priority and power requirements
            sorted_tasks = sorted(
                tasks,
                key=lambda t: (
                    self.get_task_priority(t),
                    self.get_task_power_requirement(t)
                )
            )
            
            current_time = datetime.now()
            available_power = profile['battery_level']
            
            for task in sorted_tasks:
                task_profile = self.config['task_profiles'].get(task['type'])
                if not task_profile:
                    optimized_schedule.append(task)
                    continue
                
                # Check if task can be deferred
                if task_profile['deferrable']:
                    # Predict power availability
                    prediction = await self.predict_power_availability(
                        device_id,
                        task.get('estimated_duration', 3600)
                    )
                    
                    if prediction['probability'] < 0.7:
                        # Defer task
                        task['deferred'] = True
                        task['defer_reason'] = 'power_conservation'
                        continue
                
                # Schedule task if power available
                if available_power >= task_profile['min_battery']:
                    optimized_schedule.append(task)
                    available_power -= self.estimate_power_consumption(task)
            
            return optimized_schedule
            
        except Exception as e:
            logging.error(f"Error optimizing task schedule: {str(e)}")
            return tasks
    
    def get_task_priority(self, task: Dict) -> int:
        """Get task priority value"""
        priority_map = {
            'critical': 0,
            'high': 1,
            'normal': 2,
            'low': 3
        }
        return priority_map.get(task.get('priority', 'normal'), 2)
    
    def get_task_power_requirement(self, task: Dict) -> float:
        """Get task power requirement score"""
        task_profile = self.config['task_profiles'].get(task['type'])
        if not task_profile:
            return 0.5
        
        return (task_profile['cpu_weight'] +
                task_profile['memory_weight'] +
                task_profile['network_weight']) / 3
    
    def estimate_power_consumption(self, task: Dict) -> float:
        """Estimate power consumption for task"""
        task_profile = self.config['task_profiles'].get(task['type'])
        if not task_profile:
            return 0.0
        
        base_consumption = (
            task_profile['cpu_weight'] * 0.1 +
            task_profile['memory_weight'] * 0.05 +
            task_profile['network_weight'] * 0.15
        )
        
        duration_factor = task.get('estimated_duration', 3600) / 3600
        return base_consumption * duration_factor

    async def start(self):
        """Start the power-aware scheduler"""
        try:
            logging.info("Starting Power-Aware Scheduler")
            while True:
                # Update all device states
                for device_id in self.device_profiles.keys():
                    await self.update_power_state(device_id)
                
                # Sleep for update interval
                await asyncio.sleep(60)
                
        except Exception as e:
            logging.error(f"Error in power-aware scheduler: {str(e)}")
            raise

# Run the power-aware scheduler
if __name__ == "__main__":
    scheduler = PowerAwareScheduler()
    asyncio.run(scheduler.start())
```

I'll continue with the Application-Specific Caching system next. Would you like me to proceed?