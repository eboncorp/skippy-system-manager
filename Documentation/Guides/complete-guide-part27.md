# Complete Home Cloud Setup Guide - Part 27

## Part 10.22: Traffic Management System

### Traffic Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
from collections import defaultdict
import numpy as np
from typing import Dict, List, Any, Optional
from enum import Enum
import aiohttp
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery

class ThrottleLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class RateLimitConfig:
    requests_per_second: int
    burst_size: int
    window_size: int
    client_id: str
    priority: int

class TrafficManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=20)
        self.load_config()
        self.setup_rate_limiters()
        self.setup_circuit_breakers()
        self.setup_metrics()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/traffic_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        """Load traffic management configuration"""
        self.config = {
            'rate_limiting': {
                'enabled': True,
                'default_limits': {
                    'requests_per_second': 1000,
                    'burst_size': 2000,
                    'window_size': 1
                },
                'priority_multipliers': {
                    'critical': 2.0,
                    'high': 1.5,
                    'normal': 1.0,
                    'low': 0.5
                },
                'client_specific': {
                    'premium': {
                        'requests_per_second': 5000,
                        'burst_size': 10000,
                        'window_size': 1
                    },
                    'basic': {
                        'requests_per_second': 1000,
                        'burst_size': 2000,
                        'window_size': 1
                    }
                }
            },
            'circuit_breaker': {
                'error_threshold': 0.5,  # 50% error rate
                'min_requests': 10,
                'reset_timeout': 30,  # seconds
                'half_open_timeout': 60,  # seconds
                'max_retries': 3,
                'backoff_factor': 2,
                'service_groups': {
                    'critical': {
                        'error_threshold': 0.7,
                        'reset_timeout': 15
                    },
                    'non_critical': {
                        'error_threshold': 0.5,
                        'reset_timeout': 30
                    }
                }
            },
            'throttling': {
                'enabled': True,
                'thresholds': {
                    'cpu': {
                        'low': 0.6,
                        'medium': 0.7,
                        'high': 0.8,
                        'critical': 0.9
                    },
                    'memory': {
                        'low': 0.7,
                        'medium': 0.8,
                        'high': 0.9,
                        'critical': 0.95
                    },
                    'io': {
                        'low': 0.6,
                        'medium': 0.7,
                        'high': 0.8,
                        'critical': 0.9
                    }
                },
                'actions': {
                    'low': {
                        'rate_limit_multiplier': 0.8,
                        'max_concurrent': 100
                    },
                    'medium': {
                        'rate_limit_multiplier': 0.6,
                        'max_concurrent': 50
                    },
                    'high': {
                        'rate_limit_multiplier': 0.4,
                        'max_concurrent': 25
                    },
                    'critical': {
                        'rate_limit_multiplier': 0.2,
                        'max_concurrent': 10
                    }
                }
            },
            'failure_recovery': {
                'retry_strategies': {
                    'immediate': {
                        'attempts': 3,
                        'delay': 0
                    },
                    'linear_backoff': {
                        'attempts': 3,
                        'base_delay': 1,
                        'increment': 2
                    },
                    'exponential_backoff': {
                        'attempts': 3,
                        'base_delay': 1,
                        'multiplier': 2
                    }
                },
                'fallback_options': {
                    'cache_fallback': True,
                    'degraded_mode': True,
                    'alternative_endpoints': True
                }
            }
        }
        
    def setup_rate_limiters(self):
        """Initialize rate limiting components"""
        self.rate_limiters = {}
        self.rate_limit_counters = defaultdict(lambda: defaultdict(int))
        self.rate_limit_windows = defaultdict(dict)
        
    def setup_circuit_breakers(self):
        """Initialize circuit breakers"""
        self.circuit_breakers = defaultdict(lambda: {
            'state': CircuitState.CLOSED,
            'failures': 0,
            'last_failure_time': None,
            'last_success_time': None,
            'half_open_attempts': 0
        })
        
    def setup_metrics(self):
        """Initialize metrics tracking"""
        self.metrics = {
            'rate_limiting': defaultdict(lambda: {
                'requests': 0,
                'throttled': 0,
                'allowed': 0
            }),
            'circuit_breaker': defaultdict(lambda: {
                'failures': 0,
                'successes': 0,
                'state_changes': []
            }),
            'throttling': defaultdict(lambda: {
                'level': ThrottleLevel.NONE,
                'duration': 0,
                'impact': 0
            })
        }
        
    async def check_rate_limit(self, client_id: str, priority: str) -> bool:
        """Check if request is within rate limits"""
        try:
            # Get rate limit configuration
            config = self.get_rate_limit_config(client_id, priority)
            
            # Get current window
            current_time = datetime.now().timestamp()
            window_key = int(current_time / config.window_size)
            
            # Clean up old windows
            await self.cleanup_old_windows(client_id, window_key)
            
            # Check current window count
            current_count = self.rate_limit_counters[client_id][window_key]
            
            # Check if within limits
            if current_count >= config.requests_per_second:
                # Check burst allowance
                if current_count >= config.burst_size:
                    self.metrics['rate_limiting'][client_id]['throttled'] += 1
                    return False
                    
            # Increment counter
            self.rate_limit_counters[client_id][window_key] += 1
            self.metrics['rate_limiting'][client_id]['allowed'] += 1
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking rate limit: {str(e)}")
            return False
    
    def get_rate_limit_config(self, client_id: str, priority: str) -> RateLimitConfig:
        """Get rate limit configuration for client"""
        try:
            # Check for client-specific config
            if client_id in self.config['rate_limiting']['client_specific']:
                base_config = self.config['rate_limiting']['client_specific'][client_id]
            else:
                base_config = self.config['rate_limiting']['default_limits']
            
            # Apply priority multiplier
            multiplier = self.config['rate_limiting']['priority_multipliers'].get(
                priority,
                1.0
            )
            
            return RateLimitConfig(
                requests_per_second=int(base_config['requests_per_second'] * multiplier),
                burst_size=int(base_config['burst_size'] * multiplier),
                window_size=base_config['window_size'],
                client_id=client_id,
                priority=priority
            )
            
        except Exception as e:
            logging.error(f"Error getting rate limit config: {str(e)}")
            return RateLimitConfig(
                requests_per_second=100,
                burst_size=200,
                window_size=1,
                client_id=client_id,
                priority='normal'
            )
    
    async def cleanup_old_windows(self, client_id: str, current_window: int):
        """Clean up old rate limit windows"""
        try:
            # Remove windows older than current
            old_windows = [
                window for window in self.rate_limit_counters[client_id].keys()
                if window < current_window
            ]
            
            for window in old_windows:
                del self.rate_limit_counters[client_id][window]
                
        except Exception as e:
            logging.error(f"Error cleaning up old windows: {str(e)}")
    
    async def check_circuit_breaker(self, service: str) -> bool:
        """Check if service circuit breaker allows requests"""
        try:
            breaker = self.circuit_breakers[service]
            
            if breaker['state'] == CircuitState.OPEN:
                # Check if reset timeout has elapsed
                if await self.should_reset_circuit(service):
                    await self.transition_to_half_open(service)
                else:
                    return False
                    
            elif breaker['state'] == CircuitState.HALF_OPEN:
                # Allow limited requests in half-open state
                if breaker['half_open_attempts'] >= self.config['circuit_breaker']['min_requests']:
                    return False
                    
            return True
            
        except Exception as e:
            logging.error(f"Error checking circuit breaker: {str(e)}")
            return True
    
    async def should_reset_circuit(self, service: str) -> bool:
        """Check if circuit breaker should be reset"""
        try:
            breaker = self.circuit_breakers[service]
            if not breaker['last_failure_time']:
                return True
                
            reset_timeout = self.get_reset_timeout(service)
            time_since_failure = (
                datetime.now() - breaker['last_failure_time']
            ).total_seconds()
            
            return time_since_failure >= reset_timeout
            
        except Exception as e:
            logging.error(f"Error checking circuit reset: {str(e)}")
            return True
    
    async def record_success(self, service: str):
        """Record successful request"""
        try:
            breaker = self.circuit_breakers[service]
            breaker['last_success_time'] = datetime.now()
            
            if breaker['state'] == CircuitState.HALF_OPEN:
                breaker['half_open_attempts'] += 1
                
                # Check if we should close the circuit
                if breaker['half_open_attempts'] >= self.config['circuit_breaker']['min_requests']:
                    if await self.check_error_rate(service):
                        await self.transition_to_closed(service)
                    else:
                        await self.transition_to_open(service)
                        
            # Update metrics
            self.metrics['circuit_breaker'][service]['successes'] += 1
            
        except Exception as e:
            logging.error(f"Error recording success: {str(e)}")
    
    async def record_failure(self, service: str, error: Exception):
        """Record failed request"""
        try:
            breaker = self.circuit_breakers[service]
            breaker['failures'] += 1
            breaker['last_failure_time'] = datetime.now()
            
            # Check if we should open the circuit
            if breaker['state'] == CircuitState.CLOSED:
                if await self.check_error_rate(service):
                    await self.transition_to_open(service)
                    
            elif breaker['state'] == CircuitState.HALF_OPEN:
                await self.transition_to_open(service)
            
            # Update metrics
            self.metrics['circuit_breaker'][service]['failures'] += 1
            
        except Exception as e:
            logging.error(f"Error recording failure: {str(e)}")
    
    async def check_error_rate(self, service: str) -> bool:
        """Check if error rate exceeds threshold"""
        try:
            breaker = self.circuit_breakers[service]
            total_requests = (
                self.metrics['circuit_breaker'][service]['successes'] +
                self.metrics['circuit_breaker'][service]['failures']
            )
            
            if total_requests < self.config['circuit_breaker']['min_requests']:
                return False
                
            error_rate = breaker['failures'] / total_requests
            threshold = self.get_error_threshold(service)
            
            return error_rate >= threshold
            
        except Exception as e:
            logging.error(f"Error checking error rate: {str(e)}")
            return False
    
    def get_error_threshold(self, service: str) -> float:
        """Get error threshold for service"""
        try:
            # Check service group configuration
            for group, config in self.config['circuit_breaker']['service_groups'].items():
                if service.startswith(group):
                    return config['error_threshold']
            
            return self.config['circuit_breaker']['error_threshold']
            
        except Exception as e:
            logging.error(f"Error getting error threshold: {str(e)}")
            return 0.5
    
    def get_reset_timeout(self, service: str) -> int:
        """Get reset timeout for service"""
        try:
            # Check service group configuration
            for group, config in self.config['circuit_breaker']['service_groups'].items():
                if service.startswith(group):
                    return config['reset_timeout']
            
            return self.config['circuit_breaker']['reset_timeout']
            
        except Exception as e:
            logging.error(f"Error getting reset timeout: {str(e)}")
            return 30

    async def start(self):
        """Start the traffic manager"""
        try:
            logging.info("Starting Traffic Manager")
            
            # Start background tasks
            asyncio.create_task(self.monitor_resources())
            asyncio.create_task(self.update_metrics())
            
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Error in traffic manager: {str(e)}")
            raise

# Run the traffic manager
if __name__ == "__main__":
    manager = TrafficManager()
    asyncio.run(manager.start())
```

I'll continue with the Resource Monitoring System implementation next. Would you like me to proceed?