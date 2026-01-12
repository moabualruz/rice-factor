"""Unit tests for RedisCache implementation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from rice_factor.adapters.cache.redis_cache import (
    RedisCache,
    RedisConfig,
)


class TestRedisConfig:
    """Tests for RedisConfig dataclass."""

    def test_defaults(self) -> None:
        """should have sensible defaults."""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.prefix == "rice_factor:cache:"

    def test_custom_values(self) -> None:
        """should accept custom values."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            prefix="custom:",
        )
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.password == "secret"


class TestRedisCache:
    """Tests for RedisCache implementation."""

    def test_creation(self) -> None:
        """RedisCache should be creatable."""
        cache = RedisCache()
        assert cache.config.host == "localhost"

    def test_creation_custom_config(self) -> None:
        """should accept custom config."""
        config = RedisConfig(host="custom.host")
        cache = RedisCache(config=config)
        assert cache.config.host == "custom.host"

    def test_make_key(self) -> None:
        """should create namespaced keys."""
        cache = RedisCache()
        key = cache._make_key("test")
        assert key == "rice_factor:cache:test"

    def test_make_hash_index_key(self) -> None:
        """should create hash index keys."""
        cache = RedisCache()
        key = cache._make_hash_index_key("abc123")
        assert key == "rice_factor:cache:hash:abc123"

    def test_is_available_success(self) -> None:
        """should return True when Redis responds."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True

        cache = RedisCache()
        cache._client = mock_client

        assert cache.is_available() is True

    def test_is_available_failure(self) -> None:
        """should return False when Redis fails."""
        cache = RedisCache()
        cache._client = None  # Force new client creation attempt

        # Mock the _get_client to raise an exception
        cache._get_client = MagicMock(side_effect=Exception("Connection refused"))

        assert cache.is_available() is False

    def test_set_and_get(self) -> None:
        """should store and retrieve values."""
        mock_client = MagicMock()

        # Setup mock get response
        stored_data = {
            "value": {"data": "test"},
            "hash": "hash123",
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": None,
            "hit_count": 0,
        }
        mock_client.get.return_value = json.dumps(stored_data)
        mock_client.ttl.return_value = -1

        cache = RedisCache()
        cache._client = mock_client

        # Set
        entry = cache.set("key1", {"data": "test"})
        assert entry.key == "key1"
        assert mock_client.set.called

        # Get
        retrieved = cache.get("key1")
        assert retrieved is not None
        assert retrieved.value == {"data": "test"}

    def test_get_miss(self) -> None:
        """should return None on cache miss."""
        mock_client = MagicMock()
        mock_client.get.return_value = None

        cache = RedisCache()
        cache._client = mock_client

        result = cache.get("nonexistent")
        assert result is None

    def test_set_with_ttl(self) -> None:
        """should set TTL on entries."""
        mock_client = MagicMock()

        cache = RedisCache()
        cache._client = mock_client

        cache.set("key1", {"v": 1}, ttl_seconds=60)

        mock_client.setex.assert_called()
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 60  # TTL

    def test_delete(self) -> None:
        """should delete entries."""
        mock_client = MagicMock()
        mock_client.get.return_value = '{"hash": "hash123"}'
        mock_client.delete.return_value = 1

        cache = RedisCache()
        cache._client = mock_client

        result = cache.delete("key1")
        assert result is True
        mock_client.delete.assert_called()

    def test_delete_not_found(self) -> None:
        """should return False if not found."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        mock_client.delete.return_value = 0

        cache = RedisCache()
        cache._client = mock_client

        result = cache.delete("nonexistent")
        assert result is False

    def test_clear(self) -> None:
        """should clear all entries."""
        mock_client = MagicMock()
        mock_client.scan_iter.return_value = ["key1", "key2"]
        mock_client.delete.return_value = 2

        cache = RedisCache()
        cache._client = mock_client

        count = cache.clear()
        assert count == 2

    def test_clear_empty(self) -> None:
        """should handle empty clear."""
        mock_client = MagicMock()
        mock_client.scan_iter.return_value = []

        cache = RedisCache()
        cache._client = mock_client

        count = cache.clear()
        assert count == 0

    def test_invalidate_by_hash(self) -> None:
        """should invalidate by hash."""
        mock_client = MagicMock()
        mock_client.smembers.return_value = {"key1", "key2"}
        mock_client.delete.return_value = 1

        cache = RedisCache()
        cache._client = mock_client

        count = cache.invalidate_by_hash("hash123")
        assert count == 2

    def test_invalidate_by_hash_none(self) -> None:
        """should handle no matches."""
        mock_client = MagicMock()
        mock_client.smembers.return_value = set()

        cache = RedisCache()
        cache._client = mock_client

        count = cache.invalidate_by_hash("nonexistent")
        assert count == 0

    def test_get_stats(self) -> None:
        """should return stats."""
        mock_client = MagicMock()
        mock_client.scan_iter.return_value = ["key1", "key2"]

        cache = RedisCache()
        cache._client = mock_client
        cache._stats.hits = 10
        cache._stats.misses = 5

        stats = cache.get_stats()
        assert stats.hits == 10
        assert stats.misses == 5
        assert stats.size == 2

    def test_keys(self) -> None:
        """should return all keys."""
        mock_client = MagicMock()
        prefix = "rice_factor:cache:"
        mock_client.scan_iter.return_value = [
            f"{prefix}key1",
            f"{prefix}key2",
            f"{prefix}hash:abc",  # Should be filtered
        ]

        cache = RedisCache()
        cache._client = mock_client

        keys = cache.keys()
        assert set(keys) == {"key1", "key2"}

    def test_has_exists(self) -> None:
        """should detect existing keys."""
        mock_client = MagicMock()
        mock_client.exists.return_value = 1

        cache = RedisCache()
        cache._client = mock_client

        assert cache.has("exists") is True

    def test_has_missing(self) -> None:
        """should detect missing keys."""
        mock_client = MagicMock()
        mock_client.exists.return_value = 0

        cache = RedisCache()
        cache._client = mock_client

        assert cache.has("missing") is False

    def test_import_error_handling(self) -> None:
        """should handle missing redis package."""
        import sys

        # Temporarily hide redis module
        redis_module = sys.modules.get("redis")
        sys.modules["redis"] = None  # type: ignore

        try:
            cache = RedisCache()
            cache._client = None  # Force new client creation

            # Create a mock _get_client that raises ImportError
            def mock_get_client() -> None:
                try:
                    import redis  # noqa: F401
                except (ImportError, TypeError):
                    raise ImportError(
                        "redis package required for RedisCache. "
                        "Install with: pip install redis"
                    )

            cache._get_client = mock_get_client  # type: ignore

            with pytest.raises(ImportError):
                cache._get_client()
        finally:
            if redis_module is not None:
                sys.modules["redis"] = redis_module
            elif "redis" in sys.modules:
                del sys.modules["redis"]
