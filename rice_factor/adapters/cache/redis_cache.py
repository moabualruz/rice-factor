"""Redis-based artifact cache implementation.

This module provides a Redis-backed cache for distributed environments
where multiple processes need to share cached artifacts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from rice_factor.adapters.cache.artifact_cache import (
    ArtifactCachePort,
    CacheEntry,
    CacheStats,
    compute_hash,
)


@dataclass
class RedisConfig:
    """Configuration for Redis connection.

    Attributes:
        host: Redis host.
        port: Redis port.
        db: Redis database number.
        password: Redis password (optional).
        prefix: Key prefix for namespacing.
        socket_timeout: Socket timeout in seconds.
    """

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    prefix: str = "rice_factor:cache:"
    socket_timeout: float = 5.0


@dataclass
class RedisCache:
    """Redis-based artifact cache.

    Implements ArtifactCachePort using Redis as the backend for
    distributed caching across multiple processes.

    Attributes:
        config: Redis configuration.
    """

    config: RedisConfig = field(default_factory=RedisConfig)
    _client: Any = field(default=None, init=False, repr=False)
    _stats: CacheStats = field(default_factory=CacheStats, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize Redis client."""
        self._connected = False

    def _get_client(self) -> Any:
        """Get or create Redis client.

        Returns:
            Redis client instance.

        Raises:
            ImportError: If redis package not installed.
            ConnectionError: If cannot connect to Redis.
        """
        if self._client is not None:
            return self._client

        try:
            import redis
        except ImportError as e:
            raise ImportError(
                "redis package required for RedisCache. "
                "Install with: pip install redis"
            ) from e

        self._client = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            db=self.config.db,
            password=self.config.password,
            socket_timeout=self.config.socket_timeout,
            decode_responses=True,
        )
        self._connected = True
        return self._client

    def _make_key(self, key: str) -> str:
        """Create namespaced Redis key.

        Args:
            key: Base key.

        Returns:
            Prefixed key.
        """
        return f"{self.config.prefix}{key}"

    def _make_hash_index_key(self, content_hash: str) -> str:
        """Create hash index key.

        Args:
            content_hash: Content hash.

        Returns:
            Hash index key.
        """
        return f"{self.config.prefix}hash:{content_hash}"

    def is_available(self) -> bool:
        """Check if Redis is available.

        Returns:
            True if Redis is connected and responding.
        """
        try:
            client = self._get_client()
            return client.ping()
        except Exception:
            return False

    def get(self, key: str) -> CacheEntry | None:
        """Get an entry from the cache.

        Args:
            key: Cache key.

        Returns:
            CacheEntry if found, None otherwise.
        """
        try:
            client = self._get_client()
            redis_key = self._make_key(key)
            data = client.get(redis_key)

            if data is None:
                self._stats.misses += 1
                return None

            entry_data = json.loads(data)

            # Check expiry (Redis handles TTL, but double-check)
            expires_at = None
            if entry_data.get("expires_at"):
                expires_at = datetime.fromisoformat(entry_data["expires_at"])
                if datetime.now(UTC) > expires_at:
                    client.delete(redis_key)
                    self._stats.misses += 1
                    return None

            entry = CacheEntry(
                key=key,
                value=entry_data["value"],
                hash=entry_data["hash"],
                created_at=datetime.fromisoformat(entry_data["created_at"]),
                expires_at=expires_at,
                hit_count=entry_data.get("hit_count", 0) + 1,
                last_accessed=datetime.now(UTC),
            )

            # Update hit count in Redis
            entry_data["hit_count"] = entry.hit_count
            entry_data["last_accessed"] = entry.last_accessed.isoformat()
            ttl = client.ttl(redis_key)
            if ttl > 0:
                client.setex(redis_key, ttl, json.dumps(entry_data))
            else:
                client.set(redis_key, json.dumps(entry_data))

            self._stats.hits += 1
            return entry

        except Exception:
            self._stats.misses += 1
            return None

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
        now = datetime.now(UTC)
        content_hash = compute_hash(value)

        expires_at = None
        if ttl_seconds is not None:
            from datetime import timedelta

            expires_at = now + timedelta(seconds=ttl_seconds)

        entry = CacheEntry(
            key=key,
            value=value,
            hash=content_hash,
            created_at=now,
            expires_at=expires_at,
            hit_count=0,
            last_accessed=now,
        )

        entry_data = {
            "value": value,
            "hash": content_hash,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "hit_count": 0,
            "last_accessed": now.isoformat(),
        }

        try:
            client = self._get_client()
            redis_key = self._make_key(key)

            if ttl_seconds is not None:
                client.setex(redis_key, int(ttl_seconds), json.dumps(entry_data))
            else:
                client.set(redis_key, json.dumps(entry_data))

            # Update hash index for invalidation
            hash_index_key = self._make_hash_index_key(content_hash)
            client.sadd(hash_index_key, key)

        except Exception:
            pass  # Cache failures should not break the application

        return entry

    def delete(self, key: str) -> bool:
        """Delete an entry from the cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        try:
            client = self._get_client()
            redis_key = self._make_key(key)

            # Get hash before deletion for index cleanup
            data = client.get(redis_key)
            if data:
                entry_data = json.loads(data)
                content_hash = entry_data.get("hash")
                if content_hash:
                    hash_index_key = self._make_hash_index_key(content_hash)
                    client.srem(hash_index_key, key)

            result = client.delete(redis_key)
            return result > 0
        except Exception:
            return False

    def clear(self) -> int:
        """Clear all entries from the cache.

        Returns:
            Number of entries cleared.
        """
        try:
            client = self._get_client()
            pattern = f"{self.config.prefix}*"
            keys = list(client.scan_iter(pattern))
            if keys:
                return client.delete(*keys)
            return 0
        except Exception:
            return 0

    def invalidate_by_hash(self, content_hash: str) -> int:
        """Invalidate entries by content hash.

        Args:
            content_hash: Hash to match.

        Returns:
            Number of entries invalidated.
        """
        try:
            client = self._get_client()
            hash_index_key = self._make_hash_index_key(content_hash)
            keys = client.smembers(hash_index_key)

            if not keys:
                return 0

            count = 0
            for key in keys:
                redis_key = self._make_key(key)
                if client.delete(redis_key):
                    count += 1

            client.delete(hash_index_key)
            return count

        except Exception:
            return 0

    def get_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            CacheStats with current metrics.
        """
        try:
            client = self._get_client()
            pattern = f"{self.config.prefix}*"
            # Count only non-hash-index keys
            prefix_len = len(self.config.prefix)
            size = sum(
                1
                for key in client.scan_iter(pattern)
                if not key[prefix_len:].startswith("hash:")
            )

            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                size=size,
                max_size=0,  # Redis doesn't have a fixed max size
            )
        except Exception:
            return self._stats

    def keys(self) -> list[str]:
        """Get all cache keys (without prefix).

        Returns:
            List of keys.
        """
        try:
            client = self._get_client()
            pattern = f"{self.config.prefix}*"
            prefix_len = len(self.config.prefix)
            return [
                key[prefix_len:]
                for key in client.scan_iter(pattern)
                if not key[prefix_len:].startswith("hash:")
            ]
        except Exception:
            return []

    def has(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Cache key.

        Returns:
            True if exists.
        """
        try:
            client = self._get_client()
            redis_key = self._make_key(key)
            return client.exists(redis_key) > 0
        except Exception:
            return False
