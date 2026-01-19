"""Парсер медиа Wildberries через прямые basket URL."""

import asyncio
import aiohttp
from typing import List, Optional
from dataclasses import dataclass
import logging
import time

from utils.exceptions import ProductNotFoundError, WBAPIError, NoMediaError
from config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class ProductMedia:
    """Медиафайлы товара."""

    nm_id: str
    name: str
    photos: List[str]  # URLs фотографий
    video: Optional[str]  # URL видео или None

    def has_photos(self) -> bool:
        """Есть ли фотографии."""
        return len(self.photos) > 0

    def has_video(self) -> bool:
        """Есть ли видео."""
        return self.video is not None


class WBParser:
    """Парсер медиа Wildberries через прямые basket URL."""

    MAX_PHOTOS = 20    # Максимальное количество фото для проверки
    BASKET_BATCH_SIZE = 50  # Размер батча для параллельной проверки basket
    BASKET_SEARCH_TIMEOUT = 90  # Максимум секунд на поиск basket
    MAX_BASKET = 100  # Максимальный номер basket для проверки

    # In-memory кеш vol → basket для ускорения повторных запросов
    _basket_cache: dict[int, int] = {}

    def __init__(self):
        self.settings = Settings()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Создание HTTP сессии."""
        timeout = aiohttp.ClientTimeout(
            total=self.settings.WB_API_TIMEOUT,
            connect=5,
            sock_read=5
        )
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие HTTP сессии."""
        if self.session:
            await self.session.close()

    async def get_product_media(self, nm_id: str) -> ProductMedia:
        """
        Получить медиа товара по артикулу.

        Алгоритм:
        1. Вычислить vol и part из nmID
        2. Перебрать basket до нахождения или timeout
        3. Перебрать номера фото (1,2,3...) пока не получим 404
        4. Проверить видео по URL video.wildberries.ru

        Args:
            nm_id: Артикул товара

        Returns:
            ProductMedia объект с URLs фото и видео

        Raises:
            ProductNotFoundError: Товар не найден (нет медиа)
            WBAPIError: Ошибка сети
        """
        if not self.session:
            raise RuntimeError("Parser not initialized. Use 'async with'.")

        logger.info(f"Fetching product {nm_id}")

        try:
            # Вычисляем vol и part
            nm_id_int = int(nm_id)
            vol = nm_id_int // 100000
            part = nm_id_int // 1000

            logger.debug(f"Product {nm_id}: vol={vol}, part={part}")

            # 1. Найти рабочий basket (безлимитный поиск с timeout)
            working_basket = await self._find_basket(nm_id, vol, part)

            if not working_basket:
                raise ProductNotFoundError(
                    f"Товар {nm_id} не найден (timeout {self.BASKET_SEARCH_TIMEOUT}s)"
                )

            logger.info(f"Product {nm_id}: found basket={working_basket:02d}")

            # 2. Найти все фото
            photos = await self._find_photos(nm_id, vol, part, working_basket)

            logger.info(f"Product {nm_id}: found {len(photos)} photos")

            # 3. Проверить видео
            video = await self._check_video(nm_id)

            if video:
                logger.info(f"Product {nm_id}: video found")
            else:
                logger.info(f"Product {nm_id}: no video")

            # Проверка что нашли хоть что-то
            if not photos and not video:
                raise NoMediaError(f"У товара {nm_id} нет фото и видео")

            return ProductMedia(
                nm_id=nm_id,
                name=f"Товар {nm_id}",  # Название недоступно без API
                photos=photos,
                video=video
            )

        except ValueError:
            raise WBAPIError(f"Invalid article format: {nm_id}")
        except ProductNotFoundError:
            raise
        except NoMediaError:
            raise
        except Exception as e:
            logger.error(f"Error fetching product {nm_id}: {e}")
            raise WBAPIError(f"Error fetching product: {e}")

    async def _find_basket(self, nm_id: str, vol: int, part: int) -> Optional[int]:
        """
        Найти рабочий basket с оптимизацией через кеш и приоритетную проверку.

        Стратегия:
        1. Проверить кеш vol → basket
        2. Приоритетно проверить "горячую зону" (basket 20-30) - большинство товаров
        3. Проверить оставшиеся диапазоны параллельными батчами

        Args:
            nm_id: Артикул
            vol: Volume
            part: Part

        Returns:
            Номер basket или None если не найден
        """
        start_time = time.time()

        # Проверка кеша
        if vol in self._basket_cache:
            cached_basket = self._basket_cache[vol]
            logger.debug(f"Product {nm_id}: checking cached basket {cached_basket} for vol {vol}")
            if await self._check_single_basket(nm_id, vol, part, cached_basket):
                logger.debug(f"Product {nm_id}: cache hit - basket {cached_basket}")
                return cached_basket

        # Приоритетная "горячая зона" (basket 20-30) - проверяем первой
        hot_zone = list(range(20, 31))
        logger.debug(f"Product {nm_id}: checking hot zone {hot_zone[0]}-{hot_zone[-1]}")

        basket = await self._check_basket_batch(nm_id, vol, part, hot_zone)
        if basket:
            self._basket_cache[vol] = basket  # Сохраняем в кеш
            logger.info(f"Product {nm_id}: found basket={basket:02d} in hot zone")
            return basket

        # Проверка остальных диапазонов (1-19, 31-100) батчами
        remaining_baskets = list(range(1, 20)) + list(range(31, self.MAX_BASKET + 1))

        # Разбиваем на батчи
        for i in range(0, len(remaining_baskets), self.BASKET_BATCH_SIZE):
            # Проверка timeout
            if time.time() - start_time > self.BASKET_SEARCH_TIMEOUT:
                logger.warning(
                    f"Product {nm_id}: basket search timeout after {self.BASKET_SEARCH_TIMEOUT}s "
                    f"(checked {i + len(hot_zone)} baskets, vol={vol}, part={part})"
                )
                return None

            batch = remaining_baskets[i:i + self.BASKET_BATCH_SIZE]
            basket = await self._check_basket_batch(nm_id, vol, part, batch)

            if basket:
                self._basket_cache[vol] = basket  # Сохраняем в кеш
                logger.info(f"Product {nm_id}: found basket={basket:02d}")
                return basket

            # Минимальная задержка между батчами
            await asyncio.sleep(0.05)

        # Товар не найден ни в одном basket
        logger.error(
            f"Product {nm_id} NOT FOUND in any basket (1-{self.MAX_BASKET}). "
            f"vol={vol}, part={part}. Требуется расследование!"
        )
        return None

    async def _check_basket_batch(
        self, nm_id: str, vol: int, part: int, baskets: list[int]
    ) -> Optional[int]:
        """
        Проверить батч basket параллельно.

        Args:
            nm_id: Артикул
            vol: Volume
            part: Part
            baskets: Список номеров basket для проверки

        Returns:
            Номер первого найденного basket или None
        """
        tasks = [self._check_single_basket(nm_id, vol, part, b) for b in baskets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for basket, result in zip(baskets, results):
            if result is True:
                return basket
            elif isinstance(result, Exception):
                logger.debug(f"Product {nm_id}: basket {basket} error - {result}")

        return None

    async def _check_single_basket(
        self, nm_id: str, vol: int, part: int, basket: int
    ) -> bool:
        """
        Проверить один basket.

        Args:
            nm_id: Артикул
            vol: Volume
            part: Part
            basket: Номер basket

        Returns:
            True если basket существует, False иначе
        """
        test_url = (
            f"https://basket-{basket:02d}.wbbasket.ru"
            f"/vol{vol}/part{part}/{nm_id}/images/big/1.webp"
        )

        try:
            async with self.session.head(test_url) as response:
                return response.status == 200

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def _find_photos(
        self, nm_id: str, vol: int, part: int, basket: int
    ) -> List[str]:
        """
        Найти все фото товара перебором номеров.

        Args:
            nm_id: Артикул
            vol: Volume
            part: Part
            basket: Номер basket

        Returns:
            Список URLs фотографий
        """
        photos = []
        base_url = (
            f"https://basket-{basket:02d}.wbbasket.ru"
            f"/vol{vol}/part{part}/{nm_id}/images/big"
        )

        for photo_num in range(1, self.MAX_PHOTOS + 1):
            photo_url = f"{base_url}/{photo_num}.webp"

            try:
                await asyncio.sleep(self.settings.WB_RATE_LIMIT_DELAY / 20)  # Уменьшена задержка

                async with self.session.head(photo_url) as response:
                    if response.status == 200:
                        photos.append(photo_url)
                    else:
                        # Если не нашли, дальше не проверяем
                        break

            except (aiohttp.ClientError, asyncio.TimeoutError):
                break

        return photos

    async def _check_video(self, nm_id: str) -> Optional[str]:
        """
        Проверить наличие видео.

        Args:
            nm_id: Артикул

        Returns:
            URL видео или None
        """
        video_url = f"https://video.wildberries.ru/{nm_id}/{nm_id}.mp4"

        try:
            await asyncio.sleep(self.settings.WB_RATE_LIMIT_DELAY / 10)  # Уменьшена задержка

            async with self.session.head(video_url) as response:
                if response.status == 200:
                    return video_url

        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass

        return None
