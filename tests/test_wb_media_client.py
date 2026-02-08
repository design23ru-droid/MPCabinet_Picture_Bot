"""Тесты для services/wb_media_client.py — адаптер к wb-media-service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import httpx

from services.wb_parser import ProductMedia


class TestWbMediaClientViaService:
    """Тесты: USE_WB_MEDIA_SERVICE=True — вызов микросервиса."""

    @pytest.mark.asyncio
    async def test_get_product_media_via_service(self):
        """Тест: получение медиа через wb-media-service (happy path)."""
        mock_response = httpx.Response(
            status_code=200,
            json={
                "nm_id": 12345678,
                "photos": [
                    "https://basket-01.wbbasket.ru/vol123/part12345/12345678/images/big/1.webp",
                    "https://basket-01.wbbasket.ru/vol123/part12345/12345678/images/big/2.webp",
                ],
                "video_url": "https://videonme-basket-15.wbbasket.ru/vol10/part1234/12345678/hls/1440p/index.m3u8",
                "photo_count": 2,
                "has_video": True,
                "basket": 1,
                "from_cache": False,
            },
            request=httpx.Request("GET", "http://test/api/wb/media/12345678"),
        )

        mock_settings = MagicMock()
        mock_settings.USE_WB_MEDIA_SERVICE = True
        mock_settings.WB_MEDIA_SERVICE_URL = "http://wb-media-service:8013"
        mock_settings.WB_MEDIA_SERVICE_TIMEOUT = 40

        with patch("services.wb_media_client.get_settings", return_value=mock_settings), \
             patch("services.wb_media_client.httpx.AsyncClient") as MockClient:

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            media = await client.get_product_media("12345678", skip_video=False)

        assert isinstance(media, ProductMedia)
        assert media.nm_id == "12345678"
        assert media.name == "Товар 12345678"
        assert len(media.photos) == 2
        assert media.video is not None
        assert "index.m3u8" in media.video

    @pytest.mark.asyncio
    async def test_skip_video_maps_to_include_video_false(self):
        """Тест: skip_video=True передаётся как include_video=false в query params."""
        mock_response = httpx.Response(
            status_code=200,
            json={
                "nm_id": 12345678,
                "photos": ["https://basket-01.wbbasket.ru/photo1.webp"],
                "video_url": None,
                "photo_count": 1,
                "has_video": False,
                "basket": 1,
                "from_cache": False,
            },
            request=httpx.Request("GET", "http://test/api/wb/media/12345678"),
        )

        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            await client.get_product_media("12345678", skip_video=True)

            # Проверяем что include_video=false передан
            call_args = mock_client.get.call_args
            params = call_args[1].get("params", {})
            assert params.get("include_video") is False

    @pytest.mark.asyncio
    async def test_skip_photos_ignores_photos_from_response(self):
        """Тест: skip_photos=True — photos пустой список, даже если сервис вернул фото."""
        mock_response = httpx.Response(
            status_code=200,
            json={
                "nm_id": 12345678,
                "photos": [
                    "https://basket-01.wbbasket.ru/photo1.webp",
                    "https://basket-01.wbbasket.ru/photo2.webp",
                ],
                "video_url": "https://videonme-basket-15.wbbasket.ru/hls/index.m3u8",
                "photo_count": 2,
                "has_video": True,
                "basket": 1,
                "from_cache": False,
            },
            request=httpx.Request("GET", "http://test/api/wb/media/12345678"),
        )

        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            media = await client.get_product_media("12345678", skip_photos=True)

        assert media.photos == []
        assert media.video is not None

    @pytest.mark.asyncio
    async def test_mapping_response_to_product_media(self):
        """Тест: корректный маппинг полей ответа сервиса на ProductMedia."""
        mock_response = httpx.Response(
            status_code=200,
            json={
                "nm_id": 99887766,
                "photos": ["https://basket-05.wbbasket.ru/photo1.webp"],
                "video_url": "https://videonme-basket-05.wbbasket.ru/hls/index.m3u8",
                "photo_count": 1,
                "has_video": True,
                "basket": 5,
                "from_cache": True,
            },
            request=httpx.Request("GET", "http://test/api/wb/media/99887766"),
        )

        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            media = await client.get_product_media("99887766")

        # nm_id: int → str
        assert media.nm_id == "99887766"
        # name: хардкод
        assert media.name == "Товар 99887766"
        # photos: прямой маппинг
        assert media.photos == ["https://basket-05.wbbasket.ru/photo1.webp"]
        # video: video_url → video
        assert media.video == "https://videonme-basket-05.wbbasket.ru/hls/index.m3u8"

    @pytest.mark.asyncio
    async def test_search_video_via_service(self):
        """Тест: поиск видео через wb-media-service."""
        mock_response = httpx.Response(
            status_code=200,
            json={
                "nm_id": 12345678,
                "photos": [],
                "video_url": "https://videonme-basket-15.wbbasket.ru/hls/index.m3u8",
                "photo_count": 0,
                "has_video": True,
                "basket": 15,
                "from_cache": False,
            },
            request=httpx.Request("GET", "http://test/api/wb/media/12345678"),
        )

        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            video_url = await client.search_video("12345678")

        assert video_url == "https://videonme-basket-15.wbbasket.ru/hls/index.m3u8"


class TestWbMediaClientFallback:
    """Тесты: fallback на WBParser при ошибке сервиса."""

    @pytest.mark.asyncio
    async def test_get_product_media_fallback_on_timeout(self, product_media):
        """Тест: при timeout сервиса — fallback на WBParser."""
        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient, \
             patch("services.wb_media_client.WBParser") as MockParser:

            # Сервис отвечает timeout
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            # WBParser (fallback)
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            media = await client.get_product_media("12345678")

        assert isinstance(media, ProductMedia)
        assert media.nm_id == "12345678"
        # WBParser должен быть вызван
        mock_parser.get_product_media.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product_media_no_fallback_on_404(self):
        """Тест: при 404 от сервиса — ProductNotFoundError, НЕ fallback."""
        mock_response = httpx.Response(
            status_code=404,
            json={"detail": "Product not found"},
            request=httpx.Request("GET", "http://test/api/wb/media/99999999"),
        )

        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from services.wb_media_client import WbMediaClient
            from utils.exceptions import ProductNotFoundError
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            with pytest.raises(ProductNotFoundError):
                await client.get_product_media("99999999")

    @pytest.mark.asyncio
    async def test_get_product_media_no_fallback_on_422(self):
        """Тест: при 422 от сервиса — InvalidArticleError, НЕ fallback."""
        mock_response = httpx.Response(
            status_code=422,
            json={"detail": "Invalid nm_id"},
            request=httpx.Request("GET", "http://test/api/wb/media/abc"),
        )

        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from services.wb_media_client import WbMediaClient
            from utils.exceptions import InvalidArticleError
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            with pytest.raises(InvalidArticleError):
                await client.get_product_media("abc")

    @pytest.mark.asyncio
    async def test_search_video_fallback_on_error(self, product_media):
        """Тест: при ошибке сервиса search_video — fallback на WBParser._check_video."""
        with patch("services.wb_media_client.httpx.AsyncClient") as MockClient, \
             patch("services.wb_media_client.WBParser") as MockParser:

            # Сервис отвечает ошибкой
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            # WBParser fallback
            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser._check_video = AsyncMock(return_value="https://video.url/hls/index.m3u8")
            MockParser.return_value = mock_parser

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = True
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            video_url = await client.search_video("12345678")

        assert video_url == "https://video.url/hls/index.m3u8"
        mock_parser._check_video.assert_called_once()


class TestWbMediaClientLocalMode:
    """Тесты: USE_WB_MEDIA_SERVICE=False — локальный WBParser."""

    @pytest.mark.asyncio
    async def test_get_product_media_local_when_flag_off(self, product_media):
        """Тест: USE_WB_MEDIA_SERVICE=False — используется WBParser напрямую."""
        with patch("services.wb_media_client.WBParser") as MockParser, \
             patch("services.wb_media_client.httpx.AsyncClient") as MockClient:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser.get_product_media = AsyncMock(return_value=product_media)
            MockParser.return_value = mock_parser

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = False
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            media = await client.get_product_media("12345678")

        assert isinstance(media, ProductMedia)
        # httpx НЕ должен вызываться
        MockClient.assert_not_called()
        # WBParser должен быть вызван
        mock_parser.get_product_media.assert_called_once_with(
            "12345678", skip_video=False, skip_photos=False
        )

    @pytest.mark.asyncio
    async def test_search_video_local_when_flag_off(self):
        """Тест: USE_WB_MEDIA_SERVICE=False — search_video через WBParser._check_video."""
        with patch("services.wb_media_client.WBParser") as MockParser, \
             patch("services.wb_media_client.httpx.AsyncClient") as MockClient:

            mock_parser = AsyncMock()
            mock_parser.__aenter__.return_value = mock_parser
            mock_parser.__aexit__.return_value = None
            mock_parser._check_video = AsyncMock(
                return_value="https://videonme-basket-01.wbbasket.ru/hls/index.m3u8"
            )
            MockParser.return_value = mock_parser

            from services.wb_media_client import WbMediaClient
            client = WbMediaClient.__new__(WbMediaClient)
            client.use_service = False
            client.service_url = "http://wb-media-service:8013"
            client.timeout = 40

            video_url = await client.search_video("12345678")

        assert video_url == "https://videonme-basket-01.wbbasket.ru/hls/index.m3u8"
        MockClient.assert_not_called()
        mock_parser._check_video.assert_called_once()


class TestGetWbMediaClient:
    """Тесты: singleton get_wb_media_client()."""

    def test_singleton_returns_same_instance(self):
        """Тест: get_wb_media_client() возвращает один и тот же экземпляр."""
        mock_settings = MagicMock()
        mock_settings.USE_WB_MEDIA_SERVICE = False
        mock_settings.WB_MEDIA_SERVICE_URL = "http://wb-media-service:8013"
        mock_settings.WB_MEDIA_SERVICE_TIMEOUT = 40

        with patch("services.wb_media_client.get_settings", return_value=mock_settings):
            import services.wb_media_client as mod
            # Сбросить singleton
            mod._wb_media_client = None

            client1 = mod.get_wb_media_client()
            client2 = mod.get_wb_media_client()

            assert client1 is client2

            # Очистка
            mod._wb_media_client = None