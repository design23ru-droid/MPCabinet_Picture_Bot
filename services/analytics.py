"""Сервис аналитики и сбора статистики."""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Optional

import asyncpg

from db.connection import get_pool

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Сервис для отслеживания событий и сбора статистики."""

    async def track_user_start(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str]
    ) -> bool:
        """
        Отследить запуск бота пользователем (/start).

        Создаёт запись в shared.users если пользователь новый,
        обновляет last_seen если пользователь уже существует.
        Создаёт событие 'user_start' в shared.analytics_events.

        Args:
            user_id: Telegram ID пользователя
            username: Username пользователя (без @)
            first_name: Имя пользователя
            last_name: Фамилия пользователя

        Returns:
            True если пользователь новый, False если повторный
            None при ошибке БД (graceful degradation)
        """
        pool = await get_pool()
        if pool is None:
            logger.warning("БД недоступна - track_user_start пропущен")
            return None

        try:
            async with pool.acquire() as conn:
                # Проверяем существование пользователя
                existing = await conn.fetchrow(
                    "SELECT telegram_id FROM shared.users WHERE telegram_id = $1",
                    user_id
                )

                is_new_user = existing is None

                if is_new_user:
                    # Новый пользователь - создаём запись
                    await conn.execute(
                        """
                        INSERT INTO shared.users (telegram_id, username, first_name, last_name)
                        VALUES ($1, $2, $3, $4)
                        """,
                        user_id, username, first_name, last_name
                    )
                    logger.info(
                        f"✅ Новый пользователь добавлен в БД: "
                        f"id={user_id}, @{username or 'no_username'}"
                    )
                else:
                    # Повторный пользователь - обновляем last_seen и данные
                    await conn.execute(
                        """
                        UPDATE shared.users
                        SET last_seen = NOW(),
                            username = $2,
                            first_name = $3,
                            last_name = $4
                        WHERE telegram_id = $1
                        """,
                        user_id, username, first_name, last_name
                    )
                    logger.debug(f"Обновлен last_seen для user {user_id}")

                # Создаём событие user_start
                await conn.execute(
                    """
                    INSERT INTO shared.analytics_events (telegram_id, event_type, event_data)
                    VALUES ($1, 'user_start', $2::jsonb)
                    """,
                    user_id,
                    f'{{"is_new": {str(is_new_user).lower()}}}'
                )

                return is_new_user

        except Exception as e:
            logger.warning(
                f"⚠️  Ошибка при track_user_start для user {user_id}: "
                f"{type(e).__name__}: {e}"
            )
            return None

    async def track_article_request(self, user_id: int, nm_id: int) -> None:
        """
        Отследить запрос артикула пользователем.

        Args:
            user_id: Telegram ID пользователя
            nm_id: Артикул WB (nmId)
        """
        pool = await get_pool()
        if pool is None:
            logger.warning("БД недоступна - track_article_request пропущен")
            return

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO shared.analytics_events (telegram_id, event_type, event_data)
                    VALUES ($1, 'article_request', $2::jsonb)
                    """,
                    user_id,
                    f'{{"nm_id": {nm_id}}}'
                )
                logger.debug(f"Событие article_request: user={user_id}, nm_id={nm_id}")

        except Exception as e:
            logger.warning(
                f"⚠️  Ошибка при track_article_request: {type(e).__name__}: {e}"
            )

    async def track_photos_sent(self, user_id: int, nm_id: int, count: int) -> None:
        """
        Отследить отправку фото пользователю.

        Args:
            user_id: Telegram ID пользователя
            nm_id: Артикул WB (nmId)
            count: Количество отправленных фото
        """
        pool = await get_pool()
        if pool is None:
            logger.warning("БД недоступна - track_photos_sent пропущен")
            return

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO shared.analytics_events (telegram_id, event_type, event_data)
                    VALUES ($1, 'photo_sent', $2::jsonb)
                    """,
                    user_id,
                    f'{{"nm_id": {nm_id}, "count": {count}}}'
                )
                logger.debug(
                    f"Событие photo_sent: user={user_id}, nm_id={nm_id}, count={count}"
                )

        except Exception as e:
            logger.warning(
                f"⚠️  Ошибка при track_photos_sent: {type(e).__name__}: {e}"
            )

    async def track_video_sent(self, user_id: int, nm_id: int) -> None:
        """
        Отследить отправку видео пользователю.

        Args:
            user_id: Telegram ID пользователя
            nm_id: Артикул WB (nmId)
        """
        pool = await get_pool()
        if pool is None:
            logger.warning("БД недоступна - track_video_sent пропущен")
            return

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO shared.analytics_events (telegram_id, event_type, event_data)
                    VALUES ($1, 'video_sent', $2::jsonb)
                    """,
                    user_id,
                    f'{{"nm_id": {nm_id}}}'
                )
                logger.debug(f"Событие video_sent: user={user_id}, nm_id={nm_id}")

        except Exception as e:
            logger.warning(
                f"⚠️  Ошибка при track_video_sent: {type(e).__name__}: {e}"
            )

    async def track_error(
        self,
        user_id: int,
        error_type: str,
        error_message: str
    ) -> None:
        """
        Отследить ошибку при работе с пользователем.

        Args:
            user_id: Telegram ID пользователя
            error_type: Тип ошибки (например, 'product_not_found', 'wb_api_error')
            error_message: Сообщение об ошибке
        """
        pool = await get_pool()
        if pool is None:
            logger.warning("БД недоступна - track_error пропущен")
            return

        try:
            async with pool.acquire() as conn:
                # Экранируем кавычки в JSON
                safe_message = error_message.replace('"', '\\"').replace("'", "\\'")
                await conn.execute(
                    """
                    INSERT INTO shared.analytics_events (telegram_id, event_type, event_data)
                    VALUES ($1, 'error', $2::jsonb)
                    """,
                    user_id,
                    f'{{"error_type": "{error_type}", "message": "{safe_message}"}}'
                )
                logger.debug(
                    f"Событие error: user={user_id}, type={error_type}, "
                    f"message={error_message[:50]}"
                )

        except Exception as e:
            logger.warning(
                f"⚠️  Ошибка при track_error: {type(e).__name__}: {e}"
            )

    async def get_daily_stats(self, target_date: date) -> Optional[Dict]:
        """
        Получить статистику за конкретный день.

        Args:
            target_date: Дата для получения статистики

        Returns:
            Словарь со статистикой:
            {
                "new_users": int,
                "total_users": int,
                "returning_users": int,
                "article_requests": int,
                "photos_sent": int,
                "unique_products": int,
                "videos_sent": int,
                "errors": int
            }
            None при ошибке БД
        """
        pool = await get_pool()
        if pool is None:
            logger.warning("БД недоступна - get_daily_stats пропущен")
            return None

        try:
            async with pool.acquire() as conn:
                # Начало и конец дня (UTC)
                start_dt = datetime.combine(target_date, datetime.min.time())
                end_dt = datetime.combine(
                    target_date + timedelta(days=1),
                    datetime.min.time()
                )

                # Новые пользователи за день
                new_users = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM shared.users
                    WHERE first_seen >= $1 AND first_seen < $2
                    """,
                    start_dt, end_dt
                )

                # Всего пользователей (на конец дня)
                total_users = await conn.fetchval(
                    "SELECT COUNT(*) FROM shared.users WHERE first_seen < $1",
                    end_dt
                )

                # Повторные пользователи (вернулись)
                returning_users = await conn.fetchval(
                    """
                    SELECT COUNT(DISTINCT telegram_id)
                    FROM shared.analytics_events
                    WHERE event_type = 'user_start'
                      AND created_at >= $1
                      AND created_at < $2
                      AND event_data->>'is_new' = 'false'
                    """,
                    start_dt, end_dt
                )

                # Запросы артикулов
                article_requests = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM shared.analytics_events
                    WHERE event_type = 'article_request'
                      AND created_at >= $1
                      AND created_at < $2
                    """,
                    start_dt, end_dt
                )

                # Фото отправлено (сумма count из event_data)
                photos_result = await conn.fetchrow(
                    """
                    SELECT
                        COALESCE(SUM((event_data->>'count')::int), 0) as total_photos,
                        COUNT(DISTINCT (event_data->>'nm_id')::int) as unique_products
                    FROM shared.analytics_events
                    WHERE event_type = 'photo_sent'
                      AND created_at >= $1
                      AND created_at < $2
                    """,
                    start_dt, end_dt
                )
                photos_sent = photos_result["total_photos"] if photos_result else 0
                unique_products = photos_result["unique_products"] if photos_result else 0

                # Видео отправлено
                videos_sent = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM shared.analytics_events
                    WHERE event_type = 'video_sent'
                      AND created_at >= $1
                      AND created_at < $2
                    """,
                    start_dt, end_dt
                )

                # Ошибки
                errors = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM shared.analytics_events
                    WHERE event_type = 'error'
                      AND created_at >= $1
                      AND created_at < $2
                    """,
                    start_dt, end_dt
                )

                return {
                    "new_users": new_users or 0,
                    "total_users": total_users or 0,
                    "returning_users": returning_users or 0,
                    "article_requests": article_requests or 0,
                    "photos_sent": photos_sent or 0,
                    "unique_products": unique_products or 0,
                    "videos_sent": videos_sent or 0,
                    "errors": errors or 0,
                }

        except Exception as e:
            logger.error(
                f"❌ Ошибка при get_daily_stats для {target_date}: "
                f"{type(e).__name__}: {e}"
            )
            return None
