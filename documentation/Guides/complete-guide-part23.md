# Complete Home Cloud Setup Guide - Part 23

## Part 10.18: Compression and Data Organization System

### Adaptive Data Optimizer
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
import zlib
import lz4.frame
import brotli
import msgpack
import xxhash
from enum import Enum
import io
import struct

class CompressionAlgorithm(Enum):
    ZLIB = "zlib"
    LZ4 = "lz4"
    BROTLI = "brotli"
    NONE = "none"

class DataFormat(Enum):
    JSON = "json"
    MSGPACK = "msgpack"
    BINARY = "binary"
    CUSTOM = "custom"

class DataOptimizer:
    def __init__(self):
        self.setup_logging()
        self.redis = redis.Redis(host='localhost', port=6379, db=16)
        self.load_config()
        self.setup_compression_stats()
        
    def setup_logging(self):
        logging.basicConfig(
            filename='/var/log/data_optimizer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def load_config(self):
        """Load data optimization configuration"""
        self.config = {
            'compression': {
                'algorithms': {
                    'zlib': {
                        'levels': range(1, 10),
                        'default_level': 6,
                        'min_size': 1024,
                        'threshold': 0.8
                    },
                    'lz4': {
                        'levels': range(1, 17),
                        'default_level': 9,
                        'min_size': 512,
                        'threshold': 0.6
                    },
                    'brotli': {
                        'levels': range(0, 12),
                        'default_level': 4,
                        'min_size': 1024,
                        'threshold': 0.7
                    }
                },
                'content_types': {
                    'text': {
                        'default_algo': 'brotli',
                        'fallback': 'zlib'
                    },
                    'json': {
                        'default_algo': 'zlib',
                        'fallback': 'lz4'
                    },
                    'binary': {
                        'default_algo': 'lz4',
                        'fallback': 'zlib'
                    },
                    'media': {
                        'default_algo': 'lz4',
                        'fallback': 'none'
                    }
                }
            },
            'data_formats': {
                'json': {
                    'compression': True,
                    'validation': True,
                    'schema_check': True
                },
                'msgpack': {
                    'compression': True,
                    'use_bin_type': True,
                    'use_single_float': True
                },
                'binary': {
                    'compression': True,
                    'alignment': 8,
                    'endian': 'little'
                },
                'custom': {
                    'compression': True,
                    'version': 1,
                    'checksum': True
                }
            },
            'optimization': {
                'min_compress_size': 128,
                'max_compress_size': 1024 * 1024 * 10,  # 10MB
                'compression_ratio_threshold': 0.8,
                'adaptive_threshold': 1000,
                'sampling_rate': 0.1
            },
            'monitoring': {
                'stats_interval': 300,
                'adaptation_interval': 3600,
                'cleanup_interval': 86400
            }
        }
    
    def setup_compression_stats(self):
        """Initialize compression statistics tracking"""
        self.compression_stats = defaultdict(lambda: {
            'original_size': 0,
            'compressed_size': 0,
            'compression_time': 0,
            'decompression_time': 0,
            'success_count': 0,
            'failure_count': 0
        })
    
    async def optimize_data(self, data: Any, content_type: str) -> Dict:
        """Optimize data for storage"""
        try:
            # Analyze data characteristics
            data_info = await self.analyze_data(data, content_type)
            
            # Choose optimal format
            data_format = await self.select_data_format(data_info)
            
            # Serialize data
            serialized_data = await self.serialize_data(data, data_format)
            
            # Choose and apply compression
            compressed_data = await self.compress_data(
                serialized_data,
                content_type,
                data_info
            )
            
            return {
                'data': compressed_data,
                'format': data_format.value,
                'compression': compressed_data['algorithm'] if compressed_data else None,
                'metadata': data_info
            }
            
        except Exception as e:
            logging.error(f"Error optimizing data: {str(e)}")
            return {'data': data, 'format': 'raw', 'compression': None}
    
    async def analyze_data(self, data: Any, content_type: str) -> Dict:
        """Analyze data characteristics"""
        try:
            analysis = {
                'size': len(str(data)) if isinstance(data, (str, bytes)) else len(json.dumps(data)),
                'type': type(data).__name__,
                'content_type': content_type,
                'structure': await self.analyze_structure(data),
                'entropy': await self.calculate_entropy(data),
                'patterns': await self.detect_patterns(data)
            }
            
            return analysis
            
        except Exception as e:
            logging.error(f"Error analyzing data: {str(e)}")
            return {}
    
    async def analyze_structure(self, data: Any) -> Dict:
        """Analyze data structure"""
        try:
            if isinstance(data, dict):
                return {
                    'type': 'dict',
                    'keys': len(data),
                    'nested_depth': await self.calculate_nested_depth(data),
                    'key_types': await self.analyze_key_types(data)
                }
            elif isinstance(data, (list, tuple)):
                return {
                    'type': 'sequence',
                    'length': len(data),
                    'homogeneous': await self.check_homogeneous(data),
                    'element_types': await self.analyze_element_types(data)
                }
            elif isinstance(data, str):
                return {
                    'type': 'string',
                    'length': len(data),
                    'encoding': 'utf-8',
                    'contains_binary': await self.check_binary_content(data)
                }
            else:
                return {
                    'type': 'other',
                    'size': len(str(data))
                }
                
        except Exception as e:
            logging.error(f"Error analyzing structure: {str(e)}")
            return {}
    
    async def calculate_entropy(self, data: Any) -> float:
        """Calculate Shannon entropy of data"""
        try:
            if isinstance(data, (str, bytes)):
                # Convert to bytes if string
                byte_data = data.encode() if isinstance(data, str) else data
                
                # Count byte frequencies
                freq = defaultdict(int)
                for byte in byte_data:
                    freq[byte] += 1
                
                # Calculate entropy
                length = len(byte_data)
                return -sum(count/length * np.log2(count/length) 
                          for count in freq.values())
            else:
                # Convert to JSON for non-string/bytes data
                return await self.calculate_entropy(json.dumps(data))
                
        except Exception as e:
            logging.error(f"Error calculating entropy: {str(e)}")
            return 0.0
    
    async def detect_patterns(self, data: Any) -> Dict:
        """Detect patterns in data"""
        try:
            patterns = {
                'repetitive': False,
                'structured': False,
                'random': False,
                'sequential': False
            }
            
            if isinstance(data, (str, bytes)):
                # Check for repetitive patterns
                patterns['repetitive'] = await self.check_repetitive_patterns(data)
                
                # Check for structured data
                patterns['structured'] = await self.check_structured_patterns(data)
                
                # Check for randomness
                patterns['random'] = await self.check_randomness(data)
                
                # Check for sequential patterns
                patterns['sequential'] = await self.check_sequential_patterns(data)
            
            return patterns
            
        except Exception as e:
            logging.error(f"Error detecting patterns: {str(e)}")
            return {}
    
    async def select_data_format(self, data_info: Dict) -> DataFormat:
        """Select optimal data format"""
        try:
            # Decision matrix for format selection
            if data_info['content_type'] == 'binary':
                return DataFormat.BINARY
            
            if data_info['structure']['type'] in ['dict', 'sequence']:
                if data_info['size'] > 1000000:  # Large data
                    return DataFormat.MSGPACK
                else:
                    return DataFormat.JSON
            
            if data_info['entropy'] > 7.0:  # High entropy
                return DataFormat.BINARY
            
            # Default to JSON for unknown cases
            return DataFormat.JSON
            
        except Exception as e:
            logging.error(f"Error selecting data format: {str(e)}")
            return DataFormat.JSON
    
    async def serialize_data(self, data: Any, format: DataFormat) -> bytes:
        """Serialize data to specified format"""
        try:
            if format == DataFormat.JSON:
                return json.dumps(data).encode()
            
            elif format == DataFormat.MSGPACK:
                return msgpack.packb(data, use_bin_type=True)
            
            elif format == DataFormat.BINARY:
                return await self.serialize_binary(data)
            
            elif format == DataFormat.CUSTOM:
                return await self.serialize_custom(data)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logging.error(f"Error serializing data: {str(e)}")
            raise
    
    async def compress_data(self, data: bytes, content_type: str, 
                          data_info: Dict) -> Optional[Dict]:
        """Compress data using optimal algorithm"""
        try:
            if len(data) < self.config['optimization']['min_compress_size']:
                return None
            
            # Select compression algorithm
            algorithm = await self.select_compression_algorithm(
                content_type,
                data_info
            )
            
            if algorithm == CompressionAlgorithm.NONE:
                return None
            
            # Get compression settings
            settings = self.config['compression']['algorithms'][algorithm.value]
            
            # Try compression
            start_time = datetime.now()
            compressed = await self.apply_compression(data, algorithm, settings)
            compression_time = (datetime.now() - start_time).total_seconds()
            
            # Check compression ratio
            ratio = len(compressed) / len(data)
            if ratio > self.config['optimization']['compression_ratio_threshold']:
                return None
            
            # Update statistics
            self.update_compression_stats(
                algorithm.value,
                len(data),
                len(compressed),
                compression_time
            )
            
            return {
                'data': compressed,
                'algorithm': algorithm.value,
                'original_size': len(data),
                'compressed_size': len(compressed),
                'ratio': ratio
            }
            
        except Exception as e:
            logging.error(f"Error compressing data: {str(e)}")
            return None
    
    async def select_compression_algorithm(self, content_type: str, 
                                        data_info: Dict) -> CompressionAlgorithm:
        """Select optimal compression algorithm"""
        try:
            # Get content type configuration
            content_config = self.config['compression']['content_types'].get(
                content_type,
                self.config['compression']['content_types']['binary']
            )
            
            # Check data characteristics
            if data_info['entropy'] > 7.5:  # High entropy
                return CompressionAlgorithm.NONE
            
            if data_info['patterns']['random']:
                return CompressionAlgorithm.LZ4  # Fast compression for random data
            
            if data_info['patterns']['repetitive']:
                return CompressionAlgorithm.BROTLI  # Good for repetitive patterns
            
            # Use default algorithm for content type
            return CompressionAlgorithm(content_config['default_algo'])
            
        except Exception as e:
            logging.error(f"Error selecting compression algorithm: {str(e)}")
            return CompressionAlgorithm.NONE
    
    async def apply_compression(self, data: bytes, algorithm: CompressionAlgorithm,
                              settings: Dict) -> bytes:
        """Apply compression algorithm"""
        try:
            if algorithm == CompressionAlgorithm.ZLIB:
                return zlib.compress(data, level=settings['default_level'])
            
            elif algorithm == CompressionAlgorithm.LZ4:
                return lz4.frame.compress(
                    data,
                    compression_level=settings['default_level']
                )
            
            elif algorithm == CompressionAlgorithm.BROTLI:
                return brotli.compress(
                    data,
                    quality=settings['default_level']
                )
            
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
                
        except Exception as e:
            logging.error(f"Error applying compression: {str(e)}")
            raise

    async def start(self):
        """Start the data optimizer"""
        try:
            logging.info("Starting Data Optimizer")
            
            while True:
                # Analyze compression statistics
                await self.analyze_compression_performance()
                
                # Adapt compression settings
                await self.adapt_compression_settings()
                
                # Clean up old statistics
                await self.cleanup_old_stats()
                
                await asyncio.sleep(
                    self.config['monitoring']['adaptation_interval']
                )
                
        except Exception as e:
            logging.error(f"Error in data optimizer: {str(e)}")
            raise

# Run the data optimizer
if __name__ == "__main__":
    optimizer = DataOptimizer()
    asyncio.run(optimizer.start())
```

I'll continue with the Access Pattern Optimization System next. Would you like me to proceed?