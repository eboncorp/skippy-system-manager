# Complete Home Cloud Setup Guide - Part 26

## Part 10.21: Load Balancing System

### Load Balancer Engine
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
import aiojobs
from dataclasses import dataclass

class BalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RESPONSE = "weighted_response"
    RESOURCE_BASED = "resource_based"

class QueuePriority(Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class RequestContext:
    id: str
    priority: QueuePriority
    timestamp: datetime
    size: int
    timeout: float
    retries: int
    metadata: Dict

class LoadBalancer:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=19)
        self.load_config()
        self.setup_queues()
        self.setup_metrics()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/load_balancer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def load_config(self):
        """Load load balancer configuration"""
        self.config = {
            'request_distribution': {
                'strategies': {
                    'round_robin': {
                        'enabled': True,
                        'weight_decay': 0.95,
                        'reset_interval': 3600
                    },
                    'least_connections': {
                        'enabled': True,
                        'max_connections': 1000,
                        'connection_timeout': 30
                    },
                    'weighted_response': {
                        'enabled': True,
                        'window_size': 100,
                        'min_responses': 10
                    },
                    'resource_based': {
                        'enabled': True,
                        'cpu_weight': 0.4,
                        'memory_weight': 0.3,
                        'io_weight': 0.3
                    }
                },
                'default_strategy': 'weighted_response'
            },
            'queues': {
                'priorities': {
                    'critical': {
                        'weight': 1.0,
                        'timeout': 5,
                        'max_retries': 3
                    },
                    'high': {
                        'weight': 0.8,
                        'timeout': 10,
                        'max_retries': 2
                    },
                    'normal': {
                        'weight': 0.5,
                        'timeout': 30,
                        'max_retries': 1
                    },
                    'low': {
                        'weight': 0.2,
                        'timeout': 60,
                        'max_retries': 0
                    }
                },
                'max_size': 10000,
                'batch_size': 100,
                'processing_interval': 0.1
            },
            'resources': {
                'cpu_threshold': 0.8,
                'memory_threshold': 0.8,
                'io_threshold': 0.7,
                'max_connections': 5000
            },
            'rate_limiting': {
                'enabled': True,
                'default_rate': 1000,
                'window_size': 60,
                'burst_multiplier': 2
            },
            'circuit_breaker': {
                'error_threshold': 0.5,
                'min_requests': 10,
                'reset_timeout': 30,
                'half_open_requests': 3
            },
            'monitoring': {
                'metrics_interval': 10,
                'health_check_interval': 30,
                'cleanup_interval': 300
            }
        }
        
    def setup_queues(self):
        """Initialize request queues"""
        self.queues = {
            QueuePriority.CRITICAL: asyncio.PriorityQueue(),
            QueuePriority.HIGH: asyncio.PriorityQueue(),
            QueuePriority.NORMAL: asyncio.PriorityQueue(),
            QueuePriority.LOW: asyncio.PriorityQueue()
        }
        
        self.queue_stats = defaultdict(lambda: {
            'processed': 0,
            'errors': 0,
            'latency': [],
            'size': 0
        })
        
        self.active_requests = {}
    
    def setup_metrics(self):
        """Initialize metrics tracking"""
        self.metrics = {
            'request_count': defaultdict(int),
            'error_count': defaultdict(int),
            'latency': defaultdict(list),
            'queue_size': defaultdict(int),
            'resource_usage': defaultdict(list)
        }
        
        self.node_stats = defaultdict(lambda: {
            'cpu_usage': [],
            'memory_usage': [],
            'io_usage': [],
            'connections': 0,
            'health_status': True
        })
    
    async def enqueue_request(self, request: RequestContext) -> bool:
        """Enqueue a new request"""
        try:
            # Check rate limits
            if not await self.check_rate_limit(request):
                return False
            
            # Check circuit breaker
            if not await self.check_circuit_breaker(request):
                return False
            
            # Get queue for priority
            queue = self.queues[request.priority]
            
            # Check queue size
            if queue.qsize() >= self.config['queues']['max_size']:
                logging.warning(f"Queue full for priority {request.priority}")
                return False
            
            # Add to queue
            await queue.put((
                -request.priority.value,  # Negative for proper priority ordering
                request.timestamp.timestamp(),
                request
            ))
            
            # Update stats
            self.queue_stats[request.priority]['size'] += 1
            self.metrics['queue_size'][request.priority] += 1
            
            return True
            
        except Exception as e:
            logging.error(f"Error enqueueing request: {str(e)}")
            return False
    
    async def process_queues(self):
        """Process requests from queues"""
        try:
            while True:
                # Check resource availability
                if not await self.check_resources():
                    await asyncio.sleep(1)
                    continue
                
                # Process batch from each queue
                for priority in QueuePriority:
                    await self.process_queue_batch(priority)
                
                await asyncio.sleep(
                    self.config['queues']['processing_interval']
                )
                
        except Exception as e:
            logging.error(f"Error processing queues: {str(e)}")
    
    async def process_queue_batch(self, priority: QueuePriority):
        """Process a batch of requests from a queue"""
        try:
            queue = self.queues[priority]
            batch_size = min(
                queue.qsize(),
                self.config['queues']['batch_size']
            )
            
            if batch_size == 0:
                return
            
            # Get batch of requests
            requests = []
            for _ in range(batch_size):
                if queue.empty():
                    break
                    
                _, _, request = await queue.get()
                requests.append(request)
            
            # Process batch
            results = await asyncio.gather(
                *[self.process_request(req) for req in requests],
                return_exceptions=True
            )
            
            # Handle results
            for request, result in zip(requests, results):
                if isinstance(result, Exception):
                    # Handle failure
                    await self.handle_request_failure(request, result)
                else:
                    # Update stats
                    await self.update_request_stats(request, result)
                
                # Mark task as done
                queue.task_done()
            
        except Exception as e:
            logging.error(f"Error processing queue batch: {str(e)}")
    
    async def process_request(self, request: RequestContext) -> Dict:
        """Process a single request"""
        try:
            start_time = datetime.now()
            
            # Select node for processing
            node = await self.select_node(request)
            
            # Send request to node
            result = await self.send_request_to_node(node, request)
            
            # Calculate metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'node': node,
                'processing_time': processing_time,
                'result': result
            }
            
        except Exception as e:
            logging.error(f"Error processing request: {str(e)}")
            raise
    
    async def select_node(self, request: RequestContext) -> str:
        """Select node for request processing"""
        try:
            strategy = BalancingStrategy(
                self.config['request_distribution']['default_strategy']
            )
            
            if strategy == BalancingStrategy.ROUND_ROBIN:
                return await self.select_round_robin()
            elif strategy == BalancingStrategy.LEAST_CONNECTIONS:
                return await self.select_least_connections()
            elif strategy == BalancingStrategy.WEIGHTED_RESPONSE:
                return await self.select_weighted_response()
            elif strategy == BalancingStrategy.RESOURCE_BASED:
                return await self.select_resource_based()
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
                
        except Exception as e:
            logging.error(f"Error selecting node: {str(e)}")
            raise
    
    async def select_round_robin(self) -> str:
        """Select node using round-robin strategy"""
        try:
            # Get available nodes
            nodes = await self.get_healthy_nodes()
            if not nodes:
                raise Exception("No healthy nodes available")
            
            # Get next node index
            next_index = self.metrics['request_count']['round_robin'] % len(nodes)
            
            # Update counter
            self.metrics['request_count']['round_robin'] += 1
            
            return nodes[next_index]
            
        except Exception as e:
            logging.error(f"Error in round-robin selection: {str(e)}")
            raise
    
    async def select_least_connections(self) -> str:
        """Select node with least active connections"""
        try:
            # Get nodes and their connection counts
            nodes = await self.get_healthy_nodes()
            if not nodes:
                raise Exception("No healthy nodes available")
            
            # Find node with minimum connections
            min_connections = float('inf')
            selected_node = None
            
            for node in nodes:
                connections = self.node_stats[node]['connections']
                if connections < min_connections:
                    min_connections = connections
                    selected_node = node
            
            if not selected_node:
                raise Exception("Could not select node")
            
            return selected_node
            
        except Exception as e:
            logging.error(f"Error in least-connections selection: {str(e)}")
            raise
    
    async def select_weighted_response(self) -> str:
        """Select node based on weighted response times"""
        try:
            nodes = await self.get_healthy_nodes()
            if not nodes:
                raise Exception("No healthy nodes available")
            
            # Calculate weights based on response times
            weights = []
            for node in nodes:
                latencies = self.metrics['latency'].get(node, [])
                if len(latencies) < self.config['request_distribution']['strategies']['weighted_response']['min_responses']:
                    weights.append(1.0)  # Default weight for new nodes
                else:
                    avg_latency = np.mean(latencies[-self.config['request_distribution']['strategies']['weighted_response']['window_size']:])
                    weights.append(1.0 / (avg_latency + 1))  # Convert to weight
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight == 0:
                return np.random.choice(nodes)  # Fallback to random selection
            
            weights = [w/total_weight for w in weights]
            
            # Select node
            return np.random.choice(nodes, p=weights)
            
        except Exception as e:
            logging.error(f"Error in weighted-response selection: {str(e)}")
            raise
    
    async def select_resource_based(self) -> str:
        """Select node based on resource availability"""
        try:
            nodes = await self.get_healthy_nodes()
            if not nodes:
                raise Exception("No healthy nodes available")
            
            # Calculate resource scores
            scores = []
            for node in nodes:
                stats = self.node_stats[node]
                
                # Calculate weighted resource score
                score = (
                    (1 - np.mean(stats['cpu_usage'][-10:])) * 
                    self.config['request_distribution']['strategies']['resource_based']['cpu_weight'] +
                    (1 - np.mean(stats['memory_usage'][-10:])) * 
                    self.config['request_distribution']['strategies']['resource_based']['memory_weight'] +
                    (1 - np.mean(stats['io_usage'][-10:])) * 
                    self.config['request_distribution']['strategies']['resource_based']['io_weight']
                )
                scores.append(score)
            
            # Select node with highest score
            return nodes[np.argmax(scores)]
            
        except Exception as e:
            logging.error(f"Error in resource-based selection: {str(e)}")
            raise

    async def start(self):
        """Start the load balancer"""
        try:
            logging.info("Starting Load Balancer")
            
            # Start background tasks
            asyncio.create_task(self.process_queues())
            asyncio.create_task(self.monitor_resources())
            asyncio.create_task(self.health_check())
            asyncio.create_task(self.cleanup_tasks())
            
            # Main loop
            while True:
                await asyncio.sleep(
                    self.config['monitoring']['metrics_interval']
                )
                
        except Exception as e:
            logging.error(f"Error in load balancer: {str(e)}")
            raise

# Run the load balancer
if __name__ == "__main__":
    balancer = LoadBalancer()
    asyncio.run(balancer.start())
```

I'll continue with the Traffic Management and Resource Monitoring components next. Would you like me to proceed?