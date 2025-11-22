"""
Enhanced Multi-Level Caching System for Synapse AI Web Application

This module provides a sophisticated caching system with TTL, LRU eviction,
compression, and performance monitoring for the serendipity analysis system.
"""

import time
import threading
import pickle
import gzip
import hashlib
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path
import weakref
import sys
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class CacheEntry(Generic[T]):
    """Enhanced cache entry with comprehensive metadata"""
    key: str
    value: T
    created_at: float
    last_accessed: float
    access_count: int
    ttl_seconds: int
    size_bytes: int
    compressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        if self.ttl_seconds <= 0:
            return False  # No expiration
        return time.time() > self.created_at + self.ttl_seconds
    
    def access(self) -> T:
        """Access the cached value and update statistics"""
        self.last_accessed = time.time()
        self.access_count += 1
        return self.value
    
    def get_age_seconds(self) -> float:
        """Get the age of the cache entry in seconds"""
        return time.time() - self.created_at
    
    def get_idle_time_seconds(self) -> float:
        """Get the time since last access in seconds"""
        return time.time() - self.last_accessed

class CacheEvictionPolicy(ABC):
    """Abstract base class for cache eviction policies"""
    
    @abstractmethod
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Determine if an entry should be evicted"""
        pass
    
    @abstractmethod
    def get_eviction_candidates(self, entries: Dict[str, CacheEntry], 
                               count: int) -> List[str]:
        """Get a list of keys to evict"""
        pass

class LRUEvictionPolicy(CacheEvictionPolicy):
    """Least Recently Used eviction policy"""
    
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Evict if cache is over capacity"""
        return cache_size > max_size
    
    def get_eviction_candidates(self, entries: Dict[str, CacheEntry], 
                               count: int) -> List[str]:
        """Get LRU candidates for eviction"""
        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: x[1].last_accessed
        )
        return [key for key, _ in sorted_entries[:count]]

