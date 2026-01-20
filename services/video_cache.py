"""Кеш для найденных видео URLs."""

import time
from typing import Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class VideoCache:
    """
    Кеш видео URLs с TTL.

    Хранит найденные видео URLs чтобы не искать их повторно.
    TTL: 1 час (видео редко меняются).
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Args:
            ttl_seconds: Time to live в секундах (по умолчанию 1 час)
        """
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl_seconds

    def get(self, nm_id: str) -> Tuple[bool, Optional[str]]:
        """
        Получить URL видео из кеша.

        Args:
            nm_id: Артикул товара

        Returns:
            (found, url) - found=True если в кеше, url может быть None если видео нет
        """
        if nm_id not in self._cache:
            return (False, None)

        entry = self._cache[nm_id]

        # Проверка TTL
        if time.time() - entry['timestamp'] > self._ttl:
            logger.debug(f"Video cache EXPIRED for {nm_id}")
            del self._cache[nm_id]
            return (False, None)

        logger.info(f"Video cache HIT for {nm_id}")
        return (True, entry['url'])

    def set(self, nm_id: str, url: Optional[str]):
        """
        Сохранить URL видео в кеш.

        Args:
            nm_id: Артикул товара
            url: URL видео (None если видео нет)
        """
        self._cache[nm_id] = {
            'url': url,
            'timestamp': time.time()
        }

        status = "found" if url else "not found"
        logger.info(f"Video cache SET for {nm_id}: {status}")

    def clear_expired(self):
        """Очистить истекшие записи."""
        now = time.time()
        expired_keys = [
            nm_id for nm_id, entry in self._cache.items()
            if now - entry['timestamp'] > self._ttl
        ]

        for nm_id in expired_keys:
            del self._cache[nm_id]

        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired video cache entries")

    def size(self) -> int:
        """Размер кеша."""
        return len(self._cache)


# Глобальный экземпляр кеша
_video_cache = VideoCache()


def get_video_cache() -> VideoCache:
    """Получить глобальный экземпляр кеша."""
    return _video_cache
