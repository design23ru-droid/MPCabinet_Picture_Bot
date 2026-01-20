"""Парсер медиа Wildberries через прямые basket URL."""

import asyncio
import aiohttp
import socket
from typing import List, Optional, Callable, Awaitable
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
    MAX_BASKET = 100   # Максимальный номер basket для проверки

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
    async def get_product_media(
        self,
        nm_id: str,
        skip_video: bool = False,
        skip_photos: bool = False
    ) -> ProductMedia:
        """
        Получить медиа товара по артикулу.

        Args:
            nm_id: Артикул товара
            skip_video: Пропустить поиск видео (ускоряет запрос)
            skip_photos: Пропустить поиск фото (только видео)

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

            # 1. Найти фото (если не skip_photos)
            photos = []
            if not skip_photos:
                # Найти рабочий basket для фото
                basket_start = time.perf_counter()
                working_basket = await self._find_basket(nm_id, vol, part)
                basket_elapsed = time.perf_counter() - basket_start

                if not working_basket:
                    logger.error(f"❌ Product {nm_id}: basket NOT FOUND ({basket_elapsed:.2f}s)")
                    # Если нужны только фото и basket не найден — ошибка
                    if skip_video:
                        raise ProductNotFoundError(f"Товар {nm_id} не найден")
                else:
                    logger.info(
                        f"✅ Product {nm_id}: basket={working_basket:02d} найден за {basket_elapsed:.2f}s"
                    )
                    photos_start = time.perf_counter()
                    photos = await self._find_photos(nm_id, vol, part, working_basket)
                    photos_elapsed = time.perf_counter() - photos_start
                    logger.info(f"📷 Product {nm_id}: найдено {len(photos)} фото за {photos_elapsed:.2f}s")

            # 3. Найти видео (если не skip_video)
            video = None
            if not skip_video:
                # Проверка кеша
                from services.video_cache import get_video_cache
                cache = get_video_cache()
                found_in_cache, cached_video = cache.get(nm_id)

                if found_in_cache:
                    # В кеше (может быть None если видео нет)
                    video = cached_video
                    status = "есть" if video else "НЕТ"
                    logger.info(f"🎥 Product {nm_id}: видео из КЕША ({status})")
                else:
                    # Нет в кеше - ищем
                    video_start = time.perf_counter()
                    video = await self._check_video(nm_id)
                    video_elapsed = time.perf_counter() - video_start

                    # Сохранить в кеш (даже если None - чтобы не искать повторно)
                    cache.set(nm_id, video)

                    if video:
                        logger.info(f"🎥 Product {nm_id}: видео найдено за {video_elapsed:.2f}s")
                    else:
                        logger.info(f"🎥 Product {nm_id}: видео НЕ найдено ({video_elapsed:.2f}s)")

            # Проверка что нашли хоть что-то
            if not photos and not video:
                raise NoMediaError(f"У товара {nm_id} нет медиа")

            return ProductMedia(
                nm_id=nm_id,
                name=f"Товар {nm_id}",
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
        Найти рабочий basket параллельной проверкой всех 100.

        Стратегия:
        1. Проверить кеш vol → basket
        2. Все 100 basket параллельно (1-2 сек)

        Args:
            nm_id: Артикул
            vol: Volume
            part: Part

        Returns:
            Номер basket или None если не найден
        """
        # Проверка кеша
        if vol in self._basket_cache:
            cached_basket = self._basket_cache[vol]
            if await self._check_single_basket(nm_id, vol, part, cached_basket):
                logger.info(f"✅ Product {nm_id}: cache HIT basket={cached_basket}")
                return cached_basket

        # Все 100 basket параллельно
        logger.debug(f"🔍 Product {nm_id}: проверка всех {self.MAX_BASKET} basket параллельно")

        all_baskets = list(range(1, self.MAX_BASKET + 1))
        basket = await self._check_basket_batch(nm_id, vol, part, all_baskets)

        if basket:
            self._basket_cache[vol] = basket
            logger.info(f"✅ Product {nm_id}: basket={basket:02d} найден, сохранен в кеш")
            return basket

        logger.error(f"❌ Product {nm_id} NOT FOUND in any basket (1-{self.MAX_BASKET})")
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

    async def _find_video_hls(
        self,
        nm_id: str,
        progress_callback: Optional[Callable[[int], Awaitable[None]]] = None
    ) -> Optional[str]:
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
            progress_callback: Callback для обновления прогресса (0-100%)

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

        batch_times = []  # Время обработки батчей для анализа
        last_progress_update = start_time  # Для дебаунсинга обновлений прогресса

        for i in range(0, len(all_combinations), BATCH_SIZE):
            # Timeout check
            elapsed = time.time() - start_time
            if elapsed > 30:
                avg_time = sum(batch_times) / len(batch_times) if batch_times else 0
                logger.warning(
                    f"⏱️  Video search TIMEOUT для {nm_id} после {elapsed:.1f}s, "
                    f"остановлен на batch {batch_num}/{total_batches}, "
                    f"avg batch time: {avg_time:.3f}s"
                )
                return None

            batch = all_combinations[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            batch_start = time.time()

            # Обновление прогресса (каждые 10% с дебаунсингом 2 сек)
            progress = int((batch_num / total_batches) * 100)
            time_since_last_update = time.time() - last_progress_update

            # Обновляем если прошло 2+ секунды ИЛИ каждые 10%
            should_update = (
                progress_callback is not None and
                (time_since_last_update >= 2.0 or progress % 10 == 0)
            )

            if should_update:
                try:
                    await progress_callback(progress)
                    last_progress_update = time.time()
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

            result = await self._check_video_batch(nm_id, part, batch)

            batch_time = time.time() - batch_start
            batch_times.append(batch_time)

            # Логирование каждые 10 батчей
            if batch_num % 10 == 0:
                avg_time = sum(batch_times[-10:]) / 10
                logger.info(
                    f"🔄 Video {nm_id}: batch {batch_num}/{total_batches}, "
                    f"elapsed={elapsed:.1f}s, last 10 avg={avg_time:.3f}s/batch"
                )

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

    async def _check_video(
        self,
        nm_id: str,
        progress_callback: Optional[Callable[[int], Awaitable[None]]] = None
    ) -> Optional[str]:
        """
        Проверить наличие видео (HLS формат).

        Args:
            nm_id: Артикул
            progress_callback: Callback для обновления прогресса (0-100%)

        Returns:
            URL видео или None
        """
        # HLS формат — единственный рабочий способ
        hls_url = await self._find_video_hls(nm_id, progress_callback)

        if hls_url:
            return hls_url

        logger.info(f"❌ No video found for {nm_id}")
        return None
