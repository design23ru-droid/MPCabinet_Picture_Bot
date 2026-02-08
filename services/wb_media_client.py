"""
WbMediaClient — адаптер для интеграции с wb-media-service (8013).

Feature Flag: USE_WB_MEDIA_SERVICE
- True: вызовы через HTTP к wb-media-service
- False: локальный WBParser (текущая логика)

При ошибке сервиса автоматический fallback на WBParser.
"""

import logging
from typing import Optional, Callable, Awaitable

import httpx

from config.settings import get_settings
from services.wb_parser import WBParser, ProductMedia
from utils.exceptions import ProductNotFoundError, InvalidArticleError

logger = logging.getLogger(__name__)


class WbMediaClient:
    """
    Адаптер для работы с wb-media-service или локальным WBParser.

    Feature Flag USE_WB_MEDIA_SERVICE:
    - True: HTTP GET к wb-media-service → маппинг → ProductMedia
    - False: WBParser напрямую (текущее поведение)

    При ошибке сервиса — автоматический fallback на WBParser.
    """

    def __init__(self):
        settings = get_settings()
        self.use_service = settings.USE_WB_MEDIA_SERVICE
        self.service_url = settings.WB_MEDIA_SERVICE_URL
        self.timeout = settings.WB_MEDIA_SERVICE_TIMEOUT

        logger.info(
            f"WbMediaClient инициализирован: USE_WB_MEDIA_SERVICE={self.use_service}, "
            f"URL={self.service_url if self.use_service else 'N/A'}"
        )

    async def get_product_media(
        self,
        nm_id: str,
        skip_video: bool = False,
        skip_photos: bool = False,
    ) -> ProductMedia:
        """
        Получить медиа товара по артикулу.

        Args:
            nm_id: Артикул товара
            skip_video: Пропустить поиск видео
            skip_photos: Пропустить поиск фото (только видео)

        Returns:
            ProductMedia с URLs фото и видео

        Raises:
            ProductNotFoundError: Товар не найден (404)
            InvalidArticleError: Неверный формат артикула (422)
        """
        if self.use_service:
            try:
                return await self._get_via_service(nm_id, skip_video, skip_photos)
            except (ProductNotFoundError, InvalidArticleError):
                raise
            except Exception as e:
                logger.warning(
                    f"wb-media-service ошибка для {nm_id}: {e}. Fallback на WBParser."
                )
                return await self._get_via_parser(nm_id, skip_video, skip_photos)
        else:
            return await self._get_via_parser(nm_id, skip_video, skip_photos)

    async def search_video(
        self,
        nm_id: str,
        progress_callback: Optional[Callable[[int], Awaitable[None]]] = None,
    ) -> Optional[str]:
        """
        Поиск видео товара.

        Args:
            nm_id: Артикул товара
            progress_callback: Callback для обновления прогресса (только для WBParser)

        Returns:
            URL видео или None
        """
        if self.use_service:
            try:
                return await self._search_video_via_service(nm_id)
            except Exception as e:
                logger.warning(
                    f"wb-media-service video search ошибка для {nm_id}: {e}. "
                    f"Fallback на WBParser."
                )
                return await self._search_video_via_parser(nm_id, progress_callback)
        else:
            return await self._search_video_via_parser(nm_id, progress_callback)

    async def _get_via_service(
        self, nm_id: str, skip_video: bool, skip_photos: bool
    ) -> ProductMedia:
        """Получение медиа через wb-media-service."""
        params = {
            "include_video": not skip_video,
        }

        url = f"{self.service_url}/api/wb/media/{nm_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)

        if response.status_code == 404:
            raise ProductNotFoundError(f"Товар {nm_id} не найден")
        if response.status_code == 422:
            raise InvalidArticleError(f"Неверный артикул: {nm_id}")

        response.raise_for_status()

        data = response.json()

        photos = [] if skip_photos else data.get("photos", [])
        video_url = data.get("video_url")

        logger.info(
            f"wb-media-service ответ для {nm_id}: "
            f"photos={len(photos)}, video={bool(video_url)}, "
            f"from_cache={data.get('from_cache', False)}"
        )

        return ProductMedia(
            nm_id=str(data["nm_id"]),
            name=f"Товар {nm_id}",
            photos=photos,
            video=video_url,
        )

    async def _get_via_parser(
        self, nm_id: str, skip_video: bool, skip_photos: bool
    ) -> ProductMedia:
        """Получение медиа через локальный WBParser."""
        async with WBParser() as parser:
            return await parser.get_product_media(
                nm_id, skip_video=skip_video, skip_photos=skip_photos
            )

    async def _search_video_via_service(self, nm_id: str) -> Optional[str]:
        """Поиск видео через wb-media-service."""
        params = {"include_video": True}
        url = f"{self.service_url}/api/wb/media/{nm_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)

        if response.status_code in (404, 422):
            return None

        response.raise_for_status()

        data = response.json()
        video_url = data.get("video_url")

        logger.info(
            f"wb-media-service video search для {nm_id}: "
            f"video={bool(video_url)}"
        )

        return video_url

    async def _search_video_via_parser(
        self,
        nm_id: str,
        progress_callback: Optional[Callable[[int], Awaitable[None]]] = None,
    ) -> Optional[str]:
        """Поиск видео через локальный WBParser."""
        async with WBParser() as parser:
            return await parser._check_video(nm_id, progress_callback)


# Singleton instance
_wb_media_client: Optional[WbMediaClient] = None


def get_wb_media_client() -> WbMediaClient:
    """Получить singleton экземпляр WbMediaClient."""
    global _wb_media_client
    if _wb_media_client is None:
        _wb_media_client = WbMediaClient()
    return _wb_media_client