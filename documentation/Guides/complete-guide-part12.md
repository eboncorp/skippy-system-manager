# Complete Home Cloud Setup Guide - Part 12

## Part 10.7: Mobile Cache Management System

### Intelligent Cache Manager
```python
#!/usr/bin/env python3
import asyncio
import json
import logging
from datetime import datetime, timedelta
import redis
import aiohttp
from collections import defaultdict
import numpy as np
import os
import hashlib

class CacheManager:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=5)
        self.load_config()
        self.cache_stats = defaultdict(lambda: {
            'hits': 0,
            'misses': 0,
            'size': 0,
            'items': {}
        })
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/cache_manager.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load cache configuration"""
        self.config = {
            'max_cache_size': 1024 * 1024 * 1024,  # 1GB default
            'min_free_space': 100 * 1024 * 1024,   # 100MB
            'cache_priorities': {
                'critical': 1.0,    # System files
                'high': 0.8,        # Active media
                'medium': 0.5,      # Recent content
                'low': 0.2         # Old content
            },
            'prefetch_threshold': 0.7,  # Prefetch if probability > 70%
            'cache_ttl': {
                'critical': 30 * 24 * 3600,  # 30 days
                'high': 7 * 24 * 3600,       # 7 days
                'medium': 3 * 24 * 3600,     # 3 days
                'low': 24 * 3600             # 1 day
            }
        }
    
    async def manage_cache(self, device_id, file_info):
        """Main cache management function"""
        try:
            # Calculate file hash
            file_hash = self.calculate_file_hash(file_info['content'])
            
            # Check if file exists in cache
            cache_key = f"cache:{device_id}:{file_hash}"
            cached_info = self.redis.hgetall(cache_key)
            
            if cached_info:
                # Cache hit
                self.cache_stats[device_id]['hits'] += 1
                await self.update_cache_stats(device_id, file_hash, 'hit')
                return self.get_cached_file(cache_key)
            else:
                # Cache miss
                self.cache_stats[device_id]['misses'] += 1
                await self.update_cache_stats(device_id, file_hash, 'miss')
                
                # Check cache capacity
                await self.ensure_cache_capacity(device_id, file_info['size'])
                
                # Cache the file
                await self.cache_file(device_id, file_info, file_hash)
                
                # Trigger prefetch for related content
                asyncio.create_task(self.prefetch_related(device_id, file_info))
                
                return file_info['content']
                
        except Exception as e:
            logging.error(f"Error managing cache: {str(e)}")
            return None
    
    def calculate_file_hash(self, content):
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    async def update_cache_stats(self, device_id, file_hash, action):
        """Update cache statistics"""
        try:
            timestamp = datetime.now().isoformat()
            
            stats = {
                'action': action,
                'timestamp': timestamp,
                'file_hash': file_hash
            }
            
            # Store in Redis
            self.redis.lpush(
                f"cache_stats:{device_id}",
                json.dumps(stats)
            )
            
            # Trim old stats
            self.redis.ltrim(
                f"cache_stats:{device_id}",
                0,
                999  # Keep last 1000 events
            )
            
        except Exception as e:
            logging.error(f"Error updating cache stats: {str(e)}")
    
    async def ensure_cache_capacity(self, device_id, required_size):
        """Ensure sufficient cache capacity"""
        try:
            current_size = self.cache_stats[device_id]['size']
            
            if current_size + required_size > self.config['max_cache_size']:
                # Need to free up space
                await self.cleanup_cache(
                    device_id,
                    required_size + self.config['min_free_space']
                )
                
        except Exception as e:
            logging.error(f"Error ensuring cache capacity: {str(e)}")
    
    async def cleanup_cache(self, device_id, required_space):
        """Clean up cache to free space"""
        try:
            # Get all cached items
            items = self.cache_stats[device_id]['items']
            
            # Score items for removal
            scored_items = []
            for file_hash, item in items.items():
                score = self.calculate_retention_score(item)
                scored_items.append((score, file_hash, item))
            
            # Sort by score (lowest first)
            scored_items.sort()
            
            # Remove items until we have enough space
            space_freed = 0
            for score, file_hash, item in scored_items:
                if space_freed >= required_space:
                    break
                
                # Remove from cache
                await self.remove_from_cache(device_id, file_hash)
                space_freed += item['size']
            
        except Exception as e:
            logging.error(f"Error cleaning up cache: {str(e)}")
    
    def calculate_retention_score(self, item):
        """Calculate retention score for cached item"""
        try:
            # Factors to consider
            age_factor = self.calculate_age_factor(item['last_access'])
            priority_factor = self.config['cache_priorities'][item['priority']]
            usage_factor = self.calculate_usage_factor(item['access_count'])
            
            # Combine factors
            score = (age_factor * 0.4 +
                    priority_factor * 0.4 +
                    usage_factor * 0.2)
            
            return score
            
        except Exception as e:
            logging.error(f"Error calculating retention score: {str(e)}")
            return 0
    
    def calculate_age_factor(self, last_access):
        """Calculate age factor for cache item"""
        age = (datetime.now() - datetime.fromisoformat(last_access)).total_seconds()
        max_age = max(self.config['cache_ttl'].values())
        return max(0, 1 - (age / max_age))
    
    def calculate_usage_factor(self, access_count):
        """Calculate usage factor based on access frequency"""
        return min(1.0, access_count / 100)  # Cap at 100 accesses
    
    async def cache_file(self, device_id, file_info, file_hash):
        """Add file to cache"""
        try:
            cache_key = f"cache:{device_id}:{file_hash}"
            
            # Store file info
            cache_info = {
                'content': file_info['content'],
                'size': file_info['size'],
                'type': file_info['type'],
                'priority': self.determine_priority(file_info),
                'created_at': datetime.now().isoformat(),
                'last_access': datetime.now().isoformat(),
                'access_count': 1
            }
            
            # Store in Redis
            self.redis.hmset(cache_key, cache_info)
            
            # Set expiry based on priority
            ttl = self.config['cache_ttl'][cache_info['priority']]
            self.redis.expire(cache_key, ttl)
            
            # Update cache statistics
            self.cache_stats[device_id]['size'] += file_info['size']
            self.cache_stats[device_id]['items'][file_hash] = cache_info
            
        except Exception as e:
            logging.error(f"Error caching file: {str(e)}")
    
    def determine_priority(self, file_info):
        """Determine cache priority for file"""
        if file_info.get('system_file', False):
            return 'critical'
        elif file_info.get('actively_used', False):
            return 'high'
        elif file_info.get('recently_accessed', False):
            return 'medium'
        else:
            return 'low'
    
    async def prefetch_related(self, device_id, file_info):
        """Prefetch related content"""
        try:
            # Get related files
            related_files = await self.get_related_files(file_info)
            
            for related in related_files:
                # Calculate probability of access
                probability = self.calculate_access_probability(
                    device_id,
                    related,
                    file_info
                )
                
                if probability > self.config['prefetch_threshold']:
                    # Prefetch file
                    asyncio.create_task(
                        self.prefetch_file(device_id, related)
                    )
                
        except Exception as e:
            logging.error(f"Error in prefetch: {str(e)}")
    
    async def get_related_files(self, file_info):
        """Get list of related files"""
        # Implementation depends on file type and relationship logic
        return []
    
    def calculate_access_probability(self, device_id, related_file, current_file):
        """Calculate probability of related file being accessed"""
        try:
            # Factors to consider
            pattern_factor = self.analyze_access_patterns(
                device_id,
                related_file,
                current_file
            )
            time_factor = self.analyze_time_patterns(
                device_id,
                related_file
            )
            relationship_factor = self.analyze_relationship(
                related_file,
                current_file
            )
            
            # Combine factors
            probability = (pattern_factor * 0.4 +
                         time_factor * 0.3 +
                         relationship_factor * 0.3)
            
            return probability
            
        except Exception as e:
            logging.error(f"Error calculating access probability: {str(e)}")
            return 0
    
    def analyze_access_patterns(self, device_id, related_file, current_file):
        """Analyze historical access patterns"""
        # Implementation depends on access pattern analysis logic
        return 0.5
    
    def analyze_time_patterns(self, device_id, related_file):
        """Analyze time-based access patterns"""
        # Implementation depends on time pattern analysis logic
        return 0.5
    
    def analyze_relationship(self, related_file, current_file):
        """Analyze relationship between files"""
        # Implementation depends on file relationship logic
        return 0.5
    
    async def prefetch_file(self, device_id, file_info):
        """Prefetch a file into cache"""
        try:
            # Check if we have space
            if self.cache_stats[device_id]['size'] + file_info['size'] > self.config['max_cache_size']:
                return
            
            # Fetch and cache file
            await self.cache_file(
                device_id,
                file_info,
                self.calculate_file_hash(file_info['content'])
            )
            
        except Exception as e:
            logging.error(f"Error prefetching file: {str(e)}")

# Run the cache manager
if __name__ == "__main__":
    manager = CacheManager()
```

I'll continue with the Network Performance Optimization system next. Would you like me to proceed?