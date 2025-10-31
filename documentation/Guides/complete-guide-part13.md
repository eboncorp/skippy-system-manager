# Complete Home Cloud Setup Guide - Part 13

## Part 10.8: Network Performance Optimization

### Network Performance Manager
```python
#!/usr/bin/env python3
import asyncio
import aiohttp
import logging
import json
import zlib
import brotli
from collections import defaultdict
from datetime import datetime, timedelta
import redis
import numpy as np
from typing import Dict, List, Any
import ssl

class NetworkOptimizer:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=6)
        self.load_config()
        self.connection_pools = {}
        self.performance_metrics = defaultdict(list)
        self.compression_stats = defaultdict(dict)
    
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/network_optimizer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load optimization configuration"""
        self.config = {
            'connection_pools': {
                'max_size': 100,
                'min_size': 10,
                'max_idle': 30,
                'ttl': 300
            },
            'compression': {
                'min_size': 1024,  # Minimum size to compress (bytes)
                'algorithms': ['brotli', 'gzip'],
                'level_map': {
                    'text': 9,      # Maximum compression for text
                    'image': 6,     # Medium compression for images
                    'video': 3,     # Light compression for video
                    'default': 6    # Default compression level
                }
            },
            'request_optimization': {
                'batch_size': 10,
                'max_concurrent': 5,
                'timeout': 30,
                'retry_attempts': 3
            },
            'protocol': {
                'http2_enabled': True,
                'tcp_nodelay': True,
                'keep_alive': True,
                'websocket_enabled': True
            }
        }

    async def create_connection_pool(self, host: str) -> aiohttp.ClientSession:
        """Create and configure connection pool"""
        try:
            # Configure SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
            ssl_context.set_alpn_protocols(['h2', 'http/1.1'])

            # Configure connection pool
            conn = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=self.config['connection_pools']['max_size'],
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )

            # Create session with optimized settings
            session = aiohttp.ClientSession(
                connector=conn,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'Connection': 'keep-alive',
                    'Accept-Encoding': 'br, gzip'
                }
            )

            self.connection_pools[host] = {
                'session': session,
                'created': datetime.now(),
                'active_connections': 0
            }

            return session

        except Exception as e:
            logging.error(f"Error creating connection pool: {str(e)}")
            raise

    async def optimize_request(self, url: str, method: str = 'GET', 
                             data: Any = None) -> Dict:
        """Optimize and execute HTTP request"""
        try:
            host = url.split('/')[2]
            
            # Get or create connection pool
            if host not in self.connection_pools:
                session = await self.create_connection_pool(host)
            else:
                session = self.connection_pools[host]['session']

            # Prepare request
            headers = await self.optimize_headers(url, method)
            data = await self.optimize_payload(data) if data else None

            start_time = datetime.now()

            # Execute request with retry logic
            for attempt in range(self.config['request_optimization']['retry_attempts']):
                try:
                    async with session.request(method, url, 
                                             headers=headers, 
                                             data=data) as response:
                        content = await response.read()
                        
                        # Decompress if necessary
                        if response.headers.get('Content-Encoding') in ['br', 'gzip']:
                            content = await self.decompress_content(
                                content,
                                response.headers['Content-Encoding']
                            )

                        # Record metrics
                        await self.record_request_metrics(
                            url, method, datetime.now() - start_time,
                            len(content) if content else 0,
                            response.status
                        )

                        return {
                            'status': response.status,
                            'content': content,
                            'headers': dict(response.headers)
                        }

                except Exception as e:
                    if attempt == self.config['request_optimization']['retry_attempts'] - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        except Exception as e:
            logging.error(f"Error in optimize_request: {str(e)}")
            raise

    async def optimize_headers(self, url: str, method: str) -> Dict[str, str]:
        """Optimize request headers"""
        headers = {
            'Accept-Encoding': 'br, gzip',
            'Connection': 'keep-alive'
        }

        # Add conditional headers if we have cached content
        cached_etag = await self.get_cached_etag(url)
        if cached_etag:
            headers['If-None-Match'] = cached_etag

        return headers

    async def optimize_payload(self, data: Any) -> bytes:
        """Optimize request payload"""
        if isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
        
        # Compress if size exceeds threshold
        if len(data) > self.config['compression']['min_size']:
            return await self.compress_content(data)
        
        return data

    async def compress_content(self, content: bytes, 
                             content_type: str = 'default') -> bytes:
        """Compress content using optimal algorithm"""
        try:
            compression_level = self.config['compression']['level_map'].get(
                content_type, 
                self.config['compression']['level_map']['default']
            )

            # Try Brotli first
            try:
                start_time = datetime.now()
                compressed = brotli.compress(content, quality=compression_level)
                compression_time = (datetime.now() - start_time).total_seconds()

                if len(compressed) < len(content):
                    await self.update_compression_stats(
                        'brotli',
                        len(content),
                        len(compressed),
                        compression_time
                    )
                    return compressed
            except Exception as e:
                logging.warning(f"Brotli compression failed: {str(e)}")

            # Fallback to gzip
            start_time = datetime.now()
            compressed = zlib.compress(content, level=compression_level)
            compression_time = (datetime.now() - start_time).total_seconds()

            await self.update_compression_stats(
                'gzip',
                len(content),
                len(compressed),
                compression_time
            )
            return compressed

        except Exception as e:
            logging.error(f"Error compressing content: {str(e)}")
            return content

    async def decompress_content(self, content: bytes, encoding: str) -> bytes:
        """Decompress content based on encoding"""
        try:
            if encoding == 'br':
                return brotli.decompress(content)
            elif encoding == 'gzip':
                return zlib.decompress(content, wbits=16+zlib.MAX_WBITS)
            return content
        except Exception as e:
            logging.error(f"Error decompressing content: {str(e)}")
            raise

    async def update_compression_stats(self, algorithm: str, original_size: int,
                                     compressed_size: int, compression_time: float):
        """Update compression statistics"""
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'original_size': original_size,
                'compressed_size': compressed_size,
                'ratio': compressed_size / original_size,
                'time': compression_time
            }

            # Store in Redis
            self.redis.lpush(
                f"compression_stats:{algorithm}",
                json.dumps(stats)
            )

            # Trim old stats
            self.redis.ltrim(f"compression_stats:{algorithm}", 0, 999)

        except Exception as e:
            logging.error(f"Error updating compression stats: {str(e)}")

    async def record_request_metrics(self, url: str, method: str,
                                   duration: timedelta, size: int,
                                   status: int):
        """Record request performance metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'url': url,
                'method': method,
                'duration_ms': duration.total_seconds() * 1000,
                'size': size,
                'status': status
            }

            # Store in Redis
            self.redis.lpush('request_metrics', json.dumps(metrics))
            self.redis.ltrim('request_metrics', 0, 9999)

        except Exception as e:
            logging.error(f"Error recording metrics: {str(e)}")

    async def analyze_performance(self):
        """Analyze network performance metrics"""
        while True:
            try:
                # Get recent metrics
                raw_metrics = self.redis.lrange('request_metrics', 0, 999)
                metrics = [json.loads(m) for m in raw_metrics]

                # Calculate statistics
                durations = [m['duration_ms'] for m in metrics]
                sizes = [m['size'] for m in metrics]
                status_codes = [m['status'] for m in metrics]

                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'request_count': len(metrics),
                    'avg_duration': np.mean(durations),
                    'p95_duration': np.percentile(durations, 95),
                    'avg_size': np.mean(sizes),
                    'error_rate': sum(1 for s in status_codes if s >= 400) / len(status_codes),
                    'success_rate': sum(1 for s in status_codes if 200 <= s < 300) / len(status_codes)
                }

                # Store analysis
                self.redis.lpush('performance_analysis', json.dumps(stats))
                self.redis.ltrim('performance_analysis', 0, 99)

                # Adjust configurations if needed
                await self.adjust_optimization_parameters(stats)

                await asyncio.sleep(300)  # Analyze every 5 minutes

            except Exception as e:
                logging.error(f"Error analyzing performance: {str(e)}")
                await asyncio.sleep(60)

    async def adjust_optimization_parameters(self, stats: Dict):
        """Adjust optimization parameters based on performance"""
        try:
            # Adjust connection pool size
            if stats['avg_duration'] > 1000:  # If average duration > 1s
                self.config['connection_pools']['max_size'] = min(
                    self.config['connection_pools']['max_size'] + 10,
                    200
                )
            elif stats['avg_duration'] < 100:  # If average duration < 100ms
                self.config['connection_pools']['max_size'] = max(
                    self.config['connection_pools']['max_size'] - 5,
                    self.config['connection_pools']['min_size']
                )

            # Adjust compression levels
            if stats['avg_size'] > 1000000:  # If average size > 1MB
                for content_type in self.config['compression']['level_map']:
                    self.config['compression']['level_map'][content_type] = min(
                        self.config['compression']['level_map'][content_type] + 1,
                        9
                    )

            # Adjust retry attempts
            if stats['error_rate'] > 0.1:  # If error rate > 10%
                self.config['request_optimization']['retry_attempts'] = min(
                    self.config['request_optimization']['retry_attempts'] + 1,
                    5
                )

        except Exception as e:
            logging.error(f"Error adjusting parameters: {str(e)}")

    async def cleanup_connection_pools(self):
        """Clean up idle connection pools"""
        while True:
            try:
                current_time = datetime.now()
                for host, pool_info in list(self.connection_pools.items()):
                    if (current_time - pool_info['created']).total_seconds() > self.config['connection_pools']['ttl']:
                        await pool_info['session'].close()
                        del self.connection_pools[host]

                await asyncio.sleep(60)

            except Exception as e:
                logging.error(f"Error cleaning up connection pools: {str(e)}")
                await asyncio.sleep(60)

    async def start(self):
        """Start the network optimizer"""
        logging.info("Starting Network Performance Optimizer")
        
        # Start background tasks
        asyncio.create_task(self.analyze_performance())
        asyncio.create_task(self.cleanup_connection_pools())
        
        # Keep the optimizer running
        while True:
            await asyncio.sleep(3600)

# Run the network optimizer
if __name__ == "__main__":
    optimizer = NetworkOptimizer()
    asyncio.run(optimizer.start())
```

I'll continue with the final components of the mobile optimization system:
1. Quality of Service (QoS) Management
2. Application-specific optimizations
3. Error handling and recovery
4. Monitoring and reporting

Would you like me to proceed with these sections?