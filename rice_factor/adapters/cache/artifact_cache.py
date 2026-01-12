"""Artifact caching layer with memory and Redis implementations.

This module provides caching infrastructure for artifacts to improve
performance by avoiding redundant disk I/O and validation operations.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from abc import abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable


@dataclass
class CacheEntry:
    """A cached artifact entry.

    Attributes:
        key: Cache key.
        value: Cached artifact data.
        hash: Content hash for invalidation.
        created_at: When the entry was created.
        expires_at: When the entry expires (None = never).
        hit_count: Number of times this entry was accessed.
        last_accessed: Last access timestamp.
    """

    key: str
    value: dict[str, Any]
    hash: str
    created_at: datetime
    expires_at: datetime | None = None
    hit_count: int = 0
    last_accessed: datetime | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "hash": self.hash,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "hit_count": self.hit_count,
            "last_accessed": (
                self.last_accessed.isoformat() if self.last_accessed else None
            ),
        }


@dataclass
class CacheStats:
    """Statistics for cache operations.

    Attributes:
        hits: Number of cache hits.
        misses: Number of cache misses.
        evictions: Number of evicted entries.
        size: Current number of entries.
        max_size: Maximum cache size.
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return (self.hits / total) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "size": self.size,
            "max_size": self.max_size,
            "hit_rate": round(self.hit_rate, 2),
        }


@runtime_checkable
class ArtifactCachePort(Protocol):
    """Protocol for artifact cache implementations."""

    @abstractmethod
    def get(self, key: str) -> CacheEntry | None:
        """Get an entry from the cache.

        Args:
            key: Cache key.

        Returns:
            CacheEntry if found and not expired, None otherwise.
        """
        ...

    @abstractmethod
    def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl_seconds: float | None = None,
    ) -> CacheEntry:
        """Store an entry in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Time to live in seconds.

        Returns:
            Created CacheEntry.
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an entry from the cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        ...

    @abstractmethod
    def clear(self) -> int:
        """Clear all entries from the cache.

        Returns:
            Number of entries cleared.
        """
        ...

    @abstractmethod
    def invalidate_by_hash(self, content_hash: str) -> int:
        """Invalidate entries by content hash.

        Args:
            content_hash: Hash to match.

        Returns:
            Number of entries invalidated.
        """
        ...

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats with current metrics.
        """
        ...


def compute_hash(data: dict[str, Any]) -> str:
    """Compute a hash for artifact data.

    Args:
        data: Artifact data to hash.

    Returns:
        SHA256 hash string.
    """
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class MemoryCache:
    """In-memory LRU cache for artifacts.

    Implements an LRU (Least Recently Used) eviction policy with
    optional TTL (time-to-live) for entries.

    Attributes:
        max_size: Maximum number of entries.
        default_ttl: Default TTL in seconds (None = no expiry).
    """

    max_size: int = 1000
    default_ttl: float | None = None
    _cache: OrderedDict[str, CacheEntry] = field(
        default_factory=OrderedDict, init=False, repr=False
    )
    _lock: threading.RLock = field(
        default_factory=threading.RLock, init=False, repr=False
    )
    _stats: CacheStats = field(default_factory=CacheStats, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize stats."""
        self._stats.max_size = self.max_size

    def get(self, key: str) -> CacheEntry | None:
        """Get an entry from the cache.

        Args:
            key: Cache key.

        Returns:
            CacheEntry if found and not expired, None otherwise.
        """
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            # Check expiry
            if entry.is_expired:
                del self._cache[key]
                self._stats.misses += 1
                self._stats.size = len(self._cache)
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            # Update access stats
            entry.hit_count += 1
            entry.last_accessed = datetime.now(UTC)

            self._stats.hits += 1
            return entry

    def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl_seconds: float | None = None,
    ) -> CacheEntry:
        """Store an entry in the cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl_seconds: Time to live in seconds (uses default if None).

        Returns:
            Created CacheEntry.
        """
        with self._lock:
            now = datetime.now(UTC)
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

            expires_at = None
            if ttl is not None:
                from datetime import timedelta

                expires_at = now + timedelta(seconds=ttl)

            entry = CacheEntry(
                key=key,
                value=value,
                hash=compute_hash(value),
                created_at=now,
                expires_at=expires_at,
                hit_count=0,
                last_accessed=now,
            )

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Evict if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)  # Remove oldest
                self._stats.evictions += 1

            self._cache[key] = entry
            self._stats.size = len(self._cache)
            return entry

    def delete(self, key: str) -> bool:
        """Delete an entry from the cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False

    def clear(self) -> int:
        """Clear all entries from the cache.

        Returns:
            Number of entries cleared.
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.size = 0
            return count

    def invalidate_by_hash(self, content_hash: str) -> int:
        """Invalidate entries by content hash.

        Args:
            content_hash: Hash to match.

        Returns:
            Number of entries invalidated.
        """
        with self._lock:
            keys_to_delete = [
                key for key, entry in self._cache.items() if entry.hash == content_hash
            ]
            for key in keys_to_delete:
                del self._cache[key]
            self._stats.size = len(self._cache)
            return len(keys_to_delete)

    def get_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats with current metrics.
        """
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=len(self._cache),
                max_size=self.max_size,
            )

    def keys(self) -> list[str]:
        """Get all cache keys.

        Returns:
            List of keys.
        """
        with self._lock:
            return list(self._cache.keys())

    def has(self, key: str) -> bool:
        """Check if key exists (without counting as hit).

        Args:
            key: Cache key.

        Returns:
            True if exists and not expired.
        """
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                self._stats.size = len(self._cache)
                return False
            return True

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        with self._lock:
            now = datetime.now(UTC)
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry.expires_at and entry.expires_at < now
            ]
            for key in expired_keys:
                del self._cache[key]
            self._stats.size = len(self._cache)
            return len(expired_keys)
