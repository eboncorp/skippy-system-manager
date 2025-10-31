# Complete Home Cloud Setup Guide - Part 18

## Part 10.13: Application-Specific Caching System

### Intelligent Cache Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
from collections import defaultdict, OrderedDict
import hashlib
import numpy as np
from typing import Dict, List, Any, Optional
import aiofiles
import os

class CacheLevel:
    L1 = "memory"    # Fast, small capacity
    L2 = "disk"      # Medium speed, medium capacity
    L3 = "storage"   # Slow, large capacity

class ContentType:
    MEDIA = "media"
    METADATA = "metadata"
    THUMBNAIL = "thumbnail"
    CONFIG = "config"
    USER_DATA = "user_data"

class IntelligentCacheManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=11)
        self.load_config()
        self.cache_stats = defaultdict(lambda: {
            'hits': 0,
            'misses': 0,
            'size': 0
        })
        self.setup_cache_levels()
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/cache_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load cache configuration"""
        self.config = {
            'cache_levels': {
                'memory': {
                    'max_size': 512 * 1024 * 1024,  # 512MB
                    'eviction_policy': 'lru',
                    'ttl': 3600,  # 1 hour
                    'priority': 1
                },
                'disk': {
                    'max_size': 5 * 1024 * 1024 * 1024,  # 5GB
                    'eviction_policy': 'lfu',
                    'ttl': 86400,  # 1 day
                    'priority': 2
                },
                'storage': {
                    'max_size': 50 * 1024 * 1024 * 1024,  # 50GB
                    'eviction_policy': 'weight',
                    'ttl': 604800,  # 1 week
                    'priority': 3
                }
            },
            'content_types': {
                'media': {
                    'default_level': 'storage',
                    'compression': True,
                    'chunk_size': 1024 * 1024,  # 1MB
                    'prefetch_threshold': 0.7
                },
                'metadata': {
                    'default_level': 'memory',
                    'compression': True,
                    'chunk_size': 1024,  # 1KB
                    'prefetch_threshold': 0.8
                },
                'thumbnail': {
                    'default_level': 'disk',
                    'compression': True,
                    'chunk_size': 100 * 1024,  # 100KB
                    'prefetch_threshold': 0.6
                },
                'config': {
                    'default_level': 'memory',
                    'compression': False,
                    'chunk_size': 4096,  # 4KB
                    'prefetch_threshold': 0.9
                },
                'user_data': {
                    'default_level': 'disk',
                    'compression': True,
                    'chunk_size': 512 * 1024,  # 512KB
                    'prefetch_threshold': 0.75
                }
            },
            'prediction': {
                'window_size': 100,
                'min_confidence': 0.6,
                'max_prefetch_size': 100 * 1024 * 1024  # 100MB
            },
            'monitoring': {
                'stats_interval': 300,  # 5 minutes
                'cleanup_interval': 3600,  # 1 hour
                'max_stats_age': 86400  # 1 day
            }
        }
    
    def setup_cache_levels(self):
        """Initialize cache levels"""
        self.caches = {
            CacheLevel.L1: OrderedDict(),  # Memory cache
            CacheLevel.L2: OrderedDict(),  # Disk cache
            CacheLevel.L3: OrderedDict()   # Storage cache
        }
        
        # Create cache directories
        os.makedirs('/opt/cache/disk', exist_ok=True)
        os.makedirs('/opt/cache/storage', exist_ok=True)
    
    async def get_cached_item(self, key: str, content_type: str) -> Optional[Any]:
        """Retrieve item from cache"""
        try:
            # Generate cache key
            cache_key = self.generate_cache_key(key, content_type)
            
            # Try each cache level in order
            for level in [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]:
                item = await self.get_from_cache_level(cache_key, level)
                if item is not None:
                    # Cache hit
                    await self.record_cache_hit(level, content_type)
                    
                    # Promote to higher cache level if beneficial
                    await self.consider_promotion(cache_key, item, level, content_type)
                    
                    return item
            
            # Cache miss
            await self.record_cache_miss(content_type)
            return None
            
        except Exception as e:
            logging.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    def generate_cache_key(self, key: str, content_type: str) -> str:
        """Generate unique cache key"""
        return hashlib.sha256(f"{content_type}:{key}".encode()).hexdigest()
    
    async def get_from_cache_level(self, cache_key: str, level: str) -> Optional[Any]:
        """Retrieve item from specific cache level"""
        try:
            if level == CacheLevel.L1:
                # Memory cache
                return self.caches[level].get(cache_key)
            else:
                # Disk or Storage cache
                cache_path = self.get_cache_path(cache_key, level)
                if os.path.exists(cache_path):
                    async with aiofiles.open(cache_path, 'rb') as f:
                        content = await f.read()
                        return json.loads(content)
                return None
                
        except Exception as e:
            logging.error(f"Error retrieving from cache level {level}: {str(e)}")
            return None
    
    def get_cache_path(self, cache_key: str, level: str) -> str:
        """Get file path for cached item"""
        base_path = '/opt/cache/disk' if level == CacheLevel.L2 else '/opt/cache/storage'
        return os.path.join(base_path, cache_key[:2], cache_key[2:4], cache_key)
    
    async def record_cache_hit(self, level: str, content_type: str):
        """Record cache hit statistics"""
        self.cache_stats[f"{level}_{content_type}"]['hits'] += 1
        
        # Store in Redis for persistence
        self.redis.hincrby(
            f"cache_stats:{level}_{content_type}",
            'hits',
            1
        )
    
    async def record_cache_miss(self, content_type: str):
        """Record cache miss statistics"""
        self.cache_stats[f"miss_{content_type}"]['misses'] += 1
        
        # Store in Redis for persistence
        self.redis.hincrby(
            f"cache_stats:misses",
            content_type,
            1
        )
    
    async def consider_promotion(self, cache_key: str, item: Any, 
                               current_level: str, content_type: str):
        """Consider promoting item to higher cache level"""
        try:
            # Calculate item's access frequency and recency
            stats = await self.get_item_stats(cache_key)
            
            # Get content type configuration
            content_config = self.config['content_types'][content_type]
            
            # Calculate promotion score
            score = self.calculate_promotion_score(stats, content_type)
            
            # Determine target level
            target_level = await self.determine_target_level(
                current_level,
                score,
                len(json.dumps(item)),
                content_type
            )
            
            if target_level and target_level != current_level:
                await self.promote_item(cache_key, item, current_level, target_level)
                
        except Exception as e:
            logging.error(f"Error considering promotion: {str(e)}")
    
    async def get_item_stats(self, cache_key: str) -> Dict:
        """Get item access statistics"""
        stats = self.redis.hgetall(f"item_stats:{cache_key}")
        if not stats:
            return {
                'access_count': 0,
                'last_access': None,
                'total_time': 0
            }
        return {
            'access_count': int(stats.get(b'access_count', 0)),
            'last_access': stats.get(b'last_access', None),
            'total_time': float(stats.get(b'total_time', 0))
        }
    
    def calculate_promotion_score(self, stats: Dict, content_type: str) -> float:
        """Calculate item's promotion score"""
        try:
            # Base score on access frequency
            base_score = stats['access_count']
            
            # Factor in recency if available
            if stats['last_access']:
                last_access = datetime.fromisoformat(stats['last_access'].decode())
                time_factor = 1.0 / (1.0 + (datetime.now() - last_access).total_seconds() / 3600)
                base_score *= time_factor
            
            # Apply content type weights
            content_config = self.config['content_types'][content_type]
            prefetch_weight = content_config['prefetch_threshold']
            
            return base_score * prefetch_weight
            
        except Exception as e:
            logging.error(f"Error calculating promotion score: {str(e)}")
            return 0.0
    
    async def determine_target_level(self, current_level: str, score: float,
                                   size: int, content_type: str) -> Optional[str]:
        """Determine target cache level for item"""
        try:
            levels = [CacheLevel.L1, CacheLevel.L2, CacheLevel.L3]
            current_index = levels.index(current_level)
            
            # Can't promote from L1
            if current_index == 0:
                return None
            
            # Get next level up
            target_level = levels[current_index - 1]
            
            # Check if promotion is beneficial
            if (score > self.config['prediction']['min_confidence'] and
                size <= self.get_available_space(target_level)):
                return target_level
            
            return None
            
        except Exception as e:
            logging.error(f"Error determining target level: {str(e)}")
            return None
    
    def get_available_space(self, level: str) -> int:
        """Get available space in cache level"""
        try:
            max_size = self.config['cache_levels'][level]['max_size']
            current_size = sum(
                len(json.dumps(item)) for item in self.caches[level].values()
            )
            return max_size - current_size
            
        except Exception as e:
            logging.error(f"Error getting available space: {str(e)}")
            return 0
    
    async def promote_item(self, cache_key: str, item: Any,
                          current_level: str, target_level: str):
        """Promote item to higher cache level"""
        try:
            # Remove from current level
            if current_level == CacheLevel.L1:
                del self.caches[current_level][cache_key]
            else:
                os.remove(self.get_cache_path(cache_key, current_level))
            
            # Add to target level
            await self.add_to_cache_level(cache_key, item, target_level)
            
            # Log promotion
            logging.info(f"Promoted item {cache_key} from {current_level} to {target_level}")
            
        except Exception as e:
            logging.error(f"Error promoting item: {str(e)}")
    
    async def add_to_cache_level(self, cache_key: str, item: Any, level: str):
        """Add item to specific cache level"""
        try:
            if level == CacheLevel.L1:
                # Memory cache
                self.caches[level][cache_key] = item
            else:
                # Disk or Storage cache
                cache_path = self.get_cache_path(cache_key, level)
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                
                async with aiofiles.open(cache_path, 'wb') as f:
                    await f.write(json.dumps(item).encode())
            
        except Exception as e:
            logging.error(f"Error adding to cache level: {str(e)}")

# Run the cache manager
if __name__ == "__main__":
    manager = IntelligentCacheManager()
    asyncio.run(manager.start())
```

I'll continue with the Cache Prediction and Invalidation systems. Would you like me to proceed?