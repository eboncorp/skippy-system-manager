# Complete Home Cloud Setup Guide - Part 20

## Part 10.15: Cache Invalidation System

### Cache Invalidation Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
from enum import Enum

class InvalidationStrategy(Enum):
    IMMEDIATE = "immediate"
    LAZY = "lazy"
    SCHEDULED = "scheduled"
    BACKGROUND = "background"

class ConsistencyLevel(Enum):
    STRICT = "strict"
    EVENTUAL = "eventual"
    RELAXED = "relaxed"

class CacheInvalidationManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=13)
        self.load_config()
        self.setup_dependency_graph()
        self.invalidation_queue = asyncio.Queue()
        self.pending_invalidations = defaultdict(set)
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/cache_invalidation.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load invalidation configuration"""
        self.config = {
            'ttl_management': {
                'default_ttl': 3600,  # 1 hour
                'min_ttl': 60,        # 1 minute
                'max_ttl': 86400,     # 1 day
                'ttl_policies': {
                    'media': {
                        'base_ttl': 86400,      # 1 day
                        'access_multiplier': 1.5,
                        'max_extension': 604800  # 1 week
                    },
                    'metadata': {
                        'base_ttl': 300,        # 5 minutes
                        'access_multiplier': 2.0,
                        'max_extension': 3600    # 1 hour
                    },
                    'config': {
                        'base_ttl': 1800,       # 30 minutes
                        'access_multiplier': 1.2,
                        'max_extension': 7200    # 2 hours
                    }
                }
            },
            'dependency_tracking': {
                'max_depth': 5,
                'circular_resolution': 'break',  # or 'maintain'
                'update_frequency': 300,         # 5 minutes
                'prune_threshold': 100          # Max dependencies per item
            },
            'consistency': {
                'strict': {
                    'propagation_delay': 0,
                    'verification_required': True,
                    'retry_attempts': 3
                },
                'eventual': {
                    'propagation_delay': 5,
                    'verification_required': False,
                    'retry_attempts': 1
                },
                'relaxed': {
                    'propagation_delay': 30,
                    'verification_required': False,
                    'retry_attempts': 0
                }
            },
            'invalidation_strategies': {
                'immediate': {
                    'priority': 1,
                    'max_batch_size': 1,
                    'propagation_mode': 'sync'
                },
                'lazy': {
                    'priority': 3,
                    'max_batch_size': None,
                    'propagation_mode': 'async'
                },
                'scheduled': {
                    'priority': 2,
                    'max_batch_size': 100,
                    'propagation_mode': 'sync',
                    'schedule_interval': 300  # 5 minutes
                },
                'background': {
                    'priority': 4,
                    'max_batch_size': 1000,
                    'propagation_mode': 'async',
                    'batch_interval': 60  # 1 minute
                }
            }
        }
    
    def setup_dependency_graph(self):
        """Initialize dependency tracking graph"""
        self.dependency_graph = nx.DiGraph()
        self.reverse_dependencies = defaultdict(set)
        self.dependency_metadata = defaultdict(dict)
    
    async def invalidate_cache_item(self, key: str, 
                                  strategy: InvalidationStrategy = InvalidationStrategy.IMMEDIATE,
                                  consistency: ConsistencyLevel = ConsistencyLevel.STRICT) -> bool:
        """Invalidate a cached item"""
        try:
            # Create invalidation context
            context = {
                'key': key,
                'strategy': strategy,
                'consistency': consistency,
                'timestamp': datetime.now().isoformat(),
                'dependencies': await self.get_dependencies(key),
                'status': 'pending'
            }
            
            # Add to invalidation queue
            await self.invalidation_queue.put(context)
            
            # Process immediately if using IMMEDIATE strategy
            if strategy == InvalidationStrategy.IMMEDIATE:
                return await self.process_invalidation(context)
            
            return True
            
        except Exception as e:
            logging.error(f"Error invalidating cache item: {str(e)}")
            return False
    
    async def get_dependencies(self, key: str, depth: int = 0) -> Set[str]:
        """Get all dependencies for a cache item"""
        try:
            if depth >= self.config['dependency_tracking']['max_depth']:
                return set()
            
            dependencies = set()
            direct_deps = self.dependency_graph.neighbors(key)
            
            for dep in direct_deps:
                dependencies.add(dep)
                if self.config['dependency_tracking']['circular_resolution'] == 'break':
                    child_deps = await self.get_dependencies(dep, depth + 1)
                    dependencies.update(child_deps)
            
            return dependencies
            
        except Exception as e:
            logging.error(f"Error getting dependencies: {str(e)}")
            return set()
    
    async def process_invalidation(self, context: Dict) -> bool:
        """Process cache invalidation"""
        try:
            strategy_config = self.config['invalidation_strategies'][context['strategy'].value]
            consistency_config = self.config['consistency'][context['consistency'].value]
            
            # Track invalidation start
            context['start_time'] = datetime.now().isoformat()
            
            # Determine invalidation order
            invalidation_order = self.determine_invalidation_order(
                context['key'],
                context['dependencies']
            )
            
            # Process each item
            success = True
            for item in invalidation_order:
                result = await self.invalidate_single_item(
                    item,
                    strategy_config,
                    consistency_config
                )
                if not result and consistency_config['verification_required']:
                    success = False
                    break
            
            # Update context
            context['status'] = 'completed' if success else 'failed'
            context['end_time'] = datetime.now().isoformat()
            
            # Store invalidation record
            await self.store_invalidation_record(context)
            
            return success
            
        except Exception as e:
            logging.error(f"Error processing invalidation: {str(e)}")
            return False
    
    def determine_invalidation_order(self, key: str, 
                                   dependencies: Set[str]) -> List[str]:
        """Determine optimal invalidation order"""
        try:
            # Create subgraph with dependencies
            subgraph = self.dependency_graph.subgraph(dependencies.union({key}))
            
            # Use topological sort for ordering
            return list(nx.topological_sort(subgraph))
            
        except Exception as e:
            logging.error(f"Error determining invalidation order: {str(e)}")
            return list(dependencies)
    
    async def invalidate_single_item(self, key: str,
                                   strategy_config: Dict,
                                   consistency_config: Dict) -> bool:
        """Invalidate a single cache item"""
        try:
            # Apply invalidation strategy
            if strategy_config['propagation_mode'] == 'sync':
                return await self.sync_invalidation(
                    key,
                    consistency_config
                )
            else:
                asyncio.create_task(
                    self.async_invalidation(key, consistency_config)
                )
                return True
            
        except Exception as e:
            logging.error(f"Error invalidating single item: {str(e)}")
            return False
    
    async def sync_invalidation(self, key: str, 
                              consistency_config: Dict) -> bool:
        """Perform synchronous invalidation"""
        try:
            for attempt in range(consistency_config['retry_attempts'] + 1):
                # Remove from all cache levels
                removed = await self.remove_from_cache(key)
                
                if consistency_config['verification_required']:
                    # Verify removal
                    if await self.verify_invalidation(key):
                        return True
                    elif attempt < consistency_config['retry_attempts']:
                        await asyncio.sleep(1)  # Wait before retry
                        continue
                    return False
                
                return removed
            
            return False
            
        except Exception as e:
            logging.error(f"Error in sync invalidation: {str(e)}")
            return False
    
    async def async_invalidation(self, key: str, 
                               consistency_config: Dict):
        """Perform asynchronous invalidation"""
        try:
            # Add to pending invalidations
            self.pending_invalidations[key].add(datetime.now().isoformat())
            
            # Apply propagation delay
            await asyncio.sleep(consistency_config['propagation_delay'])
            
            # Remove from cache
            await self.remove_from_cache(key)
            
            # Update pending invalidations
            self.pending_invalidations[key].remove(
                min(self.pending_invalidations[key])
            )
            
        except Exception as e:
            logging.error(f"Error in async invalidation: {str(e)}")
    
    async def remove_from_cache(self, key: str) -> bool:
        """Remove item from all cache levels"""
        try:
            # Remove from Redis
            self.redis.delete(f"cache:{key}")
            
            # Remove from in-memory cache
            if key in self.cache:
                del self.cache[key]
            
            # Remove from disk cache
            cache_path = self.get_cache_path(key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
            
            return True
            
        except Exception as e:
            logging.error(f"Error removing from cache: {str(e)}")
            return False
    
    async def verify_invalidation(self, key: str) -> bool:
        """Verify cache item is invalidated"""
        try:
            # Check all cache levels
            redis_exists = self.redis.exists(f"cache:{key}")
            memory_exists = key in self.cache
            disk_exists = os.path.exists(self.get_cache_path(key))
            
            return not (redis_exists or memory_exists or disk_exists)
            
        except Exception as e:
            logging.error(f"Error verifying invalidation: {str(e)}")
            return False
    
    async def store_invalidation_record(self, context: Dict):
        """Store invalidation record"""
        try:
            record_key = f"invalidation:{context['key']}:{context['timestamp']}"
            self.redis.setex(
                record_key,
                self.config['ttl_management']['default_ttl'],
                json.dumps(context)
            )
            
        except Exception as e:
            logging.error(f"Error storing invalidation record: {str(e)}")
    
    async def start(self):
        """Start the invalidation manager"""
        try:
            logging.info("Starting Cache Invalidation Manager")
            
            # Start background tasks
            asyncio.create_task(self.process_invalidation_queue())
            asyncio.create_task(self.cleanup_pending_invalidations())
            asyncio.create_task(self.update_dependency_graph())
            
            while True:
                await asyncio.sleep(3600)
                
        except Exception as e:
            logging.error(f"Error in invalidation manager: {str(e)}")
            raise

# Run the invalidation manager
if __name__ == "__main__":
    manager = CacheInvalidationManager()
    asyncio.run(manager.start())
```

I'll continue with the final components of the caching system:
1. Cache Monitoring and Analytics
2. Performance Optimization
3. Error Recovery
4. Administration Interface

Would you like me to proceed with these sections?