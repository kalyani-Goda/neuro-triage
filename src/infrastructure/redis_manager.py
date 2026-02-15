"""Redis client for session state management."""

import redis
import json
import logging
from typing import Dict, Any, Optional
from datetime import timedelta

from src.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Manager for Redis operations."""

    def __init__(self):
        """Initialize Redis client."""
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)

    def set_session_state(
        self,
        session_id: str,
        state: Dict[str, Any],
        expire_hours: int = 24,
    ) -> bool:
        """Store session state in Redis."""
        try:
            key = f"session:{session_id}"
            self.redis_client.setex(
                key,
                timedelta(hours=expire_hours),
                json.dumps(state),
            )
            logger.info(f"Session state stored: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store session state: {e}")
            return False

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session state from Redis."""
        try:
            key = f"session:{session_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve session state: {e}")
            return None

    def delete_session_state(self, session_id: str) -> bool:
        """Delete session state from Redis."""
        try:
            key = f"session:{session_id}"
            self.redis_client.delete(key)
            logger.info(f"Session state deleted: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session state: {e}")
            return False

    def cache_query_result(
        self,
        query_key: str,
        result: Any,
        expire_hours: int = 1,
    ) -> bool:
        """Cache query results for quick retrieval."""
        try:
            cache_key = f"cache:{query_key}"
            self.redis_client.setex(
                cache_key,
                timedelta(hours=expire_hours),
                json.dumps(result),
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
            return False

    def get_cached_query(self, query_key: str) -> Optional[Any]:
        """Retrieve cached query result."""
        try:
            cache_key = f"cache:{query_key}"
            data = self.redis_client.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve cached query: {e}")
            return None

    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global Redis manager instance
redis_manager = RedisManager()