class TTLEvictionPolicy(CacheEvictionPolicy):
    """Time-to-Live eviction policy"""
    
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Evict if entry is expired"""
        return entry.is_expired()
    
    def get_eviction_candidates(self, entries: Dict[str, CacheEntry], 
                               count: int) -> List[str]:
        """Get expired entries for eviction"""
        expired_keys = []
        for key, entry in entries.items():
            if entry.is_expired():
                expired_keys.append(key)
        return expired_keys[:count]

class SizeBasedEvictionPolicy(CacheEvictionPolicy):
    """Size-based eviction policy (evict largest entries first)"""
    
    def should_evict(self, entry: CacheEntry, cache_size: int, max_size: int) -> bool:
        """Evict if cache is over capacity"""
        return cache_size > max_size
    
    def get_eviction_candidates(self, entries: Dict[str, CacheEntry], 
                               count: int) -> List[str]:
        """Get largest entries for eviction"""
        # Sort by size (largest first)
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: x[1].size_bytes,
            reverse=True
        )
        return [key for key, _ in sorted_entries[:count]]

@dataclass
class CacheConfiguration:
    """Configuration for cache behavior"""
    max_entries: int = 1000
    max_size_mb: float = 100.0
    default_ttl_seconds: int = 3600  # 1 hour
    enable_compression: bool = True
    compression_threshold_bytes: int = 1024  # Compress entries larger than 1KB
    eviction_policy: str = "lru"  # "lru", "ttl", "size"
    cleanup_interval_seconds: int = 300  # 5 minutes
    enable_persistence: bool = False
    persistence_file: Optional[str] = None
    enable_statistics: bool = True

class EnhancedCache:
    """
    Enhanced multi-level cache with compression, TTL, and advanced eviction policies
    """
    
    def __init__(self, name: str, config: Optional[CacheConfiguration] = None):
        """Initialize the enhanced cache"""
        self.name = name
        self.config = config or CacheConfiguration()
        
        # Cache storage
        self._entries: Dict[str, CacheEntry] = {}
        self._access_order = OrderedDict()  # For LRU tracking
        
        # Synchronization
        self._lock = threading.RLock()
        
        # Eviction policy
        self._eviction_policies = {
            "lru": LRUEvictionPolicy(),
            "ttl": TTLEvictionPolicy(),
            "size": SizeBasedEvictionPolicy()
        }
        self._eviction_policy = self._eviction_policies.get(
            self.config.eviction_policy, 
            LRUEvictionPolicy()
        )
        
        # Statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "compressions": 0,
            "decompressions": 0,
            "total_size_bytes": 0,
            "average_access_time_ms": 0.0,
            "last_cleanup": time.time()
        }
        
        # Background cleanup
        self._cleanup_thread = None
        self._shutdown_event = threading.Event()
        
        # Performance monitoring
        from performance_monitor import get_performance_monitor
        self.performance_monitor = get_performance_monitor()
        
        # Start background cleanup if enabled
        if self.config.cleanup_interval_seconds > 0:
            self._start_cleanup_thread()
        
        # Load from persistence if enabled
        if self.config.enable_persistence and self.config.persistence_file:
            self._load_from_persistence()
        
        logger.info(f"Enhanced cache '{name}' initialized with {self.config.max_entries} max entries")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_expired_entries,
            daemon=True,
            name=f"CacheCleanup-{self.name}"
        )
        self._cleanup_thread.start()
    
    def _cleanup_expired_entries(self):
        """Background thread for cleaning up expired entries"""
        while not self._shutdown_event.wait(self.config.cleanup_interval_seconds):
            try:
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"Error in cache cleanup for {self.name}: {e}")
    
    def _perform_cleanup(self):
        """Perform cache cleanup operations"""
        with self._lock:
            # Clean up expired entries
            expired_keys = []
            for key, entry in self._entries.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_entry(key)
                self._stats["evictions"] += 1
            
            # Check size limits and evict if necessary
            self._enforce_size_limits()
            
            # Update cleanup timestamp
            self._stats["last_cleanup"] = time.time()
            
            if expired_keys:
                logger.debug(f"Cache {self.name}: cleaned up {len(expired_keys)} expired entries")
    
    def _enforce_size_limits(self):
        """Enforce cache size limits using eviction policy"""
        current_entries = len(self._entries)
        current_size_mb = self._stats["total_size_bytes"] / (1024 * 1024)
        
        # Check entry count limit
        if current_entries > self.config.max_entries:
            excess_count = current_entries - self.config.max_entries
            candidates = self._eviction_policy.get_eviction_candidates(
                self._entries, excess_count
            )
            for key in candidates:
                self._remove_entry(key)
                self._stats["evictions"] += 1
        
        # Check size limit
        if current_size_mb > self.config.max_size_mb:
            # Evict entries until under size limit
            while (self._stats["total_size_bytes"] / (1024 * 1024) > self.config.max_size_mb and 
                   self._entries):
                candidates = self._eviction_policy.get_eviction_candidates(
                    self._entries, 1
                )
                if not candidates:
                    break
                self._remove_entry(candidates[0])
                self._stats["evictions"] += 1
    
    def _remove_entry(self, key: str):
        """Remove an entry from the cache"""
        if key in self._entries:
            entry = self._entries[key]
            self._stats["total_size_bytes"] -= entry.size_bytes
            del self._entries[key]
            
            # Remove from access order tracking
            if key in self._access_order:
                del self._access_order[key]
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate the size of a value in bytes"""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode('utf-8') if isinstance(value, str) else value)
            elif isinstance(value, (int, float)):
                return sys.getsizeof(value)
            else:
                # Use pickle to estimate size
                return len(pickle.dumps(value))
        except Exception:
            # Fallback estimate
            return sys.getsizeof(value)
    
    def _compress_value(self, value: Any) -> tuple[bytes, bool]:
        """Compress a value if it's large enough"""
        try:
            # Serialize the value
            serialized = pickle.dumps(value)
            
            # Check if compression is beneficial
            if (self.config.enable_compression and 
                len(serialized) > self.config.compression_threshold_bytes):
                
                compressed = gzip.compress(serialized)
                
                # Only use compression if it actually reduces size
                if len(compressed) < len(serialized):
                    self._stats["compressions"] += 1
                    return compressed, True
            
            return serialized, False
            
        except Exception as e:
            logger.warning(f"Failed to compress cache value: {e}")
            return pickle.dumps(value), False
    
    def _decompress_value(self, data: bytes, compressed: bool) -> Any:
        """Decompress and deserialize a value"""
        try:
            if compressed:
                self._stats["decompressions"] += 1
                decompressed = gzip.decompress(data)
                return pickle.loads(decompressed)
            else:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Failed to decompress cache value: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        start_time = time.time()
        
        with self._lock:
            if key not in self._entries:
                self._stats["misses"] += 1
                self.performance_monitor.update_cache_stats(
                    f"{self.name}_cache", False, (time.time() - start_time) * 1000
                )
                return default
            
            entry = self._entries[key]
            
            # Check if expired
            if entry.is_expired():
                self._remove_entry(key)
                self._stats["misses"] += 1
                self._stats["evictions"] += 1
                self.performance_monitor.update_cache_stats(
                    f"{self.name}_cache", False, (time.time() - start_time) * 1000
                )
                return default
            
            # Update access tracking
            self._access_order[key] = time.time()
            
            # Get the value
            try:
                if entry.compressed:
                    value = self._decompress_value(entry.value, True)
                else:
                    value = self._decompress_value(entry.value, False)
                
                # Update statistics
                entry.access()
                self._stats["hits"] += 1
                
                access_time_ms = (time.time() - start_time) * 1000
                self.performance_monitor.update_cache_stats(
                    f"{self.name}_cache", True, access_time_ms
                )
                
                return value
                
            except Exception as e:
                logger.error(f"Error retrieving cache value for key {key}: {e}")
                self._remove_entry(key)
                self._stats["misses"] += 1
                return default
    
    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Put a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (uses default if None)
            
        Returns:
            bool: True if successfully cached
        """
        try:
            # Compress and serialize the value
            serialized_value, compressed = self._compress_value(value)
            size_bytes = len(serialized_value)
            
            # Use default TTL if not specified
            if ttl_seconds is None:
                ttl_seconds = self.config.default_ttl_seconds
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=serialized_value,
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=0,
                ttl_seconds=ttl_seconds,
                size_bytes=size_bytes,
                compressed=compressed
            )
            
            with self._lock:
                # Remove existing entry if present
                if key in self._entries:
                    old_entry = self._entries[key]
                    self._stats["total_size_bytes"] -= old_entry.size_bytes
                
                # Add new entry
                self._entries[key] = entry
                self._access_order[key] = time.time()
                self._stats["total_size_bytes"] += size_bytes
                
                # Enforce size limits
                self._enforce_size_limits()
            
            return True
            
        except Exception as e:
            logger.error(f"Error caching value for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            bool: True if key was found and deleted
        """
        with self._lock:
            if key in self._entries:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self):
        """Clear all entries from the cache"""
        with self._lock:
            self._entries.clear()
            self._access_order.clear()
            self._stats["total_size_bytes"] = 0
            logger.info(f"Cache {self.name} cleared")
    
    def contains(self, key: str) -> bool:
        """Check if a key exists in the cache (without accessing it)"""
        with self._lock:
            if key not in self._entries:
                return False
            
            entry = self._entries[key]
            if entry.is_expired():
                self._remove_entry(key)
                self._stats["evictions"] += 1
                return False
            
            return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            
            # Calculate average entry size
            avg_entry_size = 0.0
            if self._entries:
                avg_entry_size = self._stats["total_size_bytes"] / len(self._entries)
            
            # Calculate age statistics
            ages = []
            access_counts = []
            for entry in self._entries.values():
                ages.append(entry.get_age_seconds())
                access_counts.append(entry.access_count)
            
            avg_age = sum(ages) / len(ages) if ages else 0.0
            avg_access_count = sum(access_counts) / len(access_counts) if access_counts else 0.0
            
            return {
                "name": self.name,
                "total_entries": len(self._entries),
                "max_entries": self.config.max_entries,
                "total_size_mb": self._stats["total_size_bytes"] / (1024 * 1024),
                "max_size_mb": self.config.max_size_mb,
                "hit_rate": hit_rate,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "compressions": self._stats["compressions"],
                "decompressions": self._stats["decompressions"],
                "average_entry_size_bytes": avg_entry_size,
                "average_entry_age_seconds": avg_age,
                "average_access_count": avg_access_count,
                "utilization_percent": (len(self._entries) / self.config.max_entries) * 100,
                "size_utilization_percent": (self._stats["total_size_bytes"] / (self.config.max_size_mb * 1024 * 1024)) * 100,
                "last_cleanup": datetime.fromtimestamp(self._stats["last_cleanup"]).isoformat(),
                "configuration": {
                    "max_entries": self.config.max_entries,
                    "max_size_mb": self.config.max_size_mb,
                    "default_ttl_seconds": self.config.default_ttl_seconds,
                    "enable_compression": self.config.enable_compression,
                    "eviction_policy": self.config.eviction_policy,
                    "cleanup_interval_seconds": self.config.cleanup_interval_seconds
                }
            }
    
    def _save_to_persistence(self):
        """Save cache to persistent storage"""
        if not self.config.enable_persistence or not self.config.persistence_file:
            return
        
        try:
            persistence_data = {
                "entries": {},
                "stats": self._stats,
                "saved_at": time.time()
            }
            
            # Only save non-expired entries
            with self._lock:
                for key, entry in self._entries.items():
                    if not entry.is_expired():
                        persistence_data["entries"][key] = {
                            "value": entry.value,
                            "created_at": entry.created_at,
                            "last_accessed": entry.last_accessed,
                            "access_count": entry.access_count,
                            "ttl_seconds": entry.ttl_seconds,
                            "size_bytes": entry.size_bytes,
                            "compressed": entry.compressed,
                            "metadata": entry.metadata
                        }
            
            # Save to file
            with open(self.config.persistence_file, 'wb') as f:
                pickle.dump(persistence_data, f)
            
            logger.info(f"Cache {self.name} saved to {self.config.persistence_file}")
            
        except Exception as e:
            logger.error(f"Error saving cache {self.name} to persistence: {e}")
    
    def _load_from_persistence(self):
        """Load cache from persistent storage"""
        if not Path(self.config.persistence_file).exists():
            return
        
        try:
            with open(self.config.persistence_file, 'rb') as f:
                persistence_data = pickle.load(f)
            
            # Restore entries
            loaded_count = 0
            with self._lock:
                for key, entry_data in persistence_data.get("entries", {}).items():
                    entry = CacheEntry(
                        key=key,
                        value=entry_data["value"],
                        created_at=entry_data["created_at"],
                        last_accessed=entry_data["last_accessed"],
                        access_count=entry_data["access_count"],
                        ttl_seconds=entry_data["ttl_seconds"],
                        size_bytes=entry_data["size_bytes"],
                        compressed=entry_data.get("compressed", False),
                        metadata=entry_data.get("metadata", {})
                    )
                    
                    # Only restore non-expired entries
                    if not entry.is_expired():
                        self._entries[key] = entry
                        self._access_order[key] = entry.last_accessed
                        self._stats["total_size_bytes"] += entry.size_bytes
                        loaded_count += 1
                
                # Restore statistics (but don't overwrite current counters)
                saved_stats = persistence_data.get("stats", {})
                for key in ["compressions", "decompressions"]:
                    if key in saved_stats:
                        self._stats[key] = saved_stats[key]
            
            logger.info(f"Cache {self.name} loaded {loaded_count} entries from persistence")
            
        except Exception as e:
            logger.error(f"Error loading cache {self.name} from persistence: {e}")
    
    def shutdown(self):
        """Shutdown the cache and cleanup resources"""
        # Stop cleanup thread
        if self._cleanup_thread:
            self._shutdown_event.set()
            self._cleanup_thread.join(timeout=5)
        
        # Save to persistence if enabled
        if self.config.enable_persistence:
            self._save_to_persistence()
        
        logger.info(f"Cache {self.name} shutdown complete")

