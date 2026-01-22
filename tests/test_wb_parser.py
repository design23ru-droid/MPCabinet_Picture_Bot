"""Тесты для services/wb_parser.py"""

import pytest
from aioresponses import aioresponses
from services.wb_parser import WBParser, ProductMedia
from utils.exceptions import ProductNotFoundError, WBAPIError, NoMediaError


class TestWBParser:
    """Тесты для WBParser."""

    @pytest.mark.asyncio
    async def test_get_product_media_photos_and_video(self, mock_aiohttp):
        """Тест: получение товара с фото и видео."""
        nm_id = "12345678"
        vol = 123
        part = 12345
        video_part = 1234  # nm_id // 10000 для видео

        # Мокируем basket (найден с первой попытки - basket 01)
        mock_aiohttp.head(
            f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
            status=200
        )

        # Мокируем фото (3 фото, затем 404)
        for i in range(1, 4):
            mock_aiohttp.head(
                f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/{i}.webp",
                status=200
            )
        mock_aiohttp.head(
            f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/4.webp",
            status=404
        )

        # Мокируем HLS видео (найдено на basket 01, vol 1)
        mock_aiohttp.head(
            f"https://videonme-basket-01.wbbasket.ru/vol1/part{video_part}/{nm_id}/hls/1440p/index.m3u8",
            status=200
        )

        async with WBParser() as parser:
            media = await parser.get_product_media(nm_id)

        assert media.nm_id == nm_id
        assert len(media.photos) == 3
        assert media.has_photos()
        assert media.has_video()
        assert media.video == f"https://videonme-basket-01.wbbasket.ru/vol1/part{video_part}/{nm_id}/hls/1440p/index.m3u8"

    @pytest.mark.asyncio
    async def test_get_product_media_photos_only(self, mock_aiohttp):
        """Тест: получение товара только с фото (без видео)."""
        nm_id = "87654321"
        vol = 876
        part = 87654

        # Мокируем basket
        mock_aiohttp.head(
            f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
            status=200
        )

        # Мокируем 2 фото
        for i in range(1, 3):
            mock_aiohttp.head(
                f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/{i}.webp",
                status=200
            )
        mock_aiohttp.head(
            f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/3.webp",
            status=404
        )

        # Видео НЕ найдено
        mock_aiohttp.head(
            f"https://video.wildberries.ru/{nm_id}/{nm_id}.mp4",
            status=404
        )
        # HLS видео тоже не найдено (проверяем несколько вариантов)
        for basket in range(1, 21):
            for vol_variant in range(vol, vol + 5):
                mock_aiohttp.head(
                    f"https://videonme-basket-{basket:02d}.wbbasket.ru/vol{vol_variant}/part{part}/{nm_id}/hls/1440p/index.m3u8",
                    status=404
                )

        async with WBParser() as parser:
            media = await parser.get_product_media(nm_id)

        assert media.nm_id == nm_id
        assert len(media.photos) == 2
        assert media.has_photos()
        assert not media.has_video()
        assert media.video is None

    @pytest.mark.asyncio
    async def test_get_product_media_not_found_basket(self, mock_aiohttp):
        """Тест: товар не найден (basket не найден, только фото запрошены)."""
        nm_id = "99999999"
        vol = 999
        part = 99999

        # Мокируем все basket как 404 (товар не существует)
        for basket in range(1, 101):
            mock_aiohttp.head(
                f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
                status=404
            )

        async with WBParser() as parser:
            with pytest.raises(ProductNotFoundError, match="не найден"):
                await parser.get_product_media(nm_id, skip_video=True)

    @pytest.mark.asyncio
    async def test_get_product_media_no_media(self, mock_aiohttp):
        """Тест: товар найден, но нет ни фото, ни видео."""
        nm_id = "11111111"
        vol = 111
        part = 11111

        # Basket найден
        mock_aiohttp.head(
            f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
            status=200
        )

        # Но фото НЕТ (все 404)
        for i in range(1, 21):
            mock_aiohttp.head(
                f"https://basket-01.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/{i}.webp",
                status=404
            )

        # Видео тоже НЕТ
        mock_aiohttp.head(
            f"https://video.wildberries.ru/{nm_id}/{nm_id}.mp4",
            status=404
        )
        # HLS видео тоже нет
        for basket in range(1, 21):
            for vol_variant in range(vol, vol + 5):
                mock_aiohttp.head(
                    f"https://videonme-basket-{basket:02d}.wbbasket.ru/vol{vol_variant}/part{part}/{nm_id}/hls/1440p/index.m3u8",
                    status=404
                )

        async with WBParser() as parser:
            with pytest.raises(NoMediaError, match="нет медиа"):
                await parser.get_product_media(nm_id)

    @pytest.mark.asyncio
    async def test_get_product_media_invalid_article(self):
        """Тест: невалидный формат артикула."""
        async with WBParser() as parser:
            with pytest.raises(WBAPIError, match="Invalid article format"):
                await parser.get_product_media("invalid_id")

    @pytest.mark.asyncio
    async def test_find_basket_cache_hit(self, mock_aiohttp):
        """Тест: cache hit - basket взят из кеша."""
        nm_id = "22222222"
        vol = 222
        part = 22222

        # Первый вызов: находим basket 05
        mock_aiohttp.head(
            f"https://basket-05.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
            status=200,
            repeat=True  # Повторяющийся мок для кеш-проверки
        )

        # Мокируем 404 для basket 1-4
        for basket in range(1, 5):
            mock_aiohttp.head(
                f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
                status=404
            )

        async with WBParser() as parser:
            # Первый вызов - заполняем кеш
            basket1 = await parser._find_basket(nm_id, vol, part)
            assert basket1 == 5

            # Второй вызов - должен взять из кеша (без новых HTTP запросов)
            basket2 = await parser._find_basket(nm_id, vol, part)
            assert basket2 == 5

    @pytest.mark.asyncio
    async def test_find_basket_cache_miss(self, mock_aiohttp):
        """Тест: cache miss - кешированный basket устарел."""
        nm_id = "33333333"
        vol = 333
        part = 33333

        # Сначала добавляем в кеш basket 10
        async with WBParser() as parser:
            parser._basket_cache[vol] = 10

            # Мокируем что basket 10 теперь не работает
            mock_aiohttp.head(
                f"https://basket-10.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
                status=404
            )

            # Новый рабочий basket - 15
            for basket in range(1, 15):
                mock_aiohttp.head(
                    f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
                    status=404
                )
            mock_aiohttp.head(
                f"https://basket-15.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/1.webp",
                status=200
            )

            basket = await parser._find_basket(nm_id, vol, part)
            assert basket == 15
            assert parser._basket_cache[vol] == 15  # Кеш обновлен

    @pytest.mark.asyncio
    async def test_find_photos_multiple(self, mock_aiohttp):
        """Тест: нахождение нескольких фото."""
        nm_id = "44444444"
        vol = 444
        part = 44444
        basket = 1

        # Мокируем 5 фото
        for i in range(1, 6):
            mock_aiohttp.head(
                f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/{i}.webp",
                status=200
            )
        # 6-е фото не найдено
        mock_aiohttp.head(
            f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/6.webp",
            status=404
        )

        async with WBParser() as parser:
            photos = await parser._find_photos(nm_id, vol, part, basket)

        assert len(photos) == 5
        for i, photo_url in enumerate(photos, start=1):
            assert f"/images/big/{i}.webp" in photo_url

    @pytest.mark.asyncio
    async def test_find_photos_none(self, mock_aiohttp):
        """Тест: фото не найдены."""
        nm_id = "55555555"
        vol = 555
        part = 55555
        basket = 1

        # Все фото - 404
        for i in range(1, 21):
            mock_aiohttp.head(
                f"https://basket-{basket:02d}.wbbasket.ru/vol{vol}/part{part}/{nm_id}/images/big/{i}.webp",
                status=404
            )

        async with WBParser() as parser:
            photos = await parser._find_photos(nm_id, vol, part, basket)

        assert len(photos) == 0

    @pytest.mark.asyncio
    async def test_product_media_dataclass(self):
        """Тест: ProductMedia dataclass методы."""
        # С фото и видео
        media1 = ProductMedia(
            nm_id="123",
            name="Test",
            photos=["url1.webp", "url2.webp"],
            video="video.mp4"
        )
        assert media1.has_photos() is True
        assert media1.has_video() is True

        # Только фото
        media2 = ProductMedia(nm_id="456", name="Test", photos=["url1.webp"], video=None)
        assert media2.has_photos() is True
        assert media2.has_video() is False

        # Только видео
        media3 = ProductMedia(nm_id="789", name="Test", photos=[], video="video.mp4")
        assert media3.has_photos() is False
        assert media3.has_video() is True

        # Нет медиа
        media4 = ProductMedia(nm_id="000", name="Test", photos=[], video=None)
        assert media4.has_photos() is False
        assert media4.has_video() is False
