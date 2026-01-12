"""Unit tests for ArtifactCache implementations."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest

from rice_factor.adapters.cache.artifact_cache import (
    CacheEntry,
    CacheStats,
    MemoryCache,
    compute_hash,
)


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_creation(self) -> None:
        """CacheEntry should be creatable."""
        now = datetime.now(UTC)
        entry = CacheEntry(
            key="test-key",
            value={"data": "value"},
            hash="abc123",
            created_at=now,
        )
        assert entry.key == "test-key"
        assert entry.value == {"data": "value"}

    def test_is_expired_no_expiry(self) -> None:
        """should not be expired without expiry time."""
        entry = CacheEntry(
            key="test",
            value={},
            hash="hash",
            created_at=datetime.now(UTC),
        )
        assert entry.is_expired is False

    def test_is_expired_future(self) -> None:
        """should not be expired with future expiry."""
        entry = CacheEntry(
            key="test",
            value={},
            hash="hash",
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert entry.is_expired is False

    def test_is_expired_past(self) -> None:
        """should be expired with past expiry."""
        entry = CacheEntry(
            key="test",
            value={},
            hash="hash",
            created_at=datetime.now(UTC) - timedelta(hours=2),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert entry.is_expired is True

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        now = datetime.now(UTC)
        entry = CacheEntry(
            key="test",
            value={"a": 1},
            hash="hash123",
            created_at=now,
            hit_count=5,
        )
        data = entry.to_dict()
        assert data["key"] == "test"
        assert data["hash"] == "hash123"
        assert data["hit_count"] == 5


class TestCacheStats:
    """Tests for CacheStats dataclass."""

    def test_creation(self) -> None:
        """CacheStats should be creatable."""
        stats = CacheStats(hits=10, misses=5)
        assert stats.hits == 10
        assert stats.misses == 5

    def test_hit_rate_with_hits(self) -> None:
        """should calculate hit rate."""
        stats = CacheStats(hits=75, misses=25)
        assert stats.hit_rate == 75.0

    def test_hit_rate_zero_total(self) -> None:
        """should handle zero total."""
        stats = CacheStats(hits=0, misses=0)
        assert stats.hit_rate == 0.0

    def test_to_dict(self) -> None:
        """should serialize to dictionary."""
        stats = CacheStats(hits=10, misses=2, evictions=1, size=50, max_size=100)
        data = stats.to_dict()
        assert data["hits"] == 10
        assert data["misses"] == 2
        assert "hit_rate" in data


class TestComputeHash:
    """Tests for compute_hash function."""

    def test_compute_hash(self) -> None:
        """should compute consistent hash."""
        data = {"a": 1, "b": 2}
        hash1 = compute_hash(data)
        hash2 = compute_hash(data)
        assert hash1 == hash2

    def test_hash_different_data(self) -> None:
        """should compute different hashes for different data."""
        hash1 = compute_hash({"a": 1})
        hash2 = compute_hash({"a": 2})
        assert hash1 != hash2

    def test_hash_order_independent(self) -> None:
        """should be order independent for dict keys."""
        hash1 = compute_hash({"a": 1, "b": 2})
        hash2 = compute_hash({"b": 2, "a": 1})
        assert hash1 == hash2


class TestMemoryCache:
    """Tests for MemoryCache implementation."""

    def test_creation(self) -> None:
        """MemoryCache should be creatable."""
        cache = MemoryCache()
        assert cache.max_size == 1000

    def test_creation_custom_size(self) -> None:
        """should accept custom size."""
        cache = MemoryCache(max_size=100)
        assert cache.max_size == 100

    def test_set_and_get(self) -> None:
        """should store and retrieve values."""
        cache = MemoryCache()
        entry = cache.set("key1", {"data": "value"})
        assert entry.key == "key1"

        retrieved = cache.get("key1")
        assert retrieved is not None
        assert retrieved.value == {"data": "value"}

    def test_get_nonexistent(self) -> None:
        """should return None for nonexistent key."""
        cache = MemoryCache()
        result = cache.get("nonexistent")
        assert result is None

    def test_get_updates_hit_count(self) -> None:
        """should update hit count on get."""
        cache = MemoryCache()
        cache.set("key1", {"data": "value"})

        entry1 = cache.get("key1")
        assert entry1.hit_count == 1

        entry2 = cache.get("key1")
        assert entry2.hit_count == 2

    def test_delete(self) -> None:
        """should delete entries."""
        cache = MemoryCache()
        cache.set("key1", {"data": "value"})

        result = cache.delete("key1")
        assert result is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self) -> None:
        """should return False for nonexistent delete."""
        cache = MemoryCache()
        result = cache.delete("nonexistent")
        assert result is False

    def test_clear(self) -> None:
        """should clear all entries."""
        cache = MemoryCache()
        cache.set("key1", {"a": 1})
        cache.set("key2", {"b": 2})

        count = cache.clear()
        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_lru_eviction(self) -> None:
        """should evict least recently used."""
        cache = MemoryCache(max_size=3)
        cache.set("a", {"v": 1})
        cache.set("b", {"v": 2})
        cache.set("c", {"v": 3})

        # Access 'a' to make it recent
        cache.get("a")

        # Add new entry, should evict 'b' (least recently used)
        cache.set("d", {"v": 4})

        assert cache.get("a") is not None  # Still present
        assert cache.get("b") is None  # Evicted
        assert cache.get("c") is not None
        assert cache.get("d") is not None

    def test_ttl_expiry(self) -> None:
        """should expire entries after TTL."""
        cache = MemoryCache()
        cache.set("short", {"v": 1}, ttl_seconds=0.05)

        # Should be present immediately
        assert cache.get("short") is not None

        # Wait for expiry
        time.sleep(0.1)

        # Should be expired
        assert cache.get("short") is None

    def test_default_ttl(self) -> None:
        """should use default TTL."""
        cache = MemoryCache(default_ttl=0.05)
        cache.set("key1", {"v": 1})

        time.sleep(0.1)
        assert cache.get("key1") is None

    def test_invalidate_by_hash(self) -> None:
        """should invalidate by hash."""
        cache = MemoryCache()
        entry = cache.set("key1", {"data": "value"})
        content_hash = entry.hash

        # Add another with different hash
        cache.set("key2", {"other": "data"})

        count = cache.invalidate_by_hash(content_hash)
        assert count == 1
        assert cache.get("key1") is None
        assert cache.get("key2") is not None

    def test_get_stats(self) -> None:
        """should return accurate stats."""
        cache = MemoryCache(max_size=100)
        cache.set("key1", {"v": 1})
        cache.set("key2", {"v": 2})

        cache.get("key1")  # hit
        cache.get("key2")  # hit
        cache.get("nonexistent")  # miss

        stats = cache.get_stats()
        assert stats.hits == 2
        assert stats.misses == 1
        assert stats.size == 2
        assert stats.max_size == 100

    def test_keys(self) -> None:
        """should return all keys."""
        cache = MemoryCache()
        cache.set("a", {"v": 1})
        cache.set("b", {"v": 2})

        keys = cache.keys()
        assert set(keys) == {"a", "b"}

    def test_has(self) -> None:
        """should check key existence."""
        cache = MemoryCache()
        cache.set("exists", {"v": 1})

        assert cache.has("exists") is True
        assert cache.has("missing") is False

    def test_has_doesnt_count_as_hit(self) -> None:
        """has() should not count as hit."""
        cache = MemoryCache()
        cache.set("key1", {"v": 1})

        cache.has("key1")
        cache.has("key1")

        stats = cache.get_stats()
        assert stats.hits == 0

    def test_cleanup_expired(self) -> None:
        """should cleanup expired entries."""
        cache = MemoryCache()
        cache.set("short1", {"v": 1}, ttl_seconds=0.05)
        cache.set("short2", {"v": 2}, ttl_seconds=0.05)
        cache.set("long", {"v": 3}, ttl_seconds=60)

        time.sleep(0.1)

        count = cache.cleanup_expired()
        assert count == 2
        assert cache.has("long") is True

    def test_overwrite_existing(self) -> None:
        """should overwrite existing entries."""
        cache = MemoryCache()
        cache.set("key1", {"v": 1})
        cache.set("key1", {"v": 2})

        entry = cache.get("key1")
        assert entry.value == {"v": 2}
        assert entry.hit_count == 1  # Reset on overwrite

    def test_thread_safety(self) -> None:
        """should be thread-safe."""
        import threading

        cache = MemoryCache(max_size=1000)
        errors: list[Exception] = []

        def worker(thread_id: int) -> None:
            try:
                for i in range(100):
                    key = f"thread{thread_id}-{i}"
                    cache.set(key, {"v": i})
                    cache.get(key)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