class MultiLevelCacheManager:
    """
    Manager for multiple cache levels with different policies
    """
    
    def __init__(self):
        """Initialize the multi-level cache manager"""
        self._caches: Dict[str, EnhancedCache] = {}
        self._lock = threading.RLock()
        
        # Default cache configurations
        self._default_configs = {
            "memory_cache": CacheConfiguration(
                max_entries=500,
                max_size_mb=50.0,
                default_ttl_seconds=3600,  # 1 hour
                eviction_policy="lru",
                enable_compression=True
            ),
            "analysis_cache": CacheConfiguration(
                max_entries=100,
                max_size_mb=200.0,
                default_ttl_seconds=1800,  # 30 minutes
                eviction_policy="ttl",
                enable_compression=True
            ),
            "formatted_cache": CacheConfiguration(
                max_entries=200,
                max_size_mb=100.0,
                default_ttl_seconds=1800,  # 30 minutes
                eviction_policy="lru",
                enable_compression=True
            )
        }
        
        logger.info("Multi-level cache manager initialized")
    
    def get_cache(self, cache_name: str, config: Optional[CacheConfiguration] = None) -> EnhancedCache:
        """
        Get or create a cache with the specified name
        
        Args:
            cache_name: Name of the cache
            config: Cache configuration (uses default if None)
            
        Returns:
            EnhancedCache: The cache instance
        """
        with self._lock:
            if cache_name not in self._caches:
                # Use provided config or default
                cache_config = config or self._default_configs.get(
                    cache_name, CacheConfiguration()
                )
                
                self._caches[cache_name] = EnhancedCache(cache_name, cache_config)
                logger.info(f"Created cache: {cache_name}")
            
            return self._caches[cache_name]
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        with self._lock:
            return {
                name: cache.get_statistics() 
                for name, cache in self._caches.items()
            }
    
    def clear_all_caches(self):
        """Clear all caches"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
            logger.info("All caches cleared")
    
    def shutdown_all(self):
        """Shutdown all caches"""
        with self._lock:
            for cache in self._caches.values():
                cache.shutdown()
            self._caches.clear()
            logger.info("All caches shutdown")

# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> MultiLevelCacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = MultiLevelCacheManager()
    return _cache_manager

def get_cache(cache_name: str, config: Optional[CacheConfiguration] = None) -> EnhancedCache:
    """Get a specific cache from the global manager"""
    return get_cache_manager().get_cache(cache_name, config)

def shutdown_cache_manager():
    """Shutdown global cache manager"""
    global _cache_manager
    if _cache_manager:
        _cache_manager.shutdown_all()
        _cache_manager = None