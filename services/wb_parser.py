"""Парсер медиа Wildberries через прямые basket URL."""

import asyncio
import aiohttp
import socket
from typing import List, Optional
from dataclasses import dataclass
import logging
import time

from utils.exceptions import ProductNotFoundError, WBAPIError, NoMediaError
from config.settings import Settings
from utils.decorators import log_execution_time

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
        # Ограничиваем количество одновременных соединений для предотвращения перегрузки
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        logger.debug(
            f"📡 HTTP сессия создана: timeout={self.settings.WB_API_TIMEOUT}s, "
            f"limit=100, limit_per_host=50"
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие HTTP сессии."""
        if self.session:
            await self.session.close()
            logger.debug("📡 HTTP сессия закрыта")

    @log_execution_time()
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

            logger.info(
                f"🔍 Product {nm_id}: vol={vol}, part={part}, "
                f"nmId_int={nm_id_int}"
            )

            # 1. Найти рабочий basket (безлимитный поиск с timeout)
            basket_start = time.perf_counter()
            working_basket = await self._find_basket(nm_id, vol, part)
            basket_elapsed = time.perf_counter() - basket_start

            if not working_basket:
                logger.error(
                    f"❌ Product {nm_id}: basket NOT FOUND после {basket_elapsed:.2f}s"
                )
                raise ProductNotFoundError(
                    f"Товар {nm_id} не найден (timeout {self.BASKET_SEARCH_TIMEOUT}s)"
                )

            logger.info(
                f"✅ Product {nm_id}: basket={working_basket:02d} найден за {basket_elapsed:.2f}s"
            )

            # 2. Найти все фото
            photos_start = time.perf_counter()
            photos = await self._find_photos(nm_id, vol, part, working_basket)
            photos_elapsed = time.perf_counter() - photos_start

            logger.info(
                f"📷 Product {nm_id}: найдено {len(photos)} фото за {photos_elapsed:.2f}s"
            )

            # 3. Проверить видео
            video_start = time.perf_counter()
            video = await self._check_video(nm_id)
            video_elapsed = time.perf_counter() - video_start

            if video:
                logger.info(f"🎥 Product {nm_id}: видео найдено за {video_elapsed:.2f}s")
            else:
                logger.info(f"🎥 Product {nm_id}: видео НЕ найдено (поиск {video_elapsed:.2f}s)")

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
        Найти рабочий basket последовательным перебором с кешем.

        Стратегия:
        1. Проверить кеш vol → basket
        2. Последовательный перебор 1-100 батчами по 50

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
            logger.debug(f"🗂️  Product {nm_id}: проверка кеша basket={cached_basket} для vol={vol}")
            if await self._check_single_basket(nm_id, vol, part, cached_basket):
                logger.info(f"✅ Product {nm_id}: cache HIT - basket={cached_basket}")
                return cached_basket
            else:
                logger.debug(f"❌ Product {nm_id}: cache MISS - basket={cached_basket} не актуален")

        # Последовательный перебор 1-100 батчами
        logger.debug(f"🔍 Product {nm_id}: начинаем перебор basket 1-{self.MAX_BASKET} батчами по {self.BASKET_BATCH_SIZE}")

        for i in range(1, self.MAX_BASKET + 1, self.BASKET_BATCH_SIZE):
            # Проверка timeout
            elapsed = time.time() - start_time
            if elapsed > self.BASKET_SEARCH_TIMEOUT:
                logger.warning(
                    f"⏱️  Product {nm_id}: basket search TIMEOUT после {elapsed:.1f}s "
                    f"(проверено до basket {i-1}, vol={vol}, part={part})"
                )
                return None

            # Формируем батч
            batch = list(range(i, min(i + self.BASKET_BATCH_SIZE, self.MAX_BASKET + 1)))
            logger.debug(f"🔄 Product {nm_id}: проверка batch {i}-{batch[-1]} ({len(batch)} baskets)")

            basket = await self._check_basket_batch(nm_id, vol, part, batch)

            if basket:
                self._basket_cache[vol] = basket  # Сохраняем в кеш
                logger.info(
                    f"✅ Product {nm_id}: basket={basket:02d} найден в batch {i}-{batch[-1]}, "
                    f"сохранен в кеш для vol={vol}"
                )
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
            request_start = time.perf_counter()
            async with self.session.head(test_url) as response:
                request_time = (time.perf_counter() - request_start) * 1000  # ms

                if response.status == 200:
                    logger.debug(
                        f"✅ HTTP HEAD {response.status} basket={basket:02d} {request_time:.0f}ms"
                    )
                    return True
                else:
                    logger.debug(
                        f"❌ HTTP HEAD {response.status} basket={basket:02d} {request_time:.0f}ms"
                    )
                    return False

        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror) as e:
            logger.debug(f"❌ HTTP HEAD ERROR basket={basket:02d} - {type(e).__name__}")
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

        logger.debug(f"📷 Product {nm_id}: начинаем поиск фото (макс {self.MAX_PHOTOS})")

        for photo_num in range(1, self.MAX_PHOTOS + 1):
            photo_url = f"{base_url}/{photo_num}.webp"

            try:
                await asyncio.sleep(self.settings.WB_RATE_LIMIT_DELAY / 20)  # Уменьшена задержка

                request_start = time.perf_counter()
                async with self.session.head(photo_url) as response:
                    request_time = (time.perf_counter() - request_start) * 1000  # ms

                    if response.status == 200:
                        photos.append(photo_url)
                        logger.debug(f"✅ Фото {photo_num}: найдено ({request_time:.0f}ms)")
                    else:
                        logger.debug(
                            f"❌ Фото {photo_num}: не найдено (HTTP {response.status}), "
                            f"останавливаем поиск"
                        )
                        # Если не нашли, дальше не проверяем
                        break

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.debug(f"❌ Фото {photo_num}: ошибка {type(e).__name__}, останавливаем поиск")
                break

        logger.info(f"📷 Product {nm_id}: найдено {len(photos)} фото из {self.MAX_PHOTOS} возможных")
        return photos

    async def _check_single_video(
        self, nm_id: str, part: int, basket: int, vol: int
    ) -> bool:
        """
        Проверить одну basket+vol комбинацию для HLS видео.

        Args:
            nm_id: Артикул
            part: Part (nmId // 10000)
            basket: Номер basket
            vol: Номер vol

        Returns:
            True если видео существует, False иначе
        """
        test_url = (
            f"https://videonme-basket-{basket:02d}.wbbasket.ru"
            f"/vol{vol}/part{part}/{nm_id}/hls/1440p/index.m3u8"
        )

        try:
            async with self.session.head(test_url) as response:
                return response.status == 200

        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror):
            return False

    async def _check_video_batch(
        self, nm_id: str, part: int, combinations: list[tuple[int, int]]
    ) -> Optional[tuple[int, int]]:
        """
        Проверить батч basket+vol комбинаций для видео.

        Args:
            nm_id: Артикул
            part: Part (nmId // 10000)
            combinations: Список (basket, vol) для проверки

        Returns:
            Первая найденная комбинация (basket, vol) или None
        """
        tasks = [
            self._check_single_video(nm_id, part, basket, vol)
            for basket, vol in combinations
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for (basket, vol), result in zip(combinations, results):
            if result is True:
                return (basket, vol)
            elif isinstance(result, Exception):
                # Ошибки игнорируем (DNS, timeout и т.д.)
                pass

        return None

    async def _find_video_hls(self, nm_id: str) -> Optional[str]:
        """
        Найти HLS видео товара через быстрый перебор basket+vol.

        Стратегия с приоритетом:
        1. Сначала vol 1-50 (горячая зона, 99% видео)
        2. Потом vol 51-200 (редкие случаи)
        - basket: 1-100
        - 50 батчей по 400 параллельных запросов
        - Timeout: 30 сек
        - Early exit при нахождении

        Args:
            nm_id: Артикул товара

        Returns:
            URL плейлиста index.m3u8 или None
        """
        start_time = time.time()

        nm_id_int = int(nm_id)
        part = nm_id_int // 10000  # Формула для видео

        # Приоритет 1: Горячая зона vol 1-50
        hot_combinations = [
            (basket, vol)
            for basket in range(1, 101)
            for vol in range(1, 51)
        ]

        # Приоритет 2: Расширенная зона vol 51-200
        extended_combinations = [
            (basket, vol)
            for basket in range(1, 101)
            for vol in range(51, 201)
        ]

        logger.info(
            f"🎥 Video HLS search for {nm_id}: part={part}, "
            f"проверка {len(hot_combinations) + len(extended_combinations)} комбинаций"
        )

        all_combinations = hot_combinations + extended_combinations

        # Батчи по 100 комбинаций (баланс скорости и стабильности)
        BATCH_SIZE = 100
        total_batches = len(all_combinations) // BATCH_SIZE

        logger.info(
            f"🎥 Video search {nm_id}: {len(all_combinations)} комбинаций, "
            f"{total_batches} батчей, timeout=30s"
        )

        for i in range(0, len(all_combinations), BATCH_SIZE):
            # Timeout check
            elapsed = time.time() - start_time
            if elapsed > 30:
                logger.warning(f"⏱️  Video search TIMEOUT для {nm_id} после {elapsed:.1f}s")
                return None

            batch = all_combinations[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            logger.debug(
                f"🔄 Video {nm_id}: batch {batch_num}/{total_batches} "
                f"(elapsed {elapsed:.1f}s)"
            )

            result = await self._check_video_batch(nm_id, part, batch)
            if result:
                basket, vol = result
                url = (
                    f"https://videonme-basket-{basket:02d}.wbbasket.ru"
                    f"/vol{vol}/part{part}/{nm_id}/hls/1440p/index.m3u8"
                )
                elapsed = time.time() - start_time
                logger.info(
                    f"Video found for {nm_id}: basket={basket:02d}, vol={vol}, "
                    f"batch {batch_num}/{total_batches}, time={elapsed:.1f}s"
                )
                return url

            # Задержка между батчами (уменьшена для скорости)
            await asyncio.sleep(0.01)  # 10ms

        elapsed = time.time() - start_time
        logger.info(
            f"❌ Video NOT FOUND для {nm_id} после полного поиска "
            f"({elapsed:.1f}s, проверено {len(all_combinations)} комбинаций)"
        )
        return None

    async def _check_video(self, nm_id: str) -> Optional[str]:
        """
        Проверить наличие видео (HLS формат).

        Сначала пробуем старый URL (для совместимости),
        затем ищем через HLS.

        Args:
            nm_id: Артикул

        Returns:
            URL видео или None
        """
        # Попытка 1: старый формат (может работать для старых товаров)
        old_video_url = f"https://video.wildberries.ru/{nm_id}/{nm_id}.mp4"

        logger.debug(f"🎥 Product {nm_id}: проверка legacy формата видео")
        try:
            request_start = time.perf_counter()
            async with self.session.head(old_video_url) as response:
                request_time = (time.perf_counter() - request_start) * 1000  # ms

                if response.status == 200:
                    logger.info(
                        f"✅ Video found (legacy MP4) for {nm_id} ({request_time:.0f}ms)"
                    )
                    return old_video_url
                else:
                    logger.debug(
                        f"❌ Legacy video HTTP {response.status} ({request_time:.0f}ms)"
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror) as e:
            logger.debug(f"❌ Legacy video error: {type(e).__name__}")

        # Попытка 2: HLS формат (новый)
        logger.debug(f"🎥 Product {nm_id}: переход к HLS формату")
        hls_url = await self._find_video_hls(nm_id)

        if hls_url:
            return hls_url

        logger.info(f"❌ No video found for {nm_id}")
        return None
