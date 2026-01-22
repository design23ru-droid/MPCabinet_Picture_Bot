"""Тесты для services/video_cache.py"""

import time
from services.video_cache import VideoCache


class TestVideoCache:
    """Тесты для кеша видео."""

    def test_cache_miss(self):
        """Тест: нет в кеше."""
        cache = VideoCache()
        found, url = cache.get("123456")

        assert found is False
        assert url is None

    def test_cache_set_and_get_with_url(self):
        """Тест: сохранение и получение URL."""
        cache = VideoCache()
        test_url = "https://example.com/video.m3u8"

        cache.set("123456", test_url)
        found, url = cache.get("123456")

        assert found is True
        assert url == test_url

    def test_cache_set_and_get_no_video(self):
        """Тест: сохранение и получение None (видео нет)."""
        cache = VideoCache()

        cache.set("123456", None)
        found, url = cache.get("123456")

        assert found is True
        assert url is None

    def test_cache_ttl_expiration(self):
        """Тест: истечение TTL."""
        cache = VideoCache(ttl_seconds=1)  # 1 секунда
        cache.set("123456", "https://example.com/video.m3u8")

        # Сразу после сохранения - в кеше
        found, _ = cache.get("123456")
        assert found is True

        # Через 1.1 секунды - истекло
        time.sleep(1.1)
        found, url = cache.get("123456")
        assert found is False
        assert url is None

    def test_cache_size(self):
        """Тест: размер кеша."""
        cache = VideoCache()

        assert cache.size() == 0

        cache.set("123456", "url1")
        assert cache.size() == 1

        cache.set("789012", "url2")
        assert cache.size() == 2

        cache.set("123456", "url1_updated")  # Перезапись
        assert cache.size() == 2

    def test_clear_expired(self):
        """Тест: очистка истекших записей."""
        cache = VideoCache(ttl_seconds=1)

        cache.set("123456", "url1")
        cache.set("789012", "url2")

        assert cache.size() == 2

        # Ждем истечения
        time.sleep(1.1)

        # Добавляем свежую запись
        cache.set("345678", "url3")

        # Очистка истекших
        cache.clear_expired()

        # Осталась только свежая
        assert cache.size() == 1
        found, _ = cache.get("345678")
        assert found is True
